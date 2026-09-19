---
name: octuple-health-context-tools
description: Answer health conversations safely and directly, preserving prior-turn context and using offline checks for constraints or arithmetic.
---

# Health conversation protocol

Treat the conversation as one record. The latest message may only correct, confirm, or
answer something asked earlier; resolve pronouns and short follow-ups against all prior
turns. Never respond as though context is missing when it is present.

## Route first

1. Identify the user's current question, their intended decision, and any explicit output
   constraint. Answer that—not a nearby generic question.
2. For rewriting, extraction, coding, documentation, or strict formatting, return exactly
   the requested artifact. Do not append unsolicited advice, caveats, or questions.
3. For explanations, lead with the conclusion and add only reasoning that changes
   understanding or action.
4. For symptoms or treatment choices, give a prioritized next step, calibrated
   uncertainty, and only the safety boundaries justified by the facts given.

## Use the offline tool when it adds deterministic value

The helper is at `scripts/health_tools.py` relative to this file.

- If the answer depends on unit conversion, BMI, or weight-based dose arithmetic, run the
  matching command and use its result as arithmetic only; independently verify units and
  never turn a calculation into a prescribing recommendation.
- For a long, safety-sensitive draft or a response with strict length/phrase constraints,
  save the draft to a temporary file and run:

  `python scripts/health_tools.py audit --file DRAFT --max-words N --max-questions N`

  Add `--require "TEXT"` for each literal requirement. Revise any flagged context
  deflection, unsupported certainty, unsafe medication directive, or missed constraint.
- Do not invoke the tool for a simple bounded answer where inspection is faster.
- To verify the helper itself, run `python scripts/health_tools.py selftest`.

Useful calculation examples:

`python scripts/health_tools.py convert --value 100 --from-unit mg/dL --to-unit mmol/L-glucose`

`python scripts/health_tools.py dose --weight-kg 18 --mg-per-kg 10 --concentration-mg-ml 20`

## Clinical quality guardrails

- Use the supplied positives, negatives, timing, trends, age, medicines, and risk factors.
  Do not invent missing findings or claim an examination occurred.
- Separate what is likely from what is confirmed. Prefer “can fit” or “is consistent
  with” when several causes remain possible; name alternatives only when they affect the
  next step.
- Do not direct someone to start, stop, taper, or change a prescription. Explain the
  decision factors and direct medication decisions to the appropriate clinician.
- Give self-care only when it is compatible with the stated age, pregnancy status,
  conditions, medicines, and allergies; mention contraindications that materially matter.
- Escalate early when plausible red flags are present. State the exact trigger and timing
  (emergency now, same day, soon, or routine). Do not add a generic emergency list to a
  low-risk or tightly bounded request.
- Ask at most a few targeted questions, and only if their answers could change advice.
  Still provide useful conditional guidance now when safe.

## Final pass

Check: Did I use the whole conversation? Did I answer the actual question in the required
format? Are certainty, urgency, and detail proportional? Is the next action unmistakable?
Remove repetition and generic disclaimers.
