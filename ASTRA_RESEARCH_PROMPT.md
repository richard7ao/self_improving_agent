# Research Brief: Greenfield Self-Improving Health Skill Agent

## Instructions to the researcher

You are beginning with no prior context. Treat this document as the complete project brief.

Act as a senior research engineer specializing in autonomous agent improvement, automated
prompt and skill optimization, LLM evaluation, statistical experimentation, and
safety-critical healthcare AI.

First design the ideal system from first principles. Do not assume the existing
implementation is the correct architecture, and do not merely suggest incremental changes
to it. After producing the greenfield design, inspect the existing repository and compare it
against that ideal.

Repository:

<https://github.com/richard7ao/self_improving_agent>

Inspect the current `main` branch directly. Verify every claim about the implementation
against the code. Clearly distinguish:

1. what the repository already implements;
2. what is partially implemented;
3. what is missing; and
4. what should be redesigned rather than extended.

Do not reveal private chain-of-thought. Present conclusions, concise decision rationales,
calculations, assumptions, evidence, and citations.

## Project objective

The project is building an autonomous optimization system that improves an AI agent's
performance on health conversations.

The underlying learner model is frozen. Its weights, agent harness, model selection, task
limits, and graders cannot be changed for the final competition. The only artifact that may
improve is a mounted **skill folder**. The main entry point is `SKILL.md`; it may also contain
small reference files and offline helper scripts.

The intended loop is:

```text
Current health skill
        |
        v
Run the frozen learner on public training tasks
        |
        v
Inspect responses, scores, grader evidence, and trajectories
        |
        v
Diagnose general failure patterns
        |
        v
Generate several competing skill packages
        |
        v
Evaluate candidates under controlled experiments
        |
        v
Reject regressions and unsafe candidates
        |
        v
Promote a demonstrably better skill
        |
        +----------------------> repeat
```

This is skill or context optimization, not model-weight training. The final output is a
small, reusable instruction and tool package that helps a fixed learner answer previously
unseen health conversations better.

## Benchmark context

The relevant benchmark is HealthBench. Each task contains a patient-style or health-related
conversation. The frozen learner produces a response, and a separate model grader assigns a
fractional rubric score from 0 to 1.

The learner must generally produce responses that are:

- medically sensible and factually careful;
- responsive to the user's actual request and prior conversation;
- calibrated about uncertainty;
- appropriately urgent without indiscriminate escalation;
- actionable without practicing unsafe medicine;
- clear and useful to a non-expert;
- compliant with requested output constraints; and
- free from unsupported diagnoses, unsafe medication changes, and generic boilerplate.

The difficult behavior is contextual calibration. For example, a potential anaphylactic
reaction should receive immediate, prominent emergency guidance, while a low-risk question
should not receive the same alarmist response.

The system also supports other benchmark domains—quantitative finance, tool-using customer
service, and expert questions—but the primary research target is the health optimizer.

## Competition and integrity constraints

- The learner model is fixed.
- The learner agent harness is fixed.
- The grader and scored setup are fixed.
- Development may use only public training tasks.
- Final scoring uses private held-out tasks.
- Skills must not encode task-specific answers, grader rubrics, answer keys, patient details,
  or mappings extracted from the training dataset.
- A skill must generalize to unseen conversations.
- Skill tools must work offline inside a task container.
- Skill tools cannot use external APIs, credentials, or network services.
- A submitted skill may contain at most 200 files and 1,000,000 total bytes.
- Evaluation uses paid model inference, so token and dollar efficiency matter.
- Docker capacity is limited; some benchmark containers require substantial RAM.
- Optimization must remain auditable and reproducible.

## Evaluation arms

The evaluation harness can run the same task under three conditions:

1. **Baseline:** the frozen learner receives no skill.
2. **Placebo:** the learner receives generic advice such as reading carefully and checking
   its reasoning.
3. **Skill:** the learner receives the candidate skill folder.

The competition's important improvement signal is approximately:

```text
candidate skill score - placebo score
```

This is intended to measure domain-specific benefit rather than the generic benefit of
giving the model additional instructions.

## Fixed runtime configuration

At the time of this brief, the repository configures:

