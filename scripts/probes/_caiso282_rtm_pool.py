"""caiso-282: pool the caiso-281 RTM/DAM bid-ladder intake and apply the charter's gates.

ZERO LP. Reads only the committed per-quarter aggregates under
``results/rtm-intake/caiso281/<q>/{agg,agg_dam}`` and the repo's own gas /
fleet-geometry / carbon inputs. Every parameter and estimator is IMPORTED from
``scripts/data/derive_caiso_offer_surface.py`` so the classifier and band
construction are the derive's, not a re-typed copy.

Charter: ``docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md`` §4,
``docs/ADDENDUM-caiso281-rtm-classification-is-independent-2026-09-13.md`` §3.
Method fixed before any number: ``docs/PRECOMMIT-caiso282-rtm-pool-and-gates-2026-09-16.md``.

Usage:
    .venv/bin/python scripts/probes/_caiso282_rtm_pool.py [--hr-cut 8.5] [--out results.json]
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

INTAKE = REPO / "results/rtm-intake/caiso281"
COMMITTED = REPO / "data/raw/_validation-source/caiso_offer_curve_measured.json"
GRID = np.round(np.arange(0.05, 1.0001, 0.05), 4)
GRID_COLS = [f"p{int(round(f * 100)):03d}" for f in GRID]

#: Charter pools (PRECOMMIT caiso-282 §2.6).
REPRO_START, REPRO_END = pd.Timestamp("2023-01-01"), pd.Timestamp("2025-09-30")
VERDICT_START, VERDICT_END = pd.Timestamp("2022-01-01"), pd.Timestamp("2025-09-30")
#: Charter thresholds (verbatim; never moved here).
REPRO_TOL_BASE, REPRO_TOL_BAND = 0.02, 0.01
VERDICT_DELTA = 0.05


def load_market(market_dir: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Concatenate every quarter's hourly + ladder parquet for one market run."""
    hs, ls = [], []
    for q in sorted(INTAKE.iterdir()):
        d = q / market_dir
        if not (d / "ladder.parquet").exists():
            continue
        h = pd.read_parquet(d / "hourly.parquet")
        l = pd.read_parquet(d / "ladder.parquet")
        h["quarter"] = l["quarter"] = q.name
        hs.append(h)
        ls.append(l)
    hourly = pd.concat(hs, ignore_index=True)
    ladder = pd.concat(ls, ignore_index=True)
    for df in (hourly, ladder):
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year.astype("int16")
    return hourly, ladder


def rescale_to_year(ladder: pd.DataFrame, cap_y: pd.Series) -> pd.DataFrame:
    """Attach year capacity; return ladder rows with cap_year, cap_quarter, ratio."""
    out = ladder.join(cap_y.rename("cap_year"), on=["RESOURCEBID_SEQ", "year"])
    out = out.dropna(subset=["cap_year"])
    out = out[out.cap_year >= D.MIN_CAP_MW]
    out["ratio_q_over_y"] = out.quarter_capacity_mw / out.cap_year
    return out


def price_at_year_frac(rows: pd.DataFrame, f_y: float) -> np.ndarray:
    """Price at fraction f_y of YEAR capacity, read off the quarter grid by linear interp."""
    P = rows[GRID_COLS].to_numpy(float)
    f_q = np.clip(f_y * rows.ratio_q_over_y.to_numpy(float) ** -1, GRID[0], GRID[-1])
    # f_q = f_y * cap_year / cap_quarter ; ratio_q_over_y = cap_q / cap_y
    idx = np.searchsorted(GRID, f_q, side="left")
    idx = np.clip(idx, 1, len(GRID) - 1)
    g0, g1 = GRID[idx - 1], GRID[idx]
    w = (f_q - g0) / (g1 - g0)
    r = np.arange(len(rows))
    return P[r, idx - 1] * (1 - w) + P[r, idx] * w


