# Local run dashboard

Start the read-only dashboard from the repository root:

```bash
uv run python -m dashboard.app
```

It opens <http://127.0.0.1:8765>, scans the ignored `runs/` directory, and refreshes
every five seconds. It displays completed scores, placebo-adjusted deltas, task counts,
delivery failures, tokens, costs, and partial Harbor job progress for active runs.
Click any run row to see each Harbor job's task, arm, score, delivery, action count,
token use, duration, and verifier metrics.

Useful options:

```bash
uv run python -m dashboard.app --no-open
uv run python -m dashboard.app --port 9000
uv run python -m dashboard.app --runs-dir /path/to/runs
```

The server binds to `127.0.0.1` by default and never writes to run artifacts.

For a terminal snapshot of the newest results and all active evaluations:

```bash
uv run python scripts/check_results.py
```

Watch Health, HLE, and TAU3 and print a new snapshot whenever their artifacts change:

```bash
uv run python scripts/check_results.py --domain health,hle,tau3 --watch 5
```

Use `--json` for machine-readable output or `--latest 3` to include the three newest
completed runs per domain. Add `--include-incomplete` when diagnosing abandoned or
summary-less historical directories. Like the web dashboard, this command is read-only.
