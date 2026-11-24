"""Regression tests for OCR ratio selection from one screenshot."""

import unittest

from PIL import Image, ImageDraw

from hht_ocr import (
    confirm_income_pair,
    parse_ratio_text,
    select_ratio_candidate,
    should_enter_precision_mode,
    visual_change_ratio,
)


class ConfirmIncomePairTests(unittest.TestCase):
    def test_small_initial_income_increment_is_accepted(self):
        current, maximum, note = confirm_income_pair(0, 1500, 4, 1500)
        self.assertEqual((current, maximum), (4, 1500))
        self.assertIn("небольшое изменение", note)

    def test_small_reverse_ocr_variation_uses_larger_reading(self):
        current, maximum, _ = confirm_income_pair(4, 1500, 0, 1500)
        self.assertEqual((current, maximum), (4, 1500))

    def test_large_income_difference_is_rejected(self):
        self.assertEqual(confirm_income_pair(0, 1500, 40, 1500)[:2], (None, None))

    def test_different_targets_are_rejected(self):
        self.assertEqual(confirm_income_pair(0, 1500, 4, 1900)[:2], (None, None))


class PrecisionIncomeModeTests(unittest.TestCase):
    def test_precision_mode_starts_in_final_thirty_percent(self):
        self.assertFalse(should_enter_precision_mode(1049, 1500))
        self.assertTrue(should_enter_precision_mode(1050, 1500))
        self.assertTrue(should_enter_precision_mode(1330, 1900))
        self.assertFalse(should_enter_precision_mode(1329, 1900))

    def test_precision_mode_handles_missing_or_invalid_values(self):
        self.assertFalse(should_enter_precision_mode(None, 1500))
        self.assertFalse(should_enter_precision_mode(1400, None))
        self.assertFalse(should_enter_precision_mode(0, 0))
        self.assertTrue(should_enter_precision_mode(1600, 1500))

    def test_precision_mode_rejects_invalid_window(self):
        with self.assertRaises(ValueError):
            should_enter_precision_mode(100, 1500, window_ratio=1.5)


class SelectRatioCandidateTests(unittest.TestCase):
    def test_full_ratio_is_parsed_normally(self):
        self.assertEqual(parse_ratio_text("268/700"), [(268, 700, "268/700")])

    def test_numerator_only_uses_previously_confirmed_maximum(self):
        result = parse_ratio_text("310", expected_max=700)
        self.assertEqual(result[0][0:2], (310, 700))
        self.assertIn("700", result[0][2])

    def test_numerator_only_is_not_accepted_without_confirmed_maximum(self):
        self.assertEqual(parse_ratio_text("310"), [])

    def test_multiple_unseparated_numbers_are_not_accepted_as_numerator(self):
        self.assertEqual(parse_ratio_text("310 700", expected_max=700), [])

    def test_numerator_above_confirmed_maximum_is_rejected(self):
        self.assertEqual(parse_ratio_text("710", expected_max=700), [])

    def test_denominator_only_is_not_misread_as_full_energy(self):
        self.assertEqual(parse_ratio_text("700", expected_max=700), [])

    def test_single_complete_ratio_is_provisional_not_rejected(self):
        result = select_ratio_candidate([(292, 700, "292/700")])

        self.assertEqual(result[0:2], (292, 700))
        self.assertIn("второго снимка", result[2])

    def test_two_matching_denominator_votes_keep_largest_numerator(self):
        result = select_ratio_candidate([
            (70, 700, "70/700"),
            (292, 700, "292/700"),
            (290, 700, "290/700"),
        ])

        self.assertEqual(result[0:2], (292, 700))

    def test_conflicting_single_candidates_are_rejected(self):
        result = select_ratio_candidate([
            (292, 700, "292/700"),
            (29, 100, "29/100"),
        ])

        self.assertEqual(result[0:2], (None, None))
        self.assertIn("противоречивые", result[2])

    def test_empty_candidates_are_rejected(self):
        self.assertEqual(select_ratio_candidate([]), (None, None, ""))


if __name__ == "__main__":
    unittest.main()



class VisualRewardChangeTests(unittest.TestCase):
    def test_identical_images_have_no_change(self):
        before = Image.new("RGB", (100, 100), "black")
        after = before.copy()
        self.assertEqual(visual_change_ratio(before, after, (10, 10, 90, 90)), 0.0)

    def test_large_button_region_change_is_detected(self):
        before = Image.new("RGB", (100, 100), "black")
        after = before.copy()
        ImageDraw.Draw(after).rectangle((20, 35, 80, 65), fill="white")
        ratio = visual_change_ratio(before, after, (10, 10, 90, 90))
        self.assertGreaterEqual(ratio, 0.08)

    def test_small_cursor_like_change_does_not_pass_reward_gate(self):
        before = Image.new("RGB", (100, 100), "black")
        after = before.copy()
        ImageDraw.Draw(after).rectangle((45, 45, 50, 50), fill="white")
        ratio = visual_change_ratio(before, after, (10, 10, 90, 90))
        self.assertLess(ratio, 0.08)


if __name__ == "__main__":
    unittest.main()
