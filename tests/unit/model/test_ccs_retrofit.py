"""Tests for the CCS retrofit pathway and configurable heat-rate binning.

Covers :func:`market_sim.model.capacity.apply_ccs_retrofit` (the W2-C
margin-based screen: attainable inframarginal margin at the post-retrofit
cost basis, §45Q with its statutory credit window, the federal-CES premium
as a bid offset, and incremental-over-unabated valuation), the joint
retrofit-or-retire ordering inside :func:`evolve_fleet` (retrofit screen
before economic retirements, cap displacement falling back to the loss
counter), the §45Q window levelization in the new-build CCS LCOE, and the
configurable-bin-count aggregation in
:func:`market_sim.data.fleet.aggregate_fleet_by_efficiency`.

Trivial-scale fixtures throughout (repo testing pattern): one zone, 24
hourly prices — the screen annualizes short series by ``8760 / T``.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    Generator,
    aggregate_fleet_by_efficiency,
    assemble_mc,
    generators_to_fleet_arrays,
)
from market_sim.model.capacity import (
    CumulativeDeployment,
    _adjust_retrofit_capex,
    _capital_recovery_factor,
    _ccs_45q_window_years,
    _ccs_retrofit_payback_years,
    _emerging_lcoe,
    apply_ccs_retrofit,
    compute_lcoe,
    evolve_fleet,
)
from market_sim.policy.ira import CCUS_45Q_CREDIT_PER_TON

# 24-hour trivial price fixtures (annualized inside the screen by 8760/24).
T = 24
HIGH_PRICES = np.full((1, T), 60.0)  # deep in merit for a gas CC
LOW_PRICES = np.full((1, T), 5.0)  # below every state's effective cost
DISTRESS_PRICES = np.full((1, T), 33.0)  # thin unabated margin, far below FOM
# 12 h at $60 / 12 h at $5: enough in-window margin to be worth doing under
# an indefinite 45Q but NOT enough to pay back inside the 12-year statutory
# window (the post-window uplift is negative) — the window discriminator.
SPLIT_PRICES = np.concatenate(
    [np.full((1, T // 2), 60.0), np.full((1, T // 2), 5.0)], axis=1
)


def _gas_cc(
    unit_id,
    heat_rate=6.9,
    emission_rate=0.37,
    pmax=500.0,
    zone="Z0",
    online_year=2015,
    vom=2.0,
):
    """Build a gas CC :class:`Generator` for retrofit screening."""
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone=zone,
        fuel_type="gas_cc",
        pmax_mw=pmax,
        heat_rate=heat_rate,
        emission_rate_co2=emission_rate,
        vom=vom,
        online_year=online_year,
    )


# FIXTURE COST PIN (capx D41, 2026-09-02) — the same remedy G-32 applied to the
# five ``test_capacity.py`` margin tests when it flipped the FOM defaults:
# **a behavioural identification test must not silently ride a default it does
# not intend to exercise.** Every crafted margin in this file (the 24-hour $60 /
# $33 / split price fixtures) was sized against the pre-repair retrofit cost
# basis, so once ``fixed_om_gas_cc_ccs`` and ``ccs_retrofit_capex_kw`` were
# re-identified onto the NREL ATB 2024 (2026$) basis — 25.0 -> 65.0 $/kW-yr and
# 900.0 -> 1521.4 $/kW, repairing a screen ΔFOM that was a *saving* and a capex
# 59 % of the increment the model's own new-build CCS charges — the fixtures
# stopped placing their units near the bar and seven mechanism assertions went
# red without any mechanism changing.
#
# The pin restores the fixtures' INTENT, not the old defect: the ΔFOM keeps the
# repaired POSITIVE sign (the capture island is charged, at the shipped
# ``fixed_om_gas_cc_ccs``), and only the fixture's capex is lowered, to place
# these synthetic 24-hour margins back in the window where the mechanism under
# test is discriminating. That is what these tests are for — the screen's
# ordering, its cap displacement, its §45Q window gate and its
# beats-staying-unabated gate — never the cost LEVEL, which is asserted against
# its source in ``tests/unit/config/test_ccs_retrofit_fixed_cost_basis.py`` and
# measured for consequence in
# ``docs/handoffs/FINDING-capx-d41-ccs-fixedcost-2026-09-02.md``.
_FIXTURE_RETROFIT_CAPEX_KW = 300.0


def _fixture_config(**overrides):
    """``ScenarioConfig`` for the ERCOT screen fixtures, with the capex pin."""
    overrides.setdefault("ccs_retrofit_capex_kw", _FIXTURE_RETROFIT_CAPEX_KW)
    return ScenarioConfig(iso="ERCOT", **overrides)


def _screen(
    fleet,
    prices,
    year=2030,
    config=None,
    gas_price=4.0,
    carbon_price=0.0,
    zone_names=None,
    cumulative=None,
):
    """Run the retrofit screen with the fixture defaults."""
    config = config or _fixture_config()
    return apply_ccs_retrofit(
        fleet,
        prices,
        year,
        config,
        "ERCOT",
        gas_price_per_mmbtu=gas_price,
        carbon_price=carbon_price,
        zone_names=zone_names,
        cumulative=cumulative,
    )


def _uniform_gas_cc_fleet(n=100, hr_lo=6.0, hr_hi=8.5, zone="Z0"):
    """Build ``n`` gas CC units with heat rates uniformly spanning a range."""
    fleet = []
    for i, hr in enumerate(np.linspace(hr_lo, hr_hi, n)):
        if hr < 6.5:
            ebin = "h_class"
        elif hr < 7.2:
            ebin = "f_class"
        else:
            ebin = "older"
        fleet.append(
            Generator(
                unit_id=f"G{i}",
                name=f"G{i}",
                zone=zone,
                fuel_type="gas_cc",
                efficiency_bin=ebin,
                pmax_mw=100.0,
                heat_rate=float(hr),
                emission_rate_co2=0.40,
                vom=2.0,
            )
        )
    return fleet


class TestWindowedPaybackArithmetic(unittest.TestCase):
    """§45Q window arithmetic: the two-segment payback helper (plan §11 Q2)."""

    def test_recovery_inside_window_is_classic_payback(self):
        # capex 100, in-window uplift 10, window 12 -> 100 <= 120 recovered
        # inside the window at the classic capex/uplift rate.
        self.assertAlmostEqual(
            _ccs_retrofit_payback_years(100.0, 10.0, 10.0, 12.0), 10.0
        )

    def test_spillover_recovers_at_post_window_rate(self):
        # capex 100, window 8 x uplift 10 = 80 recovered in-window; the
        # remaining 20 recovers at the post-window uplift 5 -> 8 + 4 = 12.
        self.assertAlmostEqual(_ccs_retrofit_payback_years(100.0, 10.0, 5.0, 8.0), 12.0)

    def test_nonpositive_in_window_uplift_never_pays_back(self):
        self.assertEqual(
            _ccs_retrofit_payback_years(100.0, 0.0, 5.0, 12.0), float("inf")
        )
        self.assertEqual(
            _ccs_retrofit_payback_years(100.0, -3.0, 5.0, 12.0), float("inf")
        )

    def test_spillover_with_nonpositive_post_uplift_never_pays_back(self):
        # The credit expires before recovery and the post-window uplift
        # cannot finish the job.
        self.assertEqual(
            _ccs_retrofit_payback_years(100.0, 10.0, 0.0, 8.0), float("inf")
        )
        self.assertEqual(
            _ccs_retrofit_payback_years(100.0, 10.0, -5.0, 8.0), float("inf")
        )

    def test_window_years_statutory_none_and_clipping(self):
        cfg_12 = ScenarioConfig()
        cfg_none = ScenarioConfig(ira_45q_credit_window_years=None)
        # Statutory default 12, clipped to the asset horizon when shorter.
        self.assertEqual(_ccs_45q_window_years(cfg_12, 25.0), 12.0)
        self.assertEqual(_ccs_45q_window_years(cfg_12, 8.0), 8.0)
        # None => indefinite: the credit runs the full horizon.
        self.assertEqual(_ccs_45q_window_years(cfg_none, 25.0), 25.0)

    def test_window_guard_rejects_nonpositive(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(ira_45q_credit_window_years=0)


class TestScreenRequiresPriceSignal(unittest.TestCase):
    """The margin-based screen skips without a prior-year price signal."""

    def test_no_prices_no_screen(self):
        fleet, log = _screen([_gas_cc("G0")], None)
        self.assertEqual(log, [])
        self.assertEqual(fleet[0].fuel_type, "gas_cc")

    def test_prices_below_cost_no_retrofit(self):
        # Endogenous utilization: prices below both states' effective costs
        # leave no margin in either continuation, so nothing pays back the
        # capex — no fixed screen CF invents utilization that isn't there.
        fleet, log = _screen([_gas_cc("G0")], LOW_PRICES)
        self.assertEqual(log, [])
        self.assertEqual(fleet[0].fuel_type, "gas_cc")


class TestBau45QRetrofit(unittest.TestCase):
    """§45Q alone can now clear a BAU retrofit — the W2-C point."""

    def test_45q_only_retrofit_fires_at_high_utilization(self):
        # Zero carbon price, zero EAC, no federal premium: the statutory
        # $85/t on ~0.33 t/MWh captured (~$28/MWh for 12 years) pays back
        # the $900/kW retrofit at deep-in-merit prices.
        fleet, log = _screen([_gas_cc("G0")], HIGH_PRICES)
        self.assertEqual(len(log), 1)
        self.assertEqual(fleet[0].fuel_type, "gas_cc_ccs")
        entry = log[0]
        self.assertGreater(entry["q45_usd_per_mwh"], 20.0)
        self.assertEqual(entry["window_years"], 12.0)
        self.assertLess(entry["payback_years"], 12.0)
        # Endogenous utilization: the in-window margin (45Q as a bid offset)
        # is deeper than the post-window margin.
        self.assertGreater(
            entry["margin_window_per_mw_yr"], entry["margin_post_window_per_mw_yr"]
        )
        self.assertGreater(
            entry["margin_window_per_mw_yr"], entry["margin_unabated_per_mw_yr"]
        )

    def test_expiry_year_gating_at_commit(self):
        # 2033 > ira_ccus_45q_last_year (2032): no 45Q for a project
        # committed past the deadline, and without it the retrofit fails.
        fleet, log = _screen([_gas_cc("G0")], HIGH_PRICES, year=2033)
        self.assertEqual(log, [])
        self.assertEqual(fleet[0].fuel_type, "gas_cc")
        # Extending the deadline restores the credit and the retrofit.
        cfg = _fixture_config(ira_ccus_45q_last_year=2040)
        fleet2, log2 = _screen([_gas_cc("G1")], HIGH_PRICES, year=2033, config=cfg)
        self.assertEqual(len(log2), 1)
        self.assertEqual(fleet2[0].fuel_type, "gas_cc_ccs")


class Test45QWindowInScreen(unittest.TestCase):
    """The credit window binds the payback: 12-year vs indefinite (None)."""

    def test_window_12_blocks_what_indefinite_allows(self):
        # SPLIT_PRICES: uplift is ~55k $/MW-yr while 45Q pays but NEGATIVE
        # after the window (the HR penalty + VOM adder + transport exceed the
        # 12h/day in-merit margin without the credit). Under the statutory
        # 12-year window the capex cannot be recovered before the credit
        # dies -> no retrofit; under the indefinite extension (None) the
        # credit runs the full remaining life and the payback (~20 yr at the
        # capx-D41 fixture capex pin; ~16 yr before it) clears the 25-year
        # remaining life.
        fleet, log = _screen([_gas_cc("G0")], SPLIT_PRICES)
        self.assertEqual(log, [])
        self.assertEqual(fleet[0].fuel_type, "gas_cc")

        cfg_none = _fixture_config(ira_45q_credit_window_years=None)
        fleet2, log2 = _screen([_gas_cc("G1")], SPLIT_PRICES, config=cfg_none)
        self.assertEqual(len(log2), 1)
        self.assertEqual(fleet2[0].fuel_type, "gas_cc_ccs")
        entry = log2[0]
        # Indefinite window = the unit's whole remaining life (2030 online
        # 2015, 40-year book life -> 25 years).
        self.assertEqual(entry["window_years"], 25.0)
        self.assertGreater(entry["payback_years"], 12.0)
        self.assertLess(entry["payback_years"], 25.0)
        # And the payback is the classic single-segment ratio, since the
        # credit never expires within the horizon.
        self.assertAlmostEqual(
            entry["payback_years"],
            _FIXTURE_RETROFIT_CAPEX_KW * 1000.0 / entry["annual_net_savings_per_mw"],
            places=6,
        )

    def test_carbon_price_rescues_the_windowed_case(self):
        # Same split prices, statutory window: a $100/t carbon price makes
        # the post-retrofit state's avoided carbon valuable enough that the
        # payback completes inside the window — the carbon-crossover
        # behavior of the old screen, preserved on the new margin basis.
        fleet, log = _screen([_gas_cc("G0")], SPLIT_PRICES, carbon_price=100.0)
        self.assertEqual(len(log), 1)
        self.assertEqual(fleet[0].fuel_type, "gas_cc_ccs")


class TestPremiumTermAndStacking(unittest.TestCase):
    """Premium = max(legacy EAC, premium x capture credit); 45Q stacks."""

    def _log_entry(self, config):
        _, log = _screen([_gas_cc("G0")], HIGH_PRICES, config=config)
        self.assertEqual(len(log), 1)
        return log[0]

    def test_legacy_eac_wins_when_higher(self):
        cfg = ScenarioConfig(
            iso="ERCOT",
            eac_price_gas_cc_ccs=20.0,
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=10.0,  # x0.95 = 9.5 < 20
        )
        entry = self._log_entry(cfg)
        self.assertAlmostEqual(entry["attr_post_usd_per_mwh"], 20.0)
        # 45Q is a separate statutory instrument stacking on top of the
        # certificate: both appear in the same in-window margin.
        self.assertGreater(entry["q45_usd_per_mwh"], 0.0)

    def test_premium_times_capture_fraction_wins_when_higher(self):
        cfg = ScenarioConfig(
            iso="ERCOT",
            eac_price_gas_cc_ccs=20.0,
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=40.0,  # x0.95 = 38 > 20
        )
        entry = self._log_entry(cfg)
        self.assertAlmostEqual(entry["attr_post_usd_per_mwh"], 38.0)


class TestIncrementalNotGross(unittest.TestCase):
    """Uplift nets the unabated state's own credit (cesa_ci) — never gross."""

    def _uplift(self, crediting):
        cfg = ScenarioConfig(
            iso="ERCOT",
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=30.0,
            federal_ces_crediting=crediting,
        )
        _, log = _screen([_gas_cc("G0")], HIGH_PRICES, config=cfg)
        self.assertEqual(len(log), 1)
        return log[0]

    def test_clean_capture_unabated_credit_is_zero(self):
        entry = self._uplift("clean_capture")
        self.assertAlmostEqual(entry["attr_unabated_usd_per_mwh"], 0.0)
        self.assertAlmostEqual(entry["attr_post_usd_per_mwh"], 30.0 * 0.95)

    def test_cesa_ci_nets_unabated_partial_credit(self):
        # An efficient CCGT (0.37 t/MWh <= the 0.45 line) already earns a
        # partial credit unabated: 30 x (1 - 0.37/0.82) ~= 16.46 $/MWh. The
        # retrofit uplift must be valued NET of it.
        entry = self._uplift("cesa_ci")
        self.assertAlmostEqual(
            entry["attr_unabated_usd_per_mwh"], 30.0 * (1.0 - 0.37 / 0.82), places=6
        )
        self.assertAlmostEqual(
            entry["attr_post_usd_per_mwh"],
            30.0 * (1.0 - 0.37 * 0.1 / 0.82),
            places=6,
        )
        gross = self._uplift("clean_capture")
        # Same premium, same unit: the cesa_ci incremental uplift is smaller
        # than clean_capture's because the unabated continuation already
        # collects its partial certificate.
        self.assertLess(
            entry["annual_net_savings_per_mw"], gross["annual_net_savings_per_mw"]
        )


