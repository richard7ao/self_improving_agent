# Tool discovery and safe actions

Use this reference when the customer's request may require a discoverable user tool, a discoverable agent tool, or any state-changing operation.

## Discover first

Search the KB for the action and its procedure. Extract only what the result explicitly establishes:

- permitted and prohibited actions;
- prerequisites and required confirmation;
- exact tool name and whether it is user-side or agent-side;
- required arguments and their meanings;
- authentication requirement;
- exceptions or escalation path.

Never infer a tool name from naming conventions.

## User discoverable tool

Use this route only when the KB says the customer must perform the action:

1. Confirm that the customer wants that action.
2. Call `give_discoverable_user_tool` with the exact KB-discovered name. Do not give unrelated tools.
3. In the next customer message, explain its purpose and the grounded arguments the customer should provide.
4. Process the returned user response and any user-side tool activity. Inspect the resulting state or response before deciding that the action is complete.

Giving a tool is an action; merely naming it is not. Conversely, do not give it if it will not actually be used.

## Agent discoverable tool

Use this route only when the KB explicitly assigns the action to the agent:

1. Satisfy policy, authentication, confirmation, and argument prerequisites.
2. Call `unlock_discoverable_agent_tool` with the exact discovered name only when ready to use it.
3. Inspect the unlocked parameter contract.
4. Call `call_discoverable_agent_tool` once with grounded arguments matching that contract.
5. Inspect the result before communicating an outcome.

Never unlock speculatively, guess arguments, or substitute a similarly named tool.

## Mutation safety

For disputes, profile or account changes, transfers, closures, payments, and similar mutations, establish the correct customer and target object plus every required amount, date, reason, destination, and confirmation before calling.

After a call:

- success: checkpoint it and never repeat it;
- refusal or ineligibility: do not describe it as completed;
- invalid or missing argument: obtain the specific grounded value before retrying;
- partial completion: preserve what succeeded and handle only the remainder;
- ambiguous or temporary failure: do not blindly retry an irreversible call; retrieve or escalate according to policy.

Tool output overrides plans, customer assumptions, and prior conversational wording.
