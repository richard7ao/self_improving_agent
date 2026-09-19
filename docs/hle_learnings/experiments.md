# HLE experiment log

## `runs/hle-baseline-20260919-001`

- Design: 4 fixed public tasks × baseline/placebo/skill = 12 intended attempts.
- Outcome: incomplete; learner token pool exhausted, so no aggregate comparison is
  valid. Seven attempts were recorded, all scored zero.
- Usage: 1,989,357 learner charged tokens ($0.12870745 reported) and 53,954 grader
  charged tokens ($0.199206 reported).
- Delivery evidence: three recorded attempts lacked a response file; four produced
  well-formed but incorrect responses.
- Reasoning evidence: submitted failures included shared conceptual commitment across
  arms and high confidence without an independent falsification check.
- Operational evidence: cold container setup and infrastructure retries increased
  wall time; one image attempt consumed a very large context while trying to recover
  semantic content through terminal operations.
- Decision: do not score or promote from this run. Reduce trial count per invocation,
  prioritize response delivery, and use fixed explicit tasks.

## `runs/hle-short-router-screen-20260919-001`

- Design: one fixed tune task, skill-only, testing a shorter bounded prompt.
- Outcome: manually stopped under the declared rejection rule after more than 1.13M
  cumulative input tokens with no response file.
- Pattern: concise wording alone did not enforce early delivery or a tool-call bound.
- Antipattern: the learner continued deterministic analysis, then emitted malformed
  tool calls rather than submitting.
- Decision: reject the candidate. Add an atomic response/validation tool and make its
  use the first post-read action.

## `runs/hle-deterministic-screen-20260919-001`

- Design: one fixed transformation task, skill-only, adding offline deterministic
  helpers and an explicit bounded workflow.
- Outcome: manually stopped after 20 learner actions and about 284,000 input tokens;
  no response file existed.
- Pattern: helper availability did not make the learner checkpoint an answer.
- Decision: reject; enforce delivery through a first-action state tool rather than a
  prose instruction alone.

## `runs/hle-stateful-screen-20260919-001`

- Design: one fixed transformation task, skill-only, with a local state folder and
  explicit checkpoints.
- Outcome: manually stopped after 16 learner actions and about 174,000 input tokens;
  the scratch state was used, but no final response was delivered.
- Antipattern: recording analysis state is not equivalent to preserving a gradeable
  answer.
- Decision: reject; the initialization command itself must create a valid fallback.

## `runs/hle-failsafe-screen-20260919-001`

- Design: one fixed transformation task, skill-only, whose start command immediately
  created a fallback response.
- Outcome: response delivery was protected, but the learner kept looping through more
  than 28 actions and 432,000 input tokens before manual interruption.
- Pattern: atomic fallback creation prevents an automatic delivery zero.
- Antipattern: a placeholder response does not bound exploration or establish answer
  quality.
- Decision: retain the delivery primitive but reject this workflow as a complete
  candidate.

## `runs/hle-orchestrated-reasoning-screen-20260919-001`

- Design: one fixed known-failure task, skill-only, with decomposer, solver, critic,
  and orchestrator roles executed sequentially by the frozen learner.
- Outcome: score 0; 338,526 learner tokens and 807 grader tokens.
- Delivery: a valid response was finalized. The failure was conceptual, not formatting.
- Antipattern: decomposition anchored on the preferred answer by creating sufficiency
  and necessity tasks for that answer rather than first comparing answer families.
- Decision: reject this version; require variable/condition and answer-family inventory
  before candidate-proof subtasks.

## `runs/hle-dispatcher-reasoning-screen-20260919-001`

- Design: the same fixed known-failure task, skill-only, with coverage-aware roles and
  a one-call high-level dispatcher.
- Outcome: score 0; 432,098 learner tokens ($0.0228 reported) and 810 grader tokens
  ($0.0041 reported).
- Delivery: the dispatcher atomically saved and re-read a valid response and returned a
  passing report, but the conceptual answer remained incorrect.
- Antipattern: every role and schema field rationalized the same unsupported geometric
  premise; structural completeness did not create independent evidence.
- Decision: reject and do not rerun this task again. Preserve the dispatcher for
  mechanical batching, add general dimension/simplex checks, and use fresh tasks for
  further evidence.

## `runs/hle-simplified-fresh-screen-20260919-001`

- Design: two different public tasks, skill-only, using the concise response-first
  router, sequential reasoning roles, and batched dispatcher.
- Outcome: one of two passed (50%); 482,984 learner prompt tokens, 14,663 completion
  tokens, and 2,026 grader tokens. Reported costs were $0.02628022 learner and
  $0.00963 grader.
- Delivery: both trial directories contained nonempty response files (218 and 533
  bytes). The run-level empty-output count of two was a harness extraction bug, not a
  delivery failure.
- Interpretation: this is screening signal only. The task count is too small and the
  run lacks a control arm.
- Decision: compare the incumbent on the identical task list; reject a tie and do not
  promote without strict improvement.

## `runs/hle-incumbent-fresh-compare-20260919-001`

- Design: current live skill on the identical two-task list used by the simplified
  candidate screen.
- Outcome: one of two passed (50%); 268,032 learner tokens and 24,836 grader tokens.
  Reported costs were $0.0196 learner and $0.1439 grader.
- Delivery: both final trials contained nonempty responses. One verifier call stalled
  and triggered an infrastructure retry before the run completed.
- Decision: the simplified candidate tied the incumbent at 50%, so it was not eligible
  for promotion.

## `runs/hle-routed-smoke-20260919-001`

- Design: skill-only smoke on three fresh non-image public tasks selected by metadata:
  CS/AI multiple choice, Chemistry exact match, and Engineering multiple choice.
- Outcome: invalid infrastructure run. No learner trajectory or response was created.
  Container package downloads failed, Harbor retries also failed, and an upstream
  streaming read error occurred.
- Decision: do not classify this as a skill, reasoning, formatting, or delivery
  failure. Retry one task after infrastructure recovers before making an accuracy
  claim.

## `runs/hle-routed-smoke-20260919-002`

- Design: one fresh non-image CS/AI multiple-choice task, skill-only, under the real
  50-iteration contract.
- Outcome: score 0; 591,867 learner prompt tokens, 13,287 completion tokens, and
  36,908 grader tokens. Reported costs were $0.02851539 learner and $0.082026 grader.
- Delivery: the trial contained a 940-byte response. The run-level empty-output field
  was the known binary-HLE extraction bug, not a delivery failure.
- Behavior: 30 high-level calls (21 terminal, 6 file editor, 2 think, 1 finish). The
  learner attempted router/reviewer use repeatedly because reasonable classification
  aliases and its compact review schema were rejected. It did not call irrelevant
  chemistry or engineering helpers.
- Earliest answer failure: question misinterpretation/invalid derivation. A conceptual
  analogy and preferred consistency reading were treated as proof; the structured
  review then rationalized the same premise. Confidence remained 85%.
- Infrastructure: the grader needed 17 extraction attempts before returning a valid
  incorrect judgment.
- Decision: add tolerant structured aliases and review normalization to remove tool
  repair loops, plus a general well-definedness-versus-analogy check. Do not run a
  placebo comparison or claim accuracy improvement from this failed smoke.
