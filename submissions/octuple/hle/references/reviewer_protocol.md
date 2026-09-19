# Skeptical reviewer protocol

Assume the proposed answer is wrong. Find the first unsupported inference and the
strongest competitor. Check necessity separately from sufficiency, uniqueness
separately from existence, unused variables, hidden assumptions, units, signs,
symmetries, and boundary/degenerate cases. Approve only if no material counterexample
survives.

For conceptual questions, label the decisive support as definition, deduction,
empirical evidence, recall, or analogy. An analogy cannot close a missing existence,
well-definedness, consistency, or entailment step. If no deterministic check applies,
the reviewer must still compare the exact claims rather than marking a coherent story
as verified.

The structured review passed to `scripts/hle_review.py` contains:

- `classification`: domain, task types, answer type, image flag, and features;
- `interpreted_question`, `proposed_answer`, and `strongest_competitor`;
- `variables`: objects with `name`, `role`, `explained`, and `reason`;
- `assumptions` and optional unresolved `conventions`;
- `derivation`, `sufficiency`, `necessity`, and `uniqueness` status records;
- `counterexamples_attempted`, each with `kind`, `outcome`, and `evidence`;
- `confidence`, `final_format`, and justified deterministic `checks`.

Statuses are `passed`, `failed`, `missing`, `partial`, `unresolved`, or
`not_applicable`. Counterexample outcomes are `refuted`, `survived`, or
`inconclusive`. The dispatcher applies confidence caps and returns a compact approval
report; it cannot certify the domain premise.
