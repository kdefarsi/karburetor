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
"""

from PySide6.QtWidgets import QMenu
import KStatusNotifierItem as KSNI


class Tray:
    """
    Owns a KStatusNotifierItem and keeps its menu/icon in sync with the
    connection state.
    """

    def __init__(self, window, controller):
        self._window = window
        self._controller = controller
        self._menu = None
        self._sni = KSNI.KStatusNotifierItem("karburetor")
        self._sni.setCategory(KSNI.KStatusNotifierItem.ItemCategory.ApplicationStatus)
        self._sni.setTitle("Karburetor")
        self._sni.setToolTipTitle("Karburetor")
        self._sni.setToolTipSubTitle("Not connected")
        self._sni.activateRequested.connect(self._on_activate)
        controller.stateChanged.connect(self._on_state_changed)
        self._rebuild_menu()
        self._on_state_changed(controller.state)

    def _on_activate(self, _active: bool) -> None:
        self._window.show()
        self._window.requestActivate()

    def _rebuild_menu(self) -> None:
        menu = QMenu()
        state = self._controller.state

        toggle_text = {
            "stopped": "Start",
            "connecting": "Cancel",
            "running": "Stop",
        }.get(state, "Start")
        toggle = menu.addAction(toggle_text)
        toggle.triggered.connect(self._toggle)

        menu.addAction("New Identity", self._controller.newId)

        check = menu.addAction("Set Proxy")
        check.setCheckable(True)
        check.setChecked(self._controller.proxyEnabled)
        check.toggled.connect(self._controller.setProxy)
        check.setEnabled(state == "running")

        menu.addSeparator()
        menu.addAction("Quit", self._on_quit)

        self._sni.setContextMenu(menu)
        self._menu = menu

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
        icon, tooltip = {
            "stopped": ("network-vpn-symbolic", "Not connected"),
            "dead": ("network-error-symbolic", "Connection failed"),
            "connecting": ("network-acquiring-symbolic", "Connecting…"),
            "running": ("network-vpn", "Connected"),
        }.get(state, ("network-vpn-symbolic", "Not connected"))
        self._sni.setIconByName(icon)
        self._sni.setToolTipIconByName(icon)
        self._sni.setToolTipSubTitle(tooltip)
        self._rebuild_menu()
