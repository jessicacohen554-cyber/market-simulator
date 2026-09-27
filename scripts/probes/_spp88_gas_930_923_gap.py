"""SPP-88 Card D, phase 0 (ZERO LP): why EIA-930 SWPP gas sits BELOW the EIA-923 gas benchmark.

SPP-87 §2 left a 2.5–3.4 TWh/yr gap open (bench ``classFull`` gas − EIA-930 ``NG``). Coal shows the
opposite sign (930 ≈ CEMS gross > 923 net), so station service cannot explain gas. This probe
splits the keeper's own EIA-923 gas frame by plant type and fits EIA-930 ``NG`` hourly against
CEMS gross, like SPP-87 did for coal:

  930_h = a·nonCHP_gross_h + b·CHP_gross_h + c

If 930 sees CHP only at the grid meter, ``b`` falls below 1. Separately, the annual residual is
attributed to non-CHP station service, the CHP host share, units without CEMS, and the scorer's
own ``classFull`` transforms (CHP scaling, the OTHER_FOSSIL re-bucket, the reconcile scale).

Reads committed artifacts only. Writes ``results/calibration/_spp88_gas_930_923_gap.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))
import _spp87_benchmark_reconcile as s87  # noqa: E402
import calibration_verdict as cv  # noqa: E402

OUT = REPO / "results/calibration/_spp88_gas_930_923_gap.json"
GAS = s87.GAS
CHP = tuple(k for k in GAS if k.endswith("_CHP"))


def cems_gas(year: int, ids: set[int]) -> pd.DataFrame:
    """Hourly CEMS gross MWh of gas-fired units at ``ids`` (CAMPD local standard time)."""
    frames = []
    for st in s87.STATES:
        f = REPO / f"data/raw/campd-unit-level/{st}_{year}.parquet"
        if not f.exists():
            continue
        d = pd.read_parquet(
            f, columns=["facilityId", "date", "hour", "opTime", "grossLoad", "primaryFuelInfo"]
        )
        d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
        frames.append(d[d.facilityId.isin(ids) & (d.primaryFuelInfo != "Coal")])
    c = pd.concat(frames)
    c["mwh"] = c.grossLoad.fillna(0.0) * c.opTime.fillna(0.0)
    c["ts"] = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], unit="h")
    return c[["facilityId", "ts", "mwh"]]


def main() -> None:
    """Build the annual attribution and the hourly fit; print and dump."""
    art = cv.load_artifacts(s87.RUN_ID)
    bench = art["bench"]
    frame = pd.read_parquet(s87.FRAME)
    e = pd.read_parquet(REPO / "data/raw/SWPP_fueltype.parquet")
    e = e[e.fueltype == "NG"].dropna(subset=["value_mwh"]).copy()
    e["year"] = e.period.dt.tz_convert("America/Chicago").dt.year
    e["ts"] = e.period.dt.tz_convert("Etc/GMT+6").dt.tz_localize(None) - pd.Timedelta(hours=1)
    rec: dict = {}
    for y in s87.YEARS:
        fy = frame[(frame.year == y) & frame.klass.isin(GAS)]
        net = fy.groupby("plant_id").annual_mwh.sum() / 1e6
        is_chp = fy.groupby("plant_id").klass.agg(lambda k: any(x in CHP for x in k))
        c = cems_gas(y, set(net.index.astype(int)))
        gross = c.groupby("facilityId").mwh.sum() / 1e6
        pp = pd.DataFrame({"net": net, "gross": gross, "chp": is_chp}).fillna({"net": 0.0, "gross": 0.0})
        pp["chp"] = pp["chp"].fillna(False).astype(bool)
        met = pp[(pp.gross > 0) & (pp.net > 0)]
        un = pp[pp.gross <= 0]
        cf = bench[y]["classFull"]
        e930 = float(bench[y]["e930"]["gas"])
        row = {
            "e930_gas": e930,
            "bench_classFull_gas": round(sum(cf.get(k, 0.0) for k in (*GAS,)), 3),
            "frame_gas_net923": round(float(net.sum()), 3),
            "frame_chp_net923": round(float(pp[pp.chp].net.sum()), 3),
            "bench_chp": round(sum(cf.get(k, 0.0) for k in CHP), 3),
            "bench_other_fossil": round(float(cf.get("OTHER_FOSSIL", 0.0)), 3),
            "nonchp_metered_net": round(float(met[~met.chp].net.sum()), 3),
            "nonchp_metered_gross": round(float(met[~met.chp].gross.sum()), 3),
            "chp_metered_net": round(float(met[met.chp].net.sum()), 3),
            "chp_metered_gross": round(float(met[met.chp].gross.sum()), 3),
            "unmetered_net": round(float(un.net.sum()), 3),
            "unmetered_chp_net": round(float(un[un.chp].net.sum()), 3),
            "cems_only_gross": round(float(pp[(pp.net <= 0) & (pp.gross > 0)].gross.sum()), 3),
        }
        # hourly fit on CEMS gross, CHP split out
        c = c.merge(pp["chp"], left_on="facilityId", right_index=True, how="left")
        h = c.pivot_table(index="ts", columns="chp", values="mwh", aggfunc="sum").fillna(0.0)
        h.columns = ["nonchp" if not k else "chp" for k in h.columns]
        s930 = e[e.year == y].set_index("ts").value_mwh
        j = pd.concat([h, s930.rename("e")], axis=1, sort=True).dropna()
        X = np.column_stack([j["nonchp"], j.get("chp", 0.0 * j["nonchp"]), np.ones(len(j))])
        coef = np.linalg.lstsq(X, j["e"], rcond=None)[0]
        row["hourly_fit"] = {"n": int(len(j)), "a_nonchp": round(float(coef[0]), 3),
                             "b_chp": round(float(coef[1]), 3), "c_mw": round(float(coef[2]), 1),
                             "corr_total": round(float(np.corrcoef(j["nonchp"] + j.get("chp", 0), j["e"])[0, 1]), 3),
                             "sum_e930": round(float(j["e"].sum() / 1e6), 3),
                             "sum_cems_gross": round(float((j["nonchp"] + j.get("chp", 0)).sum() / 1e6), 3)}
        # coverage legs: monthly 930 − 923 net, total generation, SPP portal market/self gas
        M = [f"m{i:02d}" for i in range(1, 13)]
        e_m = e[e.ts.dt.year == y].groupby(e.ts.dt.month).value_mwh.sum().reindex(range(1, 13))
        row["monthly_930_minus_923net"] = [round(float(v), 3) for v in (e_m.to_numpy() / 1e6 - fy[M].sum().to_numpy() / 1e6)]
        tot = pd.read_parquet(REPO / "data/raw/SWPP_fueltype.parquet")
        tot = tot[(tot.period.dt.tz_convert("America/Chicago").dt.year == y) & (tot.value_mwh < 1.0e6)]
        row["e930_total_gen"] = round(float(tot.value_mwh.sum() / 1e6), 3)
        row["frame923_total_gen"] = round(float(frame[frame.year == y].annual_mwh.sum() / 1e6), 3)
        gm = pd.read_csv(REPO / f"data/raw/spp-genmix/GenMix_{y}.csv", skipinitialspace=True)
        gm.columns = [c.strip() for c in gm.columns]
        hrs = 8784 if y % 4 == 0 else 8760
        for col in ("Natural Gas Market", "Gas Self"):
            row[f"portal_{col.lower().replace(' ', '_')}"] = round(
                float(pd.to_numeric(gm[col], errors="coerce").fillna(0.0).mean() * hrs / 1e6), 3)
        rec[y] = row
        print(y, json.dumps({k: v for k, v in row.items() if k != "monthly_930_minus_923net"}))
    OUT.write_text(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
