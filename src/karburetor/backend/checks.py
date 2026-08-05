# © 2020-2025 Danial Behzadi <dani.behzi@ubuntu.com>
# © 2026 KDE Farsi Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
actions for tractor internals
"""

import socket
import urllib
from contextlib import contextmanager

import socks
from stem.util import system

from . import control, db, kde_proxy


def running() -> bool:
    """
    checks if Tractor is running or not
    """
    if system.is_running("tor"):
        pid = control.get_pid()
        if pid:
            return system.is_running(pid)
    return False


def _getaddrinfo(*args):
    """
    Perform DNS resolution through the socket
    """
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (args[0], args[1]))]


@contextmanager
def _patch_socket():
    """
    Context manager for mokey patching the socket
    """
    old_socket = socket.socket
    old_getaddrinfo = socket.getaddrinfo
    socket.socket = socks.socksocket
    socket.getaddrinfo = _getaddrinfo
    try:
        yield
    finally:
        socket.socket = old_socket
        socket.getaddrinfo = old_getaddrinfo


def _fetched() -> bool:
    """
    Checks if the expected resource fetched or not
    """
    port = control.get_listener("socks")[1]
    host = "https://check.torproject.org/"
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", port)
    expectation = "Congratulations."
    err = urllib.error
    with _patch_socket():
        try:
            with urllib.request.urlopen(host) as request:
                status = request.status
                response = request.read().decode("utf-8")
        except (err.HTTPError, err.URLError, TimeoutError):
            return False
    return status == 200 and expectation in response


def connected() -> bool:
    """
    checks if Tractor is connected or not
    """
    if running():
        return _fetched()
    return False


def proxy_set() -> bool:
    """
    checks if proxy is set or not
    """
    try:
        x_ip, x_port = control.get_listener("socks")
    except ValueError:
        x_ip = "0.0.0.0" if db.get_val("accept-connection") else "127.0.0.1"
        x_port = db.get_val("socks-port")
    return kde_proxy.is_proxy_set(x_ip, x_port)


def verbose_print(text: str, verbose):
    """
    Print text only if the verbose is True
    """
    if verbose:
        print(text)


def verbose_return(obj1: type, obj2: type, verbose: bool):
    """
    Return object based on verbosity
    """
    if verbose:
        return obj2
    return obj1
