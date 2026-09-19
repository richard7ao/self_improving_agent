"""Compact comparisons for stbench evaluation and optimization outputs."""

from __future__ import annotations

import json
from pathlib import Path


def _load(raw: str | Path) -> tuple[Path, dict]:
    path = Path(raw).expanduser()
    if path.is_dir():
        options = [path / "optimization.json", path / "eval_result.json"]
        path = next((candidate for candidate in options if candidate.is_file()), path)
    if not path.is_file():
        raise ValueError(f"no optimization.json or eval_result.json at {raw}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"result must be a JSON object: {path}")
    return path.resolve(), value


def compare_results(paths: list[str | Path]) -> dict:
    rows = []
    for raw in paths:
        path, value = _load(raw)
        if "rounds" in value:
            rows.append({
                "path": str(path), "type": "optimization", "domain": value.get("domain"),
                "score": value.get("final_score"), "improvement": value.get("improvement"),
                "tasks": len(value.get("split", {}).get("tune", []))
                         + len(value.get("split", {}).get("validation", [])),
            })
        else:
            summary = value.get("summary", {})
            rows.append({
                "path": str(path), "type": "evaluation", "domain": value.get("domain"),
                "score": summary.get("skill_rate"), "improvement": summary.get("net_delta"),
                "tasks": summary.get("n_tasks"),
            })
    ranked = sorted(rows, key=lambda row: (row["score"] is not None, row["score"] or 0), reverse=True)
    return {"results": rows, "best": ranked[0]["path"] if ranked else None}


def format_comparison(result: dict) -> str:
    header = f"{'score':>8} {'change':>8} {'tasks':>6} {'domain':<10} result"
    lines = [header, "-" * len(header)]
    for row in sorted(result["results"], key=lambda item: (item["score"] is not None, item["score"] or 0),
                      reverse=True):
        score = "-" if row["score"] is None else f"{row['score']:.4f}"
        change = "-" if row["improvement"] is None else f"{row['improvement']:+.4f}"
        lines.append(f"{score:>8} {change:>8} {str(row['tasks']):>6} {str(row['domain']):<10} {row['path']}")
    return "\n".join(lines)
