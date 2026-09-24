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
        # NP15, ZP26, LA_BASIN, SDGE, SP15_rest in-state (1.0); WECC_import
        # external (0.0). Post-SP15-split topology (c28d57b1, 2026-07-09).
        np.testing.assert_array_equal(res.membership, [1.0, 1.0, 1.0, 1.0, 1.0, 0.0])

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
        # 0.0 from 2024 (VA exited 1 Jan 2024) — the year-aware zone_share.
        dominion_idx = 5
        res_2023 = resolve_carbon_program(
            ScenarioConfig(iso="PJM", mode="backcast"), 2023
        )
        res_2024 = resolve_carbon_program(
            ScenarioConfig(iso="PJM", mode="backcast"), 2024
        )
        assert res_2023.membership[dominion_idx] == pytest.approx(0.9881)
        assert res_2024.membership[dominion_idx] == 0.0

    def test_pjm_membership_rows_cover_every_keeper_year(self):
        # pjm-h22: NJ rejoined 2020; VA a member 2021-2023 only. The 2022 row
        # used to fall back to the 2025 set, un-enrolling VA in a member year.
        from market_sim.config.constants import (
            PJM_RGGI_ZONE_SHARE,
            RGGI_MEMBER_STATES_BY_YEAR,
        )

        assert "NJ" in RGGI_MEMBER_STATES_BY_YEAR[2020]
        assert "VA" not in RGGI_MEMBER_STATES_BY_YEAR[2020]
        assert "VA" in RGGI_MEMBER_STATES_BY_YEAR[2022]
        dominion_idx = 5
        for year, expected in [(2020, 0.0), (2021, 0.9893), (2022, 0.9894)]:
            res = resolve_carbon_program(
                ScenarioConfig(iso="PJM", mode="backcast"), year
            )
            assert res.membership[dominion_idx] == pytest.approx(expected)
        for zone, shares in PJM_RGGI_ZONE_SHARE.items():
            assert set(shares) == set(range(2020, 2026)), zone


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

    def test_explicit_rff_path_no_longer_suppresses_the_program_adder(self):
        # Owner ruling S2 (card D-1, 2026-09-06) — FLOOR, not replace. This
        # test previously asserted the opposite (``price_adder == 0.0``): an
        # explicit non-default carbon_price_path nulled the program adder, so a
        # named federal RFF path REPLACED the state program. That made
        # policy_bundle="tight" a carbon-price CUT of $16-$102/tCO2 on
        # CAISO/NYISO/NEISO in all 25 horizon years
        # (FINDING-scn-ws1a-2026-09-05.md §0.1). The resolver now answers ONE
        # question — what the program itself charges — in every mode, and the
        # composition with the path happens in policy.carbon (rule 19).
        res = resolve_carbon_program(
            ScenarioConfig(iso="CAISO", carbon_price_path="mid"), 2030
        )
        assert res.price_adder == pytest.approx(
            projected_price(CAP_AND_TRADE_PROGRAMS["CAISO"], "CAISO", 2030)
        )
        # ...and it is the SAME adder the default path resolves, i.e. the path
        # no longer reaches this function at all.
        assert res.price_adder == pytest.approx(
            resolve_carbon_program(ScenarioConfig(iso="CAISO"), 2030).price_adder
        )


