"""Regression tests for OCR ratio selection from one screenshot."""

import unittest

from hht_ocr import parse_ratio_text, select_ratio_candidate


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
