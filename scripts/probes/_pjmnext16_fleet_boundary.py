"""PJM-NEXT-16 (zero LP): the energy identity and the LP-fleet vs C1-benchmark boundary.

For every year 2019-2025, from committed artifacts only:

1. **Energy identity** (the NEXT-6 construction on the current keeper): model generation
   (``class_hourly``) vs the C1 benchmark ``classFull``, split into the model's net
   export shortfall, its losses and ``U_a`` = EIA-930 demand + tie-meter export -
   ``classFull``.
2. **Fleet boundary**: EIA-923 Page-1 fossil generation of plants the C1 benchmark's
   membership (``run_calibration_full._iso_plant_ids(..., vintage_union=True)``, the
   keeper's setting) counts but the keeper's LP fleet (the registered payload's plant
   set) does not dispatch, per plant.
3. ``classFull`` COAL_BIT minus the per-plant bench sum (which follows the dispatch).

Writes ``results/calibration/_pjmnext16_fleet_boundary.json``.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "scripts"), str(REPO / "scripts" / "probes")):
    if p not in sys.path:
        sys.path.insert(0, p)

import _pjmnext16_cc_loading as P  # noqa: E402

OUT = REPO / "results/calibration/_pjmnext16_fleet_boundary.json"
F923 = REPO / "data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv"
TIES = REPO / "data/raw/iso-specific-transmission"
FOSSIL = ("BIT", "SUB", "LIG", "RC", "WC", "NG", "OG", "BFG", "DFO", "RFO", "KER", "JF", "PC")


def main() -> None:
    """Census every year; write the JSON artifact."""
    import run_calibration_full as R

    pay = {int(y): r["plants"] for y, r in P._payload(P.RUN)["years"].items()}
    g = pd.read_csv(F923, low_memory=False)
    names = (
        pd.read_parquet(REPO / "data/raw/eia-860/eia860_plant.parquet")
        .drop_duplicates("Plant Code")
        .set_index("Plant Code")["Plant Name"]
    )
    res = {"what": "PJM-NEXT-16 energy identity + fleet boundary. ZERO LP.", "years": {}}
    for y in P.YEARS:
        bench = json.load(gzip.open(P.BENCH / f"{y}.json.gz"))["bench"]
        cf = bench["classFull"]
        cm = pd.read_parquet(P.HOURLY / f"class_hourly_{y}.parquet")
        cm = cm.groupby("klass").mw.sum() / 1e6
        dm = pd.read_parquet(P.HOURLY / f"system_{y}.parquet").demand.sum() / 1e6
        phys = [k for k in cm.index if k not in ("import", "VIRTUAL_DEC", "VIRTUAL_INC")]
        gm, xm = float(cm[phys].sum()), float(-cm["import"])
        tie = pd.read_csv(TIES / f"PJM_{y}_import_export_act_sch_interchange.csv")
        xa = float(-tie.actual_flow.sum() / 1e6)
        da = float(P._e930(y).demand.sum() / 1e6)
        ga = float(sum(cf.values()))
        members = set(R._iso_plant_ids("PJM", y, True))
        fleet = {int(str(k).split(":")[0]) for k in pay[y] if str(k).split(":")[0].isdigit()}
        gy = g[(g.year == y) & g.fuel_type.isin(FOSSIL)]
        gen = gy.groupby("plant_id").net_generation_mwh.sum() / 1e6
        missing = gen.reindex(sorted(members - fleet)).fillna(0).sort_values(ascending=False)
        bit_sum = sum(
            float(p.get("e_ann") or p.get("c_ann") or 0)
            for p in bench["plants"].values()
            if p.get("group") == "COAL_BIT" and str(p.get("nodata")) != "True"
        )
        res["years"][str(y)] = {
            "model_gen": round(gm, 2),
            "classFull": round(ga, 2),
            "d_gen": round(gm - ga, 2),
            "export_model": round(xm, 2),
            "export_tie": round(xa, 2),
            "d_export": round(xm - xa, 2),
            "losses_model": round(gm - xm - float(dm), 2),
            "U_a": round(da + xa - ga, 2),
            "bench_not_fleet_fossil_twh": round(float(missing.sum()), 2),
            "bench_not_fleet_top": [
                [int(p), str(names.get(p, "?")), round(float(v), 2)]
                for p, v in missing.head(8).items()
                if v > 0.1
            ],
            "classFull_minus_bench_plants_COAL_BIT": round(cf["COAL_BIT"] - bit_sum, 2),
        }
        r = res["years"][str(y)]
        print(
            y,
            f"dGen {r['d_gen']:+.1f} = dX {r['d_export']:+.1f} + L {r['losses_model']:+.1f}"
            f" + U_a {r['U_a']:.1f} | bench-not-fleet {r['bench_not_fleet_fossil_twh']:.2f}",
            r["bench_not_fleet_top"][:3],
            flush=True,
        )
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
