import unittest

from skilltrainbench.evaluate import delivery_summary


class EvaluateTests(unittest.TestCase):
    def test_delivery_summary_tracks_empty_outputs_per_arm(self):
        rows = [
            {"arm": "placebo", "answer": "complete"},
            {"arm": "placebo", "answer": "  "},
            {"arm": "skill", "answer": ""},
            {"arm": "skill", "answer": "complete"},
        ]

        result = delivery_summary(rows, ["placebo", "skill"])

        self.assertEqual(result["empty_outputs_by_arm"], {"placebo": 1, "skill": 1})
        self.assertEqual(result["empty_outputs_total"], 2)
        self.assertIn("delivery failures", result["note"])
