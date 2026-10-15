import QtQuick
import Launcher

Rectangle {
    id: root
    property string text: ""
    property bool compact: false
    signal clicked()
    implicitHeight: compact ? 36 : 44
    implicitWidth: label.implicitWidth + 36
    radius: 10
    color: mouse.containsMouse ? Theme.ghostHover : Theme.ghost
    border.width: 1
    border.color: mouse.containsMouse ? Theme.ghostLineHover : Theme.ghostLine
    Text { id: label; anchors.centerIn: parent; text: root.text; color: Theme.text
           font.family: Theme.fontText; font.pixelSize: 14; font.weight: Font.DemiBold
           elide: Text.ElideRight; width: Math.min(implicitWidth, parent.width - 16); horizontalAlignment: Text.AlignHCenter }
    MouseArea { id: mouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                onClicked: root.clicked() }
    Accessible.role: Accessible.Button
    Accessible.name: text
}
