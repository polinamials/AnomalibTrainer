import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

Page {
    id: page
    signal showModel(string name)
    signal trainNew()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 32
        spacing: 20
        Label { text: "Trained Models"; font.pixelSize: 30; font.bold: true }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10
            clip: true
            model: backend.trainedModels

            Label {
                anchors.centerIn: parent
                visible: parent.count === 0
                text: "No trained models yet"
                opacity: 0.65
            }

            delegate: ItemDelegate {
                id: modelEntry
                required property string name
                required property string status
                width: ListView.view.width
                height: 72
                onClicked: if (status !== "training") page.showModel(name)

                HoverHandler { cursorShape: Qt.PointingHandCursor }
                background: Rectangle {
                    radius: 8
                    color: modelEntry.hovered
                           ? Material.color(Material.BlueGrey, Material.Shade700)
                           : Material.color(Material.BlueGrey, Material.Shade800)
                    border.width: 1
                    border.color: Material.color(Material.BlueGrey, Material.Shade500)
                    opacity: Material.theme === Material.Dark ? 0.8 : 0.16
                }
                contentItem: RowLayout {
                    spacing: 12
                    Label {
                        text: modelEntry.name
                        font.pixelSize: 18
                        font.bold: true
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }
                    BusyIndicator {
                        running: modelEntry.status === "training" || modelEntry.status === "exporting"
                        visible: running
                        implicitWidth: 36
                        implicitHeight: 36
                    }
                    Label {
                        visible: modelEntry.status !== "training" && modelEntry.status !== "exporting"
                        text: modelEntry.status === "exported" ? "Exported"
                              : modelEntry.status === "trained" ? "Trained" : "Failed"
                        color: modelEntry.status === "failed"
                               ? Material.color(Material.Red) : Material.color(Material.Green)
                    }
                    Button {
                        visible: modelEntry.status === "training"
                        text: "×"
                        font.pixelSize: 22
                        ToolTip.visible: hovered
                        ToolTip.text: "Cancel training"
                        onClicked: backend.cancelTraining(modelEntry.name)
                    }
                    Button {
                        text: modelEntry.status === "exporting" ? "Exporting…" : "Export To ONNX"
                        enabled: modelEntry.status === "trained"
                        onClicked: backend.exportModel(modelEntry.name)
                    }
                }
            }
        }

        Button {
            text: "Train New"
            Layout.preferredWidth: 180
            Layout.preferredHeight: 56
            Layout.alignment: Qt.AlignRight
            onClicked: page.trainNew()
        }
    }
}
