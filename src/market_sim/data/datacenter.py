"""Data-center load block + electrification adder (CX-4, gap G-34).

Implements the forecast-mode-only data-center (DC) demand block designed in
``docs/handoffs/cx4-datacenter-load-design-2026-07.md``. The DC boom is today
implicitly buried in the near-term ``DEMAND_GROWTH_RATES`` scalar, which grows a
*flat* load type with the system's *peaky* weather-year shape — overstating peak
growth and understating energy growth per MW of DC (memo §1). This module lifts
DC out into an explicit **flat load block** added to demand:

    block_mw = resolve_datacenter_mw(config, iso, year) * config.datacenter_load_factor

distributed across zones by :func:`datacenter_zone_shares` and added to every
hour of the year_demand array (a pure additive load block — NOT netted from
renewables; it respects the CLAUDE.md energy-balance convention that load is on
the RHS of the balance and renewables are LHS decision variables).

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

The electrification shape adder (memo §4) is a documented successor and is NOT
built here; see :func:`electrification_shape` for the deferred-interface note.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from market_sim.config.constants import (
    DATACENTER_ADDITIONS_MW,
    DATACENTER_ZONE_SHARE,
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


def add_datacenter_block(
    year_demand: np.ndarray,
    config: "ScenarioConfig",
    iso: str,
    year: int,
    zone_names: list[str],
) -> np.ndarray:
    """Add the flat data-center load block to a ``(n_zones, T)`` demand array.

    The demand-assembly consumer (memo §3.4): call it immediately after
    ``_scale_demand`` and before ``peak_demand`` is taken, so peak, energy, and
    every capacity screen downstream pick the block up for free. Vectorized —
    broadcasts the per-zone flat MW over all ``T`` hours, no hour loop (rule 2).

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
        ``year_demand`` with the flat DC block added (a new array), or the input
        array unchanged when the block is off/unsourced.
    """
    per_zone = datacenter_block_mw_by_zone(config, iso, year, zone_names)
    if not per_zone.any():
        return year_demand
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


def electrification_shape(
    config: "ScenarioConfig", iso: str, year: int, n_hours: int
) -> np.ndarray:
    """Return the additive electrification hourly profile (deferred stub).

    Design successor from memo §4: an additive, *shape-bearing* profile
    (winter-morning + evening heat-pump ridge, EV evening peak) scaled by a
    per-ISO annual TWh trajectory (NREL Electrification Futures Study). Unlike the
    flat DC block it reshapes hours — the capability a demand-growth scalar lacks.
    The sourced per-ISO profiles are **deferred** (memo §4, §10.3); this interface
    ships returning an all-zero profile so ``"off"`` is a true no-op and the
    demand-assembly seam exists for when the profiles land.

    Args:
        config: Scenario config (``electrification_shape_path`` selector, deferred).
        iso: ISO identifier.
        year: Simulation year.
        n_hours: Length of the hourly horizon (typically 8760).

    Returns:
        ``(n_hours,)`` float array of additive MW; all zeros until profiles land.
    """
    return np.zeros(int(n_hours), dtype=float)
