"""Net-load reliability / drag floors and cold-snap derates (min-gen scaffolding).

Split out of ``data/fleet.py`` (11,199 ln) into the ``data/fleet`` package
(refactor-consolidation plan §5 item 8, 2026-07-23) as pure code motion:
every moved body is byte-identical; only this header and the census'd
``_pkg_ns()`` call-site routings are new. The package ``__init__`` re-exports
the full pre-split surface; patch semantics are preserved via
:func:`market_sim.data.fleet.models._pkg_ns`.
"""

from __future__ import annotations

import json
import logging
import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.floor_mechanisms import (
    MECH_CT_NETLOAD_DRAG,
    MECH_ST_NETLOAD_DRAG,
    ensure_mechanism,
)
from market_sim.config.constants import ST_GAS_COMMITMENT_PARAMS
from market_sim.data.outages import ST_GAS_PEAKER_PLANTS
from pathlib import Path
from market_sim.data.fleet.models import FleetArrays, Generator

# Pre-split logger name: records keep the historical module path.
logger = logging.getLogger("market_sim.data.fleet")


def _netload_drag_tranche_rank(unit_id: str) -> int:
    """Return a tranche's commitment rank: 0 must-run, 1 committed, 2 economic.

    The fill order for :func:`_netload_drag_merit_targets`. A plant's commitment
    block is its contracted (``mustrun``) and measured minimum-stable-load
    (``committed``, including the ``committed1``/``committed2``.. ramp slices)
    tranches; everything below the excluded ``peak`` band is economic capacity a
    plant only reaches once it is already synchronized. Ranking the blocks ahead
    of every economic tranche is what makes the fill a COMMITMENT stack: units
    are committed cheapest-first at minimum load, and only once the whole class
    is committed does the mandate push anyone above it.
    """
    suffix = unit_id.rpartition("_")[2]
    if suffix.startswith("mustrun"):
        return 0
    if suffix.startswith("committed"):
        return 1
    return 2


def _netload_drag_merit_targets(
    rows: list[int],
    generators: list[Generator],
    pmax: np.ndarray,
    basis: dict[int, np.ndarray],
    floor_frac: np.ndarray,
) -> dict[int, np.ndarray]:
    """Fill the class's mandated drag MW cheapest-first instead of pro-rata.

    The ``merit_allocation`` limb of :func:`apply_netload_reliability_floor`
    (ercot-259). The mandate for hour ``t`` is the MW the pro-rata path actually
    DELIVERS that hour, ``sum_g min(floor_frac[t], basis[g][t]) x pmax[g]`` over
    exactly the same ``rows`` — **the hourly aggregate is preserved by
    construction**, and only its distribution changes. It is deliberately NOT
    the nominal ``floor_frac[t] x sum(pmax)``: the pro-rata path clips every row
    at its own eligible capacity and drops the shortfall, so the nominal figure
    overstates what it puts on the system by 20-40 % on the real ERCOT fleet
    (2021: 5.7671 TWh delivered against 7.1171 nominal), and targeting it would
    fold a LEVEL change into an ALLOCATION swap.

    Rows are filled in ``(commitment rank, bid heat rate, unit_id)`` order:
    every plant's commitment block before any economic tranche
    (:func:`_netload_drag_tranche_rank`), cheapest plant first within a rank,
    unit id breaking ties so the order is deterministic. Each row absorbs up to
    its own eligible capacity ``basis[g] x pmax[g]`` — the availability- and
    lay-up-net basis the caller already built — and the marginal row takes the
    remainder. A row past the fill point gets a zero target, i.e. no floor at
    all, which is the point: the expensive, least-committed plants stop being
    forced.

    Heat rate is the merit signal because every unit in a reliability-drag class
    burns the same fuel, so the tranche bid heat rate IS the cost ordering up to
    a common fuel price. Its measured weakness is recorded rather than tuned
    around: Spearman(heat rate, CAMPD online fraction) over the ERCOT ST_GAS
    fleet is -0.714 / -0.833 / -0.690 in 2021/2023/2024 but only -0.286
    (p = 0.49) in 2025, where R W Miller -- the most expensive plant in the
    fleet -- ran 88.0 % of hours. Cost order is right in three of four years and
    materially wrong in one (owner ruling 2026-09-08 selected it over a measured
    pooled online-fraction ordering, which the same measurement shows is not
    year-stable either).

    Args:
        rows: Indices of the class's non-``peak`` tranches, the caller's own
            row set -- also the denominator of the preserved aggregate.
        generators: The dispatch fleet, aligned row-for-row with ``pmax``.
        pmax: Per-row nameplate capacity, shape ``(n_gen,)``.
        basis: ``{row: (T,) eligible-capacity FRACTION}``, availability net of
            any measured lay-up share, as built by the caller.
        floor_frac: The driver curve's per-hour fleet capacity factor, ``(T,)``.

    Returns:
        ``{row: (T,) min-gen target MW}`` for every filled row. Rows that the
        fill never reaches are absent (no floor), and an empty dict means the
        class has no rows at all.
    """
    if not rows:
        return {}
    # The SAME hourly aggregate the pro-rata path actually DELIVERS (T,).
    # Not ``floor_frac x sum(pmax)``: the pro-rata path clips each row at its own
    # eligible capacity (``min(floor_frac, basis_g) x pmax_g``) and simply drops
    # the shortfall wherever a plant is out or laid up, so the nominal mandate
    # overstates what it puts on the system by 20-40 % on the real ERCOT fleet
    # (2021: 5.7671 TWh delivered against a 7.1171 TWh nominal). Targeting the
    # nominal figure would make this a LEVEL change as well as an allocation
    # one -- two mechanisms on one gate (rule 19 [R-ONE-MECH]) and an
    # unfalsifiable A/B. Matching the delivered figure hour by hour makes the
    # swap provably aggregate-neutral, so the ONLY thing that changes is WHICH
    # plants carry the mandate -- exactly the diagnosed defect and nothing else.
    target_mw = np.zeros_like(floor_frac, dtype=float)
    for g in rows:
        target_mw += np.minimum(floor_frac, basis[g]) * float(pmax[g])
    if not float(target_mw.max()) > 0.0:
        return {}
    order = sorted(
        rows,
        key=lambda g: (
            _netload_drag_tranche_rank(str(generators[g].unit_id)),
            float(generators[g].heat_rate),
            str(generators[g].unit_id),
        ),
    )
    # (n, T) eligible MW per row, then a vectorized cumulative fill: no Python
    # loop over hours anywhere (rule 2 [R-VECTOR]).
    block = np.stack([basis[g] * float(pmax[g]) for g in order])
    filled_below = np.cumsum(block, axis=0) - block
    take = np.clip(target_mw[np.newaxis, :] - filled_below, 0.0, block)
    return {g: take[i] for i, g in enumerate(order) if float(take[i].max()) > 0.0}


