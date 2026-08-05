# © 2026 KDE Farsi Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
PySide6 + Kirigami entry point for the Karburetor GUI.
"""

import os
import sys

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from karburetor.backend import actions
from karburetor.controller import Controller
from karburetor.settings import Settings
from karburetor.tray import Tray


def _version() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version

        return version("karburetor")
    except PackageNotFoundError:
        return "0.1.0"


def _init_ki18n(engine) -> bool:
    """
    Make the KDE i18n()/i18nc()/i18np()/i18ndc() globals available to QML.

    The ``org.kde.ki18n`` QML module ships as an ``optional`` plugin whose
    ``initializeEngine`` is not always invoked under PySide6, which leaves the
    i18n functions undefined and every translated string blank.  Wire the
    ``KLocalizedContext`` onto the engine's root context directly instead.
    """
    import ctypes

    try:
        from shiboken6 import Shiboken
    except ImportError:
        return False

    for library_name in ("libKF6I18nQml.so.6", "libKF6I18nQml.so"):
        try:
            library = ctypes.CDLL(library_name)
        except OSError:
            continue
        symbol = "_ZN13KLocalization8Internal22createLocalizedContextEP10QQmlEngine"
        try:
            create_context = getattr(library, symbol)
        except AttributeError:
            return False
        create_context.argtypes = [ctypes.c_void_p]
        create_context.restype = ctypes.c_void_p
        create_context(Shiboken.getCppPointer(engine)[0])
        context = engine.rootContext().contextObject()
        if context is not None:
            context.setProperty("translationDomain", "karburetor")
            return True
        return False
    return False


def main() -> int:
    """
    Run the Karburetor GUI.
    """
    QCoreApplication.setOrganizationName("karburetor")
    QCoreApplication.setApplicationName("karburetor")
    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Karburetor")
    app.setApplicationVersion(_version())
    # Keep running in the system tray after the window closes
    app.setQuitOnLastWindowClosed(False)

    engine = QQmlApplicationEngine()
    for import_path in ("/usr/lib/qt6/qml", "/usr/lib64/qt6/qml"):
        if os.path.isdir(import_path):
            engine.addImportPath(import_path)

    _init_ki18n(engine)

    settings = Settings()
    controller = Controller()
    engine.rootContext().setContextProperty("settings", settings)
    engine.rootContext().setContextProperty("controller", controller)

    qml_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qml")
    engine.load(QUrl.fromLocalFile(os.path.join(qml_dir, "main.qml")))
    if not engine.rootObjects():
        return 1

    window = engine.rootObjects()[0]
    try:
        tray = Tray(window, controller)
        window.tray = tray  # keep the tray alive
    except Exception:
        # No session bus / status notifier host available (e.g. a test env)
        pass

    app.aboutToQuit.connect(actions.kill_tor)
    return app.exec()
