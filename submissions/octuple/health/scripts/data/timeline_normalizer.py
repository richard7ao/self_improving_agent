#!/usr/bin/env python3
"""Order explicitly dated or ranked events without inventing missing dates."""

from __future__ import annotations

from datetime import date, datetime, timezone

from _common import items, number, run, text

MAX_EVENTS = 500


def timestamp_key(value: str) -> tuple[tuple[int, int], str]:
    try:
        if "T" in value:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            mode = "aware" if parsed.tzinfo is not None else "naive"
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
            microseconds = ((parsed.hour * 60 + parsed.minute) * 60 + parsed.second) * 1_000_000 + parsed.microsecond
            return (parsed.date().toordinal(), microseconds), mode
        parsed_date = date.fromisoformat(value)
        return (parsed_date.toordinal(), -1), "date"
    except ValueError as exc:
        raise ValueError("timestamp must be ISO YYYY-MM-DD or ISO datetime") from exc


def normalize(payload: dict) -> dict:
    source = items(payload.get("events"), "events", maximum=MAX_EVENTS)
    seen: set[str] = set()
    datetime_modes: set[str] = set()
    absolute, relative, unplaced = [], [], []
    for index, raw in enumerate(source):
        if not isinstance(raw, dict):
            raise ValueError(f"events[{index}] must be an object")
        event_id = text(raw.get("id"), f"events[{index}].id")
        if event_id in seen:
            raise ValueError(f"duplicate event id: {event_id}")
        seen.add(event_id)
        event = {"id": event_id, "label": text(raw.get("label"), f"events[{index}].label")}
        if "when_text" in raw:
            event["when_text"] = text(raw["when_text"], f"events[{index}].when_text", allow_empty=True)
        if "timestamp" in raw and "order" in raw:
            raise ValueError(f"events[{index}] must not contain both timestamp and order")
        if "timestamp" in raw:
            stamp = text(raw["timestamp"], f"events[{index}].timestamp")
            key, mode = timestamp_key(stamp)
            if mode != "date":
                datetime_modes.add(mode)
            event["timestamp"] = stamp
            absolute.append((key, index, event))
        elif "order" in raw:
            order = number(raw["order"], f"events[{index}].order")
            event["order"] = order
            relative.append((order, index, event))
        else:
            unplaced.append(event)
    if len(datetime_modes) > 1:
        raise ValueError("timezone-aware and timezone-naive datetimes must not be mixed")
    return {
        "absolute_events": [event for _, _, event in sorted(absolute)],
        "relative_events": [event for _, _, event in sorted(relative)],
        "unplaced_events": unplaced,
        "note": "Groups are separate; no date or relationship was inferred. Aware datetimes are ordered in UTC.",
    }


def self_test() -> None:
    result = normalize({"events": [
        {"id": "b", "label": "B", "timestamp": "2025-02-01"},
        {"id": "a", "label": "A", "timestamp": "2025-01-01"},
        {"id": "r2", "label": "Later", "order": 2},
        {"id": "r1", "label": "Earlier", "order": 1},
        {"id": "u", "label": "Unknown", "when_text": "recently"},
        {"id": "z", "label": "Zoned", "timestamp": "2024-12-31T23:00:00Z"},
    ]})
    assert [x["id"] for x in result["absolute_events"]] == ["z", "a", "b"]
    assert [x["id"] for x in result["relative_events"]] == ["r1", "r2"]
    assert result["unplaced_events"][0]["when_text"] == "recently"
    try:
        normalize({"events": [
            {"id": "a", "label": "A", "timestamp": "2025-01-01T00:00:00Z"},
            {"id": "b", "label": "B", "timestamp": "2025-01-01T00:00:00"},
        ]})
    except ValueError:
        pass
    else:
        raise AssertionError("mixed timezone modes must fail")


if __name__ == "__main__":
    run(normalize, self_test, __doc__)
