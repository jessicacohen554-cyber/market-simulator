"""Reduce one CAISO public-bid MARKET-YEAR of raw OASIS zips to the derive's EXACT per-resource-year statistics.

WHY THIS EXISTS (caiso-283, 2026-09-16 — the successor to caiso-282)
---------------------------------------------------------------------
``aggregate_caiso_bid_ladders.py`` (caiso-281) reduced a QUARTER of zips to a
20-point price grid on quarter capacity. That instrument failed the charter's
G-REPRO on every CC band by +0.10..+0.14 (``docs/RESULT-caiso282-rtm-pool-
g-repro-failed-2026-09-16.md``): one cause was a rung-convention defect (fixed
there), the others are approximations a quarter cannot avoid — quarter vs
year capacity, a grid integral in place of the derive's exact step integral,
and a median of daily medians in place of the derive's median over hours.

A shard that holds a WHOLE YEAR of one market run can compute the derive's
estimation unit exactly, so this script does, by calling the derive's OWN
functions on the curate step's OWN parser:

* capacity  = ``p98`` of ``segment_mw`` over every GENERATOR/EN curve row of
  the resource-year (``derive_caiso_offer_surface.main``: ``cap_ry``), exact
  from a per-resource value-count histogram (pass 1);
* body probe = ``_price_at_frac(seg, BODY_FRAC)`` per resource-hour, then the
  per-(resource, LOCAL day) median — the Theil-Sen classifier's daily table;
* band mults = ``_band_price(seg, lo, hi)`` per resource-hour for EVERY class
  geometry (``class_band_windows``) and band, turned into the derive's
  multiplier with the same gas flow-day staircase and CARB carbon netting,
  then the **resource-year median over hours** — the derive's estimation
  unit, per candidate class, so the parent picks the class after it has
  classified (masked ids carry no class at reduce time).

What the parent still does: pool years, classify (Theil-Sen on the daily
body table), locate ``st_cut``, weight by the resource's first classified
year capacity, cap-weighted class medians, gates. Nothing here decides a
class or a band.

What this deliberately does NOT reproduce: the net-load-binned peak LADDER
(``caiso_offer_surface_condbinned.json``), which no gate in the caiso-281
charter reads. State it rather than hide it.

Memory: the per-hour frame is ~50 k rows/day x 13 float32 columns, ~1 GB for
an RTM year; run ``scripts/prepare_solve_container.py`` first (swap), as the
shard prompt says.

Usage:
    python scripts/data/reduce_caiso_bid_year.py --zip-dir data/raw/caiso-public-bids/zips-rtm \\
        --market RTM --year 2023 --out results/rtm-intake/caiso283/2023_RTM
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from scripts.data import derive_caiso_offer_surface as D  # noqa: E402
from scripts.lib.dam_public_bids.caiso import parse_day  # noqa: E402

BANDS = ("committed", "econ_low", "econ_high", "peak")


def _curve_rows(path: Path) -> pd.DataFrame:
    """GENERATOR / EN / segment rows of one daily zip, the derive's ``_load_bids`` frame."""
    df = parse_day(path)
    df = df[
        (df.resource_type == "GENERATOR")
        & (df["product"] == "EN")
        & (df.row_kind == "segment")
    ]
    out = df[
        [
            "interval_start_utc",
            "resource_seq",
            "segment_mw",
            "segment_price_usd_per_mwh",
        ]
    ]
    return out.rename(columns={"segment_price_usd_per_mwh": "price"}).reset_index(
        drop=True
    )


def exact_quantile_from_counts(
    values: np.ndarray, counts: np.ndarray, q: float
) -> float:
    """``pandas.Series.quantile(q)`` (linear) of the multiset {values x counts}, without expanding it."""
    order = np.argsort(values, kind="mergesort")
    v, c = values[order], counts[order]
    n = int(c.sum())
    if n == 0:
        return float("nan")
    pos = (n - 1) * q
    lo = int(np.floor(pos))
    hi = min(lo + 1, n - 1)
    cum = np.cumsum(c)  # cum[i] = number of elements with index < i+1
    v_lo = v[np.searchsorted(cum, lo + 1, side="left")]
    v_hi = v[np.searchsorted(cum, hi + 1, side="left")]
    return float(v_lo + (v_hi - v_lo) * (pos - lo))


def pass1_capacity(zips: list[Path], cache: Path) -> tuple[pd.Series, pd.Series, dict]:
    """Per-resource exact p98 capacity and min MW over the year; cache the curve rows per day."""
    cache.mkdir(parents=True, exist_ok=True)
    counts: list[pd.Series] = []
    mins: list[pd.Series] = []
    n_rows = 0
    for i, z in enumerate(zips, 1):
        seg = _curve_rows(z)
        n_rows += len(seg)
        seg.to_parquet(cache / f"{z.name[:8]}.parquet", index=False)
        counts.append(seg.groupby(["resource_seq", "segment_mw"]).size())
        mins.append(seg.groupby("resource_seq").segment_mw.min())
        if i % 20 == 0 or i == len(zips):
            print(f"  pass1 {i}/{len(zips)} {z.name}", flush=True)
    vc = pd.concat(counts).groupby(level=[0, 1]).sum()
    cap = {}
    for rid, g in vc.groupby(level=0):
        cap[rid] = exact_quantile_from_counts(
            g.index.get_level_values(1).to_numpy(float), g.to_numpy(float), 0.98
        )
    cap_s = pd.Series(cap, name="cap").rename_axis("resource_seq")
    min_s = pd.concat(mins).groupby(level=0).min().rename("min_mw")
    return cap_s, min_s, {"curve_rows": int(n_rows)}


