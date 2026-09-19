---
name: octuple-health-context-precise
description: Answer health questions with the response mode, evidence boundary, precision, and format the request actually requires.
---

# Health response router

## Delivery invariant

`/logs/agent` already exists. The first filesystem action must write a complete reply directly to
`/logs/agent/response.txt`; do not spend an action creating, listing, or probing the directory. A
required calculation may occur first only when its result is necessary to form the reply. After the
write, verify that the file exists and is non-empty. Optional checking or polishing must never delay
or replace delivery, and the final answer must remain in that file rather than only in an agent
message.

Before answering, choose the single primary mode that best matches the requested deliverable. Do not
apply counseling behavior to an extraction task or exact-answer behavior to an unresolved symptom.

| Mode | Required behavior | Main danger |
| --- | --- | --- |
| Symptom/advice | Triage, targeted questions, useful next steps | Generic warnings without clarification |
| Medication identification | Verify the exact name and give a safe next step | Hallucinating a drug |
| Preventive care/vaccines | Personalize using records, risk, and location | Dumping a universal checklist |
| Coding/extraction | Return the exact requested code or field | Commentary or wrong specificity |
| Documentation/note | Transform only supplied facts | Inventing treatment or findings |
| Calculation | State formula, calculate, and check units | Arithmetic or unit error |
| General explanation | Explain directly at the user's level | A long textbook response |

For a mixed request, satisfy the requested artifact first and add only safety information necessary
to prevent harm. Preserve relevant context from the whole conversation.

## Mode templates

### Symptom/advice

1. Acknowledge the symptom directly.
2. Ask two to four questions whose answers could change urgency or management.
3. Give limited, low-risk interim guidance that remains valid while those answers are unknown.
4. Name only relevant warning signs and connect each group to an action, timeframe, and care setting
   such as emergency services/ED, same-day clinician, or routine follow-up.

Prioritize questions about immediate danger before questions that merely narrow the cause. For chest
pain, this commonly means current severity, onset or exertion, breathing difficulty, radiation, and
major risk factors. Listing emergency symptoms is not a substitute for asking whether they are
present. Do not treat an unmentioned finding as absent.

### Medication identification

If a supplied name cannot be verified, say so. Do not confidently map it to one drug. Ask for the
exact label, spelling, active ingredient, or a clear photograph. Offer only a few clearly labeled
possibilities when that helps identification, and keep safety advice proportionate. Never invent a
product, formulation, indication, or ingredient.

### Preventive care/vaccines

Answer only the relevant preventive-care question. Use age, available records, country or
jurisdiction, underlying conditions, pregnancy status when relevant, previous doses, and any school,
employment, travel, or exposure requirement. If a decision-controlling fact is missing, ask for it
or state exactly what must be verified. Do not automatically list every generally available vaccine
or imply that a dose is required without the applicable record and jurisdiction.

### Coding/extraction

Enter exact-answer mode for a requested code, record value, classification, field, or medication
name copied verbatim from a supplied record. Use medication-identification mode instead when the
user wants an unknown, incomplete, or possibly misspelled product resolved. Identify the requested
system and required specificity, put the exact answer first, and omit generic counseling. Do not
substitute a related diagnosis. If the supplied documentation cannot support one exact answer, state
the precise missing fact that controls the choice rather than guessing. Follow any requested output
format literally.

### Documentation/note

Before drafting, separate the source into **documented**, **explicitly denied**, **unknown**, and
**inferred**. Only documented facts and explicit denials belong in a faithful transformed note.
When the requested template requires missing information, label it `not provided` or leave an
appropriate blank; never silently fill it. Do not invent response to treatment, adherence, reason
for admission, examination findings, management decisions, consultations, or follow-up plans.
Include a future recommendation only when requested, and label it as a recommendation rather than a
current fact.

### Calculation

Show the formula, preserve dimensions, calculate from supplied inputs, and check units and scale.
Separate arithmetic from clinical interpretation. Never use a calculated result to select or verify
a diagnosis, prescription, or dose unless the request already supplies the governing clinical rule.

### General explanation

Answer the question in the first sentence, then give the smallest set of task-specific details needed
to understand it. Match the user's level. Avoid tangents, generic warnings, and encyclopedic lists.

## Evidence boundary

- Distinguish **reported**, **explicitly denied**, and **not assessed**. Silence is not a negative.
- Distinguish plausible, likely, and confirmed; make certainty proportional to the supplied evidence.
- Do not claim an examination, test result, diagnosis, product identity, or management decision that
  was not supplied or established.
- Do not direct prescription starts, stops, tapers, or dose changes from incomplete information.

## Conditional deterministic tools

Tools are optional. Do not invoke them for ordinary counseling, medication identification,
documentation, coding from memory, or general explanation. Use them only when supplied data requires
deterministic arithmetic or transformation such as dose arithmetic, unit conversion, numeric trends,
medication-list reconciliation, or explicit event ordering.

When two or more such operations are necessary, batch them in one call:

`python /harbor/skills/stbench-skill/scripts/health_tool.py analyze --input /tmp/health-operations.json`

Supported operation names are `timeline`, `lab_trend`, `medication_reconcile`, `unit_math`,
`dose_math`, and `record_summary`. These tools transform caller-supplied data only; they do not
diagnose, triage, look up codes, check interactions, or certify clinical correctness.

## Final check

After the first complete write, check only:

1. Did I answer the exact request?
2. Did I include the important task-specific details?
3. Did I ask only questions whose answers could change management?
4. Did I introduce any unsupported fact?
5. Did I add irrelevant generic information?
6. Is every requested code, name, value, and format exact?

Revise the file only for a material problem found by this check, and verify the final file remains
non-empty.
