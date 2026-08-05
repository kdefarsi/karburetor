# © 2026 KDE Farsi Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Shared INI store used by the karburetor backend.

The settings file lives at ``$XDG_CONFIG_HOME/karburetorrc`` (default
``~/.config/karburetorrc``) and uses the KConfig INI layout, so KDE's own
tools (``kwriteconfig6``, System Settings) can read and modify it.

The GUI's ``Settings`` QObject uses ``QSettings`` against the same file;
these helpers are the pure-Python counterpart used by the CLI/backend so it
runs without Qt.
"""

import os

from configparser import ConfigParser

CONFIG_HOME_ENV = "XDG_CONFIG_HOME"


def config_file_path() -> str:
    """Return the absolute path of the shared settings file."""
    base = os.environ.get(CONFIG_HOME_ENV)
    if not base:
        base = os.path.expanduser("~/.config")
    return os.path.join(base, "karburetorrc")


def read_store() -> ConfigParser:
    """Read the settings file into a fresh ``ConfigParser``."""
    parser = ConfigParser(interpolation=None)
    path = config_file_path()
    if os.path.isfile(path):
        try:
            parser.read(path, encoding="utf-8")
        except OSError:
            pass
    return parser


def write_store(parser: ConfigParser) -> None:
    """Persist the parser to the settings file with 0600 permissions."""
    path = config_file_path()
    directory = os.path.dirname(path)
    os.makedirs(directory, mode=0o700, exist_ok=True)
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as file:
        parser.write(file)
    os.chmod(temp_path, 0o600)
    os.replace(temp_path, path)
