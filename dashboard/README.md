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
