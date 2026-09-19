#!/usr/bin/env python3
"""Reject critical labeled task regressions between two evaluation results."""

import argparse
import json
from pathlib import Path

from skilltrainbench.optimizer_tools import evaluation_scores, safety_regression_gate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("incumbent", type=Path)
    parser.add_argument("challenger", type=Path)
    parser.add_argument("labels", type=Path, help="JSON object mapping task IDs to label arrays")
    parser.add_argument("--critical", action="append", default=[])
    parser.add_argument("--tolerance", type=float, default=0.0)
    args = parser.parse_args()
    incumbent = evaluation_scores(json.loads(args.incumbent.read_text()))
    challenger = evaluation_scores(json.loads(args.challenger.read_text()))
    labels = json.loads(args.labels.read_text())
    result = safety_regression_gate(incumbent, challenger, labels, tolerance=args.tolerance,
                                    critical_labels=args.critical)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
