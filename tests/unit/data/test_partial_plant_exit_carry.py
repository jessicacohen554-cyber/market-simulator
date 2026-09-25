"""Tests for the partial-plant mid-window exit carry (miso-190).

``fleet.load_retired_within_window(..., partial_plant_exit_carry=True)``
widens the retiree channel's membership with units retired mid-window whose
plants SURVIVE in the operable snapshot (the builder's deliberate
whole-plant complement), each timed out at unit grain on its own actual
retirement month through ``cod_ramp.effective_cod``'s per-unit preference;
``load_mothballed_but_operating(..., partial_plant_exit_carry=True)``
widens the snapshot status set {OA} -> {OA, OS, SB} under the same
vintage-OP oracle. Design:
``results/calibration/PREREG-miso190-partial-plant-exit-carry-2026-08-30.md``.

Committed-data cases (real MISO channel: Sherco-2 / Dallman-3 /
Big Cajun 2-1 / Warrick-2), byte-inertness with the flag off, the exit
timing through effective_cod, and the gated coal supply registry.
"""

from market_sim.config.plant_taxonomy import COAL_CLASSES
import unittest

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.cod_ramp import effective_cod, load_cod_map, monthly_online_mask
from market_sim.data.fleet import (
    load_mothballed_but_operating,
    load_retired_within_window,
)


class TestPartialPlantExitCarry(unittest.TestCase):
    """Leg 1 through the real MISO retiree channel (committed data)."""

    @classmethod
    def setUpClass(cls):
        cls.ic = get_iso_config("MISO")

    def test_gate_default_off_in_config(self):
        self.assertFalse(ScenarioConfig().partial_plant_exit_carry)

    def test_default_off_is_byte_inert(self):
        # rule 24 / S-0 premise: the un-widened call is unchanged by the
        # field's existence — same membership with and without the kwarg.
        a = load_retired_within_window("MISO", self.ic, year=2024)
        b = load_retired_within_window(
            "MISO", self.ic, year=2024, partial_plant_exit_carry=False
        )
        self.assertEqual([g.unit_id for g in a], [g.unit_id for g in b])

    def test_partial_units_injected_with_unit_grain_exits(self):
        on = load_retired_within_window(
            "MISO",
            self.ic,
            year=2023,
            vintage_status_scope=True,
            partial_plant_exit_carry=True,
        )
        by_id = {g.unit_id: g for g in on}
        # Sherco-2 (682 MW, ret 2023-12) in a SURVIVING plant.
        self.assertIn("6090_2", by_id)
        sherco2 = by_id["6090_2"]
        self.assertEqual(sherco2.retirement_year, 2023)
        self.assertEqual(sherco2.retirement_month, 12)
        # More §6.6 named units.
        for uid in ("994_ST2", "6137_1", "6137_2", "4041_5", "4041_6", "1400_3"):
            self.assertIn(uid, by_id)
        # The armed oracle scopes the widened membership: Dallman-3 (OS in
        # vintage_2023, CAMPD-dark) and Weston-2 (OS in vintage_2022) out.
        self.assertNotIn("963_3", by_id)
        self.assertNotIn("4078_2", by_id)
        # Surviving siblings are NOT injected here (they live in the
        # operable snapshot, not this channel).
        self.assertNotIn("6090_1", by_id)
        self.assertNotIn("6090_3", by_id)
        # The whole-plant channel rides unchanged: Rush Island kept, the
        # miso-188 oracle drops stay dropped.
        self.assertIn(6155, {int(g.plant_code) for g in on})
        self.assertNotIn(862, {int(g.plant_code) for g in on})

    def test_exit_timing_rides_effective_cod_per_unit_preference(self):
        on = load_retired_within_window(
            "MISO", self.ic, year=2023, partial_plant_exit_carry=True
        )
        sherco2 = {g.unit_id: g for g in on}["6090_2"]
        cod_map = load_cod_map()
        oy, om, ry, rm = effective_cod(
            int(sherco2.plant_code),
            sherco2.online_year,
            sherco2.online_month,
            sherco2.retirement_year,
            sherco2.retirement_month,
            cod_map,
        )
        # The per-unit retirement wins over the plant-collapsed date (the
        # Homer City seam): online all of 2023, gone all of 2024 — while the
        # plant entry itself keeps whatever future date its SURVIVING units
        # carry (Sherco's siblings hold planned retirements years out), so
        # the siblings are untouched by the unit-grain exit.
        self.assertEqual((ry, rm), (2023, 12))
        self.assertTrue(monthly_online_mask(oy, om, ry, rm, 2023).all())
        self.assertFalse(monthly_online_mask(oy, om, ry, rm, 2024).any())
        plant_entry = cod_map.get(6090)
        self.assertIsNotNone(plant_entry)
        plant_ry = plant_entry[2]
        self.assertTrue(plant_ry is None or plant_ry > 2023)

    def test_registry_resolves_unranked_coal_and_never_overrides(self):
        from market_sim.data.coal import coal_supply_class

        load_retired_within_window(
            "MISO", self.ic, year=2023, partial_plant_exit_carry=True
        )
        # A B Brown (BIT) and Dan E Karn (SUB) resolve through the gated
        # registry; Sherco (receipt-resolved prb) is untouched by it.
        self.assertEqual(coal_supply_class(6137), "bituminous")
        self.assertEqual(coal_supply_class(1702), "prb")
        self.assertEqual(coal_supply_class(6090), "prb")


