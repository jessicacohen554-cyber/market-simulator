"""Tests for the unified carbon-program resolver (policy/cap_and_trade.py)."""

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.policy.cap_and_trade import (
    CarbonProgramResolution,
    MassCapSpec,
    measured_price,
    named_program_price,
    per_generator_membership,
    projected_price,
    resolve_carbon_program,
)
from market_sim.config.constants import CAP_AND_TRADE_PROGRAMS


class TestResolverInvariant:
    """Exactly one of price_adder / cap_spec is set (plan §6)."""

    def test_adder_path_sets_only_price(self):
        res = resolve_carbon_program(ScenarioConfig(iso="CAISO", mode="backcast"), 2024)
        assert res is not None
        assert res.price_adder is not None
        assert res.cap_spec is None

    def test_construct_with_both_raises(self):
        with pytest.raises(ValueError):
            CarbonProgramResolution(
                membership=np.ones(3),
                price_adder=10.0,
                cap_spec=MassCapSpec(membership=np.ones(3), cap_tons=1.0),
            )

    def test_construct_with_neither_raises(self):
        with pytest.raises(ValueError):
            CarbonProgramResolution(membership=np.ones(3))


class TestMembership:
    """Per-zone membership m_zone (plan §5)."""

    def test_caiso_excludes_wecc_import_node(self):
        res = resolve_carbon_program(ScenarioConfig(iso="CAISO", mode="backcast"), 2024)
        # NP15, ZP26, SP15 in-state (1.0); WECC_import external (0.0).
        np.testing.assert_array_equal(res.membership, [1.0, 1.0, 1.0, 0.0])

    def test_nyiso_all_zones_member(self):
        res = resolve_carbon_program(ScenarioConfig(iso="NYISO", mode="backcast"), 2024)
        np.testing.assert_array_equal(res.membership, np.ones(5))

    def test_neiso_excludes_hq_import_node(self):
        res = resolve_carbon_program(ScenarioConfig(iso="NEISO", mode="backcast"), 2024)
        # North, Central, Boston, Connecticut member (1.0); HQ_import (0.0).
        np.testing.assert_array_equal(res.membership, [1.0, 1.0, 1.0, 1.0, 0.0])

    def test_pjm_fractional_membership_from_eia860_crosswalk(self):
        # PJM_RGGI_ZONE_SHARE is populated from the EIA-860→state crosswalk
        # (plan §5): most zones are non-member, EMAAC/SWMAAC are mostly
        # member (NJ/DE/MD), Dominion (VA+NC) drops to 0 after VA's 2024 exit.
        res = resolve_carbon_program(ScenarioConfig(iso="PJM", mode="backcast"), 2024)
        assert res is not None
        zone_names = [
            "PJM_ComEd",
            "PJM_AEP_Ohio",
            "PJM_ATSI",
            "PJM_West_APS",
            "PJM_Central_PA",
            "PJM_Dominion",
            "PJM_EMAAC",
            "PJM_SWMAAC",
        ]
        np.testing.assert_array_equal(
            res.membership,
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.7252, 0.9976],
        )
        assert len(zone_names) == res.membership.size
        # The adder path stays inert: PJM has no measured price series.
        assert res.price_adder == 0.0

    def test_pjm_dominion_membership_reflects_virginia_exit(self):
        # PJM_Dominion (VA+NC) is ~0.99 member in 2023 (VA still in RGGI) and
        # 0.0 from 2024 (VA exited 1 Jan 2024) -- the year-aware zone_share.
        dominion_idx = 5
        res_2023 = resolve_carbon_program(
            ScenarioConfig(iso="PJM", mode="backcast"), 2023
        )
        res_2024 = resolve_carbon_program(
            ScenarioConfig(iso="PJM", mode="backcast"), 2024
        )
        assert res_2023.membership[dominion_idx] == pytest.approx(0.9881)
        assert res_2024.membership[dominion_idx] == 0.0


class TestNoProgram:
    def test_ercot_and_miso_have_no_program(self):
        for iso in ("ERCOT", "MISO"):
            assert resolve_carbon_program(ScenarioConfig(iso=iso), 2024) is None

    def test_state_carbon_pricing_off_disables(self):
        res = resolve_carbon_program(
            ScenarioConfig(iso="CAISO", mode="backcast", state_carbon_pricing=False),
            2024,
        )
        assert res is None


