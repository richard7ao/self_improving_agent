# Engineering and physics adapter

Define the system boundary, knowns, unknowns, reference frame, sign convention, and
boundary/initial conditions. Choose and justify governing laws, construct equations,
solve, then check dimensions, signs, conservation, scale, residuals, and limiting
behavior.

Use `scripts/engineering_check.py` for unit conversion, dimension comparison,
force/moment or mass/energy balance, residuals, uncertainty propagation, and boundary
evaluation. Use `matrix_check.py` for justified linear systems, circuits, determinants,
and ranks. Attack RMS versus peak, degree versus radian, gauge versus absolute, series
versus parallel, steady versus transient, singular systems, impossible scale, and
conservation failures. Tools do not select the physical model.
