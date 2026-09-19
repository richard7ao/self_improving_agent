# QF development — 2026-09-19

The current objective is to improve the frozen QF learner's pass rate over the
placebo arm on public training tasks. The learner, benchmark scoring, and
`hackathon.toml` are unchanged.

## Evaluation readiness

The starting checkout was `96b8d96`, which already fixes CSV NaN detection.
This development batch addresses two additional blockers:

- QF attempts intentionally leave the textual `answer` field empty. Delivery
  reporting and reviewer failure classification now use the benchmark identity
  and verifier/runtime outcomes instead of labeling every QF attempt as an
  undelivered answer. Legacy task IDs and saved QF evaluation reports are covered.
  HealthBench's empty-answer detection remains enabled.
- The QF toolkit no longer imports `subprocess` or launches a solution. It writes
  and compares output fingerprints, while the learner reruns its solution through
  its existing terminal tool. Complete candidates retaining the toolkit now pass
  the optimizer's generated-script audit.

Regression coverage includes passing and failing QF verifier outcomes, runtime
errors, tune-only reviewer evidence, complete candidate materialization, and
fingerprint detection of changed, added, and removed files.

## Training data and initial experiment

All 54 QF public training tasks were downloaded from
`armin-aptura/skilltrainbench-public` at revision
`9d6f3a635bd9464d1930516215c760b2ebc213cd`. Other domains were not downloaded.
Source data and benchmark files remain under ignored `dataset/`.

Initial paired pipeline smoke:

- Task: `corporate-action-adjustment`.
- Arms: placebo and skill; concurrency 1.
- Evidence: `runs/qf-smoke-20260919T145953Z/`.
- The run saves a frozen skill folder, its digest, a manifest, and the source diff.
- Planned next development tasks: `alpha-hedge-strategy` and
  `asian-option-levy-curran`, using the same frozen skill and paired arms.

The smoke completed with placebo **1/1**, skill **1/1**, and net gain **0**.
Recorded learner usage was 284,060 tokens and estimated cost **$0.01959858**;
this excludes the separate doctor inference probes. Both arms correctly report
zero text-delivery failures. The placebo used 6 tool calls; the skill used 16.
The learner's own trajectory cost field reports zero, so costs above come from
the metered evaluation ledger instead.

The skill initially made a nearest-prior date lookup error, then corrected it.
It also spent actions repairing ad hoc verification code. A general as-of helper
and boundary-check candidate is isolated in
`runs/qf-asof-candidate-20260919T1510/skill/`; its 15 offline tests pass, but it
has not been evaluated or promoted. It contains no task-specific answers.

The paired development evaluation is running at
`runs/qf-development-20260919T151534Z/` on `alpha-hedge-strategy` and
`asian-option-levy-curran`, using the same frozen skill and concurrency 1.

An additional paired development run on `13f-amendment-aware-crowding` is at
`runs/qf-filings-20260919T151938Z/`. It also uses concurrency 1; at most two
learner containers run across the two evaluations, after checking actual memory
usage. Alpha strategy completed with placebo **0/1** and skill **0/1**, both
without infrastructure exceptions. The skill solution added a positive cost
series to returns, so schema/repeatability checks did not establish financial
correctness.

The isolated candidate additionally makes the signal information timeline and
full-calendar rebalance boundaries explicit. It passed the generated-script audit
and a verbatim 12-word overlap scan against all public QF instructions. These
checks do not establish benchmark improvement or prove absence of all leakage.

A second isolated candidate at
`runs/qf-temporal-cost-candidate-20260919T1530/skill/` adds an explicit cost-sign
identity, fee-monotonicity check, and tested `net_of_costs` helper. Its 16 offline
tests, script audit, and verbatim-overlap scan pass. It is not promoted. Its split
is fixed: corporate actions and alpha strategy for tuning; Asian options and
filing reconstruction for validation.

## Runtime invalidation discovered during development

The filing placebo crashed with an upstream `litellm.exceptions.APIError` and
`NonZeroAgentExitCodeError`. Harbor nevertheless emitted a verifier reward of
zero. The earlier harness accepted that fallback as a scored failure.

The adapter now recognizes explicit provider exception lines accompanying a
nonzero agent exit and a failing reward, and routes those attempts through the
existing infrastructure retry path. Ordinary wrong answers are still not
retried; budget exhaustion remains a stop condition. All 38 repository tests
pass, including these cases. The original filing attempt is recorded in
`runs/qf-filings-20260919T151938Z/infrastructure-invalidations.json` and must be
excluded from comparisons and rerun. The already-running process uses the old
adapter, so its raw aggregate must not be quoted as a valid paired score.

No candidate has been promoted. The one-task smoke is a tie and does not
establish generalization. Broader or fresh-family confirmation remains required
before any leaderboard claim.
