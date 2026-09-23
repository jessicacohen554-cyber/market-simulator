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
    # Demand only: ERCO's interchange legitimately reads 0.0 MW on idle DC
    # ties, so the dropout screen must never see it (see the screen's docstring).
    return _screen_demand_dropouts(demand, ba_code="ERCO", year=year), interchange


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
    # Repaired on the source clock, before any realignment shifts rows.
    demand = _screen_demand_dropouts(demand, ba_code="CISO", year=year)
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
    return _screen_demand_dropouts(demand, ba_code="NYIS", year=year)


# Multiple of the annual median above which an hourly demand reading is treated
# as a metering artifact rather than a real system peak. The EIA-930 wide
# extracts carry sentinel / integer-overflow spikes in some pre-2022
# out-of-sample years (PJM 2019 417,669 MW ~ 4.7x median; 2021 2,147,483,648 ~
# 2^31 overflow; 2020 five sub-300 GW hours) -- none within 2x of a genuine
# system peak. 2.5x clears every real 2023-2025 training-year peak untouched
# (max observed ratio ~ 1.7x), so the screen is a byte-identical no-op on the
# tuned years; only physically-impossible readings are repaired.
_DEMAND_SPIKE_THRESHOLD: float = 2.5


def _screen_demand_spikes(demand: np.ndarray, *, ba_code: str, year: int) -> np.ndarray:
    """Repair physically-impossible spikes in an hourly demand series.

    Hours whose demand exceeds :data:`_DEMAND_SPIKE_THRESHOLD` * the annual
    median are metering artifacts (sentinels, integer overflow, unit slips) in
    the raw EIA-930 wide extract, not real load -- no ISO's demand more than
    doubles the yearly median for an isolated hour. Each flagged hour is dropped
    and linearly interpolated from its neighbours (end hours held from the
    nearest valid value), the same repair the loaders apply to missing meter
    hours. The annual median is robust to the handful of spike hours, so it is
    computed on the raw series without a bootstrap.

    A no-op on any year whose peak stays under the threshold -- every 2023-2025
    training year of the six ISOs registered before SPP does, so the screen
    never perturbs one of their keepers (rule 22). Returns the array unchanged
    (same object) when nothing is flagged.

    THE ONE LIVE CASE is SPP 2023 (registered 2026-09-06, lane SPP-20): the
    ``SWPP hourly`` extract posts ``Demand`` = 3,621,097 MW at 2023-06-12
    21:00 local, a ~100x unit slip at 117.7x the annual median
    (docs/multi-iso/spp-data-audit.md §3.4), which this screen repairs by
    interpolation exactly as designed. That is not a keeper perturbation:
    SPP's first keeper is solved WITH the repair, and no other ISO-year is
    touched.
    """
    finite = demand[np.isfinite(demand)]
    if finite.size == 0:
        return demand
    median = float(np.median(finite))
    if median <= 0.0:
        return demand
    spike = np.isfinite(demand) & (demand > _DEMAND_SPIKE_THRESHOLD * median)
    n_spike = int(spike.sum())
    if n_spike == 0:
        return demand
    logger.warning(
        "%s %d: repairing %d demand-spike hour(s) > %.1fx median (%.0f MW); "
        "max raw %.0f MW -- EIA-930 metering artifact(s)",
        ba_code,
        year,
        n_spike,
        _DEMAND_SPIKE_THRESHOLD,
        median,
        float(np.nanmax(demand)),
    )
    repaired = demand.copy()
    repaired[spike] = np.nan
    return pd.Series(repaired).interpolate().bfill().ffill().to_numpy(dtype=float)


