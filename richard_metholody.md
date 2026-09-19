# Richard's Skill-Improvement Methodology

## Objective

Build the strongest general-purpose HealthBench skill for the fixed hackathon learner.
The learner model, task harness, grader, and budgets remain unchanged. The only artifact
that evolves is the skill folder mounted into the learner:

```text
submissions/octuple/health/
├── SKILL.md
├── references/       # optional focused knowledge or checklists
└── scripts/          # optional deterministic, offline tools
```

The methodology treats skill development as a measured search problem. Several competing
skill prompts are generated, each is tested against the same public training tasks, and
only a demonstrably better candidate replaces the live skill.

## Design influence

The skill layout follows the pattern used by
[Anthropic's public XLSX skill](https://github.com/anthropics/skills/tree/main/skills/xlsx):

- `SKILL.md` is the concise entry point and router.
- Essential rules stay in the entry point because the agent must always see them.
- Detailed or conditional guidance moves into `references/`.
- Repeated deterministic work moves into `scripts/`.
- `SKILL.md` explicitly tells the agent when and how to use each supporting resource.

This progressive-disclosure design avoids turning the main prompt into a long reference
manual while still giving the agent reliable procedures and tools when they are useful.

## The optimization loop

```text
                         ┌──────────────────────────────┐
                         │ Live health skill (survivor) │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         Evaluate on fixed training split
                                        │
                                        ▼
                     Review scores, responses, and failure patterns
                                        │
                                        ▼
                  Generate N distinct complete skill-folder candidates
                         │              │              │
                         ▼              ▼              ▼
                      Skill A        Skill B        Skill C
                         │              │              │
                         └──── score on identical tune tasks ────┘
                                        │
                                        ▼
                              Best tune challenger
                                        │
                                        ▼
                            Verify on validation tasks
                                        │
                       ┌────────────────┴────────────────┐
                       │                                 │
                score improves                    no improvement
                       │                                 │
                       ▼                                 ▼
              promote atomically                 keep incumbent
                       │                                 │
                       └──────── discard losers ─────────┘
                                        │
                                        ▼
                                  next round
```

### 1. Select tasks once

The harness chooses a reproducible subset of public training tasks using `--seed`. It
splits them into:

- **Tune tasks:** every candidate is scored here. These make iteration affordable.
- **Validation tasks:** only the best challenger is scored here. These reduce the chance
  of promoting a prompt that merely overfits the tune examples.

Every candidate within a run sees the same task split. This makes comparisons paired and
removes task selection as a source of variance.

### 2. Measure the incumbent

The current `submissions/octuple/health` folder is evaluated before any mutation. Its
HealthBench rubric fraction is the incumbent score and the promotion threshold for the
entire run.

HealthBench produces a continuous rubric score from 0 to 1, not simple binary accuracy.
In this methodology, “accuracy” means the mean rubric score across the selected tasks.

### 3. Review failures

The reviewer receives:

- the current skill files;
- aggregate and per-task scores; and
- the learner's responses from the tune attempts.

It looks for recurring, general causes of lost score: missed safety language, weak
uncertainty calibration, poor prioritization, incomplete escalation criteria, excessive
verbosity, or failure to answer the user's actual question. The review proposes several
competing hypotheses rather than assuming one large rewrite is correct.

The reviewer is explicitly prohibited from copying task text, patient details, grading
rubrics, reference answers, or dataset-specific mappings into the skill.

### 4. Generate diverse skill packages

The skill changer creates multiple candidates from the review. Each model response is a
structured package containing a complete `SKILL.md` and, when justified, supporting
files. Candidates are asked to pursue materially different hypotheses so the tournament
tests alternatives rather than superficial rewrites of the same prompt.

A candidate may add:

- a focused response-planning checklist;
- a reference for risk communication or triage structure;
- a small offline Python tool for a deterministic calculation or text check; or
- another reusable resource that changes the learner's decisions.

It may not add network calls, credentials, external service dependencies, hidden task
answers, or files outside `SKILL.md`, `references/`, and `scripts/`.

### 5. Validate before spending evaluation budget

Every generated candidate goes through static checks before it reaches the learner:

- required YAML frontmatter and root `SKILL.md`;
- safe relative paths only;
- no symlinks;
- repository file-count and byte limits;
- no external endpoint or API-key warnings; and
- Python syntax checks for generated `.py` files.

Malformed or unsafe candidates are rejected without running benchmark tasks.

### 6. Run the tournament

All valid candidates run through the existing `stbench eval` machinery with the frozen
learner and the pinned HealthBench grader. Candidates are ranked by mean tune score. Only
the top tune candidate spends validation budget.

The challenger is promoted only when its task-count-weighted tune plus validation score
exceeds the incumbent by more than `--min-improvement` and its validation score strictly
improves. A validation tie or regression never replaces the incumbent.
This is an elitist survivor strategy: the live skill cannot regress according to the run's
fixed evaluation set.

### 7. Promote safely and discard losers

Promotion replaces the live skill directory atomically and preserves the previous folder
until the replacement succeeds. Losing candidate folders are removed by default. The run
keeps compact metadata containing scores, rationales, promotion decisions, and reviewer
reports so the search remains auditable without accumulating obsolete skills.

Use `--keep-candidates` only while debugging generation behavior.

## Running the health optimizer

Start with a small, inexpensive experiment:

```bash
uv run stbench optimize \
  --domain health \
  --skill submissions/octuple/health \
  --out runs/octuple-health-001 \
  --iterations 2 \
  --candidates 3 \
  --limit 8 \
  --validation-fraction 0.25 \
  --concurrency 4 \
  --candidate-parallelism 3 \
  --seed 42
```

The command uses the configured learner model for review and mutation unless
`--optimizer-model` selects another OpenAI-compatible model. It reads the same upstream
connection and credential configuration as `stbench eval`.

Candidate generation and candidate scoring run concurrently. The harness divides
`--concurrency` task-container slots among concurrent candidate evaluations so ordinary
runs do not multiply the intended Docker load. `--candidate-parallelism` can be raised on
a larger host or lowered when memory is constrained. Health tasks are relatively light;
for the default three candidates and four container slots, parallel candidate scoring is
usually the fastest useful setting.

Once the loop is working, increase tasks before increasing candidate count. More tasks
usually improve selection confidence more than many variants scored on a tiny sample.

## Run artifacts

Each run writes a self-contained record below its `--out` directory:

```text
runs/octuple-health-001/
├── optimization.json          # split, scores, candidates, promotions
├── initial/                   # incumbent tune/validation evaluations
└── round-01/
    ├── review.txt             # general failure analysis
    ├── eval-candidate-01/     # benchmark outputs and trajectories
    ├── eval-candidate-02/
    ├── eval-candidate-03/
    └── validation/            # best challenger's validation result
```

Each evaluation directory contains `eval_result.json`, `attempts.jsonl`, token ledgers,
and Harbor trajectories. These are the evidence for why a candidate won or lost.

## Principles for reliable improvement

1. **Optimize general behavior, not remembered examples.** Training failures reveal a
   class of mistake; the skill should address that class.
2. **Keep comparisons paired.** Never compare candidates evaluated on different tasks.
3. **Protect a validation slice.** Candidate generation must not receive validation
   responses during the same run.
4. **Prefer small causal changes.** Concise rules are easier to attribute and less likely
   to crowd out the patient conversation.
5. **Use scripts for determinism, not decoration.** A tool earns its place only if it
   reliably performs work the model would otherwise repeat or get wrong.
6. **Never promote on a tie.** Model-graded evaluations contain noise; use a positive
   `--min-improvement` when enough tasks are available.
7. **Re-test the final survivor broadly.** The optimization score guides development; a
   larger fresh training sample is the final local check before submission.

## Recommended progression

- **Smoke test:** 1 round, 2 candidates, 4 tasks.
- **Development run:** 2–4 rounds, 3 candidates, 8–16 tasks.
- **Confirmation run:** evaluate the survivor on a larger task set with baseline, placebo,
  and skill arms.
- **Submission check:** run `uv run stbench check-skill submissions/octuple/health` and
  inspect every warning before committing.

The final confirmation should use a new task selection seed or explicitly named tasks not
used for the last optimization run. That does not create a true private holdout, but it is
a stronger generalization check than reporting the tournament score alone.

## Limitations and next improvements

The methodology is intentionally conservative, but one evaluation per candidate is still
noisy: learner sampling and a model grader can vary between attempts. Testing many
candidates also creates a winner's-curse effect—the best observed score may partly reflect
luck. A mature version should re-run the top one or two finalists with additional seeds
and promote on their mean score or a confidence-aware lower bound.

The validation slice is protected from the changer during a run, but it still comes from
the public training distribution and becomes known to the controller after scoring. Use a
fresh seed for confirmation and do not repeatedly optimize against the same validation
tasks across many runs.

Finally, scripts are less naturally useful for conversational HealthBench tasks than for
spreadsheet or coding domains. The changer may create them, but selection should favor a
script only when it supplies deterministic value—such as a local calculation or format
check. Most health gains are more likely to come from better prioritization, factual
precision, uncertainty calibration, and strict instruction following.
