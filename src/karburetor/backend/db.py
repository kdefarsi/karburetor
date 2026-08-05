# © 2023-2026 Danial Behzadi <dani.behzi@ubuntu.com>
# © 2026 KDE Farsi Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Settings storage for karburetor.

This is a KDE port of tractor's `db.py`. Instead of GSettings/dconf it
reads and writes a plain KConfig-compatible INI file at
``$XDG_CONFIG_HOME/karburetorrc`` (i.e. ``~/.config/karburetorrc``) which
the GUI (QSettings) and the CLI backend share. The file format is exactly
what KDE's KConfig produces, so it can be edited with ``kwriteconfig6``.

The public API mirrors the upstream tractor module so the rest of the
vendored backend works unchanged:

* ``dconf()`` (kept for compatibility, returns a ``Store``)
* ``get_val(key)`` / ``set_val(key, value)`` / ``reset(key)``
* ``get_config_directory()`` / ``get_data_directory()``
"""

import json
import os

from configparser import ConfigParser

from .store import config_file_path, read_store, write_store

CONFIG_DIR_ENV = "XDG_CONFIG_HOME"
DATA_DIR_ENV = "XDG_DATA_HOME"

# key name in the INI file -> type
_INT_KEYS = ("pid", "socks-port", "http-port", "dns-port")
_STR_KEYS = ("exit-node", "bridge-type")
_BOOL_KEYS = (
    "accept-connection",
    "fascist-firewall",
    "auto-set",
    "hidden-services",
)
_LIST_KEYS = ("proxy-ignore",)
_TUPLE_KEYS = ("upstream-proxy",)

#: Schema defaults matching the upstream tractor.gschema.xml
_DEFAULTS: dict[str, object] = {
    "auto-set": False,
    "proxy-ignore": [
        "localhost",
        "127.0.0.0/8",
        "::1",
        "192.168.0.0/16",
        "10.0.0.0/8",
        "172.16.0.0/12",
    ],
    "exit-node": "ww",
    "socks-port": 9052,
    "dns-port": 9053,
    "http-port": 9080,
    "pid": 0,
    "bridge-type": "none",
    "accept-connection": False,
    "fascist-firewall": False,
    "upstream-proxy": ("none", "", 0),
    "hidden-services": False,
}


def _to_ini(key: str) -> str:
    """Convert a tractor key name to the karburetorrc INI key."""
    return key.replace("-", "").capitalize()


def _user_dir(env: str, fallback: str) -> str:
    """Return an XDG base directory (XDG_CONFIG_HOME/XDG_DATA_HOME)."""
    base = os.environ.get(env)
    if not base:
        base = os.path.expanduser(fallback)
    return base


def get_config_directory() -> str:
    """Return the tractor config directory (~/.config/tractor), 0700."""
    directory = os.path.join(_user_dir(CONFIG_DIR_ENV, "~/.config"), "tractor")
    os.makedirs(directory, mode=0o700, exist_ok=True)
    return directory


def get_data_directory() -> str:
    """Return the tractor data directory (~/.local/share/tractor), 0700."""
    directory = os.path.join(_user_dir(DATA_DIR_ENV, "~/.local/share"), "tractor")
    os.makedirs(directory, mode=0o700, exist_ok=True)
    return directory


def _read_group(group: str) -> ConfigParser:
    """Return a parser with the given group initialised, read from disk."""
    parser = read_store()
    if not parser.has_section(group):
        parser.add_section(group)
    return parser


def get_val(key: str):
    """
    Get the value of the key from the shared karburetorrc file.
    """
    parser = read_store()
    group = "General"
    section = parser[group] if parser.has_section(group) else {}

    def _raw() -> str:
        return section.get(_to_ini(key), "")

    _default = _DEFAULTS.get(key)

    if key in _INT_KEYS:
        raw = _raw()
        if not raw:
            return _default if isinstance(_default, int) else 0
        return int(raw)
    if key in _BOOL_KEYS:
        raw = _raw()
        return raw.lower() == "true" if raw else bool(_default)
    if key in _STR_KEYS:
        raw = _raw()
        return raw if raw else (str(_default) if _default is not None else "")
    if key in _LIST_KEYS:
        raw = _raw()
        return (
            [item.strip() for item in raw.split(",")]
            if raw
            else list(_default) if isinstance(_default, list) else []
        )
    if key in _TUPLE_KEYS:
        raw = _raw()
        try:
            return tuple(json.loads(raw)) if raw else tuple(_default)
        except (json.JSONDecodeError, TypeError):
            return tuple(_default)
    raise TypeError(f"key is not supported: {key}")


def set_val(
    key: str,
    value: bool | int | str | list[str] | tuple[str, str, int],
) -> None:
    """
    Set a value for the key in the shared karburetorrc file.
    """
    group = "General"
    ini_key = _to_ini(key)
    parser = _read_group(group)

    if key in _INT_KEYS:
        parser.set(group, ini_key, str(int(value)))
    elif key in _BOOL_KEYS:
        parser.set(group, ini_key, "true" if value else "false")
    elif key in _STR_KEYS:
        parser.set(group, ini_key, str(value))
    elif key in _LIST_KEYS:
        parser.set(group, ini_key, ",".join(value))
    elif key in _TUPLE_KEYS:
        parser.set(group, ini_key, json.dumps(list(value)))
    else:
        raise TypeError("key is not supported")
    write_store(parser)


def reset(key: str) -> None:
    """Reset a key to its default value."""
    parser = read_store()
    if parser.has_section("General"):
        parser.remove_option("General", _to_ini(key))
    write_store(parser)


def dconf():
    """
    Compatibility shim for the upstream module name.

    Returns a lightweight ``Store`` object exposing ``get_val``, ``set_val``
    and ``reset`` so code that kept a handle to ``dconf()`` still works.
    """
    return Store()


class Store:
    """
    Minimal proxy around the module-level functions.

    Present so callers can keep a reference (e.g. ``conf = dconf()``) like
    they could with ``Gio.Settings``.
    """

    def get_val(self, key: str):
        return get_val(key)

    def set_val(self, key: str, value) -> None:
        set_val(key, value)

    def reset(self, key: str) -> None:
        reset(key)


def data_directory() -> str:
    """
    Compatibility alias used by older carburetor code.
    """
    return get_config_directory()
