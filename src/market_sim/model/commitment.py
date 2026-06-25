"""Startup-cost bid markup and heuristic CC/CT unit commitment.

This module supports the three-solve dispatch calibration architecture:

* :func:`compute_monthly_markup` measures average run lengths per month from
  a base-cost (P0) dispatch and turns them into a monthly startup
  amortization markup (``startup_cost / run_length``). The markup is added to
  base marginal cost to form the *bid* marginal cost used in the P1 solve, so
  clearing prices reflect cycling costs.

* :func:`compute_commitment` screens CC/CT commitment using P1 clearing
  prices against *base* marginal cost (fuel + VOM, no markup). Generators
  earn the clearing price but their actual cost is the base MC, so the margin
  is ``P1_price - base_MC``. A run must clear an IRR hurdle on its startup
  cost to justify a physical start. Margin earned in hours when P1 storage is
  net-charging the zone is discounted, so a cycling unit is not committed
  purely to serve speculative battery-charging load; with the in-merit floor
  active, a deep charging trough also breaks the run outright.

* :func:`apply_commitment_with_coal_pin` zeros the availability of every
  screened generator in its decommitted hours. CAMPD coal is screened
  like CC/CT (its 36-hour minimum run keeps it on through all but the
  longest low-price spells). Legacy coal — the take-or-pay-tranche fleet
  used when ``use_campd_bins=False`` — is never screened: its dispatch is
  pinned to the P1 levels instead.
"""

from __future__ import annotations

import calendar

import numpy as np

from market_sim.config.constants import (
    CC_COMMITMENT_PARAMS,
    CC_STARTUP_PARAMS,
    CT_COMMITMENT_PARAMS,
    CT_STARTUP_PARAMS,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays, Generator


COMMITMENT_PARAMS_BY_FUEL: dict[str, list] = {
    "gas_cc": CC_COMMITMENT_PARAMS,
    "gas_ct": CT_COMMITMENT_PARAMS,
}

STARTUP_PARAMS_BY_FUEL: dict[str, list] = {
    "gas_cc": CC_STARTUP_PARAMS,
    "gas_ct": CT_STARTUP_PARAMS,
}


def find_runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """Return ``(start, end)`` pairs of consecutive ``True`` segments.

    ``end`` is exclusive, so a run spans ``mask[start:end]`` and its length
    is ``end - start``. An all-``False`` mask yields an empty list.
    """
    mask = np.asarray(mask, dtype=bool)
    if mask.size == 0:
        return []
    # Pad with False on both ends so every run has a rising and a falling
    # edge; the diff then marks starts (+1) and ends (-1).
    edges = np.diff(np.concatenate(([0], mask.astype(np.int8), [0])))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)
    return [(int(s), int(e)) for s, e in zip(starts, ends)]


def _merge_runs(
    runs: list[tuple[int, int]], min_down_hours: float
) -> list[tuple[int, int]]:
    """Merge accepted runs whose idle gap is shorter than ``min_down_hours``.

    Bridging a short gap keeps the unit idling at minimum generation rather
    than paying a second startup, so the gap hours become committed too.
    """
    if not runs:
        return []
    runs = sorted(runs)
    merged = [runs[0]]
    for start, end in runs[1:]:
        prev_start, prev_end = merged[-1]
        if start - prev_end < min_down_hours:
            merged[-1] = (prev_start, end)
        else:
            merged.append((start, end))
    return merged


