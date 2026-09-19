# Context-reconstruction patterns and antipatterns

## C1 — Classify context sufficiency before answering

- **Observed symptom:** A sparse message receives an assumed diagnosis and management advice before
  the user's actual concern is established.
- **Likely cause:** The model tries to be immediately helpful and overweights a single medical term.
- **Positive pattern:** State the most reasonable interpretation briefly, ask one to three questions
  that could change urgency or next action, and add only a compact conditional safety boundary.
- **Antipattern:** Build a full differential or treatment plan around an inferred condition.
- **Evidence strength:** Strong within context-poor examples and consistent with broader dataset
  categorization.
- **Confidence:** 0.89.
- **Deterministic check/tool:** No reliable semantic checker. A curator can count questions, but only
  model judgment can decide whether they are informative.
- **Next experiment:** Ablate “infer then ask” versus “ask then conditionally help” on context-poor
  tasks selected independently of candidate generation.

## C2 — Use earlier turns before declaring context missing

- **Observed symptom:** A short follow-up is treated as a new conversation even though it answers an
  earlier question or modifies prior information.
- **Likely cause:** Recency bias and over-literal processing of the final message.
- **Positive pattern:** Silently reconstruct the unresolved question and classify the latest turn as
  confirmation, denial, correction, or new request.
- **Antipattern:** Ask the user to repeat information already present or acknowledge a fragment without
  connecting it to the active decision.
- **Evidence strength:** Moderate to strong across candidate comparisons.
- **Confidence:** 0.86.
- **Deterministic check/tool:** A text checker cannot validate semantic continuity safely.
- **Next experiment:** Use synthetic multi-turn conversations to test pronoun and correction handling,
  then confirm with paired benchmark evaluation.
