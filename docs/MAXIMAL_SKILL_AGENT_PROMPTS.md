# Maximal skill construction prompts

These prompts intentionally create broad source packages first. They do not authorize
replacing the live submissions. Compression and promotion happen in a later phase.

## Health agent prompt

```text
Build the largest useful, general-purpose Health skill source package you can justify. Do
not compress, shorten, or optimize for the learner's context budget yet. We will reduce it
only after the maximal package and its full inventory exist.

Work only in a new ignored directory:

  runs/health-maximal-source-20260919-001/

Do not edit or replace `submissions/octuple/health/`. Another agent may be working in the
same repository, so never stage broad paths, reset files, or overwrite unrelated work.

Read `AGENTS.md`, `README.md`, `richard_metholody.md`, `docs/TEAMMATE_GUIDE.md`, the current
Health submission, `health-skill-agent-research.md`, and relevant completed Health run
artifacts before building. Run `git status --short --branch` and `uv run stbench doctor`
first. Do not launch a paid evaluation while another benchmark process is active.

Goal for this phase

Create an intentionally comprehensive source library containing every reusable Health
response mechanism, decision checklist, reference, and deterministic offline helper that
could plausibly improve held-out performance. Breadth is desired in this phase. Do not
remove material merely because it is too large for runtime. Do not copy benchmark task
text, patient details, rubrics, answers, grader wording, or task-to-answer mappings.

Required package structure

- `SKILL.md`: a maximal router and complete top-level protocol. It may be long in this
  source phase.
- `references/INDEX.md`: routes every reference and explains when not to load it.
- Focused references covering, where justified: conversation continuity, sparse context,
  bounded artifacts, symptom assessment, treatment decisions, medication safety, test and
  record interpretation, uncertainty calibration, escalation levels, emergency ordering,
  pediatrics, pregnancy, older/complex patients, mental-health crisis, documentation
  integrity, response completeness, and delivery reliability.
- `scripts/`: deterministic offline tools for work that is genuinely mechanical, such as
  exact-format validation, response delivery verification, arithmetic/unit checks,
  structured evidence-state validation, constraint parsing, and package self-audit.
- `tests/` or a development-only test area beside the package for every script. Tests must
  include boundary, malformed-input, Unicode, timeout, and conflicting-constraint cases
  where relevant.
- `MANIFEST.md`: every file, purpose, trigger, dependencies, expected benefit, likely harm,
  confidence from 0 to 1, evidence basis, and whether it must survive final compression.
- `REDUCTION_MAP.md`: do not reduce now; identify future tiers such as `essential`,
  `conditional`, `experimental`, and `remove-first`, plus dependency relationships.

Construction rules

1. Start broad. Write the complete ideal behavior library before considering size.
2. Keep clinical facts general and reusable. Prefer decision procedures and evidence
   boundaries over encyclopedic treatment tables.
3. Do not invent medical guidance or include instructions that direct unsupported
   prescription starts, stops, tapers, or individualized doses.
4. Every reference and script must be explicitly routed from `SKILL.md` with conditions for
   use and non-use, even though the maximal router will later be compressed.
5. Scripts must use only the standard library unless the frozen environment already
   guarantees a dependency. They must not use network access, credentials, model gateways,
   shell execution, dynamic code execution, or unrestricted filesystem traversal.
6. A tool may calculate or validate mechanics; it must not pretend to make clinical
   judgments. Record low-confidence clinical decisions as review points rather than code.
7. For every design decision, record a concise rationale, assumptions, counterhypothesis,
   calculations, confidence, expected score mechanism, and failure mode. Do not request or
   store private chain-of-thought.
8. Preserve the maximal package byte-for-byte once complete. Do not overwrite it during
   later compression; compressed candidates must be copied to new directories.

Research rules

- Public primary medical guidance may inform general response principles, but do not add
  external benchmark cases, example patients, answer keys, or dataset-derived mappings.
- Cite sources in development documentation. The runtime skill should contain only what
  materially assists the learner.
- Clearly distinguish sourced clinical principles, repository evidence, and untested
  hypotheses.

Verification for the maximal source

- Run every script's independent tests and self-tests.
- Run static syntax, path, dependency, network/capability, and deterministic-output checks.
- Run `uv run stbench check-skill` and record all failures, including expected size/file
  warnings. Do not shrink the package to make this check pass during this phase.
- Measure total files, bytes, `SKILL.md` words/tokens, routed-reference count, and script
  count.
- Do not promote this package and do not run it on the reserved confirmation tasks.
- Because the learner has only four iterations, explicitly predict which maximal workflows
  would exceed that limit. Keep them anyway, but mark them `remove-first` or `merge` in the
  reduction map.

Before finishing, deliver:

1. the untouched maximal package;
2. its complete manifest;
3. test and static-analysis results;
4. exact file/byte/token measurements;
5. the reduction map, without performing the reduction;
6. the three highest-value and three highest-risk components;
7. an explicit statement that the live Health submission was not changed.

Do not commit `runs/`. If you change any tracked development documentation, stage only the
exact file after showing `git diff --cached`.
```

