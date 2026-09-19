# Delivery patterns and antipatterns

## D1 — Spend turns on the answer

- **Observed symptom:** The agent consumes a tool turn listing or creating an output directory before
  writing a file that the editor can create directly.
- **Likely cause:** Generic repository-agent habits override the simple response-file contract.
- **Positive pattern:** Create the final response in the first action when possible, reserve at most
  one action for a necessary revision, then finish.
- **Antipattern:** Probe directories, inspect unrelated files, or create a plan for a one-file reply.
- **Evidence strength:** Strong across multiple trajectories.
- **Confidence:** 0.96.
- **Deterministic check/tool:** Count pre-write tool calls and flag any unrelated to producing the
  required output.
- **Next experiment:** Add one short execution instruction and compare pre-write calls, total prompt
  replay, completion rate, and score on identical tasks.

## D2 — Optimize relevance, not a universal word limit

- **Observed symptom:** Longer replies sometimes repeat conclusions and low-value details, while some
  shorter replies omit decision-changing branches.
- **Likely cause:** Length is used as a proxy for either completeness or concision.
- **Positive pattern:** Preserve the direct answer, reasoning needed to trust it, next action, time
  frame, and relevant safety boundary; delete everything else.
- **Antipattern:** Enforce a hard short answer or reward length without evaluating informational value.
- **Evidence strength:** Moderate; length and score varied by request type.
- **Confidence:** 0.74.
- **Deterministic check/tool:** Word, paragraph, bullet, and repeated-paragraph counts can warn but
  must not gate ordinary advice.
- **Next experiment:** Compare a relevance checklist against a soft length target on a broader paired
  task set.
