"""Tests for the CAISO belly-hour WECC import cap (caiso-117 LEG 1).

In the belly (midday) hours both CAISO and the WECC-West neighbor (EIA-930
NW+SW) are solar-long, so the West's physical belly export capability bounds
CAISO's total import well below the loose per-corridor p95 ATC ceiling. The
cap is a belly-scoped SIMULTANEOUS interface group over both corridor links,
capped hour by hour at the West's measured net export (``np.inf`` — no cap —
outside the belly, so the evening is untouched: C3a preserved by construction).
The cap is a WEST-side capability ceiling the LP clears below, never a flow
pinned to CA's residual (rule 13).
"""

import unittest

import numpy as np

from market_sim.config.interchange_config import (
    CAISO_BELLY_EXPORT_PERCENTILE,
    CAISO_BELLY_HOURS,
)
from market_sim.config.iso_configs import TransferLink
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia_loader import measured_west_belly_export_cap
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.model.transmission import (
    build_caiso_belly_import_cap_group,
    build_incidence_matrix,
)

T = 24


class TestConfigDefault(unittest.TestCase):
    def test_flag_default_off(self):
        self.assertFalse(ScenarioConfig(iso="CAISO").caiso_belly_import_cap)


class TestBuildBellyGroup(unittest.TestCase):
    """The builder returns one simultaneous group over BOTH corridor links."""

    def _links(self):
        return [
            TransferLink(from_zone="WECC_PNW", to_zone="NP15", ttc_mw=4800.0),
            TransferLink(from_zone="WECC_DSW", to_zone="SP15_rest", ttc_mw=10623.0),
            TransferLink(from_zone="NP15", to_zone="SP15_rest", ttc_mw=4000.0),
        ]

    def test_single_simultaneous_group_over_both_links(self):
        cap = np.full(T, np.inf)
        cap[12] = 2000.0
        groups = build_caiso_belly_import_cap_group(self._links(), cap)
        self.assertEqual(len(groups), 1)
        idx, group_cap, bidir = groups[0]
        # Both corridor link indices (0 = PNW, 1 = DSW), summed; one-sided.
        self.assertEqual(sorted(idx.tolist()), [0, 1])
        self.assertFalse(bidir)
        np.testing.assert_array_equal(group_cap, cap)

    def test_empty_when_no_corridor_links(self):
        links = [TransferLink(from_zone="NP15", to_zone="SP15_rest", ttc_mw=4000.0)]
        self.assertEqual(build_caiso_belly_import_cap_group(links, np.ones(T)), [])


class TestBellyCapEnvelope(unittest.TestCase):
    """The measured West belly cap is CAISO-only, belly-scoped, and non-negative."""

    def test_scope_and_belly_only(self):
        self.assertIsNone(measured_west_belly_export_cap("PJM", 2024, T))
        cap = measured_west_belly_export_cap("CAISO", 2024, 8760)
        self.assertIsNotNone(cap)
        self.assertEqual(cap.shape, (8760,))
        hod = np.arange(8760) % 24
        belly = np.isin(hod, CAISO_BELLY_HOURS)
        # Non-belly hours are always uncapped (inf) — the evening is untouched.
        self.assertTrue(np.all(np.isinf(cap[~belly])))
        # Belly hours carry a finite, positive cap (where the West is long).
        finite = np.isfinite(cap) & belly
        self.assertTrue(finite.any())
        self.assertTrue(np.all(cap[finite] > 0.0))
        # 2024's West is long across the whole belly (derive: 100% capped).
        self.assertGreater(finite.sum() / belly.sum(), 0.8)

    def test_percentile_default(self):
        self.assertEqual(CAISO_BELLY_EXPORT_PERCENTILE, 90.0)


class TestBellyCapLimitsImport(unittest.TestCase):
    """End-to-end: a tight belly cap on the summed corridors forces in-state gen
    in the belly hour while leaving a non-belly hour uncapped."""

    def _solve(self, belly_cap):
        # SP15_rest load fed by expensive in-state gen + two cheap import gens,
        # one per corridor (PNW→NP15→SP15_rest and DSW→SP15_rest). The belly cap
        # bounds the SUM of both corridor flows.
        zone_names = ["SP15_rest", "NP15", "WECC_PNW", "WECC_DSW"]
        links = [
            TransferLink(from_zone="WECC_PNW", to_zone="NP15", ttc_mw=5000.0),
            TransferLink(from_zone="WECC_DSW", to_zone="SP15_rest", ttc_mw=5000.0),
            TransferLink(from_zone="NP15", to_zone="SP15_rest", ttc_mw=5000.0),
        ]
        gens = [
            Generator(
                unit_id="instate",
                name="instate",
                zone="SP15_rest",
                fuel_type="gas_cc",
                pmax_mw=5000.0,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=50.0,
            ),
            Generator(
                unit_id="WECC_PNW_imp",
                name="pnw",
                zone="WECC_PNW",
                fuel_type="import",
                pmax_mw=5000.0,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=10.0,
            ),
            Generator(
                unit_id="WECC_DSW_imp",
                name="dsw",
                zone="WECC_DSW",
                fuel_type="import",
                pmax_mw=5000.0,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=10.0,
            ),
        ]
        fleet = generators_to_fleet_arrays(gens, zone_names, hours=T)
        mc = np.array([[50.0] * T, [10.0] * T, [10.0] * T])
        demand = np.zeros((4, T))
        demand[0, :] = 3000.0  # all load in SP15_rest
        incidence = build_incidence_matrix(links, zone_names)
        groups = build_caiso_belly_import_cap_group(links, belly_cap)
        return solve_dispatch(
            fleet=fleet,
            demand=demand,
            wind_cf=np.zeros((4, T)),
            wind_cap=np.zeros(4),
            solar_cf=np.zeros((4, T)),
            solar_cap=np.zeros(4),
            mc=mc,
            incidence=incidence,
            ttc=np.array([5000.0, 5000.0, 5000.0]),
            interface_groups=groups or None,
        )

    def test_belly_cap_binds_only_in_belly_hour(self):
        cap = np.full(T, np.inf)
        cap[12] = 800.0  # tight belly cap on TOTAL import
        res = self._solve(cap)
        total_import = res.dispatch[1] + res.dispatch[2]
        instate = res.dispatch[0]
        # Belly hour 12: total import capped at 800 → in-state serves 2200.
        self.assertAlmostEqual(total_import[12], 800.0, delta=1.0)
        self.assertAlmostEqual(instate[12], 2200.0, delta=1.0)
        # Non-belly hour 0: uncapped → cheap imports serve all 3000, in-state idle.
        self.assertAlmostEqual(total_import[0], 3000.0, delta=1.0)
        self.assertAlmostEqual(instate[0], 0.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()