## HLE agent prompt

```text
Build the largest useful, general-purpose HLE skill source package you can justify. Do not
compress, shorten, or optimize for the learner's context budget yet. We will reduce it only
after the maximal package and its full inventory exist.

Work only in a new ignored directory:

  runs/hle-maximal-source-20260919-001/

Do not edit or replace `submissions/octuple/hle/`. Another agent may be working in the same
repository, so never stage broad paths, reset files, or overwrite unrelated work.

Read `AGENTS.md`, `README.md`, `richard_metholody.md`, `docs/TEAMMATE_GUIDE.md`, the current
HLE submission, HLE learning notes, and relevant completed HLE run artifacts before
building. Run `git status --short --branch` and `uv run stbench doctor` first. Do not launch
a paid evaluation while another benchmark process is active.

Goal for this phase

Create an intentionally comprehensive source library containing every reusable HLE problem-
solving protocol, domain router, verification method, adversarial check, answer-format rule,
and deterministic offline helper that could plausibly improve held-out performance. Breadth
is desired in this phase. Do not remove material merely because it is too large for runtime.
Never copy public task text, reference answers, grader material, image-specific labels, or
task-to-answer mappings into the package.

Required package structure

- `SKILL.md`: a maximal router and complete top-level solving protocol. It may be long in
  this source phase.
- `references/INDEX.md`: routes every reference and explains when not to load it.
- Focused references for mathematics, probability/statistics, physics, chemistry,
  engineering, computer science/AI, algorithms, logic, multiple choice, exact-match
  questions, image-grounded problems, symbolic derivation, numerical estimation,
  literature/factual recall uncertainty, counterexample construction, and final-answer
  extraction.
- `scripts/`: deterministic offline tools for arithmetic with Decimal/Fraction, symbolic or
  numerical checking where local libraries permit, finite enumeration, unit/dimension
  validation, graph/constraint search, reversible text transforms, option comparison,
  answer-format validation, image metadata inspection, and atomic response delivery.
- `tests/` or a development-only test area beside the package for every script, including
  malformed, adversarial, boundary, precision, timeout, Unicode, and empty-output cases.
- `MANIFEST.md`: every file, purpose, trigger, dependencies, expected benefit, likely harm,
  confidence from 0 to 1, evidence basis, and whether it must survive final compression.
- `REDUCTION_MAP.md`: do not reduce now; classify components as `essential`, `conditional`,
  `experimental`, or `remove-first`, and record dependencies.

Construction rules

1. Start broad. Build the complete ideal library before considering size.
2. Include methods, checks, and reusable derivations, not benchmark-specific facts or
   memorized answers.
3. Every reference and script must be explicitly routed from `SKILL.md` with use and non-use
   conditions.
4. Separate necessary and sufficient arguments, assumptions and conclusions, and factual-
   recall uncertainty from calculation uncertainty.
5. Require the solver to test its strongest competing answer, check whether every supplied
   variable matters, construct counterexamples to claimed bounds, verify units and limiting
   cases, and preserve exact requested output conventions.
6. Scripts must be offline and self-contained. No credentials, external APIs, model calls,
   network access, package installation, or task/reference lookup tables.
7. A script must expose a declared deterministic contract and independently testable
   oracle. Do not encode an unsupported premise or formula merely to make it deterministic.
8. For every design decision, record concise rationale, evidence, assumptions,
   counterhypothesis, calculation, confidence from 0 to 1, expected score mechanism, and
   failure mode. Do not request or store private chain-of-thought.
9. Preserve the maximal package byte-for-byte when complete. Later compressed candidates
   must be copies in new directories.

Verification for the maximal source

- Run all independent tests and script self-tests.
- Run static syntax, path, dependency, network/capability, determinism, and bounded-runtime
  checks.
- Run `uv run stbench check-skill` and record every failure, including expected size/file
  warnings. Do not shrink the package merely to pass during this phase.
- Measure total files, bytes, `SKILL.md` words/tokens, routed-reference count, and script
  count.
- Do not promote this package and do not run it on the reserved HLE confirmation tasks.
- Explicitly predict which workflows risk exceeding the 50-iteration HLE limit or getting
  trapped in tool loops. Keep them in the source library but flag them in the reduction map.

Before finishing, deliver:

1. the untouched maximal package;
2. its complete manifest;
3. test and static-analysis results;
4. exact file/byte/token measurements;
5. the reduction map, without performing the reduction;
6. the three highest-value and three highest-risk components;
7. an explicit statement that the live HLE submission was not changed.

Do not commit `runs/`. If you change tracked development documentation, stage only the exact
file after showing `git diff --cached`.
```