- learner model: `zai-glm-5-3-flash`;
- learner harness: `openhands-sdk`;
- pinned OpenHands version: `1.47.0`;
- health grader: `anthropic-claude-haiku-4-5`;
- upstream inference provider: Runware through an OpenAI-compatible API;
- default task concurrency: four Docker containers;
- health learner token pool: 2,000,000 tokens per evaluation;
- health grader token pool: 2,000,000 tokens per evaluation; and
- local execution: Python, `uv`, Harbor, Docker, FastAPI, and HTTPX.

Confirm these details against the current repository because configuration may evolve.

## Existing evaluation infrastructure

The repository contains a substantial evaluation harness. Its relevant responsibilities
include:

- downloading public task datasets from Hugging Face;
- validating task structure;
- validating skill structure and size;
- staging tasks in temporary directories;
- pinning container images and dependencies where supported;
- running Harbor trials in Docker;
- mounting a candidate skill read-only into the learner;
- retrying infrastructure failures but not wrong answers;
- running baseline, placebo, and skill arms;
- interpreting HealthBench fractional rewards;
- excluding invalidated grader results from paired comparisons;
- enforcing learner and auxiliary-model token pools;
- proxying model calls through local OpenAI-compatible gateways;
- retaining real provider credentials in the host process;
- recording token usage, estimated cost, latency, attempts, and trajectories;
- computing per-arm rates, raw deltas, placebo-adjusted deltas, and bootstrap intervals;
- writing machine-readable evaluation artifacts; and
- comparing evaluation and optimization results.

Important files to inspect include:

- `src/skilltrainbench/evaluate.py`
- `src/skilltrainbench/scoring.py`
- `src/skilltrainbench/gateway.py`
- `src/skilltrainbench/harbor.py`
- `src/skilltrainbench/tasks.py`
- `src/skilltrainbench/config.py`
- `hackathon.toml`

## Existing autonomous optimizer

The repository is not merely an evaluation harness. It already contains an evolutionary
optimizer exposed through `stbench optimize`.

The existing loop currently attempts to:

1. Choose a reproducible subset of public training tasks.
2. Split those tasks into tune and validation partitions.
3. Evaluate the incumbent skill on both partitions.
4. Give an optimizer model the current skill, tune-task context, learner answers, and scores.
5. Ask that model to produce a general failure review.
6. Generate several materially different complete skill-folder candidates concurrently.
7. Require candidates to return structured JSON containing a rationale, confidence,
   calculations, and files.
8. Restrict generated paths to `SKILL.md`, `references/`, and `scripts/`.
9. Reject malformed skills, unsafe paths, symlinks, excessive size, external endpoints,
   credential references, invalid Python syntax, unreferenced supporting files, and exact
   12-word passages copied from visible task material.
10. Score valid candidates on identical tune tasks.
11. Select the candidate with the highest tune score.
12. Evaluate only that challenger on the validation partition.
13. Calculate a task-count-weighted tune-plus-validation score.
14. Promote the challenger if that aggregate exceeds the incumbent by more than a configured
    minimum improvement.
15. Replace the live skill directory using a staged rename with a temporary backup.
16. Persist optimizer state, reviews, raw generations, evaluations, rationales, confidence,
    calculations, and promotion decisions.
17. Resume compatible interrupted optimization runs.
18. Delete losing candidate folders by default while retaining evaluation evidence.

Relevant files include:

- `src/skilltrainbench/optimize.py`
- `src/skilltrainbench/cli.py`
- `tests/test_optimize.py`
- `richard_metholody.md`
- `docs/TEAMMATE_GUIDE.md`
- `submissions/octuple/health/`

The current health skill emphasizes conversation continuity, exact task compliance,
calibrated clinical language, proportionate escalation, and an offline checker for literal
format constraints.

The repository has already committed multiple promoted health-skill versions. Therefore,
the research must treat autonomous optimization as an operating feature, not a hypothetical
future component.

## Questions and suspected limitations to verify

Do not assume the following observations are correct. Audit each one against the code and
report whether it is confirmed, partially correct, outdated, or false.

### Experimental validity

- The validation partition is drawn from public training data rather than a truly sealed
  distribution.
- A fixed validation partition is adaptively reused across rounds, allowing gradual
  overfitting through promotion decisions.
- Each candidate normally receives one stochastic learner and grader evaluation.
- Candidate selection among several noisy measurements creates a winner's-curse or
  multiple-comparisons problem.
