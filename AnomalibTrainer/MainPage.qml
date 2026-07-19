import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

Page {
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
            spacing: 8
            clip: true
            model: backend.trainedModels

            Label {
                anchors.centerIn: parent
                visible: parent.count === 0
                text: "No trained models yet"
                opacity: 0.65
            }

            delegate: ItemDelegate {
                required property string name
                required property string status
                width: ListView.view.width
                height: 64
                enabled: status !== "training"
                onClicked: showModel(name)

                contentItem: RowLayout {
                    Label { text: name; font.pixelSize: 18; Layout.fillWidth: true; elide: Text.ElideRight }
                    BusyIndicator {
                        visible: running
                        running: status === "training"
                        implicitWidth: 36
                        implicitHeight: 36
                    }
                    Label {
                        visible: status !== "training"
                        text: status === "trained" ? "Trained" : "Failed"
                        color: status === "trained" ? Material.color(Material.Green) : Material.color(Material.Red)
                    }
                }
            }
        }

        Button {
            text: "Train New"
            Layout.preferredWidth: 180
            Layout.preferredHeight: 56
            Layout.alignment: Qt.AlignRight
            onClicked: trainNew()
        }
    }
}
