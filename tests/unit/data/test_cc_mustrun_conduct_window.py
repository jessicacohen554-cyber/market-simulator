"""Tests for the plant-conduct placement of the CC_REGULAR per-plant must-run window.

``ScenarioConfig.cc_mustrun_conduct_window`` (PJM-NEXT-17) changes only WHICH hours the
``cc_mustrun_per_plant`` window selects: the same ``online_frac``-sized window is ranked by
the plant's own measured month x hour-of-day online probability, ties by system load. Size,
level, membership and mechanism id are untouched (rule 19); a backcast excludes its own solve
year's meter (rule 13).
"""

import unittest
from unittest import mock

import numpy as np
import pandas as pd

import market_sim.data.fleet as fleet_pkg
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fleet import campd_bins
from market_sim.data.fleet.arrays import _CONDUCT_CELL
from market_sim.data.floor_mechanisms import MECH_CC_MUSTRUN_PER_PLANT

ZONES = ["Dominion"]
HOURS = 8760
_CODE = 7213


def _load(hours: int = HOURS) -> np.ndarray:
    """Load peaking in the afternoon, so the incumbent window is afternoon-heavy."""
    t = np.arange(hours, dtype=float)
    return 30_000.0 * (1.0 + 0.35 * np.sin(2.0 * np.pi * ((t % 24) - 8.0) / 24.0))


def _night_profile() -> np.ndarray:
    """A plant that is on overnight (HOD 0-5) and off otherwise."""
    p = np.full(288, 0.1)
    for m in range(12):
        p[m * 24 : m * 24 + 6] = 0.9
    return p


def _gen(code: int = _CODE) -> Generator:
    return Generator(
        unit_id=f"CC_REGULAR_Dominion_p{code}_committed",
        name="cc committed",
        zone="Dominion",
        fuel_type="gas_cc",
        pmax_mw=300.0,
        plant_group="CC_REGULAR",
        plant_code=code,
        is_campd_bin=True,
        cc_mustrun_pmin_mw=120.0,
        cc_mustrun_online_frac=0.2,
    )


def _arrays(armed: bool, mode: str = "backcast", code: int = _CODE, profile=None):
    cfg = ScenarioConfig(
        iso="PJM",
        weather_year=2023,
        mode=mode,
        hours=HOURS,
        cc_mustrun_conduct_window=armed,
    )
    prof = {_CODE: _night_profile()} if profile is None else profile
    with mock.patch.object(fleet_pkg, "cc_conduct_profile", return_value=prof) as m:
        out = generators_to_fleet_arrays(
            [_gen(code)], ZONES, hours=HOURS, iso="PJM", config=cfg, load_shape=_load()
        )
    return out, m


class TestFleetArrays(unittest.TestCase):
    """End-to-end through the floor composer."""

    def test_default_off_never_reads_the_profile(self):
        _, m = _arrays(False)
        m.assert_not_called()

    def test_window_moves_to_the_plants_on_cells(self):
        off, _ = _arrays(False)
        on, _ = _arrays(True)
        night = (np.arange(HOURS) % 24) < 6
        w_off, w_on = off.min_gen[0] > 0.0, on.min_gen[0] > 0.0
        self.assertLess(w_off[night].mean(), 0.1)
        # k = 0.2 x 8760 = 1752 < 2190 night hours, so the window is all night.
        self.assertTrue(night[w_on].all())

    def test_size_level_and_mechanism_are_unchanged(self):
        off, _ = _arrays(False)
        on, _ = _arrays(True)
        self.assertEqual(
            int((off.min_gen[0] > 0).sum()), int((on.min_gen[0] > 0).sum())
        )
        self.assertEqual(off.min_gen.max(), on.min_gen.max())
        tagged = on.min_gen_mechanism[0][on.min_gen[0] > 0.0]
        self.assertTrue((tagged == MECH_CC_MUSTRUN_PER_PLANT).all())

    def test_ties_break_by_system_load(self):
        on, _ = _arrays(True)
        # Within the night cells the window prefers the higher-load night hours.
        hod = np.arange(HOURS) % 24
        sel = hod[on.min_gen[0] > 0.0]
        self.assertGreater((sel == 5).sum(), (sel == 0).sum() - 1)

    def test_plant_without_a_profile_keeps_the_incumbent_window(self):
        off, _ = _arrays(False)
        on, _ = _arrays(True, profile={})
        np.testing.assert_array_equal(off.min_gen, on.min_gen)
        np.testing.assert_array_equal(off.min_gen_mechanism, on.min_gen_mechanism)

    def test_backcast_excludes_its_solve_year_forecast_does_not(self):
        _, m = _arrays(True, mode="backcast")
        self.assertEqual(m.call_args.args[1], 2023)
        _, m = _arrays(True, mode="forecast")
        self.assertIsNone(m.call_args.args[1])


class TestConfigAndLoader(unittest.TestCase):
    """The rule-19 refusal and the leave-one-year-out loader."""

    def test_refused_with_the_day_grain(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="PJM",
                cc_mustrun_conduct_window=True,
                mustrun_window_commitment_grain=True,
            )

    def test_loader_pools_other_years_only(self):
        import tempfile
        from pathlib import Path

        rows = []
        for year, on in ((2022, 0), (2023, 10), (2024, 20)):
            for c in range(288):
                rows.append((_CODE, year, c // 24, c % 24, on, 30))
        with tempfile.TemporaryDirectory() as d:
            pd.DataFrame(
                rows,
                columns=["plant_code", "year", "month", "hod", "sync_hours", "hours"],
            ).to_csv(Path(d) / "cc_conduct_profile_ZZ.csv", index=False)
            with mock.patch.object(campd_bins, "PROCESSED_DIR", Path(d)):
                campd_bins.cc_conduct_profile.cache_clear()
                loo = campd_bins.cc_conduct_profile("ZZ", 2023)
                allp = campd_bins.cc_conduct_profile("ZZ", None)
                campd_bins.cc_conduct_profile.cache_clear()
        np.testing.assert_allclose(loo[_CODE], 10 / 30)  # (0 + 20) / 60
        np.testing.assert_allclose(allp[_CODE], 30 / 90)
        self.assertEqual(_CONDUCT_CELL.size, HOURS)
        self.assertEqual(int(_CONDUCT_CELL.max()), 287)


if __name__ == "__main__":
    unittest.main()
