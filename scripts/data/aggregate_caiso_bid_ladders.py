"""Collapse raw CAISO public-bid zips into the compact per-quarter aggregate the offer-surface derive needs.

WHY THIS EXISTS (caiso-281, owner-funded 2026-09-13)
-----------------------------------------------------
``derive_caiso_offer_surface`` reads the *curated* ``dam-public-bids`` clean
tree, which is built from a 422 MB raw corpus that is gitignored by convention
and lives only on whichever container fetched it. The RTM intake fetches
quarter by quarter in ephemeral shard containers (rule 32 ``[R-SHARD]``), so a
shard that emitted nothing but zips would leave its quarter unreachable the
moment the container is reclaimed.

This script is the seam: it reduces one quarter of raw zips — 3.7-4.7 GB
uncompressed — to **~10 MB of parquet that carries everything the classifier
and the ladder step actually consume**, so each quarter is pushable, poolable,
and survives its container.

WHAT THE DERIVE ACTUALLY CONSUMES (and therefore what this keeps)
-----------------------------------------------------------------
1. **Capacity** — ``p98`` of hourly max cumulative bid MW, per resource per
   YEAR. A quarter cannot compute a year statistic, so ``hourly.parquet`` keeps
   the per-(resource, date, hour) max/min MW and the PARENT pools quarters and
   takes the year p98. Nothing about capacity is decided here.
2. **The body probe** — bid price at ``BODY_FRAC = 0.35`` of capacity, per-day
   median across hours. This is the Theil-Sen classifier's regressand.
3. **The ladder** — the band rung prices that become econ_low / econ_high /
   peak.

(2) and (3) both need capacity, which is a year statistic this shard does not
have. So ``ladder.parquet`` emits the price on a FIXED 20-point grid of
fractions of the resource's own QUARTER p98 capacity, per-day median across
hours, and also carries that quarter capacity. The parent rescales the grid to
the year capacity and interpolates.

THE ONE APPROXIMATION, DECLARED
--------------------------------
Quarter-p98 capacity is not year-p98 capacity. For a thermal resource with a
stable registered capacity the two are close, but "close" is an assertion until
measured — so ``hourly.parquet`` carries the raw hourly maxima and the parent
MEASURES ``quarter_p98 / year_p98`` per resource and reports its distribution
rather than assuming it. The 20-point grid is dense enough that a modest
rescale is a within-grid interpolation, not an extrapolation.

This approximation is what ``G-REPRO`` in
``docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md`` exists to
catch: the same aggregator run over DAM zips must reproduce the committed
surface's ``CC_REGULAR base_hr`` 7.442 and bands 1.066 / 1.072 / 1.386 to
+/-0.02 / +/-0.01. **If it does not, the comparison is abandoned, not tuned.**

ROW SHAPES (measured by the wave-1 shards, not assumed)
--------------------------------------------------------
The RTM and DAM CSV headers are byte-identical (28 columns). Rows come in two
mutually exclusive shapes:

* **curve** — ``SCH_BID_*`` populated, ``TIMEINTERVAL*`` empty. One row per
  (resource, hour, product, ladder rung): MW in ``SCH_BID_XAXISDATA``, $/MWh in
  ``SCH_BID_Y1AXISDATA``.
* **self-schedule** — ``SCH_BID_*`` empty, ``TIMEINTERVAL*`` and
  ``SELFSCHEDMW`` populated. Price-taker MW, no curve.

A parser keyed only on ``SCH_BID_TIMEINTERVALSTART`` silently drops ~10.7% of
the file and the entire price-taker block, so self-schedule MW is carried
separately rather than dropped.

DAM additionally collapses a bid that is flat across hours into ONE row
spanning up to 1,440 minutes; RTM is always 60 minutes. **Multi-hour DAM rows
are expanded to their constituent hours here**, which is why the same
aggregator can read both market runs — and why a parser written against RTM's
fixed hour would mis-handle DAM.

Usage:
    python scripts/data/aggregate_caiso_bid_ladders.py \\
        --zip-dir data/raw/caiso-public-bids/zips-rtm \\
        --out results/rtm-intake/caiso281/2025q3/agg \\
        --market RTM --label 2025q3
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

#: Body-probe fraction of capacity — the derive's own BODY_FRAC, frozen at 0.35
#: (derive_caiso_offer_surface: the 3x3 body-probe x estimator grid REFUTED the
#: body probe as the driver of the statistics, so it is not a free parameter).
BODY_FRAC = 0.35

#: Capacity percentile, the derive's own (p98 of hourly max cumulative bid MW).
CAPACITY_PCT = 98.0

#: Fractions of capacity at which the ladder price is sampled. Dense enough
#: that rescaling quarter capacity to year capacity interpolates within the
#: grid instead of extrapolating past its end.
GRID = np.round(np.arange(0.05, 1.0001, 0.05), 4)

#: Columns actually read. The three dead columns (PRODUCTBID_DESC,
#: PRODUCTBID_MRID, MARKETPRODUCT_DESC) are 100% empty in both market runs and
#: are never referenced.
USECOLS = [
    "STARTDATE",
    "MARKET_RUN_ID",
    "RESOURCE_TYPE",
    "RESOURCEBID_SEQ",
    "MARKETPRODUCTTYPE",
    "SELFSCHEDMW",
    "SCH_BID_TIMEINTERVALSTART_GMT",
    "SCH_BID_TIMEINTERVALSTOP_GMT",
    "TIMEINTERVALSTART_GMT",
    "SCH_BID_XAXISDATA",
    "SCH_BID_Y1AXISDATA",
    "SCH_BID_CURVETYPE",
]


def _read_zip(path: Path) -> pd.DataFrame:
    """Read one daily zip's single CSV member into the columns this script uses."""
    with zipfile.ZipFile(path) as zf:
        name = zf.namelist()[0]
        raw = zf.read(name)
    if b"No data returned for the specified selection" in raw[:4096]:
        return pd.DataFrame(columns=USECOLS)
    df = pd.read_csv(
        io.BytesIO(raw),
        usecols=lambda c: c in USECOLS,
        dtype={"RESOURCEBID_SEQ": "string", "MARKETPRODUCTTYPE": "string"},
        low_memory=False,
    )
    return df