def band_price_grid(rows: pd.DataFrame, lo: float, hi: float) -> np.ndarray:
    """Integral of the grid step function over [lo, hi) of YEAR capacity, / width.

    Grid point f_k (quarter-capacity fraction) carries the price applying on
    (f_{k-1}, f_k], f_0 = 0. Window edges are converted to quarter fractions
    through the measured ratio and the overlap of each grid cell is the weight.
    The grid's exact analogue of the derive's ``_band_price``.
    """
    P = rows[GRID_COLS].to_numpy(float)
    scale = 1.0 / rows.ratio_q_over_y.to_numpy(float)  # cap_year / cap_quarter
    lo_q, hi_q = lo * scale, hi * scale
    edges_lo = np.r_[0.0, GRID[:-1]]
    edges_hi = GRID.copy()
    a = np.maximum(edges_lo[None, :], lo_q[:, None])
    b = np.minimum(edges_hi[None, :], hi_q[:, None])
    w = np.clip(b - a, 0.0, None)
    # Past the last grid point the top price holds flat (the aggregator holds the
    # last breakpoint's price past the end of the curve).
    tail = np.clip(hi_q - np.maximum(lo_q, GRID[-1]), 0.0, None)
    num = (w * P).sum(axis=1) + tail * P[:, -1]
    den = w.sum(axis=1) + tail
    return np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)


def classify(
    ladder: pd.DataFrame,
    hourly: pd.DataFrame,
    gas: pd.Series,
    hr_cut: float,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
):
    """The derive's classifier over the pooled span: Theil-Sen body price on flow-day gas.

    ``start``/``end`` restrict the classifier's days (diagnostic A: the committed
    artifact classified on its own 2023-25 span, so G-REPRO is read both ways).
    """
    if start is not None:
        ladder = ladder[(ladder.date >= start) & (ladder.date <= end)]
    body = ladder[["RESOURCEBID_SEQ", "date", "year", "cap_year"]].copy()
    body["p_body"] = price_at_year_frac(ladder, D.BODY_FRAC)
    body["gas"] = body.date.map(gas)
    body = body.dropna(subset=["gas", "p_body"])
    # The derive's cap for classification/weighting: the resource's FIRST classified year.
    first_cap = (
        body.sort_values(["RESOURCEBID_SEQ", "date"]).groupby("RESOURCEBID_SEQ").cap_year.first()
    )
    min_mw = hourly.groupby("RESOURCEBID_SEQ").hour_min_mw.min()
    rows = []
    for rid, g in body.groupby("RESOURCEBID_SEQ"):
        n = len(g)
        if n < D.GAS_MIN_DAYS or g.gas.std() < 0.5:
            continue
        x, y = g.gas.to_numpy(float), g.p_body.to_numpy(float)
        slope, _, _, _ = theilslopes(y, x)
        r = float(np.corrcoef(x, y)[0, 1])
        rows.append({"resource_seq": rid, "slope": float(slope), "r": r, "n_days": n})
    res = pd.DataFrame(rows).set_index("resource_seq")
    res["cap"] = first_cap
    res["min_mw"] = min_mw
    res["is_gas"] = (
        res.slope.between(*D.GAS_SLOPE_RANGE) & (res.r >= D.GAS_MIN_R) & (res.min_mw >= -1.0)
    )
    res["cls"] = D._assign_classes(res, hr_cut, None)
    st_cut = D.locate_st_cut(res, hr_cut)
    if st_cut is not None:
        res["cls"] = D._assign_classes(res, hr_cut, st_cut)
    return res, st_cut, body


def band_windows(geom: dict, cls: str) -> dict[str, tuple[float, float]]:
    """The derive's band windows from the model's class geometry."""
    c = geom[cls]["pct_committed"] / 100.0
    p = geom[cls]["pct_peaking"] / 100.0
    els = D.ECON_LOW_SHARE[cls]
    e_lo, e_hi = c, 1.0 - p
    e_mid = e_lo + (e_hi - e_lo) * els
    return {
        "committed": (0.0, c),
        "econ_low": (e_lo, e_mid),
        "econ_high": (e_mid, e_hi),
        "peak": (e_hi, 1.0),
    }


