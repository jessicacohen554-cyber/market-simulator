"""Shared CAMPD outage-window detectors (single home for every ISO).

This module is the one home for the CAMPD outage-detection primitives. They were
formerly defined in ``scripts/derive_campd_outages.py`` (the facility-summed
detector, deleted 2026-07-17 — it summed a plant's units and so hid single-unit
outages and folded daily-cycling combined-cycle operation into phantom summer
outages) and, for the partial-plateau detector, in
``scripts/data/derive_partial_outages.py``. The per-unit detector
(:mod:`scripts.data.derive_campd_unit_outages`) is now the sole CAMPD outage source
for every ISO; it and :mod:`scripts.data.derive_partial_outages` both import their
detection primitives from here.

All parameters carry the ERCOT-79 availability-envelope audit tightening
(``results/calibration/FINDING-ercot79-phantom-outage-2026-07.md``): daily-cycling
combined-cycle / cogen classes are detected EVENT-based (a single running hour
breaks a window), and a detected down span is kept as a real outage only where
the unit was actually DOWN through the system's high-net-load hours (the
revealed-availability filter). Every detector is keyed only on measured CAMPD
operation (capacity factor) + EIA-930 net load — no LMP / price / MWh residual
(CLAUDE.md #11/#26); the parameters are frozen against residuals (CLAUDE.md #23)
and re-derive only on a source-data change.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Repository root: this module lives at scripts/lib/outage_detect.py, so the
# repo is two directories up. Used only to resolve the EIA-930 net-load file for
# the revealed-availability mask and the merit-order guard's measured fuel-price
# series (no market_sim import, so the lib stays usable regardless of the
# importing script's sys.path setup).
_REPO = Path(__file__).resolve().parents[2]

# A sustained CF above this is a "real run"; below it (off, or low-output
# idling) is treated as not running. Set to 5%: a plant idling at 5-10% CF is
# still running (so low-output baseload like J K Spruce is not mislabeled as
# out), while genuine full-outage gaps (CF < 5%) are still caught.
REAL_RUN_CF: float = 0.05
# A real run must hold above REAL_RUN_CF for at least this many hours; shorter
# spikes are false starts and stay folded into the surrounding outage.
MIN_REAL_RUN_HOURS: int = 24

# ST_GAS outages are detected event-based on the full calendar-year clock
# (CAMPD-omitted hours zero-filled = no activity = offline): an outage is a
# maximal run of consecutive hours whose CF never reaches ST_GAS_CF_PEAK,
# lasting at least ST_GAS_MIN_OUTAGE_HOURS. Any single hour at/above the peak
# breaks the window, so intermittent generation (sporadic starts) is never
# mislabeled as outage. Coal/CC keep the averaged 5%/2-day real-run rule.
ST_GAS_CF_PEAK: float = 0.02
ST_GAS_MIN_OUTAGE_HOURS: int = 120

# ERCOT-79 availability-envelope audit: daily-cycling combined-cycle / cogen
# classes are detected EVENT-based (like ST_GAS) rather than with the run-based
# 24 h-consecutive rule — otherwise a unit that runs the afternoon peak and shuts
# overnight (never 24 h continuous) has its whole operating season folded into
# one phantom "outage". Coal stays run-based (baseload; no daily-cycling phantom).
EVENTBASED_CYCLING_GROUPS: frozenset[str] = frozenset(
    {"CC_REGULAR", "CC_CHP", "CT_CHP", "CT_PEAKER"}
)

# Revealed-availability filter (shared by the unit-level detector) -----------
# A sustained CF<threshold span is detected as an "outage", but for a
# dispatchable coal/CC unit that span is ambiguous: a mechanical outage vs
# economic idling (out of merit, e.g. cheap-gas shoulder season). From CEMS
# alone the two are indistinguishable, and the rules below mislabel the second
# as the first — removing ~40-80 GW of economically-idle coal/CC in low-demand
# SHOULDER/winter months, which the energy+reserve co-opt then reads as a
# reserve shortfall and prices to VOLL (model Oct-2024 17 h>$200 at 73 GW peak
# vs the genuinely loose actual Oct $23.8/4 h; the over-fire the 2024/25 keeper
# could never shake). The fix is a revealed-availability test keyed on EXOGENOUS
# NET LOAD (demand − wind − solar): a down span is a real (binding) outage only
# if the unit stayed down through the system's HIGH-NET-LOAD hours, when a coal/
# CC unit would be called. NET load (not raw load) so WINTER-STORM and VRE-
# drought tightness — high-net-load hours that sit below the summer-dominated
# raw-load peak — is caught (a raw-load percentile over-cuts winter outages and
# under-fires winter storms). A span entirely within low-net-load hours is
# economic idling — the unit is left AVAILABLE (capacity not removed) so the
# co-opt keeps it in the reserve pool. Real outages coincide with the net-load
# peak band and are kept. The signal is measured EIA-930 demand/wind/solar (a
# backcast INPUT, not a solved output) — no circularity with the LMP, no price
# target fitted. A relative NET-LOAD PERCENTILE (per ISO-year) self-scales.
HIGH_LOAD_PCTL: float = 0.85
# A down span must overlap at least this many high-load hours to be kept as a
# real (binding) outage; fewer ⇒ economic idle, unit left available.
MIN_INMERIT_HOURS: int = 24
# Width (days) of the centered window the high-load band is measured over. A
# *single annual* percentile makes "high load" mean only the summer/winter peak,
# so a genuine multi-week SHOULDER maintenance outage — which by definition never
# spans an annual-top-15% hour — is wrongly dropped as economic idle (ERCOT CC:
# 69% of outage GW-days cut, incl. 90-day continuous outages like T H Wharton).
# A LOCAL (seasonal) percentile over a rolling +/-WINDOW_DAYS band instead asks
# "did the unit stay down through the high-net-load hours of ITS OWN period?":
# the real shoulder outage spans that period's local peaks and is kept, while
# the short economic-idle gap returns to service during those same local peaks
# and is still dropped. Set 0 to fall back to the legacy single-annual
# percentile (the over-tight behaviour). 30 days = ~one maintenance season's
# net-load cycle. Still net-load-keyed (exogenous input, no LMP / price fit).
WINDOW_DAYS: int = 30

# Full-stop duration+depth override (shared, all ISOs) -----------------------
# The net-load revealed-availability test above can still DROP a genuine
# MECHANICAL outage as "economic idle" when the down span sits just below the
# high-net-load band — e.g. a 14-20 day continuous full stop of a baseload coal
# unit whose span happens to overlap only ~17-22 of the required 24 high-load
# hours (a STEP-1 audit found ~1.7 GW-thousand-days of such spans pooled across
# the six ISOs, 98% of them dead stops, concentrated right at the 24 h gate
# margin). Economic idling backs DOWN but rarely fully STOPS for weeks: a coal
# baseload unit out of merit cycles or returns the moment any local peak hits, so
# a sustained, weeks-long CF≈0 dead stop is the mechanical-outage signature
# regardless of net-load overlap. So a down span is ALSO kept if it is a full
# stop — mean CF below FULL_STOP_OVERRIDE_CF — lasting at least
# FULL_STOP_OVERRIDE_DAYS continuous days. Keyed ONLY on measured CAMPD
# operation (CF) + EIA-930 net load (the mask) — no LMP / price / MWh-residual
# input (claude.md #11). N lowered 14 -> 5 d (2026-07-07): a PJM PRB audit
# (Kincaid/Powerton, 2023-2025) found ~62 plant-days of genuine dead stops
# (span CF == 0.000) in the 5-13 d SHOULDER band being dropped as "economic
# idle" because they overlapped < 24 high-net-load hours and fell short of the
# 14 d override. The real protection here is the DEPTH gate, not the duration:
# economic idling backs down but "rarely fully STOPS for weeks" — a sustained
# CF < FULL_STOP_OVERRIDE_CF (0.02) dead stop is the mechanical-outage signature
# at any duration, and 5 d matches the unit-level detector's own
# UNIT_OUTAGE_MIN_DAYS floor (outages.py), so no span shorter than an already-
# recognized outage is admitted. 21 d / 28 d recovered almost nothing the local
# band did not already keep; 5 d recovers the shoulder-season dead-stop band the
# 14 d knee left exposed. Set FULL_STOP_OVERRIDE_DAYS very large (or pass
# --no-fullstop-override) to disable.
FULL_STOP_OVERRIDE_DAYS: int = 5
FULL_STOP_OVERRIDE_CF: float = 0.02

# EIA-930 balancing-authority code per model ISO (the eia-930-hourly file stem).
_ISO_TO_BA: dict[str, str] = {
    "ERCOT": "ERCO",
    "CAISO": "CISO",
    "PJM": "PJM",
    "NYISO": "NYIS",
    "NEISO": "ISNE",
    "MISO": "MISO",
}


def filter_revealed_outages(
    windows: list[tuple[int, int]],
    mask: np.ndarray | None,
    cf: np.ndarray,
    min_inmerit_hours: int,
    override_days: int = FULL_STOP_OVERRIDE_DAYS,
    override_cf: float = FULL_STOP_OVERRIDE_CF,
) -> list[tuple[int, int]]:
    """Apply the revealed-availability filter with the full-stop duration override.

    Shared by every ISO's outage detector so the gate is one filter. A detected
    down span ``(s, e)`` is kept when EITHER

    * it overlaps at least ``min_inmerit_hours`` high-NET-LOAD hours (the
      local-band revealed-availability test — ``mask`` is :func:`high_load_mask`),
      OR
    * it is a sustained **full stop** — mean capacity factor over the span below
      ``override_cf`` — lasting at least ``override_days`` continuous days (the
      mechanical-outage signature; economic idling backs down but does not fully
      stop for weeks).

    ``cf`` is the unit/plant hourly capacity factor (gross / nameplate) on the
    same clock as ``mask``. Both inputs are exogenous measured quantities (CAMPD
    operation + EIA-930 net load) — no LMP / price / MWh-residual. ``mask`` None
    (no net-load file) ⇒ every span kept (the original no-op behaviour). Pass
    ``override_days`` ≥ the year length to disable only the override.
    """
    if mask is None:
        return list(windows)
    kept: list[tuple[int, int]] = []
    for s, e in windows:
        high = mask[s:e]
        cf_span = cf[s:e]
        # Revealed-availability (ERCOT-79 availability-envelope audit fix). A
        # down span is NOT an outage if, during its high-net-load hours, the unit
        # REVEALED it was available by RUNNING (cf >= REAL_RUN_CF) for at least
        # ``min_inmerit_hours`` of them. The old test kept a span whenever it
        # merely OVERLAPPED >= min_inmerit_hours high-load hours, never checking
        # whether the unit was actually down then — so the run-based detector's
        # habit of folding a daily-cycling CC's overnight-down gaps into one
        # summer-long "outage" produced a hard availability=0 across the whole
        # summer for a plant its own CEMS shows generating on the peak afternoons
        # (T H Wharton, ORIS 3469: it ran during 392 of its 480 summer high-load
        # hours yet was zeroed all 3,404 h — ~800 MW deleted from the June/Sept
        # 2023 event afternoons). Running through the tight hours is the
        # market's own revealed-availability signal; overlap alone is not.
        # Keyed only on measured CAMPD cf + EIA-930 net load — no LMP / price /
        # MWh-residual (claude.md #11/#26).
        ran_high = int((high & (cf_span >= REAL_RUN_CF)).sum())
        if ran_high >= min_inmerit_hours:
            continue  # revealed available when the system was tight — not an outage
        # A genuine outage is DOWN through the tight hours it spans.
        if int((high & (cf_span < REAL_RUN_CF)).sum()) >= min_inmerit_hours:
            kept.append((s, e))
            continue
        dur_days = (e - s) / 24.0
        span_cf = float(cf_span.mean()) if e > s else 1.0
        if dur_days >= override_days and span_cf < override_cf:
            kept.append((s, e))
    return kept


def high_load_mask(
    iso: str,
    year: int,
    n_hours: int,
    pctl: float = HIGH_LOAD_PCTL,
    win_days: int = WINDOW_DAYS,
) -> np.ndarray | None:
    """Boolean ``(n_hours,)`` mask: was the system in its high-NET-LOAD band?

    Net load = measured EIA-930 ``demand − wind gen − solar gen``
    (data/raw/eia-930-hourly/``<BA> hourly.parquet``). ERCOT's file carries EIA's
    reconciled ``Adjusted demand``/``Adjusted WND Gen``/``Adjusted SUN Gen``
    series; the other BA extracts only carry the raw ``Demand``/``NG: WND``/
    ``NG: SUN`` columns, so we fall back to those when the Adjusted ones are
    absent (the raw series is an equally exogenous net-load proxy).

    An hour is "high load" if its net load exceeds the ``pctl`` percentile of a
    centered rolling ``+/- win_days`` net-load window (the LOCAL / seasonal band)
    — so a unit that stays down through the high-net-load hours of its own period
    is caught even where those hours sit below the summer/winter annual peak. The
    real multi-week shoulder maintenance outage spans its period's local peaks
    (kept); a short economic-idle gap returns to service during those same local
    peaks (still dropped). Set ``win_days <= 0`` to fall back to a single annual
    percentile (the legacy over-tight band that cut genuine shoulder outages).

    Results map onto the detector's calendar clock by ``(month, day, hour)`` (the
    EIA-930 file is itself calendar/leap-aware, so alignment is exact). Net load
    (not raw load) so winter-storm / VRE-drought tightness — high-net-load hours
    below the summer raw-load peak — is caught. Returns ``None`` when the BA
    file/year is unavailable, or the demand column is missing (no-op).
    """
    ba = _ISO_TO_BA.get(iso.upper())
    if ba is None:
        return None
    path = _REPO / "data" / "raw" / "eia-930-hourly" / f"{ba} hourly.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[pd.to_datetime(df["Local date"]).dt.year == year].copy()
    if df.empty:
        return None
    df["dt"] = pd.to_datetime(df["Local date"]) + pd.to_timedelta(
        df["Hour"].astype(int) - 1, unit="h"
    )

    def _col(*names: str) -> np.ndarray:
        """First present column among ``names`` as float, else all-zeros."""
        for nm in names:
            if nm in df.columns:
                return df[nm].to_numpy(dtype=float)
        return np.zeros(len(df), dtype=float)

    dem = _col("Adjusted demand", "Demand")
    if not np.isfinite(dem).any():
        return None
    wnd = np.nan_to_num(_col("Adjusted WND Gen", "NG: WND"))
    sun = np.nan_to_num(_col("Adjusted SUN Gen", "NG: SUN"))
    net = dem - wnd - sun
    if win_days and win_days > 0:
        # Local (seasonal) band: per-hour threshold = the pctl percentile of a
        # centered +/- win_days net-load window. Sort to chronological order for
        # the rolling quantile, then scatter the thresholds back to the file's
        # native row order so the (month, day, hour) key below stays aligned.
        dt = df["dt"].to_numpy()
        order = np.argsort(dt, kind="stable")
        ser = pd.Series(net[order], index=dt[order])
        w = int(win_days) * 24
        roll = (
            ser.rolling(w, center=True, min_periods=max(1, w // 2))
            .quantile(pctl)
            .to_numpy()
        )
        thresh = np.full(len(net), np.nan)
        thresh[order] = roll
    else:
        thresh = np.full(len(net), float(np.nanquantile(net, pctl)))
    key = {
        (t.month, t.day, t.hour): bool(np.isfinite(v) and np.isfinite(th) and v > th)
        for t, v, th in zip(df["dt"], net, thresh)
    }
    clock = pd.date_range(f"{year}-01-01", periods=n_hours, freq="h")
    out = np.zeros(n_hours, dtype=bool)
    for i, t in enumerate(clock):
        v = key.get((t.month, t.day, t.hour))
        if v is None and t.month == 2 and t.day == 29:
            v = key.get((2, 28, t.hour))
        out[i] = bool(v)
    return out


def _runs(mask: np.ndarray):
    """Yield (start, stop_exclusive) for each maximal True run in ``mask``."""
    if not mask.any():
        return
    idx = np.flatnonzero(np.diff(np.r_[0, mask.view(np.int8), 0]))
    for s, e in zip(idx[::2], idx[1::2]):
        yield int(s), int(e)


def detect_outages(
    gross: np.ndarray,
    nameplate: float,
    min_outage_hours: int,
    real_run_cf: float = REAL_RUN_CF,
) -> list[tuple[int, int]]:
    """Return outage windows ``[(start, stop_exclusive), ...]`` (hour indices).

    A real run is a CF>``real_run_cf`` spell of >= MIN_REAL_RUN_HOURS; outages
    are the complement, kept when >= ``min_outage_hours``.
    """
    cf = gross / nameplate if nameplate > 0 else np.zeros_like(gross)
    running = cf > real_run_cf
    real = np.zeros_like(running)
    for s, e in _runs(running):
        if e - s >= MIN_REAL_RUN_HOURS:
            real[s:e] = True
    return [(s, e) for s, e in _runs(~real) if e - s >= min_outage_hours]


def detect_outages_eventbased(
    gross: np.ndarray,
    nameplate: float,
    min_outage_hours: int,
    cf_peak: float = ST_GAS_CF_PEAK,
) -> list[tuple[int, int]]:
    """Event-based outage windows ``[(start, stop_exclusive), ...]``.

    An outage is a maximal run of consecutive hours whose CF stays strictly
    below ``cf_peak`` for *every* hour, kept when >= ``min_outage_hours``. A
    single hour at/above ``cf_peak`` breaks the window, so a plant with
    intermittent generation is not mislabeled as out. ``gross`` must already be
    on the full-year clock with omitted hours zero-filled.
    """
    cf = gross / nameplate if nameplate > 0 else np.zeros_like(gross)
    below = cf < cf_peak
    return [(s, e) for s, e in _runs(below) if e - s >= min_outage_hours]


# Partial-plateau detector (formerly scripts/data/derive_partial_outages._detect) --
# Frozen against residuals (CLAUDE.md #23): these constants re-derive only on a
# source-data change. A partial outage shows up as a sustained *ceiling plateau*
# — the plant keeps running but its daily-max CF drops well below its normal
# capability, then recovers.
_MIN_DAYS = 5  # sustained plateau length
_SMOOTH_DAYS = 7  # rolling-median window to ride through recovery blips
_CEILING_FRAC = 0.65  # daily max below this fraction of the normal ceiling
_RUN_FLOOR_CF = 0.06  # daily mean above this = running (not a full outage)


def _plateau_state(
    cf: np.ndarray,
) -> tuple[np.ndarray, float, np.ndarray, np.ndarray] | None:
    """Return ``(dmax, ref, sm, partial)`` — the plateau detector's statistics.

    The single definition of the detector's own quantities, shared by
    :func:`_detect` (the incumbent flat-plateau factor) and
    :func:`detect_shaped` (the ercot-185 day-shaped profile) so the two can
    never drift apart. ``None`` when the series carries no usable day grid or
    the plant never runs (``ref <= 0``), which both callers treat as "no
    plateaus".

    * ``dmax`` — per-day maximum capacity factor (the plant's revealed daily
      ceiling); ``ref`` — its 90th percentile over RUNNING days
      (``dmean > _RUN_FLOOR_CF``), i.e. the plant's normal ceiling.
    * ``sm`` — the centered ``_SMOOTH_DAYS`` rolling median of ``dmax``, so
      brief recovery blips (a unit cycling back for a day or two) don't break
      an otherwise sustained partial outage.
    * ``partial`` — the plateau membership mask, ``running & (sm <
      _CEILING_FRAC * ref)``.
    """
    nd = cf.shape[0] // 24
    if nd == 0:
        return None
    day = cf[: nd * 24].reshape(nd, 24)
    dmax, dmean = day.max(1), day.mean(1)
    running = dmean > _RUN_FLOOR_CF
    ref = float(np.percentile(dmax[running], 90)) if running.any() else 0.0
    if ref <= 0.0:
        return None
    sm = (
        pd.Series(dmax)
        .rolling(_SMOOTH_DAYS, center=True, min_periods=4)
        .median()
        .to_numpy()
    )
    partial = running & (sm < _CEILING_FRAC * ref)
    return dmax, ref, sm, partial


def _plateau_spans(partial: np.ndarray) -> list[tuple[int, int]]:
    """Return the ``[(start_day, end_day_excl), ...]`` sustained plateaus.

    Maximal runs of :func:`_plateau_state`'s membership mask lasting at least
    the frozen :data:`_MIN_DAYS`. Both plateau consumers read their spans from
    here, so the detected population is one object by construction (the
    ercot-185 SP-2 covered-hour-set identity is a consequence of this, not an
    accident of two parallel loops).
    """
    nd = int(partial.shape[0])
    out: list[tuple[int, int]] = []
    i = 0
    while i < nd:
        if partial[i]:
            j = i
            while j < nd and partial[j]:
                j += 1
            if j - i >= _MIN_DAYS:
                out.append((i, j))
            i = j
        else:
            i += 1
    return out


def _detect(cf: np.ndarray) -> list[tuple[int, int, float]]:
    """Return ``[(start_day, end_day_excl, derate_factor), ...]`` plateaus."""
    st = _plateau_state(cf)
    if st is None:
        return []
    dmax, ref, _sm, partial = st
    out: list[tuple[int, int, float]] = []
    for i, j in _plateau_spans(partial):
        # Typical depressed ceiling over the window (median ignores the blips,
        # so the derate reflects the sustained reduced capacity).
        ceiling = float(np.median(dmax[i:j]))
        out.append((i, j, round(min(1.0, ceiling / ref), 3)))
    return out


def detect_shaped(cf: np.ndarray) -> list[tuple[int, int, np.ndarray]]:
    """Return ``[(start_day, end_day_excl, per-day derate), ...]`` plateaus.

    The ercot-185 fault-3 repair: the SAME plateaus as :func:`_detect`, over the
    SAME day spans, but carrying a **day-resolved** derate profile instead of a
    single flat factor. `FINDING-ercot172` §4 fault 3 measured the defect this
    fixes — a multi-week MEDIAN of daily maxima imposed as an HOURLY ceiling, so
    a plant averaging 40 % over three weeks is forbidden the 80 % afternoons its
    own CEMS record shows it ran (W A Parish h2827: ceiling 0.36 vs measured
    0.78).

    Construction (``docs/PRECOMMIT-ercot185-fault3-partial-layer-construction-2026-08-09.md``
    §2a, amendment A-1), per plateau ``[i, j)``::

        f0        = round(min(1, median(dmax[i:j]) / ref), 3)   # the incumbent factor
        shaped(d) = clip(f0 * sm[d] / median(sm[i:j]), 0, 1)    # for each day d in [i, j)

    ``f0`` and ``sm`` are medians of the SAME daily-maximum series, differing
    only in the window the median is taken over — the whole plateau versus a
    centered ``_SMOOTH_DAYS`` band — so this is a **grain refinement in time** of
    one measured statistic, the temporal analogue of the ercot-174 unit-grain
    refinement. Because scaling commutes with the median, ``median(shaped[i:j])
    == f0`` exactly (before clipping/rounding): the profile is a **pure
    re-shaping of the incumbent plateau, never a net lift or cut** (the ercot-185
    SP-6 property). Every input is the frozen detector's own — ``_MIN_DAYS``,
    ``_SMOOTH_DAYS``, ``_CEILING_FRAC``, ``_RUN_FLOOR_CF``, ``ref`` — so **zero**
    new scalars enter (rule 23 `[R-DOF]`).

    Fail-safe: a plateau whose ``median(sm[i:j])`` is non-positive cannot be
    normalised, so it falls back to the incumbent flat ``f0`` on every day.

    ``detect_shaped_raw`` is the reported-only variant that skips the
    normalisation; it is NOT the mechanism (see the precommit §2a-bis).
    """
    return _detect_shaped(cf, normalize=True)


def detect_shaped_raw(cf: np.ndarray) -> list[tuple[int, int, np.ndarray]]:
    """Variant RAW of :func:`detect_shaped`: ``min(1, sm[d] / ref)`` per day.

    REPORTED ONLY — measured at the seam as the evidence for the precommit
    §2a-bis argument and never armed, because it changes the plateau's LEVEL as
    well as its shape: plateau membership already guarantees ``sm[d] <
    _CEILING_FRAC * ref`` on every day inside a plateau, so this form is bounded
    above by ``_CEILING_FRAC`` while the incumbent factor (a median of the raw,
    upward-tailed ``dmax``) is not.
    """
    return _detect_shaped(cf, normalize=False)


def _detect_shaped(
    cf: np.ndarray, normalize: bool
) -> list[tuple[int, int, np.ndarray]]:
    """Shared body of :func:`detect_shaped` / :func:`detect_shaped_raw`."""
    st = _plateau_state(cf)
    if st is None:
        return []
    dmax, ref, sm, partial = st
    out: list[tuple[int, int, np.ndarray]] = []
    for i, j in _plateau_spans(partial):
        f0 = round(min(1.0, float(np.median(dmax[i:j])) / ref), 3)
        win = np.asarray(sm[i:j], dtype=float)
        if not normalize:
            prof = np.minimum(1.0, win / ref)
        else:
            mid = float(np.median(win))
            # Fail-safe: an unnormalisable plateau keeps the incumbent flat
            # factor, so the shaped extract can never be worse-identified than
            # the file it refines.
            prof = (
                np.full(win.shape, f0, dtype=float)
                if not mid > 0.0
                else np.clip(f0 * win / mid, 0.0, 1.0)
            )
        out.append((i, j, np.round(prof, 3)))
    return out


def detect_shaped_dayguard(
    cf: np.ndarray,
) -> list[tuple[int, int, np.ndarray, np.ndarray]]:
    """Return ``[(start_day, end_day_excl, guarded derate, day floor), ...]``.

    The R-ERCOT-4 day-grain guard on :func:`detect_shaped`: the SAME plateaus
    over the SAME day spans with the SAME normalized profile, except that no
    day's derate may sit below the plant's OWN same-day measured ceiling::

        floor(d)   = round(min(1, dmax[d] / ref), 3)
        guarded(d) = max(shaped(d), floor(d))

    ``shaped`` scales every day off ``sm``, the centered ``_SMOOTH_DAYS`` rolling
    median of daily maxima, so a cycling plant's full-load days inside a
    low-loading week are capped at the week's level even though its own CEMS
    record shows it ran at ceiling that day (Martin Lake 2021-10-20/21: shaped
    0.385 vs measured 0.997). Availability is never below what a plant
    measurably produced, so the floor is the detector's own statistic applied at
    the detector's own grain; every quantity (``dmax``, ``ref``) is the frozen
    detector's, so zero new scalars enter (rules 21/23). It is a net LIFT on the
    capped days, so the ercot-185 SP-6 median-preservation does not hold for
    this variant; the deriver asserts ``guarded >= floor`` instead.
    docs/handoffs/FINDING-r-ercot-4-validation-years-2026-09-25.md.
    """
    st = _plateau_state(cf)
    if st is None:
        return []
    dmax, ref, _sm, _partial = st
    out: list[tuple[int, int, np.ndarray, np.ndarray]] = []
    for i, j, prof in _detect_shaped(cf, normalize=True):
        floor = np.round(np.minimum(1.0, np.asarray(dmax[i:j], dtype=float) / ref), 3)
        out.append((i, j, np.maximum(prof, floor), floor))
    return out


# ---------------------------------------------------------------------------
# Merit-order guard: economic layup vs mechanical outage (neiso-64)
# ---------------------------------------------------------------------------
# `filter_revealed_outages` above keeps a down span when EITHER it is down
# through >= MIN_INMERIT_HOURS local high-net-load hours OR it is a >= 5-day
# full stop. Both branches were written on the premise the full-stop override
# states outright — "economic idling backs down but does not fully stop for
# weeks" — which is FALSE for a unit priced out of merit for weeks: a New
# England gas CC in a high-basis winter simply does not start. A sustained
# economic LAYUP satisfies both surviving branches, so it is booked as a
# mechanical outage and its capacity is deleted from the availability envelope.
# Measured consequence (results/calibration/FINDING-neiso63-campd-economic-
# layup-2026-07.md): every ISO books 23-46% of its CC capacity-year as outage
# against a real EFOR + planned-maintenance norm of ~10-15%.
#
# The guard is the fix frozen in docs/handoffs/campd-economic-layup-fix-
# charter-2026-07.md section 3a. The phenomenon is fuel-economic, so the
# discriminator is: a window is ECONOMIC LAYUP when the unit's own measured
# short-run marginal cost sat ABOVE the revealed marginal cost of the capacity
# that WAS running, for essentially the whole window.
#
#   SRMC_u(t) = HR_u x delivered_fuel_price(u, t)
#   RCC(t)    = capacity-weighted MERIT_RCC_PCTL quantile of SRMC over the
#               units MEASURED RUNNING at t (CEMS CF >= REAL_RUN_CF)
#   layup     <=> #{t in window : SRMC_u(t) > RCC(t)} / #window >= MERIT_OOM_FRAC
#
# Every input is a measured physical/market quantity — CAMPD operation and heat
# input, and delivered fuel prices (an explicitly admissible backcast input,
# CLAUDE.md rule 13). There is no LMP, no cleared price, no cleared quantity and
# no MWh/price residual anywhere in the construction (rules 11/26): the guard
# reconciles the outage extract to its own measurement basis (rule 14), never to
# a dispatch outcome (rule 13).
#
# Why not the self-referential variant (compare the window's fuel price to a
# percentile of the unit's OWN running-hour price distribution): the unit's heat
# rate cancels out of a within-unit percentile comparison, so it can only see
# the fuel-cost-blowout half of out-of-merit. Probed and REJECTED — it fixed
# NEISO winter but left summer untouched (1.93x -> 1.93x) and, in the mild 2024
# winter, its gain sat inside the same-GW-days placebo band. Ranking against RCC
# is what puts the heat rate back in; it is the only variant that moves all four
# seasons. Common-mode / class-simultaneity discrimination and unit-frequency
# filtering were ruled out earlier (FINDING doc); do not rebuild them.
#
# Identification (rule 23 — these re-derive only on a SOURCE-DATA change, never
# because a residual moved): MERIT_RCC_PCTL and MERIT_OOM_FRAC are identified
# JOINTLY across the ISOs that carry a published outage instrument, against that
# published series alone. They are structural percentiles over per-ISO
# self-referential distributions, so no scalar fitted on one ISO's residual is
# carried into another (rule 24). The window-grain out-of-merit share is close
# to binary (NEISO: p25 = 0.00, p75 = 1.00), so MERIT_OOM_FRAC is not
# load-bearing: 0.70 -> 1.00 moves the NEISO veto count only 560 -> 412.
MERIT_ORDER_GUARD_ENABLED: bool = False
# Capacity-weighted quantile of running-unit SRMC that stands for the revealed
# clearing cost. p90 rather than the max so a single reliability-committed or
# ramping unit cannot set the band.
MERIT_RCC_PCTL: float = 0.90
# Share of a window's hours that must be out of merit for it to be layup.
MERIT_OOM_FRAC: float = 0.90
# Measured heat rates are clipped to this band against CEMS meter noise (a unit
# metering heat input during a start with near-zero gross load prints an
# absurd ratio). 4 MMBtu/MWh is below any real thermal unit; 20 is above any
# unit that would ever be economic.
MERIT_HR_MIN: float = 4.0
MERIT_HR_MAX: float = 20.0

# CAMPD primaryFuelInfo values treated as solid fuel (priced off the F923
# delivered COAL ladder) and as pipeline gas (priced off the ISO delivered gas
# hub). Anything else — oil, wood, process gas, "other" — has no admissible
# delivered series here, so the unit is excluded from BOTH the RCC panel and the
# guard and its windows are kept unchanged (charter D4, fail-safe).
_MERIT_COAL_FUELS: frozenset[str] = frozenset({"coal", "coal refuse"})
_MERIT_GAS_FUELS: frozenset[str] = frozenset(
    {"pipeline natural gas", "natural gas", "other gas"}
)

_MERIT_GAS_BASIS_CSV = _REPO / "data" / "raw" / "gas_basis_by_iso_month.csv"
_MERIT_HH_DAILY_CSV = _REPO / "data" / "raw" / "gas-prices" / "henry_hub_daily.csv"
_MERIT_HH_MONTHLY_CSV = _REPO / "data" / "raw" / "gas-prices" / "henry_hub_monthly.csv"
_MERIT_F923_COSTS = (
    _REPO / "data" / "raw" / "_processed-legacy" / "eia923_monthly_fuel_costs.parquet"
)
_MERIT_UNIT_LEVEL_DIR = _REPO / "data" / "raw" / "campd-unit-level"


def delivered_gas_price_hourly(iso: str, year: int, n_hours: int) -> np.ndarray | None:
    """Measured delivered gas hub price ($/MMBtu) on the year clock, or ``None``.

    ``Henry Hub daily``, re-centred within each month onto the measured
    ``Henry Hub monthly`` mean, plus the ISO's measured monthly basis
    (``data/raw/gas_basis_by_iso_month.csv`` — all six ISOs, 2015-2026). The
    re-centring makes the daily leg mean-preserving at the monthly hub level, so
    only the within-month *shape* is added and the monthly delivered level is
    exactly the measured one. Both legs are measured EIA gas-market series.

    Returns ``None`` when either file is missing or the ISO-year carries no
    basis rows — the guard is then INERT for that ISO-year (charter D4). Henry
    Hub is deliberately NEVER substituted for a missing basis: for NEISO the
    basis IS the signal, and a Henry-Hub fallback would silently switch the test
    off while appearing to run.
    """
    if not (_MERIT_HH_DAILY_CSV.exists() and _MERIT_HH_MONTHLY_CSV.exists()):
        return None
    if not _MERIT_GAS_BASIS_CSV.exists():
        return None
    basis_f = pd.read_csv(_MERIT_GAS_BASIS_CSV)
    basis_f = basis_f[
        (basis_f["iso"] == iso.upper()) & (basis_f["year"].astype(int) == int(year))
    ]
    if basis_f.empty:
        return None
    basis = {
        int(r.month): float(r.basis_usd_mmbtu)
        for r in basis_f.itertuples(index=False)
        if np.isfinite(r.basis_usd_mmbtu)
    }
    hhm_f = pd.read_csv(_MERIT_HH_MONTHLY_CSV)
    hhm_f = hhm_f[hhm_f["year"].astype(int) == int(year)]
    hh_month = {
        int(r.year_month): float(r.price)
        for r in hhm_f.rename(
            columns={"month": "year_month", "price_usd_mmbtu": "price"}
        ).itertuples(index=False)
    }
    hhd = pd.read_csv(_MERIT_HH_DAILY_CSV, parse_dates=["date"])
    hhd = hhd[hhd["date"].dt.year == int(year)]
    if hhd.empty or not hh_month:
        return None
    clock = pd.date_range(f"{year}-01-01", periods=n_hours, freq="h")
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    daily = (
        hhd.set_index("date")["price_usd_mmbtu"]
        .reindex(days)
        .ffill()
        .bfill()
        .to_numpy(dtype=float)
    )
    out_day = np.full(len(days), np.nan)
    for m in range(1, 13):
        sel = days.month == m
        hm, bm = hh_month.get(m), basis.get(m)
        if hm is None or bm is None or not sel.any():
            continue
        dm = float(np.nanmean(daily[sel]))
        # Mean-preserving re-centring: the daily leg contributes exactly hm to
        # the month's mean, so the delivered monthly level is the measured one.
        leg = daily[sel] * (hm / dm) if dm > 0 else np.full(int(sel.sum()), hm)
        out_day[sel] = leg + bm
    if not np.isfinite(out_day).any():
        return None
    day_idx = (clock.normalize() - pd.Timestamp(f"{year}-01-01")).days.to_numpy()
    day_idx = np.clip(day_idx, 0, len(days) - 1)
    return out_day[day_idx]


def _delivered_coal_price_tables(
    iso_states: frozenset[str], year: int
) -> tuple[dict, dict, dict] | None:
    """F923 delivered COAL price ladder: ``(plant-month, state-month, iso-month)``.

    Each rung is the measured EIA-923 delivered cost ($/MMBtu); the state and
    ISO rungs are volume-weighted over the reporting plants. Consumed
    plant → state → ISO, so a plant that does not itself file still prices off
    real regional delivered coal. ``None`` when the F923 cache is absent.
    """
    if not _MERIT_F923_COSTS.exists():
        return None
    d = pd.read_parquet(_MERIT_F923_COSTS)
    d = d[(d["fuel_group"] == "Coal") & (d["year"].astype(int) == int(year))]
    if d.empty:
        return None
    plant = {
        (int(r.plant_id), int(r.month)): float(r.price_per_mmbtu)
        for r in d.itertuples(index=False)
        if np.isfinite(r.price_per_mmbtu)
    }

    def _vw(frame: pd.DataFrame, keys: list[str]) -> dict:
        g = frame.assign(num=frame["price_per_mmbtu"] * frame["quantity"]).groupby(keys)
        s = g["num"].sum() / g["quantity"].sum().replace(0, np.nan)
        return {
            (k if len(keys) == 1 else tuple(k)): float(v)
            for k, v in s.items()
            if np.isfinite(v)
        }

    state = {(str(k[0]), int(k[1])): v for k, v in _vw(d, ["state", "month"]).items()}
    in_iso = d[d["state"].isin(iso_states)]
    iso_m = (
        {int(k): v for k, v in _vw(in_iso, ["month"]).items()}
        if not in_iso.empty
        else {}
    )
    return plant, state, iso_m


@dataclass(frozen=True)
class MeritOrderPanel:
    """Measured merit-order state for one ISO-year (the guard's whole input).

    ``rcc`` is the revealed clearing cost on the year clock — the
    capacity-weighted :data:`MERIT_RCC_PCTL` quantile of ``SRMC`` over the units
    MEASURED RUNNING that hour, ``NaN`` where no running unit could be priced.
    ``srmc`` holds each identified unit's own ``HR x delivered price`` series on
    the same clock. Both are built only from CAMPD operation/heat input and
    delivered fuel prices.

    A unit absent from ``srmc`` is unidentified — no measured heat rate, no
    delivered price for its fuel, or cogeneration (measured non-zero CAMPD
    ``steamLoad``: heat-driven, so it is not economically dispatched and carries
    no merit information). Unidentified units are excluded from the RCC panel
    AND from the guard, so their windows are always kept (charter D4).
    """

    iso: str
    year: int
    rcc: np.ndarray
    srmc: dict[tuple[int, str], np.ndarray]

    def out_of_merit_share(
        self, key: tuple[int, str], start: int, stop: int
    ) -> float | None:
        """Share of hours in ``[start, stop)`` where the unit was out of merit.

        ``None`` when the unit is unidentified or the span carries no hour with
        both a priced unit SRMC and a defined RCC.
        """
        s = self.srmc.get((int(key[0]), str(key[1])))
        if s is None:
            return None
        lo, hi = max(0, int(start)), min(len(self.rcc), int(stop))
        if hi <= lo:
            return None
        unit, ref = s[lo:hi], self.rcc[lo:hi]
        ok = np.isfinite(unit) & np.isfinite(ref)
        n = int(ok.sum())
        if n == 0:
            return None
        return float((unit[ok] > ref[ok]).sum()) / n

    def is_economic_layup(
        self, key: tuple[int, str], start: int, stop: int, frac: float = MERIT_OOM_FRAC
    ) -> bool:
        """True when the span is ECONOMIC LAYUP rather than a mechanical outage.

        Fail-safe: an unidentified unit or an unpriceable span returns ``False``
        (the window is kept), so the guard can only ever REMOVE windows it has
        positive measured evidence against.
        """
        share = self.out_of_merit_share(key, start, stop)
        return share is not None and share >= float(frac)


def build_merit_order_panel(
    iso: str,
    year: int,
    n_hours: int,
    states: tuple[str, ...] | list[str],
    rcc_pctl: float = MERIT_RCC_PCTL,
    member_facilities: dict[str, tuple[int, ...]] | None = None,
) -> MeritOrderPanel | None:
    """Build the ISO-year :class:`MeritOrderPanel` from measured CAMPD + fuel.

    Self-contained by design: it re-reads the CAMPD unit-level parquets for
    ``states`` rather than taking the caller's frames, so the guard never
    depends on how a particular deriver assembled its fleet, and it needs no
    EIA-860 join. ``member_facilities`` optionally admits the ISO's own
    out-of-state fleet members (state -> facility ids): those states' parquets
    are loaded FILTERED to the listed facilities and appended after ``states``,
    and they join the delivered-coal-table scope. The caller derives the map
    from its fleet registry (caiso-199 §3b / PRECHECK-caiso200 §2 — the panel
    stays fleet-blind over ``states``; membership knowledge stays with the
    deriver). Per unit, entirely from CAMPD:

    * **capacity basis** — the unit's own measured peak ``grossLoad`` for the
      year. Used only for the running test and for capacity-weighting the RCC
      quantile, both rank statistics, so the measured peak is a sufficient
      denominator and no nameplate join is required.
    * **running** — ``grossLoad / peak >= REAL_RUN_CF``, the same revealed-run
      threshold the detectors above use.
    * **heat rate** — ``sum(heatInput) / sum(grossLoad)`` over the unit's
      running hours, clipped to ``[MERIT_HR_MIN, MERIT_HR_MAX]``. A unit with
      fewer than :data:`MIN_REAL_RUN_HOURS` running hours has no identified heat
      rate and is dropped (charter D4).
    * **fuel** — ``primaryFuelInfo``: solid fuel prices off the F923 delivered
      coal ladder, pipeline gas off the ISO delivered gas hub, anything else is
      dropped.
    * **cogeneration** — any non-zero measured ``steamLoad`` in the year. Keyed
      on the measured physical quantity, not on a class name (CLAUDE.md rule 17).

    Returns ``None`` when the ISO-year cannot be identified at all (no CEMS
    files, no priceable unit, or no hour with a defined RCC) — the caller then
    leaves every window untouched and the extract is byte-identical.
    """
    cols = [
        "stateCode",
        "facilityId",
        "unitId",
        "date",
        "hour",
        "grossLoad",
        "steamLoad",
        "heatInput",
        "primaryFuelInfo",
    ]
    frames = []
    for st in states:
        path = _MERIT_UNIT_LEVEL_DIR / f"{st}_{year}.parquet"
        if not path.exists():
            continue
        frames.append(pd.read_parquet(path, columns=cols))
    for st, keep in (member_facilities or {}).items():
        path = _MERIT_UNIT_LEVEL_DIR / f"{st}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path, columns=cols)
        fid = pd.to_numeric(df["facilityId"], errors="coerce")
        frames.append(df[fid.isin({int(f) for f in keep})])
    if not frames:
        return None
    c = pd.concat(frames, ignore_index=True)
    c["facilityId"] = pd.to_numeric(c["facilityId"], errors="coerce")
    c = c.dropna(subset=["facilityId"])
    c["facilityId"] = c["facilityId"].astype(int)
    c["unitId"] = c["unitId"].astype(str)
    # Common-generator stack pairs (campd.CAMPD_STACK_DUPLICATE_UNITS) repeat
    # ONE generator's grossLoad on both monitored flue paths while splitting
    # its heat input between them. Summed per unit below, that halves the
    # pair's heat rate and prices the unit at half its SRMC, so its dead spans
    # look IN merit more often and fewer of them clear the guard's
    # MERIT_OOM_FRAC bar (nyiso-184 §4.1: Astoria 8906 panel HR 5.55 against a
    # merged 11.01). Mirror campd._normalize_campd — drop the duplicate's
    # grossLoad copy and re-label it onto its primary, so the per-unit group-by
    # sums the pair into the single generator it physically is (generation
    # once, heat over both paths). Byte-identical for every extract with no
    # registered stack pair.
    from market_sim.data.campd import merge_stack_duplicate_units, stack_duplicate_mask

    _dup = stack_duplicate_mask(c["facilityId"], c["unitId"])
    if bool(_dup.any()):
        c.loc[_dup, "grossLoad"] = 0.0
        c["unitId"] = merge_stack_duplicate_units(c["facilityId"], c["unitId"])
    c["date"] = pd.to_datetime(c["date"])
    c["hour"] = pd.to_numeric(c["hour"], errors="coerce")
    c = c.dropna(subset=["hour"])
    for col in ("grossLoad", "steamLoad", "heatInput"):
        c[col] = pd.to_numeric(c[col], errors="coerce").fillna(0.0)
    c["_h"] = (
        (c["date"] - pd.Timestamp(f"{year}-01-01")).dt.days * 24 + c["hour"].astype(int)
    ).to_numpy()
    c = c[(c["_h"] >= 0) & (c["_h"] < n_hours)]
    if c.empty:
        return None

    gas_px = delivered_gas_price_hourly(iso, year, n_hours)
    # Member states join the coal-table scope so a coal-fuelled member could be
    # priced; inert for CAISO (CA carries no CEMS coal in any derive year and
    # the sole member facility is gas-fuelled — caiso-199 §1b measurement).
    coal_states = frozenset(str(s) for s in states) | frozenset(
        str(s) for s in (member_facilities or {})
    )
    coal_tables = _delivered_coal_price_tables(coal_states, year)
    month_of = pd.date_range(
        f"{year}-01-01", periods=n_hours, freq="h"
    ).month.to_numpy()

    srmc: dict[tuple[int, str], np.ndarray] = {}
    cap: dict[tuple[int, str], float] = {}
    running: dict[tuple[int, str], np.ndarray] = {}
    for (fid, uid), g in c.groupby(["facilityId", "unitId"], observed=True):
        gross = np.zeros(n_hours, dtype=float)
        heat = np.zeros(n_hours, dtype=float)
        steam = np.zeros(n_hours, dtype=float)
        hi = g["_h"].to_numpy(dtype=int)
        np.add.at(gross, hi, g["grossLoad"].to_numpy(dtype=float))
        np.add.at(heat, hi, g["heatInput"].to_numpy(dtype=float))
        np.add.at(steam, hi, g["steamLoad"].to_numpy(dtype=float))
        if steam.any():
            continue  # cogeneration: heat-driven, carries no merit information
        peak = float(gross.max())
        if peak <= 0.0:
            continue
        run = (gross / peak) >= REAL_RUN_CF
        if int(run.sum()) < MIN_REAL_RUN_HOURS:
            continue
        gl = float(gross[run].sum())
        if gl <= 0.0:
            continue
        hr = float(np.clip(heat[run].sum() / gl, MERIT_HR_MIN, MERIT_HR_MAX))
        fuel = str(g["primaryFuelInfo"].iloc[0]).strip().lower()
        if fuel in _MERIT_COAL_FUELS:
            if coal_tables is None:
                continue
            plant_t, state_t, iso_t = coal_tables
            st = str(g["stateCode"].iloc[0])
            px = np.array(
                [
                    plant_t.get((int(fid), int(m)))
                    or state_t.get((st, int(m)))
                    or iso_t.get(int(m))
                    or np.nan
                    for m in month_of
                ],
                dtype=float,
            )
        elif fuel in _MERIT_GAS_FUELS:
            if gas_px is None:
                continue
            px = gas_px
        else:
            continue
        if not np.isfinite(px).any():
            continue
        srmc[(int(fid), str(uid))] = hr * px
        cap[(int(fid), str(uid))] = peak
        running[(int(fid), str(uid))] = run
    if not srmc:
        return None

    keys = sorted(srmc)
    s_mat = np.vstack([srmc[k] for k in keys])  # (n_units, n_hours)
    r_mat = np.vstack([running[k] for k in keys])
    w_vec = np.array([cap[k] for k in keys], dtype=float)
    # Capacity-weighted rcc_pctl quantile of SRMC over the RUNNING units, every
    # hour at once. Units that are off (or unpriced) that hour are pushed to the
    # top of the sort with +inf and carry zero weight, so they can never be
    # selected. Vectorised over hours: the per-hour Python loop this replaces is
    # a 3-order-of-magnitude cost on a six-ISO three-year re-derive.
    on = r_mat & np.isfinite(s_mat)
    s_sort = np.where(on, s_mat, np.inf)
    order = np.argsort(s_sort, axis=0, kind="stable")
    s_sorted = np.take_along_axis(s_sort, order, axis=0)
    w_sorted = np.take_along_axis(np.where(on, w_vec[:, None], 0.0), order, axis=0)
    total = w_sorted.sum(axis=0)
    live = total > 0.0
    cum = np.cumsum(w_sorted, axis=0)
    # First row whose cumulative weight share reaches the quantile. argmax on a
    # boolean picks the first True; an all-False column can only occur where
    # total == 0, which `live` already masks out.
    hit = np.argmax(cum >= rcc_pctl * np.where(live, total, 1.0), axis=0)
    rcc = np.where(live, np.take_along_axis(s_sorted, hit[None, :], axis=0)[0], np.nan)
    rcc = np.where(np.isfinite(rcc), rcc, np.nan)
    if not np.isfinite(rcc).any():
        return None
    return MeritOrderPanel(iso=iso.upper(), year=int(year), rcc=rcc, srmc=srmc)


def filter_merit_order_layup(
    windows: list[tuple[int, int]],
    panel: MeritOrderPanel | None,
    facility_id: int,
    unit_id: object,
    frac: float = MERIT_OOM_FRAC,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Split ``windows`` into ``(mechanical, economic_layup)``.

    ``panel`` ``None`` (guard off, or an ISO-year the guard could not identify)
    returns every window as mechanical and an empty layup list — byte-inert.
    """
    if panel is None:
        return list(windows), []
    key = (int(facility_id), str(unit_id))
    mech: list[tuple[int, int]] = []
    layup: list[tuple[int, int]] = []
    for s, e in windows:
        (layup if panel.is_economic_layup(key, s, e, frac) else mech).append((s, e))
    return mech, layup
