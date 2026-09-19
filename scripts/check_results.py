#!/usr/bin/env python3
"""Print or watch read-only summaries of local benchmark run artifacts."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.app import DEFAULT_RUNS_DIR, DOMAINS, collect_job_results, collect_runs


def _domains(values: list[str] | None) -> tuple[str, ...]:
    if not values:
        return DOMAINS
    selected: list[str] = []
    for value in values:
        for domain in value.split(","):
            domain = domain.strip().lower()
            if domain not in DOMAINS:
                raise ValueError(f"unknown domain {domain!r}; choose from {', '.join(DOMAINS)}")
            if domain not in selected:
                selected.append(domain)
    return tuple(selected)


def build_report(
    runs_dir: Path,
    domains: tuple[str, ...],
    latest: int,
    include_incomplete: bool = False,
) -> dict[str, Any]:
    payload = collect_runs(runs_dir)
    records = [record for record in payload["runs"] if record["domain"] in domains]
    output: dict[str, Any] = {
        "generated_at": payload["generated_at"],
        "runs_dir": payload["runs_dir"],
        "domains": {},
    }
    for domain in domains:
        subset = [record for record in records if record["domain"] == domain]
        visible_states = {"running"}
        if include_incomplete:
            visible_states.update({"incomplete", "awaiting-summary"})
        active = [record.copy() for record in subset if record["status"] in visible_states]
        completed = [record for record in subset if record["status"] == "complete"][:latest]
        for record in active:
            try:
                detail = collect_job_results(record["name"], runs_dir)
            except (FileNotFoundError, OSError):
                detail = {"count": 0, "jobs": []}
            record["job_results"] = detail["jobs"]
        output["domains"][domain] = {"active": active, "completed": completed}
    return output


def _number(value: Any) -> str:
    return "—" if not isinstance(value, (int, float)) else f"{float(value):.4f}"


def render(report: dict[str, Any]) -> str:
    lines = [f"Benchmark results · {report['generated_at']}", f"Runs: {report['runs_dir']}"]
    for domain, group in report["domains"].items():
        lines.append("")
        lines.append(domain.upper())
        active = group["active"]
        completed = group["completed"]
        if not active:
            lines.append("  active: none")
        for record in active:
            lines.append(
                "  {status:<16} {name} · jobs {done}/{total} · responses {responses}".format(
                    status=record["status"],
                    name=record["name"],
                    done=record["jobs_finished"],
                    total=record["jobs"],
                    responses=record["responses"],
                )
            )
            for job in record.get("job_results", []):
                score = _number(job.get("score"))
                arm = job.get("arm") or "arm-pending"
                errors = job.get("errored_trials") or 0
                lines.append(
                    f"    {job['state']:<8} {arm:<11} score={score} errors={errors} "
                    f"task={job['task_id']}"
                )
        if not completed:
            lines.append("  completed: none")
        for record in completed:
            lines.append(
                "  complete         {name} · skill={skill} placebo={placebo} "
                "net={net} tasks={tasks} empty={empty}".format(
                    name=record["name"],
                    skill=_number(record["skill_rate"]),
                    placebo=_number(record["placebo_rate"]),
                    net=_number(record["net_delta"]),
                    tasks=record["n_tasks"] if record["n_tasks"] is not None else "—",
                    empty=(
                        record["empty_outputs"]
                        if record["empty_outputs"] is not None
                        else "—"
                    ),
                )
            )
    return "\n".join(lines)


def _fingerprint(report: dict[str, Any]) -> str:
    stable = dict(report)
    stable.pop("generated_at", None)
    return json.dumps(stable, sort_keys=True, default=str)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show completed scores and partial progress for local benchmark runs."
    )
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument(
        "--domain",
        action="append",
        help="Domain or comma-separated domains. Defaults to health, hle, qf, tau3.",
    )
    parser.add_argument("--latest", type=int, default=1, help="Completed runs per domain.")
    parser.add_argument(
        "--watch",
        type=float,
        metavar="SECONDS",
        help="Poll continuously and print only when artifacts change.",
    )
    parser.add_argument(
        "--include-incomplete",
        action="store_true",
        help="Also show abandoned or summary-less historical run directories.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        domains = _domains(args.domain)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    if args.latest < 1:
        raise SystemExit("--latest must be at least 1")
    if args.watch is not None and args.watch < 1:
        raise SystemExit("--watch must be at least 1 second")

    previous: str | None = None
    try:
        while True:
            report = build_report(
                args.runs_dir,
                domains,
                args.latest,
                include_incomplete=args.include_incomplete,
            )
            fingerprint = _fingerprint(report)
            if fingerprint != previous:
                if previous is not None and not args.json:
                    print("\n" + "=" * 80 + "\n")
                print(json.dumps(report, indent=2) if args.json else render(report), flush=True)
                previous = fingerprint
            if args.watch is None:
                return 0
            time.sleep(args.watch)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
