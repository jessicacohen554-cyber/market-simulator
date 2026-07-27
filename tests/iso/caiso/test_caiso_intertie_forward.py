"""Tests for the CAISO FORWARD per-hub intertie seam (reference price + ATC).

The forecast-native replacement for the two MEASURED CAISO levers: each WECC
corridor is priced from ``(henry_hub + gas_basis) × marginal_heat_rate ×
load_shape`` (the desert-SW on net load, so its midday price dips with the solar
glut) instead of the measured hub LMP, and its import deliverability is capped at
a forward ATC (corridor TTC × posted-ATC fraction × forward solar derate) instead
of the measured p95 envelope. Nothing reads the measured realization — the
honesty gate (CLAUDE.md #10/#12).
"""

import unittest

import numpy as np

from market_sim.config.constants import HENRY_HUB_TRAJECTORIES
from market_sim.config.interchange_config import (
    CAISO_PER_HUB_NEIGHBORS,
    IMPORT_TRANCHES,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.eia_loader import caiso_solar_fraction
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.data.neighbor_price import (
    caiso_hub_load_shape,
    caiso_hub_reference_price,
)
from market_sim.model.transmission import (
    build_caiso_per_hub_intertie,
    forward_corridor_atc_envelope,
    inject_caiso_per_hub_reference_prices,
    split_caiso_import_node_per_hub,
    wecc_border_carbon_adder,
)

HOURS = 8760
YEAR = 2024


def _hod_mask(lo: int, hi: int, n: int = HOURS) -> np.ndarray:
    """Return a boolean mask for hours-of-day in ``[lo, hi]`` over ``n`` hours."""
    hod = np.arange(n) % 24
    return (hod >= lo) & (hod <= hi)


class TestForwardReferencePrice(unittest.TestCase):
    """The per-hub forward price tracks gas × HR × the neighbor's load shape."""

    def test_desert_sw_dips_midday_pnw_does_not(self):
        midday, evening = _hod_mask(10, 15), _hod_mask(18, 21)
        dsw = caiso_hub_reference_price(
            CAISO_PER_HUB_NEIGHBORS["WECC_DSW"], YEAR, HOURS
        )
        pnw = caiso_hub_reference_price(
            CAISO_PER_HUB_NEIGHBORS["WECC_PNW"], YEAR, HOURS
        )
        self.assertIsNotNone(dsw)
        self.assertIsNotNone(pnw)
        # The solar-driven desert-SW (net-load shape) is markedly cheaper midday
        # than in the evening ramp — the duck the measured Palo Verde hub carries.
        self.assertLess(dsw[midday].mean(), dsw[evening].mean() - 5.0)
        # The hydro-following Pacific-NW (gross-load shape) has a much shallower
        # midday/evening split (no solar trough).
        pnw_split = pnw[evening].mean() - pnw[midday].mean()
        dsw_split = dsw[evening].mean() - dsw[midday].mean()
        self.assertLess(pnw_split, dsw_split)

    def test_level_rides_henry_hub(self):
        # A dearer gas year reprices the seam up (forward-native level), with the
        # same shape — the property that keeps it live in a forecast year.
        spec = CAISO_PER_HUB_NEIGHBORS["WECC_DSW"]
        cheap = caiso_hub_reference_price(spec, 2024, HOURS)  # HH 2.19
        dear = caiso_hub_reference_price(spec, 2025, HOURS)  # HH 3.52
        self.assertGreater(dear.mean(), cheap.mean())
        ratio = (HENRY_HUB_TRAJECTORIES["mid"][2025] + spec.gas_basis) / (
            HENRY_HUB_TRAJECTORIES["mid"][2024] + spec.gas_basis
        )
        # Mean scales exactly with delivered gas (the shape is mean-preserving).
        self.assertAlmostEqual(dear.mean() / cheap.mean(), ratio, places=2)

    def test_net_shape_has_lower_mean_floor_than_gross(self):
        net = caiso_hub_load_shape(CAISO_PER_HUB_NEIGHBORS["WECC_DSW"], YEAR, HOURS)
        gross = caiso_hub_load_shape(CAISO_PER_HUB_NEIGHBORS["WECC_PNW"], YEAR, HOURS)
        # Both shapes are ~mean-preserving (linear exponent 1.0).
        self.assertAlmostEqual(float(net.mean()), 1.0, places=1)
        self.assertAlmostEqual(float(gross.mean()), 1.0, places=1)
        # The net-load shape has the deeper midday trough.
        midday = _hod_mask(10, 15)
        self.assertLess(net[midday].mean(), gross[midday].mean())


class TestInjectForwardReferencePrices(unittest.TestCase):
    """Each corridor is repriced at its forward reference, arbitrage-free."""

    def _fleet(self):
        gens = build_caiso_per_hub_intertie(wecc_border_carbon_adder(35.0))
        fa = generators_to_fleet_arrays(gens, ["WECC_PNW", "WECC_DSW"], hours=HOURS)
        return fa, gens

    def test_per_hub_basis_and_arbitrage_free(self):
        fa, gens = self._fleet()
        mc = np.zeros((len(gens), HOURS))
        applied = inject_caiso_per_hub_reference_prices(fa, mc, "CAISO", YEAR, 35.0)
        self.assertTrue(applied)
        uids = list(fa.unit_ids)

        # The two corridors carry DIFFERENT prices (per-hub basis preserved).
        pnw = mc[uids.index("WECC_PNW_PNW_hydro_base")]
        dsw = mc[uids.index("WECC_DSW_DSW_solar_PV")]
        self.assertFalse(np.allclose(pnw, dsw))

        # Arbitrage-free PER CORRIDOR: every import leg ≥ that corridor's export
        # leg every hour (so each corridor nets to one direction per hour).
        for zone in ("WECC_PNW", "WECC_DSW"):
            exp_row = next(
                i for i, u in enumerate(uids) if u.startswith(f"{zone}_export_")
            )
            imp_rows = [
                i
                for i, u in enumerate(uids)
                if u.startswith(f"{zone}_") and not u.startswith(f"{zone}_export_")
            ]
            self.assertTrue(np.all(mc[imp_rows].min(axis=0) >= mc[exp_row]))

    def test_import_carries_wheel_and_carbon_over_export(self):
        # The desert-SW gas block (carbon EF) is priced strictly above the clean
        # solar block (EF 0) on the same corridor — the carbon ladder survives.
        fa, gens = self._fleet()
        mc = np.zeros((len(gens), HOURS))
        inject_caiso_per_hub_reference_prices(fa, mc, "CAISO", YEAR, 35.0)
        uids = list(fa.unit_ids)
        solar = mc[uids.index("WECC_DSW_DSW_solar_PV")]
        ct = mc[uids.index("WECC_DSW_DSW_CT")]
        self.assertTrue(np.all(ct > solar))


class TestForwardCorridorATC(unittest.TestCase):
    """The forward ATC is a capability ceiling that tightens midday."""

    def test_atc_scales_with_ttc_and_tightens_midday(self):
        cfg = split_caiso_import_node_per_hub(get_iso_config("CAISO"))
        env = forward_corridor_atc_envelope(cfg, "CAISO", YEAR, HOURS)
        self.assertIsNotNone(env)
        midday, overnight = _hod_mask(10, 15), _hod_mask(0, 5)
        for zone, spec in CAISO_PER_HUB_NEIGHBORS.items():
            cap = env[zone]
            # Bounded by the corridor TTC × base fraction (the off-peak ceiling).
            link_ttc = {"WECC_PNW": 4800.0, "WECC_DSW": 10623.0}[zone]
            self.assertLessEqual(cap.max(), link_ttc * spec.atc_base_fraction + 1.0)
            # Never below the solar floor of that ceiling.
            floor = link_ttc * spec.atc_base_fraction * spec.atc_solar_floor
            self.assertGreaterEqual(cap.min(), floor - 1.0)
            # Midday (solar-saturated) is tighter than overnight.
            self.assertLess(cap[midday].mean(), cap[overnight].mean())

    def test_non_caiso_is_noop(self):
        cfg = get_iso_config("PJM")
        self.assertIsNone(forward_corridor_atc_envelope(cfg, "PJM", YEAR, HOURS))


class TestCaisoSolarFraction(unittest.TestCase):
    """The forward solar driver is a bounded fraction peaking midday."""

    def test_fraction_bounded_and_peaks_midday(self):
        frac = caiso_solar_fraction(YEAR, HOURS)
        self.assertIsNotNone(frac)
        self.assertTrue(np.all(frac >= 0.0) and np.all(frac <= 1.0))
        self.assertGreater(frac[_hod_mask(10, 15)].mean(), frac[_hod_mask(0, 5)].mean())


class TestImportTrancheCoverage(unittest.TestCase):
    """Every CAISO import tranche maps to one of the two forward corridors."""

    def test_all_tranches_have_a_corridor(self):
        from market_sim.config.interchange_config import (
            CAISO_IMPORT_TRANCHE_HUB,
            CAISO_PER_HUB_IMPORT_ZONES,
        )

        zones = {spec.zone for spec in CAISO_PER_HUB_NEIGHBORS.values()}
        for name, _, _ in IMPORT_TRANCHES["CAISO"]:
            hub = CAISO_IMPORT_TRANCHE_HUB[name]
            self.assertIn(CAISO_PER_HUB_IMPORT_ZONES[hub], zones)


if __name__ == "__main__":
    unittest.main()