class TestAdderSource:
    """Measured backcast vs projected forecast (EM-6 seam closure, §9.3)."""

    @pytest.mark.parametrize(
        "iso,year,expected",
        [("CAISO", 2024, 35.23), ("NYISO", 2025, 22.09), ("NEISO", 2023, 14.87)],
    )
    def test_backcast_uses_measured(self, iso, year, expected):
        res = resolve_carbon_program(ScenarioConfig(iso=iso, mode="backcast"), year)
        assert res.price_adder == pytest.approx(expected)

    def test_forecast_carries_projected_nonzero(self):
        # Seam closure: a forecast year now has a positive program adder where a
        # program exists (plan §9.3), instead of the pre-EM-6 zero.
        for iso in ("CAISO", "NYISO", "NEISO"):
            res = resolve_carbon_program(ScenarioConfig(iso=iso), 2030)
            assert res.price_adder > 0.0

    def test_projected_escalates_from_last_measured(self):
        prog = CAP_AND_TRADE_PROGRAMS["CAISO"]
        anchor = measured_price("CAISO", 2025)
        assert projected_price(prog, "CAISO", 2027) == pytest.approx(
            anchor * (1 + prog.escalation_rate) ** 2
        )

    def test_explicit_rff_path_wins_in_forecast(self):
        # A non-default carbon_price_path keeps its exogenous meaning.
        res = resolve_carbon_program(
            ScenarioConfig(iso="CAISO", carbon_price_path="mid"), 2030
        )
        # No program adder → falls through to the RFF path (handled by the
        # scalar wrapper); the resolver returns a zero program adder here.
        assert res.price_adder == 0.0


