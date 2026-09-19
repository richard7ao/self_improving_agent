# Offline health data tools

These standard-library commands transform only caller-supplied data. They do not diagnose, triage,
select treatments, check interactions, interpret clinical meaning, or retrieve external knowledge.
Each accepts a JSON object from `--input FILE` or stdin and prints JSON to stdout. Input is capped at
1,000,000 bytes; per-tool collection limits are documented below. Errors are JSON and exit with code
2. Run any tool with `--self-test` to execute its built-in tests.

## Routing

Use a tool only when its deterministic output directly supports the requested work:

- `timeline_normalizer.py`: separate and order explicit ISO timestamps, explicit numeric relative
  ranks, and unplaced events. It never converts vague time language into a date.
- `lab_trend.py`: calculate adjacent and overall numeric changes for one same-unit series already in
  the intended order. It rejects mixed units and does not interpret direction.
- `medication_reconcile.py`: case-sensitive exact-string deduplication and previous/current list diff.
  It makes no drug-equivalence, interaction, dose, indication, or safety claim.
- `unit_math.py`: explicit mass, volume, length, temperature conversions and basic arithmetic. It
  performs no clinical interpretation.
- `dose_math.py`: multiply caller-supplied weight and per-weight amount, optionally divide by a
  supplied concentration and multiply by supplied daily frequency. It never chooses or validates an
  input and always returns a not-a-prescription warning.
- `record_summary.py`: preserve caller-supplied section order and values, then report required fields
  that are absent, null, or empty. It never fills gaps.

Do not use these commands to decide diagnosis, urgency, a medication or dose, a contraindication, a
drug interaction, or the meaning of a result. Do not silently repair units or malformed inputs.

## Commands

```bash
python timeline_normalizer.py --input payload.json
python lab_trend.py --input payload.json
python medication_reconcile.py --input payload.json
python unit_math.py --input payload.json
python dose_math.py --input payload.json
python record_summary.py --input payload.json
```

From stdin:

```bash
printf '%s' '{"operation":"add","left":2,"right":3}' | python unit_math.py
```

Self-tests:

```bash
for tool in timeline_normalizer.py lab_trend.py medication_reconcile.py unit_math.py dose_math.py record_summary.py; do
  python "$tool" --self-test
done
```

## Input contracts

### Timeline normalizer

```json
{"events":[{"id":"e1","label":"first","timestamp":"2025-01-01"},{"id":"e2","label":"later","order":2},{"id":"e3","label":"unknown","when_text":"recently"}]}
```

Maximum 500 events. `timestamp` accepts ISO dates or datetimes; timezone-aware datetimes are ordered
in UTC, and aware and naive datetimes cannot be mixed. An event without `timestamp` may use numeric
`order`; otherwise it remains unplaced. A single event cannot contain both. Absolute and relative
groups are not merged.

### Lab trend

```json
{"series":"marker","observations":[{"label":"first","value":10,"unit":"u"},{"label":"second","value":12,"unit":"u"}]}
```

Maximum 500 observations. Units must match exactly. Percent change is null when the earlier value is
zero. Observation order is never changed.

### Medication reconcile

```json
{"previous":["Alpha 1 mg","Beta"],"current":["Beta","Gamma"]}
```

Maximum 500 strings per list. Equality is exact and case-sensitive; similar spellings remain distinct.

### Unit math

Conversion:

```json
{"operation":"convert","value":1,"from_unit":"kg","to_unit":"g"}
```

Supported scale units are `kg`, `g`, `mg`, `ug`, `l`, `ml`, `ul`, `m`, `cm`, and `mm`; `c` and `f`
are supported for temperature. Arithmetic operations are `add`, `subtract`, `multiply`, `divide`, and
`percent_change`, with numeric `left` and `right`.

### Dose math

```json
{"weight_kg":20,"amount_per_kg":5,"amount_unit":"mg","concentration_amount_per_ml":10,"administrations_per_day":2}
```

`weight_kg` and `amount_per_kg` are required nonnegative numbers. Optional concentration must be
greater than zero. Supported amount labels are `mg`, `mcg`, and `g`; the script does not convert them.

### Record summary

```json
{"sections":[{"name":"Overview","fields":{"present":"supplied value"},"required_fields":["present","missing"]}]}
```

Maximum 100 sections and 200 fields per section. Field values are preserved as JSON. Only absent,
null, and empty-string required values are reported missing; zero and false are preserved as present.
