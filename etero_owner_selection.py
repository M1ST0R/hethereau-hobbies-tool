from __future__ import annotations

import os
import re
import json
import threading
import ctypes
import time
import shutil
import subprocess
import sys
from datetime import datetime

import customtkinter as ctk
import pyautogui
import pytesseract
from PIL import Image, ImageOps, ImageGrab

# Use physical pixels for reliable Win32 client-area coordinates.
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

try:
    import psutil
except ImportError:
    psutil = None

if os.name == "nt":
    try:
        import win32gui
        import win32process
        import win32con
    except ImportError:
        win32gui = win32process = win32con = None
else:
    win32gui = win32process = win32con = None

if sys.platform.startswith("linux"):
    try:
        from Xlib import X, display as xdisplay
    except ImportError:
        X = xdisplay = None
else:
    X = xdisplay = None

try:
    from pynput import keyboard
except Exception:
    keyboard = None


# ---------------------------- FIXED SETTINGS -----------------------------
APP_TITLE = "Hethereau Owner's Selection Tool (HOST)"
TARGET_EXE = "HTGame.exe"
REFERENCE_WIDTH = 1600
REFERENCE_HEIGHT = 900

# Coordinates are relative to the HTGame.exe client area (1600x900 reference).
DEFAULT_POINTS = {
    "Магазин": (1435, 838),
    "Молоток": (65, 383),
    "Получить": (968, 699),
}

# OCR rectangles are relative to the game client area.
INCOME_REGION = (1380, 70, 200, 58)  # Только числовой счётчик, без подписи «Доход»
ENERGY_REGION = (1235, 8, 245, 65)

MIN_INCOME_TARGET = 100  # Reject clearly truncated OCR denominators such as "1" or "90".
CLAIM_COST = 24
SHOP_COST_MAX = 8
MINIMUM_ENERGY_PER_CYCLE = CLAIM_COST + SHOP_COST_MAX
CLICK_INTERVAL = 0.08
OCR_INTERVAL = 1.0
ENERGY_RETRY_INTERVAL = 1.5
MAX_ENERGY_OCR_FAILURES = 8
def configure_tesseract():
    """Prefer the bundled OCR engine, then fall back to a system installation."""
    bundle_root = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    executable = "tesseract.exe" if os.name == "nt" else "tesseract"
    bundled_path = os.path.join(bundle_root, "tesseract", executable)
    if os.path.isfile(bundled_path):
        pytesseract.pytesseract.tesseract_cmd = bundled_path
        bundled_tessdata = os.path.join(bundle_root, "tesseract", "tessdata")
        if os.path.isdir(bundled_tessdata):
            os.environ["TESSDATA_PREFIX"] = bundled_tessdata
        return bundled_path

    system_path = shutil.which("tesseract")
    if system_path:
        pytesseract.pytesseract.tesseract_cmd = system_path
        return system_path

    legacy_windows_path = "C:/Program Files/Tesseract-OCR/tesseract.exe"
    if os.path.isfile(legacy_windows_path):
        pytesseract.pytesseract.tesseract_cmd = legacy_windows_path
        return legacy_windows_path
    return None



EN_TRANSLATIONS = {
    APP_TITLE: APP_TITLE,
    "УВЛЕЧЕНИЯ ЭТЕРО": "HETHEREAU",
    "ПОДБОРКА ВЛАДЕЛЬЦА": "OWNER'S SELECTION",
    "Автоматизация игрового события": "Game event automation",
    "↻  Обновить окно": "↻  Refresh game window",
    "ИГРОВОЕ ОКНО": "GAME WINDOW",
    "Поиск HTGame.exe…": "Searching for HTGame.exe…",
    "ТЕКУЩЕЕ СОСТОЯНИЕ": "CURRENT STATUS",
    "ГОТОВ К РАБОТЕ": "READY",
    "Ожидание запуска": "Waiting to start",
    "ЦИКЛЫ": "CYCLES",
    "Завершено": "Completed",
    "ЭНЕРГИЯ": "ENERGY",
    "Текущий запас": "Current amount",
    "ДОХОД": "INCOME",
    "Автоопределение уровня": "Level target detected automatically",
    "▶  Запустить / Пауза  ·  F6": "▶  Start / Pause  ·  F6",
    "■  Стоп  ·  F7": "■  Stop  ·  F7",
    "Проверить распознавание": "Test OCR",
    "Запуск / пауза": "Start / pause",
    "Остановить": "Stop",
    "ЖУРНАЛ": "ACTIVITY LOG",
    "Последние действия": "Recent activity",
    "Программа готова. F6 — старт / пауза, F7 — остановка.": "Ready. F6 — start / pause, F7 — stop.",
    "Открой событие «Увлечения Этеро — Подборка владельца» перед запуском.": "Open the Hethereau “Owner's Selection” event before starting.",
    "Глобальные хоткеи недоступны. Кнопки GUI остаются доступны.": "Global hotkeys are unavailable. GUI controls are still available.",
    "Глобальные F6 / F7 активны.": "Global F6 / F7 hotkeys are active.",
    "Пауза снята.": "Resumed.",
    "Пауза включена.": "Paused.",
    "Автоматизация запущена.": "Automation started.",
    "Получена команда остановки.": "Stop command received.",
    "Автоматизация остановлена пользователем": "Automation stopped by user",
    "Автоматизация не запущена": "Automation is not running",
    "Завершаю текущую операцию": "Finishing the current operation",
    "Подготовка первого цикла": "Preparing the first cycle",
    "Продолжаю текущий цикл": "Resuming the current cycle",
    "Автоматизация приостановлена. Нажми F6 для продолжения.": "Automation paused. Press F6 to resume.",
    "Ожидаю F6 для продолжения": "Waiting for F6 to resume",
    "Проверяю, хватит ли энергии на следующий полный цикл": "Checking whether enough energy remains for another full cycle",
    "Открываю магазин события": "Opening the event shop",
    "Открываю магазин": "Opening shop",
    "Накопление целевого дохода": "Building the target income",
    "Нажимаю Esc и ожидаю экран награды": "Pressing Esc and waiting for the reward screen",
    "Забираю награду за испытание": "Claiming the challenge reward",
    "Работа завершена": "Finished",
    "Язык интерфейса изменён.": "Interface language changed.",
    "Не удалось сохранить язык интерфейса: ": "Could not save UI language: ",
    "Определяю целевой доход по уровню": "Detecting this level's target income",
    "Не удалось включить глобальные хоткеи: ": "Could not enable global hotkeys: ",
    "Остановка завершена": "Stopped",
    "Снимок области OCR: ": "OCR capture: ",
    "Область дохода: ": "Income OCR area: ",
    "Область энергии: ": "Energy OCR area: ",
    "Магазин открыт. Начинаю нажимать молоток.": "Shop opened. Starting hammer clicks.",
    "Запуск / пауза": "Start / pause",
    "Остановлено": "STOPPED",
    "ОСТАНОВЛЕНО": "STOPPED",
    "ОСТАНОВКА": "STOPPING",
    "РАБОТАЕТ": "RUNNING",
    "ПАУЗА": "PAUSED",
    "ЗАПУСК": "STARTING",
    "ПРОВЕРКА ЭНЕРГИИ": "CHECKING ENERGY",
    "ЭНЕРГИЯ ЗАКОНЧИЛАСЬ": "OUT OF ENERGY",
    "ОТКРЫВАЮ МАГАЗИН": "OPENING SHOP",
    "ФАРМ ДОХОДА": "FARMING INCOME",
    "ЗАВЕРШАЮ ИСПЫТАНИЕ": "COMPLETING CHALLENGE",
    "ПОЛУЧАЮ НАГРАДУ": "CLAIMING REWARD",
    "ОШИБКА OCR ЭНЕРГИИ": "ENERGY OCR ERROR",
    "ОШИБКА РАСПОЗНАВАНИЯ": "INCOME OCR ERROR",
    "АВАРИЙНАЯ ОСТАНОВКА": "EMERGENCY STOP",
    "ЗАВЕРШЕНО": "COMPLETED",
    "ОШИБКА": "ERROR",
    "Не установлены pywin32 / psutil": "pywin32 / psutil are not installed",
    "Ошибка поиска окна": "Window search error",
    "Не удалось активировать HTGame.exe. Переключись в окно игры и повтори.": "Could not activate HTGame.exe. Focus the game window and try again.",
    "У HTGame.exe нет доступной клиентской области. Возможно, окно свёрнуто.": "HTGame.exe has no available client area. The window may be minimized.",
    "Не удалось определить запас энергии. Проверь debug_energy_capture.png.": "Could not read the energy value. Check debug_energy_capture.png.",
    "Значение дохода не читается. Проверь debug_income_capture.png.": "The income value cannot be read. Check debug_income_capture.png.",
    "Определён целевой доход текущего уровня: ": "Detected target income for this level: ",
    "Привязано окно ": "Attached to window ",
    "Окно ": "Window ",
    " не найдено": " not found",
    "Открой игру и нажми «Обновить окно».": "Open the game and click Refresh game window.",
    "Не удалось прочитать энергию (": "Could not read energy (",
    "). Попытка ": "). Attempt ",
    "Не удалось прочитать энергию": "Could not read energy",
    "Сработал аварийный механизм PyAutoGUI": "PyAutoGUI failsafe was triggered",
    "Автоматизация остановлена без кликов: значение энергии не подтверждено.": "Automation stopped without clicking: the energy value was not confirmed.",
    "Для следующего цикла нужно не менее ": "At least ",
    " энергии.": " energy is required for the next cycle.",
    "Запас энергии перед циклом: ": "Energy before cycle: ",
    "Определён целевой доход текущего уровня: ": "Detected target income for this level: ",
    "Тест энергии: ": "Energy test: ",
    "Тест дохода: ": "Income test: ",
    "Ошибка проверки OCR: ": "OCR test error: ",
    "Ошибка: ": "Error: ",
    "Не удалось сохранить язык интерфейса: ": "Could not save interface language: ",
}


