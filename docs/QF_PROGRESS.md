# QF development — 2026-09-19

## Current conclusion

No measured skill improvement has been established and no candidate has been
promoted. The live QF skill matches the frozen incumbent used in the initial
comparisons (digest `6eee54bacc74a13a422a4578aa2b43ef60545151c972763815922c346b63f92a`).
The strongest completed challenger finished normally but failed alpha strategy.
The next hypothesis separates daily return accrual from monthly holdings updates.

The user authorized pulling, consolidating, pushing, and continued work. Pulling
`origin/main` into `codex/qf-evaluation-and-tools` found no newer upstream changes.
Only source, submission tooling fixes, tests, and this report are tracked;
credentials, datasets, candidates, and detailed run evidence remain local/ignored.

## Tested engineering changes

- QF is graded from generated artifacts. Empty textual answers no longer become
  false delivery failures in reports or optimizer reviews. Health text checks remain.
- QF repeatability checks use output fingerprints instead of launching subprocesses,
  so the complete skill passes the optimizer script audit.
- Confirmed provider crashes with fallback verifier zeros enter infrastructure retry
  handling rather than being silently accepted as wrong answers.
- Completed gateway calls are persisted during evaluation. Unknown costs for charged
  transport failures correctly mark total cost as incomplete.

Commits: `a01a129`, `635f879`, `b87de7f`, `f386cf2`.
Verification: **43 repository tests pass**, **14 live-toolkit tests pass**, live skill
static check passes (8 files, 48,814 bytes), and `git diff --check` passes.
The period-boundary challenger has **20 passing offline tests**, a clean generated
script audit, and no 12-word verbatim overlap with the 54 public instructions.

The pinned learner, task limits, scoring, and `hackathon.toml` are unchanged.
Timeouts with confirmed transport failures still need manual exclusion when the
legacy gateway ledger cannot reliably attribute events to individual attempts.
An ordinary learner failure is never retried merely to improve its score.

## Public training evidence

All 54 QF tasks are available from `armin-aptura/skilltrainbench-public`, revision
`9d6f3a635bd9464d1930516215c760b2ebc213cd`. Other domains were not downloaded;
that explains the doctor's global dataset-completeness failure. Docker, API
credentials, and tiny Runware/OpenAI inference probes passed.

Fixed split: corporate actions and alpha strategy for tuning; Asian options and
filing reconstruction for validation. Validation solutions were not used to
write candidates. No no-skill baseline arm was run; placebo is the comparison.
Promotion requires strict improvement on the task-weighted aggregate and reserved
validation scores, never a tie.

| Task | Placebo | Incumbent skill | Valid conclusion |
|---|---|---|---|
| `corporate-action-adjustment` | pass | pass | tie |
| `alpha-hedge-strategy` | fail | fail | tie |
| `asian-option-levy-curran` | API crash; replacement running | timeout with transport failures | inconclusive |
| `13f-amendment-aware-crowding` | replacement failed normally | timeout with transport failures | inconclusive |

The original options and filing raw zero/zero reports must not be quoted as clean
paired comparisons. Their invalidations are recorded alongside the run evidence.

## Experiments and recorded cost

Paths below are under ignored `runs/`. Costs are the recorded estimates for
successfully priced calls; entries marked incomplete exclude unknown failed-call
charges. Separate doctor probes are not included.

| Run directory | Outcome | Recorded USD |
|---|---|---:|
| `qf-smoke-20260919T145953Z/evaluation` | corporate actions 1/1 in both arms; 284,060 tokens | 0.01959858 |
| `qf-development-20260919T151534Z/evaluation` | valid alpha 0/0; both options arms contaminated by infrastructure | 0.03639786, incomplete |
| `qf-filings-20260919T151938Z/evaluation` | placebo API crash; skill timeout with two long read timeouts | 0.02430515, incomplete |
| `qf-filing-placebo-retry-20260919T155039Z/evaluation` | valid placebo 0/1; 58,701 tokens | 0.00455863 |
| `qf-temporal-cost-candidate-20260919T1530/eval-alpha` | inconclusive: two 600-second read failures consumed most of the agent limit | 0.01514160, incomplete |
| `qf-astra-concise-20260919T155138Z/eval-alpha` | inconclusive: read timeout and repeated HTTP 429 responses before agent timeout | 0.01494540, incomplete |
| `qf-astra-period-boundary-20260919T161307Z/eval-alpha` | normal completion, score 0/1; 336,556 tokens; rejected for no gain | 0.02028193 |
| `qf-asian-placebo-retry-20260919T160833Z/evaluation` | replacement still running | pending |

Older raw reports incorrectly mark some transport-failure costs complete; the
new cost-reporting fix corrects future runs without overwriting old evidence.

## What the tuning trajectories taught us

1. The incumbent added a nonnegative fee series to gross returns. The temporal
   candidate introduced explicit net-return subtraction and fee monotonicity checks.
2. That candidate then compared integer day numbers with datetime values when
   constructing a rebalance mask. No dates matched; zero returns led to undefined
   ratios and JSON failure. The period-boundary helper fixes this operation.
3. The latest challenger constructed its calendar correctly but calculated P&L only
   on rebalance dates, dropping intervening daily returns from regression and
   performance statistics. Holdings update frequency and return accrual frequency
   must be kept separate. This is the next focused change.

Some signal and sizing conventions in the public alpha task are underspecified.
These ambiguities do not explain the concrete return-sampling bug. Candidates
must teach general methods, not memorize task constants or expected outputs.

The standalone synthetic-timing candidate at
`qf-astra-tune-20260919T155123Z/skill` passed offline checks but was not evaluated.
The concise and period-boundary candidates remain isolated and unpromoted.

## Next work

Prepare a small daily-accrual candidate, then test alpha under the unchanged
learner. Because provider read timeouts and HTTP 429 responses contaminated
parallel runs, let existing work finish and run subsequent evaluations one at a
time. Do not change pinned inference settings or extend task limits.

If the challenger gains on tuning, check the corporate-action regression case and
both reserved validation tasks against valid incumbent attempts. Otherwise retain
the incumbent. A larger fresh training confirmation is required before claiming
broad QF improvement; local results cannot guarantee held-out leaderboard gains.
