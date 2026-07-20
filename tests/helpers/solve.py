"""``solve_tiny`` — the trivial-case LP driver for tests.

CLAUDE.md's testing pattern is "always test with trivial cases first: 1 gen,
1 zone, 24 hours". Dozens of tests reimplement the boilerplate around that
call: build the zero-renewable arrays, assemble incidence/TTC from a link list,
shape ``mc`` and ``demand``. :func:`solve_tiny` wraps exactly that assembly so a
test writes the interesting inputs and nothing else.

It is a thin, transparent wrapper over
:func:`market_sim.model.dispatch.solve_dispatch` — every extra keyword passes
straight through, so anything ``solve_dispatch`` accepts (reserve co-opt,
storage, interface groups, ...) still works.
"""

from __future__ import annotations

import numpy as np

from market_sim.data.fleet import FleetArrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.model.transmission import build_incidence_matrix, get_ttc_array


def solve_tiny(
    fleet: FleetArrays,
    demand_by_zone,
    zone_names=None,
    *,
    hours: int = 24,
    mc=None,
    links=None,
    **kwargs,
):
    """Solve a trivial dispatch LP and return the :class:`DispatchResult`.

    Args:
        fleet: The :class:`FleetArrays` (e.g. from
            :func:`tests.helpers.builders.make_fleet`). Its ``availability``
            already carries the EFORd derate — no extra assembly needed.
        demand_by_zone: Either a ``{zone_name: demand}`` mapping (each value a
            scalar held flat across the horizon or a length-``hours`` array) or
            a ``(n_zones, hours)`` array. The mapping form also fixes the zone
            axis order when ``zone_names`` is omitted.
        zone_names: Explicit zone axis. Defaults to the mapping keys, or
            ``["Z0", "Z1", ...]`` for the array form.
        hours: Dispatch horizon T (24 for the trivial case).
        mc: Marginal-cost array. ``None`` → flat ``$20/MWh`` for every gen; a
            scalar → that flat price; a length-``n_gen`` vector → tiled across
            the horizon; otherwise passed through as ``(n_gen, hours)``.
        links: Optional ``list[TransferLink]``; when given, the incidence
            matrix and TTC array are built from it and threaded in (unless the
            caller already passed ``incidence``/``ttc`` explicitly).
        **kwargs: Forwarded verbatim to ``solve_dispatch`` (renewable arrays
            override the zero defaults; storage/reserve/interface kwargs work).

    Returns:
        The ``solve_dispatch`` result (``.prices``, ``.dispatch``, ...).
    """
    T = hours
    n_gen = int(len(fleet.pmax))

    if hasattr(demand_by_zone, "items"):
        if zone_names is None:
            zone_names = list(demand_by_zone.keys())
        demand = np.zeros((len(zone_names), T))
        for zi, z in enumerate(zone_names):
            demand[zi, :] = demand_by_zone[z]
    else:
        demand = np.asarray(demand_by_zone, dtype=float)
        if demand.ndim == 1:
            demand = demand.reshape(1, T)
        if zone_names is None:
            zone_names = [f"Z{z}" for z in range(demand.shape[0])]

    n_zones = len(zone_names)

    if mc is None:
        mc = np.full((n_gen, T), 20.0)
    else:
        mc = np.asarray(mc, dtype=float)
        if mc.ndim == 0:
            mc = np.full((n_gen, T), float(mc))
        elif mc.ndim == 1:
            mc = np.tile(mc.reshape(-1, 1), (1, T))

    renewables = {
        "wind_cf": np.zeros((n_zones, T)),
        "wind_cap": np.zeros(n_zones),
        "solar_cf": np.zeros((n_zones, T)),
        "solar_cap": np.zeros(n_zones),
    }
    for key in list(renewables):
        if key in kwargs:
            renewables[key] = kwargs.pop(key)

    if links:
        kwargs.setdefault("incidence", build_incidence_matrix(links, zone_names))
        kwargs.setdefault("ttc", get_ttc_array(links))

    return solve_dispatch(fleet, demand, mc=mc, T=T, **renewables, **kwargs)
