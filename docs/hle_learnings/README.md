# HLE learning log

This folder records reusable lessons from public HLE training evaluations. It is
development evidence, not part of the submitted skill.

## Integrity rules

- Record behavioral patterns, aggregate metrics, and causal hypotheses.
- Do not copy question text, patient or image details, canonical answers, grader
  prompts, rubrics, or task-to-answer mappings.
- Link evidence by ignored run directory and arm; keep raw trajectories in `runs/`.
- Distinguish an observed fact from an inference.
- A single binary result is a case study, not proof of general improvement.
- Promote a lesson into `submissions/octuple/hle/references/` only when it is
  general, reusable, and explicitly routed from `SKILL.md`.

## Per-experiment procedure

After every correct or incorrect judged response:

1. Record delivery, score, answer type, token/cost totals, and stopping behavior.
2. Identify the earliest decision that determined success or failure.
3. Add one pattern (repeat) or antipattern (prevent), with supporting evidence.
4. State a falsifiable intervention and expected score/token effect.
5. Test candidates on the same fixed tune tasks.
6. Validate only the strongest strict improvement on fresh tasks.

See `patterns.md` for the current catalog and `experiments.md` for chronological
evidence.