class TestExitCohortBinning(unittest.TestCase):
    """Binning-aware exit-cohort delivery (miso-191, PREREG-miso191 §1-§2).

    The miso-190 A/B found MISO's plant-binned LP discards per-unit
    retirements at ``fleet_to_bins`` (FINDING-miso190 §3). Form (a), frozen
    ex ante: a loader-stamped leg-1 partial-exit unit aggregates into its
    own date-scoped exit-cohort bin, whose tranches carry the unit's own
    retirement so ``effective_cod``'s per-unit preference times them out.
    """

    @classmethod
    def setUpClass(cls):
        cls.ic = get_iso_config("MISO")
        cls.channel = load_retired_within_window(
            "MISO",
            cls.ic,
            year=2023,
            vintage_status_scope=True,
            partial_plant_exit_carry=True,
        )

    def test_loader_stamps_partial_provenance_only(self):
        by_id = {g.unit_id: g for g in self.channel}
        # Leg-1 partial-exit units are stamped ...
        for uid in ("6090_2", "994_ST2", "6137_1", "1702_1A", "4041_5"):
            self.assertTrue(by_id[uid].partial_exit_unit, uid)
        # ... the whole-plant channel is NOT (Rush Island keeps today's
        # plant-collapsed timing; PREREG-miso191 §1 frozen scope).
        for g in self.channel:
            if int(g.plant_code) == 6155:
                self.assertFalse(g.partial_exit_unit)

    def test_loader_off_path_never_stamps(self):
        off = load_retired_within_window("MISO", self.ic, year=2023)
        self.assertFalse(any(g.partial_exit_unit for g in off))

    def test_fleet_to_bins_routes_cohorts_when_armed(self):
        from market_sim.data.fleet import fleet_to_bins

        cfg = ScenarioConfig(
            mode="backcast", weather_year=2023, partial_plant_exit_carry=True
        )
        bins = fleet_to_bins(self.channel, "MISO", cfg)
        coal = bins[bins["Plant_Group"].isin(COAL_CLASSES)]
        # Sherco-2's cohort: its own row, its own retirement.
        sherco = coal[(coal["Plant_Code"] == 6090) & (coal["Retirement_Year"].notna())]
        self.assertEqual(len(sherco), 1)
        self.assertEqual(int(sherco["Retirement_Year"].iloc[0]), 2023)
        self.assertEqual(int(sherco["Retirement_Month"].iloc[0]), 12)
        self.assertAlmostEqual(float(sherco["capacity_mw"].iloc[0]), 682.0, 0)
        # Karn's four same-month units pool into ONE cohort bin.
        karn = coal[coal["Plant_Code"] == 1702]
        self.assertEqual(len(karn), 1)
        self.assertEqual(int(karn["Retirement_Year"].iloc[0]), 2023)
        self.assertEqual(int(karn["Retirement_Month"].iloc[0]), 5)
        self.assertAlmostEqual(float(karn["capacity_mw"].iloc[0]), 486.0, 0)
        # The whole-plant channel keeps ordinary rows (no retirement carry).
        rush = bins[bins["Plant_Code"] == 6155]
        self.assertTrue(rush["Retirement_Year"].isna().all())

    def test_fleet_to_bins_pools_when_flag_off(self):
        from market_sim.data.fleet import fleet_to_bins

        cfg = ScenarioConfig(mode="backcast", weather_year=2023)
        bins = fleet_to_bins(self.channel, "MISO", cfg)
        # No cohort routing: every row's retirement columns are empty even
        # though the input units carry tags + retirements (the gate is the
        # config field, so a control build is unchanged).
        self.assertTrue(bins["Retirement_Year"].isna().all())
        self.assertTrue(bins["Retirement_Month"].isna().all())

    def test_bins_to_fleet_stamps_cohort_tranches(self):
        from market_sim.data.fleet import bins_to_fleet, fleet_to_bins

        cfg = ScenarioConfig(
            mode="backcast", weather_year=2023, partial_plant_exit_carry=True
        )
        bins = fleet_to_bins(self.channel, "MISO", cfg)
        fleet, _ = bins_to_fleet(bins, [z.name for z in self.ic.zones], cfg)
        cohort = [g for g in fleet if "_p6090_r202312_" in g.unit_id]
        self.assertTrue(cohort)  # presence, never vacuous (miso-190 §5.1)
        for g in cohort:
            self.assertEqual(g.retirement_year, 2023)
            self.assertEqual(g.retirement_month, 12)
            self.assertEqual(int(g.plant_code), 6090)
        # The COD ramp seam: online all 2023, gone all 2024.
        cod_map = load_cod_map()
        g = cohort[0]
        oy, om, ry, rm = effective_cod(
            int(g.plant_code),
            g.online_year,
            g.online_month,
            g.retirement_year,
            g.retirement_month,
            cod_map,
        )
        self.assertEqual((ry, rm), (2023, 12))
        self.assertTrue(monthly_online_mask(oy, om, ry, rm, 2023).all())
        self.assertFalse(monthly_online_mask(oy, om, ry, rm, 2024).any())
        # Non-cohort tranches carry no retirement.
        rush = [g for g in fleet if int(g.plant_code) == 6155]
        self.assertTrue(rush)
        for g in rush:
            self.assertIsNone(g.retirement_year)
            self.assertNotIn("_r20", g.unit_id)


