# Agent instructions

This repository optimizes read-only skill folders for a fixed benchmark learner. Work on
the domain the user assigns; do not modify `hackathon.toml` to improve a score because the
organizers use their own pinned copy.

## Start every session

1. Run `git status --short --branch` and preserve unrelated work.
2. Run `uv run stbench doctor` to check Docker, API authentication, and dataset status.
3. Read `README.md`, `richard_metholody.md`, and `docs/TEAMMATE_GUIDE.md` before changing
   optimization logic or a submission.
4. Inspect the target skill and its latest relevant run artifacts before editing it.

## Submission rules

- Work only from public training tasks. Never put task text, patient details, grading
  rubrics, reference answers, or task-to-answer mappings into a submission.
- Skill scripts must run offline without credentials, external APIs, or network access.
- Keep essential decisions in `SKILL.md`; place conditional detail in `references/` and
  repeatable deterministic work in `scripts/`.
- Do not add a supporting file unless `SKILL.md` tells the learner when and how to use it.
- Run `uv run stbench check-skill submissions/<team>/<domain>` after every material edit.

## Evaluation discipline

- Use unique output directories under ignored `runs/`; never overwrite evidence.
- Start with a cheap smoke test, then confirm promising changes on more or fresh tasks.
- Compare candidates on the same task list. Do not promote ties.
- `stbench optimize` may replace the live skill. Use a clean Git state or commit first so
  any promotion is recoverable.
- Benchmark evaluation spends Runware credits. `stbench doctor --live-api` also makes tiny
  paid calls. Do not launch either when the user requested only read-only inspection.

## Verification and handoff

- Run the relevant unit tests and `git diff --check` before committing.
- Do not commit `.env`, `dataset/`, or `runs/`.
- Make focused commits. When the user has authorized pushing, push each stable tested batch
  and report its commit hash.
- Summarize the exact task set, score, cost, promoted skill, and remaining uncertainty in
  the handoff. A local training score is not a held-out leaderboard guarantee.
