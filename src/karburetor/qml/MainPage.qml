import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.ki18n

Kirigami.Page {
    id: page

    title: "Karburetor"

    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(parent.width - Kirigami.Units.largeSpacing * 4, 360)
        spacing: Kirigami.Units.largeSpacing

        Item {
            id: iconHolder
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 140
            Layout.preferredHeight: 140

            Kirigami.Icon {
                anchors.fill: parent
                source: controller.state === "running" ? "security-high-symbolic"
                      : controller.state === "dead" ? "network-offline"
                      : "security-low-symbolic"
                selected: false
            }

            Controls.BusyIndicator {
                anchors.centerIn: parent
                width: 132
                height: 132
                running: controller.state === "connecting"
                visible: running
            }
        }

        Controls.Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: controller.title
            font.pixelSize: 30
            font.weight: Font.Bold
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
            Layout.preferredHeight: 48
            Layout.topMargin: Kirigami.Units.largeSpacing
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
            onClicked: controller.newId()
        }

        Controls.Button {
            Layout.fillWidth: true
            text: i18n("Check Connection")
            visible: controller.state === "running"
            onClicked: controller.checkConnection()
        }
    }
}