class TestPjmGatedAllowance:
    """pjm-146 gated PJM RGGI adder (PREREG-pjm146-rggi-allowance §2)."""

    def test_default_off_keeps_pjm_adder_zero(self):
        # The incumbent no-op: PJM has a program but no price series, so the
        # adder is $0 under the default-True state_carbon_pricing flag.
        res = resolve_carbon_program(ScenarioConfig(iso="PJM", mode="backcast"), 2024)
        assert res is not None
        assert res.price_adder == 0.0

    @pytest.mark.parametrize(
        "year,expected",
        [
            (2020, 7.07),
            (2021, 10.44),
            (2022, 14.84),
            (2023, 14.87),
            (2024, 22.83),
            (2025, 24.35),
        ],
    )
    def test_gate_arms_metric_converted_series(self, year, expected):
        res = resolve_carbon_program(
            ScenarioConfig(iso="PJM", mode="backcast", pjm_rggi_allowance_pricing=True),
            year,
        )
        assert res.price_adder == pytest.approx(expected)

    def test_gate_off_series_year_outside_registry_stays_zero(self):
        # 2019 has no registered PJM price (pjm-h22 landed 2020-2022 only) —
        # the gated lookup must return 0, not invent an anchor (rule 13).
        res = resolve_carbon_program(
            ScenarioConfig(iso="PJM", mode="backcast", pjm_rggi_allowance_pricing=True),
            2019,
        )
        assert res.price_adder == 0.0

    def test_pjm_series_is_the_neiso_metric_series_and_recomputes_from_csv(self):
        # pjm-h22: the PJM registry is the same RGGI auction means as NEISO's
        # metric block, and each year re-derives from the committed auction CSV
        # (four quarterly clearing prices, simple mean rounded to the cent,
        # x 1.10231, rounded to the cent). Zero free parameters.
        import csv

        from market_sim.config import paths
        from market_sim.config.fuel_trajectories import (
            PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE,
            STATE_CARBON_PRICE_BY_ISO,
        )

        csv_path = (
            paths.RAW_DIR
            / "policy"
            / "carbon-auction-results"
            / "carbon-auction-results.csv"
        )
        by_year: dict[int, list[float]] = {}
        with open(csv_path, newline="") as fh:
            for row in csv.DictReader(fh):
                if row["program"] == "RGGI":
                    by_year.setdefault(int(row["year"]), []).append(
                        float(row["clearing_price"])
                    )
        for year, value in PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE.items():
            assert value == STATE_CARBON_PRICE_BY_ISO["NEISO"][year]
            prices = by_year[year]
            assert len(prices) == 4
            mean_short_ton = round(sum(prices) / 4, 2)
            assert round(mean_short_ton * 1.10231, 2) == pytest.approx(value)
        assert set(PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE) == set(range(2020, 2026))

    def test_gate_is_backcast_only(self):
        # Forecast years stay on projected_price, which has no PJM anchor
        # (mode B — measured backcast overlay; promotion unifies this later).
        res = resolve_carbon_program(
            ScenarioConfig(iso="PJM", pjm_rggi_allowance_pricing=True), 2030
        )
        assert res.price_adder == 0.0

    def test_gate_is_pjm_scoped_other_isos_unchanged(self):
        # The field is inert for a whole-ISO program: NYISO's measured path
        # resolves before the gate is consulted, byte-identically.
        on = resolve_carbon_program(
            ScenarioConfig(
                iso="NYISO", mode="backcast", pjm_rggi_allowance_pricing=True
            ),
            2024,
        )
        off = resolve_carbon_program(ScenarioConfig(iso="NYISO", mode="backcast"), 2024)
        assert on.price_adder == off.price_adder == pytest.approx(20.71)

    def test_default_cache_key_is_unmoved_by_the_field(self):
        # _CACHE_KEY_OPTIONAL_FIELDS registration: default-valued configs keep
        # the pinned key; an armed run gets a distinct key.
        base = ScenarioConfig()
        armed = ScenarioConfig(pjm_rggi_allowance_pricing=True)
        assert base.cache_key() != armed.cache_key()
        assert (
            ScenarioConfig(pjm_rggi_allowance_pricing=False).cache_key()
            == base.cache_key()
        )


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
        # Post-SP15-split 6-zone membership (c28d57b1, 2026-07-09).
        np.testing.assert_array_equal(
            res.cap_spec.membership, [1.0, 1.0, 1.0, 1.0, 1.0, 0.0]
        )

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
                ("PJM_EMAAC", 301),  # NJ — member
                ("PJM_EMAAC", 302),  # PA (Philly-metro slice) — non-member
                ("PJM_AEP_Ohio", 303),  # OH — non-member
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
        # ERCOT/MISO have no program at all — per_generator_membership is a
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
        from scripts.data import curate_carb_cap_schedule as carb

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
        from scripts.data import curate_rggi_co2_budgets as rggi

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


