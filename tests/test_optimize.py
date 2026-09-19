from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from skilltrainbench.config import load_config
from skilltrainbench.optimize import (
    Split,
    _aggregate,
    _parse_object,
    _reject_task_copy,
    _safe_relative,
    _without_grading_material,
    make_split,
    materialize_candidate,
    run_optimization,
)


class OptimizeTests(unittest.IsolatedAsyncioTestCase):
    def test_split_is_deterministic_disjoint_and_complete(self):
        names = [f"task-{index}" for index in range(10)]
        first = make_split(names, 0.2, 42)
        second = make_split(names, 0.2, 42)
        self.assertEqual(first, second)
        self.assertEqual(len(first.validation), 2)
        self.assertFalse(set(first.tune) & set(first.validation))
        self.assertEqual(set(names), set(first.tune) | set(first.validation))

    def test_single_task_uses_tune_only(self):
        self.assertEqual(make_split(["only"], 0.5, 0), Split(tune=["only"], validation=[]))

    def test_parse_fenced_json(self):
        self.assertEqual(_parse_object('```json\n{"files": []}\n```'), {"files": []})

    def test_safe_paths_reject_escape(self):
        for path in ("../SKILL.md", "/tmp/SKILL.md", "assets/file.txt", "SKILL.md/extra"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                _safe_relative(path)

    def test_grading_material_is_removed_recursively(self):
        cleaned = _without_grading_material({
            "messages": [{"role": "user", "content": "question"}],
            "rubrics": [{"criteria": "secret"}],
            "reference_answer": "secret",
        })
        self.assertEqual(cleaned, {"messages": [{"role": "user", "content": "question"}]})

    def test_materialize_valid_candidate(self):
        cfg = load_config()
        payload = {
            "rationale": "focused checklist",
            "files": [
                {"path": "SKILL.md", "content": "---\nname: test-health\ndescription: Test health skill.\n---\n\n# Method\nBe useful.\n"},
                {"path": "scripts/check.py", "content": "print('ok')\n"},
            ],
        }
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw) / "candidate"
            rationale = materialize_candidate(payload, destination, cfg)
            self.assertEqual(rationale, "focused checklist")
            self.assertTrue((destination / "SKILL.md").is_file())

    def test_materialize_rejects_external_endpoint_warning(self):
        cfg = load_config()
        payload = {"files": [{
            "path": "SKILL.md",
            "content": "---\nname: test\ndescription: Test.\n---\nVisit https://example.com\n",
        }]}
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(ValueError, "static checks"):
                materialize_candidate(payload, Path(raw) / "candidate", cfg)

    def test_training_passage_copy_is_rejected(self):
        source = "one two three four five six seven eight nine ten eleven twelve thirteen"
        with self.assertRaisesRegex(ValueError, "12-word training-task passage"):
            _reject_task_copy({"SKILL.md": f"prefix {source} suffix"}, [source])

    def test_weighted_aggregate(self):
        tune = {"summary": {"skill_rate": 0.75}}
        validation = {"summary": {"skill_rate": 0.5}}
        split = Split(tune=["a", "b", "c"], validation=["d"])
        self.assertEqual(_aggregate(tune, validation, split), 0.6875)

    async def test_loop_promotes_best_candidate_and_discards_variants(self):
        cfg = load_config()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            tasks_root = root / "tasks"
            for name in ("one", "two", "three", "four"):
                task = tasks_root / name
                task.mkdir(parents=True)
                (task / "task.toml").write_text("[agent]\ntimeout_sec = 1\n", encoding="utf-8")
            health = replace(cfg.domain("health"), dataset_dir=tasks_root)
            cfg = replace(cfg, domains={**cfg.domains, "health": health})
            live = root / "live"
            live.mkdir()
            (live / "SKILL.md").write_text(
                "---\nname: incumbent\ndescription: Initial.\n---\nincumbent\n", encoding="utf-8"
            )

            async def fake_chat(_client, _model, system, user, *, seed):
                if "Return plain text" in system:
                    return "Try clearer prioritization."
                variant = __import__("json").loads(user)["variant"]
                score = 60 if variant == 1 else 80
                return __import__("json").dumps({
                    "rationale": f"variant {variant}",
                    "files": [{
                        "path": "SKILL.md",
                        "content": (
                            f"---\nname: candidate-{variant}\ndescription: Candidate.\n---\n"
                            f"candidate-score-{score}\n"
                        ),
                    }],
                })

            async def fake_score(_cfg, _domain, skill, out, tasks, _base, _key, _concurrency):
                text = (Path(skill) / "SKILL.md").read_text(encoding="utf-8")
                value = 0.8 if "score-80" in text else 0.6 if "score-60" in text else 0.5
                out.mkdir(parents=True, exist_ok=True)
                (out / "attempts.jsonl").write_text("", encoding="utf-8")
                return {"summary": {"skill_rate": value}, "tasks": tasks}

            with patch("skilltrainbench.optimize._chat", side_effect=fake_chat), patch(
                "skilltrainbench.optimize._score", side_effect=fake_score
            ):
                result = await run_optimization(
                    cfg, "health", skill_dir=live, out=root / "run", iterations=1,
                    candidates=2, task_ids=None, limit=4, validation_fraction=0.25,
                    min_improvement=0.0, seed=42, optimizer_model="test-model",
                    upstream_base_url="http://localhost", upstream_key="test",
                    concurrency=1, candidate_parallelism=None, keep_candidates=False,
                )

            self.assertEqual(result["final_score"], 0.8)
            self.assertTrue(result["rounds"][0]["promoted"])
            self.assertIn("candidate-score-80", (live / "SKILL.md").read_text(encoding="utf-8"))
            self.assertFalse((root / "run" / "round-01" / "candidates").exists())


if __name__ == "__main__":
    unittest.main()
