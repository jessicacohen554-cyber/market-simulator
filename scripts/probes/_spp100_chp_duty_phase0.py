"""SPP-100 phase 0 (zero LP): would ``chp_steam_duty_window`` clear Lake Road's D-4 row?

SPP-75 armed ``chp_steam_floor_p25`` alone and the owner declined it ("Don't
promote", 2026-09-24) because the swap held Lake Road (MO) 2098 ST_CHP at a
24/7 trickle while its CAMPD meter read zero in 78-97 % of hours: a new rule-17
D-4 unit-conduct FAIL in every year. The cell ``chp_steam_following`` was set R
with one re-open route: the swap scoped away from cyclers. ``chp_steam_duty_window``
(caiso-293, on main, default off, zero DOF) is that scope: the floor is held at the
undiluted ``median_cf`` only in the top ``on_frac`` share of live hours by the
shared commitment-window series (system load; SPP's keeper leaves
``commitment_floor_window_netload`` off).

This probe replays that window placement on the keeper's committed demand
(``spp99_remap_span/hourly/system_<y>.parquet``) and scores Lake Road's own CAMPD
meter inside it with D-4's own threshold-free test (median measured MW over the
floor's hours == 0 -> FAIL). The floor binds in a SUBSET of the window (where the
LP would not otherwise run the unit), so the probe reports the whole window and a
pessimistic subset: the window's lowest-load half. It also reports Eastman 55176
and Black Hawk 55064, the two hosts the swap exists for.

Run: ``python scripts/probes/_spp100_chp_duty_phase0.py``. No solve, no write
outside stdout.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.data.fleet.campd_bins import thermal_tranche_chp_steam_duty

BUNDLE = "results/calibration/spp99_remap_span/hourly"
PLANTS = {
    2098: ("MO", "Lake Road"),
    55176: ("TX", "Eastman"),
    55064: ("TX", "Black Hawk"),
}
YEARS = range(2019, 2026)


def plant_hourly(state: str, oris: int, year: int, n: int) -> np.ndarray:
    """Return the plant's CAMPD gross load (MW) on an hour-of-year index, zeros filled."""
    d = pd.read_parquet(
        f"data/raw/campd-unit-level/{state}_{year}.parquet",
        columns=["facilityId", "date", "hour", "grossLoad"],
    )
    d = d[d.facilityId.astype(int) == oris]
    ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    how = ((ts - pd.Timestamp(year, 1, 1)) / pd.Timedelta(hours=1)).astype(int)
    s = d.assign(h=how.values).groupby("h").grossLoad.sum()
    out = np.zeros(n)
    s = s[(s.index >= 0) & (s.index < n)]
    out[s.index.values] = s.fillna(0).values
    return out


def main() -> None:
    """Print the per-plant, per-year window census."""
    duty = thermal_tranche_chp_steam_duty("SPP")
    print("artifact (on_frac, level_on_cf):", {k: duty[k] for k in duty})
    for oris, (st, name) in PLANTS.items():
        key = [k for k in duty if k[0] == oris][0]
        on_frac, lvl = duty[key]
        print(f"\n{name} {oris} {key[1]} on_frac={on_frac:.4f} level_on={lvl:.1f}%")
        print(
            "year  n   k   meas_on%  win_med_MW  win_zero%  lowhalf_med  lowhalf_zero%  verdict(whole/low)"
        )
        for y in YEARS:
            s = pd.read_parquet(f"{BUNDLE}/system_{y}.parquet")
            s = s[s["pass"] == "P1"]
            load = s.groupby("hour").demand.sum().sort_index().values
            n = load.size
            meas = plant_hourly(st, oris, y, n)
            k = int(round(on_frac * n))
            win = np.argsort(-load, kind="stable")[:k]
            low = win[k // 2 :]
            wm, wz = np.median(meas[win]), (meas[win] <= 0).mean()
            lm, lz = np.median(meas[low]), (meas[low] <= 0).mean()
            v = ("FAIL" if wm <= 0 else "pass") + "/" + ("FAIL" if lm <= 0 else "pass")
            print(
                f"{y} {n} {k:5d} {100 * (meas > 0).mean():7.1f} {wm:10.1f} {100 * wz:9.1f} "
                f"{lm:11.1f} {100 * lz:12.1f}  {v}"
            )


if __name__ == "__main__":
    main()