def static_bands(
    ladder: pd.DataFrame,
    res: pd.DataFrame,
    gas: pd.Series,
    geom: dict,
    start: pd.Timestamp,
    end: pd.Timestamp,
    classes=("CC_REGULAR", "CT_PEAKER", "ST_GAS"),
) -> dict:
    """Cap-weighted median band mults per class over [start, end], + per-year detail."""
    from market_sim.config.constants import STATE_CARBON_PRICE_BY_ISO

    carbon = STATE_CARBON_PRICE_BY_ISO["CAISO"]
    win = ladder[(ladder.date >= start) & (ladder.date <= end)].copy()
    win = win[win.year.isin(list(carbon))]
    win["gas"] = win.date.map(gas)
    win = win.dropna(subset=["gas"])
    out = {}
    for cls in classes:
        sub = res[res.is_gas & (res.cls == cls)]
        rows = win[win.RESOURCEBID_SEQ.isin(sub.index)]
        if rows.empty:
            out[cls] = None
            continue
        base_hr = geom[cls]["base_hr"]
        vom = D.VOM_BY_CLASS[cls]
        denom = base_hr * (rows.gas.to_numpy(float) + D.CO2_FACTOR * rows.year.map(carbon).to_numpy(float))
        cls_out = {"n_resources": int(len(sub)), "bucket_mw": float(sub.cap.sum()), "bands": {}, "per_year": {}}
        for band, (lo, hi) in band_windows(geom, cls).items():
            bp = band_price_grid(rows, lo, hi)
            m = (bp - vom) / denom
            ry = (
                pd.DataFrame({"seq": rows.RESOURCEBID_SEQ.to_numpy(), "year": rows.year.to_numpy(), "m": m})
                .dropna()
                .groupby(["seq", "year"])
                .m.median()
                .reset_index()
            )
            ry["cap"] = ry.seq.map(sub.cap)
            cls_out["bands"][band] = round(D._wquantile(ry.m.to_numpy(float), ry.cap.to_numpy(float), 0.5), 3)
            cls_out["per_year"][band] = {
                str(y): round(D._wquantile(ry[ry.year == y].m.to_numpy(float), ry[ry.year == y].cap.to_numpy(float), 0.5), 3)
                for y in sorted(ry.year.unique())
            }
        out[cls] = cls_out
    return out


