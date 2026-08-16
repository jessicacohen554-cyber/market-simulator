"""nyiso-137 — GRADE the NYISO-RTD-CLOCK disclosure against the JOINT Zone-K
lever's kill gates and against the C3c ACTUAL tail count.

Read-only. Solves nothing, scores no model output, writes no product. It reads
the *input* side only (the staged NYISO P-24A monthly zips and the committed
``actual_lmp_hourly_NYISO.parquet``) and answers one question the joint Zone-K
pre-registration has to settle before it is worth a solve:

    Is any instrument the lever is judged by contaminated by the interval
    mis-binning adjudicated in ADDENDUM docs/handoffs/d32-f6fix-2026-08-13.md?

Two parts, because the staged coverage does not permit a direct recount:

PART A — EXACT, on the months whose source zips are present. Rebuilds the
producer's own hub reduction (``derive_actual_lmp._nyiso_wide`` +
``nyiso_zone_hourly``: simple mean of the 11 internal zones) with EXACTLY ONE
thing changed — ``.floor("h")`` (interval-BEGINNING, the committed producer,
adjudicated WRONG) vs ``(ts - 1s).floor("h")`` (interval-ENDING, adjudicated
RIGHT) — and reports the movement of the hub series and of the $300 tail count.
Hours whose 12x300s sample set is incomplete under either convention (month
boundaries) are excluded and reported separately, so no boundary artefact is
counted as a crossing.

PART B — a BOUND on the full-year counts, which Part A cannot measure directly
(only 1 of 10, 3 of 12 and 2 of 42 actual tail hours fall in staged months).
Counts the committed hub series' population inside a proximity band around the
$300 threshold. An hour can only change the tail count if the re-binning moves
it across $300, so the population within +/-d of the threshold is a hard ceiling
on the count movement for any convention delta bounded by d.

Rule 22: 2023-2025 only. The twelve 2022 zips are present and are NOT read --
2022 is under the ACTIVE holdout spend freeze re-confirmed 2026-08-15.

Usage:
    .venv/bin/python scripts/probes/_nyiso137_rtd_clock_c3c_grading.py
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import CALIBRATION_DIR  # noqa: E402
from scripts.data.derive_actual_lmp import (  # noqa: E402
    LMP_DIR,
    NYISO_INTERNAL,
    _EASTERN_TZ,
    _localize_ordered,
    _read_nyiso_csv,
)

OUT = REPO / "results" / "calibration" / "_nyiso137_rtd_clock_c3c_grading.json"

THRESHOLD = 300.0  # calibration_verdict.TAIL_THRESHOLD["NYISO"]
# The tail lives far above the all-hours price distribution, and the
# convention delta is NOT homoskedastic in price, so an all-hours max is the
# wrong ruler for a threshold-crossing ceiling. These are the price floors the
# delta is re-measured over.
PRICE_BANDS = (100.0, 200.0, 250.0, THRESHOLD)
TRAINING_YEARS = (2023, 2024, 2025)
# Rule 22 -- 2022 zips exist on disk and are deliberately NOT enumerated.
STAGED = {
    2023: (6, 12),
    2024: (2, 3, 4, 5, 6, 9),
    2025: (8,),
}
FULL_INTERVALS = 12  # a whole hour of 5-minute RTD stamps


def _month_zone_hourly(year: int, month: int) -> pd.DataFrame | None:
    """``{BEGINNING, ENDING}`` hub series for one staged month, with counts.

    Returns a frame indexed by real (UTC) hour with columns ``beg``/``end``
    (the 11-internal-zone simple-mean hub under each convention) and
    ``n_beg``/``n_end`` (the zone-interval sample count backing each), so
    incomplete boundary hours are identifiable rather than silently averaged.
    """
    path = LMP_DIR / "NYISO" / f"{year}{month:02d}01realtime_zone_csv.zip"
    if not path.exists():
        return None
    with zipfile.ZipFile(path) as z:
        frames = [
            _read_nyiso_csv(z.read(dn)) for dn in z.namelist() if dn.endswith(".csv")
        ]
    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True)
    df = df[df["Name"].isin(NYISO_INTERNAL)]
    ts = pd.to_datetime(df["Time Stamp"], format="%m/%d/%Y %H:%M:%S", errors="coerce")
    df = df[ts.notna()]
    ts = ts[ts.notna()]
    utc = _localize_ordered(ts, df["Name"], _EASTERN_TZ).tz_convert("UTC")
    utc = pd.DatetimeIndex(utc)

    out = {}
    for tag, idx in (
        ("beg", utc.floor("h")),  # committed producer -- adjudicated WRONG
        ("end", (utc - pd.Timedelta("1s")).floor("h")),  # adjudicated RIGHT
    ):
        wide = df.assign(ts=idx).pivot_table(
            index="ts", columns="Name", values="lmp", aggfunc="mean"
        )
        counts = (
            df.assign(ts=idx).pivot_table(
                index="ts", columns="Name", values="lmp", aggfunc="count"
            )
        ).min(axis=1)
        present = [z for z in NYISO_INTERNAL if z in wide.columns]
        out[tag] = wide[present].mean(axis=1)
        out[f"n_{tag}"] = counts
    return pd.DataFrame(out)


def part_a() -> dict:
    """Exact convention delta on every staged in-training month."""
    months: list[dict] = []
    pooled: list[pd.DataFrame] = []
    for year in TRAINING_YEARS:
        for month in STAGED[year]:
            f = _month_zone_hourly(year, month)
            if f is None:
                continue
            # Complete hours only: 12 x 300 s under BOTH conventions. Anything
            # short is a month-boundary artefact of slicing one month out of a
            # continuous series, not a real disagreement.
            whole = (f["n_beg"] == FULL_INTERVALS) & (f["n_end"] == FULL_INTERVALS)
            g = f[whole]
            d = (g["end"] - g["beg"]).abs()
            beg_tail = int((g["beg"] > THRESHOLD).sum())
            end_tail = int((g["end"] > THRESHOLD).sum())
            up = int(((g["beg"] <= THRESHOLD) & (g["end"] > THRESHOLD)).sum())
            down = int(((g["beg"] > THRESHOLD) & (g["end"] <= THRESHOLD)).sum())
            pooled.append(g[["beg", "end"]].assign(year=year, month=month))
            months.append(
                {
                    "year": year,
                    "month": month,
                    "hours_total": int(len(f)),
                    "hours_whole": int(len(g)),
                    "hours_excluded_boundary": int(len(f) - len(g)),
                    "hours_moved_gt_1c": int((d > 0.01).sum()),
                    "share_moved": round(float((d > 0.01).mean()), 4),
                    # C3b is a MONTHLY-shape criterion, so the month mean is
                    # the quantity it actually sees.
                    "month_mean_beginning": round(float(g["beg"].mean()), 4),
                    "month_mean_ending": round(float(g["end"].mean()), 4),
                    "month_mean_shift_pct": round(
                        100.0 * (g["end"].mean() - g["beg"].mean()) / g["beg"].mean(),
                        4,
                    ),
                    "mean_abs_delta": round(float(d.mean()), 4),
                    "p99_abs_delta": round(float(d.quantile(0.99)), 4),
                    "max_abs_delta": round(float(d.max()), 4),
                    "tail_beginning": beg_tail,
                    "tail_ending": end_tail,
                    "crossings_up": up,
                    "crossings_down": down,
                    "net_tail_delta": end_tail - beg_tail,
                }
            )
    agg = {
        "months_measured": len(months),
        "hours_whole": sum(m["hours_whole"] for m in months),
        "hours_moved_gt_1c": sum(m["hours_moved_gt_1c"] for m in months),
        "tail_beginning": sum(m["tail_beginning"] for m in months),
        "tail_ending": sum(m["tail_ending"] for m in months),
        "crossings_up": sum(m["crossings_up"] for m in months),
        "crossings_down": sum(m["crossings_down"] for m in months),
        "max_abs_delta": max((m["max_abs_delta"] for m in months), default=0.0),
    }
    agg["crossings_total"] = agg["crossings_up"] + agg["crossings_down"]
    agg["share_moved"] = (
        round(agg["hours_moved_gt_1c"] / agg["hours_whole"], 4)
        if agg["hours_whole"]
        else None
    )

    # The delta is NOT homoskedastic in price. Re-measure it inside the price
    # region the tail actually lives in -- an all-hours max applied to the
    # threshold neighbourhood would be a ceiling built from the wrong sample.
    pool = pd.concat(pooled)
    by_band: dict[str, dict] = {}
    for floor in (None, *PRICE_BANDS):
        sel = pool if floor is None else pool[pool["beg"] > floor]
        signed = sel["end"] - sel["beg"]
        d = signed.abs()
        key = "all" if floor is None else f">{floor:g}"
        by_band[key] = {
            "hours": int(len(sel)),
            # C3a is a LEVEL criterion: what it sees is the mean shift, not the
            # per-hour movement. Carried here so both can be read off one table.
            "mean_price_beginning": round(float(sel["beg"].mean()), 4),
            "mean_price_ending": round(float(sel["end"].mean()), 4),
            "mean_shift_pct": (
                round(
                    100.0 * (sel["end"].mean() - sel["beg"].mean()) / sel["beg"].mean(),
                    4,
                )
                if len(sel) and float(sel["beg"].mean()) != 0.0
                else None
            ),
            "mean_abs_delta": round(float(d.mean()), 4) if len(sel) else None,
            "p99_abs_delta": round(float(d.quantile(0.99)), 4) if len(sel) else None,
            "max_abs_delta": round(float(d.max()), 4) if len(sel) else None,
            # Signed, because the DIRECTION decides whether the actual tail
            # count rises (tightening C3c's lower band edge) or falls.
            "mean_signed_delta": round(float(signed.mean()), 4) if len(sel) else None,
            "n_up": int((signed > 0).sum()),
            "n_down": int((signed < 0).sum()),
        }

    # Every staged hour that is IN the tail under either convention, itemised.
    tail_rows = pool[(pool["beg"] > THRESHOLD) | (pool["end"] > THRESHOLD)]
    tail_hours = [
        {
            "utc_hour": str(ts),
            "beginning": round(float(r["beg"]), 2),
            "ending": round(float(r["end"]), 2),
            "abs_delta": round(abs(float(r["end"] - r["beg"])), 4),
        }
        for ts, r in tail_rows.iterrows()
    ]
    return {
        "per_month": months,
        "aggregate": agg,
        "delta_by_price_band": by_band,
        "staged_tail_hours": tail_hours,
    }


def part_b(deltas: tuple[float, ...]) -> dict:
    """Proximity-band ceiling on the full-year tail-count movement.

    Only an hour within ``d`` of the threshold can cross it when the
    convention moves prices by at most ``d``. Read off the COMMITTED series
    (the interval-BEGINNING product the scorer actually uses today).
    """
    src = CALIBRATION_DIR / "actual_lmp_hourly_NYISO.parquet"
    df = pd.read_parquet(src)
    years: dict[str, dict] = {}
    for year in TRAINING_YEARS:
        rt = df[df["year"] == year]["rt"].astype("float64")
        row = {
            "hours": int(len(rt)),
            "tail_committed": int((rt > THRESHOLD).sum()),
            "bands": {},
        }
        for d in deltas:
            lo, hi = THRESHOLD - d, THRESHOLD + d
            within = rt[(rt > lo) & (rt <= hi)]
            row["bands"][f"+/-{d:g}"] = {
                "hours_within": int(len(within)),
                "could_drop_out": int((within > THRESHOLD).sum()),
                "could_come_in": int((within <= THRESHOLD).sum()),
            }
        years[str(year)] = row
    return {"source": str(src.relative_to(REPO)), "per_year": years}


# The designated keeper's C3c model tail counts, read off
# `calibration_verdict.py --run-id 2026-08-08-nyiso-133-cod-arm`.
KEEPER_MODEL_TAIL = {2023: 21, 2024: 3, 2025: 24}
TAIL_LO, TAIL_HI = 0.5, 2.0  # calibration_verdict.TAIL_LO / TAIL_HI
TAIL_SMALL_COUNT = 10  # calibration_verdict.TAIL_SMALL_COUNT


def _c3c_pass(model: int, actual: int) -> bool:
    """calibration_verdict's C3c rule, reproduced exactly (lines 1686-1694)."""
    if actual < TAIL_SMALL_COUNT:
        return abs(model - actual) <= TAIL_SMALL_COUNT
    return TAIL_LO <= model / actual <= TAIL_HI


