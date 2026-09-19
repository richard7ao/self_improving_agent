# Tool-use patterns and antipatterns

## O1 — Route tools only to deterministic work

- **Observed symptom:** Tool-bearing skills add instructions, but ordinary advice tasks never invoke
  the script because the work is clinical judgment rather than mechanical validation.
- **Likely cause:** Scripts are added for completeness even when their coverage is narrow.
- **Positive pattern:** Use one standard-library checker only for explicit phrases, format, counts, or
  user-supplied section order; skip it for ordinary advice.
- **Antipattern:** Run clinical lint, diagnosis, triage, or treatment selection from keyword rules.
- **Evidence strength:** Strong runtime evidence for zero appropriate invocations; strong safety
  rationale against clinical automation.
- **Confidence:** 0.95.
- **Deterministic check/tool:** Audit trajectories for script command frequency, task route, latency,
  and whether a flagged constraint was actually corrected.
- **Next experiment:** Evaluate a bounded-artifact subset where the checker should activate and verify
  that it improves compliance enough to repay a tool turn.

## O2 — Separate successful usage from failed reserved charges

- **Observed symptom:** Evaluation summaries report very large completion-token totals despite normal
  answer sizes and trajectory output counts.
- **Likely cause:** Fail-closed gateway accounting adds reserved tokens from failed calls to successful
  completion usage.
- **Positive pattern:** Report successful prompt/completion/cache tokens, failed reserved charges,
  retries, and latency as separate fields attributed to task and arm.
- **Antipattern:** Treat aggregate charged tokens as model-generated output or as evidence about prompt
  efficiency.
- **Evidence strength:** Conclusive in the diagnosed run.
- **Confidence:** 0.99.
- **Deterministic check/tool:** Assert that summary generated-token totals reconcile with successful
  ledger entries; report but do not merge failed reservations.
- **Next experiment:** Add a curator-only ledger reconciliation command and test it against synthetic
  success, retry, and fail-closed fixtures.

## O3 — Protect the four-turn budget

- **Observed symptom:** Directory probes and cosmetic rewrites consume actions that could be needed for
  output creation or recovery.
- **Likely cause:** Generic agent workflow encourages exploration even for a single response file.
- **Positive pattern:** Write directly, revise only for a material defect, and finish; keep checker use
  to tasks with explicit mechanical constraints.
- **Antipattern:** List directories, inspect the injected skill again, self-test tools at task runtime,
  or repeatedly polish wording.
- **Evidence strength:** Strong trajectory evidence.
- **Confidence:** 0.96.
- **Deterministic check/tool:** Count actions before first write and alert when an attempt reaches the
  maximum without a finish call.
- **Next experiment:** Add a direct-write execution hint and measure response-write latency, action
  count, invalid outputs, and score.
