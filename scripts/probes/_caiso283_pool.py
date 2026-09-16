"""caiso-283: pool the exact per-market-year reductions, classify on DAM, carry to RTM, apply the gates.

ZERO LP. Reads only ``results/rtm-intake/caiso283/<year>_<MKT>/{resource_year,body_daily}.parquet``
(written by ``scripts/data/reduce_caiso_bid_year.py`` in the fetch shards) plus the repo's gas
staircase and fleet geometry, all through the derive's own functions and constants.

Charter: ``docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md`` §4 (G-REPRO,
G-OVERLAP, verdict thresholds). Method fixed before any number:
``docs/PRECOMMIT-caiso283-rtm-exact-rederive-2026-09-16.md`` §3.

Usage:
    .venv/bin/python scripts/probes/_caiso283_pool.py [--hr-cut 8.5] [--out results.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import theilslopes

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from scripts.data import derive_caiso_offer_surface as D  # noqa: E402

INTAKE = REPO / "results/rtm-intake/caiso283"
COMMITTED = REPO / "data/raw/_validation-source/caiso_offer_curve_measured.json"
BANDS = ("committed", "econ_low", "econ_high", "peak")
CLASSIFY_YEARS = (2023, 2024, 2025)  # the committed artifact's own span
VERDICT_YEARS = (2022, 2023, 2024, 2025)
# Charter thresholds, verbatim — never moved here.
REPRO_TOL_BASE, REPRO_TOL_BAND = 0.02, 0.01
OVERLAP_MIN = 0.60
VERDICT_DELTA = 0.05


def load_market(mkt: str, years) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Concatenate a market's resource_year + body_daily over the years present."""
    ry, bd, meta = [], [], {}
    for y in years:
        d = INTAKE / f"{y}_{mkt}"
        if not (d / "resource_year.parquet").exists():
            continue
        r = pd.read_parquet(d / "resource_year.parquet")
        b = pd.read_parquet(d / "body_daily.parquet")
        b["year"] = np.int16(y)
        ry.append(r)
        bd.append(b)
        meta[str(y)] = json.loads((d / "meta.json").read_text())
    if not ry:
        raise SystemExit(f"no {mkt} reductions under {INTAKE}")
    ry = pd.concat(ry, ignore_index=True)
    bd = pd.concat(bd, ignore_index=True)
    bd["day"] = pd.to_datetime(bd["day"])
    return ry, bd, meta


def classify(ry: pd.DataFrame, bd: pd.DataFrame, gas: pd.Series, hr_cut: float, years):
    """The derive's ``_classify`` on the reduced tables: Theil-Sen body price on flow-day gas."""
    daily = bd[bd.year.isin(years)].copy()
    daily["gas"] = daily.day.map(gas)
    daily = daily.dropna(subset=["gas"])
    r_years = ry[ry.year.isin(years)].sort_values(["resource_seq", "year"])
    cap_first = r_years.groupby("resource_seq").cap_mw.first()
    min_mw = r_years.groupby("resource_seq").min_mw.min()
    rows = []
    for rid, g in daily.groupby("resource_seq"):
        n = len(g)
        if n < D.GAS_MIN_DAYS or g.gas.std() < 0.5:
            continue
        x, y = g.gas.to_numpy(float), g.p_body.to_numpy(float)
        slope, _, _, _ = theilslopes(y, x)
        rows.append(
            {"resource_seq": rid, "slope": float(slope), "r": float(np.corrcoef(x, y)[0, 1]), "n_days": n}
        )
    res = pd.DataFrame(rows).set_index("resource_seq")
    res["cap"] = cap_first
    res["min_mw"] = min_mw
    res["is_gas"] = res.slope.between(*D.GAS_SLOPE_RANGE) & (res.r >= D.GAS_MIN_R) & (res.min_mw >= -1.0)
    res["cls"] = D._assign_classes(res, hr_cut, None)
    st_cut = D.locate_st_cut(res, hr_cut)
    if st_cut is not None:
        res["cls"] = D._assign_classes(res, hr_cut, st_cut)
    return res, st_cut


def class_bands(ry: pd.DataFrame, res: pd.DataFrame, cls: str, years, seqs=None) -> dict:
    """Cap-weighted median (weight = first classified year's cap) of the resource-year band mults."""
    bucket = res[res.is_gas & (res.cls == cls)]
    if seqs is not None:
        bucket = bucket[bucket.index.isin(seqs)]
    rows = ry[ry.resource_seq.isin(bucket.index) & ry.year.isin(years)].copy()
    rows["w"] = rows.resource_seq.map(bucket.cap)
    out = {"n_resources": int(rows.resource_seq.nunique()), "n_resource_years": int(len(rows)), "bands": {}, "per_year": {}}
    for b in BANDS:
        col = f"m_{cls}_{b}"
        v = rows[[col, "w", "year"]].dropna()
        out["bands"][b] = round(D._wquantile(v[col].to_numpy(float), v.w.to_numpy(float), 0.5), 3)
        out["per_year"][b] = {
            str(y): round(D._wquantile(v[v.year == y][col].to_numpy(float), v[v.year == y].w.to_numpy(float), 0.5), 3)
            for y in years
            if (v.year == y).any()
        }
    return out