class TestRetrofitHeatRatePenalty(unittest.TestCase):
    """The heat-rate penalty is percentage-based, per unit."""

    def test_penalty_applied_to_individual_heat_rates(self):
        h_class = _gas_cc("H", heat_rate=6.3, emission_rate=0.36)
        older = _gas_cc("O", heat_rate=7.5, emission_rate=0.43)
        fleet, log = _screen([h_class, older], HIGH_PRICES, carbon_price=120.0)
        self.assertEqual(len(log), 2)
        # Each unit keeps its individual penalized heat rate (x1.12).
        self.assertAlmostEqual(h_class.heat_rate, 6.3 * 1.12, places=6)
        self.assertAlmostEqual(older.heat_rate, 7.5 * 1.12, places=6)
        self.assertEqual(h_class.fuel_type, "gas_cc_ccs")
        self.assertEqual(older.fuel_type, "gas_cc_ccs")


class TestRetrofitEfficientFirst(unittest.TestCase):
    """With a binding cap, shortest-payback (efficient) units retrofit first."""

    def test_shortest_payback_units_chosen(self):
        # Cap of 1.0 GW/yr admits only 2 of the 3 x 500 MW units.
        config = _fixture_config(ccs_retrofit_max_gw_per_year=1.0)
        g_eff = _gas_cc("EFF", heat_rate=6.3, emission_rate=0.40)
        g_mid = _gas_cc("MID", heat_rate=6.9, emission_rate=0.40)
        g_old = _gas_cc("OLD", heat_rate=7.5, emission_rate=0.40)
        _, log = _screen(
            [g_old, g_mid, g_eff], HIGH_PRICES, config=config, carbon_price=120.0
        )
        retrofitted = {entry["unit_id"] for entry in log}
        self.assertEqual(retrofitted, {"EFF", "MID"})
        self.assertEqual(g_eff.fuel_type, "gas_cc_ccs")
        self.assertEqual(g_mid.fuel_type, "gas_cc_ccs")
        self.assertEqual(g_old.fuel_type, "gas_cc")


