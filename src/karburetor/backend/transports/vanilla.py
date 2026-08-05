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
# pylint: disable=too-few-public-methods

"""
Vanilla transport plugin
"""

from ..transport import PluggableTransport, registry


class Vanilla(PluggableTransport):
    """
    Vanilla pluggable transport
    """

    name = "vanilla"

    def render_bridge_prelude(self) -> str:
        return "UseBridges 1\n"


registry.register(Vanilla)
