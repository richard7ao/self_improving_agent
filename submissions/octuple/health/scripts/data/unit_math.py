#!/usr/bin/env python3
"""Perform explicit unit conversions or basic arithmetic on supplied numbers."""

from __future__ import annotations

from _common import number, run, text


SCALES = {
    "kg": ("mass", 1.0), "g": ("mass", 1e-3), "mg": ("mass", 1e-6), "ug": ("mass", 1e-9),
    "l": ("volume", 1.0), "ml": ("volume", 1e-3), "ul": ("volume", 1e-6),
    "m": ("length", 1.0), "cm": ("length", 1e-2), "mm": ("length", 1e-3),
}


def calculate(payload: dict) -> dict:
    operation = text(payload.get("operation"), "operation")
    if operation == "convert":
        value = number(payload.get("value"), "value")
        source = text(payload.get("from_unit"), "from_unit").casefold()
        target = text(payload.get("to_unit"), "to_unit").casefold()
        if source in ("c", "f") or target in ("c", "f"):
            if (source, target) == ("c", "f"):
                result, formula = value * 9 / 5 + 32, "value * 9 / 5 + 32"
            elif (source, target) == ("f", "c"):
                result, formula = (value - 32) * 5 / 9, "(value - 32) * 5 / 9"
            elif source == target and source in ("c", "f"):
                result, formula = value, "value"
            else:
                raise ValueError("unsupported temperature conversion")
        else:
            if source not in SCALES or target not in SCALES:
                raise ValueError("unsupported unit")
            source_kind, source_scale = SCALES[source]
            target_kind, target_scale = SCALES[target]
            if source_kind != target_kind:
                raise ValueError("units have incompatible dimensions")
            result, formula = value * source_scale / target_scale, "value * from_scale / to_scale"
        return {"operation": operation, "input": {"value": value, "unit": source},
                "result": {"value": result, "unit": target}, "formula": formula,
                "note": "Arithmetic only; units and value were supplied by the caller."}

    left = number(payload.get("left"), "left")
    right = number(payload.get("right"), "right")
    if operation == "add":
        result, formula = left + right, "left + right"
    elif operation == "subtract":
        result, formula = left - right, "left - right"
    elif operation == "multiply":
        result, formula = left * right, "left * right"
    elif operation == "divide":
        if right == 0:
            raise ValueError("division by zero")
        result, formula = left / right, "left / right"
    elif operation == "percent_change":
        if left == 0:
            raise ValueError("percent change baseline must not be zero")
        result, formula = (right - left) / abs(left) * 100, "(right - left) / abs(left) * 100"
    else:
        raise ValueError("unsupported operation")
    return {"operation": operation, "inputs": {"left": left, "right": right},
            "result": result, "formula": formula, "note": "General arithmetic only."}


def self_test() -> None:
    assert calculate({"operation": "convert", "value": 1, "from_unit": "kg", "to_unit": "g"})["result"]["value"] == 1000
    assert calculate({"operation": "convert", "value": 0, "from_unit": "C", "to_unit": "F"})["result"]["value"] == 32
    assert calculate({"operation": "percent_change", "left": 20, "right": 15})["result"] == -25


if __name__ == "__main__":
    run(calculate, self_test, __doc__)
