"""ERCOT-81 leg 1: August-2023 under-formation anatomy on a solved probe bundle.

Reads a probe bundle's P1 system parquet, builds the demand-weighted system
price, and decomposes the ACTUAL >$200 RT hours (the 181-hour 2023 set; 100 in
August) by how the model priced them: energy dual vs overlay/adder, against the
measured NP6-905 reserves (RTOLCAP) and actual RT/DA. Also reports monthly
means (model vs actual) and tail counts, so a single-delta B probe can be read
against the A leg without the dashboard pipeline.

Usage::

    uv run python scripts/probes/_ercot81_aug_anatomy.py \
        results/calibration/_ercot81_keeper_2023 [--year 2023]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ACTUAL = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--over", type=float, default=200.0)
    args = ap.parse_args()
    bundle = Path(args.bundle)
    yr = args.year

    sysf = None
    for cand in (f"system_{yr}.parquet", "system.parquet"):
        p = bundle / cand
        if p.exists():
            sysf = pd.read_parquet(p)
            break
    if sysf is None:
        cands = sorted(bundle.glob("**/system*.parquet"))
        if not cands:
            raise SystemExit(f"no system parquet under {bundle}")
        sysf = pd.concat([pd.read_parquet(c) for c in cands], ignore_index=True)
    if "year" in sysf.columns:
        sysf = sysf[sysf["year"] == yr]
    if "pass" in sysf.columns and (sysf["pass"] == "P1").any():
        sysf = sysf[sysf["pass"] == "P1"]

    # Demand-weighted system price per hour (the payload-lw construction).
    g = sysf.groupby("hour")
    dw = g.apply(
        lambda d: float(np.average(d["price"], weights=np.maximum(d["demand"], 1e-9))),
        include_groups=False,
    )
    price = dw.sort_index().to_numpy()
    T = price.size
    cols = {}
    for c in ("ordc_adder", "rtordpa_overlay", "dam_as_overlay", "reserve_price"):
        if c in sysf.columns:
            cols[c] = g[c].first().sort_index().to_numpy()

    act = pd.read_parquet(ACTUAL)
    act = act[act["year"] == yr].reset_index(drop=True)
    rt = act["rt"].to_numpy()[:T]
    da = act["da"].to_numpy()[:T]
    res_p = REPO / "data" / "raw" / "ercot" / f"ercot_{yr}_ordc_reserves_hourly.parquet"
    res = pd.read_parquet(res_p) if res_p.exists() else None

    ts = pd.date_range(f"{yr}-01-01", periods=T, freq="h")
    month = ts.month.to_numpy()
    df = pd.DataFrame(
        {
            "model": price[:T],
            "rt": rt,
            "da": da,
            "month": month,
            "hod": ts.hour.to_numpy(),
        }
    )
    for c, v in cols.items():
        df[c] = v[:T]
    if res is not None:
        df["rtolcap"] = res["rtolcap"].to_numpy()[:T]
        df["lam_act"] = res["system_lambda"].to_numpy()[:T]

    print(f"== {bundle.name} year {yr} ==")
    m = df.groupby("month")[["model", "rt", "da"]].mean().round(1)
    m["resid"] = (m["model"] - m["rt"]).round(1)
    print(m.to_string())
    print(
        f"\nannual mean: model {df.model.mean():.2f} rt {df.rt.mean():.2f} "
        f"da {df.da.mean():.2f}"
    )
    for thr in (200.0, 500.0, 1000.0):
        print(
            f"hours >${thr:.0f}: actual {(df.rt > thr).sum():3d}  "
            f"model {(df.model > thr).sum():3d}"
        )

    sc = df[df.rt > args.over]
    print(f"\n== actual >${args.over:.0f} hours: {len(sc)} ==")
    for mo, d in sc.groupby("month"):
        line = (
            f"month {mo:2d}: n={len(d):3d}  actual rt p50 ${d.rt.median():7.0f} "
            f"| model p10/p50/p90 ${np.percentile(d.model, 10):7.0f} "
            f"${np.percentile(d.model, 50):7.0f} ${np.percentile(d.model, 90):7.0f}"
        )
        if "rtolcap" in d:
            line += f" | meas RTOLCAP p50 {d.rtolcap.median():6.0f}"
        if "ordc_adder" in d:
            line += f" | adder p50 ${d.ordc_adder.median():6.1f}"
        print(line)
    # Bands of the miss (Aug focus): where does the model sit when reality
    # printed each band?
    aug = sc[sc.month == 8]
    if len(aug):
        print(f"\n== august miss bands (n={len(aug)}) ==")
        for lo, hi in ((200, 500), (500, 1000), (1000, 3000), (3000, 6000)):
            d = aug[(aug.rt > lo) & (aug.rt <= hi)]
            if not len(d):
                continue
            line = (
                f"actual (${lo},{hi}]: n={len(d):3d}  model p50 "
                f"${d.model.median():7.0f}  mean ${d.model.mean():7.0f}"
            )
            if "rtolcap" in d:
                line += f"  meas RTOLCAP p50 {d.rtolcap.median():6.0f}"
            print(line)
    # False-positive check: model-scarce hours reality was not.
    fp = df[(df.model > args.over) & (df.rt <= args.over)]
    print(f"\nmodel >${args.over:.0f} where actual was not: {len(fp)} hours")
    if len(fp):
        print(
            fp.groupby("month")["model"].agg(["count", "median"]).round(0).to_string()
        )


if __name__ == "__main__":
    main()
