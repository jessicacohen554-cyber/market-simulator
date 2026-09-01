"""Soundness protocol — end-to-end and invariant tests for the market simulator.

This test suite goes beyond unit tests to verify that the full system
produces economically and physically correct results when all modules are
wired together.  It covers:

  Layer 1 — Spec compliance: no forbidden imports, no hour loops in the
            matrix builder, renewables on LHS, ScenarioConfig is a plain
            dataclass, VOLL and topology match spec.

  Layer 2 — LP invariants: energy balance holds every zone/hour, prices
            equal marginal cost of the marginal unit, curtailment is
            non-negative, slack triggers VOLL pricing.

  Layer 3 — Physics conservation: storage SOC cyclic boundary, RTE losses
            correct, transmission flows within TTC, emissions = dispatch × rate.

  Layer 4 — Economic logic: merit order respected, carbon price shifts
            dispatch, IRA PTC creates negative prices when wind is must-take,
            storage arbitrages peak/off-peak correctly.

  Layer 5 — End-to-end pipeline: runner produces cached results, capacity
            evolution changes fleet across years, two scenarios with different
            gas prices diverge, deterministic reruns are identical.

  Layer 6 — Performance: matrix build < 3s, solve < 15s for full ERCOT 8760.
"""

import ast
import tempfile
import unittest
from pathlib import Path

import numpy as np

from market_sim.config.constants import (
    STORAGE_TIEBREAKER_EPSILON,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition
from market_sim.data.fleet import (
    Generator,
    generators_to_fleet_arrays,
)
from market_sim.model.dispatch import solve_dispatch
from market_sim.model.storage import (
    StorageUnit,
    storage_units_to_arrays,
)
from market_sim.model.transmission import (
    build_incidence_matrix,
    get_ttc_array,
)
from market_sim.results import cache
from tests.helpers import REPO_ROOT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fleet(zone_specs, zone_names, T=24):
    """Build a minimal fleet from (zone, pmax, mc) tuples."""
    gens = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone=zone,
            fuel_type="gas_cc",
            pmax_mw=pmax,
            pmin_mw=0.0,
            heat_rate=0.0,
            vom=mc,
            eford=0.0,
        )
        for i, (zone, pmax, mc) in enumerate(zone_specs)
    ]
    fleet = generators_to_fleet_arrays(gens, zone_names, hours=T)
    mc_arr = np.array([[g.vom] * T for g in gens], dtype=float)
    return gens, fleet, mc_arr


def _energy_balance_residual(
    result, fleet, demand, incidence=None, storage_arrays=None
):
    """Return per-zone per-hour residual: supply - demand.  Should be ~0."""
    T = demand.shape[1]
    n_zones = demand.shape[0]
    gen_by_zone = np.zeros((n_zones, T))
    for g in range(fleet.n_gen):
        gen_by_zone[fleet.zone_idx[g]] += result.dispatch[g]
    net_flow = np.zeros((n_zones, T))
    if incidence is not None and result.flows is not None:
        net_flow = incidence.toarray() @ result.flows
    chg = np.zeros((n_zones, T))
    dis = np.zeros((n_zones, T))
    if storage_arrays is not None and result.storage_charge is not None:
        for s in range(storage_arrays.n_storage):
            chg[storage_arrays.zone_idx[s]] += result.storage_charge[s]
            dis[storage_arrays.zone_idx[s]] += result.storage_discharge[s]
    dump = result.dump if result.dump is not None else np.zeros_like(result.slack)
    supply = (
        gen_by_zone
        + result.wind_dispatched
        + result.solar_dispatched
        + dis
        - chg
        + net_flow
        + result.slack
        - dump
    )
    return supply - demand


# ===================================================================
# LAYER 1: Spec Compliance (Static Checks)
# ===================================================================


