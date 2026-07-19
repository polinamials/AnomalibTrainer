import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Page {
    id: page
    signal back()
    signal trainingStarted()
    property string rootPath: ""

    FolderDialog {
        id: rootFolderDialog
        title: "Select Root Dataset Folder"
        onAccepted: page.rootPath = decodeURIComponent(
            selectedFolder.toString().replace(/^file:\/\//, ""))
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 32
        spacing: 18
        ToolButton { text: "←"; onClicked: back() }
        Label { text: "Train New Model"; font.pixelSize: 28; font.bold: true }

        GridLayout {
            Layout.fillWidth: true
            columns: 3
            columnSpacing: 16
            rowSpacing: 12
            Label { text: "Model:"; Layout.preferredWidth: 180; horizontalAlignment: Text.AlignRight }
            ComboBox { id: modelCombo; Layout.columnSpan: 2; Layout.fillWidth: true; model: backend.availableModels; textRole: "display" }
            Label { text: "Dataset Name:"; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true }
            TextField { id: datasetName; Layout.columnSpan: 2; Layout.fillWidth: true }
            Label { text: "Root Folder:"; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true }
            TextField { Layout.fillWidth: true; readOnly: true; text: rootPath }
            Button { text: "Browse"; onClicked: rootFolderDialog.open() }
            Label { text: "Normal Folder:"; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true }
            TextField { id: normalField; Layout.columnSpan: 2; Layout.fillWidth: true }
            Label { text: "Abnormal Folder:"; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true }
            TextField { id: abnormalField; Layout.columnSpan: 2; Layout.fillWidth: true }
            Label { text: "Train Batch Size:"; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true }
            SpinBox { id: trainBatchSize; Layout.columnSpan: 2; Layout.fillWidth: true; from: 1; to: 1024; value: 1 }
            Label { text: "Evaluation Batch Size:"; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true }
            SpinBox { id: evalBatchSize; Layout.columnSpan: 2; Layout.fillWidth: true; from: 1; to: 1024; value: 1 }
            Label { text: "Worker Threads:"; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true }
            SpinBox { id: workerThreads; Layout.columnSpan: 2; Layout.fillWidth: true; from: 1; to: 64; value: 16 }
            Label { text: "Seed:"; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true }
            SpinBox { id: seedBox; Layout.columnSpan: 2; Layout.fillWidth: true; from: 0; to: 999999; value: 42 }
        }

        Item { Layout.fillHeight: true }
        Button {
            text: "Train"
            Layout.preferredWidth: 180
            Layout.preferredHeight: 56
            Layout.alignment: Qt.AlignRight
            enabled: modelCombo.currentIndex >= 0 && datasetName.text.trim().length > 0
                     && rootPath.length > 0 && normalField.text.trim().length > 0
                     && abnormalField.text.trim().length > 0
            onClicked: {
                backend.startTraining(modelCombo.currentText, datasetName.text.trim(), rootPath,
                    normalField.text.trim(), abnormalField.text.trim(), trainBatchSize.value,
                    evalBatchSize.value, workerThreads.value, seedBox.value)
                trainingStarted()
            }
        }
    }
}