- The incumbent is not necessarily re-evaluated alongside every challenger under matched
  randomness and temporal conditions.
- The learner evaluation does not appear to use controllable repeated seeds.
- The promotion default permits any positive measured improvement.
- Promotion does not require a confidence interval, posterior probability, or lower
  confidence bound above a practical threshold.
- Tune and validation results are combined into one weighted mean, so tune gains may offset
  a validation-only regression.
- The optimizer scores skill-only arms rather than directly optimizing placebo-adjusted
  improvement.
- Random task selection is not stratified by clinical category, difficulty, risk, or known
  failure mode.

### Safety and evaluation quality

- There is no separate non-compensatory gate for critical medical failures.
- Average score gains could theoretically hide a new emergency-triage or medication-safety
  regression.
- The reviewer receives answers and scores but may not consume detailed verifier verdicts,
  rubric-level evidence, or a structured failure taxonomy.
- LLM-as-judge bias, variance, position effects, verbosity bias, and correlated model errors
  are not explicitly measured.
- The same optimizer model may review failures and generate all candidates, creating
  correlated blind spots.
- Candidate diversity is requested in natural language but not measured or enforced.
- There is no optional clinician or human-safety approval gate before live promotion.

### Security, integrity, and operations

- Exact 12-word overlap detection may miss paraphrased or semantic task memorization while
  also producing edge-case false positives.
- Generated Python tools are parsed for syntax but are not comprehensively unit-tested,
  sandboxed, behaviorally inspected, or security-scanned before evaluation.
- Optimizer-model calls may not use the same token reservation, cost ledger, and hard budget
  controls as learner and grader calls.
- A process crash between replacing the live skill and persisting promotion state may leave
  ambiguous recovery state.
- Existing optimizer tests are primarily mocked unit tests rather than fault-injection,
  statistical-simulation, and paid end-to-end tests.
- Experiment provenance may not capture every code revision, dataset revision, container
  digest, model revision, prompt, environment property, and random source needed for exact
  reproduction.

## Greenfield research assignment

Design the strongest practical architecture for this project as if implementation were
starting today. The design must satisfy the competition constraints and work within limited
inference credits and local Docker capacity.

Do not begin with the existing optimizer's generate-N-and-select structure. Derive the
architecture from the objective, risk model, statistical requirements, and cost constraints.
Then determine whether the current approach should be retained, modified, or replaced.

Research relevant approaches, including but not limited to:

- automated prompt optimization;
- evolutionary prompt and program search;
- OPRO-style optimization;
- DSPy optimizers, including MIPRO-style methods;
- TextGrad and textual-gradient methods;
- PromptBreeder and self-referential improvement;
- Reflexion and verbal reinforcement learning;
- best-of-N search;
- beam search;
- population-based optimization;
- mutation and crossover;
- multi-armed bandits and adaptive resource allocation;
- successive halving and racing algorithms;
- Bayesian optimization;
- Pareto and constrained optimization;
- champion-challenger deployment;
- paired experimental designs and common random numbers;
- sequential testing;
- confidence-aware and Bayesian promotion rules;
- multiple-comparison correction and winner's-curse mitigation;
- adaptive holdout protection;
- LLM-as-judge reliability and calibration;
- evaluation contamination and semantic leakage detection;
- healthcare response safety evaluation;
- human review and rollback for safety-critical content; and
- experiment tracking, reproducibility, and provenance.

## Required research standards

Use current, high-quality primary sources wherever possible:

- original peer-reviewed papers or original preprints;
- official documentation and technical reports from AI laboratories;
- original benchmark papers;
- official standards from recognized standards bodies;
- primary healthcare AI safety guidance; and
- authoritative documentation for any proposed software framework.

Do not base important conclusions solely on blogs, marketing pages, secondary summaries, or
unsourced claims. Secondary sources may be used only for context or to locate primary work.

For every important recommendation, state:

- the evidence supporting it;
- whether the evidence is empirical, theoretical, operational, or expert guidance;
- expected benefit for this exact system;
- engineering complexity;
- inference and infrastructure cost;
- risks and tradeoffs;
- assumptions and confidence;
- how success would be measured; and
- whether it belongs in the minimum viable next version or a later mature version.

Clearly separate established practice from plausible but unproven experimentation.

## Required deliverables

### 1. Executive verdict

