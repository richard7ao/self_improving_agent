# Uncertainty patterns and antipatterns

## U1 — Express a boundary without refusing the task

- **Observed symptom:** The answer spends its opening explaining why certainty is impossible and
  delays or omits the useful interpretation the user requested.
- **Likely cause:** Safety calibration is implemented as a generic limitation statement.
- **Positive pattern:** State the practical conclusion, identify its evidence level, explain the one
  limitation that matters, and continue with useful conditional guidance.
- **Antipattern:** Lead with role disclaimers or make inability to guarantee certainty the whole answer.
- **Evidence strength:** Strong across treatment and context-seeking comparisons.
- **Confidence:** 0.91.
- **Deterministic check/tool:** Generic-disclaimer phrases can be flagged for review; whether a
  limitation is necessary remains semantic judgment.
- **Next experiment:** Compare conclusion-first calibration against disclaimer-first responses while
  tracking context-awareness and instruction-following axes.

## U2 — Attach uncertainty to the claim and action

- **Observed symptom:** Hedge words appear, but the recommended action remains overconfident or lacks
  conditions that would change it.
- **Likely cause:** Lexical hedging substitutes for reasoning about evidence.
- **Positive pattern:** Use “possible,” “likely,” or “confirmed” consistently, then state what evidence
  or symptom change would move the recommendation.
- **Antipattern:** Add “probably” to a definitive diagnosis or use reassurance without an examination
  boundary.
- **Evidence strength:** Moderate to strong.
- **Confidence:** 0.85.
- **Deterministic check/tool:** No safe automated clinical check; absolute-phrase detection is warning
  only.
- **Next experiment:** Test a claim-evidence-action audit on fresh tasks and manually classify false
  reassurance versus excessive caution.
