"""SPP-98 phase 0 (zero LP): census of SPP CEMS units whose CAMPD facility differs from their EIA plant.

Source of the mapping: EPA CAMD-EIA Power Sector Data Crosswalk (data/raw/reference/camd-eia-crosswalk,
intaken by miso-277). A unit is RE-KEYED when CAMD_PLANT_ID != EIA_PLANT_ID. Reports, per year 2019-2025,
the CEMS gross load of re-keyed units whose EIA plant OR CAMD facility is in the SPP keeper fleet
(fleet plant codes from the committed bench + model payload), grouped by (CAMD facility -> EIA plant).

Usage: uv run python scripts/probes/_spp98_crosswalk_census.py <payload.json>
Writes docs/handoffs/spp98/crosswalk_census.json
"""

import gzip
import json
import sys
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
X = REPO / "data/raw/reference/camd-eia-crosswalk/epa_eia_crosswalk.csv"


def main():
    """Census re-keyed CEMS units touching the SPP fleet."""
    j = json.load(open(sys.argv[1]))
    fleet = set()
    for y, d in j["years"].items():
        fleet |= {int(k.split(":")[0]) for k in d["plants"]}
        b = json.load(
            gzip.open(REPO / f"frontend/data/backcast/bench/SPP/{y}.json.gz")
        )["bench"]["plants"]
        fleet |= {int(k.split(":")[0]) for k in b}
    x = pd.read_csv(X, encoding="utf-8-sig", low_memory=False)
    x = x.dropna(subset=["EIA_PLANT_ID"])
    x["EIA_PLANT_ID"] = x.EIA_PLANT_ID.astype(int)
    x["CAMD_PLANT_ID"] = x.CAMD_PLANT_ID.astype(int)
    rk = x[x.CAMD_PLANT_ID != x.EIA_PLANT_ID]
    rk = rk[rk.CAMD_PLANT_ID.isin(fleet) | rk.EIA_PLANT_ID.isin(fleet)]
    units = rk[
        [
            "CAMD_STATE",
            "CAMD_PLANT_ID",
            "CAMD_UNIT_ID",
            "CAMD_FACILITY_NAME",
            "EIA_PLANT_ID",
            "EIA_PLANT_NAME",
            "EIA_UNIT_TYPE",
        ]
    ].drop_duplicates(["CAMD_PLANT_ID", "CAMD_UNIT_ID", "EIA_PLANT_ID"])
    print(units.to_string())
    out = {"units": units.to_dict("records"), "gross_twh": {}}
    states = sorted(units.CAMD_STATE.unique())
    for y in range(2019, 2026):
        tot = {}
        for s in states:
            f = REPO / f"data/raw/campd-unit-level/{s}_{y}.parquet"
            if not f.exists():
                continue
            d = pd.read_parquet(f, columns=["facilityId", "unitId", "grossLoad"])
            d["facilityId"] = d.facilityId.astype(int)
            m = d.merge(
                units[["CAMD_PLANT_ID", "CAMD_UNIT_ID", "EIA_PLANT_ID"]],
                left_on=["facilityId", "unitId"],
                right_on=["CAMD_PLANT_ID", "CAMD_UNIT_ID"],
            )
            for (cp, ep), g in m.groupby(["CAMD_PLANT_ID", "EIA_PLANT_ID"]):
                tot[f"{cp}->{ep}"] = round(g.grossLoad.sum() / 1e6, 3)
        out["gross_twh"][y] = tot
        print(y, tot, "total", round(sum(tot.values()), 3))
    p = REPO / "docs/handoffs/spp98"
    p.mkdir(parents=True, exist_ok=True)
    (p / "crosswalk_census.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
