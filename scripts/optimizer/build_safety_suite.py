#!/usr/bin/env python3
"""Build a reproducible labeled safety-suite manifest from a task catalog."""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path, help="JSON array with task_id and labels")
    parser.add_argument("--critical", action="append", default=[])
    parser.add_argument("--per-label", type=int, default=0, help="0 keeps every labeled task")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    records = json.loads(args.catalog.read_text(encoding="utf-8"))
    groups = defaultdict(list)
    labels = {}
    for row in records:
        task_id = row.get("task_id")
        task_labels = sorted(set(row.get("labels") or []))
        if not isinstance(task_id, str) or not task_id or not task_labels:
            raise SystemExit("each catalog row needs task_id and a nonempty labels array")
        labels[task_id] = task_labels
        for label in task_labels:
            groups[label].append(task_id)
    rng = random.Random(args.seed)
    selected = set()
    allocation = {}
    for label in sorted(groups):
        tasks = sorted(set(groups[label]))
        rng.shuffle(tasks)
        chosen = tasks if args.per_label <= 0 else tasks[:args.per_label]
        selected.update(chosen)
        allocation[label] = len(chosen)
    critical = set(args.critical)
    missing = sorted(critical - set(groups))
    result = {"seed": args.seed, "tasks": sorted(selected),
              "labels": {task: labels[task] for task in sorted(selected)},
              "critical_labels": sorted(critical), "allocation": allocation,
              "missing_critical_labels": missing, "ok": not missing}
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
