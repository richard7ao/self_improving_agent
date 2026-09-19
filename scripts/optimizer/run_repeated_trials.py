#!/usr/bin/env python3
"""Execute a repeated-trial manifest only when explicitly passed --execute."""

import argparse
import json
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true", help="required because runs spend provider credits")
    parser.add_argument("--concurrency", type=int, default=1)
    args = parser.parse_args()
    trials = json.loads(args.manifest.read_text(encoding="utf-8")).get("trials", [])
    commands = []
    for index, row in enumerate(trials, 1):
        output = args.out_root / f"trial-{index:04d}"
        commands.append(["uv", "run", "stbench", "eval", "--domain", args.domain,
                         "--skill", row["candidate"], "--arms", "skill",
                         "--tasks", row["task_id"], "--concurrency", str(args.concurrency),
                         "--out", str(output)])
    if not args.execute:
        print(json.dumps({"execute": False, "paid_runs": len(commands), "commands": commands}, indent=2))
        return 0
    for command in commands:
        result = subprocess.run(command, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
