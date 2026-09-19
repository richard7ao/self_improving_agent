#!/usr/bin/env python3
"""Make a promote/reject/continue decision from sequential paired-score differences."""

import argparse
import json
import math
import statistics
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("differences", type=Path, help="JSON array of challenger-minus-incumbent scores")
    parser.add_argument("--min-improvement", type=float, default=0.0)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--min-samples", type=int, default=8)
    args = parser.parse_args()
    values = [float(value) for value in json.loads(args.differences.read_text(encoding="utf-8"))]
    if not values:
        raise SystemExit("at least one difference is required")
    mean = statistics.fmean(values)
    if len(values) > 1:
        standard_error = statistics.stdev(values) / math.sqrt(len(values))
        z = statistics.NormalDist().inv_cdf(0.5 + args.confidence / 2)
        interval = [mean - z * standard_error, mean + z * standard_error]
    else:
        standard_error, interval = None, [None, None]
    if len(values) < args.min_samples or interval[0] is None:
        decision = "continue"
    elif interval[0] > args.min_improvement:
        decision = "promote"
    elif interval[1] <= args.min_improvement:
        decision = "reject"
    else:
        decision = "continue"
    print(json.dumps({"decision": decision, "n": len(values), "mean_delta": mean,
                      "standard_error": standard_error, "interval": interval,
                      "confidence": args.confidence,
                      "min_improvement": args.min_improvement}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