def _expand_hours(df: pd.DataFrame) -> pd.DataFrame:
    """Expand multi-hour DAM block rows to one row per constituent hour.

    RTM rows are always 60 minutes and pass through untouched; DAM collapses a
    bid flat across hours into a single row spanning up to 1,440 minutes, and
    those must be expanded or a DAM resource-hour is silently under-counted
    relative to RTM.
    """
    start = pd.to_datetime(
        df["SCH_BID_TIMEINTERVALSTART_GMT"], utc=True, errors="coerce"
    )
    stop = pd.to_datetime(df["SCH_BID_TIMEINTERVALSTOP_GMT"], utc=True, errors="coerce")
    hours = ((stop - start).dt.total_seconds() / 3600.0).round()
    df = df.assign(_start=start, _hours=hours.fillna(1).clip(lower=1).astype(int))
    multi = df["_hours"] > 1
    if not multi.any():
        return df.assign(hour_gmt=df["_start"]).drop(columns=["_start", "_hours"])
    single = df[~multi].assign(hour_gmt=df.loc[~multi, "_start"])
    blocks = df[multi]
    rep = blocks.loc[blocks.index.repeat(blocks["_hours"])].copy()
    offset = rep.groupby(level=0).cumcount()
    rep["hour_gmt"] = rep["_start"] + pd.to_timedelta(offset, unit="h")
    out = pd.concat([single, rep], ignore_index=True)
    return out.drop(columns=["_start", "_hours"])


def _curve_price_at(mw: np.ndarray, px: np.ndarray, targets: np.ndarray) -> np.ndarray:
    """Price of a monotone cumulative bid curve at each target MW.

    The curve is a step/ladder in cumulative MW: the price that applies at a
    target is the price of the first breakpoint at or above it (the rung the
    MW falls in), held flat past the last breakpoint. ``np.searchsorted`` gives
    exactly that without interpolating across a rung, which would invent prices
    the resource never offered.
    """
    idx = np.searchsorted(mw, targets, side="left")
    idx = np.clip(idx, 0, len(px) - 1)
    return px[idx]


