"""Tests for the MISO loss-surface derive on a tiny synthetic fixture.

Writes a minimal ``lmp-components`` clean partition (via the real
``write_clean`` seam, into a tmp CLEAN_DIR) with hand-constructed
MLC/MEC so the expected delivery-factor deviations are exact, then asserts
the ratio-of-sums math, the Plains neighbor interpolation, derive
determinism, and the offline acceptance-band logic (charter §4).
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from scripts.data import derive_miso_loss_surface as dls
from scripts.lib import clean_io

# Constructed per-hub deviations (dimensionless) and the flat MEC level.
_DEV = {
    "MINN.HUB": -0.02,
    "ILLINOIS.HUB": -0.01,
    "INDIANA.HUB": 0.03,
    "MICHIGAN.HUB": 0.02,
    "ARKANSAS.HUB": -0.015,
    "LOUISIANA.HUB": -0.015,
    "TEXAS.HUB": -0.015,
    "MS.HUB": -0.015,
}
_MEC = 40.0
_YEAR = 2023
_N_DAYS = 3  # small but > 1 day so the monthly sums pool hours


def _fixture_frame() -> pd.DataFrame:
    """One tiny DA partition: MLC = dev x MEC exactly, MCC = 0."""
    hours = pd.date_range(
        f"{_YEAR}-01-01 05:00", periods=24 * _N_DAYS, freq="h", tz="UTC"
    )
    rows = []
    for hub, dev in _DEV.items():
        for ts in hours:
            mlc = dev * _MEC
            rows.append(
                {
                    "iso": "MISO",
                    "market": "da",
                    "node": hub,
                    "node_type": "Hub",
                    "interval_start_utc": ts,
                    "interval_start_est": ts.tz_convert("Etc/GMT+5").tz_localize(None),
                    "lmp_usd_per_mwh": _MEC + mlc,
                    "mcc_usd_per_mwh": 0.0,
                    "mlc_usd_per_mwh": mlc,
                }
            )
    return pd.DataFrame(rows)


class TestDeriveMisoLossSurface(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = Path(self._tmp.name) / "clean"
        path = clean_io.write_clean(
            _fixture_frame(), "lmp-components", iso="MISO", year=_YEAR, market="da"
        )
        clean_io.validate_clean(path)

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _derive(self) -> pd.DataFrame:
        return dls.derive(years=(_YEAR,))

    def test_ratio_of_sums_recovers_constructed_deviations(self) -> None:
        surf = self._derive()
        jan = surf[(surf["year"] == _YEAR) & (surf["month"] == 1)].set_index("zone")
        self.assertAlmostEqual(jan.loc["MISO-West", "df_deviation"], -0.02, places=9)
        self.assertAlmostEqual(
            jan.loc["MISO-Illinois", "df_deviation"], -0.01, places=9
        )
        self.assertAlmostEqual(jan.loc["MISO-Indiana", "df_deviation"], 0.03, places=9)
        self.assertAlmostEqual(jan.loc["MISO-East", "df_deviation"], 0.02, places=9)
        # South = mean of its four member-hub deviations (all -0.015).
        self.assertAlmostEqual(jan.loc["MISO-South", "df_deviation"], -0.015, places=9)

    def test_plains_is_neighbor_interpolation(self) -> None:
        surf = self._derive()
        jan = surf[(surf["year"] == _YEAR) & (surf["month"] == 1)].set_index("zone")
        # Plains = mean(West, Illinois) = mean(-0.02, -0.01), flagged.
        self.assertAlmostEqual(jan.loc["MISO-Plains", "df_deviation"], -0.015, places=9)
        self.assertTrue(bool(jan.loc["MISO-Plains", "interpolated"]))
        self.assertFalse(bool(jan.loc["MISO-West", "interpolated"]))

    def test_pooled_rows_present_and_deterministic(self) -> None:
        a, b = self._derive(), self._derive()
        pd.testing.assert_frame_equal(a, b)
        self.assertIn(dls.POOLED_YEAR, set(a["year"]))
        # Single-year fixture: pooled == the year block, zone-for-zone.
        pooled = a[a["year"] == dls.POOLED_YEAR].set_index(["zone", "month"])
        year = a[a["year"] == _YEAR].set_index(["zone", "month"])
        np.testing.assert_allclose(
            pooled["df_deviation"].sort_index().to_numpy(),
            year["df_deviation"].sort_index().to_numpy(),
        )

    def test_acceptance_band_logic(self) -> None:
        surf = self._derive()
        # Faithful surface: implied == measured up to the second-order
        # (1+dev_ref) factor — squarely in [0.5x, 1.5x].
        self.assertTrue(dls.acceptance(surf, years=(_YEAR,)))
        # A surface distorted 3x must fail the band.
        bad = surf.copy()
        bad["df_deviation"] = bad["df_deviation"] * 3.0
        self.assertFalse(dls.acceptance(bad, years=(_YEAR,)))


if __name__ == "__main__":
    unittest.main()
