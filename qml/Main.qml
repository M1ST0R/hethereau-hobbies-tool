import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: root
    visible: true
    width: 1180
    height: 820
    minimumWidth: 940
    minimumHeight: 680
    title: "Hethereau Hobbies Tool"
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "transparent"
    background: Rectangle {
        radius: 14
        color: root.bg
        border.color: root.borderColor
        border.width: 1
    }

    property bool darkMode: backend.theme === "dark"
    property string currentPage: "owner"
    property string language: backend.language

    // Shared visual system. New module pages should reuse these tokens.
    readonly property color bg: darkMode ? "#0A0E18" : "#F2F4FA"
    readonly property color sidebarBg: darkMode ? "#0D1321" : "#FFFFFF"
    readonly property color panel: darkMode ? "#121B2C" : "#FFFFFF"
    readonly property color panelRaised: darkMode ? "#18243A" : "#F8FAFF"
    readonly property color panelAlt: darkMode ? "#1B2940" : "#EDF1F8"
    readonly property color borderColor: darkMode ? "#263650" : "#DCE3EF"
    readonly property color textColor: darkMode ? "#F1F5FF" : "#1B2740"
    readonly property color mutedColor: darkMode ? "#91A1BC" : "#6D7A92"
    readonly property color faintColor: darkMode ? "#63738F" : "#A0AABD"
    readonly property color accent: darkMode ? "#9A8BFF" : "#6556DC"
    readonly property color accentBright: darkMode ? "#B1A7FF" : "#7769ED"
    readonly property color cyan: darkMode ? "#6CD8D5" : "#219D9C"
    readonly property color green: darkMode ? "#79DDB0" : "#20865E"
    readonly property color amber: darkMode ? "#FFD27A" : "#A96B12"
    readonly property color red: darkMode ? "#FF8798" : "#BF4055"

    // This is the module registry. Add future hobbies here; each gets a page
    // in the StackLayout below without changing the common application shell.
    readonly property var moduleItems: [
        { id: "owner", ru: "Подборка владельца", en: "Owner's Selection", icon: "sports_esports", glyph: "01", ready: true },
        { id: "fishing", ru: "Рыбалка", en: "Fishing", icon: "", glyph: "≈", ready: false }
    ]

    function tr(ru, en) {
        return language === "ru" ? ru : en
    }

    function iconPath(name) {
        return "../assets/icons/qml/" + name + (darkMode ? "_dark.svg" : "_light.svg")
    }

    function pageIndex() {
        if (currentPage === "fishing")
            return 1
        if (currentPage === "settings")
            return 2
        if (currentPage === "about")
            return 3
        if (currentPage === "logs")
            return 4
        return 0
    }

    function pageTitle() {
        if (currentPage === "fishing")
            return tr("Рыбалка", "Fishing")
        if (currentPage === "settings")
            return tr("Настройки", "Settings")
        if (currentPage === "about")
            return tr("О программе", "About")
        if (currentPage === "logs")
            return tr("Журнал событий", "Activity log")
        return tr("Подборка владельца", "Owner's Selection")
    }

    function pageSubtitle() {
        if (currentPage === "fishing")
            return tr("Отдельный модуль автоматизации · скоро", "Standalone automation module · coming soon")
        if (currentPage === "settings")
            return tr("Управление, горячие клавиши и поведение приложения", "Controls, global shortcuts and application behavior")
        if (currentPage === "about")
            return tr("Информация о приложении и его возможностях", "Application information and capabilities")
        if (currentPage === "logs")
            return tr("Диагностика, события и история автоматизации", "Diagnostics, events and automation history")
        return tr("Автоматизация игрового события Neverness to Everness", "Neverness to Everness event automation")
    }

    Connections {
        target: backend

        function onLanguageChanged() {
            root.language = backend.language
        }

        function onThemeChanged() {
            root.darkMode = backend.theme === "dark"
        }

        function onLogsChanged() {
            logsCount.text = root.tr(backend.logCount + " записей", backend.logCount + " entries")
            if (root.currentPage === "logs" && logFlick.followTail) {
                Qt.callLater(function() {
                    logFlick.contentY = Math.max(0, logFlick.contentHeight - logFlick.height)
                })
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 6
        spacing: 0

        Rectangle {
            id: titleBar
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            radius: 11
            color: root.darkMode ? "#111A2B" : "#FFFFFF"
            border.color: root.borderColor
            clip: true

            MouseArea {
                anchors.fill: parent
                z: 0
                acceptedButtons: Qt.LeftButton
                onPressed: root.startSystemMove()
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 13
                anchors.rightMargin: 8
                spacing: 9
                z: 1

                Image {
                    source: "../assets/app_icon.png"
                    sourceSize: Qt.size(24, 24)
                    Layout.preferredWidth: 24
                    Layout.preferredHeight: 24
                }

                Text {
                    text: "HETHEREAU"
                    color: root.accentBright
                    font.pixelSize: 9
                    font.bold: true
                    font.letterSpacing: 1.1
                }

                Text {
                    text: "HOBBIES TOOL"
                    color: root.textColor
                    font.pixelSize: 9
                    font.bold: true
                    font.letterSpacing: 0.5
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 18
                    color: root.borderColor
                    Layout.leftMargin: 4
                    Layout.rightMargin: 4
                }

                Text {
                    text: root.pageTitle()
                    color: root.mutedColor
                    font.pixelSize: 9
                    elide: Text.ElideRight
                    Layout.maximumWidth: 260
                }

                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }

                Button {
                    id: minimizeWindowButton
                    Layout.preferredWidth: 34
                    Layout.preferredHeight: 29
                    onClicked: root.showMinimized()
                    background: Rectangle {
                        radius: 7
                        color: minimizeWindowButton.hovered ? root.panelAlt : "transparent"
                    }
                    contentItem: Text {
                        text: "—"
                        color: root.mutedColor
                        font.pixelSize: 15
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Button {
                    id: maximizeWindowButton
                    Layout.preferredWidth: 34
                    Layout.preferredHeight: 29
                    onClicked: {
                        if (root.visibility === Window.Maximized)
                            root.showNormal()
                        else
                            root.showMaximized()
                    }
                    background: Rectangle {
                        radius: 7
                        color: maximizeWindowButton.hovered ? root.panelAlt : "transparent"
                    }
                    contentItem: Text {
                        text: root.visibility === Window.Maximized ? "❐" : "□"
                        color: root.mutedColor
                        font.pixelSize: 13
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Button {
                    id: closeWindowButton
                    Layout.preferredWidth: 37
                    Layout.preferredHeight: 29
                    onClicked: root.close()
                    background: Rectangle {
                        radius: 7
                        color: closeWindowButton.hovered ? "#C94C63" : "transparent"
                    }
                    contentItem: Text {
                        text: "×"
                        color: closeWindowButton.hovered ? "#FFFFFF" : root.mutedColor
                        font.pixelSize: 20
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }

        RowLayout {
            id: workspaceLayout
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

        // -----------------------------------------------------------------
        // SIDEBAR
        // -----------------------------------------------------------------
        Rectangle {
            id: sidebar
            Layout.preferredWidth: 244
            Layout.minimumWidth: 224
            Layout.maximumWidth: 258
            Layout.fillHeight: true
            color: sidebarBg
            border.color: borderColor
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: 17
                anchors.rightMargin: 17
                anchors.topMargin: 22
                anchors.bottomMargin: 16
                spacing: 0

                RowLayout {
                    Layout.fillWidth: true
                    Layout.bottomMargin: 34
                    spacing: 12

                    Image {
                        source: "../assets/app_icon.png"
                        sourceSize: Qt.size(48, 48)
                        Layout.preferredWidth: 48
                        Layout.preferredHeight: 48
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                    }

                    ColumnLayout {
                        spacing: 2
                        Text {
                            text: "HETHEREAU"
                            color: accentBright
                            font.pixelSize: 10
                            font.bold: true
                            font.letterSpacing: 2.0
                        }
                        Text {
                            text: "HOBBIES TOOL"
                            color: textColor
                            font.pixelSize: 13
                            font.bold: true
                            font.letterSpacing: 0.8
                        }
                        Text {
                            text: "AUTOMATION HUB"
                            color: faintColor
                            font.pixelSize: 8
                            font.letterSpacing: 1.5
                        }
                    }
                }

                Text {
                    text: tr("МОДУЛИ", "HOBBY MODULES")
                    color: faintColor
                    font.pixelSize: 9
                    font.bold: true
                    font.letterSpacing: 1.6
                    Layout.leftMargin: 9
                    Layout.bottomMargin: 10
                }

                Repeater {
                    model: root.moduleItems

                    delegate: Rectangle {
                        id: moduleNav
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: 54
                        Layout.bottomMargin: 6
                        radius: 13

                        property bool selected: root.currentPage === modelData.id
                        property bool hovered: moduleMouse.containsMouse

                        color: selected
                            ? (root.darkMode ? "#282448" : "#EFEDFF")
                            : (hovered && modelData.ready ? panelAlt : "transparent")
                        border.width: selected ? 1 : 0
                        border.color: root.darkMode ? "#514A82" : "#D9D4FF"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 11
                            spacing: 11

                            Rectangle {
                                Layout.preferredWidth: 31
                                Layout.preferredHeight: 31
                                radius: 10
                                color: moduleNav.selected
                                    ? (root.darkMode ? "#514A86" : "#DCD7FF")
                                    : panelAlt

                                Image {
                                    anchors.centerIn: parent
                                    visible: moduleNav.modelData.icon !== ""
                                    source: moduleNav.modelData.icon !== ""
                                        ? root.iconPath(moduleNav.modelData.icon) : ""
                                    sourceSize: Qt.size(18, 18)
                                    width: 18
                                    height: 18
                                }

                                Text {
                                    anchors.centerIn: parent
                                    visible: moduleNav.modelData.icon === ""
                                    text: moduleNav.modelData.glyph
                                    color: cyan
                                    font.pixelSize: 21
                                    font.bold: true
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3
                                Text {
                                    text: root.tr(moduleNav.modelData.ru, moduleNav.modelData.en)
                                    color: moduleNav.selected ? accentBright : textColor
                                    font.pixelSize: 11
                                    font.bold: moduleNav.selected
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                Text {
                                    text: moduleNav.modelData.ready
                                        ? root.tr("Доступен", "Available")
                                        : root.tr("В разработке", "In development")
                                    color: moduleNav.modelData.ready ? green : faintColor
                                    font.pixelSize: 9
                                }
                            }

                            Rectangle {
                                visible: !moduleNav.modelData.ready
                                radius: 6
                                color: panelAlt
                                implicitWidth: 30
                                implicitHeight: 20
                                Text {
                                    anchors.centerIn: parent
                                    text: "SOON"
                                    color: mutedColor
                                    font.pixelSize: 7
                                    font.bold: true
                                    font.letterSpacing: 0.5
                                }
                            }

                            Rectangle {
                                visible: moduleNav.selected && moduleNav.modelData.ready
                                width: 5
                                height: 5
                                radius: 3
                                color: accentBright
                            }
                        }

                        MouseArea {
                            id: moduleMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.currentPage = moduleNav.modelData.id
                        }

                        Behavior on color { ColorAnimation { duration: 140 } }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.topMargin: 17
                    Layout.bottomMargin: 19
                    height: 1
                    color: borderColor
                }

                Text {
                    text: tr("ПРИЛОЖЕНИЕ", "WORKSPACE")
                    color: faintColor
                    font.pixelSize: 9
                    font.bold: true
                    font.letterSpacing: 1.6
                    Layout.leftMargin: 9
                    Layout.bottomMargin: 10
                }

                Repeater {
                    model: [
                        { id: "settings", ru: "Настройки", en: "Settings", icon: "", glyph: "⚙" },
                        { id: "logs", ru: "Журнал событий", en: "Activity log", icon: "article", glyph: "" },
                        { id: "about", ru: "О программе", en: "About", icon: "info", glyph: "" }
                    ]

                    delegate: Rectangle {
                        id: toolNav
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: 43
                        Layout.bottomMargin: 4
                        radius: 11
                        property bool selected: root.currentPage === modelData.id
                        property bool hovered: toolMouse.containsMouse
                        color: selected ? panelAlt : (hovered ? panelAlt : "transparent")

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 13
                            anchors.rightMargin: 12
                            spacing: 12
                            Image {
                                visible: toolNav.modelData.icon !== ""
                                source: toolNav.modelData.icon !== "" ? root.iconPath(toolNav.modelData.icon) : ""
                                sourceSize: Qt.size(18, 18)
                                Layout.preferredWidth: 18
                                Layout.preferredHeight: 18
                                opacity: toolNav.selected ? 1.0 : 0.72
                            }
                            Text {
                                visible: toolNav.modelData.icon === ""
                                text: toolNav.modelData.glyph
                                color: toolNav.selected ? accentBright : mutedColor
                                font.pixelSize: 17
                                Layout.preferredWidth: 18
                                horizontalAlignment: Text.AlignHCenter
                            }
                            Text {
                                text: root.tr(toolNav.modelData.ru, toolNav.modelData.en)
                                color: toolNav.selected ? textColor : mutedColor
                                font.pixelSize: 11
                                font.bold: toolNav.selected
                                Layout.fillWidth: true
                            }
                        }

                        MouseArea {
                            id: toolMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.currentPage = toolNav.modelData.id
                        }

                        Behavior on color { ColorAnimation { duration: 130 } }
                    }
                }

                Item { Layout.fillHeight: true }

                // Compact connection card anchors the sidebar visually.
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 77
                    radius: 14
                    color: panel
                    border.color: borderColor

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 7
                            Rectangle {
                                width: 7
                                height: 7
                                radius: 4
                                color: backend.gameConnected ? green : amber
                            }
                            Text {
                                text: backend.gameConnected
                                    ? root.tr("Игра подключена", "Game connected")
                                    : root.tr("Ожидание игры", "Waiting for game")
                                color: textColor
                                font.pixelSize: 10
                                font.bold: true
                                Layout.fillWidth: true
                            }
                        }
                        Text {
                            text: "v" + backend.version + "  ·  " + backend.channel.toUpperCase()
                            color: faintColor
                            font.pixelSize: 9
                        }
                    }
                }

            }
        }

        // -----------------------------------------------------------------
        // MAIN WORKSPACE
        // -----------------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 27
            Layout.rightMargin: 27
            Layout.topMargin: 22
            Layout.bottomMargin: 21
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                Layout.bottomMargin: 20
                spacing: 12

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    Text {
                        text: root.pageTitle()
                        color: textColor
                        font.pixelSize: 25
                        font.bold: true
                        font.letterSpacing: -0.3
                    }
                    Text {
                        text: root.pageSubtitle()
                        color: mutedColor
                        font.pixelSize: 11
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 35
                    color: borderColor
                }

                Button {
                    id: languageButton
                    Layout.preferredWidth: 48
                    Layout.preferredHeight: 38
                    text: backend.language === "ru" ? "RU" : "EN"
                    onClicked: backend.setLanguage(backend.language === "ru" ? "en" : "ru")
                    background: Rectangle {
                        radius: 11
                        color: languageButton.hovered ? panelAlt : panel
                        border.color: borderColor
                    }
                    contentItem: Text {
                        text: languageButton.text
                        color: textColor
                        font.pixelSize: 10
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Button {
                    id: themeButton
                    Layout.preferredWidth: 42
                    Layout.preferredHeight: 38
                    text: root.darkMode ? "☼" : "☾"
                    onClicked: backend.setTheme(root.darkMode ? "light" : "dark")
                    background: Rectangle {
                        radius: 11
                        color: themeButton.hovered ? panelAlt : panel
                        border.color: borderColor
                    }
                    contentItem: Text {
                        text: themeButton.text
                        color: accentBright
                        font.pixelSize: 18
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }

            StackLayout {
                id: pages
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: root.pageIndex()
                onCurrentIndexChanged: pageTransition.restart()

                SequentialAnimation {
                    id: pageTransition
                    ParallelAnimation {
                        NumberAnimation {
                            target: pages
                            property: "opacity"
                            to: 0.88
                            duration: 65
                            easing.type: Easing.OutCubic
                        }
                        NumberAnimation {
                            target: pages
                            property: "scale"
                            to: 0.994
                            duration: 65
                            easing.type: Easing.OutCubic
                        }
                    }
                    ParallelAnimation {
                        NumberAnimation {
                            target: pages
                            property: "opacity"
                            to: 1
                            duration: 145
                            easing.type: Easing.OutCubic
                        }
                        NumberAnimation {
                            target: pages
                            property: "scale"
                            to: 1
                            duration: 145
                            easing.type: Easing.OutCubic
                        }
                    }
                }

                // =========================================================
                // MODULE 01 — OWNER'S SELECTION
                // =========================================================
                Item {
                    Flickable {
                        id: ownerFlick
                        anchors.fill: parent
                        clip: true
                        contentWidth: width
                        contentHeight: ownerContent.implicitHeight + 14
                        boundsBehavior: Flickable.StopAtBounds

                        ColumnLayout {
                            id: ownerContent
                            width: ownerFlick.width
                            spacing: 14

                            // Module identity banner.
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 178
                                radius: 19
                                clip: true
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: root.darkMode ? "#29234B" : "#5548C6" }
                                    GradientStop { position: 0.55; color: root.darkMode ? "#202B4C" : "#4165B9" }
                                    GradientStop { position: 1.0; color: root.darkMode ? "#163A4A" : "#278D91" }
                                }

                                Rectangle {
                                    width: 255
                                    height: 255
                                    radius: 128
                                    x: parent.width - 225
                                    y: -118
                                    color: "#20B8C8D8"
                                    border.color: "#35FFFFFF"
                                    border.width: 1
                                }
                                Rectangle {
                                    width: 190
                                    height: 190
                                    radius: 96
                                    x: parent.width - 193
                                    y: -86
                                    color: "#10FFFFFF"
                                    border.color: "#45FFFFFF"
                                    border.width: 1
                                }
                                Rectangle {
                                    width: 128
                                    height: 128
                                    radius: 65
                                    x: parent.width - 162
                                    y: -55
                                    color: "#12FFFFFF"
                                    border.color: "#35FFFFFF"
                                    border.width: 1
                                }

                                Image {
                                    source: "../assets/app_icon.png"
                                    sourceSize: Qt.size(142, 142)
                                    width: 142
                                    height: 142
                                    x: parent.width - 169
                                    y: 29
                                    fillMode: Image.PreserveAspectFit
                                    smooth: true
                                    opacity: 0.94
                                }

                                ColumnLayout {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 23
                                    anchors.right: parent.right
                                    anchors.rightMargin: 170
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: 8

                                    Rectangle {
                                        radius: 7
                                        color: "#28FFFFFF"
                                        border.color: "#42FFFFFF"
                                        Layout.preferredWidth: moduleEyebrow.implicitWidth + 18
                                        Layout.preferredHeight: 23
                                        Text {
                                            id: moduleEyebrow
                                            anchors.centerIn: parent
                                            text: "MODULE 01   /   EVENT AUTOMATION"
                                            color: "#E7E9FF"
                                            font.pixelSize: 8
                                            font.bold: true
                                            font.letterSpacing: 1.2
                                        }
                                    }

                                    Text {
                                        text: root.tr("Подборка владельца", "Owner's Selection")
                                        color: "#FFFFFF"
                                        font.pixelSize: 24
                                        font.bold: true
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }

                                    Text {
                                        text: root.tr(
                                            "Автоматизация события, контроль ресурсов и повторение игровых циклов.",
                                            "Automate the event, monitor resources and repeat gameplay cycles."
                                        )
                                        color: "#D9E3FF"
                                        font.pixelSize: 10
                                        wrapMode: Text.WordWrap
                                        lineHeightMode: Text.ProportionalHeight
                                        lineHeight: 1.2
                                        Layout.fillWidth: true
                                    }

                                    RowLayout {
                                        Layout.topMargin: 2
                                        spacing: 7
                                        Rectangle {
                                            width: 7
                                            height: 7
                                            radius: 4
                                            color: backend.gameConnected ? "#8EF0C1" : "#FFD27A"
                                        }
                                        Text {
                                            text: backend.gameConnected
                                                ? root.tr("ИГРА ОБНАРУЖЕНА", "GAME DETECTED")
                                                : root.tr("ОЖИДАНИЕ ИГРЫ", "WAITING FOR GAME")
                                            color: "#E5F5FF"
                                            font.pixelSize: 8
                                            font.bold: true
                                            font.letterSpacing: 1.1
                                        }
                                    }
                                }
                            }

                            // Live status and main controls.
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 145
                                radius: 17
                                color: panel
                                border.color: borderColor

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 19
                                    spacing: 16

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 8

                                        Text {
                                            text: root.tr("СОСТОЯНИЕ АВТОМАТИЗАЦИИ", "AUTOMATION STATUS")
                                            color: faintColor
                                            font.pixelSize: 8
                                            font.bold: true
                                            font.letterSpacing: 1.4
                                        }

                                        RowLayout {
                                            spacing: 8
                                            Rectangle {
                                                width: 8
                                                height: 8
                                                radius: 4
                                                color: backend.paused ? amber : (backend.running ? green : faintColor)
                                            }
                                            Text {
                                                text: backend.status
                                                color: backend.paused ? amber : (backend.running ? green : textColor)
                                                font.pixelSize: 12
                                                font.bold: true
                                                Layout.fillWidth: true
                                                elide: Text.ElideRight
                                            }
                                        }

                                        Text {
                                            text: backend.stage
                                            color: mutedColor
                                            font.pixelSize: 10
                                            wrapMode: Text.WordWrap
                                            maximumLineCount: 2
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }
                                    }

                                    Rectangle {
                                        Layout.preferredWidth: 1
                                        Layout.preferredHeight: 80
                                        color: borderColor
                                    }

                                    ColumnLayout {
                                        Layout.preferredWidth: 196
                                        Layout.minimumWidth: 154
                                        spacing: 8

                                        Button {
                                            id: runButton
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 43
                                            text: backend.running && !backend.paused
                                                ? root.tr("Пауза", "Pause")
                                                : root.tr("Запустить", "Start")
                                            onClicked: backend.toggleRunPause()
                                            background: Rectangle {
                                                radius: 11
                                                gradient: Gradient {
                                                    GradientStop { position: 0.0; color: runButton.down ? accent : accentBright }
                                                    GradientStop { position: 1.0; color: runButton.down ? accentBright : (root.darkMode ? "#7464DD" : "#5142C6") }
                                                }
                                            }
                                            contentItem: Row {
                                                anchors.centerIn: parent
                                                spacing: 9
                                                Text {
                                                    text: backend.running && !backend.paused ? "Ⅱ" : "▶"
                                                    color: "#FFFFFF"
                                                    font.pixelSize: 15
                                                    font.bold: true
                                                    anchors.verticalCenter: parent.verticalCenter
                                                }
                                                Text {
                                                    text: runButton.text
                                                    color: "#FFFFFF"
                                                    font.pixelSize: 10
                                                    font.bold: true
                                                    anchors.verticalCenter: parent.verticalCenter
                                                }
                                            }
                                        }

                                        Button {
                                            id: stopButton
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 36
                                            text: root.tr("Остановить", "Stop")
                                            onClicked: backend.stop()
                                            background: Rectangle {
                                                radius: 10
                                                color: stopButton.hovered ? (root.darkMode ? "#422838" : "#FCE8EE") : panelAlt
                                                border.color: root.darkMode ? "#664052" : "#EBCBD4"
                                            }
                                            contentItem: Row {
                                                anchors.centerIn: parent
                                                spacing: 8
                                                Text {
                                                    text: "■"
                                                    color: red
                                                    font.pixelSize: 10
                                                    anchors.verticalCenter: parent.verticalCenter
                                                }
                                                Text {
                                                    text: stopButton.text
                                                    color: red
                                                    font.pixelSize: 9
                                                    font.bold: true
                                                    anchors.verticalCenter: parent.verticalCenter
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            // Resource cards.
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 12

                                Repeater {
                                    model: [
                                        { key: "cycles", ru: "ЦИКЛЫ", en: "CYCLES", subRu: "Завершено", subEn: "Completed", glyph: "↻", tone: "accent" },
                                        { key: "energy", ru: "ЭНЕРГИЯ", en: "ENERGY", subRu: "Текущий запас", subEn: "Current reserve", glyph: "ϟ", tone: "green" },
                                        { key: "income", ru: "ДОХОД", en: "INCOME", subRu: "Цель уровня", subEn: "Level target", glyph: "↗", tone: "amber" }
                                    ]

                                    delegate: Rectangle {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        Layout.preferredWidth: 1
                                        Layout.preferredHeight: 121
                                        radius: 15
                                        color: panel
                                        border.color: borderColor

                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 14
                                            spacing: 7

                                            RowLayout {
                                                Layout.fillWidth: true
                                                Text {
                                                    text: root.tr(modelData.ru, modelData.en)
                                                    color: mutedColor
                                                    font.pixelSize: 8
                                                    font.bold: true
                                                    font.letterSpacing: 1.0
                                                }
                                                Item { Layout.fillWidth: true }
                                                Text {
                                                    text: modelData.glyph
                                                    color: modelData.tone === "green" ? green : (modelData.tone === "amber" ? amber : accentBright)
                                                    font.pixelSize: 18
                                                    font.bold: true
                                                }
                                            }

                                            Text {
                                                text: modelData.key === "cycles" ? backend.cycles
                                                    : (modelData.key === "energy" ? backend.energy : backend.income)
                                                color: modelData.tone === "green" ? green
                                                    : (modelData.tone === "amber" ? amber : accentBright)
                                                font.pixelSize: 22
                                                font.bold: true
                                                elide: Text.ElideRight
                                                Layout.fillWidth: true
                                            }

                                            Text {
                                                text: root.tr(modelData.subRu, modelData.subEn)
                                                color: faintColor
                                                font.pixelSize: 9
                                            }
                                        }
                                    }
                                }
                            }

                            // Connection and diagnostics tools.
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 12

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 1
                                    Layout.preferredHeight: 93
                                    radius: 15
                                    color: panel
                                    border.color: borderColor

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 14
                                        spacing: 11

                                        Rectangle {
                                            width: 36
                                            height: 36
                                            radius: 11
                                            color: panelAlt
                                            Image {
                                                anchors.centerIn: parent
                                                source: root.iconPath("desktop_windows")
                                                sourceSize: Qt.size(19, 19)
                                                width: 19
                                                height: 19
                                            }
                                        }

                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 4
                                            Text {
                                                text: root.tr("ИГРОВОЕ ОКНО", "GAME WINDOW")
                                                color: faintColor
                                                font.pixelSize: 8
                                                font.bold: true
                                                font.letterSpacing: 1.0
                                            }
                                            Text {
                                                text: backend.windowStatus
                                                color: textColor
                                                font.pixelSize: 10
                                                font.bold: true
                                                elide: Text.ElideRight
                                                Layout.fillWidth: true
                                            }
                                            Text {
                                                text: backend.gameConnected
                                                    ? root.tr("Подключение активно", "Connection active")
                                                    : root.tr("Проверь, что игра запущена", "Make sure the game is running")
                                                color: backend.gameConnected ? green : amber
                                                font.pixelSize: 8
                                            }
                                        }

                                        Button {
                                            id: refreshButton
                                            Layout.preferredWidth: 37
                                            Layout.preferredHeight: 37
                                            onClicked: backend.refreshGameWindow()
                                            background: Rectangle {
                                                radius: 10
                                                color: refreshButton.hovered ? panelAlt : "transparent"
                                                border.color: borderColor
                                            }
                                            contentItem: Image {
                                                source: root.iconPath("refresh")
                                                sourceSize: Qt.size(17, 17)
                                                width: 17
                                                height: 17
                                            }
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 1
                                    Layout.preferredHeight: 93
                                    radius: 15
                                    color: panel
                                    border.color: borderColor

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 14
                                        spacing: 10
                                        Rectangle {
                                            width: 36
                                            height: 36
                                            radius: 11
                                            color: root.darkMode ? "#28304A" : "#EEEAFE"
                                            Text {
                                                anchors.centerIn: parent
                                                text: "⌕"
                                                color: accentBright
                                                font.pixelSize: 23
                                                font.bold: true
                                            }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 4
                                            Text {
                                                text: root.tr("ДИАГНОСТИКА", "DIAGNOSTICS")
                                                color: faintColor
                                                font.pixelSize: 8
                                                font.bold: true
                                                font.letterSpacing: 1.0
                                            }
                                            Text {
                                                text: root.tr("Проверить OCR", "Verify OCR")
                                                color: textColor
                                                font.pixelSize: 10
                                                font.bold: true
                                            }
                                            Text {
                                                text: root.tr("Энергия и доход", "Energy and income")
                                                color: mutedColor
                                                font.pixelSize: 8
                                            }
                                        }
                                        Button {
                                            id: scanButton
                                            Layout.preferredWidth: 72
                                            Layout.preferredHeight: 37
                                            text: root.tr("Скан", "Scan")
                                            onClicked: backend.scanState()
                                            background: Rectangle {
                                                radius: 10
                                                color: scanButton.hovered ? panelAlt : panelRaised
                                                border.color: borderColor
                                            }
                                            contentItem: Text {
                                                text: scanButton.text
                                                color: accentBright
                                                font.pixelSize: 9
                                                font.bold: true
                                                horizontalAlignment: Text.AlignHCenter
                                                verticalAlignment: Text.AlignVCenter
                                            }
                                        }
                                    }
                                }
                            }

                }

                // =========================================================
                    }
                }

                // MODULE 02 — FISHING PLACEHOLDER
                // =========================================================
                Item {
                    Flickable {
                        anchors.fill: parent
                        clip: true
                        contentWidth: width
                        contentHeight: fishingContent.implicitHeight + 16

                        ColumnLayout {
                            id: fishingContent
                            width: parent.width
                            spacing: 16

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 250
                                radius: 20
                                clip: true
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: root.darkMode ? "#153A47" : "#247D8B" }
                                    GradientStop { position: 0.55; color: root.darkMode ? "#1E3450" : "#3B719F" }
                                    GradientStop { position: 1.0; color: root.darkMode ? "#29244D" : "#5B54AE" }
                                }

                                Rectangle {
                                    width: 290
                                    height: 290
                                    radius: 145
                                    x: parent.width - 220
                                    y: -145
                                    color: "#10FFFFFF"
                                    border.color: "#35FFFFFF"
                                    border.width: 1
                                }
                                Rectangle {
                                    width: 205
                                    height: 205
                                    radius: 103
                                    x: parent.width - 177
                                    y: -103
                                    color: "#10FFFFFF"
                                    border.color: "#35FFFFFF"
                                    border.width: 1
                                }
                                Text {
                                    x: parent.width - 175
                                    y: 35
                                    width: 130
                                    height: 130
                                    text: "≈"
                                    color: "#8CE8E1"
                                    font.pixelSize: 126
                                    font.bold: true
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    opacity: 0.9
                                }

                                ColumnLayout {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 27
                                    anchors.right: parent.right
                                    anchors.rightMargin: 155
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: 12

                                    Text {
                                        text: "MODULE 02   /   FIELD AUTOMATION"
                                        color: "#D5F4F2"
                                        font.pixelSize: 8
                                        font.bold: true
                                        font.letterSpacing: 1.5
                                    }
                                    Text {
                                        text: root.tr("Рыбалка", "Fishing")
                                        color: "#FFFFFF"
                                        font.pixelSize: 31
                                        font.bold: true
                                    }
                                    Text {
                                        text: root.tr(
                                            "Новый модуль появится здесь. Общая оболочка, настройки и журнал уже готовы для расширения.",
                                            "The new module will live here. The shared shell, settings and activity log are ready to grow."
                                        )
                                        color: "#D8E9F7"
                                        font.pixelSize: 11
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                    Rectangle {
                                        radius: 8
                                        color: "#24FFFFFF"
                                        border.color: "#45FFFFFF"
                                        Layout.preferredWidth: fishingBadge.implicitWidth + 20
                                        Layout.preferredHeight: 27
                                        Text {
                                            id: fishingBadge
                                            anchors.centerIn: parent
                                            text: root.tr("В РАЗРАБОТКЕ", "IN DEVELOPMENT")
                                            color: "#FFFFFF"
                                            font.pixelSize: 8
                                            font.bold: true
                                            font.letterSpacing: 1.1
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 132
                                radius: 17
                                color: panel
                                border.color: borderColor

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    spacing: 15

                                    Rectangle {
                                        width: 43
                                        height: 43
                                        radius: 13
                                        color: panelAlt
                                        Text {
                                            anchors.centerIn: parent
                                            text: "✦"
                                            color: cyan
                                            font.pixelSize: 22
                                        }
                                    }

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 5
                                        Text {
                                            text: root.tr("Модульная структура", "Modular architecture")
                                            color: textColor
                                            font.pixelSize: 13
                                            font.bold: true
                                        }
                                        Text {
                                            text: root.tr(
                                                "Рыбалка будет подключена как самостоятельное хобби со своей логикой, настройками и состоянием — без переделки остальных разделов.",
                                                "Fishing will be added as an independent hobby with its own logic, settings and state — without reshaping the other sections."
                                            )
                                            color: mutedColor
                                            font.pixelSize: 10
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 104
                                radius: 15
                                color: panelAlt
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 17
                                    spacing: 12
                                    Text {
                                        text: "01"
                                        color: accentBright
                                        font.pixelSize: 22
                                        font.bold: true
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 4
                                        Text {
                                            text: root.tr("Подборка владельца", "Owner's Selection")
                                            color: textColor
                                            font.pixelSize: 11
                                            font.bold: true
                                        }
                                        Text {
                                            text: root.tr("Уже доступна и работает независимо от будущих модулей.", "Available now and independent from future modules.")
                                            color: mutedColor
                                            font.pixelSize: 9
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                    Button {
                                        id: ownerJumpButton
                                        text: root.tr("Открыть", "Open")
                                        onClicked: root.currentPage = "owner"
                                        background: Rectangle {
                                            radius: 9
                                            color: panel
                                            border.color: borderColor
                                        }
                                        contentItem: Text {
                                            text: ownerJumpButton.text
                                            color: accentBright
                                            font.pixelSize: 9
                                            font.bold: true
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // =========================================================
                // APPLICATION SETTINGS
                // =========================================================
                Item {
                    Flickable {
                        anchors.fill: parent
                        clip: true
                        contentWidth: width
                        contentHeight: settingsContent.implicitHeight + 18
                        boundsBehavior: Flickable.StopAtBounds

                        ColumnLayout {
                            id: settingsContent
                            width: parent.width
                            spacing: 15

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 112
                                radius: 17
                                color: panel
                                border.color: borderColor

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 19
                                    spacing: 14
                                    Rectangle {
                                        Layout.preferredWidth: 43
                                        Layout.preferredHeight: 43
                                        radius: 13
                                        color: root.darkMode ? "#302A50" : "#EFEDFF"
                                        Text {
                                            anchors.centerIn: parent
                                            text: "⚙"
                                            color: accentBright
                                            font.pixelSize: 24
                                        }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 5
                                        Text {
                                            text: root.tr("Управление приложением", "Application controls")
                                            color: textColor
                                            font.pixelSize: 14
                                            font.bold: true
                                        }
                                        Text {
                                            text: root.tr(
                                                "Настрой глобальные клавиши запуска и остановки. Выбранные значения сохраняются между запусками.",
                                                "Configure global start and stop keys. Your choices are saved between sessions."
                                            )
                                            color: mutedColor
                                            font.pixelSize: 10
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 16
                                color: panel
                                border.color: borderColor
                                implicitHeight: hotkeySettings.implicitHeight + 34

                                ColumnLayout {
                                    id: hotkeySettings
                                    anchors.fill: parent
                                    anchors.margins: 17
                                    spacing: 13

                                    Text {
                                        text: root.tr("ГЛОБАЛЬНЫЕ ГОРЯЧИЕ КЛАВИШИ", "GLOBAL SHORTCUTS")
                                        color: faintColor
                                        font.pixelSize: 8
                                        font.bold: true
                                        font.letterSpacing: 1.3
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 15
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 4
                                            Text {
                                                text: root.tr("Запуск / пауза", "Start / pause")
                                                color: textColor
                                                font.pixelSize: 11
                                                font.bold: true
                                            }
                                            Text {
                                                text: root.tr("Переключает выполнение автоматизации", "Toggles automation")
                                                color: mutedColor
                                                font.pixelSize: 9
                                            }
                                        }

                                        ComboBox {
                                            id: toggleHotkeyBox
                                            Layout.preferredWidth: 118
                                            model: backend.hotkeyOptions
                                            currentIndex: Math.max(0, backend.hotkeyOptions.indexOf(backend.toggleHotkey))
                                            onActivated: backend.setHotkeys(currentText, stopHotkeyBox.currentText)
                                            background: Rectangle {
                                                radius: 9
                                                color: panelAlt
                                                border.color: borderColor
                                            }
                                            contentItem: Text {
                                                leftPadding: 10
                                                text: toggleHotkeyBox.displayText
                                                color: textColor
                                                font.pixelSize: 10
                                                verticalAlignment: Text.AlignVCenter
                                            }
                                        }
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 1
                                        color: borderColor
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 15
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 4
                                            Text {
                                                text: root.tr("Остановка", "Stop")
                                                color: textColor
                                                font.pixelSize: 11
                                                font.bold: true
                                            }
                                            Text {
                                                text: root.tr("Прекращает ввод и завершает цикл", "Stops input and ends the cycle")
                                                color: mutedColor
                                                font.pixelSize: 9
                                            }
                                        }

                                        ComboBox {
                                            id: stopHotkeyBox
                                            Layout.preferredWidth: 118
                                            model: backend.hotkeyOptions
                                            currentIndex: Math.max(0, backend.hotkeyOptions.indexOf(backend.stopHotkey))
                                            onActivated: backend.setHotkeys(toggleHotkeyBox.currentText, currentText)
                                            background: Rectangle {
                                                radius: 9
                                                color: panelAlt
                                                border.color: borderColor
                                            }
                                            contentItem: Text {
                                                leftPadding: 10
                                                text: stopHotkeyBox.displayText
                                                color: textColor
                                                font.pixelSize: 10
                                                verticalAlignment: Text.AlignVCenter
                                            }
                                        }
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        Item { Layout.fillWidth: true }
                                        Button {
                                            id: resetHotkeysButton
                                            text: root.tr("По умолчанию", "Restore defaults")
                                            onClicked: backend.setHotkeys("F6", "F7")
                                            background: Rectangle {
                                                radius: 9
                                                color: resetHotkeysButton.hovered ? panelAlt : "transparent"
                                                border.color: borderColor
                                            }
                                            contentItem: Text {
                                                text: resetHotkeysButton.text
                                                color: mutedColor
                                                font.pixelSize: 9
                                                horizontalAlignment: Text.AlignHCenter
                                                verticalAlignment: Text.AlignVCenter
                                            }
                                        }
                                    }

                                    Text {
                                        text: root.tr(
                                            "Можно выбрать любую пару разных функциональных клавиш F1–F12. Изменения применяются сразу.",
                                            "Choose any two different function keys from F1–F12. Changes apply immediately."
                                        )
                                        color: faintColor
                                        font.pixelSize: 9
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 15
                                color: panelAlt
                                implicitHeight: preferencesInfo.implicitHeight + 28
                                ColumnLayout {
                                    id: preferencesInfo
                                    anchors.fill: parent
                                    anchors.margins: 15
                                    spacing: 6
                                    Text {
                                        text: root.tr("ВНЕШНИЙ ВИД", "APPEARANCE")
                                        color: faintColor
                                        font.pixelSize: 8
                                        font.bold: true
                                        font.letterSpacing: 1.2
                                    }
                                    Text {
                                        text: root.tr(
                                            "Тема и язык интерфейса переключаются в верхней панели и сохраняются автоматически.",
                                            "Change the interface theme and language from the top bar. Both are saved automatically."
                                        )
                                        color: textColor
                                        font.pixelSize: 10
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                        }
                    }
                }

                // =========================================================
                // ABOUT
                // =========================================================
                Item {
                    Rectangle {
                        anchors.fill: parent
                        radius: 18
                        color: panel
                        border.color: borderColor

                        Flickable {
                            anchors.fill: parent
                            anchors.margins: 24
                            clip: true
                            contentWidth: width
                            contentHeight: aboutColumn.implicitHeight + 12

                            ColumnLayout {
                                id: aboutColumn
                                width: parent.width
                                spacing: 17

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 20

                                    Image {
                                        source: "../assets/app_icon.png"
                                        sourceSize: Qt.size(112, 112)
                                        Layout.preferredWidth: 112
                                        Layout.preferredHeight: 112
                                        fillMode: Image.PreserveAspectFit
                                    }

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 5
                                        Text {
                                            text: "HETHEREAU HOBBIES TOOL"
                                            color: accentBright
                                            font.pixelSize: 9
                                            font.bold: true
                                            font.letterSpacing: 1.6
                                        }
                                        Text {
                                            text: "Hethereau Hobbies Tool"
                                            color: textColor
                                            font.pixelSize: 25
                                            font.bold: true
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
                                        }
                                        Text {
                                            text: "v" + backend.version + "  ·  " + backend.channel.toUpperCase()
                                            color: mutedColor
                                            font.pixelSize: 10
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 1
                                    color: borderColor
                                }

                                Text {
                                    text: root.tr(
                                        "Единое рабочее пространство для автоматизации игровых хобби в Neverness to Everness. Каждый модуль отвечает за отдельное занятие, а настройки, навигация и диагностика остаются общими.",
                                        "A unified workspace for automating hobbies in Neverness to Everness. Each module handles a separate activity while settings, navigation and diagnostics remain shared."
                                    )
                                    color: textColor
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                    lineHeightMode: Text.ProportionalHeight
                                    lineHeight: 1.3
                                    Layout.fillWidth: true
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    radius: 14
                                    color: panelAlt
                                    implicitHeight: aboutDetails.implicitHeight + 28

                                    ColumnLayout {
                                        id: aboutDetails
                                        anchors.fill: parent
                                        anchors.margins: 15
                                        spacing: 13

                                        RowLayout {
                                            Layout.fillWidth: true
                                            Text { text: root.tr("Интерфейс", "Interface"); color: mutedColor; font.pixelSize: 10 }
                                            Item { Layout.fillWidth: true }
                                            Text { text: "PySide6 + Qt Quick / QML"; color: textColor; font.pixelSize: 10; font.bold: true }
                                        }
                                        RowLayout {
                                            Layout.fillWidth: true
                                            Text { text: root.tr("Игровой процесс", "Game process"); color: mutedColor; font.pixelSize: 10 }
                                            Item { Layout.fillWidth: true }
                                            Text { text: "HTGame.exe"; color: textColor; font.pixelSize: 10; font.bold: true }
                                        }
                                        RowLayout {
                                            Layout.fillWidth: true
                                            Text { text: root.tr("Доступные модули", "Available modules"); color: mutedColor; font.pixelSize: 10 }
                                            Item { Layout.fillWidth: true }
                                            Text { text: "1 / 2"; color: textColor; font.pixelSize: 10; font.bold: true }
                                        }
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 78
                                        radius: 12
                                        color: panelRaised
                                        border.color: borderColor
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 12
                                            spacing: 4
                                            Text { text: "01"; color: accentBright; font.pixelSize: 15; font.bold: true }
                                            Text { text: root.tr("Подборка владельца", "Owner's Selection"); color: textColor; font.pixelSize: 9; font.bold: true }
                                            Text { text: root.tr("Доступен", "Available"); color: green; font.pixelSize: 8 }
                                        }
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 78
                                        radius: 12
                                        color: panelRaised
                                        border.color: borderColor
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 12
                                            spacing: 4
                                            Text { text: "02"; color: cyan; font.pixelSize: 15; font.bold: true }
                                            Text { text: root.tr("Рыбалка", "Fishing"); color: textColor; font.pixelSize: 9; font.bold: true }
                                            Text { text: root.tr("В разработке", "In development"); color: mutedColor; font.pixelSize: 8 }
                                        }
                                    }
                                }

                                Button {
                                    id: githubButton
                                    Layout.preferredWidth: 175
                                    Layout.preferredHeight: 42
                                    text: root.tr("Открыть GitHub", "Open GitHub")
                                    onClicked: backend.openUrl("https://github.com/M1ST0R/hethereau-hobbies-tool")
                                    background: Rectangle {
                                        radius: 10
                                        color: accent
                                    }
                                    contentItem: Text {
                                        text: githubButton.text
                                        color: "#FFFFFF"
                                        font.pixelSize: 10
                                        font.bold: true
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }
                    }
                }

                // =========================================================
                // ACTIVITY LOG
                // =========================================================
                Item {
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 12

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            ColumnLayout {
                                spacing: 3
                                Text {
                                    text: root.tr("Диагностика и события", "Diagnostics and events")
                                    color: textColor
                                    font.pixelSize: 15
                                    font.bold: true
                                }
                                Text {
                                    id: logsCount
                                    text: root.tr(backend.logCount + " записей", backend.logCount + " entries")
                                    color: mutedColor
                                    font.pixelSize: 9
                                }
                            }
                            Item { Layout.fillWidth: true }

                            Button {
                                id: copyLogsButton
                                text: root.tr("Копировать всё", "Copy all")
                                onClicked: backend.copyAllLogs()
                                background: Rectangle {
                                    radius: 9
                                    color: copyLogsButton.hovered ? panelAlt : panel
                                    border.color: borderColor
                                }
                                contentItem: Text {
                                    text: copyLogsButton.text
                                    color: textColor
                                    font.pixelSize: 9
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }

                            Button {
                                id: clearLogsButton
                                text: root.tr("Очистить", "Clear")
                                onClicked: backend.clearLogs()
                                background: Rectangle {
                                    radius: 9
                                    color: clearLogsButton.hovered ? (root.darkMode ? "#422838" : "#FCE8EE") : panel
                                    border.color: borderColor
                                }
                                contentItem: Text {
                                    text: clearLogsButton.text
                                    color: red
                                    font.pixelSize: 9
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            radius: 16
                            color: root.darkMode ? "#080D17" : "#FFFFFF"
                            border.color: borderColor
                            clip: true

                            RowLayout {
                                anchors.fill: parent
                                spacing: 0

                                Rectangle {
                                    Layout.fillHeight: true
                                    Layout.preferredWidth: 4
                                    color: accent
                                }

                                Flickable {
                                    id: logFlick
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    Layout.margins: 12
                                    clip: true
                                    contentWidth: width
                                    contentHeight: logsArea.height
                                    boundsBehavior: Flickable.StopAtBounds
                                    property bool followTail: true
                                    onMovementEnded: followTail = atYEnd
                                    onContentHeightChanged: {
                                        if (followTail && root.currentPage === "logs")
                                            Qt.callLater(function() {
                                                logFlick.contentY = Math.max(0, logFlick.contentHeight - logFlick.height)
                                            })
                                    }

                                    TextArea {
                                        id: logsArea
                                        width: logFlick.width
                                        height: Math.max(logFlick.height, contentHeight + topPadding + bottomPadding)
                                        text: backend.logsText
                                        readOnly: true
                                        selectByMouse: true
                                        selectByKeyboard: true
                                        wrapMode: TextEdit.Wrap
                                        color: root.darkMode ? "#DDE6F8" : "#26334B"
                                        selectedTextColor: "#FFFFFF"
                                        selectionColor: accent
                                        font.family: "Consolas"
                                        font.pixelSize: 10
                                        background: null
                                        padding: 3
                                    }

                                    ScrollBar.vertical: ScrollBar {
                                        policy: ScrollBar.AsNeeded
                                    }
                                }
                            }
                        }

                        Text {
                            text: root.tr("Выдели фрагмент журнала и нажми Ctrl+C, чтобы скопировать его.", "Select part of the log and press Ctrl+C to copy it.")
                            color: faintColor
                            font.pixelSize: 9
                        }
                    }
                }
            }
        }
    }

    }

        }
    }

    // Native edge resizing, with custom title-bar controls.
    MouseArea {
        z: 1000
        visible: root.visibility !== Window.Maximized
        width: 6
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        cursorShape: Qt.SizeHorCursor
        onPressed: root.startSystemResize(Qt.LeftEdge)
    }
    MouseArea {
        z: 1000
        visible: root.visibility !== Window.Maximized
        width: 6
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        cursorShape: Qt.SizeHorCursor
        onPressed: root.startSystemResize(Qt.RightEdge)
    }
    MouseArea {
        z: 1000
        visible: root.visibility !== Window.Maximized
        height: 6
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        cursorShape: Qt.SizeVerCursor
        onPressed: root.startSystemResize(Qt.TopEdge)
    }
    MouseArea {
        z: 1000
        visible: root.visibility !== Window.Maximized
        height: 6
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        cursorShape: Qt.SizeVerCursor
        onPressed: root.startSystemResize(Qt.BottomEdge)
    }
    MouseArea {
        z: 1001
        visible: root.visibility !== Window.Maximized
        width: 10; height: 10
        anchors.left: parent.left; anchors.top: parent.top
        cursorShape: Qt.SizeFDiagCursor
        onPressed: root.startSystemResize(Qt.LeftEdge | Qt.TopEdge)
    }
    MouseArea {
        z: 1001
        visible: root.visibility !== Window.Maximized
        width: 10; height: 10
        anchors.right: parent.right; anchors.top: parent.top
        cursorShape: Qt.SizeBDiagCursor
        onPressed: root.startSystemResize(Qt.RightEdge | Qt.TopEdge)
    }
    MouseArea {
        z: 1001
        visible: root.visibility !== Window.Maximized
        width: 10; height: 10
        anchors.left: parent.left; anchors.bottom: parent.bottom
        cursorShape: Qt.SizeBDiagCursor
        onPressed: root.startSystemResize(Qt.LeftEdge | Qt.BottomEdge)
    }
    MouseArea {
        z: 1001
        visible: root.visibility !== Window.Maximized
        width: 10; height: 10
        anchors.right: parent.right; anchors.bottom: parent.bottom
        cursorShape: Qt.SizeFDiagCursor
        onPressed: root.startSystemResize(Qt.RightEdge | Qt.BottomEdge)
    }

    Component.onCompleted: {
        Qt.callLater(function() {
            logFlick.contentY = Math.max(0, logFlick.contentHeight - logFlick.height)
        })
    }
}
