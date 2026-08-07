import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.ki18n

Kirigami.Page {
    id: page

    // On desktop the app name already lives in the sidebar header, so don't
    // repeat it in the toolbar; the hamburger-menu layout needs it though.
    title: applicationWindow() && applicationWindow().wideMode
        ? ""
        : i18n("Karburetor")

    // Suppress the default page padding so we can center the content ourselves
    topPadding: 0
    bottomPadding: 0
    leftPadding: 0
    rightPadding: 0

    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(parent.width - Kirigami.Units.largeSpacing * 4, 360)
        spacing: Kirigami.Units.largeSpacing

        Item {
            id: iconHolder
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 128
            Layout.preferredHeight: 128

            Kirigami.Icon {
                anchors.fill: parent
                source: controller.state === "running" ? "karburetor"
                      : controller.state === "dead" ? "network-offline"
                      : "karburetor-symbolic"
                selected: false
            }

            Controls.BusyIndicator {
                anchors.centerIn: parent
                width: 120
                height: 120
                running: controller.state === "connecting"
                visible: running
            }
        }

        Kirigami.Heading {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: controller.title
            level: 2
            color: controller.state === "running"
                ? Kirigami.Theme.positiveTextColor
                : controller.state === "dead"
                    ? Kirigami.Theme.negativeTextColor
                    : Kirigami.Theme.textColor
        }

        Controls.Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: controller.description
            wrapMode: Text.WordWrap
            color: Kirigami.Theme.disabledTextColor
        }

        Controls.ProgressBar {
            Layout.fillWidth: true
            visible: controller.state === "connecting"
            from: 0
            to: 100
            value: controller.progress
        }

        Controls.Button {
            Layout.fillWidth: true
            Layout.preferredHeight: Kirigami.Units.gridUnit * 3
            Layout.topMargin: Kirigami.Units.largeSpacing
            highlighted: true
            text: controller.state === "running" ? i18n("Stop")
                : controller.state === "connecting" ? i18n("Cancel")
                : i18n("Start")
            onClicked: {
                if (controller.state === "stopped" || controller.state === "dead") {
                    controller.connect()
                } else {
                    controller.cancel()
                }
            }
        }

        Controls.Button {
            Layout.fillWidth: true
            text: i18n("New Identity")
            visible: controller.state === "running"
            icon.name: "contact-new"
            onClicked: controller.newId()
        }

        Controls.Button {
            Layout.fillWidth: true
            text: i18n("Check Connection")
            visible: controller.state === "running"
            icon.name: "network-connect"
            onClicked: controller.checkConnection()
        }

        ColumnLayout {
            visible: controller.state === "running"
            Layout.fillWidth: true
            Layout.topMargin: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing

            Controls.Label {
                Layout.alignment: Qt.AlignHCenter
                text: i18n("Local Ports")
                color: Kirigami.Theme.disabledTextColor
            }

            Controls.Label {
                Layout.alignment: Qt.AlignHCenter
                text: i18n("SOCKS: %1", "127.0.0.1:" + controller.ports.socks)
            }
            Controls.Label {
                Layout.alignment: Qt.AlignHCenter
                text: i18n("DNS: %1", "127.0.0.1:" + controller.ports.dns)
            }
            Controls.Label {
                Layout.alignment: Qt.AlignHCenter
                text: i18n("HTTP: %1", "127.0.0.1:" + controller.ports.http)
            }
        }
    }
}
