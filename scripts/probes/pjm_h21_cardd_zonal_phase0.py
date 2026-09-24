"""pjm-h21 phase 0, part 2 — WHERE the PJM CC_REGULAR surplus sits. ZERO LP.

Three reads, all from existing artifacts:

1. ZONE: per-zone CC_REGULAR energy, model minus actual (bench EIA-923 net), for
   the keeper (``runs/2026-09-23-pjm-h19-dbs-*.js``) and the pjm-h20 level-form arm
   (its shard ``unit_hourly`` legs, pulled read-only to a scratch dir).
2. RGGI: the same per-zone table for pjm-146's registered pair, read from git
   history at ``25dd3b3d`` (``runs/2026-08-02-pjm-146{a,b}-*.js``), which pjm-146
   only ever reported at class level.
3. HEAT RATE: ``scripts/data/derive_campd_cc_heat_rates.py --iso PJM --years
   2020..2025`` (run to a scratch path, copied to
   ``results/calibration/_pjm_h21_cc_heat_rate_census.csv``; it is NOT placed at the
   ``measured_cc_heat_rates`` input path, so nothing is armed), joined to the
   plants' actual-CF terciles.

Run: ``python scripts/probes/pjm_h21_cardd_zonal_phase0.py <legs dir> <pjm146 payload dir>``
Writes ``results/calibration/_pjm_h21_cardd_zonal_phase0.json``.
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
HR = REPO / "results/calibration/_pjm_h21_cc_heat_rate_census.csv"


def _bench_cc(y: int) -> list[tuple[str, int, dict]]:
    """Bench CC_REGULAR plants for year ``y`` as (key, plant code, record)."""
    b = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
    return [
        (k, int(k.split("|")[0].split(":")[0]), v)
        for k, v in b.items()
        if v.get("group") == "CC_REGULAR" and not v.get("nodata")
    ]


def _zone_table(y: int, runs: dict[str, dict]) -> dict:
    """Per-zone model-minus-actual CC TWh for each run in ``runs`` (key -> plant dict)."""
    rows = []
    for k, c, v in _bench_cc(y):
        r = dict(
            zone=v["zone"].replace("PJM_", ""),
            act=float(v.get("e_ann") or v.get("c_ann") or 0.0),
        )
        for tag, plants in runs.items():
            rec = plants.get(k) if isinstance(plants.get(k), dict) else None
            r[tag] = (
                float(rec.get("m_ann") or 0.0) if rec else float(plants.get(c, 0.0))
            )
        rows.append(r)
    t = pd.DataFrame(rows).groupby("zone").sum()
    return {tag: (t[tag] - t["act"]).round(3).to_dict() for tag in runs}


def main(legs: Path, p146: Path) -> None:
    """Run the three reads and write the JSON artifact."""
    keep = {}
    for p in P.RUNS.values():
        for y, rec in P._payload(p)["years"].items():
            keep[int(y)] = rec["plants"]
    ctl = P._payload(p146 / "2026-08-02-pjm-146a-control-zerodelta.js")["years"]
    rggi = P._payload(p146 / "2026-08-02-pjm-146b-rggi-allowance.js")["years"]
    out: dict = {
        "what": __doc__.splitlines()[0],
        "zone_keeper_arm": {},
        "zone_pjm146": {},
        "hr_terciles": {},
    }
    for y in P.YEARS:
        uh = pd.read_parquet(
            legs / f"pjm_h20_cardc_{y}/hourly/unit_hourly_{y}.parquet",
            columns=["unit_id", "plant_code", "mw"],
        )
        uh = uh[uh["unit_id"].astype(str).str.startswith("CC_REGULAR_")]
        arm = (uh.groupby("plant_code", observed=True)["mw"].sum() / 1e6).to_dict()
        out["zone_keeper_arm"][str(y)] = _zone_table(y, {"keeper": keep[y], "arm": arm})
        if str(y) in ctl:
            out["zone_pjm146"][str(y)] = _zone_table(
                y, {"control": ctl[str(y)]["plants"], "rggi": rggi[str(y)]["plants"]}
            )
    hr = pd.read_csv(HR).set_index("plant_code")
    for y in (2020, 2023):
        rows = [
            dict(
                c=c,
                npl=v["npl"],
                cf=float(v.get("e_ann") or 0.0) * 1e6 / (v["npl"] * 8760),
            )
            for _, c, v in _bench_cc(y)
        ]
        t = (
            pd.DataFrame(rows)
            .drop_duplicates("c")
            .join(hr[["heat_rate", "model_heat_rate_egrid", "flag"]], on="c")
        )
        t["terc"] = pd.qcut(
            t["cf"].rank(method="first"), 3, labels=["lowCF", "midCF", "highCF"]
        ).astype(str)
        ok = t[t["flag"] == "ok"]
        out["hr_terciles"][str(y)] = {
            k: dict(
                n_ok=len(g),
                measured=float((g.heat_rate * g.npl).sum() / g.npl.sum()),
                model=float((g.model_heat_rate_egrid * g.npl).sum() / g.npl.sum()),
            )
            for k, g in ok.groupby("terc")
        }
    dst = REPO / "results/calibration/_pjm_h21_cardd_zonal_phase0.json"
    dst.write_text(json.dumps(out, indent=1))
    print(json.dumps(out["hr_terciles"], indent=1))
    print("wrote", dst)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
