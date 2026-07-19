import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Page {
    id: page
    signal back()
    signal trainingStarted()
    property string rootPath: backend.trainingDefaults.rootPath

    FolderDialog {
        id: rootFolderDialog
        title: "Select Root Dataset Folder"
        onAccepted: page.rootPath = decodeURIComponent(
            selectedFolder.toString().replace(/^file:\/\//, ""))
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 12

        ToolButton { text: "←"; onClicked: page.back() }
        Label { text: "Train New Model"; font.pixelSize: 28; font.bold: true }

        GridLayout {
            Layout.maximumWidth: 680
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter
            columns: 3
            columnSpacing: 12
            rowSpacing: 9

            Label {
                text: "Model:"
                Layout.preferredWidth: 130
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignRight
            }
            ComboBox {
                id: modelCombo
                Layout.columnSpan: 2
                Layout.fillWidth: true
                model: backend.availableModels
                textRole: "display"
                Component.onCompleted: {
                    const savedIndex = find(backend.trainingDefaults.model)
                    if (savedIndex >= 0)
                        currentIndex = savedIndex
                }
            }
            Label { text: "Dataset Name:"; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true }
            TextField {
                id: datasetName
                Layout.columnSpan: 2
                Layout.fillWidth: true
                text: backend.trainingDefaults.dataset
            }
            Label { text: "Root Folder:"; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true }
            TextField { Layout.fillWidth: true; readOnly: true; text: page.rootPath }
            Button { text: "Browse"; onClicked: rootFolderDialog.open() }
            Label { text: "Normal Folder:"; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true }
            TextField {
                id: normalField
                Layout.columnSpan: 2
                Layout.fillWidth: true
                text: backend.trainingDefaults.normalFolder
            }
            Label { text: "Abnormal Folder:"; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true }
            TextField {
                id: abnormalField
                Layout.columnSpan: 2
                Layout.fillWidth: true
                text: backend.trainingDefaults.abnormalFolder
            }
        }

        GridLayout {
            Layout.maximumWidth: 680
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter
            columns: 4
            columnSpacing: 12
            rowSpacing: 4

            Label { text: "Train Batch"; Layout.fillWidth: true }
            Label { text: "Evaluation Batch"; Layout.fillWidth: true }
            Label { text: "Workers"; Layout.fillWidth: true }
            Label { text: "Seed"; Layout.fillWidth: true }
            SpinBox {
                id: trainBatchSize
                Layout.fillWidth: true
                from: 1; to: 1024
                value: backend.trainingDefaults.trainBatchSize
            }
            SpinBox {
                id: evalBatchSize
                Layout.fillWidth: true
                from: 1; to: 1024
                value: backend.trainingDefaults.evalBatchSize
            }
            SpinBox {
                id: workerThreads
                Layout.fillWidth: true
                from: 1; to: 64
                value: backend.trainingDefaults.workers
            }
            SpinBox {
                id: seedBox
                Layout.fillWidth: true
                from: 0; to: 999999
                value: backend.trainingDefaults.seed
            }
        }

        Item { Layout.fillHeight: true }
        Button {
            text: "Train"
            Layout.preferredWidth: 180
            Layout.preferredHeight: 56
            Layout.alignment: Qt.AlignRight
            enabled: modelCombo.currentIndex >= 0 && datasetName.text.trim().length > 0
                     && page.rootPath.length > 0 && normalField.text.trim().length > 0
                     && abnormalField.text.trim().length > 0
            onClicked: {
                backend.startTraining(modelCombo.currentText, datasetName.text.trim(), page.rootPath,
                    normalField.text.trim(), abnormalField.text.trim(), trainBatchSize.value,
                    evalBatchSize.value, workerThreads.value, seedBox.value)
                page.trainingStarted()
            }
        }
    }
}
