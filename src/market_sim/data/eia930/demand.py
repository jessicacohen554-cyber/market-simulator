"""Hourly ISO demand loading for :mod:`market_sim.data.eia930`.

The six per-ISO ``_load_<iso>_hourly_demand`` readers, the
:data:`DEMAND_LOADERS` registry that replaced ``load_demand``'s historical
if/elif ladder, the repaired demand-profile seam, and the public
``load_demand`` / ``load_demand_meta`` entry points. Split out of
``data/eia_loader.py`` (W-D2, 2026-07-20) as pure code motion apart from the
registry conversion, which is documented block-by-block below.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import ISOConfig, SUPPORTED_ISOS, get_iso_config

from .envelopes import (
    _SCALAR_INTERCHANGE_ISOS,
    pjm_net_interchange,
    pjm_zonal_interchange,
)
from .frames import (
    DATA_DIR,
    _DEMAND_META_FILE,
    _DEMAND_PROFILES_FILE,
    _META_FIELDS,
    _eia_hourly_frame_filled,
    _ercot_hourly_frame,
    _filter_iso_year,
    _read_clean_iso_year,
    _read_clean_seam,
    _use_clean,
    logger,
)


def _pkg_ns():
    """Return the shared package namespace (:mod:`market_sim.data.eia930`).

    The ``eia_loader`` facade aliases itself to this package, so every
    historical ``mock.patch("market_sim.data.eia_loader.<name>")`` lands on
    the package namespace. The demand path resolves its per-ISO loaders and
    ``load_zonal_shares`` through it at call time so those patches keep
    intercepting the lookups, exactly as the pre-split module-global reads
    behaved.
    """
    from market_sim.data import eia930

    return eia930


# ISOs whose clean ``load`` dataset reconstructs the *system* demand series the
# model uses today (the EIA-930 ``<BA> hourly`` Demand, summed over the clean
# zones). Restricted to the ISOs whose model demand already comes from that same
# ``<BA> hourly`` extract: CAISO/NYISO read native zonal feeds into clean (a
# different series from the CISO/NYIS BA demand the model serves), MISO and PJM
# serve their ``<BA> hourly`` extracts directly (neither clean feed is rebuilt
# onto the local clock; see :data:`_ISO_LOCAL_TZ`), and SPP serves the
# demand-profiles parquet, so their clean override is left off to avoid
# silently swapping the source under the flag.
_CLEAN_DEMAND_ISOS: frozenset[str] = frozenset({"ERCOT", "NEISO"})


def _clean_system_demand(iso: str, year: int) -> np.ndarray | None:
    """Return the clean-backed system demand (MW) on the model clock, or ``None``.

    Sums the clean ``load`` zones per hour into the ISO-wide system series the
    raw demand path produces. Returns ``None`` (caller falls back to the raw
    extract) when the ISO is unsupported, the clean partition is absent, or the
    reconstructed series is not a clean, gap-free full year — matching the strict
    8760-hour requirement of :func:`_eia_hourly_frame`.
    """
    if iso not in _CLEAN_DEMAND_ISOS:
        return None
    rows = _read_clean_iso_year("load", iso, year)
    if rows is None:
        return None
    system = (
        rows.groupby("interval_start_utc", as_index=False)["load_mw"]
        .sum()
        .sort_values("interval_start_utc")
    )
    mw = system["load_mw"].to_numpy(dtype=float)
    if mw.shape[0] != HOURS_PER_YEAR or np.isnan(mw).any():
        return None
    return mw


# Exact command that regenerates the repaired ``demand-profile`` clean tree
# (see ``scripts/regenerate_clean.py``'s per-datatype ``DATATYPES`` list).
_REGEN_DEMAND_PROFILE_CMD = "python scripts/regenerate_clean.py demand-profile"


class DemandProfileNotRepairedError(RuntimeError):
    """Strict-mode error: the repaired ``demand-profile`` partition is missing.

    Raised by :func:`load_demand` / :func:`load_demand_meta` when
    ``strict_demand_profile=True`` and the requested ``(iso, year)`` is
    covered by the raw ``eia_demand_profiles.parquet`` repair manifest (i.e.
    ``scripts/data/curate_demand_profile.py`` would produce a clean partition for
    it) but that partition has not actually been regenerated on disk. Without
    strict mode the caller falls back to the corrupted legacy series instead
    (PR #1426) — this is the fail-closed alternative for solve entry points
    that cannot tolerate that silent corruption risk.
    """


@lru_cache(maxsize=1)
def _demand_profile_raw_pairs(data_dir: Path) -> frozenset[tuple[str, int]] | None:
    """Return every ``(iso, year)`` pair covered by the demand-profile repair.

    This is the exact set of pairs ``scripts/data/curate_demand_profile.py``
    repairs into a clean ``demand-profile`` partition — every ``(iso, year)``
    group present in the raw ``eia_demand_profiles.parquet`` extract (the
    script further restricts writes to the six modeled ISOs, which is every
    ISO :func:`load_demand` ever calls this with, so that restriction is not
    re-checked here). Used to tell a *missing* repair (should warn/raise) from
    an *out-of-scope* year (silently ``None``, e.g. a forecast year with no
    raw row at all). Returns ``None`` when the raw extract itself is absent.
    """
    path = data_dir / _DEMAND_PROFILES_FILE
    if not path.exists():
        return None
    profiles = pd.read_parquet(path, columns=["iso", "year"]).drop_duplicates()
    return frozenset(
        (str(iso), int(year)) for iso, year in profiles.itertuples(index=False)
    )


def _demand_profile_clean(
    iso: str,
    year: int,
    *,
    strict: bool = False,
    data_dir: Path = DATA_DIR,
) -> np.ndarray | None:
    """Return the repaired ``demand-profile`` system-total demand, or ``None``.

    Unlike :func:`_clean_system_demand` (an opt-in, parity-gated alternate
    source), this is a bug fix on the exact series :func:`load_demand` already
    falls back to, so it is consumed unconditionally — not gated behind
    ``MARKET_SIM_USE_CLEAN``. ``scripts/data/curate_demand_profile.py`` repairs the
    physically-impossible hours found in ``eia_demand_profiles.parquet`` (see
    that script's docstring); this reads the repaired clean partition it
    writes.

    The clean tree is gitignored/disposable (``data/clean``), so the repaired
    partition is routinely absent until someone runs
    ``scripts/regenerate_clean.py demand-profile``. Silently returning
    ``None`` in that case (the old behavior) means the caller falls back to
    the corrupted legacy ``eia_demand_profiles.parquet`` series without any
    signal (PR #1426; before PJM gained its per-BA extract wiring —
    :func:`_load_pjm_hourly_demand` — this fallback was PJM's *only* demand
    source). So when the partition is missing for an ``(iso, year)``
    the raw file's repair manifest actually covers (see
    :func:`_demand_profile_raw_pairs`), this now either:

    - logs a loud warning naming the exact regenerate command (default,
      ``strict=False``) and returns ``None`` (caller falls back to raw, same
      as before), or
    - raises :class:`DemandProfileNotRepairedError` (``strict=True``) instead
      of falling back at all.

    An ``(iso, year)`` the raw manifest does *not* cover (e.g. an uncovered
    forecast year) still returns ``None`` silently — there is nothing to
    regenerate, so there is nothing to warn about.

    Returns ``None`` when the clean seam is unavailable, the partition is
    absent/incomplete, or the reconstructed series is not a clean full year
    (in strict mode, the manifest-covered case raises instead of returning).
    """
    seam = _read_clean_seam()
    mw: np.ndarray | None = None
    if seam is not None:
        read_clean, clean_exists = seam
        if clean_exists("demand-profile", iso=iso, year=year):
            df = read_clean("demand-profile", iso=iso, year=year, validate=False)
            df = df.sort_values("hour")
            if len(df) == HOURS_PER_YEAR:
                mw = df["raw_mw"].to_numpy(dtype=float)
    if mw is not None:
        return mw

    manifest = _demand_profile_raw_pairs(data_dir)
    if manifest is not None and (iso, year) in manifest:
        message = (
            f"{iso} {year}: repaired 'demand-profile' clean partition not found "
            f"-- falling back to the corrupted legacy eia_demand_profiles.parquet "
            f"series (PR #1426). Run `{_REGEN_DEMAND_PROFILE_CMD}` before solving "
            f"{iso} {year} to avoid dispatching on physically-impossible demand."
        )
        if strict:
            raise DemandProfileNotRepairedError(message)
        logger.warning(message)
    return None


# The CISO extract's ``Demand`` column rides a clock convention +1 h LATE
# relative to the extract's own (astronomy-verified) generation columns for
# local dates BEFORE 2023-11-01, then flips to aligned — an upstream
# EIA-930 submission-convention change, not a loader artifact. Measured
# 2026-07-11 (FINDING-caiso75-demand-clock-2026-07-11.md): monthly best lag of
# Demand vs the extract's own balance identity (net_gen − interchange) is −1
# for 2023-01..2023-10 at r = 0.984-0.997 (near-identity), 0 from 2023-12 and
# all of 2024/2025 (November 2023 is the mixed transition month, r = 0.68);
# the OASIS SLD TAC actual corroborates (corr 0.9953 at the same shift,
# Jan-2023, seam-tz FINDING §2 "open ±1h question" — closed by this window).
# Frozen against residuals (rule 23): re-derives only from the lag scan in
# scripts/validate_caiso_demand_clock.py when the extract is re-fetched.
_CAISO_DEMAND_CLOCK_LAG_H: int = 1
_CAISO_DEMAND_CLOCK_REALIGN_END: str = "2023-11-01"  # exclusive, local date


def _load_ercot_hourly(year: int) -> tuple[np.ndarray, np.ndarray] | None:
    """Return ERCOT hourly metered demand and net interchange for a year.

    Both series are read from the same chronological ``ERCO hourly`` rows,
    keeping interchange aligned to demand. EIA's interchange sign
    convention is positive = net export, negative = net import. Returns
    ``None`` when no full-year frame is available, signaling the caller to
    fall back to the per-ISO demand-profiles parquet (no interchange).
    """
    frame = _ercot_hourly_frame(year)
    if frame is None:
        return None
    # Interpolate isolated missing meter hours (e.g. 2025 has 48 NaN demand
    # hours). Falling back to the demand-profiles parquet here is NOT
    # equivalent: that series is hour-shifted relative to this frame, which
    # desynchronizes demand from the wind/solar/benchmark series read off the
    # same rows (the 2025 backcast served its evening demand peak ~2h after
    # sunset, manufacturing scarcity).
    demand = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
    interchange = (
        frame["Total interchange"].interpolate().bfill().ffill().to_numpy(dtype=float)
    )
    if np.isnan(demand).any() or np.isnan(interchange).any():
        return None
    return demand, interchange


def _load_caiso_supply_consistent_demand(year: int) -> np.ndarray:
    """Return the supply-consistent CAISO hourly demand series (MW).

    Reads the derived measured artifact written by
    ``scripts/data/derive_caiso_supply_consistent_demand.py`` (caiso-80,
    owner-signed Option A —
    ``results/calibration/FINDING-caiso80-demand-basis-wedge-2026-07-13.md``):
    ``demand(t) = 930 NetGen(t) − NG_cell(t) + CEMS bench-gas grid(t) +
    cogen grid flat + geo/biomass fold-in flat − TI(t)`` — the honest
    CEMS-anchored basis the backcast is scored against, replacing the raw
    EIA-930 ``Demand`` cell (which carries the corrupt NG cell's fabricated
    block by the Demand = NetGen + TI identity, plus the CHP host-accounting
    wedge and the chronic 930 identity gap). Built on the generation frame's
    clock, so no clock realign applies.

    Raises (never silently falls back to the corrupt cell):
        FileNotFoundError: when the artifact for ``year`` is missing.
        AssertionError: when the artifact is not a full clean year.
    """
    from market_sim.config.paths import CAISO_SUPPLY_CONSISTENT_DEMAND_DIR

    path = (
        CAISO_SUPPLY_CONSISTENT_DEMAND_DIR
        / f"caiso_supply_consistent_demand_{year}.csv"
    )
    if not path.exists():
        raise FileNotFoundError(
            f"caiso_supply_consistent_demand: no artifact for {year} at "
            f"{path} — run scripts/data/derive_caiso_supply_consistent_demand.py"
        )
    demand = pd.read_csv(path)["demand_mw"].to_numpy(dtype=float)
    assert demand.shape[0] == HOURS_PER_YEAR, (
        f"caiso_supply_consistent_demand {year}: {demand.shape[0]} rows"
    )
    assert not np.isnan(demand).any(), (
        f"caiso_supply_consistent_demand {year}: NaN demand"
    )
    assert demand.min() > 0.0, f"caiso_supply_consistent_demand {year}: <=0 hour"
    return demand


def _load_caiso_hourly_demand(
    year: int, clock_realign: bool = False, supply_consistent: bool = False
) -> np.ndarray | None:
    """Return CAISO hourly metered demand (MW) for a year, or ``None``.

    Reads the EIA-930 ``CISO hourly`` extract so demand shares the
    chronological clock of the wind/solar/benchmark series read off the same
    rows (the ERCOT precedent: the demand-profiles parquet is hour-shifted
    relative to this frame, which desynchronizes demand from the renewable
    series — fatal for CAISO's duck curve). Isolated missing meter hours are
    interpolated.

    **Net-load convention (playbook §8.1):** this series is metered at the
    transmission level and is already net of CAISO's ~15+ GW of
    behind-the-meter PV; backcasts model only front-of-meter resources
    against it. Unlike ERCOT, the BA's net interchange is *not* folded into
    demand here: CAISO imports are modeled as supply by the ``WECC_import``
    node's priced pseudo-generators
    (:func:`market_sim.model.transmission.build_wecc_import_generators`), so
    netting interchange into demand would double count them.

    Returns ``None`` when no usable full-year frame is available, signaling
    the caller to fall back to the per-ISO demand-profiles parquet.

    ``clock_realign`` (``ScenarioConfig.caiso_demand_clock_realign``, GATED
    default off) applies the measured source-data clock correction: the
    extract's ``Demand`` column is +1 h late relative to its own wall-true
    generation frame for local dates before
    :data:`_CAISO_DEMAND_CLOCK_REALIGN_END` (see the constant's derivation
    comment), so those rows are pulled forward by
    :data:`_CAISO_DEMAND_CLOCK_LAG_H`. The single seam hour at the window
    boundary duplicates the first aligned value (a one-hour, ~3 a.m.-load
    approximation, documented in the FINDING). A reconciled-real-data clock
    fix (rule 14) — never a level rescale.

    ``supply_consistent`` (``ScenarioConfig.caiso_supply_consistent_demand``,
    GATED default off) replaces the raw ``Demand`` cell with the
    supply-consistent honest series (caiso-80 owner-signed Option A; see
    :func:`_load_caiso_supply_consistent_demand`). Takes precedence over
    ``clock_realign``.
    """
    if supply_consistent:
        # caiso-80 Option A: the supply-consistent honest series supersedes
        # both the raw Demand cell and the clock realign (it is built on the
        # generation frame's clock by construction).
        if clock_realign:
            logger.info(
                "CAISO %d: caiso_supply_consistent_demand supersedes "
                "caiso_demand_clock_realign (reconstruction rides the "
                "generation frame's clock)",
                year,
            )
        return _load_caiso_supply_consistent_demand(year)
    frame = _eia_hourly_frame_filled("CISO", year)
    if frame is None:
        return None
    demand = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
    if np.isnan(demand).any():
        return None
    if clock_realign and "Local date" in frame.columns:
        end = pd.Timestamp(_CAISO_DEMAND_CLOCK_REALIGN_END)
        misaligned = (pd.to_datetime(frame["Local date"]) < end).to_numpy()
        n = int(misaligned.sum())
        if 0 < n < len(demand):
            lag = _CAISO_DEMAND_CLOCK_LAG_H
            demand = demand.copy()
            demand[: n - lag] = demand[lag:n]
            demand[n - lag : n] = demand[n]
            logger.info(
                "CAISO %d demand clock realigned: first %d rows pulled "
                "forward %d h (measured source-data convention window)",
                year,
                n,
                lag,
            )
    return demand


def _load_nyiso_hourly_demand(year: int) -> np.ndarray | None:
    """Return NYISO hourly metered demand (MW) for a year, or ``None``.

    Reads the EIA-930 ``NYIS hourly`` extract so demand shares the
    chronological clock of the wind/solar/benchmark series read off the same
    rows (the ERCOT/CAISO precedent: the demand-profiles parquet is
    hour-shifted relative to this frame). Isolated missing meter hours are
    interpolated.

    **Net-load convention (playbook §8.1):** this series is metered at the
    transmission level and is already net of behind-the-meter PV/storage/DER.
    Backcasts model only front-of-meter resources against it. NY's BTM wedge
    is smaller than CAISO's (~15+ GW) but growing downstate — document per
    backcast year. Unlike ERCOT, net interchange is *not* folded into demand
    here: NYISO imports are modeled as a calibrated priced node (P9 /
    playbook §8.2), so netting interchange into demand would double count them.

    Returns ``None`` when no usable full-year frame is available, signaling
    the caller to fall back to the per-ISO demand-profiles parquet.
    """
    frame = _eia_hourly_frame_filled("NYIS", year)
    if frame is None:
        return None
    demand = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
    if np.isnan(demand).any():
        return None
    return demand


def _load_neiso_hourly_demand(year: int) -> np.ndarray | None:
    """Return NEISO hourly metered demand (MW) for a year, or ``None``.

    Reads the EIA-930 ``ISNE hourly`` extract so demand shares the
    chronological clock of the wind/solar/benchmark series read off the same
    rows (same rationale as CAISO/NYISO). Isolated missing meter hours are
    interpolated. This keeps demand aligned with the measured net-interchange
    schedule (:func:`neiso_net_interchange`) drawn from the same ISNE frame.

    **Net-load convention (playbook §8.1):** EIA-930 ISNE demand is metered
    at the transmission level and is already net of behind-the-meter PV
    (material in MA/CT). Backcasts model only front-of-meter resources
    against it; do not add a BTM solar profile on the supply side.

    Returns ``None`` when no usable full-year frame is available, signaling
    the caller to fall back to the per-ISO demand-profiles parquet.
    """
    frame = _eia_hourly_frame_filled("ISNE", year)
    if frame is None:
        return None
    demand = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
    if np.isnan(demand).any():
        return None
    return demand


def _load_miso_hourly_demand(year: int) -> np.ndarray | None:
    """Return MISO hourly metered demand (MW) for a year, or ``None``.

    Reads the EIA-930 ``MISO hourly`` extract's ``Demand`` column off the same
    :func:`_eia_hourly_frame_filled` frame the MISO renewable CF series are
    drawn from, so demand shares the renewables' chronological clock (row k =
    local hour k of the year). The per-ISO demand-profiles parquet, by contrast,
    stamps MISO on UTC (its row 0 is the first *UTC* hour), which lags the local
    renewable/Demand clock by ~5h (CDT) to ~6h (CST). Sourcing both demand and
    renewables off this one frame removes that offset by construction — no tz
    assumption, the frame's own ``Local time`` column fixes the clock and DST.
    MISO is therefore handled here rather than via the clean-demand override
    (its clean feed is not reconstructed onto the local clock; see
    :data:`_ISO_LOCAL_TZ`). Isolated missing meter hours are interpolated.

    The level is unchanged from the demand-profiles series (same EIA-930 MISO
    BA Demand: identical annual energy and peak); only the hour alignment moves.

    Returns ``None`` when no usable full-year frame is available, signaling the
    caller to fall back to the per-ISO demand-profiles parquet.
    """
    frame = _eia_hourly_frame_filled("MISO", year)
    if frame is None:
        return None
    demand = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
    if np.isnan(demand).any():
        return None
    return demand


def _load_pjm_hourly_demand(year: int) -> np.ndarray | None:
    """Return PJM hourly metered demand (MW) for a year, or ``None``.

    Reads the EIA-930 ``PJM hourly`` extract's ``Demand`` column off the same
    :func:`_eia_hourly_frame_filled` frame family every other ISO's demand now
    comes from, so demand shares the chronological clock of the renewables,
    benchmark series, and the PJM metered-load zonal shares
    (:func:`load_zonal_shares` reads the local-clock ``hrl_load_metered``
    files). The legacy per-ISO demand-profiles series PJM used to serve is
    defective three ways, and only the first is caught by the
    ``curate_demand_profile.py`` repair screen:

    * **Zero-hour gaps** — 23 h in 2023 and 22 h in 2024 read 0 MW (the
      repair screen interpolates these);
    * **Peak shaving** — 2024's 22-hour gap sits on a real ~104 GW ridge
      (p80 of the year), so the repair's linear interpolation silently cuts
      it to ~63 GW; the per-BA extract carries the real meter data in
      exactly those hours;
    * **Clock lag** — the legacy series lags this frame by 1-2 h, which
      desynchronizes demand from the wind/solar series and the metered
      zonal-share weights (the ERCOT/MISO precedent: serving the evening
      peak hours after sunset manufactures or destroys scarcity).

    The level is unchanged (same EIA-930 PJM BA Demand: identical peaks);
    only the gap hours and the alignment move. Isolated missing meter hours
    (the extract's first local hour; the 2023-11-05 fall-back day) are
    interpolated. Net interchange is NOT read here — PJM's measured tie-line
    export is applied separately in :func:`load_demand` (per-border-zone
    attribution via :func:`pjm_zonal_interchange`).

    Returns ``None`` when no usable full-year frame is available, signaling
    the caller to fall back to the repaired demand-profiles partition.
    """
    frame = _eia_hourly_frame_filled("PJM", year)
    if frame is None:
        return None
    demand = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
    if np.isnan(demand).any():
        return None
    return demand


def _ercot_demand_source(
    year: int, ctx: dict
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """ERCOT: metered demand + DC-tie net interchange off one ``ERCO hourly`` frame."""
    hourly = _pkg_ns()._load_ercot_hourly(year)
    if hourly is None:
        return None, None
    raw_mw, interchange = hourly
    return raw_mw, interchange


def _caiso_demand_source(
    year: int, ctx: dict
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """CAISO: EIA-930 ``CISO hourly`` demand; no interchange netting (imports are
    supply, modeled by the ``WECC_import`` node — see :func:`load_demand`)."""
    raw_mw = _pkg_ns()._load_caiso_hourly_demand(
        year,
        clock_realign=ctx["caiso_demand_clock_realign"],
        supply_consistent=ctx["caiso_supply_consistent_demand"],
    )
    return raw_mw, None


def _nyiso_demand_source(
    year: int, ctx: dict
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """NYISO: EIA-930 ``NYIS hourly`` demand (interchange served separately)."""
    return _pkg_ns()._load_nyiso_hourly_demand(year), None


def _neiso_demand_source(
    year: int, ctx: dict
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """NEISO: EIA-930 ``ISNE hourly`` demand (interchange served separately)."""
    return _pkg_ns()._load_neiso_hourly_demand(year), None


def _miso_demand_source(
    year: int, ctx: dict
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """MISO: system demand off the same hourly frame as its renewables.

    Sourced there so ``demand[t]`` and ``renewable_cf[t]`` refer to the same
    wall-clock hour; the demand-profiles fallback in :func:`load_demand` is on
    UTC and lags the local renewable clock by ~5-6h (see
    :func:`_load_miso_hourly_demand`).
    """
    return _pkg_ns()._load_miso_hourly_demand(year), None


def _pjm_demand_source(
    year: int, ctx: dict
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """PJM: system demand off the per-BA EIA-930 extract.

    The legacy demand-profiles series lags this clock by 1-2h AND its 2024
    22-hour zero gap sits on a real ~104 GW ridge that the demand-profile
    repair can only interpolate away (peak shaving); the per-BA extract
    carries the real meter data there (see :func:`_load_pjm_hourly_demand`).
    """
    return _pkg_ns()._load_pjm_hourly_demand(year), None


# Per-ISO system-demand source registry, replacing load_demand's historical
# if/elif ladder (pure code motion of each branch into its adapter above).
# Each adapter maps ``(year, ctx)`` to ``(raw_mw | None, interchange | None)``;
# a ``None`` raw_mw falls through to the demand-profiles fallback exactly as
# the ladder did, and only ERCOT ever supplies loader-side interchange. ``ctx``
# carries the CAISO-only demand kwargs so every adapter shares one signature.
DEMAND_LOADERS: dict[
    str, Callable[[int, dict], tuple[np.ndarray | None, np.ndarray | None]]
] = {
    "ERCOT": _ercot_demand_source,
    "CAISO": _caiso_demand_source,
    "NYISO": _nyiso_demand_source,
    "NEISO": _neiso_demand_source,
    "MISO": _miso_demand_source,
    "PJM": _pjm_demand_source,
}

# Registry keys are model ISO names: every key must be a registered topology
# (iso_configs.SUPPORTED_ISOS) so an ISO rename cannot silently strand a
# loader on a stale key.
_UNKNOWN_LOADER_KEYS = set(DEMAND_LOADERS) - set(SUPPORTED_ISOS)
assert not _UNKNOWN_LOADER_KEYS, (
    f"DEMAND_LOADERS keys not in SUPPORTED_ISOS: {sorted(_UNKNOWN_LOADER_KEYS)}"
)


def load_demand(
    iso: str,
    year: int,
    iso_config: ISOConfig | None = None,
    td_loss_factor: float = 0.0,
    data_dir: Path = DATA_DIR,
    include_interchange: bool = True,
    strict_demand_profile: bool = False,
    caiso_demand_clock_realign: bool = False,
    caiso_supply_consistent_demand: bool = False,
) -> np.ndarray:
    """Load hourly ISO demand and allocate it across zones.

    The total ISO demand for ``(iso, year)`` is read from the demand-profiles
    parquet and split across the ISO's zones in proportion to each zone's
    ``load_share``. A zone with ``load_share == 0.0`` (such as CAISO's
    ``WECC_import`` import node) therefore receives an all-zero row.

    The EIA-930 series reports metered system load. When ``td_loss_factor``
    is positive, demand is grossed up to the generation level the fleet must
    actually serve (``demand × (1 + factor)``), since transmission and
    distribution losses sit between generation and the meter.

    For ERCOT, demand and DC-tie interchange are read together from the
    EIA-930 ``ERCO hourly`` extract: a net import lowers what the internal
    fleet must serve, a net export raises it. For PJM, the internal-load
    demand-profiles series is combined with the measured tie-line net export
    from :func:`pjm_net_interchange` (PJM's import/export node), so the fleet
    generates internal load *plus* the ~40 TWh PJM actually exported. For
    CAISO, demand comes from the EIA-930 ``CISO hourly`` extract with **no**
    interchange netting — imports are supply, modeled by the ``WECC_import``
    node (see :func:`_load_caiso_hourly_demand`; the series is net load,
    already net of ~15+ GW BTM PV, per the playbook §8.1 convention). For
    NYISO and NEISO, demand comes from the EIA-930 ``NYIS hourly`` / ``ISNE
    hourly`` extracts (see :func:`_load_nyiso_hourly_demand` /
    :func:`_load_neiso_hourly_demand`), combined by default with the measured
    EIA-930 net-interchange schedule from :func:`nyiso_net_interchange` /
    :func:`neiso_net_interchange` — both are
    steady net importers, so serving the measured (predominantly import) wedge
    lowers what the in-state fleet must generate instead of over-filling with
    internal gas (P9 / playbook §8.2). The priced import node remains the
    forward mechanism, used under ``--priced-interchange`` (where
    ``include_interchange`` is ``False`` so the wedge is not double counted).
    The demand series is net load, already net of behind-the-meter
    PV/storage/DER (playbook §8.1). PJM's internal load likewise comes from
    the EIA-930 ``PJM hourly`` extract (see :func:`_load_pjm_hourly_demand`
    — the legacy demand-profiles series lags this clock by 1-2 h and its 2024
    zero gap interpolates away a real ~104 GW ridge). Other ISOs, and any
    (iso, year) whose dedicated per-BA extract is unavailable (CAISO/MISO
    2021-2022), fall back to the demand-profiles parquet alone, with no
    interchange — preferring the repaired ``demand-profile`` clean partition
    (see :func:`_demand_profile_clean`) when it has been regenerated, since
    the raw extract carries a handful of physically-impossible hours (raw/ is
    immutable, so the fix lives at the curation seam, not in-place).

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Calendar year to load.
        iso_config: Topology configuration supplying zone load shares. If
            ``None``, it is fetched via :func:`get_iso_config`.
        td_loss_factor: T&D losses as a fraction of metered load. The
            allocated demand is scaled by ``1 + td_loss_factor``. Defaults
            to ``0.0`` (no gross-up).
        data_dir: Directory containing the EIA-930 parquet extracts.
        include_interchange: When ``False``, the measured net-interchange
            schedule is left out of the returned demand (PJM tie-line
            export; ERCOT DC ties). Callers serving interchange through the
            priced import/export node instead
            (:func:`market_sim.model.transmission.build_import_generators`)
            must disable it here so the export is not counted twice.
        strict_demand_profile: When ``True``, raise
            :class:`DemandProfileNotRepairedError` instead of silently
            falling back to the corrupted legacy ``eia_demand_profiles``
            series when the repaired ``demand-profile`` clean partition is
            missing for an ``(iso, year)`` the repair covers (see
            :func:`_demand_profile_clean`). Defaults to ``False``
            (warn-and-fall-back, byte-identical to the pre-existing
            behavior) — a solve entry point that wants fail-closed
            protection against PR #1426's silent-corruption trap should pass
            ``True`` here.
        caiso_demand_clock_realign: CAISO only — apply the measured +1 h
            source-data clock correction to the ``Demand`` cell (caiso-75;
            see :func:`_load_caiso_hourly_demand`).
        caiso_supply_consistent_demand: CAISO only — replace the EIA-930
            ``Demand`` cell with the supply-consistent honest series
            (caiso-80 owner-signed Option A; see
            :func:`_load_caiso_supply_consistent_demand`). Takes precedence
            over ``caiso_demand_clock_realign``.

    Returns:
        A ``(n_zones, HOURS_PER_YEAR)`` array of zonal demand in MW, ordered
        to match ``iso_config.zones``.

    Raises:
        ValueError: if no data matches ``(iso, year)``.
        AssertionError: if the series is not a full year, contains NaN
            demand, or has a non-positive peak.
        DemandProfileNotRepairedError: if ``strict_demand_profile`` is
            ``True`` and the repaired demand-profile partition is missing
            for an ``(iso, year)`` the raw repair manifest covers.
    """
    if iso_config is None:
        iso_config = get_iso_config(iso)

    interchange = np.zeros(HOURS_PER_YEAR, dtype=float)
    raw_mw: np.ndarray | None = None
    demand_source = DEMAND_LOADERS.get(iso)
    if demand_source is not None:
        raw_mw, source_interchange = demand_source(
            year,
            {
                "caiso_demand_clock_realign": caiso_demand_clock_realign,
                "caiso_supply_consistent_demand": caiso_supply_consistent_demand,
            },
        )
        if source_interchange is not None:
            interchange = source_interchange
    # Clean-data seam (gated, default OFF): source the system demand from the
    # curated clean ``load`` dataset for the ISOs whose clean feed reconstructs
    # the raw EIA-930 series exactly (parity-checked in tests). Only the demand
    # magnitude is swapped; the interchange / zonal-share / loss logic below is
    # unchanged. A missing or incomplete clean partition returns ``None`` and
    # leaves the raw series (or the profiles-parquet fallback) in place.
    if _use_clean():
        clean_mw = _clean_system_demand(iso, year)
        if clean_mw is not None:
            raw_mw = clean_mw
    if raw_mw is None:
        raw_mw = _demand_profile_clean(
            iso, year, strict=strict_demand_profile, data_dir=data_dir
        )
    if raw_mw is None:
        profiles = pd.read_parquet(data_dir / _DEMAND_PROFILES_FILE)
        subset = _filter_iso_year(profiles, iso, year).sort_values("hour")
        assert len(subset) == HOURS_PER_YEAR, (
            f"Expected {HOURS_PER_YEAR} hours for {iso} {year}, got {len(subset)}"
        )
        raw_mw = subset["raw_mw"].to_numpy(dtype=float)

    assert not np.isnan(raw_mw).any(), f"NaN demand for {iso} {year}"
    assert raw_mw.max() > 0.0, f"Non-positive peak demand for {iso} {year}"

    if not include_interchange:
        interchange = np.zeros(HOURS_PER_YEAR, dtype=float)

    # Measured net interchange as an import/export "node": add the BA's net
    # export to the demand the internal fleet must serve (the ``raw_mw`` is
    # internal load). PJM is a large net exporter (without this the fleet
    # under-generates by the export and mis-attributes the missing gas to
    # coal); NYISO/NEISO are steady net importers (a negative schedule, which
    # lowers the residual the in-state fleet serves so the import wedge is not
    # over-generated as internal gas). The ERCOT path already carries
    # interchange from its EIA-930 extract. PJM prefers the per-border-zone
    # attribution (export drawn from the zone that carries the tie) over a
    # system-wide spread, falling back to the scalar; NYISO/NEISO use the
    # scalar spread by load share.
    zone_interchange = None
    if iso == "PJM" and include_interchange:
        zone_interchange = pjm_zonal_interchange(year, iso_config.zone_names)
        if zone_interchange is not None:
            logger.info(
                "PJM net interchange applied for %d: %+.0f MW avg "
                "(export-positive, per border zone)",
                year,
                float(zone_interchange.sum(axis=0).mean()),
            )
        else:
            pjm_ix = pjm_net_interchange(year)
            if pjm_ix is not None:
                interchange = pjm_ix
    elif iso in _SCALAR_INTERCHANGE_ISOS and include_interchange:
        # NYISO/NEISO are steady net importers (HQ, NYISO/PJM/IESO, NB ties).
        # Serve the *measured* EIA-930 net-interchange schedule so the import
        # wedge displaces internal gas instead of being over-generated in-state
        # (P9 / playbook §8.2; the priced node is the forward mechanism, used
        # under --priced-interchange where include_interchange is False). No
        # per-zone tie attribution yet, so the scalar is spread by load share.
        measured_ix = _SCALAR_INTERCHANGE_ISOS[iso](year)
        if measured_ix is not None:
            interchange = measured_ix
            logger.info(
                "%s net interchange applied for %d: %+.0f MW avg "
                "(export-positive, measured EIA-930)",
                iso,
                year,
                float(measured_ix.mean()),
            )

    # PJM, ERCOT, CAISO, NYISO, NEISO and MISO allocate demand by each zone's
    # own measured hourly shape (from the PJM metered-load / ERCOT native-load /
    # CAISO TAC-area / NYISO pal / ISO-NE SMD / MISO sub-BA demand files) when
    # available, so zones peak at different times; every other ISO (and these
    # six without their file) uses the static per-zone share broadcast across
    # hours. Both are (n_zones, T) weight matrices summing to 1.0 down each
    # hour, so the rest of the math is identical.
    # Resolved through the package namespace so tests patching
    # ``market_sim.data.eia_loader.load_zonal_shares`` keep intercepting it.
    zonal_shares = _pkg_ns().load_zonal_shares(iso, year, iso_config.zone_names)
    if zonal_shares is not None:
        weights = zonal_shares
    else:
        load_shares = np.array(
            [zone.load_share for zone in iso_config.zones], dtype=float
        )
        weights = np.broadcast_to(
            load_shares[:, None], (len(load_shares), HOURS_PER_YEAR)
        )
    demand = weights * raw_mw[None, :]
    if td_loss_factor > 0.0:
        demand *= 1.0 + td_loss_factor
    # Net interchange displaces internal generation: a net import (negative)
    # lowers what the fleet must serve, a net export raises it. Interchange is
    # a transmission-level flow, so it is not loss-grossed. PJM uses per-zone
    # attribution (export at its border zone); everything else spreads the
    # scalar by the same weights as demand.
    if zone_interchange is not None:
        demand += zone_interchange
    else:
        demand += weights * interchange[None, :]
    return demand


def load_demand_meta(
    iso: str,
    year: int,
    data_dir: Path = DATA_DIR,
    strict_demand_profile: bool = False,
) -> dict:
    """Load summary demand statistics for an ISO and year.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Calendar year to load.
        data_dir: Directory containing the EIA-930 parquet extracts.
        strict_demand_profile: When ``True``, raise
            :class:`DemandProfileNotRepairedError` instead of silently
            falling back to the corrupted legacy ``eia_demand_meta``/
            ``eia_demand_profiles`` series when the repaired
            ``demand-profile`` clean partition is missing for an ``(iso,
            year)`` the repair covers (see :func:`_demand_profile_clean`).
            Defaults to ``False`` (warn-and-fall-back, byte-identical to the
            pre-existing behavior).

    Returns:
        A dict with keys ``peak_mw``, ``min_mw``, ``avg_mw`` and
        ``total_annual_mwh``.

    Raises:
        ValueError: if no data matches ``(iso, year)``.
        DemandProfileNotRepairedError: if ``strict_demand_profile`` is
            ``True`` and the repaired demand-profile partition is missing
            for an ``(iso, year)`` the raw repair manifest covers.
    """
    # ``eia_demand_meta.parquet`` is a per-(iso, year) summary of the same raw
    # ``eia_demand_profiles.parquet`` hourly series :func:`load_demand` reads,
    # so it carries the identical physically-impossible-hour defect (e.g. PJM
    # 2021's peak_mw is the 2.147e9 MW spike; MISO 2021/2022/2024's min_mw is
    # the 0.0 MW sentinel). Recomputed from the repaired ``demand-profile``
    # clean series once it has been regenerated (see
    # :func:`_demand_profile_clean`); falls back to the raw meta parquet,
    # unchanged, when the clean partition is absent.
    clean_mw = _demand_profile_clean(
        iso, year, strict=strict_demand_profile, data_dir=data_dir
    )
    if clean_mw is not None:
        return {
            "peak_mw": float(clean_mw.max()),
            "min_mw": float(clean_mw.min()),
            "avg_mw": float(clean_mw.mean()),
            "total_annual_mwh": float(clean_mw.sum()),
        }
    meta = pd.read_parquet(data_dir / _DEMAND_META_FILE)
    row = _filter_iso_year(meta, iso, year).iloc[0]
    return {field: row[field] for field in _META_FIELDS}
