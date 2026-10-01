"""PJM-NEXT-22 card 1b (zero LP): coal margin on PJM's actual ZONAL RT price, not system RT.

NEXT-20/21 and card 1 measured each coal plant's margin against PJM system RT. 2025's
over-run sits in the west (AEP-Ohio, West-APS). If actual western zonal RT fell further
below system in the miss years than the model's west-minus-system spread, the model's coal
margin is too large there by a congestion term, and the miss would order by it.

Per year with zonal data on disk (``data/raw/pjm-zonal-lmp/rt_hrl_lmps_<y>_<m>.parquet``,
gitignored DataMiner2; refetch with ``scripts/data/fetch_pjm_zonal_lmp_components.py
--feeds rt_hrl_lmps --years <y>``):

- the actual zonal RT for each model zone (hour axis fixed EST, Feb 29 dropped): simple mean of its PJM transmission-zone pnodes
  (crosswalk ``eia930.zonal_shares._PJM_LOAD_ZONE_GROUPS``);
- coal-MW-weighted (keeper P1) spreads: model zone price - actual zonal RT, and actual zonal
  RT - actual system RT (``PJM-RTO``);
- the keeper vs real (C1 bench) coal loading on LP capacity by margin bin, with margin taken
  against the actual ZONAL RT, per zone group (west = AEP-Ohio + West-APS, rest).

Writes ``results/phase0/pjm/_pjmnext22_coal_zonal_margin.json``.
Run: ``python3 scripts/probes/_pjmnext22_coal_zonal_margin.py``
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
from _pjmnext16_cc_loading import _dec  # noqa: E402

HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
BENCH = REPO / "frontend/data/backcast/bench/PJM"
ZONAL = REPO / "data/raw/pjm-zonal-lmp"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
OUT = REPO / "results/phase0/pjm/_pjmnext22_coal_zonal_margin.json"
T = 8760
# DataMiner2 zone pnode -> model zone (the _PJM_LOAD_ZONE_GROUPS crosswalk, pnode names).
PNODE_TO_ZONE = {
    "COMED": "PJM_ComEd",
    "AEP": "PJM_AEP_Ohio",
    "DAY": "PJM_AEP_Ohio",
    "DEOK": "PJM_AEP_Ohio",
    "OVEC": "PJM_AEP_Ohio",
    "ATSI": "PJM_ATSI",
    "APS": "PJM_West_APS",
    "DUQ": "PJM_West_APS",
    "PPL": "PJM_Central_PA",
    "PENELEC": "PJM_Central_PA",
    "METED": "PJM_Central_PA",
    "EKPC": "PJM_Central_PA",
    "DOM": "PJM_Dominion",
    "PSEG": "PJM_EMAAC",
    "JCPL": "PJM_EMAAC",
    "PECO": "PJM_EMAAC",
    "DPL": "PJM_EMAAC",
    "AECO": "PJM_EMAAC",
    "RECO": "PJM_EMAAC",
    "BGE": "PJM_SWMAAC",
    "PEPCO": "PJM_SWMAAC",
}
WEST = {"PJM_AEP_Ohio", "PJM_West_APS"}
BINS = ((-1e9, 0.0), (0.0, 5.0), (5.0, 15.0), (15.0, 1e9))


def zonal_rt(y: int) -> tuple[pd.DataFrame, np.ndarray] | None:
    """Hour-of-year (EPT, DST-collapsed) actual RT by model zone, plus PJM-RTO."""
    files = sorted(ZONAL.glob(f"rt_hrl_lmps_{y}_*.parquet"))
    if len(files) < 12:
        return None
    z = pd.concat(
        pd.read_parquet(
            f, columns=["datetime_beginning_utc", "pnode_name", "total_lmp_rt"]
        )
        for f in files
    ).reset_index(drop=True)
    # Fixed EST (UTC-5), Feb 29 dropped: the hour axis of the keeper and of
    # actual_lmp_hourly_PJM (corr 0.98-0.99 against PJM-RTO on this axis).
    ts = pd.to_datetime(
        z.datetime_beginning_utc, format="%m/%d/%Y %I:%M:%S %p"
    ) - pd.Timedelta(hours=5)
    keep = ~((ts.dt.month == 2) & (ts.dt.day == 29))
    z, ts = z[keep].copy(), ts[keep]
    doy = ts.dt.dayofyear - ((ts.dt.month > 2) & ts.dt.is_leap_year).astype(int)
    z["hour"] = ((doy - 1) * 24 + ts.dt.hour).to_numpy()
    z = z[(z.hour >= 0) & (z.hour < T)]
    rto = z[z.pnode_name == "PJM-RTO"].groupby("hour").total_lmp_rt.mean()
    z["zone"] = z.pnode_name.map(PNODE_TO_ZONE)
    zz = z.dropna(subset=["zone"]).groupby(["zone", "hour"]).total_lmp_rt.mean()
    zz = zz.unstack("hour").reindex(columns=range(T)).ffill(axis=1).bfill(axis=1)
    rto = rto.reindex(range(T)).ffill().bfill().to_numpy()
    return zz, rto


def year(y: int) -> dict | None:
    """One year's zonal coal margin split."""
    zr = zonal_rt(y)
    if zr is None:
        return None
    zz, rto = zr
    act = pd.read_parquet(ACTUAL)
    rt_sys = act[act.year == y].sort_values("hour").rt.to_numpy()[:T]
    cols = ["plant_code", "plant_group", "zone", "hour", "mw", "cap_mw", "mc"]
    u = pd.read_parquet(HOURLY / f"unit_marginal_{y}.parquet", columns=cols)
    u = u[u.plant_group.astype(str).str.startswith("COAL") & (u.hour < T)].copy()
    s = pd.read_parquet(
        HOURLY / f"system_{y}.parquet", columns=["zone", "hour", "price"]
    )
    u = u.merge(s[s.hour < T], on=["zone", "hour"], how="left")
    u["zone"] = u.zone.astype(str)
    u["capmc"] = u.cap_mw * u.mc
    p = (
        u.groupby(["plant_code", "zone", "hour"], observed=True)
        .agg(
            mw=("mw", "sum"),
            cap=("cap_mw", "sum"),
            capmc=("capmc", "sum"),
            price=("price", "first"),
        )
        .reset_index()
    )
    p["az"] = zz.to_numpy()[zz.index.get_indexer(p.zone), p.hour.to_numpy()]
    p["rto"] = rto[p.hour.to_numpy()]
    p["rt_sys"] = rt_sys[p.hour.to_numpy()]
    p["offer"] = p.capmc / p.cap.where(p.cap > 0)
    bp = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
    real = {}
    for key, b in bp.items():
        raw = str(b.get("pcode") or key).split(":")[0]
        if (
            str(b.get("group", "")).startswith("COAL")
            and raw.isdigit()
            and b.get("nodata") not in (True, "True")
            and b.get("campd")
        ):
            real[int(raw)] = _dec(b["campd"], b.get("e_ann") or b.get("c_ann"))
    p = p[p.plant_code.isin(real)].copy()
    p["real"] = [real[c][h] for c, h in zip(p.plant_code, p.hour)]
    w = p.mw
    res: dict = {
        "rto_vs_sys_rt_mean": round(float(np.mean(rto - rt_sys)), 2),
        "coalw_model_minus_actual_zonal": round(
            float(((p.price - p.az) * w).sum() / w.sum()), 2
        ),
        "coalw_actual_zonal_minus_rto": round(
            float(((p.az - p.rto) * w).sum() / w.sum()), 2
        ),
        "coalw_model_minus_rto": round(
            float(((p.price - p.rto) * w).sum() / w.sum()), 2
        ),
    }
    by_zone = {}
    for zname, g in p.groupby("zone"):
        ww = g.mw
        if ww.sum() <= 0:
            continue
        by_zone[zname] = {
            "model_twh": round(float(g.mw.sum()) / 1e6, 2),
            "over_twh": round(float((g.mw - g.real).sum()) / 1e6, 2),
            "model_minus_actual_zonal": round(
                float(((g.price - g.az) * ww).sum() / ww.sum()), 2
            ),
            "actual_zonal_minus_rto": round(
                float(((g.az - g.rto) * ww).sum() / ww.sum()), 2
            ),
        }
    res["by_zone"] = by_zone
    for grp, mk_g in (("west", p.zone.isin(WEST)), ("rest", ~p.zone.isin(WEST))):
        q = p[mk_g & (p.cap > 0)]
        out = {}
        for basis, price in (("sys_rt", q.rt_sys), ("zonal_rt", q.az)):
            m = price - q.offer
            d = {}
            for lo, hi in BINS:
                mk = (m >= lo) & (m < hi)
                c = q.cap[mk].sum()
                d[f"{lo:g}..{hi:g}"] = {
                    "cf_model": round(float(q.mw[mk].sum() / c), 3) if c else None,
                    "cf_real": round(float(q.real[mk].sum() / c), 3) if c else None,
                    "over_twh": round(float((q.mw - q.real)[mk].sum()) / 1e6, 2),
                    "cap_twh": round(float(c) / 1e6, 1),
                }
            out[basis] = d
        res[grp] = out
    return res


def main() -> None:
    """Every year with a complete zonal RT year on disk."""
    out: dict = {
        "what": "PJM-NEXT-22 card 1b: coal margin on actual zonal RT. ZERO LP."
    }
    for y in range(2019, 2026):
        r = year(y)
        if r is None:
            continue
        out[str(y)] = r
        print(y, {k: v for k, v in r.items() if not isinstance(v, dict)})
        for zname, v in r["by_zone"].items():
            print("   ", zname, v)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
