# © 2020-2026 Danial Behzadi <dani.behzi@ubuntu.com>
# © 2026 KDE Farsi Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
real actions of tractor
"""

import os
import signal
import threading
from collections.abc import Callable
from shutil import rmtree

from stem.process import launch_tor
from stem.util import term

from . import checks, control, db, proxy, tractorrc

no_color = "NO_COLOR" in os.environ

#: Optional callables receiving every log line (used by the GUI).
LOG_SINKS: list[Callable[[str], None]] = []


def add_log_sink(sink: Callable[[str], None]) -> None:
    """
    Register a callable that receives every produced log line.
    """
    LOG_SINKS.append(sink)


def remove_log_sink(sink: Callable[[str], None]) -> None:
    """
    Unregister a previously added log sink.
    """
    if sink in LOG_SINKS:
        LOG_SINKS.remove(sink)


def _emit(line: str) -> None:
    """
    Print a line to standard output and forward it to registered sinks.
    """
    print(term.format(line, "" if no_color else term.Color.BLUE), flush=True)
    for sink in LOG_SINKS:
        try:
            sink(line)
        except Exception:
            pass


def _print_bootstrap_lines(line: str) -> None:
    """
    prints bootstrap line in standard output
    """
    if "Bootstrapped " in line:
        _emit(line)


def _print_all_lines(line: str) -> None:
    """
    prints all lines in standard output
    """
    _emit(line)


def _finish_notification(verbose: bool) -> None:
    """
    Notify user after start finished
    """
    if not checks.running():
        print(
            term.format(
                "Tractor could not connect.\n"
                "Please check your connection and try again.",
                "" if no_color else term.Attr.BOLD,
                "" if no_color else term.Color.RED,
            )
        )
    else:
        checks.verbose_print(
            term.format(
                "Connected",
                "" if no_color else term.Attr.BOLD,
                "" if no_color else term.Color.GREEN,
            ),
            verbose,
        )
        if db.get_val("auto-set"):
            proxy.proxy_set(verbose)
        else:
            checks.verbose_print(
                term.format(
                    "You may set the proxy manually.",
                    "",
                    "" if no_color else term.Color.YELLOW,
                ),
                verbose,
            )
        if db.get_val("hidden-services"):
            data_dir = db.get_data_directory()
            service_dir = os.path.join(data_dir, "hidden_service")
            hostname_file = os.path.join(service_dir, "hostname")
            with open(hostname_file, encoding="utf-8") as file:
                address = file.read()
            checks.verbose_print(
                term.format(
                    f"onion address: {address}",
                    "",
                    "" if no_color else term.Color.YELLOW,
                ),
                verbose,
            )


def _register_io_watches(proc, print_func: Callable[[str], None]) -> list[threading.Thread]:
    """
    Start daemon threads reading ``proc.stdout`` and ``proc.stderr`` and
    forwarding every complete line to ``print_func``.  This replaces the
    upstream GLib ``io_add_watch`` loop so no GLib main loop is required.
    """
    threads: list[threading.Thread] = []

    def reader(stream) -> None:
        try:
            for raw in iter(stream.readline, b""):
                if raw:
                    print_func(raw.decode(errors="replace").rstrip())
        except OSError:
            pass
        finally:
            try:
                stream.close()
            except OSError:
                pass

    for stream in (proc.stdout, proc.stderr):
        if stream is None:
            continue
        thread = threading.Thread(target=reader, args=(stream,), daemon=True)
        thread.start()
        threads.append(thread)
    return threads


def _launch(torrc: str, tmpdir: str, verbose: bool) -> None:
    """
    Actually launch tor and, when verbose, stream its logs to standard
    output and any registered log sinks until the process exits.
    """
    msg_handler = checks.verbose_return(
        _print_bootstrap_lines, _print_all_lines, verbose
    )
    tractor_process = None
    stream_threads = []
    try:
        tractor_process = launch_tor(
            torrc_path=torrc,
            init_msg_handler=msg_handler,
            timeout=None,
            close_output=not (verbose),
        )
        db.set_val("pid", tractor_process.pid)
    except OSError as error:
        print(term.format(f"{error}\n", "" if no_color else term.Color.RED))
    except KeyboardInterrupt:
        pass
    else:
        _finish_notification(verbose)
        if verbose:
            # Stream all tor logs until the process exits
            stream_threads = _register_io_watches(
                tractor_process, _print_all_lines
            )

            def _terminate():
                tractor_process.terminate()
                os.killpg(os.getpgid(tractor_process.pid), signal.SIGTERM)
                db.reset("pid")

            try:
                tractor_process.wait()
            except KeyboardInterrupt:
                _terminate()
    finally:
        for thread in stream_threads:
            thread.join(timeout=0.5)
        if os.path.exists(tmpdir):
            rmtree(tmpdir, ignore_errors=True)


def _start_launch(verbose: bool) -> None:
    """
    Start launching tor
    """
    try:
        tmpdir, torrc = tractorrc.create()
    except ValueError as error:
        print(
            term.format(
                f"Error Creating torrc. Check your configurations\n{error}",
                "" if no_color else term.Attr.BOLD,
                "" if no_color else term.Color.RED,
            )
        )
    except OSError as error:
        print(
            term.format(
                str(error),
                "" if no_color else term.Attr.BOLD,
                "" if no_color else term.Color.RED,
            )
        )
    else:
        checks.verbose_print(
            term.format(
                "Starting connection…",
                "" if no_color else term.Attr.BOLD,
                "" if no_color else term.Color.YELLOW,
            ),
            verbose,
        )
        _launch(torrc, tmpdir, verbose)


def start(verbose: bool = False) -> None:
    """
    starts onion routing
    """
    if not checks.running():
        _start_launch(verbose)
    else:
        print(
            term.format(
                "Tractor is already started",
                "" if no_color else term.Attr.BOLD,
                "" if no_color else term.Color.GREEN,
            )
        )


def stop(verbose: bool = False) -> None:
    """
    stops onion routing
    """
    if checks.running():
        control.send_signal("term")
        db.reset("pid")
        proxy.proxy_unset()
        db.reset("upstream-proxy")
        checks.verbose_print(
            term.format(
                "Tractor stopped",
                "" if no_color else term.Attr.BOLD,
                "" if no_color else term.Color.YELLOW,
            ),
            verbose,
        )
    else:
        checks.verbose_print(
            term.format(
                "Tractor seems to be stopped.",
                "" if no_color else term.Attr.BOLD,
                "" if no_color else term.Color.YELLOW,
            ),
            verbose,
        )


def restart(verbose: bool = False) -> None:
    """
    stop, then start
    """
    stop(verbose)
    start(verbose)


def new_id(verbose: bool = False) -> None:
    """
    gives user a new identity
    """
    if not checks.running():
        print(
            term.format(
                "Tractor is stopped.",
                "" if no_color else term.Attr.BOLD,
                "" if no_color else term.Color.YELLOW,
            )
        )
    else:
        control.send_signal("newnym")
        checks.verbose_print(
            term.format(
                "You now have a new ID.",
                "" if no_color else term.Attr.BOLD,
                "" if no_color else term.Color.GREEN,
            ),
            verbose,
        )


def kill_tor(verbose: bool = False) -> None:
    """
    kill tor process
    """
    pid = control.get_pid()
    if pid:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        db.reset("pid")
        checks.verbose_print(
            term.format(
                "Tor process has been successfully killed!",
                "" if no_color else term.Attr.BOLD,
                "" if no_color else term.Color.GREEN,
            ),
            verbose,
        )
    else:
        checks.verbose_print(
            term.format(
                "Couldn't find any process to kill!",
                "" if no_color else term.Attr.BOLD,
                "" if no_color else term.Color.RED,
            ),
            verbose,
        )
