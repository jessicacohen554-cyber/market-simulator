#!/usr/bin/env python3
"""closeout-MISO-w3d (ZERO LP): measured EIA-923 Sched 6/7 CHP self-use vs the chp_btm_pct in use.

For every MISO plant the keeper fleet carries in a CHP group (CC_CHP / CT_CHP /
ST_CHP), compare the sector-default/override ``chp_btm_pct`` (the share BOTH the
LP hold-out and the benchmark subtrahend use) with the plant's measured
on-site self-consumption share from EIA-923 Schedules 6/7 ("Annual Source and
Disposition of Electricity for Non-Utility Generators"):

    own_onsite = (gross - station_use) - sales_for_resale - retail - tolling - outgoing
    share      = clip(own_onsite / (gross - station_use), 0, 1)

(the CAISO-w6 definition). First-order grid-energy reach of swapping the share:
dE = class_netgen x (default - measured): positive dE = more grid CHP energy in
the model (and in the bench actual), to be displaced from the marginal classes.
Plants absent from Sched 6/7 (utility-owned) keep the default (dE = 0).

Inputs: f923_<y>.zip Sched 6/7 workbooks (EIA archive; SHA-256 in the output),
the keeper's committed unit_marginal sidecars (plant -> group), EIA-923 page 1.
Reach (``reach`` block, 2019-2025 where Sched 6/7 exists): on the seam-full-span
probe's committed legs (the w3 control), each covered plant's grid tranche is
scaled by (1 - measured)/(1 - default) and dispatched at its own solved hourly
utilisation (first order: the new MW runs like the plant's existing grid MW);
the hourly sum is then walked down the solved stack from the top (highest
offer at or below the hour's marginal offer first -- units dispatched above
it are floor-held and not displaced; imports included; nuclear, hydro and CHP
excluded) to give the
static class displacement and the static marginal-offer move. Static, so the
LP response is smaller (the w3 seam arm realised 0.53 static->LP on price).

Output: results/phase0/miso/_closeout_miso_w3d_chp_selfuse_census.json
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.data.chp import chp_btm_pct, chp_class_netgen_mwh  # noqa: E402

F923_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "f923"
KEEPER = REPO / "results/calibration/closeout_miso_nuc_span/hourly"
OUT = REPO / "results/phase0/miso/_closeout_miso_w3d_chp_selfuse_census.json"
CHP = ("CC_CHP", "CT_CHP", "ST_CHP")
CONTROL = REPO / "results/calibration"  # closeout_miso_w3_<y> legs (seam probe)
NO_WALK = ("nuclear", "hydro")


def reach(year: int, share: dict[tuple[int, str], tuple[float, float]]) -> dict:
    """Static first-order grid reach of measured shares on the control leg ``year``."""
    um = pd.read_parquet(CONTROL / f"closeout_miso_w3_{year}/hourly/unit_marginal_{year}.parquet",
                         columns=["plant_code", "plant_group", "fuel", "hour", "mw", "cap_mw", "mc", "marginal"])
    um["plant_group"] = um.plant_group.astype(str)
    um["fuel"] = um.fuel.astype(str)
    chp = um[um.plant_group.isin(CHP)].copy()
    f = np.array([share.get((int(p), g), (0.0, 0.0)) for p, g in zip(chp.plant_code, chp.plant_group)])
    d, m = f[:, 0], f[:, 1]
    scale = np.where(d < 1.0, (d - m) / np.maximum(1.0 - d, 1e-9), 0.0)
    chp["add"] = chp.mw.to_numpy() * scale  # added grid MW x own utilisation
    add_h = chp.groupby("hour").add.sum()
    add_grp = chp.groupby("plant_group").add.sum() / 1e6
    # Only units offered at or below the hour's marginal offer are displaceable;
    # a unit dispatched above it is held on by a floor / commitment, not by merit.
    price = um[um.marginal == 1].groupby("hour").mc.max()
    um["price"] = um.hour.map(price)
    w = um[~um.plant_group.isin(CHP) & ~um.fuel.isin(NO_WALK) & (um.mw > 0)
           & (um.mc <= um.price + 1e-6)].copy()
    w = w.sort_values(["hour", "mc"], ascending=[True, False])
    w["above"] = w.groupby("hour").mw.cumsum() - w.mw
    w["need"] = w.hour.map(add_h).fillna(0.0).clip(lower=0.0)
    w["cut"] = (w.need - w.above).clip(lower=0.0).clip(upper=w.mw)
    w["left"] = w.mw - w.cut
    cls = (w.groupby("plant_group").cut.sum() / 1e6).round(3)
    marg_old = price
    marg_new = w[w.left > 1e-6].groupby("hour").mc.max()
    dp = (marg_new.reindex(marg_old.index) - marg_old).dropna()
    return {
        "model_grid_chp_add_twh": round(float(add_h.sum() / 1e6), 3),
        "model_grid_chp_add_by_group": add_grp.round(3).to_dict(),
        "displaced_twh_by_class": {k: float(v) for k, v in cls.items() if abs(v) >= 0.005},
        "unabsorbed_twh": round(float((add_h.clip(lower=0) - w.groupby("hour").cut.sum().reindex(add_h.index).fillna(0)).sum() / 1e6), 3),
        "static_marginal_offer_move_mean": round(float(dp.mean()), 2),
    }
COLS = {
    "Plant Code": "plant", "CHP Plant": "chp", "Gross\n Generation": "gross",
    "Station_Use": "station", "Direct_Use": "direct", "Retail Sales": "retail",
    "Sales\n for Resale": "resale", "Tolling\n Agreements": "tolling",
    "Outgoing\n Electricity": "outgoing", "Incoming\n Electricity": "incoming",
}


def load_sd(year: int) -> pd.DataFrame:
    f = glob.glob(str(F923_DIR / f"y{year}" / "*Schedules_6_7*.xlsx"))[0]
    d = pd.read_excel(f, sheet_name=0, header=4)
    d = d.rename(columns=COLS)[list(COLS.values())]
    for c in COLS.values():
        if c not in ("chp",):
            d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0.0)
    d = d.groupby("plant", as_index=False).sum(numeric_only=True)
    net = d.gross - d.station
    own = net - d.resale - d.retail - d.tolling - d.outgoing
    d["net"] = net
    d["share"] = np.where(net > 0, np.clip(own / net.where(net > 0, 1), 0, 1), np.nan)
    return d.set_index("plant")


def main() -> None:
    res = {}
    for y in range(2019, 2025):
        um = pd.read_parquet(KEEPER / f"unit_marginal_{y}.parquet",
                             columns=["plant_code", "plant_group"]).drop_duplicates()
        um = um[um.plant_group.astype(str).isin(CHP)]
        sd = load_sd(y)
        netgen = chp_class_netgen_mwh(y)
        rows = []
        shares = {}
        for pid, grp in zip(um.plant_code.astype(int), um.plant_group.astype(str)):
            e = netgen.get((pid, grp), 0.0)
            default = chp_btm_pct(pid, grp, iso="MISO") / 100.0
            meas = float(sd.share.get(pid, np.nan)) if pid in sd.index else np.nan
            rows.append({"plant": pid, "group": grp, "netgen_twh": e / 1e6,
                         "default": default, "measured": meas,
                         "dE_twh": (e * (default - meas) / 1e6) if not np.isnan(meas) else 0.0})
            if not np.isnan(meas):
                shares[(pid, grp)] = (default, meas)
        df = pd.DataFrame(rows)
        cov = df[~df.measured.isna()]
        by = df.groupby("group").agg(netgen=("netgen_twh", "sum"), dE=("dE_twh", "sum"))
        res[y] = {
            "plants": int(len(df)), "plants_in_sched67": int(len(cov)),
            "netgen_twh_all": round(float(df.netgen_twh.sum()), 3),
            "netgen_twh_covered": round(float(cov.netgen_twh.sum()), 3),
            "btm_twh_default": round(float((df.netgen_twh * df["default"]).sum()), 3),
            "btm_twh_measured_where_covered": round(float(
                (df.netgen_twh * df.measured.fillna(df["default"])).sum()), 3),
            "dE_grid_twh": round(float(df.dE_twh.sum()), 3),
            "by_group": {g: {"netgen": round(r.netgen, 3), "dE": round(r.dE, 3)} for g, r in by.iterrows()},
            "default_shares": sorted({round(v, 3) for v in df["default"]}),
            "top": cov.assign(a=cov.dE_twh.abs()).sort_values("a", ascending=False).head(8)[
                ["plant", "group", "netgen_twh", "default", "measured", "dE_twh"]].round(3).to_dict("records"),
        }
        res[y]["reach"] = reach(y, shares)
        print(y, json.dumps({k: v for k, v in res[y].items() if k != "top"}))
    res["sha256_sched67_xlsx"] = {p.parent.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(F923_DIR.glob("y*/*Schedules_6_7*.xlsx"))}
    OUT.write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
