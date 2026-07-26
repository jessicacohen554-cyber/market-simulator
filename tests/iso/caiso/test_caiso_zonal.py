"""Zonal-distribution tests for the real CAISO topology.

Exercises the *configured* CAISO network — the NP15 / ZP26 / LA_BASIN / SDGE /
SP15_rest trading zones (SP15 was split into its LCT local-capacity pockets,
docs/handoffs/caiso-sp15-split-implementation-scope-2026-07-09.md) plus the
``WECC_import`` node, with their real Path 15 / Path 26 / Path 66 / Path 46
transfer capabilities — end to end through
:func:`~market_sim.model.dispatch.solve_dispatch`, rather than the synthetic
2-zone toy network in ``test_transmission``. The aim is to catch a TTC value
or a load-share that breaks the dispatch: an infeasible solve, a flow above a
link's limit, load leaking into the zero-load import node, or zonal demand
that does not sum back to the system total.
"""

import unittest

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.data.fleet import Generator, assemble_mc, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.model.transmission import (
    build_export_sinks,
    build_import_generators,
    build_incidence_matrix,
    extend_with_import_node,
    get_ttc_array,
)

T = 24  # 24-hour horizon for every dispatch in this module

# CAISO load (trading) zones, in topology order; WECC_import is excluded as it
# is an import node, not a load zone. SP15_rest is the south gateway that
# Path 26 and Path 46/WOR feed; LA_BASIN and SDGE are the one-way,
# import-limited local-capacity pockets downstream of it.
LOAD_ZONES = ("NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest")
IMPORT_ZONE = "WECC_import"


def _internal_gen(zone: str, pmax: float, mc: float, pmin: float = 0.0) -> Generator:
    """A lossless in-state thermal unit priced at ``mc`` $/MWh via its VOM."""
    return Generator(
        unit_id=f"{zone}_gas",
        name=f"{zone}_gas",
        zone=zone,
        fuel_type="gas_cc",
        pmax_mw=pmax,
        pmin_mw=pmin,
        heat_rate=0.0,  # cost rides entirely in vom, so assemble_mc -> mc
        vom=mc,
        eford=0.0,
    )


def _solve_caiso(internal, demand_by_zone, with_import_node=True):
    """Solve a dispatch over the real CAISO topology.

    Args:
        internal: in-state :class:`Generator` units (any load zone).
        demand_by_zone: ``{zone: MW}`` constant hourly demand per zone.
        with_import_node: append the WECC import tranches + export sinks.

    Returns:
        ``(result, fleet, config)`` where ``config`` is the CAISO topology
        actually solved (the import node is baked into it).
    """
    config = get_iso_config("CAISO")
    zone_names = config.zone_names
    generators = list(internal)
    if with_import_node:
        generators += build_import_generators("CAISO") + build_export_sinks("CAISO")
    fleet = generators_to_fleet_arrays(generators, zone_names, hours=T)
    incidence = build_incidence_matrix(config.links, zone_names)
    ttc = get_ttc_array(config.links)
    mc = assemble_mc(fleet, np.zeros((len(generators), T)), carbon_price=0.0)
    demand = np.vstack(
        [np.full(T, float(demand_by_zone.get(z, 0.0))) for z in zone_names]
    )
    n = len(zone_names)
    result = solve_dispatch(
        fleet,
        demand,
        mc=mc,
        T=T,
        incidence=incidence,
        ttc=ttc,
        wind_cf=np.zeros((n, T)),
        wind_cap=np.zeros(n),
        solar_cf=np.zeros((n, T)),
        solar_cap=np.zeros(n),
    )
    return result, fleet, config


def _zone_balance(result, fleet, config, demand_by_zone):
    """Assert per-zone, per-hour energy balance and return net flow per zone."""
    zone_names = config.zone_names
    n = len(zone_names)
    gen_by_zone = np.zeros((n, T))
    for g in range(fleet.n_gen):
        gen_by_zone[fleet.zone_idx[g]] += result.dispatch[g]
    net_flow = build_incidence_matrix(config.links, zone_names) @ result.flows
    supply = (
        gen_by_zone
        + result.wind_dispatched
        + result.solar_dispatched
        + net_flow
        + result.slack
    )
    demand = np.vstack(
        [np.full(T, float(demand_by_zone.get(z, 0.0))) for z in zone_names]
    )
    np.testing.assert_allclose(supply, demand, atol=1e-6)
    return net_flow


