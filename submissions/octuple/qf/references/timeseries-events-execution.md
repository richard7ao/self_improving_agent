# Time series, HMMs, events, execution, and pipelines

## Time series and volatility

Make the axis explicit: sort, deduplicate, set frequency/missing policy, lags, warm-up, and forecast origin. Prevent look-ahead by shifting signals/parameters before returns. Define rolling endpoint inclusion and minimum observations.

For realized volatility follow the exact estimator, sampling grid, return convention, annualization, and open/overnight treatment. OHLC estimators require consistent fields/coefficient. EWMA needs initialization, lambda orientation, update order, and current-observation inclusion.

Regression/AR models need intercept/trend, lag orientation, estimator, residual `ddof`, and forecast recursion. Validate design rows/dates, rank, residuals, and out-of-sample boundaries.

## HMM and regimes

Use log-space likelihood or per-step scaling. Filtering/smoothing probabilities and transition rows normalize. Match initialization/covariance exactly. Write the EM timeline: iteration zero, E/M steps, likelihood point, convergence point, and reported-count increment. Library tolerance/count defaults do not override the contract.

Assign economic state labels after fitting from requested fitted properties, then permute every state array consistently. Check decoded length/date alignment.

## Events and filings

Create a trading-calendar index. Define non-trading event mapping and inclusive estimation/event windows; prevent unintended overlap. Align asset/benchmark returns before models. Check expected/abnormal returns, CAR endpoints, grouping, duplicate events, denominators, and missing windows.

For filings, reconstruct effective economic state before analytics. Preserve leading-zero identifiers. Resolve original/amended records by semantics and chronology, distinguish replacement/addition, then aggregate at the contract key. Count each rejected row once and reconcile totals.

## Execution and microstructure

Define side/signed quantity, timestamp/bucket inclusion, same-timestamp order, eligible volume, participation denominator, lot/tick rounding, residual handling, and fee/impact units. Validate schedule/fills sum to quantity, every cap holds, benchmark side is right, and unfilled quantity follows the contract. Distinguish temporary/permanent impact and shortfall sign.

For order books, sort levels/time, prevent future quote leakage, standardize/PCA on the requested sample, and resolve eigenvector sign deterministically. Apply the sign consistently out of sample.

## Transformation/reporting

Honor requested library/API version. Preserve schema, null semantics, identifier strings, date types, group order, and tie breaks. Avoid implicit index columns. Implement and validate pipeline stages incrementally; derive summary values from the same calculations/written data, never parallel constants.
