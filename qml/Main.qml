import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: root
    visible: true
    width: 1120
    height: 780
    minimumWidth: 900
    minimumHeight: 650
    title: "Hethereau Hobbies Tool"
    color: bg

    property bool darkMode: backend.theme === "dark"
    property string currentPage: "owner"
    property string language: backend.language

    readonly property color bg: darkMode ? "#0B0F19" : "#F3F5FA"
    readonly property color panel: darkMode ? "#131A29" : "#FFFFFF"
    readonly property color panelAlt: darkMode ? "#1A2436" : "#E9EDF5"
    readonly property color borderColor: darkMode ? "#28344A" : "#D8DFEA"
    readonly property color textColor: darkMode ? "#F2F5FC" : "#1B263B"
    readonly property color mutedColor: darkMode ? "#94A2BA" : "#66748D"
    readonly property color accent: darkMode ? "#809BFF" : "#4668DA"
    readonly property color accentHover: darkMode ? "#91A9FF" : "#3858C5"
    readonly property color green: darkMode ? "#64D6A5" : "#16865D"
    readonly property color amber: darkMode ? "#FFD27A" : "#A86B08"
    readonly property color red: darkMode ? "#FF8798" : "#BF4055"

    function tr(ru, en) {
        return language === "ru" ? ru : en
    }

    function iconPath(name) {
        return "../assets/icons/qml/" + name + (darkMode ? "_dark.svg" : "_light.svg")
    }

    function pageTitle() {
        if (currentPage === "about")
            return tr("О программе", "About")
        if (currentPage === "logs")
            return tr("Логи", "Logs")
        return tr("Владелец", "Owner")
    }

    function pageSubtitle() {
        if (currentPage === "about")
            return "Hethereau Hobbies Tool"
        if (currentPage === "logs")
            return tr("История работы и диагностика", "Activity history and diagnostics")
        return tr("Автоматизация события «Подборка владельца»", "Owner's Selection automation")
    }

    onDarkModeChanged: {
        // Icon URLs are theme-specific SVGs; changing the theme refreshes them.
    }

    Connections {
        target: backend
        function onLanguageChanged() {
            root.language = backend.language
        }
        function onThemeChanged() {
            root.darkMode = backend.theme === "dark"
        }
        function onLogAdded(line) {
            if (root.currentPage !== "logs")
                return
            var atBottom = logFlick.contentY + logFlick.height >= logFlick.contentHeight - 12
            logsArea.append(line)
            Qt.callLater(function() {
                if (atBottom)
                    logFlick.contentY = Math.max(0, logFlick.contentHeight - logFlick.height)
            })
        }
        function onLogsReset() {
            logsArea.text = backend.logsText
            Qt.callLater(function() {
                logFlick.contentY = Math.max(0, logFlick.contentHeight - logFlick.height)
            })
        }
        function onLogsChanged() {
            logsCount.text = root.tr(backend.logCount + " записей", backend.logCount + " entries")
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            id: sidebar
            Layout.preferredWidth: 224
            Layout.fillHeight: true
            color: panel
            border.color: borderColor
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 14
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 8
                    Layout.bottomMargin: 20
                    spacing: 11

                    Image {
                        source: "../assets/app_icon.png"
                        sourceSize: Qt.size(46, 46)
                        Layout.preferredWidth: 46
                        Layout.preferredHeight: 46
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                    }

                    ColumnLayout {
                        spacing: 1
                        Text {
                            text: "HETHEREAU"
                            color: accent
                            font.pixelSize: 10
                            font.bold: true
                        }
                        Text {
                            text: "HOBBIES TOOL"
                            color: textColor
                            font.pixelSize: 13
                            font.bold: true
                        }
                    }
                }

                Text {
                    text: tr("РАЗДЕЛЫ", "WORKSPACE")
                    color: mutedColor
                    font.pixelSize: 10
                    font.bold: true
                    Layout.leftMargin: 7
                    Layout.bottomMargin: 5
                }

                Repeater {
                    model: [
                        { id: "owner", ru: "Владелец", en: "Owner", icon: "sports_esports" },
                        { id: "about", ru: "О программе", en: "About", icon: "info" },
                        { id: "logs", ru: "Логи", en: "Logs", icon: "article" }
                    ]

                    delegate: Rectangle {
                        id: navItem
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: 48
                        radius: 11
                        property bool selected: root.currentPage === modelData.id
                        property bool hovered: navMouse.containsMouse
                        color: selected ? accent : (hovered ? panelAlt : "transparent")

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 10
                            spacing: 12

                            Image {
                                source: root.iconPath(navItem.modelData.icon)
                                sourceSize: Qt.size(21, 21)
                                Layout.preferredWidth: 21
                                Layout.preferredHeight: 21
                                smooth: true
                            }

                            Text {
                                text: root.tr(navItem.modelData.ru, navItem.modelData.en)
                                color: navItem.selected ? "#FFFFFF" : textColor
                                font.pixelSize: 13
                                font.bold: navItem.selected
                                Layout.fillWidth: true
                            }
                        }

                        MouseArea {
                            id: navMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.currentPage = navItem.modelData.id
                        }

                        Behavior on color { ColorAnimation { duration: 130 } }
                    }
                }

                Item { Layout.fillHeight: true }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: borderColor
                }

                Text {
                    text: "v" + backend.version + (backend.channel === "dev" ? " · DEV" : " · RELEASE")
                    color: mutedColor
                    font.pixelSize: 10
                    Layout.leftMargin: 5
                    Layout.bottomMargin: 2
                }

                Text {
                    text: "F6  " + tr("ЗАПУСК / ПАУЗА", "START / PAUSE") + "   ·   F7  " + tr("СТОП", "STOP")
                    color: mutedColor
                    font.pixelSize: 9
                    Layout.leftMargin: 5
                    Layout.bottomMargin: 8
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 20
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                Layout.bottomMargin: 16
                spacing: 12

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3

                    Text {
                        text: root.pageTitle()
                        color: textColor
                        font.pixelSize: 25
                        font.bold: true
                    }

                    Text {
                        text: root.pageSubtitle()
                        color: mutedColor
                        font.pixelSize: 11
                    }
                }

                Button {
                    text: tr("Обновить окно", "Refresh window")
                    visible: root.currentPage === "owner"
                    onClicked: backend.refreshGameWindow()
                    contentItem: Row {
                        spacing: 7
                        Image {
                            source: root.iconPath("refresh")
                            sourceSize: Qt.size(16, 16)
                            width: 16
                            height: 16
                        }
                        Text {
                            text: parent.parent.text
                            color: textColor
                            font.pixelSize: 11
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                    background: Rectangle {
                        radius: 9
                        color: parent.hovered ? panelAlt : panel
                        border.color: borderColor
                    }
                }

                ComboBox {
                    id: languageBox
                    Layout.preferredWidth: 116
                    model: ["English", "Русский"]
                    currentIndex: backend.language === "ru" ? 1 : 0
                    onActivated: backend.setLanguage(currentIndex === 1 ? "ru" : "en")
                }

                Switch {
                    checked: root.darkMode
                    onToggled: backend.setTheme(checked ? "dark" : "light")
                }
            }

            StackLayout {
                id: pages
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: root.currentPage === "owner" ? 0 : (root.currentPage === "about" ? 1 : 2)

                // OWNER PAGE
                Item {
                    Flickable {
                        anchors.fill: parent
                        clip: true
                        contentWidth: width
                        contentHeight: ownerContent.implicitHeight + 12

                        ColumnLayout {
                            id: ownerContent
                            width: parent.width
                            spacing: 13

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 76
                                radius: 14
                                color: panel
                                border.color: borderColor

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 15
                                    spacing: 12
                                    Image {
                                        source: root.iconPath("desktop_windows")
                                        sourceSize: Qt.size(24, 24)
                                        Layout.preferredWidth: 24
                                        Layout.preferredHeight: 24
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 3
                                        Text {
                                            text: tr("ИГРОВОЕ ОКНО", "GAME WINDOW")
                                            color: mutedColor
                                            font.pixelSize: 9
                                            font.bold: true
                                        }
                                        Text {
                                            text: backend.windowStatus
                                            color: textColor
                                            font.pixelSize: 12
                                            font.bold: true
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }
                                    }
                                    Rectangle {
                                        radius: 20
                                        width: 9
                                        height: 9
                                        color: backend.gameConnected ? green : red
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 108
                                radius: 15
                                color: panel
                                border.color: borderColor

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 16
                                    spacing: 8
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Text {
                                            text: tr("ТЕКУЩЕЕ СОСТОЯНИЕ", "CURRENT STATUS")
                                            color: mutedColor
                                            font.pixelSize: 10
                                            font.bold: true
                                        }
                                        Item { Layout.fillWidth: true }
                                        Rectangle {
                                            radius: 9
                                            color: backend.paused ? (darkMode ? "#493A1D" : "#FFF0CF")
                                                : (backend.running ? (darkMode ? "#153A31" : "#DDF5E9") : panelAlt)
                                            implicitWidth: statusText.implicitWidth + 22
                                            implicitHeight: 30
                                            Text {
                                                id: statusText
                                                anchors.centerIn: parent
                                                text: backend.status
                                                color: backend.paused ? amber : (backend.running ? green : textColor)
                                                font.pixelSize: 10
                                                font.bold: true
                                            }
                                        }
                                    }
                                    Text {
                                        text: backend.stage
                                        color: textColor
                                        font.pixelSize: 14
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 3
                                columnSpacing: 12
                                rowSpacing: 12

                                Repeater {
                                    model: [
                                        { key: "cycles", ru: "ЦИКЛЫ", en: "CYCLES", subtitleRu: "Завершено", subtitleEn: "Completed", icon: "monitoring", tone: "accent" },
                                        { key: "energy", ru: "ЭНЕРГИЯ", en: "ENERGY", subtitleRu: "Текущий запас", subtitleEn: "Current reserve", icon: "bolt", tone: "green" },
                                        { key: "income", ru: "ДОХОД", en: "INCOME", subtitleRu: "Лимит уровня", subtitleEn: "Level target", icon: "payments", tone: "amber" }
                                    ]

                                    delegate: Rectangle {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 126
                                        radius: 14
                                        color: panel
                                        border.color: borderColor

                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 13
                                            spacing: 5

                                            RowLayout {
                                                Layout.fillWidth: true
                                                Text {
                                                    text: root.tr(modelData.ru, modelData.en)
                                                    color: mutedColor
                                                    font.pixelSize: 9
                                                    font.bold: true
                                                }
                                                Item { Layout.fillWidth: true }
                                                Image {
                                                    source: root.iconPath(modelData.icon)
                                                    sourceSize: Qt.size(19, 19)
                                                    Layout.preferredWidth: 19
                                                    Layout.preferredHeight: 19
                                                }
                                            }

                                            Text {
                                                text: modelData.key === "cycles" ? backend.cycles :
                                                      (modelData.key === "energy" ? backend.energy : backend.income)
                                                color: modelData.tone === "green" ? green :
                                                       (modelData.tone === "amber" ? amber : accent)
                                                font.pixelSize: 23
                                                font.bold: true
                                                elide: Text.ElideRight
                                                Layout.fillWidth: true
                                            }

                                            Text {
                                                text: root.tr(modelData.subtitleRu, modelData.subtitleEn)
                                                color: mutedColor
                                                font.pixelSize: 10
                                            }
                                        }
                                    }
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10

                                Button {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 48
                                    text: backend.running && !backend.paused
                                        ? tr("Пауза · F6", "Pause · F6")
                                        : tr("Запустить / Продолжить · F6", "Start / Resume · F6")
                                    onClicked: backend.toggleRunPause()
                                    background: Rectangle {
                                        radius: 11
                                        color: parent.down ? accentHover : accent
                                    }
                                    contentItem: Row {
                                        spacing: 8
                                        anchors.centerIn: parent
                                        Image {
                                            source: root.iconPath(backend.running && !backend.paused ? "pause" : "play_arrow")
                                            sourceSize: Qt.size(20, 20)
                                            width: 20
                                            height: 20
                                        }
                                        Text {
                                            text: parent.parent.text
                                            color: "#FFFFFF"
                                            font.pixelSize: 12
                                            font.bold: true
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                    }
                                }

                                Button {
                                    Layout.preferredWidth: 150
                                    Layout.preferredHeight: 48
                                    text: tr("Стоп · F7", "Stop · F7")
                                    onClicked: backend.stop()
                                    background: Rectangle {
                                        radius: 11
                                        color: parent.down ? (darkMode ? "#572B3A" : "#F5DDE3")
                                            : (darkMode ? "#392433" : "#FBEAF0")
                                        border.color: darkMode ? "#704052" : "#EFC8D2"
                                    }
                                    contentItem: Row {
                                        spacing: 8
                                        anchors.centerIn: parent
                                        Image {
                                            source: root.iconPath("stop")
                                            sourceSize: Qt.size(18, 18)
                                            width: 18
                                            height: 18
                                        }
                                        Text {
                                            text: parent.parent.text
                                            color: red
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                    }
                                }
                            }

                            Button {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 38
                                text: tr("Сканировать доход и энергию", "Scan income and energy")
                                onClicked: backend.scanState()
                                background: Rectangle {
                                    radius: 9
                                    color: parent.hovered ? panelAlt : "transparent"
                                    border.color: borderColor
                                }
                                contentItem: Text {
                                    text: parent.text
                                    color: mutedColor
                                    font.pixelSize: 11
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 54
                                radius: 11
                                color: panelAlt
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 13
                                    spacing: 9
                                    Image {
                                        source: root.iconPath("keyboard")
                                        sourceSize: Qt.size(18, 18)
                                        Layout.preferredWidth: 18
                                        Layout.preferredHeight: 18
                                    }
                                    Text {
                                        text: "F6"
                                        color: accent
                                        font.pixelSize: 11
                                        font.bold: true
                                    }
                                    Text {
                                        text: tr("Запуск / пауза", "Start / pause")
                                        color: textColor
                                        font.pixelSize: 10
                                    }
                                    Item { Layout.fillWidth: true }
                                    Text {
                                        text: "F7"
                                        color: red
                                        font.pixelSize: 11
                                        font.bold: true
                                    }
                                    Text {
                                        text: tr("Остановить", "Stop")
                                        color: textColor
                                        font.pixelSize: 10
                                    }
                                }
                            }
                        }
                    }
                }

                // ABOUT PAGE
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
                            contentHeight: aboutColumn.implicitHeight + 10

                            ColumnLayout {
                                id: aboutColumn
                                width: parent.width
                                spacing: 16

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 22
                                    Image {
                                        source: "../assets/app_icon.png"
                                        sourceSize: Qt.size(120, 120)
                                        Layout.preferredWidth: 120
                                        Layout.preferredHeight: 120
                                        fillMode: Image.PreserveAspectFit
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 5
                                        Text {
                                            text: "HETHEREAU HOBBIES TOOL"
                                            color: accent
                                            font.pixelSize: 11
                                            font.bold: true
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
                                            text: "v" + backend.version + " · " + backend.channel.toUpperCase()
                                            color: mutedColor
                                            font.pixelSize: 11
                                        }
                                    }
                                }

                                Rectangle { Layout.fillWidth: true; height: 1; color: borderColor }

                                Text {
                                    text: tr(
                                        "Утилита для автоматизации игровых хобби в Neverness to Everness. Сейчас доступен модуль «Подборка владельца». Рыбалка и другие занятия будут добавляться отдельно.",
                                        "A desktop toolkit for automating hobbies in Neverness to Everness. Owner's Selection is available now. Fishing and other activities will be added as separate modules."
                                    )
                                    color: textColor
                                    font.pixelSize: 13
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    radius: 12
                                    color: panelAlt
                                    implicitHeight: aboutDetails.implicitHeight + 24

                                    ColumnLayout {
                                        id: aboutDetails
                                        anchors.fill: parent
                                        anchors.margins: 14
                                        spacing: 12
                                        RowLayout {
                                            Layout.fillWidth: true
                                            Text { text: tr("Текущий модуль", "Current module"); color: mutedColor; font.pixelSize: 11 }
                                            Item { Layout.fillWidth: true }
                                            Text { text: tr("Подборка владельца", "Owner's Selection"); color: textColor; font.pixelSize: 11; font.bold: true }
                                        }
                                        RowLayout {
                                            Layout.fillWidth: true
                                            Text { text: tr("Игровой процесс", "Game process"); color: mutedColor; font.pixelSize: 11 }
                                            Item { Layout.fillWidth: true }
                                            Text { text: "HTGame.exe"; color: textColor; font.pixelSize: 11; font.bold: true }
                                        }
                                        RowLayout {
                                            Layout.fillWidth: true
                                            Text { text: tr("Интерфейс", "Interface"); color: mutedColor; font.pixelSize: 11 }
                                            Item { Layout.fillWidth: true }
                                            Text { text: "PySide6 + Qt Quick / QML"; color: textColor; font.pixelSize: 11; font.bold: true }
                                        }
                                    }
                                }

                                Button {
                                    Layout.preferredWidth: 190
                                    Layout.preferredHeight: 42
                                    text: tr("Открыть GitHub", "Open GitHub")
                                    onClicked: backend.openUrl("https://github.com/M1ST0R/hethereau-hobbies-tool")
                                    background: Rectangle { radius: 9; color: accent }
                                    contentItem: Text {
                                        text: parent.text
                                        color: "#FFFFFF"
                                        font.pixelSize: 11
                                        font.bold: true
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }
                    }
                }

                // LOGS PAGE
                Item {
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10

                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: tr("Журнал событий", "Activity log")
                                color: textColor
                                font.pixelSize: 17
                                font.bold: true
                            }
                            Text {
                                id: logsCount
                                text: tr(backend.logCount + " записей", backend.logCount + " entries")
                                color: mutedColor
                                font.pixelSize: 10
                            }
                            Item { Layout.fillWidth: true }

                            Button {
                                text: tr("Копировать всё", "Copy all")
                                onClicked: backend.copyAllLogs()
                                background: Rectangle { radius: 8; color: panelAlt }
                                contentItem: Text {
                                    text: parent.text
                                    color: textColor
                                    font.pixelSize: 10
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }

                            Button {
                                text: tr("Очистить", "Clear")
                                onClicked: backend.clearLogs()
                                background: Rectangle { radius: 8; color: darkMode ? "#392433" : "#FBEAF0" }
                                contentItem: Text {
                                    text: parent.text
                                    color: red
                                    font.pixelSize: 10
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            radius: 14
                            color: darkMode ? "#080C14" : "#FFFFFF"
                            border.color: borderColor
                            clip: true

                            Flickable {
                                id: logFlick
                                anchors.fill: parent
                                anchors.margins: 10
                                clip: true
                                contentWidth: width
                                contentHeight: logsArea.implicitHeight

                                TextArea {
                                    id: logsArea
                                    width: logFlick.width
                                    height: Math.max(logFlick.height, implicitHeight)
                                    text: backend.logsText
                                    readOnly: true
                                    selectByMouse: true
                                    selectByKeyboard: true
                                    wrapMode: TextEdit.Wrap
                                    color: darkMode ? "#DDE5F5" : "#26334B"
                                    selectedTextColor: "#FFFFFF"
                                    selectionColor: accent
                                    font.family: "Consolas"
                                    font.pixelSize: 10
                                    background: null
                                    padding: 2
                                }

                                ScrollBar.vertical: ScrollBar {
                                    policy: ScrollBar.AsNeeded
                                }
                            }
                        }

                        Text {
                            text: tr("Выдели нужный фрагмент и нажми Ctrl+C.", "Select a fragment and press Ctrl+C.")
                            color: mutedColor
                            font.pixelSize: 10
                        }
                    }
                }
            }
        }
    }

    Component.onCompleted: {
        logsArea.text = backend.logsText
    }
}
