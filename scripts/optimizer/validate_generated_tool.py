#!/usr/bin/env python3
"""Statically audit generated skill scripts and optionally run explicit self-tests."""

import argparse
import json
from pathlib import Path

from skilltrainbench.optimizer_tools import audit_generated_scripts, run_script_self_test


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", type=Path)
    parser.add_argument("--run-self-tests", action="store_true")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    result = audit_generated_scripts(args.skill)
    if args.run_self_tests and result["ok"]:
        result["self_tests"] = [run_script_self_test(row["path"], timeout_s=args.timeout)
                                for row in result["scripts"]]
        result["ok"] = all(item["ok"] for item in result["self_tests"])
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
