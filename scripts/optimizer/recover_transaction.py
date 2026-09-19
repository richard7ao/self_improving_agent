#!/usr/bin/env python3
"""Inspect or explicitly restore an interrupted skill-promotion backup."""

import argparse
import json
import os
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", type=Path)
    parser.add_argument("--restore", type=Path, help="specific hidden promotion directory to restore")
    args = parser.parse_args()
    skill = args.skill.resolve()
    candidates = sorted(skill.parent.glob(f".{skill.name}-promote-*/previous"))
    if not args.restore:
        print(json.dumps({"skill": str(skill), "live_exists": skill.exists(),
                          "recoverable_backups": [str(path.parent) for path in candidates]}, indent=2))
        return 0
    transaction = args.restore.resolve()
    if transaction.parent != skill.parent or not transaction.name.startswith(f".{skill.name}-promote-"):
        raise SystemExit("--restore is not a promotion directory beside the requested skill")
    backup = transaction / "previous"
    if not backup.is_dir():
        raise SystemExit("selected transaction contains no previous skill backup")
    quarantine = None
    if skill.exists():
        quarantine = Path(tempfile.mkdtemp(prefix=f".{skill.name}-recovery-", dir=skill.parent)) / "replaced"
        os.replace(skill, quarantine)
    try:
        os.replace(backup, skill)
    except Exception:
        if quarantine is not None and quarantine.exists():
            os.replace(quarantine, skill)
        raise
    print(json.dumps({"restored": str(skill), "from": str(transaction),
                      "replaced_live_backup": str(quarantine) if quarantine else None}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
