# Treatment-decision patterns and antipatterns

## T1 — Separate decision authority from information usefulness

- **Observed symptom:** The assistant correctly says it cannot prescribe, but then rejects records or
  other information that could support a more useful discussion.
- **Likely cause:** Safety limitations are framed as refusal instead of calibrated assistance.
- **Positive pattern:** Invite a focused set of relevant information, explain what it can clarify,
  help organize questions and tradeoffs, and reserve the final treatment decision for the clinician.
- **Antipattern:** Say that more information cannot help because the assistant cannot make the final
  decision.
- **Evidence strength:** Strong; this policy difference tracked a large paired score movement.
- **Confidence:** 0.93.
- **Deterministic check/tool:** A surface checker may flag blanket refusal phrases for review, but it
  cannot establish whether additional context is clinically useful.
- **Next experiment:** Isolate one prompt sentence distinguishing “interpret” from “decide” and run a
  paired context-seeking evaluation.

## T2 — Focus on decision factors and time horizon

- **Observed symptom:** Treatment answers drift into broad therapy lectures or unsupported medication
  changes instead of addressing urgency and the upcoming decision.
- **Likely cause:** Medical knowledge retrieval displaces user-centered planning.
- **Positive pattern:** Answer whether action appears immediate or planned, cite the few supplied trends
  that support that timing, name the remaining decision factors, and specify who should decide.
- **Antipattern:** Enumerate treatment classes, choose a prescription, or imply that one result settles
  the choice.
- **Evidence strength:** Moderate to strong.
- **Confidence:** 0.84.
- **Deterministic check/tool:** Medication-directive regexes can warn about explicit imperatives, but
  false positives require human/model review.
- **Next experiment:** Compare a four-part decision response against unrestricted explanation on fresh
  treatment-choice tasks.
