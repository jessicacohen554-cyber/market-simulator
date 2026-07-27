"""Tests for the CAISO south-corridor surplus-clean import depth (caiso-87).

Covers the builder gate (``build_caiso_per_hub_intertie(surplus_clean=)`` —
zero-capacity tranche only when armed), the availability injector
(:func:`market_sim.model.transmission.inject_caiso_dsw_surplus_clean` —
surplus-trigger hours only, measured year depth net of the shaped firm block,
eford preservation, inert without measured inputs), the raw-evidence hub
loader (NaN-preserving), the SoCal weekly gas staircase, and byte-identity of
the shared seam when the flag is off.
"""

import unittest

import numpy as np

from market_sim.config.interchange_config import (
    CAISO_DSW_SURPLUS_CLEAN_DEPTH_BY_YEAR,
    CAISO_DSW_SURPLUS_CLEAN_NAME,
    CAISO_DSW_SURPLUS_REMOTE_VOM,
    CAISO_PER_HUB_IMPORT_ZONES,
    IMPORT_TRANCHE_EF,
)
from market_sim.data.eia_loader import measured_intertie_hub_price_raw
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.data.fuel import socal_citygate_weekly_hourly
from market_sim.model.transmission import (
    _CAISO_IMPORT_COUPLE_HR,
    build_caiso_per_hub_intertie,
    inject_caiso_dsw_surplus_clean,
    inject_caiso_firm_import_shape,
)

HOURS = 8760
CLEAN_UID = f"{CAISO_PER_HUB_IMPORT_ZONES['PALOVRDE']}_{CAISO_DSW_SURPLUS_CLEAN_NAME}"


def _fleet(surplus_clean=True, hours=HOURS):
    gens = build_caiso_per_hub_intertie(surplus_clean=surplus_clean)
    zones = sorted({g.zone for g in gens})
    return generators_to_fleet_arrays(gens, zones, hours=hours)


class TestBuilderGate(unittest.TestCase):
    def test_off_has_no_clean_row(self):
        gens = build_caiso_per_hub_intertie()
        self.assertNotIn(CLEAN_UID, [g.unit_id for g in gens])

    def test_on_builds_zero_capacity_row(self):
        gens = build_caiso_per_hub_intertie(surplus_clean=True)
        row = next(g for g in gens if g.unit_id == CLEAN_UID)
        self.assertEqual(row.pmax_mw, 0.0)
        self.assertEqual(row.zone, CAISO_PER_HUB_IMPORT_ZONES["PALOVRDE"])
        # The clean tranche pays no border carbon by registry.
        self.assertEqual(IMPORT_TRANCHE_EF["CAISO"][CAISO_DSW_SURPLUS_CLEAN_NAME], 0.0)


class TestLoaders(unittest.TestCase):
    def test_raw_hub_preserves_the_2023_retention_gap(self):
        raw = measured_intertie_hub_price_raw("CAISO", 2023, HOURS, "PALOVRDE")
        self.assertIsNotNone(raw)
        self.assertEqual(raw.shape, (HOURS,))
        self.assertGreater(int(np.isnan(raw).sum()), 1000)  # Jan-Feb gap stays NaN

    def test_raw_hub_full_years_are_dense(self):
        for year in (2024, 2025):
            raw = measured_intertie_hub_price_raw("CAISO", year, HOURS, "PALOVRDE")
            self.assertEqual(int(np.isnan(raw).sum()), 0)

    def test_raw_hub_non_caiso_none(self):
        self.assertIsNone(
            measured_intertie_hub_price_raw("PJM", 2024, HOURS, "PALOVRDE")
        )

    def test_socal_weekly_staircase(self):
        for year in (2023, 2024, 2025):
            g = socal_citygate_weekly_hourly(year, HOURS)
            self.assertEqual(g.shape, (HOURS,))
            self.assertTrue(np.all(np.isfinite(g)))
        self.assertIsNone(socal_citygate_weekly_hourly(1999, HOURS))


