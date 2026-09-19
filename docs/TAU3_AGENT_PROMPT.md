# TAU3 agent prompt

Copy the prompt below into the agent session responsible for τ³-bench.

---

Build and optimize the TAU3 submission for the fixed banking customer-service learner.

The local public set contains 67 banking scenarios. TAU3 is a stateful conversation and
tool-use benchmark:

- The learner has 100 iterations.
- A simulated customer responds after agent messages and user-side tool activity.
- Policy compliance, authentication, tool ordering, database state, and communicated
  information are graded.
- A plausible final message is insufficient if the required actions or state changes are
  wrong.
- Never invent policy, customer data, tool results, tool names, or actions.

Build broadly first. Reduce the skill only after experiments identify dead weight.

## Scope and repository discipline

Start with:

```bash
git status --short --branch
uv run stbench doctor
```

Read completely:

- `AGENTS.md`
- `README.md`
- `richard_metholody.md`
- `docs/TEAMMATE_GUIDE.md`
- the complete current `submissions/octuple/tau3/`
- the TAU3 policy and tool protocol in representative public task instructions
- all completed TAU3 run artifacts and relevant trajectories

Inspect public training metadata only to identify general scenario families and failure
classes. Never encode task text, customer details, expected actions, assertions,
reference outcomes, tool-call mappings, or answer keys into the submission.

Work only on `submissions/octuple/tau3/`, TAU3-specific tests/documentation when
required, and isolated ignored candidate folders under `runs/`. Do not edit other
submissions, `.env`, datasets, `hackathon.toml`, the learner, runtime server, graders,
tests, or shared harness code without explicit authorization.

Preserve concurrent work. Stage exact paths only. Never use `git add .`, `git add -A`,
or `git commit -a`. Submitted scripts must run offline without credentials, network
access, external APIs, or external LLMs.

## Objective

Create a general TAU3 skill that makes the learner reliably:

1. Start or resume the conversation exactly once.
2. Identify the customer's actual goal and current conversation state.
3. Search the knowledge base when policy or tool availability is needed.
4. Authenticate only when accessing or modifying customer-specific information.
5. Never disclose customer information before successful verification.
6. Unlock only explicitly discovered agent tools that will actually be used.
7. Give only explicitly discovered user tools that the customer needs.
8. Respect tool prerequisites, confirmations, and call ordering.
9. Treat tool responses as the only truth about external state.
10. Confirm the case is actually resolved, communicate the outcome, and end correctly.

The competition metric is `skill pass rate - placebo pass rate`.

## Non-negotiable interaction protocol

Put these rules prominently in `SKILL.md`:

- Call `start_conversation` exactly once at the beginning.
- In each step, either send a user message or call one domain tool; never combine both.
- Use `send_message_to_user` for customer-facing communication and process the returned
  next customer message before acting again.
- End only after resolution, using the supported conversation-ending mechanism.
- Do not emit internal policy, hidden state, database details, or chain-of-thought.
- Do not claim an action succeeded until its tool result confirms success.
- Do not repeat irreversible or state-changing calls after success.
- Do not unlock speculative tools.

## Core state machine

Use a compact internal state ledger:

```text
conversation_started
customer_goal
scenario_family
knowledge_needed
identity_required
identity_verified_and_logged
customer_confirmation_required
tool_discovered
tool_unlocked
action_attempted
action_result
remaining_requirement
transfer_requested_count
resolved
```

Then follow:

```text
start once
→ understand goal
→ distinguish general information from account-specific access/action
→ search policy/KB when needed
→ authenticate if and only if required
→ obtain missing decision-changing facts or confirmation
→ discover/unlock the exact permitted tool
→ execute once
→ inspect result and update state
→ communicate the actual outcome
→ resolve or offer policy-compliant escalation
→ end
```

Do not turn the ledger into a long user-visible checklist or spend actions writing large
scratch artifacts.

## Knowledge-only requests

For general policy or product information:

- do not authenticate unnecessarily;
- search the KB with focused terms;
- answer only from retrieved policy;
- distinguish eligibility, process, timing, fees, limits, and exceptions;
- say when information is unavailable;
- do not perform or unlock actions the customer did not request.

## Authentication

Authenticate before accessing or modifying customer-specific records. Do not
authenticate merely to answer general information.

Follow the task policy exactly. Under the current banking policy, verification normally
requires the customer to correctly provide any two permitted values among date of birth,
email, phone number, and address, followed by the required verification logging call.

Never:

- reveal known values for the customer to confirm;
- count name or user ID as sufficient when policy excludes them;
- access private records before verification;
- skip verification logging;
- verify repeatedly after successful logged verification;
- request documents unless the KB explicitly authorizes the process.

If the user supplies insufficient or incorrect information, request only what is still
needed without leaking stored values.

## Knowledge-base search

Search when policy, eligibility, procedure, limits, transfer guidance, or discoverable
tools are uncertain. Use concise targeted queries and refine once if the first result is
insufficient. Extract:

- permitted and prohibited actions;
- prerequisites;
- exact tool names;
- required arguments;
- whether the tool is agent-side or user-side;
- confirmation or authentication requirements;
- exceptions and escalation conditions.

Do not search repeatedly after the decisive policy has been found.

## Discoverable user tools

Give a user tool only when:

