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

from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    BIN_GROUP_TO_FUEL,
    load_campd_bins,
)

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
GROUPS = frozenset(
    {"COAL", "CC_REGULAR", "CC_CHP", "CT_CHP", "ST_GAS", "ST_CHP"}
)


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
    return [
        (s, e) for s, e in _runs(~real) if e - s >= min_outage_hours
    ]


def detect_outages_eventbased(
    gross: np.ndarray, nameplate: float, min_outage_hours: int,
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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument("--min-outage-days", type=float, default=2.0)
    ap.add_argument(
        "--bins", default=str(REPO / "inputs" / "custom-bin-assignments.csv")
    )
    ap.add_argument(
        "--out", default=str(REPO / "inputs" / "raw-data" / "campd-outages.csv")
    )
    args = ap.parse_args()
    min_outage_hours = int(round(args.min_outage_days * 24))

    bins = load_campd_bins(args.bins)
    coalcc = bins[bins["Plant_Group"].isin(GROUPS)]
    nameplate = dict(zip(coalcc["Plant_Code"].astype(int), coalcc["capacity_mw"]))
    pname = dict(zip(coalcc["Plant_Code"].astype(int), coalcc["Plant_Name"]))
    grp = dict(zip(coalcc["Plant_Code"].astype(int), coalcc["Plant_Group"]))

    states = campd.states_for_iso(args.iso)
    df = campd.load_campd_hourly(states, args.years)

    rows = []
    summary = []
    for code in sorted(nameplate):
        npl = float(nameplate[code])
        for yr in args.years:
            grid = campd.plant_hourly_grid(df, code, yr)
            if grid.empty:
                continue
            if grp[code] == "ST_GAS":
                # Full calendar-year clock: CAMPD only zero-fills within a
                # plant's reported span, so months entirely outside it (a
                # non-reporting shutdown) are missing. Reindex to the whole
                # year and zero-fill — missing = no activity = offline.
                full = pd.date_range(
                    f"{yr}-01-01", f"{yr}-12-31 23:00:00",
                    freq="h", tz=grid.index.tz,
                )
                gross = grid["gross_mw"].reindex(full).fillna(0.0).to_numpy(
                    dtype=float
                )
                ts = full
                windows = detect_outages_eventbased(
                    gross, npl, ST_GAS_MIN_OUTAGE_HOURS, ST_GAS_CF_PEAK,
                )
            else:
                gross = grid["gross_mw"].to_numpy(dtype=float)
                ts = grid.index
                windows = detect_outages(gross, npl, min_outage_hours)
            tot_days = sum(e - s for s, e in windows) / 24.0
            if windows:
                summary.append((code, pname[code], grp[code], yr,
                                len(windows), tot_days,
                                max(e - s for s, e in windows) / 24.0))
            for s, e in windows:
                start = ts[s]
                stop = ts[e - 1] + pd.Timedelta(hours=1)
                rows.append({
                    "oris_code": code,
                    "plant_name": pname[code],
                    "unit": 1,
                    "outage_start": start.strftime("%Y-%m-%d %H:00:00"),
                    "outage_stop": stop.strftime("%Y-%m-%d %H:00:00"),
                    "duration_hours": int((stop - start).total_seconds() // 3600),
                })

    out = pd.DataFrame(rows, columns=[
        "oris_code", "plant_name", "unit", "outage_start", "outage_stop",
        "duration_hours",
    ]).sort_values(["oris_code", "outage_start"])
    out.to_parquet  # noqa: B018  (silence linters; we write CSV)
    out.to_csv(args.out, index=False)

    print(f"wrote {len(out)} outage windows to {args.out}\n")
    print(f"{'code':>6} {'plant':<26}{'group':<12}{'yr':>5}{'#win':>5}"
          f"{'out d':>8}{'maxwin d':>9}")
    for code, nm, g, yr, n, td, mx in sorted(summary, key=lambda r: (r[0], r[3])):
        print(f"{code:>6} {nm[:25]:<26}{g:<12}{yr:>5}{n:>5}{td:>8.0f}{mx:>9.0f}")


if __name__ == "__main__":
    main()
