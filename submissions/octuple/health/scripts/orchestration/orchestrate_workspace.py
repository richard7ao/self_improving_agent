#!/usr/bin/env python3
"""Deterministic filesystem orchestration for bounded per-question review.

This script does not call models, networks, subprocesses, or clinical services.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROLES = (
    "context-evidence",
    "clinical-options-uncertainty",
    "safety-urgency",
    "constraints-artifact",
    "quantitative-data",
)
MODES = (
    "symptom",
    "treatment",
    "sparse-context",
    "bounded-artifact",
    "quantitative-data",
)
MODE_ROLES = {
    "symptom": ("context-evidence", "clinical-options-uncertainty", "safety-urgency"),
    "treatment": ("context-evidence", "clinical-options-uncertainty", "safety-urgency"),
    "sparse-context": ("context-evidence",),
    "bounded-artifact": ("context-evidence", "constraints-artifact"),
    "quantitative-data": ("context-evidence", "quantitative-data", "safety-urgency"),
}
ROLE_SPECS = {
    "context-evidence": {
        "objective": "Establish context sufficiency and an evidence ledger before conclusions.",
        "scope": [
            "Separate reported, explicitly denied, inferred, and unassessed findings.",
            "Identify one or two decision-changing unknowns and conversation-continuity risks.",
            "Flag unsupported assumptions; do not diagnose or choose treatment.",
        ],
    },
    "clinical-options-uncertainty": {
        "objective": "Compare reasonable action pathways and calibrate the strongest claim.",
        "scope": [
            "Describe conditional options, evidence limits, alternatives, and monitoring needs.",
            "Identify contraindication or special-population questions when relevant.",
            "State a strongest counterhypothesis; do not prescribe or provide a final diagnosis.",
        ],
    },
    "safety-urgency": {
        "objective": "Audit urgency, under-triage, needless escalation, and unresolved harm.",
        "scope": [
            "Prioritize observable warning signs and attach proportionate timing.",
            "Check vulnerable populations and dangerous reassurance without boilerplate.",
            "Emit structured safety flags; unresolved critical risk must remain open.",
        ],
    },
    "constraints-artifact": {
        "objective": "Audit the requested artifact and mechanical response contract.",
        "scope": [
            "Identify audience, inclusions, exclusions, headings/order, length, and tone constraints.",
            "Check that facts and uncertainty are preserved without adding unsolicited advice.",
            "Specify mechanical validation and delivery requirements; do not invent a schema.",
        ],
    },
    "quantitative-data": {
        "objective": "Verify arithmetic, units, chronology, and data presentation.",
        "scope": [
            "Check inputs, units, denominators, ordering, formulas, and rounding.",
            "Separate deterministic calculation from clinical interpretation.",
            "Reject ambiguous inputs; never select a dose or treatment.",
        ],
    },
}
RESULT_KEYS = {
    "schema_version", "question_id", "subtask_id", "role", "status", "summary",
    "rationale", "evidence", "assumptions", "confidence", "counterhypothesis",
    "recommendations", "conflicts", "safety_flags", "created_at",
}
DECISION_KEYS = {
    "schema_version", "question_id", "summary", "rationale", "evidence_refs",
    "assumptions", "confidence", "counterhypothesis", "conflict_resolutions",
    "safety_dispositions", "final_requirements", "approved_for_delivery", "created_at",
}
MAX_TEXT_BYTES = 200_000


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_question(text: str) -> str:
    value = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not value:
        raise ValueError("question must be non-empty")
    encoded = (value + "\n").encode("utf-8")
    if len(encoded) > MAX_TEXT_BYTES:
        raise ValueError("question exceeds size limit")
    if b"\x00" in encoded:
        raise ValueError("question contains NUL")
    return value + "\n"


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError(f"refusing symlink path: {path}")
    descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(raw)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_text(path: Path, text: str) -> None:
    atomic_write(path, text.encode("utf-8"))


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def require_string(value: Any, name: str, *, minimum: int = 1, maximum: int = 1200) -> str:
    if not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum:
        raise ValueError(f"{name} must be a string of {minimum}..{maximum} nonblank characters")
    return value


def require_string_list(value: Any, name: str, *, minimum: int = 0, maximum: int = 8,
                        item_maximum: int = 500) -> list[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ValueError(f"{name} must contain {minimum}..{maximum} items")
    for index, item in enumerate(value):
        require_string(item, f"{name}[{index}]", maximum=item_maximum)
    return value


def question_paths(qdir: Path) -> dict[str, Path]:
    return {
        "question": qdir / "question.txt",
        "manifest": qdir / "manifest.json",
        "subtasks": qdir / "subtasks",
        "decision": qdir / "synthesis" / "decision.json",
        "final": qdir / "final.txt",
        "validation": qdir / "validation.json",
    }


def load_question(qdir_raw: str | Path) -> tuple[Path, dict[str, Any]]:
    qdir = Path(qdir_raw).expanduser().resolve()
    if not qdir.is_dir() or qdir.is_symlink():
        raise ValueError(f"invalid question directory: {qdir}")
    paths = question_paths(qdir)
    manifest = load_json(paths["manifest"])
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported manifest schema")
    question = paths["question"]
    if not question.is_file() or question.is_symlink():
        raise ValueError("question.txt is missing or unsafe")
    if sha256_file(question) != manifest.get("question_sha256"):
        raise ValueError("question.txt hash does not match manifest")
    expected_id = f"q-{manifest['question_sha256'][:16]}"
    if manifest.get("question_id") != expected_id or qdir.name != expected_id:
        raise ValueError("question identity mismatch")
    return qdir, manifest


def init_workspace(workspace: str | Path, question: str, *, max_subtasks: int = 3) -> Path:
    if not 1 <= max_subtasks <= len(ROLES):
        raise ValueError("max_subtasks must be between 1 and 5")
    normalized = normalize_question(question)
    digest = sha256_bytes(normalized.encode("utf-8"))
    question_id = f"q-{digest[:16]}"
    root = Path(workspace).expanduser().resolve()
    qdir = root / "questions" / question_id
    if qdir.exists():
        existing, manifest = load_question(qdir)
        if (existing / "question.txt").read_text(encoding="utf-8") != normalized:
            raise ValueError("stable question ID collision")
        return existing
    qdir.mkdir(parents=True, exist_ok=False)
    paths = question_paths(qdir)
    paths["subtasks"].mkdir()
    paths["decision"].parent.mkdir()
    write_text(paths["question"], normalized)
    timestamp = now()
    manifest = {
        "schema_version": 1,
        "question_id": question_id,
        "question_sha256": digest,
        "created_at": timestamp,
        "updated_at": timestamp,
        "state": "initialized",
        "mode": None,
        "max_subtasks": max_subtasks,
        "selected_roles": [],
        "subtasks": [],
        "decision_sha256": None,
        "final_sha256": None,
        "paths": {
            "question": "question.txt",
            "subtasks": "subtasks",
            "decision": "synthesis/decision.json",
            "final": "final.txt",
            "validation": "validation.json",
        },
    }
    write_json(paths["manifest"], manifest)
    write_json(paths["validation"], {
        "schema_version": 1, "question_id": question_id, "delivered": False,
        "checks": ["not yet delivered"], "updated_at": timestamp,
    })
    return qdir


def _assignment(question_id: str, subtask_id: str, role: str) -> dict[str, Any]:
    spec = ROLE_SPECS[role]
    return {
        "schema_version": 1,
        "question_id": question_id,
        "subtask_id": subtask_id,
        "role": role,
        "objective": spec["objective"],
        "scope": spec["scope"],
        "question_ref": "../../question.txt",
        "required_result": {
            "schema": "../../../schemas/subtask_result.schema.json",
            "fields": [
                "summary", "rationale", "evidence", "assumptions", "confidence",
                "counterhypothesis", "recommendations", "conflicts", "safety_flags",
            ],
            "instruction": "Be concise; cite supplied evidence; declare conflicts and unresolved safety risk.",
        },
        "assigned_to": None,
        "status": "planned",
        "created_at": now(),
        "updated_at": now(),
    }


def plan_question(qdir_raw: str | Path, mode: str, *, roles: Iterable[str] = (),
                  max_subtasks: int | None = None) -> dict[str, Any]:
    qdir, manifest = load_question(qdir_raw)
    if mode not in MODES:
        raise ValueError(f"unsupported mode: {mode}")
    cap = max_subtasks if max_subtasks is not None else int(manifest["max_subtasks"])
    if not 1 <= cap <= len(ROLES):
        raise ValueError("max_subtasks must be between 1 and 5")
    allowed = MODE_ROLES[mode]
    selected = list(dict.fromkeys(roles)) if list(roles) else list(allowed[:cap])
    if not selected or len(selected) > cap:
        raise ValueError(f"plan needs 1..{cap} roles")
    unknown = [role for role in selected if role not in ROLES]
    irrelevant = [role for role in selected if role not in allowed]
    if unknown:
        raise ValueError(f"unknown roles: {unknown}")
    if irrelevant:
        raise ValueError(f"roles not relevant to mode {mode}: {irrelevant}")
    if manifest["subtasks"]:
        if manifest["mode"] == mode and manifest["selected_roles"] == selected:
            return manifest
        raise ValueError("question is already planned; do not silently replace assignments")

    paths = question_paths(qdir)
    records = []
    for index, role in enumerate(selected, 1):
        subtask_id = f"{index:02d}-{role}"
        folder = paths["subtasks"] / subtask_id
        folder.mkdir()
        assignment_path = folder / "assignment.json"
        write_json(assignment_path, _assignment(manifest["question_id"], subtask_id, role))
        records.append({
            "id": subtask_id, "role": role, "status": "planned",
            "assignment_sha256": sha256_file(assignment_path), "result_sha256": None,
        })
    manifest.update({
        "mode": mode, "max_subtasks": cap, "selected_roles": selected,
        "subtasks": records, "state": "planned", "updated_at": now(),
    })
    write_json(paths["manifest"], manifest)
    return manifest


def _subtask(manifest: dict[str, Any], subtask_id: str) -> dict[str, Any]:
    for record in manifest["subtasks"]:
        if record["id"] == subtask_id:
            return record
    raise ValueError(f"unknown subtask: {subtask_id}")


def assign_subtask(qdir_raw: str | Path, subtask_id: str, agent: str) -> dict[str, Any]:
    require_string(agent, "agent", maximum=120)
    qdir, manifest = load_question(qdir_raw)
    record = _subtask(manifest, subtask_id)
    path = qdir / "subtasks" / subtask_id / "assignment.json"
    assignment = load_json(path)
    current = assignment.get("assigned_to")
    if current not in (None, agent):
        raise ValueError(f"subtask already assigned to {current}")
    assignment.update({"assigned_to": agent, "status": "assigned", "updated_at": now()})
    write_json(path, assignment)
    record.update({"status": "assigned", "assignment_sha256": sha256_file(path)})
    manifest.update({"state": "assigned", "updated_at": now()})
    write_json(qdir / "manifest.json", manifest)
    return assignment


def validate_result(value: dict[str, Any], *, question_id: str, subtask_id: str,
                    role: str) -> None:
    if set(value) != RESULT_KEYS:
        raise ValueError(f"result keys mismatch: missing={sorted(RESULT_KEYS-set(value))}, extra={sorted(set(value)-RESULT_KEYS)}")
    if value["schema_version"] != 1 or value["question_id"] != question_id:
        raise ValueError("result question identity mismatch")
    if value["subtask_id"] != subtask_id or value["role"] != role:
        raise ValueError("result subtask identity mismatch")
    if value["status"] not in {"complete", "blocked"}:
        raise ValueError("result status must be complete or blocked")
    require_string(value["summary"], "summary")
    require_string_list(value["rationale"], "rationale", minimum=1, maximum=6)
    require_string_list(value["assumptions"], "assumptions", maximum=6)
    require_string_list(value["recommendations"], "recommendations", minimum=1, maximum=6)
    require_string_list(value["conflicts"], "conflicts", maximum=6)
    if not isinstance(value["confidence"], (int, float)) or isinstance(value["confidence"], bool) or not 0 <= value["confidence"] <= 1:
        raise ValueError("confidence must be numeric in [0, 1]")
    evidence = value["evidence"]
    if not isinstance(evidence, list) or not 1 <= len(evidence) <= 10:
        raise ValueError("evidence must contain 1..10 items")
    for index, item in enumerate(evidence):
        if not isinstance(item, dict) or set(item) != {"claim", "source_type", "reference"}:
            raise ValueError(f"invalid evidence[{index}]")
        require_string(item["claim"], f"evidence[{index}].claim", maximum=500)
        if item["source_type"] not in {"question", "supplied-record", "deterministic-calculation", "public-guidance", "unknown"}:
            raise ValueError(f"invalid evidence[{index}].source_type")
        require_string(item["reference"], f"evidence[{index}].reference", maximum=300)
    counter = value["counterhypothesis"]
    if not isinstance(counter, dict) or set(counter) != {"statement", "evidence_that_would_support"}:
        raise ValueError("invalid counterhypothesis")
    require_string(counter["statement"], "counterhypothesis.statement", maximum=600)
    require_string_list(counter["evidence_that_would_support"], "counterhypothesis.evidence_that_would_support", minimum=1, maximum=5, item_maximum=300)
    flags = value["safety_flags"]
    if not isinstance(flags, list) or len(flags) > 8:
        raise ValueError("safety_flags must contain at most 8 items")
    seen = set()
    for index, flag in enumerate(flags):
        required = {"flag_id", "severity", "issue", "evidence", "status"}
        if not isinstance(flag, dict) or set(flag) != required:
            raise ValueError(f"invalid safety_flags[{index}]")
        flag_id = require_string(flag["flag_id"], f"safety_flags[{index}].flag_id", maximum=64)
        if flag_id in seen or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789-" for ch in flag_id):
            raise ValueError("safety flag IDs must be unique lowercase slugs")
        seen.add(flag_id)
        if flag["severity"] not in {"critical", "major", "quality", "unresolved"}:
            raise ValueError("invalid safety severity")
        if flag["status"] not in {"open", "resolved"}:
            raise ValueError("invalid safety status")
        require_string(flag["issue"], "safety issue", maximum=500)
        require_string(flag["evidence"], "safety evidence", maximum=500)
    require_string(value["created_at"], "created_at", maximum=80)


def record_result(qdir_raw: str | Path, subtask_id: str, value: dict[str, Any]) -> dict[str, Any]:
    qdir, manifest = load_question(qdir_raw)
    record = _subtask(manifest, subtask_id)
    validate_result(value, question_id=manifest["question_id"], subtask_id=subtask_id, role=record["role"])
    path = qdir / "subtasks" / subtask_id / "result.json"
    write_json(path, value)
    record.update({"status": value["status"], "result_sha256": sha256_file(path)})
    statuses = {row["status"] for row in manifest["subtasks"]}
    if "blocked" in statuses:
        state = "blocked"
    elif statuses == {"complete"}:
        state = "ready_for_synthesis"
    else:
        state = "collecting"
    manifest.update({"state": state, "updated_at": now()})
    write_json(qdir / "manifest.json", manifest)
    return value


def verified_results(qdir: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    values = []
    for record in manifest["subtasks"]:
        if record["status"] != "complete" or not record["result_sha256"]:
            raise ValueError(f"subtask is not complete: {record['id']}")
        assignment = qdir / "subtasks" / record["id"] / "assignment.json"
        result_path = qdir / "subtasks" / record["id"] / "result.json"
        if sha256_file(assignment) != record["assignment_sha256"]:
            raise ValueError(f"assignment hash mismatch: {record['id']}")
        if not result_path.is_file() or result_path.is_symlink() or sha256_file(result_path) != record["result_sha256"]:
            raise ValueError(f"result hash mismatch: {record['id']}")
        value = load_json(result_path)
        validate_result(value, question_id=manifest["question_id"], subtask_id=record["id"], role=record["role"])
        values.append(value)
    return values


def validate_decision(value: dict[str, Any], *, question_id: str, results: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    if set(value) != DECISION_KEYS:
        raise ValueError(f"decision keys mismatch: missing={sorted(DECISION_KEYS-set(value))}, extra={sorted(set(value)-DECISION_KEYS)}")
    if value["schema_version"] != 1 or value["question_id"] != question_id:
        raise ValueError("decision question identity mismatch")
    require_string(value["summary"], "decision.summary", maximum=1600)
    require_string_list(value["rationale"], "decision.rationale", minimum=1, maximum=8)
    require_string_list(value["evidence_refs"], "decision.evidence_refs", minimum=1, maximum=16, item_maximum=300)
    require_string_list(value["assumptions"], "decision.assumptions", maximum=8)
    require_string_list(value["final_requirements"], "decision.final_requirements", minimum=1, maximum=12)
    if not isinstance(value["confidence"], (int, float)) or isinstance(value["confidence"], bool) or not 0 <= value["confidence"] <= 1:
        raise ValueError("decision confidence must be numeric in [0, 1]")
    if not isinstance(value["approved_for_delivery"], bool):
        raise ValueError("approved_for_delivery must be boolean")
    require_string(value["created_at"], "decision.created_at", maximum=80)
    counter = value["counterhypothesis"]
    if not isinstance(counter, dict) or set(counter) != {"statement", "evidence_that_would_support"}:
        raise ValueError("invalid decision counterhypothesis")
    require_string(counter["statement"], "decision.counterhypothesis.statement", maximum=600)
    require_string_list(counter["evidence_that_would_support"], "decision.counterhypothesis.evidence_that_would_support", minimum=1, maximum=6)

    declared_conflicts = list(dict.fromkeys(conflict for result in results for conflict in result["conflicts"]))
    resolutions = value["conflict_resolutions"]
    if not isinstance(resolutions, list) or len(resolutions) > 12:
        raise ValueError("conflict_resolutions must be a bounded array")
    resolved_conflicts = set()
    for index, item in enumerate(resolutions):
        if not isinstance(item, dict) or set(item) != {"conflict", "resolution", "evidence_refs"}:
            raise ValueError(f"invalid conflict_resolutions[{index}]")
        resolved_conflicts.add(require_string(item["conflict"], "conflict", maximum=500))
        require_string(item["resolution"], "resolution", maximum=800)
        require_string_list(item["evidence_refs"], "conflict evidence_refs", minimum=1, maximum=6, item_maximum=300)
    unresolved_conflicts = [item for item in declared_conflicts if item not in resolved_conflicts]
    if unresolved_conflicts:
        raise ValueError(f"unresolved declared conflicts: {unresolved_conflicts}")

    open_flags = [flag for result in results for flag in result["safety_flags"]
                  if flag["status"] == "open" and flag["severity"] in {"critical", "unresolved"}]
    dispositions = value["safety_dispositions"]
    if not isinstance(dispositions, list) or len(dispositions) > 16:
        raise ValueError("safety_dispositions must be a bounded array")
    by_flag = {}
    for index, item in enumerate(dispositions):
        required = {"flag_id", "disposition", "rationale", "final_requirement"}
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError(f"invalid safety_dispositions[{index}]")
        flag_id = require_string(item["flag_id"], "safety disposition flag_id", maximum=64)
        if item["disposition"] not in {"addressed", "block"}:
            raise ValueError("safety disposition must be addressed or block")
        require_string(item["rationale"], "safety disposition rationale", maximum=800)
        require_string(item["final_requirement"], "safety final_requirement", maximum=600)
        if flag_id in by_flag:
            raise ValueError(f"duplicate safety disposition: {flag_id}")
        by_flag[flag_id] = item
    missing_flags = [flag["flag_id"] for flag in open_flags if flag["flag_id"] not in by_flag]
    if missing_flags:
        raise ValueError(f"unresolved critical safety flags: {missing_flags}")
    blocked = [item for item in by_flag.values() if item["disposition"] == "block"]
    if blocked and value["approved_for_delivery"]:
        raise ValueError("decision cannot approve delivery while a safety disposition blocks")
    return declared_conflicts, open_flags


def synthesize_check(qdir_raw: str | Path, decision: dict[str, Any]) -> dict[str, Any]:
    qdir, manifest = load_question(qdir_raw)
    results = verified_results(qdir, manifest)
    validate_decision(decision, question_id=manifest["question_id"], results=results)
    path = qdir / "synthesis" / "decision.json"
    write_json(path, decision)
    manifest.update({
        "decision_sha256": sha256_file(path),
        "state": "synthesized" if decision["approved_for_delivery"] else "blocked",
        "updated_at": now(),
    })
    write_json(qdir / "manifest.json", manifest)
    return decision


def deliver(qdir_raw: str | Path, final_text: str, *, target: str | Path | None = None) -> dict[str, Any]:
    qdir, manifest = load_question(qdir_raw)
    if manifest["state"] != "synthesized" or not manifest.get("decision_sha256"):
        raise ValueError("question does not have an approved synthesis decision")
    results = verified_results(qdir, manifest)
    decision_path = qdir / "synthesis" / "decision.json"
    if not decision_path.is_file() or sha256_file(decision_path) != manifest["decision_sha256"]:
        raise ValueError("synthesis decision hash mismatch")
    decision = load_json(decision_path)
    validate_decision(decision, question_id=manifest["question_id"], results=results)
    if not decision["approved_for_delivery"]:
        raise ValueError("synthesis decision does not approve delivery")
    encoded = final_text.encode("utf-8")
    if not final_text.strip() or len(encoded) > MAX_TEXT_BYTES or b"\x00" in encoded:
        raise ValueError("final reply must be non-empty UTF-8 text within size limit")
    final_path = qdir / "final.txt"
    write_text(final_path, final_text)
    if not final_path.is_file() or final_path.is_symlink() or not final_path.read_text(encoding="utf-8").strip():
        raise ValueError("final.txt delivery verification failed")
    final_hash = sha256_file(final_path)
    target_record = None
    if target is not None:
        target_path = Path(target).expanduser().resolve()
        if target_path == final_path.resolve():
            target_hash = final_hash
        else:
            write_text(target_path, final_text)
            if not target_path.is_file() or target_path.is_symlink() or not target_path.read_text(encoding="utf-8").strip():
                raise ValueError("external target delivery verification failed")
            target_hash = sha256_file(target_path)
        if target_hash != final_hash:
            raise ValueError("external target hash differs from final.txt")
        target_record = {"path": str(target_path), "sha256": target_hash}
    validation = {
        "schema_version": 1,
        "question_id": manifest["question_id"],
        "delivered": True,
        "updated_at": now(),
        "question_sha256": manifest["question_sha256"],
        "decision_sha256": manifest["decision_sha256"],
        "final_sha256": final_hash,
        "final_bytes": len(encoded),
        "target": target_record,
        "subtasks": [{
            "id": row["id"], "assignment_sha256": row["assignment_sha256"],
            "result_sha256": row["result_sha256"],
        } for row in manifest["subtasks"]],
        "checks": [
            "question hash verified", "all assignments and results hash verified",
            "conflicts resolved", "critical/unresolved safety flags addressed",
            "decision approved", "final exists", "final is non-empty", "final hash verified",
        ],
    }
    write_json(qdir / "validation.json", validation)
    manifest.update({"final_sha256": final_hash, "state": "delivered", "updated_at": now()})
    write_json(qdir / "manifest.json", manifest)
    return validation


def status(qdir_raw: str | Path) -> dict[str, Any]:
    qdir, manifest = load_question(qdir_raw)
    rows = []
    for record in manifest["subtasks"]:
        assignment = qdir / "subtasks" / record["id"] / "assignment.json"
        result = qdir / "subtasks" / record["id"] / "result.json"
        rows.append({
            **record,
            "assignment_hash_valid": assignment.is_file() and sha256_file(assignment) == record["assignment_sha256"],
            "result_present": result.is_file(),
            "result_hash_valid": bool(record["result_sha256"] and result.is_file() and sha256_file(result) == record["result_sha256"]),
        })
    return {
        "question_id": manifest["question_id"], "state": manifest["state"],
        "mode": manifest["mode"], "selected_roles": manifest["selected_roles"],
        "subtasks": rows, "decision_present": (qdir / "synthesis" / "decision.json").is_file(),
        "final_present": (qdir / "final.txt").is_file(),
        "validation": load_json(qdir / "validation.json"),
    }


def synthetic_result(question_id: str, subtask_id: str, role: str, *, conflict: str | None = None,
                     flag: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1, "question_id": question_id, "subtask_id": subtask_id,
        "role": role, "status": "complete", "summary": "Synthetic concise finding.",
        "rationale": ["The supplied evidence supports a bounded conclusion."],
        "evidence": [{"claim": "A fact was supplied.", "source_type": "question", "reference": "question.txt"}],
        "assumptions": [], "confidence": 0.7,
        "counterhypothesis": {"statement": "The interpretation may change with missing context.",
                              "evidence_that_would_support": ["A decision-changing missing fact."]},
        "recommendations": ["Keep the final claim conditional."],
        "conflicts": [conflict] if conflict else [], "safety_flags": [flag] if flag else [],
        "created_at": now(),
    }


def synthetic_decision(question_id: str, *, conflicts: list[str] | None = None,
                       flag_ids: list[str] | None = None, approved: bool = True) -> dict[str, Any]:
    return {
        "schema_version": 1, "question_id": question_id, "summary": "Synthetic synthesis.",
        "rationale": ["Results were reconciled against supplied evidence."],
        "evidence_refs": ["01-context-evidence:question.txt"], "assumptions": [],
        "confidence": 0.7,
        "counterhypothesis": {"statement": "Missing context may change the decision.",
                              "evidence_that_would_support": ["New supplied evidence."]},
        "conflict_resolutions": [{"conflict": item, "resolution": "Prefer directly supplied evidence.",
                                  "evidence_refs": ["question.txt"]} for item in (conflicts or [])],
        "safety_dispositions": [{"flag_id": item, "disposition": "addressed",
                                 "rationale": "Make the uncertainty and action explicit.",
                                 "final_requirement": "State the safety action clearly."} for item in (flag_ids or [])],
        "final_requirements": ["Answer directly and preserve uncertainty."],
        "approved_for_delivery": approved, "created_at": now(),
    }


class WorkspaceTests(unittest.TestCase):
    def test_stable_init_reuses_exact_question(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            first = init_workspace(raw, "A synthetic question")
            second = init_workspace(raw, " A synthetic question\n")
            self.assertEqual(first, second)
            self.assertTrue((first / "validation.json").is_file())

    def test_default_dispatch_is_bounded_and_relevant(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            qdir = init_workspace(raw, "Question")
            manifest = plan_question(qdir, "symptom")
            self.assertEqual(len(manifest["subtasks"]), 3)
            self.assertEqual(tuple(manifest["selected_roles"]), MODE_ROLES["symptom"])

    def test_sparse_and_artifact_dispatch_only_relevant_roles(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            sparse = init_workspace(Path(raw) / "a", "Sparse")
            artifact = init_workspace(Path(raw) / "b", "Artifact")
            self.assertEqual(plan_question(sparse, "sparse-context")["selected_roles"], ["context-evidence"])
            self.assertEqual(plan_question(artifact, "bounded-artifact")["selected_roles"], ["context-evidence", "constraints-artifact"])

    def test_irrelevant_explicit_role_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            qdir = init_workspace(raw, "Question")
            with self.assertRaisesRegex(ValueError, "not relevant"):
                plan_question(qdir, "sparse-context", roles=["quantitative-data"])

    def test_assignment_and_result_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            qdir = init_workspace(raw, "Question")
            manifest = plan_question(qdir, "sparse-context")
            row = manifest["subtasks"][0]
            assigned = assign_subtask(qdir, row["id"], "agent-one")
            self.assertEqual(assigned["assigned_to"], "agent-one")
            result = synthetic_result(manifest["question_id"], row["id"], row["role"])
            record_result(qdir, row["id"], result)
            self.assertEqual(status(qdir)["state"], "ready_for_synthesis")

    def test_result_requires_rationale_evidence_confidence_and_counterhypothesis(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            qdir = init_workspace(raw, "Question")
            manifest = plan_question(qdir, "sparse-context")
            row = manifest["subtasks"][0]
            result = synthetic_result(manifest["question_id"], row["id"], row["role"])
            for key in ("rationale", "evidence", "confidence", "counterhypothesis"):
                broken = dict(result)
                broken.pop(key)
                with self.subTest(key=key), self.assertRaises(ValueError):
                    record_result(qdir, row["id"], broken)

    def test_unresolved_conflict_blocks_synthesis(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            qdir = init_workspace(raw, "Question")
            manifest = plan_question(qdir, "sparse-context")
            row = manifest["subtasks"][0]
            record_result(qdir, row["id"], synthetic_result(manifest["question_id"], row["id"], row["role"], conflict="conflict-a"))
            with self.assertRaisesRegex(ValueError, "unresolved declared conflicts"):
                synthesize_check(qdir, synthetic_decision(manifest["question_id"]))

    def test_unresolved_critical_flag_blocks_synthesis(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            qdir = init_workspace(raw, "Question")
            manifest = plan_question(qdir, "sparse-context")
            row = manifest["subtasks"][0]
            flag = {"flag_id": "critical-one", "severity": "critical", "issue": "Potential harm.",
                    "evidence": "Uncertainty remains.", "status": "open"}
            record_result(qdir, row["id"], synthetic_result(manifest["question_id"], row["id"], row["role"], flag=flag))
            with self.assertRaisesRegex(ValueError, "unresolved critical safety flags"):
                synthesize_check(qdir, synthetic_decision(manifest["question_id"]))

    def test_delivery_is_atomic_nonempty_and_hash_verified(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            qdir = init_workspace(raw, "Question")
            manifest = plan_question(qdir, "sparse-context")
            row = manifest["subtasks"][0]
            flag = {"flag_id": "critical-one", "severity": "critical", "issue": "Potential harm.",
                    "evidence": "Uncertainty remains.", "status": "open"}
            record_result(qdir, row["id"], synthetic_result(manifest["question_id"], row["id"], row["role"], conflict="conflict-a", flag=flag))
            decision = synthetic_decision(manifest["question_id"], conflicts=["conflict-a"], flag_ids=["critical-one"])
            synthesize_check(qdir, decision)
            target = Path(raw) / "response.txt"
            validation = deliver(qdir, "Complete final reply.\n", target=target)
            self.assertTrue(validation["delivered"])
            self.assertEqual(target.read_text(), "Complete final reply.\n")
            self.assertEqual(load_json(qdir / "manifest.json")["state"], "delivered")

    def test_empty_delivery_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            qdir = init_workspace(raw, "Question")
            manifest = plan_question(qdir, "sparse-context")
            row = manifest["subtasks"][0]
            record_result(qdir, row["id"], synthetic_result(manifest["question_id"], row["id"], row["role"]))
            synthesize_check(qdir, synthetic_decision(manifest["question_id"]))
            with self.assertRaisesRegex(ValueError, "non-empty"):
                deliver(qdir, "  \n")

    def test_question_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            qdir = init_workspace(raw, "Question")
            write_text(qdir / "question.txt", "Tampered\n")
            with self.assertRaisesRegex(ValueError, "hash"):
                status(qdir)


def run_selftest() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(WorkspaceTests)
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--workspace", required=True, type=Path)
    source = init.add_mutually_exclusive_group(required=True)
    source.add_argument("--question")
    source.add_argument("--question-file", type=Path)
    init.add_argument("--max-subtasks", type=int, default=3)
    plan = commands.add_parser("plan")
    plan.add_argument("--question-dir", required=True, type=Path)
    plan.add_argument("--mode", required=True, choices=MODES)
    plan.add_argument("--role", action="append", default=[])
    plan.add_argument("--max-subtasks", type=int)
    assign = commands.add_parser("assign")
    assign.add_argument("--question-dir", required=True, type=Path)
    assign.add_argument("--subtask", required=True)
    assign.add_argument("--agent", required=True)
    record = commands.add_parser("record")
    record.add_argument("--question-dir", required=True, type=Path)
    record.add_argument("--subtask", required=True)
    record.add_argument("--input", required=True, type=Path)
    stat = commands.add_parser("status")
    stat.add_argument("--question-dir", required=True, type=Path)
    synth = commands.add_parser("synthesize-check")
    synth.add_argument("--question-dir", required=True, type=Path)
    synth.add_argument("--input", required=True, type=Path)
    delivery = commands.add_parser("deliver")
    delivery.add_argument("--question-dir", required=True, type=Path)
    delivery.add_argument("--input", required=True, type=Path)
    delivery.add_argument("--target", type=Path)
    commands.add_parser("selftest")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "selftest":
            return run_selftest()
        if args.command == "init":
            question = args.question if args.question is not None else args.question_file.read_text(encoding="utf-8")
            output: Any = {"question_dir": str(init_workspace(args.workspace, question, max_subtasks=args.max_subtasks))}
        elif args.command == "plan":
            output = plan_question(args.question_dir, args.mode, roles=args.role, max_subtasks=args.max_subtasks)
        elif args.command == "assign":
            output = assign_subtask(args.question_dir, args.subtask, args.agent)
        elif args.command == "record":
            output = record_result(args.question_dir, args.subtask, load_json(args.input))
        elif args.command == "status":
            output = status(args.question_dir)
        elif args.command == "synthesize-check":
            output = synthesize_check(args.question_dir, load_json(args.input))
        elif args.command == "deliver":
            output = deliver(args.question_dir, args.input.read_text(encoding="utf-8"), target=args.target)
        else:  # pragma: no cover
            raise AssertionError(args.command)
    except (OSError, UnicodeError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2
    print(json.dumps({"ok": True, "result": output}, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
