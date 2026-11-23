"""Tests for arbitrary single-key and modifier-combination shortcuts."""

import unittest

from hht_hotkeys import (
    base_from_pynput_key, build_hotkey, display_hotkey, hotkey_from_qt,
    is_valid_hotkey, modifier_from_pynput_key, parse_hotkey,
)


class FakeKey:
    def __init__(self, *, char=None, name=None, vk=None):
        self.char = char
        self.name = name
        self.vk = vk


class HotkeyTests(unittest.TestCase):
    def test_qt_letters_digits_and_punctuation(self):
        self.assertEqual(hotkey_from_qt("Key_A", "a", 0), "A")
        self.assertEqual(hotkey_from_qt("Key_7", "7", 0), "7")
        self.assertEqual(hotkey_from_qt("Key_Plus", "+", 0), "PLUS")

    def test_qt_special_keys(self):
        self.assertEqual(hotkey_from_qt("Key_Space", " ", 0), "SPACE")
        self.assertEqual(hotkey_from_qt("Key_PageUp", "", 0), "PAGE_UP")
        self.assertEqual(hotkey_from_qt("Key_F24", "", 0), "F24")
        self.assertEqual(hotkey_from_qt("Key_Escape", "", 0), "ESC")

    def test_qt_modifier_combinations(self):
        ctrl_shift = 0x04000000 | 0x02000000
        self.assertEqual(hotkey_from_qt("Key_A", "a", ctrl_shift), "CTRL+SHIFT+A")
        self.assertEqual(hotkey_from_qt("Key_F7", "", 0x08000000), "ALT+F7")

    def test_modifier_alone_is_rejected(self):
        self.assertIsNone(hotkey_from_qt("Key_Shift", "", 0))
        self.assertIsNone(hotkey_from_qt("Key_Control", "", 0))

    def test_duplicate_or_invalid_shortcuts_are_rejected(self):
        self.assertFalse(is_valid_hotkey("CTRL+CTRL+A"))
        self.assertFalse(is_valid_hotkey("CTRL+"))
        self.assertFalse(is_valid_hotkey("F25"))
        self.assertFalse(is_valid_hotkey("SHIFT"))
        self.assertTrue(is_valid_hotkey("CTRL+ALT+PAGE_UP"))

    def test_parse_hotkey_orders_modifiers_consistently(self):
        self.assertEqual(parse_hotkey("SHIFT+CTRL+A"), (("CTRL", "SHIFT"), "A"))

    def test_pynput_character_key_matches_qt_token(self):
        self.assertEqual(base_from_pynput_key(FakeKey(char="A")), "A")
        self.assertEqual(base_from_pynput_key(FakeKey(char="+")), "PLUS")
        self.assertEqual(base_from_pynput_key(FakeKey(char=" ")), "SPACE")

    def test_pynput_virtual_key_matches_when_ctrl_suppresses_text(self):
        self.assertEqual(base_from_pynput_key(FakeKey(char="\x01", vk=0x41)), "A")

    def test_pynput_special_key_matches_qt_token(self):
        self.assertEqual(base_from_pynput_key(FakeKey(name="page_up")), "PAGE_UP")
        self.assertEqual(modifier_from_pynput_key(FakeKey(name="ctrl_l")), "CTRL")

    def test_display_hotkey_is_readable(self):
        self.assertEqual(display_hotkey("CTRL+SHIFT+PAGE_UP"), "Ctrl + Shift + Page Up")

    def test_shortcut_validation_and_building(self):
        self.assertEqual(build_hotkey("a", ["SHIFT", "CTRL"]), "CTRL+SHIFT+A")
        self.assertEqual(build_hotkey("A", ["CTRL", "SHIFT"]), "CTRL+SHIFT+A")


if __name__ == "__main__":
    unittest.main()