def _commitment_params(gen: Generator, heat_rate: float) -> dict[str, float] | None:
    """Return startup/min-run params for a generator, or ``None`` to skip.

    ``None`` means the generator is never commitment-screened (always
    committed): nuclear and every non-thermal fuel.

    For a CAMPD-bin generator the parameters come straight from the bin
    (``min_run_hours`` / ``min_down_hours`` / ``startup_cost_per_mw``).
    CAMPD coal IS screened — it carries a 36-hour minimum run, so it
    rarely decommits, but an extended low-price spell can still shut it
    down. Only the ``_committed`` tranche of a bin carries the min-run
    window; the ``_econ`` and ``_peak`` tranches carry ``min_run_hours = 0``
    and are never screened directly — the ``_econ`` tranche instead shuts
    down whenever its paired ``_committed`` tranche does (see
    :func:`apply_commitment_with_coal_pin`). For a legacy generator the fuel's parameter
    table is keyed by ascending heat-rate cutoff; the first row whose
    cutoff exceeds ``heat_rate`` applies (legacy coal has no table entry,
    so it stays committed).
    """
    if gen.is_campd_bin:
        if gen.min_run_hours <= 0:
            return None
        return {
            "startup_per_mw": gen.startup_cost_per_mw,
            "min_run_hours": gen.min_run_hours,
            "min_down_hours": gen.min_down_hours,
        }
    table = COMMITMENT_PARAMS_BY_FUEL.get(gen.fuel_type)
    if table is None:
        return None
    for cutoff, params in table:
        if heat_rate < cutoff:
            return params
    return table[-1][1]


def _startup_cost(gen: Generator, heat_rate: float) -> float:
    """Return the ``$/MW`` startup cost for a generator, or ``0`` if none.

    Coal, nuclear and non-thermal fuels get no startup markup. A CAMPD-bin
    generator carries its startup cost on the bin; legacy CC/CT generators
    look it up in a heat-rate-keyed table.
    """
    if gen.is_campd_bin:
        return gen.startup_cost_per_mw
    table = STARTUP_PARAMS_BY_FUEL.get(gen.fuel_type)
    if table is None:
        return 0.0
    for cutoff, cost in table:
        if heat_rate < cutoff:
            return cost
    return table[-1][1]


def _month_bounds(T: int) -> list[tuple[int, int]]:
    """Return ``(start, end)`` hour bounds for each calendar month within ``T``.

    Uses a representative non-leap year (2023) so an 8760-hour horizon maps
    cleanly onto twelve months; a shorter horizon yields fewer bounds.
    """
    bounds: list[tuple[int, int]] = []
    hour = 0
    for month in range(1, 13):
        start = hour
        hour += calendar.monthrange(2023, month)[1] * 24
        if start >= T:
            break
        bounds.append((start, min(hour, T)))
    return bounds


# May-Sep span on the representative non-leap clock (hour indices), for the
# ST_GAS seasonal startup amortization: May starts at 2880h, Oct at 6552h.
_GAS_ST_SEASON: tuple[int, int] = (2880, 6552)