class TestCarbonMcColumn:
    """SCN-WS1a G-C3: the forecast orchestrator's ``assemble_mc`` carbon argument.

    ``carbon_mc_column`` is the backcast's partial-footprint gate lifted
    verbatim so ``runner.py`` and ``scripts/run_calibration.py`` agree. The
    load-bearing property is byte-identity on the scalar path: every ISO whose
    program membership is uniform (or absent) must hand ``assemble_mc`` the
    SAME scalar object it received before the seam existed.
    """

    @staticmethod
    def _fleet(zone_idx, plant_code):
        class _Fleet:
            pass

        f = _Fleet()
        f.zone_idx = np.asarray(zone_idx, dtype=int)
        f.plant_code = np.asarray(plant_code, dtype=int)
        f.n_gen = len(f.zone_idx)
        return f

    @pytest.mark.parametrize("iso", ["ERCOT", "CAISO", "MISO", "NYISO", "NEISO"])
    @pytest.mark.parametrize("mode", ["forecast", "backcast"])
    def test_uniform_membership_isos_return_the_identical_scalar(self, iso, mode):
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.policy.cap_and_trade import carbon_mc_column
        from market_sim.policy.carbon import resolve_carbon_price

        cfg = ScenarioConfig(iso=iso, mode=mode)
        year = 2024 if mode == "backcast" else 2030
        zones = get_iso_config(iso).zone_names
        price = resolve_carbon_price(cfg, year)
        # Force a nonzero scalar so the gate's first leg cannot short-circuit
        # for the program-less ISOs: the identity must hold on the value, not
        # on "carbon was zero anyway".
        if not price:
            price = 12.5
        fleet = self._fleet([0] * 3, [-1, -2, -3])
        out = carbon_mc_column(cfg, iso, year, price, fleet, zones)
        assert out is price

    def test_zero_price_short_circuits_before_any_lookup(self):
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.policy.cap_and_trade import carbon_mc_column

        cfg = ScenarioConfig(iso="PJM", mode="forecast")
        zones = get_iso_config("PJM").zone_names
        price = 0.0
        out = carbon_mc_column(cfg, "PJM", 2030, price, object(), zones)
        assert out is price

    def test_pjm_forecast_adder_is_zero_today_so_scalar_path(self):
        # G-C3 is INERT at HEAD: projected_price has no PJM anchor, so the
        # resolved forecast scalar is 0.0 and the column is never built.
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.policy.cap_and_trade import carbon_mc_column
        from market_sim.policy.carbon import resolve_carbon_price

        cfg = ScenarioConfig(iso="PJM", mode="forecast")
        price = resolve_carbon_price(cfg, 2030)
        assert price == 0.0
        zones = get_iso_config("PJM").zone_names
        assert carbon_mc_column(cfg, "PJM", 2030, price, object(), zones) is price

    def test_pjm_partial_footprint_builds_the_membership_column(self):
        # The one live path: PJM's gated RGGI adder (backcast) with a synthetic
        # fleet (plant_code <= 0 keeps the committed zone-share fallback).
        from market_sim.config.constants import PJM_RGGI_ZONE_SHARE
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.policy.cap_and_trade import carbon_mc_column
        from market_sim.policy.carbon import resolve_carbon_price

        cfg = ScenarioConfig(
            iso="PJM", mode="backcast", pjm_rggi_allowance_pricing=True
        )
        zones = list(get_iso_config("PJM").zone_names)
        year = 2024
        price = resolve_carbon_price(cfg, year)
        assert price == pytest.approx(22.83)
        z_emaac = zones.index("PJM_EMAAC")
        z_comed = zones.index("PJM_ComEd")
        fleet = self._fleet([z_emaac, z_comed], [-1, -2])
        out = carbon_mc_column(cfg, "PJM", year, price, fleet, zones, plant_state={})
        assert isinstance(out, np.ndarray)
        assert out.shape == (2,)
        assert out[0] == pytest.approx(PJM_RGGI_ZONE_SHARE["PJM_EMAAC"][year] * price)
        assert out[1] == pytest.approx(0.0)

    def test_scalar_path_assemble_mc_is_byte_identical(self):
        # The end-to-end statement of the byte-identity claim: for a uniform-
        # membership ISO, assemble_mc over the seam's output equals
        # assemble_mc over the scalar, bit for bit.
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.fleet import Generator, generators_to_fleet_arrays
        from market_sim.data.fleet.legacy_bins import assemble_mc
        from market_sim.policy.cap_and_trade import carbon_mc_column

        iso = "NEISO"
        zones = get_iso_config(iso).zone_names
        gens = [
            Generator(
                unit_id=f"g{i}",
                name=f"g{i}",
                zone=zones[0],
                fuel_type="gas_cc",
                pmax_mw=100.0,
                heat_rate=7.0 + i,
                vom=2.0,
                emission_rate_co2=0.4,
            )
            for i in range(3)
        ]
        fleet = generators_to_fleet_arrays(gens, zones, hours=24)
        fuel = np.full((3, 24), 3.0)
        cfg = ScenarioConfig(iso=iso, mode="forecast")
        price = 26.05
        col = carbon_mc_column(cfg, iso, 2026, price, fleet, zones)
        assert col is price
        a = assemble_mc(fleet, fuel, price, 0.0)
        b = assemble_mc(fleet, fuel, col, 0.0)
        assert a.tobytes() == b.tobytes()


