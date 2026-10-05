#!/usr/bin/env python3
"""closeout-MISO-w3f (ZERO LP): why the measured-carve CHP grid tranche under-dispatches.

On the w3e arm legs (miso_chp_btm_measured on the seam-full-span probe):

1. COMMITMENT CENSUS: per MISO CHP plant (CC_CHP / CT_CHP / ST_CHP), CAMPD CEMS
   online fraction and starts per year vs the model's committed tranche online
   fraction and starts (online = > 5 % of the series max).
2. MARKUP INVERSION: the committed tranche's P1 offer minus the econ-low
   tranche's (same plant, same hour) -- the monthly startup-amortization
   markup (model/commitment.compute_monthly_markup) that
   ``chp_startup_covered`` exempts CHP from.
3. STATIC REACH of pricing the committed tranche at its econ-low offer:
   committed headroom in hours where the plant's econ-low tranche is at cap
   (so the committed band, not the price, is what stops it), walked down the
   solved stack at or below the hour's marginal offer (the w3d walk).

Output: results/phase0/miso/_closeout_miso_w3f_chp_dispatch_phase0.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "src"), str(REPO), str(REPO / "scripts")]

import scripts.run_calibration_full as rcf  # noqa: E402

OUT = REPO / "results/phase0/miso/_closeout_miso_w3f_chp_dispatch_phase0.json"
ARM = REPO / "results/calibration"  # closeout_miso_w3e_<y> legs
CHP = ("CC_CHP", "CT_CHP", "ST_CHP")
NO_WALK = ("nuclear", "hydro")


def _runs(on: np.ndarray) -> list[int]:
    """Lengths of the True runs in a boolean series."""
    d = np.diff(np.concatenate([[0], on.astype(int), [0]]))
    return list(np.flatnonzero(d == -1) - np.flatnonzero(d == 1))


def census(y: int, um: pd.DataFrame, campd: pd.DataFrame) -> list[dict]:
    """CEMS vs model commitment per CHP plant (plants with CEMS output)."""
    rows = []
    com = um[um.band == "committed"]
    for pid, u in com.groupby("plant_code"):
        c = (
            campd[campd.plant_id == pid]
            .groupby("hour")
            .net_mw.sum()
            .reindex(range(8760), fill_value=0.0)
            .to_numpy()
        )
        if c.max() <= 0:
            continue
        on = c > 0.05 * c.max()
        g = (
            u.groupby("hour")
            .agg(mw=("mw", "sum"), cap=("cap_mw", "sum"))
            .reindex(range(8760), fill_value=0.0)
        )
        mon = (g.mw > 0.05 * max(g.cap.max(), 1e-9)).to_numpy()
        rows.append(
            {
                "plant": int(pid),
                "group": str(u.plant_group.iloc[0]),
                "cems_twh": round(c.sum() / 1e6, 3),
                "cems_on": round(float(on.mean()), 3),
                "cems_starts": len(_runs(on)),
                "model_on": round(float(mon.mean()), 3),
                "model_starts": len(_runs(mon)),
            }
        )
    return rows


def reach(um_all: pd.DataFrame, um: pd.DataFrame) -> dict:
    """Static gain of committed-at-econ pricing and its stack-walk displacement."""
    com = um[um.band == "committed"].set_index(["plant_code", "hour"])
    lo = (
        um[um.band == "econlo"]
        .set_index(["plant_code", "hour"])[["mw", "cap_mw", "mc"]]
        .add_suffix("_lo")
    )
    j = com.join(lo, how="inner")
    bind = (
        (j.mw_lo >= 0.98 * j.cap_mw_lo)
        & (j.mw < 0.98 * j.cap_mw)
        & (j.mc > j.mc_lo + 0.5)
    )
    add = ((j.cap_mw - j.mw) * bind).rename("add")
    add_h = add.groupby(level="hour").sum()
    by_group = (add.groupby(j.plant_group.astype(str)).sum() / 1e6).round(3).to_dict()
    price = um_all[um_all.marginal == 1].groupby("hour").mc.max()
    w = um_all.assign(price=um_all.hour.map(price))
    w = w[
        ~w.plant_group.astype(str).isin(CHP)
        & ~w.fuel.astype(str).isin(NO_WALK)
        & (w.mw > 0)
        & (w.mc <= w.price + 1e-6)
    ].copy()
    w = w.sort_values(["hour", "mc"], ascending=[True, False])
    w["above"] = w.groupby("hour").mw.cumsum() - w.mw
    w["need"] = w.hour.map(add_h).fillna(0.0)
    w["cut"] = (w.need - w.above).clip(lower=0.0).clip(upper=w.mw)
    cls = (w.groupby(w.plant_group.astype(str)).cut.sum() / 1e6).round(3)
    inv = j.mc - j.mc_lo
    return {
        "gain_twh": round(float(add.sum() / 1e6), 3),
        "gain_by_group": by_group,
        "displaced_by_class": {k: float(v) for k, v in cls.items() if abs(v) >= 0.005},
        "markup_committed_minus_econlo_mean": round(float(inv.mean()), 2),
        "plants_inverted": int(((inv.groupby(level=0).mean()) > 0.5).sum()),
        "plants": int(inv.index.get_level_values(0).nunique()),
    }


def main() -> None:
    pf = rcf._parasitic_factor_map()
    res = {}
    for y in range(2019, 2026):
        um_all = pd.read_parquet(
            ARM / f"closeout_miso_w3e_{y}/hourly/unit_marginal_{y}.parquet",
            columns=[
                "plant_code",
                "plant_group",
                "fuel",
                "unit_id",
                "hour",
                "mw",
                "cap_mw",
                "mc",
                "marginal",
            ],
        )
        um = um_all[um_all.plant_group.astype(str).isin(CHP)].copy()
        um["band"] = um.unit_id.astype(str).str.split("_").str[-1]
        cen = census(y, um, rcf._campd_hourly_frame(y, "MISO", pf, 8760))
        df = pd.DataFrame(cen)
        wt = df.cems_twh / df.cems_twh.sum()
        res[y] = {
            "census_summary": {
                "plants": len(df),
                "cems_on_wmean": round(float((df.cems_on * wt).sum()), 3),
                "model_on_wmean": round(float((df.model_on * wt).sum()), 3),
                "cems_starts_median": float(df.cems_starts.median()),
                "model_starts_median": float(df.model_starts.median()),
            },
            "census_top": df.sort_values("cems_twh", ascending=False)
            .head(10)
            .to_dict("records"),
            "reach": reach(um_all, um),
        }
        print(y, json.dumps(res[y]["census_summary"]), json.dumps(res[y]["reach"]))
    OUT.write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
