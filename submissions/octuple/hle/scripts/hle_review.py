#!/usr/bin/env python3
"""Run one offline routed HLE verification and skeptical-review pass."""

from __future__ import annotations

import argparse
import json
import re
import unittest
from pathlib import Path
from typing import Any

import chem_check
import cs_check
import engineering_check
import exact_math
import finite_search
import image_prepare
import matrix_check
import text_transform
import tool_router


STATUSES = {"passed", "failed", "missing", "partial", "unresolved", "not_applicable"}
INCOMPLETE = {"failed", "missing", "partial", "unresolved"}


def status(record: Any) -> str:
    if not isinstance(record, dict):
        return "missing"
    value = str(record.get("status", "missing"))
    return value if value in STATUSES else "missing"


def run_check(check: dict[str, Any]) -> dict[str, Any]:
    name, operation = check.get("tool"), check.get("operation")
    data = check.get("input", {})
    result: dict[str, Any] = {"id": check.get("id"), "tool": name,
                              "operation": operation, "pass": True}
    try:
        if name == "exact_math":
            value = exact_math.calculate(data["expression"])
            output = {"value": exact_math.serializable(value)}
            if "expected" in data:
                expected = exact_math.calculate(data["expected"])
                output.update({"expected": exact_math.serializable(expected),
                               "matches": float(value) == float(expected)})
                result["pass"] = output["matches"]
        elif name == "finite_search":
            output = finite_search.search(data["domains"], data["constraint"], int(data.get("max_cases", 100000)))
        elif name == "matrix_check":
            if operation == "determinant":
                output = {"determinant": matrix_check.show(matrix_check.determinant(data["matrix"]))}
            elif operation == "rank":
                output = {"rank": matrix_check.rank(data["matrix"])}
            elif operation == "solve":
                output = {"solution": [matrix_check.show(value) for value in matrix_check.solve(data["matrix"], data["vector"])]}
            else:
                raise ValueError("matrix_check requires determinant, rank, or solve")
        elif name == "text_transform":
            transformed = text_transform.transform(operation, data["text"], int(data.get("shift", 13)))
            output = {"output": transformed}
        elif name == "cs_check":
            output = cs_check.run(operation, data)
        elif name == "chem_check":
            output = chem_check.run(operation, data)
        elif name == "engineering_check":
            output = engineering_check.run(operation, data)
        elif name == "image_prepare":
            if operation == "discover":
                output = {"images": [{"path": str(path), "dimensions": image_prepare.dimensions(path)}
                                     for path in image_prepare.discover(Path(data.get("root", "/app")))]}
            elif operation == "inspect":
                path = Path(data["path"])
                output = {"path": str(path), "dimensions": image_prepare.dimensions(path)}
            else:
                raise ValueError("image_prepare dispatcher supports discover or inspect")
        elif name == "answer_format":
            answer = str(data.get("answer", ""))
            kind = data.get("kind", "exactMatch")
            passed = bool(answer.strip()) and "\n" not in answer
            if kind == "multipleChoice":
                passed = answer.strip() in [str(option) for option in data.get("options", [])]
            elif kind == "number":
                try:
                    float(answer)
                except ValueError:
                    passed = False
            elif kind == "integer":
                passed = re.fullmatch(r"[+-]?\d+", answer.strip()) is not None
            if data.get("pattern"):
                passed = passed and re.fullmatch(data["pattern"], answer) is not None
            output = {"valid": passed}
            result["pass"] = passed
        else:
            raise ValueError(f"unsupported routed tool: {name}")
        result["output"] = output
    except (KeyError, TypeError, ValueError, ZeroDivisionError, OSError) as error:
        result.update({"pass": False, "error": str(error)})
    return result


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept the documented schema plus a compact explicit legacy record."""
    if isinstance(payload.get("classification"), dict):
        return payload
    if not payload.get("domain") or not payload.get("task_type"):
        return payload
    normalized = dict(payload)
    raw_type = payload["task_type"]
    type_items = [raw_type] if isinstance(raw_type, str) else list(raw_type)
    answer_type = payload.get("answer_type")
    if not answer_type:
        answer_type = "multipleChoice" if any("multiple_choice" in str(item) for item in type_items) else "exactMatch"
    normalized["classification"] = {
        "domain": payload["domain"], "task_types": type_items, "answer_type": answer_type,
        "has_image": bool(payload.get("has_image", False)), "features": payload.get("features", []),
    }
    candidate = payload.get("candidate") if isinstance(payload.get("candidate"), dict) else {}
    competitor = payload.get("competitor") if isinstance(payload.get("competitor"), dict) else {}
    normalized.setdefault("interpreted_question", payload.get("question_summary", ""))
    normalized.setdefault("proposed_answer", candidate.get("answer", candidate.get("claim", "")))
    normalized.setdefault("strongest_competitor", competitor.get("answer", competitor.get("claim", "")))
    ledger = payload.get("variable_ledger") if isinstance(payload.get("variable_ledger"), dict) else {}
    normalized.setdefault("variables", [{"name": name, "role": role, "explained": True, "reason": role}
                                         for name, role in ledger.items()])
    normalized.setdefault("assumptions", [])
    normalized.setdefault("conventions", [])
    normalized.setdefault("derivation", {"status": "passed" if candidate.get("derivation") else "missing"})
    normalized.setdefault("sufficiency", {"status": "not_applicable"})
    normalized.setdefault("necessity", {"status": "not_applicable"})
    normalized.setdefault("uniqueness", {"status": "not_applicable"})
    checks = payload.get("discriminating_checks") if isinstance(payload.get("discriminating_checks"), list) else []
    normalized.setdefault("counterexamples_attempted", [
        {"kind": "discriminating", "outcome": "refuted", "evidence": str(item)} for item in checks
    ])
    normalized.setdefault("confidence", payload.get("confidence_requested", 0))
    normalized.setdefault("final_format", {"kind": answer_type})
    normalized.setdefault("checks", [])
    return normalized


def review(payload: dict[str, Any]) -> dict[str, Any]:
    payload = normalize_payload(payload)
    classification = payload.get("classification")
    if not isinstance(classification, dict):
        raise ValueError("classification must be an object")
    route = tool_router.route(classification)
    variables = payload.get("variables") if isinstance(payload.get("variables"), list) else []
    unused = [str(item.get("name", "?")) for item in variables
              if isinstance(item, dict) and not item.get("explained")]
    conventions = payload.get("conventions") if isinstance(payload.get("conventions"), list) else []
    unresolved_conventions = [item for item in conventions
                              if isinstance(item, dict) and not item.get("resolved")]
    attempts = payload.get("counterexamples_attempted")
    attempts = attempts if isinstance(attempts, list) else []
    surviving = [item for item in attempts if isinstance(item, dict)
                 and item.get("outcome") in {"survived", "inconclusive"}]
    checks = [run_check(item) for item in payload.get("checks", []) if isinstance(item, dict)]
    task_types = set(route["task_types"])
    necessity_required = bool(task_types & {"necessity", "minimum", "maximum", "proof"})
    uniqueness_required = "uniqueness" in task_types
    image_central = bool(route["has_image"] and payload.get("image_detail_central", True))
    objections: list[str] = []
    for field in ("interpreted_question", "proposed_answer", "strongest_competitor"):
        if not str(payload.get(field, "")).strip():
            objections.append(f"{field} is missing")
    if status(payload.get("derivation")) in INCOMPLETE:
        objections.append("derivation is incomplete")
    if necessity_required and status(payload.get("necessity")) in INCOMPLETE:
        objections.append("required necessity/minimality check is incomplete")
    if uniqueness_required and status(payload.get("uniqueness")) in INCOMPLETE:
        objections.append("required uniqueness check is incomplete")
    if task_types & {"existence", "sufficiency", "minimum", "maximum", "proof"} and status(payload.get("sufficiency")) in INCOMPLETE:
        objections.append("required sufficiency/achievability check is incomplete")
    if task_types & {"minimum", "maximum", "uniqueness", "proof"} and not attempts:
        objections.append("no adversarial counterexample or boundary attempt")
    if unused:
        objections.append("central variables remain unexplained: " + ", ".join(unused))
    if unresolved_conventions:
        objections.append("unit or sign conventions remain unresolved")
    if surviving:
        objections.append("a counterexample or objection survived")
    if any(not check["pass"] for check in checks):
        objections.append("a deterministic check failed")
    if not isinstance(payload.get("final_format"), dict):
        objections.append("final format contract is missing")

    requested = max(0, min(100, int(payload.get("confidence", 0))))
    caps: list[int] = []
    if necessity_required and status(payload.get("necessity")) != "passed":
        caps.append(55)
    if uniqueness_required and status(payload.get("uniqueness")) != "passed":
        caps.append(55)
    if unused:
        caps.append(50)
    if unresolved_conventions:
        caps.append(60)
    if image_central and not payload.get("image_detail_verified", False):
        caps.append(65)
    if surviving:
        caps.append(0)
    calibrated = min([requested, *caps])
    corrected = payload.get("corrected_answer")
    return {
        "task_classification": {key: route[key] for key in ("domain", "task_types", "answer_type", "has_image", "features")},
        "tool_plan": route["human_plan"], "proposed_answer": payload.get("proposed_answer"),
        "strongest_competitor": payload.get("strongest_competitor"),
        "derivation_status": status(payload.get("derivation")),
        "deterministic_checks": checks, "sufficiency_status": status(payload.get("sufficiency")),
        "necessity_minimality_status": status(payload.get("necessity")),
        "uniqueness_status": status(payload.get("uniqueness")), "unused_variables": unused,
        "assumptions": payload.get("assumptions", []), "counterexamples_attempted": attempts,
        "surviving_objections": objections, "corrected_answer": corrected,
        "final_answer": corrected if corrected not in (None, "") else payload.get("proposed_answer"),
        "requested_confidence": requested, "confidence_caps": caps,
        "calibrated_confidence": calibrated, "final_format_status": "present" if isinstance(payload.get("final_format"), dict) else "missing",
        "warnings": route["warnings"], "approved": not objections,
    }


class SelfTests(unittest.TestCase):
    def test_approved_and_confidence_caps(self) -> None:
        base = {"classification": {"domain": "engineering_physics", "task_types": ["minimum"], "answer_type": "expression", "has_image": False, "features": ["matrix", "rank"]},
                "interpreted_question": "exact minimum under stated model", "proposed_answer": "k", "strongest_competitor": "k-1",
                "variables": [{"name": "d", "explained": True}], "assumptions": [], "conventions": [],
                "derivation": {"status": "passed"}, "sufficiency": {"status": "passed"}, "necessity": {"status": "passed"},
                "uniqueness": {"status": "not_applicable"}, "counterexamples_attempted": [{"kind": "boundary", "outcome": "refuted"}],
                "confidence": 88, "final_format": {"kind": "expression"}, "checks": []}
        self.assertTrue(review(base)["approved"])
        broken = json.loads(json.dumps(base))
        broken["necessity"] = {"status": "missing"}
        broken["variables"][0]["explained"] = False
        result = review(broken)
        self.assertFalse(result["approved"])
        self.assertEqual(result["calibrated_confidence"], 50)

    def test_dispatches_domain_check(self) -> None:
        result = run_check({"tool": "chem_check", "operation": "formula", "input": {"formula": "H2O"}})
        self.assertTrue(result["pass"])
        self.assertEqual(result["output"]["atoms"], {"H": 2, "O": 1})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests)).wasSuccessful() else 1
    if not args.input:
        parser.error("--input is required")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = review(payload)
    print(json.dumps(result, indent=2))
    return 0 if result["approved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
