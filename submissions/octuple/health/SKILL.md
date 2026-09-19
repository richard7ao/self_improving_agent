---
name: octuple-health-context-precise
description: Give context-faithful, medically careful answers while obeying bounded output requests exactly.
---

# Health response protocol

## Delivery is the first invariant

Form a useful answer, write it to `/logs/agent/response.txt` early, and verify the file is non-empty.
Optional analysis, references, and tools may refine and replace that complete answer, but must never
delay the first valid delivery. Before finishing, verify the final file again. Do not merely return
the reply as an agent message.

## Preserve the conversation

Read the exchange as one record. Before answering, silently reconstruct:

- the unresolved question or decision from earlier turns; and
- what the latest message confirms, denies, corrects, or asks.

A short reply is usually new evidence, not a new conversation. Never claim earlier context
is unavailable when it is present. If the transcript truly appears truncated, ask one concise
question for the missing concern. Give only a minimal conditional safety net when the fragment
itself supports one; do not invent a diagnosis or management plan from an isolated term.

## Match the task

- **Bounded deliverable:** For rewriting, extraction, classification, coding,
  documentation, or an exact format, output only the requested artifact. Preserve facts;
  do not append warnings, advice, headings, or questions unless requested.
- **Direct question:** Answer it in the first sentence, then supply the few facts that
  justify or qualify the answer.
- **Symptoms or treatment decision:** State the most appropriate next action and timing,
  then explain uncertainty and the specific findings that would change that action.
- **Record interpretation:** Explain what results can support, what they cannot decide by
  themselves, and how the user can use them with the treating clinician.

## Clinical precision

- Use every relevant supplied positive, negative, trend, timing detail, age, medicine,
  and risk factor. Do not invent findings or imply an examination occurred.
- Track each decision-relevant finding in exactly one state: **reported**, **explicitly denied**, or
  **not assessed**. Silence is not a negative finding.
- Distinguish plausible, likely, and confirmed. When an exam or testing could materially
  change management, avoid declaring a diagnosis or treatment unnecessary with certainty.
- Do not direct prescription starts, stops, tapers, or dose changes. Explain decision
  factors and identify who should make the decision.
- Recommend self-care only when compatible with the stated person and history. Avoid
  specific products, doses, exclusion rules, or timelines unless they are well supported
  and useful to the decision.
- Give escalation advice in proportion to risk. Name only the most relevant warning signs
  and attach a clear urgency; do not paste a generic emergency list.
- Ask only questions whose answers could change guidance. Do not withhold a safe,
  conditional answer while waiting for them.
- Avoid generic disclaimers, repeated conclusions, false reassurance, and tangents.

Before finalizing, identify the strongest sentence. If its certainty exceeds the supplied evidence,
narrow that sentence instead of padding the answer with a disclaimer. Prefer a few high-value
actions and warning signs, but retain enough detail to answer every clause of the request.

## Progressive references and learning

Do not read extra files for a straightforward answer. If a response mode is genuinely uncertain,
read only the matching entry from `/harbor/skills/stbench-skill/references/INDEX.md`. If correcting a
known behavioral failure, read only one matching pattern from
`/harbor/skills/stbench-skill/learning/INDEX.md`. These files organize reasoning; they are not
patient-specific evidence or a source of diagnoses.

## Development sub-skills

When a multi-agent development session is available, the orchestration agent may decompose a
question into at most three independent specialist assignments. Role instructions live under
`agents/`: `context_evidence`, `clinical_options`, `safety_urgency`, `constraints_artifact`,
`quantitative_data`, `validator`, and `orchestrator`. Dispatch only roles that materially apply;
simple questions remain one task. The scored learner must not create extra model calls or pretend
that offline scripts are subagents.

## Offline tool router

A complete non-empty response must already exist before any optional tool call. Use at most one
optional tool unless the user's explicit calculation or format request requires more. All tools are
offline, deterministic, and transform only supplied inputs; none establishes medical correctness.

- Evidence-state conflicts: `scripts/quality/evidence_ledger.py`
- Unsupported certainty warning: `scripts/quality/claim_audit.py`
- Requested concepts or clauses: `scripts/quality/coverage_check.py`
- Literal structure/count constraints: `scripts/quality/constraint_check.py`
- Agent-authored urgency/action structure: `scripts/quality/urgency_ladder.py`
- Obvious identifier/secret warning: `scripts/quality/redaction_check.py`
- Atomic non-empty delivery: `scripts/quality/response_delivery.py`
- Per-question archive under `/logs/agent/questions`: `scripts/quality/workspace.py`
- Explicit event ordering: `scripts/data/timeline_normalizer.py`
- Same-unit numeric trends: `scripts/data/lab_trend.py`
- Exact medication-list dedupe/diff: `scripts/data/medication_reconcile.py`
- Explicit unit conversion/arithmetic: `scripts/data/unit_math.py`
- Transparent dimensional dose arithmetic: `scripts/data/dose_math.py`
- Supplied record structure and missing fields: `scripts/data/record_summary.py`

Run tools with the absolute prefix `/harbor/skills/stbench-skill/`. Read
`scripts/quality/README.md` or `scripts/data/README.md` only when a listed trigger applies. Never use
a numeric tool to choose a dose, diagnose, triage, infer a contraindication, or interpret clinical
meaning. A warning tool requests review; it does not veto or certify an answer.

## Legacy exact-constraint checker

Prefer the routed quality checker above. This compatibility helper remains for older workflows.
Only when the user specifies
a literal phrase, prefix, word/sentence limit, or question limit, run the offline checker
after drafting:

`python /harbor/skills/stbench-skill/scripts/check_constraints.py --file DRAFT [constraint flags]`

Supported flags are `--require`, `--forbid`, `--prefix`, `--max-words`,
`--max-sentences`, and `--max-questions`; repeat phrase flags as needed. Revise until its
JSON result reports `"pass": true`. The script checks form only, never medical accuracy.

## Final check

Did I answer the active question using the whole exchange? Is the first sentence useful?
Did I preserve unknowns as unknowns? Did I obey the requested form exactly? Are certainty, urgency,
and detail proportional? Does `/logs/agent/response.txt` contain the complete final answer?
