# QF development — 2026-09-19

## Current conclusion

The timing-only candidate passed **alpha-hedge-strategy: 1/1**, compared with
**0/1** for both the original skill and the accounting-only edit on the same public
training task. This is the first measured tuning improvement, not a held-out result.
The run completed normally, with 152,676 tokens and **$0.01008204** recorded cost
(complete). Evidence: `runs/qf-original-timing-20260919T170311Z/eval-alpha`.

The candidate retains the original references and scripts and adds one instruction
to trace information availability before crediting returns. Its digest is
`9e4d063aa0ee93c80002f3f8df149a1d6fb43b6add61d5e33bcac426f1f34977`.
The user explicitly selected the best available QF version. The active submission
now includes this successful timing rule, the earlier accounting checks, and the
verified numerical fix below. This is a manual selection based on the strongest
observed tuning result, not an automated validation-gated promotion. Reserved
validation and the corporate-action regression check remain outstanding. The exact
previously evaluated candidate remains reproducible under `docs/qf-candidates/`.
No unsuccessful rewritten candidate has replaced the base.

The original incumbent remains frozen at digest
`6eee54bacc74a13a422a4578aa2b43ef60545151c972763815922c346b63f92a`.
The accounting-only evaluation at
`runs/qf-astra-daily-accrual-20260919T164105Z/eval-alpha` scored **0/1**, with no
provider errors and **$0.01542876** cost. Original Brinson attribution and
corporate-action checks both passed, tying their placebo controls.

The user authorized direct pushes to main. Upstream changes through `450e3d3`
are consolidated. Credentials, datasets, and detailed run artifacts remain ignored.
Doctor confirms Docker, API authentication, and all 54 QF tasks; the full-dataset
check fails because other domains have not been downloaded.

## Live numerical correctness fix

The original Black–Scholes helper lost representable tail probabilities through
`1 + erf(...)` cancellation. For synthetic spot 100, strike 600, maturity 1,
rate 0, and volatility 0.2, the old call price was zero. The stable `erfc` form
returns **8.721049889482367e-19**, agreeing with independent payoff-density
quadrature (**8.721049889095937e-19**) within 1e-8 relative tolerance. Put delta
now uses the opposite tail directly instead of subtracting one from a rounded CDF.

The live fix preserves the base and adds a regression covering numerical integration,
call/put symmetry, and finite-difference put delta. All **15 toolkit tests** and
**44 repository tests** pass. Static skill validation, offline script audit,
54-instruction exact-overlap scan, and diff checks pass. Live digest:
`24d3ff688c71bc1bfe524ba30d639ec9c021aa656e400bc45840d7d4ebae990a`
(includes the user-selected timing rule).
This is a verified numerical improvement; no benchmark score gain is attributed
to this helper change. The exact timing-only candidate remains separately reproducible. The combined
active package has passed offline checks but has not itself been benchmarked.

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
static check passes (8 files, 49,794 bytes), and `git diff --check` passes.
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
| `brinson-sector-attribution` | pass | pass | tie; original base preserved |

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
| `qf-asian-placebo-retry-20260919T160833Z/evaluation` | interrupted to prioritize the candidate after further transport failures; unscored | partial ledger retained |
| `qf-astra-daily-accrual-20260919T164105Z/eval-alpha` | original base plus accounting checks, normal completion 0/1; no gain | 0.01542876 |
| `qf-brinson-incumbent-20260919T170151Z/evaluation` | original skill 1/1, placebo 1/1; includes an unscored verifier-download failure before retry | 0.02689535 |
| `qf-original-timing-20260919T170311Z/eval-alpha` | normal completion 1/1; first tuning gain, validation pending | 0.01008204 |

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
   must be kept separate.
4. The original-base accounting edit fixed daily accrual, cost signs, and schedule
   construction, but still selected positions using the same return later credited
   to those positions. The timing-only candidate addresses this look-ahead without
   imposing a universal lag or changing the original references and scripts.

Some signal and sizing conventions in the public alpha task are underspecified.
These ambiguities do not explain the concrete return-sampling bug. Candidates
must teach general methods, not memorize task constants or expected outputs.

The standalone synthetic-timing candidate at
`qf-astra-tune-20260919T155123Z/skill` passed offline checks but was not evaluated.
The concise and period-boundary candidates remain isolated and unpromoted. A small
drift-helper candidate also passed 18 offline tests, but it will not be evaluated
on attribution because the original already passes that task.

## Next work

Confirm the successful timing edit on the corporate-action regression task and
reserved validation tasks under the unchanged learner. Because provider read timeouts and HTTP 429 responses contaminated
parallel runs, let existing work finish and run subsequent evaluations one at a
time. Do not change pinned inference settings or extend task limits.

Check the active version on the corporate-action regression case and both
reserved validation tasks against valid incumbent attempts; reassess the manual
selection if confirmation shows a regression. A larger fresh training confirmation is required before claiming
broad QF improvement; local results cannot guarantee held-out leaderboard gains.
