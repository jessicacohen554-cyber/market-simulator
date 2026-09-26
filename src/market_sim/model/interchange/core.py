"""ISO-agnostic transmission plumbing: incidence/TTC/interface groups + floors.

The network-representation core of the pipe-and-bubble (transportation)
transmission model: the incidence/TTC/interface-group builders that turn a
list of :class:`~market_sim.config.iso_configs.TransferLink` objects into the
``incidence`` / ``ttc`` / flow-group arrays
:func:`~market_sim.model.dispatch.solve_dispatch` accepts, plus the generic
registry-driven reliability-floor engine (:func:`inject_reliability_floor`
and its shared kernels). Moved INTACT from ``model/transmission.py``
(session 3F, refactor-consolidation plan §5 item 6); ``transmission`` remains
the full-surface facade.
"""

import numpy as np
import scipy.sparse as sp

from market_sim.config.plant_taxonomy import artifact_class_array
from market_sim.config.iso_configs import (
    InterfaceLimit,
    TransferLink,
)
from market_sim.data.floor_mechanisms import (
    MECH_RELIABILITY_FLOOR,
    ensure_mechanism,
)


def build_incidence_matrix(
    links: list[TransferLink], zone_names: list[str]
) -> sp.csr_matrix:
    """Return the node-link incidence matrix of the transmission network.

    The result has shape ``(n_zones, n_links)``. For each link the
    ``from_zone`` row entry is ``-1`` (the exporting zone loses power) and
    the ``to_zone`` row entry is ``+1`` (the importing zone gains power).
    A positive link flow therefore moves power from ``from_zone`` to
    ``to_zone``.

    Args:
        links: Transfer links connecting pairs of zones.
        zone_names: Ordered zone names; row index of each zone.

    Returns:
        A CSR incidence matrix of shape ``(n_zones, n_links)``.
    """
    zone_to_idx = {name: i for i, name in enumerate(zone_names)}
    n_zones = len(zone_names)
    n_links = len(links)

    rows = np.empty(2 * n_links, dtype=int)
    cols = np.empty(2 * n_links, dtype=int)
    data = np.empty(2 * n_links, dtype=float)
    for ln, link in enumerate(links):  # ln: transmission link index
        rows[2 * ln] = zone_to_idx[link.from_zone]
        rows[2 * ln + 1] = zone_to_idx[link.to_zone]
        cols[2 * ln] = ln
        cols[2 * ln + 1] = ln
        data[2 * ln] = -1.0  # exporting zone
        data[2 * ln + 1] = 1.0  # importing zone

    return sp.csr_matrix((data, (rows, cols)), shape=(n_zones, n_links))


def get_ttc_array(links: list[TransferLink]) -> np.ndarray:
    """Return the ``(n_links,)`` array of total transfer capabilities in MW."""
    return np.array([link.ttc_mw for link in links], dtype=float)


def build_interface_groups(
    links: list[TransferLink], interface_limits: list[InterfaceLimit]
) -> list[tuple]:
    """Resolve aggregate interface limits to LP flow-column groups.

    Maps each :class:`~market_sim.config.iso_configs.InterfaceLimit`'s
    ``(from_zone, to_zone)`` pair references onto EVERY link joining that zone
    pair: a link whose own from→to matches the listed orientation enters with
    sign ``+1``, a reversed link with ``-1`` — so the group sum reads as the
    net corridor flow in the listed direction (a one-way link pair such as
    MISO's RDT contributes ``flow(a→b) − flow(b→a)`` from one listed pair).
    Returns one ``(link_idx, cap_mw, bidirectional, lower_cap_mw, signs)``
    tuple per limit for :func:`market_sim.model.dispatch.build_constraints`,
    where ``lower_cap_mw`` is the limit's ``reverse_cap_mw`` (``None`` keeps
    the symmetric/one-sided ``bidirectional`` behaviour). Returns an empty
    list when the ISO declares no interface limits (the LP is then identical).
    """
    groups: list[tuple] = []
    for limit in interface_limits:
        idx: list[int] = []
        signs: list[float] = []
        for pair in limit.links:
            a, b = tuple(pair)
            for i, ln in enumerate(links):
                if (ln.from_zone, ln.to_zone) == (a, b):
                    idx.append(i)
                    signs.append(1.0)
                elif (ln.from_zone, ln.to_zone) == (b, a):
                    idx.append(i)
                    signs.append(-1.0)
        lower = None if limit.reverse_cap_mw is None else float(limit.reverse_cap_mw)
        groups.append(
            (
                np.array(idx, dtype=int),
                float(limit.cap_mw),
                bool(limit.bidirectional),
                lower,
                np.array(signs, dtype=float),
            )
        )
    return groups


