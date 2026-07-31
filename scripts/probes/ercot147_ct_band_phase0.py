#!/usr/bin/env python
"""ERCOT-147 Phase 0 — is the on-disk SCED TPO corpus sufficient to identify
the ERCOT CT band levels?

The measured CT-band re-identification lane (the ERCOT-145 §4 / ERCOT-146 §4
reopen condition: retire the fitted CT_PEAKER ``offer_curve_by_group``
multipliers — econ_low 1.27 / econ_high 2.18 / peak 13.15 — onto measured
conduct) is chartered Phase-0-first: BEFORE any per-plant construction, measure
whether the four on-disk 60-Day SCED probe-day extracts can identify a band
LEVEL for the CT fleet at all. The ERCOT-144 standard governs: the corpus
licenses a LEVEL identification only when the submitted object is time-stable
(the coal precedent — Oak Grove's modal TPO curve repeats identically x1436
across subsets AND years); it never licenses a time-shape (ERCOT-143 §3).

Diagnostic only: no LP is built, no year is solved, nothing is registered, and
no ``ScenarioConfig`` field or solve path is touched. Rule 23 is honoured —
every quantity is read from the raw disclosure extracts (2024-2025 committed
intake) plus the committed Henry Hub daily series; no residual enters any
derivation. Rule 22: the extracts span 2024-2025 probe days only; no holdout
year is read.

Sections
--------
A  coverage — CT (SCLE90/SCGT90) rows, curve share, resources, days, hours
B  modal-curve stability across the four extracts (the ERCOT-144 licence
   test), on the full (MW, price) key AND the price-tuple-only key (so
   ambient HSL derating cannot be the explanation)
C  the level object — per-resource daily-median price at 10/50/90 % of the
   curve's own reach: dispersion raw, and normalized by daily Henry Hub
   (is it a $ level? is it a gas multiple?)
D  subset dependence — per-resource p50 by extract, against each extract's
   own mean gas (year-pair level moves vs the gas move)
E  intra-day vs day-to-day variance decomposition (what grain reprices?)
F  hour-of-day bias, from the one all-24h subset (three extracts are h11-22)
G  crosswalk reach — the in-repo resource->plant mapping available to a
   per-plant resolution (ercot-dam-plant-crosswalk.csv CT_PEAKER rows)
H  the sub-cost bound — capacity share whose p50 sits below sheet-HR x HH
   burn, per extract (HH-only: no Texas hub daily basis series is on disk,
   so conduct margin and local fuel basis are NOT separable in-repo)

SAMPLING — carry this caveat on every number
--------------------------------------------
The extracts are probe days, not a span: 82 delivery days across 2024-2025
(no 2023 SCED exists on disk), day families chosen as price-tail and control
selections, and three of the four sample only hours 11-22 (ERCOT-123).

Usage
-----
    python scripts/probes/ercot147_ct_band_phase0.py [--json-out PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from market_sim.config import paths  # noqa: E402

_RAW = paths.RAW_DIR / "ercot"

#: Simple-cycle gas resource types (the ERCOT-122 documented taxonomy: SCLE90
#: is simple cycle <=90 MW, SCGT90 >90 MW; both are the CT fleet — CLLIG is
#: coal, GSREH/GSNONR/GSSUP gas steam, CCGT90/CCLE90 combined cycle).
CT_TYPES = ("SCLE90", "SCGT90")

ONLINE = frozenset(
    {"ON", "ONOS", "ONRR", "ONTEST", "ONEMR", "ONREG", "EMR", "EMRSWGR",
     "ONRUC", "ONHOLD"}
)

TPO_MW = [f"Submitted TPO-MW{k}" for k in range(1, 11)]
TPO_PR = [f"Submitted TPO-Price{k}" for k in range(1, 11)]

SUBSETS: tuple[tuple[str, int, str], ...] = (
    ("2024_ercot74_tail_days", 2024, "tail"),
    ("2024_ercot75_control_days", 2024, "control"),
    ("2025_ercot75_control_days", 2025, "control"),
    ("2025_ercot86_tail_days", 2025, "tail"),
)

#: The curated sheet's cap-weighted CT_PEAKER physical heat rate on the 25
#: matched plants (ERCOT-146 §2 — the dispatched basis the replacement's
#: physical-HR term would carry). Used only for the §H sub-cost BOUND.
SHEET_CT_HR = 10.947

#: Capacity fractions of each curve's own reach at which the level is read.
FRACS = (0.10, 0.50, 0.90)


def load_ct(tag: str) -> pd.DataFrame | None:
    """Load one extract's CT rows with numeric TPO columns and an online flag.

    Unlike ``ercot123_coal_sced_reach.load_sced`` this keeps BOTH online and
    offline rows (a submitted TPO curve is standing conduct for the day
    whatever the telemetered status; conditioning on online status would
    select on dispatch) and needs no ``HASL``, so the December-2025 schema
    revision does not drop rows here.
    """
    path = _RAW / f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{tag}.parquet"
    if not path.exists():
        return None
    cols = (["SCED Time Stamp", "Resource Name", "Resource Type",
             "Telemetered Resource Status", "HSL", "LSL"] + TPO_MW + TPO_PR)
    df = pd.read_parquet(path, columns=cols)
    df = df[df["Resource Type"].isin(CT_TYPES)].copy()
    if df.empty:
        return None
    for c in ["HSL", "LSL"] + TPO_MW + TPO_PR:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["online"] = (
        df["Telemetered Resource Status"].astype(str).str.strip().isin(ONLINE)
    )
    df["ts"] = pd.to_datetime(df["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S")
    df["day"] = df["ts"].dt.normalize()
    df["subset"] = tag
    return df.reset_index(drop=True)


def _curve_arrays(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(P, M, ok) for the TPO columns of a frame."""
    P = df[TPO_PR].to_numpy(float)
    M = df[TPO_MW].to_numpy(float)
    return P, M, np.isfinite(P) & np.isfinite(M)


