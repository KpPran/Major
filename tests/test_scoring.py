
import unittest

from app.github_evidence.scoring import combine_scores


class TestCombinedScoring(unittest.TestCase):

    def test_80_20_example(self):
        result = combine_scores(47, 80, "COMPLETED", "80:20")
        self.assertEqual(result.combined_score, 53.6)

    def test_no_evidence_uses_zero_with_fixed_weights(self):
        result = combine_scores(47, None, "NO_EVIDENCE", "80:20")
        self.assertEqual(result.github_score, 0.0)
        self.assertEqual(result.combined_score, 37.6)

    def test_failed_evaluation_cannot_be_finalized(self):
        with self.assertRaises(ValueError):
            combine_scores(47, None, "EVALUATION_FAILED", "80:20")

    def test_invalid_strategy_is_rejected(self):
        with self.assertRaises(ValueError):
            combine_scores(47, 80, "COMPLETED", "90:10")

    def test_scores_outside_range_are_rejected(self):
        with self.assertRaises(ValueError):
            combine_scores(101, 80, "COMPLETED", "80:20")

        with self.assertRaises(ValueError):
            combine_scores(47, 101, "COMPLETED", "80:20")


if __name__ == "__main__":
    unittest.main(verbosity=2)