- the customer wants the corresponding action;
- the KB explicitly identifies that exact tool;
- it is the appropriate self-service route;
- you will explain its purpose and required arguments.

Call `give_discoverable_user_tool` with the exact discovered name. Merely mentioning a
tool is insufficient. Do not unlock or give unrelated tools.

## Discoverable agent tools

For an agent-side discoverable tool:

1. Find the exact tool name in the KB.
2. Confirm the requested action and all prerequisites.
3. Authenticate and obtain confirmation when required.
4. Unlock that exact tool.
5. Inspect its parameter contract.
6. Call it once with grounded arguments.
7. Inspect the result before communicating success.

Never guess tool names or arguments. Never unlock a tool that will not be used.

## State-changing actions

Before mutations such as disputes, account changes, transfers, closures, or payment
actions, check:

- correct customer and object;
- successful logged verification;
- policy eligibility;
- required customer confirmation;
- exact amount, account, transaction, date, and reason;
- duplicate-action risk;
- whether a prior attempt already succeeded.

After the call, distinguish success, refusal, missing prerequisite, invalid arguments,
temporary failure, and partial completion. Never tell the customer an action succeeded
when the tool says otherwise.

## Clarification and communication

Ask only questions whose answers change the next policy decision or tool arguments.
Keep customer messages concise, professional, and action-oriented. Do not expose
internal policy text or intermediate processing. When a tool fails, explain the
customer-relevant consequence and the next permitted step without inventing a cause.

## Transfers

Transfer only under the active policy. Generally:

- exhaust permitted actions first;
- ask whether the customer wants transfer when the issue truly cannot be resolved;
- do not transfer without consent unless scenario-specific policy explicitly requires it;
- when the issue is within capability, attempt to help before transferring;
- track repeated explicit human-agent requests according to policy;
- use the exact transfer tool only when the threshold and prerequisites are met.

## Scenario routing

Build general guidance for families such as:

- general banking/product knowledge;
- balances and transaction history;
- account profile/settings;
- cards and card problems;
- transfers and payments;
- disputes and fraud;
- loans and credit;
- account opening/closure;
- fees, limits, and eligibility;
- referrals and rewards;
- authentication failures;
- user-tool workflows;
- human transfer/escalation;
- multi-intent or interrupted conversations.

Keep actual policy facts in the runtime KB; do not hardcode changing banking policy in
the skill. The skill should teach retrieval, prerequisites, sequencing, and state
tracking.

## Adversarial pre-action review

Before every consequential action, internally ask:

1. Is this what the customer requested?
2. Is it permitted by retrieved policy?
3. Is authentication required and logged?
4. Is confirmation required?
5. Was this exact tool explicitly discovered?
6. Are arguments grounded in user/tool data?
7. Could this duplicate a successful mutation?
8. What tool result will prove success?

If any answer is unresolved, do not mutate state yet.

## Supporting resources

Keep essential decisions in `SKILL.md`. Put conditional detail in focused references,
for example authentication, KB/tool discovery, mutation safety, transfers, and
conversation completion. Every supporting file must be explicitly routed from
`SKILL.md`.

Offline scripts may validate a locally represented state ledger or policy checklist,
but they cannot call MCP tools, know live customer state, replace KB retrieval, or act as
a second LLM. Do not force scripts into every conversation.

## Failure analysis

For every failed task, identify the earliest category:

- conversation not started exactly once;
- wrong goal or scenario classification;
- unnecessary or missing KB search;
- policy hallucination;
- premature private-data access;
- authentication question error;
- missing verification log;
- guessed or unnecessary tool unlock;
- wrong tool or arguments;
- missing confirmation;
- duplicate mutation;
- ignored/overridden tool result;
- incorrect customer communication;
- premature or missing transfer;
- unresolved case ended;
- resolved case not ended;
- simulator/infrastructure failure.

Improve the earliest generalizable cause, not the task-specific surface wording.

## Evaluation

1. Inspect existing TAU3 runs before launching new paid evaluations.
2. Begin with a small stratified public set covering knowledge, authentication, a
   state-changing action, discoverable tools, and transfer when available.
3. Compare skill and placebo on identical tasks.
4. Inspect the complete conversation, every tool call/result, final state, and grader
   assertions.
5. Confirm promising changes on fresh scenarios.
6. Do not promote ties or validation regressions.
7. Use unique ignored output directories.

Report exact task set, scenario-family coverage, baseline/placebo/skill rates, net
improvement, per-task assertions, tool sequences, action counts, costs, promotion, and
uncertainty. A local training result is not a held-out guarantee.

Use development subagents, if available, only for bounded independent reviews such as
authentication/tool sequencing, mutation safety, and knowledge/transfer conversations.
They must not encode task-specific expected actions or customer details.

## Verification and handoff

After material edits run:

```bash
uv run stbench check-skill submissions/octuple/tau3
uv run python -m unittest discover -s tests -q
git diff --check -- submissions/octuple/tau3
git status --short --branch
```

Commit only exact tested TAU3 paths and report the hash. Never commit `.env`, `dataset/`,
or `runs/`.

Core principle: retrieve policy, authenticate at the correct moment, perform only
authorized grounded actions, trust tool results, preserve state, and close the
conversation only when genuinely resolved.
