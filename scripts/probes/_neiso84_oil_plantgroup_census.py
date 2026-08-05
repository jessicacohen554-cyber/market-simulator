"""neiso-84 Phase-0 census: the oil-unit ``plant_group`` gap, all six ISOs.

NO LP. Reads committed artifacts only — the EIA-860 fleet each ISO's outage
deriver itself loads, the committed ``campd-unit-outages-<ISO>.csv`` extracts,
and CAMPD unit-level metadata (``unitType`` / ``primaryFuelInfo``).

Measures the blast radius of the defect filed by neiso-83 §5(c):
``data/fleet/eia860.py`` assigns ``plant_group`` only to coal and gas, so every
oil unit carries an EMPTY group. Two consequences follow mechanically:

  (1) ``outages._iso_plant_capacity`` skips every group-less unit (its
      ``if code <= 0 or not g.plant_group: continue``), so an oil unit's
      capacity is absent from the derate DENOMINATOR.
  (2) ``derive_campd_unit_outages._resolve_unit_group`` short-circuits at
      ``if fac_group in QUALIFYING_PLANT_GROUPS and fac_group != "COAL"`` —
      BEFORE it ever consults the unit's own ``unitType`` — so at a plant whose
      only MODELLED group is a single gas bin, every non-coal CAMPD unit's
      outage window is routed to that bin, oil peakers included.

Emits JSON: per-ISO fleet gap (A), per-ISO exposed-plant census (B).
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    load_fleet_from_csv,
    load_retired_within_window,
)

ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]
RAW = Path("data/raw")
# The deriver's own gas-bin vocabulary (QUALIFYING_PLANT_GROUPS minus COAL).
UNIT_LEVEL = RAW / "campd-unit-level"


def fleet_for(iso: str):
    cfg = get_iso_config(iso)
    return load_fleet_from_csv(iso, cfg) + load_retired_within_window(iso, cfg)


def census_a() -> dict:
    """Fleet-side gap: units carrying NO plant_group, by fuel, per ISO."""
    out = {}
    for iso in ISOS:
        by_fuel = defaultdict(lambda: {"units": 0, "mw": 0.0})
        tot = {"units": 0, "mw": 0.0}
        for g in fleet_for(iso):
            fuel = str(getattr(g, "fuel_type", "") or "?")
            mw = float(getattr(g, "pmax_mw", 0.0) or 0.0)
            tot["units"] += 1
            tot["mw"] += mw
            if not g.plant_group:
                by_fuel[fuel]["units"] += 1
                by_fuel[fuel]["mw"] += mw
        out[iso] = {
            "fleet_units": tot["units"],
            "fleet_mw": round(tot["mw"], 1),
            "no_group": {
                k: {"units": v["units"], "mw": round(v["mw"], 1)}
                for k, v in sorted(by_fuel.items(), key=lambda kv: -kv[1]["mw"])
            },
            "no_group_units": sum(v["units"] for v in by_fuel.values()),
            "no_group_mw": round(sum(v["mw"] for v in by_fuel.values()), 1),
        }
    return out


def unit_meta(states: set[str], years=(2023, 2024, 2025)) -> pd.DataFrame:
    """Unique (facilityId, unitId) -> unitType / primaryFuelInfo from CAMPD."""
    frames = []
    for st in sorted(states):
        for y in years:
            f = UNIT_LEVEL / f"{st}_{y}.parquet"
            if not f.exists():
                continue
            d = pd.read_parquet(
                f, columns=["facilityId", "unitId", "unitType", "primaryFuelInfo"]
            )
            frames.append(d.drop_duplicates(["facilityId", "unitId"]))
    if not frames:
        return pd.DataFrame(
            columns=["facilityId", "unitId", "unitType", "primaryFuelInfo"]
        )
    return pd.concat(frames).drop_duplicates(["facilityId", "unitId"])


def is_oil(fuel: str) -> bool:
    if fuel is None or (isinstance(fuel, float) and fuel != fuel):
        return False
    try:
        f = str(fuel).lower()
    except Exception:  # pragma: no cover - pandas NA sentinels
        return False
    if f in ("<na>", "nan", "none", ""):
        return False
    return "diesel" in f or "oil" in f or "residual" in f or "kerosene" in f


def bin_mismatch(unit_type: str, group: str) -> bool:
    """True when a CAMPD ``unitType`` is inconsistent with its routed model bin.

    Mirrors the deriver's OWN unitType branches (``_resolve_unit_group`` lines
    512-523) — which are exactly the branches the ``fac_group`` short-circuit at
    line 509 skips. A combustion turbine landing in a ``CC_*`` bin (NEISO 6081
    units 004/005) is the filed defect; a dual-fuel oil-fired STEAM unit landing
    in ``ST_GAS`` (PJM Martins Creek, NEISO Montville) is NOT — the model
    represents those machines in that bin, so a raw "oil unit in a gas bin"
    count over-states the exposure and is reported separately.
    """
    ut = "" if pd.isna(unit_type) else str(unit_type).strip().lower()
    g = "" if pd.isna(group) else str(group).strip()
    if not ut or not g:
        return False
    if "combined cycle" in ut:
        return not g.startswith("CC_")
    if "combustion turbine" in ut:
        return not g.startswith("CT_")
    # Everything else CAMPD reports is a boiler/steam machine.
    return g.startswith("CC_") or g.startswith("CT_")


def census_b(states_by_iso: dict[str, set[str]]) -> dict:
    """Exposure: plants where an oil unit's outage row lands in a gas bin."""
    out = {}
    for iso in ISOS:
        ext = RAW / f"campd-unit-outages-{iso}.csv"
        if not ext.exists():
            ext = RAW / f"campd-unit-outages-e923-{iso}.csv"
        if not ext.exists():
            out[iso] = {"extract": None}
            continue
        rows = pd.read_csv(ext)
        meta = unit_meta(states_by_iso[iso])
        meta["unitId"] = meta["unitId"].astype(str)
        meta["facilityId"] = meta["facilityId"].astype("int64")
        rows["unit_id"] = rows["unit_id"].astype(str)
        rows["facility_id"] = rows["facility_id"].astype("int64")
        m = rows.merge(
            meta,
            left_on=["facility_id", "unit_id"],
            right_on=["facilityId", "unitId"],
            how="left",
        )
        m["oil_unit"] = m["primaryFuelInfo"].map(is_oil)
        m["mismatch"] = [
            bin_mismatch(ut, g)
            for ut, g in zip(m["unitType"], m["plant_group"], strict=False)
        ]
        # Superset: ANY unit whose type contradicts its routed bin (what the
        # line-509 short-circuit produces, oil or not).
        allmis = m[m["mismatch"]]
        # The FILED defect: an oil unit AND a type/bin contradiction.
        bad = m[m["oil_unit"].fillna(False) & m["mismatch"]]
        bad_plants = sorted(bad["facility_id"].unique().tolist())
        # Reported separately: oil unit in a gas bin with a CONSISTENT type
        # (dual-fuel steam in ST_GAS) — correctly modelled, not a defect.
        oil_in_gas = m[m["oil_unit"].fillna(False) & m["plant_group"].notna()]
        # Per exposed plant: are the oil rows the plant's ONLY outage source?
        detail = []
        for pid in bad_plants:
            allrows = m[m["facility_id"] == pid]
            oilrows = allrows[allrows["oil_unit"].fillna(False) & allrows["mismatch"]]
            detail.append(
                {
                    "facility_id": int(pid),
                    "facility_name": str(allrows["facility_name"].iloc[0]),
                    "groups": sorted(
                        {str(g) for g in allrows["plant_group"].dropna().unique()}
                    ),
                    "rows_total": int(len(allrows)),
                    "rows_from_oil_units": int(len(oilrows)),
                    "oil_only_source": bool(len(oilrows) == len(allrows)),
                    "oil_unit_ids": sorted({str(u) for u in oilrows["unit_id"]}),
                    "oil_unit_types": sorted(
                        {str(t) for t in oilrows["unitType"].dropna()}
                    ),
                    "oil_mw": round(
                        float(
                            oilrows.drop_duplicates("unit_id")["unit_capacity_mw"].sum()
                        ),
                        1,
                    ),
                }
            )
        detail.sort(key=lambda d: -d["rows_from_oil_units"])
        out[iso] = {
            "extract": ext.name,
            "rows": int(len(rows)),
            "rows_matched_to_campd_meta": int(m["primaryFuelInfo"].notna().sum()),
            "rows_oil_unit_in_any_gas_bin": int(len(oil_in_gas)),
            "rows_any_unit_type_bin_mismatch": int(len(allmis)),
            "rows_from_oil_units_in_gas_bins": int(len(bad)),
            "exposed_plants": len(bad_plants),
            "exposed_plants_oil_only_source": sum(
                1 for d in detail if d["oil_only_source"]
            ),
            "detail": detail[:25],
        }
    return out


def main() -> None:
    states = {
        iso: {
            str(getattr(g, "state", "") or "")
            for g in fleet_for(iso)
            if getattr(g, "state", None)
        }
        for iso in ISOS
    }
    res = {
        "note": "neiso-84 Phase-0 census, NO LP. See module docstring.",
        "states_by_iso": {k: sorted(v) for k, v in states.items()},
        "A_fleet_group_gap": census_a(),
        "B_outage_routing_exposure": census_b(states),
    }
    p = Path("results/calibration/_neiso84_oil_plantgroup_census.json")
    p.write_text(json.dumps(res, indent=1))
    print(json.dumps(res["A_fleet_group_gap"], indent=1))
    print("WROTE", p)


if __name__ == "__main__":
    main()