class TestRetrofitMinRemainingLife(unittest.TestCase):
    """Units near end of life are skipped."""

    def test_old_unit_skipped_young_unit_eligible(self):
        # available_year lowered so the 2025 screen year passes the gate.
        config = _fixture_config(ccs_retrofit_available_year=2020)
        near_eol = _gas_cc("OLD", online_year=1990)
        young = _gas_cc("YOUNG", online_year=2005)
        _, log = _screen(
            [near_eol, young],
            HIGH_PRICES,
            year=2025,
            config=config,
            carbon_price=150.0,
        )
        retrofitted = {entry["unit_id"] for entry in log}
        self.assertEqual(retrofitted, {"YOUNG"})
        self.assertEqual(near_eol.fuel_type, "gas_cc")
        self.assertEqual(young.fuel_type, "gas_cc_ccs")


class TestZoneMapping(unittest.TestCase):
    """Multi-zone price signals resolve through zone_names; unknowns skip."""

    def test_unit_priced_at_its_own_zone(self):
        # Zone A prices are below cost, zone B deep in merit: the unit in B
        # retrofits on B's row, and an unmappable zone is skipped (never
        # silently priced at the wrong bus).
        prices = np.concatenate([LOW_PRICES, HIGH_PRICES], axis=0)
        in_b = _gas_cc("B0", zone="B")
        unmapped = _gas_cc("X0", zone="C")
        _, log = _screen(
            [in_b, unmapped], prices, zone_names=["A", "B"], carbon_price=100.0
        )
        self.assertEqual({e["unit_id"] for e in log}, {"B0"})
        self.assertEqual(in_b.fuel_type, "gas_cc_ccs")
        self.assertEqual(unmapped.fuel_type, "gas_cc")


