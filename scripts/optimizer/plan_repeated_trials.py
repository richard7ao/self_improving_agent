#!/usr/bin/env python3
"""Build a deterministic manifest for repeated candidate/task evaluation trials."""

import argparse
import json
import random
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", type=Path, help="JSON array of task IDs")
    parser.add_argument("candidates", nargs="+")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if args.repeats < 1:
        raise SystemExit("--repeats must be positive")
    tasks = json.loads(args.tasks.read_text(encoding="utf-8"))
    rows = [{"candidate": candidate, "task_id": task, "repeat": repeat,
             "seed": args.seed + repeat}
            for repeat in range(args.repeats) for candidate in args.candidates for task in tasks]
    random.Random(args.seed).shuffle(rows)
    print(json.dumps({"seed": args.seed, "trials": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
