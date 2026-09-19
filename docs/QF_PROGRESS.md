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

No candidate has been promoted. The one-task smoke is a tie and does not
establish generalization. Broader or fresh-family confirmation remains required
before any leaderboard claim.
