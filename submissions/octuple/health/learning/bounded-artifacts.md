# Bounded-artifact patterns and antipatterns

## B1 — Treat the requested artifact as the entire output

- **Observed symptom:** A rewrite, note, extraction, or formatted deliverable is followed by
  unsolicited clinical commentary or questions.
- **Likely cause:** General health-safety prompting overrides explicit output boundaries.
- **Positive pattern:** Preserve supplied facts and return only the requested artifact in its requested
  voice and structure.
- **Antipattern:** Append disclaimers, escalation advice, headings, or a second explanation that the
  user did not request.
- **Evidence strength:** Strong from the dataset-level constraint census; limited direct evidence in
  the three runtime tasks.
- **Confidence:** 0.88.
- **Deterministic check/tool:** Required/forbidden literals, prefix/suffix, counts, and user-supplied
  section checks are appropriate.
- **Next experiment:** Evaluate bounded tasks with and without an explicit “artifact only” routing rule
  and record format violations separately from medical score.

## B2 — Never invent a default schema

- **Observed symptom:** A checker or prompt forces headings and fields not requested by the user.
- **Likely cause:** Reusable templates are mistaken for universal clinical documentation standards.
- **Positive pattern:** Pass only user-specified sections to the checker; preserve omission when the
  source lacks a fact.
- **Antipattern:** Require a fixed medical-note schema or fill absent fields with guesses.
- **Evidence strength:** Strong safety rationale; moderate observed coverage.
- **Confidence:** 0.91.
- **Deterministic check/tool:** Ordered-section validation is safe when headings are explicit inputs.
- **Next experiment:** Add synthetic missing, duplicate, empty, and out-of-order section fixtures to
  the checker regression suite.
