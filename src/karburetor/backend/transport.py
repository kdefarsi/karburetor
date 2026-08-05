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
Transport registry and base classes for pluggable transports.

This module provides executable lookup, transport base types, and the
runtime registry used by tractorrc generation.
"""

import importlib
import pkgutil
from dataclasses import dataclass
from typing import ClassVar

from . import config
from . import transports as transports_path


def get_executable(transport: str) -> str:
    """
    Return executable path configured for a transport
    """
    return config.get_executable(transport)


@dataclass(slots=True)
class PluggableTransport:
    """
    Base class for a pluggable transport
    """

    name: ClassVar[str] = ""

    def render_bridge_prelude(self) -> str:
        """
        Render transport-specific torrc prelude lines
        """
        return "UseBridges 1\n"


class TransportRegistry:
    """
    Registry for available pluggable transport classes.
    The registry is populated by importing modules in `tractor.transports`
    """

    def __init__(self) -> None:
        self._by_name: dict[str, type[PluggableTransport]] = {}
        self._loaded = False

    def register(self, cls: type[PluggableTransport]) -> None:
        """
        Register a transport class by its `name` attribute

        Raises:
            ValueError: If `cls.name` is empty
        """
        if not cls.name:
            raise ValueError(f"{cls.__name__} has empty name")
        self._by_name[cls.name] = cls

    def _load_all(self) -> None:
        """
        Import all transport modules under `tractor.transports` once.
        Importing a module is expected to register one or more transport
        classes via `registry.register(...)` at module scope
        """
        if self._loaded:
            return
        for m in pkgutil.iter_modules(transports_path.__path__):
            if m.name.startswith("_"):
                continue
            importlib.import_module(f"{transports_path.__name__}.{m.name}")
        self._loaded = True

    def get_transport(self, name: str) -> PluggableTransport:
        """
        Create a transport instance by registered name

        Raises:
            ValueError: If `name` is unknown
        """
        self._load_all()
        try:
            return self._by_name[name]()
        except KeyError as exc:
            raise ValueError(f"Unknown transport: {name}") from exc

    def get_all(self) -> list[str]:
        """
        Load and return the sorted names of all available transports
        """
        self._load_all()
        return sorted(self._by_name.keys())


registry = TransportRegistry()