class TestRetrofitFlowsIntoLP(unittest.TestCase):
    """Retrofitted capacity converts correctly into FleetArrays."""

    def test_retrofit_attributes_and_marginal_cost(self):
        gen = _gas_cc("G0")
        fleet, log = _screen([gen], HIGH_PRICES, carbon_price=100.0)
        self.assertEqual(len(log), 1)

        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=1)
        self.assertEqual(arrays.fuel_type_idx[0], FUEL_TYPE_MAP["gas_cc_ccs"])
        self.assertAlmostEqual(arrays.heat_rate[0], 6.9 * 1.12, places=6)
        self.assertAlmostEqual(arrays.emission_rate[0], 0.37 * 0.10, places=6)
        self.assertAlmostEqual(arrays.vom[0], 2.0 + 8.0, places=6)
        self.assertAlmostEqual(arrays.pmax[0], 500.0, places=6)

        # The marginal cost reflects the penalized heat rate, the VOM adder
        # and the reduced (post-capture) emission rate.
        mc = assemble_mc(arrays, np.array([[4.0]]), 100.0, 0.0)
        expected = 6.9 * 1.12 * 4.0 + 10.0 + 0.037 * 100.0
        self.assertAlmostEqual(mc[0, 0], expected, places=3)


class TestJointRetrofitOrRetire(unittest.TestCase):
    """The joint three-way choice inside evolve_fleet (plan §11 final block)."""

    def _prior(self, fleet, prices):
        """Bare-dict prior with the arrays the retirement screen needs."""
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=T)
        from types import SimpleNamespace

        return {
            "fleet_arrays": arrays,
            "dispatch_result": SimpleNamespace(dispatch=np.zeros((len(fleet), T))),
            "prices": prices,
            "mc_cost": np.full((len(fleet), T), 29.6),  # 6.9x4 + 2 vom
            "peak_demand": 0.0,
            "zone_names": ["Z0"],
        }

    def _evolve(self, fleet, tracker, config=None, prices=DISTRESS_PRICES):
        config = config or _fixture_config()
        return evolve_fleet(
            fleet,
            self._prior(fleet, prices),
            2030,
            config,
            tracker,
            gas_price_per_mmbtu=4.0,
            carbon_price=0.0,
        )

    def test_distressed_ccgt_retrofits_instead_of_retiring(self):
        # D0 enters its third consecutive loss year (gas_cc threshold 3):
        # without the joint choice it exits this year. Its retrofit
        # continuation clears (45Q at distress prices still pays back in
        # ~8.6 yr), so it converts BEFORE the retirement screen runs.
        d0 = _gas_cc("D0", pmax=100.0)
        fleet, tracker, _, retrofit_log, _ = self._evolve([d0], {"D0": 2})
        self.assertEqual({e["unit_id"] for e in retrofit_log}, {"D0"})
        self.assertAlmostEqual(
            sum(g.pmax_mw for g in fleet if g.fuel_type == "gas_cc_ccs"), 100.0
        )
        # The retrofit is this year's capital decision: the unabated loss
        # history is cleared and the unit is exempt from this year's screen.
        self.assertNotIn("D0", tracker)

    def test_distressed_ccgt_retires_when_retrofit_not_viable(self):
        # Same distressed unit, but 45Q unavailable (deadline in the past):
        # without the credit the post-retrofit margin cannot pay back, so
        # BOTH continuations fail and the unit exits on its loss counter.
        cfg = _fixture_config(ira_ccus_45q_last_year=2000)
        d0 = _gas_cc("D0", pmax=100.0)
        fleet, tracker, _, retrofit_log, _ = self._evolve([d0], {"D0": 2}, config=cfg)
        self.assertEqual(retrofit_log, [])
        self.assertEqual(
            sum(g.pmax_mw for g in fleet if g.fuel_type in ("gas_cc", "gas_cc_ccs")),
            0.0,
        )
        self.assertNotIn("D0", tracker)

    def test_cap_displaced_unit_falls_back_to_loss_counter(self):
        # Both distressed units have viable retrofits; the 0.5 GW cap admits
        # only the shorter-payback EFF. OLD is cap-displaced: it falls back
        # to the unabated path and its normal loss counter — entering year 3
        # of losses, it retires. (It may equally retire in a LATER year if
        # unabated keeps failing and the cap keeps binding.)
        eff = _gas_cc("EFF", heat_rate=6.5)
        old = _gas_cc("OLD", heat_rate=7.4)
        cfg = _fixture_config(ccs_retrofit_max_gw_per_year=0.5)
        fleet, tracker, _, retrofit_log, _ = self._evolve(
            [eff, old], {"EFF": 2, "OLD": 2}, config=cfg
        )
        self.assertEqual({e["unit_id"] for e in retrofit_log}, {"EFF"})
        self.assertAlmostEqual(
            sum(g.pmax_mw for g in fleet if g.fuel_type == "gas_cc_ccs"), 500.0
        )
        # OLD retired on the normal counter; EFF's counter was cleared by
        # the retrofit.
        self.assertEqual(sum(g.pmax_mw for g in fleet if g.fuel_type == "gas_cc"), 0.0)
        self.assertNotIn("OLD", tracker)
        self.assertNotIn("EFF", tracker)

    def test_cap_displaced_unit_survives_below_threshold(self):
        # Cap-displaced with only one prior loss year: the counter
        # increments (2 of 3) but the unit does NOT retire this year — the
        # loss-year semantics are preserved, not short-circuited.
        # retirement_rule="legacy" pinned (D-1 flipped the default to "pipeline"
        # 2026-08-02): the loss-year counter asserted below is a LEGACY-rule
        # construct the R-NEW pipeline does not keep.
        eff = _gas_cc("EFF", heat_rate=6.5)
        old = _gas_cc("OLD", heat_rate=7.4)
        cfg = _fixture_config(
            ccs_retrofit_max_gw_per_year=0.5, retirement_rule="legacy"
        )
        fleet, tracker, _, retrofit_log, _ = self._evolve(
            [eff, old], {"EFF": 2, "OLD": 1}, config=cfg
        )
        self.assertEqual({e["unit_id"] for e in retrofit_log}, {"EFF"})
        self.assertAlmostEqual(
            sum(g.pmax_mw for g in fleet if g.fuel_type == "gas_cc"), 500.0
        )
        self.assertEqual(tracker.get("OLD"), 2)

    def test_healthy_unit_retrofits_early_when_profitable(self):
        # No distress anywhere (zero loss years, deep-in-merit prices): the
        # retrofit still fires because it is more profitable than staying
        # unabated — "they may go retrofit sooner" (plan §11).
        h0 = _gas_cc("H0", pmax=100.0)
        fleet, tracker, _, retrofit_log, _ = self._evolve([h0], {}, prices=HIGH_PRICES)
        self.assertEqual({e["unit_id"] for e in retrofit_log}, {"H0"})
        self.assertAlmostEqual(
            sum(g.pmax_mw for g in fleet if g.fuel_type == "gas_cc_ccs"), 100.0
        )
        self.assertNotIn("H0", tracker)


