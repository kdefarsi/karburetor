# © 2024-2026 Danial Behzadi <dani.behzi@ubuntu.com>
# © 2026 KDE Farsi Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Things to do with control socket
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager

from stem import Signal
from stem.connection import connect
from stem.control import Controller

from . import bridges, db


def _get_controller() -> Controller | None:
    """
    Return the control socket
    """
    data_dir = db.get_data_directory()
    socket_path = os.path.join(data_dir, "control.sock")
    controller = connect(control_socket=socket_path)
    return controller


@contextmanager
def _open_controller() -> Iterator[Controller | None]:
    """Open a controller and guarantee that it is closed after use."""
    controller = _get_controller()
    try:
        yield controller
    finally:
        if controller:
            controller.close()


def send_signal(signal: str) -> None:
    """
    Send a signal to the tor process
    """
    signals = {"term": Signal.TERM, "newnym": Signal.NEWNYM}
    try:
        tor_signal = signals[signal]
    except KeyError as error:
        raise ValueError(f"Wrong signal '{signal}'.") from error
    with _open_controller() as controller:
        if controller:
            controller.signal(tor_signal)


def get_listener(listener_type: str) -> tuple[str, int]:
    """
    Get configuration from control socket
    """
    with _open_controller() as controller:
        if controller:
            value = controller.get_listeners(listener_type)
            return value[0]
    raise ValueError("No listener.")


def get_pid() -> int:
    """
    Get pid of the tor process
    """
    with _open_controller() as controller:
        if controller:
            return controller.get_pid()
    return 0


def get_bridge() -> str:
    """
    Return the currently used bridge/transport from Tor runtime status.
    """
    with _open_controller() as controller:
        if not controller or not controller.get_conf("UseBridges"):
            return ""
        established = controller.get_info("status/circuit-established", "0")
        if established != "1":
            return ""
        bridge_lines = controller.get_conf("Bridge", multiple=True)
        if not bridge_lines:
            return ""
        bridge_by_fingerprint = {}
        for line in bridge_lines:
            fingerprint = bridges.parse_bridge_line(line).get("fingerprint")
            if fingerprint:
                bridge_by_fingerprint[fingerprint] = line
        if not bridge_by_fingerprint:
            return ""
        # Find most recent circuit and match its first hop to a bridge.
        circuits = controller.get_circuits()
    built = [
        circuit
        for circuit in circuits
        if str(circuit.status) == "BUILT" and circuit.path
    ]
    if not built:
        return ""
    # "Most recent" heuristic: highest circuit id (good practical proxy).
    latest = max(built, key=lambda c: int(c.id))
    first_hop_fp = latest.path[0][0].lstrip("$").upper()
    return (
        "".join(bridges.create_emoji(bridge_by_fingerprint[first_hop_fp]))
        if first_hop_fp in bridge_by_fingerprint
        else ""
    )
