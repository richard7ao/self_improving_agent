#!/usr/bin/env python3
"""Capture a non-secret Git, environment, and artifact provenance snapshot."""

import argparse
import json
from pathlib import Path

from skilltrainbench.optimizer_tools import provenance_snapshot, write_json_atomic


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = provenance_snapshot(args.repo, extra_paths=args.artifact)
    if args.out:
        write_json_atomic(args.out, result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
