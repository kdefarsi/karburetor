# © 2026 KDE Farsi Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
QObject controller connecting the QML UI to the karburetor backend.

Connection runs the ``karburetor start --verbose`` CLI in a subprocess (with
its own process group) and streams its output into Qt signals, mirroring how
carburetor drives ``tractor start --verbose``.  All Qt signal emissions happen
from worker threads, which PySide6 delivers as queued connections, keeping the
UI thread responsive.
"""

import os
import re
import signal
import subprocess
import sys
import threading

from PySide6.QtCore import QObject, Property, Signal, Slot

from karburetor.backend import actions, checks, db, proxy

_BOOTSTRAP_RE = re.compile(r"Bootstrapped (\d+)%")
_PORT_IN_USE = "Failed to bind one of the listener ports"


class Controller(QObject):
    """
    State machine: stopped -> connecting -> running; cancelled or failed
    transitions return to stopped or dead.
    """

    stateChanged = Signal(str)
    progressChanged = Signal(int)
    titleChanged = Signal(str)
    descriptionChanged = Signal(str)
    logLine = Signal(str)
    toast = Signal(str)
    proxyChanged = Signal(bool)
    checkResult = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc = None
        self._state = "stopped"
        self._progress = 0
        self._title = "Unprotected"
        self._description = 'Press "Start" to find a secure line'
        self._reached_running = False
        self._cancelled = threading.Event()
        self._auto_set = db.get_val("auto-set")
        self._log_lock = threading.Lock()

    @Property(str, notify=stateChanged)
    def state(self) -> str:
        return self._state

    @Property(int, notify=progressChanged)
    def progress(self) -> int:
        return self._progress

    @Property(str, notify=titleChanged)
    def title(self) -> str:
        return self._title

    @Property(str, notify=descriptionChanged)
    def description(self) -> str:
        return self._description

    @Property(bool, notify=proxyChanged)
    def proxyEnabled(self) -> bool:
        return self._auto_set

    def _set_state(self, state: str) -> None:
        if self._state == state:
            return
        self._state = state
        self.stateChanged.emit(state)

    def _set_progress(self, value: int) -> None:
        value = max(0, min(100, value))
        if value == self._progress:
            return
        self._progress = value
        self.progressChanged.emit(value)

    def _set_title(self, text: str) -> None:
        if text == self._title:
            return
        self._title = text
        self.titleChanged.emit(text)

    def _set_description(self, text: str) -> None:
        if text == self._description:
            return
        self._description = text
        self.descriptionChanged.emit(text)

    def _stop_on_no_bridges(self) -> bool:
        """Return True and toast when the selected transport has no bridges."""
        from karburetor.backend import config as tconfig

        bridge_type = db.get_val("bridge-type")
        if bridge_type == "none":
            return False
        if tconfig.get_bridges(bridge_type):
            return False
        self.toast.emit("No relevant bridges found")
        return True

    def _stop_on_no_executable(self) -> bool:
        """Return True and toast when the transport executable is missing."""
        from karburetor.backend import config as tconfig

        bridge_type = db.get_val("bridge-type")
        if bridge_type in ("none", "vanilla"):
            return False
        executable = tconfig.get_executable(bridge_type)
        if executable and os.path.exists(executable):
            return False
        self.toast.emit("Transport executable not found")
        return True

    @Slot()
    def connect(self) -> None:
        """
        Start the Tor subprocess and stream its output to the UI.
        """
        if self._proc is not None:
            return
        if self._stop_on_no_executable() or self._stop_on_no_bridges():
            return
        env = os.environ.copy()
        env["NO_COLOR"] = "1"
        self._cancelled.clear()
        self._reached_running = False
        self._set_progress(0)
        self._set_title("Connecting…")
        self._set_description("Starting")
        self._set_state("connecting")
        try:
            proc = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "karburetor",
                    "start",
                    "--verbose",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env=env,
            )
        except OSError as error:
            self.toast.emit(str(error))
            self._set_state("dead")
            return
        self._proc = proc
        reader = threading.Thread(
            target=self._read_output, args=(proc,), daemon=True
        )
        reader.start()
        waiter = threading.Thread(
            target=self._wait_process, args=(proc,), daemon=True
        )
        waiter.start()

    def _read_output(self, proc: subprocess.Popen) -> None:
        """Read subprocess stdout line by line and emit Qt signals."""
        try:
            while True:
                raw = proc.stdout.readline()
                if not raw:
                    break
                line = raw.decode(errors="replace").rstrip()
                self._handle_line(line)
        except OSError:
            pass

    def _handle_line(self, line: str) -> None:
        """Parse a single log line into UI state."""
        with self._log_lock:
            self.logLine.emit(line)
            if _PORT_IN_USE in line:
                self.toast.emit("One of the listener ports is in use")
            match = _BOOTSTRAP_RE.search(line)
            if match:
                percentage = int(match.group(1))
                self._set_progress(percentage)
                notice = line.split(": ", maxsplit=1)[-1]
                self._set_description(notice)
                if percentage >= 100 and not self._reached_running:
                    self._reached_running = True
                    self._set_title("Protected")
                    self._set_description(
                        "A secure line has been established"
                    )
                    self._set_state("running")

    def _wait_process(self, proc: subprocess.Popen) -> None:
        """Wait for the subprocess and update the final state."""
        returncode = proc.wait()
        with self._log_lock:
            if proc is not self._proc:
                return
            self._proc = None
            if self._cancelled.is_set():
                # stop()/cancel() already moved us to stopped
                return
            self._set_progress(0)
            if self._reached_running:
                self._set_state("stopped")
            else:
                self._set_title("Connection failed")
                self._set_description(
                    "Check your connection and try again"
                )
                self._set_state("dead")
                if returncode != 0:
                    self.toast.emit("Failed to connect to the Tor network")

    @Slot()
    def cancel(self) -> None:
        """
        Abort a connection attempt or stop a running Tor, mirroring
        carburetor's Cancel/Stop semantics.
        """
        self._cancelled.set()
        proc = self._proc
        if proc is not None and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGINT)
            except ProcessLookupError:
                pass
        if db.get_val("auto-set"):
            try:
                proxy.proxy_unset()
            except Exception:
                pass
        self._set_progress(0)
        self._set_title("Unprotected")
        self._set_description('Press "Start" to find a secure line')
        self._set_state("stopped")

    @Slot()
    def newId(self) -> None:
        """Request a fresh Tor identity."""
        if checks.running():
            try:
                actions.new_id()
            except Exception as error:
                self.toast.emit(str(error))
            else:
                self.toast.emit("You have a new identity!")
        else:
            self.toast.emit("Tractor is not running!")

    @Slot()
    def checkConnection(self) -> None:
        """Check the connection in a worker thread."""
        self._set_title("Checking…")
        self._set_description("")
        checker = threading.Thread(
            target=self._check_worker, daemon=True
        )
        checker.start()

    def _check_worker(self) -> None:
        result = checks.connected()
        if not result:
            self._set_title("Unprotected")
            self._set_description("Failed to connect to the Tor network")
        else:
            self._set_title("Protected")
            self._set_description("Your connection is secure")
        self.checkResult.emit(result)

    @Slot(bool)
    def setProxy(self, enabled: bool) -> None:
        """Toggle the system proxy (kioslaverc)."""
        db.set_val("auto-set", enabled)
        self._auto_set = enabled
        self.proxyChanged.emit(enabled)
        if checks.running():
            try:
                if enabled:
                    proxy.proxy_set()
                    self.toast.emit("Proxy has been set")
                else:
                    proxy.proxy_unset()
                    self.toast.emit("Proxy has been unset")
            except Exception as error:
                self.toast.emit(str(error))
