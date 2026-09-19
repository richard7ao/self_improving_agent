# QF agent prompt

Copy the prompt below into the agent session responsible for QuantitativeFinance-Bench.

---

Build and optimize the QF submission for QuantitativeFinance-Bench.

QF is a deterministic coding and calculation benchmark:

- The learner has 100 iterations.
- Tasks are pass/fail based on generated files and numerical tests.
- The learner normally builds executable artifacts under `/app`; prose is not the
  deliverable.
- Deterministic tools, financial invariants, exact conventions, and local test-driven
  debugging are high-value.
- Tool-call compression is secondary to mathematical and executable correctness.

Build broadly first. Do not reduce the skill or scripts until experiments identify dead
weight; compression happens at the end.

## Scope and repository discipline

Start with:

```bash
git status --short --branch
uv run stbench doctor
```

Read completely:

- `AGENTS.md`
- `README.md`
- `richard_metholody.md`
- `docs/TEAMMATE_GUIDE.md`
- `docs/FINANCE_LOOP.md`
- `docs/FINANCE_LOOP_HANDOFF.md`
- the complete current `submissions/octuple/qf/`
- completed QF run artifacts and relevant trajectories

Inspect public QF training-task metadata and instructions to identify general task
families and failure modes. Never copy task text, expected outputs, verifier logic,
solutions, task-specific constants, or task-to-answer mappings into the submission.

Work only on `submissions/octuple/qf/`, QF-specific tests/documentation when required,
and isolated ignored candidate folders under `runs/`. Do not edit other submissions,
`.env`, datasets, `hackathon.toml`, the frozen learner, benchmark tests, or shared harness
code without explicit authorization.

Preserve concurrent work. Stage exact paths only. Never use `git add .`, `git add -A`,
or `git commit -a`. Submitted scripts must run offline without APIs, credentials,
network access, or external LLMs.

## Objective

Create a general QF skill that makes the frozen learner reliably:

1. Parse the complete task contract.
2. Inspect input files and installed dependencies.
3. Select the required quantitative-finance model.
4. Implement a deterministic solution early.
5. Produce every required output file and intermediate.
6. Run permitted tests without inspecting or copying expected answers.
7. Diagnose the earliest causal failure.
8. Correct formulas, conventions, schemas, and edge cases.
9. Stop only when artifacts exist and tests pass, or a real blocker is documented.

The competition-relevant metric is `skill pass rate - placebo pass rate`. Optimize
executable correctness, not response prose.

## Mandatory learner workflow

### 1. Extract the contract

Record:

- inputs and schemas;
- required output files and exact field names/types;
- required intermediates;
- mandated algorithm and initialization;
- parameters that must be read rather than hardcoded;
- return, frequency, annualization, sign, indexing, and `ddof` conventions;
- date alignment and missing-data rules;
- normalization constraints;
- convergence rule and iteration-count definition;
- random seed, tolerance, dependencies, and execution command.

Never replace a mandated algorithm with a convenient library default.

### 2. Inspect data efficiently

Inspect filenames, shapes, columns, types, heads/tails, date ranges/order, missing and
non-finite values, units, frequencies, identifiers, matrices, and parameter files. Do
not repeatedly print entire datasets.

### 3. Route the task

Choose one or more primary families:

- derivatives, Monte Carlo, tree, or PDE pricing;
- volatility, stochastic processes, jump diffusion, or time series;
- HMM/regime switching;
- portfolio optimization, Black–Litterman, factors, or attribution;
- hedging and Greeks;
- VaR/CVaR, EVT, copulas, credit risk, or fixed income;
- execution, market impact, or microstructure;
- event studies and regulatory filing signals;
- data transformation/reporting;
- mixed or uncertain.

Select from task semantics and explicit requirements, not keywords alone.

### 4. Build and execute early

Create the main solution early, normally `/app/solution.py`. Separate I/O, model
fitting, calculations, validation, and output writing. Read parameters from inputs,
preserve precision, use stable numerical methods, create directories safely, and reject
NaN/Infinity in JSON. Execute a complete first version before spending many actions on
planning artifacts.

