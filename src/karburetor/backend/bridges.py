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
module to manages bridges
"""

import re

_BRIDGE_PATTERN = re.compile(
    r"""
    (?:(?P<transport>\S+)\s+)?
    (?P<addr>[0-9a-fA-F\.\[\]\:]+:\d{1,5})
    (?:\s+(?P<fingerprint>[0-9a-fA-F]{40}))?
    (?:\s+(?P<args>.+))?
    """,
    re.VERBOSE,
)


def relevant_lines(my_bridges: str, transport: str) -> list[str]:
    """
    Return bridge lines matching the requested transport
    """
    matches = [
        bridge
        for bridge in my_bridges.splitlines()
        if parse_bridge_line(bridge)["transport"] == transport
    ]
    return matches


def parse_bridge_line(line: str) -> dict[str, str | None]:
    """
    return a dict of transport, addr, id and args for a bridge line
    """
    line = line.strip()
    if line.startswith("#") or not line:
        return {"transport": None}
    match = _BRIDGE_PATTERN.fullmatch(line)
    if not match:
        return {"transport": None}
    bridge = match.groupdict()
    if "transport" not in bridge or not bridge["transport"]:
        bridge["transport"] = "vanilla"
    return bridge


def create_emoji(bridge_line: str) -> list[str]:
    """
    Create FNV-1a hash for the given address and map it to the emoji list.
    """
    emoji_list = [
        "👽️",
        "🤖",
        "🧠",
        "👁️",
        "🧙",
        "🧚",
        "🧜",
        "🐵",
        "🦧",
        "🐶",
        "🐺",
        "🦊",
        "🦝",
        "🐱",
        "🦁",
        "🐯",
        "🐴",
        "🦄",
        "🦓",
        "🦌",
        "🐮",
        "🐷",
        "🐗",
        "🐪",
        "🦙",
        "🦒",
        "🐘",
        "🦣",
        "🦏",
        "🐭",
        "🐰",
        "🐿️",
        "🦔",
        "🦇",
        "🐻",
        "🐨",
        "🦥",
        "🦦",
        "🦘",
        "🐥",
        "🐦️",
        "🕊️",
        "🦆",
        "🦉",
        "🦤",
        "🪶",
        "🦩",
        "🦚",
        "🦜",
        "🐊",
        "🐢",
        "🦎",
        "🐍",
        "🐲",
        "🦕",
        "🐳",
        "🐬",
        "🦭",
        "🐟️",
        "🐠",
        "🦈",
        "🐙",
        "🐚",
        "🐌",
        "🦋",
        "🐛",
        "🐝",
        "🐞",
        "💐",
        "🌹",
        "🌺",
        "🌻",
        "🌷",
        "🌲",
        "🌳",
        "🌴",
        "🌵",
        "🌿",
        "🍁",
        "🍇",
        "🍈",
        "🍉",
        "🍊",
        "🍋",
        "🍌",
        "🍍",
        "🥭",
        "🍏",
        "🍐",
        "🍑",
        "🍒",
        "🍓",
        "🫐",
        "🥝",
        "🍅",
        "🫒",
        "🥥",
        "🥑",
        "🍆",
        "🥕",
        "🌽",
        "🌶️",
        "🥬",
        "🥦",
        "🧅",
        "🍄",
        "🥜",
        "🥐",
        "🥖",
        "🥨",
        "🥯",
        "🥞",
        "🧇",
        "🍔",
        "🍕",
        "🌭",
        "🌮",
        "🍿",
        "🦀",
        "🦞",
        "🍨",
        "🍩",
        "🍪",
        "🎂",
        "🧁",
        "🍫",
        "🍬",
        "🍭",
        "🫖",
        "🧃",
        "🧉",
        "🧭",
        "🏔️",
        "🌋",
        "🏕️",
        "🏝️",
        "🏡",
        "⛲️",
        "🎠",
        "🎡",
        "🎢",
        "💈",
        "🚆",
        "🚋",
        "🚍️",
        "🚕",
        "🚗",
        "🚚",
        "🚜",
        "🛵",
        "🛺",
        "🛴",
        "🛹",
        "🛼",
        "⚓️",
        "⛵️",
        "🛶",
        "🚤",
        "🚢",
        "✈️",
        "🚁",
        "🚠",
        "🛰️",
        "🚀",
        "🛸",
        "⏰",
        "🌙",
        "🌡️",
        "☀️",
        "🪐",
        "🌟",
        "🌀",
        "🌈",
        "☂️",
        "❄️",
        "☄️",
        "🔥",
        "💧",
        "🌊",
        "🎃",
        "✨",
        "🎈",
        "🎉",
        "🎏",
        "🎀",
        "🎁",
        "🎟️",
        "🏆️",
        "⚽️",
        "🏀",
        "🏈",
        "🎾",
        "🥏",
        "🏓",
        "🏸",
        "🤿",
        "🥌",
        "🎯",
        "🪀",
        "🪁",
        "🔮",
        "🎲",
        "🧩",
        "🎨",
        "🧵",
        "👕",
        "🧦",
        "👗",
        "🩳",
        "🎒",
        "👟",
        "👑",
        "🧢",
        "💄",
        "💍",
        "💎",
        "📢",
        "🎶",
        "🎙️",
        "📻️",
        "🎷",
        "🪗",
        "🎸",
        "🎺",
        "🎻",
        "🪕",
        "🥁",
        "☎️",
        "🔋",
        "💿️",
        "🧮",
        "🎬️",
        "💡",
        "🔦",
        "🏮",
        "📕",
        "🏷️",
        "💳️",
        "✏️",
        "🖌️",
        "🖍️",
        "📌",
        "📎",
        "🔑",
        "🪃",
        "🏹",
        "⚖️",
        "🧲",
        "🧪",
        "🧬",
        "🔬",
        "🔭",
        "📡",
        "🪑",
        "🧹",
        "🗿",
    ]
    prime = 0x01000193
    offset = 0x811C9DC5
    hash_value = offset
    # Calculate FNV-1a hash of the bridge_line
    for byte in bridge_line.encode("utf-8"):
        hash_value = (hash_value ^ byte) * prime
        hash_value %= 2**32  # Get the last 32-bit of the integer
    # Map every 4 bytes of the hash to emojis
    hash_bytes = hash_value.to_bytes(length=4, byteorder="big")
    return [emoji_list[hash_bytes[i] % len(emoji_list)] for i in range(4)]
