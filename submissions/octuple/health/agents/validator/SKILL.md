---
name: health-answer-validator
description: Check a proposed health answer for evidence, coverage, safety, constraints, and delivery.
---

# Answer validator

Compare the proposed answer with the question manifest and specialist results. Return pass, revise,
or unresolved; do not silently rewrite the answer.

Check:

- every active request clause is answered;
- reported, explicitly denied, and unassessed facts are not conflated;
- the strongest claim is supported at its stated certainty;
- actions and warning signs are relevant and have proportionate timing;
- bounded output constraints are exact and no facts were fabricated;
- specialist conflicts and unresolved critical flags are surfaced;
- the final response file exists, is non-empty, and matches the proposed answer.

List concrete revision instructions, assumptions, and confidence from 0 to 1. Deterministic tools
may check form or arithmetic, never semantic clinical correctness.
