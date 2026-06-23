"""Calibration-page storage throughput metric: payload helpers + C5b wiring.

The render payload carries a ``storage`` block on both the benchmark side
(``bench[year].storage.throughput_twh``, from the EIA-930 battery + pumped-storage
discharge half) and the model side (``run.years[year].storage.throughput_twh``,
from the bundle's ``storage.parquet`` discharge), keyed exactly as
``calibration_verdict.score_storage`` (C5b) reads them. These tests pin the
discharge-TWh contract of the two render helpers and confirm the verdict
activates off that payload shape (it was SKIPPED for want of a committed series).
"""

import importlib.util
import sys
import unittest
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location(
    "rch_storage", str(REPO / "scripts" / "render_calibration_html.py")
)
rch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rch)

from scripts import calibration_verdict as cv  # noqa: E402


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


class StorageVerdictWiringTests(unittest.TestCase):
    def test_c5b_activates_off_payload(self):
        ypay = {"storage": {"throughput_twh": 1.1}}
        ybench = {"storage": {"throughput_twh": 1.0}}
        self.assertEqual(cv.score_storage(2024, ypay, ybench)["status"], cv.PASS)

    def test_c5b_fails_outside_band(self):
        # +47% over-cycling, outside the +/-30% cycling-realism band.
        r = cv.score_storage(
            2024,
            {"storage": {"throughput_twh": 0.46}},
            {"storage": {"throughput_twh": 0.31}},
        )
        self.assertEqual(r["status"], cv.FAIL)

    def test_c5b_skips_without_actual(self):
        r = cv.score_storage(2024, {"storage": {"throughput_twh": 0.34}}, {})
        self.assertEqual(r["status"], cv.SKIPPED)


if __name__ == "__main__":
    unittest.main()
