"""nyiso-85 Task 1 — anatomy of NYISO's actual RT >$300 scarcity tail (C3c).

Characterises the ACTUAL hours the C3c criterion scores NYISO against — the
10 / 12 / 42 hours of 2023 / 2024 / 2025 whose **hourly** RT hub price cleared
$300/MWh (``frontend/data/backcast/tail/actual_tail.json``) — in order to bound
how many of them an **hourly** LP could reach at all.

Two questions, two data resolutions:

1. **When and how long?** From the committed hub series
   (``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet``, columns
   ``year, hour, rt, da``) — the same array ``calibration_verdict`` scores. The
   ``hour`` index is the model's chronological clock: row *k* is the *k*-th real
   (UTC) hour after local-standard-time midnight Jan 1, local-standard Feb 29
   dropped (``scripts/data/derive_actual_lmp.py`` module docstring). NYISO local
   standard time is EST = UTC-5, so ``utc(k) = Jan 1 05:00Z + k h``. Tail hours
   are grouped into consecutive-hour *episodes*.

2. **Sustained or a 5-minute transient averaged up?** From the raw RTD 5-minute
   zonal LBMP files (``data/raw/lmp-data/NYISO/<YYYYMM>01realtime_zone_csv.zip``,
   one CSV per day, 5-minute rows per zone). The hub the hourly series uses is
   the simple mean of the ELEVEN INTERNAL zones (external proxy buses HQ / NPX /
   O H / PJM excluded) — so this probe rebuilds that same 11-zone mean at native
   5-minute resolution and reports, per tail hour, how many of the ~12 intervals
   were themselves above threshold. An hour carried by 1-3 intervals is a
   real-time *interval* shortage that an hourly LP has no representation for; an
   hour where most intervals clear high is a sustained condition an hourly LP
   can in principle reproduce.

Only 2023-2025 are read (CLAUDE.md rule 22 [R-HOLDOUT]: NYISO has no
calibration-complete marker, so 2022 / 2019 / <=2021 / H1-2026 stay untouched).
Months with no committed 5-minute zip are reported as ``no_5min`` rather than
guessed at.

This is a SCORING-SIDE characterisation of committed actuals. It runs no LP,
reads no model output, and changes no input.

Usage:
    PYTHONPATH=$PWD:$PWD/src .venv/bin/python scripts/probes/nyiso85_tail_anatomy.py \
        [--threshold 300] [--json-out out.json]
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import CALIBRATION_DIR, RAW_DIR  # noqa: E402

# The eleven internal NYISO load zones the hub mean is taken over, and their
# fold into the five MODEL zones — imported from the deriver that builds the
# committed scoring series rather than duplicated, so this probe and the actual
# it characterises can never drift apart (rule 5 [R-NO-MAGIC]).
sys.path.insert(0, str(REPO / "scripts" / "data"))
from derive_actual_lmp import NYISO_INTERNAL, NYISO_ZONE_MAP  # noqa: E402

# Rule 22 [R-HOLDOUT]: NYISO carries no calibration-complete marker.
YEARS = (2023, 2024, 2025)

LMP_DIR = RAW_DIR / "lmp-data" / "NYISO"


# Chronological-clock row index of local-standard Feb 29 00:00 in a leap year:
# 31 (Jan) + 28 (Feb 1-28) days of hours. The model calendar DROPS local-standard
# Feb 29, so every row at or past this index is 24 real hours later than a naive
# "Jan 1 + k hours" would put it (derive_actual_lmp.py module docstring).
_LEAP_SKIP_INDEX = (31 + 28) * 24


def _is_leap(year: int) -> bool:
    """Gregorian leap-year test."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _utc_of_hour(year: int, hour: int) -> dt.datetime:
    """Return the UTC instant of chronological-clock row ``hour`` in ``year``.

    Row 0 is local-standard-time midnight Jan 1 = 05:00Z for NYISO (EST=UTC-5).
    In a leap year the local-standard Feb 29 is dropped from the 8760 calendar,
    so rows at/after ``_LEAP_SKIP_INDEX`` step over that day. Verified against
    the raw 5-minute source: the shifted mapping reproduces the committed hourly
    parquet to MAE 0.00 $/MWh for 2024-04 and 2024-06, the naive one to 9.8-11.9.
    """
    k = int(hour)
    if _is_leap(year) and k >= _LEAP_SKIP_INDEX:
        k += 24
    return dt.datetime(year, 1, 1, 5, 0) + dt.timedelta(hours=k)