def part_c(bound: dict, ruler: str) -> dict:
    """Which C3c verdicts are REACHABLE inside the mis-binning's own ceiling.

    The kill gates are model-side and invariant (see the finding), but the C3c
    band's DENOMINATOR is the actual count, and the actual count is produced by
    the mis-binned series. This maps the reachable actual-count interval onto
    the verdict the keeper's model counts would then receive.
    """
    out: dict[str, dict] = {}
    for year, model in KEEPER_MODEL_TAIL.items():
        row = bound["per_year"][str(year)]
        committed = row["tail_committed"]
        band = row["bands"][ruler]
        # Ceiling interval: worst case every near-threshold hour crosses.
        lo = committed - band["could_drop_out"]
        hi = committed + band["could_come_in"]
        # The full set of actual counts at which the verdict differs from today.
        today = _c3c_pass(model, committed)
        flips = [a for a in range(max(lo, 0), hi + 1) if _c3c_pass(model, a) != today]
        # Smallest move (in hours, signed) that changes the verdict at all.
        nearest = min(flips, key=lambda a: abs(a - committed)) if flips else None
        out[str(year)] = {
            "model_tail": model,
            "actual_committed": committed,
            "verdict_today": "PASS" if today else "FAIL",
            "reachable_actual_lo": lo,
            "reachable_actual_hi": hi,
            "verdict_flips_within_ceiling": bool(flips),
            "nearest_flipping_actual": nearest,
            "hours_of_movement_to_flip": (
                None if nearest is None else nearest - committed
            ),
            "flip_to": (None if nearest is None else ("PASS" if not today else "FAIL")),
        }
    return out


