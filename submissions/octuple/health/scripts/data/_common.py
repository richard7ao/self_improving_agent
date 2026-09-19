#!/usr/bin/env python3
"""Shared bounded JSON I/O helpers for the offline data tools."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

MAX_INPUT_BYTES = 1_000_000
MAX_TEXT_CHARS = 2_000
MAX_ITEMS = 1_000


def parser(description: str) -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=description)
    result.add_argument("--input", type=Path, help="JSON file; omit to read JSON from stdin")
    result.add_argument("--self-test", action="store_true")
    return result


def read_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    else:
        if path.stat().st_size > MAX_INPUT_BYTES:
            raise ValueError(f"input exceeds {MAX_INPUT_BYTES} bytes")
        raw = path.read_bytes()
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError(f"input exceeds {MAX_INPUT_BYTES} bytes")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("top-level JSON value must be an object")
    return value


def emit(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def number(value: object, name: str, *, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    result = float(value)
    if not math.isfinite(result) or abs(result) > 1e15:
        raise ValueError(f"{name} must be finite and within the arithmetic limit")
    if nonnegative and result < 0:
        raise ValueError(f"{name} must be nonnegative")
    return result


def text(value: object, name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    if len(value) > MAX_TEXT_CHARS:
        raise ValueError(f"{name} exceeds {MAX_TEXT_CHARS} characters")
    if not allow_empty and not value:
        raise ValueError(f"{name} must not be empty")
    return value


def items(value: object, name: str, *, maximum: int = MAX_ITEMS) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    if len(value) > maximum:
        raise ValueError(f"{name} exceeds {maximum} items")
    return value


def run(main_fn, self_test_fn, description: str) -> None:
    command = parser(description)
    args = command.parse_args()
    try:
        if args.self_test:
            self_test_fn()
            emit({"self_test": "passed"})
            return
        emit(main_fn(read_json(args.input)))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        emit({"error": str(exc)})
        raise SystemExit(2) from exc