class TestBorderSeamResolvesCarbon:
    """SCN-WS1a G-C2: ``spec.py``'s corridor border adder prices off the resolver."""

    def _spec(self, **overrides):
        from market_sim.model.interchange.spec import get_interchange_spec

        cfg = ScenarioConfig(
            iso="CAISO",
            mode="forecast",
            start_year=2026,
            end_year=2026,
            caiso_per_hub_intertie=True,
            **overrides,
        )
        return cfg, get_interchange_spec(cfg, "CAISO", year=2026)

    def test_corridor_adder_is_resolved_price_times_unspecified_ef(self):
        from market_sim.config.constants import CARB_UNSPECIFIED_IMPORT_EF
        from market_sim.policy.carbon import resolve_carbon_price

        cfg, spec = self._spec()
        assert cfg.carbon_price == 0.0  # the program-resolved posture
        price = resolve_carbon_price(cfg, 2026)
        assert price > 0.0
        assert spec.corridors, "per-hub posture must emit the corridor inventory"
        for corridor in spec.corridors:
            assert corridor.carbon_adder == pytest.approx(
                CARB_UNSPECIFIED_IMPORT_EF * price
            )

    def test_corridor_adder_moves_by_ef_times_delta(self):
        from market_sim.config.constants import CARB_UNSPECIFIED_IMPORT_EF

        _, base = self._spec()
        _, high = self._spec(carbon_price_delta=25.0)
        for b, h in zip(base.corridors, high.corridors):
            assert h.carbon_adder - b.carbon_adder == pytest.approx(
                CARB_UNSPECIFIED_IMPORT_EF * 25.0
            )

    def test_corridor_adder_matches_runner_border(self):
        # The inventory now agrees with the border the runner actually prices
        # the import fleet with (runner.py's build_interchange_fleet border).
        from market_sim.model.interchange.import_nodes import wecc_border_carbon_adder
        from market_sim.policy.carbon import resolve_carbon_price

        cfg, spec = self._spec()
        runner_border = wecc_border_carbon_adder(resolve_carbon_price(cfg, 2026))
        for corridor in spec.corridors:
            assert corridor.carbon_adder == pytest.approx(runner_border)