def _screen_demand_dropouts(
    demand: np.ndarray, *, ba_code: str, year: int
) -> np.ndarray:
    """Repair EIA-930 reporting dropouts posted as exactly 0.0 MW.

    The low-side twin of :func:`_screen_demand_spikes`. EIA-930 posts some
    reporting gaps as a literal ``0.0`` **value** rather than an absent row, so
    they survive the NaN reindex in :func:`_eia_hourly_frame_filled` and the
    ``interpolate().bfill().ffill()`` every loader applies — the frame looks
    complete and the LP is handed an hour in which the balancing authority
    serves no load at all. A whole BA's metered demand is never 0 MW, so an
    exactly-zero reading is an artifact by construction and needs no threshold.
    Each flagged hour is dropped and linearly interpolated from its neighbours,
    the same repair the spike screen and the missing-meter path already use.

    Provenance (nyiso-99, extending the nyiso-98 audit that first identified
    this artifact class in the NYIS ``NG: NUC`` series): across the six modeled
    BAs and 2023-2025 the ONLY affected series is ``NYIS`` ``Demand`` — 3 hours
    in 2024 (403, 6760, 6761) and 2 in 2025 (354, 355), each bracketed by
    ~17-22 GW readings and each reproduced 1:1 in the solved bundle's served
    load. Every other BA-year is untouched, so this is byte-identical outside
    NYISO 2024/2025 (rule 22).

    Scoped to **demand only, never interchange**: a BA's net interchange
    legitimately *is* 0.0 MW when its ties are idle (ERCO posts 187/140/113
    such hours in 2023/24/25 on its ~1.2 GW DC ties), so the same screen on an
    interchange series would delete real measurements — the rule-14 failure
    mode this repair exists to avoid.

    Returns the array unchanged (same object) when nothing is flagged, and
    when *every* hour is zero (an empty extract, which the caller's own
    ``None`` fallback must handle rather than this screen inventing a series).
    """
    dropout = np.isfinite(demand) & (demand == 0.0)
    n_dropout = int(dropout.sum())
    if n_dropout == 0 or n_dropout == demand.size:
        return demand
    logger.warning(
        "%s %d: repairing %d demand-dropout hour(s) reported as exactly 0 MW "
        "-- EIA-930 reporting gap posted as a value, not an absent row",
        ba_code,
        year,
        n_dropout,
    )
    repaired = demand.copy()
    repaired[dropout] = np.nan
    return pd.Series(repaired).interpolate().bfill().ffill().to_numpy(dtype=float)


# Tukey's "far out" fence multiplier (Tukey 1977, *Exploratory Data Analysis*,
# §2C): a value beyond Q3 + 3·IQR of its own distribution is an extreme
# outlier by the published convention. Used by :func:`_screen_demand_balance`
# as the scale of an implausible hourly demand STEP, measured on each
# BA-year's own ramp distribution — the conventional constant, never fitted
# to the hours it flags (PRECOMMIT-pjm-h19, bar v2 declared before any flag
# was measured).
_TUKEY_FAR_OUT_IQR: float = 3.0

# ISO -> single-BA EIA-930 frame whose balance identity corroborates the
# demand reading. NWPP is absent on purpose: its pool frame DEFINES
# ``Total interchange = Net generation - Demand``
# (:func:`~market_sim.data.eia930.frames._pool_hourly_frame`), so the identity
# cannot discriminate and the screen is inert there by construction.
_BALANCE_SCREEN_BA: dict[str, str] = {
    "ERCOT": "ERCO",
    "CAISO": "CISO",
    "NYISO": "NYIS",
    "NEISO": "ISNE",
    "MISO": "MISO",
    "PJM": "PJM",
    "SPP": "SWPP",
    "SOCO": "SOCO",
}


