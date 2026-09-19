#!/usr/bin/env python3
"""Validate explicit engineering units, balances, residuals, and boundaries."""

from __future__ import annotations

import argparse
import json
import math
import unittest
from pathlib import Path


CONVERSIONS = {
    ("m", "cm"): 100.0, ("m", "mm"): 1000.0, ("km", "m"): 1000.0,
    ("kg", "g"): 1000.0, ("h", "s"): 3600.0, ("min", "s"): 60.0,
    ("Pa", "kPa"): 0.001, ("Pa", "MPa"): 1e-6, ("J", "kJ"): 0.001,
    ("W", "kW"): 0.001, ("rad", "deg"): 180.0 / math.pi,
}


def normalize_dimensions(value: dict) -> dict[str, float]:
    return {str(name): float(power) for name, power in value.items() if float(power) != 0}


def run(operation: str, data: dict) -> dict:
    if operation == "convert":
        source, target = data["from"], data["to"]
        if source == target:
            factor = 1.0
        elif (source, target) in CONVERSIONS:
            factor = CONVERSIONS[(source, target)]
        elif (target, source) in CONVERSIONS:
            factor = 1.0 / CONVERSIONS[(target, source)]
        else:
            raise ValueError("unsupported conversion; do not infer dimensions from unit names")
        return {"value": float(data["value"]) * factor, "unit": target, "factor": factor}
    if operation == "dimensions":
        left, right = normalize_dimensions(data["left"]), normalize_dimensions(data["right"])
        return {"consistent": left == right, "left": left, "right": right}
    if operation in {"force_balance", "moment_balance", "conservation"}:
        inputs = sum(float(value) for value in data.get("inputs", []))
        outputs = sum(float(value) for value in data.get("outputs", []))
        residual = inputs - outputs
        tolerance = float(data.get("tolerance", 0))
        return {"inputs": inputs, "outputs": outputs, "residual": residual,
                "balanced": abs(residual) <= tolerance}
    if operation == "residual":
        observed = float(data["observed"])
        predicted = float(data["predicted"])
        residual = observed - predicted
        scale = max(abs(observed), abs(predicted), 1.0)
        tolerance = float(data.get("absolute_tolerance", 0)) + float(data.get("relative_tolerance", 0)) * scale
        return {"residual": residual, "tolerance": tolerance, "pass": abs(residual) <= tolerance}
    if operation == "error_propagation":
        terms = [abs(float(item["sensitivity"])) * float(item["uncertainty"]) for item in data["terms"]]
        mode = data.get("mode", "independent")
        uncertainty = math.sqrt(sum(term * term for term in terms)) if mode == "independent" else sum(terms)
        return {"uncertainty": uncertainty, "mode": mode, "terms": terms}
    if operation == "boundary":
        values = [float(value) for value in data["values"]]
        lower, upper = data.get("lower"), data.get("upper")
        checks = [(lower is None or value >= float(lower)) and (upper is None or value <= float(upper)) for value in values]
        return {"values": values, "within_bounds": checks, "pass": all(checks)}
    raise ValueError(f"unsupported operation: {operation}")


class SelfTests(unittest.TestCase):
    def test_dimensions_balance_conversion(self) -> None:
        self.assertTrue(run("dimensions", {"left": {"M": 1, "L": 1, "T": -2}, "right": {"M": 1, "L": 1, "T": -2}})["consistent"])
        self.assertTrue(run("force_balance", {"inputs": [5, -2], "outputs": [3]})["balanced"])
        self.assertAlmostEqual(run("convert", {"value": math.pi, "from": "rad", "to": "deg"})["value"], 180)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("operation", nargs="?")
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests)).wasSuccessful() else 1
    if not args.operation or not args.input:
        parser.error("operation and --input are required")
    print(json.dumps(run(args.operation, json.loads(args.input.read_text())), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