def _prevailing(utc: dt.datetime) -> tuple[dt.datetime, str]:
    """Return (local prevailing timestamp, tz label) for a UTC instant.

    NYISO prevailing time is EST (UTC-5) outside DST and EDT (UTC-4) inside it.
    US DST: second Sunday in March 07:00Z -> first Sunday in November 06:00Z.
    """
    y = utc.year
    mar = dt.datetime(y, 3, 1)
    second_sun = mar + dt.timedelta(days=(6 - mar.weekday()) % 7 + 7)
    nov = dt.datetime(y, 11, 1)
    first_sun = nov + dt.timedelta(days=(6 - nov.weekday()) % 7)
    start = second_sun.replace(hour=7)
    end = first_sun.replace(hour=6)
    if start <= utc < end:
        return utc - dt.timedelta(hours=4), "EDT"
    return utc - dt.timedelta(hours=5), "EST"


def _hub_hourly(year: int) -> pd.DataFrame:
    """Committed hourly hub RT/DA series for ``year`` (the C3c scoring basis)."""
    df = pd.read_parquet(CALIBRATION_DIR / "actual_lmp_hourly_NYISO.parquet")
    df = df[df["year"] == int(year)].sort_values("hour").reset_index(drop=True)
    return df


# Public NYISO MIS archive for the monthly 5-minute zonal RTD LBMP zips — the
# same product already partly committed under data/raw/lmp-data/NYISO/ and the
# verified source of the committed hourly parquet (see _utc_of_hour). Months not
# in the repo are fetched here on demand to a cache dir rather than bulk-added to
# the immutable raw root; the URL makes the characterisation reproducible.
MIS_URL = "http://mis.nyiso.com/public/csv/realtime/{year}{month:02d}01realtime_zone_csv.zip"


def _month_zip(year: int, month: int, cache: Path | None) -> Path | None:
    """Return a path to the month's 5-minute zip: committed copy, else cache.

    With ``cache`` set, a month absent from ``data/raw/lmp-data/NYISO`` is
    downloaded from the public MIS archive into ``cache``. Rule 22 [R-HOLDOUT]:
    only in-training years are ever requested (``YEARS`` gates every caller).
    """
    committed = LMP_DIR / f"{year}{month:02d}01realtime_zone_csv.zip"
    if committed.exists():
        return committed
    if cache is None:
        return None
    if int(year) not in YEARS:  # rule 22 belt-and-braces
        raise SystemExit(f"refusing to fetch out-of-training year {year}")
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / f"{year}{month:02d}01realtime_zone_csv.zip"
    if not dest.exists():
        import urllib.request

        url = MIS_URL.format(year=year, month=month)
        try:
            with urllib.request.urlopen(url, timeout=180) as r, dest.open("wb") as fh:
                fh.write(r.read())
        except Exception as exc:  # noqa: BLE001 - a missing month is reported, not fatal
            print(f"  [fetch failed] {url}: {exc}", file=sys.stderr)
            dest.unlink(missing_ok=True)
            return None
    return dest


