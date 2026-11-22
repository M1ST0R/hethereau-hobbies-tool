"""Qt/QML bridge for the existing HHT automation engine.

The legacy automation implementation is reused without constructing its Tk UI.
The QML layer communicates with it only through Qt properties, signals and slots.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtGui import QGuiApplication

from hethereau_hobbies_tool import (
    APP_CHANNEL,
    APP_TITLE,
    APP_VERSION,
    OwnerSelectionApp,
    configure_tesseract,
)
try:
    from pynput import keyboard
except Exception:
    keyboard = None


class HHTBackend(QObject):
    statusChanged = Signal()
    metricsChanged = Signal()
    windowChanged = Signal()
    languageChanged = Signal()
    themeChanged = Signal()
    logsChanged = Signal()
    logAdded = Signal(str)
    logsReset = Signal()
    hotkeyRequested = Signal(str)
    runStateChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.core = OwnerSelectionApp.__new__(OwnerSelectionApp)
        core = self.core

        # State normally initialized by OwnerSelectionApp.__init__, excluding
        # all Tk/CustomTkinter widgets and the old UI event loop.
        core.language = core._load_language()
        core.theme_mode = core._load_theme()
        core.ui_metrics = {"cycles": "0", "energy": "—", "income": "—"}
        core.current_status = "ГОТОВ К РАБОТЕ"
        core.current_stage = "Ожидание запуска"
        core.log_history = []
        core.closed = False
        core.game_hwnd = None
        core.game_pid = None
        core.cycle_count = 0
        core.last_ocr_meta = ""
        core.last_ocr_debug_path = ""
        core.current_page = "owner"
        core.game_screen_context = "outside_event"
        core.stop_event = threading.Event()
        core.pause_event = threading.Event()
        core.worker_thread = None
        core.active_income_ocr_thread = None
        core.hotkey_listener = None
        core.hotkey_lock = threading.Lock()
        core.last_hotkey_time = {}
        core.rescan_requested = threading.Event()
        core.pause_scan_requested = threading.Event()
        core.last_pause_scan = None
        core.last_resume_scan = None
        core._stop_scan_lock = threading.Lock()
        core._stop_scan_pending = False
        core.worker_error = None
        core.last_scan_error = ""

        # Replace the old view callbacks with a Qt signal bridge.
        core.log = self.log
        core.set_status = self.set_status
        core.set_stage = self.set_stage
        core.set_metric = self.set_metric
        core.set_window_status = self.set_window_status

        self._lock = threading.RLock()
        self._log_lines: list[str] = []
        self._status = core.tr(core.current_status)
        self._stage = core.tr(core.current_stage)
        self._cycles = "0"
        self._energy = "—"
        self._income = "—"
        self._window_status = core.tr("Поиск HTGame.exe…")
        self._game_connected = False
        self._language = core.language
        self._theme = core.theme_mode

        configure_tesseract()
        core.refresh_game_window(silent=True)
        self.hotkeyRequested.connect(self._handle_hotkey)
        self._start_hotkeys()

        self.log("HHT готов. F6 — старт / пауза, F7 — остановка.")
        self.log("Открой событие «Подборка владельца» перед запуском.")

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @Property(str, notify=statusChanged)
    def stage(self) -> str:
        return self._stage

    @Property(str, notify=metricsChanged)
    def cycles(self) -> str:
        return self._cycles

    @Property(str, notify=metricsChanged)
    def energy(self) -> str:
        return self._energy

    @Property(str, notify=metricsChanged)
    def income(self) -> str:
        return self._income

    @Property(str, notify=windowChanged)
    def windowStatus(self) -> str:
        return self._window_status

    @Property(bool, notify=windowChanged)
    def gameConnected(self) -> bool:
        return self._game_connected

    @Property(bool, notify=runStateChanged)
    def running(self) -> bool:
        worker = self.core.worker_thread
        return bool(worker and worker.is_alive())

    @Property(bool, notify=runStateChanged)
    def paused(self) -> bool:
        return self.core.pause_event.is_set()

    @Property(str, notify=languageChanged)
    def language(self) -> str:
        return self._language

    @Property(str, notify=themeChanged)
    def theme(self) -> str:
        return self._theme

    @Property(str, constant=True)
    def version(self) -> str:
        return APP_VERSION

    @Property(str, constant=True)
    def channel(self) -> str:
        return APP_CHANNEL

    @Property(str, notify=logsChanged)
    def logsText(self) -> str:
        with self._lock:
            return "\n".join(self._log_lines)

    @Property(int, notify=logsChanged)
    def logCount(self) -> int:
        with self._lock:
            return len(self._log_lines)

    def log(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        try:
            visible = self.core.tr(message)
        except Exception:
            visible = message
        line = f"{stamp}  ·  {visible}"

        with self._lock:
            self.core.log_history.append((stamp, message))
            self.core.log_history = self.core.log_history[-1000:]
            self._log_lines.append(line)
            if len(self._log_lines) > 1000:
                self._log_lines.pop(0)

        self.logAdded.emit(line)
        self.logsChanged.emit()

    def set_status(self, status: str, stage: str | None = None) -> None:
        self.core.current_status = status
        if stage is not None:
            self.core.current_stage = stage
        self._status = self.core.tr(status)
        if stage is not None:
            self._stage = self.core.tr(stage)
        self.statusChanged.emit()
        self.runStateChanged.emit()

    def set_stage(self, stage: str) -> None:
        self.core.current_stage = stage
        self._stage = self.core.tr(stage)
        self.statusChanged.emit()

    def set_metric(self, metric: str, value: str) -> None:
        self.core.ui_metrics[metric] = value
        if metric == "cycles":
            self._cycles = value
        elif metric == "energy":
            self._energy = value
        elif metric == "income":
            self._income = value
        self.metricsChanged.emit()

    def set_window_status(self, text: str, found: bool) -> None:
        self._window_status = self.core.tr(text)
        self._game_connected = bool(found)
        self.windowChanged.emit()

    @Slot()
    def toggleRunPause(self) -> None:
        self.core.toggle_run_pause()
        self.runStateChanged.emit()

    @Slot()
    def stop(self) -> None:
        self.core.stop()
        self.runStateChanged.emit()

    @Slot()
    def scanState(self) -> None:
        self.core.scan_state_manual()

    @Slot()
    def refreshGameWindow(self) -> None:
        self.core.refresh_game_window(silent=False)

    @Slot()
    def copyAllLogs(self) -> None:
        QGuiApplication.clipboard().setText(self.logsText)

    @Slot()
    def clearLogs(self) -> None:
        with self._lock:
            self._log_lines.clear()
            self.core.log_history.clear()
        self.logsReset.emit()
        self.logsChanged.emit()

    @Slot(str)
    def setLanguage(self, language: str) -> None:
        if language not in ("en", "ru") or language == self._language:
            return
        self.core.language = language
        self._language = language
        self.core._save_preferences()
        self._rebuild_translated_logs()
        self.languageChanged.emit()

    def _rebuild_translated_logs(self) -> None:
        with self._lock:
            self._log_lines = [
                f"{stamp}  ·  {self.core.tr(message)}"
                for stamp, message in self.core.log_history
            ][-1000:]
        self.logsReset.emit()
        self.logsChanged.emit()

    @Slot(str)
    def setTheme(self, theme: str) -> None:
        if theme not in ("dark", "light") or theme == self._theme:
            return
        self.core.theme_mode = theme
        self._theme = theme
        self.core._save_preferences()
        self.themeChanged.emit()

    @Slot(str)
    def openUrl(self, url: str) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl(url))

    def _start_hotkeys(self) -> None:
        if keyboard is None:
            self.log("Глобальные хоткеи недоступны. Используй кнопки приложения.")
            return

        def on_press(key):
            now = time.monotonic()
            if key == keyboard.Key.f6:
                name = "toggle"
            elif key == keyboard.Key.f7:
                name = "stop"
            else:
                return

            with self.core.hotkey_lock:
                if now - self.core.last_hotkey_time.get(name, 0) < 0.45:
                    return
                self.core.last_hotkey_time[name] = now
            if not self.core.closed:
                self.hotkeyRequested.emit(name)

        try:
            self.core.hotkey_listener = keyboard.Listener(on_press=on_press)
            self.core.hotkey_listener.daemon = True
            self.core.hotkey_listener.start()
            self.log("Глобальные F6 / F7 активны.")
        except Exception as exc:
            self.log(f"Не удалось включить глобальные хоткеи: {exc}")

    @Slot(str)
    def _handle_hotkey(self, action: str) -> None:
        if action == "toggle":
            self.toggleRunPause()
        elif action == "stop":
            self.stop()

    @Slot()
    def shutdown(self) -> None:
        if self.core.closed:
            return
        self.core.closed = True
        self.core.stop_event.set()
        self.core.pause_event.clear()
        listener = self.core.hotkey_listener
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                pass
