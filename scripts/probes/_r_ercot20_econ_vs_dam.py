"""R-ERCOT-20 Task 2 (zero LP): CC_REGULAR model offer vs the 60-Day DAM curve at the same MW point.

Question (handoff Task 2): why do high-HR CCs' ``econ*`` tranches clear so often?
Is there a measured, heat-rate-dependent discrepancy between the model's econ
offer and the plant's real DAM energy offer at the same loading point?

Model side: the keeper's own year leg (``unit_hourly_<Y>.parquet``: per tranche
``cap_mw`` and ``mc``), per plant-month: tranches sorted by mc, the offer price at
loading fraction f of plant capacity. Actual side: 60-Day DAM Gen Resource Data
(CCGT90/CCLE90 configurations of the plant's DAM sites, via
``data/raw/reference/ercot-dam-plant-crosswalk.csv``), per hour with the plant
ON: the configurations' step curves summed, the price at f of the online HSL
(self-schedule points <= -249 excluded); monthly median. Heat rate = EIA-923
NG ``elec_fuel_mmbtu / net_generation_mwh`` for the plant-year.

Reported per HR cohort and f: model − DAM ($/MWh), and the same after removing
each month's fleet median on each side (the level-free, HR-relative test).
Solves nothing. Usage: python _r_ercot20_econ_vs_dam.py <Y>:<unit_hourly path> ...
"""

from __future__ import annotations

import glob
import json
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from market_sim.config.paths import RAW_DATA_DIR

FRACS = (0.4, 0.6, 0.8, 0.95)
MW = [f"QSE submitted Curve-MW{i}" for i in range(1, 11)]
PR = [f"QSE submitted Curve-Price{i}" for i in range(1, 11)]
ON = {"ON", "ONRUC", "ONREG", "ONOPTOUT", "ONEMR", "ONRR", "ONDSR", "ONDSRREG", "FRRSUP"}
HR_BINS = [0, 7.0, 7.5, 8.0, 9.0, 99]
# DIAGNOSTIC-ONLY site identifications (name- and QSE-evident, NOT accepted into
# ercot-dam-plant-crosswalk.csv): the high-HR CCs the accepted crosswalk misses.
# Only the plants' CC configurations; their simple-cycle GT sites are excluded.
EXTRA_SITES = {"THW_CC1": 3469, "THW_CC2": 3469, "SANDHSYD_CC1": 7900,
               "B_DAVIS_CC1": 4939, "RAYBURN_CC1": 3631, "SILASRAY_CC1": 3559}


def heat_rates(year: int) -> pd.Series:
    """EIA-923 NG plant heat rate (MMBtu/MWh), plants with >= 0.05 TWh."""
    g = pd.read_csv(RAW_DATA_DIR / "eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv")
    g = g[(g.year == year) & (g.fuel_type == "NG") & (g.plant_state == "TX")]
    a = g.groupby("plant_id")[["elec_fuel_mmbtu", "net_generation_mwh"]].sum()
    a = a[a.net_generation_mwh >= 5e4]
    return (a.elec_fuel_mmbtu / a.net_generation_mwh).rename("hr")


def model_curve(path: str, year: int) -> pd.DataFrame:
    """Per plant-month offer price at each f from the model's CC_REGULAR tranches."""
    u = pd.read_parquet(path, columns=["unit_id", "plant_group", "hour", "cap_mw", "mc"],
                        filters=[("plant_group", "=", "CC_REGULAR")])
    u["plant"] = u.unit_id.astype(str).str.extract(r"_p(\d+)_")[0].astype(int)
    u["tr"] = u.unit_id.astype(str).str.rsplit("_", n=1).str[-1]
    u["month"] = (pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(u.hour, unit="h")).dt.month
    m = u.groupby(["plant", "month", "tr"]).agg(cap=("cap_mw", "mean"), mc=("mc", "mean")).reset_index()
    rows = []
    for (p, mo), g in m.groupby(["plant", "month"]):
        g = g.sort_values("mc")
        cum = g.cap.cumsum() / g.cap.sum()
        for f in FRACS:
            i = int(np.searchsorted(cum.to_numpy(), f))
            i = min(i, len(g) - 1)
            rows.append({"plant": p, "month": mo, "f": f, "model": g.mc.iloc[i], "model_tr": g.tr.iloc[i]})
    return pd.DataFrame(rows)


