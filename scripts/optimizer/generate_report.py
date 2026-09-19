#!/usr/bin/env python3
"""Render a compact Markdown report from an evaluation or optimization JSON result."""

import argparse
import json
from pathlib import Path


def report(path: Path, value: dict) -> str:
    lines = [f"# Experiment report: {path.parent.name}", "", f"Source: `{path}`", ""]
    if "rounds" in value:
        lines.extend([
            "## Optimization", "",
            f"- Domain: `{value.get('domain')}`",
            f"- Initial score: `{value.get('initial_score')}`",
            f"- Final score: `{value.get('final_score')}`",
            f"- Improvement: `{value.get('improvement')}`",
            f"- Rounds: `{len(value.get('rounds', []))}`",
            f"- Promotions: `{sum(bool(row.get('promoted')) for row in value.get('rounds', []))}`",
            "", "## Round decisions", "",
        ])
        for row in value.get("rounds", []):
            lines.append(f"- Round {row.get('round')}: promoted={row.get('promoted')}, "
                         f"challenger={row.get('challenger')}, score={row.get('challenger_score')}")
    else:
        summary = value.get("summary", {})
        lines.extend(["## Evaluation", "", f"- Domain: `{value.get('domain')}`",
                      f"- Benchmark: `{value.get('benchmark')}`",
                      f"- Tasks: `{summary.get('n_tasks')}`",
                      f"- Skill rate: `{summary.get('skill_rate')}`",
                      f"- Net delta: `{summary.get('net_delta')}`",
                      f"- CI95: `{summary.get('ci95')}`"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    value = json.loads(args.result.read_text(encoding="utf-8"))
    text = report(args.result, value)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
