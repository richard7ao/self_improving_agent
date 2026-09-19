#!/usr/bin/env python3
"""Create a deterministic tune/validation split while preserving task strata."""

import argparse
import json
from pathlib import Path

from skilltrainbench.optimizer_tools import stratified_split


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path, help="JSON array with task_id and stratum fields")
    parser.add_argument("--validation-fraction", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    records = json.loads(args.records.read_text(encoding="utf-8"))
    print(json.dumps(stratified_split(records, args.validation_fraction, args.seed), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
