#!/usr/bin/env python3
"""Create a best-effort replay manifest and command from optimization metadata."""

import argparse
import json
import shlex
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("optimization", type=Path)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    state = json.loads(args.optimization.read_text(encoding="utf-8"))
    split = state.get("split", {})
    tasks = list(split.get("tune", [])) + list(split.get("validation", []))
    candidates = max((len(row.get("candidates", [])) for row in state.get("rounds", [])), default=1)
    command = ["uv", "run", "stbench", "optimize", "--domain", str(state.get("domain")),
               "--skill", str(state.get("skill_dir")), "--out", args.out,
               "--iterations", str(max(1, len(state.get("rounds", [])))),
               "--candidates", str(candidates), "--tasks", ",".join(tasks),
               "--seed", str(state.get("seed", 0))]
    policy = state.get("promotion_policy", {})
    if policy.get("require_confidence"):
        command.append("--require-confidence")
    result = {"command": shlex.join(command), "tasks": tasks,
              "source": str(args.optimization),
              "warning": "Review provider, concurrency, model, and budget settings before executing."}
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
