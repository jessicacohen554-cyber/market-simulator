"""Zero-LP decomposition of SPP C3a/C3b 2024 (owner R-62) against 2023/2025, from committed sidecars.

Lane closeout-SPP-w2. Model: P1 zonal duals and demand (`system_<y>`), marginal flags
(`unit_marginal_<y>`) of keeper bundle closeout_spp_nuc_span. Actual: SPP hub RT/DA
(`actual_lmp_hourly_zonal_SPP`, North/South hub mapped to the model zone), weighted by the model's
own zonal demand (the scorer's rt_lw construction). The gap is the demand-weighted mean of
(model - actual) split by month, hour of day, actual-RT tercile, zone and model marginal class.
Output: results/phase0/spp/_closeoutsppw2_c3a2024_decomp.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/closeout_spp_nuc_span"
HUB = {"SPP-North": "SPPNORTH_HUB", "SPP-South": "SPPSOUTH_HUB"}


def frame(year: int) -> pd.DataFrame:
    """Zone-hour frame: model price, demand, actual RT/DA, model marginal class."""
    s = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"][["zone", "hour", "price", "demand"]].copy()
    s["zone"] = s["zone"].astype(str)
    z = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet"
    )
    z = z[z.year == year].copy()
    z["zone"] = z["zone"].map({v: k for k, v in HUB.items()})
    f = s.merge(z[["zone", "hour", "rt", "da"]], on=["zone", "hour"], how="left")
    um = pd.read_parquet(
        BUNDLE / f"hourly/unit_marginal_{year}.parquet",
        columns=["zone", "hour", "plant_group", "fuel", "mw", "marginal"],
    )
    um = um[um["marginal"] == 1].copy()
    um["cls"] = um["plant_group"].astype(str)
    um.loc[um["cls"] == "", "cls"] = um["fuel"].astype(str)
    um["zone"] = um["zone"].astype(str)
    # one setter per zone-hour: the marginal row with the largest output
    um = um.sort_values("mw").groupby(["zone", "hour"]).tail(1)
    f = f.merge(um[["zone", "hour", "cls"]], on=["zone", "hour"], how="left")
    f["cls"] = f["cls"].fillna("none/renewable")
    f["month"] = (
        pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(f["hour"], unit="h")
    ).dt.month
    f["hod"] = f["hour"] % 24
    return f


def contrib(f: pd.DataFrame, key: str, ref: str) -> list[dict]:
    """Per bucket: weight share, model/actual lw means, contribution to the C3a gap (pts)."""
    g = f.dropna(subset=[ref])
    tot_w = g["demand"].sum()
    act = (g[ref] * g["demand"]).sum() / tot_w
    out = []
    for k, b in g.groupby(key, observed=True):
        w = b["demand"].sum()
        m = (b["price"] * b["demand"]).sum() / w
        a = (b[ref] * b["demand"]).sum() / w
        out.append(
            {
                key: str(k),
                "w_share": round(w / tot_w, 4),
                "model": round(m, 2),
                "actual": round(a, 2),
                "gap_$": round(m - a, 2),
                "contrib_pts": round(100 * (m - a) * w / tot_w / act, 2),
            }
        )
    return out


def main() -> None:
    """Run the decomposition for 2023-2025 on RT (scored) and DA (diagnostic)."""
    rec = {}
    for year in (2023, 2024, 2025):
        f = frame(year)
        g = f.dropna(subset=["rt"])
        w = g["demand"]
        m, a = (g["price"] * w).sum() / w.sum(), (g["rt"] * w).sum() / w.sum()
        gd = f.dropna(subset=["da"])
        ad = (gd["da"] * gd["demand"]).sum() / gd["demand"].sum()
        # actual-RT tercile on system (demand-weighted) hourly price
        sysh = g.groupby("hour").apply(
            lambda b: (b["rt"] * b["demand"]).sum() / b["demand"].sum()
        )
        terc = pd.qcut(sysh, 3, labels=["low", "mid", "high"])
        f["rt_tercile"] = f["hour"].map(terc)
        r = {
            "model_lw": round(m, 2),
            "rt_lw": round(a, 2),
            "c3a_pct": round(100 * (m / a - 1), 1),
            "da_lw": round(ad, 2),
            "c3a_vs_da_pct": round(100 * (m / ad - 1), 1),
            "model_eq": round(f.groupby("hour")["price"].mean().mean(), 2),
        }
        for key in ("month", "hod", "rt_tercile", "zone", "cls"):
            r[f"by_{key}_rt"] = contrib(f, key, "rt")
        r["by_month_da"] = contrib(f, "month", "da")
        r["by_rt_tercile_da"] = contrib(f, "rt_tercile", "da")
        rec[year] = r
        print(year, {k: v for k, v in r.items() if not k.startswith("by_")}, flush=True)
    out = REPO / "results/phase0/spp/_closeoutsppw2_c3a2024_decomp.json"
    out.write_text(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