def dam_curve(year: int) -> pd.DataFrame:
    """Per plant-month median DAM offer price at each f of online HSL."""
    xw = pd.read_csv(RAW_DATA_DIR / "reference/ercot-dam-plant-crosswalk.csv")
    xw = xw[(xw["class"] == "CC_REGULAR") & (xw.accepted == 1)]
    site2plant = dict(zip(xw.site, xw.plant_code))
    site2plant.update(EXTRA_SITES)
    fs = sorted(glob.glob(str(RAW_DATA_DIR / f"ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_{year}_*.parquet")))
    cols = ["Delivery Date", "Hour Ending", "Resource Name", "Resource Type", "HSL", "Resource Status"] + MW + PR
    d = pd.concat([pq.read_table(f, columns=cols, filters=[("Resource Type", "in", ["CCGT90", "CCLE90"])]).to_pandas()
                   for f in fs], ignore_index=True)
    d = d.drop_duplicates(["Delivery Date", "Hour Ending", "Resource Name"])
    d["site"] = d["Resource Name"].str.replace(r"_\d+$", "", regex=True)
    d["plant"] = d.site.map(site2plant)
    d = d[d.plant.notna() & d["Resource Status"].isin(ON)]
    d["date"] = pd.to_datetime(d["Delivery Date"], format="%m/%d/%Y")
    d = d[d.date.dt.year == year]
    d["month"] = d.date.dt.month
    rows = []
    for (p, dt, he), g in d.groupby(["plant", "Delivery Date", "Hour Ending"], sort=False):
        M = np.nan_to_num(g[MW].to_numpy(float))
        P = g[PR].to_numpy(float)
        hsl = float(np.nansum(g.HSL.to_numpy(float)))
        if hsl <= 0 or not np.isfinite(P).any():
            continue
        inc = np.clip(M - np.concatenate([np.zeros((len(M), 1)), M[:, :-1]], axis=1), 0, None)
        ok = np.isfinite(P) & (inc > 0)
        pr, w = P[ok], inc[ok]
        o = np.argsort(pr)
        pr, cw = pr[o], np.cumsum(w[o])
        for f in FRACS:
            i = int(np.searchsorted(cw, f * hsl))
            if i >= len(pr):
                continue  # curve never reaches f x HSL: that MW is not offered
            if pr[i] <= -249:
                continue
            rows.append((int(p), int(g.month.iloc[0]), f, pr[i]))
    r = pd.DataFrame(rows, columns=["plant", "month", "f", "dam"])
    return r.groupby(["plant", "month", "f"]).dam.median().reset_index()


def main(args: list[str]) -> None:
    """Print cohort tables and write the JSON record."""
    rec: dict = {}
    for a in args:
        y, path = a.split(":", 1)
        y = int(y)
        mc = model_curve(path, y)
        dm = dam_curve(y)
        hr = heat_rates(y)
        j = mc.merge(dm, on=["plant", "month", "f"]).merge(hr, left_on="plant", right_index=True)
        j["diff"] = j.model - j.dam
        for side in ("model", "dam"):
            j[f"{side}_rel"] = j[side] - j.groupby(["month", "f"])[side].transform("median")
        j["rel_diff"] = j.model_rel - j.dam_rel
        j["cohort"] = pd.cut(j.hr, HR_BINS)
        t = j.groupby(["f", "cohort"], observed=True).agg(
            plants=("plant", "nunique"), model=("model", "mean"), dam=("dam", "mean"),
            diff=("diff", "mean"), rel_diff=("rel_diff", "mean")).round(2)
        corr = j.groupby("f").apply(lambda x: pd.Series({
            "corr_hr_diff": x.hr.corr(x["diff"]), "corr_hr_rel_diff": x.hr.corr(x.rel_diff),
            "corr_hr_model_rel": x.hr.corr(x.model_rel), "corr_hr_dam_rel": x.hr.corr(x.dam_rel)})).round(3)
        trm = j.groupby("f").model_tr.agg(lambda s: s.value_counts(normalize=True).round(2).to_dict())
        print(f"\n===== {y}: {j.plant.nunique()} matched CC_REGULAR plants")
        print(t.to_string())
        print(corr.to_string())
        print(trm.to_string())
        rec[str(y)] = {"plants": int(j.plant.nunique()),
                       "by_f_cohort": {f"{k[0]}|{k[1]}": v for k, v in t.to_dict(orient="index").items()},
                       "corr": json.loads(corr.to_json(orient="index")),
                       "model_tranche_at_f": {str(k): v for k, v in trm.items()}}
    with open("docs/records/ercot/r-ercot/r_ercot20_econ_vs_dam.json", "w") as f:
        json.dump(rec, f, indent=1, default=str)


if __name__ == "__main__":
    main(sys.argv[1:])
