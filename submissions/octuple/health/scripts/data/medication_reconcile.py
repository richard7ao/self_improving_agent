#!/usr/bin/env python3
"""Deduplicate and diff exact user-supplied medication strings."""

from __future__ import annotations

from _common import items, run, text

MAX_MEDICATIONS = 500


def unique_exact(values: object, name: str) -> tuple[list[str], list[str]]:
    source = items(values, name, maximum=MAX_MEDICATIONS)
    unique, duplicates, seen = [], [], set()
    for index, value in enumerate(source):
        entry = text(value, f"{name}[{index}]")
        if entry in seen:
            duplicates.append(entry)
        else:
            seen.add(entry)
            unique.append(entry)
    return unique, duplicates


def reconcile(payload: dict) -> dict:
    previous, previous_duplicates = unique_exact(payload.get("previous", []), "previous")
    current, current_duplicates = unique_exact(payload.get("current", []), "current")
    previous_set, current_set = set(previous), set(current)
    return {
        "previous_unique": previous,
        "current_unique": current,
        "added": [item for item in current if item not in previous_set],
        "removed": [item for item in previous if item not in current_set],
        "unchanged": [item for item in current if item in previous_set],
        "duplicates": {"previous": previous_duplicates, "current": current_duplicates},
        "comparison": "case-sensitive exact string equality",
        "note": "List reconciliation only; no interaction, indication, dose, or safety claim is made.",
    }


def self_test() -> None:
    result = reconcile({"previous": ["Alpha 1 mg", "Alpha 1 mg", "Beta"], "current": ["Beta", "alpha 1 mg"]})
    assert result["removed"] == ["Alpha 1 mg"]
    assert result["added"] == ["alpha 1 mg"]
    assert result["duplicates"]["previous"] == ["Alpha 1 mg"]


if __name__ == "__main__":
    run(reconcile, self_test, __doc__)
