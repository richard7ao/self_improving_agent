#!/usr/bin/env python3
"""Calculate deltas and percentages for a user-supplied same-unit numeric series."""

from __future__ import annotations

from _common import items, number, run, text

MAX_OBSERVATIONS = 500


def trend(payload: dict) -> dict:
    series = text(payload.get("series"), "series")
    source = items(payload.get("observations"), "observations", maximum=MAX_OBSERVATIONS)
    if not source:
        raise ValueError("observations must not be empty")
    normalized = []
    expected_unit = None
    for index, raw in enumerate(source):
        if not isinstance(raw, dict):
            raise ValueError(f"observations[{index}] must be an object")
        unit = text(raw.get("unit"), f"observations[{index}].unit")
        if expected_unit is None:
            expected_unit = unit
        elif unit != expected_unit:
            raise ValueError(f"unit mismatch at observations[{index}]: {unit} != {expected_unit}")
        normalized.append({
            "label": text(raw.get("label"), f"observations[{index}].label"),
            "value": number(raw.get("value"), f"observations[{index}].value"),
            "unit": unit,
        })
    changes = []
    for previous, current in zip(normalized, normalized[1:]):
        delta = current["value"] - previous["value"]
        percent = None if previous["value"] == 0 else delta / abs(previous["value"]) * 100
        changes.append({
            "from": previous["label"], "to": current["label"], "delta": delta,
            "percent_change": percent, "unit": expected_unit,
        })
    overall_delta = normalized[-1]["value"] - normalized[0]["value"]
    overall_percent = None if normalized[0]["value"] == 0 else overall_delta / abs(normalized[0]["value"]) * 100
    return {
        "series": series, "unit": expected_unit, "observations": normalized, "changes": changes,
        "overall": {"delta": overall_delta, "percent_change": overall_percent},
        "note": "Arithmetic only; ordering and values are exactly those supplied.",
    }


def self_test() -> None:
    result = trend({"series": "marker", "observations": [
        {"label": "first", "value": 10, "unit": "u"},
        {"label": "second", "value": 15, "unit": "u"},
    ]})
    assert result["overall"] == {"delta": 5.0, "percent_change": 50.0}
    try:
        trend({"series": "x", "observations": [
            {"label": "a", "value": 1, "unit": "x"}, {"label": "b", "value": 2, "unit": "y"}
        ]})
    except ValueError:
        pass
    else:
        raise AssertionError("mixed units must fail")


if __name__ == "__main__":
    run(trend, self_test, __doc__)