class TestRetrofitsAddToCumulative(unittest.TestCase):
    """Retrofits expand the global CCS experience base."""

    def test_retrofits_increment_cumulative_tracker(self):
        config = _fixture_config()
        cumulative = CumulativeDeployment.initial()
        before = cumulative.get("gas_cc_ccs")

        # Four 500 MW gas CC units => 2.0 GW retrofitted.
        fleet = [_gas_cc(f"G{i}", online_year=2020) for i in range(4)]
        prior = {"prices": HIGH_PRICES, "zone_names": ["Z0"]}
        fleet, _tracker, _additions, retrofit_log, _ = evolve_fleet(
            fleet,
            prior,
            2030,
            config,
            {},
            carbon_price=100.0,
            gas_price_per_mmbtu=4.0,
            cumulative=cumulative,
        )
        self.assertEqual(len(retrofit_log), 4)
        after = cumulative.get("gas_cc_ccs")
        self.assertAlmostEqual(after - before, 2.0, places=6)

        # The updated cumulative lowers next year's new-build CCS LCOE.
        lcoe_before = compute_lcoe("gas_cc_ccs", 2031, config, cumulative_gw=before)
        lcoe_after = compute_lcoe("gas_cc_ccs", 2031, config, cumulative_gw=after)
        self.assertLess(lcoe_after, lcoe_before)