### 5. Check independent invariants

Always check applicable invariants:

- outputs exist, parse, contain exact keys/types, and are finite;
- shapes, dates, and identifiers align;
- probabilities and transition rows normalize;
- covariance matrices are symmetric and variances nonnegative;
- portfolio constraints and exposure conventions hold;
- prices respect basic bounds/parity/limiting behavior;
- risk tails and signs are correct;
- HMM labels derive from fitted properties rather than assumed indices;
- event windows use correct trading days and inclusivity;
- reruns are deterministic.

### 6. Run tests and fix the earliest cause

Classify failures as missing file, schema/type, wrong model, wrong parameter source,
frequency/annualization, `ddof`, date-window, sign/tail, normalization,
convergence/iteration, numerical stability, nondeterminism, tolerance, dependency, or
edge case. Fix the first causal error rather than patching downstream values.

## High-risk convention checklist

Make these prominent in `SKILL.md`:

- simple versus log returns;
- arithmetic versus geometric annualization;
- daily versus annual parameters;
- variance versus volatility;
- `ddof=0` versus `ddof=1`;
- calendar versus trading days;
- inclusive versus exclusive windows;
- gains versus losses and left versus right tail;
- decimal, percent, and basis points;
- gross exposure versus sum-to-one;
- matrix orientation and asset indexing;
- state-label switching;
- convergence timing and iteration reporting;
- maximum-drawdown sign versus positive magnitude.

## Offline toolkit

Build reusable offline scripts under `submissions/octuple/qf/scripts/`, preferably with a
single routed entry point such as `qf_tool.py`. Provide general helpers for:

- CSV/JSON schema, finiteness, dates, required keys, and serialization;
- return conversion, wealth, annualization, volatility, Sharpe, drawdown, turnover;
- covariance/correlation, PSD/symmetry, exposures, matrix conditioning and residuals;
- Black–Litterman components and portfolio constraints;
- Black–Scholes/Greeks, parity, payoff and simulation checks;
- historical/parametric VaR, ES, EVT, copulas, and credit aggregation;
- lags, EWMA, realized volatility, regressions, HMM normalization and likelihood;
- event windows, abnormal returns, schedules, participation, and impact units.

Tools validate a model selected by the learner; they must not pretend to choose the
correct financial model or embed task-specific solutions. The router should return the
smallest relevant tool set, required inputs, uncertainty reduced, stopping conditions,
and misuse warnings.

Add offline tests for annualization, drawdown, covariance `ddof`, normalization, matrix
residuals, risk-tail orientation, option parity, HMM probability normalization,
transition matrices, window inclusivity, JSON finiteness, and determinism.

## Evaluation

1. Inspect existing QF runs before launching anything.
2. Start with at least three stratified public tasks so validation is meaningful.
3. Compare skill and placebo on identical tasks.
4. Inspect every failed trajectory and artifact.
5. Confirm promising changes on fresh task families.
6. Do not promote ties or validation regressions.
7. Never overwrite run evidence; use unique ignored directories.

Report task list, family coverage, baseline/placebo/skill pass rates, net improvement,
per-task outcomes, artifact failures, action counts, cost, promotion decision, and
uncertainty. Training performance is not a held-out guarantee.

Use development subagents, if available, only for bounded independent analysis such as
derivatives, portfolio/risk, and time-series/event/execution. They may derive reusable
principles but must not place task-specific answers into the skill.

## Verification and handoff

After each material edit run:

```bash
uv run stbench check-skill submissions/octuple/qf
uv run python -m unittest discover -s tests -q
git diff --check -- submissions/octuple/qf
git status --short --branch
```

Commit only exact tested QF paths and report the hash. Never commit `.env`, `dataset/`,
or `runs/`.

Core principle: correct executable artifacts, exact conventions, deterministic
calculations, and passing tests are the deliverable.
