"""Shared EIA-930 frame plumbing for :mod:`market_sim.data.eia930`.

Path constants, the non-leap hour-calendar anchor, the clean-data consumption
seam, and the per-BA ``<BA> hourly`` extract loaders that every other module
in the package (demand, envelopes, actuals, zonal shares) reads its frames
through. Split out of ``data/eia_loader.py`` as pure code motion (W-D2,
2026-07-20); the facade module aliases that historical import path to this
package, so the compatibility contract lives there.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import EIA_930_DIR, EIA_HOURLY_DIR, RAW_DIR

# The package keeps the pre-split logger name: logging config and the
# ``assertLogs("market_sim.data.eia_loader")`` assertions in the test suite
# key on it (the split is code motion, not a logging rename). Every module in
# the package shares this one logger.
logger = logging.getLogger("market_sim.data.eia_loader")


# Default location of the EIA-930 parquet extracts (from the central registry).
DATA_DIR: Path = EIA_930_DIR


# Cumulative hours before the first of each 1-based month, non-leap calendar,
# for mapping a (month, day, hour) to an hour-of-year index in [0, 8760).
_MONTH_START_HOUR: tuple[int, ...] = tuple(
    int(sum((31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[:m]) * 24)
    for m in range(12)
)

_DEMAND_PROFILES_FILE = "eia_demand_profiles.parquet"
_DEMAND_META_FILE = "eia_demand_meta.parquet"
_GENERATION_PROFILES_FILE = "eia_generation_profiles.parquet"


# Per-BA wide EIA-930 hourly extracts live here, one ``<BA> hourly.parquet``
# per balancing authority (built from the long uploads by
# scripts/data/convert_eia930.py). Unlike the per-ISO demand-profiles parquet,
# they carry the Total Interchange series (DC-tie imports/exports), used to
# net out interchange in load_demand. Re-exported from the central registry.

# Model ISO -> EIA-930 BA code for the per-BA wide hourly extract. An ISO
# with no entry here falls back to the demand-profiles parquet.
_ISO_TO_HOURLY_BA: dict[str, str] = {
    "ERCOT": "ERCO",
    "CAISO": "CISO",
    "PJM": "PJM",
    "NYISO": "NYIS",
    "MISO": "MISO",
    "NEISO": "ISNE",
    # SPP = EIA-930 balancing authority SWPP (``SWPP hourly.parquet``,
    # 2015-07 -> 2026-05, America/Chicago; docs/multi-iso/spp-data-audit.md
    # §3.1). Registered 2026-09-06 by lane SPP-20.
    "SPP": "SWPP",
    # NWPP = a POOL of seventeen balancing authorities, not one extract. The
    # code ``"NWPP"`` names no file: :func:`_eia_hourly_frame` recognises it
    # as a pool (``_POOL_HOURLY_MEMBERS``) and returns the UTC-joined sum of
    # the members' ``<BA> hourly.parquet`` extracts (all seventeen landed by
    # lane NWPP-11 as a zero-residual derive from the committed BALANCE
    # archive). Every consumer of this map — demand, renewables, actuals,
    # envelopes — therefore reads a footprint frame through the same seam it
    # reads a single-BA frame. Registered 2026-09-14 by lane NWPP-20.
    "NWPP": "NWPP",
    # SOCO = the Southern Company balancing authority, EIA-930 code ``SOCO``
    # (``SOCO hourly.parquet``, 2023-01 -> 2025-12, ``America/Chicago``
    # DST-aware hour-ending for the WHOLE BA although Georgia is civil-Eastern
    # — measured 0 / 26,304 mismatches vs a Central wall clock, docs/multi-iso/
    # soco-data-audit.md §3.4). Registered 2026-09-14 by lane SOCO-20.
    "SOCO": "SOCO",
}

# Pool regions: model region -> the EIA-930 balancing authorities whose
# extracts are summed into its hourly frame. The member set is
# ``market_sim.data.fleet.models.NWPP_BAS`` (owner ruling N1, all 17; pinned
# equal by test). Order is BA_CODE_TO_ISO insertion order.
_POOL_HOURLY_MEMBERS: dict[str, tuple[str, ...]] = {
    "NWPP": (
        "BPAT",
        "PACE",
        "PACW",
        "PGE",
        "PSEI",
        "AVA",
        "IPCO",
        "NWMT",
        "CHPD",
        "DOPD",
        "GCPD",
        "SCL",
        "TPWR",
        "AVRN",
        "GRID",
        "WAUW",
        "NEVP",
    ),
}

# The member whose local clock IS the pool's model clock. NWPP spans two
# timezones — EIA-930 files 14 members on America/Los_Angeles and three (NWMT,
# PACE, WAUW) on America/Denver, IPCO included among the Pacific fourteen
# (measured, card N6) — so members are joined on UTC, the only admissible key,
# onto the PACIFIC local year of BPAT (the largest BA; Pacific members carry
# 81.6 % of load). The Mountain members' local-time columns are provenance
# only and never read. Row k of the pool frame is Pacific local hour k, the
# same positional clock as every single-BA frame.
_POOL_CLOCK_BA: dict[str, str] = {"NWPP": "BPAT"}

# Pool members whose ``Demand`` is null in every hour — generation-only
# balancing authorities (NWPP-10 §2 item 4: AVRN and GRID, all 26,304 hours,
# in every demand variant). They enter the pool demand as exactly 0.0 and the
# per-member dropout screen skips them (an all-NaN series is not a dropout).
_POOL_GENERATION_ONLY_BAS: frozenset[str] = frozenset({"AVRN", "GRID"})

# ERCOT extract path, kept as a named constant for the ERCOT-specific helpers.
_ERCO_HOURLY_FILE: Path = EIA_HOURLY_DIR / "ERCO hourly.parquet"

# Column names in the demand-meta parquet that make up the returned metadata.
_META_FIELDS = ("peak_mw", "min_mw", "avg_mw", "total_annual_mwh")


# ---------------------------------------------------------------------------
# Clean-data consumption seam (gated behind MARKET_SIM_USE_CLEAN, default OFF)
# ---------------------------------------------------------------------------
# The standardization contract curates the raw EIA-930 feeds into the canonical
# ``load`` / ``generation`` datatypes under ``data/clean`` (one Parquet per
# ``(iso, year)``), read back through the frozen ``scripts.lib.clean_io`` seam.
# When ``MARKET_SIM_USE_CLEAN`` is truthy these helpers source the system demand
# and per-fuel generation from that clean tree instead of the raw extracts; the
# default-OFF gate keeps every existing raw path byte-identical. Parity between
# the clean-backed and raw series is asserted in
# ``tests/test_consume_load_generation.py``.

# Truthy values for the opt-in environment flag.
_CLEAN_FLAG_TRUE = frozenset({"1", "true", "yes", "on"})

# IANA timezone per ISO whose clean feed is reconstructed onto the model's
# fixed non-leap local-year 8760 clock. The clean ``load`` feed for these BAs
# carries no local-time column, so the model clock is rebuilt from the tz-aware
# UTC timestamps via this zone (verified to reproduce each BA's parquet "Local
# time" exactly). MISO is intentionally absent: its EIA-930 extract stamps a
# fixed-offset local clock that no single IANA zone reproduces.
_ISO_LOCAL_TZ: dict[str, str] = {
    "CAISO": "America/Los_Angeles",
    "ERCOT": "America/Chicago",
    "NEISO": "America/New_York",
    "NYISO": "America/New_York",
}


def _use_clean() -> bool:
    """Whether the clean-data consumption seam is enabled (default OFF)."""
    return (
        os.environ.get("MARKET_SIM_USE_CLEAN", "").strip().lower() in _CLEAN_FLAG_TRUE
    )


def _read_clean_seam() -> (
    tuple[Callable[..., pd.DataFrame], Callable[..., bool]] | None
):
    """Return ``(read_clean, clean_exists)`` from the frozen seam, or ``None``.

    The seam lives under ``scripts/`` (not the installed model package), so the
    import is lazy and failure-tolerant: a missing module simply disables the
    clean path and the caller falls back to the raw extracts.
    """
    try:
        from scripts.lib.clean_io import clean_exists, read_clean
    except Exception:  # pragma: no cover - only when scripts/ is off sys.path
        logger.debug("scripts.lib.clean_io unavailable; using raw data paths")
        return None
    return read_clean, clean_exists


def _clean_local_year_rows(
    df: pd.DataFrame, iso: str, year: int
) -> pd.DataFrame | None:
    """Restrict a clean frame to the model's non-leap local-year rows, UTC-sorted.

    Mirrors :func:`_eia_hourly_frame`'s row selection (rows whose EIA-930 "Local
    date" falls in ``year``, local Feb 29 dropped, ordered by UTC) but rebuilt
    from the clean dataset's tz-aware ``interval_start_utc``. EIA-930 stamps
    hours as *hour-ending*, so a row belongs to the local date one hour before
    its (hour-ending) local timestamp; the hour-ending basis is applied before
    the year / Feb-29 filter. Returns ``None`` when the ISO has no known zone.
    """
    tz = _ISO_LOCAL_TZ.get(iso)
    if tz is None:
        return None
    utc = pd.DatetimeIndex(df["interval_start_utc"])
    local = utc.tz_convert(tz).tz_localize(None)
    hour_ending_date = local - pd.Timedelta(hours=1)
    keep = (hour_ending_date.year == year) & ~(
        (hour_ending_date.month == 2) & (hour_ending_date.day == 29)
    )
    out = df.loc[keep].copy()
    return out.sort_values("interval_start_utc")


def _read_clean_iso_year(datatype: str, iso: str, year: int) -> pd.DataFrame | None:
    """Read the clean ``datatype`` rows covering the model's local ``year``.

    A local year straddles two UTC-partitioned clean files (the BA's UTC offset
    pushes the year's tail hours into ``year + 1``), so both partitions are read
    when present and concatenated before the local-year window is cut out by
    :func:`_clean_local_year_rows`. Returns ``None`` when the seam is
    unavailable, no partition exists, or the ISO's clock cannot be rebuilt.
    """
    seam = _read_clean_seam()
    if seam is None:
        return None
    read_clean, clean_exists = seam
    frames = [
        read_clean(datatype, iso=iso, year=y, validate=False)
        for y in (year, year + 1)
        if clean_exists(datatype, iso=iso, year=y)
    ]
    if not frames:
        return None
    rows = _clean_local_year_rows(pd.concat(frames, ignore_index=True), iso, year)
    if rows is None or rows.empty:
        return None
    return rows


def _eia_hourly_path(ba_code: str) -> Path:
    """Return the path to the wide hourly extract for an EIA-930 BA code."""
    # Resolved through the shared package namespace at call time so tests
    # patching ``market_sim.data.eia_loader.EIA_HOURLY_DIR`` (the facade
    # aliases this package) keep redirecting the lookup, exactly as the
    # pre-split module-global read behaved.
    from market_sim.data import eia930 as _pkg

    return _pkg.EIA_HOURLY_DIR / f"{ba_code} hourly.parquet"


def _screen_fuel_spikes(
    frame: pd.DataFrame | None, ba_code: str, year: int
) -> pd.DataFrame | None:
    """Apply the ``NG:`` unit-slip screen at the frame-CONSTRUCTION seam.

    One mechanism (:func:`~market_sim.data.eia930.actuals.
    _screen_fuel_spike_columns`, lane SPP-41) applied wherever this module
    builds an hourly frame out of the parquet, so a reader cannot obtain an
    unscreened copy by calling a frame loader directly (rule 19
    ``[R-ONE-MECH]``; lane NWPP-37). The screen itself — its threshold, its two
    order statistics and its ``NG: <CODE>`` scope — is unchanged and still
    defined in one place; only the application point moved here, from three
    per-reader call sites in ``actuals``.

    The import is deferred because ``actuals`` imports this module at module
    level; this is the same cycle, and the same remedy, as
    :func:`_pool_hourly_frame`'s local import of ``_screen_demand_dropouts``.

    ``None`` passes through so the callers' "year unavailable" contract is
    untouched. The screen COPIES before it edits, which stays load-bearing
    here: :func:`_pool_hourly_frame` is itself cached, so screening its return
    must not write a repair back into the pool cache.
    """
    if frame is None:
        return None
    from market_sim.data.eia930.actuals import _screen_fuel_spike_columns

    return _screen_fuel_spike_columns(frame, ba_code=ba_code, year=year)


def _eia_hourly_frame_raw(ba_code: str, year: int) -> pd.DataFrame | None:
    """Return the strict BA-year frame BEFORE the ``NG:`` unit-slip screen.

    The unscreened core of :func:`_eia_hourly_frame`, split out so that
    :func:`_ercot_hourly_frame` can fill its NaN windows from the long-format
    API series and screen the RESULT, rather than screening first and then
    letting :func:`_fill_hourly_frame_from_long` refill the holes the screen
    just made from a long series that may carry the same slip. That is also
    the order the ERCOT readers had before the screen moved to this module
    (lane NWPP-37), so ERCOT stays byte-identical.

    Do NOT call this from a reader: it is the one place in the package that
    returns unrepaired ``NG:`` columns, and its two callers both screen. Every
    reader wants :func:`_eia_hourly_frame` or :func:`_eia_hourly_frame_filled`.

    Deliberately NOT ``lru_cache``d, although its two callers are. A third
    cache would be a third thing every test that patches ``EIA_HOURLY_DIR``
    has to remember to clear, and the ones that exist clear by name — when
    this was cached, a synthetic ``SWPP`` extract leaked out of one test class
    into a live-data assertion in another. The pool branch it delegates to is
    cached on its own, so the only uncached re-read is one parquet slice for
    a single BA, taken at most twice per (BA, year).
    """
    if ba_code in _POOL_HOURLY_MEMBERS:
        return _pool_hourly_frame(ba_code, year)
    path = _eia_hourly_path(ba_code)
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    local = df["Local date"]
    df = df[
        (local.dt.year == year) & ~((local.dt.month == 2) & (local.dt.day == 29))
    ].sort_values("UTC time")
    if len(df) != HOURS_PER_YEAR:
        return None
    return df.reset_index(drop=True)


@lru_cache(maxsize=32)
def _eia_hourly_frame(ba_code: str, year: int) -> pd.DataFrame | None:
    """Return the EIA-930 ``<BA> hourly`` rows for one calendar year.

    The rows are restricted to ``year`` (by the BA's local date), sorted
    chronologically by UTC time, and reduced to a clean 8760-hour series —
    in a leap year Feb 29 is dropped. Row 0 is the first local hour of the
    year, matching the HSL parquet's index, so demand, interchange and
    renewable generation drawn from this frame all share one clock.

    The ``NG:`` fuel columns are screened for unit-slip artifacts on the way
    out (:func:`_screen_fuel_spikes`), so every reader of this frame — and of
    the two loaders built on it, :func:`_eia_hourly_frame_filled` and
    :func:`_ercot_hourly_frame` — sees the repaired series. ``Demand``,
    ``Net generation`` and ``Total interchange`` are outside that screen by
    ruling and are returned exactly as filed.

    Returns ``None`` when the file is missing or the year is not covered by a
    full 8760-hour series. A pool code (``_POOL_HOURLY_MEMBERS``) returns the
    members' UTC-joined sum via :func:`_pool_hourly_frame`.
    """
    return _screen_fuel_spikes(_eia_hourly_frame_raw(ba_code, year), ba_code, year)


def _screen_pool_member_frame(
    df: pd.DataFrame, *, member: str, year: int
) -> pd.DataFrame:
    """Screen ONE pool member's ``NG:`` columns and bridge the flagged hours.

    A pool's fuel column is the sum of its members', so a member's unit-slip
    hour has to be repaired on the member's OWN population before the sum —
    the NWPP-10 dropout precedent ("a footprint sum can never read zero, so
    the screen has to run per member") in the other direction, and the
    population ``build_calibration_reference._pool_hourly_benchmark`` already
    screens on (FINDING-nwpp-37 §5 named the two paths' disagreement as the
    real finding). The statistic is unchanged — :func:`_screen_fuel_spikes`'s
    function, factor and anchor — only the series it is computed over is the
    member's: NWMT posts ``NG: WAT`` = 65,891 MW against its own 641 MW robust
    peak (2024, h5723), which the pooled series' 19,533 MW peak lets through a
    2.5x bar (measured: the pooled pass catches 2 of NWMT's 4 hydro hours in
    2024 and 3 of the 6 in 2025; per member catches all — lane NWPP-37b).

    The flagged hours are then bridged by the member's own linear
    interpolation, evaluated at the flagged positions ONLY — the fill a
    single-BA reader applies to a screened hour, and the per-member
    interpolation the reference builder sums — so the pooled hour carries the
    member's interpolated output instead of dropping the member from the sum.
    Every hour the screen did not flag keeps the pool's existing semantics: an
    hour a member does not carry stays NaN for the ``min_count=1`` sum, and a
    storage series that has not started reporting is not back-filled. Returns
    ``df`` itself when nothing is flagged. The pooled frame still passes
    :func:`_screen_fuel_spikes` once on its way out of :func:`_eia_hourly_frame`
    (the constructor's uniform guarantee); with the members repaired first that
    pass is measured inert on NWPP 2023-2025 (0 flags), and it is a different
    series, so no series is screened twice.
    """
    from market_sim.data.eia930.actuals import (
        _EIA930_FUEL_COLUMN_PREFIX,
        _screen_fuel_spike_columns,
    )

    screened = _screen_fuel_spike_columns(df, ba_code=member, year=year)
    if screened is df:
        return df
    for column in screened.columns:
        if not str(column).startswith(_EIA930_FUEL_COLUMN_PREFIX):
            continue
        raw = pd.to_numeric(df[column], errors="coerce").to_numpy(dtype=float)
        # ``to_numpy`` may hand back a read-only view; the repair writes in place.
        repaired = (
            pd.to_numeric(screened[column], errors="coerce")
            .to_numpy(dtype=float)
            .copy()
        )
        flagged = np.isnan(repaired) & ~np.isnan(raw)
        if not flagged.any():
            continue
        bridged = (
            pd.Series(repaired).interpolate().bfill().ffill().to_numpy(dtype=float)
        )
        repaired[flagged] = bridged[flagged]
        screened[column] = repaired
    return screened


# Pool-frame columns carried from the clock member as provenance (the pool's
# own clock), never summed.
_POOL_CLOCK_COLUMNS: tuple[str, ...] = ("UTC time", "Local date", "Hour", "Local time")


def _pool_member_frames(pool: str, year: int) -> dict[str, pd.DataFrame] | None:
    """Return every member's extract for ``year`` re-indexed onto the pool clock.

    The clock is the ``_POOL_CLOCK_BA`` member's strict local-year frame (8760
    rows, Feb 29 dropped, UTC-sorted); each member's whole extract is
    de-duplicated on ``UTC time`` and re-indexed onto that frame's ``UTC time``
    column — a pure UTC join, so a Mountain member's rows land on the Pacific
    hour that is the same physical hour. Hours a member does not carry come
    back NaN (none in 2023-2025: NWPP-11 §3 measured zero gaps for all 17).
    Each member's ``NG:`` fuel columns then pass through the unit-slip screen
    on the member's OWN population (:func:`_screen_pool_member_frame`, lane
    NWPP-37b) — the pool sum is built from repaired members, never raw ones.
    Returns ``None`` when the clock member's year is unavailable or ANY member
    file is missing — a pool is never silently served from a subset.
    """
    clock_ba = _POOL_CLOCK_BA[pool]
    clock = _eia_hourly_frame_filled(clock_ba, year)
    if clock is None:
        return None
    utc = pd.DatetimeIndex(clock["UTC time"])
    out: dict[str, pd.DataFrame] = {}
    for member in _POOL_HOURLY_MEMBERS[pool]:
        path = _eia_hourly_path(member)
        if not path.exists():
            logger.warning("%s pool: member extract missing: %s", pool, path.name)
            return None
        df = pd.read_parquet(path).drop_duplicates(subset="UTC time")
        df = df.set_index(pd.DatetimeIndex(df["UTC time"])).reindex(utc)
        out[member] = _screen_pool_member_frame(
            df.reset_index(drop=True), member=member, year=year
        )
    return out


@lru_cache(maxsize=8)
def _pool_hourly_frame(pool: str, year: int) -> pd.DataFrame | None:
    """Return a pool region's hourly frame: the UTC-joined sum of its members.

    Shape and columns match a single-BA strict frame (row k = local hour k of
    the pool clock, the 20 ``<BA> hourly`` columns), so every consumer reads it
    unchanged. Three conventions are fixed here, once, for the whole pool
    (NWPP-10 §1.3 / audit §4.4 — the demand convention is NOT optional):

    * ``Demand`` is the sum of the members' **``Demand (Adjusted)``** series,
      not the raw ``Demand``: EIA's Adjusted column repairs all 30 artifact
      hours of 2023-2025 (AVA 10, NWMT 11, NEVP 6, PACE 1, SCL 2 — e.g. AVA
      810,948 MW at 2025-10-12 10:00 UTC) and reproduces the cleaned coincident
      peaks 49,290 / 52,564 / 50,953 MW to the MW. ``Net generation`` and
      ``Total interchange`` likewise read the Adjusted family.
    * Each member's demand passes the exact-zero **dropout** screen
      (:func:`~market_sim.data.eia930.demand._screen_demand_dropouts`) BEFORE
      the sum — 17 NEVP hours of 2025 survive into Adjusted as literal 0.0,
      and a footprint sum can never read zero, so the screen has to run per
      member. The **spike** screen is deliberately NOT applied: its 2.5 × median
      bar flags 54 REAL CHPD hours of 12-16 January 2024 (a documented cold
      snap holding CHPD's and the whole NWPP-NW zone's 2024 annual peak;
      CHPD's peak/median is 2.29/2.83/2.50, falsifying the screen's own ≤ 2.1
      premise) — applying it would delete a real regional peak, a rule-14
      violation by construction. Generation-only members (AVRN, GRID) enter as
      0.0. Nothing is padded, interpolated or rescaled beyond the two repairs
      named here (rule 13).
    * ``Total interchange`` is **NOT** the sum of the members' interchange
      columns. That sum is broken for this pool: BPAT's ``Total interchange``
      carried a ~4,000 MW over-report on its internal legs until 2025-06 (the
      identity NG − D − TI = −36.0 TWh in 2024, closing to 0.0 from the month
      the series dropped by that amount while NG and D stayed continuous), so
      Σ TI reads +32.7 TWh where the footprint's energy-balance position is
      −3.1 TWh. The pool column is therefore Σ (NG_adj − D_adj) — the
      footprint's external net position by energy balance, which holds
      exactly (to 0.00 TWh) for the other sixteen members and is immune to
      the defective series. The served schedule applies one further
      correction on top of it (:func:`~market_sim.data.eia930.envelopes.
      nwpp_net_interchange`, the GRID Desert-Southwest legs) where the
      per-counterparty file is read.

    Fuel columns (``NG: *``) are plain sums of the members' SCREENED columns
    (:func:`_screen_pool_member_frame` — the unit-slip screen runs per member,
    before the sum, on the member's own population, lane NWPP-37b) with
    ``min_count=1`` (an hour every member lacks stays NaN for the caller's own
    gap handling). Returns ``None`` when the members cannot be assembled.
    """
    members = _pool_member_frames(pool, year)
    if members is None:
        return None
    from market_sim.data.eia930.demand import _screen_demand_dropouts

    clock = members[_POOL_CLOCK_BA[pool]]
    out = pd.DataFrame({c: clock[c].to_numpy() for c in _POOL_CLOCK_COLUMNS})

    demand = np.zeros(HOURS_PER_YEAR, dtype=float)
    net_gen = np.zeros(HOURS_PER_YEAR, dtype=float)
    for member, df in members.items():
        d = df["Demand (Adjusted)"].to_numpy(dtype=float)
        if member in _POOL_GENERATION_ONLY_BAS or np.isnan(d).all():
            d = np.zeros(HOURS_PER_YEAR, dtype=float)
        else:
            d = pd.Series(d).interpolate().bfill().ffill().to_numpy(dtype=float)
            d = _screen_demand_dropouts(d, ba_code=member, year=year)
        demand += d
        ng = pd.Series(df["Net generation (Adjusted)"].to_numpy(dtype=float))
        net_gen += ng.interpolate().bfill().ffill().fillna(0.0).to_numpy(dtype=float)
    out["Demand forecast"] = sum(
        df["Demand forecast"].to_numpy(dtype=float) for df in members.values()
    )
    out["Demand"] = demand
    out["Net generation"] = net_gen
    out["Total interchange"] = net_gen - demand
    fuel_cols = sorted(
        {c for df in members.values() for c in df.columns if c.startswith("NG: ")}
    )
    for col in fuel_cols:
        stack = pd.concat(
            [df[col] for df in members.values() if col in df.columns], axis=1
        )
        out[col] = stack.sum(axis=1, min_count=1).to_numpy(dtype=float)
    out["Demand (Adjusted)"] = demand
    out["Net generation (Adjusted)"] = net_gen
    out["Total interchange (Adjusted)"] = net_gen - demand
    return out


# Largest hole (hours) the gap-filling hourly frame will bridge. The PJM
# extract is missing its first local hour and the 2023-11-05 fall-back day
# (25 hours) plus a few scattered hours in 2024; anything bigger than a few
# days signals a structurally incomplete extract that should stay rejected
# rather than silently interpolated.
_HOURLY_FRAME_MAX_GAP: int = 72


@lru_cache(maxsize=32)
def _eia_hourly_frame_filled(ba_code: str, year: int) -> pd.DataFrame | None:
    """Return the BA-year hourly frame, bridging small gaps with NaN rows.

    Some extracts fall a few hours short of a clean local calendar year (PJM
    is missing its first local hour and the 2023-11-05 fall-back day), which
    the strict :func:`_eia_hourly_frame` rejects outright. This variant
    reindexes the present rows onto the complete hourly UTC clock for the
    local year — anchored from the first present row's ``Local time``, with a
    leap year's local Feb 29 dropped — so the missing hours come back as NaN
    rows for the caller to interpolate. Row k is local hour k of the year,
    the same clock as the strict frame.

    Both exits are screened for ``NG:`` unit-slip artifacts
    (:func:`_screen_fuel_spikes`): the fast path inherits the screen from
    :func:`_eia_hourly_frame`, and the reconstruction below — which reads the
    parquet itself rather than going through that loader — applies it on its
    own return. The screen runs on the RAW observations, before any caller's
    gap-fill, which is the order :func:`~market_sim.data.eia930.actuals.
    _screen_fuel_spike_columns` documents as load-bearing; the inserted gap
    rows are NaN in every column and cannot be flagged.

    Returns ``None`` when the file is missing, the ``Local time`` anchor
    column is absent, more than :data:`_HOURLY_FRAME_MAX_GAP` hours are
    missing, or the reconstruction does not come out at exactly
    ``HOURS_PER_YEAR`` rows.
    """
    strict = _eia_hourly_frame(ba_code, year)
    if strict is not None:
        return strict
    path = _eia_hourly_path(ba_code)
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    if "Local time" not in df.columns:
        return None
    local = df["Local date"]
    df = df[local.dt.year == year].sort_values("UTC time")
    if len(df) < HOURS_PER_YEAR - _HOURLY_FRAME_MAX_GAP or df.empty:
        return None
    # Anchor the complete UTC clock on the local year boundaries: the first /
    # last present rows fix the UTC<->local offset at each end (both ends are
    # on standard time, so the offsets are exact even mid-DST).
    utc = pd.DatetimeIndex(df["UTC time"])
    # ``Local time`` is the HOUR-ENDING label (HE convention, uniform across
    # the per-BA extracts: the year's first interval [00:00, 01:00) is
    # stamped 01:00 / Hour 1). Row k of this frame must be local hour k
    # INTERVAL-BEGINNING to match the strict frame's positional clock, so
    # shift the stamps back one hour before anchoring. Without this the whole
    # reconstructed year lands one hour late — the CISO-2025 solar-profile
    # +1h shift (FINDING-caiso102, 2026-07-19; also hit PJM-2023/MISO-2025).
    loc = pd.DatetimeIndex(df["Local time"]) - pd.Timedelta(hours=1)
    utc_start = utc[0] - (loc[0] - pd.Timestamp(year=year, month=1, day=1))
    utc_end = utc[-1] + (pd.Timestamp(year=year, month=12, day=31, hour=23) - loc[-1])
    full = pd.date_range(utc_start, utc_end, freq="h")
    # Drop the local Feb 29 of a leap year; February is on standard time, so
    # the January 1st offset maps UTC to local exactly there.
    winter_offset = pd.Timestamp(year=year, month=1, day=1) - utc_start
    approx_local = full + winter_offset
    full = full[~((approx_local.month == 2) & (approx_local.day == 29))]
    if len(full) != HOURS_PER_YEAR:
        return None
    out = (
        df.drop_duplicates(subset="UTC time")
        .set_index("UTC time")
        .reindex(full)
        .reset_index()
        .rename(columns={"index": "UTC time"})
    )
    return _screen_fuel_spikes(out, ba_code, year)


# EIA-930 long-format (API) region ``type`` code -> wide extract column, for
# the measured NaN-window fill below (same map as scripts/data/convert_eia930.py).
_EIA930_LONG_REGION_COLUMNS: dict[str, str] = {
    "D": "Demand",
    "DF": "Demand forecast",
    "NG": "Net generation",
    "TI": "Total interchange",
}


def _fill_hourly_frame_from_long(frame: pd.DataFrame, ba_code: str) -> pd.DataFrame:
    """Fill a wide hourly frame's NaN hours from the BA's long API series.

    The hand-curated ``<BA> hourly`` extract can carry NaN windows where EIA's
    bulk download lagged — e.g. the ERCO extract's 48-hour 2025-12-04/05 hole,
    two real winter-peak days (measured demand tops 58.4 GW) that the
    per-loader linear interpolation would otherwise bridge as a flat ~48 GW
    valley, fabricating two days of demand and benchmark generation. The
    EIA-930 API long-format uploads of the SAME series
    (``<BA>_region.parquet`` / ``<BA>_fueltype.parquet``,
    ``scripts/data/fetch_eia930_long.py``) were fetched after EIA backfilled the
    window, so the measured hours exist on disk. Fill NaN hours from those
    measured series BEFORE the per-loader interpolation touches them — a
    measured-input repair that regenerates for any future gap (no per-window
    registry), never modifying the immutable extract on disk. Hours absent
    from BOTH sources stay NaN and fall through to the loaders'
    isolated-hour interpolation (or, for the battery series, their
    NaN-preserving not-yet-reporting semantics: the API carries no BAT/UES
    rows before a BA starts filing them, so the reindex leaves those NaN).
    """
    value_cols = [
        c
        for c in frame.columns
        if c in _EIA930_LONG_REGION_COLUMNS.values() or c.startswith("NG: ")
    ]
    if not frame[value_cols].isna().to_numpy().any():
        return frame
    # The extract's UTC clock is tz-naive; the API ``period`` is tz-aware UTC.
    utc = pd.DatetimeIndex(frame["UTC time"])
    if utc.tz is None:
        utc = utc.tz_localize("UTC")
    long_series: dict[str, pd.Series] = {}
    region_path = RAW_DIR / f"{ba_code}_region.parquet"
    if region_path.exists():
        piv = pd.read_parquet(region_path).pivot_table(
            index="period", columns="type", values="value_mwh", aggfunc="first"
        )
        for code, col in _EIA930_LONG_REGION_COLUMNS.items():
            if code in piv.columns:
                long_series[col] = piv[code]
    fuel_path = RAW_DIR / f"{ba_code}_fueltype.parquet"
    if fuel_path.exists():
        piv = pd.read_parquet(fuel_path).pivot_table(
            index="period", columns="fueltype", values="value_mwh", aggfunc="first"
        )
        for code in piv.columns:
            long_series[f"NG: {code}"] = piv[code]
    if not long_series:
        return frame
    frame = frame.copy()
    for col, series in long_series.items():
        if col not in frame.columns:
            continue
        # copy=True: ``to_numpy`` can hand back a read-only view of the
        # column's block, and the assignment below writes into it in place.
        vals = frame[col].to_numpy(dtype=float, copy=True)
        gap = np.isnan(vals)
        if not gap.any():
            continue
        fill = series.reindex(utc).to_numpy(dtype=float)
        vals[gap] = fill[gap]
        frame[col] = vals
    return frame


@lru_cache(maxsize=8)
def _ercot_hourly_frame(year: int) -> pd.DataFrame | None:
    """Return the EIA-930 ``ERCO hourly`` rows for one calendar year.

    Thin ERCOT-specific wrapper over :func:`_eia_hourly_frame` for the
    demand/interchange, fossil and nuclear paths that are ERCOT-only today,
    with NaN windows filled from the measured long-format API series
    (:func:`_fill_hourly_frame_from_long`) so a multi-day extract hole is
    repaired with measured data rather than bridged by interpolation.
    ERCOT-only for now: other ISOs' committed benchmarks were rendered off
    the un-filled extracts, so generalizing the fill is a deliberate
    per-ISO re-render decision, not a silent side effect.
    """
    frame = _eia_hourly_frame_raw("ERCO", year)
    if frame is None:
        return None
    return _screen_fuel_spikes(
        _fill_hourly_frame_from_long(frame, "ERCO"), "ERCO", year
    )


def _filter_iso_year(df: pd.DataFrame, iso: str, year: int) -> pd.DataFrame:
    """Return the rows of ``df`` matching the given ISO and year.

    Args:
        df: A DataFrame with ``iso`` and ``year`` columns.
        iso: ISO identifier to select.
        year: Calendar year to select.

    Returns:
        The matching subset, with the row order preserved.

    Raises:
        ValueError: if no rows match the requested ISO and year.
    """
    subset = df[(df["iso"] == iso) & (df["year"] == year)]
    if subset.empty:
        raise ValueError(f"No EIA-930 data for ISO '{iso}' in year {year}")
    return subset