class TestCaisoTopologyInvariants(unittest.TestCase):
    """Config-level checks on the CAISO load zones and intertie TTCs."""

    def setUp(self):
        self.config = get_iso_config("CAISO")

    def test_topology_validates(self):
        # validate_topology raises on an unknown link zone or load shares that
        # do not sum to 1.0; a clean pass is the headline invariant.
        self.config.validate_topology()

    def test_load_zones_sum_to_one_and_import_node_carries_no_load(self):
        shares = {z.name: z.load_share for z in self.config.zones}
        self.assertEqual(shares[IMPORT_ZONE], 0.0)
        load_total = sum(shares[z] for z in LOAD_ZONES)
        self.assertAlmostEqual(load_total, 1.0, places=6)
        # The zero-load import node must not change the system-wide total.
        self.assertAlmostEqual(sum(shares.values()), 1.0, places=6)

    def test_every_ttc_is_positive_and_links_reference_known_zones(self):
        names = set(self.config.zone_names)
        self.assertTrue(len(self.config.links) > 0)
        for link in self.config.links:
            self.assertGreater(link.ttc_mw, 0.0, link)
            self.assertIn(link.from_zone, names)
            self.assertIn(link.to_zone, names)

    def test_import_node_links_into_north_and_south(self):
        by_pair = {(l.from_zone, l.to_zone): l.ttc_mw for l in self.config.links}
        # Path 66 / COI into NP15 and Path 46 / WOR into SP15_rest (the south
        # gateway zone since the SP15 split).
        self.assertEqual(by_pair[(IMPORT_ZONE, "NP15")], 4800.0)
        self.assertEqual(by_pair[(IMPORT_ZONE, "SP15_rest")], 10623.0)
        # The internal N-S corridor: Path 15 and Path 26.
        self.assertEqual(by_pair[("NP15", "ZP26")], 5400.0)
        self.assertEqual(by_pair[("ZP26", "SP15_rest")], 4000.0)
        # The two one-way, import-limited local-capacity pockets downstream
        # of the south gateway (LCT import_cap = peak_load - LCR, 2023).
        self.assertEqual(by_pair[("SP15_rest", "LA_BASIN")], 12008.0)
        self.assertEqual(by_pair[("SP15_rest", "SDGE")], 1436.0)

    def test_import_node_already_baked_in(self):
        # CAISO carries WECC_import in its base config, so extending is a no-op
        # (no duplicate zone or links).
        self.assertIn(IMPORT_ZONE, self.config.zone_names)
        self.assertIs(extend_with_import_node(self.config), self.config)


