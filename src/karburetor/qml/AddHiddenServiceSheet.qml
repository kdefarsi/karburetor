import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard 1.0 as FormCard
import org.kde.ki18n

Kirigami.OverlaySheet {
    id: sheet

    title: i18n("Add Hidden Service")

    property bool valid: false

    function checkEntry() {
        errorLabel.text = ""
        valid = nameField.text.trim().length > 0 && hostField.text.trim().length > 0
    }

    function apply() {
        const err = settings.addHiddenService(
            nameField.text.trim(),
            portSpin.value,
            hostField.text.trim(),
            targetSpin.value
        )
        if (err) {
            errorLabel.text = i18n(err)
            return
        }
        nameField.text = ""
        sheet.close()
    }

    ColumnLayout {
        Layout.preferredWidth: 480
        spacing: Kirigami.Units.largeSpacing

        FormCard.FormCard {
            Layout.fillWidth: true

            FormCard.FormTextFieldDelegate {
                id: nameField
                label: i18n("Name")
                onTextChanged: sheet.checkEntry()
            }
            FormCard.FormSpinBoxDelegate {
                id: portSpin
                label: i18n("Onion Port")
                description: i18n("Port on the onion address")
                from: 1
                to: 65535
                value: 80
            }
            FormCard.FormTextFieldDelegate {
                id: hostField
                label: i18n("Target Host")
                text: "127.0.0.1"
                onTextChanged: sheet.checkEntry()
            }
            FormCard.FormSpinBoxDelegate {
                id: targetSpin
                label: i18n("Target Port")
                description: i18n("Local port to forward to")
                from: 1
                to: 65535
                value: 8080
            }
        }

        Controls.Label {
            id: errorLabel
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Kirigami.Theme.negativeTextColor
            visible: text.length > 0
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing

            Item {
                Layout.fillWidth: true
            }
            Controls.Button {
                text: i18n("Cancel")
                onClicked: sheet.close()
            }
            Controls.Button {
                text: i18n("Add")
                enabled: sheet.valid
                highlighted: true
                onClicked: sheet.apply()
            }
        }
    }
}
