"""NYISO 2023 energy-price LEVEL residual diagnostic (nyiso-70 handoff).

Localizes the C3a +15.9% 2023 over-pricing: is it broad (gas-basis passthrough
or offer markup) or concentrated (specific months/zones = congestion/import)?
Reads the keeper's committed system_2023 sidecar — NO re-solve.
"""
import gzip
import json

import numpy as np
import pandas as pd

BUNDLE = "results/calibration/nyiso70_scr_edrp_reserve"
LOAD_ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
HOURS_PER_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # 2023 non-leap


def _month_of_hour():
    return np.repeat(np.arange(1, 13), [h * 24 for h in HOURS_PER_MONTH])


def lw(g):
    return float(np.average(g["price"], weights=g["demand"]))


def main():
    df = pd.read_parquet(f"{BUNDLE}/hourly/system_2023.parquet")
    m = df[df.zone.isin(LOAD_ZONES)].copy()
    moh = _month_of_hour()
    m["month"] = m["hour"].map(lambda h: moh[h])

    with gzip.open("frontend/data/backcast/bench/NYISO/2023.json.gz") as f:
        avg = json.load(f)["bench"]["avgLMP"]
    act_mon = np.array(avg["rt_lw_mon"])
    act_sys = avg["rt_lw"]

    # --- monthly ---
    model_mon = m.groupby("month").apply(lw, include_groups=False)
    model_sys = float(np.average(m["price"], weights=m["demand"]))
    print("=== MONTHLY load-weighted mean LMP (model vs actual RT) ===")
    print(f"{'Mo':>3} {'model':>7} {'actual':>7} {'diff':>7} {'pct':>7}")
    for mo in range(1, 13):
        md, ad = model_mon[mo], act_mon[mo - 1]
        print(f"{mo:>3} {md:>7.2f} {ad:>7.2f} {md - ad:>+7.2f} {(md / ad - 1) * 100:>+6.1f}%")
    print(f"SYS {model_sys:>7.2f} {act_sys:>7.2f} {model_sys - act_sys:>+7.2f} "
          f"{(model_sys / act_sys - 1) * 100:>+6.1f}%")

    # --- per-zone (system) ---
    print("\n=== PER-ZONE load-weighted mean LMP (model) ===")
    zmodel = m.groupby("zone").apply(lw, include_groups=False)
    for z in LOAD_ZONES:
        print(f"{z:>16} {zmodel[z]:>7.2f}")

    # --- price distribution: where does the excess $ live? ---
    print("\n=== PRICE BUCKET share of hours (model, system simple mean across zones) ===")
    sys_hourly = m.groupby("hour").apply(lambda g: np.average(g["price"], weights=g["demand"]),
                                         include_groups=False)
    for lo, hi in [(-1e9, 0), (0, 20), (20, 30), (30, 40), (40, 60), (60, 100), (100, 1e9)]:
        n = int(((sys_hourly >= lo) & (sys_hourly < hi)).sum())
        print(f"  [{lo:>6.0f},{hi:>6.0f}) : {n:>5} h ({n / len(sys_hourly) * 100:>4.1f}%)")
    print(f"  model system simple-mean hourly price: {sys_hourly.mean():.2f}")


if __name__ == "__main__":
    main()
