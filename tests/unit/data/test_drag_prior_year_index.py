"""Tests for the R-ERCOT-18 prior-year overnight-commitment drag allocation index."""

import tempfile
import unittest
import unittest.mock
from pathlib import Path

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.data.fleet.floors import (
    apply_gas_st_netload_drag_floor,
    load_prior_year_overnight_mwh,
)
from market_sim.data.fleet.models import Generator
from market_sim.data.floor_mechanisms import MECH_ST_NETLOAD_DRAG


def _plants():
    """Three 200-MW non-peak ST_GAS plants (committed + econ) plus a peak rung."""
    out = []
    for code in (111, 222, 333):
        shared = dict(
            name=f"P{code}",
            zone="North",
            fuel_type="gas_st",
            online_year=1975,
            plant_group="ST_GAS",
            plant_code=code,
        )
        out += [
            Generator(
                unit_id=f"p{code}_committed", pmax_mw=100.0, heat_rate=10.0, **shared
            ),
            Generator(
                unit_id=f"p{code}_econc00", pmax_mw=100.0, heat_rate=11.0, **shared
            ),
            Generator(unit_id=f"p{code}_peak", pmax_mw=50.0, heat_rate=13.0, **shared),
        ]
    return out


def _cfg():
    return ScenarioConfig(
        gas_st_netload_drag=True,
        gas_st_drag_slope_per_gw=0.00906,
        gas_st_drag_intercept=-0.1376,
        gas_st_drag_cap=0.34,
    )


def _floor(prior, net=None):
    gens = _plants()
    net = np.full(24, 40_000.0) if net is None else net
    fa = generators_to_fleet_arrays(gens, ["North"], hours=len(net))
    apply_gas_st_netload_drag_floor(fa, gens, net, _cfg(), prior_overnight_mwh=prior)
    by_plant = {}
    for i, g in enumerate(gens):
        by_plant[g.plant_code] = by_plant.get(g.plant_code, 0.0) + float(
            fa.min_gen[i].sum()
        )
    return gens, fa, by_plant


class TestPriorYearCommitmentIndex(unittest.TestCase):
    """Allocation-only swap: same mandate, redistributed by prior-year overnight energy."""

    def test_none_is_byte_identical_to_pro_rata(self):
        _, fa_none, _ = _floor(None)
        _, fa_empty, _ = _floor({})
        gens = _plants()
        fa_plain = generators_to_fleet_arrays(gens, ["North"], hours=24)
        apply_gas_st_netload_drag_floor(fa_plain, gens, np.full(24, 40_000.0), _cfg())
        np.testing.assert_array_equal(fa_none.min_gen, fa_plain.min_gen)
        np.testing.assert_array_equal(fa_empty.min_gen, fa_plain.min_gen)

    def test_a_plant_dark_overnight_last_year_carries_no_floor(self):
        _, _, by = _floor({111: 0.0, 222: 1000.0, 333: 1000.0})
        self.assertEqual(by[111], 0.0)
        self.assertGreater(by[222], 0.0)

    def test_the_nominal_mandate_is_preserved(self):
        _, _, pro = _floor(None)
        _, _, idx = _floor({111: 100.0, 222: 300.0, 333: 800.0})
        self.assertAlmostEqual(sum(idx.values()), sum(pro.values()), places=6)

    def test_unmetered_plants_keep_pro_rata(self):
        _, _, pro = _floor(None)
        _, _, idx = _floor({111: 0.0, 222: 1000.0})  # 333 unmetered
        self.assertAlmostEqual(idx[333], pro[333], places=9)
        self.assertAlmostEqual(idx[111] + idx[222], pro[111] + pro[222], places=6)

    def test_zero_overnight_fleet_falls_back_to_pro_rata(self):
        _, fa_pro, _ = _floor(None)
        _, fa_zero, _ = _floor({111: 0.0, 222: 0.0, 333: 0.0})
        np.testing.assert_array_equal(fa_zero.min_gen, fa_pro.min_gen)

    def test_peak_rungs_stay_unfloored_and_forcing_stays_attributed(self):
        gens, fa, _ = _floor({111: 10.0, 222: 500.0, 333: 900.0})
        for i, g in enumerate(gens):
            if g.unit_id.endswith("_peak"):
                np.testing.assert_allclose(fa.min_gen[i], 0.0)
        forced = fa.min_gen > 0.0
        self.assertTrue(forced.any())
        self.assertTrue(np.all(fa.min_gen_mechanism[forced] == MECH_ST_NETLOAD_DRAG))

    def test_floor_never_exceeds_available_capacity(self):
        gens, fa, _ = _floor({111: 0.0, 222: 0.0, 333: 10_000.0}, np.full(24, 55_000.0))
        pm = fa.pmax[:, None] * fa.availability
        self.assertTrue(np.all(fa.min_gen <= pm + 1e-9))


class TestLoadPriorYearOvernight(unittest.TestCase):
    """The loader's gates: flag, backcast mode, vintage Y-1, ISO, metered."""

    def _write(self, d):
        p = Path(d) / "ercot_stgas_overnight_commitment.csv"
        p.write_text(
            "iso,plant_code,year,overnight_net_mwh,overnight_hours,metered,source_sha256\n"
            "ERCOT,3452,2021,1000.0,2555,True,x\n"
            "ERCOT,3460,2021,50000.0,2555,True,x\n"
            "ERCOT,56708,2021,0.0,2555,False,x\n"
        )
        return p

    def _load(self, cfg, year):
        with tempfile.TemporaryDirectory() as d:
            self._write(d)
            with unittest.mock.patch(
                "market_sim.config.paths.CALIBRATION_DIR", Path(d)
            ):
                return load_prior_year_overnight_mwh(cfg, "ERCOT", year)

    def test_off_returns_none(self):
        self.assertIsNone(self._load(ScenarioConfig(mode="backcast"), 2022))

    def test_forecast_refuses_the_flag(self):
        """Backcast-only overlay: the config guard refuses it in forecast mode."""
        with self.assertRaises(ValueError):
            ScenarioConfig(netload_drag_prior_year_commitment_index=True)

    def test_reads_prior_vintage_metered_only(self):
        cfg = ScenarioConfig(
            mode="backcast",
            weather_year=2022,
            netload_drag_prior_year_commitment_index=True,
        )
        got = self._load(cfg, 2022)
        self.assertEqual(got, {3452: 1000.0, 3460: 50000.0})

    def test_missing_vintage_fails_closed(self):
        cfg = ScenarioConfig(
            mode="backcast",
            weather_year=2019,
            netload_drag_prior_year_commitment_index=True,
        )
        self.assertIsNone(self._load(cfg, 2019))


if __name__ == "__main__":
    unittest.main()
