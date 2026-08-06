import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard 1.0 as FormCard
import org.kde.ki18n

Kirigami.ApplicationWindow {
    id: root

    width: 480
    height: 720
    minimumWidth: 320
    minimumHeight: 440

    title: "Karburetor"

    pageStack.initialPage: MainPage {}

    globalDrawer: Kirigami.GlobalDrawer {
        id: drawer
        objectName: "drawer"
        title: i18n("Karburetor")
        titleIcon: "karburetor"

        actions: [
            Kirigami.Action {
                text: i18n("Set Proxy")
                icon.name: "preferences-system-network-proxy"
                checkable: true
                checked: controller.proxyEnabled
                enabled: controller.state === "running"
                onTriggered: controller.setProxy(!controller.proxyEnabled)
            },
            Kirigami.Action {
                separator: true
            },
            Kirigami.Action {
                text: i18n("Preferences")
                icon.name: "settings-configure"
                onTriggered: {
                    pageStack.push(Qt.resolvedUrl("PreferencesPage.qml"), {
                        addBridgeSheet: addBridgeSheet,
                        addHiddenServiceSheet: addHiddenServiceSheet
                    })
                    drawer.close()
                }
            },
            Kirigami.Action {
                text: i18n("Logs")
                icon.name: "utilities-terminal"
                onTriggered: {
                    logsSheet.open()
                    drawer.close()
                }
            },
            Kirigami.Action {
                text: i18n("About Karburetor")
                icon.name: "help-about"
                onTriggered: {
                    pageStack.push(Qt.resolvedUrl("AboutPage.qml"))
                    drawer.close()
                }
            },
            Kirigami.Action {
                separator: true
            },
            Kirigami.Action {
                text: i18n("Quit")
                icon.name: "application-exit"
                onTriggered: Qt.quit()
            }
        ]
    }

    Connections {
        target: controller
        function onToast(message) {
            root.showPassiveNotification(message)
        }
    }

    LogsSheet {
        id: logsSheet
        objectName: "logsSheet"
    }
    AddBridgeSheet {
        id: addBridgeSheet
        objectName: "addBridgeSheet"
    }
    AddHiddenServiceSheet {
        id: addHiddenServiceSheet
        objectName: "addHiddenServiceSheet"
    }

    // First-run introduction
    Kirigami.Dialog {
        id: firstRunSheet
        objectName: "firstRunSheet"

        title: i18n("Welcome to Karburetor")
        standardButtons: Kirigami.Dialog.NoButton
        closePolicy: Controls.Popup.NoAutoClose

        padding: Kirigami.Units.largeSpacing * 2

        ColumnLayout {
            spacing: Kirigami.Units.largeSpacing
            implicitWidth: Kirigami.Units.gridUnit * 20

            Kirigami.Icon {
                Layout.alignment: Qt.AlignHCenter
                source: "karburetor"
                implicitWidth: Kirigami.Units.iconSizes.huge
                implicitHeight: Kirigami.Units.iconSizes.huge
            }

            Controls.Label {
                Layout.fillWidth: true
                text: i18n(
                    "Karburetor lets you browse privately by routing your " +
                    "traffic through the Tor network. When you are connected, " +
                    "set the system proxy or use the local ports directly."
                )
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }
        }

        customFooterActions: [
            Kirigami.Action {
                text: i18n("Get Started")
                icon.name: "go-next"
                onTriggered: {
                    settings.firstRun = false
                    firstRunSheet.close()
                }
            }
        ]

        Component.onCompleted: {
            if (settings.firstRun) {
                firstRunSheet.open()
            }
        }
    }
}
