#!/usr/bin/env python3
import json
import math
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

import qf_tool as q


class QFToolTests(unittest.TestCase):
    def test_fingerprint_cli_detects_changed_added_and_removed_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "output"
            root.mkdir()
            result = root / "result.json"
            result.write_text('{"value": 1}')
            extra = root / "extra.csv"
            extra.write_text('value\n1\n')
            snapshot = str(Path(tmp) / "before.json")
            argv = ["validate", str(root), "--required", "result.json"]
            with redirect_stdout(StringIO()):
                self.assertEqual(q.main(argv + ["--write-fingerprint", snapshot]), 0)
                self.assertEqual(q.main(argv + ["--compare-fingerprint", snapshot]), 0)
                result.write_text('{"value": 2}')
                self.assertEqual(q.main(argv + ["--compare-fingerprint", snapshot]), 1)
                result.write_text('{"value": 1}')
                added = root / "added.csv"
                added.write_text('value\n2\n')
                self.assertEqual(q.main(argv + ["--compare-fingerprint", snapshot]), 1)
                added.unlink()
                extra.unlink()
                self.assertEqual(q.main(argv + ["--compare-fingerprint", snapshot]), 1)
            with redirect_stderr(StringIO()):
                self.assertEqual(q.main(argv + ["--write-fingerprint", str(root / "bad.json")]), 2)
            self.assertFalse((root / "bad.json").exists())

    def test_returns_conventions(self):
        self.assertAlmostEqual(q.simple_returns([100, 110])[0], 0.1)
        self.assertAlmostEqual(q.log_returns([100, 110])[0], math.log(1.1))

    def test_annualization(self):
        rs = [0.01] * 12
        self.assertAlmostEqual(q.annualized_return(rs, 12, "arithmetic"), 0.12)
        self.assertAlmostEqual(q.annualized_return(rs, 12, "geometric"), 1.01 ** 12 - 1)
        self.assertAlmostEqual(q.annualized_volatility([1, 2, 3], 4, 1), 2.0)

    def test_drawdown(self):
        self.assertAlmostEqual(q.max_drawdown([0.1, -0.2, 0.05]), 0.2)
        self.assertAlmostEqual(q.max_drawdown([0.1, -0.2], False), -0.2)

    def test_covariance_ddof(self):
        rows = [[1, 2], [2, 4], [3, 6]]
        self.assertEqual(q.covariance_matrix(rows, 1), [[1, 2], [2, 4]])
        self.assertEqual(q.covariance_matrix(rows, 0), [[2/3, 4/3], [4/3, 8/3]])

    def test_weights_and_matrix_residuals(self):
        weights = q.normalize_weights([2, -1], 1, "gross")
        self.assertAlmostEqual(sum(abs(x) for x in weights), 1)
        check = q.exposure_check([0.6, 0.4], net=1, gross=1)
        self.assertTrue(check["ok"])
        self.assertTrue(q.matrix_diagnostics([[1, .2], [.2, 1]])["symmetric"])
        self.assertFalse(q.matrix_diagnostics([[1, .3], [.2, 1]])["symmetric"])

    def test_var_es_tail_orientation(self):
        result = q.historical_var_es([-0.10, -0.02, 0, 0.01], .75,
                                     input_kind="return", method="higher")
        self.assertAlmostEqual(result["var"], .10)
        self.assertAlmostEqual(result["es"], .10)

    def test_black_scholes_parity(self):
        c = q.black_scholes(100, 95, .5, .04, .3, "call", .01)
        p = q.black_scholes(100, 95, .5, .04, .3, "put", .01)
        residual = q.put_call_parity_residual(c["price"], p["price"], 100, 95, .5, .04, .01)
        self.assertAlmostEqual(residual, 0, places=11)
        self.assertGreater(c["gamma"], 0)

    def test_transition_and_hmm_normalization(self):
        self.assertEqual(q.normalize_probabilities([2, 3]), [.4, .6])
        self.assertTrue(q.transition_diagnostics([[.8, .2], [0, 1]], absorbing_index=1)["ok"])
        self.assertFalse(q.transition_diagnostics([[.8, .3], [0, 1]])["ok"])

    def test_date_window_inclusive(self):
        dates = ["2025-01-02", "2025-01-03", "2025-01-06"]
        self.assertEqual(q.inclusive_window(dates, dates[0], dates[1]), [0, 1])

    def test_json_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.json"
            with self.assertRaises(ValueError):
                q.write_json_strict(path, {"bad": math.nan})
            q.write_json_strict(path, {"ok": 1.25})
            self.assertEqual(json.loads(path.read_text()), {"ok": 1.25})

    def test_schema_and_repeatability(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            q.write_json_strict(root / "result.json", {"x": 1})
            (root / "table.csv").write_text("date,value\n2025-01-01,2.0\n")
            self.assertTrue(q.validate_outputs(root, ["result.json", "table.csv"])["ok"])
            self.assertEqual(q.directory_fingerprint(root), q.directory_fingerprint(root))

    def test_csv_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bad.csv").write_text("value\nNaN\n")
            result = q.validate_outputs(root, ["bad.csv"])
            self.assertFalse(result["ok"])
            self.assertIn("non-finite", result["errors"][0])

    def test_router_minimal_and_warns(self):
        result = q.route(["hmm"], ["annualization"], ["results.json"])
        self.assertIn("transition_diagnostics", result["helpers"])
        self.assertIn("annualized_return", result["helpers"])
        self.assertTrue(any("does not select" in x for x in result["misuse_warnings"]))


if __name__ == "__main__":
    unittest.main()
