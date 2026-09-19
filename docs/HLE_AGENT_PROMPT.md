# HLE agent kickoff prompt

Copy the prompt below into the second agent's session.

```text
You own only the Octuple HLE submission in this repository:

  submissions/octuple/hle/

Your goal is to improve its held-out HLE score for the frozen learner configured in
hackathon.toml. Work autonomously, use subagents for independent experiments when useful,
and base changes only on public training-task evidence.

Start by reading AGENTS.md, README.md, docs/TEAMMATE_GUIDE.md, richard_metholody.md, and the
current submissions/octuple/hle/SKILL.md. Then run:

  git status --short --branch
  uv run stbench doctor
  uv run stbench check-skill submissions/octuple/hle
  uv run stbench tasks --domain hle | sed -n '1,20p'

Repository coordination rules:

- Another agent is working concurrently. Never use `git add .` or `git add -A`; stage only
  the exact HLE/docs files you intentionally changed.
- Do not edit health, qf, tau3, shared harness code, hackathon.toml, .env, dataset/, or runs/
  unless the user explicitly expands your scope.
- Preserve unrelated working-tree changes. Never reset or overwrite another agent's work.
- Push each tested, stable HLE commit and report its hash.

Benchmark integrity:

- Learn from public training tasks only. Never copy task text, reference answers, grader
  material, image-specific labels, or task-to-answer mappings into the skill.
- Skill tools must be offline and self-contained. No credentials, network calls, or
  external APIs.
- Use unique ignored directories under runs/ for every evaluation.

Development loop:

1. Establish a small baseline on a reproducibly selected task list. Use skill-only runs for
   fast candidate screening, but use baseline/placebo/skill for confirmation.
2. Review each trajectory. For every proposed change, record:
   - causal hypothesis;
   - exact score/token arithmetic used;
   - expected score delta;
   - confidence from 0 to 1 and why;
   - unresolved low-confidence calculations or reasoning steps.
3. Turn repeatable low-confidence deterministic work into a tested script under
   submissions/octuple/hle/scripts/ (or the isolated candidate folder first). Examples:
   arithmetic with Decimal/Fraction, finite enumeration, unit checks, reversible string
   transforms, constraint/format validation, or answer extraction. Route every tool from
   SKILL.md with explicit conditions for using and not using it.
4. Ask independent subagents for competing candidates or adversarial reviews. Give them
   tune artifacts only; keep validation tasks hidden during that cycle.
5. Score candidates on identical tune tasks. Validate only the best challenger and promote
   only a strict aggregate improvement. Preserve the incumbent on ties or regressions.
6. Challenge the methodology when evidence supports an experiment: try a shorter prompt,
   a tool-first version, a domain router, or stricter answer formatting. Keep the benchmark
   rules fixed and isolate each hypothesis so its effect is measurable.

HLE-specific priorities:

- Read `/app/instruction.md` and obey exact answer formatting.
- Separate factual recall uncertainty from deterministic calculation uncertainty.
- Use local code for calculations, enumeration, parsing, simulation, and reversible checks;
  do not use a script to hide an unjustified formula or premise.
- For images, inspect the supplied local image and distinguish visible evidence from
  inference.
- Make the final answer independently extractable and preserve units, precision, option
  labels, order, capitalization, and transformations.
- Keep the core SKILL.md concise enough that it does not crowd out the actual expert task.

Begin with one cheap experiment. Before any paid evaluation, state the exact task count,
arms, expected calls, and stopping rule. After it finishes, report per-task scores, token
and cost totals, wall-clock bottlenecks, what improved, what regressed, and the next
experiment. Do not claim general improvement from a tiny or noisy sample.

Before committing:

  uv run stbench check-skill submissions/octuple/hle
  git diff --check -- submissions/octuple/hle docs/HLE_AGENT_PROMPT.md
  git status --short

Stage only your explicit files.
```