def main() -> None:
    a = part_a()
    # Band widths, weakest ruler last: the delta measured INSIDE the tail's own
    # price region (the defensible one), the all-hours staged max, and the
    # addendum's 2022 all-hours max -- so the ceiling is quoted against several
    # bounds rather than one chosen number.
    tail_band = a["delta_by_price_band"][f">{THRESHOLD:g}"]["max_abs_delta"] or 0.0
    hi_band = a["delta_by_price_band"][">200"]["max_abs_delta"] or 0.0
    ruler = f"+/-{round(tail_band, 2):g}"
    b = part_b(
        (
            0.01,
            round(tail_band, 2),
            round(hi_band, 2),
            round(a["aggregate"]["max_abs_delta"], 2),
            257.21,
        )
    )
    c = part_c(b, ruler)

    rec = {
        "session": "nyiso-137",
        "what": (
            "Grades the NYISO-RTD-CLOCK interval mis-binning against the joint "
            "Zone-K lever's kill gates K1-K6 and against the C3c ACTUAL tail "
            "count. Input-side only: no LP solved, no model output scored, no "
            "product written."
        ),
        "threshold": THRESHOLD,
        "convention": {
            "committed_producer": "derive_actual_lmp._nyiso_wide -> .floor('h') (interval-BEGINNING, ADJUDICATED WRONG)",
            "correct": "(ts - 1s).floor('h') (interval-ENDING, ADJUDICATED RIGHT)",
            "adjudication": "docs/handoffs/d32-f6fix-2026-08-13.md ADDENDUM A.1-A.7",
        },
        "holdout": (
            "2023-2025 only. The twelve 2022 zips are on disk and were NOT read "
            "-- ACTIVE spend freeze re-confirmed 2026-08-15."
        ),
        "part_a_exact_staged_months": a,
        "part_b_proximity_ceiling": b,
        "part_c_c3c_verdict_reachability": {
            "ruler": ruler,
            "ruler_basis": (
                "max |delta| measured on staged hours ALREADY above the $300 "
                "threshold -- the tail's own price region, not the all-hours "
                "distribution"
            ),
            "keeper": "2026-08-08-nyiso-133-cod-arm",
            "per_year": c,
        },
    }
    OUT.write_text(json.dumps(rec, indent=1, ensure_ascii=True) + "\n")

    ag = a["aggregate"]
    print(f"PART A -- {ag['months_measured']} staged in-training months")
    print(f"  whole hours measured   : {ag['hours_whole']}")
    print(
        f"  hours moved > $0.01    : {ag['hours_moved_gt_1c']} ({ag['share_moved']:.1%})"
    )
    print(f"  max |delta|            : ${ag['max_abs_delta']:.2f}")
    print(f"  tail BEGINNING/ENDING  : {ag['tail_beginning']} / {ag['tail_ending']}")
    print(
        f"  threshold crossings    : {ag['crossings_total']} "
        f"(up {ag['crossings_up']}, down {ag['crossings_down']})"
    )
    for m in a["per_month"]:
        print(
            f"    {m['year']}-{m['month']:02d}  whole {m['hours_whole']:4d}  "
            f"moved {m['share_moved']:6.1%}  mean|d| ${m['mean_abs_delta']:7.4f}  "
            f"max ${m['max_abs_delta']:8.2f}  month-mean shift "
            f"{m['month_mean_shift_pct']:+7.4f}%  tail "
            f"{m['tail_beginning']}->{m['tail_ending']}  "
            f"cross +{m['crossings_up']}/-{m['crossings_down']}"
        )
    print("\n  |delta| BY PRICE BAND (pooled staged hours)")
    for band, v in a["delta_by_price_band"].items():
        print(
            f"    beg {band:>6}: n {v['hours']:5d}  mean|d| ${v['mean_abs_delta']:<9}"
            f"max|d| ${v['max_abs_delta']:<9}"
            f"mean shift {v['mean_shift_pct']:+.4f}%  (up {v['n_up']}/dn {v['n_down']})"
        )
    print("  STAGED TAIL HOURS, itemised")
    for h in a["staged_tail_hours"]:
        print(
            f"    {h['utc_hour']}  beg ${h['beginning']:8.2f}  end ${h['ending']:8.2f}"
            f"  |d| ${h['abs_delta']:.4f}"
        )
    print("\nPART B -- proximity ceiling on the committed full-year counts")
    for y, row in b["per_year"].items():
        print(f"  {y}: committed tail {row['tail_committed']} h")
        for band, v in row["bands"].items():
            print(
                f"      within {band:>10}: {v['hours_within']:4d} h "
                f"(out {v['could_drop_out']}, in {v['could_come_in']})"
            )
    print(f"\nPART C -- C3c verdict reachability, ruler {ruler}")
    for y, v in c.items():
        flip = (
            "verdict STABLE inside the ceiling"
            if not v["verdict_flips_within_ceiling"]
            else (
                f"FLIPS to {v['flip_to']} at actual "
                f"{v['nearest_flipping_actual']} h "
                f"({v['hours_of_movement_to_flip']:+d} h)"
            )
        )
        print(
            f"  {y}: model {v['model_tail']:3d} h vs actual "
            f"{v['actual_committed']:3d} h -> {v['verdict_today']:4s} | "
            f"reachable actual [{v['reachable_actual_lo']}, "
            f"{v['reachable_actual_hi']}] | {flip}"
        )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