def ratio_report(ladder: pd.DataFrame) -> dict:
    """Quarter-p98 / year-p98 capacity ratio distribution (PRECOMMIT §2.2)."""
    r = ladder.drop_duplicates(["RESOURCEBID_SEQ", "quarter"])
    full = r[r.quarter != "2021q3"].ratio_q_over_y
    part = r[r.quarter == "2021q3"].ratio_q_over_y

    def q(s):
        return {
            "n": int(len(s)),
            "p05": round(float(s.quantile(0.05)), 4),
            "p50": round(float(s.quantile(0.5)), 4),
            "p95": round(float(s.quantile(0.95)), 4),
            "within_5pct": round(float(((s - 1).abs() <= 0.05).mean()), 4),
        }

    return {"full_quarters": q(full), "2021q3_partial": q(part)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hr-cut", type=float, default=8.5)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument(
        "--classify-span",
        choices=["full", "repro"],
        default="full",
        help="days the classifier sees: the full pooled intake (PRECOMMIT §2.4) or the "
        "committed artifact's own 2023-01-01..2025-09-30 (diagnostic A)",
    )
    args = ap.parse_args(argv)
    c_start, c_end = (REPRO_START, REPRO_END) if args.classify_span == "repro" else (None, None)

    geom = D._fleet_geometry()
    gas = D._gas_staircase()
    committed = json.loads(COMMITTED.read_text())
    result = {"hr_cut": args.hr_cut, "markets": {}}

    per_market = {}
    for label, sub in (("DAM", "agg_dam"), ("RTM", "agg")):
        hourly, ladder = load_market(sub)
        cap_y = hourly.groupby(["RESOURCEBID_SEQ", "year"])["hour_max_mw"].quantile(0.98)
        ladder = rescale_to_year(ladder, cap_y)
        res, st_cut, body = classify(ladder, hourly, gas, args.hr_cut, c_start, c_end)
        gaslike = res[res.is_gas]
        g1 = {}
        for cls in ("CC_REGULAR", "CT_PEAKER", "ST_GAS"):
            b = gaslike[gaslike.cls == cls]
            ratio = float(b.cap.sum()) / geom[cls]["fleet_mw"]
            lo, hi = D.G1_BOUNDS[cls]
            g1[cls] = {
                "n": int(len(b)),
                "bucket_mw": round(float(b.cap.sum()), 0),
                "fleet_mw": round(geom[cls]["fleet_mw"], 0),
                "ratio": round(ratio, 3),
                "bounds": [lo, hi],
                "pass": bool(lo <= ratio <= hi),
                "slope_wmedian": round(D._wquantile(b.slope.to_numpy(float), b.cap.to_numpy(float), 0.5), 3) if len(b) else None,
            }
        m = {
            "n_days": int(ladder.date.nunique()),
            "span": [str(ladder.date.min().date()), str(ladder.date.max().date())],
            "n_resources_classified": int(len(res)),
            "n_gas": int(gaslike.shape[0]),
            "st_cut": st_cut,
            "G1": g1,
            "ratio_q_over_y": ratio_report(ladder),
            "bands_repro_pool": static_bands(ladder, res, gas, geom, REPRO_START, REPRO_END),
            "bands_verdict_pool": static_bands(ladder, res, gas, geom, VERDICT_START, VERDICT_END),
        }
        per_market[label] = {"res": res, "ladder": ladder}
        result["markets"][label] = m
        print(f"\n=== {label}: {m['n_days']} days {m['span']}, classified {m['n_resources_classified']}, gas {m['n_gas']}, st_cut {st_cut}")
        print("G1:", json.dumps(g1))
        print("ratio q/y:", json.dumps(m["ratio_q_over_y"]))
        for pool in ("bands_repro_pool", "bands_verdict_pool"):
            for cls in ("CC_REGULAR", "CT_PEAKER"):
                c = m[pool][cls]
                print(f"  {pool} {cls}: n={c['n_resources']} bands={c['bands']}")
                print(f"      per_year={c['per_year']}")

    # ---------------- G-REPRO ----------------
    dam = result["markets"]["DAM"]
    cc_commit = committed["CC_REGULAR"]
    repro = {"base_hr": {"committed": cc_commit["base_hr"], "pooled": round(geom["CC_REGULAR"]["base_hr"], 3),
                          "note": "fleet-geometry constant in the derive; reproduces by construction",
                          "pass": abs(geom["CC_REGULAR"]["base_hr"] - cc_commit["base_hr"]) <= REPRO_TOL_BASE},
             "cc_slope_wmedian_measured": dam["G1"]["CC_REGULAR"]["slope_wmedian"]}
    ok = repro["base_hr"]["pass"]
    for band in ("econ_low", "econ_high", "peak"):
        c, p = cc_commit["bands"][band], dam["bands_repro_pool"]["CC_REGULAR"]["bands"][band]
        row = {"committed": c, "pooled": p, "dev": round(p - c, 3), "tol": REPRO_TOL_BAND, "pass": bool(abs(p - c) <= REPRO_TOL_BAND)}
        repro[band] = row
        ok = ok and row["pass"]
    # CT reported (charter's G-REPRO names CC only)
    ct_commit = committed["CT_PEAKER"]
    repro["CT_PEAKER_reported"] = {b: {"committed": ct_commit["bands"][b], "pooled": dam["bands_repro_pool"]["CT_PEAKER"]["bands"][b]} for b in ("econ_low", "econ_high", "peak")}
    repro["pass"] = bool(ok)
    result["G_REPRO"] = repro
    print("\nG-REPRO:", json.dumps(repro, indent=1))

    # ---------------- G-POP ----------------
    rtm = result["markets"]["RTM"]
    gpop = {cls: rtm["G1"][cls] for cls in ("CC_REGULAR", "CT_PEAKER")}
    gpop["pass"] = bool(all(gpop[c]["pass"] for c in ("CC_REGULAR", "CT_PEAKER")))
    jac = {}
    for cls in ("CC_REGULAR", "CT_PEAKER"):
        a = set(per_market["RTM"]["res"].query("is_gas and cls == @cls").index)
        b = set(per_market["DAM"]["res"].query("is_gas and cls == @cls").index)
        jac[cls] = {"rtm": len(a), "dam": len(b), "both": len(a & b), "jaccard": round(len(a & b) / max(1, len(a | b)), 3)}
    a = set(per_market["RTM"]["res"].query("is_gas").index)
    b = set(per_market["DAM"]["res"].query("is_gas").index)
    jac["all_gas"] = {"rtm": len(a), "dam": len(b), "both": len(a & b), "jaccard": round(len(a & b) / max(1, len(a | b)), 3)}
    gpop["jaccard_diagnostic"] = jac
    result["G_POP"] = gpop
    print("\nG-POP:", json.dumps(gpop, indent=1))

    # ---------------- Verdict ----------------
    deltas = {}
    for cls in ("CC_REGULAR", "CT_PEAKER"):
        deltas[cls] = {b: round(rtm["bands_verdict_pool"][cls]["bands"][b] - dam["bands_verdict_pool"][cls]["bands"][b], 3)
                       for b in ("committed", "econ_low", "econ_high", "peak")}
    cc = deltas["CC_REGULAR"]
    if not repro["pass"]:
        verdict = "ABANDONED (G-REPRO failed)"
    elif not gpop["pass"]:
        verdict = "INCONCLUSIVE (G-POP failed)"
    elif cc["econ_low"] <= -VERDICT_DELTA and cc["econ_high"] <= -VERDICT_DELTA:
        verdict = "RTM-BELOW"
    elif abs(cc["econ_low"]) < VERDICT_DELTA and abs(cc["econ_high"]) < VERDICT_DELTA:
        verdict = "RTM-FLAT"
    else:
        verdict = "INDETERMINATE"
    result["deltas_rtm_minus_dam_verdict_pool"] = deltas
    result["verdict"] = verdict
    print("\nΔ RTM−DAM (verdict pool):", json.dumps(deltas))
    print("VERDICT:", verdict)

    # ---------------- Diagnostics (gate nothing, decide nothing) ----------------
    diag = {}
    rres, dres = per_market["RTM"]["res"], per_market["DAM"]["res"]
    rlad, dlad = per_market["RTM"]["ladder"], per_market["DAM"]["ladder"]
    # B. RTM gas-like capacity whose seq never bids DAM anywhere in the span (WEIM signature).
    dam_seqs = set(dlad.RESOURCEBID_SEQ.unique())
    rg = rres[rres.is_gas]
    never_dam = ~rg.index.isin(dam_seqs)
    diag["rtm_gaslike_never_in_dam"] = {
        cls: {
            "n": int((never_dam & (rg.cls == cls)).sum()),
            "mw": round(float(rg.cap[never_dam & (rg.cls == cls)].sum()), 0),
            "share_of_bucket_mw": round(
                float(rg.cap[never_dam & (rg.cls == cls)].sum() / max(1e-9, rg.cap[rg.cls == cls].sum())), 3
            ),
        }
        for cls in ("CC_REGULAR", "CT_PEAKER")
    }
    # C. Paired per-resource RTM-DAM band delta on the DAM-classified buckets: same seqs,
    #    same dates, same (shifted) sampling convention on both sides.
    paired = {}
    for cls in ("CC_REGULAR", "CT_PEAKER"):
        sub = dres[dres.is_gas & (dres.cls == cls)]
        rows_r = rlad[rlad.RESOURCEBID_SEQ.isin(sub.index)]
        rows_d = dlad[dlad.RESOURCEBID_SEQ.isin(sub.index)]
        bands_r = static_bands(rows_r, dres, gas, geom, VERDICT_START, VERDICT_END, classes=(cls,))[cls]
        bands_d = static_bands(rows_d, dres, gas, geom, VERDICT_START, VERDICT_END, classes=(cls,))[cls]
        paired[cls] = {
            "n_dam_classified": int(len(sub)),
            "n_with_rtm_rows": int(rows_r.RESOURCEBID_SEQ.nunique()),
            "rtm_bands_on_dam_population": bands_r["bands"] if bands_r else None,
            "dam_bands_same_population": bands_d["bands"] if bands_d else None,
            "delta": {b: round(bands_r["bands"][b] - bands_d["bands"][b], 3) for b in bands_r["bands"]}
            if bands_r and bands_d
            else None,
        }
    diag["paired_same_population_same_convention"] = paired
    result["diagnostics"] = diag
    print("\nDIAGNOSTICS:", json.dumps(diag, indent=1))

    if args.out:
        args.out.write_text(json.dumps(result, indent=1, default=float) + "\n")
        print("wrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
