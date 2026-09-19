# Finance improvement loop: handoff

## Goal and repository

Build a first automated self-improvement loop for quantitative-finance tasks,
run a small real experiment, and measure whether the generated skill helps.
The learner is frozen: only its skill instructions and optional offline tools
change. The user authorized the small paid evaluation and pushing to GitHub.

- Workspace: `/home/rachelyin/hackathon/self-improve`
- Remote: `https://github.com/richard7ao/self_improving_agent.git`
- Branch: `main`
- First-version implementation pushed as `ae7be07`.

## Architecture and changes

We extended the existing `src/skilltrainbench/optimize.py`, rather than creating
a second orchestration system. Its reviewer and worker are separate model calls
with different system prompts; Python controls the loop. They currently use the
configured Runware learner model by default. These are application-level agent
roles, not Codex subagents or additional conversations.

Flow: evaluate incumbent -> reviewer analyzes tune failures -> worker generates
one or more complete candidate skill folders -> static checks -> candidate tune
evaluation -> best candidate validation -> promote or retain incumbent.

The important fixes in this version:

1. Finance attempt records have an empty `answer` field. Added
   `_trajectory_evidence()` so the reviewer can see actual learner actions,
   tool arguments/results, and the final visible response from Harbor's
   `agent/trajectory.json`.
2. Evidence uses an explicit field allowlist, bounded excerpts, and path
   containment checks. It excludes system/reasoning fields and does not read
   verifier files. `_observations()` filters out tasks outside the tune split.
3. Added `_should_promote()`: a candidate must improve the weighted aggregate
   score by more than `min_improvement` AND strictly improve validation.
   Validation ties/regressions keep the incumbent. Single-task runs have no
   validation gate. This rule applies to every domain using this optimizer.
4. Round records now include previous aggregate/validation scores and a decision
   reason. Existing candidate isolation, static validation, and promotion remain.
5. Added four regression tests; all 15 tests passed. Updated the README,
   methodology, teammate guide, and `docs/FINANCE_LOOP.md`.

## Active experiment: status snapshot

As of this handoff's creation on 2026-09-19, the original conversation is still
monitoring this run. Do not launch a duplicate or change its skill while active.
Read `/tmp/qf-loop-v1.log` and the run artifacts for newer status.

- Output: `runs/qf-loop-v1/`
- Skill: `submissions/octuple/qf/` (initially a committed placeholder)
- One round, one candidate, seed 42, concurrency 1, candidate parallelism 1.
- Tune: `13f-amendment-aware-crowding`, `asian-option-levy-curran`.
- Validation: `alpha-hedge-strategy`.
- Incumbent tune results: 0/2; recorded learner cost $0.0480403.
- Incumbent validation is still running. No candidate result or improvement
  claim exists yet. The initial checkpoint is written after validation completes.

The launched command was:

```bash
sg docker -c 'DOCKER_CONFIG=/tmp/stbench-docker-tools/config PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -u -m skilltrainbench.cli optimize --domain qf --skill submissions/octuple/qf --out runs/qf-loop-v1 --iterations 1 --candidates 1 --tasks 13f-amendment-aware-crowding,alpha-hedge-strategy,asian-option-levy-curran --limit 3 --validation-fraction 0.34 --concurrency 1 --candidate-parallelism 1 --seed 42 --keep-candidates' > /tmp/qf-loop-v1.log 2>&1
```

Docker and Runware access work with this local setup. `uv` is not on PATH;
use `.venv/bin/python`. The optional OpenAI key is absent, and other domains'
datasets are incomplete; neither blocks this finance run. Do not modify
`hackathon.toml` or interfere with the separate full finance baseline run.

## Remaining work and limits

Finish the six expected learner attempts, inspect the generated skill/tools,
report paired per-task results and promotion decision, sum recorded evaluation
costs, and save a concise experiment report. Push any final report and any
legitimately promoted skill. Do not force promotion if the candidate fails.

This is a three-task training smoke test against the current skill, not a
baseline/placebo leaderboard comparison. No broad improvement is established.
Generated Python receives syntax/static checks; its functional correctness still
needs inspection/testing. Reviewer/worker calls currently lack a separate cost
ledger, so reported evaluation costs exclude them. Run data and credentials
remain Git-ignored; another machine will need the run artifacts separately.