def _screen_demand_balance(demand: np.ndarray, *, iso: str, year: int) -> np.ndarray:
    """Repair isolated demand readings that break EIA-930's own balance identity.

    The neighbour-relative twin of :func:`_screen_demand_spikes` (whose bar,
    2.5x the annual median, only reaches sentinels) and
    :func:`_screen_demand_dropouts` (exactly 0 MW only). EIA-930 reports, per
    hour, ``Demand``, ``Net generation`` and ``Total interchange``; served
    demand equals net generation minus net export, so ``S = NG - TI`` is an
    independent measurement of the same load. An hour is flagged when BOTH:

    1. **Isolated reversal** — the demand steps into and out of the hour have
       opposite signs and each exceeds ``F = Q3 + 3·IQR`` of the BA-year's
       own ``|ΔD|`` distribution (Tukey far-out fence, the published
       convention :data:`_TUKEY_FAR_OUT_IQR`). Real load does not jump by an
       extreme hourly ramp and straight back.
    2. **The demand reading carries the departure** — its disagreement with
       the balance identity, ``|D - S|``, is larger at the hour than at
       either neighbour. A reading consistent with the reported generation
       and interchange is left alone, so a generation-side glitch is never
       "repaired" into demand, and a correct reading sandwiched between two
       bad ones is never blamed for them (the CAISO 2019 h1068 false
       positive that retired bar v2's neighbour-curvature test).

    Flagged hours are interpolated from their neighbours, the repair every
    sibling screen uses. ZERO fitted parameters (rule 14 [R-ACCURATE] source
    repair). **Cannot reach** an artifact that EIA-930 propagated into ``NG``
    or ``TI`` as well (``D == S`` in that hour — e.g. SWPP 2025 h4107,
    SOCO 2025), nor multi-hour artifacts, nor any ISO whose frame is absent.

    Provenance: pjm-h18 §5-A / PRECOMMIT-pjm-h19 — PJM 2020 h5003 (192.2 GW),
    h5031 (176.1 GW), h5383 (138.6 GW) and 2024 h7787 (56.3 GW), each
    departing ``S`` by 35–57 GW. Returns ``demand`` unchanged (same object)
    when nothing is flagged or the ISO's frame is unavailable.
    """
    ba = _BALANCE_SCREEN_BA.get(iso)
    if ba is None:
        return demand
    frame = (
        _ercot_hourly_frame(year)
        if iso == "ERCOT"
        else _eia_hourly_frame_filled(ba, year)
    )
    if frame is None or len(frame) != demand.size:
        return demand
    supply = (frame["Net generation"] - frame["Total interchange"]).to_numpy(
        dtype=float
    )
    steps = np.abs(np.diff(demand))
    steps = steps[np.isfinite(steps)]
    if steps.size == 0:
        return demand
    q1, q3 = np.percentile(steps, [25.0, 75.0])
    fence = q3 + _TUKEY_FAR_OUT_IQR * (q3 - q1)
    step_in = demand[1:-1] - demand[:-2]
    step_out = demand[2:] - demand[1:-1]
    reversal = (step_in * step_out < 0.0) & (
        np.minimum(np.abs(step_in), np.abs(step_out)) > fence
    )
    gap = np.abs(demand - supply)
    carried = np.isfinite(gap[1:-1] + gap[:-2] + gap[2:]) & (
        gap[1:-1] > np.maximum(gap[:-2], gap[2:])
    )
    flagged = np.zeros(demand.size, dtype=bool)
    flagged[1:-1] = reversal & carried
    n_flag = int(flagged.sum())
    if n_flag == 0:
        return demand
    logger.warning(
        "%s %d: repairing %d demand hour(s) breaking the EIA-930 balance "
        "identity (isolated reversal > %.0f MW Tukey far-out ramp): hours %s",
        ba,
        year,
        n_flag,
        fence,
        np.flatnonzero(flagged).tolist(),
    )
    repaired = demand.copy()
    repaired[flagged] = np.nan
    return pd.Series(repaired).interpolate().bfill().ffill().to_numpy(dtype=float)


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
    return _screen_demand_spikes(
        _screen_demand_dropouts(demand, ba_code="ISNE", year=year),
        ba_code="ISNE",
        year=year,
    )


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
    return _screen_demand_spikes(
        _screen_demand_dropouts(demand, ba_code="MISO", year=year),
        ba_code="MISO",
        year=year,
    )


