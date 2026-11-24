import QtQuick 2.15

Rectangle {
    id: root
    color: "#1E1218"
    property int stage

    onStageChanged: if (stage === 6) fadeOut.start()

    Column {
        anchors.centerIn: parent
        spacing: 18
        Image {
            source: "images/logo.png"
            width: 220; height: 220
            fillMode: Image.PreserveAspectFit
            smooth: false
            anchors.horizontalCenter: parent.horizontalCenter
        }
        Image {
            source: "images/wordmark.png"
            anchors.horizontalCenter: parent.horizontalCenter
        }
        Row {
            spacing: 14
            anchors.horizontalCenter: parent.horizontalCenter
            Repeater {
                model: 6
                Image {
                    id: paw
                    source: index % 2 ? "images/paw1.png" : "images/paw0.png"
                    opacity: index < root.stage ? 1 : 0.25
                    Behavior on opacity { NumberAnimation { duration: 250 } }
                    SequentialAnimation on y {
                        loops: Animation.Infinite
                        PauseAnimation { duration: index * 140 }
                        NumberAnimation { from: 0; to: -12; duration: 220; easing.type: Easing.OutQuad }
                        NumberAnimation { from: -12; to: 0; duration: 220; easing.type: Easing.InQuad }
                        PauseAnimation { duration: (5 - index) * 140 + 300 }
                    }
                }
            }
        }
    }

    OpacityAnimator { id: fadeOut; target: root; from: 1; to: 0; duration: 600 }
}
