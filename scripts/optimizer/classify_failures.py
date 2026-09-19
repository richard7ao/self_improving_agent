#!/usr/bin/env python3
"""Classify attempt JSONL rows into deterministic high-level failure classes."""

import argparse
import json
from pathlib import Path

from skilltrainbench.optimizer_tools import classify_attempts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempts", type=Path)
    parser.add_argument("--low-score", type=float, default=0.5)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.attempts.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(json.dumps(classify_attempts(rows, low_score=args.low_score), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
