import unittest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from skilltrainbench.evaluate import delivery_summary, _attempt_with_retries
from skilltrainbench.tasks import Task, attempt_from_trial, score
from skilltrainbench.optimize import _delivery_failures
from skilltrainbench.optimizer_tools import classify_attempts


class EvaluateTests(unittest.TestCase):
    def test_upstream_crash_is_not_a_scored_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "agent").mkdir()
            log = root / "agent/openhands_sdk.txt"
            log.write_text("Traceback (most recent call last):\nlitellm.exceptions.APIError: provider failed\n")
            task = Task("qfbench-train-synthetic", "synthetic", "qfbench", root, 60)
            result = {"verifier_result": {"rewards": {"reward": 0.0}},
                      "exception_info": {"exception_type": "NonZeroAgentExitCodeError"}}
            failed = attempt_from_trial(task, root, result)
            self.assertEqual(failed["status"], "infra_error")
            self.assertEqual(failed["error_class"], "runtime_upstream_failure")
            # An ordinary failed solution command must remain a learner failure.
            log.write_text("ValueError: incorrect shape in the learner's program\n")
            self.assertEqual(attempt_from_trial(task, root, result)["status"], "ok")
            log.write_text("litellm.exceptions.APIError: 402 Payment Required: budget exhausted\n")
            self.assertEqual(attempt_from_trial(task, root, result)["status"], "budget_exhausted")

    def test_upstream_failures_retry_but_wrong_answers_do_not(self):
        task = Task("qfbench-train-synthetic", "synthetic", "qfbench", Path("/unused"), 60)
        for status, expected_calls in [("infra_error", 2), ("ok", 1)]:
            runner = AsyncMock(side_effect=[{"status": status}, {"status": "ok"}])
            async def run():
                return await _attempt_with_retries(task, None, asyncio.Semaphore(1),
                                                   registry=None, tags={})
            with patch("skilltrainbench.evaluate.harbor.run_attempt", runner), \
                 patch("skilltrainbench.evaluate._RETRY_DELAYS", (0.0,)):
                attempt = asyncio.run(run())
            self.assertEqual(runner.await_count, expected_calls)
            self.assertIsNone(attempt["error"])

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
