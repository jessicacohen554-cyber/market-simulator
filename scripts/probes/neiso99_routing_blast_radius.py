"""neiso-99 probe: blast radius of the CAMPD unit-outage group-routing repair.

Measures, for every ISO, which committed ``campd-unit-outages-<ISO>.csv`` rows
would change ``plant_group`` if :func:`_resolve_unit_group`'s ``fac_group``
short-circuit stopped overriding a unit's OWN CAMPD ``unitType`` /
``primaryFuelInfo``. Read-only: no CSV is rewritten, no LP is constructed.

Context: audit escalation O5's sibling (ASSESSMENT-neiso98 §4.2). Plant 6081
Stony Brook's units 004/005 are CAMPD "Combustion turbine" / "Diesel Oil"
peakers that inherit ``plant_group=CC_REGULAR`` from their three combined-cycle
siblings, derating a fully-available CC block on machines that are not in it.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    load_fleet_from_csv,
    load_retired_within_window,
)

ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]


def campd_unit_attrs(iso: str, years: range) -> dict[tuple[int, str], dict]:
    """Return ``{(facilityId, unitId): {unitType, primaryFuelInfo}}`` for an ISO."""
    states = campd.states_for_iso(iso)
    out: dict[tuple[int, str], dict] = {}
    for st in states:
        for y in years:
            f = RAW_DATA_DIR / "campd-unit-level" / f"{st}_{y}.parquet"
            if not f.exists():
                continue
            df = pd.read_parquet(
                f, columns=["facilityId", "unitId", "unitType", "primaryFuelInfo"]
            ).drop_duplicates()
            for r in df.itertuples(index=False):
                out[(int(r.facilityId), str(r.unitId))] = {
                    "unitType": str(r.unitType),
                    "fuel": str(r.primaryFuelInfo),
                }
    return out


def fleet_groups(iso: str) -> tuple[dict[int, str], dict[int, set], dict[int, list]]:
    """Return the deriver's own ``group_by_code`` / ``groups_by_code`` plus fleet rows."""
    cfg = get_iso_config(iso)
    fleet = load_fleet_from_csv(iso, cfg) + load_retired_within_window(iso, cfg)
    group_by_code: dict[int, str] = {}
    groups_by_code: dict[int, set] = defaultdict(set)
    rows_by_code: dict[int, list] = defaultdict(list)
    for g in fleet:
        code = int(g.plant_code)
        if code <= 0:
            continue
        rows_by_code[code].append(
            {"group": g.plant_group, "fuel": g.fuel_type, "pmax": float(g.pmax_mw)}
        )
        if g.plant_group:
            group_by_code[code] = g.plant_group
            groups_by_code[code].add(g.plant_group)
    return group_by_code, groups_by_code, rows_by_code


def main() -> None:
    """Measure the routing repair's blast radius across all six ISOs."""
    result: dict[str, dict] = {}
    for iso in ISOS:
        fname = (
            "campd-unit-outages.csv"
            if iso == "ERCOT"
            else f"campd-unit-outages-{iso}.csv"
        )
        path = RAW_DATA_DIR / fname
        if not path.exists():
            result[iso] = {"error": f"missing {fname}"}
            continue
        df = pd.read_csv(path)
        attrs = campd_unit_attrs(iso, range(2018, 2027))
        _, groups_by_code, rows_by_code = fleet_groups(iso)

        # Candidate rows: the unit's own CAMPD unitType says COMBUSTION TURBINE
        # while the row was written into a NON-CT bin (the short-circuit's work).
        flagged: dict[tuple[int, str], dict] = {}
        for r in df.itertuples(index=False):
            key = (int(r.facility_id), str(r.unit_id))
            a = attrs.get(key)
            if a is None:
                continue
            ut = a["unitType"].strip().lower()
            grp = str(r.plant_group)
            if "combustion turbine" in ut and not grp.startswith("CT"):
                e = flagged.setdefault(
                    key,
                    {
                        "facility_name": r.facility_name,
                        "plant_group_written": grp,
                        "unitType": a["unitType"],
                        "primaryFuelInfo": a["fuel"],
                        "unit_capacity_mw": float(r.unit_capacity_mw),
                        "rows": 0,
                        "fleet_bins": sorted(groups_by_code.get(key[0], set())),
                        "fleet_rows": rows_by_code.get(key[0], []),
                    },
                )
                e["rows"] += 1
        result[iso] = {
            "csv": fname,
            "total_rows": int(len(df)),
            "flagged_units": len(flagged),
            "flagged_rows": sum(v["rows"] for v in flagged.values()),
            "units": {f"{k[0]}:{k[1]}": v for k, v in sorted(flagged.items())},
        }
        print(
            f"{iso}: {len(df)} rows, {len(flagged)} CT-in-non-CT-bin units, "
            f"{sum(v['rows'] for v in flagged.values())} rows"
        )
        for k, v in sorted(flagged.items()):
            print(
                f"   {k[0]}:{k[1]} {v['facility_name'][:34]:34s} "
                f"-> {v['plant_group_written']:11s} fuel={v['primaryFuelInfo'][:22]:22s} "
                f"cap={v['unit_capacity_mw']:7.1f} rows={v['rows']:3d} "
                f"bins={v['fleet_bins']}"
            )

    out = ROOT / "results" / "calibration" / "_neiso99_routing_blast_radius.json"
    out.write_text(json.dumps(result, indent=1, sort_keys=True, default=str))
    print("\nwrote", out)


if __name__ == "__main__":
    main()
