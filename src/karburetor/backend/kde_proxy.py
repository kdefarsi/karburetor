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

The settings are written through ``kwriteconfig6`` (falling back to
``kwriteconfig5``) instead of editing the file directly, and after every
change ``kded6`` is told to ``reconfigure`` so running KDE applications pick
up the new proxy configuration immediately.
"""

import os
import shutil
import subprocess

PROXY_CONFIG = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    "kioslaverc",
)

_PROXY_GROUP = "Proxy Settings"


def _kwriteconfig() -> str:
    """Return the path of the kwriteconfig binary, 6 preferred over 5."""
    for name in ("kwriteconfig6", "kwriteconfig5"):
        path = shutil.which(name)
        if path:
            return path
    raise FileNotFoundError("kwriteconfig6 or kwriteconfig5 not found")


def _kreadconfig() -> str:
    """Return the path of the kreadconfig binary, 6 preferred over 5."""
    for name in ("kreadconfig6", "kreadconfig5"):
        path = shutil.which(name)
        if path:
            return path
    raise FileNotFoundError("kreadconfig6 or kreadconfig5 not found")


def _get(key: str) -> str:
    """Return the value of a ``[Proxy Settings]`` key, or ``""``."""
    result = subprocess.run(
        [
            _kreadconfig(),
            "--file",
            PROXY_CONFIG,
            "--group",
            _PROXY_GROUP,
            "--key",
            key,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _set(key: str, value: str) -> None:
    """Write a ``[Proxy Settings]`` key through kwriteconfig."""
    subprocess.run(
        [
            _kwriteconfig(),
            "--file",
            PROXY_CONFIG,
            "--group",
            _PROXY_GROUP,
            "--key",
            key,
            value,
        ],
        check=False,
    )


def _delete(key: str) -> None:
    """Remove a ``[Proxy Settings]`` key through kwriteconfig."""
    subprocess.run(
        [
            _kwriteconfig(),
            "--file",
            PROXY_CONFIG,
            "--group",
            _PROXY_GROUP,
            "--key",
            key,
            "--delete",
        ],
        check=False,
    )


def _reload() -> None:
    """
    Tell running KDE applications to reload their proxy configuration. Best
    effort: no-op when no qdbus/dbus-send binary is available.

    Two mechanisms are used:

    * ``org.kde.kded6.reconfigure`` reloads kded modules so they re-read
      ``kioslaverc``.
    * The ``org.kde.KIO ProxySettingsChanged`` signal is what Plasma's own
      System Settings proxy module emits after saving; KIO-based applications
      listen for it and flush their cached proxy settings.
    """
    for name in ("qdbus6", "qdbus"):
        path = shutil.which(name)
        if path:
            subprocess.run(
                [path, "org.kde.kded6", "/kded", "org.kde.kded6.reconfigure"],
                check=False,
            )
            break
    path = shutil.which("dbus-send")
    if path:
        subprocess.run(
            [
                path,
                "--session",
                "--type=signal",
                "/KIO",
                "org.kde.KIO.ProxySettingsChanged",
            ],
            check=False,
        )


def _manual_host(value: str) -> tuple[str, int]:
    """Return ``(host, port)`` parsed from a ``scheme://host:port`` value."""
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
    if _get("ProxyType") != "1":
        return False
    host, port = _manual_host(_get("socksProxy"))
    return host == socks_host and port == socks_port


def get_proxy() -> tuple[str, str, int]:
    """
    Return the currently configured manual proxy as
    ``(mode, host, port)`` where mode is ``"socks"``, ``"http"``, ``"https"``
    or ``"none"``.
    """
    if _get("ProxyType") != "1":
        return "none", "", 0
    for key, mode in (
        ("socksProxy", "socks"),
        ("httpProxy", "http"),
        ("httpsProxy", "https"),
    ):
        host, port = _manual_host(_get(key))
        if host and port:
            return mode, host, port
    return "none", "", 0


def proxy_set(socks_host: str, socks_port: int, ignore_hosts: list[str]) -> None:
    """
    Configure KDE's system proxy to route everything through the local
    Tor SOCKS listener, then reload kded.
    """
    proxy = f"http://{socks_host}:{socks_port}"
    _set("ProxyType", "1")  # manual
    _set("httpProxy", proxy)
    _set("httpsProxy", proxy)
    _set("ftpProxy", proxy)
    _set("socksProxy", f"socks://{socks_host}:{socks_port}")
    _set("NoProxyFor", ",".join(ignore_hosts))
    _set("ProxyCgiScript", "")
    _set("ReversedException", "false")
    _reload()


def proxy_unset(mode: str, host: str, port: int) -> None:
    """
    Restore the proxy configuration that was active before karburetor set it.

    Args:
        mode: Previous mode. ``"none"`` disables the proxy, otherwise a
            manual proxy with the given host/port is written back.
    """
    if mode == "none":
        _set("ProxyType", "0")  # no proxy
        for key in ("httpProxy", "httpsProxy", "ftpProxy", "socksProxy"):
            _delete(key)
    else:
        _set("ProxyType", "1")
        if mode == "socks":
            _set("socksProxy", f"socks://{host}:{port}")
        elif mode == "http":
            _set("httpProxy", f"http://{host}:{port}")
        elif mode == "https":
            _set("httpsProxy", f"https://{host}:{port}")
    _reload()
