# © 2026 KDE Farsi Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
KDE system-proxy backend.

This replaces tractor's GNOME ``org.gnome.system.proxy`` GSettings calls.
KDE stores system-wide proxy settings in ``~/.config/kioslaverc`` under the
``[Proxy Settings]`` group (read by KIO/KProtocolManager and by Plasma's
System Settings "Network Proxy" module), so it is fully KDE-compatible.

``ProxyType`` values understood by KDE:

* ``0`` no proxy
* ``1`` manual proxy
* ``2`` PAC (proxy auto-config) URL
* ``3`` WPAD (auto-detect)
* ``4`` environment variables
* ``5`` system (other)
"""

import os

from configparser import ConfigParser

PROXY_CONFIG = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    "kioslaverc",
)

_PROXY_GROUP = "Proxy Settings"


def _read() -> ConfigParser:
    """Read kioslaverc into a fresh parser."""
    parser = ConfigParser(interpolation=None)
    if os.path.isfile(PROXY_CONFIG):
        try:
            parser.read(PROXY_CONFIG, encoding="utf-8")
        except OSError:
            pass
    if not parser.has_section(_PROXY_GROUP):
        parser.add_section(_PROXY_GROUP)
    return parser


def _write(parser: ConfigParser) -> None:
    """Persist kioslaverc."""
    os.makedirs(os.path.dirname(PROXY_CONFIG), exist_ok=True)
    with open(PROXY_CONFIG, "w", encoding="utf-8") as file:
        parser.write(file)


def _manual_host(parser: ConfigParser, key: str) -> tuple[str, int]:
    """Return ``(host, port)`` parsed from a ``scheme://host:port`` value."""
    value = parser.get(_PROXY_GROUP, key, fallback="")
    if not value:
        return "", 0
    # strip scheme:// if present
    rest = value.split("://", maxsplit=1)[-1]
    host, _, port = rest.rpartition(":")
    if not port.isdigit():
        return "", 0
    return host, int(port)


def is_proxy_set(socks_host: str, socks_port: int) -> bool:
    """
    Return True when kioslaverc is set to manual proxy pointing at our
    SOCKS listener.
    """
    parser = _read()
    if parser.get(_PROXY_GROUP, "ProxyType", fallback="0") != "1":
        return False
    host, port = _manual_host(parser, "socksProxy")
    return host == socks_host and port == socks_port


def get_proxy() -> tuple[str, str, int]:
    """
    Return the currently configured manual proxy as
    ``(mode, host, port)`` where mode is ``"socks"``, ``"http"``, ``"https"``
    or ``"none"``.
    """
    parser = _read()
    if parser.get(_PROXY_GROUP, "ProxyType", fallback="0") != "1":
        return "none", "", 0
    for key, mode in (
        ("socksProxy", "socks"),
        ("httpProxy", "http"),
        ("httpsProxy", "https"),
    ):
        host, port = _manual_host(parser, key)
        if host and port:
            return mode, host, port
    return "none", "", 0


def proxy_set(socks_host: str, socks_port: int, ignore_hosts: list[str]) -> None:
    """
    Configure KDE's system proxy to route everything through the local
    Tor SOCKS listener.
    """
    parser = _read()
    section = parser[_PROXY_GROUP]
    section["ProxyType"] = "1"  # manual
    section["httpProxy"] = f"http://{socks_host}:{socks_port}"
    section["httpsProxy"] = f"http://{socks_host}:{socks_port}"
    section["ftpProxy"] = f"http://{socks_host}:{socks_port}"
    section["socksProxy"] = f"socks://{socks_host}:{socks_port}"
    section["NoProxyFor"] = ",".join(ignore_hosts)
    section["ProxyCgiScript"] = ""
    section["ReversedException"] = "false"
    _write(parser)


def proxy_unset(mode: str, host: str, port: int) -> None:
    """
    Restore the proxy configuration that was active before karburetor set it.

    Args:
        mode: Previous mode. ``"none"`` disables the proxy, otherwise a
            manual proxy with the given host/port is written back.
    """
    parser = _read()
    section = parser[_PROXY_GROUP]
    if mode == "none":
        section["ProxyType"] = "0"  # no proxy
        section.pop("httpProxy", None)
        section.pop("httpsProxy", None)
        section.pop("ftpProxy", None)
        section.pop("socksProxy", None)
    else:
        section["ProxyType"] = "1"
        if mode == "socks":
            section["socksProxy"] = f"socks://{host}:{port}"
        elif mode == "http":
            section["httpProxy"] = f"http://{host}:{port}"
        elif mode == "https":
            section["httpsProxy"] = f"https://{host}:{port}"
    _write(parser)
