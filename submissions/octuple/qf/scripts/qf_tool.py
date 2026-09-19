#!/usr/bin/env python3
"""Deterministic, standard-library QF calculations and artifact checks."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
from typing import Any, Iterable, Sequence

EPS = 1e-12


def _floats(values: Iterable[float], name: str = "values") -> list[float]:
    out = [float(x) for x in values]
    if not out:
        raise ValueError(f"{name} must not be empty")
    if not all(math.isfinite(x) for x in out):
        raise ValueError(f"{name} contains non-finite values")
    return out


def simple_returns(prices: Sequence[float]) -> list[float]:
    p = _floats(prices, "prices")
    if len(p) < 2 or any(x == 0 for x in p[:-1]):
        raise ValueError("need at least two prices and nonzero lagged prices")
    return [p[i] / p[i - 1] - 1.0 for i in range(1, len(p))]


def log_returns(prices: Sequence[float]) -> list[float]:
    p = _floats(prices, "prices")
    if len(p) < 2 or any(x <= 0 for x in p):
        raise ValueError("log returns require at least two positive prices")
    return [math.log(p[i] / p[i - 1]) for i in range(1, len(p))]


def cumulative_wealth(returns: Sequence[float], initial: float = 1.0) -> list[float]:
    rs = _floats(returns, "returns")
    if initial <= 0 or not math.isfinite(initial) or any(r <= -1 for r in rs):
        raise ValueError("wealth requires positive initial value and returns > -1")
    out, value = [], float(initial)
    for r in rs:
        value *= 1.0 + r
        out.append(value)
    return out


def annualized_return(returns: Sequence[float], periods: float, method: str) -> float:
    rs = _floats(returns, "returns")
    if periods <= 0:
        raise ValueError("periods must be positive")
    if method == "arithmetic":
        return statistics.fmean(rs) * periods
    if method == "geometric":
        if any(r <= -1 for r in rs):
            raise ValueError("geometric annualization requires returns > -1")
        return math.exp(statistics.fmean(math.log1p(r) for r in rs) * periods) - 1.0
    raise ValueError("method must be arithmetic or geometric")


def sample_variance(values: Sequence[float], ddof: int) -> float:
    xs = _floats(values)
    if ddof < 0 or len(xs) <= ddof:
        raise ValueError("require 0 <= ddof < sample size")
    mean = statistics.fmean(xs)
    return sum((x - mean) ** 2 for x in xs) / (len(xs) - ddof)


def annualized_volatility(returns: Sequence[float], periods: float, ddof: int) -> float:
    if periods <= 0:
        raise ValueError("periods must be positive")
    return math.sqrt(sample_variance(returns, ddof) * periods)


def sharpe_ratio(returns: Sequence[float], periods: float, ddof: int,
                 risk_free_per_period: float = 0.0) -> float:
    excess = [r - risk_free_per_period for r in _floats(returns, "returns")]
    vol = math.sqrt(sample_variance(excess, ddof))
    if vol <= EPS:
        raise ValueError("Sharpe undefined for zero volatility")
    return statistics.fmean(excess) / vol * math.sqrt(periods)


def downside_deviation(returns: Sequence[float], target: float, periods: float,
                       denominator: str = "all") -> float:
    rs = _floats(returns, "returns")
    shortfalls = [min(0.0, r - target) ** 2 for r in rs]
    n = len(rs) if denominator == "all" else sum(r < target for r in rs)
    if denominator not in {"all", "downside"} or n == 0:
        raise ValueError("invalid denominator or no downside observations")
    return math.sqrt(sum(shortfalls) / n * periods)


def max_drawdown(returns: Sequence[float], positive_magnitude: bool = True) -> float:
    wealth = cumulative_wealth(returns)
    peak, worst = 1.0, 0.0
    for value in wealth:
        peak = max(peak, value)
        worst = min(worst, value / peak - 1.0)
    return -worst if positive_magnitude else worst


def turnover(old: Sequence[float], new: Sequence[float], half_l1: bool) -> float:
    if len(old) != len(new):
        raise ValueError("weight lengths differ")
    value = sum(abs(float(a) - float(b)) for a, b in zip(old, new))
    return value / 2.0 if half_l1 else value


def exposure_check(weights: Sequence[float], *, net: float | None = None,
                   gross: float | None = None, lower: float | None = None,
                   upper: float | None = None, tol: float = 1e-9) -> dict[str, Any]:
    w = _floats(weights, "weights")
    actual_net, actual_gross = sum(w), sum(abs(x) for x in w)
    checks = {
        "net": net is None or abs(actual_net - net) <= tol,
        "gross": gross is None or abs(actual_gross - gross) <= tol,
        "lower": lower is None or min(w) >= lower - tol,
        "upper": upper is None or max(w) <= upper + tol,
    }
    return {"ok": all(checks.values()), "net": actual_net, "gross": actual_gross,
            "checks": checks}


def normalize_weights(weights: Sequence[float], target: float = 1.0,
                      mode: str = "net") -> list[float]:
    w = _floats(weights, "weights")
    denominator = sum(w) if mode == "net" else sum(abs(x) for x in w)
    if mode not in {"net", "gross"} or abs(denominator) <= EPS:
        raise ValueError("invalid mode or zero normalization denominator")
    return [x * target / denominator for x in w]


def covariance_matrix(rows: Sequence[Sequence[float]], ddof: int) -> list[list[float]]:
    data = [list(map(float, row)) for row in rows]
    if not data or not data[0] or any(len(r) != len(data[0]) for r in data):
        raise ValueError("rows must be a nonempty rectangular observation matrix")
    n, k = len(data), len(data[0])
    if n <= ddof:
        raise ValueError("not enough observations for ddof")
    means = [sum(row[j] for row in data) / n for j in range(k)]
    return [[sum((row[i] - means[i]) * (row[j] - means[j]) for row in data) /
             (n - ddof) for j in range(k)] for i in range(k)]


def correlation_matrix(cov: Sequence[Sequence[float]]) -> list[list[float]]:
    m = [list(map(float, row)) for row in cov]
    n = len(m)
    if not n or any(len(row) != n for row in m):
        raise ValueError("covariance must be square")
    sd = [math.sqrt(max(0.0, m[i][i])) for i in range(n)]
    if any(x <= EPS for x in sd):
        raise ValueError("correlation undefined for zero variance")
    return [[m[i][j] / (sd[i] * sd[j]) for j in range(n)] for i in range(n)]


def matrix_diagnostics(matrix: Sequence[Sequence[float]], tol: float = 1e-10) -> dict[str, Any]:
    m = [list(map(float, row)) for row in matrix]
    n = len(m)
    square = n > 0 and all(len(row) == n for row in m)
    finite = square and all(math.isfinite(x) for row in m for x in row)
    sym_error = max((abs(m[i][j] - m[j][i]) for i in range(n) for j in range(n)),
                    default=math.inf) if finite else math.inf
    # Gershgorin is a conservative diagnostic, not an eigenvalue test.
    gershgorin_lower = min((m[i][i] - sum(abs(m[i][j]) for j in range(n) if j != i)
                            for i in range(n)), default=-math.inf) if finite else -math.inf
    return {"square": square, "finite": finite, "symmetric": sym_error <= tol,
            "symmetry_error": sym_error, "gershgorin_lower_bound": gershgorin_lower}


def quadratic_form(weights: Sequence[float], matrix: Sequence[Sequence[float]]) -> float:
    w = _floats(weights, "weights")
    m = [list(map(float, row)) for row in matrix]
    if len(m) != len(w) or any(len(row) != len(w) for row in m):
        raise ValueError("matrix/weight dimensions differ")
    return sum(w[i] * m[i][j] * w[j] for i in range(len(w)) for j in range(len(w)))


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _normal_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def black_scholes(spot: float, strike: float, maturity: float, rate: float,
                  sigma: float, kind: str = "call", dividend: float = 0.0) -> dict[str, float]:
    if spot <= 0 or strike <= 0 or maturity <= 0 or sigma <= 0:
        raise ValueError("spot, strike, maturity, and sigma must be positive")
    if kind not in {"call", "put"}:
        raise ValueError("kind must be call or put")
    root_t = math.sqrt(maturity)
    d1 = (math.log(spot / strike) + (rate - dividend + 0.5 * sigma ** 2) * maturity) / (sigma * root_t)
    d2 = d1 - sigma * root_t
    dq, dr = math.exp(-dividend * maturity), math.exp(-rate * maturity)
    if kind == "call":
        price = spot * dq * _normal_cdf(d1) - strike * dr * _normal_cdf(d2)
        delta = dq * _normal_cdf(d1)
    else:
        price = strike * dr * _normal_cdf(-d2) - spot * dq * _normal_cdf(-d1)
        delta = dq * (_normal_cdf(d1) - 1.0)
    gamma = dq * _normal_pdf(d1) / (spot * sigma * root_t)
    vega = spot * dq * _normal_pdf(d1) * root_t
    return {"price": price, "delta": delta, "gamma": gamma, "vega_per_unit_vol": vega,
            "d1": d1, "d2": d2}


def put_call_parity_residual(call: float, put: float, spot: float, strike: float,
                             maturity: float, rate: float, dividend: float = 0.0) -> float:
    return call - put - (spot * math.exp(-dividend * maturity) -
                         strike * math.exp(-rate * maturity))


def quantile(values: Sequence[float], probability: float, method: str = "linear") -> float:
    xs = sorted(_floats(values))
    if not 0 <= probability <= 1:
        raise ValueError("probability outside [0,1]")
    h = (len(xs) - 1) * probability
    lo, hi = math.floor(h), math.ceil(h)
    if method == "lower":
        return xs[lo]
    if method == "higher":
        return xs[hi]
    if method == "nearest":
        return xs[math.floor(h + 0.5)]
    if method == "midpoint":
        return (xs[lo] + xs[hi]) / 2.0
    if method == "linear":
        return xs[lo] + (h - lo) * (xs[hi] - xs[lo])
    raise ValueError("unsupported quantile method")


def historical_var_es(values: Sequence[float], confidence: float, *, input_kind: str,
                      method: str = "linear", include_var: bool = True) -> dict[str, float]:
    xs = _floats(values)
    if not 0 < confidence < 1 or input_kind not in {"return", "loss"}:
        raise ValueError("invalid confidence or input_kind")
    losses = [-x for x in xs] if input_kind == "return" else xs
    var = quantile(losses, confidence, method)
    tail = [x for x in losses if x >= var] if include_var else [x for x in losses if x > var]
    if not tail:
        raise ValueError("empty ES tail under selected inclusion rule")
    return {"var": var, "es": statistics.fmean(tail), "tail_count": len(tail)}


def normalize_probabilities(values: Sequence[float]) -> list[float]:
    p = _floats(values, "probabilities")
    if any(x < 0 for x in p) or sum(p) <= EPS:
        raise ValueError("probabilities must be nonnegative with positive sum")
    total = sum(p)
    return [x / total for x in p]


def transition_diagnostics(matrix: Sequence[Sequence[float]], tol: float = 1e-9,
                           absorbing_index: int | None = None) -> dict[str, Any]:
    m = [list(map(float, row)) for row in matrix]
    n = len(m)
    square = n > 0 and all(len(row) == n for row in m)
    finite = square and all(math.isfinite(x) for row in m for x in row)
    nonnegative = finite and all(x >= -tol for row in m for x in row)
    residuals = [sum(row) - 1.0 for row in m] if finite else []
    absorbing = True
    if absorbing_index is not None:
        absorbing = (0 <= absorbing_index < n and all(
            abs(m[absorbing_index][j] - (1.0 if j == absorbing_index else 0.0)) <= tol
            for j in range(n)))
    return {"ok": square and finite and nonnegative and
            max((abs(x) for x in residuals), default=math.inf) <= tol and absorbing,
            "square": square, "finite": finite, "nonnegative": nonnegative,
            "row_sum_residuals": residuals, "absorbing": absorbing}


def inclusive_window(dates: Sequence[str], start: str, end: str) -> list[int]:
    parsed = [dt.date.fromisoformat(str(x)[:10]) for x in dates]
    lo, hi = dt.date.fromisoformat(start[:10]), dt.date.fromisoformat(end[:10])
    if lo > hi or parsed != sorted(parsed):
        raise ValueError("invalid boundaries or unsorted dates")
    return [i for i, value in enumerate(parsed) if lo <= value <= hi]


def _native_finite(value: Any, path: str = "$") -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite JSON value at {path}")
        return value
    if isinstance(value, dict):
        return {str(k): _native_finite(v, f"{path}.{k}") for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_native_finite(v, f"{path}[{i}]") for i, v in enumerate(value)]
    if hasattr(value, "item"):
        return _native_finite(value.item(), path)
    if hasattr(value, "tolist"):
        return _native_finite(value.tolist(), path)
    raise TypeError(f"unsupported JSON type at {path}: {type(value).__name__}")


def write_json_strict(path: str | Path, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(_native_finite(value), handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def directory_fingerprint(path: str | Path) -> dict[str, str]:
    root = Path(path).resolve()
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def _is_missing(text: str) -> bool:
    return text.strip().lower() in {"", "na", "null", "none"}


def _csv_summary(path: Path) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        count, missing, nonfinite = 0, {c: 0 for c in columns}, {c: 0 for c in columns}
        first, last, samples = None, None, {c: set() for c in columns}
        for row in reader:
            count += 1
            first = first or row
            last = row
            for c in columns:
                text = row.get(c, "")
                if _is_missing(text):
                    missing[c] += 1
                else:
                    try:
                        if not math.isfinite(float(text)):
                            nonfinite[c] += 1
                    except ValueError:
                        if len(samples[c]) < 8:
                            samples[c].add(text)
    date_ranges = {}
    for c in columns:
        if "date" in c.lower() and first and last:
            date_ranges[c] = {"first": first.get(c), "last": last.get(c)}
    return {"kind": "csv", "rows": count, "columns": columns, "missing": missing,
            "nonfinite_numeric": nonfinite, "date_like_first_last": date_ranges,
            "categorical_samples": {c: sorted(v) for c, v in samples.items() if v}}


def _json_summary(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle, parse_constant=lambda x: (_ for _ in ()).throw(
            ValueError(f"invalid JSON constant {x}")))
    _native_finite(value)
    if isinstance(value, dict):
        return {"kind": "json", "type": "object", "keys": list(value),
                "value_types": {k: type(v).__name__ for k, v in value.items()}}
    if isinstance(value, list):
        return {"kind": "json", "type": "array", "length": len(value),
                "item_type": type(value[0]).__name__ if value else None}
    return {"kind": "json", "type": type(value).__name__}


def inspect_path(path: str | Path) -> dict[str, Any]:
    root = Path(path)
    paths = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    results = {}
    for item in paths:
        key = item.name if root.is_file() else item.relative_to(root).as_posix()
        try:
            if item.suffix.lower() == ".csv":
                results[key] = _csv_summary(item)
            elif item.suffix.lower() == ".json":
                results[key] = _json_summary(item)
            else:
                results[key] = {"kind": "file", "bytes": item.stat().st_size}
        except Exception as exc:  # diagnostics should report per-file errors
            results[key] = {"error": f"{type(exc).__name__}: {exc}"}
    return {"root": str(root), "files": results}


def validate_outputs(root: str | Path, required: Sequence[str]) -> dict[str, Any]:
    base, errors, summaries = Path(root), [], {}
    for name in required:
        path = base / name
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty: {name}")
            continue
        try:
            if path.suffix.lower() == ".json":
                summaries[name] = _json_summary(path)
            elif path.suffix.lower() == ".csv":
                summary = _csv_summary(path)
                if any(summary["nonfinite_numeric"].values()):
                    errors.append(f"non-finite numeric CSV value: {name}")
                summaries[name] = summary
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    return {"ok": not errors, "errors": errors, "summaries": summaries}


ROUTES = {
    "derivatives": ["black_scholes", "put_call_parity_residual", "matrix_diagnostics"],
    "pricing": ["black_scholes", "put_call_parity_residual"],
    "monte_carlo": ["sample_variance", "directory_fingerprint"],
    "fixed_income": ["matrix_diagnostics", "quadratic_form"],
    "portfolio": ["covariance_matrix", "exposure_check", "normalize_weights", "quadratic_form"],
    "risk": ["historical_var_es", "quantile", "covariance_matrix"],
    "credit": ["transition_diagnostics", "historical_var_es"],
    "hmm": ["normalize_probabilities", "transition_diagnostics"],
    "time_series": ["simple_returns", "log_returns", "annualized_volatility"],
    "events": ["inclusive_window"],
    "execution": ["turnover", "exposure_check"],
    "reporting": ["inspect_path", "validate_outputs", "write_json_strict"],
}
FEATURES = {
    "annualization": ["annualized_return", "annualized_volatility", "sharpe_ratio"],
    "covariance": ["covariance_matrix", "correlation_matrix", "matrix_diagnostics"],
    "gross_exposure": ["exposure_check", "normalize_weights", "turnover"],
    "convergence": ["directory_fingerprint"],
    "var": ["historical_var_es", "quantile"],
    "drawdown": ["cumulative_wealth", "max_drawdown"],
    "dates": ["inclusive_window"],
    "schema": ["inspect_path", "validate_outputs", "write_json_strict"],
}


def route(families: Sequence[str], features: Sequence[str], outputs: Sequence[str]) -> dict[str, Any]:
    helpers = []
    for key in list(families) + list(features):
        for helper in ROUTES.get(key, FEATURES.get(key, [])):
            if helper not in helpers:
                helpers.append(helper)
    delivery = ["validate_outputs", "write_json_strict", "directory_fingerprint"] if outputs else []
    for helper in delivery:
        if helper not in helpers:
            helpers.append(helper)
    return {
        "families": list(families), "features": list(features), "outputs": list(outputs),
        "helpers": helpers,
        "inputs_required": "Task data, explicit convention arguments, and required output schema",
        "uncertainty_reduced": ["delivery/schema", "units/conventions", "algebraic invariants",
                                "deterministic repeatability"],
        "stopping_condition": "All required artifacts parse, applicable invariants hold, deterministic rerun matches, and task tests pass",
        "misuse_warnings": ["Router does not select the financial model",
                            "Defaults never override task conventions",
                            "Generic checks do not replace a mandated algorithm"],
        "invariants": ["finite values", "shape/order agreement", "normalization constraints",
                       "date alignment", "cross-file reconciliation"],
    }


def _split_csv(value: str) -> list[str]:
    return [part.strip().lower() for part in value.split(",") if part.strip()]


def selftest() -> None:
    observed_returns = simple_returns([100, 110, 99])
    assert all(abs(a - b) < 1e-12 for a, b in zip(observed_returns, [0.1, -0.1]))
    assert abs(annualized_return([0.01] * 12, 12, "geometric") - (1.01 ** 12 - 1)) < 1e-12
    assert abs(max_drawdown([0.1, -0.2, 0.05]) - 0.2) < 1e-12
    cov = covariance_matrix([[1, 2], [2, 4], [3, 6]], 1)
    assert cov == [[1.0, 2.0], [2.0, 4.0]]
    c = black_scholes(100, 100, 1, 0.03, 0.2, "call")
    p = black_scholes(100, 100, 1, 0.03, 0.2, "put")
    assert abs(put_call_parity_residual(c["price"], p["price"], 100, 100, 1, 0.03)) < 1e-10
    assert transition_diagnostics([[0.9, 0.1], [0.2, 0.8]])["ok"]
    assert inclusive_window(["2024-01-01", "2024-01-02", "2024-01-03"],
                            "2024-01-01", "2024-01-02") == [0, 1]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    route_parser = commands.add_parser("route")
    route_parser.add_argument("--family", default="")
    route_parser.add_argument("--features", default="")
    route_parser.add_argument("--outputs", default="")
    inspect_parser = commands.add_parser("inspect")
    inspect_parser.add_argument("path")
    validate_parser = commands.add_parser("validate")
    validate_parser.add_argument("path")
    validate_parser.add_argument("--required", required=True)
    validate_parser.add_argument("--compare-command")
    commands.add_parser("selftest")
    args = parser.parse_args(argv)
    try:
        if args.command == "route":
            result = route(_split_csv(args.family), _split_csv(args.features),
                           [x.strip() for x in args.outputs.split(",") if x.strip()])
        elif args.command == "inspect":
            result = inspect_path(args.path)
        elif args.command == "validate":
            required = [x.strip() for x in args.required.split(",") if x.strip()]
            result = validate_outputs(args.path, required)
            if args.compare_command and result["ok"]:
                before = directory_fingerprint(args.path)
                completed = subprocess.run(args.compare_command, shell=True, check=False,
                                           text=True, capture_output=True, cwd="/app")
                after = directory_fingerprint(args.path)
                result["rerun"] = {"returncode": completed.returncode,
                                   "stdout_tail": completed.stdout[-2000:],
                                   "stderr_tail": completed.stderr[-2000:],
                                   "identical": before == after}
                result["ok"] = result["ok"] and completed.returncode == 0 and before == after
        else:
            selftest()
            result = {"ok": True, "tests": "embedded"}
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return 0 if result.get("ok", True) else 1
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
