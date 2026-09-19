#!/usr/bin/env python3
"""Report suspicious lexical-shingle overlap between a skill and source text files."""

import argparse
import json
from pathlib import Path

from skilltrainbench.optimizer_tools import semantic_leakage_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--threshold", type=float, default=0.18)
    parser.add_argument("--width", type=int, default=5)
    args = parser.parse_args()
    sources = {str(path): path.read_text(encoding="utf-8", errors="replace") for path in args.sources}
    result = semantic_leakage_report(args.candidate, sources, shingle_width=args.width,
                                     warn_jaccard=args.threshold)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
