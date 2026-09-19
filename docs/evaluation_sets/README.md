# Reserved evaluation sets

These manifests reserve public training tasks for later confirmation runs. They contain
task IDs only. At selection time, none of the IDs appeared in existing `runs/` artifacts.
Do not inspect their prompts, rubrics, or answers before evaluation; keeping them unseen
makes them a more useful local generalization check.

The sets were selected deterministically with the seed label
`confirmation-20260919`. The HLE set is stratified across Computer Science/AI,
Chemistry, and Engineering, including both image and non-image tasks. The Health set is
a deterministic sample from the remaining unused HealthBench Hard tasks.

Run Health after current evaluations have stopped:

```bash
HEALTH_CONFIRM_TASKS=$(paste -sd, docs/evaluation_sets/health-confirmation-20260919.txt)
uv run stbench eval \
  --domain health \
  --skill submissions/octuple/health \
  --arms baseline,placebo,skill \
  --tasks "$HEALTH_CONFIRM_TASKS" \
  --concurrency 2 \
  --out runs/health-confirmation-20260919-001
```

Run HLE after current evaluations have stopped:

```bash
HLE_CONFIRM_TASKS=$(paste -sd, docs/evaluation_sets/hle-confirmation-20260919.txt)
uv run stbench eval \
  --domain hle \
  --skill submissions/octuple/hle \
  --arms baseline,placebo,skill \
  --tasks "$HLE_CONFIRM_TASKS" \
  --concurrency 2 \
  --out runs/hle-confirmation-20260919-001
```

Use the complete manifest for confirmation. If a cheap plumbing check is needed first,
use the first four IDs with `--arms placebo,skill`, but do not use that small result to
promote a skill. For competition relevance, report `summary.net_delta` (skill minus
placebo), alongside the raw skill rate, task count, invalidated-task count, and cost.