def g1(res: pd.DataFrame, geom: dict) -> dict:
    """The derive's G1 capacity reconciliation per class."""
    out = {}
    for cls in D.CLASSES:
        b = res[res.is_gas & (res.cls == cls)]
        ratio = float(b.cap.sum()) / geom[cls]["fleet_mw"]
        lo, hi = D.G1_BOUNDS[cls]
        out[cls] = {
            "n": int(len(b)),
            "bucket_mw": round(float(b.cap.sum()), 0),
            "fleet_mw": round(geom[cls]["fleet_mw"], 0),
            "ratio": round(ratio, 3),
            "bounds": [lo, hi],
            "pass": bool(lo <= ratio <= hi),
            "slope_wmedian": round(D._wquantile(b.slope.to_numpy(float), b.cap.to_numpy(float), 0.5), 3) if len(b) else None,
        }
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hr-cut", type=float, default=8.5)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--verdict-years", nargs="*", type=int, default=list(VERDICT_YEARS))
    args = ap.parse_args(argv)

    geom = D._fleet_geometry()
    gas = D._gas_staircase()
    committed = json.loads(COMMITTED.read_text())
    dam_ry, dam_bd, dam_meta = load_market("DAM", VERDICT_YEARS)
    rtm_ry, rtm_bd, rtm_meta = load_market("RTM", VERDICT_YEARS)
    result = {"hr_cut": args.hr_cut, "dam_years": sorted(dam_meta), "rtm_years": sorted(rtm_meta),
              "dam_missing_dates": {y: m["missing_dates"] for y, m in dam_meta.items()},
              "rtm_missing_dates": {y: m["missing_dates"] for y, m in rtm_meta.items()}}

    # 1. classify on DAM, artifact span
    res, st_cut = classify(dam_ry, dam_bd, gas, args.hr_cut, CLASSIFY_YEARS)
    result["dam_classifier"] = {"n_classified": int(len(res)), "n_gas": int(res.is_gas.sum()), "st_cut": st_cut, "G1": g1(res, geom)}
    print("DAM classifier:", json.dumps(result["dam_classifier"]))

    # 2. G-REPRO
    dam_bands = {cls: class_bands(dam_ry, res, cls, CLASSIFY_YEARS) for cls in D.CLASSES}
    cc = committed["CC_REGULAR"]
    repro = {"base_hr": {"committed": cc["base_hr"], "pooled": round(geom["CC_REGULAR"]["base_hr"], 3),
                          "pass": abs(geom["CC_REGULAR"]["base_hr"] - cc["base_hr"]) <= REPRO_TOL_BASE,
                          "note": "fleet-geometry constant in the derive; reproduces by construction"}}
    ok = repro["base_hr"]["pass"]
    for b in ("econ_low", "econ_high", "peak"):
        p = dam_bands["CC_REGULAR"]["bands"][b]
        row = {"committed": cc["bands"][b], "pooled": p, "dev": round(p - cc["bands"][b], 3), "tol": REPRO_TOL_BAND, "pass": bool(abs(p - cc["bands"][b]) <= REPRO_TOL_BAND)}
        repro[b] = row
        ok = ok and row["pass"]
    ct = committed["CT_PEAKER"]
    repro["CT_PEAKER_reported"] = {b: {"committed": ct["bands"][b], "pooled": dam_bands["CT_PEAKER"]["bands"][b], "dev": round(dam_bands["CT_PEAKER"]["bands"][b] - ct["bands"][b], 3)} for b in ("econ_low", "econ_high", "peak")}
    repro["committed_unarmed"] = {"CC": (cc["unarmed"]["committed"], dam_bands["CC_REGULAR"]["bands"]["committed"]), "CT": (ct["unarmed"]["committed"], dam_bands["CT_PEAKER"]["bands"]["committed"])}
    repro["pass"] = bool(ok)
    result["G_REPRO"] = repro
    result["dam_bands_artifact_span"] = dam_bands
    print("G-REPRO:", json.dumps(repro, indent=1))

    # 3. carry to RTM by seq; G-OVERLAP
    gas_cc_ct = res[res.is_gas & res.cls.isin(["CC_REGULAR", "CT_PEAKER"])]
    rtm_seqs = set(rtm_ry.resource_seq.unique())
    covered = gas_cc_ct[gas_cc_ct.index.isin(rtm_seqs)]
    overlap = {
        "dam_classified_cc_ct_mw": round(float(gas_cc_ct.cap.sum()), 0),
        "with_rtm_rows_mw": round(float(covered.cap.sum()), 0),
        "coverage": round(float(covered.cap.sum() / gas_cc_ct.cap.sum()), 3),
        "n_dam_classified": int(len(gas_cc_ct)),
        "n_with_rtm_rows": int(len(covered)),
        "min": OVERLAP_MIN,
    }
    overlap["pass"] = bool(overlap["coverage"] >= OVERLAP_MIN)
    result["G_OVERLAP"] = overlap
    print("G-OVERLAP:", json.dumps(overlap))

    # 4. verdict pool: same seqs, both markets
    vy = tuple(args.verdict_years)
    pooled = {}
    for cls in ("CC_REGULAR", "CT_PEAKER"):
        d = class_bands(dam_ry, res, cls, vy)
        r = class_bands(rtm_ry, res, cls, vy)
        pooled[cls] = {"DAM": d, "RTM": r, "delta_rtm_minus_dam": {b: round(r["bands"][b] - d["bands"][b], 3) for b in BANDS}}
        # same-seq strictness: RTM rows restricted to seqs that have DAM rows in the pool and vice versa
        common = set(dam_ry[dam_ry.year.isin(vy)].resource_seq) & set(rtm_ry[rtm_ry.year.isin(vy)].resource_seq)
        d2 = class_bands(dam_ry, res, cls, vy, seqs=common)
        r2 = class_bands(rtm_ry, res, cls, vy, seqs=common)
        pooled[cls]["same_seqs_only"] = {"n": d2["n_resources"], "DAM": d2["bands"], "RTM": r2["bands"], "delta": {b: round(r2["bands"][b] - d2["bands"][b], 3) for b in BANDS}}
        pooled[cls]["per_year_delta"] = {
            str(y): {b: round(r["per_year"][b][str(y)] - d["per_year"][b][str(y)], 3) for b in BANDS if str(y) in r["per_year"][b] and str(y) in d["per_year"][b]}
            for y in vy
        }
    result["verdict_pool"] = pooled
    ccd = pooled["CC_REGULAR"]["delta_rtm_minus_dam"]
    if not repro["pass"]:
        verdict = "ABANDONED (G-REPRO failed)"
    elif not overlap["pass"]:
        verdict = "INCONCLUSIVE (G-OVERLAP failed)"
    elif ccd["econ_low"] <= -VERDICT_DELTA and ccd["econ_high"] <= -VERDICT_DELTA:
        verdict = "RTM-BELOW"
    elif abs(ccd["econ_low"]) < VERDICT_DELTA and abs(ccd["econ_high"]) < VERDICT_DELTA:
        verdict = "RTM-FLAT"
    else:
        verdict = "INDETERMINATE"
    result["verdict"] = verdict
    print("Δ CC RTM−DAM:", json.dumps(ccd), "| CT:", json.dumps(pooled["CT_PEAKER"]["delta_rtm_minus_dam"]))
    print("VERDICT:", verdict)

    # 5. diagnostics: independent RTM classification (the caiso-282 G-POP), gates nothing
    rres, rst = classify(rtm_ry, rtm_bd, gas, args.hr_cut, CLASSIFY_YEARS)
    dam_seqs_any = set(dam_ry.resource_seq.unique())
    rg = rres[rres.is_gas]
    never = ~rg.index.isin(dam_seqs_any)
    result["diag_rtm_independent"] = {
        "n_gas": int(len(rg)),
        "st_cut": rst,
        "G1": g1(rres, geom),
        "never_in_dam_share_of_bucket_mw": {
            cls: round(float(rg.cap[never & (rg.cls == cls)].sum() / max(1e-9, rg.cap[rg.cls == cls].sum())), 3)
            for cls in ("CC_REGULAR", "CT_PEAKER")
        },
        "jaccard_vs_dam": {
            cls: round(len(set(rg[rg.cls == cls].index) & set(res[res.is_gas & (res.cls == cls)].index)) / max(1, len(set(rg[rg.cls == cls].index) | set(res[res.is_gas & (res.cls == cls)].index))), 3)
            for cls in ("CC_REGULAR", "CT_PEAKER")
        },
    }
    print("diag RTM independent:", json.dumps(result["diag_rtm_independent"]))

    if args.out:
        args.out.write_text(json.dumps(result, indent=1, default=float) + "\n")
        print("wrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
