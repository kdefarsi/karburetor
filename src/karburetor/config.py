# © 2026 KDE Farsi Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
GUI-side configuration helpers (country list, transport titles).

A KDE port of carburetor's ``config.py`` that does not require GSettings.
"""

import gettext
import os

import pycountry


def _nodes() -> dict:
    """
    Return a dictionary of countries and their (localized) names.
    """
    codes = ("CA", "CH", "DE", "ES", "GB", "IT", "FR", "NL", "SE", "US")
    countries = [pycountry.countries.get(alpha_2=code) for code in codes]
    language = os.environ.get("LANG", "en_US.UTF-8").split(".")[0]
    try:
        countries_l10n = gettext.translation(
            "iso3166-1", pycountry.LOCALES_DIR, [language]
        )
    except FileNotFoundError:
        country_names = [country.name for country in countries]
    else:
        country_names = [
            countries_l10n.gettext(country.name) for country in countries
        ]
    return dict(zip(countries, country_names))


NODES = _nodes()

TRANSPORT_TITLES = {
    "none": "None",
    "vanilla": "Vanilla",
    "obfs4": "Obfuscated",
    "snowflake": "Snowflake",
    "conjure": "Conjure",
    "meek_lite": "Meek",
    "webtunnel": "WebTunnel",
}


def transport_title(transport_name: str) -> str:
    """
    Return a human-readable title for a transport type.
    """
    return TRANSPORT_TITLES.get(
        transport_name, transport_name.replace("_", " ").title()
    )
