# Bounded per-question orchestration

This is a development-time filesystem protocol for decomposing one difficult Health question into
at most three independent, auditable subtasks. The Python script performs no model or network calls.
It creates assignments, validates returned JSON, checks synthesis preconditions, and verifies final
delivery.

## Execution boundary

The root Codex session may use collaboration subagents to complete assignment files during skill
development. Each subagent reads `question.txt` plus its own `assignment.json`, then returns a
small `result.json`. The root remains responsible for conflict resolution, synthesis, and delivery.

The scored learner cannot add model calls or spawn this development team. Inside a benchmark task,
it remains one frozen learner with its fixed turn budget. Therefore this protocol must not be
described as a runtime ensemble advantage. Reusable ideas may later be compressed into an offline
checklist or deterministic script, but model-generated specialist results cannot be shipped or
called during scoring.

## Specialist roles

- `context-evidence`: separates reported, explicitly denied, inferred, and unassessed information;
  identifies missing decision-changing evidence and conversation-continuity risks.
- `clinical-options-uncertainty`: compares reasonable action pathways, evidence limits,
  contraindication/monitoring questions, and the strongest counterhypothesis without prescribing.
- `safety-urgency`: checks under-triage and needless escalation, observable warning signs, urgency,
  vulnerable populations, and unresolved critical risk.
- `constraints-artifact`: checks audience, requested artifact, inclusions/exclusions, formatting,
  section order, length, and delivery contract.
- `quantitative-data`: verifies arithmetic, units, chronology, denominators, trends, and uncertainty;
  it does not interpret clinical meaning or select a dose.

`plan` dispatches only roles relevant to the selected mode and caps selection at three by default.
Sparse context gets one role; bounded artifacts get context plus constraint review; symptom and
treatment decisions get context, clinical-options, and safety; quantitative mode adds data review.
Use `--role` only to select a subset of the roles permitted for that mode.

## Stable workspace

```text
WORKSPACE/questions/q-<question-hash>/
├── question.txt
├── manifest.json
├── subtasks/
│   └── 01-context-evidence/
│       ├── assignment.json
│       └── result.json
├── synthesis/
│   └── decision.json
├── final.txt
└── validation.json
```

The normalized question hash determines the folder name, so repeated `init` calls reuse the same
question rather than silently creating variants. JSON is written atomically. The manifest stores
hashes and workflow state; tampering with `question.txt` blocks later commands.

## Workflow

Initialize and plan:

```bash
python orchestrate_workspace.py init --workspace WORKSPACE --question-file question.txt
python orchestrate_workspace.py plan --question-dir WORKSPACE/questions/q-... --mode symptom
python orchestrate_workspace.py status --question-dir WORKSPACE/questions/q-...
```

Assign a development subagent:

```bash
python orchestrate_workspace.py assign --question-dir QUESTION_DIR \
  --subtask 01-context-evidence --agent codex-context-1
```

Record a result after the subagent produces schema-valid JSON:

```bash
python orchestrate_workspace.py record --question-dir QUESTION_DIR \
  --subtask 01-context-evidence --input /tmp/context-result.json
```

Every completed result must contain concise rationale, evidence references, assumptions, numeric
confidence, a counterhypothesis, recommendations, declared conflicts, and structured safety flags.
The script enforces size/count bounds but does not pretend to judge clinical truth.

After all results are recorded, the root writes a decision JSON and checks it:

```bash
python orchestrate_workspace.py synthesize-check --question-dir QUESTION_DIR \
  --input /tmp/decision.json
```

All declared conflicts require explicit resolution. Every open `critical` or `unresolved` safety
flag requires an addressed disposition tied to final-response requirements; a `block` disposition
or an unaddressed flag prevents approval. Semantic conflicts that specialists failed to declare
remain a human/root-agent review responsibility.

Deliver only an approved, non-empty final reply:

```bash
python orchestrate_workspace.py deliver --question-dir QUESTION_DIR \
  --input /tmp/final.txt
```

`deliver` atomically writes and re-reads `final.txt`, checks its hash/size/non-whitespace content,
verifies the decision and every recorded subtask hash, then writes `validation.json`. An optional
`--target /logs/agent/response.txt` performs the same atomic non-empty verification at an explicit
external delivery path. It never creates a second model call.

Run synthetic tests:

```bash
python orchestrate_workspace.py selftest
```

## Safety and scope

- Maximum three subtasks by default; raising the cap requires an explicit flag and remains bounded
  to the five registered roles.
- No network imports, subprocess calls, provider credentials, prompts, or model clients.
- No automatic diagnosis, treatment selection, triage decision, or clinical conflict resolution.
- Confidence is metadata, not a probability of correctness and never overrides an open safety flag.
- Evidence references should point to the question, supplied records, deterministic calculations,
  or named public guidance—not copy hidden rubric or answer material.
- Question workspaces belong under ignored `runs/`; never submit their patient/task content inside a
  skill.
