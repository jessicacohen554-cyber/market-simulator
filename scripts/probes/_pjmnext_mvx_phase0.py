"""PJM-NEXT card 1 phase 0 (zero LP): mid_vintage_exit_carry fleet census on the R-PJM-2 keeper recipe.

Rebuilds the PJM keeper recipe (results/calibration/rpjm2_span/meta.json) through the
sanctioned fleet-only path (replay_keeper.run_year_kwargs -> run_calibration.run_year(
fleet_only=True)) for each year 2019-2025 in two postures -- ``off`` (the keeper),
``on`` (keeper + ``mid_vintage_exit_carry``) and ``onz`` (``on`` + ``fleet_zone_vintage_coords``) -- and records every LP unit the flag adds
or changes: plant, zone, class, pmax, retirement month, and the pmax-hours the COD ramp
leaves it online in the solved year. Answers, before any solve: which plants the flag
injects per year, whether any is already carried by another channel (rule 19 double
carry), and whether each lands in its real zone. No LP is built.

Usage:
    python scripts/probes/_pjmnext_mvx_phase0.py --years 2019 2020 --out <json>
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/rpjm2_span"


def _units(year: int, posture: str) -> dict:
    """Fleet-only rebuild of the keeper recipe for one year/posture."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year
    import market_sim.data.virtual_bids as _vb

    # DA virtuals are a gitignored corpus and append pseudo-units only; the
    # physical fleet under census does not read them (stated, census-only).
    _vb.build_pjm_da_virtual_units = lambda *a, **k: ([], {}, {})

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    prb = dict(kw.get("prb_overrides") or {})
    prb["mid_vintage_exit_carry"] = posture in ("on", "onz")
    prb["fleet_zone_vintage_coords"] = posture == "onz"
    kw["prb_overrides"] = prb
    gp = float(meta["gas_prices"][str(year)])
    built = run_year(year, meta["iso"], 8760, gp, {}, fleet_only=True, **kw)
    cfg = built["config"]
    assert bool(getattr(cfg, "mid_vintage_exit_carry", False)) == (
        posture in ("on", "onz")
    )
    assert bool(getattr(cfg, "fleet_zone_vintage_coords", False)) == (posture == "onz")
    fleet = built["fleet"]
    out = {}
    for g in fleet:
        out[g.unit_id] = {
            "plant": int(getattr(g, "plant_code", 0) or 0),
            "name": str(g.name),
            "zone": str(g.zone),
            "cls": str(getattr(g, "plant_group", "") or g.fuel_type),
            "fuel": str(g.fuel_type),
            "pmax": float(g.pmax_mw),
            "ret": [g.retirement_year, g.retirement_month],
            "mid": bool(getattr(g, "mid_vintage_exit_unit", False)),
        }
    return {"units": out, "keys": sorted(built.keys())}


def _geo_zone(plant: int, year: int) -> "str | None":
    """Zone the plant's OWN EIA-860 coordinates imply, from the solved year's vintage.

    Census-only reference (no model path reads it): the vintage_<year> plant
    file (canonical for 2025) lat/lon/state through the PJM zone rules, with
    the state FIPS from the plant file. ``None`` when the plant is absent.
    """
    import pandas as pd

    from market_sim.data import zone_assignment as za

    d = REPO / "data/raw/eia-860" / (f"vintage_{year}" if year <= 2024 else "")
    df = pd.read_parquet(d / "eia860_plant.parquet")
    df = df[pd.to_numeric(df["Plant Code"], errors="coerce") == plant]
    if df.empty:
        return None
    r = df.iloc[0]
    fips = za._STATE_POSTAL_TO_FIPS.get(str(r["State"]).strip().upper())
    return za._pjm_zone(float(r["Latitude"]), float(r["Longitude"]), fips, None)


def unzoned_census(units: dict, year: int) -> dict:
    """Plants in a fleet absent from the eGRID-2023 zone lookup, with their zones."""
    from collections import defaultdict as dd

    from market_sim.data.zone_assignment import build_zone_lookup

    lk = build_zone_lookup("PJM")
    agg = dd(lambda: {"mw": 0.0, "zones": set(), "cls": set(), "name": ""})
    for v in units.values():
        pc = v["plant"]
        if pc <= 0 or pc in lk:
            continue
        a = agg[pc]
        a["mw"] += v["pmax"]
        a["zones"].add(v["zone"])
        a["cls"].add(v["cls"])
        a["name"] = v["name"]
    return {
        str(pc): {
            "name": a["name"],
            "mw": round(a["mw"], 1),
            "zones": sorted(a["zones"]),
            "cls": sorted(a["cls"]),
            "geo_zone": _geo_zone(pc, year),
        }
        for pc, a in sorted(agg.items(), key=lambda kv: -kv[1]["mw"])
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    logging.basicConfig(level=logging.WARNING)
    p = Path(args.out)
    res = json.loads(p.read_text()) if p.exists() else {}
    for y in args.years:
        off = _units(y, "off")
        on = _units(y, "on")
        uo, un = off["units"], on["units"]
        added = {k: v for k, v in un.items() if k not in uo}
        removed = {k: v for k, v in uo.items() if k not in un}
        changed = {k: [uo[k], un[k]] for k in un if k in uo and un[k] != uo[k]}
        plants_off = defaultdict(float)
        for v in uo.values():
            plants_off[v["plant"]] += v["pmax"]
        by_plant = defaultdict(
            lambda: {"mw": 0.0, "zones": set(), "cls": set(), "ret": set(), "name": ""}
        )
        for v in added.values():
            b = by_plant[v["plant"]]
            b["mw"] += v["pmax"]
            b["zones"].add(v["zone"])
            b["cls"].add(v["cls"])
            b["ret"].add(tuple(v["ret"]))
            b["name"] = v["name"]
        res[str(y)] = {
            "n_off": len(uo),
            "n_on": len(un),
            "mw_off": round(sum(v["pmax"] for v in uo.values()), 1),
            "mw_on": round(sum(v["pmax"] for v in un.values()), 1),
            "added_n": len(added),
            "removed_n": len(removed),
            "changed_n": len(changed),
            "added_plants": {
                str(pc): {
                    "name": b["name"],
                    "mw": round(b["mw"], 1),
                    "zones": sorted(b["zones"]),
                    "cls": sorted(b["cls"]),
                    "ret": sorted(b["ret"]),
                    "plant_mw_in_off_fleet": round(plants_off.get(pc, 0.0), 1),
                }
                for pc, b in sorted(by_plant.items(), key=lambda kv: -kv[1]["mw"])
            },
            "removed": removed,
            "changed": changed,
            "unzoned_off": unzoned_census(uo, y),
            "unzoned_on": unzoned_census(un, y),
            "unzoned_onz": unzoned_census(_units(y, "onz")["units"], y),
            "fleet_keys": on["keys"],
        }
        print(
            y,
            {
                k: res[str(y)][k]
                for k in (
                    "n_off",
                    "n_on",
                    "mw_off",
                    "mw_on",
                    "added_n",
                    "removed_n",
                    "changed_n",
                )
            },
            flush=True,
        )
        p.write_text(json.dumps(res, indent=1, default=list))


if __name__ == "__main__":
    main()