def attach_levels(df: pd.DataFrame) -> pd.DataFrame:
    """Keep curve-carrying rows; attach price at each FRAC of the curve's reach.

    The read is curve-relative (fraction of the row's own top MW), so ambient
    HSL derating moves the window with the curve instead of aliasing into the
    price read.
    """
    P, M, ok = _curve_arrays(df)
    df = df[ok.any(axis=1)].reset_index(drop=True)
    P, M, ok = _curve_arrays(df)
    top = np.where(ok, M, -np.inf).max(axis=1)
    Mm = np.where(ok, M, np.inf)
    order = np.argsort(Mm, axis=1)
    Ms = np.take_along_axis(Mm, order, axis=1)
    Ps = np.take_along_axis(np.where(ok, P, np.nan), order, axis=1)
    for f in FRACS:
        idx = (Ms >= (f * top)[:, None]).argmax(axis=1)
        df[f"p{int(f * 100)}"] = Ps[np.arange(len(df)), idx]
    df["top_mw"] = top
    return df


def _capq(frame: pd.DataFrame, col: str, w: str = "hsl",
          qs: tuple[float, ...] = (0.25, 0.5, 0.75)) -> dict[str, float]:
    """Capacity-weighted quantiles of a per-resource column."""
    o = frame.dropna(subset=[col]).sort_values(col)
    if o.empty:
        return {}
    cw = o[w].cumsum() / o[w].sum()
    return {f"p{int(q * 100)}": round(float(np.interp(q, cw, o[col])), 3)
            for q in qs}


