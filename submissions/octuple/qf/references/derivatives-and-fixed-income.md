# Derivatives, simulation, FX, and fixed income

Use the exact requested method. Similar labels can hide different monitoring, rebates, settlement, smile-delta, compounding, or day-count definitions.

## Pricing

Write the timeline: valuation, observation, exercise, fixing, payment, settlement, endpoint inclusion, and discount time. State risk-neutral dynamics/numeraire, payoff direction, settlement, barrier monitoring, dividends/carry, and domains.

For Black–Scholes work, check finiteness, intrinsic/discounted bounds, put-call parity, spot/strike monotonicity, nonnegative vega, limiting cases, and finite-difference Greeks away from kinks. FX requires domestic/foreign rate roles, quote orientation, delta convention, premium inclusion/currency/units.

For path dependence, build the observation grid exactly and decide if time zero participates. Do not confuse arithmetic and geometric averages. Barrier inequalities and bridge correction follow the contract.

## Monte Carlo

Use the specified RNG API, seed, path/step count, discretization, variance reduction, and draw order. Seed once. Discount once. Standard error is the requested payoff standard deviation divided by `sqrt(n)`, with the requested `ddof`.

Validate nested cases: zero jumps/correlation, European payoff, analytic geometric average, or increased paths. Reproducible noise is not correctness; compare discrepancies to SE and inspect bias. For jumps distinguish count/size and multiple jumps; compensate drift only when required. For stochastic volatility use the stated variance scheme and correlation construction.

## Lattices and PDEs

Match node/time indexing, exercise timing, probabilities, discounting, dividends, and terminal/boundary rules. Check transition probabilities, exact terminal payoff, and American/Bermudan dominance where applicable. For finite differences state grids and iteration semantics, independently verify boundaries and stability. Never replace a mandated tree/PDE with a closed form.

## Curves and fixed income

Lock price/yield, clean/dirty, accrued interest, discount/zero/forward, compounding, day count, business-day adjustment, interpolation variable, and schedules. Bootstrap sequentially and reprice every input. Require positive discount factors and tiny repricing residuals. Distinguish discount and projection curves. Verify value/duration/convexity constraints in optimizer units.

FX forwards require explicit base/quote orientation. Reciprocal bid/ask swaps sides. Apply CIP with each currency's day count and rate units; convert pips/points only at output. Cross bid/ask paths represent executable directions, not mid-rate algebra.
