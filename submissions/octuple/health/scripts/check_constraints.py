#!/usr/bin/env python3
"""Offline response-form checker; it does not assess medical correctness."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unittest
from pathlib import Path


def check(
    text: str,
    *,
    required: list[str] | None = None,
    forbidden: list[str] | None = None,
    prefix: str | None = None,
    max_words: int | None = None,
    max_sentences: int | None = None,
    max_questions: int | None = None,
) -> dict[str, object]:
    """Return counts and deterministic constraint violations."""
    words = re.findall(r"\b[\w'-]+\b", text)
    sentences = re.findall(r"[^.!?]+[.!?](?=\s|$)|[^.!?]+$", text.strip())
    questions = text.count("?")
    folded = text.casefold()
    violations: list[str] = []

    if not text.strip():
        violations.append("empty response")
    if prefix is not None and not text.startswith(prefix):
        violations.append(f"response does not start with: {prefix}")
    for phrase in required or []:
        if phrase.casefold() not in folded:
            violations.append(f"missing required text: {phrase}")
    for phrase in forbidden or []:
        if phrase.casefold() in folded:
            violations.append(f"contains forbidden text: {phrase}")
    limits = (
        ("words", len(words), max_words),
        ("sentences", len(sentences), max_sentences),
        ("questions", questions, max_questions),
    )
    for label, actual, maximum in limits:
        if maximum is not None and actual > maximum:
            violations.append(f"{actual} {label} exceeds limit {maximum}")

    return {
        "pass": not violations,
        "words": len(words),
        "sentences": len(sentences),
        "questions": questions,
        "violations": violations,
    }


class SelfTests(unittest.TestCase):
    def test_passes_matching_constraints(self) -> None:
        result = check(
            "Summary: Stable today.",
            required=["stable"],
            prefix="Summary:",
            max_words=4,
            max_sentences=1,
            max_questions=0,
        )
        self.assertTrue(result["pass"])

    def test_reports_each_violation(self) -> None:
        result = check(
            "Could this wait? Extra sentence.",
            required=["today"],
            forbidden=["extra"],
            prefix="Answer:",
            max_sentences=1,
            max_questions=0,
        )
        self.assertFalse(result["pass"])
        self.assertEqual(len(result["violations"]), 5)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, help="Draft path; omit to read stdin")
    parser.add_argument("--require", action="append", default=[])
    parser.add_argument("--forbid", action="append", default=[])
    parser.add_argument("--prefix")
    parser.add_argument("--max-words", type=int)
    parser.add_argument("--max-sentences", type=int)
    parser.add_argument("--max-questions", type=int)
    parser.add_argument("--self-test", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1
    try:
        text = args.file.read_text() if args.file else sys.stdin.read()
    except OSError as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    result = check(
        text,
        required=args.require,
        forbidden=args.forbid,
        prefix=args.prefix,
        max_words=args.max_words,
        max_sentences=args.max_sentences,
        max_questions=args.max_questions,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
