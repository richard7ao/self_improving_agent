#!/usr/bin/env python3
"""Forecast benchmark attempts and approximate token use before an optimization run."""

import argparse
import json

from skilltrainbench.optimizer_tools import budget_forecast


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=int, required=True)
    parser.add_argument("--candidates", type=int, required=True)
    parser.add_argument("--rounds", type=int, required=True)
    parser.add_argument("--tune-fraction", type=float, default=0.75)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--arms", type=int, default=1)
    parser.add_argument("--learner-tokens-per-attempt", type=int, default=0)
    parser.add_argument("--grader-tokens-per-attempt", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(budget_forecast(**vars(args)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
