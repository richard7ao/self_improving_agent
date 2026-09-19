#!/usr/bin/env python3
"""Compute paired task-level bootstrap statistics for two evaluation results."""

import argparse
import json
from pathlib import Path

from skilltrainbench.optimizer_tools import evaluation_scores, paired_statistics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("incumbent", type=Path)
    parser.add_argument("challenger", type=Path)
    parser.add_argument("--arm", default="skill")
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    incumbent = evaluation_scores(json.loads(args.incumbent.read_text()), arm=args.arm)
    challenger = evaluation_scores(json.loads(args.challenger.read_text()), arm=args.arm)
    print(json.dumps(paired_statistics(incumbent, challenger, iterations=args.iterations,
                                      confidence=args.confidence, seed=args.seed), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
