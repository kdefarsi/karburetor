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
Snowflake transport plugin
"""

from ..transport import PluggableTransport, get_executable, registry


class Snowflake(PluggableTransport):
    """
    Snowflake pluggable transport
    """

    name = "snowflake"

    def render_bridge_prelude(self) -> str:
        exe = get_executable(self.name)
        return (
            "UseBridges 1\n"
            f"ClientTransportPlugin snowflake exec {exe} "
            "-ice stun:stun.antisip.com:347,"
            "stun:stun.epygi.com:3478,"
            "stun:stun.uls.co.za:3478,"
            "stun:stun.voipgate.com:3478,"
            "stun:stun.mixvoip.com:3478,"
            "stun:stun.nextcloud.com:3478,"
            "stun:stun.bethesda.net:3478,"
            "stun:stun.nextcloud.com:443\n"
        )


registry.register(Snowflake)
