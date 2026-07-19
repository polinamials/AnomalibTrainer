import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    signal back()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 32
        spacing: 16

        ToolButton { text: "←"; onClicked: back() }
        Label { text: backend.selectedModelName; font.pixelSize: 28; font.bold: true }
        GridLayout {
            columns: 2
            columnSpacing: 28
            rowSpacing: 10
            Label { text: "Status"; font.bold: true }
            Label { text: backend.selectedModelStatus === "trained" ? "Trained" : backend.selectedModelStatus }
            Label { text: "Dataset"; font.bold: true }
            Label { text: backend.selectedModelDataset }
            Label { text: "Version"; font.bold: true }
            Label { text: backend.selectedModelVersion }
            Label { text: "Created"; font.bold: true }
            Label { text: backend.selectedModelCreated }
            Label { text: "Location"; font.bold: true }
            Label { text: backend.selectedModelPath; wrapMode: Text.WrapAnywhere; Layout.fillWidth: true }
        }
        Label { text: "Configuration"; font.bold: true; font.pixelSize: 18 }
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            TextArea {
                text: backend.selectedModelConfig
                readOnly: true
                selectByMouse: true
                wrapMode: TextEdit.NoWrap
                font.family: "monospace"
            }
        }
    }
}