class TestCapPath:
    """The optional power-sector mass-cap row path (plan §6)."""

    def test_mass_cap_enabled_with_budget_returns_cap_spec(self):
        res = resolve_carbon_program(
            ScenarioConfig(
                iso="CAISO", mode="backcast", mass_cap_enabled=True, mass_cap_tons=1.0e6
            ),
            2024,
        )
        assert res.cap_spec is not None
        assert res.price_adder is None
        assert res.cap_spec.cap_tons == 1.0e6
        np.testing.assert_array_equal(res.cap_spec.membership, [1.0, 1.0, 1.0, 0.0])

    def test_mass_cap_enabled_uses_published_budget(self):
        # With the CARB/RGGI schedules landed, enabling the row with no explicit
        # mass_cap_tons pulls the published budget for the ISO/year, unit-
        # converted to metric tonnes (CARB MMT CO2e x 1e6).
        from market_sim.config.constants import CARB_ALLOWANCE_BUDGET

        res = resolve_carbon_program(
            ScenarioConfig(iso="CAISO", mode="backcast", mass_cap_enabled=True), 2024
        )
        assert res.price_adder is None
        assert res.cap_spec is not None
        assert res.cap_spec.cap_tons == pytest.approx(CARB_ALLOWANCE_BUDGET[2024] * 1e6)

    def test_rggi_row_uses_member_state_budget_in_metric_tonnes(self):
        # A RGGI ISO's row RHS is the SUM of its own member states' published
        # budgets (not the region-wide over-bound) converted to metric tonnes.
        from market_sim.config.constants import (
            RGGI_STATE_CO2_BUDGET,
            SHORT_TON_TO_METRIC_TONNE,
        )

        res = resolve_carbon_program(
            ScenarioConfig(iso="NYISO", mode="backcast", mass_cap_enabled=True), 2025
        )
        expected = RGGI_STATE_CO2_BUDGET["NY"][2025] * SHORT_TON_TO_METRIC_TONNE
        assert res.cap_spec.cap_tons == pytest.approx(expected)
        # The per-state sum is strictly tighter than the old regional over-bound.
        assert (
            res.cap_spec.cap_tons
            < RGGI_STATE_CO2_BUDGET["RGGI"][2025] * SHORT_TON_TO_METRIC_TONNE
        )

    def test_neiso_row_sums_its_six_member_states(self):
        # NEISO's row is CT+ME+MA+NH+RI+VT's budgets summed, not NY's or the
        # full regional total.
        from market_sim.config.constants import (
            RGGI_STATE_CO2_BUDGET,
            SHORT_TON_TO_METRIC_TONNE,
        )

        res = resolve_carbon_program(
            ScenarioConfig(iso="NEISO", mode="backcast", mass_cap_enabled=True), 2025
        )
        expected_short_tons = sum(
            RGGI_STATE_CO2_BUDGET[s][2025] for s in ("CT", "ME", "MA", "NH", "RI", "VT")
        )
        assert res.cap_spec.cap_tons == pytest.approx(
            expected_short_tons * SHORT_TON_TO_METRIC_TONNE
        )

    def test_pjm_row_drops_virginia_after_2023(self):
        # PJM's member-state budget sum includes VA only in 2023; from 2024 it
        # is MD+DE+NJ only (VA's 2024-01-01 exit, RGGI_MEMBER_STATES_BY_YEAR).
        from market_sim.config.constants import (
            RGGI_STATE_CO2_BUDGET,
            SHORT_TON_TO_METRIC_TONNE,
        )

        res_2023 = resolve_carbon_program(
            ScenarioConfig(iso="PJM", mode="backcast", mass_cap_enabled=True), 2023
        )
        res_2024 = resolve_carbon_program(
            ScenarioConfig(iso="PJM", mode="backcast", mass_cap_enabled=True), 2024
        )
        expected_2023 = sum(
            RGGI_STATE_CO2_BUDGET[s][2023] for s in ("MD", "DE", "NJ", "VA")
        )
        expected_2024 = sum(RGGI_STATE_CO2_BUDGET[s][2024] for s in ("MD", "DE", "NJ"))
        assert res_2023.cap_spec.cap_tons == pytest.approx(
            expected_2023 * SHORT_TON_TO_METRIC_TONNE
        )
        assert res_2024.cap_spec.cap_tons == pytest.approx(
            expected_2024 * SHORT_TON_TO_METRIC_TONNE
        )

    def test_explicit_tons_override_wins_over_published(self):
        # An explicit scenario budget is taken as-is (metric tonnes), ahead of
        # the published schedule.
        res = resolve_carbon_program(
            ScenarioConfig(
                iso="CAISO", mode="backcast", mass_cap_enabled=True, mass_cap_tons=5.0e6
            ),
            2024,
        )
        assert res.cap_spec.cap_tons == pytest.approx(5.0e6)

    def test_quarantined_year_has_no_published_budget(self):
        # No 2026 budget row is landed (holdout quarantine, rule 22), so the row
        # stays inert and the adder path is used.
        res = resolve_carbon_program(
            ScenarioConfig(iso="CAISO", mode="backcast", mass_cap_enabled=True), 2026
        )
        assert res.cap_spec is None


class TestMembershipWeightedAdder:
    """assemble_mc accepts a per-generator membership-weighted carbon adder."""

    def test_fractional_membership_charges_only_member_zone(self):
        # Plan §9.6: with m_zone=[1.0, 0.0] the carbon adder charges only zone-0
        # fossil; zone-1's merit order is unchanged from the carbon-free case.
        from market_sim.data.fleet import (
            Generator,
            assemble_mc,
            generators_to_fleet_arrays,
        )

        generators = [
            Generator(
                unit_id="G0",
                name="G0",
                zone="Z0",
                fuel_type="gas_cc",
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,
                emission_rate_co2=0.37,
            ),
            Generator(
                unit_id="G1",
                name="G1",
                zone="Z1",
                fuel_type="gas_cc",
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,
                emission_rate_co2=0.37,
            ),
        ]
        fleet = generators_to_fleet_arrays(generators, ["Z0", "Z1"], hours=4)
        fuel_prices = np.zeros((fleet.n_gen, 4))  # isolate the carbon term
        price = 30.0
        m_zone = np.array([1.0, 0.0])
        per_gen_adder = m_zone[fleet.zone_idx] * price  # (n_gen,)

        mc = assemble_mc(fleet, fuel_prices, carbon_price=per_gen_adder)
        mc_free = assemble_mc(fleet, fuel_prices, carbon_price=0.0)
        # Zone-0 gets the full carbon wedge; zone-1 gets none.
        assert mc[0, 0] == pytest.approx(fleet.emission_rate[0] * price)
        assert mc[0, 0] > mc_free[0, 0]
        np.testing.assert_allclose(mc[1], mc_free[1])

    def test_uniform_membership_reproduces_scalar_bit_for_bit(self):
        # m_zone == 1 everywhere → the per-gen adder equals the scalar path.
        from market_sim.data.fleet import (
            Generator,
            assemble_mc,
            generators_to_fleet_arrays,
        )

        generators = [
            Generator(
                unit_id=f"G{i}",
                name=f"G{i}",
                zone="Z0",
                fuel_type="gas_cc",
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,
                emission_rate_co2=0.37,
            )
            for i in range(3)
        ]
        fleet = generators_to_fleet_arrays(generators, ["Z0"], hours=4)
        fuel_prices = np.full((fleet.n_gen, 4), 3.0)
        price = 28.06
        per_gen = np.ones(fleet.n_gen) * price
        np.testing.assert_array_equal(
            assemble_mc(fleet, fuel_prices, carbon_price=per_gen),
            assemble_mc(fleet, fuel_prices, carbon_price=price),
        )