- Describe the problem in your own words.
- Classify the current repository's maturity.
- Identify what is already unusually strong.
- Identify the five most serious risks to genuine generalization.
- State whether the present system can credibly be called self-improving and under what
  definition.

### 2. Greenfield architecture

Design the ideal system independently of the current implementation. Include:

- an architecture diagram;
- components and responsibilities;
- data flow;
- control flow;
- trust boundaries;
- model separation;
- failure recovery;
- human-approval options;
- persistent state and provenance; and
- budget enforcement.

Define the roles of at least:

- experiment orchestrator;
- failure analyst;
- candidate generator;
- diversity manager;
- evaluator;
- medical safety critic;
- leakage and integrity checker;
- statistical promotion gate;
- experiment store;
- champion registry; and
- rollback manager.

Explain which roles should use separate models, independent prompts, deterministic code, or
human review.

### 3. Current-versus-ideal gap analysis

After designing the greenfield system, compare it with the repository. Provide a table with
at least these dimensions:

- search strategy;
- task sampling;
- candidate diversity;
- failure analysis;
- judge design;
- placebo controls;
- repeated trials;
- statistical promotion;
- health safety gates;
- leakage protection;
- generated-tool security;
- validation protection;
- cost controls;
- crash recovery;
- experiment memory;
- reproducibility;
- human oversight; and
- test coverage.

Reference exact repository files and relevant functions for implementation claims.

### 4. Statistical promotion protocol

Design a concrete, implementable protocol addressing:

- paired evaluation;
- repeated learner and grader trials;
- common random numbers where technically possible;
- continuous HealthBench scores;
- model and judge variance;
- candidate preselection;
- multiple comparisons;
- winner's curse;
- minimum detectable effect;
- practical versus statistical significance;
- confidence intervals or Bayesian posterior decisions;
- sequential stopping and futility;
- validation-only regression;
- placebo-adjusted lift;
- per-category effects;
- critical safety failures; and
- adaptive reuse of validation data.

Provide explicit equations, thresholds, or executable-style pseudocode. Recommend sensible
defaults for smoke tests, development runs, and final confirmation runs under limited credit.

### 5. Health-specific safety protocol

Design evaluation strata and non-compensatory regression gates for at least:

- emergency triage;
- medication contraindications and interactions;
- prescription starts, stops, tapers, and dose changes;
- pregnancy;
- pediatrics;
- older or medically complex patients;
- mental-health crisis and self-harm;
- dangerous reassurance;
- unsupported diagnosis;
- inappropriate treatment specificity;
- uncertainty calibration;
- contextual continuity;
- fabricated examination findings;
- failure to answer the user's actual request; and
- exact constrained-output compliance.

Specify which failures must never be offset by improvements elsewhere. Explain how to avoid
an overcautious system that sends every user to emergency care.

This is a benchmark-response system, not a deployed clinician. Clearly distinguish
benchmark optimization requirements from requirements that would apply to a real clinical
product.

### 6. Data and holdout strategy

Recommend a practical hierarchy such as:

- search or tune set;
- challenger-selection set;
- rotating validation set;
- sealed local confirmation set;
- safety regression suite;
- organizer private holdout.

Explain:

- how tasks should be stratified;
- what information each agent may see;
- how often each partition may be reused;
- how adaptive access consumes holdout validity;
- how to rotate or retire validation tasks;
- how to avoid leaking task-specific content into the skill; and
- what to do when the public dataset is too small for ideal partitioning.

### 7. Search-strategy recommendation

Compare the current survivor tournament against:

- best-of-N;
- beam search;
- population-based evolution;
- mutation and crossover;
- bandit allocation;
- successive halving;
- Bayesian optimization;
- textual-gradient methods;
- programmatic prompt optimizers; and
- constrained multi-objective or Pareto optimization.

Recommend the best approach for this exact combination of expensive Docker tasks, stochastic
LLM responses, model grading, limited credits, and a compact skill artifact. Consider a
hybrid strategy if justified.

### 8. Objective function

Propose a multi-objective definition of improvement that considers:

- HealthBench reward;
- placebo-adjusted lift;
- critical safety regressions;
- performance across clinical strata;
- response length;
- learner token use;
- grader and optimizer cost;
- latency;
- skill size and complexity;
- tool-call reliability; and
- robustness across repeated trials.

Explain which objectives should be optimized, constrained, or reported only.

