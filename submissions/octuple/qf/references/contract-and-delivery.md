# Contract, implementation, and delivery

Read this for every task. Treat prose, tables, examples, parameters, and filenames as one contract; reconcile conflicts before coding.

## Contract ledger

Record inputs (absolute path, delimiter, schema, units, order, cleaning); outputs (directory, files, keys/columns/types/order, intermediates); computation (mandated model, parameter source, initialization/update/stopping rules); conventions; and runtime (dependencies, entry point, test command). Map every output field to its producing function and source columns.

## Inspect efficiently

Use `find`/`ls`, then bounded summaries. Read parameter JSON completely. For tables report shape, columns/dtypes, head/tail, null/non-finite counts, identifier uniqueness, duplicated keys, date range/order, categories, and units. Validate joins with cardinalities and anti-joins. Never silently discard rows: count cleaning reasons and define precedence if reasons overlap.

Probe installed packages; do not add network dependencies. Prefer installed NumPy/SciPy/pandas/statsmodels only where useful. Standard-library fallbacks suit small I/O tasks.

## Implementation skeleton

Create `/app/solution.py` early with pure `load_inputs`, `compute`, `validate`, and `write_outputs` functions plus a guarded `main`. Resolve `OUTPUT_DIR` exactly as specified and create it safely.

Fail loudly on missing columns, invalid duplicate keys, inconsistent shapes, invalid domains, optimizer failure, or non-finite results. Do not turn errors into plausible zeroes. Use float64, contract-defined stable sorting, and explicit tie breaks.

Recursively convert NumPy values to native JSON values, reject non-finite floats, and use `allow_nan=False`. Write exactly named CSV columns and prevent numeric values becoming strings. Preserve integer and boolean JSON types.

## Delivery validation

1. Isolate stale outputs without deleting inputs.
2. Run the documented entry point from the grader's likely working directory.
3. Check every required file is nonempty.
4. Parse all files; validate keys/columns, counts, uniqueness, order, types, finiteness, and cross-file identities.
5. Hash outputs, rerun, and compare hashes.
6. Run the allowed test command and work from its first failure.

Do not inspect benchmark test source, verifier code, hidden expectations, solution folders, or oracle artifacts. A public test command's emitted failure is evidence; answer data is not.

## Failure localization

- Missing file/field/type: fix writer/path before math.
- Many numeric failures: inspect parameter source, ordering, alignment, units, or a shared transform.
- Small constant factor: inspect percent/decimal/bps, day count, annualization, variance/volatility.
- One-row mismatch: inspect inclusivity, lag direction, first valid date, sort order, business-day policy.
- Sign flip: inspect side/payoff and losses versus returns.
- Optimizer nearly right: inspect status, constraints, scaling, and post-normalization.
- Values right but iteration count wrong: write the update/convergence/count timeline.
- Intermittent result: seed all RNGs, avoid unordered dependence, stabilize linear algebra, and bound MC error.
