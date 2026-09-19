#!/usr/bin/env python3
"""Append or list durable experiment metadata in an atomic JSON registry."""

import argparse
import json
from pathlib import Path

from skilltrainbench.optimizer_tools import append_registry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add")
    add.add_argument("registry", type=Path)
    add.add_argument("record", type=Path, help="JSON object to append")
    show = sub.add_parser("show")
    show.add_argument("registry", type=Path)
    args = parser.parse_args()
    if args.command == "add":
        record = json.loads(args.record.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise SystemExit("record must be a JSON object")
        print(json.dumps(append_registry(args.registry, record), indent=2))
    else:
        print(args.registry.read_text(encoding="utf-8") if args.registry.is_file() else "[]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
