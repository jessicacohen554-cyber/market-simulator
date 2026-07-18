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

from pathlib import Path

import numpy as np
import pandas as pd

# Repository root: this module lives at scripts/lib/outage_detect.py, so the
# repo is two directories up. Used only to resolve the EIA-930 net-load file for
# the revealed-availability mask (no market_sim import, so the lib stays usable
# regardless of the importing script's sys.path setup).
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


def _detect(cf: np.ndarray) -> list[tuple[int, int, float]]:
    """Return ``[(start_day, end_day_excl, derate_factor), ...]`` plateaus."""
    nd = cf.shape[0] // 24
    if nd == 0:
        return []
    day = cf[: nd * 24].reshape(nd, 24)
    dmax, dmean = day.max(1), day.mean(1)
    running = dmean > _RUN_FLOOR_CF
    ref = float(np.percentile(dmax[running], 90)) if running.any() else 0.0
    if ref <= 0.0:
        return []
    # Smooth the daily-max ceiling with a centered rolling median so brief
    # recovery blips (a unit cycling back for a day or two) don't break an
    # otherwise sustained partial outage.
    sm = (
        pd.Series(dmax)
        .rolling(_SMOOTH_DAYS, center=True, min_periods=4)
        .median()
        .to_numpy()
    )
    partial = running & (sm < _CEILING_FRAC * ref)
    out, i = [], 0
    while i < nd:
        if partial[i]:
            j = i
            while j < nd and partial[j]:
                j += 1
            if j - i >= _MIN_DAYS:
                # Typical depressed ceiling over the window (median ignores the
                # blips, so the derate reflects the sustained reduced capacity).
                ceiling = float(np.median(dmax[i:j]))
                out.append((i, j, round(min(1.0, ceiling / ref), 3)))
            i = j
        else:
            i += 1
    return out
