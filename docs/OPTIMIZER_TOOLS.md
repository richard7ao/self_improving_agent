# Optimizer tools

These utilities perform deterministic work around the model-driven optimizer. Most never
run paid benchmark evaluations; `run_repeated_trials.py` requires an explicit `--execute`
switch before it will do so. Run them from the repository root with
`uv run python scripts/optimizer/<tool>.py --help`.

| Tool | Purpose |
|---|---|
| `stratify_tasks.py` | Make reproducible tune/validation splits from labeled task records. |
| `build_safety_suite.py` | Build a reproducible critical-label task manifest. |
| `classify_failures.py` | Separate delivery, infrastructure, invalidation, and low-score failures. |
| `candidate_diversity.py` | Detect exact duplicate candidates and report lexical distance. |
| `deduplicate_candidates.py` | Produce a non-destructive exact-duplicate keep/drop plan. |
| `semantic_leakage_scan.py` | Flag suspicious token-shingle overlap with source material. |
| `validate_generated_tool.py` | Audit generated Python and optionally run explicit self-tests. |
| `paired_statistics.py` | Compute paired deltas and bootstrap confidence intervals. |
| `sequential_test.py` | Decide promote/reject/continue from accumulating paired differences. |
| `promotion_gate.py` | Require aggregate, validation, and optional confidence improvement. |
| `safety_regression_gate.py` | Reject regressions on task labels declared critical. |
| `plan_repeated_trials.py` | Produce a randomized, reproducible repeated-trial manifest. |
| `run_repeated_trials.py` | Execute a manifest only with an explicit paid-run switch. |
| `budget_forecaster.py` | Estimate attempts and learner/grader tokens before a run. |
| `snapshot_provenance.py` | Record Git state, platform, and artifact hashes without secrets. |
| `experiment_registry.py` | Append experiment metadata through atomic JSON replacement. |
| `replay_experiment.py` | Reconstruct a best-effort replay command from saved state. |
| `recover_transaction.py` | Inspect or explicitly restore interrupted promotion backups. |
| `generate_report.py` | Render evaluation or optimization JSON as a compact Markdown report. |

Core implementations live in `src/skilltrainbench/optimizer_tools.py`, so the same rules can
be imported by the optimizer and tested without spawning commands.

## Integrated protections

`stbench optimize` now automatically:

- statically rejects generated scripts that import network/process-control modules or call
  dynamic code execution primitives;
- records candidate similarity and rejects exact duplicate variants before spending task
  evaluation budget;
- includes deterministic failure-class counts in reviewer evidence;
- stores paired bootstrap evidence for every promotion decision;
- optionally requires the bootstrap lower bound to exceed the configured improvement via
  `--require-confidence`; and
- writes optimizer state atomically and records a non-secret provenance snapshot.

Confidence gating is opt-in because very small smoke runs cannot establish a useful lower
bound. Use it for broader confirmation runs:

```bash
uv run stbench optimize \
  --domain health \
  --skill submissions/octuple/health \
  --out runs/health-confidence-001 \
  --iterations 1 --candidates 3 --limit 24 \
  --min-improvement 0.01 \
  --require-confidence --promotion-confidence 0.95
```

The semantic leakage scanner is deliberately described as heuristic. Passing it does not
prove that a candidate is uncontaminated; exact-copy checks, information boundaries, and
human inspection remain necessary.

The generated-tool self-test runner uses a temporary working directory and minimal
environment, but it is not a complete operating-system sandbox. Benchmark execution still
belongs inside the existing Docker boundary.