class TestPerGeneratorMembership:
    """Per-unit RGGI membership (plan §5, §9.6): exact where plant_code is
    real, zone-level fallback only for synthetic/aggregate units."""

    def _fleet(self, specs):
        """Build a tiny FleetArrays from (zone, plant_code) pairs."""
        from market_sim.data.fleet import Generator, generators_to_fleet_arrays

        zones = sorted({zone for zone, _ in specs})
        generators = [
            Generator(
                unit_id=f"G{i}",
                name=f"G{i}",
                zone=zone,
                fuel_type="gas_cc",
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,
                emission_rate_co2=0.4,
                plant_code=plant_code,
            )
            for i, (zone, plant_code) in enumerate(specs)
        ]
        return generators_to_fleet_arrays(generators, zones, hours=4)

    def test_trivial_real_plant_overrides_synthetic_fallback(self):
        # Zone-level fallback is 0.5 for both generators; G0's real plant_code
        # resolves to a member state (exact 1.0), G1 is synthetic
        # (plant_code<=0) and keeps the zone fallback.
        fleet = self._fleet([("Z0", 101), ("Z0", 0)])
        zone_membership = np.array([0.5])
        out = per_generator_membership(
            "PJM", 2024, zone_membership, fleet, plant_state={101: "NJ"}
        )
        np.testing.assert_array_equal(out, [1.0, 0.5])

    def test_trivial_real_plant_in_nonmember_state_is_zero(self):
        fleet = self._fleet([("Z0", 202)])
        zone_membership = np.array([0.7327])  # PJM_EMAAC-like fallback
        out = per_generator_membership(
            "PJM", 2024, zone_membership, fleet, plant_state={202: "OH"}
        )
        np.testing.assert_array_equal(out, [0.0])

    def test_unresolvable_plant_code_keeps_zone_fallback(self):
        # A real plant_code absent from the injected state lookup (e.g. a
        # plant EIA-860 has no record for) keeps the zone-level share.
        fleet = self._fleet([("Z0", 999)])
        zone_membership = np.array([0.3])
        out = per_generator_membership(
            "PJM", 2024, zone_membership, fleet, plant_state={101: "NJ"}
        )
        np.testing.assert_array_equal(out, [0.3])

    def test_pjm_cap_row_coefficients_hit_only_member_units(self):
        # PJM_EMAAC (NJ-plant + PA-plant) and PJM_AEP_Ohio (OH-plant): the
        # per-generator mask must zero out the coefficient on every
        # non-member unit regardless of its zone's fractional fallback, and
        # keep it nonzero only on the member unit.
        fleet = self._fleet(
            [
                ("PJM_EMAAC", 301),  # NJ -- member
                ("PJM_EMAAC", 302),  # PA (Philly-metro slice) -- non-member
                ("PJM_AEP_Ohio", 303),  # OH -- non-member
            ]
        )
        program = CAP_AND_TRADE_PROGRAMS["PJM"]
        zone_membership = np.array(
            [
                program.zone_share["PJM_EMAAC"][2024],
                program.zone_share["PJM_AEP_Ohio"][2024],
            ]
        )
        plant_state = {301: "NJ", 302: "PA", 303: "OH"}
        mask = per_generator_membership(
            "PJM", 2024, zone_membership, fleet, plant_state=plant_state
        )
        cap_coeffs = mask * fleet.emission_rate

        np.testing.assert_array_equal(mask, [1.0, 0.0, 0.0])
        assert cap_coeffs[0] == pytest.approx(fleet.emission_rate[0])
        assert cap_coeffs[1] == 0.0
        assert cap_coeffs[2] == 0.0

    def test_non_rggi_program_returns_zone_fallback_unchanged(self):
        # ERCOT/MISO have no program at all -- per_generator_membership is a
        # no-op passthrough of the zone broadcast.
        fleet = self._fleet([("North", 401)])
        zone_membership = np.array([0.0])
        out = per_generator_membership(
            "ERCOT", 2024, zone_membership, fleet, plant_state={401: "TX"}
        )
        np.testing.assert_array_equal(out, [0.0])


