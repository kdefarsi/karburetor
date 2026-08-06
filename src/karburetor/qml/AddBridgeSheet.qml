import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard 1.0 as FormCard
import org.kde.ki18n

Kirigami.Dialog {
    id: sheet

    title: i18n("Add New Bridge")

    standardButtons: Kirigami.Dialog.NoButton

    property bool valid: false

    function checkEntry() {
        errorLabel.text = ""
        const line = bridgeField.text.trim()
        if (line.length === 0) {
            valid = false
            return
        }
        if (settings.isBridgeDuplicate(line)) {
            errorLabel.text = i18n("Duplicate bridge")
            valid = false
            return
        }
        valid = true
    }

    function apply() {
        const err = settings.addBridge(bridgeField.text.trim())
        if (err) {
            errorLabel.text = i18n(err)
            return
        }
        bridgeField.text = ""
        sheet.close()
    }

    padding: Kirigami.Units.largeSpacing

    ColumnLayout {
        implicitWidth: Math.min(Kirigami.Units.gridUnit * 30, parent?.width ?? Kirigami.Units.gridUnit * 30)
        spacing: Kirigami.Units.largeSpacing

        Controls.Label {
            Layout.fillWidth: true
            text: i18n(
                "Use bridges provided by a trusted organisation or someone " +
                "you know. A bridge line looks like an address followed by " +
                "a fingerprint and certificate."
            )
            wrapMode: Text.WordWrap
            color: Kirigami.Theme.disabledTextColor
        }

        FormCard.FormCard {
            Layout.fillWidth: true

            FormCard.FormTextFieldDelegate {
                id: bridgeField
                label: i18n("Paste your bridge address here")
                onTextChanged: sheet.checkEntry()
                onAccepted: if (sheet.valid) sheet.apply()
            }
        }

        Controls.Label {
            id: errorLabel
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Kirigami.Theme.negativeTextColor
            visible: text.length > 0
        }
    }

    customFooterActions: [
        Kirigami.Action {
            text: i18n("Add")
            icon.name: "list-add"
            enabled: sheet.valid
            onTriggered: sheet.apply()
        }
    ]
}
