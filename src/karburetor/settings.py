# © 2026 KDE Farsi Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
QObject bridge between the KConfig-style INI store (``~/.config/karburetorrc``
via the ``karburetor.backend`` modules) and the QML UI.

Every property reads/writes the same files the CLI backend uses, so the two
always agree and the files remain editable with ``kwriteconfig6`` and a text
editor.
"""

import os

from PySide6.QtCore import QObject, Property, Signal, Slot

from karburetor.backend import bridges as tbridges
from karburetor.backend import config as tconfig
from karburetor.backend import control, db, transport
from karburetor.backend.store import config_file_path, read_store, write_store
from karburetor.config import NODES, TRANSPORT_TITLES, transport_title


class Settings(QObject):
    """
    Exposes the karburetor settings to QML as typed properties.
    """

    exitNodeChanged = Signal()
    bridgeTypeChanged = Signal()
    acceptConnectionChanged = Signal()
    fascistFirewallChanged = Signal()
    hiddenServicesChanged = Signal()
    autoSetChanged = Signal()
    firstRunChanged = Signal()
    socksPortChanged = Signal()
    dnsPortChanged = Signal()
    httpPortChanged = Signal()
    pluginChanged = Signal()
    bridgesChanged = Signal()
    pluginEnabledChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def _emit(self, signal: Signal) -> None:
        signal.emit()

    @Property(str, notify=exitNodeChanged)
    def exitNode(self) -> str:
        return db.get_val("exit-node")

    @exitNode.setter
    def exitNode(self, value: str) -> None:
        db.set_val("exit-node", value.strip().lower())
        self.exitNodeChanged.emit()

    @Property(str, notify=bridgeTypeChanged)
    def bridgeType(self) -> str:
        return db.get_val("bridge-type")

    @bridgeType.setter
    def bridgeType(self, value: str) -> None:
        db.set_val("bridge-type", value)
        self.bridgeTypeChanged.emit()
        self.pluginChanged.emit()
        self.pluginEnabledChanged.emit()

    @Property(bool, notify=acceptConnectionChanged)
    def acceptConnection(self) -> bool:
        return db.get_val("accept-connection")

    @acceptConnection.setter
    def acceptConnection(self, value: bool) -> None:
        db.set_val("accept-connection", value)
        self.acceptConnectionChanged.emit()

    @Property(bool, notify=fascistFirewallChanged)
    def fascistFirewall(self) -> bool:
        return db.get_val("fascist-firewall")

    @fascistFirewall.setter
    def fascistFirewall(self, value: bool) -> None:
        db.set_val("fascist-firewall", value)
        self.fascistFirewallChanged.emit()

    @Property(bool, notify=hiddenServicesChanged)
    def hiddenServices(self) -> bool:
        return db.get_val("hidden-services")

    @hiddenServices.setter
    def hiddenServices(self, value: bool) -> None:
        db.set_val("hidden-services", value)
        self.hiddenServicesChanged.emit()

    @Property(bool, notify=autoSetChanged)
    def autoSet(self) -> bool:
        return db.get_val("auto-set")

    @autoSet.setter
    def autoSet(self, value: bool) -> None:
        db.set_val("auto-set", value)
        self.autoSetChanged.emit()

    @Property(int, notify=socksPortChanged)
    def socksPort(self) -> int:
        return db.get_val("socks-port")

    @socksPort.setter
    def socksPort(self, value: int) -> None:
        db.set_val("socks-port", value)
        self.socksPortChanged.emit()

    @Property(int, notify=dnsPortChanged)
    def dnsPort(self) -> int:
        return db.get_val("dns-port")

    @dnsPort.setter
    def dnsPort(self, value: int) -> None:
        db.set_val("dns-port", value)
        self.dnsPortChanged.emit()

    @Property(int, notify=httpPortChanged)
    def httpPort(self) -> int:
        return db.get_val("http-port")

    @httpPort.setter
    def httpPort(self, value: int) -> None:
        db.set_val("http-port", value)
        self.httpPortChanged.emit()

    @Property(bool, notify=pluginEnabledChanged)
    def pluginEnabled(self) -> bool:
        return self.bridgeType not in ("none", "vanilla")

    @Property(str, notify=pluginChanged)
    def plugin(self) -> str:
        if not self.pluginEnabled:
            return ""
        path = tconfig.get_executable(self.bridgeType)
        if not path:
            return ""
        return os.path.basename(path)

    @Slot(result=str)
    def pickExecutable(self) -> str:
        """
        Show a native file picker for the transport executable.
        """
        from PySide6.QtWidgets import QFileDialog

        transport_name = self.bridgeType
        start = tconfig.get_executable(transport_name) or os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(
            None, "Select transport executable", start
        )
        if path:
            tconfig.set_executable(transport_name, path)
            self.pluginChanged.emit()
            return path
        return ""

    @Property("QVariantList", constant=True)
    def countryModel(self):
        """
        Country choices for the exit-node combo: Auto plus the curated list.
        """
        model = [{"value": "ww", "label": "Auto (Best)"}]
        for country, label in NODES.items():
            model.append({"value": country.alpha_2, "label": label})
        return model

    @Property("QVariantList", constant=True)
    def bridgeTypeModel(self):
        """
        Transport choices: none plus all registered pluggable transports.
        """
        types = ["none", *transport.registry.get_all()]
        return [
            {
                "value": type_id,
                "label": TRANSPORT_TITLES.get(
                    type_id, type_id.replace("_", " ").title()
                ),
            }
            for type_id in types
        ]

    @Property("QVariantList", notify=bridgesChanged)
    def bridgesModel(self):
        """
        All configured bridges across transports, as QML model rows.
        """
        rows = []
        for transport_name in transport.registry.get_all():
            for line in tconfig.get_bridges(transport_name):
                rows.append(self._bridge_row(line))
        return rows

    def _bridge_row(self, line: str) -> dict:
        parsed = tbridges.parse_bridge_line(line)
        title = transport_title(parsed.get("transport", ""))
        subtitle = " ".join(tbridges.create_emoji(line))
        if parsed.get("addr"):
            subtitle = f"{subtitle}\t{parsed['addr']}"
        connected = ""
        if self._tor_running:
            try:
                if control.get_bridge() == "".join(tbridges.create_emoji(line)):
                    connected = "Connected"
            except Exception:
                pass
        return {
            "line": line,
            "title": title,
            "subtitle": subtitle,
            "connected": connected,
        }

    @property
    def _tor_running(self) -> bool:
        from karburetor.backend import checks

        return checks.running()

    @Slot(result=str)
    def bridgesFilePath(self) -> str:
        """
        Return the path of the bridges configuration file.
        """
        return tconfig.get_config_file_path()

    @Slot(str, result=bool)
    def isBridgeDuplicate(self, line: str) -> bool:
        """
        Return True when a bridge line is already configured.
        """
        parsed = tbridges.parse_bridge_line(line)
        if not parsed.get("transport"):
            return False
        return line in tconfig.get_bridges(parsed["transport"])

    @Slot(result="QVariantList")
    def refreshBridges(self):
        """
        Re-read bridges and return the model (used to repopulate views).
        """
        self.bridgesChanged.emit()
        return self.bridgesModel

    @Slot(str, result=str)
    def addBridge(self, line: str) -> str:
        """
        Validate and store a bridge line.  Returns an error message or "".
        """
        parsed = tbridges.parse_bridge_line(line)
        if not parsed.get("transport"):
            return "Invalid bridge line"
        current = tconfig.get_bridges(parsed["transport"])
        if line in current:
            return "Duplicate bridge"
        tconfig.add_bridge(parsed["transport"], line)
        self.bridgesChanged.emit()
        return ""

    @Slot(str)
    def removeBridge(self, line: str) -> None:
        """
        Remove a bridge line from the configuration.
        """
        parsed = tbridges.parse_bridge_line(line)
        bridge_key = "".join(tbridges.create_emoji(line))
        transport_name = parsed.get("transport")
        if transport_name:
            tconfig.remove_bridge(transport_name, bridge_key)
        self.bridgesChanged.emit()

    @Property("QVariantList", notify=hiddenServicesChanged)
    def hiddenServicesModel(self):
        """
        Hidden-service port mappings as QML model rows.
        """
        return [
            {"name": name, "subtitle": line}
            for name, line in tconfig.get_hidden_ports().items()
        ]

    @Slot(str, int, str, int, result=str)
    def addHiddenService(
        self, name: str, port: int, host: str, target: int
    ) -> str:
        """
        Validate and store a hidden-service mapping.  Returns an error
        message or "".
        """
        try:
            tconfig.add_hidden_port(name, port, host, target)
        except ValueError as error:
            return str(error)
        self.hiddenServicesChanged.emit()
        return ""

    @Slot(str)
    def removeHiddenService(self, name: str) -> None:
        """
        Remove a hidden-service port mapping.
        """
        tconfig.remove_hidden_port(name)
        self.hiddenServicesChanged.emit()

    @Property(bool, notify=firstRunChanged)
    def firstRun(self) -> bool:
        """
        Whether the user has not yet completed the first-run introduction.
        """
        parser = read_store()
        section = parser["General"] if parser.has_section("General") else {}
        return section.get("FirstRun", "true").lower() != "false"

    @firstRun.setter
    def firstRun(self, value: bool) -> None:
        parser = read_store()
        if not parser.has_section("General"):
            parser.add_section("General")
        parser.set("General", "FirstRun", "true" if value else "false")
        write_store(parser)
        self.firstRunChanged.emit()