class TestSnapshotStatusWidening(unittest.TestCase):
    """Leg 2 through the real MISO mothball re-carry (committed data)."""

    @classmethod
    def setUpClass(cls):
        cls.ic = get_iso_config("MISO")

    def test_default_off_is_byte_inert(self):
        a = load_mothballed_but_operating("MISO", self.ic, year=2023)
        b = load_mothballed_but_operating(
            "MISO", self.ic, year=2023, partial_plant_exit_carry=False
        )
        self.assertEqual([g.unit_id for g in a], [g.unit_id for g in b])

    def test_os_units_carried_by_vintage_op_oracle(self):
        on23 = load_mothballed_but_operating(
            "MISO", self.ic, year=2023, partial_plant_exit_carry=True
        )
        ids23 = {g.unit_id for g in on23}
        # Big Cajun 2-1 (OS in snapshot, OP in vintage_2023/2024) and
        # Warrick-2 (OS in snapshot, OP in vintage_2023 ONLY — OA in 2024).
        self.assertIn("6055_1", ids23)
        self.assertIn("6705_2", ids23)
        on24 = load_mothballed_but_operating(
            "MISO", self.ic, year=2024, partial_plant_exit_carry=True
        )
        ids24 = {g.unit_id for g in on24}
        self.assertIn("6055_1", ids24)
        self.assertNotIn("6705_2", ids24)
        # 2025: no committed vintage_2025 -> nothing carried (the Cottonwood
        # owner default), flag or no flag.
        on25 = load_mothballed_but_operating(
            "MISO", self.ic, year=2025, partial_plant_exit_carry=True
        )
        self.assertNotIn("6055_1", {g.unit_id for g in on25})

    def test_off_path_never_carries_os(self):
        off = load_mothballed_but_operating("MISO", self.ic, year=2023)
        ids = {g.unit_id for g in off}
        self.assertNotIn("6055_1", ids)
        self.assertNotIn("6705_2", ids)


if __name__ == "__main__":
    unittest.main()
