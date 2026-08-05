#!/usr/bin/python3
# © 2026 Danial Behzadi <dani.behzi@ubuntu.com>
# © 2026 KDE Farsi Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Persistent configuration store for Tractor.

This module manages the user configuration file located at:

    $XDG_CONFIG_HOME/tractor/config.ini

It stores:
- transport executable paths (``[executables]`` section), and
- per-transport bridge entries (sections such as ``[obfs4]``, ``[vanilla]``),
- hidden-service port mappings (``[hidden-service-ports]``).

Bridge entries are key-value pairs where keys are emoji IDs and values are
full bridge lines.

This is a KDE port of the upstream module: it replaces ``GLib.KeyFile`` with
a small, compatible ``KeyFile`` class built on ``configparser`` so no GLib
dependency remains.
"""

import io
import os
import shutil

from configparser import ConfigParser

from . import bridges, db

DEFAULT_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")


class KeyFile:
    """
    Drop-in replacement for the subset of ``GLib.KeyFile`` used by the
    carburetor handlers and this module.

    The storage backend is a ``ConfigParser`` with case-preserving option
    names, serialised as an INI file.
    """

    def __init__(self) -> None:
        self._parser = ConfigParser(
            interpolation=None, inline_comment_prefixes=None
        )
        self._parser.optionxform = str  # preserve key case

    def load_from_file(self, path: str, _flags: int = 0) -> None:
        """Load the key file from ``path``."""
        self._parser.read(path, encoding="utf-8")

    def to_data(self):
        """Return ``(string, None)`` like ``GLib.KeyFile.to_data()``."""
        buffer = io.StringIO()
        self._parser.write(buffer)
        return buffer.getvalue(), None

    def has_group(self, group: str) -> bool:
        """Return whether ``group`` exists."""
        return self._parser.has_section(group)

    def has_key(self, group: str, key: str) -> bool:
        """Return whether ``key`` exists in ``group``."""
        return self._parser.has_option(group, key)

    def get_keys(self, group: str):
        """Return ``(list_of_keys, None)`` like ``GLib.KeyFile.get_keys()``."""
        if not self.has_group(group):
            return [], 0
        return list(self._parser[group].keys()), len(self._parser[group])

    def get_string(self, group: str, key: str) -> str:
        """Return the string value of ``key`` in ``group``."""
        return self._parser.get(group, key, fallback="")

    def set_string(self, group: str, key: str, value: str) -> None:
        """Set the string value of ``key`` in ``group``, creating the group."""
        if not self.has_group(group):
            self._parser.add_section(group)
        self._parser.set(group, key, value)

    def remove_key(self, group: str, key: str) -> None:
        """Remove ``key`` from ``group``."""
        if self.has_option(group, key):
            self._parser.remove_option(group, key)

    def has_option(self, group: str, key: str) -> bool:
        """Return whether ``key`` exists in ``group``."""
        return self._parser.has_option(group, key)


def get_config_file_path() -> str:
    """
    Return the absolute path to the user config file.

    Ensures the application config directory exists with mode ``0700``.
    If the user config file does not exist, copies the packaged default
    ``config.ini`` from the module directory and sets mode ``0600``.

    Returns:
        Absolute path to ``config.ini``.

    Raises:
        OSError: If the default config cannot be copied due to missing file
            or insufficient permissions.
    """
    config_dir = db.get_config_directory()
    config_file = os.path.join(config_dir, "config.ini")
    if not os.path.isfile(config_file):
        try:
            shutil.copyfile(DEFAULT_CONFIG, config_file)
        except (PermissionError, FileNotFoundError) as exception:
            raise OSError(f"Bridge copy failed: {exception}") from exception
        os.chmod(config_file, 0o600)
    return config_file


def load_config_file() -> KeyFile:
    """
    Load and return the user configuration as a :class:`KeyFile`.
    """
    config_file_path = get_config_file_path()
    key_file = KeyFile()
    key_file.load_from_file(config_file_path)
    return key_file


def save_config_file(key_file: KeyFile) -> None:
    """
    Persist a :class:`KeyFile` to the user configuration file.
    """
    config_file_path = get_config_file_path()
    data = key_file.to_data()[0]
    with open(config_file_path, "w", encoding="utf-8") as file:
        file.write(data)
    os.chmod(config_file_path, 0o600)


def _get_group_keys(key_file: KeyFile, group: str) -> list[str]:
    """Return keys from ``group`` without leaking GLib tuple details."""
    if not key_file.has_group(group):
        return []
    result = key_file.get_keys(group)
    return list(result[0]) if result else []


def get_executable(transport: str) -> str:
    """
    Return the configured executable path for a transport.
    """
    config_file = load_config_file()
    if transport not in config_file.get_keys("executables")[0]:
        config_file.set_string("executables", transport, "")
        return ""
    return config_file.get_string("executables", transport)


def set_executable(transport: str, path: str) -> None:
    """
    Set and persist the executable path for a transport.
    """
    config_file = load_config_file()
    config_file.set_string("executables", transport, path)
    save_config_file(config_file)


def get_bridges(transport: str) -> list[str]:
    """
    Return list of bridge lines stored for a given transport section.
    """
    config_file = load_config_file()
    keys = _get_group_keys(config_file, transport)
    return [config_file.get_string(transport, key) for key in keys]


def add_bridge(transport: str, bridge_line: str) -> None:
    """
    Add a bridge line under a transport using an emoji-derived key.
    """
    config_file = load_config_file()
    bridge_key = "".join(bridges.create_emoji(bridge_line))
    config_file.set_string(transport, bridge_key, bridge_line)
    save_config_file(config_file)


def remove_bridge(transport: str, bridge_key: str) -> None:
    """
    Remove a bridge entry identified by key from a transport section.
    """
    config_file = load_config_file()
    if config_file.has_group(transport) and config_file.has_key(
        transport, bridge_key
    ):
        config_file.remove_key(transport, bridge_key)
        save_config_file(config_file)


def get_hidden_ports() -> dict[str, str]:
    """
    Return hidden-service port mappings from the config file.

    Reads entries from the ``[hidden-service-ports]`` section in
    ``config.ini``. Each key is a service name (for example ``web`` or
    ``ssh``), and each value is a mapping string in this format::

        <virtual_port> <target_host>:<target_port>

    Returns:
        A mapping of ``{name: line}`` for all entries in the section, or an
        empty mapping if the section does not exist.
    """
    config_file = load_config_file()
    keys = _get_group_keys(config_file, "hidden-service-ports")
    return {
        name: config_file.get_string("hidden-service-ports", name)
        for name in keys
    }


def add_hidden_port(name: str, port: int, host: str, target: int) -> None:
    """
    Add or update one hidden-service port mapping.

    Stores the entry in ``[hidden-service-ports]`` as::

        <name> = <port> <host>:<target>

    Raises:
        ValueError: If ``name`` or ``host`` is empty, or if either port is
        outside the valid range.
    """
    if not name.strip():
        raise ValueError("Hidden service name must not be empty.")
    if not host.strip():
        raise ValueError("Target host must not be empty.")
    if not 1 <= port <= 65535:
        raise ValueError("Virtual port must be between 1 and 65535.")
    if not 1 <= target <= 65535:
        raise ValueError("Target port must be between 1 and 65535.")
    config_file = load_config_file()
    line = f"{port} {host}:{target}"
    config_file.set_string("hidden-service-ports", name, line)
    save_config_file(config_file)


def remove_hidden_port(name: str) -> None:
    """
    Remove a hidden-service port mapping by name.
    """
    config_file = load_config_file()
    group = "hidden-service-ports"
    if config_file.has_group(group) and config_file.has_key(group, name):
        config_file.remove_key(group, name)
        save_config_file(config_file)
