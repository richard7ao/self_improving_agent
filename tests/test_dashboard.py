import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dashboard.app import collect_job_results, collect_runs


class DashboardTests(unittest.TestCase):
    def test_collects_completed_and_running_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp)
            completed = runs / "health-complete"
            completed.mkdir()
            (completed / "eval_result.json").write_text(
                json.dumps(
                    {
                        "domain": "health",
                        "benchmark": "healthbench",
                        "summary": {
                            "skill_rate": 0.7,
                            "placebo_rate": 0.2,
                            "net_delta": 0.5,
                            "n_tasks": 2,
                            "n_pairs": 2,
                        },
                        "delivery": {"empty_outputs_total": 0},
                        "learner": {
                            "model": "test-model",
                            "agent_kwargs": {"max_iterations": 4},
                        },
                        "learner_usage": {"total_tokens": 100},
                        "grader_usage": {"total_tokens": 50},
                        "learner_cost": {"estimated_usd": 0.01},
                        "grader_cost": {"estimated_usd": 0.02},
                    }
                ),
                encoding="utf-8",
            )
            (completed / "attempts.jsonl").write_text("{}\n{}\n", encoding="utf-8")

            active = runs / "hle-active" / "harbor-jobs" / "job-1"
            active.mkdir(parents=True)
            (active / "result.json").write_text(
                json.dumps({"started_at": "2026-01-01T00:00:00Z", "finished_at": None}),
                encoding="utf-8",
            )

            with patch("dashboard.app._active_run_names", return_value={"hle-active"}):
                payload = collect_runs(runs)

        self.assertEqual(payload["count"], 2)
        by_name = {record["name"]: record for record in payload["runs"]}
        health = by_name["health-complete"]
        self.assertEqual(health["status"], "complete")
        self.assertEqual(health["net_delta"], 0.5)
        self.assertEqual(health["tokens"], 150)
        self.assertEqual(health["cost_usd"], 0.03)
        self.assertEqual(health["attempts"], 2)
        self.assertEqual(health["max_iterations"], 4)
        hle = by_name["hle-active"]
        self.assertEqual(hle["status"], "running")
        self.assertEqual(hle["jobs"], 1)
        self.assertEqual(hle["jobs_running"], 1)

    def test_nested_evaluations_are_each_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp)
            for child, score in (("initial", 0.1), ("round-01/candidate", 0.2)):
                directory = runs / "health-opt" / child
                directory.mkdir(parents=True)
                (directory / "eval_result.json").write_text(
                    json.dumps({"domain": "health", "summary": {"skill_rate": score}}),
                    encoding="utf-8",
                )
            payload = collect_runs(runs)

        names = {record["name"] for record in payload["runs"]}
        self.assertEqual(
            names,
            {"health-opt/initial", "health-opt/round-01/candidate"},
        )

    def test_collects_individual_job_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp)
            run = runs / "health-detail"
            job = run / "harbor-jobs" / "task-name-deadbeef"
            trial = job / "task__abc" / "agent"
            trial.mkdir(parents=True)
            (trial / "response.txt").write_text("answer", encoding="utf-8")
            (job / "result.json").write_text(
                json.dumps(
                    {
                        "started_at": "2026-01-01T00:00:00Z",
                        "finished_at": "2026-01-01T00:00:10Z",
                        "stats": {
                            "n_errored_trials": 0,
                            "n_input_tokens": 20,
                            "n_output_tokens": 5,
                            "evals": {"test": {"metrics": [{"mean": 0.75}]}},
                        },
                    }
                ),
                encoding="utf-8",
            )
            (run / "attempts.jsonl").write_text(
                json.dumps(
                    {
                        "task_id": "task-name",
                        "arm": "skill",
                        "score": 0.75,
                        "passed": True,
                        "status": "ok",
                        "trial_dir": str(job / "task__abc"),
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            detail = collect_job_results("health-detail", runs)

        self.assertEqual(detail["count"], 1)
        result = detail["jobs"][0]
        self.assertEqual(result["arm"], "skill")
        self.assertEqual(result["score"], 0.75)
        self.assertEqual(result["response_bytes"], 6)
        self.assertEqual(result["duration_seconds"], 10.0)

    def test_job_detail_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                collect_job_results("../outside", Path(tmp))


if __name__ == "__main__":
    unittest.main()