def _circular_centred_mean(x: np.ndarray, window: int) -> np.ndarray:
    """Return the centred circular moving average of ``x`` over ``window`` hours.

    Circular because the LP's 8760 clock is cyclic (the convention the storage
    SOC boundary already uses), so the transform needs no edge rule and no
    calendar. Centred so it is MEAN-PRESERVING: ``result.mean() == x.mean()``
    to floating-point, which is what makes the pjm-177 persistence swap a
    reallocation of the drag's mandate in time rather than a level knob.

    Args:
        x: The hourly series, shape ``(T,)``.
        window: Averaging length in hours (``2 <= window < T``).

    Returns:
        The smoothed series, shape ``(T,)``.
    """
    w = int(window)
    kernel = np.ones(w, dtype=float) / float(w)
    # Wrap enough of each end to make the convolution exactly circular.
    pad = w
    wrapped = np.concatenate((x[-pad:], x, x[:pad]))
    smoothed = np.convolve(wrapped, kernel, mode="same")
    return smoothed[pad : pad + x.size]


def _min_run_hours(
    generator: "Generator", table: "list[tuple[float, dict[str, float]]]"
) -> int:
    """Return a generator's minimum run length from a commitment-params table.

    The identical heat-rate lookup ``model.commitment._commitment_params``
    performs for a legacy generator: the table is keyed by ascending heat-rate
    cutoff and the first row whose cutoff exceeds the generator's heat rate
    applies, with the last row as the fallback. Deliberately NOT
    ``generator.min_run_hours`` — a CAMPD-binned fleet carries ``0`` on every
    tranche (which is why ``ScenarioConfig.class_commitment_overrides``
    exists), so the frozen table is the only zero-DOF source (rule 21 [R-DOF]).

    Args:
        generator: The dispatch-fleet row.
        table: A ``*_COMMITMENT_PARAMS`` table from ``config.constants``.

    Returns:
        The minimum run length in hours (``0`` when the table carries none).
    """
    heat_rate = float(getattr(generator, "heat_rate", 0.0) or 0.0)
    params = table[-1][1]
    for cutoff, entry in table:
        if heat_rate < cutoff:
            params = entry
            break
    return int(params.get("min_run_hours", 0) or 0)


