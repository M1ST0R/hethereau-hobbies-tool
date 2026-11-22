"""Regression tests for OCR ratio selection from one screenshot."""

import unittest

from hethereau_hobbies_tool import select_ratio_candidate


class SelectRatioCandidateTests(unittest.TestCase):
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
