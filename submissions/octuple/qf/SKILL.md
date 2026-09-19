---
name: octuple-qf
description: Build, run, and debug deterministic quantitative-finance solutions whose correctness is judged from generated files and numerical tests.
---

# Quantitative-finance artifact solver

The deliverable is an executable implementation and every required artifact—not an explanation. Work in `/app`, normally create `/app/solution.py` early, run it, and continue until outputs exist and the allowed tests pass. Preserve full precision internally; round only where the contract says to.

## Mandatory loop

1. **Read the whole contract once.** Write a compact contract ledger: every input/schema; output path, filename, exact field/key/type and intermediate; mandated formula/algorithm; parameter sources; return, frequency, annualization, `ddof`, sign/tail, units, normalization, date/missing-data, initialization, convergence/iteration, seed, tolerance, library, and execution conventions. An explicit algorithm overrides a library default.
2. **Inspect before modeling.** List files; summarize schemas, dtypes, shapes, heads/tails, dates/order, null/non-finite counts, identifiers, categories, dimensions, parameter JSON, units, and output directories. Do not dump or repeatedly load large files. Check installed packages rather than assuming them.
3. **Choose the governing family from semantics.** Use one primary family and any secondary family: derivatives; Monte Carlo; lattice/tree; PDE; volatility; stochastic/jump processes; time series; HMM/regimes; portfolio/Black–Litterman; hedging/Greeks; market/credit risk; VaR/ES; copulas/EVT; credit portfolio; fixed income/term structure; execution/impact; events/filings; factor/attribution; microstructure; transformation/reporting; mixed/uncertain. Keywords alone do not choose the model.
4. **Build and run early.** Separate I/O, calculations/fitting, invariants, and writers. Read parameters from inputs, avoid output constants, create directories, seed RNGs exactly, use stable numerics, and reject JSON NaN/Infinity. Produce requested diagnostic intermediates. Run the first complete version immediately.
5. **Check independent invariants.** Confirm files, schemas, types, shapes, finiteness, alignment, deterministic reruns, and model-specific identities before tests. Use `qf_tool.py` where applicable. Invariants do not replace the mandated algorithm.
6. **Run the provided test command.** Do not inspect hidden answers or verifier implementation. From test output, localize the *earliest causal* failure: delivery/schema/type, algorithm/parameter source, unit/frequency/annualization/`ddof`, date/window, sign/tail, normalization, convergence/count, instability/seed/tolerance, edge case, or environment. Fix the cause, not downstream numbers.
7. **Preserve working parts.** After each meaningful fix, rerun the solution, schema checks, invariants, and tests. Avoid rewriting correct components. Stop only when required artifacts exist and tests pass, or report the exact blocker.

## Convention lock before coding

Record: simple/log returns; daily/annual and arithmetic/geometric annualization; variance/volatility; population/sample (`ddof=0/1`); calendar/trading days; inclusive/exclusive windows; price/total return; gains/losses and left/right tail; decimal/percent/bps/pips; covariance and risk-free frequency; net sum/gross exposure; label order/matrix orientation; fitted-state relabeling; convergence before/after update; zero/one-based indexing; and signed drawdown/positive magnitude. Never infer a convention the task states.

## Routed references

- Read [references/contract-and-delivery.md](references/contract-and-delivery.md) for every task, especially multi-file outputs or ambiguous execution/test commands.
- Read [references/derivatives-and-fixed-income.md](references/derivatives-and-fixed-income.md) for pricing, simulation, lattices/PDEs, Greeks, stochastic processes, FX, or curves.
- Read [references/portfolio-and-risk.md](references/portfolio-and-risk.md) for portfolios, factors, attribution, covariance, risk, copulas, EVT, or credit.
- Read [references/timeseries-events-execution.md](references/timeseries-events-execution.md) for HMMs, volatility/time series, events/filings, execution, microstructure, or data pipelines.

## Offline toolkit

The learner chooses the model from the contract; the router only suggests deterministic checks.

```bash
python /harbor/skills/stbench-skill/scripts/qf_tool.py route \
  --family hmm,portfolio --features covariance,annualization,gross_exposure,convergence \
  --outputs results.json,solution.json
python /harbor/skills/stbench-skill/scripts/qf_tool.py inspect /app/data
python /harbor/skills/stbench-skill/scripts/qf_tool.py validate /app/output \
  --required results.json,solution.json --write-fingerprint /app/qf-output-before.json
python /app/solution.py
python /harbor/skills/stbench-skill/scripts/qf_tool.py validate /app/output \
  --required results.json,solution.json --compare-fingerprint /app/qf-output-before.json
python /harbor/skills/stbench-skill/scripts/qf_tool.py selftest
```

Import helpers from [scripts/qf_tool.py](scripts/qf_tool.py) rather than rewriting them. It covers return/performance, matrix/portfolio, pricing, risk, HMM, date-window, and strict artifact checks. Read [scripts/README.md](scripts/README.md) for CLI/import contracts. Run [scripts/test_qf_tool.py](scripts/test_qf_tool.py) after adapting toolkit code; it does not replace task tests.

Use the task's actual output path and filenames in these commands. Store fingerprints outside the output directory and rerun the solution with the agent's terminal tool; the toolkit never executes commands. Check exact schemas and financial identities separately: generic validation checks file presence, parsing, and finiteness only.

## Completion checks

- Every required file is at the exact path and parses with exact keys/columns and native JSON types.
- No output contains NaN/Infinity; dimensions, identifiers, ordering, dates, and lengths agree across files.
- Probabilities normalize; covariance/transition matrices meet symmetry/row-sum rules; weights meet every net, gross, bound, and exposure constraint.
- Annualization occurs once. Loss direction, quantile interpolation, units, and date inclusivity match the contract.
- Pricing meets applicable bounds/parity/monotonicity; simulations use the specified discretization, seed, path count, and uncertainty.
- Likelihoods are stable; initialization, update order, convergence quantity, count, and state labels match the specification.
- Same inputs produce identical output bytes unless stochastic variation is explicitly allowed.
