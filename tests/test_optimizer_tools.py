from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skilltrainbench.optimizer_tools import (
    append_registry,
    audit_generated_scripts,
    budget_forecast,
    candidate_diversity,
    classify_attempts,
    duplicate_candidate_indexes,
    paired_statistics,
    promotion_gate,
    safety_regression_gate,
    semantic_leakage_report,
    stratified_split,
)


class OptimizerToolsTests(unittest.TestCase):
    def _skill(self, root: Path, name: str, body: str) -> Path:
        path = root / name
        path.mkdir()
        (path / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: test\n---\n{body}\n", encoding="utf-8"
        )
        return path

    def test_candidate_diversity_and_duplicates(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = self._skill(root, "first", "alpha beta gamma")
            second = self._skill(root, "second", "alpha beta gamma")
            third = self._skill(root, "third", "different material")
            # Names differ in frontmatter, so force a byte-identical duplicate.
            (second / "SKILL.md").write_text((first / "SKILL.md").read_text(), encoding="utf-8")
            self.assertEqual(duplicate_candidate_indexes([first, second, third]), {1})
            self.assertEqual(candidate_diversity([first, second, third])["exact_duplicate_pairs"], 1)

    def test_generated_script_audit_blocks_network_and_dynamic_code(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "bad.py").write_text("import socket\neval('1 + 1')\n", encoding="utf-8")
            result = audit_generated_scripts(root)
            self.assertFalse(result["ok"])
            self.assertIn("blocked_import:socket:1", result["scripts"][0]["issues"])
            self.assertIn("blocked_call:eval:2", result["scripts"][0]["issues"])

    def test_stratified_split_is_disjoint_and_preserves_groups(self):
        records = [{"task_id": f"a-{index}", "stratum": "a"} for index in range(4)]
        records += [{"task_id": f"b-{index}", "stratum": "b"} for index in range(4)]
        result = stratified_split(records, 0.25, 7)
        self.assertFalse(set(result["tune"]) & set(result["validation"]))
        self.assertEqual(result["allocation"], {
            "a": {"tune": 3, "validation": 1}, "b": {"tune": 3, "validation": 1},
        })

    def test_failure_classification(self):
        result = classify_attempts([
            {"task_id": "empty", "answer": "", "score": 0.0, "status": "ok"},
            {"task_id": "bad", "answer": "x", "score": 0.2, "status": "ok"},
            {"task_id": "good", "answer": "x", "score": 0.8, "status": "ok"},
        ])
        self.assertEqual(result["counts"], {"delivery_failure": 1, "low_score": 1, "pass": 1})

    def test_paired_statistics_and_promotion_gate(self):
        incumbent_tune = {"a": 0.2, "b": 0.3, "c": 0.4}
        challenger_tune = {"a": 0.5, "b": 0.6, "c": 0.7}
        incumbent_validation = {"v1": 0.2, "v2": 0.3}
        challenger_validation = {"v1": 0.5, "v2": 0.6}
        stats = paired_statistics(incumbent_tune, challenger_tune, iterations=100, seed=1)
        self.assertAlmostEqual(stats["mean_delta"], 0.3)
        gate = promotion_gate(incumbent_tune, challenger_tune, incumbent_validation,
                              challenger_validation, bootstrap_iterations=100, seed=1)
        self.assertTrue(gate["promote"])

    def test_safety_gate_is_non_compensatory(self):
        result = safety_regression_gate(
            {"critical": 1.0, "routine": 0.0}, {"critical": 0.9, "routine": 1.0},
            {"critical": ["emergency"], "routine": ["routine"]},
            critical_labels=["emergency"],
        )
        self.assertFalse(result["ok"])

    def test_semantic_leakage_heuristic(self):
        with tempfile.TemporaryDirectory() as raw:
            skill = self._skill(Path(raw), "candidate", "alpha beta gamma delta epsilon zeta")
            result = semantic_leakage_report(
                skill, {"task": "alpha beta gamma delta epsilon zeta eta theta"},
                shingle_width=3, warn_jaccard=0.1,
            )
            self.assertFalse(result["ok"])

    def test_budget_and_atomic_registry(self):
        forecast = budget_forecast(tasks=8, candidates=3, rounds=2, repeats=2,
                                   learner_tokens_per_attempt=100)
        self.assertGreater(forecast["attempts"]["total"], 0)
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "registry.json"
            append_registry(path, {"name": "first"})
            append_registry(path, {"name": "second"})
            self.assertEqual(len(json.loads(path.read_text())), 2)


if __name__ == "__main__":
    unittest.main()
