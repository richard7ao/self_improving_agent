#!/usr/bin/env python3
"""Small offline checks and arithmetic for health-response drafting.

This tool does not diagnose, choose a drug, or recommend a dose.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unittest
from pathlib import Path


CONTEXT_DEFLECTIONS = (
    r"what would you like help with",
    r"i (?:do not|don't) have (?:the )?(?:earlier|previous) (?:part|context)",
    r"could you (?:repeat|tell me) (?:the|your) (?:question|symptom)",
)
CERTAINTY_PHRASES = (
    r"\bdefinitely (?:is|have|has|means)\b",
    r"\b(?:this|that) (?:is|proves) (?:certainly|definitely)\b",
    r"\bguaranteed\b",
)
MEDICATION_DIRECTIVES = (
    r"\b(?:you should|you need to|please|must) (?:start|stop|discontinue|double|increase|decrease|taper)\b",
    r"(?:^|[.!?]\s+)(?:start|stop|discontinue|double|increase|decrease|taper) "
    r"(?:taking )?(?:your |the )?(?:dose|medication|medicine|prescription|insulin|antibiotic|steroid)\b",
)


def audit_text(
    text: str,
    *,
    max_words: int | None = None,
    max_questions: int | None = None,
    required: list[str] | None = None,
) -> dict[str, object]:
    """Return deterministic draft metrics and review flags."""
    words = re.findall(r"\b[\w'-]+\b", text)
    questions = text.count("?")
    flags: list[dict[str, str]] = []

    if not text.strip():
        flags.append({"kind": "empty", "detail": "Draft is empty."})
    if max_words is not None and len(words) > max_words:
        flags.append(
            {"kind": "length", "detail": f"{len(words)} words exceeds {max_words}."}
        )
    if max_questions is not None and questions > max_questions:
        flags.append(
            {
                "kind": "questions",
                "detail": f"{questions} question marks exceeds {max_questions}.",
            }
        )

    lowered = text.casefold()
    for phrase in required or []:
        if phrase.casefold() not in lowered:
            flags.append(
                {"kind": "missing_required", "detail": f"Missing literal text: {phrase}"}
            )

    checks = (
        ("context_deflection", CONTEXT_DEFLECTIONS),
        ("unsupported_certainty", CERTAINTY_PHRASES),
        ("medication_directive", MEDICATION_DIRECTIVES),
    )
    for kind, patterns in checks:
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                flags.append({"kind": kind, "detail": match.group(0)})

    return {
        "pass": not flags,
        "words": len(words),
        "questions": questions,
        "flags": flags,
    }


def convert(value: float, source: str, target: str) -> float:
    pair = (source.casefold(), target.casefold())
    conversions = {
        ("c", "f"): lambda x: x * 9 / 5 + 32,
        ("f", "c"): lambda x: (x - 32) * 5 / 9,
        ("kg", "lb"): lambda x: x * 2.2046226218,
        ("lb", "kg"): lambda x: x / 2.2046226218,
        ("mg/dl", "mmol/l-glucose"): lambda x: x / 18.0182,
        ("mmol/l-glucose", "mg/dl"): lambda x: x * 18.0182,
    }
    if pair not in conversions:
        raise ValueError(f"Unsupported conversion: {source} -> {target}")
    result = conversions[pair](value)
    if not math.isfinite(result):
        raise ValueError("Result is not finite")
    return result


def dose_math(weight_kg: float, mg_per_kg: float, concentration: float | None) -> dict:
    if weight_kg <= 0 or mg_per_kg < 0:
        raise ValueError("Weight must be positive and mg/kg must be nonnegative")
    milligrams = weight_kg * mg_per_kg
    result = {"milligrams": milligrams}
    if concentration is not None:
        if concentration <= 0:
            raise ValueError("Concentration must be positive")
        result["millilitres"] = milligrams / concentration
    return result


def bmi(weight_kg: float, height_cm: float) -> float:
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("Weight and height must be positive")
    return weight_kg / (height_cm / 100) ** 2


class ToolTests(unittest.TestCase):
    def test_audit(self) -> None:
        result = audit_text("Here is the answer.", max_words=8, max_questions=0)
        self.assertTrue(result["pass"])
        safe = audit_text("Do not stop your medication without speaking to your clinician.")
        self.assertTrue(safe["pass"])
        flagged = audit_text("What would you like help with?")
        self.assertEqual(flagged["flags"][0]["kind"], "context_deflection")

    def test_conversions(self) -> None:
        self.assertAlmostEqual(convert(0, "C", "F"), 32)
        self.assertAlmostEqual(convert(180.182, "mg/dL", "mmol/L-glucose"), 10)

    def test_dose_and_bmi(self) -> None:
        self.assertEqual(dose_math(18, 10, 20), {"milligrams": 180, "millilitres": 9})
        self.assertAlmostEqual(bmi(70, 175), 22.8571428571)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    audit = commands.add_parser("audit", help="Audit a response draft")
    audit.add_argument("--file", type=Path, help="Draft file; omit to read stdin")
    audit.add_argument("--max-words", type=int)
    audit.add_argument("--max-questions", type=int)
    audit.add_argument("--require", action="append", default=[])

    conv = commands.add_parser("convert", help="Convert a supported unit pair")
    conv.add_argument("--value", type=float, required=True)
    conv.add_argument("--from-unit", required=True)
    conv.add_argument("--to-unit", required=True)

    dose = commands.add_parser("dose", help="Perform weight-based dose arithmetic")
    dose.add_argument("--weight-kg", type=float, required=True)
    dose.add_argument("--mg-per-kg", type=float, required=True)
    dose.add_argument("--concentration-mg-ml", type=float)

    bmi_cmd = commands.add_parser("bmi", help="Calculate adult BMI arithmetic")
    bmi_cmd.add_argument("--weight-kg", type=float, required=True)
    bmi_cmd.add_argument("--height-cm", type=float, required=True)

    commands.add_parser("selftest", help="Run built-in tests")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "audit":
            text = args.file.read_text() if args.file else sys.stdin.read()
            output = audit_text(
                text,
                max_words=args.max_words,
                max_questions=args.max_questions,
                required=args.require,
            )
        elif args.command == "convert":
            output = {
                "value": convert(args.value, args.from_unit, args.to_unit),
                "unit": args.to_unit,
            }
        elif args.command == "dose":
            output = dose_math(
                args.weight_kg, args.mg_per_kg, args.concentration_mg_ml
            )
            output["warning"] = "Arithmetic only; verify inputs and clinical appropriateness."
        elif args.command == "bmi":
            output = {"bmi": bmi(args.weight_kg, args.height_cm)}
        else:
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(ToolTests)
            return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
