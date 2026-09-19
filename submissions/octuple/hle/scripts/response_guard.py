#!/usr/bin/env python3
"""Atomically write and validate the required HLE three-field response."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import unittest
from pathlib import Path


FIELDS = ("Explanation", "Answer", "Confidence")
CONFIDENCE = re.compile(r"^(?:100|[1-9]?\d)%$")
UNFINISHED = (
    re.compile(r"\b(?:todo|tbd|fixme)\b", re.IGNORECASE),
    re.compile(r"\bneed(?:s|ed)?\s+(?:to\s+)?(?:check|verify|finish|complete)\b", re.IGNORECASE),
    re.compile(r"<\s*(?:answer|explanation|reasoning|confidence|placeholder)[^>]*>", re.IGNORECASE),
    re.compile(r"\.\.\.\s*$"),
)


def unfinished_marker(value: str) -> str | None:
    for pattern in UNFINISHED:
        match = pattern.search(value)
        if match:
            return match.group(0)
    return None


def validate(text: str) -> dict[str, object]:
    lines = text.splitlines()
    violations: list[str] = []
    if len(lines) != 3:
        violations.append(f"expected exactly 3 lines, found {len(lines)}")
    values: dict[str, str] = {}
    for index, field in enumerate(FIELDS):
        prefix = f"{field}:"
        if index >= len(lines) or not lines[index].startswith(prefix):
            violations.append(f"line {index + 1} must start with {prefix}")
            continue
        value = lines[index][len(prefix):].strip()
        values[field.lower()] = value
        if not value:
            violations.append(f"{field} must not be empty")
        elif field in {"Explanation", "Answer"}:
            marker = unfinished_marker(value)
            if marker:
                violations.append(f"{field} contains unfinished marker: {marker!r}")
    if values.get("confidence") and not CONFIDENCE.fullmatch(values["confidence"]):
        violations.append("Confidence must be an integer from 0% to 100%")
    return {"pass": not violations, "violations": violations, "values": values}


def render(explanation: str, answer: str, confidence: int) -> str:
    if not 0 <= confidence <= 100:
        raise ValueError("confidence must be between 0 and 100")
    if any("\n" in value or "\r" in value for value in (explanation, answer)):
        raise ValueError("explanation and answer must each fit on one line")
    text = f"Explanation: {explanation.strip()}\nAnswer: {answer.strip()}\nConfidence: {confidence}%\n"
    result = validate(text.rstrip("\n"))
    if not result["pass"]:
        raise ValueError("; ".join(result["violations"]))
    return text


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


class SelfTests(unittest.TestCase):
    def test_valid(self) -> None:
        self.assertTrue(validate(render("Checked exactly.", "B", 91))["pass"])

    def test_wrong_order(self) -> None:
        self.assertFalse(validate("Answer: B\nExplanation: x\nConfidence: 91%") ["pass"])

    def test_rejects_unfinished_fallback(self) -> None:
        result = validate("Explanation: Candidate seems likely; need check\nAnswer: C\nConfidence: 50%")
        self.assertFalse(result["pass"])
        self.assertIn("unfinished marker", result["violations"][0])

    def test_rejects_placeholder_and_trailing_ellipsis(self) -> None:
        self.assertFalse(validate("Explanation: <reasoning>\nAnswer: B\nConfidence: 50%") ["pass"])
        self.assertFalse(validate("Explanation: complete later...\nAnswer: B\nConfidence: 50%") ["pass"])

    def test_allows_literal_ellipsis_inside_complete_sentence(self) -> None:
        text = render("The series uses terms 1, 2, ... and therefore diverges.", "diverges", 90)
        self.assertTrue(validate(text.rstrip("\n"))["pass"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="command")
    write = sub.add_parser("write")
    write.add_argument("--explanation", required=True)
    write.add_argument("--answer", required=True)
    write.add_argument("--confidence", required=True, type=int)
    write.add_argument("--output", type=Path, default=Path("/logs/agent/response.txt"))
    check = sub.add_parser("validate")
    check.add_argument("--file", type=Path, default=Path("/logs/agent/response.txt"))
    check.add_argument("--schema", choices=("three-field", "nonempty"), default="three-field")
    raw = sub.add_parser("write-raw")
    raw.add_argument("--input", required=True, type=Path)
    raw.add_argument("--output", type=Path, default=Path("/logs/agent/response.txt"))
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests)
        )
        return 0 if result.wasSuccessful() else 1
    if args.command == "write":
        text = render(args.explanation, args.answer, args.confidence)
        atomic_write(args.output, text)
        print(json.dumps({"pass": True, "output": str(args.output)}))
        return 0
    if args.command == "validate":
        try:
            text = args.file.read_text(encoding="utf-8")
            result = ({"pass": bool(text.strip()), "violations": [] if text.strip() else ["response is empty"], "values": {}}
                      if args.schema == "nonempty" else validate(text.rstrip("\n")))
        except OSError as error:
            result = {"pass": False, "violations": [str(error)], "values": {}}
        print(json.dumps(result, indent=2))
        return 0 if result["pass"] else 1
    if args.command == "write-raw":
        text = args.input.read_text(encoding="utf-8")
        if not text.strip():
            raise SystemExit("input response is empty")
        atomic_write(args.output, text)
        delivered = args.output.read_text(encoding="utf-8")
        passed = delivered == text and bool(delivered.strip())
        print(json.dumps({"pass": passed, "output": str(args.output)}))
        return 0 if passed else 1
    parser.error("choose write or validate, or pass --self-test")


if __name__ == "__main__":
    raise SystemExit(main())
