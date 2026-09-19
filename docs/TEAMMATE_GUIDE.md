# Teammate guide

This guide is the quickest safe path for a teammate—or a new coding-agent session—to work
on any Octuple submission without rediscovering the harness.

## One-minute orientation

The fixed learner receives one domain skill folder as read-only context. The benchmark
runs the same tasks with controlled arms and reports whether the skill improves the learner.
Only the skill is a submission; source changes to the harness are development tooling.

| Domain | Submission | Score |
|---|---|---|
| Quantitative finance | `submissions/octuple/qf` | tests pass/fail |
| Health | `submissions/octuple/health` | mean rubric fraction, 0–1 |
| Customer service | `submissions/octuple/tau3` | assertions pass/fail |
| Expert questions | `submissions/octuple/hle` | answer pass/fail |

Read `AGENTS.md` first. It contains the repository safety and validation rules that every
agent session should follow.

## Environment check

```bash
uv sync
uv run stbench doctor
```

For a real, minimal inference check (this spends a small amount of provider credit):

```bash
uv run stbench doctor --live-api
```

Interpretation:

- `runware_auth` proves the key and configured learner model are visible.
- `runware_inference` proves there are enough credits for learner calls.
- `openai_auth` / `openai_inference` check the optional reviewer/changer provider.
- `huggingface` reports whether every remote dataset file exists locally.
- `datasets` reports usable task counts by domain.

Never paste `.env` values into prompts, issues, logs, or commits.

## Inspect a domain

```bash
uv run stbench tasks --domain health | sed -n '1,20p'
uv run stbench check-skill submissions/octuple/health
```

Training task files may be inspected to understand general failure classes. Do not copy
their wording, rubrics, reference answers, or patient-specific facts into a skill.

## Manual evaluation loop

Use manual evaluation when testing one deliberate change:

```bash
uv run stbench eval \
  --domain health \
  --skill submissions/octuple/health \
  --arms baseline,placebo,skill \
  --limit 4 \
  --concurrency 4 \
  --out runs/health-manual-001
```

Inspect:

```bash
uv run harbor view runs/health-manual-001/harbor-jobs
uv run stbench compare runs/health-manual-001
```

Use `--tasks name1,name2` to make two candidates run on exactly the same examples.

## Automated candidate loop

The optimizer generates complete alternative skill folders, validates them, evaluates
candidates concurrently, validates the strongest challenger, and atomically promotes it
only when its aggregate score and reserved validation score both improve.

Fast health smoke run:

```bash
uv run stbench optimize \
  --domain health \
  --skill submissions/octuple/health \
  --out runs/health-opt-001 \
  --iterations 1 \
  --candidates 3 \
  --limit 4 \
  --concurrency 4 \
  --candidate-parallelism 3 \
  --seed 42
```

Use OpenAI for review and candidate generation while preserving Runware as the frozen
benchmark learner:

```bash
uv run stbench optimize \
  --domain health \
  --skill submissions/octuple/health \
  --out runs/health-opt-openai-001 \
  --optimizer-base-url https://api.openai.com \
  --optimizer-key-env OPENAI_API_KEY \
  --optimizer-model gpt-4.1-mini \
  --iterations 1 --candidates 3 --limit 4 --seed 42
```

The benchmark portion still requires Runware credits because the learner is pinned by
`hackathon.toml`.

## Speed controls

- Candidate generation is concurrent.
- Candidate evaluation is concurrent and shares the total `--concurrency` budget.
- Increase `--candidate-parallelism` only when the machine has spare memory and Docker CPU.
- Use 4 tasks for plumbing, 8–16 for development, and a larger fresh selection for final
  confirmation.
- More candidates increase search breadth; more tasks make the winner more trustworthy.
  Prefer task coverage once candidates become near-ties.

## Compare experiments

```bash
uv run stbench compare \
  runs/health-opt-001 \
  runs/health-opt-002 \
  runs/health-confirmation
```

Add `--json` when another agent or script needs to consume the result.

## Working on another domain

The same commands accept `qf`, `tau3`, or `hle`. Start by replacing only the selected
domain's placeholder `SKILL.md`. Domain-specific reminders:

- **qf:** deterministic scripts are valuable; run calculations and validate produced files.
- **tau3:** focus on policy adherence, correct tool selection, state tracking, and concise
  customer communication. Never invent tool results.
- **hle:** focus on problem decomposition, answer verification, and the exact final-answer
  format. Avoid bloating context with broad encyclopedic material.
- **health:** distinguish bounded documentation/coding tasks from advice; do not inject
  unsolicited triage language into a tightly formatted request.

The optimizer reads task instructions and bounded learner trajectory excerpts for finance.
It excludes verifier files and validation attempts from reviewer input. See
`docs/FINANCE_LOOP.md` for the first finance experiment and its limitations.

## Git handoff

Before handing work to another person or agent:

```bash
uv run python -m unittest discover -s tests -q
uv run stbench check-skill submissions/octuple/<domain>
git diff --check
git status --short --branch
```

Commit source and submission changes, but never add `.env`, `dataset/`, or `runs/`. Record
the pushed commit hash and the exact run directory that supports any claimed improvement.