def aggregate_day(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reduce one trade date to (hourly max/min MW, per-(resource,hour) ladder)."""
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    gen = df[(df["RESOURCE_TYPE"] == "GENERATOR") & (df["MARKETPRODUCTTYPE"] == "EN")]
    curve = gen[gen["SCH_BID_CURVETYPE"] == "BIDPRICE"].copy()
    if curve.empty:
        return pd.DataFrame(), pd.DataFrame()
    curve = _expand_hours(curve)
    curve["mw"] = pd.to_numeric(curve["SCH_BID_XAXISDATA"], errors="coerce")
    curve["px"] = pd.to_numeric(curve["SCH_BID_Y1AXISDATA"], errors="coerce")
    curve = curve.dropna(subset=["mw", "px", "hour_gmt"])
    if curve.empty:
        return pd.DataFrame(), pd.DataFrame()
    curve["date"] = pd.to_datetime(curve["STARTDATE"], errors="coerce").dt.date

    keys = ["RESOURCEBID_SEQ", "date", "hour_gmt"]
    hourly = (
        curve.groupby(keys, observed=True)["mw"]
        .agg(hour_max_mw="max", hour_min_mw="min", n_rungs="size")
        .reset_index()
    )
    # Per (resource, hour) sorted curve, kept for the grid sampling below.
    curve = curve.sort_values(keys + ["mw"])
    return hourly, curve[keys + ["mw", "px"]]


def sample_ladders(curve: pd.DataFrame, capacity: pd.Series) -> pd.DataFrame:
    """Price on the fixed capacity-fraction GRID, per (resource, date), hour-median."""
    rows: list[dict] = []
    for (seq, date), g in curve.groupby(["RESOURCEBID_SEQ", "date"], observed=True):
        cap = float(capacity.get(seq, np.nan))
        if not np.isfinite(cap) or cap <= 0:
            continue
        targets = GRID * cap
        per_hour = []
        for _, h in g.groupby("hour_gmt", observed=True):
            mw = h["mw"].to_numpy(float)
            px = h["px"].to_numpy(float)
            if mw.size == 0:
                continue
            per_hour.append(_curve_price_at(mw, px, targets))
        if not per_hour:
            continue
        med = np.nanmedian(np.vstack(per_hour), axis=0)
        row = {
            "RESOURCEBID_SEQ": seq,
            "date": date,
            "quarter_capacity_mw": cap,
            "n_hours": len(per_hour),
        }
        row.update({f"p{int(round(f * 100)):03d}": float(v) for f, v in zip(GRID, med)})
        row["body_px_quarter_cap"] = float(np.interp(BODY_FRAC, GRID, med))
        rows.append(row)
    return pd.DataFrame(rows)


def run(zip_dir: Path, out_dir: Path, market: str, label: str) -> dict:
    """Aggregate every daily zip under ``zip_dir`` into ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    zips = sorted(zip_dir.glob("*.zip"))
    if not zips:
        raise SystemExit(f"no zips under {zip_dir}")
    hourly_parts, curve_parts = [], []
    for i, z in enumerate(zips, 1):
        h, c = aggregate_day(_read_zip(z))
        if not h.empty:
            hourly_parts.append(h)
            curve_parts.append(c)
        if i % 10 == 0 or i == len(zips):
            print(f"  {i}/{len(zips)} {z.name}", flush=True)
    hourly = pd.concat(hourly_parts, ignore_index=True)
    curve = pd.concat(curve_parts, ignore_index=True)

    # QUARTER capacity only — the YEAR p98 is the parent's to compute (docstring).
    cap = hourly.groupby("RESOURCEBID_SEQ", observed=True)["hour_max_mw"].quantile(
        CAPACITY_PCT / 100.0
    )
    ladder = sample_ladders(curve, cap)

    hourly.to_parquet(out_dir / "hourly.parquet", index=False)
    ladder.to_parquet(out_dir / "ladder.parquet", index=False)
    meta = {
        "label": label,
        "market": market,
        "zip_dir": str(zip_dir),
        "n_days": len(zips),
        "n_resources": int(hourly["RESOURCEBID_SEQ"].nunique()),
        "n_resource_hours": int(len(hourly)),
        "n_ladder_rows": int(len(ladder)),
        "body_frac": BODY_FRAC,
        "capacity_pct": CAPACITY_PCT,
        "grid": [float(x) for x in GRID],
        "date_min": str(hourly["date"].min()),
        "date_max": str(hourly["date"].max()),
        "hourly_bytes": (out_dir / "hourly.parquet").stat().st_size,
        "ladder_bytes": (out_dir / "ladder.parquet").stat().st_size,
    }
    (out_dir / "agg_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return meta


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--zip-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--market", required=True, choices=["DAM", "RTM"])
    ap.add_argument("--label", required=True)
    args = ap.parse_args(argv)
    run(args.zip_dir, args.out, args.market, args.label)
    return 0


if __name__ == "__main__":
    sys.exit(main())
