#!/usr/bin/env python3
"""Structure caller-supplied record sections and report missing fields without inference."""

from __future__ import annotations

from _common import items, run, text

MAX_SECTIONS = 100
MAX_FIELDS = 200


def missing(value: object) -> bool:
    return value is None or value == ""


def structure(payload: dict) -> dict:
    sections = items(payload.get("sections"), "sections", maximum=MAX_SECTIONS)
    output, missing_fields = [], []
    seen_sections: set[str] = set()
    for section_index, raw in enumerate(sections):
        if not isinstance(raw, dict):
            raise ValueError(f"sections[{section_index}] must be an object")
        name = text(raw.get("name"), f"sections[{section_index}].name")
        if name in seen_sections:
            raise ValueError(f"duplicate section name: {name}")
        seen_sections.add(name)
        fields = raw.get("fields", {})
        if not isinstance(fields, dict) or len(fields) > MAX_FIELDS:
            raise ValueError(f"sections[{section_index}].fields must be an object with at most {MAX_FIELDS} fields")
        normalized_fields = {}
        for field_name, value in fields.items():
            key = text(field_name, f"sections[{section_index}] field name")
            normalized_fields[key] = value
        required = items(raw.get("required_fields", []), f"sections[{section_index}].required_fields", maximum=MAX_FIELDS)
        required_names = [text(value, f"sections[{section_index}].required_fields") for value in required]
        section_missing = [field for field in required_names if field not in normalized_fields or missing(normalized_fields[field])]
        missing_fields.extend({"section": name, "field": field} for field in section_missing)
        output.append({"name": name, "fields": normalized_fields, "missing_fields": section_missing})
    return {"sections": output, "missing_fields": missing_fields,
            "note": "Values and section order are caller-supplied; no missing value was inferred."}


def self_test() -> None:
    result = structure({"sections": [
        {"name": "Overview", "fields": {"present": 0, "blank": ""},
         "required_fields": ["present", "blank", "absent"]}
    ]})
    assert result["sections"][0]["fields"]["present"] == 0
    assert result["sections"][0]["missing_fields"] == ["blank", "absent"]


if __name__ == "__main__":
    run(structure, self_test, __doc__)
