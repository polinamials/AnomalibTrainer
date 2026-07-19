import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material

ApplicationWindow {
    width: 900
    height: 680
    minimumWidth: 780
    minimumHeight: 640
    visible: true
    title: "Anomalib Trainer"
    Material.theme: Material.System

    StackView {
        id: stack
        anchors.fill: parent
        initialItem: MainPage {
            onShowModel: function(name) {
                backend.loadModel(name)
                stack.push(detailsPage)
            }
            onTrainNew: stack.push(trainingPage)
        }
    }

    Component {
        id: detailsPage
        ModelDetailsPage { onBack: stack.pop() }
    }

    Component {
        id: trainingPage
        TrainingPage {
            onBack: stack.pop()
            onTrainingStarted: stack.pop()
        }
    }
}