def _load_spp_hourly_demand(year: int) -> np.ndarray | None:
    """Return SPP hourly metered demand (MW) for a year, or ``None``.

    Reads the EIA-930 ``SWPP hourly`` extract's ``Demand`` column off the same
    :func:`_eia_hourly_frame_filled` frame the SPP renewable CF series are
    drawn from — the MISO construction, so demand and renewables share one
    local clock (SWPP is ``America/Chicago``; the frame's own ``Local time``
    column fixes the clock and DST). Isolated missing meter hours are
    interpolated, then the two EIA-930 artifact screens run.

    SPP is the first ISO on which :func:`_screen_demand_spikes` is LIVE in a
    training year: 2023-06-12 21:00 posts ``Demand`` = 3,621,097 MW, a ~100x
    unit slip at 117.7x the annual median (docs/multi-iso/spp-data-audit.md
    §3.4), which the 2.5x screen repairs by interpolation. The two LOW-side
    dropouts the audit names (2025-06-21 05:00 = 1,505 MW; 2024-07-19 00:00, a
    partial dropout) are NOT caught here — :func:`_screen_demand_dropouts`
    flags only exact ``0.0`` readings by design, and a low-side threshold is a
    repo-wide screen with cache-key risk that owner ruling P9 (SPP desk r#2,
    2026-09-06) ROUTED to the audit track rather than letting the registering
    lane improvise it. Both hours pass through, and the served ``Total
    interchange`` series (:func:`~market_sim.data.eia930.envelopes.
    spp_net_interchange`) carries the matching impossible export prints;
    SPP-40's PRECOMMIT names both hours.

    Returns ``None`` when no usable full-year frame is available, signaling the
    caller to fall back to the per-ISO demand-profiles parquet.
    """
    frame = _eia_hourly_frame_filled("SWPP", year)
    if frame is None:
        return None
    demand = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
    if np.isnan(demand).any():
        return None
    return _screen_demand_spikes(
        _screen_demand_dropouts(demand, ba_code="SWPP", year=year),
        ba_code="SWPP",
        year=year,
    )


def _load_nwpp_hourly_demand(year: int) -> np.ndarray | None:
    """Return NWPP footprint hourly demand (MW) for a year, or ``None``.

    Reads the ``Demand`` column of the NWPP POOL frame
    (:func:`~market_sim.data.eia930.frames._pool_hourly_frame`, code
    ``"NWPP"`` in ``_ISO_TO_HOURLY_BA``): the seventeen members' EIA-930
    ``Demand (MW) (Adjusted)`` series, each passed through
    :func:`_screen_demand_dropouts` BEFORE the sum, joined on UTC onto the
    Pacific local year (BPAT's clock). The conventions — Adjusted column, per-
    member dropout screen, **no** spike screen, AVRN/GRID as 0.0 — are fixed
    on the pool frame itself (NWPP-10 §1.3) so demand and the renewable CF
    series drawn from the same frame share one clock, the SPP/MISO
    construction. Reproduces the coincident peaks 49,290 / 52,564 / 50,953 MW
    (2023/2024/2025). Interchange is served separately as the measured scalar
    schedule (``_SCALAR_INTERCHANGE_ISOS``, owner ruling N4). Returns ``None``
    when the pool cannot be assembled, signalling the profiles-parquet
    fallback (which carries no NWPP rows, so the caller raises rather than
    serving a stale series).
    """
    frame = _eia_hourly_frame_filled("NWPP", year)
    if frame is None:
        return None
    demand = frame["Demand"].to_numpy(dtype=float)
    if np.isnan(demand).any():
        return None
    return demand


