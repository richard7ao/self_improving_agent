# Isolated QF timing candidate

`timing.patch` preserves the exact SKILL.md-only change from the live skill at
commit `8c9d76a` to `runs/qf-original-timing-20260919T170311Z/skill`.
All references and scripts are unchanged. The rule checks information availability
before credited returns and requires tracing signal/execution indices without
imposing a universal lag.

## Apply to an isolated copy

Run from the repository root. Choose a new, unused directory under ignored `runs/`:

```bash
candidate_dir="runs/qf-timing-reproduce-$(date -u +%Y%m%dT%H%M%SZ)/skill"
mkdir -p "$candidate_dir"
git archive 8c9d76a submissions/octuple/qf | tar -x -C "$candidate_dir" --strip-components=3
patch -d "$candidate_dir" -p1 < docs/qf-candidates/timing.patch
uv run stbench check-skill "$candidate_dir"
PYTHONDONTWRITEBYTECODE=1 uv run python "$candidate_dir/scripts/test_qf_tool.py"
```

Expected package digest (`skilltrainbench.optimizer_tools.skill_digest`):

```text
9e4d063aa0ee93c80002f3f8df149a1d6fb43b6add61d5e33bcac426f1f34977
```

## Training evidence and limits

On the public training task `alpha-hedge-strategy`, the preceding original-base
accounting skill scored **0/1**; the timing candidate scored **1/1**.
The timing evaluation recorded **152,676 learner tokens** and estimated learner
cost **$0.01008204**. This is one task and one attempt per version; it is not a
held-out result or a confirmed generalization gain. Reserved validation has not occurred. The user subsequently selected this timing
rule for the active submission, combined with the independently verified numerical
helper fix. That combined package has not itself been benchmarked; the patch here
reproduces the exact original timing-only evaluation.

Pre-evaluation checks passed: skill validation, 14 offline helper tests,
generated-script audit, and a mechanical 12-word overlap scan against all 54 public
QF instructions. These checks do not certify absence of all leakage or establish
benchmark improvement beyond the stated training result.
