# Finance self-improvement loop

The first version uses the existing `stbench optimize` controller. The reviewer
and worker are separate model calls with separate instructions; Python controls
evaluation and promotion. The learner model and `hackathon.toml` stay fixed.

1. Evaluate the current skill on a fixed tune/validation split.
2. Give the reviewer tune instructions, scores, and a bounded excerpt of the
   learner's actions, tool outputs, and final response. Validation evidence and
   verifier files are excluded.
3. Give the worker the current skill and the review. It produces a complete
   candidate folder, optionally including offline tools routed from `SKILL.md`.
4. Check paths, submission limits, Python syntax, supporting-file references,
   and verbatim training-task copying before evaluation.
5. Run the candidate on the same tune tasks, then evaluate the best candidate
   on the reserved validation tasks.
6. Promote only when the weighted overall score clears `--min-improvement`
   **and validation strictly improves**. A validation tie or regression keeps
   the incumbent. On a single-task run there is no validation gate, so use at
   least three tasks for a useful smoke comparison.

## Small first run

Start from a committed skill so the original is recoverable. Each run needs a
new output directory. This example uses two tune tasks, one validation task,
one reviewer call, and one worker call. It normally runs six learner attempts;
infrastructure retries can add more. These calls spend provider credits.

```bash
uv run stbench optimize --domain qf \
  --skill submissions/octuple/qf --out runs/qf-loop-v1 \
  --tasks 13f-amendment-aware-crowding,alpha-hedge-strategy,asian-option-levy-curran \
  --limit 3 --validation-fraction 0.34 --seed 42 \
  --iterations 1 --candidates 1 --concurrency 1 \
  --candidate-parallelism 1 --keep-candidates
```

Use `python -m skilltrainbench.cli` from the project virtual environment if
`uv` is unavailable. The local Docker permission/Buildx setup is documented in
`BASELINE_WORKFLOW.md`.

## Inspect the evidence

- `optimization.json`: selected tasks, candidate scores, prior scores, and
  promotion decision.
- `round-01/review.txt`: reviewer findings.
- `round-01/generated-responses/`: worker responses.
- `round-01/candidates/`: candidate instructions and tools, retained for review.
- `initial/`, `round-01/eval-candidate-01/`, `round-01/validation/`: measured
  results, token/cost ledgers, and learner trajectories.

The incumbent is the existing skill, which initially is a placeholder. This
comparison is not a no-skill/placebo leaderboard evaluation. Three tasks test
the loop's operation; they do not establish generalization. Confirm any winner
on fresh training tasks with baseline, placebo, and skill arms before claiming
a reliable improvement.

Generated Python receives syntax checks, not a proof of correctness or an
offline-security guarantee. Inspect and test any generated tool before trusting
it; the learner runs candidates in benchmark containers. Reviewer/worker calls
currently have no separate cost ledger, so evaluation costs exclude those calls.
