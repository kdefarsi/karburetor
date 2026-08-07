import QtQuick
import org.kde.kirigamiaddons.formcard as FormCard
import org.kde.ki18n

FormCard.AboutPage {
    objectName: "aboutPage"

    aboutData: {
        "displayName": "Karburetor",
        "productName": "karburetor",
        "componentName": "karburetor",
        "shortDescription": i18n("A KDE Tor client"),
        "homepage": "https://github.com/kdefarsi/karburetor",
        "bugAddress": "https://github.com/kdefarsi/karburetor/issues",
        "version": Qt.application.version,
        "otherText": "",
        "authors": [
            {
                "name": "Sohrab Behdani",
                "task": i18n("Maintainer"),
                "emailAddress": "behdanisohrab@gmail.com",
                "webAddress": "",
                "ocsUsername": ""
            }
        ],
        "credits": [
            {
                "name": "Danial Behzadi",
                "task": i18n("Original Carburetor/Tractor author"),
                "emailAddress": "dani.behzi@ubuntu.com",
                "webAddress": "https://gitlab.com/dbehzi/carburetor",
                "ocsUsername": ""
            }
        ],
        "translators": [],
        "licenses": [
            {
                "name": "GPL v3",
                "text": "Karburetor is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.",
                "spdx": "GPL-3.0-or-later"
            }
        ],
        "copyrightStatement": "© 2026 KDE Farsi Community",
        "desktopFileName": "io.frama.tractor.karburetor"
    }
}
