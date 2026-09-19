from __future__ import annotations

import argparse
import json
import os
import subprocess
import threading
import webbrowser
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_DIR = ROOT / "runs"
INDEX_FILE = Path(__file__).with_name("index.html")
DOMAINS = ("health", "hle", "qf", "tau3")


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _line_count(path: Path) -> int:
    try:
        with path.open("rb") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return 0


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return records
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def _iso_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()


def _infer_domain(name: str, result: dict[str, Any] | None = None) -> str:
    if result:
        explicit = str(result.get("domain") or "").lower()
        benchmark = str(result.get("benchmark") or "").lower()
        for domain in DOMAINS:
            if explicit == domain or benchmark.startswith(domain):
                return domain
        if benchmark == "healthbench":
            return "health"
        if benchmark == "hlebench":
            return "hle"
        if benchmark == "qfbench":
            return "qf"
        if benchmark == "tau3bench":
            return "tau3"
    lowered = name.lower().replace("_", "-")
    for domain in DOMAINS:
        if lowered == domain or lowered.startswith(f"{domain}-") or f"/{domain}-" in lowered:
            return domain
    return "unknown"


def _job_progress(run_dir: Path) -> dict[str, int | bool]:
    harbor_dirs = list(run_dir.glob("**/harbor-jobs"))
    jobs: set[Path] = set()
    for harbor_dir in harbor_dirs:
        try:
            jobs.update(path for path in harbor_dir.iterdir() if path.is_dir())
        except OSError:
            continue

    finished = 0
    running = 0
    responses = 0
    for job in jobs:
        result = _read_json(job / "result.json")
        if result and result.get("finished_at"):
            finished += 1
        elif result and result.get("started_at"):
            running += 1
        for response in job.glob("task__*/agent/response.txt"):
            try:
                if response.stat().st_size > 0:
                    responses += 1
            except OSError:
                pass
    return {
        "jobs": len(jobs),
        "jobs_finished": finished,
        "jobs_running": running,
        "responses": responses,
        "has_running_job": running > 0,
    }


