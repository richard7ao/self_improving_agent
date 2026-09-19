# Symptom-guidance patterns and antipatterns

## S1 — Use a compact action ladder

- **Observed symptom:** Answers contain reasonable facts but leave the user unsure what to do now,
  when to arrange assessment, or what would make the situation urgent.
- **Likely cause:** The response organizes around medical explanation rather than the user's decision.
- **Positive pattern:** Give the likely category with calibrated language, reasonable care now,
  reassessment timing, and a short list of observable changes that increase urgency.
- **Antipattern:** Provide an unprioritized differential followed by a generic emergency disclaimer.
- **Evidence strength:** Strong across symptom-focused responses.
- **Confidence:** 0.87.
- **Deterministic check/tool:** Section presence can be checked only if the user requested headings;
  the clinical content and urgency cannot be automated safely.
- **Next experiment:** Compare explicit “now / follow-up / urgent” planning with an unstructured answer,
  while allowing natural prose in the final response.

## S2 — State what could invalidate home care

- **Observed symptom:** A plausible low-risk explanation becomes categorical reassurance even though
  key examination findings were never assessed.
- **Likely cause:** Pressure to answer directly is interpreted as pressure to eliminate uncertainty.
- **Positive pattern:** Give a conditional home-care plan and identify the few missing findings that
  would require prompt examination or a different treatment path.
- **Antipattern:** Declare treatment unnecessary or observation safe without naming the boundary of
  that conclusion.
- **Evidence strength:** Strong in rubric-level penalty analysis.
- **Confidence:** 0.90.
- **Deterministic check/tool:** None; keyword hedging is not a valid proxy for clinical calibration.
- **Next experiment:** Add one instruction to pair each home-care recommendation with its invalidating
  conditions and measure completeness and false-alarm effects.
