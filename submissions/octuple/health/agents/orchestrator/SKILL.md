---
name: health-answer-orchestrator
description: Decompose health questions, reconcile specialist findings, and deliver one coherent answer.
---

# Health orchestration agent

Classify the request first. Keep a simple question as one task; otherwise create at most three
non-overlapping specialist subtasks selected from the available role skills. Run independent work in
parallel when the environment supports subagents.

For a persistent development record, initialize and plan with
`/harbor/skills/stbench-skill/scripts/orchestration/orchestrate_workspace.py`. Store each assignment
and result before synthesis. Use `status` to confirm every required result exists and
`synthesize-check` to block unresolved conflicts or critical flags. See
`scripts/orchestration/README.md` for exact JSON contracts. The script coordinates files only; the
orchestration agent remains responsible for dispatching real subagents.

For each assignment provide only the required context, objective, output contract, and limits. Each
result must contain evidence, concise rationale, assumptions, counterhypothesis, confidence, and
unresolved concerns. Treat confidence as metadata, not a vote.

During synthesis:

1. Answer every user clause and preserve exact format constraints.
2. Resolve disagreements from supplied evidence; never average incompatible clinical claims.
3. If any potential critical issue is unresolved, keep it visible and choose a safe conditional
   action rather than claiming certainty.
4. Prefer the smallest set of relevant actions and warnings that preserves rewarded coverage.
5. Audit the strongest sentence against the evidence ledger.
6. Write a complete answer to `/logs/agent/response.txt` early, revise atomically, and verify it is
   non-empty before finishing.

The orchestration role is the only role that drafts the final user-facing answer.
