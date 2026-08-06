import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard 1.0 as FormCard
import org.kde.ki18n

FormCard.FormCardPage {
    id: page
    objectName: "preferencesPage"

    title: i18n("Preferences")

    property var addBridgeSheet: null
    property var addHiddenServiceSheet: null

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
        FormCard.FormDelegateSeparator { visible: manualCode.visible }
        FormCard.FormTextFieldDelegate {
            id: manualCode
            visible: false
            label: i18n("Country Code")
            description: i18n('ISO-3166 alpha-2 code, e.g. "us"')
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
            id: acceptConnectionDelegate
            text: i18n("Accept Incoming Connections")
            description: i18n("Allow external devices to use this network")
            checked: settings.acceptConnection
            onToggled: settings.acceptConnection = checked
        }
        FormCard.FormDelegateSeparator { below: acceptConnectionDelegate; above: fascistFirewallDelegate }
        FormCard.FormSwitchDelegate {
            id: fascistFirewallDelegate
            text: i18n("Fascist Firewall Mode")
            description: i18n("Restrict connections to ports 80 and 443")
            checked: settings.fascistFirewall
            onToggled: settings.fascistFirewall = checked
        }
        FormCard.FormDelegateSeparator { below: fascistFirewallDelegate; above: autoSetDelegate }
        FormCard.FormSwitchDelegate {
            id: autoSetDelegate
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
            id: socksPortDelegate
            label: i18n("SOCKS")
            description: i18n("Main connection point for secure communication")
            from: 1
            to: 65535
            stepSize: 1
            value: settings.socksPort
            onValueModified: settings.socksPort = value
        }
        FormCard.FormDelegateSeparator { below: socksPortDelegate; above: dnsPortDelegate }
        FormCard.FormSpinBoxDelegate {
            id: dnsPortDelegate
            label: i18n("DNS")
            description: i18n("A local DNS server for enhanced privacy")
            from: 1
            to: 65535
            stepSize: 1
            value: settings.dnsPort
            onValueModified: settings.dnsPort = value
        }
        FormCard.FormDelegateSeparator { below: dnsPortDelegate; above: httpPortDelegate }
        FormCard.FormSpinBoxDelegate {
            id: httpPortDelegate
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
            id: hiddenServicesSwitch
            text: i18n("Enable Hidden Services")
            description: i18n("Create an onion address when Karburetor connects")
            checked: settings.hiddenServices
            onToggled: settings.hiddenServices = checked
        }
        FormCard.FormDelegateSeparator {}
        Repeater {
            model: settings.hiddenServicesModel
            delegate: FormCard.AbstractFormDelegate {
                required property var modelData
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
            contentItem: RowLayout {
                spacing: Kirigami.Units.smallSpacing

                Controls.Label {
                    Layout.fillWidth: true
                    text: i18n("No hidden services yet")
                    color: Kirigami.Theme.disabledTextColor
                }
            }
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormButtonDelegate {
            text: i18n("Add Hidden Service")
            icon.name: "list-add"
            onClicked: {
                if (page.addHiddenServiceSheet) {
                    page.addHiddenServiceSheet.open()
                }
            }
        }
    }

    FormCard.FormHeader {
        title: i18n("Pluggable Transports")
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
        FormCard.FormDelegateSeparator {}
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
                required property var modelData
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
        FormCard.FormDelegateSeparator {}
        FormCard.FormButtonDelegate {
            text: i18n("Add Bridge")
            icon.name: "list-add"
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
            id: bridgeDbDelegate
            text: i18n("BridgeDB Website")
            description: i18n("Visit the BridgeDB website")
            icon.name: "internet-services"
            onClicked: Qt.openUrlExternally("https://bridges.torproject.org/options")
        }
        FormCard.FormDelegateSeparator { below: bridgeDbDelegate; above: emailDelegate }
        FormCard.FormButtonDelegate {
            id: emailDelegate
            text: i18n("Email")
            description: i18n("Exclusively from Gmail or Riseup")
            icon.name: "mail-message"
            onClicked: Qt.openUrlExternally("mailto:bridges@torproject.org?body=get%20bridges")
        }
        FormCard.FormDelegateSeparator { below: emailDelegate; above: telegramDelegate }
        FormCard.FormButtonDelegate {
            id: telegramDelegate
            text: i18n("Telegram")
            description: i18n("Message GetBridgesBot")
            icon.name: "dialog-messages"
            onClicked: Qt.openUrlExternally("tg://resolve?domain=GetBridgesBot")
        }
        FormCard.FormDelegateSeparator { below: telegramDelegate; above: openFileDelegate }
        FormCard.FormButtonDelegate {
            id: openFileDelegate
            text: i18n("Open Bridges File Externally")
            description: i18n("View as a text file to edit and share bridges")
            icon.name: "document-open"
            onClicked: Qt.openUrlExternally("file://" + settings.bridgesFilePath())
        }
    }
}
