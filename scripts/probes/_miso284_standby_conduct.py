#!/usr/bin/env python3
"""miso-284 phase 0 (ZERO LP): measured conduct of MISO's EIA-860 ``SB`` units.

``admit_standby_units`` (NWPP-NEXT-5, MISO cell ``U``) would admit every
generator EIA-860 codes ``SB`` in the year's own vintage. miso-282 sized the
admitted fleet (``_miso282_standby_delta.py``). This probe records, for each
MATERIAL admitted plant, what the unit actually did in each year:

- the ``SB`` rows in the year's EIA-860 vintage (generator, prime mover, MW);
- CAMPD unit-level gross MWh and operating hours, per CEMS unit id;
- EIA-923 plant x prime-mover net generation (the C1 benchmark's own source);
- whether any committed MISO outage extract carries a row for the plant.

It reads committed source data only. Nothing here selects a unit; it is the
evidence for the owner's admission decision (rule 13: the admission rule under
review is status alone, and this table is how the census reads that rule).

Usage::

    uv run python scripts/probes/_miso284_standby_conduct.py --out X.json
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pandas as pd  # noqa: E402

RAW = REPO / "data/raw"
YEARS = range(2019, 2026)
# Material admitted plants from _miso282_standby_delta (>= 20 MW admitted in
# any year) with their CAMPD state. The ~800 MW of SB oil / IC units add
# ~0 TWh of envelope and are summarised, not enumerated.
PLANTS: dict[int, str] = {
    10075: "MN",  # Taconite Harbor, COAL_PRB
    2050: "MS",  # Baxter Wilson, ST_GAS
    1392: "LA",  # Louisiana 2, ST_GAS
    1866: "MI",  # Wyandotte, ST_GAS
    10745: "MI",  # Midland Cogeneration Venture, CC_CHP (ST2)
    976: "IL",  # Marion, CT_PEAKER (GT 5/6)
    1979: "MN",  # Hibbing, COAL_PRB / ST_CHP
    1024: "IN",  # Crawfordsville, COAL_BIT
}


def _vintage_path(year: int) -> Path:
    """EIA-860 generator file for ``year``'s vintage (tip past the last one)."""
    p = RAW / f"eia-860/vintage_{year}/eia860_generator_operable.parquet"
    return p if p.exists() else RAW / "eia-860/eia860_generator_operable.parquet"


def sb_rows(year: int) -> list[dict]:
    """Material plants' SB generators in ``year``'s EIA-860 vintage."""
    d = pd.read_parquet(_vintage_path(year))
    pc = pd.to_numeric(d["Plant Code"], errors="coerce")
    d = d[pc.isin(list(PLANTS)) & (d["Status"] == "SB")]
    return [
        {
            "plant": int(float(r["Plant Code"])),
            "gen": str(r["Generator ID"]),
            "pm": str(r["Prime Mover"]),
            "fuel": str(r["Energy Source 1"]),
            "summer_mw": float(pd.to_numeric(r["Summer Capacity (MW)"])),
        }
        for _, r in d.iterrows()
    ]


def cems(plant: int, state: str, year: int) -> dict[str, dict]:
    """CAMPD gross GWh and operating hours per CEMS unit id."""
    f = RAW / f"campd-unit-level/{state}_{year}.parquet"
    if not f.exists():
        return {}
    d = pd.read_parquet(f, columns=["facilityId", "unitId", "opTime", "grossLoad"])
    d = d[pd.to_numeric(d["facilityId"], errors="coerce") == plant]
    return {
        str(u): {
            "gross_gwh": round(float(g["grossLoad"].fillna(0).sum()) / 1e3, 1),
            "op_hours": int((g["opTime"].fillna(0) > 0).sum()),
        }
        for u, g in d.groupby("unitId")
    }


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    e923 = pd.read_parquet(
        RAW / "_processed-legacy/eia923_monthly_generation.parquet",
        columns=["plant_id", "prime_mover", "year", "netgen_annual_mwh"],
    )
    e923 = e923[e923["plant_id"].isin(list(PLANTS))]
    ext = pd.concat(
        pd.read_csv(f, usecols=["facility_id"])
        for f in sorted(
            glob.glob(str(RAW / "campd-unit-outages*-MISO.csv"))
            + [str(RAW / "campd-partial-outages-MISO.csv")]
        )
    )
    in_extract = set(pd.to_numeric(ext["facility_id"], errors="coerce").dropna())
    out: dict = {"plants": {}}
    for plant, state in PLANTS.items():
        rec: dict = {"in_any_miso_outage_extract": plant in in_extract, "years": {}}
        for y in YEARS:
            sb = [r for r in sb_rows(y) if r["plant"] == plant]
            g = e923[(e923["plant_id"] == plant) & (e923["year"] == y)]
            rec["years"][y] = {
                "sb_gens": [f"{r['gen']}({r['pm']},{r['summer_mw']:g})" for r in sb],
                "sb_summer_mw": round(sum(r["summer_mw"] for r in sb), 1),
                "cems": cems(plant, state, y),
                "e923_gwh_by_pm": {
                    str(k): round(float(v) / 1e3, 1)
                    for k, v in g.groupby("prime_mover")["netgen_annual_mwh"]
                    .sum(min_count=1)
                    .dropna()
                    .items()
                },
            }
        out["plants"][plant] = rec
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    for plant, rec in out["plants"].items():
        print(plant, "extract:", rec["in_any_miso_outage_extract"])
        for y, v in rec["years"].items():
            if v["sb_gens"]:
                print(" ", y, v["sb_summer_mw"], v["e923_gwh_by_pm"], v["cems"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
