# QF toolkit usage

`qf_tool.py` is offline and deterministic. It uses only the standard library; its numerical helpers accept ordinary sequences and can be imported into `/app/solution.py`.

- `route`: returns the smallest relevant helper/check set for families/features/outputs. It does not choose a financial model.
- `inspect PATH`: bounded CSV/JSON schema, shape, date-like range, null/non-finite, and JSON key/type inspection.
- `validate OUTPUT_DIR --required ...`: checks file presence, parsing, and finiteness. Use `--write-fingerprint /app/before.json`, rerun the solution separately, then use `--compare-fingerprint /app/before.json` to detect changed, added, or removed files. Store the snapshot outside `OUTPUT_DIR`. Exact schemas and financial identities require task-specific checks.
- `selftest`: fast embedded checks.

Run fuller tests with `python /harbor/skills/stbench-skill/scripts/test_qf_tool.py`.

Imports cover returns/performance, covariance/correlation, weights/matrices, Black–Scholes/parity, historical VaR/ES, HMM/transitions, inclusive date windows, strict JSON, and fingerprints. Always pass contract conventions (`ddof`, periods, tail/confidence, interpolation/sign); defaults are not claims about a task.
