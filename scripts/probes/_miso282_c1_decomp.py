#!/usr/bin/env python3
"""miso-282 phase 0 (ZERO LP): decompose the keeper's C1 ST_GAS residual by year.

C1 ST_GAS = model grid-LP ST_GAS (``gmModel``, after the ``OTHER_FOSSIL``
re-bucketing of mixed plants such as Ninemile 1403) minus the benchmark
``classFull`` ST_GAS. This splits it three ways, per year:

* ``no_unit``  -- benchmark ST_GAS at plants where the model fleet has NO
  ST_GAS unit (e.g. EIA-860 ``SB`` Baxter Wilson 2050 in 2021-22);
* ``south``    -- MISO-South plants that have a model ST_GAS unit: model
  realized (payload ``volErr`` zone sums) minus benchmark;
* ``other``    -- the same for every other zone.

and, from ``_miso282_inmerit_2x2.json`` (plant-net EIA-923 basis, hub hours),
splits the South term into out-of-merit (measured energy in hours the hub was
below measured cost, minus the model floor) and in-merit (model envelope above
its floor minus measured in-merit energy).

Inputs: the keeper run payload and bench sidecars (committed), the fleet-only
unit tables written by ``_miso282_stgas_fleet.py`` and the benchmark EIA-923
frame rebuilt by ``run_calibration_full.build_benchmark_frames`` (both passed in).

Usage::

    uv run python scripts/probes/_miso282_c1_decomp.py --fleet-dir X --bench B --twox2 J --out O
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
import pandas as pd  # noqa: E402

KEEPER_ID = "2026-09-28-miso-280-splitremap"
PAYLOAD = REPO / f"frontend/data/backcast/runs/{KEEPER_ID}.js"
BENCH = REPO / "frontend/data/backcast/bench/MISO/{y}.json.gz"
MIXED = {1403}  # OTHER_FOSSIL in C1 (mixed_fossil_plants), every year 2019-2025


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--fleet-dir", required=True)
    ap.add_argument("--bench", required=True, help="benchmark eia923 parquet")
    ap.add_argument("--twox2", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    s = PAYLOAD.read_text()
    p = json.loads(
        gzip.decompress(base64.b64decode(re.search(r'="([^"]+)"', s).group(1)))
    )
    b = pd.read_parquet(args.bench)
    t2 = json.loads(Path(args.twox2).read_text())["years"]
    rows = []
    for y in range(2019, 2026):
        cf = json.loads(gzip.open(str(BENCH).format(y=y)).read())["bench"]["classFull"]
        gm = p["years"][str(y)]["gmModel"]["ST_GAS"]
        zm = p["years"][str(y)]["volErr"]["ST_GAS"]["zoneMon"]
        m_z = {z: sum(v["m"]) for z, v in zm.items()}
        u = pd.read_parquet(Path(args.fleet_dir) / f"units_{y}.parquet")
        u = u[u.group == "ST_GAS"]
        zone = u.groupby("plant_code").zone.first()
        bb = (
            b[(b.year == y) & (b.klass == "ST_GAS")]
            .groupby("plant_id")
            .annual_mwh.sum()
            / 1e6
        )
        bb = bb.drop(list(MIXED), errors="ignore")
        has = bb.index.isin(zone.index)
        bz = bb[has].groupby(bb[has].index.map(zone)).sum()
        south = m_z.get("MISO-South", 0.0) - bz.get("MISO-South", 0.0)
        other = (
            sum(m_z.values())
            - m_z.get("MISO-South", 0.0)
            - (bz.sum() - bz.get("MISO-South", 0.0))
        )
        c = t2[str(y)]["south_c1_basis"]
        rows.append(
            {
                "year": y,
                "c1_model": round(gm, 3),
                "c1_actual": round(cf["ST_GAS"], 3),
                "c1_resid": round(gm - cf["ST_GAS"], 3),
                "no_unit": round(-float(bb[~has].sum()), 3),
                "south": round(south, 3),
                "other": round(other, 3),
                "south_oom_gap": round(c["floor"] - (c["act"] - c["act_in"]), 3),
                "south_inmerit_gap": round((c["MM"] - c["floor"]) - c["act_in"], 3),
                "south_price_effect_MM_minus_HM": round(c["MM"] - c["HM"], 3),
                "south_offer_effect_MM_minus_MC": round(c["MM_hrok"] - c["MC_hrok"], 3),
            }
        )
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    Path(args.out).write_text(
        json.dumps({"keeper": KEEPER_ID, "rows": rows}, indent=1) + "\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
