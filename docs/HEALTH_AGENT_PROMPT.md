# Health agent implementation prompt

Copy the prompt below into the Health agent's session.

```text
You own the Health submission and the Health-specific optimization/evaluation work needed
to implement the recommendations in:

  health-skill-agent-research.md

Your objective is still competition performance: maximize the frozen learner's private
Health score, especially `skill_rate - placebo_rate`, without leaking benchmark content or
changing the frozen competition contract. Treat the research report as a design proposal,
not as proof that every recommendation is current, feasible, or score-improving. Verify it
against present `main`, implement it in measured stages, and preserve an easy rollback path.

Scope:

- You may edit `submissions/octuple/health/`, Health-relevant shared harness code under
  `src/skilltrainbench/`, corresponding tests, and Health documentation.
- Do not edit `submissions/octuple/hle/`, `submissions/octuple/qf/`,
  `submissions/octuple/tau3/`, `hackathon.toml`, `.env`, or datasets.
- Do not alter generic behavior for other domains unless it is necessary and fully covered
  by regression tests. Prefer Health-gated behavior when appropriate.
- `runs/` is ignored experimental evidence, never a commit target.

Start exactly as follows:

1. Run `git status --short --branch`; preserve every unrelated modification and untracked
   file.
2. Run `uv run stbench doctor` without `--live-api`.
3. Read `AGENTS.md`, `README.md`, `richard_metholody.md`,
   `docs/TEAMMATE_GUIDE.md`, the complete `health-skill-agent-research.md`, and the current
   `submissions/octuple/health/SKILL.md` plus every file it routes to.
4. Inspect the latest Health run artifacts and active `stbench`/Harbor processes. Do not
   launch another paid run while one is active or reuse an output directory.
5. Run the offline unit tests and `uv run stbench check-skill submissions/octuple/health`
   before modifying anything.

Current evidence to recheck, not blindly assume:

- The committed live Health skill is the compact round-three survivor. Its historical
  `0.4165` number is a four-task skill-only weighted aggregate, not an official score and
  not a placebo-adjusted confirmation.
- A separate experimental snapshot at `runs/subagent-health/frozen-health-v1` is much
  larger and tool-heavy. At prompt creation, three valid completed placebo/skill pairs had
  placebo mean about `0.4948`, skill mean about `-0.1307`, and provisional net delta about
  `-0.6254`; another pair had network failures and the run was incomplete. Recompute from
  final artifacts. Do not promote this package unless clean completed evidence reverses the
  conclusion.
- Round-five candidate B had a three-task raw skill mean near `0.3851`, but no observed
  validation result. This is not enough for promotion.
- Twelve unseen public Health task IDs are reserved in
  `docs/evaluation_sets/health-confirmation-20260919.txt`. Do not inspect their task text,
  rubrics, answers, or trajectories before one finalist is frozen. Do not spend them on
  iterative tuning. Twelve tasks provide a useful directional confirmation, not a strong
  small-effect guarantee.

Repository coordination:

- Other agents are active. Never use `git add .`, `git add -A`, broad pathspecs, reset,
  checkout-overwrite, or destructive cleanup.
- Before each commit, list the intended files, then stage those exact paths only. Re-run
  `git diff --cached --check` and inspect `git diff --cached` before committing.
- Make focused commits. Push only if the user has authorized pushing, and report each hash.
- If a concurrent edit overlaps your target, stop and reconcile rather than overwriting it.

Implementation order

Phase 0 — audit and freeze the incumbent

- Hash and copy the current live Health package to an immutable run-local candidate before
  any experiment. Record the Git SHA, skill hash, config hash, dataset revision, exact task
  IDs, arms, and output directory.
- Build an exposure inventory from existing Health `attempts.jsonl`, `eval_result.json`,
  optimization state, and Harbor configs. Mark tasks that have influenced review or skill
  edits as adaptive/search data. Do not relabel an exposed task as holdout because its seed
  changed.
- Compare the research report against current code and produce a short checklist of
  `already implemented`, `partially implemented`, `missing`, and `deferred`. The report
  audited an older commit, so current code wins where evidence differs.

Phase 1 — implement the minimum trustworthy promotion path before another automatic
promotion

Prioritize the P0 mechanisms that directly prevent false promotion. Keep legacy optimizer
artifacts readable and label legacy results as exploratory/unconfirmed.

1. Matched evidence and raw score correctness
   - Compare incumbent and challenger only on the intersection of valid, identical task
     IDs under the same frozen contract.
   - Preserve negative Health task rewards and full precision for decisions.
   - If repeats are present, average registered repeats within task before aggregating; do
     not sum repeat rows.
   - Treat infrastructure/grader invalidation separately from a scored bad answer.
   - Reject or mark inconclusive any comparison with arm-dependent missingness that can
     change the decision.

2. Fresh paired confirmation
   - Never compare a freshly measured challenger against a stale incumbent score for final
     promotion.
   - Freeze exactly one finalist hash, then evaluate finalist and incumbent on the same
     untouched confirmation tasks in the same time block. Include the official placebo in
     the final confirmation. Baseline is diagnostic and may be omitted when cost requires.
   - Selection/tune results must not be averaged into the final confirmation estimate.

3. Promotion statistics
   - Add a deterministic, separately tested decision function using task-level paired
     differences. Preserve the research defaults as configurable protocol values:
     practical margin `delta = 0.02` and one-sided `alpha = 0.025`.
   - Require a lower confidence bound for challenger-minus-incumbent above the registered
     margin and a lower bound for challenger-minus-placebo above zero when the registered
     task count supports the method.
   - With too few tasks, return `inconclusive`; do not quietly fall back to any-positive-
     point-estimate promotion. Search can still rank exploratory candidates.
   - Add deterministic bootstrap sensitivity over task/family clusters where metadata
     supports it. If the registered primary and sensitivity analyses change the decision,
     return `inconclusive`.
   - Test negative scores, ties, rounding boundaries, heavy tails, repeats, missing arms,
     mismatched task sets, and validation regressions. Add null simulations that estimate
     the false-promotion rate of the complete rule.

4. Artifact identity and recovery
   - Persist candidate and parent content hashes plus config/dataset/task-manifest hashes.
     Refuse incompatible resume.
   - Ensure a crash cannot make an unrecorded package the authoritative champion. If the
     full registry proposed by the report is too large for one batch, first implement a
     minimal immutable candidate registry and transactional/recoverable promotion pointer,
     with kill/failure tests.
   - A completed experiment with missing state must pause; it must never infer promotion
     from a mutable submission directory.

5. Executable and leakage controls
   - Until isolated tool qualification exists, automatically generated executable changes
     are review-required, not auto-promotable. An unchanged manually reviewed helper may be
     allowlisted by exact hash.
   - Retain exact-overlap detection and add tested normalization/fuzzy/task-ID/lookup-table
     signals without claiming they prove absence of leakage.
   - Never pass validation/confirmation conversations, patient facts, rubric wording,
     reference answers, or detailed failure hints to reviewer/generator prompts.

Phase 2 — improve the actual Health skill on search data

- Start from the compact live skill, not the failed large package.
- Diagnose no more than three general failure mechanisms from search-only evidence. For
  each mechanism record:
  - evidence IDs and observed behavior;
  - causal hypothesis and strongest counterhypothesis;
  - exact score, token, cost, and confidence calculation;
  - expected benefit and affected task types;
  - likely regression and a falsifying test;
  - confidence from 0 to 1 with its evidence basis.
- Generate at most three materially distinct candidates, normally one small mechanism edit
  each. Always include or periodically test a compression/ablation candidate because the
  current evidence suggests instruction and tool overhead can be harmful.
- Prefer concise always-visible rules. Add a reference only for genuinely conditional
  knowledge. Add a script only for repeatable deterministic work that the model has shown
  it cannot reliably perform in text.
- Every supporting file must be explicitly routed from `SKILL.md`. New scripts require a
  declared input/output contract, offline operation, independent tests, boundary cases,
  resource limits, and a with/without-tool ablation before promotion.
- Do not turn uncertain clinical judgment into a deterministic tool. Calculations suitable
  for tools include literal format/count checks and validated numeric transforms. Low-
  confidence clinical reasoning must trigger a narrower claim or review, not fake
  precision.
- Score candidates on identical task batches. Use shared 16-task search batches when budget
  permits; eliminate obviously weak candidates, retain near-ties, and test one frozen
  finalist on untouched confirmation data.

Health safety gate

- Add structured safety events with `severity`, `failure_class`, response evidence span,
  supplied-context evidence, disposition, and uncertainty. At minimum distinguish critical,
  major, quality, and unresolved.
- Confirmed critical harm is a non-compensatory veto. Unresolved potential critical harm
  blocks promotion pending adjudication; average reward cannot cancel it.
- Track both under-triage and needless emergency escalation. Do not improve apparent safety
  by adding emergency boilerplate to low-risk or bounded-output tasks.
- Track medication changes, dangerous reassurance, unsupported diagnosis, fabricated
  findings, pediatrics/pregnancy/complex-patient context when actually present, continuity,
  and exact requested artifacts. Do not encode patient-specific examples in the skill.
- A model critic may flag cases, but do not present it as clinical certification. Where no
  qualified adjudicator exists, report the unresolved limitation.

Reasoning, confidence, and calculations

- Do not request or store private chain-of-thought. Require concise decision rationale,
  evidence, assumptions, counterhypothesis, calculations, and calibrated confidence.
- Independently recompute every numeric decision in deterministic code. Never trust
  arithmetic merely because a reviewer wrote it.
- During each review cycle, convert a low-confidence repeatable calculation into a bounded
  offline development tool or test when appropriate. Do not create scripts for one-off
  arithmetic, unsupported formulas, or clinical judgment.
- Store reviewer confidence as metadata only. It is not a posterior probability and cannot
  authorize promotion.

Paid-evaluation discipline

- Before every paid call, state the hypothesis, exact task IDs/count, arms, expected learner
  episodes, likely grader fan-out, maximum concurrency, expected cost or why cost is unknown,
  stopping rule, and which evidence can influence future edits.
- Start with an offline or cheap search smoke. Do not use the reserved confirmation manifest
  until one candidate hash is frozen.
- Never overwrite a run. Do not run concurrent Health campaigns against shared Docker/API
  capacity unless explicitly coordinated.
- After each run report raw `skill_rate`, `placebo_rate`, `net_delta`, paired task deltas,
  invalidated/delivery failures, interval or why unavailable, tokens, cost, and wall time.
  A tiny skill-only mean is candidate-screening evidence, not a competition score.
- Do not promote ties, regressions, unpaired results, delivery-failed candidates, or results
  whose optimistic missing-data treatment changes the decision.

Required first deliverable

Do not begin with the full 15–23 day architecture. Produce and implement the smallest safe
vertical slice that makes one Health promotion decision materially more trustworthy:

1. current-code versus research gap checklist;
2. matched task-level comparison with repeat-safe raw scoring;
3. deterministic promotion decision with practical margin and inconclusive state;
4. provenance hashes sufficient to reject incompatible evidence;
5. focused unit/statistical tests;
6. no paid evaluation until those checks pass.

Then propose the next smallest score-focused experiment. If the active first-principles run
finishes with the provisional negative direction intact, formally reject that candidate and
use its general failure mechanism—excess process/tool overhead—as search evidence without
copying task details.

Before every commit:

  uv run python -m unittest discover -s tests -q
  uv run stbench check-skill submissions/octuple/health
  git diff --check -- <exact files you changed>
  git status --short --branch

Stage only the exact intended files. In the final handoff, report commit hashes, files
changed, tests, exact task sets, arms, raw and placebo-adjusted scores, cost, whether anything
was promoted, and the largest remaining uncertainty.
```
