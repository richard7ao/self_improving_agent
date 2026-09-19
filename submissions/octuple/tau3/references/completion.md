# Completion and transfer

Use this reference when the immediate action is finished, the request cannot be completed, or the customer asks for a human.

## Resolution audit

Before ending, check:

- each active intent has an answer or verified completed action;
- required KB facts were retrieved rather than guessed;
- protected work followed logged authentication;
- each mutation's result confirms its actual status;
- no required customer confirmation or self-service step is still pending;
- the customer has received a concise outcome and any supported next step.

Do not ask a generic “anything else?” merely to delay closure. If a necessary user-side tool action is pending, continue the conversation and interpret its returned activity. If resolved, call `end_conversation` exactly once.

## Human transfer

First retrieve and obey scenario-specific transfer guidance; it overrides the general route.

Otherwise:

- If the issue may be solved with available policy or tools, explain briefly that you can help and attempt it before transferring.
- If the issue truly cannot be resolved within capability, ask whether the customer wants a human transfer. Transfer only after consent.
- Track explicit human-agent requests. When the matter is within capability, the general policy permits transfer after the fourth explicit request unless retrieved guidance says otherwise.
- Use only the exact supported transfer tool and inspect its result. Do not claim the transfer succeeded unless confirmed.

Do not use transfer to bypass retrieval, authentication, confirmation, or an available action. Do not keep troubleshooting after a confirmed transfer.

## Interrupted and multi-intent conversations

When the customer changes topics, preserve completed checkpoints and add the new intent to the ledger. Clarify priority only when the intents conflict. A conversation is resolved only when every remaining intent has been addressed or the customer has explicitly withdrawn it.
