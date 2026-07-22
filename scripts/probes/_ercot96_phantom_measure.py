"""ERCOT-96 Lane A-1 MEASURE (solve-free): size the class-day-flat availability
phantom at plant×hour grain on the ACTUAL 2023 tail days.

Extends ERCOT-95 Finding 6 (the hod-shape phantom table) two ways:
  1. restricts to the measured tail days (2023 days carrying >=1 RT hour with
     system_lambda > $200 — the C3c benchmark set), and
  2. adds the PER-PLANT component: the capacity mass a class-grain (even
     class-HOUR-grain) overlay still allocates to the wrong sites, i.e. what
     ONLY plant-grain application can place. For each tail hour
         alloc_s(h) = live_day_mean_s x [class_hour_total(h) / class_day_total(d)]
     (the best a class-hour rescale of day-mean shares can do) and
         misalloc(h) = 0.5 x sum_s |live_s(h) - alloc_s(h)|.

Pure disclosure-side measurement (no LP, no model output beyond the committed
keeper sidecar for context). Reuses the derive module's own site collapse /
rating recipe so treatment is byte-identical to the deployed class-day derive.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_ercot_thermal_dam_availability import (  # noqa: E402
    RESTYPE_TO_CLASS,
    _RATING_QUANTILE,
    _load_year,
    _site,
)

YEAR = 2023
LAMBDA_TAIL = 200.0


def main() -> None:
    # ------------------------------------------------------------------ tail set
    res = pd.read_parquet(REPO / f"data/raw/ercot/ercot_{YEAR}_ordc_reserves_hourly.parquet")
    lam = res.set_index("hour")["system_lambda"].reindex(range(8760))
    prc = res.set_index("hour")["prc"].reindex(range(8760))
    tail_hours = np.flatnonzero((lam > LAMBDA_TAIL).values)
    # model non-leap clock: hour = (doy-1)*24 + hod
    doy = tail_hours // 24 + 1
    hod = tail_hours % 24
    dates = pd.to_datetime(f"{YEAR}-01-01") + pd.to_timedelta(doy - 1, unit="D")
    tail_days = pd.DatetimeIndex(sorted(set(dates))).normalize()
    tf = pd.DataFrame({"hour": tail_hours, "date": dates.normalize(), "hod": hod})
    print(f"[tail] {len(tail_hours)} RT hours with system_lambda > ${LAMBDA_TAIL:.0f} "
          f"across {len(tail_days)} days")
    print("[tail] by month:", tf.groupby(tf["date"].dt.month)["hour"].count().to_dict())
    print("[tail] by hod:", tf.groupby("hod")["hour"].count().to_dict())
    print(f"[tail] PRC on tail hours: median {prc.iloc[tail_hours].median():.0f} "
          f"min {prc.iloc[tail_hours].min():.0f} MW")

    # ------------------------------------------------- disclosure at site x hour
    df = _load_year(YEAR)
    df["cls"] = df["Resource Type"].map(RESTYPE_TO_CLASS)
    df["site"] = [_site(n, t) for n, t in zip(df["Resource Name"], df["Resource Type"])]
    df["date"] = pd.to_datetime(df["Delivery Date"]).dt.normalize()
    df["out"] = df["Resource Status"].eq("OUT")

    ok = df[~df["out"] & (df["HSL"] > 0.0)]
    site_hour_ok = ok.groupby(["cls", "site", "date", "Hour Ending"])["HSL"].max()
    rating = site_hour_ok.groupby(["cls", "site"]).quantile(_RATING_QUANTILE)

    live = df.copy()
    live["hsl_live"] = np.where(live["out"], 0.0, live["HSL"])
    live_sh = live.groupby(["cls", "site", "date", "Hour Ending"])["hsl_live"].max()
    live_sh = np.minimum(live_sh, rating.reindex(live_sh.index.droplevel([2, 3])).values)
    live_sh = live_sh.rename("live")
    live_day = live_sh.groupby(["cls", "site", "date"]).mean().rename("day_mean")

    sh = live_sh.reset_index()
    sh["hod"] = sh["Hour Ending"].astype(int) - 1  # HE 1-24 -> hod 0-23
    sh = sh.merge(live_day.reset_index(), on=["cls", "site", "date"])

    # ------------------------------------- 1) hod-shape phantom, tail days, CC+CT
    gas = sh[sh["cls"].isin(["CC_REGULAR", "CT_PEAKER"])]
    gt = gas[gas["date"].isin(tail_days)]
    cls_hod = (
        gt.groupby(["date", "hod"])[["day_mean", "live"]].sum()
        .assign(phantom=lambda x: x["day_mean"] - x["live"])
    )
    by_hod = cls_hod.groupby("hod")["phantom"].agg(["mean", "median", "max"])
    print("\n[shape] CC+CT phantom (day_mean - live) MW by hod, TAIL DAYS "
          f"(n={len(tail_days)}):")
    print(by_hod.round(0).to_string())
    aft = cls_hod.reset_index()
    aft = aft[aft["hod"].between(13, 19)]
    print(f"[shape] afternoon (hod 13-19) phantom: mean {aft['phantom'].mean():.0f} MW, "
          f"p90 {aft['phantom'].quantile(0.9):.0f}, max {aft['phantom'].max():.0f}")
    # per-class split on tail-day afternoons
    pc = (
        gt[gt["hod"].between(13, 19)]
        .groupby(["cls"])[["day_mean", "live"]].sum()
    )
    pc["phantom_avg_per_hour"] = (pc["day_mean"] - pc["live"]) / len(
        gt[gt["hod"].between(13, 19)][["date", "hod"]].drop_duplicates()
    )
    print("[shape] per-class afternoon phantom avg MW/h:")
    print(pc["phantom_avg_per_hour"].round(0).to_string())

    # ---------------------------------- 2) phantom ON THE 181 TAIL HOURS proper
    key = pd.MultiIndex.from_frame(tf[["date", "hod"]])
    ch = cls_hod.reindex(key)
    print(f"\n[tail-hours] CC+CT phantom on the {len(tail_hours)} actual tail hours: "
          f"mean {ch['phantom'].mean():.0f} MW, median {ch['phantom'].median():.0f}, "
          f"p90 {ch['phantom'].quantile(0.9):.0f}, max {ch['phantom'].max():.0f}")
    prc_t = prc.iloc[tail_hours].values
    ph_t = ch["phantom"].values
    m = np.isfinite(ph_t)
    print(f"[tail-hours] phantom / (PRC dip below median-day PRC): phantom vs PRC "
          f"corr {np.corrcoef(ph_t[m], prc_t[m])[0,1]:.2f}")

    # ------------------------- 3) per-plant misallocation beyond class-hour grain
    # alloc_s(h) = day_mean_s * class_hour_total / class_day_total
    gt2 = gt.copy()
    cls_tot = gt2.groupby(["cls", "date", "hod"])[["day_mean", "live"]].sum().rename(
        columns={"day_mean": "cls_day", "live": "cls_hour"}
    )
    gt2 = gt2.merge(cls_tot, on=["cls", "date", "hod"])
    gt2["alloc"] = gt2["day_mean"] * gt2["cls_hour"] / gt2["cls_day"].replace(0, np.nan)
    gt2["mis"] = (gt2["live"] - gt2["alloc"]).abs()
    mis_h = gt2.groupby(["date", "hod"])["mis"].sum() * 0.5
    mis_tail = mis_h.reindex(key)
    print(f"\n[per-plant] misallocated MW a class-HOUR overlay still leaves (tail hours): "
          f"mean {mis_tail.mean():.0f}, median {mis_tail.median():.0f}, "
          f"p90 {mis_tail.quantile(0.9):.0f}, max {mis_tail.max():.0f}")
    # concentration: top sites by (rating - live) on tail hours
    gt2["outage_mw"] = np.maximum(
        0.0, rating.reindex(pd.MultiIndex.from_frame(gt2[["cls", "site"]])).values - gt2["live"].values
    )
    th = gt2.merge(tf[["date", "hod"]], on=["date", "hod"])
    conc = th.groupby("site")["outage_mw"].mean().sort_values(ascending=False)
    print("[per-plant] top-12 sites by mean derated MW on tail hours:")
    print(conc.head(12).round(0).to_string())
    tot = conc.sum()
    print(f"[per-plant] top-10 share of mean tail-hour derate: {conc.head(10).sum()/tot:.1%} "
          f"(total {tot:.0f} MW)")

    # ------------------------------- 4) ST_GAS same table (drag class, context)
    st = sh[(sh["cls"] == "ST_GAS") & sh["date"].isin(tail_days)]
    st_hod = (
        st.groupby(["date", "hod"])[["day_mean", "live"]].sum()
        .assign(phantom=lambda x: x["day_mean"] - x["live"])
    )
    st_t = st_hod.reindex(key)
    print(f"\n[context] ST_GAS phantom on tail hours: mean {st_t['phantom'].mean():.0f} MW, "
          f"max {st_t['phantom'].max():.0f}")

    # ------------------------------------------ 5) model-side context, keeper 2023
    ch_k = pd.read_parquet(
        REPO / "results/calibration/ercot91_seasonal_drag_fullspan/hourly/class_hourly_2023.parquet"
    )
    sysk = pd.read_parquet(
        REPO / "results/calibration/ercot91_seasonal_drag_fullspan/hourly/system_2023.parquet"
    )
    px = sysk.groupby("hour")["price"].max()
    model_tail = np.flatnonzero((px > LAMBDA_TAIL).reindex(range(8760), fill_value=False).values)
    both = np.intersect1d(model_tail, tail_hours)
    print(f"\n[model] keeper 2023 model tail {len(model_tail)} h; overlap with actual "
          f"{len(both)} h; missing {len(np.setdiff1d(tail_hours, model_tail))} h")
    disp = ch_k[ch_k["klass"].isin(["CC_REGULAR", "CT_PEAKER"])].groupby("hour")["mw"].sum()
    print(f"[model] CC+CT dispatch on missing tail hours: "
          f"mean {disp.iloc[np.setdiff1d(tail_hours, model_tail)].mean():.0f} MW "
          f"(vs on-model-tail {disp.iloc[both].mean():.0f} MW)" if len(both) else "")


if __name__ == "__main__":
    main()
