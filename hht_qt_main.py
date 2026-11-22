"""Application entry point for the PySide6 + Qt Quick interface."""

from __future__ import annotations

import ctypes
import os
import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from hethereau_hobbies_tool import APP_TITLE, ensure_windows_admin, resource_path
from hht_qt_backend import HHTBackend


def main() -> int:
    if os.name == "nt":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "M1ST0R.HethereauHobbiesTool"
            )
        except Exception:
            pass

    if not ensure_windows_admin():
        return 0

    app = QGuiApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setOrganizationName("M1ST0R")
    app.setOrganizationDomain("github.com/M1ST0R")
    icon_path = resource_path("assets/app_icon.png")
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    engine = QQmlApplicationEngine()
    backend = HHTBackend()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(resource_path("qml/Main.qml")))

    if not engine.rootObjects():
        backend.shutdown()
        return 1

    app.aboutToQuit.connect(backend.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
