import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.ki18n

Kirigami.OverlaySheet {
    id: sheet

    title: i18n("Logs")
    property int lineCount: 0

    function onLogLine(line) {
        lineCount++
        textArea.append(line)
        textArea.cursorPosition = textArea.length
    }

    function clearLogs() {
        lineCount = 0
        textArea.clear()
    }

    function copyLogs() {
        textArea.selectAll()
        textArea.copy()
        textArea.deselect()
    }

    ColumnLayout {
        Layout.preferredWidth: 560
        Layout.preferredHeight: 420
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.bottomMargin: Kirigami.Units.smallSpacing
            spacing: Kirigami.Units.smallSpacing

            Controls.Label {
                Layout.fillWidth: true
                text: i18np("%1 line", "%1 lines", sheet.lineCount)
                color: Kirigami.Theme.disabledTextColor
            }
            Controls.ToolButton {
                icon.name: "edit-clear-all"
                text: i18n("Clear")
                onClicked: sheet.clearLogs()
            }
            Controls.ToolButton {
                icon.name: "edit-copy"
                text: i18n("Copy")
                onClicked: sheet.copyLogs()
            }
        }

        Controls.TextArea {
            id: textArea
            Layout.fillWidth: true
            Layout.fillHeight: true
            readOnly: true
            selectByMouse: true
            wrapMode: TextEdit.Wrap
            font.family: "monospace"
            background: Rectangle {
                color: Kirigami.Theme.backgroundColor
            }
        }
    }

    Component.onCompleted: {
        controller.logLine.connect(sheet.onLogLine)
    }
}
