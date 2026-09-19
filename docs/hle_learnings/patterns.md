# HLE patterns and antipatterns

## Delivery

### Pattern: checkpoint the answer file early

- Trigger: a plausible first-pass answer exists.
- Action: atomically write the exact three-field response before extended work;
  replace it only when evidence changes the conclusion.
- Deterministic check: validate file existence, schema, nonempty answer, and
  confidence range.
- Evidence: several observed attempts performed substantial work but scored zero
  because no response file existed.

### Antipattern: final-message-only completion

- Failure: the learner finishes or becomes stuck without writing the required file.
- Why it fails: the configured OpenHands path has no compatible fallback extraction.
- Guardrail: the last action must validate `/logs/agent/response.txt`.

## Search and tools

### Pattern: structured capability routing

- Classify domain, request type, answer contract, image dependency, and mechanical
  features before selecting tools.
- Route only the smallest helper set that can resolve a discriminating uncertainty;
  every recommendation states inputs, stopping condition, and misuse risk.
- Keep model selection and semantic interpretation with the learner. Deterministic
  helpers validate consequences, not premises.

### Antipattern: universal solver template

- Failure: the same proof/calculation checklist is applied to factual, chemical,
  algorithmic, physical, and image tasks regardless of their semantics.
- Guardrail: share the outer parse–attack–deliver workflow, but select exactly one
  primary subject adapter and feature-driven tools.

### Pattern: one discriminating falsification check

- Trigger: a candidate answer and strongest competitor are known.
- Action: choose the single definition, equivalence, observation, or calculation
  that separates them; run no more than two focused checks.
- Expected effect: reduce confident conceptual errors without open-ended search.

### Antipattern: unbounded deterministic exploration

- Failure: many locally correct calculations accumulate without producing a final
  answer.
- Signals: repeated scripts, cosmetic variants of the same check, package-install
  attempts, malformed repeated tool calls, or growing context with no saved answer.
- Guardrail: save first, stop after two checks, and preserve the best supported result.

## Multiple choice

### Pattern: definition and equivalence sweep

- Test every option against the governing definition.
- Normalize algebraically equivalent representations before rejecting an option.
- Treat “none of the above” as a claim requiring all other options to fail.
- Put only the requested label in `Answer:` when the task expects a label.

### Antipattern: coherent single-path commitment

- Failure: a plausible derivation is treated as confirmation without testing the
  most dangerous alternative or an equivalent representation.
- Guardrail: attempt to falsify the preferred option even at high confidence.

### Antipattern: analogy promoted to entailment

- Failure: a familiar theorem, paradox, or named construction is treated as proving
  the answer even though the prompt's object may not satisfy its hypotheses or be
  well-defined.
- Guardrail: label support as definition, deduction, evidence, recall, or analogy;
  establish existence/consistency before deriving properties, and compare each option
  as an exact claim.

## Abstract mathematics and computer science

### Pattern: variable-and-condition coverage

- Inventory every parameter and assumption before proving the result.
- For each item, identify where it enters the proof or prove why it is irrelevant.
- Compare answer families that depend on different parameters.

### Pattern: necessity, sufficiency, then counterexample

- Label each result before combining it: a construction proves achievability, an
  impossibility proves the complementary bound, and only matching bounds prove the
  exact optimum.
- Audit that the construction uses only operations permitted by the problem.
- Try to destroy the bound with the smallest boundary or degenerate example.

### Pattern: distinguish owned resources from shared information

- Before a class/entity counting argument, prove whether each resource is exclusive
  to one entity or can carry information about several entities.
- Soft outputs, query-dependent weights, and global measurements defeat an unproved
  one-resource/one-entity pigeonhole premise.
- For identifiability, derive the observation equations, eliminate common terms, check
  independent rank, and seek two allowed states related by an observation-preserving
  symmetry that require different outputs.

### Antipattern: intuitive premise promoted to theorem

- Failure: a one-to-one, independence, or dominance intuition is used as a lower
  bound without following from the actual model.
- Signal: the answer ignores a prominent variable or several supplied conditions.
- Guardrail: require explicit quantifiers and one attempted counterexample before
  retaining any exact minimum or maximum.

### Antipattern: construction mistaken for optimality

- Failure: a valid construction is presented as the minimum or maximum with no
  impossibility proof in the other direction.
- Signal: the argument says “this many works” and immediately concludes “this many is
  required.”
- Guardrail: record the bound direction beside every construction and reject an exact
  optimum unless the two independently proved bounds coincide.

### Antipattern: automatic dimension heuristic

- Failure: the presence of geometry and dimension triggers a memorized count without
  checking the observation model or quantifiers.
- Guardrail: verify exact versus noisy data, fixed versus adaptive measurements,
  unrestricted versus constrained state spaces, worst-case versus generic recovery,
  decoder capability, and whether indistinguishable states demand different outputs.

### Antipattern: schema-complete rationalization

- Failure: solver and critic records, condition audits, necessity/sufficiency fields,
  and high-level validation all agree because they reuse the same false premise.
- Signal: every role “supports” the candidate, no deterministic check is applicable,
  and a prominent variable is dismissed with narrative rather than a theorem.
- Guardrail: require a genuinely different answer family and an external mathematical
  principle or constructed counterexample; a dispatcher validates evidence structure,
  not conceptual truth.

### Pattern: test dimension-dependent representation

- Trigger: soft labels, weighted mixtures, interpolation, convexity, or a
  `D`-dimensional space appears alongside a proposed count bound.
- Check: compare class/count arguments with simplex, affine independence, barycentric
  coordinates, and dimension-based representation theorems, verifying hypotheses.
- Warning: distance-dependent mixtures can let one stored vector contribute
  differently at different query points, invalidating a one-object/one-class premise.

## Confidence

### Pattern: confidence follows independent evidence

- Raise confidence only after a genuinely independent check supports the answer.
- Lower it for unresolved premises, inaccessible visual evidence, or model choice.

### Antipattern: fluency-based confidence

- Failure: long coherent explanations receive 70–90% confidence despite incorrect
  conclusions.
- Guardrail: confidence never exempts an answer from the falsification check.

## Images

### Pattern: bounded measurable extraction

- Use available offline tools only for a specific measurable feature with a clear
  stop condition.
- Separate extracted evidence from inference.

### Antipattern: terminal reconstruction of semantic images

- Failure: pixel dumps, ASCII reconstruction, package exploration, or coordinate
  probing consumes the attempt without semantic access or delivery.
- Guardrail: one bounded extraction attempt, then submit the best supported answer.
