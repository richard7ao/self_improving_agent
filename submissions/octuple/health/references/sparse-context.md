# Sparse or fragmentary context

## Facts to extract

- The unresolved question from earlier turns and what the latest fragment modifies.
- Medical terms, negations, pronouns, timing words, and implied answer to a prior question.
- Any explicit goal, requested format, or decision that remains active.
- Whether context is truly absent or merely brief.

## Unknowns not to invent

- The topic of a fragment when multiple interpretations are equally plausible.
- Symptoms, diagnoses, history, or user intent not supported anywhere in the exchange.
- That a short reply starts a new topic or cancels earlier constraints.

## Discriminating questions

First infer the most likely connection to the prior exchange. Ask one concise clarification
only if competing interpretations would produce meaningfully different or unsafe advice.
When safe, state the interpretation and provide a conditional answer before asking.

## Coverage checklist

- Resolve the latest message against the complete conversation.
- Carry forward relevant positives, negatives, preferences, and format constraints.
- Answer the likely active question rather than narrating missing context.
- Mark the inference briefly and keep it reversible.
- Avoid restating questions the user already answered.

## Actions

Use: “If you mean X, then Y; if you mean Z, clarify…” only when ambiguity matters. If one
interpretation clearly dominates, answer it directly and invite correction without making
the user repeat the full history.

## Escalation and follow-up

If ambiguity could conceal an urgent situation, ask about the decision-critical warning
feature while giving the safest immediate action. Otherwise keep clarification proportionate.

## Common failure modes

- Saying earlier context is unavailable when it is visible.
- Treating a denial or confirmation as a standalone request.
- Hallucinating a detailed scenario from one term.
- Asking the user to repeat everything before providing help.
- Dropping an earlier output constraint on the final turn.