def get_link_bidirectional_array(links: list[TransferLink]) -> np.ndarray:
    """Return the ``(n_links,)`` bool array of per-link bidirectionality.

    ``True`` (the default) lets a link carry power both ways up to its TTC;
    ``False`` makes it one-way (from->to only, ``0 <= flow <= ttc``), so a
    pair of opposite one-way links can give an interface an asymmetric rating
    (e.g. a tight import limit into a load pocket with a looser export limit).
    Returns all-``True`` when every link is bidirectional (the LP then leaves
    the symmetric ``-ttc <= flow <= ttc`` path byte-identical).
    """
    return np.array(
        [getattr(link, "is_bidirectional", True) for link in links], dtype=bool
    )


def get_link_flow_cost_array(links: list[TransferLink]) -> np.ndarray | None:
    """Return the ``(n_links,)`` per-MWh flow-cost array, or ``None`` if all zero.

    Nonzero entries carry a priced transfer step (MISO's RDT TCDC tiers, see
    :func:`apply_miso_rdt_tcdc`) into the LP objective's flow block. Returning
    ``None`` when every link is free keeps the default cost vector
    byte-identical (the flow block stays zero-cost).
    """
    costs = np.array([getattr(link, "flow_cost", 0.0) for link in links], dtype=float)
    return costs if np.any(costs != 0.0) else None


def _distribute_group_floor(
    fleet_arrays,
    rows,
    frac: np.ndarray,
    hours: int,
    mech_id: int = MECH_RELIABILITY_FLOOR,
) -> None:
    """Floor a plant-group fleet at ``frac`` x available capacity, cheapest-first.

    Shared kernel for :func:`inject_reliability_floor`: sizes the hourly group
    target as ``frac`` x the group's available capacity and distributes it over
    the group's units cheapest-first (by heat rate), each capped at its available
    capacity, composing with any existing ``FleetArrays.min_gen`` floor via
    ``maximum``. ``mech_id`` tags the raised unit-hours for the D-2
    forced-energy attribution (data.floor_mechanisms).
    """
    avail_cap = fleet_arrays.pmax[rows, np.newaxis] * fleet_arrays.availability[rows, :]
    target = frac * avail_cap.sum(axis=0)
    if fleet_arrays.min_gen is None:
        fleet_arrays.min_gen = np.broadcast_to(
            fleet_arrays.pmin[:, np.newaxis], (fleet_arrays.pmin.size, hours)
        ).copy()
    mech = ensure_mechanism(fleet_arrays)
    order = rows[np.argsort(fleet_arrays.heat_rate[rows], kind="stable")]
    remaining = target.copy()
    for r in order:
        cap_r = fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
        take = np.minimum(remaining, cap_r)
        raised = fleet_arrays.min_gen[r, :] < take
        np.maximum(fleet_arrays.min_gen[r, :], take, out=fleet_arrays.min_gen[r, :])
        mech[r, raised] = mech_id
        remaining = remaining - take


# ---------------------------------------------------------------------------
# Generic registry-driven reliability-floor engine
# ---------------------------------------------------------------------------


def _bridge_flagged_runs(flagged: np.ndarray, min_event_hours: int) -> np.ndarray:
    """Extend/merge a boolean hour mask so each flagged run spans ≥ min_event_hours.

    Steam units committed for a temperature event stay online for a minimum run,
    so an isolated flagged calendar day (24 flagged hours) extends forward to
    ``min_event_hours`` and bridges into the next flagged day, merging adjacent
    runs separated by a sub-event gap. Returns a new mask (input unchanged).
    """
    out = np.asarray(flagged, dtype=bool).copy()
    if not out.any() or min_event_hours <= 24:
        return out
    n = out.size
    padded = np.concatenate(([0], out.astype(np.int8), [0]))
    diff = np.diff(padded)
    starts = np.flatnonzero(diff == 1)
    ends = np.flatnonzero(diff == -1)  # exclusive end index into `out`
    for s, e in zip(starts, ends):
        out[s : min(s + min_event_hours, n)] = True
    return out


