"""Non-secret health checks for a teammate's local stbench environment."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import httpx
from huggingface_hub import HfApi

from .config import HackathonCfg, task_names


def _result(fn) -> dict:
    try:
        detail = fn()
        if isinstance(detail, dict):
            return {"ok": True, **detail}
        return {"ok": True, "detail": detail}
    except Exception as error:
        message = str(error)
        if isinstance(error, httpx.HTTPStatusError):
            try:
                message = error.response.json().get("error", {}).get("message") or message
            except Exception:
                pass
        return {"ok": False, "error": f"{type(error).__name__}: {message[:300]}"}


def _docker() -> dict:
    executable = shutil.which("docker")
    if not executable:
        raise RuntimeError("docker executable not found")
    run = subprocess.run([executable, "info", "--format", "{{.ServerVersion}}"],
                         text=True, capture_output=True, timeout=20)
    if run.returncode:
        raise RuntimeError(run.stderr.strip() or "Docker daemon is unavailable")
    return {"server_version": run.stdout.strip()}


def _models(base_url: str, key: str | None, expected: str | None = None) -> dict:
    if not key:
        raise RuntimeError("API key is not configured")
    response = httpx.get(base_url.rstrip("/") + "/v1/models",
                         headers={"Authorization": f"Bearer {key}"}, timeout=30)
    response.raise_for_status()
    values = response.json().get("data", [])
    ids = {item.get("id") for item in values if isinstance(item, dict)}
    result = {"model_count": len(values)}
    if expected:
        result["expected_model"] = expected
        result["expected_model_present"] = expected in ids
        if expected not in ids:
            raise RuntimeError(f"configured model {expected!r} is not available")
    return result


def _chat(base_url: str, key: str | None, model: str) -> dict:
    if not key:
        raise RuntimeError("API key is not configured")
    response = httpx.post(base_url.rstrip("/") + "/v1/chat/completions",
                          headers={"Authorization": f"Bearer {key}"}, json={
                              "model": model,
                              "messages": [{"role": "user", "content": "Reply with exactly: ok"}],
                              "temperature": 0,
                              "max_tokens": 64,
                          }, timeout=90)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("inference returned no visible response content")
    return {"model": model, "returned_content": bool(content)}


def _huggingface(cfg: HackathonCfg) -> dict:
    info = HfApi(token=os.environ.get("HF_TOKEN")).dataset_info(cfg.hf_repo, revision=cfg.hf_revision)
    expected = [sibling.rfilename for sibling in info.siblings or []]
    missing = [relative for relative in expected if not (cfg.data_dir / relative).is_file()]
    if missing:
        raise RuntimeError(f"dataset download incomplete: {len(missing)} of {len(expected)} files missing")
    return {"repo_id": info.id, "revision": info.sha, "remote_files": len(expected),
            "local_files_present": len(expected) - len(missing), "download_complete": not missing,
            "missing_files": len(missing)}


def _datasets(cfg: HackathonCfg) -> dict:
    counts = {}
    for name, domain in cfg.domains.items():
        counts[name] = len(task_names(domain)) if domain.dataset_dir.is_dir() else 0
    if not any(counts.values()):
        raise RuntimeError("no downloaded benchmark tasks found; run `stbench data pull`")
    return {"task_counts": counts}


def run_doctor(cfg: HackathonCfg, *, live_api: bool = False) -> dict:
    runware_key = os.environ.get("STBENCH_UPSTREAM_KEY") or os.environ.get(cfg.upstream_key_env)
    openai_key = os.environ.get("OPENAI_API_KEY")
    checks = {
        "docker": _result(_docker),
        "runware_auth": _result(lambda: _models(cfg.upstream_base_url, runware_key, cfg.learner_model)),
        "openai_auth": _result(lambda: _models("https://api.openai.com", openai_key)),
        "huggingface": _result(lambda: _huggingface(cfg)),
        "datasets": _result(lambda: _datasets(cfg)),
    }
    if live_api:
        checks["runware_inference"] = _result(
            lambda: _chat(cfg.upstream_base_url, runware_key, cfg.learner_model)
        )
        checks["openai_inference"] = _result(
            lambda: _chat("https://api.openai.com", openai_key, "gpt-4.1-nano")
        )
    return {"ok": all(item["ok"] for item in checks.values()), "checks": checks}


def format_doctor(result: dict) -> str:
    lines = []
    for name, check in result["checks"].items():
        marker = "PASS" if check["ok"] else "FAIL"
        detail = check.get("error") or ", ".join(
            f"{key}={value}" for key, value in check.items() if key != "ok"
        )
        lines.append(f"{marker:<4} {name:<20} {detail}")
    return "\n".join(lines)