# ------------------------------- THEME -----------------------------------
BG = "#0B1020"
PANEL = "#131C31"
PANEL_ALT = "#19243D"
BORDER = "#263653"
TEXT = "#F2F5FA"
MUTED = "#91A0B8"
ACCENT = "#6C8CFF"
GREEN = "#24C78A"
RED = "#F06475"
YELLOW = "#F5C45E"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.015


class OwnerSelectionApp:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.language = self._load_language()
        self.ui_metrics = {"cycles": "0", "energy": "—", "income": "—"}
        self.current_status = "ГОТОВ К РАБОТЕ"
        self.current_stage = "Ожидание запуска"
        self.log_history: list[tuple[str, str]] = []
        self.root.title(self.tr(APP_TITLE))
        self.root.geometry("760x790")
        self.root.minsize(700, 710)
        self.root.configure(fg_color=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        configure_tesseract()

        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.worker_thread: threading.Thread | None = None
        self.hotkey_listener = None
        self.hotkey_lock = threading.Lock()
        self.last_hotkey_time: dict[str, float] = {}
        self.closed = False
        self.game_hwnd: int | None = None
        self.game_pid: int | None = None
        self.cycle_count = 0
        self.last_ocr_meta = ""
        self.last_ocr_debug_path = ""

        self.metric_labels: dict[str, ctk.CTkLabel] = {}
        self._build_ui()
        self.refresh_game_window(silent=True)
        self._start_hotkeys()
        self.log("Программа готова. F6 — старт / пауза, F7 — остановка.")
        self.log("Открой событие «Увлечения Этеро — Подборка владельца» перед запуском.")

    def _load_language(self) -> str:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as config_file:
                value = json.load(config_file).get("language", "en")
                return value if value in ("en", "ru") else "en"
        except Exception:
            return "en"

    def _save_language(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_config.json")
        try:
            with open(config_path, "w", encoding="utf-8") as config_file:
                json.dump({"language": self.language}, config_file, ensure_ascii=False, indent=2)
        except Exception as exc:
            self.log(f"Не удалось сохранить язык интерфейса: {exc}")

    def tr(self, text: str) -> str:
        """Translate UI text to the selected language."""
        if self.language == "ru":
            return text
        translated = EN_TRANSLATIONS.get(text, text)
        # Translate common dynamic status/log fragments while keeping values intact.
        patterns = (
            (r"Накопление целевого дохода: (\d+)", r"Building target income: \1"),
            (r"Определён целевой доход текущего уровня: (\d+)\.", r"Detected target for this level: \1."),
            (r"Осталось (\d+)\. Новые циклы остановлены\.", r"Remaining energy: \1. No more cycles will start."),
            (r"Осталось (\d+). Новые циклы остановлены\.", r"Remaining energy: \1. No more cycles will start."),
            (r"Цикл №(\d+) завершён\.", r"Cycle #\1 completed."),
            (r"Запас энергии перед циклом: (\d+)/(\d+)\.", r"Energy before cycle: \1/\2."),
            (r"Целевой показатель подтверждён повторно: (\d+)/(\d+)\.", r"Target confirmed again: \1/\2."),
            (r"Порог (\d+)/(\d+) распознан\. Проверяю повторно, чтобы исключить кадр анимации\.", r"Threshold \1/\2 detected. Confirming again to avoid an animation frame."),
            (r"Осталось (\d+) энергии\. Новые циклы остановлены\.", r"Energy remaining: \1. No more cycles will start."),
            (r"Распознавание дохода не работает более (\d+) секунд\. Последний результат: (.*)\.", r"Income OCR has failed for more than \1 seconds. Last result: \2."),
            (r"Не удалось прочитать энергию \(.*\)\. Попытка (\d+)/(\d+)\.", r"Could not read energy (\1). Attempt \2/\3."),
            (r"Окно подключено: HWND=(\d+), область (\d+)×(\d+)\.", r"Game window attached: HWND=\1, client area \2×\3."),
            (r"Для следующего цикла нужно не менее (\d+) энергии\.", r"At least \1 energy is required for the next cycle."),
            (r"Привязано окно HTGame\.exe, PID (\d+), область (\d+)×(\d+)\.", r"Attached to HTGame.exe, PID \1, client area \2×\3."),
            (r"HTGame\.exe не найден", r"HTGame.exe not found"),
        )
        for pattern, replacement in patterns:
            if re.search(pattern, text):
                return re.sub(pattern, replacement, text)
        prefixes = (
            ("Тест энергии: ", "Energy test: "),
            ("Тест дохода: ", "Income test: "),
            ("Ошибка проверки OCR: ", "OCR test error: "),
            ("Ошибка: ", "Error: "),
            ("Снимок области OCR: ", "OCR capture: "),
            ("Область энергии: ", "Energy OCR area: "),
            ("Область дохода: ", "Income OCR area: "),
            ("Не удалось прочитать энергию (", "Could not read energy ("),
            ("Определён целевой доход текущего уровня: ", "Detected target income for this level: "),
            ("Запас энергии перед циклом: ", "Energy before cycle: "),
            ("Окно подключено: ", "Game window attached: "),
            ("Привязано окно ", "Attached window "),
            ("Ошибка поиска окна ", "Window search failed for "),
            ("Не удалось включить глобальные хоткеи: ", "Could not enable global hotkeys: "),
        )
        for source, target in prefixes:
            if text.startswith(source):
                return target + text[len(source):]
        return translated

    def toggle_language(self):
        self.language = "ru" if self.language == "en" else "en"
        self._save_language()
        for child in self.root.winfo_children():
            child.destroy()
        self.metric_labels = {}
        self._build_ui()
        self.root.title(self.tr(APP_TITLE))
        self.set_status(self.current_status, self.current_stage)
        for metric, value in self.ui_metrics.items():
            self.set_metric(metric, value)
        self.log("Язык интерфейса изменён." if self.language == "ru" else "Interface language changed.")

    # -------------------------------- UI ----------------------------------
    def _build_ui(self):
        outer = ctk.CTkFrame(self.root, fg_color=BG, corner_radius=0)
        outer.pack(fill="both", expand=True, padx=22, pady=20)

        # Header
        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            title_box, text=self.tr("УВЛЕЧЕНИЯ ЭТЕРО"), text_color=ACCENT,
            font=ctk.CTkFont("Segoe UI", 15, "bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box, text=self.tr("ПОДБОРКА ВЛАДЕЛЬЦА"), text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 27, "bold")
        ).pack(anchor="w", pady=(1, 0))
        ctk.CTkLabel(
            title_box, text=self.tr("Автоматизация игрового события"), text_color=MUTED,
            font=ctk.CTkFont("Segoe UI", 12)
        ).pack(anchor="w", pady=(1, 0))

        self.refresh_button = ctk.CTkButton(
            header, text=self.tr("↻  Обновить окно"), width=142, height=36,
            fg_color=PANEL_ALT, hover_color=BORDER, text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            command=self.refresh_game_window,
        )
        self.refresh_button.pack(side="right", anchor="center")
        self.language_button = ctk.CTkButton(
            header, text=("RU" if self.language == "en" else "EN"), width=52, height=36,
            fg_color=PANEL_ALT, hover_color=BORDER, text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 11, "bold"), command=self.toggle_language,
        )
        self.language_button.pack(side="right", padx=(0, 8), anchor="center")

        # Game connection strip
        connection = ctk.CTkFrame(
            outer, fg_color=PANEL, corner_radius=14,
            border_width=1, border_color=BORDER,
        )
        connection.pack(fill="x", pady=(0, 14))
        connection_left = ctk.CTkFrame(connection, fg_color="transparent")
        connection_left.pack(side="left", fill="x", expand=True, padx=14, pady=11)
        ctk.CTkLabel(
            connection_left, text=self.tr("ИГРОВОЕ ОКНО"), text_color=MUTED,
            font=ctk.CTkFont("Segoe UI", 9, "bold"),
        ).pack(anchor="w")
        self.window_status_label = ctk.CTkLabel(
            connection_left, text=self.tr("Поиск HTGame.exe…"), text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 12, "bold"), anchor="w",
        )
        self.window_status_label.pack(anchor="w", pady=(2, 0))
        self.window_dot = ctk.CTkLabel(
            connection, text="●", text_color=YELLOW,
            font=ctk.CTkFont("Segoe UI", 18), width=24,
        )
        self.window_dot.pack(side="right", padx=14)

        # Current state
        state_card = ctk.CTkFrame(
            outer, fg_color=PANEL, corner_radius=16,
            border_width=1, border_color=BORDER,
        )
        state_card.pack(fill="x", pady=(0, 14))
        state_top = ctk.CTkFrame(state_card, fg_color="transparent")
        state_top.pack(fill="x", padx=16, pady=(14, 5))
        ctk.CTkLabel(
            state_top, text=self.tr("ТЕКУЩЕЕ СОСТОЯНИЕ"), text_color=MUTED,
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
        ).pack(side="left")
        self.status_badge = ctk.CTkLabel(
            state_top, text=self.tr("ГОТОВ К РАБОТЕ"), text_color=TEXT,
            fg_color=PANEL_ALT, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 10, "bold"), padx=11, pady=5,
        )
        self.status_badge.pack(side="right")
        self.stage_label = ctk.CTkLabel(
            state_card, text=self.tr("Ожидание запуска"), text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 14), anchor="w",
        )
        self.stage_label.pack(fill="x", padx=16, pady=(4, 15))

        # Metrics: one place per value, no duplicate progress line.
        metrics = ctk.CTkFrame(outer, fg_color="transparent")
        metrics.pack(fill="x", pady=(0, 14))
        metric_specs = [
            (self.tr("ЦИКЛЫ"), self.ui_metrics["cycles"], self.tr("Завершено"), ACCENT),
            (self.tr("ЭНЕРГИЯ"), self.ui_metrics["energy"], self.tr("Текущий запас"), GREEN),
            (self.tr("ДОХОД"), self.ui_metrics["income"], self.tr("Автоопределение уровня"), YELLOW),
        ]
        for index, (name, initial, subtitle, accent) in enumerate(metric_specs):
            card = ctk.CTkFrame(
                metrics, fg_color=PANEL, corner_radius=15,
                border_width=1, border_color=BORDER,
            )
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 7, 0))
            metrics.grid_columnconfigure(index, weight=1, uniform="metric")
            ctk.CTkLabel(
                card, text=name, text_color=MUTED,
                font=ctk.CTkFont("Segoe UI", 9, "bold"),
            ).pack(anchor="w", padx=13, pady=(12, 1))
            value = ctk.CTkLabel(
                card, text=initial, text_color=accent,
                font=ctk.CTkFont("Segoe UI", 22, "bold"),
            )
            value.pack(anchor="w", padx=13, pady=(2, 0))
            ctk.CTkLabel(
                card, text=subtitle, text_color=MUTED,
                font=ctk.CTkFont("Segoe UI", 10),
            ).pack(anchor="w", padx=13, pady=(0, 12))
            metric_key = {self.tr("ЦИКЛЫ"): "cycles", self.tr("ЭНЕРГИЯ"): "energy", self.tr("ДОХОД"): "income"}[name]
            self.metric_labels[metric_key] = value

        # Main controls
        controls = ctk.CTkFrame(outer, fg_color="transparent")
        controls.pack(fill="x", pady=(0, 12))
        self.toggle_button = ctk.CTkButton(
            controls, text=self.tr("▶  Запустить / Пауза  ·  F6"), height=47,
            fg_color=ACCENT, hover_color="#5676E8", text_color="#FFFFFF",
            font=ctk.CTkFont("Segoe UI", 13, "bold"), corner_radius=12,
            command=self.toggle_run_pause,
        )
        self.toggle_button.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.stop_button = ctk.CTkButton(
            controls, text=self.tr("■  Стоп  ·  F7"), height=47, width=145,
            fg_color="#39202B", hover_color="#542A39", text_color="#FFADB8",
            font=ctk.CTkFont("Segoe UI", 13, "bold"), corner_radius=12,
            command=self.stop,
        )
        self.stop_button.pack(side="left", padx=(6, 0))

        self.ocr_button = ctk.CTkButton(
            outer, text=self.tr("Проверить распознавание"), height=34,
            fg_color="transparent", hover_color=PANEL_ALT,
            border_width=1, border_color=BORDER, text_color=MUTED,
            font=ctk.CTkFont("Segoe UI", 11),
            command=self.test_ocr,
        )
        self.ocr_button.pack(fill="x", pady=(0, 12))

        # Hotkeys
        hotkeys = ctk.CTkFrame(outer, fg_color=PANEL_ALT, corner_radius=12)
        hotkeys.pack(fill="x", pady=(0, 14))
        hotkey_row = ctk.CTkFrame(hotkeys, fg_color="transparent")
        hotkey_row.pack(fill="x", padx=13, pady=10)
        ctk.CTkLabel(
            hotkey_row, text="F6", width=42, height=27, corner_radius=7,
            fg_color="#263A68", text_color="#DCE5FF",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            hotkey_row, text=self.tr("Запуск / пауза"), text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 11),
        ).pack(side="left", padx=(8, 20))
        ctk.CTkLabel(
            hotkey_row, text="F7", width=42, height=27, corner_radius=7,
            fg_color="#4A2632", text_color="#FFDDE2",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            hotkey_row, text=self.tr("Остановить"), text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 11),
        ).pack(side="left", padx=(8, 0))

        # Log
        log_header = ctk.CTkFrame(outer, fg_color="transparent")
        log_header.pack(fill="x", pady=(0, 7))
        ctk.CTkLabel(
            log_header, text=self.tr("ЖУРНАЛ"), text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            log_header, text=self.tr("Последние действия"), text_color=MUTED,
            font=ctk.CTkFont("Segoe UI", 10),
        ).pack(side="right")
        self.log_text = ctk.CTkTextbox(
            outer, height=205, corner_radius=12,
            fg_color="#080D18", border_width=1, border_color=BORDER,
            text_color="#CAD4E5", font=ctk.CTkFont("Consolas", 10),
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="normal")
        for stamp, message in self.log_history:
            self.log_text.insert("end", f"{stamp}  ·  {self.tr(message)}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # ----------------------------- UI HELPERS -----------------------------
    def log(self, message: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_history.append((stamp, message))
        self.log_history = self.log_history[-300:]

        def write():
            if self.closed:
                return
            self.log_text.configure(state="normal")
            self.log_text.insert("end", f"{stamp}  ·  {self.tr(message)}\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

        if threading.current_thread() is threading.main_thread():
            write()
        else:
            self.root.after(0, write)

    def set_status(self, status: str, stage: str | None = None):
        self.current_status = status
        if stage is not None:
            self.current_stage = stage
        def update():
            if self.closed:
                return
            if "ПАУЗА" in status:
                color = YELLOW
                fg = "#3A321F"
            elif any(word in status for word in ("ОШИБКА", "ОСТАНОВЛЕНО", "ОСТАНОВКА", "АВАРИЙНАЯ")):
                color = RED
                fg = "#3B202B"
            elif any(word in status for word in ("РАБОТАЕТ", "ЗАПУСК", "ФАРМ", "ПОЛУЧАЮ", "ОТКРЫВАЮ", "ПРОВЕРКА", "ЗАВЕРШАЮ")):
                color = GREEN
                fg = "#18382F"
            elif "ЗАКОНЧИЛАСЬ" in status or "ЗАВЕРШЕНО" in status:
                color = YELLOW
                fg = "#3A321F"
            else:
                color = TEXT
                fg = PANEL_ALT
            self.status_badge.configure(text=self.tr(status), text_color=color, fg_color=fg)
            if stage is not None:
                self.stage_label.configure(text=self.tr(stage))

        self.root.after(0, update)

    def set_metric(self, metric: str, value: str):
        self.ui_metrics[metric] = value
        def update():
            if not self.closed and metric in self.metric_labels:
                self.metric_labels[metric].configure(text=value)
        self.root.after(0, update)

    def set_stage(self, text: str):
        self.current_stage = text
        self.root.after(0, lambda: self.stage_label.configure(text=self.tr(text)) if not self.closed else None)

    def set_window_status(self, text: str, found: bool):
        def update():
            if self.closed:
                return
            self.window_status_label.configure(text=self.tr(text))
            self.window_dot.configure(text_color=GREEN if found else RED)
        if threading.current_thread() is threading.main_thread():
            update()
        else:
            self.root.after(0, update)

    # ------------------------------ HOTKEYS --------------------------------
    def _start_hotkeys(self):
        if keyboard is None:
            self.log("Глобальные хоткеи недоступны. Кнопки GUI остаются доступны.")
            return
        try:
            def on_press(key):
                if key == keyboard.Key.f6:
                    name, callback = "F6", self.toggle_run_pause
                elif key == keyboard.Key.f7:
                    name, callback = "F7", self.stop
                else:
                    return
                now = time.monotonic()
                with self.hotkey_lock:
                    if now - self.last_hotkey_time.get(name, 0) < 0.45:
                        return
                    self.last_hotkey_time[name] = now
                if not self.closed:
                    self.root.after(0, callback)

            self.hotkey_listener = keyboard.Listener(on_press=on_press)
            self.hotkey_listener.daemon = True
            self.hotkey_listener.start()
            self.log("Глобальные F6 / F7 активны.")
        except Exception as exc:
            self.log(f"Не удалось включить глобальные хоткеи: {exc}")

    # ------------------------------- CONTROL -------------------------------
    def toggle_run_pause(self):
        if self.worker_thread and self.worker_thread.is_alive():
            if self.pause_event.is_set():
                self.pause_event.clear()
                self.set_status("РАБОТАЕТ", "Продолжаю текущий цикл")
                self.log("Пауза снята.")
            else:
                self.pause_event.set()
                self.set_status("ПАУЗА", "Автоматизация приостановлена. Нажми F6 для продолжения.")
                self.log("Пауза включена.")
            return

        self.stop_event.clear()
        self.pause_event.clear()
        self.cycle_count = 0
        self.set_metric("cycles", "0")
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        self.set_status("ЗАПУСК", "Подготовка первого цикла")
        self.log("Автоматизация запущена.")

    def stop(self):
        self.stop_event.set()
        self.pause_event.clear()
        if not (self.worker_thread and self.worker_thread.is_alive()):
            self.set_status("ОСТАНОВЛЕНО", "Автоматизация не запущена")
        else:
            self.set_status("ОСТАНОВКА", "Завершаю текущую операцию")
        self.log("Получена команда остановки.")

    def close(self):
        self.closed = True
        self.stop_event.set()
        self.pause_event.clear()
        try:
            if self.hotkey_listener:
                self.hotkey_listener.stop()
        except Exception:
            pass
        self.root.destroy()

    # --------------------------- WINDOW BINDING -----------------------------
    def refresh_game_window(self, silent=False):
        if psutil is None:
            self.game_hwnd = None
            self.set_window_status("Не установлен psutil", False)
            if not silent:
                self.log("Не найден psutil. Проверь requirements.txt.")
            return None

        wanted = TARGET_EXE.lower()
        matches = []

        if os.name == "nt":
            if win32gui is None or win32process is None:
                self.game_hwnd = None
                self.set_window_status("Не установлены компоненты Windows", False)
                if not silent:
                    self.log("Не найдены pywin32-компоненты. Проверь requirements.txt.")
                return None

            def enum_callback(hwnd, _):
                try:
                    if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
                        return True
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if psutil.Process(pid).name().lower() != wanted:
                        return True
                    left, top, right, bottom = win32gui.GetClientRect(hwnd)
                    width, height = right - left, bottom - top
                    if width < 400 or height < 300:
                        return True
                    title = win32gui.GetWindowText(hwnd)
                    matches.append((hwnd, pid, width * height, title, width, height))
                except Exception:
                    pass
                return True

            try:
                win32gui.EnumWindows(enum_callback, None)
                foreground = win32gui.GetForegroundWindow()
            except Exception as exc:
                self.set_window_status("Ошибка поиска окна", False)
                if not silent:
                    self.log(f"Ошибка поиска окна {wanted}: {exc}")
                return None

        elif sys.platform.startswith("linux"):
            if xdisplay is None:
                self.game_hwnd = None
                self.set_window_status("Не установлен python-xlib", False)
                if not silent:
                    self.log("Для Linux требуется python-xlib и графическая сессия X11.")
                return None

            dpy = None
            try:
                dpy = xdisplay.Display()
                root = dpy.screen().root
                pid_atom = dpy.intern_atom("_NET_WM_PID")
                name_atom = dpy.intern_atom("_NET_WM_NAME")
                active_atom = dpy.intern_atom("_NET_ACTIVE_WINDOW")
                stack = list(root.query_tree().children)
                seen = set()
                while stack:
                    window = stack.pop()
                    if window.id in seen:
                        continue
                    seen.add(window.id)
                    try:
                        stack.extend(window.query_tree().children)
                        if window.get_attributes().map_state != X.IsViewable:
                            continue
                        pid_prop = window.get_full_property(pid_atom, X.AnyPropertyType)
                        if pid_prop is None or not len(pid_prop.value):
                            continue
                        pid = int(pid_prop.value[0])
                        try:
                            process = psutil.Process(pid)
                            process_names = {process.name().lower()}
                            try:
                                process_names.add(os.path.basename(process.exe()).lower())
                            except Exception:
                                pass
                            try:
                                process_names.update(
                                    os.path.basename(arg).lower()
                                    for arg in process.cmdline() if arg
                                )
                            except Exception:
                                pass
                            if wanted not in process_names:
                                continue
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            continue

                        geometry = window.get_geometry()
                        width, height = int(geometry.width), int(geometry.height)
                        if width < 400 or height < 300:
                            continue
                        coords = root.translate_coords(window, 0, 0)
                        title_prop = window.get_full_property(name_atom, X.AnyPropertyType)
                        title = ""
                        if title_prop is not None:
                            value = title_prop.value
                            title = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)
                        if not title:
                            legacy_title = window.get_wm_name() or ""
                            title = legacy_title.decode("utf-8", errors="replace") if isinstance(legacy_title, bytes) else str(legacy_title)
                        matches.append((
                            int(window.id), pid, width * height, title,
                            width, height, int(coords.x), int(coords.y)
                        ))
                    except Exception:
                        continue

                active_prop = root.get_full_property(active_atom, X.AnyPropertyType)
                foreground = int(active_prop.value[0]) if active_prop is not None and len(active_prop.value) else None
            except Exception as exc:
                self.set_window_status("Ошибка поиска окна X11", False)
                if not silent:
                    self.log(f"Не удалось найти окно {wanted} через X11: {exc}")
                return None
            finally:
                if dpy is not None:
                    try:
                        dpy.close()
                    except Exception:
                        pass
        else:
            self.game_hwnd = None
            self.set_window_status("Платформа не поддерживается", False)
            if not silent:
                self.log("Поддерживаются Windows и Linux с X11. Wayland-only не поддерживается.")
            return None

        if not matches:
            self.game_hwnd = None
            self.game_pid = None
            self.set_window_status(f"{TARGET_EXE} не найден", False)
            if not silent:
                self.log(f"Окно {TARGET_EXE} не найдено. Запусти игру и обнови окно.")
            return None

        selected = next((item for item in matches if item[0] == foreground), None)
        if selected is None:
            selected = max(matches, key=lambda item: item[2])
        hwnd, pid, _, title, width, height = selected[:6]
        self.game_hwnd, self.game_pid = hwnd, pid
        self.set_window_status(f"{title or TARGET_EXE}  ·  {width} × {height}", True)
        if not silent:
            self.log(f"Привязано окно {TARGET_EXE}, PID {pid}, область {width}×{height}.")
        return hwnd

    def _linux_window_exists(self, hwnd):
        if xdisplay is None:
            return False
        dpy = None
        try:
            dpy = xdisplay.Display()
            window = dpy.create_resource_object("window", int(hwnd))
            return window.get_attributes().map_state == X.IsViewable
        except Exception:
            return False
        finally:
            if dpy is not None:
                try:
                    dpy.close()
                except Exception:
                    pass

    def _get_game_hwnd(self):
        if self.game_hwnd:
            if os.name == "nt" and win32gui is not None and win32gui.IsWindow(self.game_hwnd):
                return self.game_hwnd
            if sys.platform.startswith("linux") and self._linux_window_exists(self.game_hwnd):
                return self.game_hwnd
        hwnd = self.refresh_game_window(silent=True)
        if not hwnd:
            raise RuntimeError(f"Окно {TARGET_EXE} не найдено. Открой игру и нажми «Обновить окно».")
        return hwnd

    def _client_geometry(self):
        hwnd = self._get_game_hwnd()
        if os.name == "nt":
            left, top, right, bottom = win32gui.GetClientRect(hwnd)
            width, height = right - left, bottom - top
            screen_left, screen_top = win32gui.ClientToScreen(hwnd, (0, 0))
        else:
            dpy = xdisplay.Display()
            try:
                window = dpy.create_resource_object("window", int(hwnd))
                geometry = window.get_geometry()
                coords = dpy.screen().root.translate_coords(window, 0, 0)
                width, height = int(geometry.width), int(geometry.height)
                screen_left, screen_top = int(coords.x), int(coords.y)
            finally:
                dpy.close()
        if width <= 0 or height <= 0:
            raise RuntimeError("У HTGame.exe нет доступной клиентской области. Возможно, окно свёрнуто.")
        return hwnd, screen_left, screen_top, width, height

    def _bring_game_to_front(self):
        hwnd = self._get_game_hwnd()
        if os.name == "nt":
            foreground = win32gui.GetForegroundWindow()
            try:
                foreground_root = win32gui.GetAncestor(foreground, win32con.GA_ROOT)
            except Exception:
                foreground_root = foreground
            if foreground_root == hwnd and not win32gui.IsIconic(hwnd):
                return hwnd
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            try:
                win32gui.SetForegroundWindow(hwnd)
                win32gui.BringWindowToTop(hwnd)
            except Exception:
                pass
            time.sleep(0.20)
            foreground = win32gui.GetForegroundWindow()
            try:
                foreground_root = win32gui.GetAncestor(foreground, win32con.GA_ROOT)
            except Exception:
                foreground_root = foreground
            if foreground_root != hwnd:
                raise RuntimeError("Не удалось активировать HTGame.exe. Переключись в окно игры и повтори.")
            return hwnd

        dpy = xdisplay.Display()
        try:
            root = dpy.screen().root
            active_atom = dpy.intern_atom("_NET_ACTIVE_WINDOW")
            active = root.get_full_property(active_atom, X.AnyPropertyType)
            active_id = int(active.value[0]) if active is not None and len(active.value) else None
            if active_id == int(hwnd):
                return hwnd
            try:
                subprocess.run(
                    ["wmctrl", "-ia", hex(int(hwnd))],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    check=False, timeout=2,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
            try:
                window = dpy.create_resource_object("window", int(hwnd))
                window.configure(stack_mode=X.Above)
                window.set_input_focus(X.RevertToParent, X.CurrentTime)
                dpy.sync()
            except Exception:
                pass
            time.sleep(0.25)
            active = root.get_full_property(active_atom, X.AnyPropertyType)
            active_id = int(active.value[0]) if active is not None and len(active.value) else None
            if active_id is not None and active_id != int(hwnd):
                raise RuntimeError("Не удалось активировать окно игры. Переключись на игру и повтори.")
            return hwnd
        finally:
            dpy.close()

    def _capture_client_image(self):
        self._bring_game_to_front()
        hwnd, screen_left, screen_top, width, height = self._client_geometry()
        if os.name == "nt":
            image = ImageGrab.grab(
                bbox=(screen_left, screen_top, screen_left + width, screen_top + height),
                all_screens=True,
            )
        else:
            # PyAutoGUI uses the X11 screenshot backend (scrot is installed by the package).
            image = pyautogui.screenshot(region=(screen_left, screen_top, width, height))
        if image.size != (width, height):
            image = image.resize((width, height), Image.Resampling.LANCZOS)
        return image, hwnd, width, height

    # -------------------------------- OCR -----------------------------------
    def _read_ratio(
        self,
        region,
        debug_name="ocr",
        expected_max: int | None = None,
        min_max: int = 1,
    ) -> tuple[int | None, int | None, str]:
        """Read a changing current/maximum counter using OCR consensus.

        A partial match such as 70/1 must not be accepted. The maximum is
        static during one event, so it must be recognized consistently by at
        least two independent preprocessing passes before the ratio is trusted.
        """
        client_image, hwnd, client_w, client_h = self._capture_client_image()
        x, y, width, height = region
        sx, sy = client_w / REFERENCE_WIDTH, client_h / REFERENCE_HEIGHT
        left = max(0, round(x * sx))
        top = max(0, round(y * sy))
        right = min(client_w, round((x + width) * sx))
        bottom = min(client_h, round((y + height) * sy))
        crop = client_image.crop((left, top, right, bottom))
        self.last_ocr_meta = (
            f"HTGame.exe HWND={hwnd}, клиент {client_w}x{client_h}, "
            f"область ({left},{top},{right-left},{bottom-top})"
        )

        if crop.width == 0 or crop.height == 0:
            return None, None, "пустая область захвата"

        try:
            debug_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                f"debug_{debug_name}_capture.png",
            )
            crop.save(debug_path)
            self.last_ocr_debug_path = debug_path
        except Exception:
            self.last_ocr_debug_path = ""

        if debug_name == "income":
            return self._read_income_parts(crop, min_max=min_max, expected_max=expected_max)

        rgb = crop.convert("RGB")
        gray = ImageOps.autocontrast(crop.convert("L"))
        red = ImageOps.autocontrast(rgb.getchannel("R"))
        green = ImageOps.autocontrast(rgb.getchannel("G"))
        blue = ImageOps.autocontrast(rgb.getchannel("B"))

        candidates = []
        for source in (gray, red, green, blue):
            for scale, psm in ((2, 7), (3, 7), (4, 8)):
                enlarged = source.resize(
                    (source.width * scale, source.height * scale),
                    Image.Resampling.LANCZOS,
                )
                candidates.append((enlarged, psm))

        # Also try a thresholded image; this often separates bright digits
        # from the dark textured counter background.
        threshold = gray.point(lambda value: 255 if value > 150 else 0)
        candidates.append((threshold.resize(
            (threshold.width * 4, threshold.height * 4), Image.Resampling.LANCZOS
        ), 7))

        parsed: list[tuple[int, int, str]] = []
        rejected: list[str] = []
        for candidate, psm in candidates:
            raw = pytesseract.image_to_string(
                candidate,
                config=(
                    f"--oem 3 --psm {psm} "
                    "-c tessedit_char_whitelist=0123456789/ "
                    "-c load_system_dawg=0 -c load_freq_dawg=0"
                ),
            ).strip()
            if not raw:
                continue
            compact = re.sub(r"[^0-9/]", "", raw)
            for match in re.finditer(r"(\d{1,6})/(\d{1,6})", compact):
                current, maximum = int(match.group(1)), int(match.group(2))
                if maximum < min_max or maximum <= 0 or current > maximum:
                    rejected.append(raw)
                    continue
                if expected_max is not None and maximum != expected_max:
                    rejected.append(raw)
                    continue
                parsed.append((current, maximum, raw))

        if not parsed:
            return None, None, rejected[-1] if rejected else ""

        # A denominator appearing in only one OCR pass is not trusted.
        denominator_votes: dict[int, int] = {}
        for _, maximum, _ in parsed:
            denominator_votes[maximum] = denominator_votes.get(maximum, 0) + 1
        best_max, votes = max(denominator_votes.items(), key=lambda item: item[1])
        if votes < 2:
            last_raw = parsed[-1][2]
            return None, None, f"{last_raw} (цель не подтверждена несколькими OCR-проходами)"

        confirmed = [item for item in parsed if item[1] == best_max]
        # Prefer the largest valid numerator to avoid dropping leading digits
        # when one pass sees e.g. 70 and another correctly sees 1270.
        current, maximum, raw = max(confirmed, key=lambda item: item[0])
        return current, maximum, raw


    def _read_income_parts(
        self, crop: Image.Image, min_max: int = 100, expected_max: int | None = None
    ) -> tuple[int | None, int | None, str]:
        """Read numerator and level target separately from their distinct screen colors.

        The current income is yellow and the level target is white. Separating
        the colored fields prevents the animated numerator or slash from being
        merged into the target (the old failure could turn 1270/1900 into 70/1).
        """
        rgb = crop.convert("RGB")
        width, height = rgb.size

        # Keep only yellow pixels for the animated current-income value.
        yellow_mask = Image.new("L", (width, height), 0)
        source_pixels = rgb.load()
        mask_pixels = yellow_mask.load()
        for y in range(height):
            for x in range(width):
                red, green, blue = source_pixels[x, y]
                if (
                    red > 120 and green > 80 and blue < 120
                    and red > green * 1.10 and green > blue * 1.25
                ):
                    mask_pixels[x, y] = 255

        # The white target starts after the slash. Crop just that right-hand
        # part so the changing yellow numerator cannot become a leading digit.
        target_crop = crop.crop((round(width * 0.54), 0, width, height))
        target_gray = ImageOps.autocontrast(target_crop.convert("L"))

        def read_digits(image: Image.Image, scales, psms):
            values: list[tuple[int, str]] = []
            base = ImageOps.autocontrast(image.convert("L"))
            for scale in scales:
                enlarged = base.resize(
                    (base.width * scale, base.height * scale),
                    Image.Resampling.LANCZOS,
                )
                for psm in psms:
                    raw = pytesseract.image_to_string(
                        enlarged,
                        config=(
                            f"--oem 3 --psm {psm} "
                            "-c tessedit_char_whitelist=0123456789 "
                            "-c load_system_dawg=0 -c load_freq_dawg=0"
                        ),
                    ).strip()
                    for token in re.findall(r"\d{1,6}", raw):
                        values.append((int(token), raw))
            return values

        target_candidates = read_digits(target_gray, scales=(2, 3, 4), psms=(7, 8, 13))
        target_candidates = [
            item for item in target_candidates
            if item[0] >= min_max and (expected_max is None or item[0] == expected_max)
        ]
        target_votes: dict[int, int] = {}
        for target_value, _ in target_candidates:
            target_votes[target_value] = target_votes.get(target_value, 0) + 1
        if not target_votes:
            return None, None, "не удалось отдельно распознать целевой лимит"

        target, votes = max(target_votes.items(), key=lambda item: item[1])
        if votes < 2:
            raw = target_candidates[-1][1]
            return None, None, f"цель не подтверждена несколькими OCR-проходами: {raw!r}"

        current_candidates = read_digits(yellow_mask, scales=(2, 3, 4, 5), psms=(6, 7))
        valid_current = [value for value, _ in current_candidates if value <= target]
        if not valid_current:
            return None, target, "целевой лимит найден, текущее значение дохода не распознано"

        # Some OCR passes may omit a leading digit. Prefer the largest valid
        # result, but never allow it to exceed the independently-read target.
        current = max(valid_current)
        return current, target, f"{current}/{target}; target votes={votes}"

    def read_income(self):
        # The denominator is the level-specific target (for example 1100 or 1900).
        # Detect it from the live counter instead of assuming one fixed difficulty.
        current, maximum, raw = self._read_ratio(
            INCOME_REGION, "income", expected_max=None, min_max=MIN_INCOME_TARGET
        )
        if current is not None and maximum is not None:
            self.set_metric("income", f"{current:,} / {maximum:,}")
        return current, maximum, raw

    def read_energy(self):
        current, maximum, raw = self._read_ratio(ENERGY_REGION, "energy")
        if current is not None:
            self.set_metric("energy", f"{current} / {maximum}")
        return current, maximum, raw

    def test_ocr(self):
        def run_test():
            try:
                energy, energy_max, energy_raw = self.read_energy()
                energy_meta = self.last_ocr_meta
                energy_debug = self.last_ocr_debug_path
                income, income_max, income_raw = self.read_income()
                income_meta = self.last_ocr_meta
                income_debug = self.last_ocr_debug_path
                self.log(f"Тест энергии: {energy}/{energy_max}; OCR: {energy_raw!r}; {energy_meta}")
                if energy is None and energy_debug:
                    self.log(f"Область энергии: {energy_debug}")
                self.log(f"Тест дохода: {income}/{income_max}; OCR: {income_raw!r}; {income_meta}")
                if income is None and income_debug:
                    self.log(f"Область дохода: {income_debug}")
            except Exception as exc:
                self.log(f"Ошибка проверки OCR: {exc}")

        threading.Thread(target=run_test, daemon=True).start()

    # ----------------------------- AUTOMATION -------------------------------
    def _point(self, name):
        if name not in DEFAULT_POINTS:
            raise ValueError(f"Неизвестная точка клика: {name}")
        hwnd, _, _, client_w, client_h = self._client_geometry()
        reference_x, reference_y = DEFAULT_POINTS[name]
        x = round(reference_x * client_w / REFERENCE_WIDTH)
        y = round(reference_y * client_h / REFERENCE_HEIGHT)
        if os.name == "nt":
            return win32gui.ClientToScreen(hwnd, (x, y))
        _, screen_left, screen_top, _, _ = self._client_geometry()
        return screen_left + x, screen_top + y

    def _wait(self, seconds: float) -> bool:
        remaining = seconds
        while remaining > 0:
            if self.stop_event.is_set():
                return False
            if self.pause_event.is_set():
                time.sleep(0.1)
                continue
            step = min(0.1, remaining)
            time.sleep(step)
            remaining -= step
        return not self.stop_event.is_set()

    def _click(self, name):
        while self.pause_event.is_set() and not self.stop_event.is_set():
            time.sleep(0.1)
        if self.stop_event.is_set():
            return False
        self._bring_game_to_front()
        pyautogui.click(*self._point(name))
        return not self.stop_event.is_set()

    def _worker(self):
        try:
            hwnd = self._get_game_hwnd()
            self._bring_game_to_front()
            _, _, _, client_w, client_h = self._client_geometry()
            self.log(f"Окно подключено: HWND={hwnd}, область {client_w}×{client_h}.")

            energy_ocr_failures = 0
            while not self.stop_event.is_set():
                if self.pause_event.is_set():
                    self.set_status("ПАУЗА", "Ожидаю F6 для продолжения")
                    while self.pause_event.is_set() and not self.stop_event.is_set():
                        time.sleep(0.1)
                    continue

                self.set_status("ПРОВЕРКА ЭНЕРГИИ", "Проверяю, хватит ли энергии на следующий полный цикл")
                energy, energy_max, raw = self.read_energy()
                if energy is None:
                    energy_ocr_failures += 1
                    meta = self.last_ocr_meta
                    debug_path = self.last_ocr_debug_path
                    self.log(f"Не удалось прочитать энергию ({raw!r}; {meta}). Попытка {energy_ocr_failures}/{MAX_ENERGY_OCR_FAILURES}.")
                    if debug_path:
                        self.log(f"Снимок области OCR: {debug_path}")
                    if energy_ocr_failures >= MAX_ENERGY_OCR_FAILURES:
                        self.set_status("ОШИБКА OCR ЭНЕРГИИ", "Не удалось определить запас энергии. Проверь debug_energy_capture.png.")
                        self.log("Автоматизация остановлена без кликов: значение энергии не подтверждено.")
                        return
                    if not self._wait(ENERGY_RETRY_INTERVAL):
                        break
                    continue

                energy_ocr_failures = 0
                self.log(f"Запас энергии перед циклом: {energy}/{energy_max}.")
                if energy < MINIMUM_ENERGY_PER_CYCLE or energy <= 0:
                    self.log(f"Для следующего цикла нужно не менее {MINIMUM_ENERGY_PER_CYCLE} энергии.")
                    self.set_status("ЭНЕРГИЯ ЗАКОНЧИЛАСЬ", f"Осталось {energy}. Новые циклы остановлены.")
                    return

                self.set_status("ОТКРЫВАЮ МАГАЗИН", "Открываю магазин события")
                self._click("Магазин")
                if not self._wait(2.0):
                    break

                self.set_status("ФАРМ ДОХОДА", "Определяю целевой доход по уровню")
                self.log("Магазин открыт. Начинаю нажимать молоток.")
                last_ocr = 0.0
                last_seen = time.monotonic()
                reached = False
                reached_confirmations = 0
                active_income_target = None

                while not self.stop_event.is_set():
                    while self.pause_event.is_set() and not self.stop_event.is_set():
                        self.set_status("ПАУЗА", "Фарм приостановлен. F6 продолжит текущий цикл.")
                        time.sleep(0.1)
                    if self.stop_event.is_set():
                        break

                    self._click("Молоток")
                    now = time.monotonic()
                    if now - last_ocr >= OCR_INTERVAL:
                        current, maximum, raw = self.read_income()
                        last_ocr = now
                        if current is not None and maximum is not None:
                            last_seen = now
                            if active_income_target != maximum:
                                active_income_target = maximum
                                self.log(f"Определён целевой доход текущего уровня: {maximum}.")
                                self.set_stage(f"Накопление целевого дохода: {maximum}")
                            else:
                                self.set_stage(f"Накопление целевого дохода: {maximum}")
                            if current >= maximum:
                                reached_confirmations += 1
                                if reached_confirmations >= 2:
                                    reached = True
                                    self.log(
                                        f"Целевой показатель подтверждён повторно: "
                                        f"{current}/{maximum}."
                                    )
                                    break
                                self.log(
                                    f"Порог {current}/{maximum} распознан. "
                                    "Проверяю повторно, чтобы исключить кадр анимации."
                                )
                            else:
                                reached_confirmations = 0
                        elif now - last_seen > 15:
                            self.log(f"Распознавание дохода не работает более 15 секунд. Последний результат: {raw!r}.")
                            self.set_status("ОШИБКА РАСПОЗНАВАНИЯ", "Значение дохода не читается. Проверь debug_income_capture.png.")
                            return
                    if not self._wait(CLICK_INTERVAL):
                        break

                if self.stop_event.is_set() or not reached:
                    break

                self.set_status("ЗАВЕРШАЮ ИСПЫТАНИЕ", "Нажимаю Esc и ожидаю экран награды")
                self._bring_game_to_front()
                pyautogui.press("esc")
                if not self._wait(2.0):
                    break

                self.set_status("ПОЛУЧАЮ НАГРАДУ", "Забираю награду за испытание")
                self._click("Получить")
                if not self._wait(3.0):
                    break

                self.cycle_count += 1
                self.set_metric("cycles", str(self.cycle_count))
                self.log(f"Цикл №{self.cycle_count} завершён.")

            if self.stop_event.is_set():
                self.set_status("ОСТАНОВЛЕНО", "Автоматизация остановлена пользователем")
            else:
                self.set_status("ЗАВЕРШЕНО", "Работа завершена")
        except pyautogui.FailSafeException:
            self.stop_event.set()
            self.set_status("АВАРИЙНАЯ ОСТАНОВКА", "Сработал аварийный механизм PyAutoGUI")
            self.log("Аварийная остановка: курсор перемещён в левый верхний угол.")
        except Exception as exc:
            self.stop_event.set()
            self.set_status("ОШИБКА", str(exc))
            self.log(f"Ошибка: {type(exc).__name__}: {exc}")


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    OwnerSelectionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
