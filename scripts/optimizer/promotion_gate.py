#!/usr/bin/env python3
"""Apply a confidence-aware tune/validation promotion gate to four evaluation results."""

import argparse
import json
from pathlib import Path

from skilltrainbench.optimizer_tools import evaluation_scores, promotion_gate


def _scores(path: Path) -> dict[str, float]:
    return evaluation_scores(json.loads(path.read_text(encoding="utf-8")))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("incumbent_tune", type=Path)
    parser.add_argument("challenger_tune", type=Path)
    parser.add_argument("incumbent_validation", type=Path)
    parser.add_argument("challenger_validation", type=Path)
    parser.add_argument("--min-improvement", type=float, default=0.0)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--report-only-confidence", action="store_true")
    args = parser.parse_args()
    result = promotion_gate(
        _scores(args.incumbent_tune), _scores(args.challenger_tune),
        _scores(args.incumbent_validation), _scores(args.challenger_validation),
        min_improvement=args.min_improvement, confidence=args.confidence,
        bootstrap_iterations=args.iterations, seed=args.seed,
        require_confidence=not args.report_only_confidence,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["promote"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
