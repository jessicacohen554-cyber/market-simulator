"""SPP-93 census stage 2 and pre-solve legs C-0 to C-3 (ZERO LP). PRECOMMIT-spp-93 §3, §4.1.

Reads ``census_<y>.npz`` (the keeper, N/S) and ``census_we_<y>.npz`` (the keeper recipe with
``spp_zone_partition='west_east'``), both written by ``_spp93_census_dump.py``.

Reports, per bubble and year:
- the census rows: plants, units, thermal MW by class, wind/solar MW and TWh, demand TWh and min–max MW,
  and net position;
- C-0: the two fleets are the same units (identical pmax and availability; only the zone moves), and
  every unit sits in a valid bubble;
- C-1/C-2: the wind identity Σ_z cap·cf(t) equals the N/S total in every hour, and cf ≤ 1;
- C-3: hours with min_z W/E margin < 0 while min_z N/S margin ≥ 0, keeper-slack hours exempt.
  margin_z = available thermal+hydro + wind + solar + link TTC − demand_z.

Usage: ``python scripts/probes/_spp93_census.py <census dir> <out dir>``
"""
import json
import sys

import numpy as np
import pandas as pd

ROOT = "/home/user/market-simulator"
NS_TTC, WE_TTC = 3400.0, 4000.0
WINDOW = range(8496, 8520)


def fam(uid: str) -> str:
    """Class family from an LP unit id."""
    u = uid.upper()
    if u.endswith("_HYDRO"):
        return "hydro"
    for k in ("COAL", "CC_", "CT_", "ST_", "NUC"):
        if u.startswith(k):
            return {"CC_": "gas_cc", "CT_": "gas_ct", "ST_": "gas_st", "NUC": "nuclear"}.get(k, "coal")
    return "other"


def margins(d, ttc):
    """Per-zone hourly availability-net margin, (n_zones, 8760)."""
    zi = d["zone_idx"].astype(int)
    cap = d["pmax"][:, None] * d["avail"].astype(float)
    nz = d["demand"].shape[0]
    th = np.vstack([cap[zi == z].sum(0) for z in range(nz)])
    w = d["wind_cf"] * d["wind_cap"][:, None]
    s = d["solar_cf"] * d["solar_cap"][:, None]
    return th + w + s + ttc - d["demand"], th, w, s


def main():
    """Run the census and the pre-solve legs for 2019-2025."""
    src, out = sys.argv[1], sys.argv[2]
    rows, legs = [], {}
    for y in range(2019, 2026):
        b = np.load(f"{src}/census_{y}.npz", allow_pickle=True)
        e = np.load(f"{src}/census_we_{y}.npz", allow_pickle=True)
        zones = [str(z) for z in e["zones"]]
        c0_same_units = bool(np.array_equal(b["codes"], e["codes"]) and np.allclose(b["pmax"], e["pmax"])
                             and np.allclose(b["avail"], e["avail"]))
        c0_zones_ok = zones == ["SPP-West", "SPP-East"] and set(e["zone_idx"].astype(int)) <= {0, 1}
        wb = (b["wind_cf"] * b["wind_cap"][:, None]).sum(0)
        we = (e["wind_cf"] * e["wind_cap"][:, None]).sum(0)
        c1 = float(np.max(np.abs(we - wb) / np.maximum(wb, 1e-9)))
        sb = (b["solar_cf"] * b["solar_cap"][:, None]).sum(0)
        se = (e["solar_cf"] * e["solar_cap"][:, None]).sum(0)
        c1s = float(np.max(np.abs(se - sb) / np.maximum(sb, 1.0)))
        c2 = float(e["wind_cf"].max())
        dem_rel = float(np.max(np.abs(e["demand"].sum(0) - b["demand"].sum(0)) / b["demand"].sum(0)))
        mb, *_ = margins(b, NS_TTC)
        me, th, w, s = margins(e, WE_TTC)
        k = pd.read_parquet(f"{ROOT}/results/calibration/spp86_arm_span/hourly/system_{y}.parquet").query("`pass`=='P1'")
        slack_h = set(k.loc[k.slack > 1e-6, "hour"].astype(int))
        new_neg = [h for h in range(8760) if me[:, h].min() < 0 and mb[:, h].min() >= 0 and h not in slack_h]
        legs[y] = {"C0_same_units": c0_same_units, "C0_zones_ok": bool(c0_zones_ok), "C1_wind_max_rel": c1,
                   "C1_solar_max_rel": c1s, "C2_max_cf": c2, "demand_total_max_rel": dem_rel,
                   "C3_new_negative_hours": new_neg, "keeper_slack_hours": sorted(slack_h),
                   "min_margin_we": float(me.min()), "min_margin_ns": float(mb.min()),
                   "window_min_margin_we": float(me[:, WINDOW].min()), "window_min_margin_ns": float(mb[:, WINDOW].min())}
        zi = e["zone_idx"].astype(int)
        uid = e["unit_ids"]
        for z, zn in enumerate(zones):
            m = zi == z
            r = {"year": y, "zone": zn, "plants": int(len(set(e["codes"][m]))), "units": int(m.sum())}
            for f in ("coal", "gas_cc", "gas_ct", "gas_st", "nuclear", "hydro", "other"):
                r[f"{f}_mw"] = round(float(e["pmax"][m][[fam(u) == f for u in uid[m]]].sum()), 1)
            r["thermal_hydro_mw"] = round(float(e["pmax"][m].sum()), 1)
            r["wind_mw"] = round(float(e["wind_cap"][z]), 1)
            r["wind_twh"] = round(float(w[z].sum() / 1e6), 2)
            r["solar_mw"] = round(float(e["solar_cap"][z]), 1)
            r["solar_twh"] = round(float(s[z].sum() / 1e6), 2)
            r["demand_twh"] = round(float(e["demand"][z].sum() / 1e6), 2)
            r["demand_min_mw"] = round(float(e["demand"][z].min()))
            r["demand_max_mw"] = round(float(e["demand"][z].max()))
            r["net_position_twh"] = round(float((th[z] + w[z] + s[z] - e["demand"][z]).sum() / 1e6), 1)
            rows.append(r)
    C = pd.DataFrame(rows)
    C.to_csv(f"{out}/census.csv", index=False)
    verdict = {
        "C0": all(v["C0_same_units"] and v["C0_zones_ok"] for v in legs.values()),
        "C1": all(v["C1_wind_max_rel"] <= 1e-9 for v in legs.values()),
        "C2": all(v["C2_max_cf"] <= 1.0 + 1e-12 for v in legs.values()),
        "C3": all(not v["C3_new_negative_hours"] for v in legs.values()),
    }
    json.dump({"legs": {str(k): v for k, v in legs.items()}, "verdict": verdict}, open(f"{out}/presolve_legs.json", "w"), indent=1)
    pd.set_option("display.width", 250)
    print(C.to_string(index=False))
    for y, v in legs.items():
        print(y, {k: (v[k] if not isinstance(v[k], list) else len(v[k])) for k in v})
    print(verdict)


if __name__ == "__main__":
    main()
