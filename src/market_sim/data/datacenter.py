"""Data-center load block + electrification adder (CX-4, gap G-34).

Implements the forecast-mode-only data-center (DC) demand block designed in
``docs/handoffs/cx4-datacenter-load-design-2026-07.md``. The DC boom is today
implicitly buried in the near-term ``DEMAND_GROWTH_RATES`` scalar, which grows a
*flat* load type with the system's *peaky* weather-year shape — overstating peak
growth and understating energy growth per MW of DC (memo §1). This module lifts
DC out into an explicit **flat load block**:

    block_mw = resolve_datacenter_mw(config, iso, year) * config.datacenter_load_factor

distributed across zones by :func:`datacenter_zone_shares`. Because the near-era
``DEMAND_GROWTH_RATES`` are TOTAL (DC-inclusive), :func:`add_datacenter_block`
**relocates** the block (scales the grown peaky demand down by the block's energy
fraction and adds it back flat, energy invariant) rather than naively adding it —
the growth x DC double-count fix (CX-4 §3.5 / FF-0D audit §1.6; full derivation in
that function's docstring). The block is a pure load quantity on the RHS of the
energy balance — NOT netted from renewables (it respects the CLAUDE.md convention
that load is on the RHS and renewables are LHS decision variables).

Rule-13 admissibility (CLAUDE.md rule 13): the block's MW trajectory comes from
published ISO large-load forecasts / interconnection queues
(``constants.DATACENTER_ADDITIONS_MW``) — a *forward driver* that regenerates
every forecast vintage and responds to changed conditions (queue withdrawals,
policy). It is never a backcast residual (rule 23): the block is
**forecast-mode-only** and :func:`validate_datacenter_config` (mirrored in
``ScenarioConfig.__post_init__``) raises if a non-``"off"`` DC path is set in
backcast mode, so it can never enter a scored keeper.

Default-off / byte-identity: ``ScenarioConfig.datacenter_load_path`` defaults to
``"off"``; :func:`add_datacenter_block` then returns the input ``year_demand``
unchanged (same object), so every current forecast/backcast run is byte-identical
until a scenario explicitly opts in.

**FF-G4 Option-B electrification layers (this module's second half).** The
CX-4 "electrification adder" successor designed in
``docs/handoffs/ff-g4-load-shape-design-memo-2026-07.md`` (§4.2/§5, owner box
D1 = Option B) is implemented here as additive END-USE LAYERS over the same
seam: per-ISO published annual-energy adoption anchors
(``constants.ELECTRIFICATION_LAYERS``) x a physical hourly profile per layer
(the ``heat_pump`` layer's heating-degree shape from the run weather year's
measured NOAA GHCN temperatures). :func:`add_load_layers` is the ONE fold-in
mechanism for all additive load layers (rule 19 ``[R-ONE-MECH]``): the DC
block is layer #1 and the electrification layers share its relocation algebra
(joint energy-invariant relocation, single sum-of-layers guard). Gated by
``ScenarioConfig.electrification_path`` (default ``"off"``,
backcast/hindcast-coerced off — the ``datacenter_load_path`` pattern), so
every keeper and every existing run is byte-identical until a scenario opts
in.
"""

from __future__ import annotations

import csv
from typing import TYPE_CHECKING, Callable

import numpy as np

