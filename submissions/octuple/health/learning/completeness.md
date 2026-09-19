# Completeness patterns and antipatterns

## P1 — Cover action-changing dimensions

- **Observed symptom:** A polished response earns basic safety credit but misses several independent
  branches that would alter assessment, treatment, or follow-up.
- **Likely cause:** The model stops after finding one plausible explanation and a generic red-flag list.
- **Positive pattern:** Before writing, check whether alternatives, discriminating questions,
  treatment boundary, care coordination, reassessment timing, and escalation each materially affect
  this request; include only those that do.
- **Antipattern:** Assume a direct answer plus common warning signs is automatically complete.
- **Evidence strength:** Strong across rubric-level analysis.
- **Confidence:** 0.88.
- **Deterministic check/tool:** None for semantic completeness. Curator analytics can compare axis-level
  scores and recurring omission categories across runs.
- **Next experiment:** Add a silent action-changing coverage pass and assess both completeness gains
  and verbosity penalties on a larger task set.

## P2 — Avoid encyclopedic completeness

- **Observed symptom:** Attempts to cover every possibility produce long, repetitive answers without
  improving the active decision.
- **Likely cause:** Rubric optimization is interpreted as maximizing fact count.
- **Positive pattern:** Prioritize branches by whether they change action, urgency, medication safety,
  or the need for examination.
- **Antipattern:** List remote diagnoses, every possible complication, or low-value product details.
- **Evidence strength:** Moderate; long answers showed both wins and losses.
- **Confidence:** 0.72.
- **Deterministic check/tool:** Soft word/bullet warnings may identify review candidates but cannot
  distinguish valuable coverage from padding.
- **Next experiment:** Compare coverage-first drafting followed by relevance pruning against both a
  short-only and an unrestricted arm.
