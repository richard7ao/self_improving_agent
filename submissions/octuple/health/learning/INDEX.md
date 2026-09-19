# Health skill learning library

This library stores reusable behavioral findings from public training runs. It contains no task
text, identifiers, patient facts, answer excerpts, reference answers, or rubric wording. Evidence
strength reflects repeated observations, not held-out certainty.

## Topics

- [Delivery](delivery.md): response-file execution, turn use, focus, and length.
- [Context reconstruction](context-reconstruction.md): deciding whether context is sufficient and
  resolving follow-up turns.
- [Symptom guidance](symptom-guidance.md): actionable, proportionate advice for symptom questions.
- [Treatment decisions](treatment-decisions.md): helping without prescribing or refusing useful data.
- [Bounded artifacts](bounded-artifacts.md): exact-format and transformation requests.
- [Completeness](completeness.md): covering action-changing dimensions without encyclopedic output.
- [Uncertainty](uncertainty.md): calibrating claims, limitations, and conditional guidance.
- [Tool use](tool-use.md): when deterministic offline checks repay an agent turn.

## Entry schema

Every entry records: observed symptom, likely cause, positive pattern, antipattern, evidence strength,
confidence, deterministic check/tool if any, and next experiment. Entries should be updated only from
aggregate, cross-task evidence. Disease-specific facts and evaluator-specific phrase matching do not
belong here.
