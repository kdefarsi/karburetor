# © 2026 KDE Farsi Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
System tray integration via KStatusNotifierItem.

The tray keeps Karburetor available in the Plasma system tray while the
window is closed and exposes the essential actions (connect/stop, new
identity, proxy toggle and quit).

Bugs fixed vs. original:
  1. KStatusNotifierItem defaults to ItemStatus.Passive (hidden).
     Must call setStatus(Active) to make the item visible.
  2. setStandardActionsEnabled(False) removes the built-in "Quit" action
     that KSNI adds by default — otherwise two Quit entries appear.
  3. setIconByPixmap() expects a QIcon, not a QPixmap.
  4. The context menu was replaced on every state change; now it is
     created once and mutated in-place to avoid use-after-free.
"""

import os

from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QMenu
import KStatusNotifierItem as KSNI


# Absolute path to the bundled icons directory
_ICONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")


def _load_icon(name: str) -> QIcon:
    """
    Load a named icon from the bundled hicolor SVG tree.
    Falls back to QIcon.fromTheme() so system icons keep working.
    """
    svg_path = os.path.join(
        _ICONS_DIR, "hicolor", "scalable", "apps", f"{name}.svg"
    )
    if os.path.isfile(svg_path):
        return QIcon(svg_path)
    return QIcon.fromTheme(name)


class Tray:
    """
    Owns a KStatusNotifierItem and keeps its menu/icon in sync with the
    connection state.
    """

    # Maps controller state -> (icon-name, tooltip-subtitle)
    _STATE_ICONS = {
        "stopped":    ("karburetor-symbolic", "Not connected"),
        "dead":       ("network-error-symbolic", "Connection failed"),
        "connecting": ("network-acquiring-symbolic", "Connecting…"),
        "running":    ("karburetor", "Connected"),
    }
    _DEFAULT_ICON = ("karburetor-symbolic", "Not connected")

    def __init__(self, window, controller):
        self._window = window
        self._controller = controller

        self._sni = KSNI.KStatusNotifierItem("karburetor")
        self._sni.setCategory(
            KSNI.KStatusNotifierItem.ItemCategory.ApplicationStatus
        )
        self._sni.setTitle("Karburetor")
        self._sni.setToolTipTitle("Karburetor")
        self._sni.setToolTipSubTitle("Not connected")

        # CRITICAL: default status is Passive (hidden in Plasma).
        self._sni.setStatus(KSNI.KStatusNotifierItem.ItemStatus.Active)

        # Disable the built-in Quit/About actions KSNI adds by default.
        # Without this, a second "Quit" entry appears below ours.
        self._sni.setStandardActionsEnabled(False)

        # Set the tooltip icon to the full-colour app icon
        tooltip_icon = _load_icon("karburetor")
        if not tooltip_icon.isNull():
            self._sni.setToolTipIconByPixmap(tooltip_icon)

        # Build the context menu once; _update_menu() mutates it in-place
        self._menu = QMenu()
        self._toggle_action = self._menu.addAction("Start")
        self._toggle_action.triggered.connect(self._toggle)

        self._new_id_action = self._menu.addAction("New Identity")
        self._new_id_action.triggered.connect(self._controller.newId)

        self._proxy_action = self._menu.addAction("Set Proxy")
        self._proxy_action.setCheckable(True)
        self._proxy_action.toggled.connect(self._controller.setProxy)

        self._menu.addSeparator()

        self._quit_action = self._menu.addAction("Quit")
        self._quit_action.triggered.connect(self._on_quit)

        self._sni.setContextMenu(self._menu)

        self._sni.activateRequested.connect(self._on_activate)
        controller.stateChanged.connect(self._on_state_changed)

        # Sync initial state
        self._on_state_changed(controller.state)

    def _on_activate(self, _active: bool) -> None:
        self._window.show()
        self._window.requestActivate()

    def _toggle(self) -> None:
        if self._controller.state in ("stopped", "dead"):
            self._controller.connect()
        else:
            self._controller.cancel()

    def _on_quit(self) -> None:
        from karburetor.backend import actions

        actions.kill_tor()
        self._window.close()
        from PySide6.QtWidgets import QApplication

        QApplication.quit()

    def _on_state_changed(self, state: str) -> None:
        icon_name, tooltip = self._STATE_ICONS.get(state, self._DEFAULT_ICON)

        # Update tray icon — setIconByPixmap() expects a QIcon (despite the name)
        icon = _load_icon(icon_name)
        if not icon.isNull():
            self._sni.setIconByPixmap(icon)
        else:
            self._sni.setIconByName(icon_name)

        self._sni.setToolTipSubTitle(tooltip)

        # Mutate the existing menu in-place rather than replacing it
        toggle_text = {
            "stopped":    "Start",
            "connecting": "Cancel",
            "running":    "Stop",
        }.get(state, "Start")
        self._toggle_action.setText(toggle_text)

        self._proxy_action.setChecked(self._controller.proxyEnabled)
        self._proxy_action.setEnabled(state == "running")
        self._new_id_action.setEnabled(state == "running")
