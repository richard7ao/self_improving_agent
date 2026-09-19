import json
from pathlib import Path
import tempfile
import unittest

from skilltrainbench.gateway import Ledger, tagged


class LedgerTests(unittest.TestCase):
    def test_sink_records_each_completed_call_with_summary_parity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run" / "ledger.jsonl"
            durable = Ledger(sink_path=path)
            memory = Ledger()
            rows = [
                {"status": "ok", "model": "test-model", "prompt_tokens": 7,
                 "completion_tokens": 3, "charged_tokens": 10, "cost_usd": 0.02,
                 "latency_ms": 100, "upstream_total_ms": 90},
                {"status": "error", "error_class": "ReadTimeout", "http_status": 0,
                 "reserved_tokens": 20, "charged_tokens": 20, "fail_closed": True,
                 "cost_usd": None, "latency_ms": 600000},
            ]
            with tagged(arm="skill"):
                for row in rows:
                    durable.record(row, tags={"task_id": "synthetic"})
                    memory.record(row, tags={"task_id": "synthetic"})
                    # Read before any final export: each completed request is durable.
                    persisted = [json.loads(line) for line in path.read_text().splitlines()]
                    self.assertEqual(persisted, memory.entries)
                    self.assertEqual(durable.summary(), memory.summary())
                    self.assertEqual(path.read_text(), durable.to_jsonl())
            self.assertEqual(durable.summary()["total_charged"], 30)
            self.assertEqual(durable.summary()["cost"]["estimated_usd"], 0.02)
            self.assertTrue(durable.summary()["cost"]["incomplete"])

    def test_sink_preserves_existing_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.jsonl"
            existing = b'{"seq":0,"status":"ok","cost_usd":0.5}\n'
            path.write_bytes(existing)
            ledger = Ledger(sink_path=str(path))
            self.assertEqual(path.read_bytes(), existing)
            ledger.record({"status": "budget_rejected", "charged_tokens": 0})
            self.assertEqual(path.read_bytes(), existing + ledger.to_jsonl().encode())
            self.assertEqual(ledger.summary()["n_calls"], 1)

    def test_unknown_cost_includes_charged_errors_but_not_free_rejections(self):
        cases = [
            ({"status": "error", "fail_closed": True, "charged_tokens": 20}, True),
            ({"status": "error", "fail_closed": True, "charged_tokens": 0}, True),
            ({"status": "error", "charged_tokens": 20}, True),
            ({"status": "error", "charged_tokens": 20, "cost_usd": 0.01}, False),
            ({"status": "budget_rejected", "http_status": 402, "charged_tokens": 0}, False),
            ({"status": "upstream_error", "http_status": 402, "charged_tokens": 0}, False),
            ({"status": "invalid_request", "charged_tokens": 0}, False),
            ({"status": "error", "charged_tokens": 0}, False),
            ({"status": "ok", "charged_tokens": 0}, True),
            ({"status": "fail_closed", "charged_tokens": 0}, True),
        ]
        for row, expected in cases:
            with self.subTest(row=row):
                ledger = Ledger()
                ledger.record(row)
                self.assertEqual(ledger.summary()["cost"]["incomplete"], expected)

    def test_sink_io_failure_keeps_accounting_without_failing_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Ledger(sink_path=Path(tmp))  # A directory cannot be appended to.
            with self.assertLogs("skilltrainbench.gateway", level="ERROR") as logs:
                ledger.record({"status": "ok", "charged_tokens": 5, "cost_usd": 0.01})
            self.assertIn("row retained in memory", logs.output[0])
            self.assertEqual(ledger.summary()["total_charged"], 5)
            self.assertEqual(ledger.summary()["cost"]["estimated_usd"], 0.01)


if __name__ == "__main__":
    unittest.main()