class TestNewBuildLcoe45QWindow(unittest.TestCase):
    """The same §45Q window governs the new-build CCS LCOE (plan §11 Q2)."""

    def _lcoe(self, config, year=2030):
        return _emerging_lcoe(
            "gas_cc_ccs",
            year,
            config,
            "ERCOT",
            cf=0.55,
            gas_price_per_mmbtu=4.0,
            carbon_price=0.0,
        )

    def test_windowed_credit_raises_lcoe_vs_indefinite(self):
        cfg_12 = ScenarioConfig()
        cfg_none = ScenarioConfig(ira_45q_credit_window_years=None)
        lcoe_12 = self._lcoe(cfg_12)
        lcoe_none = self._lcoe(cfg_none)
        # Crediting 12 statutory years over a 30-year life is worth less
        # than crediting all 30 — the windowed LCOE is strictly higher.
        self.assertGreater(lcoe_12, lcoe_none)

    def test_levelization_is_the_annuity_ratio(self):
        # lcoe(12) - lcoe(None) == q45_full x (1 - CRF(30)/CRF(12)) — the
        # PV-consistent levelization at the screen's own discount rate.
        from market_sim.config.constants import CCUS_PARAMS, CO2_RATES

        cfg_12 = ScenarioConfig()
        cfg_none = ScenarioConfig(ira_45q_credit_window_years=None)
        captured = min(CO2_RATES["gas_cc"].values()) * cfg_12.ccs_capture_rate
        q45_full = CCUS_45Q_CREDIT_PER_TON * captured
        life = CCUS_PARAMS["gas_cc_ccs_90"]["lifetime_yr"]
        rate = cfg_12.real_discount_rate
        ratio = _capital_recovery_factor(rate, life) / _capital_recovery_factor(
            rate, 12.0
        )
        self.assertAlmostEqual(
            self._lcoe(cfg_12) - self._lcoe(cfg_none),
            q45_full * (1.0 - ratio),
            places=6,
        )

    def test_window_longer_than_life_equals_indefinite(self):
        cfg_long = ScenarioConfig(ira_45q_credit_window_years=60)
        cfg_none = ScenarioConfig(ira_45q_credit_window_years=None)
        self.assertAlmostEqual(self._lcoe(cfg_long), self._lcoe(cfg_none), places=9)

    def test_expired_credit_makes_window_moot(self):
        # Committed past the eligibility deadline: no credit either way.
        cfg_12 = ScenarioConfig()
        cfg_none = ScenarioConfig(ira_45q_credit_window_years=None)
        self.assertAlmostEqual(
            self._lcoe(cfg_12, year=2033), self._lcoe(cfg_none, year=2033), places=9
        )
        self.assertGreater(self._lcoe(cfg_12, year=2033), self._lcoe(cfg_12, 2030))


class TestConfigurableBinCount(unittest.TestCase):
    """Configurable heat-rate bin count."""

    def test_three_bins(self):
        result = aggregate_fleet_by_efficiency(
            _uniform_gas_cc_fleet(), "gas_cc", n_bins=3
        )
        self.assertEqual(len(result), 3)

    def test_ten_bins_preserve_capacity(self):
        fleet = _uniform_gas_cc_fleet()
        result = aggregate_fleet_by_efficiency(fleet, "gas_cc", n_bins=10)
        self.assertEqual(len(result), 10)
        self.assertAlmostEqual(
            sum(g.pmax_mw for g in result),
            sum(g.pmax_mw for g in fleet),
            places=3,
        )
        # Each bin's heat rate is a capacity-weighted average within range.
        for rep in result:
            self.assertGreaterEqual(rep.heat_rate, 6.0)
            self.assertLessEqual(rep.heat_rate, 8.5)
        heat_rates = [g.heat_rate for g in result]
        self.assertEqual(heat_rates, sorted(heat_rates))

    def test_ten_bins_heat_rate_is_weighted_average(self):
        fleet = _uniform_gas_cc_fleet()
        result = aggregate_fleet_by_efficiency(fleet, "gas_cc", n_bins=10)
        hr_min, hr_max = 6.0, 8.5
        bin_width = (hr_max - hr_min) / 10
        for i, rep in enumerate(result):
            members = [
                g for g in fleet if min(int((g.heat_rate - hr_min) / bin_width), 9) == i
            ]
            total = sum(g.pmax_mw for g in members)
            expected = sum(g.heat_rate * g.pmax_mw for g in members) / total
            self.assertAlmostEqual(rep.heat_rate, expected, places=6)

    def test_none_uses_predefined_bins(self):
        result = aggregate_fleet_by_efficiency(
            _uniform_gas_cc_fleet(), "gas_cc", n_bins=None
        )
        # The test fleet spans all three predefined vintage bins.
        self.assertEqual(len(result), 3)
        self.assertEqual(
            {g.efficiency_bin for g in result},
            {"h_class", "f_class", "older"},
        )