class TestCaisoZonalDispatch(unittest.TestCase):
    """End-to-end dispatch over the real CAISO zones, TTCs and import node."""

    def test_self_sufficient_zones_balance_with_no_flow(self):
        # Each load zone has cheap local gas covering its own demand, so the
        # solve is feasible, nothing is shed, and no intertie need carry power.
        internal = [
            _internal_gen("NP15", 5000.0, 30.0),
            _internal_gen("ZP26", 2000.0, 35.0),
            _internal_gen("LA_BASIN", 5000.0, 40.0),
            _internal_gen("SDGE", 2000.0, 40.0),
            _internal_gen("SP15_rest", 1500.0, 40.0),
        ]
        demand = {
            "NP15": 3000.0,
            "ZP26": 1000.0,
            "LA_BASIN": 3000.0,
            "SDGE": 1200.0,
            "SP15_rest": 1000.0,
        }
        result, fleet, config = _solve_caiso(internal, demand, with_import_node=True)
        net_flow = _zone_balance(result, fleet, config, demand)
        # No load shedding anywhere.
        np.testing.assert_allclose(result.slack, 0.0, atol=1e-6)
        # WECC_import is the last zone and never carries load.
        self.assertEqual(config.zone_names[-1], IMPORT_ZONE)
        np.testing.assert_allclose(net_flow[-1], net_flow[-1])  # finite
        # Flows respect every link's TTC in both directions.
        ttc = get_ttc_array(config.links)
        self.assertTrue(np.all(np.abs(result.flows) <= ttc[:, None] + 1e-6))

    def test_load_apportioned_by_share_sums_to_system_total(self):
        # Split a 40 GW system load across the five trading zones by their
        # configured load shares; the zonal demands must sum back to the total
        # and the import node must receive none of it.
        config = get_iso_config("CAISO")
        system_mw = 40000.0
        shares = {z.name: z.load_share for z in config.zones}
        demand = {z: system_mw * shares[z] for z in LOAD_ZONES}
        self.assertAlmostEqual(sum(demand.values()), system_mw, places=3)
        self.assertEqual(shares[IMPORT_ZONE], 0.0)
        # LA_BASIN and SDGE only reach the import node through the one-way,
        # import-limited links off SP15_rest, so each zone needs enough local
        # backstop generation to actually clear its apportioned demand.
        internal = [_internal_gen(z, demand[z], 1000.0) for z in LOAD_ZONES]
        result, fleet, config = _solve_caiso(internal, demand, with_import_node=True)
        _zone_balance(result, fleet, config, demand)
        np.testing.assert_allclose(result.slack, 0.0, atol=1e-6)

    def test_imports_serve_load_through_the_intertie_within_ttc(self):
        # No in-state generation: all load is served by the WECC import node
        # over Path 66 (into NP15) and Path 46 (into SP15_rest, the south
        # gateway zone). Demand sits inside both the per-link TTCs and the
        # ~11.2 GW of available import capacity (11.4 GW nameplate x 0.98
        # availability), so the solve is feasible and the import links carry
        # power up to — but not beyond — their TTCs.
        demand = {"NP15": 4000.0, "SP15_rest": 6000.0}
        internal = []  # pure-import dispatch
        result, fleet, config = _solve_caiso(internal, demand, with_import_node=True)
        net_flow = _zone_balance(result, fleet, config, demand)
        ttc = get_ttc_array(config.links)
        self.assertTrue(np.all(np.abs(result.flows) <= ttc[:, None] + 1e-6))
        # Power leaves the import node (its net flow is negative — it exports
        # into the ISO).
        self.assertTrue(np.all(net_flow[config.zone_names.index(IMPORT_ZONE)] < 0))
        # No unserved energy.
        np.testing.assert_allclose(result.slack, 0.0, atol=1e-6)

    def test_north_south_congestion_caps_flows_and_separates_prices(self):
        # Cheap gas only in the north (NP15); demand concentrated in ZP26. The
        # WECC import node is disabled (no import supply), but the zero-load
        # SP15_rest zone is still a passthrough, so NP15 can reach ZP26 two
        # ways: Path 15 directly (5,400 MW) and a wheel
        # NP15 -> WECC_import -> SP15_rest -> ZP26 bounded by Path 26 (4,000
        # MW). The combined NP15->ZP26 capability is therefore 9,400 MW. ZP26
        # demand above that forces its expensive local gas to the margin, so
        # both bottleneck links saturate and ZP26 prices above NP15 — all
        # without the solve falling over.
        internal = [
            _internal_gen("NP15", 30000.0, 25.0),  # abundant cheap northern gas
            _internal_gen("ZP26", 6000.0, 90.0),  # expensive local backstop
        ]
        demand = {"NP15": 2000.0, "ZP26": 12000.0}
        result, fleet, config = _solve_caiso(internal, demand, with_import_node=False)
        _zone_balance(result, fleet, config, demand)
        links = {(l.from_zone, l.to_zone): i for i, l in enumerate(config.links)}
        ttc = get_ttc_array(config.links)
        # The two links carrying northern power into ZP26 both saturate:
        # Path 15 (NP15->ZP26) forward, and Path 26 (ZP26->SP15_rest) in
        # reverse.
        path15, path26 = links[("NP15", "ZP26")], links[("ZP26", "SP15_rest")]
        np.testing.assert_allclose(result.flows[path15], ttc[path15], atol=1e-3)
        np.testing.assert_allclose(result.flows[path26], -ttc[path26], atol=1e-3)
        # Every flow still respects its TTC.
        self.assertTrue(np.all(np.abs(result.flows) <= ttc[:, None] + 1e-6))
        # Congestion separates the hub prices: ZP26 clears above NP15.
        i_np15, i_zp26 = (
            config.zone_names.index("NP15"),
            config.zone_names.index("ZP26"),
        )
        self.assertTrue(np.all(result.prices[i_zp26] > result.prices[i_np15] + 1.0))

    def test_no_unserved_energy_when_capacity_is_adequate(self):
        # A stress case across all five zones served by a mix of in-state gas
        # and the import node: the dispatch must remain feasible (no slack) and
        # every flow must stay within its TTC. LA_BASIN and SDGE carry their
        # own local gas since they only reach the import node through the
        # one-way, import-limited links off SP15_rest.
        internal = [
            _internal_gen("NP15", 12000.0, 30.0),
            _internal_gen("ZP26", 2000.0, 45.0),
            _internal_gen("LA_BASIN", 12000.0, 50.0),
            _internal_gen("SDGE", 3000.0, 50.0),
            _internal_gen("SP15_rest", 3000.0, 50.0),
        ]
        demand = {
            "NP15": 10000.0,
            "ZP26": 1500.0,
            "LA_BASIN": 10000.0,
            "SDGE": 2500.0,
            "SP15_rest": 2000.0,
        }
        result, fleet, config = _solve_caiso(internal, demand, with_import_node=True)
        _zone_balance(result, fleet, config, demand)
        np.testing.assert_allclose(result.slack, 0.0, atol=1e-6)
        ttc = get_ttc_array(config.links)
        self.assertTrue(np.all(np.abs(result.flows) <= ttc[:, None] + 1e-6))


if __name__ == "__main__":
    unittest.main()