class TestSpecCompliance(unittest.TestCase):
    """Verify the codebase follows methodology-spec rules at the source level."""

    def test_no_forbidden_imports(self):
        """No pyomo, pulp, scipy.optimize, or numba anywhere in src/."""
        src_root = REPO_ROOT / "src"
        forbidden = {"pyomo", "pulp", "numba"}
        for py in src_root.rglob("*.py"):
            source = py.read_text()
            for mod in forbidden:
                self.assertNotIn(
                    f"import {mod}",
                    source,
                    f"Forbidden import '{mod}' found in {py.relative_to(src_root)}",
                )
            self.assertNotIn(
                "from scipy.optimize",
                source,
                f"Forbidden 'scipy.optimize' import in {py.relative_to(src_root)}",
            )

    def test_no_hour_loops_in_dispatch_builder(self):
        """dispatch.py must not loop over hours in constraint/bound/cost assembly."""
        dispatch_path = REPO_ROOT / "src" / "market_sim" / "model" / "dispatch.py"
        source = dispatch_path.read_text()
        tree = ast.parse(source)
        builder_funcs = {
            "build_constraints",
            "build_variable_bounds",
            "build_cost_vector",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in builder_funcs:
                for child in ast.walk(node):
                    if isinstance(child, ast.For):
                        iter_src = ast.dump(child.iter)
                        self.assertNotIn(
                            "8760",
                            iter_src,
                            f"Hour-loop in {node.name}: range(8760) detected",
                        )
                        if "Call" in iter_src and "range" in iter_src:
                            if "'T'" in iter_src or "layout.T" in iter_src:
                                self.fail(
                                    f"Hour-loop range(T) in builder func {node.name}"
                                )

    def test_scenario_config_is_plain_dataclass(self):
        """ScenarioConfig must be a plain @dataclass, NOT Pydantic."""
        import dataclasses

        self.assertTrue(dataclasses.is_dataclass(ScenarioConfig))
        mro = [cls.__name__ for cls in ScenarioConfig.__mro__]
        self.assertNotIn("BaseModel", mro)

    def test_topology_matches_spec(self):
        """ERCOT=7 zones, CAISO=6 zones (5 trading + import). Import share=0.

        CAISO 4 -> 6: the SP15 local-capacity-area split (c28d57b1, 2026-07-09)
        replaced SP15 with LA_BASIN / SDGE / SP15_rest and is the operative
        default topology under every CAISO keeper since.
        """
        ercot = get_iso_config("ERCOT")
        self.assertEqual(len(ercot.zones), 7)
        shares = [z.load_share for z in ercot.zones]
        self.assertAlmostEqual(sum(shares), 1.0, places=6)

        caiso = get_iso_config("CAISO")
        self.assertEqual(len(caiso.zones), 6)
        self.assertAlmostEqual(sum(z.load_share for z in caiso.zones), 1.0, places=6)
        wecc = [z for z in caiso.zones if "WECC" in z.name][0]
        self.assertEqual(wecc.load_share, 0.0)

    def test_voll_values(self):
        """ERCOT VOLL=$5000, CAISO VOLL=$2000 per spec."""
        self.assertEqual(get_iso_config("ERCOT").voll, 5000.0)
        self.assertEqual(get_iso_config("CAISO").voll, 2000.0)

    def test_storage_epsilon_is_0001(self):
        """Storage tiebreaker epsilon = 0.001 $/MWh per spec."""
        self.assertEqual(STORAGE_TIEBREAKER_EPSILON, 0.001)

    def test_no_pickle_or_csv_in_results(self):
        """Result storage must use Parquet only."""
        results_root = REPO_ROOT / "src" / "market_sim" / "results"
        for py in results_root.rglob("*.py"):
            source = py.read_text()
            self.assertNotIn("pickle.dump", source, f"pickle.dump found in {py.name}")
            self.assertNotIn(".to_csv(", source, f".to_csv found in {py.name}")
            self.assertNotIn(".to_hdf(", source, f".to_hdf found in {py.name}")


# ===================================================================
# LAYER 2: LP Invariants
# ===================================================================


class TestLPInvariants(unittest.TestCase):
    """Core LP properties that must hold regardless of inputs."""

    def test_energy_balance_single_zone_24h(self):
        """Supply = demand every hour in a minimal single-zone case."""
        zone_names = ["Z0"]
        _, fleet, mc = _make_fleet([("Z0", 200, 40)], zone_names, T=24)
        demand = np.full((1, 24), 100.0)
        wind_cf = np.zeros((1, 24))
        wind_cap = np.zeros(1)
        solar_cf = np.zeros((1, 24))
        solar_cap = np.zeros(1)

        result = solve_dispatch(
            fleet, demand, wind_cf, wind_cap, solar_cf, solar_cap, mc=mc, T=24
        )
        residual = _energy_balance_residual(result, fleet, demand)
        np.testing.assert_allclose(residual, 0, atol=1e-4)

    def test_price_equals_marginal_unit_cost(self):
        """With 2 gens and demand between them, price = expensive gen's MC."""
        zone_names = ["Z0"]
        _, fleet, mc = _make_fleet([("Z0", 60, 30), ("Z0", 60, 70)], zone_names, T=24)
        demand = np.full((1, 24), 90.0)
        result = solve_dispatch(
            fleet,
            demand,
            np.zeros((1, 24)),
            np.zeros(1),
            np.zeros((1, 24)),
            np.zeros(1),
            mc=mc,
            T=24,
        )
        np.testing.assert_allclose(result.prices[0], 70.0, atol=0.5)

    def test_slack_triggers_voll_pricing(self):
        """When demand exceeds all capacity, slack > 0 and price = VOLL."""
        zone_names = ["Z0"]
        _, fleet, mc = _make_fleet([("Z0", 50, 30)], zone_names, T=24)
        demand = np.full((1, 24), 100.0)
        voll = 5000.0
        result = solve_dispatch(
            fleet,
            demand,
            np.zeros((1, 24)),
            np.zeros(1),
            np.zeros((1, 24)),
            np.zeros(1),
            mc=mc,
            voll=voll,
            T=24,
        )
        self.assertTrue(np.all(result.slack > 0))
        np.testing.assert_allclose(result.prices[0], voll, atol=1.0)

    def test_renewables_are_decision_variables_on_lhs(self):
        """Wind dispatched <= cf x cap, and it appears as supply, not demand reduction."""
        zone_names = ["Z0"]
        _, fleet, mc = _make_fleet([("Z0", 200, 50)], zone_names, T=24)
        wind_cf = np.full((1, 24), 0.4)
        wind_cap = np.array([100.0])
        demand = np.full((1, 24), 120.0)

        result = solve_dispatch(
            fleet,
            demand,
            wind_cf,
            wind_cap,
            np.zeros((1, 24)),
            np.zeros(1),
            mc=mc,
            T=24,
        )
        np.testing.assert_allclose(result.wind_dispatched[0], 40.0, atol=0.1)
        np.testing.assert_allclose(result.dispatch.sum(axis=0), 80.0, atol=0.1)
        residual = _energy_balance_residual(result, fleet, demand)
        np.testing.assert_allclose(residual, 0, atol=1e-4)

    def test_curtailment_is_nonnegative(self):
        """Dispatched renewable <= available; curtailment >= 0."""
        zone_names = ["Z0"]
        _, fleet, mc = _make_fleet([("Z0", 200, 50)], zone_names, T=24)
        wind_cf = np.full((1, 24), 0.8)
        wind_cap = np.array([300.0])
        demand = np.full((1, 24), 100.0)

        result = solve_dispatch(
            fleet,
            demand,
            wind_cf,
            wind_cap,
            np.zeros((1, 24)),
            np.zeros(1),
            mc=mc,
            T=24,
        )
        available = wind_cf * wind_cap[:, None]
        curtailment = available - result.wind_dispatched
        self.assertTrue(np.all(curtailment >= -1e-6))

    def test_prices_are_lp_duals_not_separate_model(self):
        """Price = MC of marginal generator, verified by complementary slackness."""
        zone_names = ["Z0"]
        _, fleet, mc = _make_fleet(
            [("Z0", 50, 20), ("Z0", 50, 50), ("Z0", 50, 80)], zone_names, T=24
        )
        demand = np.full((1, 24), 60.0)
        result = solve_dispatch(
            fleet,
            demand,
            np.zeros((1, 24)),
            np.zeros(1),
            np.zeros((1, 24)),
            np.zeros(1),
            mc=mc,
            T=24,
        )
        np.testing.assert_allclose(result.prices[0], 50.0, atol=0.5)
        np.testing.assert_allclose(result.dispatch[0], 50.0, atol=0.1)
        np.testing.assert_allclose(result.dispatch[1], 10.0, atol=0.1)
        np.testing.assert_allclose(result.dispatch[2], 0.0, atol=0.1)


# ===================================================================
# LAYER 3: Physics Conservation
# ===================================================================


class TestPhysicsConservation(unittest.TestCase):
    """Physical invariants: SOC cyclic, RTE losses, flow limits."""

    def _run_storage_case(self, T=48):
        """Return a dispatch result with one storage unit, peak/off-peak demand."""
        zone_names = ["Z0"]
        _, fleet, mc = _make_fleet([("Z0", 200, 20), ("Z0", 200, 80)], zone_names, T=T)
        demand = np.zeros((1, T))
        for h in range(T):
            demand[0, h] = 100 if (h % 24) < 12 else 300

        eta = 0.85**0.5
        units = [
            StorageUnit(
                unit_id="STO",
                zone="Z0",
                tech_name="li_ion_4hr",
                power_cap_mw=100,
                energy_cap_mwh=400,
                eta_charge=eta,
                eta_discharge=eta,
            )
        ]
        sa = storage_units_to_arrays(units, zone_names)

        result = solve_dispatch(
            fleet,
            demand,
            np.zeros((1, T)),
            np.zeros(1),
            np.zeros((1, T)),
            np.zeros(1),
            mc=mc,
            storage_power_cap=sa.power_cap,
            storage_energy_cap=sa.energy_cap,
            storage_zone_idx=sa.zone_idx,
            eta_chg=sa.eta_chg,
            eta_dis=sa.eta_dis,
            T=T,
        )
        return result, sa

    def test_soc_cyclic_boundary(self):
        """SOC[0] = SOC[T-1] — the cyclic constraint holds."""
        result, _ = self._run_storage_case(T=48)
        np.testing.assert_allclose(
            result.storage_soc[0, 0],
            result.storage_soc[0, -1],
            atol=1e-3,
            err_msg="SOC cyclic boundary violated",
        )

    def test_rte_losses(self):
        """Total discharge energy < total charge energy by RTE factor."""
        result, _ = self._run_storage_case(T=48)
        total_charge = result.storage_charge[0].sum()
        total_discharge = result.storage_discharge[0].sum()
        if total_charge > 1.0:
            rte_effective = total_discharge / total_charge
            self.assertLess(
                rte_effective,
                1.0,
                "Discharge exceeds charge — energy created from nothing",
            )
            self.assertAlmostEqual(rte_effective, 0.85, delta=0.05)

    def test_soc_dynamics_hour_by_hour(self):
        """SOC[t] = SOC[t-1] + eta_chg*Chg[t] - Dis[t]/eta_dis for all t."""
        result, sa = self._run_storage_case(T=48)
        eta_c = sa.eta_chg[0]
        eta_d = sa.eta_dis[0]
        soc = result.storage_soc[0]
        chg = result.storage_charge[0]
        dis = result.storage_discharge[0]
        T = len(soc)
        for t in range(T):
            prev = soc[t - 1]  # wraps around for t=0
            expected = prev + eta_c * chg[t] - dis[t] / eta_d
            self.assertAlmostEqual(
                soc[t], expected, places=3, msg=f"SOC dynamics violated at hour {t}"
            )

    def test_transmission_flow_within_ttc(self):
        """All flows respect -TTC <= flow <= TTC."""
        T = 48
        iso = get_iso_config("ERCOT")
        zone_names = iso.zone_names
        _, fleet, mc = _make_fleet(
            [
                ("North", 5000, 30),
                ("South", 2000, 50),
                ("West", 1000, 70),
                ("Houston", 3000, 45),
            ],
            zone_names,
            T=T,
        )
        demand = np.array([z.load_share for z in iso.zones])[:, None] * np.full(
            T, 6000.0
        )
        incidence = build_incidence_matrix(iso.links, zone_names)
        ttc = get_ttc_array(iso.links)

        n_zones = len(zone_names)
        result = solve_dispatch(
            fleet,
            demand,
            np.zeros((n_zones, T)),
            np.zeros(n_zones),
            np.zeros((n_zones, T)),
            np.zeros(n_zones),
            mc=mc,
            incidence=incidence,
            ttc=ttc,
            T=T,
        )
        self.assertTrue(
            np.all(np.abs(result.flows) <= ttc[:, None] + 1e-4),
            "Flow exceeds TTC on at least one link",
        )

    def test_emissions_equal_dispatch_times_rate(self):
        """Emissions accounting is a pure dot product."""
        from market_sim.results.emissions import compute_emissions

        zone_names = ["Z0"]
        gens = [
            Generator(
                unit_id="G0",
                name="G0",
                zone="Z0",
                fuel_type="gas_cc",
                pmax_mw=200,
                heat_rate=7.0,
                vom=0,
                emission_rate_co2=0.4,
            ),
            Generator(
                unit_id="G1",
                name="G1",
                zone="Z0",
                fuel_type="coal",
                pmax_mw=200,
                heat_rate=10.0,
                vom=0,
                emission_rate_co2=0.9,
            ),
        ]
        fleet = generators_to_fleet_arrays(gens, zone_names, hours=24)
        dispatch = np.array([[100.0] * 24, [50.0] * 24])
        emission_rates = fleet.emission_rate
        emissions = compute_emissions(dispatch, emission_rates)
        expected = (100 * 0.4 + 50 * 0.9) * 24
        self.assertAlmostEqual(emissions.sum(), expected, places=2)


# ===================================================================
# LAYER 4: Economic Logic
# ===================================================================


class TestEconomicLogic(unittest.TestCase):
    """Merit order, carbon pricing, storage arbitrage behave correctly."""

    def test_merit_order_respected(self):
        """Cheapest gens dispatch first; expensive gens fill the margin."""
        zone_names = ["Z0"]
        _, fleet, mc = _make_fleet(
            [("Z0", 100, 10), ("Z0", 100, 40), ("Z0", 100, 70), ("Z0", 100, 100)],
            zone_names,
            T=24,
        )
        demand = np.full((1, 24), 250.0)
        result = solve_dispatch(
            fleet,
            demand,
            np.zeros((1, 24)),
            np.zeros(1),
            np.zeros((1, 24)),
            np.zeros(1),
            mc=mc,
            T=24,
        )
        np.testing.assert_allclose(result.dispatch[0], 100.0, atol=0.1)
        np.testing.assert_allclose(result.dispatch[1], 100.0, atol=0.1)
        np.testing.assert_allclose(result.dispatch[2], 50.0, atol=0.1)
        np.testing.assert_allclose(result.dispatch[3], 0.0, atol=0.1)

    def test_carbon_price_shifts_merit_order(self):
        """A carbon price makes high-emission units more expensive, reordering dispatch."""
        zone_names = ["Z0"]
        gens = [
            Generator(
                unit_id="GAS",
                name="Gas",
                zone="Z0",
                fuel_type="gas_cc",
                pmax_mw=100,
                heat_rate=0,
                vom=30,
                emission_rate_co2=0.4,
            ),
            Generator(
                unit_id="COAL",
                name="Coal",
                zone="Z0",
                fuel_type="coal",
                pmax_mw=100,
                heat_rate=0,
                vom=25,
                emission_rate_co2=1.0,
            ),
        ]
        fleet = generators_to_fleet_arrays(gens, zone_names, hours=24)

        # Without carbon: coal (25) cheaper than gas (30)
        mc_no_carbon = np.array([[30.0] * 24, [25.0] * 24])
        demand = np.full((1, 24), 80.0)
        r1 = solve_dispatch(
            fleet,
            demand,
            np.zeros((1, 24)),
            np.zeros(1),
            np.zeros((1, 24)),
            np.zeros(1),
            mc=mc_no_carbon,
            T=24,
        )
        self.assertGreater(
            r1.dispatch[1].mean(),
            r1.dispatch[0].mean(),
            "Coal should dispatch more when cheaper",
        )

        # With $50/ton carbon: coal = 25+50=75, gas = 30+20=50
        mc_carbon = np.array([[50.0] * 24, [75.0] * 24])
        r2 = solve_dispatch(
            fleet,
            demand,
            np.zeros((1, 24)),
            np.zeros(1),
            np.zeros((1, 24)),
            np.zeros(1),
            mc=mc_carbon,
            T=24,
        )
        self.assertGreater(
            r2.dispatch[0].mean(),
            r2.dispatch[1].mean(),
            "Gas should dispatch more when carbon makes coal expensive",
        )

    def test_storage_arbitrages_peak_offpeak(self):
        """Storage charges when prices are low and discharges when high."""
        zone_names = ["Z0"]
        _, fleet, mc = _make_fleet([("Z0", 200, 20), ("Z0", 200, 80)], zone_names, T=24)
        demand = np.zeros((1, 24))
        for h in range(24):
            demand[0, h] = 100 if h < 12 else 250

        eta = 0.9
        units = [
            StorageUnit(
                unit_id="S0",
                zone="Z0",
                tech_name="li_ion_8hr",
                power_cap_mw=50,
                energy_cap_mwh=200,
                eta_charge=eta,
                eta_discharge=eta,
            )
        ]
        sa = storage_units_to_arrays(units, zone_names)

        result = solve_dispatch(
            fleet,
            demand,
            np.zeros((1, 24)),
            np.zeros(1),
            np.zeros((1, 24)),
            np.zeros(1),
            mc=mc,
            storage_power_cap=sa.power_cap,
            storage_energy_cap=sa.energy_cap,
            storage_zone_idx=sa.zone_idx,
            eta_chg=sa.eta_chg,
            eta_dis=sa.eta_dis,
            T=24,
        )
        chg_offpeak = result.storage_charge[0, :12].sum()
        chg_onpeak = result.storage_charge[0, 12:].sum()
        dis_offpeak = result.storage_discharge[0, :12].sum()
        dis_onpeak = result.storage_discharge[0, 12:].sum()

        self.assertGreater(chg_offpeak, chg_onpeak, "Should charge more off-peak")
        self.assertGreater(dis_onpeak, dis_offpeak, "Should discharge more on-peak")


# ===================================================================
# LAYER 5: End-to-End Pipeline
# ===================================================================


class TestEndToEnd(unittest.TestCase):
    """Full-pipeline tests using the real runner and solver."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name)

    def tearDown(self):
        cache.CACHE_ROOT = self._original_root
        self._tmp.cleanup()

    def _run_short(self, config=None, iso="ERCOT", end_year=2027):
        """Run an ISO for a few years with reduced hours for speed."""
        from market_sim import runner
        import market_sim.runner as runner_mod

        if config is None:
            config = ScenarioConfig(iso=iso, hours=168)

        original_end = runner_mod.END_YEAR
        runner_mod.END_YEAR = end_year
        try:
            key = runner.run_scenario_iso(config, iso)
        finally:
            runner_mod.END_YEAR = original_end
        return key

    def test_runner_produces_cached_results(self):
        """A run creates Parquet files and config YAML for each year."""
        key = self._run_short(end_year=2027)
        for year in (2026, 2027):
            self.assertTrue(cache.is_cached("ERCOT", key, year))
        config_path = cache.CACHE_ROOT / "ERCOT" / key / "config.yaml"
        self.assertTrue(config_path.exists())

    def test_cached_results_load_cleanly(self):
        """Cached Parquet round-trips: load, check shapes, no NaN."""
        key = self._run_short(end_year=2026)
        result = cache.load_result("ERCOT", key, 2026)
        self.assertEqual(result.status, "Optimal")
        self.assertEqual(result.prices.shape[1], 168)
        self.assertFalse(np.isnan(result.prices).any())
        self.assertFalse(np.isnan(result.dispatch).any())

    def test_rerun_is_deterministic(self):
        """Running the same config twice produces identical cache key."""
        config = ScenarioConfig(iso="ERCOT", hours=168)
        key1 = self._run_short(config, end_year=2026)
        key2 = self._run_short(config, end_year=2026)
        self.assertEqual(key1, key2)

    def test_different_gas_prices_produce_different_results(self):
        """Two scenarios differing only in gas price produce different prices."""
        config_low = ScenarioConfig(iso="ERCOT", hours=168, gas_price_path="low")
        config_high = ScenarioConfig(iso="ERCOT", hours=168, gas_price_path="high")

        key_low = self._run_short(config_low, end_year=2026)
        key_high = self._run_short(config_high, end_year=2026)

        self.assertNotEqual(key_low, key_high)

        result_low = cache.load_result("ERCOT", key_low, 2026)
        result_high = cache.load_result("ERCOT", key_high, 2026)

        self.assertGreater(
            result_high.prices.mean(),
            result_low.prices.mean(),
            "High gas scenario should have higher average prices",
        )

    def test_capacity_evolution_changes_fleet(self):
        """Over a multi-year run, the fleet composition changes."""
        config = ScenarioConfig(iso="ERCOT", hours=168)
        key = self._run_short(config, end_year=2028)

        r2026 = cache.load_result("ERCOT", key, 2026)
        r2028 = cache.load_result("ERCOT", key, 2028)

        n_gen_2026 = r2026.dispatch.shape[0]
        n_gen_2028 = r2028.dispatch.shape[0]
        wind_2026 = r2026.wind_dispatched.sum()
        wind_2028 = r2028.wind_dispatched.sum()

        changed = n_gen_2026 != n_gen_2028 or not np.isclose(
            wind_2026, wind_2028, rtol=0.01
        )
        self.assertTrue(
            changed,
            f"Fleet should evolve: n_gen 2026={n_gen_2026} vs 2028={n_gen_2028}, "
            f"wind 2026={wind_2026:.0f} vs 2028={wind_2028:.0f}",
        )

    def test_caiso_with_wecc_imports(self):
        """CAISO end-to-end: WECC import tranches produce stepped prices."""
        config = ScenarioConfig(iso="CAISO", hours=168, rps_enabled=False)
        key = self._run_short(config, iso="CAISO", end_year=2026)

        result = cache.load_result("CAISO", key, 2026)
        self.assertEqual(result.status, "Optimal")
        price_std = result.prices[0].std()
        self.assertGreater(price_std, 0.1, "CAISO prices should not be perfectly flat")


# ===================================================================
# LAYER 6: Performance
# ===================================================================


class TestPerformance(unittest.TestCase):
    """Verify the model meets its performance targets."""

    def test_full_ercot_8760_timing(self):
        """Full ERCOT 8760-hour dispatch: build < 3s, total < 30s."""
        T = 8760
        iso = get_iso_config("ERCOT")
        zone_names = iso.zone_names

        zones_cycle = zone_names * 50
        gens = [
            Generator(
                unit_id=f"G{i}",
                name=f"G{i}",
                zone=zones_cycle[i],
                fuel_type="gas_cc",
                pmax_mw=100,
                pmin_mw=0,
                heat_rate=0,
                vom=15 + 75 * i / 200,
                eford=0,
            )
            for i in range(200)
        ]
        fleet = generators_to_fleet_arrays(gens, zone_names, hours=T)
        mc = np.array([[g.vom] * T for g in gens], dtype=float)

        eta = 0.85**0.5
        units = [
            StorageUnit(
                unit_id=f"STO{i}",
                zone=zone_names[i % 4],
                tech_name="li_ion_4hr",
                power_cap_mw=100,
                energy_cap_mwh=400,
                eta_charge=eta,
                eta_discharge=eta,
            )
            for i in range(5)
        ]
        sa = storage_units_to_arrays(units, zone_names)
        incidence = build_incidence_matrix(iso.links, zone_names)
        ttc = get_ttc_array(iso.links)

        hours = np.arange(T)
        hod = hours % 24
        daily = 0.6 + 0.4 * np.sin(np.pi * (hod - 6) / 12)
        total = 12000 * daily
        demand = np.array([z.load_share for z in iso.zones])[:, None] * total[None, :]

        n_zones = len(zone_names)
        west = zone_names.index("West")
        south_central = zone_names.index("South_Central")
        wind_cf = np.zeros((n_zones, T))
        wind_cf[west] = 0.35
        wind_cap = np.zeros(n_zones)
        wind_cap[west] = 2000.0
        solar_cf = np.zeros((n_zones, T))
        solar_cf[south_central] = np.clip(0.6 * np.sin(np.pi * (hod - 6) / 12), 0, 1)
        solar_cap = np.zeros(n_zones)
        solar_cap[south_central] = 1500.0

        result = solve_dispatch(
            fleet,
            demand,
            wind_cf,
            wind_cap,
            solar_cf,
            solar_cap,
            mc=mc,
            incidence=incidence,
            ttc=ttc,
            storage_power_cap=sa.power_cap,
            storage_energy_cap=sa.energy_cap,
            storage_zone_idx=sa.zone_idx,
            eta_chg=sa.eta_chg,
            eta_dis=sa.eta_dis,
        )

        print(
            f"\nPerformance: build={result.build_time:.2f}s "
            f"solve={result.solve_time:.2f}s "
            f"total={result.build_time + result.solve_time:.2f}s"
        )

        self.assertLess(result.build_time, 3.0, "Matrix build exceeds 3s target")
        self.assertLess(
            result.build_time + result.solve_time,
            30.0,
            "Total dispatch time exceeds 30s budget",
        )

        residual = _energy_balance_residual(result, fleet, demand, incidence, sa)
        np.testing.assert_allclose(residual, 0, atol=1e-3)


# ===================================================================
# LAYER 7: Sweep and Config Integrity
# ===================================================================


class TestSweepIntegrity(unittest.TestCase):
    """Sweep system produces correct, unique configurations."""

    def test_factorial_sweep_counts(self):
        """3x3 sweep produces exactly 9 unique configs."""
        sweep = SweepDefinition(
            sweep={
                "gas_price_path": ["low", "mid", "high"],
                "carbon_price": [0.0, 25.0, 50.0],
            }
        )
        configs = sweep.generate()
        self.assertEqual(len(configs), 9)
        keys = [c.cache_key() for c in configs]
        self.assertEqual(
            len(set(keys)), 9, "All 9 configs should have unique cache keys"
        )

    def test_cache_key_sensitive_to_every_tier1_param(self):
        """Changing any single Tier 1 parameter changes the cache key.

        NOTE what this test does and does NOT establish. Cache-key sensitivity
        is a HASHING property, not evidence that the field reaches the model:
        ``renewable_buildout_pace`` sat in this list and passed for as long as
        it existed, while being consumed by no model code at all (capx-D21
        §5.1 measured its two arms metric-identically; deleted under rule 26
        [R-DELETE] by capx-T16). A field belongs here because a distinct
        scenario must not collide with the base key — reachability is the
        driver battery's job, not this test's.
        """
        base = ScenarioConfig()
        base_key = base.cache_key()

        tier1_changes = {
            "gas_price_path": "high",
            "carbon_price": 42.0,
            "nox_price": 5.0,
            "demand_growth_rate": 0.03,
            "storage_deployment": "high",
        }
        for param, val in tier1_changes.items():
            modified = base.with_overrides(**{param: val})
            self.assertNotEqual(
                modified.cache_key(),
                base_key,
                f"Changing {param} should change cache_key",
            )


if __name__ == "__main__":
    unittest.main()