def compute_monthly_markup(
    generators: list[Generator],
    fleet_arrays: FleetArrays,
    dispatch: np.ndarray,
    T: int,
    gas_st_season_spread: bool = False,
    chp_startup_covered: bool = False,
    coal_warm_committed: bool = False,
) -> np.ndarray:
    """Compute the ``(n_gen, T)`` monthly startup-amortization markup.

    For each CC/CT generator, measure the average run length per calendar
    month from the base-cost (P0) ``dispatch`` and amortize the startup cost
    over it: ``markup = startup_cost / avg_run_length``. Longer summer runs
    give a lower per-MWh markup; shorter shoulder-month runs give a higher
    one. A generator counts as running in an hour when its dispatch exceeds
    5% of Pmax. Coal, nuclear and non-thermal fuels get zero markup.

    Args:
        generators: The dispatch fleet, aligned row-for-row with ``dispatch``.
        fleet_arrays: The vectorized fleet, for per-generator heat rate/Pmax.
        dispatch: The P0 dispatch result, shape ``(n_gen, T)``.
        T: Number of hours in the horizon.

    Returns:
        The markup array, shape ``(n_gen, T)``, in ``$/MWh``.
    """
    markup = np.zeros((len(generators), T))
    month_bounds = _month_bounds(T)
    s_lo, s_hi = _GAS_ST_SEASON
    s_lo, s_hi = max(0, s_lo), min(T, s_hi)

    def _amortized(g, h_start, h_end, startup, threshold):
        """Startup / mean run length over ``[h_start, h_end)`` for gen ``g``."""
        runs = find_runs(dispatch[g, h_start:h_end] > threshold)
        avg_run = float(np.mean([end - start for start, end in runs])) if runs else 0.0
        return startup / max(avg_run, 1.0)

    for g, gen in enumerate(generators):
        # A steam-host-obligated cogen never pays a cold start on its own
        # account: the host's steam demand keeps the unit hot (or the start
        # is incurred for steam regardless of the energy market), so its
        # energy bid carries no startup amortization.
        if chp_startup_covered and gen.plant_group in (
            "CC_CHP",
            "CT_CHP",
            "ST_CHP",
        ):
            continue
        # Warm-boiler exemption: a CAMPD coal bin with a must-run floor
        # never goes fully dark — its ``_mustrun`` tranche keeps the boiler
        # online — so dispatching the ``_committed`` tranche is an output
        # ramp on a hot unit, not a cold start. Without this the $100/MW
        # coal start amortized over P0 run lengths prices the committed
        # band ABOVE the econ ramp top (Parish 2024: committed cleared
        # only at LMP >= ~$20 vs econ from ~$13 — the run-97b inversion),
        # turning the design's cheap base band into a near-peak band.
        if (
            coal_warm_committed
            and gen.fuel_type == "coal"
            and getattr(gen, "must_run_pct", 0.0) > 0.0
        ):
            continue
        startup = _startup_cost(gen, float(fleet_arrays.heat_rate[g]))
        if startup == 0.0:
            continue
        threshold = float(fleet_arrays.pmax[g]) * 0.05
        # ST_GAS amortizes its startup over the whole May-Sep season (one
        # seasonal start), so the per-month markup is replaced by a single
        # season-long run length there; other months stay per-month.
        st_spread = gas_st_season_spread and gen.plant_group == "ST_GAS"
        if st_spread and s_hi > s_lo:
            markup[g, s_lo:s_hi] = _amortized(g, s_lo, s_hi, startup, threshold)
        for h_start, h_end in month_bounds:
            if st_spread and h_start >= s_lo and h_end <= s_hi:
                continue  # inside the season window, already handled
            markup[g, h_start:h_end] = _amortized(g, h_start, h_end, startup, threshold)
    return markup


def _storage_commitment_weight(
    n_zones: int,
    T: int,
    storage_charge: np.ndarray | None,
    storage_discharge: np.ndarray | None,
    storage_zone_idx: np.ndarray | None,
    demand: np.ndarray | None,
    weight: float,
) -> np.ndarray:
    """Return the ``(n_zones, T)`` storage discount on the startup hurdle.

    In an hour when storage is *net-charging* a zone, that charging is
    discretionary load that props up the clearing price. A cycling unit
    should not earn full startup-hurdle credit for margin generated in
    such an hour — it would be committing largely to feed a battery. The
    discount is ``1 - weight × net_charge / demand``, clipped to ``[0, 1]``;
    net-*discharge* hours keep weight ``1.0`` because storage and thermal
    are complements at the peak, not substitutes.

    Returns an all-ones array (a no-op) when ``weight`` is zero or any
    storage / demand input is missing.
    """
    ones = np.ones((n_zones, T), dtype=float)
    if (
        weight == 0.0
        or storage_charge is None
        or storage_discharge is None
        or storage_zone_idx is None
        or demand is None
        or len(storage_zone_idx) == 0
    ):
        return ones

    # Aggregate every storage unit's net charge into its zone row.
    net_charge_unit = np.asarray(storage_charge, dtype=float) - np.asarray(
        storage_discharge, dtype=float
    )
    zone_net_charge = np.zeros((n_zones, T), dtype=float)
    np.add.at(zone_net_charge, np.asarray(storage_zone_idx, dtype=int), net_charge_unit)

    # Only net-charging hours discount; net-discharge hours keep weight 1.
    net_charge = np.maximum(zone_net_charge, 0.0)
    denom = np.maximum(np.asarray(demand, dtype=float), 1.0)
    return np.clip(1.0 - weight * net_charge / denom, 0.0, 1.0)


