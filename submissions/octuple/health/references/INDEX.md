# Health reference router

Load only the reference needed for the active response mode. Usually one file is enough;
combine two only when both modes materially apply.

| Mode | Reference | Use when |
|---|---|---|
| New or changing symptom | `symptom-assessment.md` | The user wants likely meaning, self-care, urgency, or next steps. |
| Choosing among care options | `treatment-decisions.md` | Benefits, burdens, alternatives, timing, or shared decisions are central. |
| Any medicine or supplement | `medication-safety.md` | Starting, stopping, changing, combining, monitoring, or adverse effects are discussed. |
| Child or adolescent | `pediatric-assessment.md` | Age, development, weight, caregiver observations, or pediatric safeguards matter. |
| Test, scan, or clinical result | `tests-and-results.md` | The user wants interpretation, certainty, trends, or follow-up testing. |
| Fragmentary or missing context | `sparse-context.md` | The latest turn is short, ambiguous, or the record lacks decision-critical facts. |
| Rewrite, note, extraction, or exact format | `bounded-artifacts.md` | The requested output is an artifact rather than open-ended advice. |
| Final coverage and file delivery | `completeness-delivery.md` | A complex answer needs a final audit or must be written to a required path. |

Routing principles:

- The user's explicit format overrides the default response shape.
- Do not load symptom or escalation guidance for a purely bounded artifact unless requested.
- `medication-safety.md` supplements, but does not replace, the main response mode.
- `completeness-delivery.md` is a final audit, not a reason to lengthen a simple answer.
- References organize reasoning; none supplies a diagnosis, prescription, or current rule.