def _load_soco_hourly_demand(year: int) -> np.ndarray | None:
    """Return SOCO hourly metered demand (MW) for a year, or ``None``.

    Reads the EIA-930 ``SOCO hourly`` extract's ``Demand`` column off the same
    :func:`_eia_hourly_frame_filled` frame the SOCO solar CF series is drawn
    from — the MISO/SPP construction, so demand and renewables share one local
    clock. That clock is ``America/Chicago``, DST-aware, hour-ending, for the
    WHOLE balancing authority even though Georgia is civil-Eastern: measured
    by SOCO-10 (gate G19) as 0 mismatches against a Central wall clock over
    all 26,304 committed rows, 26,301 against Eastern (audit §3.4). Isolated
    missing meter hours are interpolated, then the two EIA-930 artifact
    screens run — both are NO-OPS on every SOCO year (max/median 1.835 /
    1.829 / 1.789 against the 2.5x spike bar; zero literal-0.0 hours), so
    SOCO needs no demand repair (audit §3.5).

    THE 2025 TAIL, named rather than hidden (audit §3.2; plan gate G19
    "explained, not padded"): the committed extract is bounded on UTC
    (2023-01-01 00:00 -> 2025-12-31 23:00 UTC), so the last SEVEN Central
    hours of 2025 — hours ending 18-24 on 2025-12-31, UTC 2026-01-01 00:00 to
    06:00 — were never fetched. :func:`_eia_hourly_frame_filled` returns them
    as NaN rows and the shared fill below forward-fills them from hour
    ending 17, exactly as it bridges PJM's first local hour. That is a
    LOADER-SIDE bridge of 7 of 8,760 hours (0.08 %), logged at WARNING when
    it fires; the data fix is a 7-UTC-hour extension of the fetch (SOCO-11
    manifest item [4]), routed, never a padded parquet.

    What the screens do NOT reach, recorded here so no lane discovers it
    mid-solve (audit §3.5, routed to SOCO-31): one partial demand dropout at
    2025-10-23 16:00 (12,638 MW between neighbours of 23,065 and 23,653 —
    below the exact-0.0 dropout screen, above nothing the spike screen
    tests), and two defects in OTHER columns (four ``NG: NG`` hours at ~70 GW
    against a 36,336 MW gas fleet; the ``Net generation`` identity breaking
    in 2025 only, 595 h, +0.696 TWh). No new screen constant was derived
    (rule 23).

    Returns ``None`` when no usable full-year frame is available, signaling
    the caller to fall back to the per-ISO demand-profiles parquet.
    """
    frame = _eia_hourly_frame_filled("SOCO", year)
    if frame is None:
        return None
    raw = frame["Demand"]
    missing = int(raw.isna().sum())
    if missing:
        logger.warning(
            "SOCO %d: %d missing meter hour(s) in the EIA-930 extract bridged "
            "by interpolation/fill (2025: the seven UTC-bounded trailing hours, "
            "audit §3.2) — extend the fetch, do not read these as measured",
            year,
            missing,
        )
    demand = raw.interpolate().bfill().ffill().to_numpy(dtype=float)
    if np.isnan(demand).any():
        return None
    return _screen_demand_spikes(
        _screen_demand_dropouts(demand, ba_code="SOCO", year=year),
        ba_code="SOCO",
        year=year,
    )


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
    return _screen_demand_spikes(
        _screen_demand_dropouts(demand, ba_code="PJM", year=year),
        ba_code="PJM",
        year=year,
    )


