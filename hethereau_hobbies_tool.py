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
import io
import tkinter as tk
import webbrowser
from datetime import datetime

import customtkinter as ctk
import pyautogui
import pytesseract
from PIL import Image, ImageOps, ImageGrab, ImageTk
import resvg_py
from hht_ocr import select_ratio_candidate

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
APP_TITLE = "Hethereau Hobbies Tool (HHT)"
try:
    from hht_build_info import APP_VERSION, APP_CHANNEL
except ImportError:
    APP_VERSION, APP_CHANNEL = "0.3.0-dev", "dev"
APP_GITHUB_URL = "https://github.com/M1ST0R/hethereau-hobbies-tool"
SUPPORTED_LANGUAGES = {"en": "English", "ru": "Русский"}
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
CLICK_INTERVAL = 0.05
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
    "УВЛЕЧЕНИЯ ЭТЕРО": "HETHEREAU HOBBIES TOOL",
    "ПОДБОРКА ВЛАДЕЛЬЦА": "OWNER'S SELECTION MODULE",
    "Автоматизация игрового события": "NTE hobby automation",
    "HETHEREAU HOBBIES TOOL": "HETHEREAU HOBBIES TOOL",
    "Автоматизация игровых хобби NTE": "NTE hobby automation",
    "Текущий модуль: Подборка владельца": "Current module: Owner's Selection",
    "Посмотреть логи": "View logs",
    "О программе": "About",
    "Тёмная тема": "Dark theme",
    "Светлая тема": "Light theme",
    "Логи": "Logs",
    "Копировать": "Copy",
    "Очистить": "Clear",
    "Закрыть": "Close",
    "Открой событие «Подборка владельца» перед запуском.": "Open the Owner's Selection event before starting.",
    "Утилита для автоматизации игровых хобби в Neverness to Everness.": "A desktop toolkit for automating hobbies in Neverness to Everness.",
    "Сейчас доступен модуль «Подборка владельца».": "The Owner's Selection module is currently available.",
    "Новые занятия, включая рыбалку, будут добавляться отдельными модулями.": "New activities, including fishing, will be added as separate modules.",
    "Версия": "Version",
    "Открыть GitHub": "Open GitHub",
    "Владелец": "Owner",
    "РАЗДЕЛЫ": "WORKSPACE",
    "Автоматизация события «Подборка владельца»": "Owner's Selection automation",
    "Журнал событий": "Activity log",
    "История работы и диагностика автоматизации": "Automation history and diagnostics",
    "Копировать выделенное": "Copy selection",
    "Копировать всё": "Copy all",
    "Очистить": "Clear",
    "записей": "entries",
    "Сначала выдели нужную часть журнала мышью.": "Select the log text you want to copy first.",
    "Выделенный фрагмент журнала скопирован.": "Selected log excerpt copied.",
    "Весь журнал скопирован.": "Full log copied.",
    "Development build": "Development build",
    "Release build": "Release build",
    "↻  Обновить окно": "↻  Refresh game window",
    "Обновить окно": "Refresh game window",
    "Запустить / Пауза · F6": "Start / Pause · F6",
    "Стоп · F7": "Stop · F7",
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
    "Сканировать доход и энергию": "Scan income and energy",
    "Запуск / пауза": "Start / pause",
    "Остановить": "Stop",
    "ЖУРНАЛ": "ACTIVITY LOG",
    "Последние действия": "Recent activity",
    "Программа готова. F6 — старт / пауза, F7 — остановка.": "Ready. F6 — start / pause, F7 — stop.",
    "Открой событие «Подборка владельца» перед запуском.": "Open the Hethereau “Owner's Selection” event before starting.",
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
    "Светлая тема включена.": "Light theme enabled.",
    "Тёмная тема включена.": "Dark theme enabled.",
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


# Add another language to SUPPORTED_LANGUAGES and provide its dictionary here.
# Any missing phrases fall back to English.
LANGUAGE_TRANSLATIONS = {
    "en": EN_TRANSLATIONS,
    "ru": {},
}


# ------------------------------- THEME -----------------------------------
THEME_PALETTES = {
    "dark": {
        "BG": "#0B1020", "PANEL": "#131C31", "PANEL_ALT": "#19243D",
        "BORDER": "#263653", "TEXT": "#F2F5FA", "MUTED": "#91A0B8",
        "ACCENT": "#6C8CFF", "ACCENT_HOVER": "#5676E8",
        "GREEN": "#24C78A", "RED": "#F06475", "YELLOW": "#F5C45E",
        "STOP_BG": "#39202B", "STOP_HOVER": "#542A39", "STOP_TEXT": "#FFADB8",
        "HOTKEY_START_BG": "#263A68", "HOTKEY_START_TEXT": "#DCE5FF",
        "HOTKEY_STOP_BG": "#4A2632", "HOTKEY_STOP_TEXT": "#FFDDE2",
        "LOG_BG": "#080D18", "LOG_TEXT": "#CAD4E5",
        "STATUS_PAUSE_BG": "#3A321F", "STATUS_ERROR_BG": "#3B202B",
        "STATUS_RUNNING_BG": "#18382F",
    },
    "light": {
        "BG": "#F1F4FA", "PANEL": "#FFFFFF", "PANEL_ALT": "#E7ECF5",
        "BORDER": "#D3DCEC", "TEXT": "#1D2942", "MUTED": "#65738C",
        "ACCENT": "#4F68C8", "ACCENT_HOVER": "#3F57B7",
        "GREEN": "#16845F", "RED": "#C8475D", "YELLOW": "#A87619",
        "STOP_BG": "#FBE8EC", "STOP_HOVER": "#F5D6DD", "STOP_TEXT": "#B43A52",
        "HOTKEY_START_BG": "#E2E9FC", "HOTKEY_START_TEXT": "#354FAD",
        "HOTKEY_STOP_BG": "#FBE5E9", "HOTKEY_STOP_TEXT": "#B43D55",
        "LOG_BG": "#F8FAFD", "LOG_TEXT": "#2B3852",
        "STATUS_PAUSE_BG": "#FFF2D7", "STATUS_ERROR_BG": "#FBE6E9",
        "STATUS_RUNNING_BG": "#E2F4EC",
    },
}


def apply_theme_palette(mode: str):
    """Set the shared widget palette from CustomTkinter's active appearance mode."""
    palette = THEME_PALETTES["light" if str(mode).lower() == "light" else "dark"]
    globals().update(palette)


