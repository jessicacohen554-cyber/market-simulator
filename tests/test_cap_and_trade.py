"""Tests for the unified carbon-program resolver (policy/cap_and_trade.py)."""

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.policy.cap_and_trade import (
    CarbonProgramResolution,
    MassCapSpec,
    measured_price,
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

    def test_pjm_ships_off_all_zero_membership(self):
        # PJM_RGGI_ZONE_SHARE empty until the EIA-860→state crosswalk lands, so
        # the fractional adder is a no-op (plan §5, §11).
        res = resolve_carbon_program(ScenarioConfig(iso="PJM", mode="backcast"), 2024)
        assert res is not None
        np.testing.assert_array_equal(res.membership, np.zeros(res.membership.size))
        assert res.price_adder == 0.0


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

    def test_mass_cap_enabled_without_budget_falls_to_adder(self):
        # Row stays inert until a budget is supplied (schedules not yet landed).
        res = resolve_carbon_program(
            ScenarioConfig(iso="CAISO", mode="backcast", mass_cap_enabled=True), 2024
        )
        assert res.cap_spec is None
        assert res.price_adder == pytest.approx(35.23)


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
