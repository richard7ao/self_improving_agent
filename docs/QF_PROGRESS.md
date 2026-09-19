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
`runs/qf-filings-20260919T151938Z/`. Each evaluation uses concurrency 1.
The initial two evaluations were later joined by candidate and infrastructure
replacement runs, with at most four learner containers after checking actual
memory usage. Alpha strategy completed with placebo **0/1** and skill **0/1**, both
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

Its alpha run ended with `AgentTimeoutError` and a raw reward of zero, but the
gateway ledger shows two confirmed `ReadTimeout` failures lasting approximately
600 seconds each. Those failures consumed about 20 minutes of the task's
30-minute agent limit. This is an **inconclusive infrastructure-contaminated
result** that does not isolate candidate quality.
The raw evidence is retained alongside `infrastructure-invalidations.json`.
Recorded successfully priced calls cost **$0.01514160**. Charges for the failed
calls are unknown; the old report's `incomplete: false` was misleading because
its check omitted fail-closed error rows. Nothing was promoted.

The last executed solution did contain an independently identifiable bug: its
rebalance mask compared integer day numbers with full datetime values. No dates
matched, positions stayed zero, performance ratios became undefined, and strict
JSON serialization failed. Cost subtraction was correct in this attempt. The
next isolated candidate addresses the calendar operation with a tested generic
period-boundary helper; it does not encode task-specific dates or parameters.

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

The replacement filing placebo completed normally at
`runs/qf-filing-placebo-retry-20260919T155039Z/evaluation/`: **0/1**, 58,701
tokens, estimated learner cost **$0.00455863**, fully priced. This replacement
was for a confirmed infrastructure failure, not a retry of a wrong answer.
The incumbent filing skill later ended with `AgentTimeoutError`. Its last two
gateway events were read timeouts lasting roughly 600 and 631 seconds. That
skill result is also inconclusive and excluded; the raw paired zero/zero report
is not valid evidence of candidate quality. The original filing evaluation
records **$0.02430515** in priced calls, with failed-call costs unknown.

The Asian-option placebo also crashed with an explicit upstream provider error.
Its fallback zero is excluded in
`runs/qf-development-20260919T151534Z/infrastructure-invalidations.json`.
The original evaluation proceeded to the skill arm under the old adapter; a new
placebo attempt is running at
`runs/qf-asian-placebo-retry-20260919T160833Z/evaluation/` for a valid comparison.

## Parallel Astra review

The user authorized Astra agents at high reasoning for parallel work. Two
isolated candidates were prepared from the frozen temporal-cost candidate:

- `runs/qf-astra-tune-20260919T155123Z/skill/`: adds a small synthetic timing
  trace and causal perturbation checks. Changes only the entry point and the
  portfolio reference. Static checks, script audit, 16 helper tests, and a
  mechanical 12-word overlap scan against public instructions pass. It has not
  been benchmark-evaluated.
- `runs/qf-astra-concise-20260919T155138Z/skill/`: shortens the entry point from
  8,167 to 5,226 bytes while retaining the helpers and references. The hypothesis
  is that conditional support and fewer mandatory checks reduce distraction.
  Static checks and 16 helper tests pass. An alpha-only tune evaluation is running.
- `runs/qf-astra-period-boundary-20260919T161307Z/skill/`: extends the concise
  candidate with `period_start_indices` and explicit first-row handling, plus
  schedule coverage and date-type checks. All 20 helper tests, static checks,
  script audit, and the overlap check pass. Its alpha evaluation is running with
  live gateway ledger persistence.

Neither agent inspected reserved validation solutions for candidate development.
The split remains corporate actions plus alpha for tuning, Asian options plus
filings for validation. No candidate is promoted on a tune result alone.

A read-only runtime audit found responsive gateways, spare CPU and memory, and
adequate token budgets. Several model responses took much longer than the initial
smoke, whose 20 API calls had median latency 27 seconds and maximum 56 seconds.
The current delays cannot be attributed to local compute saturation. Pinned
learner settings and task limits remain unchanged.

Commit `f386cf2` persists completed gateway-call metadata during evaluations and
corrects incomplete-cost reporting for charged errors. All 43 repository tests
pass. This changes observability only; timeout classification still requires
careful review where per-attempt gateway attribution is unavailable.

No candidate has been promoted. The one-task smoke is a tie and does not
establish generalization. Broader or fresh-family confirmation remains required
before any leaderboard claim.