def apply_netload_reliability_floor(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    net_load_mw: np.ndarray,
    *,
    plant_group: str,
    slope: "float | np.ndarray",
    intercept: "float | np.ndarray",
    cap: "float | np.ndarray",
    ramp_window: tuple[int, int] | None = None,
    exclude_plant_codes: frozenset[int] = frozenset(),
    mech_id: int = MECH_CT_NETLOAD_DRAG,
    layup_removed: dict[tuple[int, str], np.ndarray] | None = None,
    merit_allocation: bool = False,
    persist_params: "list[tuple[float, dict[str, float]]] | None" = None,
) -> bool:
    """Impose a net-load-indexed reliability-commitment min-gen floor on a class.

    The shared engine behind the per-class ERCOT reliability-drag floors
    (:func:`apply_gas_st_netload_drag_floor`, :func:`apply_ct_netload_drag_floor`)
    — the endogenous, weather-driven replacement for a fixed seasonal must-run
    fraction or an actuals pin. ERCOT commits these out-of-merit thermal units
    at minimum load for local/system reliability (RUC/RMR); the held fraction is
    not a calendar season but rises with system **net-load** (``load - wind -
    solar``), the operational proxy for the reserve tightness RUC keys off. Each
    non-``_peak`` tranche of ``plant_group`` (the economic ``_peak`` scarcity
    band runs purely on price) whose plant is not in ``exclude_plant_codes`` gets
    a per-hour minimum-generation floor of
    ``clip(slope*netload_GW + intercept, 0, cap) x pmax``, capped at available
    capacity and composed with any existing floor via ``maximum``; the LP
    dispatches economically *above* it. ``slope``/``intercept``/``cap`` may
    each be a scalar (one curve, the pooled derive) or a per-hour ``(T,)``
    array (a calendar-conditioned curve, e.g. the season-resolved ERCOT
    ST_GAS grain fix) — the clip is element-wise either way.

    ``ramp_window=(start, end)`` gates the floor to the local-standard
    hour-of-day window ``[start, end)`` (``hour t -> t % 24`` on the model's
    8760 clock), zeroing it elsewhere — used for resources that serve
    reliability only in a diurnal window (CT peakers in the afternoon-evening
    net-load ramp), where ``None`` applies the floor every hour (the all-hours
    gas-steam boiler). Because both the trigger (net-load) and the magnitude
    (physical min-gen) are forward-derivable and condition-responsive, the
    mechanism is admissible in both backcast and forecast (CLAUDE.md #10/#11).

    ``layup_removed`` (``config.netload_drag_layup_window_mask``, ercot-256) is
    the measured ECONOMIC-LAY-UP share per ``(plant_code, plant_group)`` and
    hour from :func:`market_sim.data.outages.unit_layup_removed_fractions`. When
    supplied, the clip basis becomes ``pmax x max(0, availability -
    layup_share)`` for a plant that carries a series — the hours the merit-order
    guard adjudicated as not-operating lose their floor exactly as measured
    OUTAGE hours already do under the plain ``pmax x availability`` clip.
    Availability itself is never touched (an economically idle unit stays
    available to the LP's own economics); only the FORCING is confined. ``None``
    (or a plant with no series) is byte-identical to the un-masked clip.

    ``merit_allocation`` (``config.netload_drag_merit_allocation``, ercot-259)
    replaces the ALLOCATION of the same mandated MW, and nothing else — same
    driver curve, same hourly aggregate, same ``mech_id``, no second floor
    (rule 19 [R-ONE-MECH], the ``st_gas_mustrun_level_p25`` pattern: only the
    level source changes). ``floor_frac`` is a FLEET capacity factor, so
    spreading it across every plant's ``pmax`` asserts that every plant is
    committed at that fraction in every hour — physically it is below any
    boiler's minimum stable level, and it over-forces the least-committed plant
    while under-forcing the workhorse. Measured on the ERCOT keeper's own
    committed D-4 conduct rows, the plant convicted of being floored while its
    meter reads zero is that year's LEAST-committed plant in all five scored
    years (3452 in 2021/2022/2023, 3491 in 2024/2025), and in 2021 the uniform
    floor holds Lake Hubbard at 1.22 TWh against 0.36 TWh measured (3.4x over)
    while holding V H Braunig at 1.50 against 3.72 (0.40x under). When True the
    same hourly fleet target ``floor_frac x sum(pmax)`` is instead FILLED
    cheapest-first across the class's own tranches — commitment blocks
    (``mustrun``, then ``committed``) before any economic tranche, ascending
    bid heat rate within a rank — so the merit order decides WHICH units are
    committed and each carries a physically-meaningful block. The target is the
    pro-rata path's own DELIVERED MW hour by hour, not the nominal
    ``floor_frac x sum(pmax)``, so the swap is provably aggregate-neutral and
    cannot double as a level knob. Zero free
    parameters: the block sizes are the frozen binning artifact's existing
    tranche capacities and the order is the fleet's own heat rates (rules
    21/23). The floor stays a per-row ``min_gen`` under the same mechanism id,
    so D-2/D-4 attribution and the C8 forced share stay fully measurable — the
    reason a class-level LP constraint was refused instead (it would carry no
    per-row mech id, so ST_GAS forced share would report ~0 % and C8 would pass
    because the diagnostic went blind, not because the forcing stopped).
    See ``docs/handoffs/FINDING-ercot259-c8-allocation-2026-09-08.md``.

    ``persist_params`` (``config.netload_drag_min_run_persistence``, pjm-177)
    replaces the HOUR-ELIGIBILITY of the same mandate, and nothing else — same
    rows, same membership, same ``(slope, intercept, cap)``, same ``mech_id``,
    no second floor (rule 19 [R-ONE-MECH]). ``floor_frac`` is read off the
    net-load curve hour by hour, so the floor collapses to zero whenever
    net-load crosses below the curve's own zero-crossing and returns when it
    rises — i.e. the mechanism representing a gas-steam boiler's COMMITMENT
    cycles that boiler on the diurnal net-load wave. The class's own frozen
    ``*_COMMITMENT_PARAMS`` table (NREL/SR-5500-55433) says it cannot: min-run
    24 h efficient / 48 h older-subcritical, because a stop-start costs more
    than idling at minimum load across a sustained event. Measured on PJM
    2023-25 raw CAMPD ``opTime``, the fleet's online capacity is FLAT across
    the day (hour-of-day max/min 1.19 / 1.07 / 1.05; hour-of-day R^2
    0.003 / 0.001 / 0.001) with multi-day run lengths (median 25 / 28 / 57 h),
    while the drag's binding excursions run a median 7-8 h.

    When supplied, each row's ``floor_frac`` becomes a CENTRED CIRCULAR moving
    average over that row's own ``min_run_hours`` — resolved from this table by
    the row's own heat rate, the identical lookup
    ``model.commitment._commitment_params`` performs for a legacy generator —
    re-clipped to ``[0, cap]``. Circular because the LP's 8760 clock is cyclic;
    centred so the transform is mean-preserving on the fraction. It CANNOT read
    ``gen.min_run_hours``: a CAMPD-binned fleet carries ``min_run_hours = 0`` on
    every tranche, which is why ``class_commitment_overrides`` exists. Zero free
    parameters (rules 21/24) and the curve's coefficients are untouched (rule 23
    — this is the driver's FORM, never its numbers). Only the ALL-HOURS boiler
    applier passes a table, so a floor carrying a ``ramp_window`` can never be
    smoothed across its own window (rule 17 [R-FLOOR-WINDOW]); ``None`` is
    byte-identical.

    Modifies ``fleet_arrays`` in place. Returns ``True`` when a floor was
    applied, ``False`` (byte-identical) when the class has no reliability units.
    """
    rows = [
        g
        for g, gen in enumerate(generators)
        if gen.plant_group == plant_group
        # exclude every peak-band rung ("peak", "peak2".. under a ladder) —
        # the scarcity band is never commitment scaffolding
        and not gen.unit_id.rpartition("_")[2].startswith("peak")
        and gen.plant_code not in exclude_plant_codes
    ]
    if not rows:
        return False

    hours = int(fleet_arrays.availability.shape[1])
    net_load_gw = np.asarray(net_load_mw, dtype=float)[:hours] / 1000.0
    floor_frac = np.clip(slope * net_load_gw + intercept, 0.0, cap)  # (T,)
    if ramp_window is not None:
        # Gate to the diurnal reliability window; zero outside it. Hour of day on
        # the model's local-standard 8760 clock is t % 24.
        start, end = ramp_window
        hod = np.arange(hours) % 24
        floor_frac = np.where((hod >= start) & (hod < end), floor_frac, 0.0)

    # pjm-177: per-row min-run persistence of the SAME mandate (hour-eligibility
    # only). Resolved once per distinct window so the convolution runs at most
    # twice for a real fleet.
    frac_by_row: dict[int, np.ndarray] = {}
    if persist_params is not None:
        for g in rows:
            w = _min_run_hours(generators[g], persist_params)
            if w <= 1 or w >= hours:
                continue
            if w not in frac_by_row:
                frac_by_row[w] = np.clip(
                    _circular_centred_mean(np.asarray(floor_frac, dtype=float), w),
                    0.0,
                    cap,
                )

    if fleet_arrays.min_gen is None:
        # min_gen replaces pmin as the LP lower bound for EVERY generator, so a
        # fresh floor must preserve export-sink rows (pmin < 0) by seeding from
        # pmin rather than zeroing them (mirrors generators_to_fleet_arrays).
        fleet_arrays.min_gen = np.broadcast_to(
            fleet_arrays.pmin[:, np.newaxis], (fleet_arrays.pmin.size, hours)
        ).copy()

    mech = ensure_mechanism(fleet_arrays)
    pmax = fleet_arrays.pmax
    avail = fleet_arrays.availability
    # Never floor above the hour's available capacity, so the LP stays feasible
    # (the drag can never manufacture unmet demand). Under the measured lay-up
    # window mask (ercot-256) the eligible-capacity basis is additionally net of
    # the plant's measured economic-lay-up share, so the floor cannot bind
    # inside a window the model's own outage pipeline classified as
    # not-operating (rule 17 [R-FLOOR-WINDOW]).
    basis: dict[int, np.ndarray] = {}
    for g in rows:
        b = avail[g, :]
        if layup_removed:
            lu = layup_removed.get(
                (
                    int(getattr(generators[g], "plant_code", 0) or 0),
                    str(getattr(generators[g], "plant_group", "") or ""),
                )
            )
            if lu is not None:
                b = np.maximum(0.0, b - np.asarray(lu, dtype=float)[:hours])
        basis[g] = b

    def _frac_for(g: int) -> np.ndarray:
        """This row's floor fraction — persisted when armed, else the curve."""
        if persist_params is None:
            return np.asarray(floor_frac, dtype=float)
        w = _min_run_hours(generators[g], persist_params)
        got = frac_by_row.get(w)
        return got if got is not None else np.asarray(floor_frac, dtype=float)

    if merit_allocation:
        # The merit fill takes ONE hourly fleet target, so persistence composes
        # with it through the capacity-weighted mean of the per-row fractions —
        # identical to ``floor_frac`` when persistence is off, and identical
        # across rows whenever the fleet resolves to a single window.
        if persist_params is None:
            merit_frac = np.asarray(floor_frac, dtype=float)
        else:
            wt = np.array([pmax[g] for g in rows], dtype=float)
            stack = np.stack([_frac_for(g) for g in rows])
            merit_frac = (
                (stack * wt[:, None]).sum(axis=0) / wt.sum()
                if wt.sum() > 0
                else np.asarray(floor_frac, dtype=float)
            )
        targets = _netload_drag_merit_targets(rows, generators, pmax, basis, merit_frac)
    else:
        targets = {
            g: np.minimum(_frac_for(g) * pmax[g], basis[g] * pmax[g]) for g in rows
        }

    for g, target in targets.items():
        raised = fleet_arrays.min_gen[g, :] < target
        fleet_arrays.min_gen[g, :] = np.maximum(fleet_arrays.min_gen[g, :], target)
        mech[g, raised] = mech_id
    return True