class TestCcsLearningCurve(unittest.TestCase):
    """CCS new-build LCOE follows a Wright's-Law learning curve."""

    def test_ccs_learning_curve(self):
        config = ScenarioConfig()
        lcoe_2026 = compute_lcoe("gas_cc_ccs", 2026, config, cumulative_gw=2.0)
        lcoe_2035 = compute_lcoe("gas_cc_ccs", 2035, config, cumulative_gw=15.0)
        lcoe_2050 = compute_lcoe("gas_cc_ccs", 2050, config, cumulative_gw=41.0)
        self.assertTrue(
            lcoe_2026 > lcoe_2035 > lcoe_2050,
            "CCS LCOE should decline with deployment",
        )
        # LCOE decline tracks the capex decline; assert at least 15%.
        self.assertLess(
            lcoe_2050,
            lcoe_2026 * 0.85,
            "CCS LCOE should decline at least 15%",
        )

    def test_ccs_learning_independent_of_gas_cc(self):
        config = ScenarioConfig()
        # CCS at low cumulative, gas_cc at high cumulative.
        lcoe_ccs = compute_lcoe("gas_cc_ccs", 2030, config, cumulative_gw=5.0)
        lcoe_gas = compute_lcoe("gas_cc", 2030, config, cumulative_gw=1300.0)
        # CCS should be more expensive (higher capex and FOM).
        self.assertGreater(lcoe_ccs, lcoe_gas)

    def test_ccs_no_cumulative_returns_base(self):
        config = ScenarioConfig()
        lcoe_base = compute_lcoe("gas_cc_ccs", 2030, config, cumulative_gw=None)
        lcoe_ref = compute_lcoe("gas_cc_ccs", 2030, config, cumulative_gw=2.0)
        # 2.0 GW is the reference point, so both equal the base cost.
        self.assertLess(abs(lcoe_base - lcoe_ref) / lcoe_ref, 0.01)


class TestRetrofitCapexLearning(unittest.TestCase):
    """CCS retrofit capex declines along the shared learning curve."""

    def test_retrofit_capex_learning(self):
        base = 900.0  # $/kW
        adjusted_early = _adjust_retrofit_capex(base, cumulative_gw=4.0)
        adjusted_late = _adjust_retrofit_capex(base, cumulative_gw=32.0)
        self.assertLess(
            adjusted_early,
            base,
            "Retrofit capex should decline after 1 doubling",
        )
        self.assertLess(
            adjusted_late,
            adjusted_early,
            "More deployment = lower capex",
        )
        self.assertGreater(
            adjusted_late,
            base * 0.5,
            "Decline shouldn't exceed 50% at 4 doublings with lr=0.10",
        )

    def test_retrofit_capex_base_when_no_cumulative(self):
        base = 900.0
        self.assertEqual(_adjust_retrofit_capex(base, None), base)
        # At or below the reference deployment, capex is unchanged.
        self.assertEqual(_adjust_retrofit_capex(base, 2.0), base)