def compute_commitment(
    p1_prices: np.ndarray,  # (n_zones, T) — from the P1 solve
    base_mc: np.ndarray,  # (n_gen, T) — fuel + VOM, NO markup
    generators: list[Generator],  # fleet list aligned with base_mc rows
    fleet_arrays: FleetArrays,  # for zone_idx, heat_rate
    config: ScenarioConfig,
    storage_charge: np.ndarray | None = None,  # (n_storage, T), P1 solve
    storage_discharge: np.ndarray | None = None,  # (n_storage, T), P1 solve
    storage_zone_idx: np.ndarray | None = None,  # (n_storage,)
    demand: np.ndarray | None = None,  # (n_zones, T)
) -> np.ndarray:
    """Return ``(n_gen, T)`` boolean mask: ``True`` = committed.

    For each CC/CT generator:

    1. Compute hourly margin = ``p1_price[zone] - base_mc``. The margin uses
       *base* MC, not bid MC: a generator earns the clearing price but its
       actual cost is fuel + VOM. Using bid MC would double-count the startup
       markup baked into clearing prices and over-decommit.
    2. Find runs of in-merit hours. An hour is in merit when its margin is
       positive *and*, when ``config.commitment_storage_in_merit_floor`` is
       above zero, its storage-charge weight clears that floor. A deep
       battery-charging trough therefore breaks a run in two, so the pieces
       face step 3's min-run filter on their own — a cycling unit is not
       carried through the night purely to charge batteries.
    3. Drop runs shorter than ``min_run_hours``.
    4. Drop runs whose total *storage-weighted* margin is below
       ``startup_per_mw × (1 + IRR)``. The weight discounts margin earned in
       hours when storage is net-charging the zone, so a cycling unit is not
       committed purely to serve speculative battery-charging load (see
       :func:`_storage_commitment_weight`). When the storage inputs are
       omitted, or ``config.commitment_storage_weight`` is zero, the weight
       is ``1.0`` everywhere and step 4 reduces to a plain margin sum.
    5. Merge surviving runs separated by less than ``min_down_hours``.

    Coal, nuclear and non-thermal generators are never screened — they stay
    committed in every hour.

    Args:
        p1_prices: Zonal clearing prices from the P1 solve, ``(n_zones, T)``.
        base_mc: Base marginal cost (fuel + VOM, no markup), ``(n_gen, T)``.
        generators: The dispatch fleet, aligned with ``base_mc`` rows.
        fleet_arrays: The vectorized fleet, for ``zone_idx`` and heat rate.
        config: Scenario configuration supplying ``commitment_irr_hurdle``,
            ``commitment_storage_weight`` and
            ``commitment_storage_in_merit_floor``.
        storage_charge: P1 storage charging power, ``(n_storage, T)``.
        storage_discharge: P1 storage discharging power, ``(n_storage, T)``.
        storage_zone_idx: Zone index of each storage unit, ``(n_storage,)``.
        demand: Zonal demand, ``(n_zones, T)``, the storage-weight denominator.

    Returns:
        The commitment mask, shape ``(n_gen, T)``.
    """
    n_gen, T = base_mc.shape
    n_zones = p1_prices.shape[0]
    irr = config.commitment_irr_hurdle
    in_merit_floor = config.commitment_storage_in_merit_floor
    committed = np.ones((n_gen, T), dtype=bool)

    storage_weight = _storage_commitment_weight(
        n_zones,
        T,
        storage_charge,
        storage_discharge,
        storage_zone_idx,
        demand,
        config.commitment_storage_weight,
    )

    for g, gen in enumerate(generators):
        if gen.fuel_type == "coal" and not config.commitment_screen_coal:
            continue  # coal exempt from the screen — stays committed everywhere
        params = _commitment_params(gen, float(fleet_arrays.heat_rate[g]))
        if params is None:
            continue  # coal, nuclear, non-thermal: always committed

        zone = int(fleet_arrays.zone_idx[g])
        margin = p1_prices[zone, :] - base_mc[g, :]
        weighted_margin = margin * storage_weight[zone, :]
        hurdle = params["startup_per_mw"] * (1.0 + irr)

        # An hour is in merit when its margin is positive; with the floor
        # active, a deep storage-charging trough (weight below the floor)
        # also drops out, breaking the run there.
        in_merit = margin > 0.0
        if in_merit_floor > 0.0:
            in_merit = in_merit & (storage_weight[zone, :] >= in_merit_floor)

        accepted: list[tuple[int, int]] = []
        for start, end in find_runs(in_merit):
            if (end - start) < params["min_run_hours"]:
                continue
            if float(weighted_margin[start:end].sum()) < hurdle:
                continue
            accepted.append((start, end))

        mask = np.zeros(T, dtype=bool)
        for start, end in _merge_runs(accepted, params["min_down_hours"]):
            mask[start:end] = True
        committed[g, :] = mask

    return committed