def _load_ercot_stgas_seasonal_drag(
    config: ScenarioConfig, hours: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Resolve the season-resolved ERCOT ST_GAS drag curve to per-hour arrays.

    Reads the frozen artifact
    (``scripts/data/derive_ercot_stgas_drag_seasonal.py`` →
    ``data/raw/_validation-source/ercot_stgas_drag_seasonal.json``) — the
    rule-22 season-grain re-derive of the pooled 2026-06 curve from the same
    CAMPD source (ERCOT-90 §3.3 / ERCOT-91 winter seam) — and maps its per-
    meteorological-season ``(slope, intercept, cap)`` onto the model's
    fixed-CST non-leap 8760 clock via the artifact's own ``season_of_month``.
    Returns ``(slope_h, intercept_h, cap_h)`` each of shape ``(hours,)``.

    Hard errors (never a silent fallback): missing/malformed artifact, a
    season absent from the artifact, or an ISO mismatch — the curve is fitted
    on ERCOT CAMPD data and must not cross ISO boundaries (rule 25).
    """
    path = getattr(config, "gas_st_drag_seasonal_path", None)
    if not path:
        from market_sim.config import paths as _paths

        path = str(_paths.CALIBRATION_DIR / "ercot_stgas_drag_seasonal.json")
    art = json.loads(Path(path).read_text())
    prov = art.get("_provenance", {})
    art_iso = str(prov.get("iso", ""))
    if art_iso != str(config.iso):
        raise ValueError(
            f"gas_st_drag_seasonal: artifact is fitted on {art_iso or '?'} "
            f"data but the run ISO is {config.iso} — a fitted curve never "
            "crosses ISO boundaries (rule 25)"
        )
    season_of_month = [int(x) for x in prov.get("season_of_month", ())]
    seasons = art.get("seasons", {})
    if len(season_of_month) != 12 or not seasons:
        raise ValueError(
            "gas_st_drag_seasonal: artifact carries no season_of_month/"
            "seasons — re-derive "
            "scripts/data/derive_ercot_stgas_drag_seasonal.py"
        )
    # Calendar coordinates on the model's fixed-CST non-leap 8760 clock (the
    # span-loader convention): month via cumulative month-start hours.
    month_start_h = (
        np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]) * 24
    )  # (12,) Jan..Dec starts
    hoy = np.arange(hours)
    month_idx = np.searchsorted(month_start_h[1:], hoy % 8760, side="right")  # 0..11
    season_idx = np.asarray(season_of_month, dtype=int)[month_idx]  # (hours,)

    n_seasons = int(max(season_of_month)) + 1
    slope_s = np.full(n_seasons, np.nan)
    icept_s = np.full(n_seasons, np.nan)
    cap_s = np.full(n_seasons, np.nan)
    for s in range(n_seasons):
        entry = seasons.get(str(s))
        if not entry:
            raise ValueError(
                f"gas_st_drag_seasonal: season {s} absent from the artifact "
                "— re-derive scripts/data/derive_ercot_stgas_drag_seasonal.py"
            )
        slope_s[s] = float(entry["slope_per_gw"])
        icept_s[s] = float(entry["intercept"])
        cap_s[s] = float(entry["cap"])
    return slope_s[season_idx], icept_s[season_idx], cap_s[season_idx]


def apply_gas_st_netload_drag_floor(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    layup_removed: dict[tuple[int, str], np.ndarray] | None = None,
) -> bool:
    """Impose the net-load-indexed ST_GAS reliability-drag min-gen floor.

    The endogenous, weather-driven net-load drag floor (a forward-native
    replacement for a fixed seasonal calendar fraction). ERCOT holds legacy
    gas-steam
    units committed at minimum load for local/system reliability (RUC); the
    held fraction is not a fixed season but rises with system **net-load**
    (``load - wind - solar``), the operational proxy for reserve tightness RUC
    keys off. Each non-peaker ST_GAS tranche (peaker-class units in
    :data:`ST_GAS_PEAKER_PLANTS` and the economic ``_peak`` tranche are
    excluded — they run purely on price) gets a per-hour minimum-generation
    floor of ``clip(slope*netload_GW + intercept, 0, cap) x pmax``, capped at
    available capacity and composed with any existing floor via ``maximum``.
    The LP dispatches economically *above* the floor, so the floor only binds
    in the low-price (overnight / shoulder) hours where an energy-only merit
    order would leave these out-of-merit boilers off — exactly the
    reliability-drag energy the dispatch was missing.

    The default curve coefficients (``config.gas_st_drag_slope_per_gw`` /
    ``_intercept`` / ``_cap``) are the CAMPD overnight (low-price) ST_GAS
    capacity factor regressed on contemporaneous system net-load, 2023-2025
    (``docs/ercot-st-gas-netload-drag-2026-06.md``); the relationship is
    year-stable, so the same curve regenerates for a forward year (which has a
    load forecast and a wind/solar build, hence a net-load) and responds to
    changed conditions (more VRE lowers net-load and so the drag). That
    forward-derivability and condition-response is what makes it admissible in
    both backcast and forecast (CLAUDE.md #10), unlike a fixed seasonal fraction
    or an offer markdown tuned to the ST_GAS residual.

    Modifies ``fleet_arrays`` in place. Returns ``True`` when a floor was
    applied, ``False`` (byte-identical) when the flag is off or the fleet has no
    reliability ST_GAS units.

    Args:
        fleet_arrays: The vectorized fleet (``min_gen`` is set in place).
        generators: The dispatch fleet, aligned row-for-row with ``fleet_arrays``.
        net_load_mw: System net-load per hour (``load - wind - solar``), the same
            LP-served (net-of-must-run) net-load convention the runner uses
            elsewhere, shape ``(T,)``.
        config: Scenario config supplying the enable flag and curve coefficients.
    """
    if not getattr(config, "gas_st_netload_drag", False):
        return False
    # ERCOT-91 season-grain fix (gas_st_drag_seasonal, default off): the same
    # curve re-derived per meteorological season from the same CAMPD source
    # (rule 22 — the pooled net-load axis conflates the winter and summer
    # net-load limbs, which carry different overnight commitment levels;
    # ERCOT-90 §3.3). Same mechanism id, same rows, same all-hours window —
    # only the coefficient grain changes.
    slope: "float | np.ndarray" = config.gas_st_drag_slope_per_gw
    intercept: "float | np.ndarray" = config.gas_st_drag_intercept
    cap: "float | np.ndarray" = config.gas_st_drag_cap
    if getattr(config, "gas_st_drag_seasonal", False):
        hours = int(fleet_arrays.availability.shape[1])
        slope, intercept, cap = _load_ercot_stgas_seasonal_drag(config, hours)
        logger.info(
            "ST_GAS net-load drag: SEASON-RESOLVED curve armed "
            "(gas_st_drag_seasonal, ERCOT-91 rule-22 grain fix) — per-hour "
            "coefficients from the frozen seasonal artifact replace the "
            "pooled scalars; slope range [%.5f, %.5f]/GW",
            float(np.min(slope)),
            float(np.max(slope)),
        )
    # All-hours boiler floor (no ramp window); peaker-class ST_GAS plants run on
    # price and are excluded.
    return apply_netload_reliability_floor(
        fleet_arrays,
        generators,
        net_load_mw,
        plant_group="ST_GAS",
        slope=slope,
        intercept=intercept,
        cap=cap,
        ramp_window=None,
        exclude_plant_codes=ST_GAS_PEAKER_PLANTS,
        mech_id=MECH_ST_NETLOAD_DRAG,
        layup_removed=layup_removed,
        # ercot-259: allocation-only swap of the SAME mandated MW (rule 19).
        merit_allocation=bool(getattr(config, "netload_drag_merit_allocation", False)),
        # pjm-177: hour-eligibility-only swap of the SAME mandate (rule 19). The
        # frozen NREL table is passed ONLY here — the CT limb below carries a
        # ramp window and fast-start peakers genuinely cycle, so it is never
        # persisted (rule 17 [R-FLOOR-WINDOW] / rule 18 [R-PHYSICS]).
        persist_params=(
            ST_GAS_COMMITMENT_PARAMS
            if getattr(config, "netload_drag_min_run_persistence", False)
            else None
        ),
    )


def apply_ct_netload_drag_floor(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    layup_removed: dict[tuple[int, str], np.ndarray] | None = None,
) -> bool:
    """Impose the net-load-indexed CT_PEAKER reliability-drag min-gen floor.

    The simple-cycle analog of :func:`apply_gas_st_netload_drag_floor`, and the
    forward-native replacement for the ``ct_mustrun_per_plant`` actuals pin.
    ERCOT commits fast-start gas peakers for summer-peak + evening
    net-load-ramp local reliability (RUC / RMR); the hourly energy-only LP,
    seeing their top-of-merit offer, never makes that commitment, so the
    backcast under-runs CT_PEAKER and the freed energy spills onto cheaper CC.

    Unlike the all-hours ST_GAS boiler, CT peakers serve reliability only in the
    afternoon-evening ramp (solar collapse): the CAMPD overnight CF is ~0 even
    at high net-load, while the evening (15-22h local-standard) CF rises cleanly
    with net-load (Spearman rho ~0.7, 2023-2025). So the floor is the same
    clipped net-load line ``clip(slope*netload_GW + intercept, 0, cap)`` but
    **gated to the ramp window** ``[ct_drag_ramp_start, ct_drag_ramp_end)`` —
    zero outside it. The window is on the model's local-standard hour-of-year
    clock (hour t → t % 24), the same clock the CAMPD fit used. Each non-``_peak``
    CT_PEAKER tranche (the duct-firing ``_peak`` scarcity band runs purely on
    price) gets the floor, capped at available capacity and composed with any
    existing floor via ``maximum``; the LP dispatches economically above it.

    The defaults (``config.ct_drag_slope_per_gw`` / ``_intercept`` / ``_cap``)
    are the CAMPD CT_PEAKER evening capacity factor regressed on contemporaneous
    net-load, 2023-2025 (``docs/ercot-ct-netload-drag-2026-06.md``); both the
    trigger (net-load) and the magnitude (physical min-gen) are forward-derivable
    and condition-responsive, so the mechanism is admissible in both backcast and
    forecast (CLAUDE.md #10/#11), unlike an offer markdown or actuals pin.

    Modifies ``fleet_arrays`` in place. Returns ``True`` when a floor was
    applied, ``False`` (byte-identical) when the flag is off or the fleet has no
    reliability CT_PEAKER units.

    Args:
        fleet_arrays: The vectorized fleet (``min_gen`` is set in place).
        generators: The dispatch fleet, aligned row-for-row with ``fleet_arrays``.
        net_load_mw: System net-load per hour (``load - wind - solar``), the same
            LP-served convention the runner uses elsewhere, shape ``(T,)``.
        config: Scenario config supplying the enable flag, curve coefficients and
            ramp window.
    """
    if not getattr(config, "ct_netload_drag", False):
        return False
    # Evening-ramp-gated floor (peakers serve reliability in the afternoon-
    # evening net-load ramp, not overnight).
    return apply_netload_reliability_floor(
        fleet_arrays,
        generators,
        net_load_mw,
        plant_group="CT_PEAKER",
        slope=config.ct_drag_slope_per_gw,
        intercept=config.ct_drag_intercept,
        cap=config.ct_drag_cap,
        ramp_window=(config.ct_drag_ramp_start, config.ct_drag_ramp_end),
        mech_id=MECH_CT_NETLOAD_DRAG,
        layup_removed=layup_removed,
        # ercot-259: allocation-only swap of the SAME mandated MW (rule 19).
        merit_allocation=bool(getattr(config, "netload_drag_merit_allocation", False)),
    )


def _drag_lp_bin_capacity(
    config: ScenarioConfig,
    iso: str,
    generators: list[Generator],
    fleet_arrays: FleetArrays,
) -> tuple[tuple[tuple[int, str], float], ...] | None:
    """The dispatched bins' own capacity for the drag lay-up shares, or ``None``.

    Gate for ``ScenarioConfig.unit_outage_dispatched_bin_denominator``
    (miso-266). Built off the very ``generators`` / ``pmax`` the drag floors
    clip against, so the lay-up share stays on the same basis as the outage
    share it is additive with. ``None`` while off (and always for ERCOT, whose
    branch caps on its own CAMPD bin sheet), which leaves the loader's
    incumbent denominator and the off path byte-inert.
    """
    if not getattr(config, "unit_outage_dispatched_bin_denominator", False):
        return None
    if (iso or "ERCOT").upper() == "ERCOT":
        return None
    # Local import for the same fleet -> data cycle reason as the loader below.
    from market_sim.data.outages import lp_bin_capacity_index

    return lp_bin_capacity_index(generators, np.asarray(fleet_arrays.pmax, dtype=float))


def _resolve_drag_layup_shares(
    config: ScenarioConfig,
    iso: str,
    year: int,
    hours: int,
    lp_bin_capacity: tuple[tuple[tuple[int, str], float], ...] | None = None,
) -> dict[tuple[int, str], np.ndarray]:
    """Measured economic-lay-up shares for the net-load drag floors, or ``{}``.

    Gate for ``ScenarioConfig.netload_drag_layup_window_mask`` (ercot-256): the
    mask is BACKCAST ONLY (rule 13 [R-MEASURED] — a same-year lay-up window has
    no forward analogue, exactly like the CAMPD outage windows the same detector
    produces), so a forecast run and an unarmed run both get an empty dict and
    the drag floors are byte-identical to their pre-mask behaviour.

    Every basis argument mirrors the availability overlay's own call, because
    :func:`market_sim.data.outages.unit_layup_removed_fractions` guarantees that
    a lay-up share and an outage share for the same plant are ADDITIVE only when
    the two sit on the same unit->plant routing and capacity denominator. An ISO
    or year with no lay-up extract yields ``{}`` (no effect).

    Args:
        config: The scenario config supplying the gate and the overlay bases.
        iso: ISO code — selects ``campd-unit-outages-layup[-<ISO>].csv``.
        year: The solve year, used when the config pins no ``weather_year``.
        hours: The fleet's hour count, so the shares align with ``availability``.

    Returns:
        ``{(plant_code, plant_group): (hours,) laid-up capacity fraction}``,
        empty when the mask is off, the run is not a backcast, or no extract
        exists for this ISO/year.
    """
    if not getattr(config, "netload_drag_layup_window_mask", False):
        return {}
    if getattr(config, "mode", "forecast") != "backcast":
        return {}
    # Local import: data.outages imports the fleet package, so a module-level
    # import here would close a cycle (the same reason the must-run seam's
    # miso-173 mask imports locally).
    from market_sim.data.outages import unit_layup_removed_fractions

    shares = unit_layup_removed_fractions(
        int(getattr(config, "weather_year", 0) or year),
        hours,
        getattr(config, "campd_bins_path", None) or _default_campd_bins_path(),
        iso=(iso or "ERCOT").upper(),
        cc_steam_part_reclass=getattr(config, "cc_steam_part_reclass", False),
        cc_nameplate_basis=getattr(config, "unit_outage_lp_capacity_basis", False),
        st_capacity_basis=getattr(config, "unit_outage_st_capacity_basis", False),
        per_unit_clip=getattr(config, "unit_outage_per_unit_clip", False),
        extract_basis_share=getattr(config, "unit_outage_extract_basis_share", False),
        coal_extract_basis_share=getattr(
            config, "unit_outage_coal_extract_basis_share", False
        ),
        # miso-266: the dispatched bin's own capacity as the denominator, for
        # the same additivity contract every basis argument here mirrors.
        lp_bin_capacity=lp_bin_capacity,
    )
    logger.info(
        "netload_drag_layup_window_mask ARMED (%s %d): %d plant-tranche lay-up "
        "share series mask the net-load drag floors",
        iso,
        year,
        len(shares),
    )
    return shares


def _default_campd_bins_path() -> str:
    """The CAMPD bins CSV the lay-up loader defaults to (no config override)."""
    from market_sim.data.outages import BINS_CSV_DEFAULT

    return str(BINS_CSV_DEFAULT)


def apply_netload_drag_floors(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    demand: np.ndarray,
    wind_cf: np.ndarray,
    wind_cap: np.ndarray,
    solar_cf: np.ndarray,
    solar_cap: np.ndarray,
    config: ScenarioConfig,
    iso: str,
    year: int,
) -> None:
    """Apply the net-load-indexed reliability-drag min-gen floors (both classes).

    The single shared gate-and-log wrapper over
    :func:`apply_gas_st_netload_drag_floor` (legacy gas-steam boilers) and
    :func:`apply_ct_netload_drag_floor` (CT_PEAKER simple-cycle, evening-ramp
    gated), called by BOTH orchestrators (orchestrator-unification Stage 6 --
    the ~40-line wrapper was previously duplicated verbatim in ``runner.py``
    and ``scripts/run_calibration.py``). Each floors a tranche's per-hour
    minimum generation by a curve rising with system net-load
    (``load - wind - solar``, the LP-served convention) -- the operational
    proxy for the reserve tightness RUC keys off -- over which the LP
    dispatches economically. Both appliers gate internally on their own
    config flag and modify ``fleet_arrays.min_gen`` in place; with both flags
    off this returns without computing anything (byte-identical).
    """
    if not (
        getattr(config, "gas_st_netload_drag", False)
        or getattr(config, "ct_netload_drag", False)
    ):
        return
    # t: hour. Net-load = load - wind - solar, LP-served convention.
    net_load = (
        demand.sum(axis=0)
        - (solar_cap[:, None] * solar_cf).sum(axis=0)
        - (wind_cap[:, None] * wind_cf).sum(axis=0)
    )
    layup_removed = _resolve_drag_layup_shares(
        config,
        iso,
        year,
        int(fleet_arrays.availability.shape[1]),
        # miso-266: built off the very generators/pmax the drag floors clip
        # against, so the lay-up share and the outage share stay additive.
        lp_bin_capacity=_drag_lp_bin_capacity(config, iso, generators, fleet_arrays),
    )
    if apply_gas_st_netload_drag_floor(
        fleet_arrays, generators, net_load, config, layup_removed
    ):
        logger.info(
            "%s %d: ST_GAS net-load reliability-drag floor applied "
            "(frac = clip(%.5f*netGW %+0.4f, 0, %.2f); net-load mean %.0f / "
            "max %.0f MW)",
            iso,
            year,
            config.gas_st_drag_slope_per_gw,
            config.gas_st_drag_intercept,
            config.gas_st_drag_cap,
            float(net_load.mean()),
            float(net_load.max()),
        )
    if apply_ct_netload_drag_floor(
        fleet_arrays, generators, net_load, config, layup_removed
    ):
        logger.info(
            "%s %d: CT_PEAKER net-load reliability-drag floor applied "
            "(frac = clip(%.5f*netGW %+0.4f, 0, %.2f) in ramp %dh-%dh)",
            iso,
            year,
            config.ct_drag_slope_per_gw,
            config.ct_drag_intercept,
            config.ct_drag_cap,
            config.ct_drag_ramp_start,
            config.ct_drag_ramp_end,
        )


def apply_neiso_coldsnap_derate(
    fleet_arrays: "FleetArrays",
    config: ScenarioConfig,
    iso: str,
    year: int,
) -> None:
    """Apply the NEISO winter gas-availability cold-snap derate (gated).

    The shared gate-and-log wrapper over
    :func:`market_sim.model.transmission.inject_neiso_gas_coldsnap_derate`
    (temperature-dependent forced outage, TDFOR): on cold snaps the
    gas-electric constraint makes non-dual-fuel gas-CC/CT capacity physically
    UNAVAILABLE, so the fleet goes reserve-short and the RCPF co-opt prices
    the >$300 scarcity tail (and widens the storage spread). Must run before
    the reserve-co-opt inputs are built so the shared-headroom RHS sees the
    derated availability. Dual-fuel units are excluded (they switch to oil,
    not vanish).

    Called by BOTH orchestrators (orchestrator-unification Stage 6 -- the
    mechanism was previously wired only in ``scripts/run_calibration.py``,
    the §2.2 accidental-drift row this stage closes). Gated on
    ``config.neiso_gas_coldsnap_derate`` (default off, byte-identical); the
    curve coefficients are plain ``ScenarioConfig`` fields (NERC
    cold-weather-anchored defaults -- see the field citations), no longer
    getattr fallback literals (CLAUDE.md #24).
    """
    if not getattr(config, "neiso_gas_coldsnap_derate", False):
        return
    # Local import: transmission imports from data.fleet at module level.
    from market_sim.model.transmission import inject_neiso_gas_coldsnap_derate

    # Conditional dual-fuel exemption (gated, default off; rule 19 scope
    # correction). The parent derate exempts every dual-fuel unit on the premise
    # that apply_dual_fuel_pricing has switched it to oil; that premise holds only
    # where delivered gas has reached the oil parity, since the switch is
    # mc = min(gas, oil). Build the SAME comparison here, so the exemption is
    # granted hour by hour exactly where the switch it cites has actually fired.
    dual_switch_active = None
    if getattr(config, "neiso_coldsnap_derate_dualfuel_unswitched", False):
        from market_sim.data.fuel.dual_fuel import dual_fuel_oil_price_series
        from market_sim.data.fuel.hubs import iso_hub_daily_gas_prices

        gas_hourly = iso_hub_daily_gas_prices(config, year)
        if gas_hourly is not None:
            oil_hourly = dual_fuel_oil_price_series(config, year)
            dual_switch_active = np.asarray(gas_hourly, dtype=float) >= np.asarray(
                oil_hourly, dtype=float
            )
            logger.info(
                "%s %d: conditional dual-fuel derate exemption — switch active in "
                "%d of %d hours; dual-fuel gas capacity is derated in the other %d",
                iso,
                year,
                int(dual_switch_active.sum()),
                int(dual_switch_active.size),
                int((~dual_switch_active).sum()),
            )

    if inject_neiso_gas_coldsnap_derate(
        fleet_arrays,
        iso,
        year,
        float(config.neiso_gas_derate_t0_c),
        float(config.neiso_gas_derate_slope_per_c),
        float(config.neiso_gas_derate_cap),
        dual_switch_active=dual_switch_active,
    ):
        logger.info(
            "%s %d: winter gas-availability derate — non-dual-fuel gas-CC/CT "
            "availability cut by clip(slope*(t0-TMIN),0,cap) over the cold-snap "
            "window (TDFOR, NERC cold-weather anchored)",
            iso,
            year,
        )