class TestFederalCarbonFloor:
    """Owner ruling S2 (card D-1, 2026-09-06): a named federal RFF path is a
    FLOOR under the state carbon program, never a replacement for it.

    ``effective = max(RFF path(year), program trajectory(year))`` on a program
    ISO, the path alone elsewhere; ``carbon_price`` (scalar) keeps its Q26
    replace semantics untouched. Executed by SCN-WS1c
    (``PRECOMMIT-scn-ws1c-2026-09-06.md``,
    ``FINDING-scn-ws1c-2026-09-06.md``); the defect it repairs is G-C1
    (``FINDING-scn-ws1a-2026-09-05.md`` §0.1, §6).

    **On the charter's "strict increase" wording.** The lane charter asked for
    a NEISO-tight *strict*-increase test over 2026-2050. Under the floor that
    assertion is FALSE and would rightly fail: the RFF mid path never exceeds a
    program trajectory in any year, so ``tight`` equals ``current`` on every
    program ISO and the increase is weak. The ruling moved the predicate before
    any code ran — S2 was recorded WITH that consequence — so these tests assert
    what the repaired semantics actually claim: ``tight >= current`` everywhere,
    with EQUALITY on CAISO/NYISO/NEISO and a STRICT increase on ERCOT/PJM/MISO
    where the path applies alone. Whether ``tight`` should mean something else
    on a program ISO is open card D-1(b) and is not asserted here either way.
    """

    HORIZON = list(range(2026, 2051))
    PROGRAM_ISOS = ("CAISO", "NYISO", "NEISO")
    PATH_ONLY_ISOS = ("ERCOT", "PJM", "MISO")

    @staticmethod
    def _resolved(iso: str, bundle: str, year: int) -> float:
        """The resolved $/tCO2 exactly as a solve sees it (bundle → ISO defaults)."""
        from market_sim.config.iso_configs import apply_iso_scenario_defaults
        from market_sim.config.scenario_resolvers import resolve_policy_bundle
        from market_sim.policy.carbon import resolve_carbon_price

        cfg = ScenarioConfig(iso=iso, mode="forecast", policy_bundle=bundle)
        cfg = apply_iso_scenario_defaults(resolve_policy_bundle(cfg), iso)
        return resolve_carbon_price(cfg, year)

    @pytest.mark.parametrize("iso", PROGRAM_ISOS + PATH_ONLY_ISOS)
    def test_tight_is_never_below_current_in_any_horizon_year(self, iso):
        # The monotonicity law of max, over the whole 25-year horizon and every
        # ISO: naming a federal path can no longer LOWER anyone's carbon price.
        # This is the assertion the charter's "strict increase" was reaching for
        # and the one the ruling actually supports.
        for year in self.HORIZON:
            assert self._resolved(iso, "tight", year) >= self._resolved(
                iso, "current", year
            ), f"{iso} {year}: tight fell below current"

    @pytest.mark.parametrize("iso", PROGRAM_ISOS)
    def test_tight_is_an_exact_no_op_on_a_program_iso(self, iso):
        # THE RULED CONSEQUENCE, pinned so it cannot drift silently: the RFF
        # mid path never exceeds a program trajectory, so on CAISO/NYISO/NEISO
        # the program is the binding instrument in every year and "tight"
        # resolves to exactly what "current" resolves to. This is the outcome
        # S2 was ruled with, not a defect to engineer around.
        for year in self.HORIZON:
            assert self._resolved(iso, "tight", year) == pytest.approx(
                self._resolved(iso, "current", year)
            ), f"{iso} {year}: tight is not the ruled no-op"

    @pytest.mark.parametrize("iso", PROGRAM_ISOS)
    def test_program_iso_tight_equals_the_program_trajectory_not_the_path(self, iso):
        # The floor's operand, named: it is the projected program price, and it
        # is strictly ABOVE the mid path it floors, in every horizon year.
        from market_sim.policy.carbon import rff_path_price

        program = CAP_AND_TRADE_PROGRAMS[iso]
        for year in self.HORIZON:
            resolved = self._resolved(iso, "tight", year)
            assert resolved == pytest.approx(projected_price(program, iso, year))
            assert resolved >= rff_path_price("mid", year)

    @pytest.mark.parametrize("iso", PATH_ONLY_ISOS)
    def test_path_only_iso_gets_a_strict_increase_from_2027(self, iso):
        # Where no program applies (ERCOT/MISO have none; PJM has one with no
        # price series) the path applies alone and "tight" IS a carbon-price
        # increase. 2026 is excluded because the RFF mid knot at 2026 is $0 —
        # both bundles are 0.00 there, which is the path's own shape, not the
        # floor's doing.
        from market_sim.policy.carbon import rff_path_price

        for year in self.HORIZON[1:]:
            resolved = self._resolved(iso, "tight", year)
            assert resolved > self._resolved(iso, "current", year)
            assert resolved == pytest.approx(rff_path_price("mid", year))

    @pytest.mark.parametrize("iso", PROGRAM_ISOS)
    def test_high_path_crosses_the_program_and_the_floor_takes_it(self, iso):
        # The floor is a max, not a "program always wins": where the federal
        # path DOES exceed the program trajectory the path binds. RFF high
        # crosses on the two RGGI ISOs mid-horizon and never on CAISO
        # (FINDING-scn-ws1a-2026-09-05.md §0.1), so this asserts the identity
        # rather than a hard-coded crossing window.
        from market_sim.policy.carbon import (
            resolved_base_trajectory_price,
            rff_path_price,
        )

        program = CAP_AND_TRADE_PROGRAMS[iso]
        crossings = 0
        for year in self.HORIZON:
            cfg = ScenarioConfig(iso=iso, mode="forecast", carbon_price_path="high")
            path, prog = (
                rff_path_price("high", year),
                projected_price(program, iso, year),
            )
            assert resolved_base_trajectory_price(cfg, year) == pytest.approx(
                max(path, prog)
            )
            crossings += path > prog
        if iso in ("NYISO", "NEISO"):
            assert crossings > 0, "RFF high is documented to cross on the RGGI ISOs"
        else:
            assert crossings == 0, "RFF high never crosses CARB's trajectory"

    def test_rollback_is_unchanged_by_the_floor(self):
        # rollback = zero path + state_carbon_pricing=False. Both operands of
        # the max are 0.0, so it stays a genuine no-carbon bundle: the floor
        # cannot resurrect a program the bundle switched off.
        for iso in self.PROGRAM_ISOS + self.PATH_ONLY_ISOS:
            for year in (2026, 2035, 2050):
                assert self._resolved(iso, "rollback", year) == 0.0

    def test_backcast_is_untouched_by_the_floor(self):
        # The changed branch is the `else` arm of `mode == "backcast"`. A
        # backcast resolves its MEASURED adder whatever the path says — the
        # keeper lane (every keeper carries path "zero") is identical either
        # way, and a non-zero path cannot reach into a backcast year.
        from market_sim.policy.carbon import resolve_carbon_price

        for iso in self.PROGRAM_ISOS:
            for year in (2023, 2024, 2025):
                measured = measured_price(iso, year)
                assert resolve_carbon_price(
                    ScenarioConfig(iso=iso, mode="backcast"), year
                ) == pytest.approx(measured)
                assert resolve_carbon_price(
                    ScenarioConfig(iso=iso, mode="backcast", carbon_price_path="mid"),
                    year,
                ) == pytest.approx(measured)

    def test_carbon_price_scalar_keeps_its_q26_replace_semantics(self):
        # Explicitly pinned because S2 changes the OTHER channel: a nonzero
        # carbon_price still REPLACES the resolved trajectory (precedence (1)),
        # including below it — that is Q26's ruling, guarded not changed.
        from market_sim.policy.carbon import resolve_carbon_price

        cfg = ScenarioConfig(iso="NEISO", mode="forecast", carbon_price=25.0)
        assert resolve_carbon_price(cfg, 2050) == 25.0  # not max(25, 132.16)

    def test_carbon_price_delta_still_rides_on_top_of_the_floor(self):
        # The D26 additive stage is applied AFTER the precedence chain, so it
        # is an increment on the floored base — unchanged, and still the
        # instrument for "more carbon everywhere" (the D-1(b) question the
        # floor deliberately does not answer).
        from market_sim.policy.carbon import resolve_carbon_price

        base = ScenarioConfig(iso="NEISO", mode="forecast", carbon_price_path="mid")
        armed = ScenarioConfig(
            iso="NEISO",
            mode="forecast",
            carbon_price_path="mid",
            carbon_price_delta=25.0,
        )
        for year in (2026, 2035, 2050):
            assert resolve_carbon_price(armed, year) == pytest.approx(
                resolve_carbon_price(base, year) + 25.0
            )

    def test_pjm_partial_footprint_seam_is_inert_so_d1c_stays_open(self):
        # Card D-1(c) — how a federal floor composes with PJM's PARTIAL RGGI
        # footprint — is open and is NOT answered by this repair. The only
        # per-generator membership seam (carbon_mc_column) reads the program
        # adder, and PJM's forecast adder is 0.0 (no PJM series in
        # STATE_CARBON_PRICE_BY_ISO), before and after. So the seam returns the
        # scalar, the IDENTICAL object, exactly as it did pre-floor.
        from market_sim.policy.cap_and_trade import carbon_mc_column

        cfg = ScenarioConfig(iso="PJM", mode="forecast", carbon_price_path="mid")
        assert resolve_carbon_program(cfg, 2030).price_adder == 0.0
        price = 15.0
        assert carbon_mc_column(cfg, "PJM", 2030, price, object(), ["A", "B"]) is price
