"""SPP-93 (zero LP): the PRECOMMIT §1.4 measured-price admissibility test for the West/East partition.

ACTUAL prices only: never model output. Same construction as ``_spp92_bubble_spread.py``:
- area price = mean RTBM LMP over the area's LOAD settlement locations;
- bubble price = areas weighted by annual EIA-930 sub-BA energy;
- clock = GMT HE - 7 h.
Only the partition differs.

    P-WE (primary): West = RZ {1,2,3,5} sub-BAs, East = RZ 4 (PRECOMMIT §1.2)
    P3 (information only): NW = RZ {1,5}, SW = RZ {2,3}, E = RZ 4
    N/S (the keeper's): for A2's comparison

A1: mean(E - W) > 0 in every year 2019-2025.
A2: mean |E - W| > mean |S - N| in >= 5 of 7 years.
Input: the load-SL parquet from ``_spp92_load_lmp_fetch.py`` (argv[1]). Output: argv[2] (json); optional argv[3] = a dir for the hourly bubble parquets (the ψ rating's spread).
Record: docs/records/spp/PRECOMMIT-spp-93-west-east-2026-09-27.md.
"""
import glob
import json
import sys

import numpy as np
import pandas as pd

ROOT = "/home/user/market-simulator"
NORTH = {"EDE", "INDN", "KACY", "KCPL", "LES", "MPS", "NPPD", "OPPD", "SECI", "SPRM", "WAUE", "WR"}
SOUTH = {"CSWS", "GRDA", "OKGE", "SPS", "WFEC"}
WEST = {"LES", "NPPD", "OPPD", "SECI", "SPS", "WAUE"}
EAST = (NORTH | SOUTH) - WEST
P3 = {"NW": {"LES", "NPPD", "OPPD", "WAUE"}, "SW": {"SECI", "SPS"}, "E": EAST}


def model_hoy(ts):
    """Model hour-of-year (Feb-29 dropped) and year from a timestamp series."""
    doy = ts.dt.dayofyear.values.copy()
    leap = ts.dt.is_leap_year.values
    feb29 = leap & (ts.dt.month.values == 2) & (ts.dt.day.values == 29)
    doy = np.where(leap & (doy > 59), doy - 1, doy)
    return np.where(feb29, -1, (doy - 1) * 24 + ts.dt.hour.values), ts.dt.year.values


def main():
    """Compute A1/A2 and the P3 information rows; write JSON."""
    L = pd.read_parquet(sys.argv[1])
    sl = pd.read_csv(f"{ROOT}/data/raw/spp-planning/SL_to_Pnode_to_Zone_with_Area.csv", dtype=str,
                     usecols=["SETLOCNAME", "SETLOCTYPE", "NODE_AREA"]).drop_duplicates("SETLOCNAME")
    L["area"] = L["loc"].map(dict(zip(sl.SETLOCNAME, sl.NODE_AREA)))
    ts = pd.to_datetime(L["date"]).dt.normalize() + pd.to_timedelta(L["he"] - 7, unit="h")
    L["hour"], L["year"] = model_hoy(ts)
    L = L[(L.hour >= 0) & L.year.between(2019, 2025)]
    A = L.groupby(["year", "hour", "area"])["value"].mean().unstack("area")
    dem = pd.concat([pd.read_csv(f) for f in glob.glob(f"{ROOT}/data/raw/zone-specific-demand/SPP/spp_subba_demand_*.csv")])
    dem["year"] = dem.period.str[:4].astype(int)
    W = dem.groupby(["year", "subba"])["value"].sum().unstack("subba")
    out = {}
    for y in range(2019, 2026):
        a = A.loc[y].reindex(range(8760))

        def bubble(S):
            cols = [c for c in S if c in a.columns]
            w = W.loc[y, cols].astype(float)
            v = a[cols]
            m = v.notna()
            return (v.fillna(0) * w.values).sum(axis=1) / (m * w.values).sum(axis=1)

        b = pd.DataFrame({"N": bubble(NORTH), "S": bubble(SOUTH), "W": bubble(WEST), "E": bubble(EAST),
                          **{f"P3_{k}": bubble(v) for k, v in P3.items()}}).dropna()
        EW, SN = b.E - b.W, b.S - b.N
        if len(sys.argv) > 3:
            b.assign(hour=b.index, year=y).to_parquet(f"{sys.argv[3]}/we_hourly_{y}.parquet")
        share_W = float(W.loc[y, list(WEST)].sum() / W.loc[y, list(NORTH | SOUTH)].sum())
        out[y] = {
            "n_hours": len(b), "west_load_share": round(share_W, 4),
            "mean_EminusW": round(float(EW.mean()), 2), "mean_abs_EminusW": round(float(EW.abs().mean()), 2),
            "mean_SminusN": round(float(SN.mean()), 2), "mean_abs_SminusN": round(float(SN.abs().mean()), 2),
            "hours_E_dearer_ge5": int((EW >= 5).sum()), "hours_W_dearer_ge5": int((EW <= -5).sum()),
            "share_hours_EW_positive": round(float((EW > 0).mean()), 3),
            "A1_pass": bool(EW.mean() > 0), "A2_year_pass": bool(EW.abs().mean() > SN.abs().mean()),
            "info_P3_mean_E_minus_NW": round(float((b.P3_E - b.P3_NW).mean()), 2),
            "info_P3_mean_E_minus_SW": round(float((b.P3_E - b.P3_SW).mean()), 2),
            "info_P3_mean_abs_NW_minus_SW": round(float((b.P3_NW - b.P3_SW).abs().mean()), 2),
        }
    verdict = {"A1": all(r["A1_pass"] for r in out.values()),
               "A2_years": sum(r["A2_year_pass"] for r in out.values()),
               "A2": sum(r["A2_year_pass"] for r in out.values()) >= 5}
    json.dump({"years": out, "verdict": verdict}, open(sys.argv[2], "w"), indent=1)
    print(pd.DataFrame(out).to_string())
    print(verdict)


if __name__ == "__main__":
    main()
