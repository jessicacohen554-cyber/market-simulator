"""Derive coal/CC outage windows from EPA CAMPD hourly gross generation.

A plant is "really running" only when it sustains a capacity factor above
:data:`REAL_RUN_CF` for at least :data:`MIN_REAL_RUN_HOURS` consecutive hours.
Everything else — fully off, and brief or low-output blips (a few hours, or
2-10% CF "testing" that never sustains) — counts as outage. Outage windows are
the maximal not-really-running spans of at least ``--min-outage-days``.

This replaces the sparse, hand-maintained ``ercot-outages.csv`` (which only
covered a handful of plants) with CAMPD-measured windows for every coal/CC
plant the CEMS extract covers. Writes a schema-compatible CSV
(oris_code, plant_name, unit, outage_start, outage_stop, duration_hours) the
historic-outage overlay consumes.

Note: mixed coal/gas facilities (W A Parish, Barney M Davis) report one
combined CEMS facility series, so a coal-unit outage is masked by the gas
units and will not be detected — same limitation noted in the manual analysis.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_campd_bins  # noqa: E402

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

# Plant groups whose outages we derive (coal + combined cycle + gas steam).
# Peaker-class ST_GAS plants are emitted here but excluded at overlay time
# (outages.ST_GAS_PEAKER_PLANTS), since they run economically without outages.
GROUPS = frozenset({"COAL", "CC_REGULAR", "CC_CHP", "CT_CHP", "ST_GAS", "ST_CHP"})

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


# EIA-930 balancing-authority code per model ISO (the eia-930-hourly file stem).
_ISO_TO_BA: dict[str, str] = {
    "ERCOT": "ERCO",
    "CAISO": "CISO",
    "PJM": "PJM",
    "NYISO": "NYIS",
    "NEISO": "ISNE",
    "MISO": "MISO",
}


def high_load_mask(
    iso: str, year: int, n_hours: int, pctl: float = HIGH_LOAD_PCTL
) -> np.ndarray | None:
    """Boolean ``(n_hours,)`` mask: was the system in its high-NET-LOAD band?

    Net load = measured EIA-930 ``demand − wind gen − solar gen``
    (data/raw/eia-930-hourly/``<BA> hourly.parquet``). ERCOT's file carries EIA's
    reconciled ``Adjusted demand``/``Adjusted WND Gen``/``Adjusted SUN Gen``
    series; the other BA extracts only carry the raw ``Demand``/``NG: WND``/
    ``NG: SUN`` columns, so we fall back to those when the Adjusted ones are
    absent (the raw series is an equally exogenous net-load proxy). Flags hours
    above the year's ``pctl`` net-load percentile and maps them onto the
    detector's calendar clock by ``(month, day, hour)`` (the EIA-930 file is
    itself calendar/leap-aware, so alignment is exact). Net load (not raw load)
    so winter-storm / VRE-drought tightness — high-net-load hours below the
    summer raw-load peak — is caught. Returns ``None`` when the BA file/year is
    unavailable, or the demand column is missing (no-op).
    """
    ba = _ISO_TO_BA.get(iso.upper())
    if ba is None:
        return None
    path = REPO / "data" / "raw" / "eia-930-hourly" / f"{ba} hourly.parquet"
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
    thresh = float(np.nanquantile(net, pctl))
    key = {
        (t.month, t.day, t.hour): bool(np.isfinite(v) and v > thresh)
        for t, v in zip(df["dt"], net)
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


def _nameplate_groups(
    iso: str, bins_path: str
) -> tuple[dict[int, float], dict[int, str], dict[int, str]]:
    """Return ``(nameplate, name, group)`` per coal/CC/gas-steam plant code.

    ERCOT reads the curated ``custom-bin-assignments.csv`` (one row per
    plant, with a measured bin nameplate). Every other ISO is built from the
    EIA-860 fleet: generators are summed per plant code over the GROUPS
    classes, the plant's dominant class (by capacity) is its group, and the
    summed capacity is its nameplate — the denominator for the capacity
    factor the outage detector thresholds on.
    """
    if iso.upper() == "ERCOT":
        bins = load_campd_bins(bins_path)
        coalcc = bins[bins["Plant_Group"].isin(GROUPS)]
        nameplate = dict(zip(coalcc["Plant_Code"].astype(int), coalcc["capacity_mw"]))
        name = dict(zip(coalcc["Plant_Code"].astype(int), coalcc["Plant_Name"]))
        group = dict(zip(coalcc["Plant_Code"].astype(int), coalcc["Plant_Group"]))
        return nameplate, name, group

    from collections import defaultdict

    from market_sim.data.fleet import load_fleet_from_csv

    cap_by_group: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    names: dict[int, str] = {}
    for g in load_fleet_from_csv(iso):
        if g.plant_group not in GROUPS:
            continue
        code = int(g.plant_code)
        if code <= 0:
            continue
        cap_by_group[code][g.plant_group] += float(g.pmax_mw)
        names.setdefault(code, g.name)

    nameplate, name, group = {}, {}, {}
    for code, groups in cap_by_group.items():
        nameplate[code] = sum(groups.values())
        group[code] = max(groups, key=groups.get)
        name[code] = names[code]
    return nameplate, name, group


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument("--min-outage-days", type=float, default=2.0)
    ap.add_argument(
        "--bins",
        default=str(REPO / "data" / "raw" / "reference" / "custom-bin-assignments.csv"),
    )
    ap.add_argument(
        "--out",
        default=None,
        help="Output CSV. Defaults to data/raw/campd-outages.csv for "
        "ERCOT and campd-outages-{ISO}.csv for other ISOs.",
    )
    ap.add_argument(
        "--no-inmerit-filter",
        action="store_true",
        help="Disable the revealed-availability (high-load) filter — keep every "
        "detected down span (pre-fix behaviour).",
    )
    ap.add_argument(
        "--high-load-pctl",
        type=float,
        default=HIGH_LOAD_PCTL,
        help=f"System-load percentile above which an hour is 'high load' "
        f"(default {HIGH_LOAD_PCTL}).",
    )
    ap.add_argument(
        "--min-inmerit-hours",
        type=int,
        default=MIN_INMERIT_HOURS,
        help=f"High-load hours a span must overlap to be a real outage "
        f"(default {MIN_INMERIT_HOURS}).",
    )
    args = ap.parse_args()
    min_outage_hours = int(round(args.min_outage_days * 24))
    inmerit_cache: dict[int, np.ndarray | None] = {}
    iso = args.iso.upper()
    if args.out is None:
        fname = "campd-outages.csv" if iso == "ERCOT" else f"campd-outages-{iso}.csv"
        args.out = str(RAW_DATA_DIR / fname)

    nameplate, pname, grp = _nameplate_groups(iso, args.bins)

    states = campd.states_for_iso(iso)
    df = campd.load_campd_hourly(states, args.years)

    rows = []
    summary = []
    for code in sorted(nameplate):
        npl = float(nameplate[code])
        for yr in args.years:
            grid = campd.plant_hourly_grid(df, code, yr)
            if grid.empty:
                continue
            # Full calendar-year clock: CAMPD only zero-fills within a plant's
            # reported span, so a unit that stops reporting when it goes offline
            # (e.g. San Miguel Sep-Dec 2025) leaves those months missing rather
            # than zero. Reindex to the whole year and zero-fill — missing = no
            # activity = offline — so the shutdown is caught for every group.
            full = pd.date_range(
                f"{yr}-01-01",
                f"{yr}-12-31 23:00:00",
                freq="h",
                tz=grid.index.tz,
            )
            gross = grid["gross_mw"].reindex(full).fillna(0.0).to_numpy(dtype=float)
            ts = full
            if grp[code] == "ST_GAS":
                windows = detect_outages_eventbased(
                    gross,
                    npl,
                    ST_GAS_MIN_OUTAGE_HOURS,
                    ST_GAS_CF_PEAK,
                )
            else:
                windows = detect_outages(gross, npl, min_outage_hours)
            # Revealed-availability filter: drop down spans that never overlap a
            # high-load (system-needed) hour — economic idling, not outage — so
            # the unit stays available and the co-opt keeps it as reserve.
            if windows and not args.no_inmerit_filter:
                if yr not in inmerit_cache:
                    inmerit_cache[yr] = high_load_mask(
                        iso, yr, len(ts), args.high_load_pctl
                    )
                mask = inmerit_cache[yr]
                if mask is not None:
                    windows = [
                        (s, e)
                        for s, e in windows
                        if mask[s:e].sum() >= args.min_inmerit_hours
                    ]
            tot_days = sum(e - s for s, e in windows) / 24.0
            if windows:
                summary.append(
                    (
                        code,
                        pname[code],
                        grp[code],
                        yr,
                        len(windows),
                        tot_days,
                        max(e - s for s, e in windows) / 24.0,
                    )
                )
            for s, e in windows:
                start = ts[s]
                stop = ts[e - 1] + pd.Timedelta(hours=1)
                rows.append(
                    {
                        "oris_code": code,
                        "plant_name": pname[code],
                        "unit": 1,
                        "outage_start": start.strftime("%Y-%m-%d %H:00:00"),
                        "outage_stop": stop.strftime("%Y-%m-%d %H:00:00"),
                        "duration_hours": int((stop - start).total_seconds() // 3600),
                    }
                )

    out = pd.DataFrame(
        rows,
        columns=[
            "oris_code",
            "plant_name",
            "unit",
            "outage_start",
            "outage_stop",
            "duration_hours",
        ],
    ).sort_values(["oris_code", "outage_start"])
    out.to_parquet  # noqa: B018  (silence linters; we write CSV)
    out.to_csv(args.out, index=False)

    print(f"wrote {len(out)} outage windows to {args.out}\n")
    print(
        f"{'code':>6} {'plant':<26}{'group':<12}{'yr':>5}{'#win':>5}"
        f"{'out d':>8}{'maxwin d':>9}"
    )
    for code, nm, g, yr, n, td, mx in sorted(summary, key=lambda r: (r[0], r[3])):
        print(f"{code:>6} {nm[:25]:<26}{g:<12}{yr:>5}{n:>5}{td:>8.0f}{mx:>9.0f}")


if __name__ == "__main__":
    main()
