import unittest
import tempfile
from pathlib import Path

from skilltrainbench.evaluate import delivery_summary
from skilltrainbench.tasks import Task, attempt_from_trial, score
from skilltrainbench.optimize import _delivery_failures
from skilltrainbench.optimizer_tools import classify_attempts


class EvaluateTests(unittest.TestCase):
    def test_qf_verifier_outcomes_do_not_require_text_delivery(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = Task("qfbench-train-synthetic", "synthetic", "qfbench", Path(tmp), 60)
            for reward, classification in [(1.0, "pass"), (0.0, "low_score")]:
                attempt = attempt_from_trial(task, Path(tmp), {
                    "verifier_result": {"rewards": {"reward": reward}},
                })
                row = dict(attempt, arm="skill", score=score(task, attempt))
                self.assertEqual(row["answer"], "")
                self.assertEqual(row["score"], reward)
                delivery = delivery_summary([row], ["skill"], benchmark="qfbench")
                self.assertEqual(delivery["empty_outputs_total"], 0)
                self.assertEqual(_delivery_failures({"benchmark": "qfbench", "delivery": delivery}), 0)
                self.assertEqual(classify_attempts([row])["counts"], {classification: 1})

    def test_legacy_nontext_records_use_task_id_for_delivery(self):
        for benchmark in ("qfbench", "hlebench", "tau3bench"):
            row = {"task_id": f"{benchmark}-train-example", "arm": "skill", "answer": ""}
            self.assertEqual(delivery_summary([row], ["skill"])["empty_outputs_total"], 0)

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