def resource_path(relative_path: str) -> str:
    """Return an asset path that works both from source and in a PyInstaller bundle."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# Official Google Material Symbols Outlined glyphs shipped locally as SVG.
SYMBOL_NAMES = {
    "play_arrow", "pause", "stop", "refresh", "language", "desktop_windows",
    "info", "monitoring", "bolt", "payments", "check_circle", "warning",
    "error", "keyboard", "history", "fact_check", "dark_mode", "light_mode",
    "article", "open_in_new", "close", "sports_esports", "folder_open",
    "copy_all", "delete", "check",
}

# (light-mode tint, dark-mode tint); one consistent Outlined icon family.
SYMBOL_COLORS = {
    "normal": ("#17243B", "#F4F6FF"),
    "muted": ("#52627D", "#C2CCE0"),
    "accent": ("#3559C7", "#B5C4FF"),
    "success": ("#147A55", "#65E4B5"),
    "warning": ("#965D00", "#FFD27A"),
    "danger": ("#B82F49", "#FF9AA9"),
}


def ensure_windows_admin() -> bool:
    """Relaunch with UAC elevation on Windows; no elevation is needed on Linux."""
    if os.name != "nt":
        return True
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
    except Exception:
        pass

    if getattr(sys, "frozen", False):
        executable = sys.executable
        parameters = subprocess.list2cmdline(sys.argv[1:])
        working_directory = os.path.dirname(sys.executable)
    else:
        executable = sys.executable
        script_path = os.path.abspath(sys.argv[0] if sys.argv else __file__)
        parameters = subprocess.list2cmdline([script_path, *sys.argv[1:]])
        working_directory = os.path.dirname(script_path)

    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", executable, parameters, working_directory, 1
        )
    except Exception as exc:
        ctypes.windll.user32.MessageBoxW(
            None,
            f"{APP_TITLE} needs administrator privileges on Windows.\\n\\n{exc}",
            APP_TITLE,
            0x10,
        )
        return False

    if result > 32:
        # The elevated child process has been started; close this unelevated parent.
        return False

    ctypes.windll.user32.MessageBoxW(
        None,
        "Administrator privileges are required to send input to elevated applications.\\n"
        "Approve the Windows UAC prompt and launch HOST again.",
        APP_TITLE,
        0x10,
    )
    return False

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.015


class OwnerSelectionApp:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.language = self._load_language()
        self.theme_mode = self._load_theme()
        ctk.set_appearance_mode(self.theme_mode)
        apply_theme_palette(self.theme_mode)
        self.ui_metrics = {"cycles": "0", "energy": "—", "income": "—"}
        self.current_status = "ГОТОВ К РАБОТЕ"
        self.current_stage = "Ожидание запуска"
        self.log_history: list[tuple[str, str]] = []
        self.root.title(APP_TITLE)
        self.root.geometry("1080x800")
        self.root.minsize(900, 680)
        self.root.configure(fg_color=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._symbol_cache: dict[tuple[str, int, str], ctk.CTkImage] = {}
        self._symbol_svg: dict[str, str] = {}
        self._logo_pil: Image.Image | None = None
        self._window_icon_photo = None
        self._window_icon_photos: list[ImageTk.PhotoImage] = []
        self.log_text = None
        self.log_context_menu = None
        self._load_visual_assets()

        configure_tesseract()

        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.worker_thread: threading.Thread | None = None
        self.active_income_ocr_thread: threading.Thread | None = None
        self.hotkey_listener = None
        self.hotkey_lock = threading.Lock()
        self.last_hotkey_time: dict[str, float] = {}
        self.closed = False
        self.game_hwnd: int | None = None
        self.game_pid: int | None = None
        self.cycle_count = 0
        self.last_ocr_meta = ""
        self.last_ocr_debug_path = ""
        self.current_page = "owner"
        self.game_screen_context = "outside_event"
        self.rescan_requested = threading.Event()
        self.pause_scan_requested = threading.Event()
        self.last_pause_scan: dict | None = None
        self.last_resume_scan: dict | None = None
        self._stop_scan_lock = threading.Lock()
        self._stop_scan_pending = False
        self.worker_error: tuple[str, str] | None = None
        self.last_scan_error = ""

        self.metric_labels: dict[str, ctk.CTkLabel] = {}
        self._build_ui()
        self.refresh_game_window(silent=True)
        self._start_hotkeys()
        self.log("HHT готов. F6 — старт / пауза, F7 — остановка.")
        self.log("Открой событие «Подборка владельца» перед запуском.")


    def _load_visual_assets(self):
        """Load the optional HHT launcher icon and bundled Material Symbols Outlined glyphs."""
        icon_path = resource_path("assets/app_icon.png")
        if os.path.isfile(icon_path):
            try:
                self._logo_pil = Image.open(icon_path).convert("RGBA")
                # Supply multiple sizes so Windows uses a sharp icon in the
                # title bar, taskbar, Alt+Tab and high-DPI shell surfaces.
                self._window_icon_photos = [
                    ImageTk.PhotoImage(self._logo_pil.resize((size, size), Image.Resampling.LANCZOS))
                    for size in (16, 24, 32, 48, 64, 128, 256)
                ]
                self._window_icon_photo = self._window_icon_photos[-1]
                self.root.iconphoto(True, *self._window_icon_photos)
                ico_path = resource_path("assets/app_icon.ico")
                if os.name == "nt" and os.path.isfile(ico_path):
                    self.root.iconbitmap(ico_path)
            except Exception as exc:
                self._logo_pil = None
                self.log_history.append((
                    datetime.now().strftime("%H:%M:%S"),
                    f"Не удалось загрузить иконку приложения: {exc}",
                ))

        try:
            with open(resource_path("assets/icons/material_symbols_outlined.json"), "r", encoding="utf-8") as icon_file:
                self._symbol_svg = json.load(icon_file)
            missing = SYMBOL_NAMES.difference(self._symbol_svg)
            if missing:
                raise ValueError(f"Missing Material Symbols: {', '.join(sorted(missing))}")
        except Exception as exc:
            self._symbol_svg = {}
            self.log_history.append((
                datetime.now().strftime("%H:%M:%S"),
                f"Не удалось загрузить Material Symbols Outlined: {exc}",
            ))

    def symbol_image(self, name: str, size: int = 20, tone: str = "normal"):
        """Render and tint a genuine Material Symbols Outlined SVG for both themes."""
        cache_key = (name, size, tone)
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]
        svg_source = self._symbol_svg.get(name)
        if not svg_source:
            self.log_history.append((
                datetime.now().strftime("%H:%M:%S"),
                f"Material Symbol is unavailable: {name}",
            ))
            return None

        light_color, dark_color = SYMBOL_COLORS.get(tone, SYMBOL_COLORS["normal"])

        def render_icon(color: str) -> Image.Image:
            # resvg honours the original Material Symbols viewBox, including
            # its non-zero origin (0 -960 960 960). svglib cropped parts of
            # several glyphs because it treated negative coordinates as offsets.
            # Rasterize at 4x and let CTkImage downsample for crisp HiDPI display.
            png_data = resvg_py.svg_to_bytes(
                svg_string=svg_source,
                width=max(96, size * 4),
                height=max(96, size * 4),
            )
            rendered = Image.open(io.BytesIO(png_data)).convert("RGBA")
            alpha = rendered.getchannel("A")
            tinted = Image.new("RGBA", rendered.size, color)
            tinted.putalpha(alpha)
            return tinted

        try:
            icon_image = ctk.CTkImage(
                light_image=render_icon(light_color),
                dark_image=render_icon(dark_color),
                size=(size, size),
            )
        except Exception as exc:
            self.log_history.append((
                datetime.now().strftime("%H:%M:%S"),
                f"Не удалось отрисовать Material Symbol {name}: {exc}",
            ))
            return None

        self._symbol_cache[cache_key] = icon_image
        return icon_image

    def _config_path(self) -> str:
        """Use a persistent per-user configuration folder, not PyInstaller's temp bundle."""
        if os.name == "nt":
            base = os.environ.get("APPDATA") or os.path.expanduser("~")
            app_dir = os.path.join(base, "Hethereau Hobbies Tool")
        elif sys.platform.startswith("linux"):
            base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
            app_dir = os.path.join(base, "hethereau-hobbies-tool")
        else:
            app_dir = os.path.join(os.path.expanduser("~"), ".hethereau-hobbies-tool")

        os.makedirs(app_dir, exist_ok=True)
        return os.path.join(app_dir, "app_config.json")

    def _read_preferences(self) -> dict:
        try:
            with open(self._config_path(), "r", encoding="utf-8") as config_file:
                value = json.load(config_file)
                return value if isinstance(value, dict) else {}
        except Exception:
            return {}

    def _load_language(self) -> str:
        value = self._read_preferences().get("language", "en")
        return value if value in SUPPORTED_LANGUAGES else "en"

    def _load_theme(self) -> str:
        value = self._read_preferences().get("theme", "dark")
        return value if value in ("light", "dark") else "dark"

    def _save_preferences(self):
        try:
            preferences = self._read_preferences()
            preferences.update({"language": self.language, "theme": self.theme_mode})
            with open(self._config_path(), "w", encoding="utf-8") as config_file:
                json.dump(preferences, config_file, ensure_ascii=False, indent=2)
        except Exception as exc:
            self.log(f"Не удалось сохранить настройки интерфейса: {exc}")

    def tr(self, text: str) -> str:
        """Translate UI text to the selected language."""
        if self.language == "ru":
            return text
        catalog = LANGUAGE_TRANSLATIONS.get(self.language, {})
        translated = catalog.get(text, EN_TRANSLATIONS.get(text, text))
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

    def _close_auxiliary_windows(self):
        # Logs and About are embedded pages now; there are no Toplevel windows.
        return

    def _rebuild_ui(self):
        current_page = self.current_page
        for child in self.root.winfo_children():
            child.destroy()
        self.metric_labels = {}
        self._symbol_cache.clear()
        self.root.configure(fg_color=BG)
        self._build_ui()
        self.root.title(APP_TITLE)
        self._show_page(current_page)
        self.set_status(self.current_status, self.current_stage)
        for metric, value in self.ui_metrics.items():
            self.set_metric(metric, value)

    def _language_changed(self, display_name: str):
        self.language = next(
            (code for code, label in SUPPORTED_LANGUAGES.items() if label == display_name),
            "en",
        )
        self._save_preferences()
        self._rebuild_ui()
        self.log("Язык интерфейса изменён." if self.language == "ru" else "Interface language changed.")

    def _theme_changed(self):
        self.theme_mode = "dark" if self.theme_switch.get() == "dark" else "light"
        ctk.set_appearance_mode(self.theme_mode)
        apply_theme_palette(self.theme_mode)
        self._save_preferences()
        self._rebuild_ui()
        self.log("Тёмная тема включена." if self.theme_mode == "dark" else "Светлая тема включена.")

    # -------------------------------- UI ----------------------------------
    def _build_ui(self):
        self.app_shell = ctk.CTkFrame(self.root, fg_color=BG, corner_radius=0)
        self.app_shell.pack(fill="both", expand=True, padx=14, pady=14)
        self.sidebar = ctk.CTkFrame(self.app_shell, width=196, fg_color=PANEL,
            corner_radius=18, border_width=1, border_color=BORDER)
        self.sidebar.pack(side="left", fill="y", padx=(0, 14))
        self.sidebar.pack_propagate(False)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=15, pady=(19, 25))
        if self._logo_pil is not None:
            self._sidebar_logo = ctk.CTkImage(light_image=self._logo_pil,
                dark_image=self._logo_pil, size=(42, 42))
            ctk.CTkLabel(brand, text="", image=self._sidebar_logo).pack(side="left", padx=(0, 10))
        brand_text = ctk.CTkFrame(brand, fg_color="transparent")
        brand_text.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(brand_text, text="HETHEREAU", text_color=ACCENT,
            font=ctk.CTkFont("Segoe UI", 10, "bold")).pack(anchor="w")
        ctk.CTkLabel(brand_text, text="HOBBIES TOOL", text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 13, "bold")).pack(anchor="w")
        ctk.CTkLabel(self.sidebar, text=self.tr("РАЗДЕЛЫ"), text_color=MUTED,
            font=ctk.CTkFont("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=17, pady=(0, 9))

        nav_items = (("owner", "Владелец", "sports_esports"),
                     ("about", "О программе", "info"),
                     ("logs", "Логи", "article"))
        self.nav_buttons = {}
        for page_key, label, icon_name in nav_items:
            button = ctk.CTkButton(
                self.sidebar, text=self.tr(label),
                image=self.symbol_image(icon_name, 20, "normal"), compound="left", anchor="w",
                height=46, corner_radius=11, fg_color="transparent", hover_color=PANEL_ALT,
                text_color=TEXT, font=ctk.CTkFont("Segoe UI", 12, "bold"),
                command=lambda key=page_key: self._show_page(key),
            )
            button.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[page_key] = button

        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)
        ctk.CTkLabel(self.sidebar, text=f"v{APP_VERSION}", text_color=MUTED,
            font=ctk.CTkFont("Segoe UI", 9)).pack(side="bottom", pady=(0, 5))
        ctk.CTkLabel(self.sidebar, text="F6 START / PAUSE · F7 STOP", text_color=MUTED,
            font=ctk.CTkFont("Segoe UI", 8)).pack(side="bottom", pady=(0, 15))

        self.main_area = ctk.CTkFrame(self.app_shell, fg_color="transparent", corner_radius=0)
        self.main_area.pack(side="left", fill="both", expand=True)
        header = ctk.CTkFrame(self.main_area, fg_color="transparent")
        header.pack(fill="x", pady=(2, 13))
        header_title = ctk.CTkFrame(header, fg_color="transparent")
        header_title.pack(side="left", fill="x", expand=True)
        self.page_heading = ctk.CTkLabel(header_title, text=self.tr("Владелец"),
            text_color=TEXT, font=ctk.CTkFont("Segoe UI", 23, "bold"))
        self.page_heading.pack(anchor="w")
        self.page_subtitle = ctk.CTkLabel(header_title,
            text=self.tr("Автоматизация игровых хобби NTE"), text_color=MUTED,
            font=ctk.CTkFont("Segoe UI", 11))
        self.page_subtitle.pack(anchor="w", pady=(1, 0))

        self.refresh_button = ctk.CTkButton(header, text=self.tr("Обновить окно"),
            image=self.symbol_image("refresh", 17, "muted"), compound="left", width=132, height=36,
            fg_color=PANEL_ALT, hover_color=BORDER, text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 10, "bold"), command=self.refresh_game_window)
        self.refresh_button.pack(side="right", padx=(8, 0), anchor="center")
        ctk.CTkLabel(header, text="", image=self.symbol_image(
            "dark_mode" if self.theme_mode == "dark" else "light_mode", 18, "muted")
        ).pack(side="right", padx=(0, 2), anchor="center")
        self.theme_switch = ctk.CTkSwitch(header, text=self.tr("Тёмная тема"),
            onvalue="dark", offvalue="light", command=self._theme_changed,
            fg_color=BORDER, progress_color=ACCENT, button_color=TEXT,
            button_hover_color=ACCENT_HOVER, text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 10, "bold"))
        self.theme_switch.pack(side="right", padx=(10, 8), anchor="center")
        if self.theme_mode == "dark": self.theme_switch.select()
        else: self.theme_switch.deselect()

        language_box = ctk.CTkFrame(header, fg_color="transparent")
        language_box.pack(side="right", padx=(8, 0), anchor="center")
        ctk.CTkLabel(language_box, text="",
            image=self.symbol_image("language", 18, "muted")).pack(side="left", padx=(0, 5))
        self.language_menu = ctk.CTkOptionMenu(language_box,
            values=list(SUPPORTED_LANGUAGES.values()), command=self._language_changed,
            width=108, height=34, fg_color=PANEL_ALT, button_color=PANEL_ALT,
            button_hover_color=BORDER, dropdown_fg_color=PANEL,
            dropdown_hover_color=PANEL_ALT, dropdown_text_color=TEXT,
            text_color=TEXT, font=ctk.CTkFont("Segoe UI", 10, "bold"))
        self.language_menu.set(SUPPORTED_LANGUAGES.get(self.language, "English"))
        self.language_menu.pack(side="left")

        self.pages_container = ctk.CTkFrame(self.main_area, fg_color="transparent", corner_radius=0)
        self.pages_container.pack(fill="both", expand=True)
        self.page_frames = {
            "owner": ctk.CTkFrame(self.pages_container, fg_color="transparent", corner_radius=0),
            "about": ctk.CTkFrame(self.pages_container, fg_color="transparent", corner_radius=0),
            "logs": ctk.CTkFrame(self.pages_container, fg_color="transparent", corner_radius=0),
        }
        self.owner_page = self.page_frames["owner"]
        outer = ctk.CTkFrame(self.owner_page, fg_color="transparent", corner_radius=0)
        outer.pack(fill="both", expand=True)

        # Owner's Selection module
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
        self.connection_icon = ctk.CTkLabel(
            connection, text="", image=self.symbol_image("desktop_windows", 23, "muted"), width=30,
        )
        self.connection_icon.pack(side="right", padx=14)

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
        self.status_icon_label = ctk.CTkLabel(
            state_top, text="", image=self.symbol_image("info", 19, "accent"), width=25,
        )
        self.status_icon_label.pack(side="left", padx=(10, 0))
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
            (self.tr("ЦИКЛЫ"), self.ui_metrics["cycles"], self.tr("Завершено"), ACCENT, "monitoring", "accent"),
            (self.tr("ЭНЕРГИЯ"), self.ui_metrics["energy"], self.tr("Текущий запас"), GREEN, "bolt", "success"),
            (self.tr("ДОХОД"), self.ui_metrics["income"], self.tr("Автоопределение уровня"), YELLOW, "payments", "warning"),
        ]
        for index, (name, initial, subtitle, accent, icon_name, icon_tone) in enumerate(metric_specs):
            card = ctk.CTkFrame(
                metrics, fg_color=PANEL, corner_radius=15,
                border_width=1, border_color=BORDER,
            )
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 7, 0))
            metrics.grid_columnconfigure(index, weight=1, uniform="metric")
            metric_header = ctk.CTkFrame(card, fg_color="transparent")
            metric_header.pack(fill="x", padx=13, pady=(12, 1))
            ctk.CTkLabel(
                metric_header, text=name, text_color=MUTED,
                font=ctk.CTkFont("Segoe UI", 9, "bold"),
            ).pack(side="left")
            ctk.CTkLabel(
                metric_header, text="", image=self.symbol_image(icon_name, 19, icon_tone),
            ).pack(side="right")
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
            controls, text=self.tr("Запустить / Пауза · F6"),
            image=self.symbol_image("play_arrow", 22, "normal"), compound="left", height=47,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#FFFFFF",
            font=ctk.CTkFont("Segoe UI", 13, "bold"), corner_radius=12,
            command=self.toggle_run_pause,
        )
        self.toggle_button.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.stop_button = ctk.CTkButton(
            controls, text=self.tr("Стоп · F7"),
            image=self.symbol_image("stop", 19, "danger"), compound="left", height=47, width=145,
            fg_color=STOP_BG, hover_color=STOP_HOVER, text_color=STOP_TEXT,
            font=ctk.CTkFont("Segoe UI", 13, "bold"), corner_radius=12,
            command=self.stop,
        )
        self.stop_button.pack(side="left", padx=(6, 0))

        self.ocr_button = ctk.CTkButton(
            outer, text=self.tr("Сканировать доход и энергию"),
            image=self.symbol_image("fact_check", 18, "muted"), compound="left", height=34,
            fg_color="transparent", hover_color=PANEL_ALT,
            border_width=1, border_color=BORDER, text_color=MUTED,
            font=ctk.CTkFont("Segoe UI", 11),
            command=self.scan_state_manual,
        )
        self.ocr_button.pack(fill="x", pady=(0, 12))

        # Hotkeys
        hotkeys = ctk.CTkFrame(outer, fg_color=PANEL_ALT, corner_radius=12)
        hotkeys.pack(fill="x", pady=(0, 14))
        hotkey_row = ctk.CTkFrame(hotkeys, fg_color="transparent")
        hotkey_row.pack(fill="x", padx=13, pady=10)
        ctk.CTkLabel(
            hotkey_row, text="", image=self.symbol_image("keyboard", 20, "muted"),
        ).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(
            hotkey_row, text="F6", width=42, height=27, corner_radius=7,
            fg_color=HOTKEY_START_BG, text_color=HOTKEY_START_TEXT,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            hotkey_row, text=self.tr("Запуск / пауза"), text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 11),
        ).pack(side="left", padx=(8, 20))
        ctk.CTkLabel(
            hotkey_row, text="F7", width=42, height=27, corner_radius=7,
            fg_color=HOTKEY_STOP_BG, text_color=HOTKEY_STOP_TEXT,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            hotkey_row, text=self.tr("Остановить"), text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 11),
        ).pack(side="left", padx=(8, 0))

        self._build_about_page()
        self._build_logs_page()
        self._show_page(getattr(self, "current_page", "owner"))
    # ----------------------------- UI HELPERS -----------------------------
    def _show_page(self, page: str):
        if page not in self.page_frames: page = "owner"
        self.current_page = page
        for frame in self.page_frames.values(): frame.pack_forget()
        self.page_frames[page].pack(fill="both", expand=True)
        headings = {
            "owner": ("Владелец", "Автоматизация события «Подборка владельца»"),
            "about": ("О программе", "Hethereau Hobbies Tool"),
            "logs": ("Логи", "История работы и диагностика автоматизации"),
        }
        title, subtitle = headings[page]
        self.page_heading.configure(text=self.tr(title))
        self.page_subtitle.configure(text=self.tr(subtitle))
        for key, button in self.nav_buttons.items():
            active = key == page
            button.configure(fg_color=ACCENT if active else "transparent",
                hover_color=ACCENT_HOVER if active else PANEL_ALT,
                text_color="#FFFFFF" if active else TEXT)

    def _build_about_page(self):
        card = ctk.CTkFrame(self.page_frames["about"], fg_color=PANEL,
            corner_radius=20, border_width=1, border_color=BORDER)
        card.pack(fill="both", expand=True, padx=4, pady=4)
        hero = ctk.CTkFrame(card, fg_color="transparent")
        hero.pack(fill="x", padx=28, pady=(30, 20))
        if self._logo_pil is not None:
            self._about_logo = ctk.CTkImage(light_image=self._logo_pil,
                dark_image=self._logo_pil, size=(108, 108))
            ctk.CTkLabel(hero, text="", image=self._about_logo).pack(side="left", padx=(0, 22))
        title_box = ctk.CTkFrame(hero, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(title_box, text="HETHEREAU HOBBIES TOOL", text_color=ACCENT,
            font=ctk.CTkFont("Segoe UI", 12, "bold")).pack(anchor="w")
        ctk.CTkLabel(title_box, text=APP_TITLE, text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 24, "bold")).pack(anchor="w", pady=(5, 3))
        channel = self.tr("Development build") if APP_CHANNEL == "dev" else self.tr("Release build")
        ctk.CTkLabel(title_box, text=f"{self.tr('Версия')} {APP_VERSION} · {channel}",
            text_color=MUTED, font=ctk.CTkFont("Segoe UI", 11)).pack(anchor="w")
        ctk.CTkFrame(card, height=1, fg_color=BORDER).pack(fill="x", padx=28, pady=(0, 22))
        descriptions = (
            "Утилита для автоматизации игровых хобби в Neverness to Everness.",
            "Сейчас доступен модуль «Подборка владельца».",
            "Новые занятия, включая рыбалку, будут добавляться отдельными модулями.",
        )
        ctk.CTkLabel(card, text="\n\n".join(self.tr(line) for line in descriptions),
            text_color=TEXT, font=ctk.CTkFont("Segoe UI", 13), justify="left",
            anchor="w", wraplength=680).pack(fill="x", padx=32, pady=(0, 25))
        details = ctk.CTkFrame(card, fg_color=PANEL_ALT, corner_radius=13)
        details.pack(fill="x", padx=28, pady=(0, 20))
        for label, value in (("Модуль", "Подборка владельца"), ("Процесс игры", "HTGame.exe"),
            ("Горячие клавиши", "F6 — запуск / пауза    ·    F7 — стоп")):
            row = ctk.CTkFrame(details, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=9)
            ctk.CTkLabel(row, text=self.tr(label), text_color=MUTED,
                font=ctk.CTkFont("Segoe UI", 11)).pack(side="left")
            ctk.CTkLabel(row, text=self.tr(value), text_color=TEXT,
                font=ctk.CTkFont("Segoe UI", 11, "bold")).pack(side="right")
        ctk.CTkButton(card, text=self.tr("Открыть GitHub"),
            image=self.symbol_image("open_in_new", 17, "normal"), compound="left",
            width=180, height=40, fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color="#FFFFFF", command=lambda: webbrowser.open(APP_GITHUB_URL)
        ).pack(anchor="w", padx=28, pady=(0, 28))

    def _build_logs_page(self):
        page = self.page_frames["logs"]
        toolbar = ctk.CTkFrame(page, fg_color="transparent")
        toolbar.pack(fill="x", pady=(2, 10))
        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(title_box, text=self.tr("Журнал событий"), text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 17, "bold")).pack(anchor="w")
        self.logs_count_label = ctk.CTkLabel(title_box, text="0 записей", text_color=MUTED,
            font=ctk.CTkFont("Segoe UI", 10))
        self.logs_count_label.pack(anchor="w", pady=(2, 0))
        specs = (
            ("Копировать выделенное", "copy_all", self.copy_selected_logs, PANEL_ALT, TEXT),
            ("Копировать всё", "article", self.copy_logs, PANEL_ALT, TEXT),
            ("Очистить", "delete", self.clear_logs, STOP_BG, STOP_TEXT),
        )
        for label, icon, command, fg, color in specs:
            ctk.CTkButton(toolbar, text=self.tr(label),
                image=self.symbol_image(icon, 16, "muted" if fg == PANEL_ALT else "danger"),
                compound="left", height=36, fg_color=fg,
                hover_color=BORDER if fg == PANEL_ALT else STOP_HOVER,
                text_color=color, font=ctk.CTkFont("Segoe UI", 10, "bold"),
                command=command).pack(side="right", padx=(7, 0))
        log_card = ctk.CTkFrame(page, fg_color=LOG_BG, corner_radius=14,
            border_width=1, border_color=BORDER)
        log_card.pack(fill="both", expand=True)
        self.log_text = ctk.CTkTextbox(log_card, corner_radius=12, fg_color=LOG_BG,
            border_width=0, text_color=LOG_TEXT,
            font=ctk.CTkFont("Consolas", 10), wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        for stamp, entry in self.log_history:
            self.log_text.insert("end", f"{stamp}  ·  {self.tr(entry)}\n")
        # Tk's disabled state can prevent partial selection/copy on Windows.
        # Keep it normal and intercept editing keys in _guard_log_text_key.
        self.log_text.configure(state="normal")
        self.log_text.see("end")
        text_widget = getattr(self.log_text, "_textbox", self.log_text)
        text_widget.bind("<KeyPress>", self._guard_log_text_key)
        text_widget.bind("<Button-3>", self._show_log_context_menu)
        self.log_context_menu = tk.Menu(self.root, tearoff=0,
            background=PANEL, foreground=TEXT,
            activebackground=ACCENT, activeforeground="#FFFFFF")
        self.log_context_menu.add_command(label=self.tr("Копировать выделенное"), command=self.copy_selected_logs)
        self.log_context_menu.add_command(label=self.tr("Копировать всё"), command=self.copy_logs)
        self.log_context_menu.add_separator()
        self.log_context_menu.add_command(label=self.tr("Очистить"), command=self.clear_logs)
        self._update_logs_count()

    def _update_logs_count(self):
        if hasattr(self, "logs_count_label"):
            try:
                self.logs_count_label.configure(text=f"{len(self.log_history)} {self.tr('записей')}")
            except Exception:
                pass

    def _guard_log_text_key(self, event):
        """Keep the log view read-only without disabling text selection."""
        key = str(event.keysym).lower()
        control_pressed = bool(event.state & 0x4)

        if control_pressed and key == "c":
            self.copy_selected_logs()
            return "break"
        if control_pressed and key == "a":
            widget = getattr(self.log_text, "_textbox", self.log_text)
            widget.tag_add("sel", "1.0", "end-1c")
            widget.mark_set("insert", "end-1c")
            return "break"
        if control_pressed and key == "insert":
            self.copy_selected_logs()
            return "break"

        if key in {
            "left", "right", "up", "down", "home", "end",
            "prior", "next", "page_up", "page_down",
            "shift_l", "shift_r", "control_l", "control_r",
            "alt_l", "alt_r", "caps_lock",
        }:
            return None

        # Block typing, paste, cut, deletion and all other text modifications.
        return "break"

    def _show_log_context_menu(self, event):
        try:
            self.log_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.log_context_menu.grab_release()

    def open_logs(self): self._show_page("logs")
    def open_about(self): self._show_page("about")

    def log(self, message: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_history.append((stamp, message))
        dropped_oldest = len(self.log_history) > 1000
        if dropped_oldest:
            self.log_history.pop(0)

        def write():
            if self.closed or self.log_text is None:
                return
            try:
                if not self.log_text.winfo_exists():
                    return

                text_widget = getattr(self.log_text, "_textbox", self.log_text)
                try:
                    has_selection = bool(text_widget.tag_ranges("sel"))
                    was_at_bottom = (
                        not has_selection and float(text_widget.yview()[1]) >= 0.985
                    )
                except Exception:
                    was_at_bottom = True

                if dropped_oldest:
                    # Rebuild only when the bounded history drops its oldest record.
                    self.log_text.delete("1.0", "end")
                    for old_stamp, old_entry in self.log_history:
                        self.log_text.insert(
                            "end", f"{old_stamp}  ·  {self.tr(old_entry)}\n"
                        )
                else:
                    self.log_text.insert("end", f"{stamp}  ·  {self.tr(message)}\n")

                # Preserve the user's scroll position and current text selection.
                if was_at_bottom:
                    self.log_text.see("end")
                self._update_logs_count()
            except Exception:
                pass

        if threading.current_thread() is threading.main_thread():
            write()
        else:
            self.root.after(0, write)

    def _copy_text_to_clipboard(self, content: str) -> bool:
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update_idletasks()
            return True
        except Exception as exc:
            self.log(f"Не удалось скопировать текст: {exc}")
            return False

    def copy_selected_logs(self):
        if self.log_text is None:
            return

        text_widget = getattr(self.log_text, "_textbox", self.log_text)
        try:
            selection = text_widget.tag_ranges("sel")
            selected = text_widget.get(selection[0], selection[1]) if len(selection) >= 2 else ""
        except (tk.TclError, AttributeError):
            selected = ""

        if not selected:
            self.log("Сначала выдели нужную часть журнала мышью.")
            return
        if self._copy_text_to_clipboard(selected):
            self.log("Выделенный фрагмент журнала скопирован.")

    def copy_logs(self):
        content = "\n".join(
            f"{stamp}  ·  {self.tr(entry)}" for stamp, entry in self.log_history
        )
        if self._copy_text_to_clipboard(content):
            self.log("Весь журнал скопирован.")

    def clear_logs(self):
        self.log_history.clear()
        if self.log_text is not None:
            self.log_text.delete("1.0", "end")
        self._update_logs_count()

    def set_status(self, status: str, stage: str | None = None):
        self.current_status = status
        if stage is not None:
            self.current_stage = stage
        def update():
            if self.closed:
                return
            if "ПАУЗА" in status:
                color = YELLOW
                fg = STATUS_PAUSE_BG
            elif any(word in status for word in ("ОШИБКА", "ОСТАНОВЛЕНО", "ОСТАНОВКА", "АВАРИЙНАЯ")):
                color = RED
                fg = STATUS_ERROR_BG
            elif any(word in status for word in ("РАБОТАЕТ", "ЗАПУСК", "ФАРМ", "ПОЛУЧАЮ", "ОТКРЫВАЮ", "ПРОВЕРКА", "ЗАВЕРШАЮ")):
                color = GREEN
                fg = STATUS_RUNNING_BG
            elif "ЗАКОНЧИЛАСЬ" in status or "ЗАВЕРШЕНО" in status:
                color = YELLOW
                fg = STATUS_PAUSE_BG
            else:
                color = TEXT
                fg = PANEL_ALT
            if "ПАУЗА" in status:
                status_icon, icon_tone = "pause", "warning"
            elif any(word in status for word in ("ОШИБКА", "ОСТАНОВЛЕНО", "ОСТАНОВКА", "АВАРИЙНАЯ")):
                status_icon, icon_tone = "error", "danger"
            elif "ЗАКОНЧИЛАСЬ" in status or "ЗАВЕРШЕНО" in status:
                status_icon, icon_tone = "check_circle", "success"
            elif any(word in status for word in ("РАБОТАЕТ", "ЗАПУСК", "ФАРМ", "ПОЛУЧАЮ", "ОТКРЫВАЮ", "ПРОВЕРКА", "ЗАВЕРШАЮ")):
                status_icon, icon_tone = "monitoring", "success"
            else:
                status_icon, icon_tone = "info", "accent"
            self.status_icon_label.configure(image=self.symbol_image(status_icon, 19, icon_tone))
            next_action_icon = "pause" if any(
                word in status for word in ("РАБОТАЕТ", "ЗАПУСК", "ФАРМ", "ПОЛУЧАЮ", "ОТКРЫВАЮ", "ПРОВЕРКА", "ЗАВЕРШАЮ")
            ) else "play_arrow"
            self.toggle_button.configure(image=self.symbol_image(next_action_icon, 22, "normal"))
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
            self.connection_icon.configure(image=self.symbol_image(
                "check_circle" if found else "desktop_windows", 23, "success" if found else "danger"
            ))
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
        if self._stop_scan_pending:
            self.log("Дождись завершения контрольного сканирования после остановки.")
            return

        if self.worker_thread and self.worker_thread.is_alive():
            if self.pause_event.is_set():
                # Resume is never allowed to continue from stale pre-pause values.
                self.pause_scan_requested.clear()
                self.rescan_requested.set()
                self.last_pause_scan = None
                self.last_resume_scan = None
                self.pause_event.clear()
                self.set_status(
                    "ПРОВЕРКА ПОСЛЕ ПАУЗЫ",
                    "Сначала заново проверю доход и энергию. До подтверждения кликов не будет.",
                )
                self.log("Пауза снята. Запрошен контрольный скан дохода и энергии.")
            else:
                self.pause_event.set()
                self.pause_scan_requested.set()
                self.set_status(
                    "ПАУЗА",
                    "Ввод остановлен. Сверяю доход и энергию на текущем экране.",
                )
                self.log("Пауза включена. Запрошен скан текущего состояния.")
            return

        self.stop_event.clear()
        self.pause_event.clear()
        self.active_income_ocr_thread = None
        self.rescan_requested.clear()
        self.pause_scan_requested.clear()
        self.last_pause_scan = None
        self.last_resume_scan = None
        self.worker_error = None
        self.cycle_count = 0
        self.set_metric("cycles", "0")
        self.set_status(
            "ЗАПУСК",
            "Сначала проверю энергию, затем открою магазин и сверю оба счётчика.",
        )
        self.log("Автоматизация запущена. Перед первым действием будет проверена энергия.")
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def stop(self):
        worker = self.worker_thread
        was_running = worker is not None and worker.is_alive()
        previous_status = self.current_status
        previous_stage = self.current_stage
        include_income = (
            self.game_screen_context == "owner_selection"
            or "ФАРМ" in previous_status
            or any(token in previous_stage.lower() for token in ("доход", "фарм", "накоплен"))
        )

        self.stop_event.set()
        self.pause_event.clear()
        self.pause_scan_requested.clear()

        if not was_running:
            self.set_status("ОСТАНОВЛЕНО", "Автоматизация не запущена")
            self.log("Получена команда остановки: активных действий не было.")
            return

        self.set_status("ОСТАНОВКА", "Прекращаю ввод и после этого сверю счётчики.")
        self.log("Получена команда остановки. Новые клики запрещены.")
        self._schedule_stop_scan(worker, include_income=include_income)

    def _schedule_stop_scan(self, worker: threading.Thread, *, include_income: bool):
        """Refresh available counters after the worker has stopped sending input."""
        with self._stop_scan_lock:
            if self._stop_scan_pending:
                return
            self._stop_scan_pending = True

        def scan_after_worker():
            try:
                worker.join()
                pending_ocr = self.active_income_ocr_thread
                if pending_ocr is not None and pending_ocr.is_alive():
                    pending_ocr.join()
                if self.closed:
                    return
                result = self._scan_game_state(
                    include_income=include_income,
                    reason="после остановки",
                    attempts=2,
                    allow_when_stopped=True,
                )
                if result is None:
                    self.log(
                        "После остановки контрольный скан не подтверждён: "
                        f"{self.last_scan_error or 'счётчики не прочитаны'}. "
                        "Игровые действия не выполнялись."
                    )
                else:
                    summary = (
                        f"После остановки подтверждены энергия "
                        f"{result['energy']}/{result['energy_max']}"
                    )
                    if include_income:
                        summary += f", доход {result['income']}/{result['income_max']}"
                    self.log(summary + ".")
                    self.set_status(
                        "ОСТАНОВЛЕНО",
                        "Ввод остановлен. Последние доступные показатели обновлены.",
                    )
            except Exception as exc:
                if not self.closed:
                    self.log(
                        f"Сканирование после остановки завершилось ошибкой: "
                        f"{type(exc).__name__}: {exc}"
                    )
            finally:
                with self._stop_scan_lock:
                    self._stop_scan_pending = False

        threading.Thread(
            target=scan_after_worker,
            daemon=True,
            name="HHT-Stop-State-Scan",
        ).start()

    def _perform_pause_scan(self, *, include_income: bool, reason: str):
        """Scan the visible counters while keeping game input paused."""
        if not self.pause_scan_requested.is_set() or self.stop_event.is_set():
            return None

        self.pause_scan_requested.clear()
        self.set_status(
            "ПАУЗА",
            "Проверяю показатели на текущем экране. Автоматизация остаётся на паузе.",
        )
        try:
            scan = self._scan_game_state(
                include_income=include_income,
                reason=reason,
                attempts=2,
            )
        except Exception as exc:
            self.last_scan_error = f"{type(exc).__name__}: {exc}"
            scan = None

        self.last_pause_scan = scan
        if scan is None:
            self.log(
                f"Скан при паузе не подтверждён ({reason}): "
                f"{self.last_scan_error or 'счётчики не прочитаны'}. "
                "При возобновлении будет выполнен новый полный скан."
            )
            if self.pause_event.is_set():
                self.set_status(
                    "ПАУЗА",
                    "Скан не подтверждён. Возобновление потребует повторной проверки.",
                )
        else:
            summary = (
                f"При паузе подтверждены энергия "
                f"{scan['energy']}/{scan['energy_max']}"
            )
            if include_income:
                summary += f", доход {scan['income']}/{scan['income_max']}"
            self.log(summary + ".")
            if self.pause_event.is_set():
                self.set_status(
                    "ПАУЗА",
                    "Показатели сверены. Нажми F6 для повторной проверки и продолжения.",
                )
        return scan

    def close(self):
        self.closed = True
        self.stop_event.set()
        self._close_auxiliary_windows()
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

    def _capture_client_image(self, ensure_focus: bool = False):
        if ensure_focus:
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
            # Keep OCR diagnostics outside PyInstaller's temporary _MEIPASS
            # directory so they remain available after a one-file EXE closes.
            debug_dir = os.path.dirname(self._config_path())
            os.makedirs(debug_dir, exist_ok=True)
            debug_path = os.path.join(
                debug_dir,
                f"debug_{debug_name}_capture.png",
            )
            crop.save(debug_path)
            self.last_ocr_debug_path = debug_path
        except Exception:
            self.last_ocr_debug_path = ""

        if debug_name == "income":
            return self._read_income_parts(crop, min_max=min_max, expected_max=expected_max)

        gray = ImageOps.autocontrast(crop.convert("L"))

        # Two independent passes are enough for the static energy fraction.
        # Avoid spawning 13 Tesseract processes for every cycle check.
        candidates = []
        for scale, psm in ((3, 7), (4, 8)):
            enlarged = gray.resize(
                (gray.width * scale, gray.height * scale),
                Image.Resampling.LANCZOS,
            )
            candidates.append((enlarged, psm))
        threshold = gray.point(lambda value: 255 if value > 150 else 0)
        candidates.append((threshold.resize(
            (threshold.width * 3, threshold.height * 3), Image.Resampling.LANCZOS
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
                timeout=2.5,
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

        # This is a provisional read of one screenshot. The caller's
        # _scan_game_state() confirms it against a second independent capture.
        return select_ratio_candidate(parsed)


    def _read_income_parts(
        self, crop: Image.Image, min_max: int = 100, expected_max: int | None = None
    ) -> tuple[int | None, int | None, str]:
        """Read yellow current income and white target separately.

        The level target is static for the active challenge. Detect it once with
        multiple OCR passes, then reuse it and OCR only the changing numerator.
        This avoids launching up to 17 Tesseract subprocesses every second.
        """
        rgb = crop.convert("RGB")
        width, height = rgb.size

        # Keep only yellow pixels from the animated current-income counter.
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
                        timeout=2.5,
                    ).strip()
                    for token in re.findall(r"\d{1,6}", raw):
                        values.append((int(token), raw))
            return values

        # The target is constant for one challenge. Reuse the confirmed value
        # after the first read instead of re-running OCR on the white digits.
        if expected_max is None:
            target_crop = crop.crop((round(width * 0.54), 0, width, height))
            target_candidates = read_digits(
                target_crop, scales=(3, 4), psms=(7, 8)
            )
            target_candidates = [
                item for item in target_candidates
                if item[0] >= min_max
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
        else:
            target = expected_max
            votes = 2  # Previously confirmed for this running event.

        # Multiple segmentation modes help retain leading digits. These passes
        # run in the background, so they do not interrupt hammer clicks.
        current_candidates = read_digits(
            yellow_mask, scales=(3, 4), psms=(6, 7, 8)
        )
        # Income can overshoot the threshold (e.g. 2303/1900). Reject only
        # implausibly large OCR noise, not legitimate values above target.
        upper_plausible = max(target * 3, target + 1000)
        valid_current = [
            value for value, _ in current_candidates
            if 0 <= value <= upper_plausible
        ]
        if not valid_current:
            return None, target, "целевой лимит найден, текущее значение дохода не распознано"

        # Prefer the largest plausible value to preserve leading digits such as
        # 1270 when another OCR pass sees only 270 or 70.
        current = max(valid_current)
        return current, target, f"{current}/{target}; target votes={votes}"

    def read_income(self, expected_max: int | None = None):
        # The denominator is level-specific (for example 1100 or 1900).
        # Once detected, pass it back to avoid repeating OCR on static digits.
        current, maximum, raw = self._read_ratio(
            INCOME_REGION, "income", expected_max=expected_max, min_max=MIN_INCOME_TARGET
        )
        if current is not None and maximum is not None:
            self.set_metric("income", f"{current:,} / {maximum:,}")
        return current, maximum, raw

    def read_energy(self):
        current, maximum, raw = self._read_ratio(ENERGY_REGION, "energy")
        if current is not None:
            self.set_metric("energy", f"{current} / {maximum}")
        return current, maximum, raw

    def _scan_game_state(
        self,
        *,
        include_income: bool = True,
        reason: str = "проверка состояния",
        attempts: int = 3,
        allow_when_stopped: bool = False,
    ) -> dict | None:
        """Focus the game and verify counters from independent screenshots.

        Energy must match exactly in two reads. Income must have a confirmed,
        matching target and a non-decreasing current value in two reads.
        Nothing should click through an ambiguous state.
        """
        if self.stop_event.is_set() and not allow_when_stopped:
            return None
        self._bring_game_to_front()
        time.sleep(0.2)

        for attempt in range(1, attempts + 1):
            if self.stop_event.is_set() and not allow_when_stopped:
                return None

            energy_a, energy_max_a, energy_raw_a = self.read_energy()
            time.sleep(0.22)
            energy_b, energy_max_b, energy_raw_b = self.read_energy()
            energy_ok = (
                energy_a is not None and energy_b is not None
                and energy_max_a is not None and energy_max_b is not None
                and energy_a == energy_b and energy_max_a == energy_max_b
            )

            scan = {
                "energy": energy_b if energy_ok else None,
                "energy_max": energy_max_b if energy_ok else None,
                "income": None,
                "income_max": None,
                "reason": reason,
            }

            income_ok = not include_income
            income_raw_a = income_raw_b = ""
            if include_income:
                income_a, income_max_a, income_raw_a = self.read_income()
                if income_a is not None and income_max_a is not None:
                    time.sleep(0.18)
                    income_b, income_max_b, income_raw_b = self.read_income(
                        expected_max=income_max_a
                    )
                else:
                    income_b, income_max_b = None, None

                income_ok = (
                    income_a is not None and income_b is not None
                    and income_max_a is not None and income_max_b == income_max_a
                    and income_b >= income_a
                )
                if income_ok:
                    scan["income"] = income_b
                    scan["income_max"] = income_max_b

            if energy_ok and income_ok:
                self.last_scan_error = ""
                self.log(
                    f"Скан подтверждён ({reason}): энергия "
                    f"{scan['energy']}/{scan['energy_max']}"
                    + (
                        f", доход {scan['income']}/{scan['income_max']}."
                        if include_income else "."
                    )
                )
                return scan

            parts = []
            if not energy_ok:
                parts.append(
                    f"энергия не совпала: {energy_a}/{energy_max_a} → "
                    f"{energy_b}/{energy_max_b} ({energy_raw_a!r}; {energy_raw_b!r})"
                )
            if include_income and not income_ok:
                parts.append(
                    f"доход не подтверждён: {income_a}/{income_max_a} → "
                    f"{income_b}/{income_max_b} ({income_raw_a!r}; {income_raw_b!r})"
                )
            self.last_scan_error = "; ".join(parts) or "счётчики не подтверждены"
            self.log(
                f"Повторный скан ({attempt}/{attempts}, {reason}): "
                f"{self.last_scan_error}"
            )
            if attempt < attempts and not self.stop_event.is_set():
                time.sleep(0.35)

        return None

    def scan_state_manual(self):
        if self.worker_thread and self.worker_thread.is_alive():
            self.log("Ручной скан пропущен: автоматизация сама проверяет счётчики при старте, паузе и смене цикла.")
            return
        def run_scan():
            try:
                self.set_status("СКАНИРОВАНИЕ", "Проверяю энергию и доход по двум независимым снимкам")
                result = self._scan_game_state(
                    include_income=True,
                    reason="ручная проверка",
                    allow_when_stopped=True,
                )
                if result is None:
                    self.set_status(
                        "ОШИБКА СИНХРОНИЗАЦИИ",
                        self.last_scan_error or "Счётчики не удалось подтвердить",
                    )
                    return
                self.set_status("СКАНИРОВАНИЕ ЗАВЕРШЕНО", "Энергия и доход подтверждены")
            except Exception as exc:
                self.log(f"Ошибка сканирования состояния: {type(exc).__name__}: {exc}")
                self.set_status("ОШИБКА СКАНИРОВАНИЯ", str(exc))

        threading.Thread(target=run_scan, daemon=True, name="HHT-State-Scan").start()

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

    def _wait(self, seconds: float, resume_scan: str = "energy") -> bool:
        remaining = seconds
        paused_during_wait = False
        while remaining > 0:
            if self.stop_event.is_set():
                return False
            if self.pause_event.is_set():
                paused_during_wait = True
                if self.pause_scan_requested.is_set():
                    self._perform_pause_scan(
                        include_income=(resume_scan == "both"),
                        reason="при паузе во время ожидания",
                    )
                time.sleep(0.1)
                continue

            if paused_during_wait and self.rescan_requested.is_set():
                if resume_scan == "both":
                    # The hammer loop owns a background income OCR thread. Let
                    # that loop join it and perform the paired scan safely.
                    paused_during_wait = False
                else:
                    self.rescan_requested.clear()
                    self.set_status(
                        "ПОВТОРНЫЙ СКАН",
                        "После паузы проверяю энергию перед продолжением",
                    )
                    scan = self._scan_game_state(
                        include_income=False,
                        reason="после паузы на экране награды",
                    )
                    if scan is None:
                        self.worker_error = (
                            "ОШИБКА СИНХРОНИЗАЦИИ",
                            self.last_scan_error or "Не удалось подтвердить энергию после паузы",
                        )
                        self.stop_event.set()
                        return False
                    self.last_resume_scan = scan
                    paused_during_wait = False

            step = min(0.1, remaining)
            time.sleep(step)
            remaining -= step
        return not self.stop_event.is_set()

    def _click(self, name):
        """Do not send input after a pause until the visible game state is checked."""
        was_paused = False
        while self.pause_event.is_set() and not self.stop_event.is_set():
            was_paused = True
            time.sleep(0.05)
        if self.stop_event.is_set():
            return False

        if was_paused or self.rescan_requested.is_set():
            # Hammer clicks are handled by the worker loop, which can first join
            # its background income OCR thread. Other buttons need an energy
            # refresh before a single click is allowed.
            if name == "Молоток":
                self.rescan_requested.set()
                return False

            self.rescan_requested.clear()
            scan = self._scan_game_state(
                include_income=False,
                reason=f"перед кликом «{name}» после паузы",
            )
            self.pause_scan_requested.clear()
            if scan is None:
                self.worker_error = (
                    "ОШИБКА СИНХРОНИЗАЦИИ",
                    self.last_scan_error or "Не удалось подтвердить энергию перед кликом",
                )
                self.set_status(*self.worker_error)
                self.stop_event.set()
                return False

            if name == "Магазин" and scan["energy"] < MINIMUM_ENERGY_PER_CYCLE:
                self.worker_error = (
                    "ЭНЕРГИЯ ЗАКОНЧИЛАСЬ",
                    f"Осталось {scan['energy']}. Магазин не открываю.",
                )
                self.set_status(*self.worker_error)
                self.stop_event.set()
                return False

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
                        if self.pause_scan_requested.is_set():
                            self._perform_pause_scan(
                                include_income=False,
                                reason="при паузе перед новым циклом",
                            )
                        time.sleep(0.1)
                    continue

                self.set_status(
                    "ПРОВЕРКА ЭНЕРГИИ",
                    "Считываю энергию дважды перед началом нового цикла",
                )
                energy_scan = self._scan_game_state(
                    include_income=False, reason="перед новым циклом"
                )
                if energy_scan is None:
                    if self.stop_event.is_set():
                        break
                    energy_ocr_failures += 1
                    debug_path = self.last_ocr_debug_path
                    self.log(
                        f"Не удалось подтвердить энергию: {self.last_scan_error}. "
                        f"Попытка {energy_ocr_failures}/{MAX_ENERGY_OCR_FAILURES}."
                    )
                    if debug_path:
                        self.log(f"Снимок области OCR: {debug_path}")
                    if energy_ocr_failures >= MAX_ENERGY_OCR_FAILURES:
                        self.set_status(
                            "ОШИБКА OCR ЭНЕРГИИ",
                            "Энергия не подтверждена двумя снимками. Новых кликов не будет.",
                        )
                        self.log("Автоматизация остановлена без кликов: энергия не подтверждена.")
                        return
                    if not self._wait(ENERGY_RETRY_INTERVAL, resume_scan="energy"):
                        break
                    continue

                energy = energy_scan["energy"]
                energy_max = energy_scan["energy_max"]
                energy_ocr_failures = 0
                self.log(f"Запас энергии перед циклом: {energy}/{energy_max}.")
                if energy < MINIMUM_ENERGY_PER_CYCLE or energy <= 0:
                    self.log(f"Для следующего цикла нужно не менее {MINIMUM_ENERGY_PER_CYCLE} энергии.")
                    self.set_status("ЭНЕРГИЯ ЗАКОНЧИЛАСЬ", f"Осталось {energy}. Новые циклы остановлены.")
                    return

                self.set_status("ОТКРЫВАЮ МАГАЗИН", "Открываю магазин события")
                if not self._click("Магазин"):
                    if self.worker_error is not None or self.stop_event.is_set():
                        break
                self.game_screen_context = "owner_selection"
                if not self._wait(2.0, resume_scan="both"):
                    break

                self.set_status(
                    "СИНХРОНИЗАЦИЯ СЧЁТЧИКОВ",
                    "Перед молотком проверяю энергию и целевой доход двумя снимками",
                )
                opening_scan = self.last_resume_scan
                self.last_resume_scan = None
                if opening_scan is None or opening_scan.get("income") is None:
                    opening_scan = self._scan_game_state(
                        include_income=True, reason="после открытия магазина"
                    )
                self.rescan_requested.clear()
                self.pause_scan_requested.clear()
                if opening_scan is None:
                    self.worker_error = (
                        "ОШИБКА СИНХРОНИЗАЦИИ",
                        self.last_scan_error or "Не удалось подтвердить доход и энергию",
                    )
                    self.set_status(*self.worker_error)
                    self.log("Молоток не нажимаю: начальные значения не подтверждены.")
                    return

                # Use the paired scan as the baseline. If the threshold is
                # already reached, proceed to the reward screen without more clicks.
                active_income_target = opening_scan["income_max"]
                current_at_open = opening_scan["income"]
                self.set_metric("income", f"{current_at_open:,} / {active_income_target:,}")
                self.log(
                    f"Начальные показатели подтверждены: энергия "
                    f"{opening_scan['energy']}/{opening_scan['energy_max']}, "
                    f"доход {current_at_open}/{active_income_target}."
                )
                last_ocr = time.monotonic()
                last_seen = time.monotonic()
                reached = current_at_open >= active_income_target
                reached_confirmations = 2 if reached else 0
                if reached:
                    self.log("Целевой доход уже достигнут. Дополнительные клики не нужны.")
                self.set_status("ФАРМ ДОХОДА", f"Набираю доход до {active_income_target}")
                if not reached:
                    self.log("Магазин открыт. Начинаю нажимать молоток.")
                income_thread = None
                income_result = None

                def read_income_background(target, output):
                    started = time.perf_counter()
                    try:
                        output["result"] = self.read_income(expected_max=target)
                    except Exception as exc:
                        output["error"] = exc
                    finally:
                        output["elapsed_ms"] = (time.perf_counter() - started) * 1000

                while not self.stop_event.is_set():
                    while self.pause_event.is_set() and not self.stop_event.is_set():
                        self.set_status("ПАУЗА", "Фарм приостановлен. Сверяю текущие показатели.")
                        if self.pause_scan_requested.is_set():
                            if income_thread is not None and income_thread.is_alive():
                                while income_thread.is_alive() and not self.stop_event.is_set():
                                    income_thread.join(timeout=0.1)
                            if not income_thread.is_alive():
                                self.active_income_ocr_thread = None
                            self._perform_pause_scan(
                                include_income=True,
                                reason="при паузе во время фарма",
                            )
                        time.sleep(0.1)
                    if self.stop_event.is_set():
                        break

                    if self.rescan_requested.is_set():
                        # Wait for any previous background OCR to finish before
                        # taking a fresh pair of screenshots after resume.
                        if income_thread is not None and income_thread.is_alive():
                            while income_thread.is_alive() and not self.stop_event.is_set():
                                income_thread.join(timeout=0.1)
                        if income_thread is not None and not income_thread.is_alive():
                            self.active_income_ocr_thread = None
                        if self.stop_event.is_set():
                            break
                        income_thread = None
                        income_result = None
                        self.rescan_requested.clear()
                        self.pause_scan_requested.clear()
                        self.last_resume_scan = None
                        self.set_status(
                            "ПОВТОРНЫЙ СКАН",
                            "После паузы проверяю доход и энергию до продолжения",
                        )
                        resume_scan_result = self._scan_game_state(
                            include_income=True, reason="после паузы во время фарма"
                        )
                        if resume_scan_result is None:
                            self.worker_error = (
                                "ОШИБКА СИНХРОНИЗАЦИИ",
                                self.last_scan_error or "Не удалось повторно прочитать счётчики",
                            )
                            self.set_status(*self.worker_error)
                            self.stop_event.set()
                            return
                        self.last_resume_scan = resume_scan_result
                        active_income_target = resume_scan_result["income_max"]
                        last_seen = time.monotonic()
                        last_ocr = last_seen
                        if resume_scan_result["income"] >= active_income_target:
                            reached = True
                            self.log(
                                f"После паузы цель уже достигнута: "
                                f"{resume_scan_result['income']}/{active_income_target}."
                            )
                            break

                    if self.stop_event.is_set():
                        break

                    # Keep the hammer loop independent from Tesseract. OCR works
                    # on its own captured frame while clicks continue at a steady rate.
                    clicked = self._click("Молоток")
                    if not clicked:
                        if self.stop_event.is_set():
                            break
                        if self.rescan_requested.is_set():
                            continue
                        break
                    now = time.monotonic()

                    if (
                        income_thread is None
                        and now - last_ocr >= OCR_INTERVAL
                    ):
                        income_result = {}
                        income_thread = threading.Thread(
                            target=read_income_background,
                            args=(active_income_target, income_result),
                            daemon=True,
                            name="HHT-Income-OCR",
                        )
                        income_thread.start()
                        self.active_income_ocr_thread = income_thread
                        last_ocr = now

                    if (
                        income_thread is not None
                        and not income_thread.is_alive()
                        and income_result is not None
                        and ("result" in income_result or "error" in income_result)
                    ):
                        ocr_duration_ms = income_result.get("elapsed_ms", 0.0)
                        if ocr_duration_ms >= 750:
                            self.log(f"Распознавание дохода заняло {ocr_duration_ms:.0f} мс.")
                        if "error" in income_result:
                            current, maximum = None, None
                            raw = f"OCR error: {income_result['error']}"
                        else:
                            current, maximum, raw = income_result["result"]

                        income_thread = None
                        self.active_income_ocr_thread = None
                        income_result = None
                        now = time.monotonic()

                        if current is not None and maximum is not None:
                            last_seen = now
                            if active_income_target != maximum:
                                active_income_target = maximum
                                self.log(f"Определён целевой доход текущего уровня: {maximum}.")
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

                    if not self._wait(CLICK_INTERVAL, resume_scan="both"):
                        break
                    resume_scan_result = self.last_resume_scan
                    self.last_resume_scan = None
                    if (
                        resume_scan_result is not None
                        and resume_scan_result.get("income") is not None
                        and resume_scan_result["income"] >= resume_scan_result["income_max"]
                    ):
                        reached = True
                        self.log(
                            f"После возобновления подтверждена цель: "
                            f"{resume_scan_result['income']}/{resume_scan_result['income_max']}."
                        )
                        break

                if self.stop_event.is_set() or not reached:
                    break

                self.set_status("ЗАВЕРШАЮ ИСПЫТАНИЕ", "Нажимаю Esc и ожидаю экран награды")
                self._bring_game_to_front()
                pyautogui.press("esc")
                self.game_screen_context = "reward_screen"
                if not self._wait(2.0, resume_scan="energy"):
                    break

                self.set_status("ПОЛУЧАЮ НАГРАДУ", "Забираю награду за испытание")
                self._click("Получить")
                self.game_screen_context = "event_result"
                if not self._wait(3.0, resume_scan="energy"):
                    break

                self.game_screen_context = "outside_event"
                self.cycle_count += 1
                self.set_metric("cycles", str(self.cycle_count))
                self.log(f"Цикл №{self.cycle_count} завершён.")

            if self.worker_error is not None:
                self.set_status(*self.worker_error)
            elif self.stop_event.is_set():
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
    # Stable Windows taskbar grouping and app identity (before Tk creates HWNDs).
    if os.name == "nt":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "M1ST0R.HethereauHobbiesTool"
            )
        except Exception:
            pass
    if not ensure_windows_admin():
        return
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    apply_theme_palette("dark")
    root = ctk.CTk()
    OwnerSelectionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