def reserve_adequacy_commit(
    committed: np.ndarray,  # (n_gen, T) bool — the energy-economic mask
    fleet_arrays: FleetArrays,
    generators: list[Generator],
    spin_eligible: np.ndarray,  # (n_gen,) bool — downstate quick-start units
    requirement_mw: float,
    headroom_frac: float = 1.0,
) -> np.ndarray:
    """Augment a commitment mask with a downstate spinning-reserve adequacy commit.

    Path B of the NYISO downstate-reserve frontier (docs/handoffs/
    nyiso-downstate-reserve-incidence-2026-06.md). :func:`compute_commitment`
    decommits CC/CT on *energy* economics only, so a peaker not needed for energy
    is decommitted and can no longer back synchronised reserve — the reason the
    spinning family never binds and the >$300 tail never fires. This step
    force-commits the cheapest-startup downstate quick-start units, hour by hour,
    until the committed quick-start capacity (``Σ pmax × availability`` over the
    committed, spin-eligible subset) covers ``requirement_mw × headroom_frac``,
    so the LP *can* hold the spinning requirement from genuinely online units.
    Those units then generate at least their pmin (the CT_PEAKER energy the model
    under-runs) and their ``pmax − P`` headroom backs the spinning family, which
    binds — and the RCPF prices a real shortfall — only when even the committed
    downstate fleet is tight. It is the reserve analogue of the ``preserve_min_gen``
    reliability carve-out in :func:`apply_commitment_with_coal_pin`: these units
    run for reserve adequacy, not energy, so the economic screen must not shut
    them off. The committed-headroom target is the MEASURED NYISO spinning
    requirement, never a price-residual fit (CLAUDE.md rule #12).

    Args:
        committed: The energy-economic commitment mask, ``(n_gen, T)``.
        fleet_arrays: The vectorized fleet, for ``pmax`` and ``availability``.
        generators: The dispatch fleet, aligned with ``committed`` rows (for the
            per-unit startup cost that orders the greedy commit).
        spin_eligible: ``(n_gen,)`` boolean — the downstate quick-start units that
            may supply the locational spinning requirement.
        requirement_mw: The spinning reserve requirement (MW).
        headroom_frac: Multiplier on the requirement for the committed-capacity
            target (1.0 = commit until committed pmax covers the requirement).

    Returns:
        A new commitment mask (a copy) with the adequacy commits applied.
    """
    out = committed.copy()
    spin_idx = np.flatnonzero(np.asarray(spin_eligible, dtype=bool))
    if spin_idx.size == 0 or requirement_mw <= 0.0:
        return out
    pmax = np.asarray(fleet_arrays.pmax, dtype=float)
    avail = np.asarray(fleet_arrays.availability, dtype=float)  # (n_gen, T)
    headroom = pmax[:, np.newaxis] * avail  # (n_gen, T) committed-capacity proxy
    target = float(requirement_mw) * float(headroom_frac)

    # Already-committed spin-eligible headroom per hour.
    cum = (headroom[spin_idx, :] * out[spin_idx, :]).sum(axis=0)  # (T,)
    # Greedy: commit cheapest-startup units first into the still-short hours.
    startup = np.array(
        [
            _startup_cost(generators[g], float(fleet_arrays.heat_rate[g]))
            for g in spin_idx
        ]
    )
    for g in spin_idx[np.argsort(startup, kind="stable")]:
        short = cum < target
        if not short.any():
            break
        add = short & (~out[g, :]) & (headroom[g, :] > 0.0)
        if not add.any():
            continue
        out[g, add] = True
        cum[add] += headroom[g, add]
    return out


