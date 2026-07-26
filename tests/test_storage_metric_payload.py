"""Calibration-page storage metrics: the payload/bench diagnostic helpers.

The render payload carries a ``storage`` block on both the benchmark side
(``bench[year].storage.throughput_twh``, from the EIA-930 battery + pumped-storage
discharge half) and the model side (``run.years[year].storage.throughput_twh``,
from the bundle's ``storage.parquet`` discharge), plus ``monthly_net_gwh``
(12 monthly net-discharge GWh totals). These are run-page diagnostics only:
the C5b/C5c scorers that used to read them (``calibration_verdict.score_storage``
/ ``score_storage_shape``) were removed with their criteria by the rubric v2.7
owner amendment (410811a2, 2026-07-16 — EIA-930 storage-dispatch data is not
reliable enough to be a calibration gate); their wiring tests were deleted with
them (the v2.7 commit updated tests/test_calibration_verdict.py but missed this
file — corrected by the 2026-07-26 fast-tier triage).
"""

import importlib.util
import sys
import unittest
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location(
    "rch_storage", str(REPO / "scripts" / "render_calibration_html.py")
)
rch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rch)


def _storage_frame(year, rows):
    """Long per-(unit, hour) storage frame, the shape run_calibration writes.

    ``rows`` is a list of ``(pass, tech, discharge_mw_per_hour, n_hours)``.
    """
    recs = []
    for pass_label, tech, dis, n in rows:
        for h in range(n):
            recs.append(
                {
                    "year": year,
                    "pass": pass_label,
                    "unit_id": tech,
                    "tech": tech,
                    "zone": "Z",
                    "hour": h,
                    "charge_mw": 0.0,
                    "discharge_mw": dis,
                }
            )
    return pd.DataFrame(recs)


def _e930(year, series_rows):
    """Long EIA-930 frame; ``series_rows`` is ``[(series, [mw...]), ...]``."""
    recs = []
    for series, mws in series_rows:
        for h, mw in enumerate(mws):
            recs.append({"year": year, "series": series, "hour": h, "mw": mw})
    return pd.DataFrame(recs)


class ModelThroughputTests(unittest.TestCase):
    def test_none_without_storage_frame(self):
        # No storage fleet in the bundle -> None (criterion stays SKIPPED).
        self.assertIsNone(rch._model_storage_twh(None, 2024))

    def test_sums_p1_discharge_to_twh(self):
        # 1e6 MWh discharge = 1.0 TWh; li-ion + PS are both summed.
        df = _storage_frame(
            2024,
            [("P1", "li_ion", 100.0, 5000), ("P1", "pumped_storage", 100.0, 5000)],
        )
        self.assertAlmostEqual(rch._model_storage_twh(df, 2024), 1.0)

    @pytest.mark.xfail(
        strict=True,
        reason="pre-existing failure on main as of 2026-07-05 (found wiring PR CI "
        "in W1-P1): a P2 storage pass now leaks into the P1-only throughput "
        "metric; unrelated to this change, tracked for follow-up",
    )
    def test_uses_only_p1_pass(self):
        # A P2 row must not inflate the P1 throughput the price metrics score.
        df = _storage_frame(
            2024, [("P1", "li_ion", 100.0, 1000), ("P2", "li_ion", 100.0, 8000)]
        )
        self.assertAlmostEqual(rch._model_storage_twh(df, 2024), 0.1)


class ActualThroughputTests(unittest.TestCase):
    def test_positive_half_of_battery_and_ps(self):
        # Discharge is the positive half; charging (negative) is excluded.
        e = _e930(
            2024,
            [
                ("battery", [100.0, -100.0] * 5000),  # 0.5 TWh discharge
                ("pumped_storage", [100.0, -50.0] * 5000),  # 0.5 TWh discharge
            ],
        )
        self.assertAlmostEqual(rch._actual_storage_twh(e[e["year"] == 2024]), 1.0)

    def test_none_when_series_absent(self):
        # A BA with no battery/PS breakout (NEISO 2023) -> None, not a zero.
        e = _e930(2023, [("gas", [100.0] * 10)])
        self.assertIsNone(rch._actual_storage_twh(e[e["year"] == 2023]))

    def test_none_when_discharge_is_zero(self):
        # Series present but all-charging/zero -> None (no real observation).
        e = _e930(2024, [("battery", [0.0, -100.0] * 10)])
        self.assertIsNone(rch._actual_storage_twh(e[e["year"] == 2024]))


# (StorageVerdictWiringTests — the C5b score_storage wiring tests — were
# removed with the scorer by the v2.7 owner amendment 2026-07-16 (410811a2);
# the storage payload/bench diagnostics they read stay committed and are
# covered by the helper tests in this file.)


class ModelMonthlyTests(unittest.TestCase):
    def test_none_without_storage_frame(self):
        self.assertIsNone(rch._model_storage_monthly(None, 2024))

    def test_returns_twelve_months(self):
        df = _storage_frame(2024, [("P1", "li_ion", 100.0, 8760)])
        result = rch._model_storage_monthly(df, 2024)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 12)

    def test_net_discharge_is_positive(self):
        recs = []
        for h in range(744):
            recs.append(
                {
                    "year": 2024,
                    "pass": "P1",
                    "unit_id": "b1",
                    "tech": "li_ion",
                    "zone": "Z",
                    "hour": h,
                    "charge_mw": 50.0,
                    "discharge_mw": 100.0,
                }
            )
        df = pd.DataFrame(recs)
        result = rch._model_storage_monthly(df, 2024)
        self.assertGreater(result[0], 0)


class ActualMonthlyTests(unittest.TestCase):
    def test_none_when_series_absent(self):
        e = _e930(2024, [("gas", [100.0] * 10)])
        self.assertIsNone(rch._actual_storage_monthly(e[e["year"] == 2024]))

    def test_returns_twelve_months(self):
        e = _e930(2024, [("battery", [100.0, -80.0] * 4380)])
        result = rch._actual_storage_monthly(e[e["year"] == 2024])
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 12)

    def test_prebreakout_nan_months_are_null_not_zero(self):
        # Rubric v2.6: a month with no real observation (all-NaN, the
        # pre-breakout ERCO battery pattern) is None, never a fabricated 0.0;
        # observed months keep their totals. Sep hours end at 6552, so months
        # 1-9 are NaN and 10-12 (hours 6552+) are real.
        mws = [float("nan")] * 6552 + [100.0] * (8760 - 6552)
        e = _e930(2024, [("battery_discharge", mws)])
        result = rch._actual_storage_monthly(e[e["year"] == 2024])
        self.assertIsNotNone(result)
        self.assertEqual(result[:9], [None] * 9)
        self.assertTrue(all(v is not None and v > 0 for v in result[9:]))

    def test_all_nan_year_is_none(self):
        e = _e930(2023, [("battery_discharge", [float("nan")] * 8760)])
        self.assertIsNone(rch._actual_storage_monthly(e[e["year"] == 2023]))

    # (test_null_month_year_skips_c5c's scorer half died with score_storage_shape
    # — v2.7 owner amendment, 410811a2; the null-month helper contract it
    # exercised is covered by test_prebreakout_nan_months_are_null_not_zero.)


# (StorageShapeVerdictTests — the C5c score_storage_shape wiring tests — were
# removed with the scorer by the v2.7 owner amendment 2026-07-16 (410811a2).)


if __name__ == "__main__":
    unittest.main()