def _load_5min_month(
    year: int, month: int, cache: Path | None = None
) -> pd.DataFrame | None:
    """Return the 5-minute zonal RTD LBMP frame for a month, or ``None``.

    Columns: ``ts`` (naive PREVAILING-clock timestamp as published), ``Name``,
    ``lbmp``. NYISO's CSVs carry no timezone column, so the caller converts.
    """
    path = _month_zip(year, month, cache)
    if path is None or not path.exists():
        return None
    frames = []
    with zipfile.ZipFile(path) as z:
        for name in sorted(n for n in z.namelist() if n.endswith(".csv")):
            d = pd.read_csv(io.BytesIO(z.read(name)))
            d = d[["Time Stamp", "Name", "LBMP ($/MWHr)"]].rename(
                columns={"Time Stamp": "ts", "LBMP ($/MWHr)": "lbmp"}
            )
            frames.append(d)
    if not frames:
        return None
    out = pd.concat(frames, ignore_index=True)
    out["ts"] = pd.to_datetime(out["ts"], format="%m/%d/%Y %H:%M:%S")
    out["lbmp"] = pd.to_numeric(out["lbmp"], errors="coerce")
    return out[out["Name"].isin(NYISO_INTERNAL)]


def _episodes(hours: list[int]) -> list[list[int]]:
    """Group a sorted hour list into runs of consecutive hours."""
    eps: list[list[int]] = []
    for h in sorted(hours):
        if eps and h == eps[-1][-1] + 1:
            eps[-1].append(h)
        else:
            eps.append([h])
    return eps


def _interval_anatomy(
    month_5min: pd.DataFrame, local: dt.datetime, threshold: float
) -> dict | None:
    """Per-interval anatomy of one tail hour from 5-minute zonal data.

    ``local`` is the PREVAILING-clock hour start (the clock NYISO's CSVs use).
    Returns ``None`` if the hour has no rows. The interval hub is the simple
    mean of the eleven internal zones in that interval — the 5-minute analogue
    of the hourly hub the C3c count is taken on.
    """
    lo = local
    hi = local + dt.timedelta(hours=1)
    win = month_5min[(month_5min["ts"] >= lo) & (month_5min["ts"] < hi)]
    if win.empty:
        return None
    hub = win.groupby("ts")["lbmp"].mean().sort_index()
    zmax = win.groupby("ts")["lbmp"].max()
    # Which model zone carried the hour (max mean-over-hour zonal price).
    zone_hour = win.groupby("Name")["lbmp"].mean()
    model_zone_mean = {
        mz: float(np.mean([zone_hour[z] for z in members if z in zone_hour.index]))
        for mz, members in NYISO_ZONE_MAP.items()
        if any(z in zone_hour.index for z in members)
    }
    top_zone = max(model_zone_mean, key=model_zone_mean.get) if model_zone_mean else None
    n = int(len(hub))
    n_gt = int((hub > threshold).sum())
    return {
        "intervals": n,
        "intervals_hub_gt": n_gt,
        "frac_intervals_gt": round(n_gt / n, 3) if n else None,
        "hub_5min_max": round(float(hub.max()), 1),
        "hub_5min_min": round(float(hub.min()), 1),
        "hub_5min_median": round(float(hub.median()), 1),
        "hub_hour_mean": round(float(hub.mean()), 1),
        "any_zone_5min_max": round(float(zmax.max()), 1),
        "top_model_zone": top_zone,
        "model_zone_hour_mean": {k: round(v, 1) for k, v in model_zone_mean.items()},
    }


