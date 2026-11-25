import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Effects
import SddmComponents 2.0 as Sddm

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "#1E1218"

    readonly property color ink: "#0E080B"
    readonly property color surface: "#2A1A22"
    readonly property color txt: "#FFECEC"
    readonly property color dim: "#C8AAB4"
    readonly property color cyan: "#7FF0F0"
    readonly property color pink: "#FF8CBE"
    readonly property color red: "#E23A44"
    property int sessionIndex: sessionModel.lastIndex
    // the login card in the system language: power buttons, greeting, password field, login button
    // 0-2 power buttons, 3 greeting, 4 password, 5 login button, 6 wrong password, 7 checking, 8 the speech bubble
    readonly property var words: ({
        "ru": ["Выключить", "Перезагрузить", "Сон", "Привет", "Пароль", "Войти →",
               "Грр! Неверный пароль", "Нюхаю пароль…", "Это твоя FurrOS. Входи — погнали!"],
        "en": ["Shut down", "Restart", "Sleep", "Hi", "Password", "Log in →",
               "Grr! Wrong password", "Sniffing the password…", "This is your FurrOS. Log in, let's go!"],
        "pl": ["Wyłącz", "Uruchom ponownie", "Uśpij", "Cześć", "Hasło", "Zaloguj →",
               "Grr! Złe hasło", "Wącham hasło…", "To twoja FurrOS. Zaloguj się i lecimy!"],
        "es": ["Apagar", "Reiniciar", "Suspender", "Hola", "Contraseña", "Entrar →",
               "¡Grr! Contraseña incorrecta", "Olfateando la contraseña…", "Esta es tu FurrOS. ¡Entra y vamos!"] })
    readonly property var labels: words[Qt.locale().name.substring(0, 2)] || words["en"]
    readonly property string fallbackAvatar: "/usr/share/furros/avatars/furros-danyok.png"

    // userModel gives each user's picture as the "icon" role: collect them to show the selected one
    Repeater {
        id: users
        model: userModel
        delegate: Item { property string icon: model.icon || ""; property string realName: model.realName || "" }
    }

    Sddm.TextConstants { id: textConstants }

    Connections {
        target: sddm
        function onLoginFailed() {
            password.text = ""
            message.text = root.labels[6]
            message.color = root.red
            shake.start()
            password.forceActiveFocus()
        }
        function onLoginSucceeded() {
            message.text = "Гав! 🐾"
        }
    }

    Image {
        anchors.fill: parent
        source: config.background
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
    }
    Rectangle { anchors.fill: parent; color: "#000000"; opacity: 0.15 }

    Canvas {  // the left page of the comic spread (FurrBoot's look): the login card sits on it
        id: page
        anchors.fill: parent
        readonly property real topX: Math.max(width * 0.47, 660)
        readonly property real botX: Math.max(width * 0.40, 600)
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            var c = getContext("2d"), w = width, h = height
            c.reset()
            c.beginPath(); c.moveTo(0, 0); c.lineTo(topX, 0); c.lineTo(botX, h); c.lineTo(0, h); c.closePath()
            c.fillStyle = "rgba(30, 18, 24, 0.92)"; c.fill()
            // halftone dots, growing towards the slanted edge
            c.fillStyle = "#3A2430"
            for (var y = 10; y < h; y += 18) {
                var edge = topX + (botX - topX) * y / h
                for (var x = edge - 300; x < edge - 14; x += 18) {
                    var r = 1 + 3.2 * (x - (edge - 300)) / 300
                    c.beginPath(); c.arc(x, y, r, 0, 2 * Math.PI); c.fill()
                }
            }
            c.lineWidth = 10; c.strokeStyle = "#0E080B"
            c.beginPath(); c.moveTo(topX, 0); c.lineTo(botX, h); c.stroke()
            c.lineWidth = 3; c.strokeStyle = "#FF8CBE"
            c.beginPath(); c.moveTo(topX + 7, 0); c.lineTo(botX + 7, h); c.stroke()
        }
    }

    Row {  // FurrOS in the corner, as in FurrBoot's header (not on short laptop screens: the clock needs the room)
        visible: parent.height >= 900
        x: parent.width * 0.04
        y: parent.height * 0.05
        spacing: 12
        Image { source: "/usr/share/furros/furros-logo.png"; height: 44; width: 44; fillMode: Image.PreserveAspectFit; smooth: false }
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "Furr<font color='#E23A44'>OS</font>"
            textFormat: Text.RichText
            color: "#FFFFFF"
            font.family: "Dela Gothic One"
            font.pixelSize: 30
        }
    }

    Image {
        id: lapa
        source: config.mascot
        height: parent.height * 0.62
        fillMode: Image.PreserveAspectFit
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: parent.width * 0.06
        smooth: true
        visible: config.showMascot === "true"
    }

    Column {
        anchors.left: parent.left
        anchors.leftMargin: parent.width * 0.09
        anchors.verticalCenter: parent.verticalCenter
        spacing: 18

        Text {
            id: clock
            color: root.txt
            font.family: "Dela Gothic One"
            font.pixelSize: 104
            style: Text.Outline
            styleColor: root.ink
            text: Qt.formatTime(new Date(), "HH:mm")
            Timer { interval: 1000; running: true; repeat: true; onTriggered: clock.text = Qt.formatTime(new Date(), "HH:mm") }
        }
        Text {
            color: root.cyan
            font.family: "Nunito"
            font.weight: Font.Bold
            font.pixelSize: 24
            text: Qt.locale().toString(new Date(), "dddd, d MMMM")
        }

        Item { width: 1; height: 6 }

        Item {
            width: bubble.width + 6
            height: bubble.height + 22
            Rectangle {  // hard shadow
                x: 5; y: 5
                width: bubble.width; height: bubble.height; radius: bubble.radius
                color: root.ink
            }
            Rectangle {
                id: bubble
                width: Math.min(bubbleText.implicitWidth + 40, 440)
                height: bubbleText.implicitHeight + 26
                radius: 20
                color: "#FFF6F2"
                border.color: root.ink
                border.width: 3
                Text {
                    id: bubbleText
                    anchors.centerIn: parent
                    width: Math.min(implicitWidth, 400)
                    wrapMode: Text.WordWrap
                    text: root.labels[8]
                    color: root.ink
                    font.family: "Nunito"
                    font.weight: Font.Black
                    font.pixelSize: 19
                }
            }
            Canvas {  // the tail, pointing down at the card
                x: 34; y: bubble.height - 3
                width: 34; height: 22
                onPaint: {
                    var c = getContext("2d")
                    c.reset()
                    c.beginPath(); c.moveTo(2, 0); c.lineTo(10, 20); c.lineTo(30, 0); c.closePath()
                    c.fillStyle = "#FFF6F2"; c.fill()
                    c.lineWidth = 3; c.strokeStyle = "#0E080B"
                    c.beginPath(); c.moveTo(2, 0); c.lineTo(10, 20); c.lineTo(30, 0); c.stroke()
                }
            }
        }

        Rectangle {
            id: card
            width: 440
            height: form.implicitHeight + 48
            radius: 22
            color: root.surface
            border.color: root.ink
            border.width: 3

            Rectangle {  // hard sticker shadow
                z: -1
                x: 6; y: 6
                width: parent.width; height: parent.height
                radius: parent.radius
                color: root.ink
            }

            SequentialAnimation {
                id: shake
                NumberAnimation { target: card; property: "x"; to: card.x + 14; duration: 50 }
                NumberAnimation { target: card; property: "x"; to: card.x - 14; duration: 80 }
                NumberAnimation { target: card; property: "x"; to: card.x; duration: 50 }
            }

            ColumnLayout {
                id: form
                anchors.fill: parent
                anchors.margins: 24
                spacing: 12

                RowLayout {
                    spacing: 16
                    Item {  // the account picture, round with a cyan ring
                        id: avatar
                        implicitWidth: 84
                        implicitHeight: 84
                        // users.count: re-evaluate once the Repeater has made its items
                        property var entry: users.count > 0 ? users.itemAt(user.currentIndex) : null
                        Image {
                            id: face
                            anchors.fill: parent
                            source: avatar.entry && avatar.entry.icon ? avatar.entry.icon : root.fallbackAvatar
                            onStatusChanged: if (status === Image.Error && source != root.fallbackAvatar) source = root.fallbackAvatar
                            sourceSize: Qt.size(168, 168)
                            fillMode: Image.PreserveAspectCrop
                            smooth: true
                            visible: false
                        }
                        Rectangle { id: faceMask; anchors.fill: parent; radius: width / 2; visible: false; layer.enabled: true }
                        MultiEffect {
                            anchors.fill: parent
                            source: face
                            maskEnabled: true
                            maskSource: faceMask
                            maskThresholdMin: 0.5
                            maskSpreadAtMin: 1.0
                        }
                        Rectangle { anchors.fill: parent; radius: width / 2; color: "transparent"; border.color: root.cyan; border.width: 3 }
                    }
                    ColumnLayout {
                        spacing: 0
                        Text {
                            text: "<b style='color:#FFFFFF'>Furr</b><b style='color:#E23A44'>OS</b>"
                            textFormat: Text.RichText
                            font.family: "Nunito"
                            font.pixelSize: 30
                        }
                        Text {
                            text: root.labels[3] + ", " + (avatar.entry && avatar.entry.realName ? avatar.entry.realName : user.currentText) + " 🐾"
                            color: root.cyan
                            font.family: "Nunito"
                            font.weight: Font.Bold
                            font.pixelSize: 16
                        }
                    }
                }

                ComboBox {
                    id: user
                    Layout.fillWidth: true
                    model: userModel
                    textRole: "name"
                    currentIndex: userModel.lastIndex
                    font.family: "Nunito"
                    font.pixelSize: 17
                    background: Rectangle { radius: 14; color: "#3A2430"; border.color: user.activeFocus ? root.pink : root.ink; border.width: 3 }
                    contentItem: Text { leftPadding: 14; text: user.displayText; color: root.txt; font: user.font; verticalAlignment: Text.AlignVCenter }
                    implicitHeight: 50
                }

                TextField {
                    id: password
                    Layout.fillWidth: true
                    implicitHeight: 50
                    echoMode: TextInput.Password
                    placeholderText: root.labels[4]
                    placeholderTextColor: root.dim
                    color: root.txt
                    font.family: "Nunito"
                    font.pixelSize: 17
                    leftPadding: 14
                    focus: true
                    background: Rectangle { radius: 14; color: "#3A2430"; border.color: password.activeFocus ? root.pink : root.ink; border.width: 3 }
                    Keys.onReturnPressed: login()
                    Keys.onEnterPressed: login()
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    ComboBox {
                        id: session
                        Layout.fillWidth: true
                        model: sessionModel
                        textRole: "name"
                        currentIndex: root.sessionIndex
                        onActivated: root.sessionIndex = currentIndex
                        font.family: "Nunito"
                        font.pixelSize: 14
                        implicitHeight: 44
                        background: Rectangle { radius: 12; color: "#3A2430"; border.color: session.activeFocus ? root.pink : root.ink; border.width: 3 }
                        contentItem: Text { leftPadding: 12; text: session.displayText; color: root.dim; font: session.font; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    }
                    Button {
                        id: go
                        implicitWidth: 130
                        implicitHeight: 44
                        onClicked: login()
                        contentItem: Text { text: root.labels[5]; font.family: "Nunito"; font.weight: Font.Black; font.pixelSize: 16; color: root.ink; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        background: Rectangle { radius: 12; color: go.down ? "#A8F7F7" : root.cyan; border.color: go.activeFocus ? root.pink : root.ink; border.width: 3 }
                    }
                }

                Text {
                    id: message
                    Layout.fillWidth: true
                    text: " "
                    color: root.dim
                    font.family: "Nunito"
                    font.pixelSize: 14
                }
            }
        }
    }

    Row {  // bottom right: on 768 px tall laptop screens the left corner is taken by the card
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 28
        spacing: 18
        Repeater {
            model: [
                { icon: "icons/power.svg", label: root.labels[0], action: function () { sddm.powerOff() }, enabled: sddm.canPowerOff },
                { icon: "icons/reboot.svg", label: root.labels[1], action: function () { sddm.reboot() }, enabled: sddm.canReboot },
                { icon: "icons/sleep.svg", label: root.labels[2], action: function () { sddm.suspend() }, enabled: sddm.canSuspend }
            ]
            delegate: Column {
                visible: modelData.enabled
                spacing: 6
                Button {
                    id: pw
                    anchors.horizontalCenter: parent.horizontalCenter
                    implicitWidth: 64
                    implicitHeight: 64
                    onClicked: modelData.action()
                    Accessible.name: modelData.label
                    contentItem: Image { source: modelData.icon; sourceSize: Qt.size(36, 36); fillMode: Image.PreserveAspectFit; horizontalAlignment: Image.AlignHCenter; verticalAlignment: Image.AlignVCenter }
                    background: Rectangle {
                        radius: 18
                        color: pw.down ? "#5A3848" : (pw.hovered ? "#4A2E3C" : root.surface)
                        border.color: pw.activeFocus || pw.hovered ? root.pink : root.ink
                        border.width: 3
                        Rectangle { z: -1; x: 4; y: 4; width: parent.width; height: parent.height; radius: parent.radius; color: root.ink }
                    }
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: modelData.label
                    color: root.txt
                    style: Text.Outline
                    styleColor: root.ink
                    font.family: "Nunito"
                    font.weight: Font.Bold
                    font.pixelSize: 14
                }
            }
        }
    }

    function login() {
        message.text = root.labels[7]
        message.color = root.dim
        sddm.login(user.currentText, password.text, root.sessionIndex)
    }

    Component.onCompleted: password.forceActiveFocus()
}
