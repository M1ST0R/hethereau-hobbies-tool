"""Headless smoke test: compile and instantiate the bundled Qt Quick UI."""

from __future__ import annotations

import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


class BackendStub(QObject):
    statusChanged = Signal()
    metricsChanged = Signal()
    windowChanged = Signal()
    languageChanged = Signal()
    themeChanged = Signal()
    logsChanged = Signal()
    logAdded = Signal(str)
    logsReset = Signal()
    runStateChanged = Signal()
    hotkeysChanged = Signal()

    @Property(str, notify=statusChanged)
    def status(self): return "READY"

    @Property(str, notify=statusChanged)
    def stage(self): return "Waiting"

    @Property(str, notify=metricsChanged)
    def cycles(self): return "0"

    @Property(str, notify=metricsChanged)
    def energy(self): return "292 / 700"

    @Property(str, notify=metricsChanged)
    def income(self): return "0 / 1900"

    @Property(str, notify=windowChanged)
    def windowStatus(self): return "HTGame.exe · 1600 × 900"

    @Property(bool, notify=windowChanged)
    def gameConnected(self): return True

    @Property(bool, notify=runStateChanged)
    def running(self): return False

    @Property(bool, notify=runStateChanged)
    def paused(self): return False

    @Property(str, notify=languageChanged)
    def language(self): return "en"

    @Property(str, notify=themeChanged)
    def theme(self): return "dark"

    @Property(str, notify=hotkeysChanged)
    def toggleHotkey(self): return "F6"

    @Property(str, notify=hotkeysChanged)
    def stopHotkey(self): return "F7"

    @Property(list, constant=True)
    def hotkeyOptions(self): return [f"F{i}" for i in range(1, 13)]

    @Property(str, constant=True)
    def version(self): return "0.3.0-dev.test"

    @Property(str, constant=True)
    def channel(self): return "dev"

    @Property(str, notify=logsChanged)
    def logsText(self): return "14:00:00  ·  QML smoke test"

    @Property(int, notify=logsChanged)
    def logCount(self): return 1

    @Slot()
    def toggleRunPause(self): pass

    @Slot()
    def stop(self): pass

    @Slot()
    def scanState(self): pass

    @Slot()
    def refreshGameWindow(self): pass

    @Slot()
    def copyAllLogs(self): pass

    @Slot()
    def clearLogs(self): pass

    @Slot(str)
    def setLanguage(self, _language): pass

    @Slot(str)
    def setTheme(self, _theme): pass

    @Slot(str, str)
    def setHotkeys(self, _toggle, _stop): pass

    @Slot(str)
    def openUrl(self, _url): pass


def main() -> int:
    app = QGuiApplication(sys.argv[:1])
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", BackendStub())

    qml_file = Path(__file__).resolve().parents[1] / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        print("QML smoke test failed: no root object was created.", file=sys.stderr)
        return 1

    print("QML smoke test passed: Main.qml loaded and created an ApplicationWindow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
