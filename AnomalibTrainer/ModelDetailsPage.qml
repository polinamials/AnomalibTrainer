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
            Label {
                text: backend.selectedModelStatus.length > 0
                      ? backend.selectedModelStatus.charAt(0).toUpperCase()
                        + backend.selectedModelStatus.slice(1) : ""
            }
            Label { text: "Dataset"; font.bold: true }
            Label {
                text: backend.selectedModelDataset
                      + (backend.selectedModelDataRoot.length > 0
                         ? " (" + backend.selectedModelDataRoot + ")" : "")
                elide: Text.ElideMiddle
                Layout.maximumWidth: 600
            }
            Label { text: "Version"; font.bold: true }
            Label { text: backend.selectedModelVersion }
            Label { text: "Created"; font.bold: true }
            Label { text: backend.selectedModelCreated }
            Label { text: "Location"; font.bold: true }
            Label { text: backend.selectedModelPath; wrapMode: Text.WrapAnywhere; Layout.fillWidth: true }
        }
        Item { Layout.fillHeight: true }
    }
}