class TestInjector(unittest.TestCase):
    def test_arms_only_surplus_hours_and_nets_firm(self):
        fleet = _fleet()
        base_avail = fleet.availability.copy()
        # Shape the firm blocks first (the injector headroom is net-of-firm).
        self.assertTrue(inject_caiso_firm_import_shape(fleet, "CAISO", 2024))
        self.assertTrue(inject_caiso_dsw_surplus_clean(fleet, "CAISO", 2024))
        row = list(fleet.unit_ids).index(CLEAN_UID)
        depth = CAISO_DSW_SURPLUS_CLEAN_DEPTH_BY_YEAR[2024]
        self.assertEqual(float(fleet.pmax[row]), depth)
        cap = fleet.pmax[row] * fleet.availability[row, :]
        # Recompute the trigger + firm headroom independently.
        hub = measured_intertie_hub_price_raw("CAISO", 2024, HOURS, "PALOVRDE")
        gas = socal_citygate_weekly_hourly(2024, HOURS)
        floor = _CAISO_IMPORT_COUPLE_HR["DSW_CCGT"] * gas + CAISO_DSW_SURPLUS_REMOTE_VOM
        surplus = np.isfinite(hub) & (hub < floor)
        firm_row = list(fleet.unit_ids).index("WECC_DSW_DSW_solar_PV")
        firm_cap = fleet.pmax[firm_row] * fleet.availability[firm_row, :]
        expected = (
            np.where(surplus, np.clip(depth - firm_cap, 0.0, None), 0.0)
            * base_avail[row, 0]  # eford preserved multiplicatively
        )
        np.testing.assert_allclose(cap, expected, rtol=1e-6)
        self.assertGreater(float(cap.max()), 0.0)
        self.assertTrue(np.all(cap[~surplus] == 0.0))

    def test_2023_gap_hours_never_arm(self):
        fleet = _fleet()
        inject_caiso_firm_import_shape(fleet, "CAISO", 2023)
        self.assertTrue(inject_caiso_dsw_surplus_clean(fleet, "CAISO", 2023))
        row = list(fleet.unit_ids).index(CLEAN_UID)
        hub = measured_intertie_hub_price_raw("CAISO", 2023, HOURS, "PALOVRDE")
        gap = ~np.isfinite(hub)
        self.assertGreater(int(gap.sum()), 0)
        cap = fleet.pmax[row] * fleet.availability[row, :]
        self.assertTrue(np.all(cap[gap] == 0.0))

    def test_no_clean_row_returns_false(self):
        fleet = _fleet(surplus_clean=False)
        self.assertFalse(inject_caiso_dsw_surplus_clean(fleet, "CAISO", 2024))

    def test_seam_gate_off_is_byte_identical(self):
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.model.transmission import apply_interchange_injections

        fleet = _fleet()
        base_avail = fleet.availability.copy()
        base_pmax = fleet.pmax.copy()
        mc = np.zeros((len(fleet.unit_ids), HOURS))
        config = ScenarioConfig().with_overrides(caiso_per_hub_intertie=True)
        apply_interchange_injections(fleet, mc, config, "CAISO", 2024)
        np.testing.assert_array_equal(fleet.availability, base_avail)
        np.testing.assert_array_equal(fleet.pmax, base_pmax)

    def test_seam_gate_on_arms_via_shared_seam(self):
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.model.transmission import apply_interchange_injections

        fleet = _fleet()
        mc = np.zeros((len(fleet.unit_ids), HOURS))
        config = ScenarioConfig().with_overrides(
            caiso_per_hub_intertie=True,
            caiso_dsw_surplus_clean=True,
        )
        apply_interchange_injections(fleet, mc, config, "CAISO", 2024)
        row = list(fleet.unit_ids).index(CLEAN_UID)
        self.assertGreater(float(fleet.pmax[row]), 0.0)

    def test_per_hub_pricing_carries_no_carbon(self):
        """The measured per-hub injector prices the clean row at hub + wheel
        with a ZERO carbon term: exactly wheel + 2·eps above the DSW export
        leg (hub − eps), and border·(0.37/0.428) BELOW the DSW_CCGT rung."""
        from market_sim.model.transmission import (
            inject_caiso_per_hub_intertie_prices,
        )

        fleet = _fleet()
        mc = np.zeros((len(fleet.unit_ids), HOURS))
        border = 15.0
        carbon_price = border / 0.428
        self.assertTrue(
            inject_caiso_per_hub_intertie_prices(fleet, mc, "CAISO", 2024, carbon_price)
        )
        uids = list(fleet.unit_ids)
        row = uids.index(CLEAN_UID)
        exp_row = uids.index("WECC_DSW_export_PALOVRDE")
        ccgt_row = uids.index("WECC_DSW_DSW_CCGT")
        diff_export = np.median(mc[row, :] - mc[exp_row, :])
        self.assertAlmostEqual(float(diff_export), 4.0, delta=0.1)  # wheel, no carbon
        diff_ccgt = np.median(mc[ccgt_row, :] - mc[row, :])
        self.assertAlmostEqual(
            float(diff_ccgt), border * (0.37 / 0.428), delta=0.1
        )  # the fossil rung keeps its carbon


if __name__ == "__main__":
    unittest.main()