def section_a(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """A — coverage: rows, curve share and resource counts per extract."""
    rows = []
    for tag, year, fam in SUBSETS:
        d = raw.get(tag)
        if d is None:
            continue
        _P, _M, ok = _curve_arrays(d)
        has = ok.any(axis=1)
        hrs = sorted(d["ts"].dt.hour.unique().tolist())
        for lab, m in (("online", d["online"].to_numpy()),
                       ("offline", (~d["online"]).to_numpy())):
            rows.append({
                "subset": tag, "year": year, "family": fam, "status": lab,
                "days": int(d["day"].nunique()),
                "hours_distinct": len(hrs),
                "rows": int(m.sum()),
                "rows_with_curve": int((m & has).sum()),
                "curve_share": float((m & has).sum() / m.sum()) if m.sum() else np.nan,
                "resources_with_curve": int(
                    d.loc[m & has, "Resource Name"].nunique()),
            })
    return pd.DataFrame(rows)


def section_b(cur: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """B — the ERCOT-144 licence test: modal-curve identity across extracts.

    Two keys per row: the full curve key (sorted (MW, price) pairs, MW to
    0.1 / price to 0.01) and the price-tuple-only key (sorted prices to 0.01).
    A resource is *stable* on a key when the same modal key wins in all four
    extracts. The coal contrast is the recorded ERCOT-144 identification fact
    (Oak Grove x1436 identical repeats), not recomputed here.
    """
    P, M, ok = _curve_arrays(cur)
    fkeys, pkeys = [], []
    for i in range(len(cur)):
        sel = ok[i]
        o = np.argsort(M[i][sel])
        fkeys.append(tuple(zip(np.round(M[i][sel][o], 1),
                               np.round(P[i][sel][o], 2))))
        pkeys.append(tuple(np.round(np.sort(P[i][sel]), 2)))
    work = cur[["Resource Name", "HSL", "subset"]].copy()
    work["fkey"] = fkeys
    work["pkey"] = pkeys
    rows = []
    for rn, g in work.groupby("Resource Name"):
        r: dict = {"res": rn, "hsl": float(g["HSL"].max()),
                   "n_subsets": int(g["subset"].nunique()), "rows": len(g)}
        for lab, key in (("full", "fkey"), ("price", "pkey")):
            modal = {s: Counter(gs[key]).most_common(1)[0][0]
                     for s, gs in g.groupby("subset")}
            mk, mc = Counter(g[key]).most_common(1)[0]
            r[f"{lab}_stable"] = bool(
                len(set(modal.values())) == 1 and len(modal) == 4)
            r[f"{lab}_modal_share"] = mc / len(g)
        rows.append(r)
    R = pd.DataFrame(rows)
    summary = {
        "resources": int(len(R)),
        "cap_gw": round(float(R["hsl"].sum() / 1e3), 3),
        "in_all_4_subsets": int((R["n_subsets"] == 4).sum()),
        "cap_gw_in_all_4": round(
            float(R.loc[R["n_subsets"] == 4, "hsl"].sum() / 1e3), 3),
        "full_stable_resources": int(R["full_stable"].sum()),
        "full_stable_cap_gw": round(
            float(R.loc[R["full_stable"], "hsl"].sum() / 1e3), 3),
        "price_stable_resources": int(R["price_stable"].sum()),
        "price_stable_cap_gw": round(
            float(R.loc[R["price_stable"], "hsl"].sum() / 1e3), 3),
        "full_modal_share_capwtd": _capq(R, "full_modal_share"),
        "price_modal_share_capwtd": _capq(R, "price_modal_share"),
    }
    return R, summary


def _hh_daily() -> pd.Series:
    """Committed Henry Hub daily series, forward-filled to calendar days."""
    hh = pd.read_csv(_REPO / "data" / "raw" / "gas-prices" / "henry_hub_daily.csv")
    dcol, vcol = hh.columns[0], hh.columns[1]
    hh[dcol] = pd.to_datetime(hh[dcol])
    return hh.set_index(dcol)[vcol].astype(float).resample("D").ffill()


def section_c(cur: pd.DataFrame, online_only: bool) -> pd.DataFrame:
    """C — the level object: daily-median price dispersion, raw and gas-normed."""
    d = cur[cur["online"]] if online_only else cur
    gas = _hh_daily()
    rows = []
    for rn, g in d.groupby("Resource Name"):
        day = g.groupby("day").agg({f"p{int(f*100)}": "median" for f in FRACS})
        day["gas"] = day.index.map(gas)
        r: dict = {"res": rn, "hsl": float(g["HSL"].max()), "days": len(day)}
        for f in FRACS:
            c = f"p{int(f * 100)}"
            v = day[c].dropna()
            if len(v) < 10:
                continue
            med = v.median()
            r[f"{c}_med"] = med
            r[f"{c}_relIQR"] = ((v.quantile(0.75) - v.quantile(0.25)) / abs(med)
                                if med else np.nan)
            both = day[[c, "gas"]].dropna()
            r[f"{c}_gascorr"] = (both[c].corr(both["gas"])
                                 if len(both) > 10 and both[c].std() > 0 else np.nan)
            ratio = (both[c] / both["gas"]).replace(
                [np.inf, -np.inf], np.nan).dropna()
            if len(ratio) > 5 and ratio.median():
                r[f"{c}_hh_ratio_med"] = ratio.median()
                r[f"{c}_hh_ratio_relIQR"] = (
                    (ratio.quantile(0.75) - ratio.quantile(0.25))
                    / abs(ratio.median()))
        rows.append(r)
    return pd.DataFrame(rows)


def section_c_summary(C: pd.DataFrame) -> dict:
    """Capacity-weighted summary of the §C per-resource table."""
    out = {}
    for f in FRACS:
        c = f"p{int(f * 100)}"
        for suf in ("_med", "_relIQR", "_gascorr", "_hh_ratio_med",
                    "_hh_ratio_relIQR"):
            col = c + suf
            if col in C:
                out[col] = _capq(C, col)
    return out


def section_d(cur: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """D — subset dependence: per-resource p50 by extract vs the gas move."""
    gas = _hh_daily()
    sub_gas = {}
    for tag, _y, _f in SUBSETS:
        days = cur.loc[cur["subset"] == tag, "day"].unique()
        sub_gas[tag] = float(np.nanmean([gas.get(d, np.nan) for d in days]))
    rows = []
    for rn, g in cur.groupby("Resource Name"):
        med = g.groupby("subset")["p50"].median()
        if len(med) != 4:
            continue
        r = {"res": rn, "hsl": float(g["HSL"].max())}
        r.update({s: round(float(v), 2) for s, v in med.items()})
        m = med.median()
        r["rel_spread"] = float((med.max() - med.min()) / abs(m)) if m else np.nan
        y24 = med[[t for t, y, _f in SUBSETS if y == 2024]].mean()
        y25 = med[[t for t, y, _f in SUBSETS if y == 2025]].mean()
        r["y25_over_y24"] = float(y25 / y24) if y24 else np.nan
        rows.append(r)
    D = pd.DataFrame(rows)
    g24 = np.mean([sub_gas[t] for t, y, _f in SUBSETS if y == 2024])
    g25 = np.mean([sub_gas[t] for t, y, _f in SUBSETS if y == 2025])
    summary = {
        "subset_mean_gas": {k: round(v, 3) for k, v in sub_gas.items()},
        "gas_ratio_25_over_24": round(float(g25 / g24), 3),
        "rel_spread_capwtd": _capq(D, "rel_spread"),
        "y25_over_y24_capwtd": _capq(D, "y25_over_y24"),
    }
    return D, summary


def section_e(cur: pd.DataFrame) -> dict:
    """E — intra-day share of p50 variance (what grain reprices the curve?)."""
    rows = []
    for rn, g in cur.groupby("Resource Name"):
        if g["day"].nunique() < 10:
            continue
        v = g["p50"].dropna()
        if len(v) < 50 or v.std() == 0:
            continue
        gm = v.mean()
        daymean = g.loc[v.index].groupby("day")["p50"].transform("mean")
        ss_tot = float(((v - gm) ** 2).sum())
        ss_intra = float(((v - daymean) ** 2).sum())
        rows.append({"res": rn, "hsl": float(g["HSL"].max()),
                     "intra_share": ss_intra / ss_tot if ss_tot > 0 else np.nan})
    E = pd.DataFrame(rows)
    return {"intra_day_variance_share_capwtd": _capq(E, "intra_share")}


def section_f(cur: pd.DataFrame) -> dict:
    """F — hour-of-day bias from the all-24h subset (2025_ercot86)."""
    g = cur[cur["subset"] == "2025_ercot86_tail_days"]
    if g.empty:
        return {}
    h = g["ts"].dt.hour
    out = {}
    for lab, m in (("h11-22", (h >= 11) & (h <= 22)),
                   ("h23-h10", (h < 11) | (h > 22))):
        gg = g[m]
        cap = gg.groupby("Resource Name")["HSL"].max()
        med = gg.groupby("Resource Name")["p50"].median()
        j = pd.concat([cap.rename("hsl"), med.rename("p50")], axis=1).dropna()
        out[lab] = {"resources": int(len(j)),
                    "capwtd_p50": round(float((j["p50"] * j["hsl"]).sum()
                                              / j["hsl"].sum()), 2)}
    return out


def section_g() -> dict:
    """G — the in-repo resource->plant crosswalk available to a CT resolution."""
    xw = pd.read_csv(_REPO / "data" / "raw" / "reference"
                     / "ercot-dam-plant-crosswalk.csv")
    ct = xw[xw["class"] == "CT_PEAKER"]
    bins = pd.read_csv(_REPO / "data" / "raw" / "reference"
                       / "custom-bin-assignments.csv")
    cb = bins[bins["Plant_Group"] == "CT_PEAKER"]
    return {
        "crosswalk_ct_sites": int(len(ct)),
        "crosswalk_ct_accepted": int(ct["accepted"].sum()),
        "curated_ct_peaker_rows": int(len(cb)),
        "curated_ct_peaker_mw": round(float(cb["Nameplate_MW"].sum()), 1),
    }


def section_h(cur: pd.DataFrame) -> pd.DataFrame:
    """H — capacity share whose p50 sits below sheet-HR x HH burn, per extract.

    HH-only BOUND: no Texas hub daily series is on disk (ERCOT-146 assessed
    the gap), so a plant buying sub-HH local gas (2024 Waha) cannot be
    distinguished from a sub-cost offer. This is why conduct margin and local
    fuel basis are not separable in-repo.
    """
    gas = _hh_daily()
    rows = []
    for tag, year, fam in SUBSETS:
        g = cur[cur["subset"] == tag]
        if g.empty:
            continue
        day = g.groupby(["Resource Name", "day"]).agg(
            p50=("p50", "median"), hsl=("HSL", "max")).reset_index()
        day["gas"] = day["day"].map(gas)
        day = day.dropna(subset=["p50", "gas"])
        day["below"] = day["p50"] < SHEET_CT_HR * day["gas"]
        rows.append({
            "subset": tag, "year": year, "family": fam,
            "res_days": int(len(day)),
            "cap_share_below_cost_hh": round(
                float((day["hsl"] * day["below"]).sum() / day["hsl"].sum()), 3),
        })
    return pd.DataFrame(rows)


def _show(title: str, obj) -> None:
    print(f"\n=== {title} ===")
    if isinstance(obj, pd.DataFrame):
        if obj.empty:
            print("(no rows)")
            return
        with pd.option_context("display.width", 220, "display.max_columns", 40,
                               "display.float_format", lambda v: f"{v:.3f}"):
            print(obj.to_string(index=False))
    else:
        print(json.dumps(obj, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    """Run every section, print the tables, optionally dump JSON."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args(argv)

    raw: dict[str, pd.DataFrame] = {}
    for tag, _y, _f in SUBSETS:
        d = load_ct(tag)
        if d is None:
            print(f"WARNING: subset missing or empty: {tag}")
            continue
        raw[tag] = d
    a = section_a(raw)
    cur = attach_levels(pd.concat(raw.values(), ignore_index=True))

    b_table, b_sum = section_b(cur)
    c_all = section_c(cur, online_only=False)
    c_on = section_c(cur, online_only=True)
    c_all_sum = section_c_summary(c_all)
    c_on_sum = section_c_summary(c_on)
    d_table, d_sum = section_d(cur)
    e_sum = section_e(cur)
    f_sum = section_f(cur)
    g_sum = section_g()
    h = section_h(cur)

    _show("A - coverage per extract", a)
    _show("B - modal-curve stability (ERCOT-144 licence test)", b_sum)
    _show("C - level dispersion, ALL curve rows (cap-wtd)", c_all_sum)
    _show("C' - level dispersion, ONLINE rows only (robustness)", c_on_sum)
    _show("D - subset dependence (per-resource p50 by extract)", d_sum)
    _show("D - largest resources", d_table.sort_values("hsl", ascending=False).head(12))
    _show("E - intra-day variance share", e_sum)
    _show("F - hour-of-day bias (all-24h subset)", f_sum)
    _show("G - crosswalk reach", g_sum)
    _show("H - sub-cost bound (HH-only)", h)

    if args.json_out:
        payload = {
            "A_coverage": json.loads(a.to_json(orient="records")),
            "B_modal_stability": b_sum,
            "C_level_all_rows": c_all_sum,
            "C_level_online_only": c_on_sum,
            "D_subset_dependence": d_sum,
            "D_largest": json.loads(
                d_table.sort_values("hsl", ascending=False).head(20)
                .to_json(orient="records")),
            "E_intraday": e_sum,
            "F_hour_bias": f_sum,
            "G_crosswalk": g_sum,
            "H_subcost_bound": json.loads(h.to_json(orient="records")),
        }
        Path(args.json_out).write_text(json.dumps(payload, indent=2))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
