#!/usr/bin/env python3
"""Produce a non-destructive keep/drop plan for exact duplicate candidate folders."""

import argparse
import json
from pathlib import Path

from skilltrainbench.optimizer_tools import duplicate_candidate_indexes, skill_digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates", nargs="+", type=Path)
    args = parser.parse_args()
    duplicates = duplicate_candidate_indexes(args.candidates)
    rows = [{"path": str(path), "digest": skill_digest(path),
             "decision": "drop_duplicate" if index in duplicates else "keep"}
            for index, path in enumerate(args.candidates)]
    print(json.dumps({"candidates": rows, "duplicates": len(duplicates)}, indent=2))
    return 1 if duplicates else 0


if __name__ == "__main__":
    raise SystemExit(main())