class TestPublishedBudgetConstantsMatchRawCsv:
    """The in-repo budget constants mirror the committed cited raw CSVs.

    The clean/ tree is gitignored, so the authoritative in-repo value lives in
    constants.py; this guards against the constant and the curated raw source
    drifting apart (single source of truth, rule 24-adjacent).
    """

    def test_carb_budget_and_floor_match_csv(self):
        from market_sim.config.constants import (
            CARB_ALLOWANCE_BUDGET,
            CARB_FLOOR_PRICE,
        )
        from market_sim.config.paths import RAW_DIR
        from scripts import curate_carb_cap_schedule as carb

        df = carb.parse(RAW_DIR)
        budget = df[df["metric"] == "allowance_budget"]
        floor = df[df["metric"] == "auction_reserve_price"]
        assert dict(zip(budget["budget_year"], budget["value"])) == pytest.approx(
            CARB_ALLOWANCE_BUDGET
        )
        assert dict(zip(floor["budget_year"], floor["value"])) == pytest.approx(
            CARB_FLOOR_PRICE
        )

    def test_rggi_regional_budget_matches_csv(self):
        from market_sim.config.constants import RGGI_STATE_CO2_BUDGET
        from market_sim.config.paths import RAW_DIR
        from scripts import curate_rggi_co2_budgets as rggi

        df = rggi.parse(RAW_DIR)
        regional = df[(df["state"] == "RGGI") & (df["metric"] == "allowance_budget")]
        assert dict(zip(regional["budget_year"], regional["value"])) == pytest.approx(
            RGGI_STATE_CO2_BUDGET["RGGI"]
        )


class TestNamedCarbonProgramPricePath:
    """``ScenarioConfig.carbon_program_price_path`` (P-1D wiring)."""

    def test_none_and_mid_are_byte_identical(self):
        default = resolve_carbon_program(
            ScenarioConfig(
                iso="CAISO", mode="forecast", carbon_program_price_path=None
            ),
            2030,
        )
        mid = resolve_carbon_program(
            ScenarioConfig(
                iso="CAISO", mode="forecast", carbon_program_price_path="mid"
            ),
            2030,
        )
        assert default.price_adder == mid.price_adder

    def test_low_below_mid_below_high(self):
        program = CAP_AND_TRADE_PROGRAMS["CAISO"]
        low = named_program_price(program, "CAISO", 2030, "low")
        mid = named_program_price(program, "CAISO", 2030, "mid")
        high = named_program_price(program, "CAISO", 2030, "high")
        assert low < mid < high

    def test_rggi_low_falls_back_to_mid_no_floor_series(self):
        program = CAP_AND_TRADE_PROGRAMS["NYISO"]
        low = named_program_price(program, "NYISO", 2030, "low")
        mid = named_program_price(program, "NYISO", 2030, "mid")
        assert low == mid

    def test_pjm_no_measured_anchor_returns_zero(self):
        program = CAP_AND_TRADE_PROGRAMS["PJM"]
        assert named_program_price(program, "PJM", 2030, "high") == 0.0
