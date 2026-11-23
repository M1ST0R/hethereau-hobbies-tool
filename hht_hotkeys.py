"""Keyboard shortcut normalization shared by the Qt UI and pynput listener."""

from __future__ import annotations

from collections.abc import Iterable

MODIFIER_ORDER = ("CTRL", "ALT", "SHIFT", "WIN")
MODIFIER_NAMES = {
    "ctrl": "CTRL", "control": "CTRL", "ctrl_l": "CTRL", "ctrl_r": "CTRL",
    "alt": "ALT", "alt_l": "ALT", "alt_r": "ALT", "alt_gr": "ALT",
    "shift": "SHIFT", "shift_l": "SHIFT", "shift_r": "SHIFT",
    "win": "WIN", "meta": "WIN", "cmd": "WIN", "cmd_l": "WIN", "cmd_r": "WIN",
}
CHAR_ALIASES = {" ": "SPACE", "+": "PLUS"}
SPECIAL_KEYS = {
    "SPACE", "TAB", "ENTER", "ESC", "BACKSPACE", "DELETE", "INSERT",
    "HOME", "END", "PAGE_UP", "PAGE_DOWN", "LEFT", "RIGHT", "UP", "DOWN",
    "CAPS_LOCK", "NUM_LOCK", "SCROLL_LOCK", "PRINT_SCREEN", "PAUSE", "MENU", "PLUS",
}
QT_KEY_ALIASES = {
    "SPACE": "SPACE", "TAB": "TAB", "BACKTAB": "TAB",
    "RETURN": "ENTER", "ENTER": "ENTER", "ESCAPE": "ESC",
    "BACKSPACE": "BACKSPACE", "DELETE": "DELETE", "INSERT": "INSERT",
    "HOME": "HOME", "END": "END", "PAGEUP": "PAGE_UP", "PAGE_UP": "PAGE_UP",
    "PAGEDOWN": "PAGE_DOWN", "PAGE_DOWN": "PAGE_DOWN",
    "LEFT": "LEFT", "RIGHT": "RIGHT", "UP": "UP", "DOWN": "DOWN",
    "CAPSLOCK": "CAPS_LOCK", "NUMLOCK": "NUM_LOCK", "SCROLLLOCK": "SCROLL_LOCK",
    "PRINT": "PRINT_SCREEN", "PRINTSCREEN": "PRINT_SCREEN", "PAUSE": "PAUSE",
    "MENU": "MENU",
}
PYNPUT_KEY_ALIASES = {
    "space": "SPACE", "tab": "TAB", "enter": "ENTER", "esc": "ESC",
    "backspace": "BACKSPACE", "delete": "DELETE", "insert": "INSERT",
    "home": "HOME", "end": "END", "page_up": "PAGE_UP", "page_down": "PAGE_DOWN",
    "left": "LEFT", "right": "RIGHT", "up": "UP", "down": "DOWN",
    "caps_lock": "CAPS_LOCK", "num_lock": "NUM_LOCK",
    "scroll_lock": "SCROLL_LOCK", "print_screen": "PRINT_SCREEN",
    "pause": "PAUSE", "menu": "MENU",
}
QT_MODIFIER_MASKS = (
    (0x04000000, "CTRL"),  # Qt.ControlModifier
    (0x08000000, "ALT"),   # Qt.AltModifier
    (0x02000000, "SHIFT"), # Qt.ShiftModifier
    (0x10000000, "WIN"),   # Qt.MetaModifier
)


def normalize_base_key(value: str | None) -> str | None:
    if not value:
        return None
    value = str(value)
    if len(value) == 1 and value.isprintable():
        return CHAR_ALIASES.get(value, value.upper())
    normalized = value.upper().replace("-", "_").replace(" ", "_")
    if normalized in SPECIAL_KEYS:
        return normalized
    if normalized.startswith("F") and normalized[1:].isdigit():
        number = int(normalized[1:])
        return normalized if 1 <= number <= 24 else None
    return None


def build_hotkey(base_key: str | None, modifiers: Iterable[str] = ()) -> str | None:
    base = normalize_base_key(base_key)
    if base is None or base in MODIFIER_ORDER:
        return None
    normalized_modifiers = set()
    for modifier in modifiers:
        normalized = MODIFIER_NAMES.get(str(modifier).casefold(), str(modifier).upper())
        if normalized not in MODIFIER_ORDER:
            return None
        normalized_modifiers.add(normalized)
    ordered = [modifier for modifier in MODIFIER_ORDER if modifier in normalized_modifiers]
    return "+".join([*ordered, base])


def parse_hotkey(value: str | None) -> tuple[tuple[str, ...], str] | None:
    if not isinstance(value, str) or not value.strip():
        return None
    parts = value.upper().split("+")
    if any(not part for part in parts):
        return None
    base = normalize_base_key(parts[-1])
    if base is None or base in MODIFIER_ORDER:
        return None
    modifiers = parts[:-1]
    if len(set(modifiers)) != len(modifiers) or any(modifier not in MODIFIER_ORDER for modifier in modifiers):
        return None
    return tuple(modifier for modifier in MODIFIER_ORDER if modifier in modifiers), base


def hotkey_from_qt(key_name: str, key_text: str, qt_modifiers: int) -> str | None:
    modifiers = [name for mask, name in QT_MODIFIER_MASKS if int(qt_modifiers) & mask]
    text = str(key_text or "")
    if len(text) == 1 and text.isprintable():
        base = normalize_base_key(text)
    else:
        name = str(key_name or "")
        if name.startswith("Key_"):
            name = name[4:]
        base = QT_KEY_ALIASES.get(name.upper(), normalize_base_key(name))
    return build_hotkey(base, modifiers)


def modifier_from_pynput_key(key) -> str | None:
    name = getattr(key, "name", None)
    return MODIFIER_NAMES.get(str(name).casefold()) if name else None


def base_from_pynput_key(key) -> str | None:
    char = getattr(key, "char", None)
    if isinstance(char, str) and len(char) == 1:
        if char.isprintable():
            return normalize_base_key(char)
        if 1 <= ord(char) <= 26:
            return normalize_base_key(chr(ord(char) + 64))
    virtual_key = getattr(key, "vk", None)
    if isinstance(virtual_key, int):
        if 0x30 <= virtual_key <= 0x39 or 0x41 <= virtual_key <= 0x5A:
            return normalize_base_key(chr(virtual_key))
    name = getattr(key, "name", None)
    if not name:
        return None
    return PYNPUT_KEY_ALIASES.get(str(name).casefold(), normalize_base_key(str(name)))


def display_hotkey(value: str) -> str:
    names = {
        "CTRL": "Ctrl", "ALT": "Alt", "SHIFT": "Shift", "WIN": "Win",
        "SPACE": "Space", "ENTER": "Enter", "ESC": "Esc",
        "PAGE_UP": "Page Up", "PAGE_DOWN": "Page Down",
        "LEFT": "Left", "RIGHT": "Right", "UP": "Up", "DOWN": "Down",
        "BACKSPACE": "Backspace", "DELETE": "Delete", "INSERT": "Insert",
        "HOME": "Home", "END": "End", "PLUS": "+",
    }
    return " + ".join(names.get(part, part) for part in value.split("+"))


def is_valid_hotkey(value: str | None) -> bool:
    return parse_hotkey(value) is not None
