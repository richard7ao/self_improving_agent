#!/usr/bin/env python3
"""One-call deterministic validation, archival, and exact response delivery."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

QUALITY = Path(__file__).resolve().parent / "quality"
DATA = Path(__file__).resolve().parent / "data"
sys.path.insert(0, str(QUALITY))
sys.path.insert(0, str(DATA))

from claim_audit import check as check_claims  # noqa: E402
from constraint_check import check as check_constraints  # noqa: E402
from coverage_check import check as check_coverage  # noqa: E402
from evidence_ledger import check as check_evidence  # noqa: E402
from response_delivery import deliver  # noqa: E402
from toolkit_common import ToolError, atomic_write  # noqa: E402
from urgency_ladder import check as check_urgency  # noqa: E402
from dose_math import dose as calculate_dose  # noqa: E402
from lab_trend import trend as calculate_lab_trend  # noqa: E402
from medication_reconcile import reconcile as reconcile_medications  # noqa: E402
from record_summary import structure as structure_record  # noqa: E402
from timeline_normalizer import normalize as normalize_timeline  # noqa: E402
from unit_math import calculate as calculate_units  # noqa: E402

MAX_INPUT_BYTES = 1_000_000
DEFAULT_OUTPUT = Path("/logs/agent/response.txt")
DEFAULT_ARCHIVE = Path("/logs/agent/questions")
ALLOWED_FIELDS = {"draft", "constraints", "evidence", "coverage", "urgency", "archive_question", "operations"}
MAX_OPERATIONS = 20
OPERATIONS = {
    "timeline": normalize_timeline,
    "lab_trend": calculate_lab_trend,
    "medication_reconcile": reconcile_medications,
    "unit_math": calculate_units,
    "dose_math": calculate_dose,
    "record_summary": structure_record,
}


def _read_payload(path: str | None) -> dict[str, Any]:
    if path in (None, "-"):
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    else:
        with Path(path).open("rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ToolError(f"input exceeds {MAX_INPUT_BYTES} bytes")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ToolError(f"input must be UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ToolError("payload must be a JSON object")
    unknown = sorted(set(value) - ALLOWED_FIELDS)
    if unknown:
        raise ToolError(f"unknown payload fields: {unknown}")
    return value


def _validate_payload(value: dict[str, Any]) -> str:
    draft = value.get("draft")
    if not isinstance(draft, str) or not draft.strip():
        raise ToolError("draft must be a non-empty string")
    if len(draft.encode("utf-8")) > MAX_INPUT_BYTES:
        raise ToolError("draft exceeds input limit")
    for field in ("constraints", "evidence", "coverage", "urgency"):
        if field in value and not isinstance(value[field], dict):
            raise ToolError(f"{field} must be an object")
    for field in ("constraints", "coverage"):
        if field in value and "text" in value[field]:
            raise ToolError(f"{field}.text is reserved; the dispatcher always checks draft")
    if "archive_question" in value and not isinstance(value["archive_question"], str):
        raise ToolError("archive_question must be a string")
    if "operations" in value:
        _validate_operations(value["operations"])
    return draft


def _validate_operations(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ToolError("operations must be an array")
    if len(value) > MAX_OPERATIONS:
        raise ToolError(f"operations must contain at most {MAX_OPERATIONS} items")
    seen: set[str] = set()
    for index, raw in enumerate(value):
        if not isinstance(raw, dict) or set(raw) != {"id", "tool", "input"}:
            raise ToolError(f"operations[{index}] must contain exactly id, tool, and input")
        operation_id, tool_name, payload = raw["id"], raw["tool"], raw["input"]
        if not isinstance(operation_id, str) or re.fullmatch(r"[A-Za-z0-9_-]{1,32}", operation_id) is None:
            raise ToolError(f"operations[{index}].id must match [A-Za-z0-9_-]{{1,32}}")
        if operation_id in seen:
            raise ToolError(f"duplicate operation id: {operation_id}")
        seen.add(operation_id)
        if tool_name not in OPERATIONS:
            raise ToolError(f"unsupported operation tool: {tool_name}")
        if not isinstance(payload, dict):
            raise ToolError(f"operations[{index}].input must be an object")
    return value


def run_operations(value: object) -> dict[str, Any]:
    """Run named, independent deterministic transforms without clinical inference."""
    operations = _validate_operations(value)
    results: list[dict[str, Any]] = []
    for raw in operations:
        operation_id, tool_name, payload = raw["id"], raw["tool"], raw["input"]
        try:
            output = OPERATIONS[tool_name](payload)
        except (TypeError, ValueError) as exc:
            results.append({"id": operation_id, "tool": tool_name, "ok": False, "error": str(exc)})
        else:
            results.append({"id": operation_id, "tool": tool_name, "ok": True, "output": output})
    return {
        "ok": all(item["ok"] for item in results),
        "operation_count": len(results),
        "results": results,
        "semantic_clinical_interpretation": False,
    }


def _archive(question: str, draft: str, report: dict[str, Any], base: Path) -> dict[str, Any]:
    normalized = "\n".join(line.rstrip() for line in question.replace("\r\n", "\n").split("\n")).strip()
    if not normalized:
        raise ToolError("archive_question must not be empty")
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    folder = base / digest[:16]
    folder.mkdir(parents=True, exist_ok=True)
    if folder.is_symlink():
        raise ToolError("archive folder may not be a symlink")
    atomic_write(folder / "question.txt", (normalized + "\n").encode("utf-8"))
    atomic_write(folder / "final.txt", draft.encode("utf-8"))
    atomic_write(folder / "validation.json", (json.dumps(report, sort_keys=True, indent=2) + "\n").encode())
    return {"id": digest[:16], "path": str(folder), "question_sha256": digest}


def finalize(value: dict[str, Any], output: Path = DEFAULT_OUTPUT, archive_base: Path = DEFAULT_ARCHIVE) -> dict[str, Any]:
    draft = _validate_payload(value)
    # Delivery precedes warning-only analysis so advisory findings cannot erase a valid answer.
    delivery = deliver(draft.encode("utf-8"), output)
    checks: dict[str, Any] = {}
    check_calls = [("claims", check_claims, draft)]
    if "constraints" in value:
        check_calls.append(("constraints", check_constraints, {**value["constraints"], "text": draft}))
    if "evidence" in value:
        check_calls.append(("evidence", check_evidence, value["evidence"]))
    if "coverage" in value:
        check_calls.append(("coverage", check_coverage, {**value["coverage"], "text": draft}))
    if "urgency" in value:
        check_calls.append(("urgency", check_urgency, value["urgency"]))
    for name, function, argument in check_calls:
        try:
            checks[name] = function(argument)
        except (ToolError, TypeError, ValueError) as exc:
            checks[name] = {"ok": False, "error": str(exc)}

    warnings: list[dict[str, Any]] = []
    if checks["claims"].get("warning_count"):
        warnings.append({"check": "claims", "findings": checks["claims"]["warnings"]})
    for name in ("constraints", "evidence", "coverage", "urgency"):
        if name in checks and not checks[name].get("ok", False):
            warnings.append({"check": name, "findings": checks[name]})
    report: dict[str, Any] = {
        "ok": True,
        "delivered": True,
        "exact_match": delivery["exact_match"],
        "bytes": delivery["bytes"],
        "sha256": delivery["sha256"],
        "output": delivery["output"],
        "blocking_errors": [],
        "warnings": warnings,
        "checks": checks,
        "semantic_clinical_validation": False,
    }
    if "operations" in value:
        report["operations"] = run_operations(value["operations"])
        if not report["operations"]["ok"]:
            report["warnings"].append({"check": "operations", "findings": report["operations"]["results"]})
    if "archive_question" in value:
        try:
            report["archive"] = {"ok": True, **_archive(value["archive_question"], draft, report, archive_base)}
        except (ToolError, OSError) as exc:
            report["archive"] = {"ok": False, "error": str(exc)}
            report["warnings"].append({"check": "archive", "findings": str(exc)})
    return report


class Tests(unittest.TestCase):
    def test_exact_delivery_with_all_checks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            payload = {
                "draft": "Action today.",
                "constraints": {"required": ["Action"], "max": {"words": 3}},
                "evidence": {"reported": ["symptom"], "explicitly_denied": [], "unassessed": ["trend"]},
                "coverage": {"required_concepts": [{"name": "action", "any_of": ["Action"]}], "required_clauses": ["today"]},
                "urgency": {"actions": [{"level": "review", "action": "contact", "timeframe": "today", "triggers": ["change"]}]},
                "archive_question": "What should I do?",
            }
            result = finalize(payload, root / "response.txt", root / "questions")
            self.assertTrue(result["exact_match"])
            self.assertEqual((root / "response.txt").read_text(), payload["draft"])
            self.assertTrue(Path(result["archive"]["path"]).is_dir())

    def test_warnings_do_not_block_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "response.txt"
            result = finalize({
                "draft": "This is definitely safe.",
                "coverage": {"required_concepts": [], "required_clauses": ["missing"]},
            }, output, Path(raw) / "questions")
            self.assertTrue(result["delivered"])
            self.assertGreaterEqual(len(result["warnings"]), 2)
            self.assertTrue(output.is_file())

    def test_invalid_payload_preserves_previous_answer(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "response.txt"
            output.write_text("previous", encoding="utf-8")
            with self.assertRaises(ToolError):
                finalize({"draft": " ", "evidence": {}}, output, Path(raw) / "questions")
            self.assertEqual(output.read_text(), "previous")

    def test_evidence_conflict_is_warning_after_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = finalize({
                "draft": "Conditional answer.",
                "evidence": {"reported": ["No fever"], "explicitly_denied": ["no fever"], "unassessed": []},
            }, Path(raw) / "response.txt", Path(raw) / "questions")
            self.assertFalse(result["checks"]["evidence"]["ok"])
            self.assertTrue(result["delivered"])

    def test_analyze_runs_multiple_operations_in_order(self) -> None:
        result = run_operations([
            {"id": "convert", "tool": "unit_math", "input": {
                "operation": "convert", "value": 1, "from_unit": "kg", "to_unit": "g"
            }},
            {"id": "trend", "tool": "lab_trend", "input": {
                "series": "x", "observations": [
                    {"label": "a", "value": 10, "unit": "u"},
                    {"label": "b", "value": 15, "unit": "u"},
                ]
            }},
        ])
        self.assertEqual([item["id"] for item in result["results"]], ["convert", "trend"])
        self.assertEqual(result["results"][0]["output"]["result"]["value"], 1000)
        self.assertEqual(result["results"][1]["output"]["overall"]["delta"], 5)

    def test_bad_optional_operation_does_not_erase_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "response.txt"
            result = finalize({
                "draft": "Complete answer.",
                "operations": [{"id": "bad", "tool": "unit_math", "input": {
                    "operation": "divide", "left": 1, "right": 0
                }}],
            }, output, Path(raw) / "questions")
            self.assertTrue(result["delivered"])
            self.assertFalse(result["operations"]["ok"])
            self.assertEqual(output.read_text(), "Complete answer.")

    def test_reserved_checker_text_is_rejected_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "response.txt"
            output.write_text("previous", encoding="utf-8")
            with self.assertRaises(ToolError):
                finalize({"draft": "new", "coverage": {"text": "different"}}, output)
            self.assertEqual(output.read_text(), "previous")

    def test_one_failed_operation_does_not_hide_other_results(self) -> None:
        result = run_operations([
            {"id": "bad", "tool": "unit_math", "input": {"operation": "divide", "left": 1, "right": 0}},
            {"id": "good", "tool": "unit_math", "input": {"operation": "add", "left": 1, "right": 2}},
        ])
        self.assertFalse(result["ok"])
        self.assertFalse(result["results"][0]["ok"])
        self.assertEqual(result["results"][1]["output"]["result"], 3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    final = commands.add_parser("finalize")
    final.add_argument("--input", help="JSON file; omit or use - for stdin")
    final.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    final.add_argument("--archive-base", type=Path, default=DEFAULT_ARCHIVE)
    analyze = commands.add_parser("analyze")
    analyze.add_argument("--input", help="JSON file containing an operations array; omit or use - for stdin")
    commands.add_parser("selftest")
    args = parser.parse_args()
    if args.command == "selftest":
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    try:
        payload = _read_payload(args.input)
        if args.command == "analyze":
            if set(payload) != {"operations"}:
                raise ToolError("analyze payload must contain exactly operations")
            result = run_operations(payload["operations"])
        else:
            result = finalize(payload, args.output, args.archive_base)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (ToolError, OSError) as exc:
        print(json.dumps({"ok": False, "delivered": False, "blocking_errors": [str(exc)]}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