def _classify(an: dict | None, threshold: float) -> str:
    """Label an hour SUSTAINED / MIXED / TRANSIENT / no_5min from its anatomy.

    The line an hourly LP can be asked to reproduce: an hour whose *majority* of
    5-minute intervals cleared the threshold is a sustained hourly condition; an
    hour carried by <= 1/4 of its intervals is an RT-interval transient whose
    hourly mean is an averaging artifact of a few deep spikes.
    """
    if an is None:
        return "no_5min"
    f = an["frac_intervals_gt"]
    if f is None:
        return "no_5min"
    if f >= 0.5:
        return "SUSTAINED"
    if f <= 0.25:
        return "TRANSIENT"
    return "MIXED"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--threshold", type=float, default=300.0)
    ap.add_argument("--json-out", type=Path, default=None)
    ap.add_argument(
        "--fetch-cache",
        type=Path,
        default=None,
        help=(
            "Directory to download months absent from data/raw/lmp-data/NYISO into "
            "(public NYISO MIS archive). Omit to characterise only committed months."
        ),
    )
    args = ap.parse_args(argv)
    thr = float(args.threshold)

    out: dict = {"threshold": thr, "years": {}}
    month_cache: dict[tuple[int, int], pd.DataFrame | None] = {}

    for year in YEARS:
        hub = _hub_hourly(year)
        tail = hub[hub["rt"] > thr]
        hours = tail["hour"].astype(int).tolist()
        rows = []
        for _, r in tail.iterrows():
            h = int(r["hour"])
            utc = _utc_of_hour(year, h)
            local, tz = _prevailing(utc)
            key = (local.year, local.month)
            if key not in month_cache:
                month_cache[key] = _load_5min_month(*key, cache=args.fetch_cache)
            m5 = month_cache[key]
            an = _interval_anatomy(m5, local, thr) if m5 is not None else None
            rows.append(
                {
                    "hour_index": h,
                    "utc": utc.strftime("%Y-%m-%d %H:%MZ"),
                    "local": local.strftime("%Y-%m-%d %H:%M") + f" {tz}",
                    "dow": local.strftime("%a"),
                    "hub_rt_hourly": round(float(r["rt"]), 1),
                    "hub_da_hourly": round(float(r["da"]), 1),
                    "class": _classify(an, thr),
                    "anatomy": an,
                }
            )
        eps = _episodes(hours)
        counts: dict[str, int] = defaultdict(int)
        for row in rows:
            counts[row["class"]] += 1
        out["years"][str(year)] = {
            "tail_hours": len(hours),
            "episodes": [
                {
                    "len": len(e),
                    "start_local": _prevailing(_utc_of_hour(year, e[0]))[0].strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                }
                for e in eps
            ],
            "n_episodes": len(eps),
            "max_episode_len": max((len(e) for e in eps), default=0),
            "class_counts": dict(counts),
            "hours": rows,
        }

    # ── report ──────────────────────────────────────────────────────────────
    for year in YEARS:
        y = out["years"][str(year)]
        print(f"\n=== {year} — {y['tail_hours']} actual RT hub hours > ${thr:.0f} ===")
        print(
            f"  episodes: {y['n_episodes']} (max run {y['max_episode_len']} h)   "
            f"classes: {dict(y['class_counts'])}"
        )
        print(
            f"  {'local':<20} {'dow':<4} {'hub_rt':>8} {'hub_da':>8} "
            f"{'int>thr':>9} {'5m max':>8} {'5m med':>8}  {'class':<10} zone"
        )
        for r in y["hours"]:
            a = r["anatomy"]
            if a:
                iv = f"{a['intervals_hub_gt']}/{a['intervals']}"
                mx = f"{a['hub_5min_max']:.0f}"
                md = f"{a['hub_5min_median']:.0f}"
                zn = a["top_model_zone"] or ""
            else:
                iv = mx = md = "-"
                zn = ""
            print(
                f"  {r['local']:<20} {r['dow']:<4} {r['hub_rt_hourly']:>8.1f} "
                f"{r['hub_da_hourly']:>8.1f} {iv:>9} {mx:>8} {md:>8}  "
                f"{r['class']:<10} {zn}"
            )

    tot: dict[str, int] = defaultdict(int)
    for year in YEARS:
        for k, v in out["years"][str(year)]["class_counts"].items():
            tot[k] += v
    n_all = sum(tot.values())
    print(f"\n=== 2023-2025 combined ({n_all} tail hours) ===")
    for k in ("SUSTAINED", "MIXED", "TRANSIENT", "no_5min"):
        if tot.get(k):
            print(f"  {k:<10} {tot[k]:>3}  ({tot[k] / n_all:.0%})")
    out["combined_class_counts"] = dict(tot)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(out, indent=1))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
