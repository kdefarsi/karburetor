import QtQuick
import org.kde.kirigami as Kirigami

Kirigami.AboutPage {
    objectName: "aboutPage"
    aboutData: {
        "displayName": "Karburetor",
        "productName": "karburetor",
        "componentName": "karburetor",
        "shortDescription": "A KDE Tor client",
        "homepage": "https://github.com/kdefarsi/karburetor",
        "bugAddress": "https://github.com/kdefarsi/karburetor/issues",
        "version": Qt.application.version,
        "otherText": "",
        "authors": [
            {
                "name": "Sohrab Behdani",
                "task": "",
                "emailAddress": "behdanisohrab@gmail.com",
                "webAddress": "",
                "ocsUsername": ""
            }
        ],
        "credits": [
            {
                "name": "Danial Behzadi",
                "task": "Original Carburetor/Tractor author",
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
        "desktopFileName": "org.kde.karburetor"
    }
}
