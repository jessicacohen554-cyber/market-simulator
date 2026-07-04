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
    DA_COMMITMENT_HORIZON_HOURS,
    RA_BRIDGE_ECON_MIN_DOWN_HOURS,
    ST_GAS_COMMITMENT_PARAMS,
    ST_GAS_STARTUP_PARAMS,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays, Generator


COMMITMENT_PARAMS_BY_FUEL: dict[str, list] = {
    "gas_cc": CC_COMMITMENT_PARAMS,
    "gas_ct": CT_COMMITMENT_PARAMS,
    "gas_st": ST_GAS_COMMITMENT_PARAMS,
}

STARTUP_PARAMS_BY_FUEL: dict[str, list] = {
    "gas_cc": CC_STARTUP_PARAMS,
    "gas_ct": CT_STARTUP_PARAMS,
    "gas_st": ST_GAS_STARTUP_PARAMS,
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


def _commitment_params(
    gen: Generator,
    heat_rate: float,
    class_overrides: dict[str, dict] | None = None,
) -> dict[str, float] | None:
    """Return startup/min-run params for a generator, or ``None`` to skip.

    ``None`` means the generator is never commitment-screened (always
    committed): nuclear and every non-thermal fuel.

    *class_overrides* (``ScenarioConfig.class_commitment_overrides``, resolved
    for this run's ISO) maps a ``plant_group`` class (e.g. ``"ST_GAS"``) to
    ``{"min_run_hours"?, "min_down_hours"?}``; when the generator's class
    matches, those keys override the table/bin defaults so a longer steam-gas
    min-run can be enabled per ISO×class without editing the constant table.

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
        base = {
            "startup_per_mw": gen.startup_cost_per_mw,
            "min_run_hours": gen.min_run_hours,
            "min_down_hours": gen.min_down_hours,
        }
    else:
        table = COMMITMENT_PARAMS_BY_FUEL.get(gen.fuel_type)
        if table is None:
            return None
        base = None
        for cutoff, params in table:
            if heat_rate < cutoff:
                base = params
                break
        if base is None:
            base = table[-1][1]

    # Per-ISO×class override (e.g. a longer steam-gas min-run). Copy so the
    # shared constant table dict is never mutated.
    ov = (class_overrides or {}).get(gen.plant_group)
    if ov:
        merged = dict(base)
        for k in ("min_run_hours", "min_down_hours"):
            if k in ov:
                merged[k] = ov[k]
        return merged
    return base


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
    gas_st_startup_cost: bool = False,
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
        # Gas-steam startup amortization is ISO-gated (default OFF, so ERCOT and
        # every other prior keeper stays byte-identical): only when
        # gas_st_startup_cost is set does ST_GAS carry the startup markup that
        # makes a stop-start cost more than idling, so the intermediate steam
        # fleet drags rather than cycling like a peaker.
        if gen.fuel_type == "gas_st" and not gas_st_startup_cost:
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
    as_value: np.ndarray | None = None,  # (n_gen, T) AS revenue estimate
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
       carried through the night purely to charge batteries. When ``as_value``
       is supplied (AS-aware commitment), an hour is ALSO in merit when the unit
       earns positive AS revenue there — a unit ERCOT keeps online *for AS* stays
       committed through hours where its energy margin alone is non-positive.
    3. Drop runs shorter than ``min_run_hours``.
    4. Drop runs whose total *storage-weighted* margin is below
       ``startup_per_mw × (1 + IRR)``. The weight discounts margin earned in
       hours when storage is net-charging the zone, so a cycling unit is not
       committed purely to serve speculative battery-charging load (see
       :func:`_storage_commitment_weight`). When the storage inputs are
       omitted, or ``config.commitment_storage_weight`` is zero, the weight
       is ``1.0`` everywhere and step 4 reduces to a plain margin sum. When
       ``as_value`` is supplied, each hour's AS revenue is ADDED to the
       run's margin total, so a run that is energy-marginal but earns AS revenue
       (the units a tight month keeps online for Reg/RRS/ECRS/NonSpin) clears the
       startup hurdle and stays committed.
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
        as_value: Optional ``(n_gen, T)`` per-unit-hour AS revenue estimate
            (reserve clearing price × reserve-eligible headroom, from the model's
            own P1 balance-row dual — see
            :func:`market_sim.results.scarcity.ercot_as_aware_unit_value`). When
            supplied (AS-aware commitment), AS revenue both keeps a unit in merit
            in its AS-earning hours and counts toward the run's startup-hurdle
            margin. ``None`` (the default) reproduces the energy-only screen
            byte-identically.

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

    class_overrides = getattr(config, "class_commitment_overrides", None)

    for g, gen in enumerate(generators):
        if gen.fuel_type == "coal" and not config.commitment_screen_coal:
            continue  # coal exempt from the screen — stays committed everywhere
        params = _commitment_params(
            gen, float(fleet_arrays.heat_rate[g]), class_overrides
        )
        if params is None:
            continue  # coal, nuclear, non-thermal: always committed

        zone = int(fleet_arrays.zone_idx[g])
        margin = p1_prices[zone, :] - base_mc[g, :]
        weighted_margin = margin * storage_weight[zone, :]
        hurdle = params["startup_per_mw"] * (1.0 + irr)

        # AS-aware: a unit's AS revenue (reserve price × headroom) counts toward
        # both keeping it in merit and clearing the startup hurdle, so the units a
        # tight month keeps online for AS are not decommitted on energy alone.
        av = None if as_value is None else as_value[g, :]
        if av is not None:
            weighted_margin = weighted_margin + av

        # An hour is in merit when its energy margin is positive; with the floor
        # active, a deep storage-charging trough (weight below the floor) also
        # drops out, breaking the run there.
        energy_in_merit = margin > 0.0
        if in_merit_floor > 0.0:
            energy_in_merit = energy_in_merit & (
                storage_weight[zone, :] >= in_merit_floor
            )
        # AS-aware: AS-priced hours join the in-merit mask so a unit's commitment
        # EXTENDS into the reserve-earning hours adjacent to an energy run. The
        # locality filter below then drops any run that is AS-only (no energy
        # hour): a unit running for energy in one window (e.g. the summer peak) is
        # not held online for AS in a DIFFERENT window (e.g. an idle May midday)
        # where the perfect-foresight LP leaves it cold — those cold slow-start
        # hours are exactly the phantom headroom this screen must drop out of the
        # reserve pool, so the co-opt can form the broad-month scarcity.
        in_merit = energy_in_merit
        if av is not None:
            in_merit = energy_in_merit | (av > 0.0)

        accepted: list[tuple[int, int]] = []
        for start, end in find_runs(in_merit):
            # Drop AS-only runs (no energy-in-merit hour) — phantom headroom from
            # a unit not online for energy in this window.
            if av is not None and not energy_in_merit[start:end].any():
                continue
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


def _ra_bridge_unit_params(
    gen: Generator, heat_rate: float
) -> tuple[float, float] | None:
    """Return ``(min_down_hours, startup_per_mw)`` for the RA must-offer bridge.

    The bridge needs a unit's PHYSICAL minimum-down time and per-MW startup cost.
    A legacy per-plant generator gets both from :func:`_commitment_params` (the
    per-fuel heat-rate table). A CAISO per-plant CAMPD **tranche**, however,
    carries ``min_run_hours = min_down_hours = 0`` on its bins (the tranche
    artifact never computed them), so ``_commitment_params`` returns ``None`` and
    the bridge would be silently inert. For such a bin the min-down is instead
    read from the same per-fuel class table by heat rate — a class-physical,
    forward-derivable property, no measured pin — and the startup cost is taken
    from the bin. Only the base (``committed``) tranche carries a startup cost;
    the incremental ``econ``/``peak`` tranches have ``startup_per_mw = 0`` and are
    rejected here (returning ``None``) so the bridge never floors above the
    plant's minimum stable load (which would pad midday gas). Returns ``None``
    when the unit has no class commitment params (a non-thermal fuel) or is a
    binned incremental tranche.
    """
    params = _commitment_params(gen, heat_rate)
    if params is not None and float(params["min_down_hours"]) > 0.0:
        return float(params["min_down_hours"]), float(params["startup_per_mw"])
    # Binned tranche (min-down zeroed on the bin): fall back to the per-fuel
    # class table for the physical min-down.
    table = COMMITMENT_PARAMS_BY_FUEL.get(gen.fuel_type)
    if table is None:
        return None
    base = None
    for cutoff, p in table:
        if heat_rate < cutoff:
            base = p
            break
    if base is None:
        base = table[-1][1]
    min_down = float(base["min_down_hours"])
    if min_down <= 0.0:
        return None
    startup = float(getattr(gen, "startup_cost_per_mw", 0.0))
    # A binned incremental tranche (econ/peak, startup 0) is not a committable
    # base band — never floor it.
    if getattr(gen, "is_campd_bin", False) and startup <= 0.0:
        return None
    if startup <= 0.0:
        startup = float(base["startup_per_mw"])
    return min_down, startup


def _apply_economic_bridges(
    floor: np.ndarray,  # (n_gen, T) — physical bridges already written; mutated
    economic_bridges: list[tuple[int, int, int, float, float, int, float]],
    p1_dispatch: np.ndarray,  # (n_gen, T)
    fleet_arrays: FleetArrays,
    generators: list[Generator],
    min_load_frac: float,
    avail: np.ndarray,  # (n_gen, T)
    pmax: np.ndarray,  # (n_gen,)
    p1_prices: np.ndarray | None,  # (n_zones, T)
    bridge_decommit: bool,
    surplus_floor_value: float,
) -> None:
    """Write the ≥min-down economic bridge floors, decommitting under surplus.

    With ``bridge_decommit`` off every candidate is floored as-is (the caiso-45
    startup bridge, byte-identical). With it on, the over-generation screen of
    :func:`caiso_ra_mustoffer_min_gen` runs first: gap hours where the candidate
    min-load floors exceed the system's dispatchable absorption (P1 import
    dispatch that can back down + unused export-sink capacity, both from the
    model's own P1 solution) reprice the held energy to ``surplus_floor_value``
    (the curtailable-renewable keep-running offer), and bridges whose repriced
    hold cost exceeds the startup they save are decommitted cheapest-startup
    first — the RUC de-commitment order. Each removal shrinks the surplus, so
    the screen is monotone and terminates in one ordered pass.
    """
    if not economic_bridges:
        return
    keep = economic_bridges
    if bridge_decommit:
        n_gen, T = p1_dispatch.shape
        # Hourly dispatchable absorption from the model's own P1 solution:
        # import-tranche dispatch backs down one-for-one, and the export sinks'
        # unused capacity absorbs (both priced-interchange Generator rows,
        # fuel_type "import": imports have pmax>0, export sinks pmin<0 and
        # dispatch ≤ 0). Storage-charge headroom is deliberately EXCLUDED: extra
        # charging midday is energy-capacity-limited (the fleet already fills by
        # the belly in P1), so counting power headroom would overstate
        # absorption; in a real deep-solar spring the marginal surplus MWh is
        # curtailed, not stored.
        fa_pmin = np.asarray(fleet_arrays.pmin, dtype=float)
        is_import = np.array(
            [gen.fuel_type == "import" for gen in generators], dtype=bool
        )
        absorb = np.zeros(T, dtype=float)
        imp_rows = np.flatnonzero(is_import & (pmax > 0.0))
        if imp_rows.size:
            absorb += np.clip(p1_dispatch[imp_rows, :], 0.0, None).sum(axis=0)
        exp_rows = np.flatnonzero(is_import & (fa_pmin < 0.0))
        if exp_rows.size:
            # headroom = capacity − current export = −pmin + dispatch (≤ 0).
            absorb += np.clip(
                -fa_pmin[exp_rows, None] + p1_dispatch[exp_rows, :], 0.0, None
            ).sum(axis=0)
        # Candidate min-load energy per hour: the physical floors already in
        # ``floor`` plus every economic candidate's contribution.
        contrib: list[np.ndarray] = [
            target_mw * avail[g, s:e] for g, s, e, target_mw, *_ in economic_bridges
        ]
        floor_total = floor.sum(axis=0)
        for (g, s, e, *_), c in zip(economic_bridges, contrib):
            floor_total[s:e] += c
        # RUC de-commitment order: the cheapest-to-restart bridges cycle off
        # first (cheapest to bring back next day). Monotone: every decommit
        # shrinks floor_total, which only RAISES the surplus-repriced value the
        # remaining bridges see, so survivors never need re-checking.
        order = sorted(
            range(len(economic_bridges)), key=lambda i: economic_bridges[i][4]
        )
        kept_idx: set[int] = set()
        for i in order:
            g, s, e, target_mw, startup_per_mw, zone, mc_gap = economic_bridges[i]
            gap = e - s
            lmp = p1_prices[zone, s:e]
            over = floor_total[s:e] > absorb[s:e]
            lmp_eff = np.where(over, np.minimum(lmp, surplus_floor_value), lmp)
            hold_cost = (mc_gap - float(np.mean(lmp_eff))) * min_load_frac * gap
            if startup_per_mw > hold_cost:
                kept_idx.add(i)
            else:
                floor_total[s:e] -= contrib[i]
        keep = [economic_bridges[i] for i in sorted(kept_idx)]
    for g, s, e, target_mw, *_ in keep:
        floor[g, s:e] = target_mw * avail[g, s:e]


def caiso_ra_mustoffer_min_gen(
    p1_dispatch: np.ndarray,  # (n_gen, T) — the economic P1 dispatch
    fleet_arrays: FleetArrays,
    generators: list[Generator],  # fleet list aligned with p1_dispatch rows
    min_load_frac: float,
    run_threshold_frac: float = 0.05,
    p1_prices: np.ndarray | None = None,  # (n_zones, T) — the P1 dual (LMP)
    base_mc: np.ndarray | None = None,  # (n_gen, T) — fuel+VOM+CARB MC, no markup
    startup_bridge: bool = False,
    bridge_decommit: bool = False,
    surplus_floor_value: float = 0.0,
) -> np.ndarray:
    """Return the ``(n_gen, T)`` CAISO RA must-offer minimum-load floor.

    Models CAISO's Resource-Adequacy **must-offer** obligation as a real
    *commitment* — not a measured-output pin. A merchant gas CC/CT unit that the
    economic P1 dispatch runs BEFORE *and* AFTER a midday idle gap SHORTER than
    its physical minimum-down time cannot economically cycle off and restart for
    the evening ramp, so it stays online at minimum stable load across the gap.
    For every such "bridge" gap this sets a floor of ``min_load_frac × pmax ×
    availability`` over the gap hours (zero everywhere else), so the unit
    dispatches economically above the floor and DOWN TO minimum load — never to
    zero — through the gap.

    The bridge is detected from the model's OWN run pattern (``p1_dispatch``) and
    the unit's physical minimum-down time (``CC_COMMITMENT_PARAMS`` /
    ``CT_COMMITMENT_PARAMS`` via :func:`_commitment_params`), both
    forward-derivable and condition-responsive — no measured generation enters
    (CLAUDE.md #1/#11). Eligibility is gated on unit PHYSICS, never a class-name
    tuple (audit rule 17): merchant gas CC/CT units (cogens carry their own
    steam-host must-run; gas steamers' thermal inertia is modelled by their own
    drag/startup mechanisms; coal/nuclear/non-thermal are never RA-bridged), and
    the ECONOMIC startup bridge additionally requires ``min_down_hours ≥
    RA_BRIDGE_ECON_MIN_DOWN_HOURS`` (4 h — the CC table's own floor). A
    fast-start CT (min-down 1 h) restarts within the hour, so it is never held
    across a gap longer than its min-down; in practice the floor lands on the
    combined-cycle fleet (``CC_REGULAR``) — the class an energy-only LP
    over-cycles midday.

    The floor replaces the removed measured-NG:NG ``inject_caiso_gas_commitment_
    floor`` slab: instead of pinning the fleet to 0.80 × its measured output, it
    holds genuinely-committed units at min-load and lets the LP set the midday
    level economically. It only binds when oversupply would otherwise drive a
    committed unit cold; the midday ~$0 price must come from real oversupply
    (solar/imports — Lever D), not from this floor.

    **Startup-restart-economics extension** (``startup_bridge``): the plain bridge
    above floors only a gap SHORTER than min-down (a physical restart bar). A real
    unit-commitment keeps a CC online across a gap that is *longer* than min-down
    too, whenever the startup cost it would re-pay to restart for the evening ramp
    exceeds the fuel it saves by cycling off. The LP, ramping a continuous
    variable from zero, pays no startup cost and over-cycles the spring belly. With
    ``startup_bridge`` on, a gap ``≥ min_down`` is ALSO floored when cycling is
    uneconomic per the standard restart inequality::

        startup_per_mw  >  (MC − LMP_gap) × min_load_frac × gap_hours

    The RHS is the *net* cost per MW of capacity of holding at min-load through the
    gap: the min-load energy is not spilled, it displaces the marginal import/gas
    at the gap-hour LMP, so the net cost is ``(MC − LMP)`` per MWh, not full ``MC``.
    When gas is near-marginal (``MC ≈ LMP``) the RHS collapses toward zero and even
    a small startup cost holds the unit online — why real CAISO keeps ~6.8 GW gas
    committed through the deep spring belly. Both ``MC`` (the unit's own marginal
    cost) and ``LMP`` (the model's own P1 dual) are forward-derivable — no measured
    generation enters, so the extension is keeper-eligible (unlike the NG:NG pin).

    **Solar-proportional / seasonal decommitment** (``bridge_decommit``, caiso-48):
    the plain startup bridge over-commits in high-solar years because the P1 LMP
    it prices the gap at is biased HIGH midday — P1 (no floors) is never long, so
    ``MC − LMP ≈ 0`` and *every* gap bridges, in every season, for gaps of any
    length. Two pieces of real unit-commitment physics correct this, both applied
    only to the ≥min-down *economic* bridges (a physical ``gap < min_down`` bridge
    is a restart bar and always holds):

    1. **Day-ahead horizon** — a DAM (IFM/RUC) commits one 24-hour operating day;
       a unit is never held at min-load across a gap longer than one DA cycle
       (``DA_COMMITMENT_HORIZON_HOURS``). A multi-day idle spell is a next-day
       decommit/re-offer decision, so those gaps never bridge. This is the
       *seasonal* decommitment: off-season multi-day idles stop padding gas.
    2. **Over-generation (surplus) repricing + RUC-order decommitment** — the
       restart inequality credits held min-load energy at the gap LMP, which is
       only right while that energy displaces *dispatchable* supply (imports back
       down, the export sink absorbs). Once the candidate floors themselves
       exceed that hourly absorption — ``Σ floors_t > imports_t +
       export_headroom_t``, both from the model's own P1 solution — the marginal
       displaced megawatt-hour is a *curtailable renewable* whose value is the
       negative keep-running offer (``surplus_floor_value``), not the LMP. Gap
       hours in surplus are repriced to that floor and the inequality re-checked;
       uneconomic bridges are decommitted cheapest-startup-first (the RUC
       de-commitment order — cheapest to bring back tomorrow cycles off first),
       each removal shrinking the surplus, until every surviving bridge is
       economic at the surplus-consistent value. The screen is monotone (surplus
       only shrinks, values only rise), so it terminates without iteration to a
       fixed point. This is the *solar-proportional* ramp: deeper solar → less
       import/export absorption headroom → more of the marginal bridged fleet
       decommits, while the spring belly keeps the committed core the system can
       actually absorb.

    Every input is the model's own P1 solution plus physical constants
    (startup cost, min-down, DA horizon, the renewable keep-running offer already
    in the config) — nothing is fitted to a gas or price residual (CLAUDE.md
    #1/#11).

    Args:
        p1_dispatch: The economic P1 dispatch, ``(n_gen, T)``.
        fleet_arrays: The vectorized fleet, for ``pmax``/``availability``/``heat_rate``.
        generators: The dispatch fleet, aligned with ``p1_dispatch`` rows.
        min_load_frac: Minimum stable load as a fraction of available capacity.
        run_threshold_frac: A unit counts as running when its dispatch exceeds
            this fraction of ``pmax`` (matches the markup run detector).
        p1_prices: The P1 clearing prices (LMP duals), ``(n_zones, T)``. Required
            when ``startup_bridge`` is on; used as ``LMP_gap`` in the restart
            inequality.
        base_mc: The base marginal cost (fuel + VOM + CARB, NO startup markup),
            ``(n_gen, T)``. Required when ``startup_bridge`` is on; used as ``MC``
            in the restart inequality.
        startup_bridge: When True, also floor a gap ``≥ min_down`` whose cycle is
            uneconomic per the restart inequality above. Default False reproduces
            the physical-only bridge byte-identically.
        bridge_decommit: When True (requires ``startup_bridge``), bound economic
            bridges to the day-ahead commitment horizon and decommit them in
            RUC order when the gap's surplus-repriced hold cost exceeds the
            startup saved (see above). Default False reproduces the caiso-45
            startup bridge byte-identically.
        surplus_floor_value: $/MWh value of the marginal displaced energy in a
            surplus (over-generation) hour — the curtailable-renewable
            keep-running offer, ``-config.renewable_keep_running_value`` when
            negative renewable offers are on, else 0. Only used when
            ``bridge_decommit`` is on.

    Returns:
        The ``(n_gen, T)`` min-load floor; all-zero (a no-op) when
        ``min_load_frac`` is non-positive.

    Raises:
        ValueError: If ``startup_bridge`` is True but ``p1_prices`` or ``base_mc``
            is None (the restart economics cannot be evaluated).
    """
    n_gen, T = p1_dispatch.shape
    floor = np.zeros((n_gen, T), dtype=float)
    if min_load_frac <= 0.0:
        return floor
    if startup_bridge and (p1_prices is None or base_mc is None):
        raise ValueError(
            "caiso_ra_mustoffer_min_gen: startup_bridge requires both p1_prices "
            "(LMP) and base_mc (MC) to evaluate the restart economics."
        )
    pmax = np.asarray(fleet_arrays.pmax, dtype=float)
    avail = np.asarray(fleet_arrays.availability, dtype=float)
    zone_idx = np.asarray(fleet_arrays.zone_idx)
    # Plant-total pmax for binned units: the floor is the PLANT's minimum stable
    # load (min_load_frac × plant_pmax) applied on its base tranche, never a
    # per-tranche fraction. A plant's tranches share the unit_id prefix (the bin
    # id), matching apply_commitment_with_coal_pin's committed/econ coupling.
    plant_pmax: dict[str, float] = {}
    for g, gen in enumerate(generators):
        if getattr(gen, "is_campd_bin", False):
            key = gen.unit_id.rpartition("_")[0]
            plant_pmax[key] = plant_pmax.get(key, 0.0) + pmax[g]
    # ≥min-down bridges held on restart ECONOMICS (startup_bridge), as
    # (g, start, end, target_mw, startup_per_mw, zone, mc_gap) records — floored
    # after the scan so the bridge_decommit surplus screen sees them all at once.
    economic_bridges: list[tuple[int, int, int, float, float, int, float]] = []
    for g, gen in enumerate(generators):
        # Merchant-gas scope by unit physics, not class names (audit rule 17):
        # cogens (*_CHP) follow their steam host's own floor and are never
        # RA-bridged; gas steamers' multi-day thermal inertia is carried by
        # their own drag/startup mechanisms (one mechanism per phenomenon);
        # coal/nuclear/non-thermal have no gas commitment params.
        if gen.plant_group.endswith("_CHP") or gen.fuel_type not in (
            "gas_cc",
            "gas_ct",
        ):
            continue
        resolved = _ra_bridge_unit_params(gen, float(fleet_arrays.heat_rate[g]))
        if resolved is None:
            continue
        min_down, startup_per_mw = resolved
        # ECONOMIC bridging (holding across a gap ≥ min-down on restart
        # economics) requires slow-restart physics: min-down at/above the CC
        # table floor. A fast-start CT (min-down 1 h, cheap start) is never
        # economically bridged — the real market cycles it off overnight
        # (RA_BRIDGE_ECON_MIN_DOWN_HOURS; audit §1.2c, rule 17).
        econ_eligible = (
            startup_bridge
            and startup_per_mw > 0.0
            and min_down >= RA_BRIDGE_ECON_MIN_DOWN_HOURS
        )
        threshold = pmax[g] * run_threshold_frac
        runs = find_runs(p1_dispatch[g, :] > threshold)
        if len(runs) < 2:
            continue
        # The min-load target is the PLANT's minimum stable load; for a binned
        # base tranche that is min_load_frac × plant_pmax, clipped to the
        # tranche's own capacity (the LP bound). Legacy per-plant units floor
        # min_load_frac × their own pmax (the original behaviour, byte-identical).
        is_bin = getattr(gen, "is_campd_bin", False)
        floor_pmax = (
            plant_pmax.get(gen.unit_id.rpartition("_")[0], pmax[g])
            if is_bin
            else pmax[g]
        )
        target_mw = min(min_load_frac * floor_pmax, pmax[g])
        zone = int(zone_idx[g])
        # Floor every idle gap between two committed runs. A gap SHORTER than the
        # unit's minimum-down time is always bridged (a physical restart bar). A
        # gap AT/OVER min-down is bridged only under startup_bridge when the
        # restart is uneconomic (holding at min-load costs less than re-paying the
        # startup) — the LP-vs-unit-commitment startup-cost gap. Economic bridges
        # are recorded as candidates so the bridge_decommit screen below can
        # reprice and decommit them; physical bridges are floored unconditionally.
        for (_, end_prev), (start_next, _) in zip(runs[:-1], runs[1:]):
            gap = start_next - end_prev
            if gap <= 0:
                continue
            if gap < min_down:
                floor[g, end_prev:start_next] = (
                    target_mw * avail[g, end_prev:start_next]
                )
                continue
            if not econ_eligible:
                continue
            # Day-ahead horizon (bridge_decommit): a DAM commits one 24-hour
            # operating day, so a gap longer than one DA cycle is a next-day
            # decommit/re-offer, never an intra-day min-load hold.
            if bridge_decommit and gap > DA_COMMITMENT_HORIZON_HOURS:
                continue
            # Net $/MW-capacity cost of holding at min-load through the gap:
            # (MC − LMP) × min_load_frac × gap_hours. Averaged over the gap.
            mc_gap = float(np.mean(base_mc[g, end_prev:start_next]))
            lmp_gap = float(np.mean(p1_prices[zone, end_prev:start_next]))
            hold_cost = (mc_gap - lmp_gap) * min_load_frac * gap
            if startup_per_mw > hold_cost:
                economic_bridges.append(
                    (g, end_prev, start_next, target_mw, startup_per_mw, zone, mc_gap)
                )
    _apply_economic_bridges(
        floor,
        economic_bridges,
        p1_dispatch,
        fleet_arrays,
        generators,
        min_load_frac,
        avail,
        pmax,
        p1_prices,
        bridge_decommit,
        surplus_floor_value,
    )
    return floor


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


def as_adequacy_commit(
    committed: np.ndarray,  # (n_gen, T) bool — the AS-aware energy/AS mask
    fleet_arrays: FleetArrays,
    generators: list[Generator],
    headroom_eligible: np.ndarray,  # (n_rows, n_gen) bool — each row's eligible set
    headroom_products: np.ndarray,  # (n_rows, n_prod) bool — products each row bounds
    requirement_mw: np.ndarray,  # (n_prod, T) per-product AS req (MEASURED ASPLANNP433)
    p1_dispatch: np.ndarray,  # (n_gen, T) P1 energy output
    headroom_frac: float = 1.0,
) -> np.ndarray:
    """Re-commit eligible units so each headroom row's online HEADROOM covers its AS.

    The ERCOT analogue of :func:`reserve_adequacy_commit`, the anti-over-fire half
    of AS-aware commitment. :func:`compute_commitment` (AS-aware) decommits the
    cold idle slow-start capacity out of the reserve pool — necessary to make the
    co-opt's shared-headroom constraint bind and form the broad-month scarcity —
    but on its own it strips committed headroom *far below* the procured AS, so the
    co-opt prices a false VOLL-scale shortage.

    The floor is **tier-aware**, mirroring the co-opt's nested shared-headroom rows
    (:func:`~market_sim.config.reserve_config._ercot_multiproduct_design`):
    the *fast* row (RegUp/RRS/ECRS, restricted to the synchronized CC/ST/coal/
    nuclear set) and the *all* row (every product, adding the offline-capable
    quick-start peakers). For each row this commits the cheapest-startup decommitted
    units **from that row's own eligible set**, hour by hour, until the row's
    committed online headroom (``Σ committed (pmax × availability − P1_dispatch)``)
    covers the sum of its products' requirements × ``headroom_frac``. Covering the
    fast row with peakers (which only back Non-Spin) would leave the fast products
    short and pricing at VOLL — the tier restriction prevents exactly that.

    With the floor in place the co-opt can no longer manufacture a shortfall the
    real market would have procured around: the reserve-balance shortfall steps
    (the VOLL-anchored curve) stay unbid in the broad month, and the broad-month
    elevation instead forms from the **shared-headroom dual** — the opportunity
    cost of holding the procured AS on a fleet that is genuinely tight (cap ≈
    energy + reserve), an endogenous LP price, not a curve-level fit. Genuinely
    short hours (the acute days, where even committing every available eligible
    unit cannot reach the requirement) keep their VOLL-curve shortfall price. The
    target is the **MEASURED** AS requirement (``ASPLANNP433``), never a
    price-residual fit (CLAUDE.md #12); ``headroom_frac`` is a coverage multiple on
    that measured quantity, not a tuned price level.

    Args:
        committed: The AS-aware commitment mask, ``(n_gen, T)``.
        fleet_arrays: The vectorized fleet, for ``pmax`` and ``availability``.
        generators: The dispatch fleet, aligned with ``committed`` rows (for the
            per-unit startup cost that orders the greedy commit).
        headroom_eligible: ``(n_rows, n_gen)`` boolean — the eligible generator set
            of each nested headroom row (fast, all).
        headroom_products: ``(n_rows, n_prod)`` boolean — which products each
            headroom row bounds; the row's target is the sum of those products' req.
        requirement_mw: ``(n_prod, T)`` per-product AS requirement (MW).
        p1_dispatch: The P1 energy dispatch, ``(n_gen, T)``. The floor targets
            committed capacity against each row's TOTAL eligible P1 energy plus its
            requirement, so it is robust to the P1->P2 redispatch (a decommitted
            unit's energy shifts onto the committed fleet).
        headroom_frac: Coverage multiple on the measured requirement (1.0 = commit
            until committed capacity covers all eligible energy + the procured AS).

    Returns:
        A new commitment mask (a copy) with the adequacy commits applied.
    """
    out = committed.copy()
    he = np.atleast_2d(np.asarray(headroom_eligible, dtype=bool))  # (n_rows, n_gen)
    hp = np.atleast_2d(np.asarray(headroom_products, dtype=bool))  # (n_rows, n_prod)
    req = np.asarray(requirement_mw, dtype=float)  # (n_prod, T)
    if req.size == 0 or req.max() <= 0.0:
        return out
    pmax = np.asarray(fleet_arrays.pmax, dtype=float)
    avail = np.asarray(fleet_arrays.availability, dtype=float)  # (n_gen, T)
    cap = pmax[:, np.newaxis] * avail  # (n_gen, T) available capacity
    disp = np.asarray(p1_dispatch, dtype=float)  # (n_gen, T)
    # Global cheapest-startup order; each row commits the cheapest units IN ITS set.
    startup = np.array(
        [
            _startup_cost(generators[g], float(fleet_arrays.heat_rate[g]))
            for g in range(len(generators))
        ]
    )
    order = np.argsort(startup, kind="stable")
    # The total responsive thermal energy (across every headroom row's eligible
    # set). When the screen decommits a quick-start peaker that ran for energy in
    # P1, the P2 re-dispatch can shift that energy onto the COMMITTED fast fleet
    # (the fast units back-fill the decommitted peakers). So the worst case for any
    # row is that it must serve the whole responsive energy, not just its own — a
    # per-row energy estimate under-commits the fast row and the co-opt then prices
    # a false VOLL shortfall on the fast products. Target each row's committed
    # capacity against this total responsive energy plus the row's requirement.
    responsive = he.any(axis=0)[:, None]  # (n_gen,1) any-row eligible
    energy_total = (disp * responsive).sum(axis=0)  # (T,)
    # Process the most-restrictive row first (fewest eligible units = the fast
    # row), so its restricted set is satisfied before the looser all row tops up
    # with peakers; a unit committed for one row counts toward every row it is in.
    rows = sorted(range(he.shape[0]), key=lambda h: int(he[h].sum()))
    for h in rows:
        elig_row = he[h][:, None]
        target = energy_total + req[hp[h]].sum(axis=0) * float(headroom_frac)  # (T,)
        if target.max() <= 0.0:
            continue
        cum = (cap * (out & elig_row)).sum(axis=0)  # (T,) committed eligible cap
        for g in order:
            if not he[h, g]:
                continue
            short = cum < target
            if not short.any():
                break
            add = short & (~out[g, :]) & (cap[g, :] > 0.0)
            if not add.any():
                continue
            out[g, add] = True
            cum[add] += cap[g, add]
    return out


def apply_commitment_with_coal_pin(
    fleet_arrays: FleetArrays,
    committed: np.ndarray,  # (n_gen, T) boolean
    p1_dispatch: np.ndarray,  # (n_gen, T) from the P1 solve
    generators: list[Generator],  # fleet list aligned with committed rows
    screen_coal: bool = True,
    preserve_min_gen: bool = False,
    couple_peak: bool = False,
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
        couple_peak: When True, a bin's ``_peak`` tranche is coupled to its
            ``_committed`` tranche exactly like the ``_econ`` tranches: the
            peak (duct-firing / max-pressure) band of a plant whose committed
            tranche is decommitted is the same COLD physical unit, so it can
            neither generate nor hold reserve headroom. Off by default (the
            historical behaviour left idle plants' peak tranches available in
            P2, a residual phantom-reserve source); enabled by the ERCOT
            commitment-state-aware reserve headroom (AS-aware P2).
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
        elif couple_peak and suffix == "peak":
            bin_tranches.setdefault(bin_id, {}).setdefault("peak", []).append(g)

    for pair in bin_tranches.values():
        c_idx = pair.get("committed")
        e_idxs = list(pair.get("econ") or []) + list(pair.get("peak") or [])
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
    p2_min_gen_mech = None
    if preserve_min_gen and fleet_arrays.min_gen is not None:
        p2_min_gen = fleet_arrays.min_gen
        p2_min_gen_mech = getattr(fleet_arrays, "min_gen_mechanism", None)
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
        min_gen_mechanism=p2_min_gen_mech,
    )
