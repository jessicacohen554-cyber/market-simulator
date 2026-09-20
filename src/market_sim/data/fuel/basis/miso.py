"""MISO zonal gas basis + the winter Chicago-citygate daily shape overlay.

Split out of ``data/fuel.py`` (W-D3; refactor-consolidation plan §5 item 3) as
pure code motion. Rule 25: MISO's measured per-zone basis rows live in
``miso_zonal_gas_hub.csv`` and apply only under ``config.miso_zonal_gas_basis``
+ ``config.iso == "MISO"``. ``_miso_citygate_daily_dated`` is resolved through
the package namespace at call time (:func:`.._shared._pkg_ns`) because tests
patch it on the facade.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays

from .._shared import (
    _DAYS_IN_MONTH,
    _GAS_FUEL_IDX,
    _GAS_PRICE_FLOOR,
    _month_index,
    _pkg_ns,
    logger,
)
from ..hubs import _flow_date_staircase, gas_daily_shape_factors
from .meanzero import (
    MISO_ZONAL_GAS_HUB_PATH,
    _apply_meanzero_zonal_gas_basis,
    _load_zonal_gas_hub,
    _zonal_gas_basis_by_zone,
)


def miso_zonal_gas_basis_by_zone(
    year: int, path: Path | None = None
) -> dict[str, float] | None:
    """Return ``{zone: basis vs Henry Hub ($/MMBtu)}`` for MISO, or None.

    Same format and semantics as :func:`pjm_zonal_gas_basis_by_zone` but reads
    :data:`MISO_ZONAL_GAS_HUB_PATH`.
    """
    return _zonal_gas_basis_by_zone(
        Path(path) if path else MISO_ZONAL_GAS_HUB_PATH, year
    )


def apply_miso_zonal_gas_basis(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
    skip_cells: np.ndarray | None = None,
) -> None:
    """Shift each MISO gas unit's price by its zone's measured regional gas basis.

    Delegates to :func:`_apply_meanzero_zonal_gas_basis` — the same
    capacity-weighted mean-zero core used by PJM. MISO-West/MISO-Plains sit
    on MidCon / Northern Natural (IA), the eastern Midwest zones (Illinois/
    Indiana/East) on Chicago Citygate (IL),
    and MISO-South on Gulf Coast (LA); the spread opens while the
    fleet-aggregate gas level is preserved.

    Gated on ``config.miso_zonal_gas_basis`` and ``config.iso == "MISO"``.
    Default-off; the calibration harness enables it for MISO.

    ``skip_cells`` (miso-213): the print-derived-cell mask returned by
    :func:`~..plant_prices.apply_plant_monthly_fuel_prices`. Honoured ONLY
    when ``config.miso_zonal_gas_basis_skip_923_priced`` is set — a caller
    may always pass the mask, and the flag decides whether the applier
    consumes it, so the flag-off behaviour is byte-identical to HEAD whatever
    the caller does. On masked cells the increment is not added (rule 19
    ``[R-ONE-MECH]``: the EIA-923 print already carries the regional
    delivered premium); unmasked (trajectory) cells still receive it.
    """
    # miso-224: a hub-priced row (apply_miso_gas_marginal_commodity) is ALSO
    # skipped — its zone's hub already IS its regional level (rule 19) — whatever
    # the miso-213 flag says. Off-state byte-identical: neither flag, no skip.
    use_skip = skip_cells is not None and (
        bool(getattr(config, "miso_zonal_gas_basis_skip_923_priced", False))
        or bool(getattr(config, "miso_gas_marginal_commodity_pricing", False))
    )
    _apply_meanzero_zonal_gas_basis(
        fuel_prices,
        fleet,
        config,
        year,
        iso="MISO",
        config_field="miso_zonal_gas_basis",
        hub_path=MISO_ZONAL_GAS_HUB_PATH,
        path_override=Path(path) if path else None,
        skip_cells=skip_cells if use_skip else None,
    )


# MISO winter fuel-security season: the pipeline-scarcity heating months in which
# the Chicago Citygate daily overlay supersedes the national Henry-Hub gas_daily_
# shape. The meteorological-winter convention (Dec/Jan/Feb); every measured MISO
# 2023-2025 winter gas event (Heather Jan-2024, the Jan-17-2025 / Feb-18-19-2025
# cold snaps) falls inside it. A structural scope, not a fitted knob (miso-72
# design §3.4).
_MISO_WINTER_MONTHS: tuple[int, ...] = (12, 1, 2)


def _miso_chicago_hub_zones(year: int, path: Path | None = None) -> set[str]:
    """Return the MISO zone names the published hub table maps to Chicago Citygate.

    Reads the SAME ``miso_zonal_gas_hub.csv`` (:data:`MISO_ZONAL_GAS_HUB_PATH`)
    :func:`apply_miso_zonal_gas_basis` uses and selects the zones whose ``hub``
    column names the Chicago Citygate (the eastern-Midwest zones MISO-Illinois /
    MISO-Indiana / MISO-East). This is the identification source for which zones
    the winter Chicago daily shape applies to — no new magic mapping (rule 5). An
    absent file or year, or a table without the ``hub`` column, yields an empty
    set (the overlay stays inert).
    """
    frame = _load_zonal_gas_hub(Path(path) if path else MISO_ZONAL_GAS_HUB_PATH)
    if frame is None or "hub" not in frame.columns:
        return set()
    sub = frame[frame["year"] == year]
    return {
        str(r.zone)
        for r in sub.itertuples()
        if str(r.hub).strip().lower().startswith("chicago")
    }


def miso_chicago_daily_shape_factors(
    year: int,
    hours: int,
    path: Path | None = None,
    year_start_package: bool = False,
) -> np.ndarray:
    """Return ``(hours,)`` within-month Chicago Citygate daily gas-price shape.

    The MISO analogue of :func:`gas_daily_shape_factors`, built from the measured
    Chicago Citygate daily spot (:func:`_miso_citygate_daily_dated`) placed on its
    gas **FLOW** days (trade + 1, weekend/holiday packages forward-filled —
    :func:`_flow_date_staircase`, the caiso-90 precedent), then renormalized so the
    calendar-day factors average to EXACTLY 1.0 within every month. Multiplying a
    (correctly-levelled) monthly gas series by these adds the real regional
    cold-snap swing while leaving the monthly mean — and hence the annual burn and
    mix — unchanged.

    Flow-date placement is REQUIRED, not cosmetic: the daily citygate is a
    next-day-delivery index, so the Winter Storm Heather Friday 2024-01-12 print
    ($25.82/MMBtu) prices the whole Sat-Mon-holiday weekend package — gas flowing
    Jan-13/14/15/16, including the record-peak Tuesday. The pre-§3.7-fix
    even-spread resampling in :func:`gas_daily_shape_factors` instead mislocated
    it to Jan-13 and dropped the true tail days to 0.88-0.96×; the flow-date
    staircase lands it on Jan-13-16 at 4.67× (verified monthly-mean factor
    1.000). (The national Henry Hub shape now uses the TRADE-date staircase —
    :func:`_trade_date_staircase` — because the HH daily spot prints the price
    of its own trading day, unlike this next-day-delivery citygate index.)
    Returns all-ones for a year with no Chicago quotes (the caller stays inert).
    """
    factors = np.ones(hours, dtype=float)
    _all = _pkg_ns()._miso_citygate_daily_dated(path)
    dated = _all.get(year, {})
    if not dated:
        return factors
    # ``year_start_package`` (xiso-8, config.gas_flow_date_year_start_package):
    # price the year's OPENING flow days with the prior December trade that
    # covered them rather than back-filling from the first January trade. Off by
    # default and byte-identical off (no seed is built). NOTE the channel this
    # reaches: the factors below renormalize to mean EXACTLY 1.0 within every
    # month, so this can never move January's gas LEVEL -- only its within-month
    # shape. MISO's measured exposure is 0.0293 % of the annual mean in its worst
    # year and only 2021/2022 are package boundaries at all; see
    # PRECOMMIT-xiso8-year-start-left-edge-2026-09-20.md §2.3.
    flow = _flow_date_staircase(  # 365-day flow-date staircase
        dated, year, prior_year_dated=_all.get(year - 1) if year_start_package else None
    )
    if flow is None:
        return factors
    hour = 0
    day0 = 0  # cumulative day-of-year offset of month m on the non-leap clock
    for _m, n_days in enumerate(_DAYS_IN_MONTH):
        if hour >= hours:
            break
        seg = flow[day0 : day0 + n_days]
        mean = float(seg.mean())
        if mean > 0:
            f = seg / mean
            fbar = float(f.mean())
            if fbar > 0:
                f = f / fbar  # renormalize: mean-preserving within the month
            rep = np.repeat(f, 24)[: max(0, hours - hour)]
            factors[hour : hour + len(rep)] = rep
        hour += n_days * 24
        day0 += n_days
    return factors


def apply_miso_winter_citygate_daily(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
    citygate_path: Path | None = None,
) -> None:
    """Reprice MISO Chicago-hub gas units at the measured Chicago winter daily shape.

    The miso-72 winter fuel-security overlay (design
    ``docs/handoffs/miso-winter-fuel-security-design-2026-07.md``). In the winter
    months (:data:`_MISO_WINTER_MONTHS`, Dec/Jan/Feb) only, for the MISO gas units
    in the Chicago-hub zones only (:func:`_miso_chicago_hub_zones`), it **replaces
    the national Henry-Hub ``gas_daily_shape`` within-month daily shape with the
    measured Chicago Citygate daily shape** (:func:`miso_chicago_daily_shape_factors`,
    flow-date-placed and mean-preserving). Every other cell — non-winter months,
    non-Chicago zones (MISO-West/Plains on MidCon, MISO-South on Gulf), the
    off-state — is byte-identical.

    This runs in :func:`resolve_fuel_prices` **immediately before**
    :func:`apply_miso_zonal_gas_basis`, so each Chicago-hub gas row is still
    ``level × national_shape`` (the additive mean-zero zonal spread not yet
    applied). The correction ``chicago_shape / national_shape`` divides out the
    national shape and multiplies in the Chicago shape — leaving ``level ×
    chicago_shape``, mean-preserving within month (the monthly gas level, and hence
    the already-correct monthly LMP, unchanged). The subsequent zonal-basis pass
    then adds its annual per-zone spread un-shaped, and dual-fuel oil parity
    (:func:`apply_dual_fuel_pricing`) still caps any winter blowout (rule 14).

    Rule-19 reconciliation (supersede, never stack): the national ``gas_daily_shape``
    is REPLACED for the Chicago-zone winter cells (not added to); the mean-zero
    ``miso_zonal_gas_basis`` spread is orthogonal (spatial/annual vs temporal/
    mean-1) and unperturbed because this overlay preserves every zone's annual mean.

    Gated on ``config.miso_winter_citygate_daily`` (tier 3, off by default) and
    ``config.iso == "MISO"``; zero fitted scalars (the measured daily series + the
    published Chicago-zone assignment). Backcast-only by construction (no forward
    Chicago daily rows). Mutates ``fuel_prices`` in place; idempotent.

    Args:
        fuel_prices: The ``(n_gen, T)`` delivered fuel-price array, updated in
            place for Chicago-hub gas generators in winter months.
        fleet: Vectorized fleet attributes; ``fuel_type_idx`` selects gas,
            ``zone_idx`` selects the Chicago-hub zones.
        config: Scenario configuration supplying ``miso_winter_citygate_daily``,
            ``gas_daily_shape``, ``iso`` and ``hours``.
        year: Calendar year keying the Chicago daily series and zone assignment.
        path: Optional override for the MISO zonal-hub CSV (zone selector).
        citygate_path: Optional override for the Chicago daily CSV.
    """
    if not getattr(config, "miso_winter_citygate_daily", False):
        return
    if config.iso.upper() != "MISO":
        return
    T = fuel_prices.shape[1]
    chicago = miso_chicago_daily_shape_factors(
        year,
        T,
        citygate_path,
        year_start_package=getattr(config, "gas_flow_date_year_start_package", False),
    )
    if not np.any(chicago != 1.0):
        return  # no Chicago daily quotes this year: inert (R4)
    national = (
        gas_daily_shape_factors(year, T)
        if getattr(config, "gas_daily_shape", False)
        else np.ones(T, dtype=float)
    )
    # Winter months only (the pipeline-scarcity heating season): swap the national
    # HH daily shape for the measured Chicago daily shape. Safe divide (national is
    # strictly positive shape factors; guard anyway).
    month0 = _month_index(T)  # 0-based month per hour
    winter = np.isin(month0, [m - 1 for m in _MISO_WINTER_MONTHS])
    correction = np.ones(T, dtype=float)
    valid = winter & (national > 0)
    correction[valid] = chicago[valid] / national[valid]
    if not np.any(correction != 1.0):
        return

    from market_sim.config.iso_configs import get_iso_config

    zone_names = get_iso_config(config.iso).zone_names
    chicago_zones = _miso_chicago_hub_zones(year, path)
    if not chicago_zones:
        return
    zone_is_chicago = np.array([zn in chicago_zones for zn in zone_names], dtype=bool)
    gas_rows = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
    if gas_rows.size == 0:
        return
    sel = gas_rows[zone_is_chicago[fleet.zone_idx[gas_rows]]]
    if sel.size == 0:
        return
    fuel_prices[sel, :] = np.maximum(
        fuel_prices[sel, :] * correction[np.newaxis, :], _GAS_PRICE_FLOOR
    )
    logger.info(
        "MISO winter citygate daily (%d): %d Chicago-hub gas units (zones %s) "
        "repriced at the measured Chicago daily shape in %d winter days; "
        "correction %.2f..%.2f (winter peak on the cold-snap flow days)",
        year,
        sel.size,
        ",".join(sorted(chicago_zones)),
        int(np.unique(np.nonzero(correction != 1.0)[0] // 24).size),
        float(correction.min()),
        float(correction.max()),
    )


# ---------------------------------------------------------------------------
# miso-224: gas offers at MARGINAL COMMODITY cost (measured daily hub spot), not
# the EIA-923 AVERAGE delivered cost.
# ---------------------------------------------------------------------------

#: Hub-table ``hub`` prefixes that select the Henry Hub daily series. Every other
#: MISO zone (Chicago Citygate zones AND the MidCon zones, see the applier
#: docstring) takes the Chicago Citygate daily series.
_MISO_HENRY_HUB_PREFIXES: tuple[str, ...] = ("gulf",)


#: The derived per-plant VARIABLE transport table (rule 23 ``[R-FROZEN-DERIVE]``),
#: written by ``scripts/data/derive_miso_gas_variable_transport.py`` from EIA-923
#: receipts against the same daily hub staircases this module prices gas rows
#: from.  Its sibling ``.pool.csv`` carries the declared fallback rungs.
MISO_GAS_VARIABLE_TRANSPORT_PATH = (
    Path(__file__).resolve().parents[4].parent
    / "data/raw/reference/miso_gas_variable_transport.csv"
)

_TRANSPORT_CACHE: dict[
    Path, tuple[dict[int, float], dict[str, float], dict[str, float], float]
] = {}


def _load_miso_gas_variable_transport(
    path: Path | None = None,
) -> tuple[dict[int, float], dict[str, float], dict[str, float], float]:
    """Return ``(by_plant, by_zone_group, by_group, miso_wide)`` transport rungs.

    The four rungs of the declared fallback ladder — own plant, ``zone|group``,
    ``group``, MISO-wide — in the order a consumer walks them.  Cached per path.
    An absent table yields empty rungs and a zero ISO-wide value; the caller
    (:func:`apply_miso_gas_marginal_commodity`) fails closed on that rather than
    silently pricing at the bare hub.
    """
    import csv

    resolved = Path(path) if path else MISO_GAS_VARIABLE_TRANSPORT_PATH
    if resolved in _TRANSPORT_CACHE:
        return _TRANSPORT_CACHE[resolved]
    by_plant: dict[int, float] = {}
    by_zone_group: dict[str, float] = {}
    by_group: dict[str, float] = {}
    miso_wide = 0.0
    if resolved.exists():
        with resolved.open() as handle:
            rows = [ln for ln in handle if not ln.startswith("#")]
        for row in csv.DictReader(rows):
            by_plant[int(row["plant_id"])] = float(row["v_usd_mmbtu"])
        pool = resolved.with_suffix(".pool.csv")
        if pool.exists():
            with pool.open() as handle:
                for row in csv.DictReader(handle):
                    value = float(row["v_usd_mmbtu"])
                    if row["rung"] == "zone_group":
                        by_zone_group[row["key"]] = value
                    elif row["rung"] == "group":
                        by_group[row["key"]] = value
                    else:
                        miso_wide = value
    out = (by_plant, by_zone_group, by_group, miso_wide)
    _TRANSPORT_CACHE[resolved] = out
    return out


def _miso_gas_variable_transport_vector(
    fleet: FleetArrays,
    rows: np.ndarray,
    zone_names: tuple[str, ...] | list[str],
    path: Path | None = None,
) -> np.ndarray:
    """Return the per-row variable transport ($/MMBtu) for ``rows``, ladder applied.

    Walks the declared ladder for each row: the plant's own measured ``v``, else
    its ``zone|group`` pooled rung, else its ``group`` rung, else the MISO-wide
    rung.  A row with no ``plant_code`` (an aggregated bin) starts at the
    ``zone|group`` rung, which is the finest rung it can be attributed to.
    """
    by_plant, by_zone_group, by_group, miso_wide = _load_miso_gas_variable_transport(
        path
    )
    groups = getattr(fleet, "plant_group", None)
    out = np.empty(rows.size, dtype=float)
    for i, g in enumerate(rows):
        code = int(fleet.plant_code[g]) if fleet.plant_code is not None else 0
        if code and code in by_plant:
            out[i] = by_plant[code]
            continue
        group = str(groups[g]) if groups is not None else ""
        zone = zone_names[int(fleet.zone_idx[g])]
        out[i] = by_zone_group.get(f"{zone}|{group}", by_group.get(group, miso_wide))
    return out


def _miso_zone_hub_kind(year: int, path: Path | None = None) -> dict[str, str]:
    """Return ``{zone: 'chicago' | 'henry'}`` from the published MISO hub table.

    Reads the SAME ``miso_zonal_gas_hub.csv`` (:data:`MISO_ZONAL_GAS_HUB_PATH`)
    the zonal basis and the winter overlay use (rule 5 — no new mapping). A
    ``hub`` string starting with one of :data:`_MISO_HENRY_HUB_PREFIXES` (the
    Gulf Coast row, MISO-South) maps to Henry Hub; every other row maps to
    Chicago Citygate. Empty when the table or the year is absent.
    """
    frame = _load_zonal_gas_hub(Path(path) if path else MISO_ZONAL_GAS_HUB_PATH)
    if frame is None or "hub" not in frame.columns:
        return {}
    sub = frame[frame["year"] == year]
    out: dict[str, str] = {}
    for r in sub.itertuples():
        hub = str(r.hub).strip().lower()
        out[str(r.zone)] = (
            "henry" if hub.startswith(_MISO_HENRY_HUB_PREFIXES) else "chicago"
        )
    return out


def apply_miso_gas_marginal_commodity(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
    citygate_path: Path | None = None,
    henry_hub_path: Path | None = None,
    transport_path: Path | None = None,
) -> np.ndarray | None:
    """Reprice EVERY MISO gas unit at the measured daily hub spot for its zone.

    The miso-224 arm. A dispatch offer is a MARGINAL cost: the commodity the next
    MMBtu costs at the hub, plus variable transport. The EIA-923 monthly print
    the backcast otherwise overlays (``gas_plant_monthly_fuel_pricing``) is the
    plant's AVERAGE delivered cost — commodity plus demand charges and contracted
    transport amortized over the month's takes — and it sits above the hub by an
    amount that grows as the commodity gets cheaper (miso-224 phase 0: the CC
    fleet's cap-weighted print exceeds the Chicago hub by +$0.5–1.3/MMBtu in most
    months of 2023–2025, +$2.6 in Feb-2024). Rule 14 ``[R-ACCURATE]``'s
    misalignment clause applies: both are measured, but the print is measured on
    a different basis (average) than the representation needs (marginal), so the
    reconciled measured input — the traded hub index — is preferred. Rule 13
    ``[R-MEASURED]``: a hub spot is a reproducible market input with a forward
    analogue (the forecast path already prices gas at hub + basis through
    ``resolve_annual_gas_price``; this makes the backcast use the SAME convention).

    Series, per zone (:func:`_miso_zone_hub_kind`, the published hub table):

    * Chicago Citygate zones (IL / IN / East) — the Chicago daily spot
      (:func:`~market_sim.data.fuel.hubs._miso_citygate_daily_dated`, the EIA NG
      Weekly "Chicago" row), a next-day index placed on its gas FLOW day by
      :func:`~market_sim.data.fuel.hubs._flow_date_staircase`;
    * the Gulf Coast zone (MISO-South) — Henry Hub daily
      (:func:`~market_sim.data.fuel.hubs._henry_hub_daily_dated`), a same-day
      spot placed by :func:`~market_sim.data.fuel.hubs._trade_date_staircase`;
    * the MidCon zones (West / Plains) — ALSO the Chicago series. No MidCon daily
      hub series is held under ``data/raw`` (``SOURCES_miso_citygate.md``: the EIA
      compact table carries no MidCon row); Chicago is the nearest accessible
      measured Midwest hub and MidCon indices trade at a small discount to it, so
      this is the conservative (slightly HIGH) reconciliation, documented here per
      rule 14 rather than guessed.

    Rule 19 ``[R-ONE-MECH]``: the daily hub series carries BOTH level and
    within-month shape, so the caller (``resolve_fuel_prices``) skips the winter
    Chicago SHAPE overlay (``apply_miso_winter_citygate_daily``) and returns the
    written mask so the mean-zero zonal basis increment is skipped on every gas
    row — the zone's hub already IS its regional level. Dual-fuel oil parity still
    runs afterwards and caps any winter blowout.

    ``config.miso_gas_variable_transport`` (miso-225) completes the offer the first
    sentence names. The owner ruled 2026-09-06, on this module's own miso-212 §8 /
    miso-224 §5 question, that a MISO gas offer is priced at marginal commodity
    **plus variable transport** — so the bare hub above is only half of it, and
    pricing at the bare hub is what killed the miso-224 arm on its dispatch gates
    (gas took 25 TWh from coal and imports because a real delivery cost had been
    removed with the demand charges). Armed, each gas row additionally carries its
    plant's MEASURED volume-invariant wedge over the hub, from the frozen derive
    ``scripts/data/derive_miso_gas_variable_transport.py`` (rule 23): the intercept
    of ``print - hub = v + F/burn`` over that plant's own 2023-2025 receipts, which
    keeps the usage charge, fuel retention and delivery-point basis it pays on the
    NEXT MMBtu and drops the reservation/demand charges it does not. Measured
    fleet-wide at ``v`` = $0.744/MMBtu capacity-weighted against a $1.179 total
    wedge, and for the margin-setting CC_REGULAR class $0.209 against $0.452 — so
    the ruled form drops 54 % of that class's print premium where the bare hub
    dropped 100 %. Zero fitted scalars; one value per plant across every scored
    year (rule 1 condition (b)). The flag is meaningless without the hub repricing
    and is refused on its own (rule 19: a transport adder ON TOP of the average
    print would double-count the transport the print already amortizes).

    Gated on ``config.miso_gas_marginal_commodity_pricing`` (off by default,
    byte-identical off). MISO-scoped: arming it on another ISO is a HARD ERROR
    (rule 25 — the cross-ISO cost-convention question is owner court, miso-212
    §8). FAIL CLOSED: an armed run whose year has no daily prints raises rather
    than silently keeping the prints it exists to replace.

    Returns the ``(n_gen, T)`` boolean mask of the cells written, or ``None``
    when off. Mutates ``fuel_prices`` in place; idempotent.
    """
    if not getattr(config, "miso_gas_marginal_commodity_pricing", False):
        if getattr(config, "miso_gas_variable_transport", False):
            raise ValueError(
                "miso_gas_variable_transport requires "
                "miso_gas_marginal_commodity_pricing: variable transport is an "
                "adder over the TRADED HUB, and adding it to the EIA-923 average "
                "print would double-count the transport that print already "
                "amortizes (rule 19 [R-ONE-MECH])"
            )
        return None
    if config.iso.upper() != "MISO":
        raise ValueError(
            "miso_gas_marginal_commodity_pricing is MISO-scoped (rule 25 "
            f"[R-ISO-SCOPE]) and was armed for {config.iso.upper()}; the "
            "average-vs-marginal delivered-cost convention is an owner-court, "
            "cross-ISO question (miso-212 §8) and no other ISO is wired here"
        )
    T = fuel_prices.shape[1]
    hubs = _pkg_ns()
    _chi_all = hubs._miso_citygate_daily_dated(citygate_path)
    chicago_daily = _flow_date_staircase(
        _chi_all.get(year, {}),
        year,
        prior_year_dated=(
            _chi_all.get(year - 1)
            if getattr(config, "gas_flow_date_year_start_package", False)
            else None
        ),
    )
    henry_daily = hubs._trade_date_staircase(
        hubs._henry_hub_daily_dated(henry_hub_path).get(year, {}), year
    )
    if chicago_daily is None or henry_daily is None:
        raise ValueError(
            f"MISO {year}: miso_gas_marginal_commodity_pricing is armed but the "
            f"daily hub series is missing (chicago={chicago_daily is not None}, "
            f"henry={henry_daily is not None}); refusing to keep the EIA-923 "
            "average prints the mechanism exists to replace"
        )
    series = {
        "chicago": np.repeat(chicago_daily, 24)[:T],
        "henry": np.repeat(henry_daily, 24)[:T],
    }
    if series["chicago"].size < T or series["henry"].size < T:
        raise ValueError(f"MISO {year}: daily hub series shorter than {T} hours")

    from market_sim.config.iso_configs import get_iso_config

    zone_names = get_iso_config(config.iso).zone_names
    kind_by_zone = _miso_zone_hub_kind(year, path)
    if not kind_by_zone:
        raise ValueError(f"MISO {year}: no hub-table rows to map zones to hubs")
    gas_rows = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
    written = np.zeros(fuel_prices.shape, dtype=bool)
    if gas_rows.size == 0:
        return written
    zone_kind = np.array(
        [kind_by_zone.get(zn, "chicago") for zn in zone_names], dtype=object
    )
    transport = None
    if getattr(config, "miso_gas_variable_transport", False):
        by_plant, _, _, _ = _load_miso_gas_variable_transport(transport_path)
        if not by_plant:
            raise ValueError(
                f"MISO {year}: miso_gas_variable_transport is armed but the derived "
                "table data/raw/reference/miso_gas_variable_transport.csv is absent "
                "or empty; refusing to price gas at the BARE hub, which is the "
                "miso-224 arm the owner ruling superseded"
            )
        transport = _miso_gas_variable_transport_vector(
            fleet, gas_rows, tuple(zone_names), transport_path
        )
    for kind in ("chicago", "henry"):
        mask = zone_kind[fleet.zone_idx[gas_rows]] == kind
        sel = gas_rows[mask]
        if sel.size == 0:
            continue
        level = series[kind][np.newaxis, :]
        if transport is not None:
            level = level + transport[mask][:, np.newaxis]
        fuel_prices[sel, :] = np.maximum(level, _GAS_PRICE_FLOOR)
        written[sel, :] = True
    logger.info(
        "MISO gas marginal-commodity pricing (%d): %d gas units repriced at the "
        "measured daily hub spot (Chicago Citygate %.2f..%.2f, Henry Hub %.2f..%.2f "
        "$/MMBtu) %s; EIA-923 average prints, the winter shape overlay and the zonal "
        "basis increment superseded on these rows (rule 19)",
        year,
        gas_rows.size,
        float(series["chicago"].min()),
        float(series["chicago"].max()),
        float(series["henry"].min()),
        float(series["henry"].max()),
        (
            "PLUS the derived per-plant variable transport "
            f"({float(transport.min()):+.3f}..{float(transport.max()):+.3f}, "
            f"mean {float(transport.mean()):+.3f} $/MMBtu)"
            if transport is not None
            else "with NO transport adder (the bare-hub miso-224 form)"
        ),
    )
    return written
