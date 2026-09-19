---
name: octuple-hle
description: Route expert HLE questions through domain-specific solving, skeptical attack, offline verification, confidence calibration, and exact delivery.
---

# HLE routed solve–attack–verify protocol

Read `/app/instruction.md` once. Solve the stated task, not a nearby easier task.
The task is incomplete until `/logs/agent/response.txt` is nonempty and validated.
Never finish with only an agent message.

## 1. Classify, parse, and preserve a candidate

Classify across all three axes:

- **Domain:** `computer_science_ai`, `chemistry`, `engineering_physics`,
  `image`, `factual_recall`, `mathematics_statistics`, `biology_medicine`,
  `earth_space_science`, `social_science`, `humanities_law`, `mixed`, `uncertain`,
  or `other`.
- **Request:** factual identification, numerical calculation, symbolic derivation,
  algorithm/code trace, proof, existence, sufficiency, necessity, minimum/maximum,
  uniqueness, transformation/cipher, or image interpretation.
- **Contract:** exact match, multiple choice, number, expression, string, entity/name,
  formula, or short explanation.

Extract the requested object, variables, units, sign/indexing conventions, boundary
conditions, assumptions, image dependencies, precision, and output format. Record where
each important variable enters the reasoning. An unexplained central variable is a
warning: test a competitor that uses it.

As soon as one defensible candidate exists, save it atomically with
`python /harbor/skills/stbench-skill/scripts/response_guard.py write`. Replace it only
when evidence changes the answer.

## 2. Select exactly one primary domain adapter

Read only the matching reference, plus `references/answer_contracts.md` when needed:

- CS/AI: `references/computer_science_ai.md`
- Chemistry: `references/chemistry.md`
- Engineering/physics: `references/engineering_physics.md`
- Image-dependent: first `references/images.md`, then one subject adapter
- Factual recall or mixed: `references/factual_mixed.md`
- Broader or unlisted subject: `references/other_domains.md`

The shared outer sequence is:

`parse → ledger → domain derivation → candidate → deterministic checks → attack →`
`skeptical review → confidence → exact format → save and validate`.

The middle derivation must follow the selected adapter. Do not force every subject into
one mathematical template, and do not use scripts to invent definitions, reaction
models, physical laws, factual knowledge, or image meaning.

## 3. Match proof obligations to the request

- Existence/sufficiency: give a permitted construction or witness.
- Necessity: prove every permitted solution obeys the restriction.
- Minimum/maximum: label each bound. A construction proves only achievability; an
  impossibility proves the opposite bound; only matching bounds prove the optimum.
- Uniqueness: establish injectivity or seek two distinct allowed states with identical
  observations that require different outputs.
- Classification/multiple choice: solve independently, normalize equivalent forms,
  test every option, and identify the strongest competitor.
- Numerical/symbolic: derive the expression before computing and substitute back.
- Proof: audit quantifiers and boundary cases.
- Short exact/factual: give one exact result and separate recall from inference.

Showing that an answer works never proves it is minimal. Prove necessity separately
from sufficiency. Before a pigeonhole argument, establish whether resources are
class-owned or shared information sources.

## 4. Attack the leading candidate

Assume it is wrong. Find the first unsupported inference and the strongest competing
answer. Test the most discriminating applicable challenge: counterexample, alternate
interpretation, unused variable, hidden assumption, equivalent form, unit/sign error,
or zero, one-dimensional, limiting, degenerate, equality, and boundary cases. Search
for reflection, sign, permutation, scaling, translation, and coordinate ambiguities.
If a counterexample survives, reject or revise the candidate.

For geometry/identifiability, write observation equations, eliminate shared terms,
check rank or affine independence, and seek two states with the same observations.
Squared-distance differences can become linear and reflection across a deficient
affine hull can show ambiguity, but only under matching model and quantifier
assumptions. Geometry plus dimension is not an automatic formula.

## 5. Run one skeptical review and deterministic batch

Perform the internal reviewer pass in `references/reviewer_protocol.md`. It must attack,
not paraphrase, the derivation. Put its structured record and all justified mechanical
checks in `/logs/agent/hle_review.json`, then prefer one call:

When more than one helper might apply, call the router first with the structured
classification (never raw question text):

```bash
python /harbor/skills/stbench-skill/scripts/tool_router.py route \
  --domain DOMAIN --task-type TYPE[,TYPE] --answer-type ANSWER_TYPE \
  --has-image true|false --features FEATURE[,FEATURE]
```

It returns ordered recommendations, required inputs, stopping conditions, misuse risks,
review checks, warnings, and a concise plan—not an answer. Use only the smallest
recommended set that can separate plausible candidates, and stop tool use once that
uncertainty is resolved. For an already structured JSON specification use
`tool_router.py suggest --spec problem_spec.json`.

```bash
python /harbor/skills/stbench-skill/scripts/hle_review.py \
  --input /logs/agent/hle_review.json
```

The dispatcher routes exact arithmetic, finite search, code/graph/recurrence checks,
formula and stoichiometry checks, matrices, dimensions/units, residuals, boundaries,
seeded counterexample sampling, image metadata/preprocessing where available, and
answer-format checks. It validates consequences of the learner's selected model; it
does not semantically solve arbitrary expert questions. Use single-purpose helpers only
when one isolated check is enough.

## 6. Calibrate confidence

Confidence follows completed evidence, never prose fluency:

- missing required necessity/minimality or uniqueness check: maximum 55%;
- central unexplained variable: maximum 50%;
- unresolved unit or sign convention: maximum 60%;
- unverified image detail central to the answer: maximum 65%;
- surviving counterexample: reject and revise;
- direct derivation plus independent check, no material assumption: 95–100%;
- strong derivation with minor recall/interpretation risk: 80–94%.

Below 80%, perform one additional discriminating check, then submit the strongest
supported answer rather than loop.

## 7. Enforce the answer contract and deliver

Follow `references/answer_contracts.md`. For multiple choice, return the exact requested
label and requested text; for exact match, normalize units, notation, capitalization,
precision, and ordering, and remove alternatives. Keep `Answer:` independently
extractable.

Unless the task explicitly requires a stricter schema, write exactly:

```text
Explanation: <concise decisive reasoning>
Answer: <one exact answer>
Confidence: <integer from 0% to 100%>
```

Task-specific formatting overrides this default; use the response guard's raw mode.
Make final validation the last tool action. Do not continue exploring after the review
passes and the saved response validates.
