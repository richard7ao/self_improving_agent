#!/usr/bin/env python3
"""Measure exact duplication and lexical diversity among skill candidates."""

import argparse
import json
from pathlib import Path

from skilltrainbench.optimizer_tools import candidate_diversity


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates", nargs="+", type=Path)
    args = parser.parse_args()
    result = candidate_diversity(args.candidates)
    print(json.dumps(result, indent=2))
    return 1 if result["exact_duplicate_pairs"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
