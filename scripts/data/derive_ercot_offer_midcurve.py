"""Derive the MEASURED ERCOT MID-CURVE offer surface (ERCOT-69 / G-22 lane).

The ERCOT-68 hand-off adjudicated the broad moderate-tightness under-pricing
(May-2024 DA shoulders, Nov-2024, winter mornings) as the DA-expressible
offer-formation family: reality printed those prices at RTORPA ~ 0 by clearing
higher up the day-ahead energy-offer stack, where the model stays at its gas
CC econ tranches. The existing ``ercot_offer_surface_conditional`` reprices
only the gas PEAK rungs (top ~263 h/yr, self-gated to true tightness); the
moderate-reserve body of the curve is unpriced. This derive measures the
day-ahead offer body per within-unit capacity share and net-load bin so the
P1 mechanism (``ScenarioConfig.ercot_offer_surface_midcurve_conditional``,
``fleet.build_ercot_offer_midcurve_conditional_markup``) can floor the model's
econ tranches at the measured offer level — the ERCOT analogue of the PJM
mid-curve surface (``scripts/data/derive_pjm_offer_midcurve.py``).

Method (measured, NOT fit to any residual — CLAUDE.md rules 1/13/21/23)
----------------------------------------------------------------------
1. Population: gas resources committed in the day-ahead market (Resource
   Status containing ``ON``) with HSL > 0, mapped by Resource Type to the
   model gas classes (CCGT90/CCLE90 -> CC; SCGT90/SCLE90 -> CT_PEAKER;
   GSREH/GSNONR/GSSUP -> ST_GAS). Source: the ERCOT 60-Day DAM Disclosure
   Gen Resource Data (``60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*``),
   the same corpus the peak-rung surface and the AS-MCPC series are built
   from.
2. WITHIN-UNIT capacity shares, not cross-fleet quantiles: per resource-hour
   the 10-point offer curve (``QSE submitted Curve-MW/Price 1..10``) is sampled
   at fixed within-unit HSL shares. A share is scale-free, so the model-fleet
   vs measured-fleet capacity mismatch cannot distort the mapping — the model's
   own plant tranches carry their within-plant share and read the surface at
   the same point of the curve (identical construction to the PJM mid-curve).
3. Normalisation: implied heat-rate ``mult = offer_price / gas_day`` vs the
   model's ERCOT delivered-gas day series (Henry Hub daily + ERCOT basis,
   identical to the offer-curve build). Multipliers only are stored, never
   prices.
4. Tightness driver: within-year net-load percentile, proxied per (delivery
   date, hour ending) by the sum of awarded thermal quantity — the identical
   driver the existing ERCOT offer surface / derive use (forward-native: the
   load+VRE forecast regenerates the ranking). Finer edges than the peak-rung
   surface (0.50/0.70/0.85/0.95) so the MODERATE regime gets its own bin.
5. Ladder value: capacity-weighted MEAN mult per (class, year, bin, share).
   The mean (not the median the PJM derive uses) is the price-relevant
   statistic here: the clearing price at a given load is set by the marginal
   offer, which the ERCOT offer distribution places in its upper tail (most
   committed gas capacity is offered near SRMC, a minority carries the wall),
   so the capacity-weighted mean tracks the marginal price-setter where the
   median does not. It is a pure measured statistic — no quantile or level is
   fitted.
6. Output: ``data/raw/_validation-source/ercot_offer_midcurve_condbinned.json``
   (+ summary CSV): multipliers per (class, delivery year, net-load bin,
   share), plus a pooled cap-weighted version for forward years.

Pre-committed honesty gate (rule 23): frozen against residuals; re-derive only
when the source disclosure updates. If the A/B degrades or does not move the
backcast, the surface does NOT change and the probe registers its verdict
(rule 15).

Usage:
    python scripts/data/derive_ercot_offer_midcurve.py [--years 2023 2024 2025]
        [--edges 0.50 0.70 0.85 0.95]
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL  # noqa: E402
from market_sim.data.fuel import HENRY_HUB_DAILY_PATH  # noqa: E402

OUT_JSON = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "ercot_offer_midcurve_condbinned.json"
)
OUT_CSV = (
    REPO / "data" / "raw" / "_validation-source" / "ercot_offer_midcurve_summary.csv"
)

_GENRES_GLOB = "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_{year}_*.parquet"

#: Resource Type -> model gas class. CHP is a plant attribute, not a Resource
#: Type, so the measured CC offers serve both CC_REGULAR and CC_CHP model rows
#: (the builder maps both to "CC").
_RESTYPE_CLASS: dict[str, str] = {
    "CCGT90": "CC",
    "CCLE90": "CC",
    "SCGT90": "CT_PEAKER",
    "SCLE90": "CT_PEAKER",
    "GSREH": "ST_GAS",
    "GSNONR": "ST_GAS",
    "GSSUP": "ST_GAS",
}

_MW_COLS = [f"QSE submitted Curve-MW{i}" for i in range(1, 11)]
_PR_COLS = [f"QSE submitted Curve-Price{i}" for i in range(1, 11)]

#: Within-unit HSL shares the curve is sampled at (share-grid midpoints) plus
#: the top-of-curve belt (0.975 / 0.995 — the last-few-% wall the decile grid
#: misses). Same sampling grid as the PJM mid-curve derive.
SHARES = np.concatenate([np.arange(0.10, 1.0, 0.10), [0.975, 0.995]])


def _gas_daily(years: list[int]) -> pd.Series:
    """ERCOT delivered-gas day series (HH daily + ERCOT basis), by calendar date."""
    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    return s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["ERCOT"])


def _netload_pct(files: list[Path], years: list[int]) -> pd.DataFrame:
    """Within-year net-load percentile per (day, he) from awarded thermal qty."""
    parts = []
    for p in files:
        df = pd.read_parquet(
            p, columns=["Delivery Date", "Hour Ending", "Awarded Quantity"]
        )
        df["aq"] = pd.to_numeric(df["Awarded Quantity"], errors="coerce")
        df["day"] = pd.to_datetime(df["Delivery Date"])
        parts.append(df.groupby(["day", "Hour Ending"])["aq"].sum().reset_index())
    g = pd.concat(parts, ignore_index=True)
    g = g.groupby(["day", "Hour Ending"], as_index=False)["aq"].sum()
    g = g[g["day"].dt.year.isin(years)].copy()
    g["q"] = g.groupby(g["day"].dt.year)["aq"].rank(pct=True)
    return g[["day", "Hour Ending", "q"]]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--edges", nargs="*", type=float, default=[0.50, 0.70, 0.85, 0.95])
    args = ap.parse_args(argv)

    files: list[Path] = []
    for y in args.years:
        files += [
            Path(f)
            for f in sorted(
                glob.glob(
                    str(REPO / "data" / "raw" / "ercot" / _GENRES_GLOB.format(year=y))
                )
            )
        ]
    if not files:
        raise FileNotFoundError("no 60-Day DAM Gen Resource Data files for the years")

    edges = tuple(args.edges)
    n_bins = len(edges) + 1
    classes = ["CC", "CT_PEAKER", "ST_GAS"]
    cls_pos = {c: i for i, c in enumerate(classes)}
    year_pos = {y: i for i, y in enumerate(args.years)}

    print("pass 1: net-load percentile ...", flush=True)
    nl = _netload_pct(files, args.years)
    gas = _gas_daily(args.years)

    # Capacity-weighted running sums for the MEAN: sum(w*mult) and sum(w) per
    # (class, year, bin, share).
    shp = (len(classes), len(args.years), n_bins, len(SHARES))
    wsum = np.zeros(shp, dtype=float)
    wxsum = np.zeros(shp, dtype=float)

    print("pass 2: mid-curve sampling ...", flush=True)
    for p in files:
        df = pd.read_parquet(
            p,
            columns=[
                "Delivery Date",
                "Hour Ending",
                "Resource Type",
                "Resource Status",
                "HSL",
            ]
            + _MW_COLS
            + _PR_COLS,
        )
        df["cls"] = df["Resource Type"].map(_RESTYPE_CLASS)
        df = df[df["cls"].notna()]
        df = df[df["Resource Status"].astype(str).str.contains("ON")]
        if df.empty:
            continue
        for c in _MW_COLS + _PR_COLS + ["HSL"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df[df["HSL"] > 0.0]
        if df.empty:
            continue
        df["day"] = pd.to_datetime(df["Delivery Date"])
        df = df[df["day"].dt.year.isin(args.years)]
        if df.empty:
            continue
        key = df[["day", "Hour Ending"]].merge(
            nl, on=["day", "Hour Ending"], how="left"
        )
        q = key["q"].to_numpy(float)
        gas_r = gas.reindex(pd.DatetimeIndex(df["day"].dt.normalize())).to_numpy(float)
        hbin = np.searchsorted(np.asarray(edges), q, side="right")
        yr = df["day"].dt.year.to_numpy()
        mw = df[_MW_COLS].to_numpy(float)
        pr = df[_PR_COLS].to_numpy(float)
        hsl = df["HSL"].to_numpy(float)
        cls_idx = df["cls"].map(cls_pos).to_numpy()
        ok = np.isfinite(q) & np.isfinite(gas_r) & (gas_r > 0.0) & (hsl > 0.0)
        rows = np.where(ok)[0]
        if rows.size == 0:
            continue
        mw_r = np.where(np.isfinite(mw[rows]), mw[rows], np.inf)
        pr_r = pr[rows]
        hsl_r = hsl[rows]
        gas_rr = gas_r[rows]
        cls_r = cls_idx[rows]
        yr_r = np.array([year_pos.get(int(v), -1) for v in yr[rows]])
        bin_r = hbin[rows]
        keep = yr_r >= 0
        for si, s in enumerate(SHARES):
            tgt = s * hsl_r[:, None]
            pos = np.clip((mw_r < tgt).sum(axis=1), 0, 9)
            price = pr_r[np.arange(len(rows)), pos]
            mult = price / gas_rr
            m = keep & np.isfinite(mult)
            # capacity weight = HSL (the resource's committed capability).
            np.add.at(
                wsum, (cls_r[m], yr_r[m], bin_r[m], np.full(m.sum(), si)), hsl_r[m]
            )
            np.add.at(
                wxsum,
                (cls_r[m], yr_r[m], bin_r[m], np.full(m.sum(), si)),
                hsl_r[m] * mult[m],
            )
        print(f"  [pass2] {p.name}: {rows.size} rows", flush=True)

    def _mean(c: int, y: int, b: int, si: int) -> float:
        w = wsum[c, y, b, si]
        return float(wxsum[c, y, b, si] / w) if w > 0.0 else float("nan")

    out: dict = {}
    summary = []
    for c, cname in enumerate(classes):
        per_year: dict = {}
        for y, yr in enumerate(args.years):
            ladders = []
            for b in range(n_bins):
                lad = [
                    [round(float(s), 3), round(_mean(c, y, b, si), 3)]
                    for si, s in enumerate(SHARES)
                ]
                ladders.append(lad)
                summary.append(
                    {
                        "class": cname,
                        "year": yr,
                        "bin": b,
                        "mw_weight": round(float(wsum[c, y, b].sum()), 0),
                        **{
                            f"s{int(sh * 100):02d}": lad[si][1]
                            for si, sh in enumerate(SHARES)
                        },
                    }
                )
            per_year[str(yr)] = ladders
        pooled = []
        for b in range(n_bins):
            row = []
            for si, s in enumerate(SHARES):
                w = wsum[c, :, b, si].sum()
                wx = wxsum[c, :, b, si].sum()
                row.append(
                    [
                        round(float(s), 3),
                        round(float(wx / w) if w > 0 else float("nan"), 3),
                    ]
                )
            pooled.append(row)
        out[cname] = {"years": per_year, "pooled": pooled}

    out_doc = {
        "_provenance": {
            "source": (
                "ERCOT 60-Day DAM Disclosure Gen Resource Data "
                f"(data/raw/ercot/), delivery years {args.years}"
            ),
            "method": (
                "within-unit HSL-share sampling of the 10-point DA energy "
                f"offer curve (shares {[round(float(x), 3) for x in SHARES]}), "
                "implied-HR mult = offer_price / delivered-gas day (HH daily + "
                "ERCOT basis), capacity(HSL)-weighted MEAN per (model gas class, "
                "delivery year, net-load bin, share). Population: DA-committed "
                "(Resource Status ~ ON) CC/CT_PEAKER/ST_GAS resources with "
                "HSL>0. Offers only; clearing prices stay validation-only "
                "(rule 13)."
            ),
            "driver": (
                "system net-load percentile within year (DA awarded thermal "
                "quantity), forward-native (load+VRE forecast regenerates it)"
            ),
            "netload_pct_edges": list(edges),
            "shares": [round(float(x), 3) for x in SHARES],
            "n_files_parsed": len(files),
            "iso": "ERCOT",
        },
        **out,
    }
    OUT_JSON.write_text(json.dumps(out_doc, indent=1))
    sdf = pd.DataFrame(summary)
    sdf.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_CSV}")
    print(sdf.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
