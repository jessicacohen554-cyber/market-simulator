"""Tests for the CAISO south-corridor DAYTIME trigger-OFF clean import depth (caiso-94).

Covers the builder gate (``build_caiso_per_hub_intertie(daytime_clean=)`` —
zero-capacity tranche only when armed), the availability injector
(:func:`market_sim.model.transmission.inject_caiso_dsw_daytime_clean` — hod 6-21
measured-hub trigger-OFF hours only, measured daytime depth net of the shaped
firm block AND the caiso-87 surplus tranche AND the caiso-93 overnight tranche,
eford preservation, inert without a measured hub), the load-bearing distinctness
(trigger-ON hours never arm — disjoint from caiso-87; hod 0-5 never arms —
disjoint from caiso-93), the 2023 Jan-Feb gap protection, the raw-hub no-wheel
pricing, and byte-identity of the shared seam when the flag is off.
"""

import unittest

import numpy as np

from market_sim.config.interchange_config import (
    CAISO_DAYTIME_CLEAN_HOD_MAX,
    CAISO_DAYTIME_CLEAN_HOD_MIN,
    CAISO_DSW_DAYTIME_CLEAN_DEPTH_BY_YEAR,
    CAISO_DSW_DAYTIME_CLEAN_NAME,
    CAISO_DSW_OVERNIGHT_CLEAN_NAME,
    CAISO_DSW_SURPLUS_CLEAN_NAME,
    CAISO_DSW_SURPLUS_REMOTE_VOM,
    CAISO_IMPORT_DELIVERY_BASIS,
    CAISO_OVERNIGHT_CLEAN_HOD_MAX,
    CAISO_PER_HUB_IMPORT_ZONES,
    IMPORT_TRANCHE_EF,
)
from market_sim.data.eia_loader import measured_intertie_hub_price_raw
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.data.fuel import socal_citygate_weekly_hourly
from market_sim.model.transmission import (
    build_caiso_per_hub_intertie,
    inject_caiso_dsw_daytime_clean,
    inject_caiso_dsw_overnight_clean,
    inject_caiso_dsw_surplus_clean,
    inject_caiso_firm_import_shape,
)

HOURS = 8760
ZONE = CAISO_PER_HUB_IMPORT_ZONES["PALOVRDE"]
DAYTIME_UID = f"{ZONE}_{CAISO_DSW_DAYTIME_CLEAN_NAME}"
SURPLUS_UID = f"{ZONE}_{CAISO_DSW_SURPLUS_CLEAN_NAME}"
OVERNIGHT_UID = f"{ZONE}_{CAISO_DSW_OVERNIGHT_CLEAN_NAME}"
HR_CCGT = 0.37 / 0.0531


def _fleet(daytime_clean=True, surplus_clean=False, overnight_clean=False, hours=HOURS):
    gens = build_caiso_per_hub_intertie(
        surplus_clean=surplus_clean,
        overnight_clean=overnight_clean,
        daytime_clean=daytime_clean,
    )
    zones = sorted({g.zone for g in gens})
    return generators_to_fleet_arrays(gens, zones, hours=hours)


def _daytime_off_mask(year, hours=HOURS):
    """The injector's exact window: daytime hod ∧ measured-hub ∧ NOT surplus."""
    hub = measured_intertie_hub_price_raw("CAISO", year, hours, "PALOVRDE")
    gas = np.asarray(socal_citygate_weekly_hourly(year, hours))
    floor = HR_CCGT * gas + CAISO_DSW_SURPLUS_REMOTE_VOM
    surplus = np.isfinite(hub) & np.isfinite(floor) & (hub < floor)
    hod = np.arange(hours) % 24
    daytime_hod = (hod >= CAISO_DAYTIME_CLEAN_HOD_MIN) & (
        hod <= CAISO_DAYTIME_CLEAN_HOD_MAX
    )
    return daytime_hod & np.isfinite(hub) & ~surplus, hub, surplus


