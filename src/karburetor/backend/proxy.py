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
Module for setting and removing the KDE system proxy.

This is a KDE port of tractor's ``proxy.py``: it configures KDE's proxy
settings (``~/.config/kioslaverc``) instead of GNOME's ``org.gnome.system
.proxy`` GSettings keys.
"""

from os import environ

from stem.util import term

from . import checks, control, db
from . import kde_proxy

no_color = "NO_COLOR" in environ


def proxy_set(verbose: bool = False) -> None:
    """
    Setup proxy
    """
    if not checks.running():
        print("Tractor is not running!")
    elif checks.proxy_set():
        checks.verbose_print("Proxy is already set", verbose)
    else:
        mode, host, port = get_proxy()
        if mode in ["socks", "https", "http"]:
            db.set_val("upstream-proxy", (mode, host, port))
        my_ip, socks_port = control.get_listener("socks")
        ignored = db.get_val("proxy-ignore")
        kde_proxy.proxy_set(my_ip, socks_port, ignored)
        checks.verbose_print(
            term.format(
                "Proxy has been set.",
                "",
                "" if no_color else term.Color.GREEN,
            ),
            verbose,
        )


def proxy_unset(verbose: bool = False) -> None:
    """
    Unset proxy
    """
    if checks.proxy_set():
        mode, host, port = tuple(db.get_val("upstream-proxy"))
        kde_proxy.proxy_unset(mode, host, port)
        checks.verbose_print("Proxy unset", verbose)
    else:
        checks.verbose_print("Proxy is not set", verbose)


def get_proxy() -> tuple[str, str, int]:
    """
    Get current proxy of the system
    """
    try:
        if checks.proxy_set():
            return "none", "", 0
    except ValueError:
        return "none", "", 0
    return kde_proxy.get_proxy()
