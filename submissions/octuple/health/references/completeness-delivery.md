# Completeness and delivery

## Facts to extract

- Active question, required output, destination path, and every explicit constraint.
- Decision-relevant facts, stated unknowns, requested actions, and required follow-up.
- Whether a deterministic validation or delivery tool is available and warranted.

## Unknowns not to invent

- That a fluent answer is complete, medically correct, or successfully written.
- That tool success validates semantics.
- A destination, filename, format, or section that was not requested.

## Discriminating questions

Before finalizing, ask internally: What decision must this answer support? Which supplied
fact changes that decision? What action and timing are expected? What explicit constraint
could be checked mechanically? Ask the user only if a missing choice blocks safe completion.

## Coverage checklist

- Answer the active request, not just the general topic.
- Cover relevant facts, uncertainty, action, and proportionate contingency.
- Remove repetition, generic disclaimers, and unrelated safety text.
- Verify literal, count, and section constraints when explicitly requested.
- For required file delivery, confirm the file exists, is nonempty, and exactly matches
  the approved draft.

## Actions

Revise semantic gaps manually. Use deterministic tools only for objective form and delivery.
Write atomically when possible, then read back and compare bytes. Treat any nonzero tool
exit or mismatch as failure; repair and rerun rather than assuming delivery succeeded.

## Escalation and follow-up

Include escalation and follow-up only when relevant to the health request or requested
artifact. Ensure timing is explicit without inventing thresholds or universal rules.

## Common failure modes

- Producing a good draft but failing to deliver it to the required path.
- Overwriting the draft before validation or leaving a partial file after failure.
- Passing a form checker while omitting the user's actual question.
- Adding completeness padding that reduces relevance.
- Claiming a checklist or regex establishes clinical safety.