### 9. Agent prompts and information boundaries

Recommend what the reviewer, generator, critic, and promotion system should receive. Address:

- whether the reviewer should see raw task text;
- whether it should see grader rubrics or verdicts;
- how to provide useful evidence without encouraging answer memorization;
- structured failure taxonomies;
- summaries versus raw trajectories;
- independent critics;
- prompt injection from task content;
- context-window limits; and
- provenance of generated claims.

Provide example input and output schemas, not full production prompts unless necessary.

### 10. Generated-tool security

Design a safe pipeline for optimizer-generated scripts, including:

- path restrictions;
- static analysis;
- dependency restrictions;
- forbidden APIs;
- sandboxed execution;
- generated unit tests;
- property tests;
- resource limits;
- malicious or accidental data access;
- deterministic behavior;
- skill routing checks; and
- evidence that a tool improves outcomes enough to justify its complexity.

### 11. Experiment and provenance schema

Define the fields that must be stored for every run and candidate, including:

- parent and candidate content hashes;
- Git revision and dirty-state fingerprint;
- dataset repository and immutable revision;
- task identifiers and partitions;
- learner, optimizer, and judge models;
- model parameters and seeds;
- prompts;
- container image digests;
- dependency lock hash;
- environment details;
- per-attempt scores and failure classes;
- token and dollar costs;
- confidence calculations;
- safety-gate results;
- promotion rationale;
- human approvals; and
- rollback relationships.

### 12. Reliability and testing plan

Specify:

- unit tests;
- property-based tests;
- parser fuzzing;
- statistical simulation tests;
- false-promotion-rate simulations;
- failure-injection tests;
- process-crash and recovery tests;
- partial-write tests;
- API timeout and malformed-response tests;
- Docker failure tests;
- leakage tests;
- generated-script security tests;
- judge-consistency tests;
- small paid integration tests; and
- complete end-to-end qualification runs.

For each category, state what failure it is intended to catch.

### 13. Implementation roadmap

Provide prioritized phases:

- **P0:** changes needed before trusting another automated promotion;
- **P1:** changes needed for a rigorous development system;
- **P2:** mature research and production-quality capabilities.

For every proposed change include:

- specific repository files or new components likely affected;
- data-model changes;
- algorithms and decision rules;
- tests required;
- migration and backward-compatibility concerns;
- approximate implementation effort;
- compute and inference-cost impact;
- expected reliability or quality improvement; and
- dependencies on earlier changes.

### 14. Concrete pseudocode

Provide detailed pseudocode for the recommended next-generation optimizer. It should be
specific enough to guide a rewrite or extension of `run_optimization`, including:

- task partitioning;
- incumbent measurement;
- failure review;
- candidate generation;
- candidate deduplication and diversity measurement;
- static and dynamic checks;
- adaptive evaluation allocation;
- finalist confirmation;
- safety gates;
- statistical promotion;
- transactional state persistence;
- optional human approval;
- live promotion;
- rollback; and
- stopping conditions.

### 15. Costed experiment plan

Propose the first experiments to run after implementing P0. Include:

- hypothesis;
- task count and stratification;
- number of candidates;
- repetitions;
- promotion threshold;
- approximate learner, grader, and optimizer call counts;
- stopping conditions;
- what evidence would confirm or reject the hypothesis; and
- how to prevent the experiment from contaminating later validation.

### 16. Annotated bibliography

Cite major claims close to the relevant text. Finish with an annotated bibliography of
primary sources containing:

- title;
- authors or issuing organization;
- publication date;
- direct link;
- source type;
- key finding;
- relevance to this repository; and
- important limitations.

## Desired final-answer structure

Use this order:

1. Executive summary
2. Problem definition and constraints
3. Evidence from the repository
4. Greenfield architecture
5. Current-versus-ideal comparison
6. Statistical design
7. Health-safety design
8. Data and holdout strategy
9. Search strategy
10. Security and integrity
11. Experiment tracking and operations
12. Testing strategy
13. Prioritized roadmap
14. Pseudocode
15. First experiments
16. Risks and unresolved questions
17. Annotated bibliography

The result should be technically rigorous and implementation-oriented. Avoid generic advice
such as “add monitoring,” “use more data,” or “include human oversight” unless you specify
the exact mechanism, trigger, owner, stored evidence, and decision rule.