from market_sim.config import paths
from market_sim.config.constants import (
    DATACENTER_ADDITIONS_MW,
    DATACENTER_ZONE_SHARE,
    ELECTRIFICATION_LAYERS,
    HEAT_PUMP_BALANCE_POINT_C,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import (
    _effective_percentile,
    _interpolate_low_mid_high,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from market_sim.config.scenarios import ScenarioConfig

# The scenario axis is off by default; "off" short-circuits every entry point to
# a no-op (memo §3.2). Kept as a module constant so callers and tests reference
# one spelling.
DATACENTER_PATH_OFF: str = "off"

# Valid path labels (memo §3.2): "off" (no block) plus the three PB-1 anchors.
DATACENTER_PATHS: tuple[str, ...] = ("off", "low", "mid", "high")


def _interp_year(curve: dict[int, float] | None, year: int) -> float | None:
    """Piecewise-linear interpolate a ``{year: cumulative_MW}`` curve at ``year``.

    Flat-extrapolates before the first anchor and after the last (``np.interp``
    default), matching the memo's "piecewise-linear between anchor years, flat
    after the last anchor" spec (§3.3). Returns ``None`` for an empty/missing
    curve so the caller can apply the low/mid/high fallback.

    Args:
        curve: Mapping of anchor year -> cumulative data-center MW, or ``None``.
        year: Simulation year to evaluate.

    Returns:
        Interpolated cumulative MW, or ``None`` if ``curve`` is empty/``None``.
    """
    if not curve:
        return None
    years = sorted(curve)
    xs = np.array(years, dtype=float)
    ys = np.array([curve[y] for y in years], dtype=float)
    return float(np.interp(float(year), xs, ys))


def resolve_datacenter_mw(config: "ScenarioConfig", iso: str, year: int) -> float:
    """Return cumulative data-center MW for ``iso`` in ``year`` under the DC lever.

    Mirrors :func:`market_sim.config.scenarios.resolve_demand_growth_rate`: it
    interpolates the low/mid/high ``{year: cumulative_MW}`` curves of
    :data:`constants.DATACENTER_ADDITIONS_MW` in *year* first, then across paths
    by the effective percentile from ``config.datacenter_load_path`` /
    ``config.datacenter_percentile`` (memo §3.4). ``path == "off"`` short-circuits
    to ``0.0``, as does an ISO with no published DC decomposition (MISO/NEISO ship
    ``{}`` per memo §2.2). A path missing from a partially-sourced ISO falls back
    to the mid curve (never silently extrapolates a fabricated anchor).

    Args:
        config: Scenario config supplying the DC path/percentile levers.
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Simulation year.

    Returns:
        Cumulative data-center MW (nameplate; the flat load-factor is applied by
        :func:`datacenter_block_mw_by_zone`). ``0.0`` when the block is off or
        unsourced for this ISO.
    """
    if config.datacenter_load_path == DATACENTER_PATH_OFF:
        return 0.0

    iso_table = DATACENTER_ADDITIONS_MW.get(iso, {})
    if not iso_table:
        return 0.0

    low = _interp_year(iso_table.get("low"), year)
    mid = _interp_year(iso_table.get("mid"), year)
    high = _interp_year(iso_table.get("high"), year)

    # Fallback chain: mid anchors the axis. A missing mid borrows whichever of
    # low/high is published (else 0); low/high missing collapse onto mid. This
    # keeps a partially-sourced ISO from fabricating an anchor it lacks.
    if mid is None:
        mid = low if low is not None else (high if high is not None else 0.0)
    if low is None:
        low = mid
    if high is None:
        high = mid

    percentile = _effective_percentile(
        config.datacenter_load_path, config.datacenter_percentile
    )
    return _interpolate_low_mid_high(percentile, low, mid, high)


def datacenter_zone_shares(iso: str, zone_names: list[str]) -> np.ndarray:
    """Return the per-zone allocation shares for the data-center block.

    Default is each zone's ``load_share`` from
    :mod:`market_sim.config.iso_configs` (memo §3.3); an ISO present in
    :data:`constants.DATACENTER_ZONE_SHARE` overrides that with published siting
    geography. Shares are returned in ``zone_names`` order and sum to ~1.0, so
    the flat block's total energy is conserved regardless of allocation.

    Args:
        iso: ISO identifier.
        zone_names: Zone names in LP column order (from
            ``ISOConfig.zone_names``).

    Returns:
        ``(n_zones,)`` float array of allocation shares summing to ~1.0.

    Raises:
        ValueError: if an override table is present but its shares do not sum to
            ~1.0 (a mis-entered siting table would silently rescale the block).
    """
    override = DATACENTER_ZONE_SHARE.get(iso)
    if override:
        shares = np.array([override.get(z, 0.0) for z in zone_names], dtype=float)
        total = float(shares.sum())
        if not np.isclose(total, 1.0, atol=1e-6):
            raise ValueError(
                f"DATACENTER_ZONE_SHARE[{iso!r}] shares sum to {total:.6f}, "
                "expected 1.0 (memo §3.3 — siting shares must conserve the block "
                "energy)."
            )
        return shares

    return _load_share_zone_shares(iso, zone_names)


def _load_share_zone_shares(iso: str, zone_names: list[str]) -> np.ndarray:
    """Return each zone's ``load_share`` from :mod:`iso_configs`, in LP order.

    The memo §3.3 default allocation, shared by the DC block (absent a
    published siting override) and the electrification layers (heating/EV
    adoption tracks population/load; no per-zone electrification split is
    published for any ISO yet — a documented limitation, refined only when a
    source lands, rule 23 ``[R-FROZEN-DERIVE]``).

    Args:
        iso: ISO identifier.
        zone_names: Zone names in LP column order.

    Returns:
        ``(n_zones,)`` float array of load shares summing to ~1.0.
    """
    iso_config = get_iso_config(iso)
    by_name = {zone.name: zone.load_share for zone in iso_config.zones}
    return np.array([by_name.get(z, 0.0) for z in zone_names], dtype=float)


def datacenter_block_mw_by_zone(
    config: "ScenarioConfig", iso: str, year: int, zone_names: list[str]
) -> np.ndarray:
    """Return the flat per-zone data-center block MW for ``year``.

    ``dc_mw × datacenter_load_factor`` distributed across zones by
    :func:`datacenter_zone_shares` (memo §3.4). Because the block is flat, this
    single per-zone MW vector is added to *every* hour, so ``ΔEnergy = block_mw ×
    8760`` and ``Δpeak = block_mw`` (both closed-form; the block adds no shape).
    Returns a zero vector when the block is off or unsourced for this ISO.

    Args:
        config: Scenario config supplying the DC levers and ``datacenter_load_factor``.
        iso: ISO identifier.
        year: Simulation year.
        zone_names: Zone names in LP column order.

    Returns:
        ``(n_zones,)`` float array of flat MW to add to each zone every hour.
    """
    dc_mw = resolve_datacenter_mw(config, iso, year)
    if dc_mw == 0.0:
        return np.zeros(len(zone_names), dtype=float)
    block_mw = dc_mw * config.datacenter_load_factor
    shares = datacenter_zone_shares(iso, zone_names)
    return block_mw * shares


def datacenter_block_energy_mwh(
    config: "ScenarioConfig", iso: str, year: int, zone_names: list[str], n_hours: int
) -> float:
    """Return the data-center block's annual energy in MWh for ``year``.

    The DC-linked voluntary-demand volume helper (SCN-WS3b; the voluntary
    clean-demand design memo §3.1): ``E_DC(ISO, y) = Σ_z block_mw[z] × T``,
    the closed form the flat block admits (``ΔEnergy = block_mw × 8760``,
    :func:`datacenter_block_mw_by_zone`). Read-only over the block the model
    already builds — the same MW vector :func:`add_load_layers` folds into
    demand — so the voluntary row's DC half and the served demand's DC block
    are ONE quantity (memo §3.4: never counted twice). ``0.0`` whenever the
    block is off or unsourced for this ISO (the resolver then sizes the
    volume on the non-DC baseline alone).

    Args:
        config: Scenario config supplying the DC levers and
            ``datacenter_load_factor``.
        iso: ISO identifier.
        year: Simulation year.
        zone_names: Zone names in LP column order.
        n_hours: Hours in the demand array the block is folded into (8760 in
            a full-year solve; the caller's ``T`` in a trivial-first test).

    Returns:
        The block's energy in MWh (``>= 0.0``).
    """
    per_zone = datacenter_block_mw_by_zone(config, iso, year, zone_names)
    return float(per_zone.sum()) * float(n_hours)


def add_datacenter_block(
    year_demand: np.ndarray,
    config: "ScenarioConfig",
    iso: str,
    year: int,
    zone_names: list[str],
) -> np.ndarray:
    """Fold the flat data-center load block into a ``(n_zones, T)`` demand array.

    **DC-only special case — the runner seam is** :func:`add_load_layers`
    (FF-G4, rule 19 [R-ONE-MECH]), which folds this block jointly with the
    electrification layers and reproduces this function bit-exactly when the
    electrification axis is off. Kept as the standalone DC entry point for
    tests and analysis; never call BOTH on the same demand array (the block
    would fold twice).

    The demand-assembly consumer (memo §3.4): call it immediately after
    ``_scale_demand`` and before ``peak_demand`` is taken, so peak, energy, and
    every capacity screen downstream pick the block up for free. Vectorized —
    broadcasts the per-zone flat MW over all ``T`` hours, no hour loop (rule 2).

    **Relocation, not naive addition — the growth x DC double-count fix**
    (CX-4 §3.5 / FF-0D audit §1.6). The near-era ``DEMAND_GROWTH_RATES`` are
    TOTAL (data-center-inclusive: the scaled ``year_demand`` already carries the
    DC boom, spread across the system's *peaky* weather-year shape). Naively
    adding the block on top would count DC twice. Instead this **relocates** the
    block's energy: it scales the grown (peaky) demand down by exactly the block's
    energy fraction and adds the block back **flat**, so total energy is
    invariant and only the hourly *shape* changes (DC's defining flatness is
    restored, lowering peak). This is algebraically identical to the memo's
    "re-derive the rate as organic-ex-DC, then add the block" co-change, but is
    computed from the block MW itself — so it is robust to the demand-growth and
    DC levers being moved independently (no reliance on a separately-keyed organic
    rate). Concretely, with ``E = year_demand.sum()`` and ``dc_E = block_mw x T``:

        year_demand := year_demand * (1 - dc_E / E) + block_mw      (relocate)

    which conserves energy exactly (``E * (1 - dc_E/E) + dc_E == E``). The scale
    factor decomposes the grown total into its organic and DC-embedded parts
    (both grew at the same total rate, so they are proportional): scaling by
    ``1 - dc_E/E`` extracts the organic-peaky component, and the flat block
    replaces the DC-peaky component it removed.

    **Tail regime (full-queue / high paths).** When the block's energy meets or
    exceeds the grown demand's energy (``dc_E >= E`` — e.g. an ERCOT "high"
    full-credible-queue path whose DC alone tops the total forecast), there is no
    containable DC to relocate: the block is genuinely *incremental* load beyond
    the ISO's total forecast, so it is **added** (``year_demand + block``). The
    MID path of every ISO sits in the relocate regime (the DC block is inside the
    published total), so the decision-relevant BAU case is always energy-invariant.

    Default-off byte-identity: when ``datacenter_load_path == "off"`` (or the ISO
    ships no DC block) the input ``year_demand`` is returned **unchanged (same
    object)**, guaranteeing zero blast radius on every existing run.

    Args:
        year_demand: ``(n_zones, T)`` scaled hourly demand (MW), zones in LP order.
        config: Scenario config supplying the DC levers.
        iso: ISO identifier.
        year: Simulation year.
        zone_names: Zone names in ``year_demand`` row order.

    Returns:
        ``year_demand`` with the flat DC block **relocated** in (energy-invariant,
        a new array), the block **added** (tail regime), or the input array
        unchanged (same object) when the block is off/unsourced.
    """
    per_zone = datacenter_block_mw_by_zone(config, iso, year, zone_names)
    if not per_zone.any():
        return year_demand
    n_hours = year_demand.shape[1]
    dc_energy = float(per_zone.sum()) * n_hours
    total_energy = float(year_demand.sum())
    # Relocate regime: the DC block is contained within the (DC-inclusive) grown
    # demand -> scale the peaky total down by the block's energy fraction and add
    # the block back flat, holding total energy invariant (no double-count).
    if total_energy > 0.0 and dc_energy < total_energy:
        scale = 1.0 - dc_energy / total_energy
        return year_demand * scale + per_zone[:, None]
    # Tail regime: the block equals/exceeds the total forecast -> genuinely
    # incremental load, added on top (documented above).
    return year_demand + per_zone[:, None]


def validate_datacenter_config(config: "ScenarioConfig") -> None:
    """Raise if the data-center block is enabled in an inadmissible configuration.

    Enforces the memo's holdout/forecast-only discipline (§6.1.5, rule 22): the
    block is forecast-mode-only, so a non-``"off"`` DC path in backcast mode is a
    hard error (a backcast pins measured load; the block must never enter a scored
    backcast). Also validates the path label. Mirrored in
    ``ScenarioConfig.__post_init__`` so misconfiguration fails at construction.

    Args:
        config: Scenario config to check.

    Raises:
        ValueError: if ``datacenter_load_path`` is unknown, or a non-``"off"``
            path is set with ``mode == "backcast"``.
    """
    if config.datacenter_load_path not in DATACENTER_PATHS:
        raise ValueError(
            "ScenarioConfig.datacenter_load_path must be one of "
            f"{DATACENTER_PATHS}, got {config.datacenter_load_path!r}"
        )
    if config.mode == "backcast" and config.datacenter_load_path != DATACENTER_PATH_OFF:
        raise ValueError(
            "datacenter_load_path is a forecast-only scenario axis and must be "
            "'off' in backcast mode (rule 22 holdout discipline / memo §6): a "
            "backcast pins measured load, so the DC block must never enter a "
            f"scored backcast. Got datacenter_load_path={config.datacenter_load_path!r}."
        )


def validate_electrification_config(config: "ScenarioConfig") -> None:
    """Raise if the electrification layers are enabled inadmissibly.

    The FF-G4 mirror of :func:`validate_datacenter_config` (memo §4.2
    "backcast identity: the FF-1F/CX-4 pattern verbatim"): the layers are
    forecast-mode-only — a backcast/hindcast pins measured load, which already
    contains realized electrification, so a non-``"off"``
    ``electrification_path`` in backcast mode is a hard error. Mirrored in
    ``ScenarioConfig.__post_init__`` (which COERCES it off in
    backcast/hindcast) so misconfiguration fails at construction; this
    standalone check is defense in depth against a post-construction
    mutation/bypass.

    Args:
        config: Scenario config to check.

    Raises:
        ValueError: if ``electrification_path`` is unknown, or a non-``"off"``
            path is set with ``mode == "backcast"``.
    """
    if config.electrification_path not in ELECTRIFICATION_PATHS:
        raise ValueError(
            "ScenarioConfig.electrification_path must be one of "
            f"{ELECTRIFICATION_PATHS}, got {config.electrification_path!r}"
        )
    if (
        config.mode == "backcast"
        and config.electrification_path != ELECTRIFICATION_PATH_OFF
    ):
        raise ValueError(
            "electrification_path is a forecast-only scenario axis and must be "
            "'off' in backcast mode (rule 22 holdout discipline / FF-G4 memo "
            "§4.2): a backcast pins measured load — which already contains "
            "realized electrification — so the layers must never enter a "
            f"scored backcast. Got electrification_path="
            f"{config.electrification_path!r}."
        )


# ---------------------------------------------------------------------------
# FF-G4 Option-B electrification end-use layers (memo §4.2/§5)
# ---------------------------------------------------------------------------
# The CX-4 "electrification adder" stub that lived here (all-zero
# ``electrification_shape``) is SUPERSEDED by this machinery (rule 26
# [R-DELETE]: the deferred interface is replaced, not kept beside the real
# thing). One scenario axis (``electrification_path``, "off" gates), the
# DATACENTER_PATHS grammar, the DC anchor-interpolation chain, and ONE fold-in
# for all additive layers (:func:`add_load_layers`, rule 19 [R-ONE-MECH]).

# Valid electrification path labels — the DC grammar verbatim (memo §5.1).
ELECTRIFICATION_PATH_OFF: str = "off"
ELECTRIFICATION_PATHS: tuple[str, ...] = ("off", "low", "mid", "high")

# Layer name -> hourly-profile builder ``(iso, weather_year, hours) ->
# (hours,) normalized profile``. FAIL-CLOSED registry: a layer whose adoption
# anchors are populated for an ISO but which has no profile source registered
# here REFUSES to arm (add_load_layers raises) rather than silently inventing
# a shape — which is why constants.ELECTRIFICATION_LAYERS ships ``ev: {}``
# everywhere until a citable charging profile lands (memo §8-D4 items 1/7).
_LAYER_PROFILE_BUILDERS: dict[str, Callable[[str, int, int], np.ndarray]] = {}


def resolve_electrification_gwh(
    config: "ScenarioConfig", iso: str, layer: str, year: int
) -> float:
    """Return the ``layer``'s incremental annual energy (GWh) for ``iso``/``year``.

    Mirrors :func:`resolve_datacenter_mw` on the
    :data:`constants.ELECTRIFICATION_LAYERS` adoption anchors: interpolate the
    low/mid/high ``{year: GWh}`` curves in *year* first (piecewise-linear,
    flat-hold outside the anchors), then across paths by the effective
    percentile from ``config.electrification_path`` /
    ``config.electrification_percentile``. ``path == "off"`` short-circuits to
    ``0.0``, as does an ISO or layer with no published anchors (ships ``{}``,
    memo §4.2 "no source ⇒ status quo, honestly documented"). A missing
    low/high collapses onto mid (never an invented band).

    The returned energy is INCREMENTAL TO THE WEATHER-YEAR BASE (the measured
    base 8760 already carries realized electrification; see the constants-table
    comment), and is *relocated*, not added, by :func:`add_load_layers`.

    Args:
        config: Scenario config supplying the electrification levers.
        iso: ISO identifier, e.g. ``"NEISO"``.
        layer: Layer name, e.g. ``"heat_pump"`` / ``"ev"``.
        year: Simulation year.

    Returns:
        Incremental annual layer energy in GWh; ``0.0`` when off or unsourced.
    """
    if config.electrification_path == ELECTRIFICATION_PATH_OFF:
        return 0.0

    curves = ELECTRIFICATION_LAYERS.get(iso, {}).get(layer, {})
    if not curves:
        return 0.0

    low = _interp_year(curves.get("low"), year)
    mid = _interp_year(curves.get("mid"), year)
    high = _interp_year(curves.get("high"), year)

    # Fallback chain (identical to resolve_datacenter_mw): mid anchors the
    # axis; a missing mid borrows whichever of low/high is published (else 0);
    # missing low/high collapse onto mid — a partially-sourced layer never
    # fabricates an anchor it lacks.
    if mid is None:
        mid = low if low is not None else (high if high is not None else 0.0)
    if low is None:
        low = mid
    if high is None:
        high = mid

    percentile = _effective_percentile(
        config.electrification_path, config.electrification_percentile
    )
    return _interpolate_low_mid_high(percentile, low, mid, high)


def heat_pump_layer_profile(iso: str, weather_year: int, hours: int) -> np.ndarray:
    """Return the heat-pump layer's normalized hourly profile for ``iso``.

    Physics construction (memo §4.2's "physics/end-use simulation" profile
    class, rule 13 [R-MEASURED] admissible — regenerates for any forward year
    from its weather driver and responds to changed conditions): hourly
    heating-degree ``HDH(h) = max(0, base − T(h))`` at the standard 65 °F /
    18.3 °C NOAA/EIA balance point (:data:`constants.HEAT_PUMP_BALANCE_POINT_C`),
    where ``T(h)`` is the run weather year's measured NOAA GHCN daily
    zone-mean TMIN/TMAX (sentinel aggregate zones excluded) bridged to hourly
    by the Parton & Logan (1981) two-piece cosine already on main
    (:func:`market_sim.data.eia930.weather.diurnal_drybulb_from_daily` — one
    reconstruction mechanism, rule 19). Normalized to sum to 1 over the run
    horizon, so ``energy × profile`` conserves the layer energy exactly.

    The profile is weather-year-aligned BY CONSTRUCTION (memo §5.4: a cold
    weather year stresses the HP layer coherently with the base load it sits
    on). Its winter-morning ridge emerges from the temperature series (TMIN at
    the pre-dawn anchor), not from a tuned shape. DOCUMENTED LIMITATION: linear
    degree-hours omit cold-climate COP rolloff / resistance backup, so the
    extreme-cold peak contribution is understated relative to the CELT HEF
    winter-peak context row — the refinement is a published HP performance
    curve (memo §8-D4), never a residual fit.

    Args:
        iso: ISO identifier.
        weather_year: The run's weather (shape base) year.
        hours: Number of run hours (typically 8760).

    Returns:
        ``(hours,)`` non-negative float array summing to 1.0.

    Raises:
        ValueError: when the ISO/weather-year has no usable TMIN/TMAX archive
            or produces zero heating degrees — an ARMED layer with no shape
            source is a hard misconfiguration, never a silent no-op.
    """
    from market_sim.data.eia930.weather import (
        _broadcast_daily_to_hourly,
        diurnal_drybulb_from_daily,
        load_weather,
    )

    df = load_weather(iso, int(weather_year))
    if df is not None:
        # Real weather zones only: the '_load_weighted' / '_downstate'
        # sentinels are aggregates of the same stations and would double-weight
        # them in the plain zone mean (the correlated-outage TMIN convention).
        df = df[~df["zone"].astype(str).str.startswith("_")]
        df = df.dropna(subset=["tmax_c", "tmin_c"])
    if df is None or df.empty:
        raise ValueError(
            f"heat_pump layer is armed for {iso} but weather year "
            f"{weather_year} has no usable TMIN/TMAX archive "
            f"(data/raw/{iso.lower()}-weather) — an armed layer never "
            "degrades silently."
        )
    daily = df.groupby("date")[["tmax_c", "tmin_c"]].mean().reset_index()
    tmax = _broadcast_daily_to_hourly(daily, int(weather_year), hours, "tmax_c")
    tmin = _broadcast_daily_to_hourly(daily, int(weather_year), hours, "tmin_c")
    if tmax is None or tmin is None:
        raise ValueError(
            f"heat_pump layer: could not broadcast {iso} weather year "
            f"{weather_year} daily TMIN/TMAX to the {hours}-hour horizon."
        )
    drybulb = diurnal_drybulb_from_daily(tmin, tmax, int(weather_year), hours)
    hdh = np.clip(HEAT_PUMP_BALANCE_POINT_C - drybulb, 0.0, None)
    total = float(hdh.sum())
    if total <= 0.0:
        raise ValueError(
            f"heat_pump layer: {iso} weather year {weather_year} produces zero "
            f"heating degrees at the {HEAT_PUMP_BALANCE_POINT_C} °C balance "
            "point — the layer cannot be shaped."
        )
    return hdh / total


_LAYER_PROFILE_BUILDERS["heat_pump"] = heat_pump_layer_profile


# ISO -> the published hourly EV charging series curated under
# ``data/raw/load-forecast/<iso>/``. RULE 25 [R-ISO-SCOPE]: this is a per-ISO
# registry, not a shared default — an ISO absent from it has no citable shape
# and its ``ev`` layer refuses to arm rather than borrowing another market's
# charging behaviour. ERCOT is the only entry because it is the only publisher
# that issues the shape as DATA (the 2025 Adjusted LTLF workbook's hourly
# ``<zone>_ev`` component); ISO-NE, NYISO and MISO publish adoption anchors but
# describe the shape in charts or defer to third-party (NREL/DOE) profiles, so
# their anchors sit in the curated datatype and their layers ship ``{}``
# (``constants.ELECTRIFICATION_LAYERS``).
_EV_PROFILE_SOURCES: dict[str, tuple[str, ...]] = {
    "ERCOT": ("load-forecast", "ercot", "ercot_ev_hourly_profile_2030.csv"),
}


def ev_layer_profile(iso: str, weather_year: int, hours: int) -> np.ndarray:
    """Return the EV layer's normalized hourly profile for ``iso``.

    Published-behaviour construction (memo §4.2's "published hourly component"
    profile class, rule 13 [R-MEASURED] admissible): the ISO's own hourly EV
    charging series, normalized to sum to 1 over the run horizon so
    ``energy × profile`` conserves the layer energy exactly. It regenerates for
    a forward year by re-reading the next forecast vintage's component and
    responds to changed conditions (managed-charging adoption, fleet mix)
    because the publisher re-forecasts it — it is never a realized outcome fed
    back.

    Unlike :func:`heat_pump_layer_profile`, this shape is **not** weather-year
    aligned: EV charging is behaviourally driven (time-of-day and day-of-week),
    which is why the publisher issues one seasonal-diurnal shape rather than a
    weather reconstruction. ``weather_year`` is therefore accepted for interface
    parity and deliberately unused; the profile is tiled/truncated to ``hours``.

    Args:
        iso: ISO identifier.
        weather_year: The run's weather (shape base) year — unused, see above.
        hours: Number of run hours (typically 8760).

    Returns:
        ``(hours,)`` non-negative float array summing to 1.0.

    Raises:
        ValueError: when the ISO has no registered published profile, or its
            curated file is missing or degenerate — an ARMED layer with no shape
            source is a hard misconfiguration, never a silent no-op.
    """
    parts = _EV_PROFILE_SOURCES.get(iso.upper())
    if parts is None:
        raise ValueError(
            f"ev layer is armed for {iso} but no published hourly charging "
            f"profile is registered for it (have: {sorted(_EV_PROFILE_SOURCES)}). "
            "A shape that cannot be cited is not a parameter (rule 5 "
            "[R-NO-MAGIC]), and another ISO's profile is never a fallback "
            "(rule 25 [R-ISO-SCOPE])."
        )
    path = paths.RAW_DIR.joinpath(*parts)
    if not path.is_file():
        raise ValueError(
            f"ev layer is armed for {iso} but its curated hourly profile is "
            f"missing at {path} — hydrate the load-forecast raw subtree "
            "(scripts/hydrate_data.py) or re-run "
            "scripts/data/curate_load_forecast.py."
        )
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        shares = np.array([float(row["share"]) for row in reader], dtype=float)
    if shares.size == 0 or not np.isfinite(shares).all() or shares.sum() <= 0.0:
        raise ValueError(
            f"ev layer: {iso} profile at {path} is empty or degenerate "
            f"({shares.size} rows) — the layer cannot be shaped."
        )
    if shares.size < hours:
        shares = np.tile(shares, int(np.ceil(hours / shares.size)))
    shares = shares[:hours]
    return shares / float(shares.sum())


_LAYER_PROFILE_BUILDERS["ev"] = ev_layer_profile


def electrification_layer_contributions(
    config: "ScenarioConfig",
    iso: str,
    year: int,
    zone_names: list[str],
    hours: int,
) -> list[tuple[str, float, np.ndarray]]:
    """Return the active electrification layers' hourly demand contributions.

    Per layer (sorted by name for determinism): resolve the incremental annual
    energy from the adoption anchors, build the layer's normalized hourly
    profile for the run's weather year, and allocate across zones by
    ``load_share`` (:func:`_load_share_zone_shares` — no per-zone
    electrification split is published yet). Zero-energy layers are skipped;
    a layer with anchors but no registered profile builder raises
    (fail-closed — a shape we cannot cite is a blocker, not a parameter).

    Args:
        config: Scenario config supplying the electrification levers and
            ``weather_year`` (the profile's shape base).
        iso: ISO identifier.
        year: Simulation year.
        zone_names: Zone names in LP column order.
        hours: Number of run hours (matches ``year_demand.shape[1]``).

    Returns:
        List of ``(layer_name, energy_mwh, (n_zones, hours) contribution)``;
        empty when the axis is off or the ISO ships no sourced layer.
    """
    if config.electrification_path == ELECTRIFICATION_PATH_OFF:
        return []
    out: list[tuple[str, float, np.ndarray]] = []
    shares: np.ndarray | None = None
    for layer in sorted(ELECTRIFICATION_LAYERS.get(iso, {})):
        energy_gwh = resolve_electrification_gwh(config, iso, layer, year)
        if energy_gwh <= 0.0:
            continue
        builder = _LAYER_PROFILE_BUILDERS.get(layer)
        if builder is None:
            raise ValueError(
                f"ELECTRIFICATION_LAYERS[{iso!r}][{layer!r}] carries adoption "
                "anchors but no profile source is registered for the layer — "
                "an uncited shape is an open blocker, not a parameter "
                "(rule 5; memo §4.2). Ship the anchors {} until the profile "
                "intake lands."
            )
        profile = builder(iso, int(config.weather_year), hours)
        if shares is None:
            shares = _load_share_zone_shares(iso, zone_names)
        energy_mwh = energy_gwh * 1000.0
        # Outer product: zone share × normalized hourly profile × annual MWh.
        # shares sums to ~1 and profile to 1, so the contribution's total
        # energy equals energy_mwh (conservation by construction).
        out.append((layer, energy_mwh, energy_mwh * shares[:, None] * profile[None, :]))
    return out


def add_load_layers(
    year_demand: np.ndarray,
    config: "ScenarioConfig",
    iso: str,
    year: int,
    zone_names: list[str],
) -> np.ndarray:
    """Fold ALL additive load layers (DC + electrification) into demand.

    THE demand-assembly seam (memo §5.3, rule 19 [R-ONE-MECH]): one fold-in
    mechanism for every additive load layer, called immediately after
    ``_scale_demand`` and before ``peak_demand`` is taken. The DC block is
    layer #1; the FF-G4 electrification layers (heat_pump/ev) share its
    relocation algebra under a single sum-of-layers guard:

    - **Relocate regime** (``Σ layer energies < grown total``): the near-era
      ``DEMAND_GROWTH_RATES`` are TOTAL (DC- and electrification-inclusive),
      so each layer's energy is relocated — the grown peaky demand is scaled
      down by the layers' combined energy fraction and each layer is added
      back on its OWN shape. Total energy is invariant; only the hourly shape
      moves. Layers are disjoint end-uses (DC ≠ EV ≠ space heating), each
      relocating its own energy exactly once — no double-count (memo §4.2).
    - **Tail regime** (``Σ ≥ total``, e.g. an ERCOT high full-queue DC path):
      no containable energy to relocate — the layers are genuinely incremental
      and are added on top (the pre-existing DC tail branch, generalized).

    DC-only bit-identity: with the electrification axis off this computes
    literally ``year_demand * (1 - dc_E/E) + dc_block`` — the exact
    :func:`add_datacenter_block` expression — so every existing forecast run
    (DC "mid" default) is bit-identical through the refactor. With everything
    off/unsourced the input array is returned **unchanged (same object)**.

    Args:
        year_demand: ``(n_zones, T)`` scaled hourly demand (MW), zones in LP order.
        config: Scenario config supplying the DC + electrification levers.
        iso: ISO identifier.
        year: Simulation year.
        zone_names: Zone names in ``year_demand`` row order.

    Returns:
        ``year_demand`` with all active layers folded in (a new array), or the
        input array unchanged (same object) when every layer is off/unsourced.
    """
    n_hours = year_demand.shape[1]
    dc_per_zone = datacenter_block_mw_by_zone(config, iso, year, zone_names)
    elec = electrification_layer_contributions(config, iso, year, zone_names, n_hours)
    if not dc_per_zone.any() and not elec:
        return year_demand

    dc_energy = float(dc_per_zone.sum()) * n_hours
    elec_energy = sum(energy for _, energy, _ in elec)
    relocate_energy = dc_energy + elec_energy
    total_energy = float(year_demand.sum())
    # Relocate regime: the layers are contained within the (layer-inclusive)
    # grown total -> scale the peaky demand down by their combined energy
    # fraction and add each back on its own shape (energy-invariant).
    if total_energy > 0.0 and relocate_energy < total_energy:
        scale = 1.0 - relocate_energy / total_energy
        out = year_demand * scale
    else:
        # Tail regime: genuinely incremental load beyond the ISO's total
        # forecast, added on top (documented above).
        out = year_demand.copy()
    if dc_per_zone.any():
        out = out + dc_per_zone[:, None]
    for _layer, _energy, contribution in elec:
        out = out + contribution
    return out
