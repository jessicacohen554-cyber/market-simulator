"""Tests for the ``chp-btm-share`` reader and its forecast wiring.

Writes a tiny ``chp-btm-share`` clean partition (via the real ``write_clean``
seam, so the schema itself is exercised) into a tmp CLEAN_DIR and asserts:
(1) :func:`market_sim.data.chp.measured_btm_share_by_plant` returns the exact
covered value and omits uncovered plants; (2)
:func:`market_sim.runner._chp_measured_co2_inputs` only sources it for
forecast years, leaving backcast untouched.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import chp as chp_mod
from scripts.lib import clean_io


def _write_partition(iso: str, rows: list[dict]) -> Path:
    df = pd.DataFrame(rows)
    path = clean_io.write_clean(df, "chp-btm-share", iso=iso, year=None)
    clean_io.validate_clean(path)
    return path


class TestMeasuredBtmShareByPlant(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = Path(self._tmp.name) / "clean"
        chp_mod.measured_btm_share_by_plant.cache_clear()

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        chp_mod.measured_btm_share_by_plant.cache_clear()
        self._tmp.cleanup()

    def test_covered_plant_returns_measured_share(self):
        _write_partition(
            "ERCOT",
            [
                {
                    "iso": "ERCOT",
                    "plant_id": 1001,
                    "plant_group": "CC_CHP",
                    "eia923_net_mwh": 1000.0,
                    "campd_net_mwh": 700.0,
                    "btm_share": 0.3,
                    "steam_load_klbh_sum": 50.0,
                    "n_years": 1,
                    "first_year": 2023,
                    "last_year": 2023,
                }
            ],
        )
        shares = chp_mod.measured_btm_share_by_plant("ERCOT")
        self.assertAlmostEqual(shares[1001], 0.3, places=6)
        # An uncovered plant id is simply absent -- caller falls back.
        self.assertNotIn(9999, shares)

    def test_missing_partition_returns_empty(self):
        self.assertEqual(chp_mod.measured_btm_share_by_plant("PJM"), {})


class TestRunnerForecastOnlyWiring(unittest.TestCase):
    """R5 wave 3: btm_share_by_plant sources only for forecast years."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = Path(self._tmp.name) / "clean"
        chp_mod.measured_btm_share_by_plant.cache_clear()
        _write_partition(
            "ERCOT",
            [
                {
                    "iso": "ERCOT",
                    "plant_id": 1001,
                    "plant_group": "CC_CHP",
                    "eia923_net_mwh": 1000.0,
                    "campd_net_mwh": 700.0,
                    "btm_share": 0.3,
                    "steam_load_klbh_sum": 50.0,
                    "n_years": 1,
                    "first_year": 2023,
                    "last_year": 2023,
                }
            ],
        )

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        chp_mod.measured_btm_share_by_plant.cache_clear()
        self._tmp.cleanup()

    def test_forecast_mode_returns_covered_share(self):
        from market_sim import runner

        config = ScenarioConfig(iso="ERCOT", mode="forecast")
        _rates, _cf, btm_share = runner._chp_measured_co2_inputs(config, "ERCOT", 2030)
        self.assertAlmostEqual(btm_share[1001], 0.3, places=6)

    def test_backcast_mode_ignores_artifact(self):
        from market_sim import runner

        config = ScenarioConfig(iso="ERCOT", mode="backcast")
        _rates, _cf, btm_share = runner._chp_measured_co2_inputs(config, "ERCOT", 2024)
        self.assertEqual(
            btm_share, {}, "backcast must keep the _btm_frame sizing untouched"
        )


if __name__ == "__main__":
    unittest.main()
