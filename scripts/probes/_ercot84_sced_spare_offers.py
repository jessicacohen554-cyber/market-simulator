"""Measure the RT (SCED) offer surface of online spare in 2024 tail vs control hours.

For each SCED interval in the on-disk ercot74/75 sample days, per gas class:
segment the SCED2 offer curve between Base Point and HASL (the energy-
dispatchable spare net of AS responsibility), MW-weighted price quantiles.
Contrast actual RT>$200 hours vs all other sampled hours.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw" / "ercot"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"

SCED2_MW = [f"SCED2 Curve-MW{i}" for i in range(1, 36)]
SCED2_PR = [f"SCED2 Curve-Price{i}" for i in range(1, 36)]
SCED1_MW = [f"SCED1 Curve-MW{i}" for i in range(1, 36)]
SCED1_PR = [f"SCED1 Curve-Price{i}" for i in range(1, 36)]
CLS = {"SCGT90": "CT", "SCLE90": "CT", "CCGT90": "CC", "CCLE90": "CC",
       "GSREH": "ST", "GSNONR": "ST", "GSSUP": "ST"}
ON = ("ON", "ONREG", "ONRR", "ONOS", "ONRUC", "ONDSR", "ONEMR", "ONOSREG",
      "ONTEST", "ONRGL", "ONHOLD")


def wq(v, w, qs):
    order = np.argsort(v)
    v, w = np.asarray(v)[order], np.asarray(w)[order]
    cw = np.cumsum(w)
    if len(cw) == 0 or cw[-1] <= 0:
        return [float("nan")] * len(qs)
    return [float(np.interp(q, cw / cw[-1], v)) for q in qs]


def segments(df, curve_mw, curve_pr, lo_col, hi_col):
    MW = df[curve_mw].to_numpy(float)
    PR = df[curve_pr].to_numpy(float)
    lo0 = df[lo_col].to_numpy(float)
    hi0 = df[hi_col].to_numpy(float)
    prev = np.maximum(lo0, 0.0)
    out_mw, out_pr, out_key = [], [], []
    key = df["_key"].to_numpy()
    for k in range(MW.shape[1]):
        q = MW[:, k]
        p = PR[:, k]
        valid = np.isfinite(q) & np.isfinite(p)
        hi = np.minimum(q, hi0)
        mw = np.where(valid, np.maximum(hi - np.maximum(prev, lo0), 0.0), 0.0)
        take = mw > 0
        if take.any():
            out_mw.append(mw[take])
            out_pr.append(np.minimum(p[take], 5000.0))
            out_key.append(key[take])
        prev = np.where(valid, np.maximum(prev, q), prev)
    return (np.concatenate(out_mw) if out_mw else np.array([]),
            np.concatenate(out_pr) if out_pr else np.array([]),
            np.concatenate(out_key) if out_key else np.array([], dtype=object))


def main() -> None:
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    files = sorted(RAW.glob(f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{year}_*.parquet"))
    act = pd.read_parquet(ACTUAL)
    act = act[act["year"] == year].reset_index(drop=True)
    T = len(act)
    ts_std = pd.date_range(f"{year}-01-01", periods=T, freq="h")
    rt = act["rt"].to_numpy(float)
    tail_keys = {(t.month, t.day, t.hour) for t, r in zip(ts_std, rt) if r > 200}
    rt_by_key = {(t.month, t.day, t.hour): r for t, r in zip(ts_std, rt)}
    print(f"{year}: actual >$200 hours total {len(tail_keys)}")

    cols = (["SCED Time Stamp", "Resource Type", "Telemetered Resource Status",
             "HSL", "HASL", "Base Point"] + SCED2_MW + SCED2_PR)
    parts = []
    for f in files:
        df = pd.read_parquet(f, columns=cols)
        parts.append(df)
    df = pd.concat(parts, ignore_index=True)
    ts = pd.to_datetime(df["SCED Time Stamp"])
    # CPT -> CST: localize America/Chicago (ambiguous fall-back: first), to fixed CST
    cst = (ts.dt.tz_localize("America/Chicago", ambiguous=True, nonexistent="shift_forward")
             .dt.tz_convert("Etc/GMT+6"))
    df["_key"] = list(zip(cst.dt.month, cst.dt.day, cst.dt.hour))
    df["cls"] = df["Resource Type"].map(CLS)
    df = df[df["cls"].notna()].copy()
    stat = df["Telemetered Resource Status"].astype(str).str.strip()
    df = df[stat.str.startswith("ON")].copy()
    df["is_tail"] = df["_key"].isin(tail_keys)
    n_int = df.groupby("_key")["SCED Time Stamp"].nunique()
    covered_tail = sorted(k for k in set(df.loc[df.is_tail, "_key"]) )
    print(f"covered tail hours in sample: {len(covered_tail)}: {covered_tail[:12]}")

    for label, sub in (("TAIL (actual RT>$200)", df[df.is_tail]),
                       ("CONTROL (other sampled hours)", df[~df.is_tail])):
        n_iv = sub.groupby(["_key", "SCED Time Stamp"]).ngroups
        if n_iv == 0:
            continue
        print(f"\n== {label}: {n_iv} class-intervals ==")
        for cls in ("CT", "CC", "ST"):
            c = sub[sub.cls == cls]
            if not len(c):
                continue
            niv = c.groupby("SCED Time Stamp").ngroups
            # spare above base point, net of AS (HASL)
            smw, spr, skey = segments(c, SCED2_MW, SCED2_PR, "Base Point", "HASL")
            spare_gw = smw.sum() / max(niv, 1) / 1e3
            qs = wq(spr, smw, (0.1, 0.3, 0.5, 0.7, 0.9))
            over200 = smw[spr > 200].sum() / max(niv, 1) / 1e3
            over500 = smw[spr > 500].sum() / max(niv, 1) / 1e3
            print(f"  {cls}: spare(BP->HASL) {spare_gw:5.2f} GW/interval | "
                  f"offer q10/30/50/70/90: "
                  + " ".join(f"${q:,.0f}" for q in qs)
                  + f" | MW>200: {over200:.2f} GW  MW>500: {over500:.2f} GW")


if __name__ == "__main__":
    main()