def pass2_hourly(
    day_files: list[Path],
    cap: pd.Series,
    geom: dict,
    gas: pd.Series,
    carbon: float | None,
) -> pd.DataFrame:
    """Per resource-hour: body price and the 12 (class x band) multipliers, the derive's own way."""
    windows = {cls: D.class_band_windows(geom, cls) for cls in D.CLASSES}
    parts = []
    for i, f in enumerate(day_files, 1):
        seg = pd.read_parquet(f)
        seg = seg.join(cap, on="resource_seq")
        seg = seg[seg.cap >= D.MIN_CAP_MW]
        if seg.empty:
            continue
        seg = seg.sort_values(["resource_seq", "interval_start_utc", "segment_mw"])
        body = D._price_at_frac(seg, D.BODY_FRAC).rename("p_body")
        cols = {"p_body": body}
        for cls in D.CLASSES:
            base_hr, vom = geom[cls]["base_hr"], D.VOM_BY_CLASS[cls]
            for band, (lo, hi) in windows[cls].items():
                cols[f"bp_{cls}_{band}"] = D._band_price(seg, lo, hi)
        day = pd.DataFrame(cols).reset_index()
        local = (
            day.interval_start_utc.dt.tz_convert("US/Pacific")
            .dt.normalize()
            .dt.tz_localize(None)
        )
        day["day"] = local
        day["gas"] = local.map(gas)
        if carbon is not None:
            denom_base = day.gas + D.CO2_FACTOR * carbon
            for cls in D.CLASSES:
                base_hr, vom = geom[cls]["base_hr"], D.VOM_BY_CLASS[cls]
                for band in BANDS:
                    day[f"m_{cls}_{band}"] = (day[f"bp_{cls}_{band}"] - vom) / (
                        base_hr * denom_base
                    )
        parts.append(day.drop(columns=[c for c in day.columns if c.startswith("bp_")]))
        if i % 20 == 0 or i == len(day_files):
            print(f"  pass2 {i}/{len(day_files)} {f.name}", flush=True)
    return pd.concat(parts, ignore_index=True)


def reduce_year(zip_dir: Path, out: Path, market: str, year: int) -> dict:
    """Run both passes for one market-year and write the two parquets + meta."""
    out.mkdir(parents=True, exist_ok=True)
    zips = sorted(p for p in zip_dir.glob("*.zip") if p.name[:4] == str(year))
    if not zips:
        raise SystemExit(f"no {year} zips under {zip_dir}")
    have = {z.name[:8] for z in zips}
    want = {
        d.strftime("%Y%m%d") for d in pd.date_range(f"{year}-01-01", f"{year}-12-31")
    }
    missing = sorted(want - have)
    print(
        f"{market} {year}: {len(zips)} zips, {len(missing)} missing dates: {missing[:10]}",
        flush=True,
    )

    geom = D._fleet_geometry()
    gas = D._gas_staircase()
    try:
        carbon = D._carbon_price(year)
    except KeyError:
        carbon = None
        print(
            f"  no CARB price registered for {year}: band multipliers NOT computed",
            flush=True,
        )

    cache = out / "_curve_cache"
    cap, min_mw, p1 = pass1_capacity(zips, cache)
    hourly = pass2_hourly(sorted(cache.glob("*.parquet")), cap, geom, gas, carbon)
    for f in cache.glob("*.parquet"):
        f.unlink()
    cache.rmdir()

    body_daily = hourly.groupby(["resource_seq", "day"], as_index=False).agg(
        p_body=("p_body", "median"), n_hours=("p_body", "size")
    )
    agg = {"n_hours": ("p_body", "size"), "n_days": ("day", "nunique")}
    for c in hourly.columns:
        if c.startswith("m_"):
            agg[c] = (c, "median")
    ry = hourly.groupby("resource_seq").agg(**agg).reset_index()
    ry["year"] = np.int16(year)
    ry["cap_mw"] = ry.resource_seq.map(cap)
    ry["min_mw"] = ry.resource_seq.map(min_mw)

    ry.to_parquet(out / "resource_year.parquet", index=False)
    body_daily.to_parquet(out / "body_daily.parquet", index=False)
    meta = {
        "market": market,
        "year": year,
        "zip_dir": str(zip_dir),
        "n_zips": len(zips),
        "missing_dates": missing,
        "curve_rows": p1["curve_rows"],
        "n_resources_any": int(len(cap)),
        "n_resources_cap_ge_min": int((cap >= D.MIN_CAP_MW).sum()),
        "n_resource_hours": int(len(hourly)),
        "n_body_daily_rows": int(len(body_daily)),
        "carbon_usd_per_t": carbon,
        "derive_constants": {
            "body_frac": D.BODY_FRAC,
            "min_cap_mw": D.MIN_CAP_MW,
            "vom": D.VOM_BY_CLASS,
            "co2_factor": D.CO2_FACTOR,
            "econ_low_share": D.ECON_LOW_SHARE,
            "windows": {c: D.class_band_windows(geom, c) for c in D.CLASSES},
            "base_hr": {c: geom[c]["base_hr"] for c in D.CLASSES},
        },
        "gas_csv_sha256": hashlib.sha256(D.CITYGATE_DAILY.read_bytes()).hexdigest(),
        "git_sha": subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO
        ).stdout.strip(),
        "reduced_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "resource_year_sha256": hashlib.sha256(
            (out / "resource_year.parquet").read_bytes()
        ).hexdigest(),
        "body_daily_sha256": hashlib.sha256(
            (out / "body_daily.parquet").read_bytes()
        ).hexdigest(),
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2, default=float))
    print(json.dumps(meta, indent=2, default=float))
    return meta


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--zip-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--market", required=True, choices=["DAM", "RTM"])
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args(argv)
    reduce_year(args.zip_dir, args.out, args.market, args.year)
    return 0


if __name__ == "__main__":
    sys.exit(main())
