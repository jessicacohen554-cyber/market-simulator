"""Tests for the whole-operating-day commitment grain of the per-plant floors.

``ScenarioConfig.mustrun_window_commitment_grain`` (spp-27) changes only WHICH
hours the per-plant must-run window selects: the same ``online_frac``-sized
window becomes ``round(k / 24)`` whole operating days ranked by that day's mean
system load, instead of ``k`` individually top-ranked hours. Size, level and
membership are untouched (rule 19 ``[R-ONE-MECH]``), and the window's diurnal
peak-to-mean becomes 1.0 — the measured shape of a commitment, against the
diurnal shape of load the hour grain inherits (rule 17 ``[R-FLOOR-WINDOW]``).
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fleet.arrays import (
    _commitment_day_order,
    _mustrun_window_hours,
)
from market_sim.data.floor_mechanisms import MECH_ST_GAS_MUSTRUN_PER_PLANT

ZONES = ["Dominion"]
HOURS = 8760
_ST_CODE = 1403


def _diurnal_load(hours: int = HOURS) -> np.ndarray:
    """A load shape with a real diurnal cycle and a seasonal envelope.

    Hour grain therefore selects afternoon hours spread over many days; day
    grain selects whole days. The two windows are the same SIZE.
    """
    t = np.arange(hours, dtype=float)
    season = 1.0 + 0.30 * np.sin(2.0 * np.pi * (t / hours) - np.pi / 2.0)
    diurnal = 1.0 + 0.35 * np.sin(2.0 * np.pi * ((t % 24) - 8.0) / 24.0)
    return 30_000.0 * season * diurnal


def _arrays(day_grain: bool, frac: float = 0.25) -> np.ndarray:
    gen = Generator(
        unit_id="ST_GAS_Dominion_p1403_committed",
        name="steamer committed",
        zone="Dominion",
        fuel_type="gas_st",
        pmax_mw=100.0,
        plant_group="ST_GAS",
        plant_code=_ST_CODE,
        is_campd_bin=True,
        cc_mustrun_pmin_mw=50.0,
        cc_mustrun_online_frac=frac,
    )
    cfg = ScenarioConfig(
        iso="MISO",
        weather_year=2024,
        mode="backcast",
        hours=HOURS,
        mustrun_window_commitment_grain=day_grain,
    )
    return generators_to_fleet_arrays(
        [gen],
        ZONES,
        hours=HOURS,
        iso="MISO",
        config=cfg,
        load_shape=_diurnal_load(),
    )


def _peak_to_mean(mask: np.ndarray) -> float:
    hod = np.arange(len(mask)) % 24
    prof = np.array([float(mask[hod == h].sum()) for h in range(24)])
    return float(prof.max() / prof.mean())


class TestHelpers(unittest.TestCase):
    """The two pure helpers, independent of the fleet build."""

    def test_day_order_is_a_permutation_of_days(self):
        order = _commitment_day_order(_diurnal_load(), HOURS)
        self.assertIsNotNone(order)
        self.assertEqual(sorted(order.tolist()), list(range(HOURS // 24)))

    def test_day_order_is_descending_in_day_mean_load(self):
        load = _diurnal_load()
        order = _commitment_day_order(load, HOURS)
        key = load.reshape(HOURS // 24, 24).mean(axis=1)[order]
        self.assertTrue((np.diff(key) <= 1e-9).all())

    def test_no_load_shape_falls_back_to_hour_grain(self):
        self.assertIsNone(_commitment_day_order(None, HOURS))
        rank = np.arange(HOURS)
        got = _mustrun_window_hours(rank, None, 100, day_grain=True)
        np.testing.assert_array_equal(got, rank[:100])

    def test_unarmed_is_the_hour_window(self):
        rank = np.argsort(-_diurnal_load(), kind="stable")
        order = _commitment_day_order(_diurnal_load(), HOURS)
        got = _mustrun_window_hours(rank, order, 1234, day_grain=False)
        np.testing.assert_array_equal(got, rank[:1234])

    def test_armed_window_is_whole_days_of_the_right_size(self):
        load = _diurnal_load()
        rank = np.argsort(-load, kind="stable")
        order = _commitment_day_order(load, HOURS)
        for k in (240, 1000, 2190):
            hrs = _mustrun_window_hours(rank, order, k, day_grain=True)
            self.assertEqual(len(hrs), 24 * round(k / 24))
            self.assertAlmostEqual(len(hrs) / k, 1.0, delta=0.02)
            # every selected hour's whole day is selected
            days = np.unique(hrs // 24)
            self.assertEqual(len(hrs), 24 * len(days))


class TestFleetArrays(unittest.TestCase):
    """End-to-end through the floor composer."""

    def test_default_off_is_byte_identical_to_the_hour_grain(self):
        base = generators_to_fleet_arrays(
            [
                Generator(
                    unit_id="ST_GAS_Dominion_p1403_committed",
                    name="steamer committed",
                    zone="Dominion",
                    fuel_type="gas_st",
                    pmax_mw=100.0,
                    plant_group="ST_GAS",
                    plant_code=_ST_CODE,
                    is_campd_bin=True,
                    cc_mustrun_pmin_mw=50.0,
                    cc_mustrun_online_frac=0.25,
                )
            ],
            ZONES,
            hours=HOURS,
            iso="MISO",
            load_shape=_diurnal_load(),
        )
        off = _arrays(day_grain=False)
        np.testing.assert_array_equal(base.min_gen, off.min_gen)
        np.testing.assert_array_equal(base.min_gen_mechanism, off.min_gen_mechanism)

    def test_window_size_and_level_are_unchanged(self):
        off, on = _arrays(False), _arrays(True)
        n_off = int((off.min_gen[0] > 0.0).sum())
        n_on = int((on.min_gen[0] > 0.0).sum())
        self.assertAlmostEqual(n_on / n_off, 1.0, delta=0.02)
        self.assertEqual(off.min_gen.max(), on.min_gen.max())

    def test_armed_window_is_flat_across_the_day(self):
        off, on = _arrays(False), _arrays(True)
        self.assertGreater(_peak_to_mean(off.min_gen[0] > 0.0), 1.5)
        self.assertAlmostEqual(_peak_to_mean(on.min_gen[0] > 0.0), 1.0, places=6)

    def test_mechanism_id_is_unchanged(self):
        on = _arrays(True)
        tagged = on.min_gen_mechanism[0][on.min_gen[0] > 0.0]
        self.assertTrue((tagged == MECH_ST_GAS_MUSTRUN_PER_PLANT).all())

    def test_gate_is_inert_when_the_host_floor_is_absent(self):
        """No must-run floor to place ⇒ the gate changes nothing."""
        gen = Generator(
            unit_id="ST_GAS_Dominion_p1403_econ",
            name="steamer econ",
            zone="Dominion",
            fuel_type="gas_st",
            pmax_mw=100.0,
            plant_group="ST_GAS",
            plant_code=_ST_CODE,
            is_campd_bin=True,
        )
        kw = dict(hours=HOURS, iso="MISO", load_shape=_diurnal_load())
        off = generators_to_fleet_arrays(
            [gen],
            ZONES,
            config=ScenarioConfig(
                iso="MISO", weather_year=2024, mode="backcast", hours=HOURS
            ),
            **kw,
        )
        on = generators_to_fleet_arrays(
            [gen],
            ZONES,
            config=ScenarioConfig(
                iso="MISO",
                weather_year=2024,
                mode="backcast",
                hours=HOURS,
                mustrun_window_commitment_grain=True,
            ),
            **kw,
        )
        self.assertEqual(off.min_gen is None, on.min_gen is None)
        if off.min_gen is not None:
            np.testing.assert_array_equal(off.min_gen, on.min_gen)


if __name__ == "__main__":
    unittest.main()
