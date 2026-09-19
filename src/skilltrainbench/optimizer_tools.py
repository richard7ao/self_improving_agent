"""Deterministic utilities for trustworthy skill-optimization experiments.

The optimizer's model calls propose changes; this module handles work that should not
depend on model judgment: splitting, comparisons, safety gates, candidate similarity,
static script auditing, provenance, budget forecasts, and durable JSON records.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import platform
import random
import re
import statistics
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence


_TOKEN = re.compile(r"[a-z0-9_]+")
_BLOCKED_IMPORTS = frozenset({
    "aiohttp", "ctypes", "ftplib", "httpx", "importlib", "requests", "socket",
    "smtplib", "subprocess", "telnetlib", "urllib", "webbrowser",
})
_BLOCKED_CALLS = frozenset({"compile", "eval", "exec", "__import__"})
_BLOCKED_ATTRIBUTES = frozenset({
    "os.popen", "os.spawnl", "os.spawnle", "os.spawnlp", "os.spawnlpe", "os.spawnv",
    "os.spawnve", "os.spawnvp", "os.spawnvpe", "os.system",
})


def canonical_tokens(text: str) -> list[str]:
    """Stable lexical representation used for similarity and leakage checks."""
    return _TOKEN.findall(text.casefold())


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def skill_files(root: str | Path) -> dict[str, str]:
    base = Path(root).resolve()
    files: dict[str, str] = {}
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            files[path.relative_to(base).as_posix()] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
    return files


def skill_digest(root: str | Path) -> str:
    digest = hashlib.sha256()
    for relative, content in skill_files(root).items():
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(content.encode())
        digest.update(b"\0")
    return digest.hexdigest()


def _token_set(root: str | Path) -> set[str]:
    values = skill_files(root)
    return set(canonical_tokens("\n".join(f"{path}\n{text}" for path, text in values.items())))


def candidate_diversity(paths: Sequence[str | Path]) -> dict:
    """Pairwise lexical similarity plus exact content hashes for candidate folders."""
    records = [{"path": str(Path(path)), "digest": skill_digest(path), "tokens": _token_set(path)}
               for path in paths]
    pairs = []
    for left_index, left in enumerate(records):
        for right in records[left_index + 1:]:
            union = left["tokens"] | right["tokens"]
            similarity = len(left["tokens"] & right["tokens"]) / len(union) if union else 1.0
            pairs.append({
                "left": left["path"], "right": right["path"],
                "jaccard": round(similarity, 6),
                "exact_duplicate": left["digest"] == right["digest"],
            })
    return {
        "candidates": [{"path": row["path"], "digest": row["digest"],
                        "token_count": len(row["tokens"])} for row in records],
        "pairs": pairs,
        "minimum_pairwise_distance": (
            round(min((1.0 - row["jaccard"] for row in pairs), default=1.0), 6)
        ),
        "exact_duplicate_pairs": sum(bool(row["exact_duplicate"]) for row in pairs),
    }


def duplicate_candidate_indexes(paths: Sequence[str | Path]) -> set[int]:
    """Return zero-based indexes that duplicate an earlier candidate exactly."""
    seen: set[str] = set()
    duplicates: set[int] = set()
    for index, path in enumerate(paths):
        digest = skill_digest(path)
        if digest in seen:
            duplicates.add(index)
        else:
            seen.add(digest)
    return duplicates


def _shingles(text: str, width: int) -> set[tuple[str, ...]]:
    tokens = canonical_tokens(text)
    return {tuple(tokens[index:index + width]) for index in range(max(0, len(tokens) - width + 1))}


def semantic_leakage_report(candidate: str | Path, sources: Mapping[str, str], *,
                            shingle_width: int = 5, warn_jaccard: float = 0.18) -> dict:
    """Heuristic paraphrase-oriented overlap report; not a proof of semantic safety."""
    candidate_text = "\n".join(skill_files(candidate).values())
    candidate_shingles = _shingles(candidate_text, shingle_width)
    matches = []
    for name, text in sources.items():
        source_shingles = _shingles(text, shingle_width)
        union = candidate_shingles | source_shingles
        overlap = len(candidate_shingles & source_shingles) / len(union) if union else 0.0
        if overlap >= warn_jaccard:
            matches.append({"source": name, "shingle_jaccard": round(overlap, 6)})
    matches.sort(key=lambda row: row["shingle_jaccard"], reverse=True)
    return {
        "ok": not matches,
        "heuristic": True,
        "shingle_width": shingle_width,
        "warning_threshold": warn_jaccard,
        "matches": matches,
        "note": "Lexical overlap can flag suspicious paraphrases but cannot certify absence of leakage.",
    }


def audit_python_source(source: str, *, filename: str = "<generated>") -> list[str]:
    """Conservative static checks for scripts generated into a submitted skill."""
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as error:
        return [f"syntax_error:{error.msg}:{error.lineno}"]
    issues: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in _BLOCKED_IMPORTS:
                    issues.append(f"blocked_import:{alias.name}:{node.lineno}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root in _BLOCKED_IMPORTS:
                issues.append(f"blocked_import:{node.module}:{node.lineno}")
            if root == "os":
                for alias in node.names:
                    if alias.name == "popen" or alias.name == "system" or alias.name.startswith("spawn"):
                        issues.append(f"blocked_import:os.{alias.name}:{node.lineno}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _BLOCKED_CALLS:
                issues.append(f"blocked_call:{node.func.id}:{node.lineno}")
            elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                qualified = f"{node.func.value.id}.{node.func.attr}"
                if qualified in _BLOCKED_ATTRIBUTES:
                    issues.append(f"blocked_call:{qualified}:{node.lineno}")
    return sorted(set(issues))


def audit_generated_scripts(root: str | Path) -> dict:
    scripts = []
    for path in sorted(Path(root).rglob("*.py")):
        if path.is_symlink():
            scripts.append({"path": str(path), "issues": ["symlink_not_allowed"]})
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            scripts.append({"path": str(path), "issues": [f"unreadable:{type(error).__name__}"]})
            continue
        scripts.append({"path": str(path), "issues": audit_python_source(source, filename=str(path))})
    return {"ok": all(not row["issues"] for row in scripts), "scripts": scripts}


def run_script_self_test(path: str | Path, *, timeout_s: float = 5.0) -> dict:
    """Run an explicit `--self-test` in a temporary cwd with a minimal environment.

    This is a reliability check, not a complete OS security sandbox.
    """
    script = Path(path).resolve()
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"}
    with tempfile.TemporaryDirectory(prefix="stbench-script-test-") as raw:
        started = time.monotonic()
        try:
            result = subprocess.run(
                [sys.executable, str(script), "--self-test"], cwd=raw, env=env,
                text=True, capture_output=True, timeout=timeout_s, check=False,
            )
            return {
                "ok": result.returncode == 0, "returncode": result.returncode,
                "duration_ms": round((time.monotonic() - started) * 1000, 3),
                "stdout": result.stdout[-4000:], "stderr": result.stderr[-4000:],
                "sandbox": "temporary-cwd-and-minimal-env-only",
            }
        except subprocess.TimeoutExpired as error:
            return {"ok": False, "error": "timeout", "timeout_s": timeout_s,
                    "stdout": str(error.stdout or "")[-4000:], "stderr": str(error.stderr or "")[-4000:]}


def stratified_split(records: Sequence[Mapping], validation_fraction: float, seed: int,
                     *, id_key: str = "task_id", stratum_key: str = "stratum") -> dict:
    if not 0 <= validation_fraction < 1:
        raise ValueError("validation_fraction must be in [0, 1)")
    groups: dict[str, list[str]] = defaultdict(list)
    for row in records:
        task_id = row.get(id_key)
        if not isinstance(task_id, str) or not task_id:
            raise ValueError(f"every record needs non-empty {id_key!r}")
        groups[str(row.get(stratum_key) or "unknown")].append(task_id)
    rng = random.Random(seed)
    tune: list[str] = []
    validation: list[str] = []
    allocation = {}
    for stratum in sorted(groups):
        values = sorted(groups[stratum])
        rng.shuffle(values)
        n_validation = 0 if len(values) == 1 else min(
            len(values) - 1, max(1, round(len(values) * validation_fraction))
        )
        validation.extend(values[:n_validation])
        tune.extend(values[n_validation:])
        allocation[stratum] = {"tune": len(values) - n_validation, "validation": n_validation}
    rng.shuffle(tune)
    rng.shuffle(validation)
    return {"tune": tune, "validation": validation, "allocation": allocation, "seed": seed}


def classify_attempts(rows: Iterable[Mapping], *, low_score: float = 0.5) -> dict:
    counts: dict[str, int] = defaultdict(int)
    by_task = []
    for row in rows:
        answer = str(row.get("answer") or "").strip()
        score = row.get("score")
        status = row.get("status")
        if not answer:
            failure = "delivery_failure"
        elif status not in (None, "ok", "invalid_output"):
            failure = "infrastructure_failure"
        elif score is None:
            failure = "invalidated_or_ungraded"
        elif float(score) < low_score:
            failure = "low_score"
        else:
            failure = "pass"
        counts[failure] += 1
        by_task.append({"task_id": row.get("task_id"), "task_name": row.get("task_name"),
                        "arm": row.get("arm"), "class": failure, "score": score})
    return {"counts": dict(sorted(counts.items())), "attempts": by_task, "low_score": low_score}


def _percentile(values: Sequence[float], quantile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot take percentile of an empty sequence")
    position = (len(ordered) - 1) * quantile
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def paired_statistics(incumbent: Mapping[str, float], challenger: Mapping[str, float], *,
                      iterations: int = 5000, confidence: float = 0.95, seed: int = 0) -> dict:
    task_ids = sorted(set(incumbent) & set(challenger))
    if not task_ids:
        raise ValueError("no paired task scores")
    diffs = [float(challenger[task]) - float(incumbent[task]) for task in task_ids]
    rng = random.Random(seed)
    means = [statistics.fmean(rng.choice(diffs) for _ in diffs) for _ in range(max(1, iterations))]
    alpha = (1.0 - confidence) / 2.0
    return {
        "n": len(diffs), "mean_delta": statistics.fmean(diffs), "median_delta": statistics.median(diffs),
        "ci": [_percentile(means, alpha), _percentile(means, 1.0 - alpha)],
        "confidence": confidence, "bootstrap_iterations": max(1, iterations),
        "wins": sum(value > 0 for value in diffs), "ties": sum(value == 0 for value in diffs),
        "losses": sum(value < 0 for value in diffs),
        "per_task": [{"task_id": task, "incumbent": float(incumbent[task]),
                      "challenger": float(challenger[task]),
                      "delta": float(challenger[task]) - float(incumbent[task])} for task in task_ids],
    }


def safety_regression_gate(incumbent: Mapping[str, float], challenger: Mapping[str, float],
                           labels: Mapping[str, Sequence[str]], *, tolerance: float = 0.0,
                           critical_labels: Sequence[str] = ()) -> dict:
    critical = set(critical_labels)
    regressions = []
    for task_id in sorted(set(incumbent) & set(challenger)):
        delta = float(challenger[task_id]) - float(incumbent[task_id])
        task_labels = sorted(set(labels.get(task_id, ())))
        if delta < -abs(tolerance):
            regressions.append({"task_id": task_id, "delta": delta, "labels": task_labels,
                                "critical": bool(critical & set(task_labels))})
    critical_regressions = [row for row in regressions if row["critical"]]
    return {"ok": not critical_regressions, "regressions": regressions,
            "critical_regressions": critical_regressions, "tolerance": tolerance}


def promotion_gate(incumbent_tune: Mapping[str, float], challenger_tune: Mapping[str, float],
                   incumbent_validation: Mapping[str, float], challenger_validation: Mapping[str, float], *,
                   min_improvement: float = 0.0, confidence: float = 0.95,
                   bootstrap_iterations: int = 5000, seed: int = 0,
                   require_confidence: bool = True, safety: dict | None = None) -> dict:
    tune = paired_statistics(incumbent_tune, challenger_tune, iterations=bootstrap_iterations,
                             confidence=confidence, seed=seed)
    validation = paired_statistics(incumbent_validation, challenger_validation,
                                   iterations=bootstrap_iterations, confidence=confidence, seed=seed + 1)
    all_incumbent = {**incumbent_tune, **incumbent_validation}
    all_challenger = {**challenger_tune, **challenger_validation}
    combined = paired_statistics(all_incumbent, all_challenger, iterations=bootstrap_iterations,
                                 confidence=confidence, seed=seed + 2)
    reasons = []
    if combined["mean_delta"] <= min_improvement:
        reasons.append("aggregate_improvement_below_threshold")
    if validation["mean_delta"] <= 0:
        reasons.append("validation_did_not_strictly_improve")
    if require_confidence and combined["ci"][0] <= min_improvement:
        reasons.append("confidence_lower_bound_below_threshold")
    if safety is not None and not safety.get("ok", False):
        reasons.append("critical_safety_regression")
    return {"promote": not reasons, "reasons": reasons, "tune": tune,
            "validation": validation, "combined": combined, "safety": safety,
            "min_improvement": min_improvement, "require_confidence": require_confidence}


def evaluation_scores(result: Mapping, *, arm: str = "skill") -> dict[str, float]:
    scores = {}
    for row in result.get("per_task", []) or []:
        task_id, value = row.get("task_id"), row.get(arm)
        if isinstance(task_id, str) and isinstance(value, (int, float)) and not isinstance(value, bool):
            scores[task_id] = float(value)
    return scores


def budget_forecast(*, tasks: int, candidates: int, rounds: int, tune_fraction: float = 0.75,
                    repeats: int = 1, arms: int = 1, learner_tokens_per_attempt: int = 0,
                    grader_tokens_per_attempt: int = 0, optimizer_calls_per_round: int | None = None) -> dict:
    if min(tasks, candidates, rounds, repeats, arms) < 0 or not 0 <= tune_fraction <= 1:
        raise ValueError("counts must be non-negative and tune_fraction must be in [0, 1]")
    tune_tasks = round(tasks * tune_fraction)
    validation_tasks = tasks - tune_tasks
    incumbent_attempts = tasks * repeats * arms
    candidate_attempts = rounds * candidates * tune_tasks * repeats * arms
    finalist_attempts = rounds * validation_tasks * repeats * arms
    attempts = incumbent_attempts + candidate_attempts + finalist_attempts
    optimizer_calls = rounds * (optimizer_calls_per_round if optimizer_calls_per_round is not None
                                else candidates + 1)
    return {
        "tasks": {"total": tasks, "tune": tune_tasks, "validation": validation_tasks},
        "attempts": {"incumbent": incumbent_attempts, "candidates": candidate_attempts,
                     "finalists": finalist_attempts, "total": attempts},
        "optimizer_calls": optimizer_calls,
        "estimated_tokens": {"learner": attempts * learner_tokens_per_attempt,
                             "grader": attempts * grader_tokens_per_attempt},
    }


def _git(repo: Path, *args: str) -> str | None:
    try:
        run = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True,
                             timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return run.stdout.strip() if run.returncode == 0 else None


def provenance_snapshot(repo: str | Path, *, extra_paths: Sequence[str | Path] = ()) -> dict:
    root = Path(repo).resolve()
    head = _git(root, "rev-parse", "HEAD")
    status = _git(root, "status", "--porcelain=v1")
    paths = {}
    for raw in extra_paths:
        path = Path(raw)
        path = path if path.is_absolute() else root / path
        if path.is_file():
            paths[str(path.relative_to(root)) if path.is_relative_to(root) else str(path)] = file_sha256(path)
        elif path.is_dir():
            paths[str(path.relative_to(root)) if path.is_relative_to(root) else str(path)] = skill_digest(path)
    return {
        "created_unix": time.time(), "repo": str(root), "git_head": head,
        "git_dirty": bool(status), "git_status": status.splitlines() if status else [],
        "python": sys.version, "platform": platform.platform(), "artifacts": paths,
    }


def write_json_atomic(path: str | Path, value: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    temporary = Path(raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def append_registry(path: str | Path, record: Mapping) -> dict:
    target = Path(path)
    current = []
    if target.is_file():
        value = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(value, list):
            raise ValueError("experiment registry must contain a JSON array")
        current = value
    entry = {"sequence": len(current), "recorded_unix": time.time(), **dict(record)}
    current.append(entry)
    write_json_atomic(target, current)
    return entry
