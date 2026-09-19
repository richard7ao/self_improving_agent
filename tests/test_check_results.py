import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.check_results import build_report, render


class CheckResultsTests(unittest.TestCase):
    def test_reports_active_and_latest_complete_without_stale_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp)
            complete = runs / "health-complete"
            complete.mkdir()
            (complete / "eval_result.json").write_text(
                json.dumps(
                    {
                        "domain": "health",
                        "summary": {
                            "skill_rate": 0.6,
                            "placebo_rate": 0.2,
                            "net_delta": 0.4,
                            "n_tasks": 2,
                        },
                    }
                ),
                encoding="utf-8",
            )
            for name in ("health-active", "health-stale"):
                job = runs / name / "harbor-jobs" / "job-one"
                job.mkdir(parents=True)
                (job / "result.json").write_text(
                    json.dumps(
                        {
                            "started_at": "2026-01-01T00:00:00Z",
                            "finished_at": None,
                        }
                    ),
                    encoding="utf-8",
                )

            with patch("dashboard.app._active_run_names", return_value={"health-active"}):
                report = build_report(runs, ("health",), latest=1)

        group = report["domains"]["health"]
        self.assertEqual([item["name"] for item in group["active"]], ["health-active"])
        self.assertEqual(
            [item["name"] for item in group["completed"]], ["health-complete"]
        )
        output = render(report)
        self.assertIn("skill=0.6000", output)
        self.assertNotIn("health-stale", output)


if __name__ == "__main__":
    unittest.main()
