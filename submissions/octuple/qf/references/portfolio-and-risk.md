# Portfolio, factor, attribution, and risk

## Returns and portfolios

Sort by date/asset. Lock simple/log returns, missing policy, signal-to-return lag, price/total return, and pre/post-return weights. Align by keys/dates with validated joins, not row order. Annualize once.

Check wealth recursion, turnover definition (including optional `1/2`), cost units, rebalance dates, and drawdown sign. Regressions must match dates and intercept rules; distinguish residual from total volatility.

Before optimization check matrix dimensions/order, symmetry, finiteness, eigenvalues/conditioning, and `ddof`. Repair covariance only if allowed. State net, gross, bound, factor, turnover, target-return/risk, and shorting constraints algebraically. Check solver success and recompute residuals. Post-normalization can break constraints.

Distinguish risk parity from inverse volatility. In Black–Litterman preserve orientation and distinguish prior mean, views, view uncertainty, posterior mean, and posterior covariance. Attribution components must reconcile under the named convention.

## VaR and ES

Prefer internal positive loss `L=-R` and document conversions. `VaR_alpha` is a loss quantile; ES averages the contract-defined loss tail. Follow exact quantile interpolation and threshold inclusion. Do not mix a 1% return quantile with 99% loss confidence.

Match mean inclusion, horizon scaling, covariance frequency, distribution, and degrees of freedom. Component contributions must sum to total risk. EVT/POT needs explicit loss tail, threshold/excess, exceedance fraction, GPD parameterization, and extrapolation probability; validate the shape domain.

## Credit and dependence

Transition rows are nonnegative and sum to one in declared state order. Keep default/recovery signs explicit and validate aggregation, horizon, migration value, correlation, and percentile method.

For copulas, use specified plotting positions, clip only for numerical necessity, preserve variable order, and validate correlation. Rank-correlation conversions are family-specific. A t-copula uses shared mixing; its likelihood subtracts marginal t densities.

## Invariants

- net/gross exposure and all constraints hold;
- covariance/correlation/posterior order, symmetry, diagonal, and conditioning are valid;
- return, attribution, and risk contributions reconcile;
- probabilities and credit transitions normalize;
- loss-tail VaR/ES use correct sign/inclusion (normally ES is at least VaR);
- deterministic optimization repeats and exposes status/residuals.
