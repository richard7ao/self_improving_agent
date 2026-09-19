# Offline response-quality tools

All commands use only the Python standard library, cap input at one million bytes, read
JSON or UTF-8 from `--input FILE` (or stdin), and emit deterministic JSON. Run any tool's
`selftest` command before merging it.

| Tool | Input contract | Use | Do not use as |
|---|---|---|---|
| `evidence_ledger.py` | Object with `reported`, `explicitly_denied`, `unassessed` string arrays | Detect the same normalized item in multiple states | Proof that evidence is true or complete |
| `claim_audit.py` | Response text | Flag absolute/certainty wording for human review | Semantic or clinical certification |
| `coverage_check.py` | `text`, agent-supplied `required_concepts` and `required_clauses` | Check literal concept/clause coverage | A judge of relevance or correctness |
| `constraint_check.py` | Draft plus explicit literal/count/section constraints | Verify objective output form | A medical checker or default note schema |
| `urgency_ladder.py` | Agent-authored action/time/trigger mappings | Validate structure and uniqueness | A triage engine or urgency recommendation |
| `redaction_check.py` | Response text | Warn about obvious identifiers and secret-shaped strings | Proof of de-identification |
| `response_delivery.py` | UTF-8 draft file | Atomically deliver and verify an exact nonempty answer | A content validator |
| `workspace.py` | Full question text and per-question artifacts | Isolate work and archive only after delivery | A reason to expose or retain task content elsewhere |

Examples:

```bash
python response_tools/evidence_ledger.py check --input /tmp/evidence.json
python response_tools/claim_audit.py check --input /tmp/draft.txt
python response_tools/constraint_check.py check --input /tmp/contract.json
python response_tools/response_delivery.py deliver --draft /tmp/final.txt
python response_tools/workspace.py init --question-file /tmp/question.txt
python response_tools/workspace.py deliver --id QUESTION_ID
```

Invoke only the narrow tool justified by the current task. The warning tools never block
delivery by themselves. None contains medical facts, thresholds, task mappings, network
calls, or current-guideline claims.
