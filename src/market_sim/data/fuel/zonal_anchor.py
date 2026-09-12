"""Solve-year, per-zone identification point of ``gas_offer_net_revenue_margin``.

The ``gas_offer_net_revenue_margin`` mechanism prices a band's markup above its
measured physical basis at a fixed delivered-gas ANCHOR, so that *at
``fuel == anchor`` the reformed offer reduces EXACTLY to the registered band
multiplier* (``scripts/data/derive_gas_offer_margin_anchor.py``). Away from the
anchor the offer moves by ``markup_hr x (anchor - fuel)`` — a linear
extrapolation with no saturation — so the anchor has to be measured on the same
delivered series the priced unit's own fuel is drawn from, on BOTH indices that
series varies over:

* **ZONE** — closed by nyiso-109 / ``gas_offer_margin_zonal_anchor``:
  ``constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE`` resolves the anchor per zone,
  because ``_gas_series`` carries the hub overlay but NOT the per-zone basis,
  which the solve applies afterwards on the ``(n_gen, T)`` array.
* **YEAR** — closed HERE (nyiso-230). Both the ISO table and the zone table are
  means over the FROZEN 2023-2025 training window, so a solve year whose
  delivered gas sits away from that window mean prices its markups at a level
  the band multipliers were never calibrated to carry. The ISO-level half of
  this was already built as ``gas_offer_margin_anchor_vintage`` (pjm-169 F4);
  that flag is mutually exclusive with the zonal one (they re-resolve the SAME
  identification point — rule 19 ``[R-ONE-MECH]``), so an ISO carrying a zonal
  basis had no way to reach the year index at all. This module is the
  composition: the SAME measurement resolved on ``(zone, year)`` instead of on
  ``(zone)`` or ``(year)``.

**ZERO free parameters** (rule 21 ``[R-DOF]``). Nothing here is fitted, chosen
or swept; the formula is the derive's own and only the index it is evaluated on
moves. It is NOT the rule 1 ``[R-STRUCT]`` offer-curve carve-out and does not
touch it — every band multiplier is untouched in every year, and what this
restores is the condition under which those multipliers mean what they were
calibrated to mean.

**Rule 13 ``[R-MEASURED]`` admissible on its own test**: a forecast year's
anchors are the means of that year's own forecast delivered-gas trajectory, per
zone, and they respond when the trajectory moves. No price, residual or actual
dispatch is read.

**Rule 1(b) is not engaged**: the config is one boolean and one formula
identical in every year; the quantity that varies is a measured fuel level, the
same class of object as ``gas_prices`` itself.

The construction mirrors ``derive_gas_offer_margin_anchor.derive_zonal_anchors``
exactly for the non-capacity-weighted ISOs (NYISO today): the applier keys only
on ``fuel_type_idx`` and ``zone_idx``, so one synthetic gas row per zone
measures its transform precisely as the solve applies it.
``tests/unit/data/test_gas_offer_zonal_anchor_vintage.py`` pins the identity —
averaging this function's per-year output over the 2023-2025 training window
reproduces the registered ``GAS_OFFER_MARGIN_ANCHOR_BY_ZONE`` table — so the
runtime resolution and the frozen derive cannot drift apart silently.
"""

from __future__ import annotations

import numpy as np

__all__ = ["CAPACITY_WEIGHTED_ZONAL_ISOS", "zonal_gas_anchors_for_year"]

#: ISOs whose zonal-basis applier re-centres on the GAS-CAPACITY-weighted fleet
#: mean, so its transform depends on the solve's own per-zone gas capacity and a
#: synthetic one-row-per-zone probe would measure the wrong thing. Mirrors
#: ``derive_gas_offer_margin_anchor.CAPWEIGHTED_ZONAL_ISOS``; these ISOs are
#: rejected here rather than silently mis-measured, and reaching one is a build
#: task (resolve against the year's real fleet), not a fallback.
CAPACITY_WEIGHTED_ZONAL_ISOS: frozenset[str] = frozenset({"PJM", "ERCOT", "MISO"})


def zonal_gas_anchors_for_year(config, year: int, hours: int) -> dict[str, float]:
    """Return ``{zone: mean delivered gas $/MMBtu}`` for one solve year.

    Parameters
    ----------
    config:
        The run's OWN :class:`~market_sim.config.scenarios.ScenarioConfig`, with
        the hub-overlay and monthly-actuals postures already applied. Passing a
        config whose gas flags are not yet set measures a series no unit ever
        pays — the caller is responsible for the ordering, exactly as
        ``gas_offer_margin_anchor_vintage`` is (see the placement comment in
        ``scripts/run_calibration.run_year``).
    year:
        The year the LP is about to solve.
    hours:
        The solve's hour count, so the mean is taken over the same horizon the
        LP prices.

    Returns
    -------
    dict[str, float]
        One entry per zone of ``config.iso``, in the ISO's own zone order.

    Raises
    ------
    ValueError
        If the ISO has no registered zonal-basis applier (there is no zonal
        anchor to resolve, and rule 25 ``[R-ISO-SCOPE]`` forbids borrowing
        another ISO's), or if it is capacity-weighted (see
        :data:`CAPACITY_WEIGHTED_ZONAL_ISOS`).
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import FleetArrays
    from market_sim.data.fuel._shared import _GAS_FUEL_IDX
    from market_sim.data.fuel.basis import ZONAL_BASIS_APPLIERS
    from market_sim.data.fuel.trajectories import _gas_series

    iso = (getattr(config, "iso", "") or "").upper()
    if iso not in ZONAL_BASIS_APPLIERS:
        raise ValueError(
            f"{iso}: no per-zone delivered-gas basis applier is registered, so "
            "there is no zonal anchor to resolve — its single anchor is "
            "already identified at the grain its units' fuel is drawn at "
            "(rule 25 [R-ISO-SCOPE]: never transfer another ISO's zone table)"
        )
    if iso in CAPACITY_WEIGHTED_ZONAL_ISOS:
        raise ValueError(
            f"{iso}: its zonal-basis applier re-centres on the GAS-CAPACITY-"
            "weighted fleet mean, so the transform depends on the solve's own "
            "fleet and a synthetic one-row-per-zone probe would measure the "
            "wrong level. Resolving the vintage zonal anchor for this ISO "
            "needs the year's real fleet and is a build task, not a fallback."
        )

    zone_names = list(get_iso_config(iso).zone_names)
    n = len(zone_names)
    series = np.asarray(_gas_series(config, year, hours), dtype=float)
    # z=zone: one synthetic gas row per zone. The applier keys only on
    # ``fuel_type_idx`` and ``zone_idx``, so this measures its transform
    # exactly as the solve applies it to the real (n_gen, T) array.
    prices = np.repeat(series[None, :], n, axis=0)
    fleet = FleetArrays(
        pmax=np.ones(n),
        pmin=np.zeros(n),
        heat_rate=np.full(n, 7.0),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.arange(n),
        fuel_type_idx=np.full(n, int(sorted(_GAS_FUEL_IDX)[0])),
        availability=np.ones((n, int(hours))),
        unit_ids=[f"probe_{z}" for z in zone_names],
        efficiency_bin=np.zeros(n, dtype=int),
        plant_code=np.zeros(n, dtype=int),
    )
    ZONAL_BASIS_APPLIERS[iso](prices, fleet, config, year)
    return {zone: float(np.nanmean(prices[i])) for i, zone in enumerate(zone_names)}
