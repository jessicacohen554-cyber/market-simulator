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

from market_sim.config.scenarios import ScenarioConfig, cache_key_drop_defaults
from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    Generator,
    aggregate_fleet_by_efficiency,
    assemble_mc,
    generators_to_fleet_arrays,
)
from market_sim.model.capacity_evolution.evolve import (
    _CCS_RETROFIT_LEDGER_SCALING_FIELDS,
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
# 9 h at $60 / 15 h at $5 — the same shape as SPLIT_PRICES but thinner, used
# ONLY by Test45QWindowInScreen. It exists because the 12 h split stopped
# discriminating when capx D65-B re-identified ccs_retrofit_vom_adder
# 8.0 -> 2.95 $/MWh (2026$): a cheaper capture island pays back in 8.3 yr, well
# inside the 12-year statutory window, so both arms retrofitted and the test
# could no longer see the window at all. At 9 h the payback is 16.5 yr, back
# inside the (12, 25) straddle the window test needs. Kept separate from
# SPLIT_PRICES so the other classes that use the 12 h split are untouched.
_WINDOW_ON_HOURS = 9
WINDOW_SPLIT_PRICES = np.concatenate(
    [
        np.full((1, _WINDOW_ON_HOURS), 60.0),
        np.full((1, T - _WINDOW_ON_HOURS), 5.0),
    ],
    axis=1,
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
    """``ScenarioConfig`` for the ERCOT screen fixtures, with the capex pin.

    ``ccs_retrofit_capex_co2_scaling`` is pinned EXPLICITLY ``False`` here
    unless a caller overrides it. The dataclass default flipped to ``True`` on
    2026-09-05 (capx D60, owner ruling Q42), and every fixture in this file
    that predates the flip was written against the flat-per-kW construction
    with CHP hosts in the candidate set; pinning the fixture keeps each of
    those tests testing what it was written to test, and the classes that
    exercise the ARMED construction pass ``True`` explicitly (as they always
    did). :class:`TestCapexCo2ScalingIsTheDefault` covers the shipped posture.
    """
    overrides.setdefault("ccs_retrofit_capex_kw", _FIXTURE_RETROFIT_CAPEX_KW)
    overrides.setdefault("ccs_retrofit_capex_co2_scaling", False)
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
    clean_attribute_price_by_fuel=None,
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
        clean_attribute_price_by_fuel=clean_attribute_price_by_fuel,
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
        # WINDOW_SPLIT_PRICES: 45Q pays but the post-window uplift is NEGATIVE
        # (the HR penalty + VOM adder + transport exceed the in-merit margin
        # without the credit). Under the statutory 12-year window the capex
        # cannot be recovered before the credit dies -> no retrofit; under the
        # indefinite extension (None) the credit runs the full remaining life
        # and the payback (~16 yr) clears the 25-year remaining life.
        #
        # RE-TUNED 2026-09-06 (capx D65-B) from the shared 12h SPLIT_PRICES to a
        # local 9h fixture. The cause is Act B — ccs_retrofit_vom_adder
        # re-identified 8.0 -> 2.95 $/MWh (2026$) off the ATB basis — which made
        # retrofits EASIER, the direction stated before the measurement, so the
        # old 12h fixture's payback fell to 8.3 yr and stopped straddling the
        # 12-year window. What is re-tuned is this UNIT TEST'S FIXTURE, to
        # restore its discriminating power over the mechanism it names; no
        # model parameter and no threshold moved, and nothing here was chosen
        # against a residual (rule 1 [R-STRUCT]). At 9 in-merit hours the
        # payback is 16.5 yr — the same (12, 25) straddle the original had.
        fleet, log = _screen([_gas_cc("G0")], WINDOW_SPLIT_PRICES)
        self.assertEqual(log, [])
        self.assertEqual(fleet[0].fuel_type, "gas_cc")

        cfg_none = _fixture_config(ira_45q_credit_window_years=None)
        fleet2, log2 = _screen([_gas_cc("G1")], WINDOW_SPLIT_PRICES, config=cfg_none)
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
        # The capture VOM adder is read from the config rather than written as
        # a literal: capx D65-B re-identified it 8.0 -> 2.95 $/MWh (2026$) off
        # the ATB 2024 v4.0.0 basis, and a literal here would have to be
        # re-typed on every such re-identification while asserting nothing about
        # the SEAM this test exists for (that the adder reaches the LP's vom).
        # The value itself is pinned to its source in
        # tests/unit/config/test_ccs_retrofit_fixed_cost_basis.py.
        vom_adder = _fixture_config().ccs_retrofit_vom_adder
        self.assertAlmostEqual(arrays.vom[0], 2.0 + vom_adder, places=6)
        self.assertAlmostEqual(arrays.pmax[0], 500.0, places=6)

        # The marginal cost reflects the penalized heat rate, the VOM adder
        # and the reduced (post-capture) emission rate.
        mc = assemble_mc(arrays, np.array([[4.0]]), 100.0, 0.0)
        expected = 6.9 * 1.12 * 4.0 + (2.0 + vom_adder) + 0.037 * 100.0
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
        # Registered cache-optional at a FROZEN "False" declaration, which the
        # 2026-09-05 default flip (capx D60, owner ruling Q42) deliberately did
        # NOT touch. So: an EXPLICIT False still drops from the hash and keeps
        # the pre-flip key, while the armed default enters it and keys apart —
        # which is the whole point of option (b'-1).
        base = ScenarioConfig()
        self.assertTrue(base.ccs_retrofit_capex_co2_scaling)
        self.assertEqual(
            base.cache_key(),
            ScenarioConfig(ccs_retrofit_capex_co2_scaling=True).cache_key(),
        )
        self.assertNotEqual(
            base.cache_key(),
            ScenarioConfig(ccs_retrofit_capex_co2_scaling=False).cache_key(),
        )
        # The literal that used to sit here ("4c6b03ae098b6e3e", the pre-Q42
        # pin) was RETIRED 2026-09-06 by capx D65-B, not re-typed. Act B
        # re-identified ccs_retrofit_vom_adder 8.0 -> 2.95 $/MWh (2026$), and a
        # plain value field has no frozen declaration to drop at, so it re-keys
        # EVERY config — this control arm included. Re-pinning the new literal
        # would assert only "some hash", so what is pinned instead is the
        # PROPERTY the literal stood for: an explicit False hashes identically
        # to a config that never mentions the field, which is what "still drops
        # from the hash, still keeps its bundle" actually means and what
        # survives the next unrelated re-key.
        self.assertEqual(
            ScenarioConfig(ccs_retrofit_capex_co2_scaling=False).cache_key(),
            ScenarioConfig(
                ccs_retrofit_capex_co2_scaling=False,
                ccs_retrofit_fixed_cost_co2_scaling=False,
            ).cache_key(),
        )
        # And the pre-Q42 key is still REACHABLE by holding Act B's value at its
        # pre-D65-B level — the decomposition PRECOMMIT-capx-d65b-2026-09-06.md
        # §3.1 uses to show Q42's drop mechanic is intact under the coupling.
        self.assertEqual(
            ScenarioConfig(
                ccs_retrofit_capex_co2_scaling=False, ccs_retrofit_vom_adder=8.0
            ).cache_key(),
            "4c6b03ae098b6e3e",
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

        # The OFF arm is the fixture's explicit False (the pre-D60 posture).
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


class TestCapexCo2ScalingIsTheDefault(unittest.TestCase):
    """capx D60 / owner ruling Q42 (2026-09-05): the repair is the SHIPPED posture.

    The classes above pin the pre-flip construction through ``_fixture_config``'s
    explicit ``False`` so each keeps testing what it was written to test. These
    two tests are the ones that would fail if the flip were ever reverted by
    accident, and they exercise the shipped default rather than a fixture.
    """

    def test_the_dataclass_default_is_armed(self):
        self.assertTrue(ScenarioConfig().ccs_retrofit_capex_co2_scaling)
        self.assertTrue(ScenarioConfig(mode="backcast").ccs_retrofit_capex_co2_scaling)

    def test_the_shipped_default_sizes_the_island_and_drops_chp(self):
        # Same fleet as TestCapexCo2Scaling's CHP case, but on a config that
        # passes NOTHING: the CHP host must be excluded and the surviving
        # host's island must be sized to its own CO2 flow.
        chp = _gas_cc("CHP", heat_rate=7.0, emission_rate=0.55)
        chp.plant_group = "CC_CHP"
        reg = _gas_cc("REG", heat_rate=7.0, emission_rate=0.55)
        reg.plant_group = "CC_REGULAR"
        cfg = ScenarioConfig(
            iso="ERCOT", ccs_retrofit_capex_kw=_FIXTURE_RETROFIT_CAPEX_KW
        )
        fleet, log = _screen([chp, reg], HIGH_PRICES, config=cfg, carbon_price=120.0)
        self.assertEqual({e["unit_id"] for e in log}, {"REG"})
        self.assertEqual({g.unit_id: g.fuel_type for g in fleet}["CHP"], "gas_cc")
        from market_sim.model.capacity_evolution.ccs import (
            ccs_retrofit_captured_ref_t_per_mwh,
        )

        entry = log[0]
        expected_scale = (
            cfg.ccs_retrofit_capture_rate * 0.55
        ) / ccs_retrofit_captured_ref_t_per_mwh(cfg)
        self.assertAlmostEqual(entry["capex_scale"], expected_scale, places=9)
        self.assertGreater(entry["capex_scale"], 1.0)


class TestFixedCostCo2Scaling(unittest.TestCase):
    """capx D65 Act A: the two FIXED-COST legs sized to the same island.

    ``ccs_retrofit_fixed_cost_co2_scaling`` (GATED, default off; requires the
    D50 gate). Seam 1 sized the island's CAPEX to the host's captured CO2 and
    left ΔFOM ($/MW-yr) and the capture VOM adder ($/MWh) at the reference
    host's values, so both diluted per captured tonne as ``er`` rose. Both are
    TPC fractions in their own sources (ATB 2024 fossil methodology; NETL
    Rev 4a B31A->B31B.90 at 95.5 % / 100 % -- FINDING-capx-d64-2026-09-05.md
    §1.2), and under seam 1 the island's TPC scales with ``k``, so on, both
    legs carry the same ``k``. Off is byte-identical.
    """

    # The reference host: er = hr_ref x CO2 factor, so captured / captured_ref
    # is exactly 1.0 and every seam-4 quantity must be invariant to the digit.
    ER_REF = 6.3 * 0.057  # 0.3591 t/MWh

    @staticmethod
    def _armed(**overrides):
        """Fixture config with BOTH seams on (seam 4 requires seam 1)."""
        overrides.setdefault("ccs_retrofit_capex_co2_scaling", True)
        overrides.setdefault("ccs_retrofit_fixed_cost_co2_scaling", True)
        return _fixture_config(**overrides)

    def test_validator_rejects_the_field_without_seam_1(self):
        # There is no ``k`` without seam 1: arming this alone would be a silent
        # no-op that nonetheless keys distinctly, so the config refuses it.
        with self.assertRaises(ValueError) as ctx:
            ScenarioConfig(
                ccs_retrofit_fixed_cost_co2_scaling=True,
                ccs_retrofit_capex_co2_scaling=False,
            )
        self.assertIn("ccs_retrofit_capex_co2_scaling", str(ctx.exception))
        # ... and accepts the pair.
        cfg = ScenarioConfig(
            ccs_retrofit_fixed_cost_co2_scaling=True,
            ccs_retrofit_capex_co2_scaling=True,
        )
        self.assertTrue(cfg.ccs_retrofit_fixed_cost_co2_scaling)

    def test_off_is_byte_identical_and_cache_neutral(self):
        # THE OFF PATH, re-expressed for the armed posture (capx D65-B,
        # 2026-09-06). Until Act A's default flip, "off" could be written as
        # "seam 4 absent" and this test compared absent-vs-explicit-False. That
        # comparison is now vacuous in the wrong direction: absent means ARMED.
        # So the off path is written EXPLICITLY on both sides, which is what the
        # D65-B charter asks this shape of test to pin — the explicit-False path
        # is byte-identical to the pre-D65 construction and cache-neutral.
        #
        # Note the two configs below reach "off" by DIFFERENT routes: cfg_false
        # says so directly, while cfg_demoted turns seam 1 off and lets the pair
        # resolution demote seam 4 (there is no k without seam 1, so it is inert
        # by construction). Their retrofit ECONOMICS differ — seam 1 also sizes
        # the island — so they are compared on the seam-4 quantities only.
        def fleet():
            return [
                _gas_cc("REF", heat_rate=6.3, emission_rate=self.ER_REF),
                _gas_cc("HOT", heat_rate=7.0, emission_rate=0.60),
            ]

        cfg_absent = _fixture_config(
            ccs_retrofit_capex_co2_scaling=True,
            ccs_retrofit_fixed_cost_co2_scaling=False,
        )
        cfg_false = _fixture_config(
            ccs_retrofit_capex_co2_scaling=True,
            ccs_retrofit_fixed_cost_co2_scaling=False,
        )
        f_absent, log_absent = _screen(
            fleet(), HIGH_PRICES, config=cfg_absent, carbon_price=120.0
        )
        f_false, log_false = _screen(
            fleet(), HIGH_PRICES, config=cfg_false, carbon_price=120.0
        )
        self.assertEqual(log_absent, log_false)
        self.assertTrue(log_absent)
        base_fom = (
            cfg_absent.fixed_om_gas_cc_ccs
            * cfg_absent.retirement_fom_multiplier_gas_cc_ccs
            - cfg_absent.fixed_om_gas_cc * cfg_absent.retirement_fom_multiplier_gas_cc
        ) * 1000.0
        for entry in log_absent:
            self.assertEqual(entry["fixed_cost_scale"], 1.0)
            self.assertEqual(entry["delta_fom_per_mw_yr"], base_fom)
            self.assertEqual(
                entry["vom_adder_per_mwh"], cfg_absent.ccs_retrofit_vom_adder
            )
        converted = {g.unit_id: g for g in f_absent if g.fuel_type == "gas_cc_ccs"}
        self.assertTrue(converted)
        for uid, g in converted.items():
            self.assertAlmostEqual(
                g.vom, 2.0 + cfg_absent.ccs_retrofit_vom_adder, places=12
            )
        self.assertEqual(
            {g.unit_id: (g.fuel_type, g.vom) for g in f_absent},
            {g.unit_id: (g.fuel_type, g.vom) for g in f_false},
        )
        # CACHE SHAPE AFTER THE FLIP (capx D65-B Act A, the (b'-1) pattern).
        # The default is ARMED, so it no longer equals the frozen "False"
        # declaration: it enters the hash. An explicit False still equals that
        # declaration, so it still DROPS — which is the property that lets a
        # control arm keep its bundle, and it is asserted as a property rather
        # than as a literal so it survives the next unrelated re-key.
        base = ScenarioConfig()
        self.assertTrue(base.ccs_retrofit_fixed_cost_co2_scaling)
        self.assertEqual(
            base.cache_key(),
            ScenarioConfig(ccs_retrofit_fixed_cost_co2_scaling=True).cache_key(),
        )
        self.assertNotEqual(
            base.cache_key(),
            ScenarioConfig(ccs_retrofit_fixed_cost_co2_scaling=False).cache_key(),
        )
        # ACT A ALONE LEAVES THE EXPLICIT-FALSE PATH ON ITS PRE-FLIP KEY. This
        # is the D65-B STOP ("the explicit-False path moving a key") decomposed:
        # hold Act B's value at its pre-change 8.0 and the explicit-False key is
        # e5ecd4105ada3e58, exactly the pre-flip forecast default. The movement
        # at HEAD is Act B's unconditional re-key, declared in advance
        # (PRECOMMIT-capx-d65b-2026-09-06.md §3.1), not Act A's.
        self.assertEqual(
            ScenarioConfig(
                ccs_retrofit_fixed_cost_co2_scaling=False, ccs_retrofit_vom_adder=8.0
            ).cache_key(),
            "e5ecd4105ada3e58",
        )
        self.assertEqual(
            ScenarioConfig(
                mode="backcast",
                ccs_retrofit_fixed_cost_co2_scaling=False,
                ccs_retrofit_vom_adder=8.0,
            ).cache_key(),
            "6a2845e50951394e",
        )
        # And the ARMED default's own keys, pre-declared before the solve.
        self.assertEqual(base.cache_key(), "547053bdfccd4264")
        self.assertEqual(
            ScenarioConfig(mode="backcast").cache_key(), "f61891696e671969"
        )

    def test_reference_host_is_invariant_on_and_off(self):
        # STOP 1 of the D65 charter, as a test: a k = 1 host must not move in
        # ANY log field, on or off. captured/captured_ref == 1 exactly, so
        # every seam-4 factor is 1.0 by construction, not by tolerance.
        from market_sim.model.capacity_evolution.ccs import (
            ccs_retrofit_captured_ref_t_per_mwh,
        )

        # Seam 4 written EXPLICITLY off: since capx D65-B (2026-09-06) its
        # default is ARMED, so omitting it no longer names the off path.
        cfg_off = _fixture_config(
            ccs_retrofit_capex_co2_scaling=True,
            ccs_retrofit_fixed_cost_co2_scaling=False,
        )
        cfg_on = self._armed()
        self.assertAlmostEqual(
            cfg_on.ccs_retrofit_capture_rate * self.ER_REF,
            ccs_retrofit_captured_ref_t_per_mwh(cfg_on),
            places=12,
        )
        f_off, log_off = _screen(
            [_gas_cc("REF", heat_rate=6.3, emission_rate=self.ER_REF)],
            HIGH_PRICES,
            config=cfg_off,
            carbon_price=120.0,
        )
        f_on, log_on = _screen(
            [_gas_cc("REF", heat_rate=6.3, emission_rate=self.ER_REF)],
            HIGH_PRICES,
            config=cfg_on,
            carbon_price=120.0,
        )
        self.assertEqual(len(log_on), 1)
        self.assertAlmostEqual(log_on[0]["capex_scale"], 1.0, places=12)
        self.assertAlmostEqual(log_on[0]["fixed_cost_scale"], 1.0, places=12)
        # Every log field, not a chosen subset: the two seam-4 keys are
        # written on BOTH paths (1.0 and the flat adder when off), so the key
        # sets match and every value must match too.
        self.assertEqual(set(log_off[0]), set(log_on[0]))
        for key, off_val in log_off[0].items():
            on_val = log_on[0][key]
            if isinstance(off_val, float):
                self.assertAlmostEqual(
                    on_val, off_val, places=9, msg=f"k=1 row moved on {key}"
                )
            else:
                self.assertEqual(on_val, off_val, msg=f"k=1 row moved on {key}")
        # The converted unit is identical too.
        self.assertEqual(
            [(g.fuel_type, round(g.vom, 12), round(g.heat_rate, 12)) for g in f_off],
            [(g.fuel_type, round(g.vom, 12), round(g.heat_rate, 12)) for g in f_on],
        )

    def test_legs_scale_with_captured_co2(self):
        # A host at twice the reference CO2 flow pays twice the island AND
        # twice the island's O&M -- the whole point of the seam.
        cfg = self._armed()
        ref = _gas_cc("REF", heat_rate=6.3, emission_rate=self.ER_REF)
        twice = _gas_cc("TWICE", heat_rate=6.3, emission_rate=2.0 * self.ER_REF)
        fleet, log = _screen([ref, twice], HIGH_PRICES, config=cfg, carbon_price=200.0)
        by_id = {e["unit_id"]: e for e in log}
        self.assertEqual(set(by_id), {"REF", "TWICE"})
        base_fom = (
            cfg.fixed_om_gas_cc_ccs * cfg.retirement_fom_multiplier_gas_cc_ccs
            - cfg.fixed_om_gas_cc * cfg.retirement_fom_multiplier_gas_cc
        ) * 1000.0
        self.assertAlmostEqual(by_id["REF"]["fixed_cost_scale"], 1.0, places=9)
        self.assertAlmostEqual(by_id["TWICE"]["fixed_cost_scale"], 2.0, places=9)
        self.assertAlmostEqual(by_id["REF"]["delta_fom_per_mw_yr"], base_fom, places=6)
        self.assertAlmostEqual(
            by_id["TWICE"]["delta_fom_per_mw_yr"], 2.0 * base_fom, places=6
        )
        self.assertAlmostEqual(
            by_id["REF"]["vom_adder_per_mwh"], cfg.ccs_retrofit_vom_adder, places=12
        )
        self.assertAlmostEqual(
            by_id["TWICE"]["vom_adder_per_mwh"],
            2.0 * cfg.ccs_retrofit_vom_adder,
            places=12,
        )
        # The fixed-cost legs move ONLY with k -- the island's capex scaling is
        # untouched by this seam (STOP 1's other half).
        self.assertAlmostEqual(by_id["TWICE"]["capex_scale"], 2.0, places=9)

    def test_converted_unit_vom_carries_the_scaled_adder(self):
        # The dispatch VOM of a converted unit must be the VOM the screen
        # priced its uplift at -- otherwise the LP runs a unit the screen never
        # evaluated.
        cfg = self._armed()
        twice = _gas_cc("TWICE", heat_rate=6.3, emission_rate=2.0 * self.ER_REF)
        fleet, log = _screen([twice], HIGH_PRICES, config=cfg, carbon_price=200.0)
        self.assertEqual([e["unit_id"] for e in log], ["TWICE"])
        conv = {g.unit_id: g for g in fleet}["TWICE"]
        self.assertEqual(conv.fuel_type, "gas_cc_ccs")
        self.assertAlmostEqual(conv.vom, 2.0 + log[0]["vom_adder_per_mwh"], places=12)
        self.assertAlmostEqual(
            conv.vom, 2.0 + 2.0 * cfg.ccs_retrofit_vom_adder, places=9
        )

    def test_per_tonne_invariance_at_carbon_zero(self):
        # Two hosts, EQUAL hr, er ratio 2:1, carbon 0. Per captured tonne the
        # only surviving difference is the HR-PENALTY term (fuel burned to run
        # the capture island), which is per host MWh and does NOT scale with
        # er -- so per tonne it FALLS as er rises. Asserted analytically: the
        # uplift-to-capex ratio of the high emitter minus the reference host's
        # equals the HR-penalty term's per-tonne difference, and nothing else.
        cfg = self._armed()
        lo_er = self.ER_REF
        hi_er = 2.0 * self.ER_REF
        lo = _gas_cc("LO", heat_rate=6.3, emission_rate=lo_er)
        hi = _gas_cc("HI", heat_rate=6.3, emission_rate=hi_er)
        _, log = _screen([lo, hi], HIGH_PRICES, config=cfg, carbon_price=0.0)
        by_id = {e["unit_id"]: e for e in log}
        self.assertEqual(set(by_id), {"LO", "HI"})

        # uplift_window / retrofit_capex_per_mw -- the per-captured-tonne
        # economics, since capex is now proportional to captured tonnes.
        def ratio(entry):
            # ``annual_net_savings_per_mw`` IS the in-window uplift (key name
            # kept for the runner's per-year retrofit logging).
            return entry["annual_net_savings_per_mw"] / entry["retrofit_capex_per_mw"]

        # The HR-penalty term, per host MWh, in $/MWh: the extra fuel burned.
        hours = float(HIGH_PRICES.shape[1])
        avail = 1.0 - lo.eford
        annualize = 8760.0 / hours
        hr_pen_per_mwh = 6.3 * cfg.ccs_retrofit_hr_penalty * 4.0  # hr x pen x gas
        # Per MW-yr the HR penalty costs the same for BOTH hosts (equal hr),
        # but each host's capex differs by k, so per dollar of island the
        # high emitter carries HALF the HR-penalty burden.
        hr_pen_per_mw_yr = hr_pen_per_mwh * hours * avail * annualize
        capex_lo = by_id["LO"]["retrofit_capex_per_mw"]
        capex_hi = by_id["HI"]["retrofit_capex_per_mw"]
        self.assertAlmostEqual(capex_hi / capex_lo, 2.0, places=9)
        expected_gap = hr_pen_per_mw_yr / capex_lo - hr_pen_per_mw_yr / capex_hi
        self.assertAlmostEqual(
            ratio(by_id["HI"]) - ratio(by_id["LO"]), expected_gap, places=9
        )
        # And the direction the seam exists to fix: per tonne the high emitter
        # is now BETTER only by that HR-penalty term, never by the diluted
        # fixed costs -- so the payback ordering no longer rewards emissions
        # through the O&M legs. Off the seam the gap is strictly larger.
        # Seam 4 written EXPLICITLY off: since capx D65-B (2026-09-06) its
        # default is ARMED, so omitting it no longer names the off path.
        cfg_off = _fixture_config(
            ccs_retrofit_capex_co2_scaling=True,
            ccs_retrofit_fixed_cost_co2_scaling=False,
        )
        _, log_off = _screen(
            [
                _gas_cc("LO", heat_rate=6.3, emission_rate=lo_er),
                _gas_cc("HI", heat_rate=6.3, emission_rate=hi_er),
            ],
            HIGH_PRICES,
            config=cfg_off,
            carbon_price=0.0,
        )
        off = {e["unit_id"]: e for e in log_off}
        self.assertGreater(
            ratio(off["HI"]) - ratio(off["LO"]),
            ratio(by_id["HI"]) - ratio(by_id["LO"]),
        )


class TestRetrofitLedgerCarriesTheScalingRecord(unittest.TestCase):
    """capx D65-B-R step 0: the ``ccs_retrofits`` ledger row carries its scales.

    The D65-B screen could not evaluate its own G2 gate (``uplift/capex`` against
    ``k``) because :func:`evolve_fleet` recorded a conversion as
    ``{unit_id, mw, from_fuel, to_fuel}`` and dropped the ``retrofit_log`` that
    carries the island sizing — so the host band and the identity had to be
    reconstructed offline from CAMPD (FINDING-capx-d65b-2026-09-06.md §6.4, the
    D65 §3d defect class: a diagnostic blind to the mechanism it exists to make
    visible). These rows are what make a CCS-seam gate readable from a committed
    bundle instead of by replay.

    The keys are LEDGER data, not config, so nothing here may move a cache key —
    asserted directly rather than argued.
    """

    def _prior(self, fleet, prices):
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=T)
        from types import SimpleNamespace

        return {
            "fleet_arrays": arrays,
            "dispatch_result": SimpleNamespace(dispatch=np.zeros((len(fleet), T))),
            "prices": prices,
            "mc_cost": np.full((len(fleet), T), 29.6),
            "peak_demand": 0.0,
            "zone_names": ["Z0"],
        }

    def _evolve_with_events(self, fleet, config):
        """Run a full ``evolve_fleet`` year with event recording armed."""
        from market_sim.results.evolution_ledger import new_events

        events = new_events()
        _fleet, _tracker, _renew, retrofit_log, _floor = evolve_fleet(
            fleet,
            self._prior(fleet, HIGH_PRICES),
            2030,
            config,
            {},
            gas_price_per_mmbtu=4.0,
            carbon_price=120.0,
            events=events,
        )
        return events, retrofit_log

    def test_ledger_row_carries_every_scaling_field(self):
        cfg = _fixture_config(
            ccs_retrofit_capex_co2_scaling=True,
            ccs_retrofit_fixed_cost_co2_scaling=True,
        )
        events, retrofit_log = self._evolve_with_events(
            [_gas_cc("HOT", heat_rate=7.0, emission_rate=0.60)], cfg
        )
        self.assertEqual(len(retrofit_log), 1, "fixture must convert its one host")
        rows = events["ccs_retrofits"]
        self.assertEqual([r["unit_id"] for r in rows], ["HOT"])
        row = rows[0]
        for key in _CCS_RETROFIT_LEDGER_SCALING_FIELDS:
            self.assertIn(key, row, f"{key} missing from the ledger row")
            self.assertIsInstance(row[key], float)
        # The persisted values ARE the screen's own, not a re-derivation.
        log_entry = retrofit_log[0]
        for key in _CCS_RETROFIT_LEDGER_SCALING_FIELDS:
            self.assertAlmostEqual(row[key], float(log_entry[key]), places=9)
        # ... and the pre-existing keys are untouched.
        self.assertEqual(row["from_fuel"], "gas_cc")
        self.assertEqual(row["to_fuel"], "gas_cc_ccs")

    def test_the_uplift_over_capex_identity_is_readable_from_the_row(self):
        # G2's object: on the armed seam a host's island is sized by ``k``, so
        # its capex carries ``k`` and the per-unit-of-capex uplift falls as
        # ``1/k``. Both sides of that ratio now live on the ledger row, which is
        # the whole point of persisting them.
        cfg = _fixture_config(
            ccs_retrofit_capex_co2_scaling=True,
            ccs_retrofit_fixed_cost_co2_scaling=True,
        )
        er_ref = 6.3 * 0.057
        events, _log = self._evolve_with_events(
            [
                _gas_cc("REF", heat_rate=6.3, emission_rate=er_ref),
                _gas_cc("HOT", heat_rate=6.3, emission_rate=er_ref * 1.5),
            ],
            cfg,
        )
        by_id = {r["unit_id"]: r for r in events["ccs_retrofits"]}
        self.assertEqual(set(by_id), {"REF", "HOT"})
        # k is the island factor: 1.0 at the reference host, 1.5 at the hot one.
        self.assertAlmostEqual(by_id["REF"]["capex_scale"], 1.0, places=6)
        self.assertAlmostEqual(by_id["HOT"]["capex_scale"], 1.5, places=6)
        # Seam 4 charges the fixed-cost legs at the SAME factor.
        for uid in ("REF", "HOT"):
            self.assertAlmostEqual(
                by_id[uid]["fixed_cost_scale"], by_id[uid]["capex_scale"], places=9
            )
        # capex carries k exactly, so capex/k is host-invariant.
        self.assertAlmostEqual(
            by_id["REF"]["retrofit_capex_per_mw"] / by_id["REF"]["capex_scale"],
            by_id["HOT"]["retrofit_capex_per_mw"] / by_id["HOT"]["capex_scale"],
            places=6,
        )

    def test_an_unarmed_run_writes_the_inert_unit_scales(self):
        # Off, both factors are identically 1.0 — so a pre-D50 posture's rows
        # are self-describing rather than silent, and the row shape does not
        # depend on which gates are armed.
        cfg = _fixture_config(ccs_retrofit_capex_co2_scaling=False)
        events, _log = self._evolve_with_events(
            [_gas_cc("HOT", heat_rate=7.0, emission_rate=0.60)], cfg
        )
        row = events["ccs_retrofits"][0]
        self.assertAlmostEqual(row["capex_scale"], 1.0, places=9)
        self.assertAlmostEqual(row["fixed_cost_scale"], 1.0, places=9)

    def test_persisting_the_record_moves_no_cache_key(self):
        # A LEDGER field is not a config field. Stated as an assertion because
        # this lane's whole batch is a re-key event and a step-0 key move would
        # be indistinguishable from Act B's.
        import dataclasses

        # No ScenarioConfig field bears any of these names, so none of them can
        # reach the hash: the record is written by the ledger, not configured.
        cfg_fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
        for key in _CCS_RETROFIT_LEDGER_SCALING_FIELDS:
            self.assertNotIn(key, cfg_fields)
        # Nor is any of them a cache-key drop default, which is the other route
        # a name reaches the hash by.
        for key in _CCS_RETROFIT_LEDGER_SCALING_FIELDS:
            self.assertNotIn(key, cache_key_drop_defaults())
        # Belt and braces: the whole six-ISO bare-key set is invariant to the
        # ledger record's presence, because the record is not read while hashing.
        keys_now = {
            (iso, mode): ScenarioConfig(iso=iso, mode=mode).cache_key()
            for iso in ("ERCOT", "NEISO", "NYISO", "CAISO", "PJM", "MISO")
            for mode in ("forecast", "backcast")
        }
        self.assertEqual(len(set(keys_now.values())), len(keys_now))


class TestCleanTierSeamReachesTheRetrofitScreen(unittest.TestCase):
    """capx D87: the prior year's clean-tier dual prices the retrofit screen.

    The seam SCN ruling S19 routed here (D-15). Before the repair
    :func:`apply_ccs_retrofit` folded two of the three buyers of a certificate
    — the legacy per-fuel scalar and the exogenous premium, both via
    ``effective_eac_price_for_unit`` — where its two sibling screens
    (``retirements.py`` step 3, ``new_entry.py`` step 5) fold all three, so a
    federal CES TARGET row's dual, or a state clean tier admitting
    ``gas_cc_ccs``, priced the LP's certificates and both other screens and
    bought the retrofit screen nothing. Under a target-row config the premium
    is ZERO by construction (``__post_init__`` refuses the two together), so
    ``attr_post`` collapsed to the ``eac_price_gas_cc_ccs`` default of 0.0.

    One doctrine, not a new one (rule 19 ``[R-ONE-MECH]``): one certificate,
    several buyers, ``max()``, never a sum.

    Fixture: ``LOW_PRICES`` ($5/MWh, below every state's cost) so the screen
    is unambiguously OFF without a credit — ``uplift_window`` is then exactly
    ``-delta_fom`` — which makes the credit the sole cause of any retrofit
    below.
    """

    CREDIT = 120.0  # $/MWh — comfortably clears the $5 fixture's cost gap.

    def _fleet(self, zone="Z0"):
        return [_gas_cc("CC1", zone=zone)]

    def test_none_family_is_byte_identical(self):
        """``None`` (every backcast, hindcast and premium-era forecast) no-ops.

        ``clean_credit_for_zone(None, ...)`` returns 0.0 and ``max(x, 0.0) ==
        x`` for the non-negative attribute prices this screen produces, so the
        whole retrofit log must be identical. Asserted against BOTH other
        empty spellings a caller can produce — ``{}`` and a dict carrying only
        fuels this screen never asks about.
        """
        base_fleet, base_log = _screen(self._fleet(), HIGH_PRICES)
        for label, by_fuel in (
            ("None", None),
            ("empty dict", {}),
            ("unrelated fuels", {"wind": np.array([80.0]), "solar": np.array([80.0])}),
        ):
            with self.subTest(family=label):
                fleet, log = _screen(
                    self._fleet(),
                    HIGH_PRICES,
                    zone_names=["Z0"],
                    clean_attribute_price_by_fuel=by_fuel,
                )
                self.assertEqual(log, base_log)
                self.assertEqual(
                    [g.fuel_type for g in fleet], [g.fuel_type for g in base_fleet]
                )

    def test_target_row_credit_buys_a_retrofit_a_zero_premium_config_does_not(self):
        """The identification: same config, same prices — only the dual differs.

        This is the defect, reproduced and then closed. The control is exactly
        a ``CES-T80``-shaped config (target row armed ⇒ premium 0.0 ⇒
        ``eac_price_gas_cc_ccs`` 0.0), which is why its ``attr_post`` is 0.
        """
        control_fleet, control_log = _screen(
            self._fleet(), LOW_PRICES, zone_names=["Z0"]
        )
        self.assertEqual(control_log, [])
        self.assertEqual(control_fleet[0].fuel_type, "gas_cc")

        arm_fleet, arm_log = _screen(
            self._fleet(),
            LOW_PRICES,
            zone_names=["Z0"],
            clean_attribute_price_by_fuel={
                "gas_cc_ccs": np.array([self.CREDIT], dtype=float)
            },
        )
        self.assertEqual(len(arm_log), 1)
        self.assertEqual(arm_fleet[0].fuel_type, "gas_cc_ccs")

    def test_attr_post_is_the_credit_exactly(self):
        """``attr_post`` IS the dual under a target row — the screen's identity.

        Under a target-row config ``effective_eac_price_for_unit`` returns 0.0
        for both fuels, so the ``max()`` resolves to the clean leg and the
        ledger's ``attr_post_usd_per_mwh`` must equal the credit to the cent.
        This is the same identity the D87 screen's gate G1 reads off a real
        NYISO bundle (dual x ``federal_ces_ccs_capture_fraction``).
        """
        _, log = _screen(
            self._fleet(),
            LOW_PRICES,
            zone_names=["Z0"],
            clean_attribute_price_by_fuel={
                "gas_cc_ccs": np.array([self.CREDIT], dtype=float)
            },
        )
        self.assertEqual(len(log), 1)
        self.assertAlmostEqual(log[0]["attr_post_usd_per_mwh"], self.CREDIT, places=9)
        # No committed config lists ``gas_cc`` in ``federal_ces_eligible_fuels``
        # and the fuel-level crediting map documents unabated gas CC as a
        # conservative 0, so the unabated leg folds to 0 — but it is FOLDED,
        # not omitted (see the symmetry test below).
        self.assertAlmostEqual(log[0]["attr_unabated_usd_per_mwh"], 0.0, places=9)

    def test_unabated_leg_folds_its_own_credit_symmetrically(self):
        """A ``gas_cc`` credit reaches ``attr_unabated``, keeping the uplift incremental.

        No committed config mints a ``gas_cc`` credit, so this is the leg's
        ONLY coverage — and it is why the leg is WRITTEN rather than left out
        "because it is zero": leaving it asymmetric is the exact shape this
        seam came from.

        What the symmetric fold guarantees, asserted here: while both states
        are in the money, a credit paid EQUALLY to both **cancels out of the
        uplift exactly**, because the uplift is a DIFFERENCE of the two
        states' margins. That is the incremental valuation W2-C is built on.
        It does NOT mean "no retrofit" — §45Q is credited on the captured
        tonne only and stays asymmetric — which is why the assertion is on the
        uplift's invariance, not on the decision.
        """
        both = {
            "gas_cc": np.array([self.CREDIT], dtype=float),
            "gas_cc_ccs": np.array([self.CREDIT], dtype=float),
        }
        # HIGH prices: both states are in the money with and without a credit,
        # so no max(., 0) clipping can mask the cancellation.
        _, base_log = _screen(self._fleet(), HIGH_PRICES, zone_names=["Z0"])
        _, both_log = _screen(
            self._fleet(),
            HIGH_PRICES,
            zone_names=["Z0"],
            clean_attribute_price_by_fuel=both,
        )
        self.assertEqual(len(base_log), 1)
        self.assertEqual(len(both_log), 1)
        # The leg is genuinely wired — both attribute prices carry the credit …
        self.assertAlmostEqual(
            both_log[0]["attr_unabated_usd_per_mwh"], self.CREDIT, places=9
        )
        self.assertAlmostEqual(
            both_log[0]["attr_post_usd_per_mwh"], self.CREDIT, places=9
        )
        # … each state's margin rises by the same certificate revenue …
        self.assertGreater(
            both_log[0]["margin_unabated_per_mw_yr"],
            base_log[0]["margin_unabated_per_mw_yr"],
        )
        # … and the INCREMENT between them is untouched, to the cent.
        for key in ("annual_net_savings_per_mw", "uplift_post_window_per_mw_yr"):
            with self.subTest(field=key):
                self.assertAlmostEqual(both_log[0][key], base_log[0][key], places=6)
        # The contrast that shows the fold is load-bearing: crediting the POST
        # state ALONE moves the same uplift, by the credit's own revenue.
        _, post_only_log = _screen(
            self._fleet(),
            HIGH_PRICES,
            zone_names=["Z0"],
            clean_attribute_price_by_fuel={
                "gas_cc_ccs": np.array([self.CREDIT], dtype=float)
            },
        )
        self.assertGreater(
            post_only_log[0]["annual_net_savings_per_mw"],
            base_log[0]["annual_net_savings_per_mw"],
        )

    def test_the_credit_is_locational_never_the_broadcast_max(self):
        """A zone outside the row's eligibility mask earns nothing.

        ``clean_credit_for_zone``'s own contract (never the broadcast max —
        "that would credit MISO-East's dual to an Arkansas unit"), asserted at
        this consumer: one credited zone, two identical units, only the unit
        in the credited zone converts.
        """
        prices = np.vstack([LOW_PRICES[0], LOW_PRICES[0]])  # 2 zones, same price
        fleet = [_gas_cc("CC_Z0", zone="Z0"), _gas_cc("CC_Z1", zone="Z1")]
        out, log = _screen(
            fleet,
            prices,
            zone_names=["Z0", "Z1"],
            clean_attribute_price_by_fuel={
                "gas_cc_ccs": np.array([0.0, self.CREDIT], dtype=float)
            },
        )
        self.assertEqual([e["unit_id"] for e in log], ["CC_Z1"])
        by_id = {g.unit_id: g.fuel_type for g in out}
        self.assertEqual(by_id["CC_Z0"], "gas_cc")
        self.assertEqual(by_id["CC_Z1"], "gas_cc_ccs")

    def test_no_zone_context_credits_nothing_fail_closed(self):
        """A unit the caller cannot place earns 0, never the vector's first row.

        ``zone_names=None`` on a MULTI-row price array is the unmappable case
        the screen already skips loudly-in-debug; on a single-row array the
        unit is priced at row 0 but still has no zone index, and the credit
        must resolve to 0.0 rather than silently indexing the vector.
        """
        _, log = _screen(
            self._fleet(),
            LOW_PRICES,
            zone_names=None,
            clean_attribute_price_by_fuel={
                "gas_cc_ccs": np.array([self.CREDIT], dtype=float)
            },
        )
        self.assertEqual(log, [])

    def test_the_exogenous_max_still_wins_when_it_is_larger(self):
        """``max()``, never a sum — the doctrine the repair had to keep.

        A legacy ``eac_price_gas_cc_ccs`` above the dual must dominate it, and
        the ledger must record the LARGER of the two, not their total.
        """
        cfg = _fixture_config(eac_price_gas_cc_ccs=200.0)
        _, log = _screen(
            self._fleet(),
            LOW_PRICES,
            config=cfg,
            zone_names=["Z0"],
            clean_attribute_price_by_fuel={
                "gas_cc_ccs": np.array([self.CREDIT], dtype=float)
            },
        )
        self.assertEqual(len(log), 1)
        self.assertAlmostEqual(log[0]["attr_post_usd_per_mwh"], 200.0, places=9)


class TestUnitIdUniquenessAtConversion(unittest.TestCase):
    """capx D88 — ``unit_id`` is a key, and a retrofit must not stale it.

    ``legacy_bins.aggregate_fleet`` mints ``f"{fuel}_{bin}_{zone}"`` for every
    aggregatable group's representative and runs at the end of EVERY evolution
    year. A retrofit changes the unit's fuel to ``gas_cc_ccs`` (not
    aggregatable, so it passes through keeping its id) while leaving that id
    asserting the ``gas_cc`` group it just left — so the next unabated gas-CC
    build in the same zone gets the SAME id re-minted for it. Measured
    in-horizon on all nine NEISO T3 golden variants and ERCOT ``ff-t1f-d65br``.

    docs/handoffs/DESIGN-capx-d87-d88-s19-read-2026-09-08.md §2
    """

    def _legacy_rep(self, zone="Z0", ebin="h_class", online_year=2015):
        """A legacy REPRESENTATIVE: the exact id ``aggregate_fleet`` mints."""
        gen = _gas_cc(f"gas_cc_{ebin}_{zone}", zone=zone, online_year=online_year)
        gen.efficiency_bin = ebin
        return gen

    def test_legacy_representative_is_reminted_with_its_vintage(self):
        """The converted representative leaves the ``gas_cc`` id behind."""
        rep = self._legacy_rep()
        fleet, log = _screen([rep], HIGH_PRICES, year=2031)
        self.assertEqual(len(log), 1, "fixture must retrofit for this to test")
        self.assertEqual(rep.fuel_type, "gas_cc_ccs")
        # The id no longer asserts the gas_cc group it left...
        self.assertEqual(rep.unit_id, "gas_cc_ccs_h_class_Z0_r2031")
        # ...and the ledger row carries BOTH names, so a cross-year join can
        # follow the rename (additive: ``unit_id`` still holds the PRE id).
        self.assertEqual(log[0]["unit_id"], "gas_cc_h_class_Z0")
        self.assertEqual(log[0]["to_unit_id"], "gas_cc_ccs_h_class_Z0_r2031")

    def test_reminted_id_frees_the_group_key_for_later_entry(self):
        """The whole point: a later gas-CC build in the zone does not collide.

        This is the defect's actual shape — a legacy representative retrofitted
        in year Y, then any economic ``gas_cc`` build in the same zone in a
        year >= Y, which ``aggregate_fleet`` collapses onto the id the
        converted unit used to hold.
        """
        rep = self._legacy_rep()
        _screen([rep], HIGH_PRICES, year=2031)
        # What the builder mints for whoever occupies the group next.
        later_entrant = self._legacy_rep()
        ids = [rep.unit_id, later_entrant.unit_id]
        self.assertEqual(len(set(ids)), 2, f"ids collide: {ids}")
        # And the fleet SoA builder accepts the pair (the guard is silent).
        fa = generators_to_fleet_arrays([rep, later_entrant], ["Z0"], hours=T)
        self.assertEqual(sorted(fa.unit_ids), sorted(ids))

    def test_two_conversions_in_one_zone_do_not_collide_with_each_other(self):
        """Why the vintage stamp is load-bearing, not decoration.

        ``gas_cc_ccs_{bin}_{zone}`` alone is INSUFFICIENT: the T3 record shows
        the same zone converting a second, third and fourth representative
        (``bau-prera``: 2031/2040/2042/2044), and ``gas_cc_ccs`` does not
        aggregate — so two converted representatives would collide with EACH
        OTHER under an unstamped id.
        """
        first = self._legacy_rep()
        _screen([first], HIGH_PRICES, year=2031)
        # The re-minted group key, again — carried by whatever entered the
        # group after the first conversion. The T3 record's own second
        # conversion is 2040; this fixture uses 2032 because the 24-hour
        # $60 fixture stops clearing its payback once the §45Q window closes
        # (2033 on), and the year that matters here is only that it DIFFERS.
        second = self._legacy_rep()
        _screen([second], HIGH_PRICES, year=2032)
        self.assertEqual(first.unit_id, "gas_cc_ccs_h_class_Z0_r2031")
        self.assertEqual(second.unit_id, "gas_cc_ccs_h_class_Z0_r2032")
        self.assertNotEqual(first.unit_id, second.unit_id)

    def test_campd_per_plant_tranche_keeps_its_id(self):
        """A CAMPD tranche id is a PLANT key, not a group key — never re-mint.

        Nothing can re-mint it, so renaming it would only break the cross-year
        joins that address it (``_plant_codes_from_unit_ids``, the D42/D53
        exempt sets) for no gain.
        """
        gen = _gas_cc("CC_REGULAR_Central_p55048_econ", zone="Z0")
        gen.efficiency_bin = "h_class"
        gen.is_campd_bin = True
        _fleet, log = _screen([gen], HIGH_PRICES, year=2031)
        self.assertEqual(len(log), 1)
        self.assertEqual(gen.unit_id, "CC_REGULAR_Central_p55048_econ")
        self.assertNotIn("to_unit_id", log[0])

    def test_non_legacy_id_is_left_alone(self):
        """The predicate is an EXACT match on the one re-mintable id family."""
        gen = _gas_cc("gas_cc_new_2028c2030_2", zone="Z0")
        gen.efficiency_bin = "h_class"
        _fleet, log = _screen([gen], HIGH_PRICES, year=2031)
        self.assertEqual(len(log), 1)
        self.assertEqual(gen.unit_id, "gas_cc_new_2028c2030_2")
        self.assertNotIn("to_unit_id", log[0])


class TestFleetArraysUnitIdGuard(unittest.TestCase):
    """capx D88 — the SoA builder refuses a fleet whose ids are not unique.

    One set build per call, no decision change. It fails loudly at the one seam
    every LP fleet passes through instead of mis-deciding in the five consumers
    that address units by ``unit_id`` (``retirements.idx_of`` is
    last-write-wins; ``exit_exempt_unit_ids``, the ``retired`` set-diff and
    ``_pre_entry_ids_all`` are set memberships with no fuel to qualify by;
    ``loss_years`` is one counter; the D57 sell-offer stack double-offers).
    """

    def test_unique_fleet_builds(self):
        fa = generators_to_fleet_arrays([_gas_cc("a"), _gas_cc("b")], ["Z0"], hours=T)
        self.assertEqual(list(fa.unit_ids), ["a", "b"])

    def test_duplicate_raises_and_names_the_offending_ids(self):
        with self.assertRaises(ValueError) as ctx:
            generators_to_fleet_arrays(
                [_gas_cc("dup"), _gas_cc("dup"), _gas_cc("ok")],
                ["Z0"],
                hours=T,
                iso="NEISO",
                year=2037,
            )
        msg = str(ctx.exception)
        self.assertIn("duplicate unit_id", msg)
        self.assertIn("'dup'x2", msg)  # named, with its multiplicity
        self.assertNotIn("'ok'", msg)  # and only the offenders
        self.assertIn("NEISO", msg)
        self.assertIn("2037", msg)

    def test_guard_is_silent_on_the_uncollided_retrofit_pair(self):
        """The D88 repair's own output passes its own guard."""
        rep = _gas_cc("gas_cc_h_class_Z0")
        rep.efficiency_bin = "h_class"
        _screen([rep], HIGH_PRICES, year=2031)
        entrant = _gas_cc("gas_cc_h_class_Z0")  # re-minted for the next build
        entrant.efficiency_bin = "h_class"
        fa = generators_to_fleet_arrays([rep, entrant], ["Z0"], hours=T)
        self.assertEqual(len(set(fa.unit_ids)), 2)


if __name__ == "__main__":
    unittest.main()
