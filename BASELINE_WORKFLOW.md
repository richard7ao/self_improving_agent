# Finance baseline workflow

Establish the frozen learner's performance on five training tasks before editing
the skills. A five-task run is an initial diagnostic, not a reliable estimate of
performance across the domain.

## 1. Prepare

```bash
uv sync --frozen
cp .env_example .env  # only if .env does not already exist
# Set RUNWARE_API_KEY in .env.
docker info
uv run stbench data pull
```

Docker must be running. Evaluation spends Runware credits. The baseline uses the
learner and limits in `hackathon.toml`.

## 2. Run the learner without a skill

Use a new output folder for each run; do not overwrite previous results.

```bash
uv run stbench eval --domain qf --arms baseline --limit 5 \
  --concurrency 1 --out runs/qf-baseline-v1
```

The harness selects the first five task names in sorted order. The `baseline`
arm mounts no submitted skill, so existing submissions can stay in place.

## 3. Review the first results

- `runs/qf-baseline-v1/eval_result.json`: selected tasks, scores, model, usage,
  and estimated cost.
- `runs/qf-baseline-v1/attempts.jsonl`: per-task outcomes and trajectory paths.
- `uv run harbor view runs/qf-baseline-v1/harbor-jobs`: learner trajectories.

Infrastructure errors are not learner failures. A run without `eval_result.json`
has not produced a completed baseline.

## 4. Make changes after the baseline completes

Review the learner's failures, then edit `submissions/octuple/qf/`. Keep the
learner configuration and harness fixed. Validate the skill:

```bash
uv run stbench check-skill submissions/octuple/qf
```

Use the exact task names recorded in the baseline for the next comparison:

```bash
TASKS=$(uv run python -c 'import json; print(",".join(json.load(open("runs/qf-baseline-v1/eval_result.json"))["tasks"]))')
uv run stbench eval --domain qf --arms baseline,placebo,skill \
  --skill submissions/octuple/qf --tasks "$TASKS" \
  --concurrency 1 --out runs/qf-v1-comparison
```

Compare both skill minus baseline and skill minus placebo. The leaderboard uses
skill minus placebo; training results only guide iteration.

## Full finance baseline

`scripts/run_finance_baseline.py` reuses the initial five results and runs the
remaining finance tasks sequentially, with one evaluation per task. This keeps
the fixed model settings and avoids combining all 54 tasks under one evaluation's
4-million-token budget. A single task exceeding that budget still stops the run.
Completed tasks are reused on restart; infrastructure failures stop the runner
and are not counted as failed answers.

On this machine, Docker group access and the temporary Buildx plugin are supplied
by this command (the plugin lives in `/tmp` and may need reinstalling after reboot):

```bash
sg docker -c 'DOCKER_CONFIG=/tmp/stbench-docker-tools/config PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -u scripts/run_finance_baseline.py'
```

With Docker permissions and Buildx installed normally, use:

```bash
uv run python scripts/run_finance_baseline.py
```

Read `runs/qf-baseline-all-v1/progress.json` for the completed count and partial
score. `runs/qf-baseline-all-v1/eval_result.json` is written only when every task
finishes. Per-task logs and results are under `runs/qf-baseline-all-v1/tasks/`.
The aggregate baseline score is the number of passes divided by all 54 tasks.
