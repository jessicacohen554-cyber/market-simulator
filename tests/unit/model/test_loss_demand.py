"""Trivial-case tests for zonal_loss_demand_reconciliation (closeout-PJM-lossdemand).

2 zones, 1 lossy one-way link A->B, 24 hours (CLAUDE.md testing pattern).
Cheap generation in A serves load in B through a measured marginal loss
``eps``. With the loss surface armed the LP generates ``D / (1 - eps)``: the
dissipation ``eps * F`` is generated on top of a demand that (as measured
EIA-930 demand) already contains it. With the reconciliation on, the P1 demand
nets the P0 dissipation out on the receiving side, so the energy identity
``generation - demand`` closes to zero while the duals keep their
delivery-factor separation.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.iso_configs import TransferLink
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.loss_demand import (
    receiving_zone_of_links,
    reconcile_loss_demand,
    zonal_loss_dissipation,
)
from market_sim.model.transmission import (
    build_incidence_matrix,
    get_link_bidirectional_array,
    get_ttc_array,
)
from market_sim.pipeline.solve import run_energy_solve

T = 24
EPS = 0.04
LOAD_B = 100.0


class _Cfg:
    """Minimal config stub with the fields run_energy_solve reads."""

    hours = T
    gas_st_startup_spread = False
    gas_st_startup_cost = False
    chp_startup_covered = False
    coal_warm_committed = False

    def __init__(self, reconcile: bool):
        self.zonal_loss_demand_reconciliation = reconcile


def _inputs():
    """Cheap A (30 $/MWh) serves B's load over one lossy one-way link."""
    zone_names = ["A", "B"]
    gens = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone=z,
            fuel_type="gas_cc",
            pmax_mw=500.0,
            pmin_mw=0.0,
            eford=0.0,
        )
        for i, z in enumerate(zone_names)
    ]
    fa = generators_to_fleet_arrays(gens, zone_names, hours=T)
    links = [
        TransferLink(from_zone="A", to_zone="B", ttc_mw=1000.0, is_bidirectional=False)
    ]
    demand = np.vstack([np.zeros(T), np.full(T, LOAD_B)])
    mc_base = np.vstack([np.full(T, 30.0), np.full(T, 80.0)])
    dk = dict(
        wind_cf=np.zeros((2, T)),
        wind_cap=np.zeros(2),
        solar_cf=np.zeros((2, T)),
        solar_cap=np.zeros(2),
        incidence=build_incidence_matrix(links, zone_names),
        ttc=get_ttc_array(links),
        link_bidirectional=get_link_bidirectional_array(links),
        link_loss=np.full((1, T), EPS),
        T=T,
    )
    return gens, fa, demand, mc_base, dk


def test_receiving_zone_is_plus_one_row():
    """The receiving end is the +1 incidence row (B for A->B)."""
    inc = np.array([[-1.0, 1.0], [1.0, -1.0]])
    assert receiving_zone_of_links(inc).tolist() == [1, 0]


def test_dissipation_lands_on_receiving_zone_only():
    """eps*max(F, 0) accumulates on the receiving zone; senders get nothing."""
    inc = np.array([[-1.0, -1.0], [1.0, 0.0], [0.0, 1.0]])  # A->B, A->C
    flows = np.array([[100.0, -5.0], [50.0, 50.0]])
    loss = np.array([[0.02, 0.02], [0.1, 0.1]])
    out = zonal_loss_dissipation(flows, inc, loss)
    np.testing.assert_allclose(out[0], 0.0)
    np.testing.assert_allclose(out[1], [2.0, 0.0])  # negative flow clamps to 0
    np.testing.assert_allclose(out[2], [5.0, 5.0])
    p1, diss = reconcile_loss_demand(np.full((3, 2), 10.0), flows, inc, loss)
    np.testing.assert_allclose(p1, 10.0 - diss)


@pytest.mark.parametrize("warm", ["0", "1"])
def test_off_is_double_count_on_closes_identity(monkeypatch, warm):
    """Off: gen - demand = eps*F (the double count). On: it closes to 0."""
    monkeypatch.setenv("MARKET_SIM_WARMSTART", warm)
    gens, fa, demand, mc_base, dk = _inputs()

    off = run_energy_solve(gens, fa, demand, mc_base, dk, _Cfg(False))
    gen_off = off.p1.dispatch.sum(axis=0)
    dissipation_off = EPS * off.p1.flows[0]
    np.testing.assert_allclose(gen_off - demand.sum(axis=0), dissipation_off, atol=1e-6)
    assert dissipation_off.sum() > 0.0
    assert off.loss_demand_netted is None

    on = run_energy_solve(gens, fa, demand, mc_base, dk, _Cfg(True))
    assert on.p1.status == "Optimal"
    assert on.p1_cold  # a changed RHS never rides the warm cost-only re-solve
    gen_on = on.p1.dispatch.sum(axis=0)
    # Energy identity against the MEASURED (loss-inclusive) demand: what is
    # left is exactly eps * (F1 - F0), the P0->P1 flow change — here the
    # second-order -eps^2 D/(1-eps)^2, because netting B's demand also
    # shrinks the flow that dissipates.
    residual_on = gen_on - demand.sum(axis=0)
    np.testing.assert_allclose(
        residual_on, EPS * (on.p1.flows[0] - on.r0.flows[0]), atol=1e-6
    )
    np.testing.assert_allclose(
        residual_on, -(EPS**2) * LOAD_B / (1.0 - EPS) ** 2, atol=1e-6
    )
    assert np.all(np.abs(residual_on) <= EPS / (1.0 - EPS) * dissipation_off + 1e-9)
    np.testing.assert_allclose(
        on.loss_demand_netted[1], EPS * off.r0.flows[0], atol=1e-9
    )
    np.testing.assert_allclose(on.loss_demand_netted[0], 0.0)
    # The duals keep the measured delivery-factor separation (rule 4); the
    # P1 level carries the startup markup, so the RATIO is the invariant.
    np.testing.assert_allclose(
        on.p1.prices[1] / on.p1.prices[0], 1.0 / (1.0 - EPS), rtol=1e-6
    )
    np.testing.assert_allclose(on.p1.prices, off.p1.prices, rtol=1e-9)
    # P0 is untouched: it is the commitment-discovery pass on measured demand.
    np.testing.assert_allclose(on.r0.dispatch, off.r0.dispatch, atol=1e-9)


def test_noop_without_a_loss_surface(monkeypatch):
    """Armed but no link_loss in the kwargs: byte-identical to off."""
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "0")
    gens, fa, demand, mc_base, dk = _inputs()
    dk.pop("link_loss")
    off = run_energy_solve(gens, fa, demand, mc_base, dk, _Cfg(False))
    on = run_energy_solve(gens, fa, demand, mc_base, dk, _Cfg(True))
    assert on.loss_demand_netted is None
    assert np.array_equal(on.p1.dispatch, off.p1.dispatch)
    assert np.array_equal(on.p1.prices, off.p1.prices)


def test_scenario_field_default_off():
    """The registered field exists and defaults off."""
    assert ScenarioConfig().zonal_loss_demand_reconciliation is False