class TestBuilderGate(unittest.TestCase):
    def test_off_has_no_daytime_row(self):
        gens = build_caiso_per_hub_intertie()
        self.assertNotIn(DAYTIME_UID, [g.unit_id for g in gens])

    def test_on_builds_zero_capacity_row(self):
        gens = build_caiso_per_hub_intertie(daytime_clean=True)
        row = next(g for g in gens if g.unit_id == DAYTIME_UID)
        self.assertEqual(row.pmax_mw, 0.0)
        self.assertEqual(row.zone, ZONE)
        # No border carbon and no wheel, by registry (WEIM transfer basis).
        self.assertEqual(IMPORT_TRANCHE_EF["CAISO"][CAISO_DSW_DAYTIME_CLEAN_NAME], 0.0)
        self.assertEqual(
            CAISO_IMPORT_DELIVERY_BASIS[CAISO_DSW_DAYTIME_CLEAN_NAME], (0.0, 0.0)
        )


class TestInjector(unittest.TestCase):
    def test_arms_daytime_off_hours_net_of_firm(self):
        fleet = _fleet()
        base_avail = fleet.availability.copy()
        self.assertTrue(inject_caiso_firm_import_shape(fleet, "CAISO", 2024))
        self.assertTrue(inject_caiso_dsw_daytime_clean(fleet, "CAISO", 2024))
        row = list(fleet.unit_ids).index(DAYTIME_UID)
        depth = CAISO_DSW_DAYTIME_CLEAN_DEPTH_BY_YEAR[2024]
        self.assertEqual(float(fleet.pmax[row]), depth)
        cap = fleet.pmax[row] * fleet.availability[row, :]
        daytime, _, _ = _daytime_off_mask(2024)
        firm_row = list(fleet.unit_ids).index(f"{ZONE}_DSW_solar_PV")
        firm_cap = fleet.pmax[firm_row] * fleet.availability[firm_row, :]
        expected = (
            np.where(daytime, np.clip(depth - firm_cap, 0.0, None), 0.0)
            * base_avail[row, 0]  # eford preserved multiplicatively
        )
        np.testing.assert_allclose(cap, expected, rtol=1e-6)
        self.assertGreater(float(cap.max()), 0.0)
        # Hours outside the daytime-OFF window never arm.
        self.assertTrue(np.all(cap[~daytime] == 0.0))

    def test_trigger_on_hours_never_arm(self):
        """LOAD-BEARING: caiso-87 surplus (trigger-ON) hours never arm — the
        daytime leg is disjoint from caiso-87's own mechanism."""
        fleet = _fleet()
        inject_caiso_firm_import_shape(fleet, "CAISO", 2024)
        self.assertTrue(inject_caiso_dsw_daytime_clean(fleet, "CAISO", 2024))
        row = list(fleet.unit_ids).index(DAYTIME_UID)
        cap = fleet.pmax[row] * fleet.availability[row, :]
        _, _, surplus = _daytime_off_mask(2024)
        self.assertGreater(int(surplus.sum()), 0)
        self.assertTrue(np.all(cap[surplus] == 0.0))

    def test_overnight_hours_never_arm(self):
        """Disjoint from caiso-93: hod 0-5 is never armed by the daytime leg."""
        fleet = _fleet()
        inject_caiso_firm_import_shape(fleet, "CAISO", 2024)
        self.assertTrue(inject_caiso_dsw_daytime_clean(fleet, "CAISO", 2024))
        row = list(fleet.unit_ids).index(DAYTIME_UID)
        cap = fleet.pmax[row] * fleet.availability[row, :]
        overnight = np.arange(HOURS) % 24 <= CAISO_OVERNIGHT_CLEAN_HOD_MAX
        self.assertTrue(np.all(cap[overnight] == 0.0))

    def test_nets_sibling_clean_tranches(self):
        """Nets the caiso-87 surplus AND caiso-93 overnight tranches so no hour
        double-carries clean depth."""
        fleet = _fleet(surplus_clean=True, overnight_clean=True)
        base_avail = fleet.availability.copy()
        self.assertTrue(inject_caiso_firm_import_shape(fleet, "CAISO", 2024))
        self.assertTrue(inject_caiso_dsw_surplus_clean(fleet, "CAISO", 2024))
        self.assertTrue(inject_caiso_dsw_overnight_clean(fleet, "CAISO", 2024))
        self.assertTrue(inject_caiso_dsw_daytime_clean(fleet, "CAISO", 2024))
        uids = list(fleet.unit_ids)
        row = uids.index(DAYTIME_UID)
        sur = uids.index(SURPLUS_UID)
        ovn = uids.index(OVERNIGHT_UID)
        depth = CAISO_DSW_DAYTIME_CLEAN_DEPTH_BY_YEAR[2024]
        cap = fleet.pmax[row] * fleet.availability[row, :]
        sur_cap = fleet.pmax[sur] * fleet.availability[sur, :]
        ovn_cap = fleet.pmax[ovn] * fleet.availability[ovn, :]
        daytime, _, _ = _daytime_off_mask(2024)
        firm_row = uids.index(f"{ZONE}_DSW_solar_PV")
        firm_cap = fleet.pmax[firm_row] * fleet.availability[firm_row, :]
        expected = (
            np.where(
                daytime,
                np.clip(depth - firm_cap - sur_cap - ovn_cap, 0.0, None),
                0.0,
            )
            * base_avail[row, 0]
        )
        np.testing.assert_allclose(cap, expected, rtol=1e-6)
        # In the daytime-OFF window the caiso-93 overnight tranche is 0 (hod 0-5
        # disjoint) and the caiso-87 surplus tranche is 0 (trigger-OFF), so the
        # netting reduces to firm only — but the code path exercises all three.
        self.assertTrue(np.all(ovn_cap[daytime] == 0.0))
        self.assertTrue(np.all(sur_cap[daytime] == 0.0))

    def test_2023_gap_hours_never_arm(self):
        fleet = _fleet()
        inject_caiso_firm_import_shape(fleet, "CAISO", 2023)
        self.assertTrue(inject_caiso_dsw_daytime_clean(fleet, "CAISO", 2023))
        row = list(fleet.unit_ids).index(DAYTIME_UID)
        hub = measured_intertie_hub_price_raw("CAISO", 2023, HOURS, "PALOVRDE")
        gap = ~np.isfinite(hub)
        self.assertGreater(int(gap.sum()), 0)
        cap = fleet.pmax[row] * fleet.availability[row, :]
        self.assertTrue(np.all(cap[gap] == 0.0))

    def test_no_daytime_row_returns_false(self):
        fleet = _fleet(daytime_clean=False)
        self.assertFalse(inject_caiso_dsw_daytime_clean(fleet, "CAISO", 2024))

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
            caiso_dsw_daytime_clean=True,
        )
        apply_interchange_injections(fleet, mc, config, "CAISO", 2024)
        row = list(fleet.unit_ids).index(DAYTIME_UID)
        self.assertGreater(float(fleet.pmax[row]), 0.0)

    def test_per_hub_pricing_raw_hub_no_wheel_no_carbon(self):
        """The measured per-hub injector prices the daytime row at the RAW hub:
        exactly 2·eps above the DSW export leg (hub − eps) — no wheel, no
        carbon — and $4 + border·(0.37/0.428) BELOW the DSW_CCGT rung."""
        from market_sim.model.transmission import inject_caiso_per_hub_intertie_prices

        fleet = _fleet()
        mc = np.zeros((len(fleet.unit_ids), HOURS))
        border = 15.0
        carbon_price = border / 0.428
        self.assertTrue(
            inject_caiso_per_hub_intertie_prices(fleet, mc, "CAISO", 2024, carbon_price)
        )
        uids = list(fleet.unit_ids)
        row = uids.index(DAYTIME_UID)
        exp_row = uids.index(f"{ZONE}_export_PALOVRDE")
        ccgt_row = uids.index(f"{ZONE}_DSW_CCGT")
        diff_export = np.median(mc[row, :] - mc[exp_row, :])
        self.assertAlmostEqual(float(diff_export), 0.0, delta=0.01)  # 2·eps only
        diff_ccgt = np.median(mc[ccgt_row, :] - mc[row, :])
        self.assertAlmostEqual(
            float(diff_ccgt), 4.0 + border * (0.37 / 0.428), delta=0.1
        )  # the fossil rung keeps its wheel and carbon


if __name__ == "__main__":
    unittest.main()
