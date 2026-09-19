"""SPP-48 phase 0: the mid-vintage-year retiree blast radius, at ZERO LP.

Measures the exposure of the ``load_retired_within_window`` mid-vintage-year
gap (``docs/handoffs/RESULT-spp-47-four-failures-2026-09-18.md`` §2) for EVERY
registered region, not just SPP -- the rule 25 ``[R-ISO-SCOPE]`` charter check
this lane owes before touching the shared ``data/fleet/eia860.py`` seam.

The defect: under a year-matched native EIA-860 vintage,
``load_retired_within_window`` returns an empty list, on the stated assumption
that "the operable fleet already has them". That holds for a plant retiring
AFTER the vintage year and is FALSE for one retiring DURING it -- the vintage's
year-end operable snapshot has already moved it to the retired sheet, so the
plant is dropped from the fleet entirely along with its real operating months.

For each (region, year) this reports the plants that are, in that year's OWN
vintage: on the Retired-and-Canceled sheet with ``Retirement Year == year``,
inside the region's balancing authorities, ABSENT from the same vintage's
operable sheet -- and then their metered CAMPD energy, which is what the LP
loses. CAMPD is STATE-scoped, never ISO-scoped (SPP-47 trap (d)), so plants are
attributed to a region through the EIA-860 ``Balancing Authority Code`` FIRST
and the CAMPD panel is only ever read for those already-attributed plants.

Zero LP, zero solves, read-only. Run: PYTHONPATH=src python3 <this file>
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.fleet.models import ba_codes  # noqa: E402

EIA860 = REPO / "data" / "raw" / "eia-860"
CAMPD = REPO / "data" / "raw" / "campd-unit-level"
REGIONS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "SOCO", "NWPP")


def _campd_plant_year_mwh(plant: int, state: str, year: int) -> float:
    """Metered CAMPD gross load (MWh) for one plant-year, or NaN if no panel."""
    f = CAMPD / f"{state}_{year}.parquet"
    if not f.exists():
        return float("nan")
    d = pd.read_parquet(f, columns=["facilityId", "grossLoad"])
    sub = d[pd.to_numeric(d["facilityId"], errors="coerce") == plant]
    if sub.empty:
        return 0.0
    return float(pd.to_numeric(sub["grossLoad"], errors="coerce").fillna(0.0).sum())


def census(region: str, year: int) -> list[dict]:
    """Mid-vintage-year retirees dropped by the gap, for one region-year."""
    vdir = EIA860 / f"vintage_{year}"
    if not vdir.is_dir():
        # No native vintage => active dir is the canonical snapshot, whose
        # retiree parquet IS present and DOES carry these plants. No defect.
        return []
    ret = vdir / "eia860_generator_retired_and_canceled.parquet"
    ope = vdir / "eia860_generator_operable.parquet"
    pl = vdir / "eia860_plant.parquet"
    if not (ret.exists() and ope.exists() and pl.exists()):
        return []

    plants = pd.read_parquet(pl, columns=["Plant Code", "Balancing Authority Code", "State"])
    codes = set(ba_codes(region))
    if not codes:
        return []
    keep = plants[plants["Balancing Authority Code"].astype(str).str.strip().isin(codes)]
    in_region = set(pd.to_numeric(keep["Plant Code"], errors="coerce").dropna().astype(int))
    state_of = {
        int(p): str(s).strip()
        for p, s in zip(keep["Plant Code"], keep["State"])
        if pd.notna(p)
    }

    r = pd.read_parquet(ret)
    r = r[pd.to_numeric(r["Plant Code"], errors="coerce").isin(in_region)]
    r = r[pd.to_numeric(r["Retirement Year"], errors="coerce") == year]
    if r.empty:
        return []

    o = pd.read_parquet(ope, columns=["Plant Code"])
    operable_plants = set(pd.to_numeric(o["Plant Code"], errors="coerce").dropna().astype(int))

    rows = []
    for plant, grp in r.groupby(pd.to_numeric(r["Plant Code"], errors="coerce").astype(int)):
        dropped = plant not in operable_plants  # whole plant gone from operable
        mw = float(pd.to_numeric(grp["Summer Capacity (MW)"], errors="coerce").fillna(0.0).sum())
        mwh = _campd_plant_year_mwh(plant, state_of.get(plant, ""), year)
        rows.append(
            {
                "region": region,
                "year": year,
                "plant": plant,
                "name": str(grp["Plant Name"].iloc[0]).strip(),
                "state": state_of.get(plant, ""),
                "units": len(grp),
                "summer_mw": round(mw, 1),
                "ret_month": grp["Retirement Month"].iloc[0],
                "whole_plant_dropped": dropped,
                "campd_mwh": mwh,
            }
        )
    return rows


def main() -> None:
    all_rows: list[dict] = []
    years = sorted(int(p.name.split("_")[1]) for p in EIA860.glob("vintage_*") if p.is_dir())
    print(f"native vintages on disk: {years}\n")
    for region in REGIONS:
        for year in years:
            all_rows.extend(census(region, year))

    df = pd.DataFrame(all_rows)
    if df.empty:
        print("no mid-vintage-year retirees anywhere")
        return

    # The LOSS is a plant whose whole record left the operable sheet AND which
    # actually ran: that is exactly what the LP drops.
    lost = df[df["whole_plant_dropped"] & (df["campd_mwh"].fillna(0.0) > 0.0)]

    print("=" * 96)
    print("A. ALL mid-vintage-year retirees, by region-year (count / whole-plant-dropped / GWh lost)")
    print("=" * 96)
    g = df.groupby(["region", "year"]).apply(
        lambda x: pd.Series(
            {
                "retirees": len(x),
                "dropped": int(x["whole_plant_dropped"].sum()),
                "dropped_with_energy": int(
                    (x["whole_plant_dropped"] & (x["campd_mwh"].fillna(0.0) > 0)).sum()
                ),
                "gwh_lost": round(
                    float(
                        x.loc[
                            x["whole_plant_dropped"] & (x["campd_mwh"].fillna(0.0) > 0),
                            "campd_mwh",
                        ].sum()
                    )
                    / 1000.0,
                    1,
                ),
            }
        ),
        include_groups=False,
    )
    print(g.to_string())

    print()
    print("=" * 96)
    print("B. THE ACTUAL LOSSES — plants dropped from the fleet WITH metered energy")
    print("=" * 96)
    if lost.empty:
        print("none")
    else:
        out = lost.copy()
        out["gwh"] = (out["campd_mwh"] / 1000.0).round(1)
        print(
            out[
                ["region", "year", "plant", "name", "state", "summer_mw", "ret_month", "gwh"]
            ]
            .sort_values(["region", "year", "gwh"], ascending=[True, True, False])
            .to_string(index=False)
        )
        print()
        print("per-region GWh lost:")
        print((lost.groupby("region")["campd_mwh"].sum() / 1000.0).round(1).to_string())


if __name__ == "__main__":
    main()
