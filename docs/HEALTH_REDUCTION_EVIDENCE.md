# Health reduction evidence

This note records development evidence for the eventual maximal-package reduction. It is
not a submission file and contains no task text, patient facts, rubric content, or answers.
All figures are local public-training measurements and do not guarantee held-out results.

## Evidence available

Fourteen candidate tune evaluations used the same three Health tasks across five rounds.
Two winning candidates also received a one-task validation run. This repeated, tiny sample
is useful for detecting gross runtime failures but is too small and adaptively reused to
establish general improvement.

| Candidate | Raw tune mean | `SKILL.md` words | Mean answer characters | Empty outputs |
|---|---:|---:|---:|---:|
| R1 A | 0.1659 | 941 | 1,527 | 0 |
| R1 B | 0.1871 | 576 | 1,671 | 0 |
| R2 A | 0.1255 | 623 | 1,292 | 0 |
| R2 B | 0.2665 | 517 | 1,981 | 0 |
| R2 C | 0.2756 | 501 | 1,489 | 0 |
| R3 A | 0.0655 | 433 | 631 | 2 |
| R3 B | 0.1934 | 476 | 1,891 | 0 |
| R3 C, current live survivor | 0.3691 | 473 | 1,932 | 0 |
| R4 A | -0.1321 | 547 | 407 | 2 |
| R4 B | 0.2045 | 220 | 1,233 | 0 |
| R4 C | -0.0094 | 452 | 780 | 1 |
| R5 A | 0.2542 | 547 | 1,719 | 0 |
| R5 B | 0.3851 | 433 | 1,921 | 0 |
| R5 C | 0.2239 | 526 | 1,531 | 0 |

Across all 14 rows, Pearson correlations were:

- score versus `SKILL.md` word count: `-0.112`;
- score versus mean answer characters: `+0.891`; and
- score versus learner-ledger call count: `+0.591`.

After excluding candidates with any empty output (`n=11`), score versus skill words was
`-0.381` and score versus answer characters was `+0.637`.

These are descriptive associations, not causal estimates. The task set is fixed and tiny;
candidate changes are confounded; answer length may proxy rubric coverage; and calls may
proxy successful task completion. They do not justify rewarding verbosity or extra calls.

## Current survivor versus the strongest unvalidated challenger

R5 B changed the live response method by adding a more explicit symptom action ladder. Its
three task scores were `0.2740`, `0.2903`, and `0.5909`, versus the live survivor's
`0.1644`, `0.6022`, and `0.3409`. The differences were therefore approximately `+0.1096`,
`-0.3118`, and `+0.2500`; their mean was `+0.0160` after rounding.

This is a useful hypothesis, not a winner. The apparent gain depends on two improvements
offsetting one large regression, and the challenger never received a recorded validation
run. Its total learner-token count was `112,968`, versus `79,107` for the live survivor,
but provider accounting differed and token totals are not a clean causal measure.

## Maximal first-principles package failure

The stopped placebo-versus-skill experiment under
`runs/subagent-health/fresh-confirmation-v1` produced four valid task pairs, one pair with
network errors, and did not start the final three planned tasks. Reconstructing arms from
the captured skill names gives:

- placebo mean: `0.435167846951`;
- experimental skill mean: `-0.162117750220`; and
- provisional paired net delta: `-0.597285597171`.

All four experimental-skill response files were empty. Each trajectory spent the four
allowed iterations initializing workspaces, running planners, or reading references, then
hit the iteration limit before drafting and delivery. The placebo produced non-empty
answers in all four cases. Therefore this result identifies a delivery/runtime failure; it
does not measure the medical quality of answers the maximal package might have produced.

## Implications for final reduction

Keep the maximal Health package as a source library, but compile a separate runtime
candidate rather than mounting the source library directly.

The first reduction candidate should:

1. Keep the always-visible decision protocol near the empirically successful 430–500-word
   range. This is a starting band, not a proven optimum.
2. Require zero preliminary tool calls for ordinary clinical answers. The learner should
   draft and deliver first; optional checking must fit after a usable answer exists.
3. Route at most one conditional reference for a genuinely specialized case. Avoid chains
   of indexes, planners, workspaces, and finalizers within a four-iteration harness.
4. Preserve direct answering, conversation continuity, bounded-artifact discipline,
   evidence calibration, concrete next actions, and proportionate escalation.
5. Test the R5 B action ladder as an isolated edit. Its likely benefit is improved symptom
   actionability; its observed risk is regression on other conversational modes.
6. Treat response delivery as a hard prerequisite. A medically excellent unwritten answer
   scores as an empty answer.
7. Do not optimize answer length directly. Use enough detail for decision-changing rubric
   coverage, then remove repetition and tangents.

## Next evidence needed

After concurrent optimizer work is stable, compare the unchanged live survivor and one
compressed action-ladder candidate on the same fresh search tasks, with matched task-level
scores and delivery accounting. Freeze only one finalist. Then use placebo, incumbent, and
finalist on untouched confirmation tasks. Report raw skill rate, skill-minus-placebo,
candidate-minus-incumbent paired differences, invalidations, empty outputs, token usage,
cost, and uncertainty. Do not average adaptive tune results into confirmation.
