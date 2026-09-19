from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from skilltrainbench.config import load_config
from skilltrainbench.optimize import (
    Split,
    _aggregate,
    _delivery_failures,
    _parse_object,
    _reject_task_copy,
    _safe_relative,
    _without_grading_material,
    _observations,
    _should_promote,
    _trajectory_evidence,
    make_split,
    materialize_candidate,
    run_optimization,
)


class OptimizeTests(unittest.IsolatedAsyncioTestCase):
    def test_tune_gain_cannot_hide_validation_regression_or_tie(self):
        result = lambda value: {"summary": {"skill_rate": value}}
        split = Split(tune=["a", "b"], validation=["c"])
        for validation in (0.0, 0.5):
            self.assertFalse(_should_promote(result(0), result(0.5), result(1),
                                            result(validation), split, 0))
        self.assertTrue(_should_promote(result(0), result(0.5), result(1), result(1), split, 0))

    def test_review_uses_only_tune_learner_trajectory(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            agent = root / "trial" / "agent"
            agent.mkdir(parents=True)
            (agent / "trajectory.json").write_text(json.dumps({"steps": [
                {"source": "system", "message": "secret-system"},
                {"source": "agent", "message": "calculation finished",
                 "reasoning_content": "secret-reasoning", "tool_calls": [],
                 "observation": {"results": [{"content": "sum=1"}]}}
            ]}))
            (root / "attempts.jsonl").write_text("\n".join(json.dumps(row) for row in [
                {"task_name": "tune", "trial_dir": str(agent.parent), "answer": ""},
                {"task_name": "validation", "answer": "secret-validation"}]))
            evidence = _observations(root, {}, {"tune": {}})
            self.assertIn("calculation finished", evidence)
            self.assertIn("sum=1", evidence)
            self.assertNotIn("secret-", evidence)

    def test_trajectory_cannot_escape_evaluation_directory(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            outside = root / "outside" / "agent"
            outside.mkdir(parents=True)
            (outside / "trajectory.json").write_text('{"steps": []}')
            evaluation = root / "evaluation"
            evaluation.mkdir()
            (evaluation / "linked-trial").symlink_to(outside.parent)
            self.assertEqual(_trajectory_evidence(evaluation, str(outside.parent))["status"],
                             "outside_evaluation")
            self.assertEqual(_trajectory_evidence(evaluation, str(evaluation / "linked-trial"))["status"],
                             "outside_evaluation")

    def test_trajectory_retains_latest_steps_with_bounded_size(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            agent = root / "trial" / "agent"
            agent.mkdir(parents=True)
            (agent / "trajectory.json").write_text(json.dumps({"steps": [
                {"source": "agent", "step_id": index, "message": "x" * 5000}
                for index in range(100)
            ]}))
            evidence = _trajectory_evidence(root, str(agent.parent))
            self.assertEqual(evidence["steps"][-1]["step_id"], 99)
            self.assertLess(len(json.dumps(evidence)), 19000)


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
            ],
        }
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw) / "candidate"
            rationale = materialize_candidate(payload, destination, cfg)
            self.assertEqual(rationale, "focused checklist")
            self.assertTrue((destination / "SKILL.md").is_file())

    def test_materialize_requires_skill_to_route_supporting_files(self):
        cfg = load_config()
        payload = {
            "files": [
                {"path": "SKILL.md", "content": "---\nname: test\ndescription: Test.\n---\nUse the method.\n"},
                {"path": "scripts/check.py", "content": "print('ok')\n"},
            ],
        }
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(ValueError, "not routed from SKILL.md"):
                materialize_candidate(payload, Path(raw) / "candidate", cfg)

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

    def test_delivery_failures_are_separate_from_quality_score(self):
        result = {
            "summary": {"skill_rate": 0.9},
            "delivery": {"empty_outputs_total": 2},
        }
        self.assertEqual(_delivery_failures(result), 2)
        self.assertEqual(_delivery_failures({"summary": {"skill_rate": 0.0}}), 0)

    def test_legacy_qf_empty_answer_counts_do_not_block_candidates(self):
        for identity in ({"domain": "qf"}, {"benchmark": "qfbench"}):
            self.assertEqual(_delivery_failures({**identity, "delivery": {"empty_outputs_total": 2}}), 0)
        self.assertEqual(_delivery_failures({"domain": "health", "delivery": {"empty_outputs_total": 2}}), 2)

    def test_qf_review_preserves_verifier_and_runtime_outcomes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            rows = [
                {"task_name": "pass", "answer": "", "score": 1.0, "status": "ok"},
                {"task_name": "wrong", "answer": "", "score": 0.0, "status": "ok"},
                {"task_name": "infra", "answer": "", "score": None, "status": "infra_error"},
                {"task_name": "held-back", "answer": "", "score": 1.0, "status": "ok"},
            ]
            (root / "attempts.jsonl").write_text("\n".join(json.dumps(row) for row in rows))
            evidence = json.loads(_observations(root, {"benchmark": "qfbench"},
                                                {name: {} for name in ("pass", "wrong", "infra")}))
            self.assertEqual(evidence["failure_summary"]["counts"],
                             {"pass": 1, "low_score": 1, "infrastructure_failure": 1})
            self.assertEqual(len(evidence["attempts"]), 3)

    def test_qf_toolkit_can_be_materialized_as_candidate(self):
        skill = Path(__file__).resolve().parents[1] / "submissions/octuple/qf"
        files = [{"path": p.relative_to(skill).as_posix(), "content": p.read_text()}
                 for p in skill.rglob("*") if p.is_file() and p.suffix in {".md", ".py"}]
        with tempfile.TemporaryDirectory() as raw:
            materialize_candidate({"files": files, "rationale": "compatibility check"},
                                  Path(raw) / "candidate", load_config())

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

            async def fake_chat(_client, _model, system, user, *, seed, json_mode=False):
                if "Return plain text" in system:
                    return "Try clearer prioritization."
                variant = __import__("json").loads(user)["variant"]
                score = 60 if variant == 1 else 80
                return __import__("json").dumps({
                    "rationale": f"variant {variant}",
                    "confidence": "high" if variant == 2 else "medium",
                    "calculations": [{
                        "check": "weighted candidate score",
                        "confidence": "high",
                        "tool": None,
                    }],
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
            winner = next(
                candidate for candidate in result["rounds"][0]["candidates"]
                if candidate.get("index") == 2
            )
            self.assertEqual(winner["confidence"], "high")
            self.assertEqual(winner["calculations"][0]["check"], "weighted candidate score")
            self.assertIn("candidate-score-80", (live / "SKILL.md").read_text(encoding="utf-8"))
            self.assertFalse((root / "run" / "round-01" / "candidates").exists())


if __name__ == "__main__":
    unittest.main()