def inject_reliability_floor(
    fleet_arrays,
    iso: str,
    year: int,
    specs: list,
    zone_names: list[str],
    *,
    demand: np.ndarray | None = None,
    wind_cf: np.ndarray | None = None,
    wind_cap: np.ndarray | None = None,
    solar_cf: np.ndarray | None = None,
    solar_cap: np.ndarray | None = None,
    layup_removed: dict[tuple[int, str], np.ndarray] | None = None,
) -> bool:
    """Apply temperature / net-load reliability-commitment floors from limb specs.

    The single ISO-agnostic floor engine. Each
    :class:`~market_sim.config.iso_configs.ReliabilityFloorSpec` in *specs* is one
    ``(zone, plant_class, driver)`` limb. For each ENABLED limb:

    1. Load the zone's daily weather via
       :func:`~market_sim.data.eia_loader.iso_zone_tmax` (already broadcast to the
       hourly horizon, constant within each calendar day).
    2. Build the day gate and optional sub-daily window:
       ``driver="tmax"`` → flag every hour of a day with ``tmax_c > threshold``;
       ``driver="tmin"`` → ``tmin_c < threshold``;
       ``driver="netload"`` → day's peak net-load (GW) > threshold.
       When ``start_hour``/``end_hour`` are set, only those hours-of-day bind.
    3. For steam classes (``min_event_hours > 24``) bridge an isolated flagged
       day to adjacent flagged days so a committed boiler spans a multi-day event.
    4. Set ``frac = floor_pct`` on flagged hours (0 elsewhere) and select rows
       ``plant_group == plant_class & zone_idx == zone & pmax > 0``.
    5. Distribute the floor into ``FleetArrays.min_gen`` via
       :func:`_distribute_group_floor` (cheapest-first) or pro-rata, composing
       with any existing floor through ``maximum``.

    ``floor_pct`` is ``commit_frac × min_stable_pct`` — a structural commitment
    share times the class's physical minimum-stable level, derived from the
    temperature→commitment relationship only and never tuned to a price/volume
    residual (CLAUDE.md #9/#11; plan §B.3).

    For ``driver="netload"`` limbs the per-zone net-load is computed from exogenous
    scenario drivers — zonal demand MINUS available VRE (wind_cf × wind_cap +
    solar_cf × solar_cap) — NOT endogenous dispatch (avoids circularity). A day is
    flagged when its peak net-load (GW) exceeds the limb threshold; on a flagged
    day the floor binds for all 24 h (same full-day gate as temperature limbs).
    Net-load limbs are skipped when the exogenous inputs are not supplied.

    Enabled limbs sharing a non-empty ``ramp_group`` are instead read as the
    ``(threshold, floor_pct)`` knots of one continuous piecewise-linear
    commitment curve: the floor is interpolated in the driver temperature between
    the knots (clamped flat outside their range) and applied every hour in the
    window, reproducing the legacy ``clip(base + slope×(T−T0), base, cap)`` ramp
    instead of a single step that over-fires on every warm day. Ramp families
    support only the ``tmax``/``tmin`` drivers (see :class:`ReliabilityFloorSpec`).

    *layup_removed* (``ScenarioConfig.reliability_floor_layup_window_mask``,
    NYISO-NEXT) maps ``(plant_code, plant_group)`` to the plant-hour share of
    capacity the merit-order guard measured as ECONOMIC LAY-UP
    (:func:`market_sim.data.outages.unit_layup_removed_fractions`). When given,
    a ``pro_rata`` limb floors each unit on ``pmax x max(0, availability -
    layup_share)`` instead of ``pmax x availability``, so no unit is forced on
    inside a window its own record classifies as laid up (rule 17
    ``[R-FLOOR-WINDOW]``); ``availability`` itself is untouched. A
    ``cheapest_first`` limb is deliberately NOT masked: its zonal target is
    placed on other units, so masking it would relocate forcing rather than
    remove it. ``None`` (the default) is the unmasked basis, byte-identical.

    Modifies *fleet_arrays* in place. Returns ``True`` iff any enabled limb
    floored at least one unit, ``False`` (byte-identical) otherwise.
    """
    if fleet_arrays.plant_group is None:
        return False
    from market_sim.data.eia_loader import iso_zone_tmax

    # Registry limbs name a class FAMILY (``ReliabilityFloorSpec.plant_class``
    # comes from reliability_floor_coeffs_<ISO>.csv, whose coal limbs carry the
    # coal family token): the limb is sized on, and distributed cheapest-first
    # across, the family's aggregate capacity, so a coal limb spans every coal
    # subclass exactly as it spanned the former bare ``COAL`` group (COAL-SUB).
    groups = artifact_class_array(fleet_arrays.plant_group)
    hours = int(fleet_arrays.availability.shape[1])
    applied = False

    def _zone_index(zone: str) -> int | None:
        return next((i for i, z in enumerate(zone_names) if z == zone), None)

    def _apply_frac(spec, z_idx: int, frac: np.ndarray) -> bool:
        """Distribute an hourly ``frac`` floor into ``min_gen`` for one limb.

        Selects the ``(plant_class, zone)`` fleet and composes ``frac × available
        capacity`` into ``FleetArrays.min_gen`` cheapest-first or pro-rata.

        Rows whose ``plant_code`` is in ``spec.exclude_plant_codes`` are dropped
        from the selection first: a persistent-baseline limb is identified on a
        FLEET-aggregate capacity factor but applied per UNIT, so an economically
        laid-up plant (idle in its own metered conduct, yet fully available
        because lay-up is not a forced outage) would otherwise be held at the
        fleet's baseline every hour — rule 17 ``[R-FLOOR-WINDOW]``. The set is
        empty unless the run arms
        ``ScenarioConfig.reliability_floor_plant_exclusions``
        (:func:`~market_sim.config.iso_configs.apply_reliability_floor_plant_exclusions`),
        so disarmed runs are byte-identical.

        Returns ``True`` iff at least one unit was floored.
        """
        if not np.any(frac > 0.0):
            return False
        sel = (
            (groups == spec.plant_class)
            & (fleet_arrays.zone_idx == z_idx)
            & (fleet_arrays.pmax > 0.0)
        )
        excluded = getattr(spec, "exclude_plant_codes", frozenset())
        if excluded:
            sel &= ~np.isin(fleet_arrays.plant_code, list(excluded))
        rows = np.flatnonzero(sel)
        if rows.size == 0:
            return False
        if fleet_arrays.min_gen is None:
            fleet_arrays.min_gen = np.broadcast_to(
                fleet_arrays.pmin[:, np.newaxis],
                (fleet_arrays.pmin.size, hours),
            ).copy()
        if spec.distribution == "cheapest_first":
            _distribute_group_floor(
                fleet_arrays, rows, frac, hours, mech_id=MECH_RELIABILITY_FLOOR
            )
        else:  # pro_rata: each unit floored at frac x its own available capacity
            mech = ensure_mechanism(fleet_arrays)
            for r in rows:
                avail_r = fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
                if layup_removed:
                    # NYISO-NEXT lay-up window mask: drop the capacity the
                    # guard measured as laid up from THIS unit's floor basis
                    # (its own forcing only; nothing is relocated).
                    # Keyed exactly as the outage overlay keys availability:
                    # (plant_code, artifact_class(plant_group)).
                    share = layup_removed.get(
                        (int(fleet_arrays.plant_code[r]), str(groups[r]))
                    )
                    if share is not None:
                        avail_r = fleet_arrays.pmax[r] * np.maximum(
                            fleet_arrays.availability[r, :] - share, 0.0
                        )
                target = frac * avail_r
                raised = fleet_arrays.min_gen[r, :] < target
                np.maximum(
                    fleet_arrays.min_gen[r, :],
                    target,
                    out=fleet_arrays.min_gen[r, :],
                )
                mech[r, raised] = MECH_RELIABILITY_FLOOR
        return True

    # System net-load (demand minus VRE, summed across zones) is computed once
    # and cached here for "netload" limbs, which key off ISO-wide tightness.
    _system_net_load: np.ndarray | None = None
    _have_netload_inputs = (
        demand is not None
        and wind_cf is not None
        and wind_cap is not None
        and solar_cf is not None
        and solar_cap is not None
    )

    # Partition enabled limbs into continuous-ramp families (shared, non-empty
    # ``ramp_group``) and standalone step limbs. A ramp family interpolates its
    # ``(threshold, floor_pct)`` knots into one piecewise-linear commitment curve
    # (see ReliabilityFloorSpec) rather than firing each knot as an independent
    # step; standalone limbs keep the original step-gate semantics below.
    ramp_families: dict[str, list] = {}
    standalone: list = []
    for spec in specs:
        if not getattr(spec, "enabled", True):
            continue
        rg = getattr(spec, "ramp_group", None)
        if rg:
            ramp_families.setdefault(rg, []).append(spec)
        else:
            standalone.append(spec)

    for rg, knots in ramp_families.items():
        head = knots[0]
        if head.driver not in ("tmax", "tmin"):
            continue  # ramps are temperature-only
        z_idx = _zone_index(head.zone)
        if z_idx is None:
            continue
        temp_result = iso_zone_tmax(iso, year, hours, zone=head.zone)
        if temp_result is None:
            continue  # no pinned weather (forecast year / unmapped) → no-op
        tmax, tmin = temp_result
        series = tmax if head.driver == "tmax" else tmin
        if series is None:
            continue
        series = np.asarray(series, dtype=float)
        # np.interp needs strictly-increasing thresholds; ys need not be monotone,
        # so tmin ramps (colder → higher floor) work by encoding descending ys.
        order = np.argsort([k.threshold for k in knots], kind="stable")
        xs = np.array([knots[i].threshold for i in order], dtype=float)
        ys = np.array([knots[i].floor_pct for i in order], dtype=float)
        floor_series = np.interp(series, xs, ys)  # clamps flat outside [xs0, xs-1]
        sh, eh = head.start_hour, head.end_hour
        if sh is not None and eh is not None:
            hod = np.arange(hours) % 24
            floor_series = np.where((hod >= sh) & (hod <= eh), floor_series, 0.0)
        if _apply_frac(head, z_idx, floor_series):
            applied = True

    for spec in standalone:
        z_idx = _zone_index(spec.zone)
        if z_idx is None:
            continue

        driver = spec.driver
        if driver in ("tmax", "tmin"):
            temp_result = iso_zone_tmax(iso, year, hours, zone=spec.zone)
            if temp_result is None:
                continue  # no pinned weather (forecast year / unmapped) → no-op
            tmax, tmin = temp_result
            series = tmax if driver == "tmax" else tmin
            if series is None:
                continue
            series = np.asarray(series, dtype=float)
            if driver == "tmax":
                flagged = series > spec.threshold
            else:
                flagged = series < spec.threshold
        elif driver == "netload":
            if not _have_netload_inputs:
                continue
            # System net-load = sum of (zonal demand - zonal VRE) across all
            # zones. CT commitment is an ISO-level reserve-tightness decision
            # (the system duck-curve neck), so the threshold (GW) is on the
            # system scale — matching the derive-script regression against
            # EIA-930 CISO system demand minus wind minus solar.
            if _system_net_load is None:
                _system_net_load = (
                    demand[:, :hours].sum(axis=0)
                    - (wind_cap[:, None] * wind_cf[:, :hours]).sum(axis=0)
                    - (solar_cap[:, None] * solar_cf[:, :hours]).sum(axis=0)
                )
            n_days = hours // 24
            daily_peak_gw = np.array(
                [
                    _system_net_load[d * 24 : (d + 1) * 24].max() / 1000.0
                    for d in range(n_days)
                ]
            )
            # Basis-consistent threshold: when the CSV carries the derivation
            # percentile, recompute the GW threshold from the engine's own
            # net-load so the flagged-day count tracks model inputs, not the
            # EIA-930 basis the derivation script used.
            threshold_gw = spec.threshold
            tp = getattr(spec, "threshold_percentile", None)
            if tp is not None:
                threshold_gw = float(np.percentile(daily_peak_gw, tp))
            day_flagged = daily_peak_gw > threshold_gw
            flagged = np.repeat(day_flagged, 24)[:hours]
        else:
            continue

        if not np.any(flagged):
            continue

        # Steam event bridging: a committed boiler stays online across a multi-day
        # event, so extend/merge flagged runs to at least min_event_hours.
        if int(getattr(spec, "min_event_hours", 24)) > 24:
            flagged = _bridge_flagged_runs(flagged, int(spec.min_event_hours))

        # Sub-daily hour-of-day window: restrict the floor to start_hour..end_hour.
        sh = getattr(spec, "start_hour", None)
        eh = getattr(spec, "end_hour", None)
        if sh is not None and eh is not None:
            hod = np.arange(hours) % 24
            flagged = flagged & (hod >= sh) & (hod <= eh)

        frac = np.where(flagged, float(spec.floor_pct), 0.0)
        if _apply_frac(spec, z_idx, frac):
            applied = True

    return applied