def _active_run_names(runs_dir: Path) -> set[str]:
    """Return top-level run directories mentioned by a live stbench process."""
    try:
        process_list = subprocess.run(
            ["ps", "-Ao", "command"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return set()
    active: set[str] = set()
    try:
        directories = [path for path in runs_dir.iterdir() if path.is_dir()]
    except OSError:
        return active
    for run_dir in directories:
        relative_marker = f"runs/{run_dir.name}"
        if relative_marker in process_list or str(run_dir) in process_list:
            active.add(run_dir.name)
    return active


def _cost_total(result: dict[str, Any]) -> float | None:
    values: list[float] = []
    for key in ("learner_cost", "grader_cost", "aux_cost"):
        block = result.get(key)
        if isinstance(block, dict) and isinstance(block.get("estimated_usd"), (int, float)):
            values.append(float(block["estimated_usd"]))
    return round(sum(values), 6) if values else None


def _token_total(result: dict[str, Any]) -> int | None:
    total = 0
    found = False
    for key in ("learner_usage", "grader_usage", "aux_usage"):
        block = result.get(key)
        if isinstance(block, dict) and isinstance(block.get("total_tokens"), int):
            total += block["total_tokens"]
            found = True
    return total if found else None


def _completed_record(eval_file: Path, runs_dir: Path) -> dict[str, Any] | None:
    result = _read_json(eval_file)
    if result is None:
        return None
    run_dir = eval_file.parent
    name = run_dir.relative_to(runs_dir).as_posix()
    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    delivery = result.get("delivery") if isinstance(result.get("delivery"), dict) else {}
    learner = result.get("learner") if isinstance(result.get("learner"), dict) else {}
    kwargs = learner.get("agent_kwargs") if isinstance(learner.get("agent_kwargs"), dict) else {}
    progress = _job_progress(run_dir)
    return {
        "id": name,
        "name": name,
        "domain": _infer_domain(name, result),
        "status": "complete",
        "updated_at": _iso_timestamp(eval_file.stat().st_mtime),
        "skill_rate": summary.get("skill_rate"),
        "placebo_rate": summary.get("placebo_rate"),
        "baseline_rate": summary.get("baseline_rate"),
        "net_delta": summary.get("net_delta"),
        "n_tasks": summary.get("n_tasks"),
        "n_pairs": summary.get("n_pairs"),
        "ci95": summary.get("ci95"),
        "note": summary.get("note") or result.get("note"),
        "empty_outputs": delivery.get("empty_outputs_total"),
        "model": learner.get("model"),
        "max_iterations": kwargs.get("max_iterations"),
        "tokens": _token_total(result),
        "cost_usd": _cost_total(result),
        "attempts": _line_count(run_dir / "attempts.jsonl"),
        **progress,
    }


def _incomplete_record(
    run_dir: Path, runs_dir: Path, active_names: set[str]
) -> dict[str, Any] | None:
    name = run_dir.relative_to(runs_dir).as_posix()
    progress = _job_progress(run_dir)
    attempts = _line_count(run_dir / "attempts.jsonl")
    recognizable = progress["jobs"] or attempts or (run_dir / "optimization.json").exists()
    if not recognizable:
        return None
    try:
        updated = max(
            [run_dir.stat().st_mtime]
            + [path.stat().st_mtime for path in run_dir.glob("**/result.json")]
            + [path.stat().st_mtime for path in run_dir.glob("**/job.log")]
        )
    except OSError:
        updated = run_dir.stat().st_mtime
    if run_dir.name in active_names:
        status = "running"
    elif progress["jobs"] and progress["jobs_finished"] == progress["jobs"]:
        status = "awaiting-summary"
    else:
        status = "incomplete"
    return {
        "id": name,
        "name": name,
        "domain": _infer_domain(name),
        "status": status,
        "updated_at": _iso_timestamp(updated),
        "skill_rate": None,
        "placebo_rate": None,
        "baseline_rate": None,
        "net_delta": None,
        "n_tasks": None,
        "n_pairs": None,
        "ci95": None,
        "note": "Evaluation has not produced eval_result.json yet",
        "empty_outputs": None,
        "model": None,
        "max_iterations": None,
        "tokens": None,
        "cost_usd": None,
        "attempts": attempts,
        **progress,
    }


def collect_runs(runs_dir: Path = DEFAULT_RUNS_DIR) -> dict[str, Any]:
    runs_dir = runs_dir.resolve()
    records: list[dict[str, Any]] = []
    completed_top_levels: set[str] = set()
    if runs_dir.is_dir():
        active_names = _active_run_names(runs_dir)
        for eval_file in runs_dir.glob("**/eval_result.json"):
            record = _completed_record(eval_file, runs_dir)
            if record:
                records.append(record)
                completed_top_levels.add(record["name"].split("/", 1)[0])
        for run_dir in runs_dir.iterdir():
            if not run_dir.is_dir() or run_dir.name in completed_top_levels:
                continue
            record = _incomplete_record(run_dir, runs_dir, active_names)
            if record:
                records.append(record)
    records.sort(key=lambda item: item["updated_at"], reverse=True)

    domains: dict[str, dict[str, Any]] = {}
    for domain in (*DOMAINS, "unknown"):
        subset = [record for record in records if record["domain"] == domain]
        completed = [record for record in subset if record["status"] == "complete"]
        latest = completed[0] if completed else (subset[0] if subset else None)
        domains[domain] = {
            "runs": len(subset),
            "completed": len(completed),
            "active": sum(record["status"] == "running" for record in subset),
            "latest_skill_rate": latest.get("skill_rate") if latest else None,
            "latest_net_delta": latest.get("net_delta") if latest else None,
        }

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "runs_dir": str(runs_dir),
        "count": len(records),
        "domains": domains,
        "runs": records,
    }


def _duration_seconds(started: Any, finished: Any) -> float | None:
    if not isinstance(started, str) or not isinstance(finished, str):
        return None
    try:
        start = datetime.fromisoformat(started.replace("Z", "+00:00"))
        end = datetime.fromisoformat(finished.replace("Z", "+00:00"))
    except ValueError:
        return None
    return round((end - start).total_seconds(), 1)


def _first_job_metrics(result: dict[str, Any]) -> dict[str, Any]:
    stats = result.get("stats")
    if not isinstance(stats, dict):
        return {}
    evals = stats.get("evals")
    if not isinstance(evals, dict):
        return {}
    for block in evals.values():
        if not isinstance(block, dict):
            continue
        metrics = block.get("metrics")
        if isinstance(metrics, list) and metrics and isinstance(metrics[0], dict):
            return metrics[0]
    return {}


def _trajectory_counts(job_dir: Path) -> tuple[int | None, int | None]:
    trajectory = next(job_dir.glob("task__*/agent/trajectory.json"), None)
    if trajectory is None:
        return None, None
    value = _read_json(trajectory)
    if value is not None:
        steps = value.get("steps")
    else:
        try:
            raw = json.loads(trajectory.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None, None
        steps = raw if isinstance(raw, list) else None
    if not isinstance(steps, list):
        return None, None
    calls = sum(
        len(step.get("tool_calls", []))
        for step in steps
        if isinstance(step, dict) and isinstance(step.get("tool_calls", []), list)
    )
    return len(steps), calls


def collect_job_results(run_name: str, runs_dir: Path = DEFAULT_RUNS_DIR) -> dict[str, Any]:
    runs_dir = runs_dir.resolve()
    run_dir = (runs_dir / run_name).resolve()
    if not run_dir.is_relative_to(runs_dir) or not run_dir.is_dir():
        raise FileNotFoundError(run_name)

    attempts_by_job: dict[str, dict[str, Any]] = {}
    for attempts_file in run_dir.glob("**/attempts.jsonl"):
        for attempt in _read_jsonl(attempts_file):
            trial_dir = attempt.get("trial_dir")
            if isinstance(trial_dir, str):
                attempts_by_job[Path(trial_dir).parent.name] = attempt

    jobs: list[dict[str, Any]] = []
    for harbor_dir in run_dir.glob("**/harbor-jobs"):
        for job_dir in sorted(path for path in harbor_dir.iterdir() if path.is_dir()):
            result = _read_json(job_dir / "result.json") or {}
            stats = result.get("stats") if isinstance(result.get("stats"), dict) else {}
            attempt = attempts_by_job.get(job_dir.name, {})
            metrics = _first_job_metrics(result)
            response = next(job_dir.glob("task__*/agent/response.txt"), None)
            try:
                response_bytes = response.stat().st_size if response else 0
            except OSError:
                response_bytes = 0
            trajectory_steps, tool_calls = _trajectory_counts(job_dir)
            if result.get("finished_at"):
                state = "error" if stats.get("n_errored_trials") else "complete"
            elif result.get("started_at"):
                state = "running"
            else:
                state = "pending"
            task_id = attempt.get("task_id")
            if not task_id:
                task_id = job_dir.name.rsplit("-", 1)[0]
            score = attempt.get("score")
            if score is None:
                score = metrics.get(
                    "reward", metrics.get("healthbench_raw_score", metrics.get("mean"))
                )
            jobs.append(
                {
                    "job": job_dir.name,
                    "task_id": task_id,
                    "arm": attempt.get("arm"),
                    "state": state,
                    "score": score,
                    "passed": attempt.get("passed"),
                    "attempt_status": attempt.get("status"),
                    "response_bytes": response_bytes,
                    "started_at": result.get("started_at"),
                    "finished_at": result.get("finished_at"),
                    "duration_seconds": _duration_seconds(
                        result.get("started_at"), result.get("finished_at")
                    ),
                    "input_tokens": stats.get("n_input_tokens"),
                    "output_tokens": stats.get("n_output_tokens"),
                    "cached_tokens": stats.get("n_cache_tokens"),
                    "trajectory_steps": trajectory_steps,
                    "tool_calls": tool_calls,
                    "metrics": metrics,
                    "errored_trials": stats.get("n_errored_trials"),
                }
            )
    jobs.sort(key=lambda item: (str(item["task_id"]), str(item["arm"]), item["job"]))
    return {"run": run_name, "count": len(jobs), "jobs": jobs}


class DashboardHandler(BaseHTTPRequestHandler):
    runs_dir = DEFAULT_RUNS_DIR

    def _send(self, content: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/runs":
            payload = json.dumps(collect_runs(self.runs_dir), separators=(",", ":")).encode()
            self._send(payload, "application/json; charset=utf-8")
            return
        if path == "/api/run":
            names = parse_qs(parsed.query).get("name", [])
            if len(names) != 1:
                self._send(b"Missing run name", "text/plain; charset=utf-8", HTTPStatus.BAD_REQUEST)
                return
            try:
                detail = collect_job_results(names[0], self.runs_dir)
            except FileNotFoundError:
                self._send(b"Run not found", "text/plain; charset=utf-8", HTTPStatus.NOT_FOUND)
                return
            payload = json.dumps(detail, separators=(",", ":")).encode()
            self._send(payload, "application/json; charset=utf-8")
            return
        if path in {"/", "/index.html"}:
            try:
                content = INDEX_FILE.read_bytes()
            except OSError as exc:
                self._send(str(exc).encode(), "text/plain; charset=utf-8", HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self._send(content, "text/html; charset=utf-8")
            return
        self._send(b"Not found", "text/plain; charset=utf-8", HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        if os.environ.get("STBENCH_DASHBOARD_LOG"):
            super().log_message(format, *args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve a read-only dashboard for benchmark runs.")
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true", help="Do not open a browser tab.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    handler = type("ConfiguredDashboardHandler", (DashboardHandler,), {"runs_dir": args.runs_dir})
    server = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{server.server_port}"
    print(f"Run dashboard: {url}")
    print(f"Reading: {args.runs_dir.resolve()}")
    print("Press Ctrl-C to stop.")
    if not args.no_open:
        threading.Timer(0.35, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
