---
name: octuple-hle
description: Solve HLE questions with early delivery, evidence-type routing, option comparison, one falsification pass, and exact formatting.
---

# HLE: answer early, then seek evidence

Read `/app/instruction.md` once. The task is not complete until
`/logs/agent/response.txt` is nonempty. Target 6–8 high-level tool calls and permit at
most one answer correction. Never call `think`, inspect helper source, or build a review
artifact merely to prove that a process was followed.

## 1. Save the best current answer by action 2

Internally identify the exact requested object, answer format, important variables,
conditions, and strongest plausible answer. Your next action after reading the task
must save that candidate:

```bash
python /harbor/skills/stbench-skill/scripts/response_guard.py write \
  --explanation 'BRIEF CURRENT BASIS' --answer 'ONE EXACT ANSWER' --confidence N
```

This is provisional. Replace it once only if later evidence changes the conclusion.

## 2. Route by evidence type

Choose one primary route. Do not apply a universal proof template.

### Mechanically verifiable

Use this for derivations, calculations, finite cases, code traces, matrices, units,
stoichiometry, or reversible transforms. Derive the governing model yourself, then run
the one deterministic check most likely to distinguish the leading answer from its
competitor. Read one matching domain reference only if needed:

- `references/computer_science_ai.md`
- `references/chemistry.md`
- `references/engineering_physics.md`

Relevant offline helpers are under `scripts/`: `exact_math.py`, `finite_search.py`,
`matrix_check.py`, `text_transform.py`, `cs_check.py`, `chem_check.py`, and
`engineering_check.py`. They verify consequences of a chosen model; they do not prove
that the model is the right interpretation. Use `tool_router.py` only when two or more
helpers genuinely fit and you cannot select the smallest one directly. Stop after the
discriminating uncertainty is resolved.

If two or more already-justified mechanical checks must be batched, `hle_review.py` may
execute them once. Its approval is structural only and must never be cited as semantic
verification.

For an exact minimum or maximum, label the two directions: a construction proves only
achievability; a separate impossibility argument proves the opposite bound; only
matching bounds prove the optimum. For uniqueness, seek two distinct allowed states
with identical observations. Test unused variables, symmetry, reflection, sign,
permutation, scaling, zero, degenerate, boundary, and limiting cases when relevant.

### Factual or source-dependent

No local calculator can verify paper-specific classifications, attributions, named
results, dates, or other source facts. Do not manufacture tool activity or call
self-review “verification.” Compare plausible recalls, audit qualifiers and scope, and
choose the best-supported exact answer. Without source evidence, confidence is at most
60%.

### Conceptual or interpretive

For definitions, analogies, philosophy, or wording such as “most plausible,” compare
formal correctness with the standard disciplinary interpretation and likely test-author
intent. Do not treat an analogy as entailment or a coherent story as proof. Check that
any named object is well-defined before deriving its properties.

For multiple choice, build this compact table internally before committing:

`option | literal fit | standard/author-intent fit | explains all details | fatal flaw`

Evaluate every option. The strongest competitor must receive its best interpretation,
not a convenient weak one. When a credible competitor remains and no external or
mechanical evidence separates it, confidence is at most 65%.

Read `references/answer_contracts.md` for ambiguous multiple-choice or exact-match
contracts and `references/factual_mixed.md` for factual/mixed tasks.

### Image-dependent

Read `references/images.md`. Inspect the complete image once, then at most one bounded
crop/enlargement with `image_prepare.py` when necessary. Separate visible evidence from
inference and route that evidence to the appropriate subject method. If a central image
detail remains unverified, confidence is at most 65%.

For mathematics, biology, earth/space science, social science, humanities/law, or an
unlisted subject, read `references/other_domains.md` only when its scope warnings matter.

## 3. One adversarial pass

Assume the saved answer is wrong. Ask only:

1. What is the first unsupported premise?
2. What is the strongest competing answer under its best interpretation?
3. What single fact, definition, calculation, counterexample, or wording cue separates
   them?

Run one check if it can create genuinely new evidence. Otherwise make the comparison
directly and acknowledge the unresolved premise in confidence. Do not create JSON,
mark your own derivation “passed,” or use `hle_review.py` as semantic certification.
Self-review is adversarial reconsideration, not independent verification.

## 4. Final answer and stop

If the leader changes, replace the provisional response once. Preserve requested
labels, units, precision, capitalization, ordering, and transformation direction. Put
one independently extractable result in `Answer:`; include option text only if asked.

Unless the task requires a stricter format, use exactly:

```text
Explanation: <concise decisive basis>
Answer: <one exact answer>
Confidence: <integer from 0% to 100%>
```

Use `response_guard.py write-raw` when the task requires another schema. Make
`response_guard.py validate` (or `--schema nonempty`) the final tool call, then finish.
Do not continue exploring after validation.
