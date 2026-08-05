import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard 1.0 as FormCard
import org.kde.ki18n

Kirigami.ScrollablePage {
    id: page
    objectName: "preferencesPage"

    title: i18n("Preferences")

    property var addBridgeSheet: null
    property var addHiddenServiceSheet: null

    leftPadding: 0
    rightPadding: 0
    topPadding: Kirigami.Units.smallSpacing
    bottomPadding: Kirigami.Units.largeSpacing

    function comboModel() {
        return settings.countryModel.concat([{
            "value": "manual",
            "label": i18n("Other (Manual)")
        }])
    }

    FormCard.FormHeader {
        title: i18n("General")
    }
    FormCard.FormCard {
        FormCard.FormComboBoxDelegate {
            id: exitCombo
            text: i18n("Exit Country")
            description: i18n("The country you want to connect from")
            model: page.comboModel()
            textRole: "label"
            valueRole: "value"

            onActivated: (index) => {
                const value = exitCombo.currentValue
                if (value === "manual") {
                    manualCode.visible = true
                } else {
                    manualCode.visible = false
                    settings.exitNode = value
                }
            }

            Component.onCompleted: {
                for (let i = 0; i < exitCombo.count; i++) {
                    if (exitCombo.model[i].value === settings.exitNode) {
                        exitCombo.currentIndex = i
                        return
                    }
                }
                if (settings.exitNode !== "ww") {
                    exitCombo.currentIndex = exitCombo.count - 1
                    manualCode.visible = true
                    manualCode.text = settings.exitNode
                }
            }
        }
        FormCard.FormTextFieldDelegate {
            id: manualCode
            visible: false
            label: i18n("Country Code")
            description: i18n("ISO-3166 alpha-2 code, e.g. “us”")
            onAccepted: {
                if (text.trim().length > 0) {
                    settings.exitNode = text.trim()
                }
            }
        }
    }

    FormCard.FormHeader {
        title: i18n("Connections")
    }
    FormCard.FormCard {
        FormCard.FormSwitchDelegate {
            text: i18n("Accept Incoming Connections")
            description: i18n("Allow external devices to use this network")
            checked: settings.acceptConnection
            onToggled: settings.acceptConnection = checked
        }
        FormCard.FormSwitchDelegate {
            text: i18n("Fascist Firewall Mode")
            description: i18n("Restrict connections to ports 80 and 443")
            checked: settings.fascistFirewall
            onToggled: settings.fascistFirewall = checked
        }
        FormCard.FormSwitchDelegate {
            text: i18n("Set Proxy Automatically")
            description: i18n(
                "Configure the KDE system proxy after a successful connection"
            )
            checked: settings.autoSet
            onToggled: settings.autoSet = checked
        }
    }

    FormCard.FormHeader {
        title: i18n("Ports")
    }
    FormCard.FormCard {
        FormCard.FormSpinBoxDelegate {
            label: i18n("SOCKS")
            description: i18n("Main connection point for secure communication")
            from: 1
            to: 65535
            stepSize: 1
            value: settings.socksPort
            onValueModified: settings.socksPort = value
        }
        FormCard.FormSpinBoxDelegate {
            label: i18n("DNS")
            description: i18n("A local DNS server for enhanced privacy")
            from: 1
            to: 65535
            stepSize: 1
            value: settings.dnsPort
            onValueModified: settings.dnsPort = value
        }
        FormCard.FormSpinBoxDelegate {
            label: i18n("HTTP")
            description: i18n("A fallback HTTP tunnel for simple connections")
            from: 1
            to: 65535
            stepSize: 1
            value: settings.httpPort
            onValueModified: settings.httpPort = value
        }
    }

    FormCard.FormHeader {
        title: i18n("Hidden Services")
    }
    FormCard.FormCard {
        FormCard.FormSwitchDelegate {
            text: i18n("Enable Hidden Services")
            description: i18n("Create an onion address when Karburetor connects")
            checked: settings.hiddenServices
            onToggled: settings.hiddenServices = checked
        }
        Repeater {
            model: settings.hiddenServicesModel
            delegate: FormCard.AbstractFormDelegate {
                contentItem: RowLayout {
                    spacing: Kirigami.Units.smallSpacing

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0

                        Controls.Label {
                            text: modelData.name
                            color: Kirigami.Theme.textColor
                        }
                        Controls.Label {
                            text: modelData.subtitle
                            color: Kirigami.Theme.disabledTextColor
                            elide: Text.ElideMiddle
                        }
                    }
                    Controls.ToolButton {
                        icon.name: "edit-delete"
                        onClicked: settings.removeHiddenService(modelData.name)
                    }
                }
            }
        }
        FormCard.AbstractFormDelegate {
            visible: settings.hiddenServicesModel.length === 0
            onClicked: {
                if (page.addHiddenServiceSheet) {
                    page.addHiddenServiceSheet.open()
                }
            }
            contentItem: RowLayout {
                spacing: Kirigami.Units.smallSpacing

                Controls.Label {
                    Layout.fillWidth: true
                    text: i18n("No hidden services yet")
                    color: Kirigami.Theme.disabledTextColor
                }
            }
        }
        FormCard.FormButtonDelegate {
            text: i18n("Add Hidden Service")
            onClicked: {
                if (page.addHiddenServiceSheet) {
                    page.addHiddenServiceSheet.open()
                }
            }
        }
    }

    FormCard.FormHeader {
        title: i18n("Bridges")
    }
    FormCard.FormCard {
        FormCard.FormComboBoxDelegate {
            id: bridgeTypeCombo
            text: i18n("Type of Transport")
            description: i18n("Pluggable transport used to reach the network")
            model: settings.bridgeTypeModel
            textRole: "label"
            valueRole: "value"

            Component.onCompleted: {
                for (let i = 0; i < bridgeTypeCombo.count; i++) {
                    if (bridgeTypeCombo.model[i].value === settings.bridgeType) {
                        bridgeTypeCombo.currentIndex = i
                        return
                    }
                }
            }
            onActivated: (index) => {
                settings.bridgeType = bridgeTypeCombo.currentValue
            }
        }
        FormCard.FormButtonDelegate {
            text: i18n("Transport Executable File")
            description: settings.pluginEnabled
                ? (settings.plugin || i18n("None"))
                : i18n("Not required for this transport")
            enabled: settings.pluginEnabled
            onClicked: settings.pickExecutable()
        }
    }

    FormCard.FormHeader {
        title: i18n("Bridges")
    }
    FormCard.FormCard {
        Repeater {
            model: settings.bridgesModel
            delegate: FormCard.AbstractFormDelegate {
                contentItem: RowLayout {
                    spacing: Kirigami.Units.smallSpacing

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0

                        Controls.Label {
                            text: modelData.connected.length > 0
                                ? modelData.title + "  ✔ " + modelData.connected
                                : modelData.title
                            color: Kirigami.Theme.textColor
                        }
                        Controls.Label {
                            text: modelData.subtitle
                            color: Kirigami.Theme.disabledTextColor
                            elide: Text.ElideMiddle
                        }
                    }
                    Controls.ToolButton {
                        icon.name: "edit-delete"
                        onClicked: settings.removeBridge(modelData.line)
                    }
                }
            }
        }
        FormCard.AbstractFormDelegate {
            visible: settings.bridgesModel.length === 0
            contentItem: RowLayout {
                spacing: Kirigami.Units.smallSpacing

                Controls.Label {
                    Layout.fillWidth: true
                    text: i18n("No bridges configured")
                    color: Kirigami.Theme.disabledTextColor
                }
            }
        }
        FormCard.FormButtonDelegate {
            text: i18n("Add Bridge")
            onClicked: {
                if (page.addBridgeSheet) {
                    page.addBridgeSheet.open()
                }
            }
        }
    }

    FormCard.FormHeader {
        title: i18n("Find More Bridges")
    }
    FormCard.FormCard {
        FormCard.FormButtonDelegate {
            text: i18n("BridgeDB Website")
            description: i18n("Visit the BridgeDB website")
            onClicked: Qt.openUrlExternally("https://bridges.torproject.org/options")
        }
        FormCard.FormButtonDelegate {
            text: i18n("Email")
            description: i18n("Exclusively from Gmail or Riseup")
            onClicked: Qt.openUrlExternally("mailto:bridges@torproject.org?body=get%20bridges")
        }
        FormCard.FormButtonDelegate {
            text: i18n("Telegram")
            description: i18n("Message GetBridgesBot")
            onClicked: Qt.openUrlExternally("tg://resolve?domain=GetBridgesBot")
        }
        FormCard.FormButtonDelegate {
            text: i18n("Open Bridges File Externally")
            description: i18n("View as a text file to edit and share bridges")
            onClicked: Qt.openUrlExternally("file://" + settings.bridgesFilePath())
        }
    }
}