def apply_commitment_with_coal_pin(
    fleet_arrays: FleetArrays,
    committed: np.ndarray,  # (n_gen, T) boolean
    p1_dispatch: np.ndarray,  # (n_gen, T) from the P1 solve
    generators: list[Generator],  # fleet list aligned with committed rows
    screen_coal: bool = True,
    preserve_min_gen: bool = False,
) -> FleetArrays:
    """Return new ``FleetArrays`` with the commitment screen applied.

    * Screened generators (the ``_committed`` tranche of every CAMPD bin and
      legacy gas CC/CT): availability is zeroed in their decommitted hours,
      so the P2 solve re-optimizes them within the commitment mask.
    * The ``_econ`` tranche of a CAMPD bin is the same physical unit as
      that bin's ``_committed`` tranche, so its availability is zeroed in
      every hour the ``_committed`` tranche is decommitted — the two
      tranches start and stop together.
    * Coal is pinned to reproduce its P1 dispatch (availability ceiling =
      P1 dispatch / Pmax, with a tiny floor) so it gains no new generation
      in P2 — P1 locks coal. This applies to legacy coal always, and to
      CAMPD coal when ``screen_coal`` is False. When ``screen_coal`` is True
      (the default), CAMPD coal is instead commitment-screened like CC/CT.
    * Nuclear, hydro and other unscreened fuels carry an all-committed
      mask, so zeroing decommitted hours is a no-op — they pass through
      unchanged and keep their Pmin (nuclear stays must-run).

    Args:
        fleet_arrays: The P1 vectorized fleet.
        committed: The commitment mask from :func:`compute_commitment`.
        p1_dispatch: The P1 dispatch result, ``(n_gen, T)``.
        generators: The dispatch fleet, aligned with ``committed`` rows.
        screen_coal: When False, CAMPD coal is pinned to its P1 dispatch
            instead of being commitment-screened (it gains no new P2 gen).
        preserve_min_gen: When True, the P1 ``min_gen`` hard floor is carried
            into the P2 fleet and each floored generator-hour's availability is
            raised to cover it, so a reserve / AS-deployment floor
            (``ct_deployment`` / ``reliability_deployment`` overlays) survives
            the *economic* commitment screen rather than being decommitted —
            those units ran for reliability, not economics, so the economic
            screen must not shut them off. Default False reproduces the prior
            behaviour exactly (``min_gen`` dropped in P2), so every non-overlay
            caller — the forecast runner and all other ISOs/keepers — is
            byte-identical.

    Returns:
        A new ``FleetArrays`` with availability adjusted for P2.
    """
    avail = fleet_arrays.availability.copy()

    for g, gen in enumerate(generators):
        # Pin coal to its P1 dispatch — reproducing P1, never gaining new
        # generation in P2 — when it is not commitment-screened: always for
        # legacy coal, and for CAMPD coal when screen_coal is False. The tiny
        # floor avoids a numerical zero.
        pin_to_p1 = gen.fuel_type == "coal" and (
            not gen.is_campd_bin or not screen_coal
        )
        if pin_to_p1:
            p1_frac = np.clip(
                p1_dispatch[g, :] / max(float(fleet_arrays.pmax[g]), 1.0),
                0.0,
                1.0,
            )
            avail[g, :] = np.maximum(p1_frac, 1e-6)
        else:
            avail[g, ~committed[g]] = 0.0

    # Couple each bin's econ tranche(s) to its committed tranche: they are the
    # same physical unit, so the econ tranche shuts down in every hour the
    # committed tranche is decommitted. The commitment screen only ran on
    # the committed tranche (the econ tranche carries min_run_hours = 0). A
    # split economic block emits two econ tranches (``econlo`` / ``econhi``);
    # both couple to the committed tranche, so any suffix starting ``econ``
    # is collected.
    bin_tranches: dict[str, dict[str, object]] = {}
    for g, gen in enumerate(generators):
        if not gen.is_campd_bin:
            continue
        bin_id, _, suffix = gen.unit_id.rpartition("_")
        if suffix == "committed":
            bin_tranches.setdefault(bin_id, {})["committed"] = g
        elif suffix.startswith("econ"):
            bin_tranches.setdefault(bin_id, {}).setdefault("econ", []).append(g)

    for pair in bin_tranches.values():
        c_idx = pair.get("committed")
        e_idxs = pair.get("econ")
        if c_idx is None or not e_idxs:
            continue
        for e_idx in e_idxs:
            avail[e_idx, ~committed[c_idx]] = 0.0

    # Adequacy backstop: the screen and the coal pin must never leave a
    # zone-hour unable to reproduce its P1 thermal output — that would force
    # the P2 solve onto load slack (unserved energy at VOLL), i.e. P2 would
    # create unmet demand. In any zone-hour where the committed available
    # capacity has dropped below the P1 thermal dispatch, restore every
    # decommitted unit in that zone to its P1 availability, so the P1
    # solution stays feasible and P2 can never invent new unmet demand.
    pmax = fleet_arrays.pmax
    zone_idx = fleet_arrays.zone_idx
    p1_frac = np.clip(p1_dispatch / np.maximum(pmax[:, None], 1.0), 0.0, 1.0)
    cap = avail * pmax[:, None]
    for z in np.unique(zone_idx):
        rows = zone_idx == z
        short = cap[rows].sum(axis=0) < p1_dispatch[rows].sum(axis=0) - 1e-6
        if not short.any():
            continue
        sub = avail[rows]
        restore = (sub == 0.0) & (p1_dispatch[rows] > 0.0) & short[None, :]
        sub[restore] = np.maximum(sub[restore], p1_frac[rows][restore])
        avail[rows] = sub

    # Carry the P1 hard floor (min_gen) into P2 when asked: a reserve /
    # AS-deployment floor must survive the economic commitment screen. The LP
    # binds ``min_gen <= P <= pmax * availability``, so wherever a floor is set
    # the screen's ``avail = 0`` in a decommitted hour would make the bound
    # infeasible — raise availability to at least ``min_gen / pmax`` for those
    # floored generator-hours so the floor stays feasible and forces the unit on.
    p2_min_gen = None
    if preserve_min_gen and fleet_arrays.min_gen is not None:
        p2_min_gen = fleet_arrays.min_gen
        pmax_safe = np.maximum(fleet_arrays.pmax, 1.0)[:, None]
        floored = p2_min_gen > 0.0
        if floored.any():
            need = np.clip(p2_min_gen / pmax_safe, 0.0, 1.0)
            avail = np.where(floored, np.maximum(avail, need), avail)

    return FleetArrays(
        pmax=fleet_arrays.pmax,
        pmin=fleet_arrays.pmin.copy(),
        heat_rate=fleet_arrays.heat_rate,
        vom=fleet_arrays.vom,
        emission_rate=fleet_arrays.emission_rate,
        nox_rate=fleet_arrays.nox_rate,
        so2_rate=fleet_arrays.so2_rate,
        zone_idx=fleet_arrays.zone_idx,
        fuel_type_idx=fleet_arrays.fuel_type_idx,
        availability=avail,
        unit_ids=fleet_arrays.unit_ids,
        efficiency_bin=fleet_arrays.efficiency_bin,
        plant_code=fleet_arrays.plant_code,
        min_gen=p2_min_gen,
    )
