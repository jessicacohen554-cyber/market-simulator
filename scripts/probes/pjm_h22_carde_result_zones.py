"""pjm-h22 Card E result — per-zone, per-class TWh: keeper vs RGGI arm vs actual. ZERO LP.

Keeper: the registered payloads (``runs/2026-09-23-pjm-h19-dbs-{span,touchpoint}.js``).
Arm: each per-year shard leg's ``hourly/unit_hourly_<y>.parquet`` (P1), summed by
(plant_code, plant_group). Actual: the bench (EIA-923 net level). Bench plants only,
the same population as pjm-h21's zonal table and this lane's phase 0.

Run: ``python scripts/probes/pjm_h22_carde_result_zones.py [years ...]``
Writes ``results/calibration/_pjm_h22_carde_result_zones.json``.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
import pjm_h21_cardd_phase0 as P  # noqa: E402

BENCH = REPO / "frontend/data/backcast/bench/PJM"
# CC_REGULAR only: the arm unit_hourly plant_group labels do not match the bench
# group keys for coal classes (a key mismatch, not a result); C1 scores those.
GROUPS = ("CC_REGULAR",)
FOCUS = ("EMAAC", "SWMAAC", "Dominion")


def _arm(y: int) -> dict[tuple[str, int], float]:
    """Arm TWh by (group, plant_code) from the leg's P1 unit hourlies."""
    uh = pd.read_parquet(
        REPO / f"results/calibration/pjm_h22_rggi_{y}/hourly/unit_hourly_{y}.parquet",
        columns=["pass", "plant_code", "plant_group", "mw"],
    )
    uh = uh[uh["pass"] == "P1"]
    s = uh.groupby(["plant_group", "plant_code"], observed=True)["mw"].sum() / 1e6
    return {(str(g), int(c)): float(v) for (g, c), v in s.items()}


def main(years: list[int]) -> None:
    """Build the per-zone table for each requested year and write the JSON."""
    keep = {}
    for p in P.RUNS.values():
        for y, rec in P._payload(p)["years"].items():
            keep[int(y)] = rec["plants"]
    out: dict = {"what": __doc__.splitlines()[0], "years": {}}
    for y in years:
        arm = _arm(y)
        b = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
        rows = []
        for k, v in b.items():
            g = v.get("group")
            if g not in GROUPS or v.get("nodata"):
                continue
            c = int(k.split("|")[0].split(":")[0])
            rec = keep[y].get(k)
            rows.append(
                dict(
                    group=g,
                    zone=v["zone"].replace("PJM_", ""),
                    act=float(v.get("e_ann") or v.get("c_ann") or 0.0),
                    keeper=float(rec.get("m_ann") or 0.0)
                    if isinstance(rec, dict)
                    else 0.0,
                    arm=arm.get((g, c), 0.0),
                )
            )
        t = pd.DataFrame(rows).groupby(["group", "zone"]).sum().round(2)
        yr = {}
        for g in GROUPS:
            if g not in t.index.get_level_values(0):
                continue
            tg = t.loc[g]
            yr[g] = {
                z: dict(
                    actual=r.act,
                    keeper_err=round(r.keeper - r.act, 2),
                    arm_err=round(r.arm - r.act, 2),
                    delta=round(r.arm - r.keeper, 2),
                )
                for z, r in tg.iterrows()
            }
            yr[g]["_bench_total"] = dict(
                actual=round(tg.act.sum(), 2),
                keeper_err=round(tg.keeper.sum() - tg.act.sum(), 2),
                arm_err=round(tg.arm.sum() - tg.act.sum(), 2),
                delta=round(tg.arm.sum() - tg.keeper.sum(), 2),
            )
        out["years"][str(y)] = yr
        cc = yr["CC_REGULAR"]
        print(
            y,
            {z: (cc[z]["keeper_err"], cc[z]["arm_err"]) for z in FOCUS},
            "total",
            cc["_bench_total"],
        )
    dst = REPO / "results/calibration/_pjm_h22_carde_result_zones.json"
    prev = json.loads(dst.read_text()) if dst.exists() else {"years": {}}
    prev["what"] = out["what"]
    prev["years"].update(out["years"])
    dst.write_text(json.dumps(prev, indent=1))
    print("wrote", dst)


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or list(P.YEARS))
