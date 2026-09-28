"""SOCO's FERC-714 system-lambda price benchmark (lane soco-84, 2026-09-28).

Owner rulings 2026-09-28 (soco-83/84 decision cards): "Score C3a vs lambda",
"Score C3b (Recommended)", and C3c "Not scored on lambda (Recommended)".

These tests pin:

* the committed ``actual_lmp.json`` SOCO block is the lambda, RT-keyed only
  (no DA), on the load-weighted basis, and says what it is on every record;
* the committed hourly sidecar is the loader's series on the CST 8760 clock;
* the verdict labels C3a/C3b as a lambda benchmark and SKIPS C3c for SOCO
  with the ruling's reason, while every other ISO's C3c path is untouched.
"""

import json
import unittest

import numpy as np
import pandas as pd

from market_sim.config import paths
from market_sim.data.ferc714 import load_ferc714_system_lambda
from tests.scoring.test_calibration_verdict import DeterminationTests, cv

_YEARS = range(2019, 2026)
_REF = paths.CALIBRATION_DIR / "actual_lmp.json"
_HOURLY = paths.CALIBRATION_DIR / "actual_lmp_hourly_SOCO.parquet"


class ReferenceBlockTests(unittest.TestCase):
    def setUp(self):
        self.block = json.loads(_REF.read_text())["SOCO"]

    def test_every_year_is_rt_only_and_load_weighted(self):
        self.assertEqual(sorted(self.block), [str(y) for y in _YEARS])
        for y in _YEARS:
            rec = self.block[str(y)]
            with self.subTest(year=y):
                for k in ("rt", "rt_mon", "rt_pct", "rt_cov", "rt_lw", "rt_lw_mon"):
                    self.assertIn(k, rec)
                for k in ("da", "da_mon", "da_lw", "zones"):
                    self.assertNotIn(k, rec)
                self.assertEqual(rec["rt_cov"]["annual"], 1.0)
                self.assertIn("SYSTEM LAMBDA", rec["src"])
                self.assertIn("NOT an LMP", rec["src"])
                self.assertIn("C3c is NOT scored", rec["comment"])

    def test_hourly_sidecar_is_the_loader_series_on_the_cst_clock(self):
        h = pd.read_parquet(_HOURLY)
        lam = load_ferc714_system_lambda()["system_lambda_usd_mwh"]
        local = lam.index - pd.Timedelta(hours=6)
        for y in _YEARS:
            with self.subTest(year=y):
                g = h[h["year"] == y].sort_values("hour")
                self.assertEqual(g["hour"].tolist(), list(range(8760)))
                self.assertTrue(g["da"].isna().all())
                keep = (local.year == y) & ~((local.month == 2) & (local.day == 29))
                exp = lam.to_numpy()[keep]
                np.testing.assert_allclose(g["rt"].to_numpy(), exp, rtol=1e-6)
                self.assertAlmostEqual(
                    float(np.mean(exp)), self.block[str(y)]["rt"], places=2
                )


class VerdictTests(unittest.TestCase):
    def test_soco_c3c_is_skipped_with_the_ruling(self):
        ypay = DeterminationTests()._clean_year_payload()
        ypay["ordc"] = {"hoursGt200": {"actual": 100, "model": 100}}
        (rec,) = cv.score_price_tail(2024, ypay, "SOCO")
        self.assertEqual(rec["status"], cv.SKIPPED)
        self.assertIn("NOT SCORED on the SOCO system lambda", rec["metric"] + str(rec))
        self.assertEqual(set(cv.C3C_NOT_SCORED), {"SOCO"})

    def test_other_isos_keep_their_c3c_path(self):
        ypay = DeterminationTests()._clean_year_payload()
        recs = cv.score_price_tail(2024, ypay, "PJM")
        self.assertFalse(any("NOT SCORED" in str(r) for r in recs))

    def test_soco_c3a_and_c3b_name_the_lambda(self):
        d = DeterminationTests()
        ypay = d._clean_year_payload()
        ybench = {"avgLMP": {"rt_lw": 29.0, "rt_lw_mon": [29.0] * 12}}
        c3a = cv.score_price_mean(2024, ypay, ybench, "SOCO")
        self.assertIn("system lambda", c3a["metric"])
        self.assertNotIn("vs RT", c3a["metric"])
        c3b = cv.score_price_shape(2024, ypay, ybench, "SOCO")
        self.assertIn("system lambda", c3b["metric"])
        pjm = cv.score_price_mean(2024, ypay, ybench, "PJM")
        self.assertIn("vs RT", pjm["metric"])


if __name__ == "__main__":
    unittest.main()
