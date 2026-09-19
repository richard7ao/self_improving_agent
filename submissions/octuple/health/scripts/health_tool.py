#!/usr/bin/env python3
"""One-call deterministic validation, archival, and exact response delivery."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

QUALITY = Path(__file__).resolve().parent / "quality"
sys.path.insert(0, str(QUALITY))

from claim_audit import check as check_claims  # noqa: E402
from constraint_check import check as check_constraints  # noqa: E402
from coverage_check import check as check_coverage  # noqa: E402
from evidence_ledger import check as check_evidence  # noqa: E402
from response_delivery import deliver  # noqa: E402
from toolkit_common import ToolError, atomic_write  # noqa: E402
from urgency_ladder import check as check_urgency  # noqa: E402

MAX_INPUT_BYTES = 1_000_000
DEFAULT_OUTPUT = Path("/logs/agent/response.txt")
DEFAULT_ARCHIVE = Path("/logs/agent/questions")
ALLOWED_FIELDS = {"draft", "constraints", "evidence", "coverage", "urgency", "archive_question"}


def _read_payload(path: str | None) -> dict[str, Any]:
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1) if path in (None, "-") else Path(path).read_bytes()
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
    if "archive_question" in value and not isinstance(value["archive_question"], str):
        raise ToolError("archive_question must be a string")
    # Validate optional contracts before replacing an existing valid response.
    if "constraints" in value:
        check_constraints({"text": draft, **value["constraints"]})
    if "evidence" in value:
        check_evidence(value["evidence"])
    if "coverage" in value:
        check_coverage({"text": draft, **value["coverage"]})
    if "urgency" in value:
        check_urgency(value["urgency"])
    return draft


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
    checks: dict[str, Any] = {"claims": check_claims(draft)}
    if "constraints" in value:
        checks["constraints"] = check_constraints({"text": draft, **value["constraints"]})
    if "evidence" in value:
        checks["evidence"] = check_evidence(value["evidence"])
    if "coverage" in value:
        checks["coverage"] = check_coverage({"text": draft, **value["coverage"]})
    if "urgency" in value:
        checks["urgency"] = check_urgency(value["urgency"])

    warnings: list[dict[str, Any]] = []
    if checks["claims"]["warning_count"]:
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
    if "archive_question" in value:
        report["archive"] = _archive(value["archive_question"], draft, report, archive_base)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    final = commands.add_parser("finalize")
    final.add_argument("--input", help="JSON file; omit or use - for stdin")
    final.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    final.add_argument("--archive-base", type=Path, default=DEFAULT_ARCHIVE)
    commands.add_parser("selftest")
    args = parser.parse_args()
    if args.command == "selftest":
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    try:
        result = finalize(_read_payload(args.input), args.output, args.archive_base)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (ToolError, OSError) as exc:
        print(json.dumps({"ok": False, "delivered": False, "blocking_errors": [str(exc)]}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
