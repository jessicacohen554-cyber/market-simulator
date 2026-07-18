"""CT population cross-tab in Aug-2023 hod14-19: award x curve x status.

No status prejudice: who cleared, who had curves, at what prices.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import derive_ercot_dam_cleared_share as dcs  # noqa: E402


def wq(v, w, qs):
    if len(v) == 0:
        return [float("nan")] * len(qs)
    return dcs._weighted_quantiles(np.asarray(v, float), np.asarray(w, float), qs)


def main() -> None:
    df = dcs._load_year(2023)
    df = df[df["Resource Type"].isin(("SCGT90", "SCLE90"))].copy()
    ts = dcs.prevailing_he_to_cst(df["dd"], df["Hour Ending"].astype(int))
    df["mo"] = ts.dt.month.to_numpy()
    df["hod"] = ts.dt.hour.to_numpy()
    d = df[(df.mo == 8) & (df.hod >= 14) & (df.hod < 20)].copy()
    n_hours = d.groupby(["dd", "Hour Ending"]).ngroups

    MW = d[dcs._MW_COLS].to_numpy(float)
    PR = np.minimum(d[dcs._PR_COLS].to_numpy(float), dcs.HCAP_USD_MWH)
    d["hsl"] = d["HSL"].astype(float)
    d["award"] = d["Awarded Quantity"].fillna(0.0).clip(lower=0.0)
    d["has_curve"] = np.isfinite(MW).any(axis=1) & np.isfinite(PR).any(axis=1)
    d["cleared"] = d["award"] > 0

    print(f"hours: {n_hours}; CT resource-hours: {len(d)}")
    tab = (
        d.groupby(["cleared", "has_curve"])
        .agg(rows=("hsl", "size"), hsl_gw=("hsl", "sum"), award_gw=("award", "sum"))
        .assign(
            hsl_gw=lambda x: (x.hsl_gw / n_hours / 1e3).round(2),
            award_gw=lambda x: (x.award_gw / n_hours / 1e3).round(2),
        )
    )
    print("\ncross-tab (per-hour GW):")
    print(tab.to_string())
    print("\nstatus mix of CLEARED rows:")
    print(d[d.cleared]["Resource Status"].value_counts().head(8).to_dict())
    print("status mix of cleared NO-CURVE rows:")
    print(d[d.cleared & ~d.has_curve]["Resource Status"].value_counts().head(8).to_dict())

    # Award-margin price for cleared WITH-curve rows, award-weighted.
    cw = d.cleared & d.has_curve
    mwc = np.where(np.isfinite(MW[cw]), MW[cw], np.inf)
    prc = PR[cw.to_numpy()]
    tgt = d.loc[cw, "award"].to_numpy(float)
    pos = np.clip((mwc < tgt[:, None]).sum(axis=1), 0, 9)
    price = prc[np.arange(cw.sum()), pos]
    m = np.isfinite(price)
    qs = wq(price[m], tgt[m], (0.1, 0.3, 0.5, 0.7, 0.9))
    print(
        f"\ncleared-with-curve award ({tgt.sum() / n_hours / 1e3:.2f} GW/h): "
        f"award-margin price q10/30/50/70/90: "
        + " ".join(f"${q:,.0f}" for q in qs)
    )
    # Full offered curve of with-curve rows (any award state), MW-weighted
    hc = d.has_curve
    mwh = np.where(np.isfinite(MW[hc]), MW[hc], np.nan)
    prh = PR[hc.to_numpy()]
    availh = d.loc[hc, "hsl"].to_numpy(float)
    prev = np.zeros(hc.sum())
    seg_mw, seg_pr = [], []
    for k in range(mwh.shape[1]):
        q = mwh[:, k]
        p = prh[:, k]
        valid = np.isfinite(q) & np.isfinite(p)
        hi = np.minimum(q, availh)
        mw = np.where(valid, np.maximum(hi - prev, 0.0), 0.0)
        take = mw > 0
        seg_mw.append(mw[take])
        seg_pr.append(p[take])
        prev = np.where(valid, np.maximum(prev, np.minimum(q, availh)), prev)
    smw = np.concatenate(seg_mw)
    spr = np.concatenate(seg_pr)
    print(
        f"ALL offered CT curve MW ({smw.sum() / n_hours / 1e3:.2f} GW/h), "
        f"MW-wtd price q10/30/50/70/90/97: "
        + " ".join(
            f"${q:,.0f}" for q in wq(spr, smw, (0.1, 0.3, 0.5, 0.7, 0.9, 0.97))
        )
    )
    # And the price of the MW between award and curve-top (offered, uncleared)
    prev = np.zeros(hc.sum())
    awardh = d.loc[hc, "award"].to_numpy(float)
    seg_mw2, seg_pr2 = [], []
    for k in range(mwh.shape[1]):
        q = mwh[:, k]
        p = prh[:, k]
        valid = np.isfinite(q) & np.isfinite(p)
        lo = np.maximum(prev, awardh)
        hi = np.minimum(q, availh)
        mw = np.where(valid, np.maximum(hi - lo, 0.0), 0.0)
        take = mw > 0
        seg_mw2.append(mw[take])
        seg_pr2.append(p[take])
        prev = np.where(valid, np.maximum(prev, q), prev)
    smw2 = np.concatenate(seg_mw2)
    spr2 = np.concatenate(seg_pr2)
    print(
        f"offered-UNCLEARED CT MW ({smw2.sum() / n_hours / 1e3:.2f} GW/h), "
        f"MW-wtd price q10/30/50/70/90: "
        + " ".join(f"${q:,.0f}" for q in wq(spr2, smw2, (0.1, 0.3, 0.5, 0.7, 0.9)))
    )


if __name__ == "__main__":
    main()