def ercot_tie_zone_interchange(
    year: int,
    zone_names: list[str],
    interchange: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray | None:
    """Measured per-neighbor DC-tie interchange placed at the tie-connected zones.

    ercot-231 N1a (``ercot_tie_zonal_interchange``): replaces the load-share
    spread of ERCOT's net interchange with attribution at the zones that
    physically host the DC ties (``constants.ERCOT_DC_TIE_ZONE_MAP`` — SWPP
    flow to Northeast/North by tie rating, CEN flow to South), the PJM
    per-border-zone precedent (:func:`pjm_zonal_interchange`) applied to
    ERCOT. Per-neighbor flows come from the EIA-930 BA-to-BA interchange
    product (``data/raw/eia-930-interchange/ERCO interchange hourly.parquet``,
    the standing keyless bulk fetch); file order per DIBA is chronological, so
    the hour-ending window slice ``[Jan-1 01:00 .. Jan-1 00:00 of year+1]``
    maps position -> model hour (verified vs the wide extract's total:
    p50 0.0 / max 1.0 MW, ercot-231 phase-0). The small residual between the
    by-neighbor sum and the wide extract's ``Total interchange`` (rounding +
    a few extract-gap hours) is spread by the caller's demand weights, so the
    column sums equal the netted total EXACTLY and the system energy balance
    is unchanged by construction — only zonal placement moves.

    Args:
        year: Backcast year to slice.
        zone_names: Model zone names, row order of the output.
        interchange: The wide-extract net interchange series (positive =
            export), length ``HOURS_PER_YEAR`` — the conserved column total.
        weights: ``(n_zones, HOURS_PER_YEAR)`` demand weights used to spread
            the residual (the same weights the load-share spread would use).

    Returns:
        ``(n_zones, HOURS_PER_YEAR)`` signed MW matrix to ADD to zonal
        demand, or ``None`` when the by-neighbor file or a full-year slice is
        unavailable (caller keeps the load-share spread).
    """
    from market_sim.config.constants import ERCOT_DC_TIE_ZONE_MAP

    path = (
        _pkg_ns().EIA_HOURLY_DIR.parent
        / "eia-930-interchange"
        / ("ERCO interchange hourly.parquet")
    )
    if not path.exists():
        return None
    nb = pd.read_parquet(path)
    lo = pd.Timestamp(f"{year}-01-01 01:00:00")
    hi = pd.Timestamp(f"{year + 1}-01-01 00:00:00")
    zone_idx = {z: i for i, z in enumerate(zone_names)}
    matrix = np.zeros((len(zone_names), HOURS_PER_YEAR), dtype=float)
    attributed = np.zeros(HOURS_PER_YEAR, dtype=float)
    matched = False
    for diba, g in nb.groupby("diba", observed=True):
        placements = ERCOT_DC_TIE_ZONE_MAP.get(str(diba))
        if placements is None:
            logger.warning(
                "ERCO interchange DIBA %s has no tie-zone placement; "
                "its flow stays in the load-share residual",
                diba,
            )
            continue
        g = g[(g["local_time"] >= lo) & (g["local_time"] <= hi)]
        # Model clock drops Feb 29 (every loader's convention); the
        # hour-ending stamps for Feb-29 run 02-29 01:00 .. 03-01 00:00, so
        # filter on the hour-BEGINNING clock (stamp - 1h) to excise exactly
        # the leap day. Without this a leap year has 8,784 rows and the
        # attribution silently fell back to the spread (caught on the first
        # authorized 3-year solve, 2024).
        hb = g["local_time"] - pd.Timedelta(hours=1)
        g = g[~((hb.dt.month == 2) & (hb.dt.day == 29))]
        if len(g) != HOURS_PER_YEAR:
            logger.info(
                "ERCO by-neighbor interchange %d: %s has %d rows (need %d) — "
                "tie-zone attribution unavailable, keeping load-share spread",
                year,
                diba,
                len(g),
                HOURS_PER_YEAR,
            )
            return None
        series = (
            pd.Series(g["mw"].to_numpy(dtype=float))
            .interpolate()
            .bfill()
            .ffill()
            .to_numpy()
        )
        for zone, share in placements:
            i = zone_idx.get(zone)
            if i is None:
                logger.warning(
                    "tie-zone map names unknown zone %s; share dropped to the residual",
                    zone,
                )
                continue
            matrix[i] += series * share
            attributed += series * share
        matched = True
    if not matched:
        return None
    # Conserve the netted total exactly: the residual (by-neighbor rounding,
    # extract-gap interpolation) rides the demand weights like the load-share
    # spread it replaces.
    matrix += weights * (interchange - attributed)[None, :]
    return matrix


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


def _spp_demand_source(
    year: int, ctx: dict
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """SPP: system demand off the ``SWPP hourly`` EIA-930 extract.

    Sourced off the same hourly frame as SPP's renewables so ``demand[t]`` and
    ``renewable_cf[t]`` refer to the same wall-clock hour (the MISO
    construction; see :func:`_load_spp_hourly_demand`). Interchange is served
    separately as the measured scalar schedule (``_SCALAR_INTERCHANGE_ISOS``,
    owner ruling P2), so the loader-side interchange slot is ``None``.
    """
    return _pkg_ns()._load_spp_hourly_demand(year), None


def _nwpp_demand_source(
    year: int, ctx: dict
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """NWPP: footprint demand off the seventeen-member EIA-930 pool frame.

    Sourced off the same pool frame as NWPP's renewables so ``demand[t]`` and
    ``renewable_cf[t]`` refer to the same wall-clock hour (see
    :func:`_load_nwpp_hourly_demand`). Interchange is served separately as
    the measured scalar schedule (``_SCALAR_INTERCHANGE_ISOS``, owner ruling
    N4), so the loader-side interchange slot is ``None``.
    """
    return _pkg_ns()._load_nwpp_hourly_demand(year), None


def _soco_demand_source(
    year: int, ctx: dict
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """SOCO: BA demand off the ``SOCO hourly`` EIA-930 extract.

    Sourced off the same hourly frame as SOCO's solar so ``demand[t]`` and
    ``renewable_cf[t]`` refer to the same Central wall-clock hour (see
    :func:`_load_soco_hourly_demand`). Interchange is served separately as the
    measured scalar schedule (``_SCALAR_INTERCHANGE_ISOS``, owner card S4 —
    SOCO is a net EXPORTER, so the served series raises what the internal
    fleet must generate in most hours), so the loader-side interchange slot is
    ``None``.
    """
    return _pkg_ns()._load_soco_hourly_demand(year), None


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
    # SPP (registered 2026-09-06, lane SPP-20) — the same commit that added
    # ``_spp_config`` to ``iso_configs._ISO_BUILDERS`` (the import-time assert
    # below is why the two must land together; plan §2.3 / gate G1).
    "SPP": _spp_demand_source,
    # NWPP (registered 2026-09-14, lane NWPP-20) — the same commit that added
    # ``_nwpp_config`` to ``iso_configs._ISO_BUILDERS`` and ``"NWPP"`` to
    # ``solve_surface.SURFACE_ISOS`` (the import-time assert below and the
    # pinned-tuple test are why the three must land together; plan §2.3 /
    # gate G1).
    "NWPP": _nwpp_demand_source,
    # SOCO (registered 2026-09-14, lane SOCO-20) — the same commit that added
    # ``_soco_config`` to ``iso_configs._ISO_BUILDERS`` and ``"SOCO"`` to
    # ``solve_surface.SURFACE_ISOS`` (the import-time assert below and the
    # pinned-tuple test are why the three must land together; plan §2.3 /
    # gate G1). A balancing authority, not an ISO — see ``_soco_config``.
    "SOCO": _soco_demand_source,
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
    ercot_tie_zonal_interchange: bool = False,
    nwpp_grid_carried_wind_served: bool = False,
    demand_balance_screen: bool = False,
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
        ercot_tie_zonal_interchange: ERCOT only — place the netted DC-tie
            interchange at the tie-connected zones by the measured
            per-neighbor split instead of the load-share spread (ercot-231
            N1a; see :func:`ercot_tie_zone_interchange`). System total
            unchanged by construction; falls back to the spread when the
            by-neighbor extract is absent for the year.
        nwpp_grid_carried_wind_served: NWPP only — stop removing the GRID
            export leg whose energy the pool's own wind supply carries
            (NWPP-47; see :func:`~market_sim.data.eia930.envelopes.
            nwpp_net_interchange`). Default ``False`` is byte-identical.
        demand_balance_screen: repair isolated demand readings that break the
            EIA-930 balance identity (pjm-h19; see
            :func:`_screen_demand_balance`). Applied to the frame-sourced
            series only, never to the demand-profiles fallback. Default
            ``False`` is byte-identical.

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
    if raw_mw is not None and demand_balance_screen:
        raw_mw = _screen_demand_balance(raw_mw, iso=iso, year=year)
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
        if iso == "NWPP" and nwpp_grid_carried_wind_served:
            measured_ix = _SCALAR_INTERCHANGE_ISOS[iso](
                year, grid_carried_wind_served=True
            )
        else:
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
    if (
        iso == "ERCOT"
        and ercot_tie_zonal_interchange
        and include_interchange
        and zone_interchange is None
    ):
        # ercot-231 N1a: place the netted DC-tie flow at the tie-connected
        # zones (measured per-neighbor split) instead of the load-share
        # spread; column sums equal the netted total exactly, so the system
        # energy balance is unchanged. Falls through to the spread when the
        # by-neighbor extract is absent for the year (data-keyed).
        zone_interchange = ercot_tie_zone_interchange(
            year, iso_config.zone_names, interchange, np.asarray(weights)
        )
        if zone_interchange is not None:
            logger.info(
                "ERCOT tie-zone interchange applied for %d: %+.0f MW avg "
                "(export-positive, per DC-tie zone)",
                year,
                float(zone_interchange.sum(axis=0).mean()),
            )
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
