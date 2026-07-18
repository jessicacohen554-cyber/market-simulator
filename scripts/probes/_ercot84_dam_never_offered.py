"""Measure the never-offered DAM capability wedge and its posture price (CT/CC).

For each class and net-load bin (cleared-share derive's own edges), split live
capability into: cleared / offered-but-uncleared / NEVER-OFFERED, and measure
the MW-weighted top-of-curve posture price distribution of the never-offered
capacity (each resource's top submitted price weighted by its never-offered MW).
All from the 60-Day DAM disclosure — the same collapse the adopted wall uses.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import derive_ercot_dam_cleared_share as dcs  # noqa: E402

YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2023


def main() -> None:
    gas_day = dcs._gas_day_series()
    df = dcs._load_year(YEAR)
    ts = dcs.prevailing_he_to_cst(df["dd"], df["Hour Ending"].astype(int))
    mo = ts.dt.month.to_numpy()
    dy = ts.dt.day.to_numpy()
    hh = ts.dt.hour.to_numpy()
    ok = ~((mo == 2) & (dy == 29))
    df = df.loc[np.asarray(ok)].copy()
    df["hoy"] = dcs._MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    df["cls"] = df["Resource Type"].map(dcs.CLASS_OF_RESTYPE)
    df["site"] = [
        dcs._site(n, t) for n, t in zip(df["Resource Name"], df["Resource Type"])
    ]
    df["avail"] = np.where(df["Resource Status"].eq("OUT"), 0.0, df["HSL"])
    df["award"] = df["Awarded Quantity"].fillna(0.0).clip(lower=0.0)
    df["_awarded"] = (df["award"] > 0).astype(int)
    df = df.sort_values(["cls", "site", "hoy", "_awarded", "avail"])
    rep = df.groupby(["cls", "site", "hoy"], sort=False).tail(1).copy()

    MW = rep[dcs._MW_COLS].to_numpy(float)
    PR = rep[dcs._PR_COLS].to_numpy(float)
    # Curve top MW (max finite MW) and top price (price at last finite point).
    mw_f = np.where(np.isfinite(MW), MW, -np.inf)
    top_mw = np.nanmax(np.where(np.isfinite(MW), MW, np.nan), axis=1)
    top_mw = np.where(np.isfinite(top_mw), top_mw, 0.0)
    last_idx = np.argmax(mw_f, axis=1)
    top_pr = np.minimum(
        PR[np.arange(len(rep)), last_idx], dcs.HCAP_USD_MWH
    )
    avail = rep["avail"].to_numpy(float)
    award = rep["award"].to_numpy(float)

    offered = np.minimum(top_mw, avail)
    never = np.maximum(avail - offered, 0.0)
    unclr = np.maximum(offered - award, 0.0)

    pct = dcs._netload_pct(YEAR)
    edges = np.asarray(dcs.NETLOAD_PCT_EDGES)
    hour_bin = np.searchsorted(edges, pct, side="right")
    b = hour_bin[rep["hoy"].to_numpy(int)]
    n_bins = len(edges) + 1

    out = pd.DataFrame(
        {
            "cls": rep["cls"].to_numpy(),
            "bin": b,
            "hoy": rep["hoy"].to_numpy(int),
            "avail": avail,
            "award": award,
            "unclr": unclr,
            "never": never,
            "top_pr": np.where(np.isfinite(top_pr), top_pr, np.nan),
        }
    )

    print(f"=== {YEAR}: live capability split by net-load bin (GW-mean per hour) ===")
    print("bin edges:", list(edges))
    for cls in ("CT", "CC"):
        d = out[out.cls == cls]
        print(f"\n== {cls} ==")
        for bb in range(n_bins):
            db = d[d.bin == bb]
            nh = db.hoy.nunique()
            if not nh:
                continue
            live = db.avail.sum() / nh / 1e3
            aw = db.award.sum() / nh / 1e3
            un = db.unclr.sum() / nh / 1e3
            nv = db.never.sum() / nh / 1e3
            # posture: MW-weighted quantiles of top price over never-offered MW
            nn = db[(db.never > 0) & np.isfinite(db.top_pr)]
            no_curve = db[(db.never > 0) & ~np.isfinite(db.top_pr)]
            qs = (
                dcs._weighted_quantiles(
                    nn.top_pr.to_numpy(), nn.never.to_numpy(), (0.1, 0.3, 0.5, 0.7, 0.9)
                )
                if len(nn)
                else [np.nan] * 5
            )
            print(
                f" bin{bb}: live {live:5.1f} GW = cleared {aw:5.1f} + "
                f"uncleared-offered {un:4.1f} + NEVER-OFFERED {nv:4.1f} "
                f"(no-curve share of never {no_curve.never.sum() / max(db.never.sum(), 1e-9):.2f}) | "
                f"never-MW posture top-price q10/30/50/70/90: "
                f"{' '.join(f'${q:,.0f}' if q == q else 'n/a' for q in qs)}"
            )

    # The Aug target hours specifically: hod 14-19, Aug, tight bins
    aug_hoy = set()
    base = dcs._MONTH_START_HOUR[7]  # Aug 1 00:00
    for day in range(31):
        for h in range(14, 20):
            aug_hoy.add(base + day * 24 + h)
    d = out[(out.cls == "CT") & out.hoy.isin(aug_hoy)]
    nh = d.hoy.nunique()
    nn = d[(d.never > 0) & np.isfinite(d.top_pr)]
    qs = (
        dcs._weighted_quantiles(
            nn.top_pr.to_numpy(), nn.never.to_numpy(), (0.1, 0.3, 0.5, 0.7, 0.9)
        )
        if len(nn)
        else [np.nan] * 5
    )
    print(
        f"\n== CT, Aug hod14-19 ({nh} hours): live {d.avail.sum() / nh / 1e3:.1f} GW = "
        f"cleared {d.award.sum() / nh / 1e3:.1f} + uncleared-offered "
        f"{d.unclr.sum() / nh / 1e3:.1f} + NEVER {d.never.sum() / nh / 1e3:.1f} | "
        f"posture q10/30/50/70/90: "
        f"{' '.join(f'${q:,.0f}' if q == q else 'n/a' for q in qs)}"
    )
    # And the uncleared-offered segment price distribution in the same hours
    # (via the derive's own segment machinery, filtered to these hours):
    site_hours, segments = dcs._collapse_and_segment(df, gas_day)
    seg = segments[(segments.cls == "CT") & segments.hoy.isin(aug_hoy)]
    gd = gas_day.reindex(
        pd.date_range(f"{YEAR}-08-01", periods=31, freq="D")
    ).mean()
    if len(seg):
        qs = dcs._weighted_quantiles(
            seg.mult.to_numpy() * float(gd), seg.mw.to_numpy(), (0.1, 0.3, 0.5, 0.7, 0.9)
        )
        print(
            f"   uncleared-OFFERED segment prices same hours (at Aug-mean gas "
            f"${gd:.2f}): q10/30/50/70/90: "
            f"{' '.join(f'${q:,.0f}' for q in qs)}"
        )


if __name__ == "__main__":
    main()