class TestCapexCo2Scaling(unittest.TestCase):
    """capx D50: the island sized to the host's captured CO2 (GATED, default off).

    The D49 §1.4 seam: §45Q credited on the host's own captured tonnes while
    the island is charged flat per kW. Under the gate a host capturing ``k``
    times the reference host's CO2 per MWh pays ``k`` times the island, and
    cogeneration hosts are not candidates. Off is byte-identical.
    """

    # The reference host pays exactly the reference increment (scale 1.0);
    # a host at twice its rate pays twice the island.
    ER_REF = 0.90 * 6.3 * 0.057 / 0.90  # 0.3591 t/MWh — hr_ref x CO2 factor

    def test_captured_ref_is_the_reference_host_derivation(self):
        from market_sim.config.constants import (
            FUEL_CO2_FACTOR_PER_MMBTU,
            HEAT_RATE_BINS,
        )
        from market_sim.model.capacity_evolution.ccs import (
            ccs_retrofit_captured_ref_t_per_mwh,
            ccs_retrofit_reference_host_heat_rate,
        )

        cfg = ScenarioConfig()
        self.assertEqual(
            ccs_retrofit_reference_host_heat_rate(),
            min(HEAT_RATE_BINS["gas_cc"].values()),
        )
        self.assertAlmostEqual(
            ccs_retrofit_captured_ref_t_per_mwh(cfg),
            cfg.ccs_retrofit_capture_rate * 6.3 * FUEL_CO2_FACTOR_PER_MMBTU["gas_cc"],
            places=12,
        )
        self.assertAlmostEqual(
            ccs_retrofit_captured_ref_t_per_mwh(cfg), 0.32319, places=5
        )

    def test_off_is_byte_identical_and_cache_neutral(self):
        # Default and explicit-False screens produce the same log, with the
        # flat reference island (scale 1.0) and CHP hosts still candidates.
        def fleet():
            chp = _gas_cc("CHP", heat_rate=7.0, emission_rate=0.55)
            chp.plant_group = "CC_CHP"
            return [_gas_cc("REG", heat_rate=7.0, emission_rate=0.55), chp]

        _, log_default = _screen(fleet(), HIGH_PRICES)
        _, log_off = _screen(
            fleet(),
            HIGH_PRICES,
            config=_fixture_config(ccs_retrofit_capex_co2_scaling=False),
        )
        self.assertEqual(log_default, log_off)
        self.assertEqual({e["unit_id"] for e in log_off}, {"REG", "CHP"})
        for entry in log_off:
            self.assertEqual(entry["capex_scale"], 1.0)
            self.assertEqual(
                entry["retrofit_capex_per_mw"], _FIXTURE_RETROFIT_CAPEX_KW * 1000.0
            )
        # Registered cache-optional at False: the shipped default keys
        # identically with the field absent or explicitly False, distinctly on.
        base = ScenarioConfig()
        self.assertEqual(
            base.cache_key(),
            ScenarioConfig(ccs_retrofit_capex_co2_scaling=False).cache_key(),
        )
        self.assertNotEqual(
            base.cache_key(),
            ScenarioConfig(ccs_retrofit_capex_co2_scaling=True).cache_key(),
        )

    def test_island_scales_with_captured_co2(self):
        cfg = _fixture_config(ccs_retrofit_capex_co2_scaling=True)
        ref = _gas_cc("REF", heat_rate=6.3, emission_rate=self.ER_REF)
        twice = _gas_cc("TWICE", heat_rate=6.3, emission_rate=2.0 * self.ER_REF)
        _, log = _screen([ref, twice], HIGH_PRICES, config=cfg, carbon_price=120.0)
        by_id = {e["unit_id"]: e for e in log}
        self.assertEqual(set(by_id), {"REF", "TWICE"})
        self.assertAlmostEqual(by_id["REF"]["capex_scale"], 1.0, places=9)
        self.assertAlmostEqual(by_id["TWICE"]["capex_scale"], 2.0, places=9)
        self.assertAlmostEqual(
            by_id["REF"]["retrofit_capex_per_mw"], _FIXTURE_RETROFIT_CAPEX_KW * 1000.0
        )
        self.assertAlmostEqual(
            by_id["TWICE"]["retrofit_capex_per_mw"],
            2.0 * _FIXTURE_RETROFIT_CAPEX_KW * 1000.0,
        )
        # The same two hosts off the gate: the high emitter's payback was
        # SHORTER than the reference host's (the D49 inversion); on, it pays
        # twice the island and its payback lengthens against its own off value.
        _, log_off = _screen(
            [
                _gas_cc("REF", heat_rate=6.3, emission_rate=self.ER_REF),
                _gas_cc("TWICE", heat_rate=6.3, emission_rate=2.0 * self.ER_REF),
            ],
            HIGH_PRICES,
            carbon_price=120.0,
        )
        off = {e["unit_id"]: e for e in log_off}
        self.assertLess(off["TWICE"]["payback_years"], off["REF"]["payback_years"])
        self.assertGreater(
            by_id["TWICE"]["payback_years"], off["TWICE"]["payback_years"]
        )
        self.assertAlmostEqual(
            by_id["REF"]["payback_years"], off["REF"]["payback_years"]
        )

    def test_high_emitter_stops_clearing_on_45q_alone(self):
        # A 0.60 t/MWh host at carbon 0: at a $1,600/kW island it clears
        # flat-per-kW (12 x uplift > 1.6 M) and FAILS once the island is
        # sized to 1.67x the reference host's CO2 flow (2.67 M > 12 x uplift).
        host = _gas_cc("HOT", heat_rate=7.0, emission_rate=0.60)
        _, log_flat = _screen(
            [host], HIGH_PRICES, config=_fixture_config(ccs_retrofit_capex_kw=1600.0)
        )
        self.assertEqual([e["unit_id"] for e in log_flat], ["HOT"])
        host2 = _gas_cc("HOT", heat_rate=7.0, emission_rate=0.60)
        _, log_scaled = _screen(
            [host2],
            HIGH_PRICES,
            config=_fixture_config(
                ccs_retrofit_capex_kw=1600.0, ccs_retrofit_capex_co2_scaling=True
            ),
        )
        self.assertEqual(log_scaled, [])
        self.assertEqual(host2.fuel_type, "gas_cc")

    def test_cogeneration_host_excluded_only_when_armed(self):
        def fleet():
            chp = _gas_cc("CHP", heat_rate=7.0, emission_rate=0.55)
            chp.plant_group = "CC_CHP"
            reg = _gas_cc("REG", heat_rate=7.0, emission_rate=0.55)
            reg.plant_group = "CC_REGULAR"
            return [chp, reg]

        f_off, log_off = _screen(fleet(), HIGH_PRICES, carbon_price=120.0)
        self.assertEqual({e["unit_id"] for e in log_off}, {"CHP", "REG"})
        f_on, log_on = _screen(
            fleet(),
            HIGH_PRICES,
            config=_fixture_config(ccs_retrofit_capex_co2_scaling=True),
            carbon_price=120.0,
        )
        self.assertEqual({e["unit_id"] for e in log_on}, {"REG"})
        self.assertEqual({g.unit_id: g.fuel_type for g in f_on}["CHP"], "gas_cc")
        self.assertEqual({g.unit_id: g.fuel_type for g in f_on}["REG"], "gas_cc_ccs")


if __name__ == "__main__":
    unittest.main()
