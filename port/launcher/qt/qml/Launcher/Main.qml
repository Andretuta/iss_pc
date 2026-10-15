import QtQuick
import QtQuick.Controls.Basic
import Launcher

Rectangle {
    id: root
    color: Theme.bg
    implicitWidth: 1120
    implicitHeight: 700
    property int current: 0
    readonly property var pages: ["play", "graphics", "controls", "fixes", "saves", "guides", "support", "updates"]
    property bool animate: true

    Rail {
        id: rail
        anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom
        current: root.current
        onPick: (i) => root.current = i
    }
    Item {
        id: stage
        anchors.left: rail.right; anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom
        clip: true
        Repeater {
            model: root.pages.length
            Item {
                id: slot
                readonly property bool on: root.current === index
                width: stage.width; height: stage.height
                opacity: on ? 1 : 0
                visible: opacity > 0.01
                y: on ? 0 : 14
                Behavior on opacity { enabled: root.animate; NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
                Behavior on y { enabled: root.animate; NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
                Loader {
                    anchors.fill: parent
                    sourceComponent: index === 0 ? home : index === 3 ? fixes : index === 4 ? saves : index === 5 ? guides : soon
                    onLoaded: if (index === 1 || index === 2 || index > 5) item.key = root.pages[index]
                }
            }
        }
    }
    Component { id: home; HomePage { animate: root.animate; onOpenFixes: root.current = 3; onOpenSaves: root.current = 4 } }
    Component { id: fixes; FixesPage { } }
    Component { id: saves; SavesPage { } }
    Component { id: guides; GuidesPage { } }
    Component { id: soon; SoonPage { } }
}
