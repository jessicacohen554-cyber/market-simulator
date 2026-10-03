"""Demand-basis reconciliation for an armed zonal loss surface (P0→P1 seam).

A zonal loss surface (``miso_/pjm_/caiso_/nyiso_zonal_loss_surface``) splits
each internal link into a one-way pair whose RECEIVING end gains
``(1 - eps[l, t]) * F[l, t]`` while the sender gives up ``F[l, t]``; the
network therefore dissipates ``sum_l eps[l, t] * F[l, t]`` MWh every hour. The
measured demand row (EIA-930 BA demand, ``D = NG - TI``) is generator-side
energy that ALREADY contains every transmission and distribution loss, so the
LP would generate the dissipated energy a second time on top of a
loss-inclusive demand (closeout-PJM-balance FINDING, 2026-10-03: +2.2 to
+4.0 TWh/yr in PJM, matching ``sum eps * F`` to 0.002 TWh).

``zonal_loss_demand_reconciliation`` (default off) nets that dissipation out of
the demand the P1 clearing solve sees, as a one-pass measurement at the P0→P1
seam (rule 10 [R-ONE-PASS], the same seam the three P1 commitment bridges use):
each zone's P1 demand is ``D[z, t]`` minus the dissipation on the lossy links
it RECEIVES, computed from the P0 flows. The ``(1 - eps)`` flow coefficient is
untouched, so the zonal duals keep their measured delivery-factor separation
(rule 4 [R-DUALS]). It is the rule-14 [R-ACCURATE] reconciled form of measured
demand on a boundary the representation does not share (a loss-inclusive
measurement against a loss-dissipating network), with no free scalar
(rule 21 [R-DOF]): every quantity is the solve's own P0 flow times the
measured surface.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp


def receiving_zone_of_links(incidence) -> np.ndarray:
    """Return the receiving zone (the ``+1`` incidence row) of every link.

    Args:
        incidence: Node-link incidence ``(n_zones, n_links)`` (dense or
            sparse); the coefficient of ``Flow`` in each zone's balance.

    Returns:
        ``(n_links,)`` int array — for each link, the row carrying its
        largest (``+1``) coefficient, exactly as
        :func:`market_sim.model.lp.rows` resolves the receiving end when it
        scales that entry to ``1 - link_loss``.
    """
    inc = incidence.toarray() if sp.issparse(incidence) else np.asarray(incidence)
    return np.argmax(np.asarray(inc, dtype=float), axis=0).astype(int)


def zonal_loss_dissipation(flows, incidence, link_loss) -> np.ndarray:
    """Return the per-zone-hour energy the loss surface dissipates, ``(n_zones, T)``.

    ``out[z, t] = sum over lossy links l received by z of link_loss[l, t] *
    max(flows[l, t], 0)`` — the energy that leaves the sender but never reaches
    zone ``z``. Loss entries are only meaningful on one-way links (whose flow is
    floored at 0); the ``max(., 0)`` keeps the quantity a dissipation even if a
    caller passes signed flows.

    Args:
        flows: ``(n_links, T)`` link flows (MW) from a solved pass.
        incidence: Node-link incidence ``(n_zones, n_links)``.
        link_loss: ``(n_links, T)`` receiving-side marginal loss fraction.

    Returns:
        ``(n_zones, T)`` float array of dissipated MW per receiving zone-hour.
    """
    inc = incidence.toarray() if sp.issparse(incidence) else np.asarray(incidence)
    n_zones = inc.shape[0]
    loss = np.asarray(link_loss, dtype=float)
    flow = np.maximum(np.asarray(flows, dtype=float), 0.0)
    per_link = loss * flow  # (n_links, T)
    recv = receiving_zone_of_links(inc)
    out = np.zeros((n_zones, per_link.shape[1]), dtype=float)
    np.add.at(out, recv, per_link)
    return out


def reconcile_loss_demand(demand, flows, incidence, link_loss):
    """Return ``(p1_demand, dissipation)`` for the P1 clearing solve.

    ``p1_demand = demand - zonal_loss_dissipation(flows, ...)``: the measured
    loss-inclusive demand with the network's own modeled dissipation (from the
    P0 flows) netted out on the receiving side, so P1 generation satisfies
    ``generation - export = demand`` up to the P0→P1 flow change.

    Args:
        demand: ``(n_zones, T)`` measured zonal demand (MW).
        flows: ``(n_links, T)`` P0 link flows (MW).
        incidence: Node-link incidence ``(n_zones, n_links)``.
        link_loss: ``(n_links, T)`` receiving-side marginal loss fraction.

    Returns:
        ``(p1_demand, dissipation)``, both ``(n_zones, T)`` float arrays.
    """
    dissipation = zonal_loss_dissipation(flows, incidence, link_loss)
    return np.asarray(demand, dtype=float) - dissipation, dissipation


__all__ = [
    "receiving_zone_of_links",
    "reconcile_loss_demand",
    "zonal_loss_dissipation",
]
