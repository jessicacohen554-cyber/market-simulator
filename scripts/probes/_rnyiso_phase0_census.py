"""R-NYISO phase 0 (zero LP): per-year fleet census on the keeper recipe, pre-F1 vs HEAD default.

Rebuilds the NYISO keeper recipe (results/calibration/hydro3_nyiso_ror_span/meta.json)
through the sanctioned fleet-only path (replay_keeper.run_year_kwargs ->
run_calibration.run_year(fleet_only=True)) for every year 2019-2025 in two postures:

* ``pre``  -- the six F1 backcast-default flags forced False (the pre-F1 posture the
  keeper was solved on: canonical 2025ER snapshot, CT+CHP measured only);
* ``post`` -- HEAD defaults (year-matched EIA-860 vintage + every measured_* flag on),
  i.e. exactly what a shard replay at the pinned SHA solves.

Per posture-year it records the resolved EIA-860 vintage, thermal MW by class, MW whose
heat rate equals a HEAT_RATE_BINS value (the audit's §3a heuristic), MW-weighted heat
rate per class, and the heat-rate SOURCE per plant (which layer set the final rate),
which is how the rule-19 precedence between the measured CAMPD rates and the eGRID
repairs is checked. No LP is built.

``--diagnostic-solar-substitution`` (2019/2020 only): NYISO's solar shape reads a NEISO donor row
in ``data/raw/eia-930/eia_generation_profiles.parquet``, which starts at 2021, so a 2019/2020 fleet
build raises before the fleet arrays exist. With this flag the absent (iso, year) rows are replaced by
that ISO's 2021 rows FOR THIS CENSUS ONLY -- the thermal fleet, heat rates and outage overlay do not
read the generation profiles, so the thermal census is unaffected. It is never a solve input, and every
record built under it is stamped ``diagnostic_solar_substitution: true``.

Usage:
    python scripts/probes/_rnyiso_phase0_census.py --years 2021 2022 2023 2024 2025 \
        --out results/calibration/_rnyiso_phase0_census.json
    python scripts/probes/_rnyiso_phase0_census.py --years 2019 2020 --diagnostic-solar-substitution \
        --out results/calibration/_rnyiso_phase0_census.json
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

BUNDLE = REPO / "results/calibration/hydro3_nyiso_ror_span"
F1_FLAGS = (
    "eia860_vintage_tracks_solve_year",
    "measured_ct_heat_rates",
    "measured_coal_heat_rates",
    "measured_st_heat_rates",
    "measured_cc_heat_rates",
    "measured_chp_heat_rates",
)
THERMAL = ("coal", "gas_cc", "gas_ct", "gas_st", "oil")


def _bin_value(fuel: str, hr: float) -> bool:
    from market_sim.config.constants import HEAT_RATE_BINS

    return any(abs(hr - v) < 1e-9 for v in HEAT_RATE_BINS.get(fuel, {}).values())


def build(year: int, posture: str) -> dict:
    """Fleet-only rebuild of the keeper recipe for one year/posture."""
    from scripts.replay_keeper import run_year_kwargs
    from scripts.run_calibration import run_year
    from scripts import run_calibration_full as rcf

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    prb = dict(kw.get("prb_overrides") or {})
    if posture == "pre":
        for f in F1_FLAGS:
            prb[f] = False
        # measured_ct / measured_chp were ON in the keeper -- keep the keeper posture
        prb["measured_ct_heat_rates"] = True
        prb["measured_chp_heat_rates"] = True
        for k in ("measured_st_heat_rates", "measured_coal_heat_rates"):
            if k in kw:
                kw[k] = False
    kw["prb_overrides"] = prb
    ref = rcf._load_reference()
    gp = rcf._henry_hub_actual(ref, year)
    built = run_year(year, meta["iso"], 8760, gp, {}, fleet_only=True, **kw)
    cfg = built["config"]
    fleet = built["fleet"]
    by_cls = defaultdict(lambda: {"mw": 0.0, "hr_mw": 0.0, "bin_mw": 0.0})
    plants = {}
    for g in fleet:
        fuel = str(getattr(g, "fuel_type", ""))
        if fuel not in THERMAL:
            continue
        pm = float(getattr(g, "pmax_mw", 0.0) or 0.0)
        hr = float(getattr(g, "heat_rate", 0.0) or 0.0)
        cls = str(getattr(g, "plant_group", "") or fuel)
        d = by_cls[cls]
        d["mw"] += pm
        d["hr_mw"] += pm * hr
        if _bin_value(fuel, hr):
            d["bin_mw"] += pm
        pc = int(getattr(g, "plant_code", 0) or 0)
        p = plants.setdefault(
            pc,
            {
                "name": str(getattr(g, "name", "")),
                "cls": cls,
                "fuel": fuel,
                "mw": 0.0,
                "hr_mw": 0.0,
                "bin_mw": 0.0,
            },
        )
        p["mw"] += pm
        p["hr_mw"] += pm * hr
        if _bin_value(fuel, hr):
            p["bin_mw"] += pm
    out_cls = {
        c: {
            "mw": round(v["mw"], 1),
            "hr": round(v["hr_mw"] / v["mw"], 4) if v["mw"] else None,
            "bin_mw": round(v["bin_mw"], 1),
        }
        for c, v in sorted(by_cls.items())
    }
    out_pl = {
        pc: {
            "name": v["name"],
            "cls": v["cls"],
            "fuel": v["fuel"],
            "mw": round(v["mw"], 1),
            "hr": round(v["hr_mw"] / v["mw"], 4) if v["mw"] else None,
            "bin_mw": round(v["bin_mw"], 1),
        }
        for pc, v in plants.items()
    }
    from market_sim.config.paths import active_eia860_dir

    return {
        "eia860_dir": active_eia860_dir().name,
        "eia860_vintage_year": getattr(cfg, "eia860_vintage_year", None),
        "flags": {
            f: getattr(cfg, f, None)
            for f in F1_FLAGS
            + (
                "egrid_identity_heat_rates",
                "egrid_family_heat_rates",
                "egrid_steam_collapse_heat_rates",
                "unit_partial_outage_windows",
                "unit_outage_short_windows",
                "unit_outage_short_windows_gas",
                "mode",
            )
        },
        "thermal_mw": round(sum(v["mw"] for v in out_cls.values()), 1),
        "bin_mw": round(sum(v["bin_mw"] for v in out_cls.values()), 1),
        "by_class": out_cls,
        "plants": out_pl,
        "n_units": len(fleet),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--postures", nargs="+", default=["pre", "post"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--diagnostic-solar-substitution", action="store_true")
    args = ap.parse_args()
    if args.diagnostic_solar_substitution:
        import market_sim.data.renewables as ren

        orig = ren.load_generation_profiles

        def _substituted(iso, year, *a):
            try:
                return orig(iso, year, *a)
            except ValueError:
                df = orig(iso, 2021, *a).copy()
                df["year"] = year
                return df

        ren.load_generation_profiles = _substituted
    logging.basicConfig(level=logging.WARNING)
    out = {}
    p = Path(args.out)
    if p.exists():
        out = json.loads(p.read_text())
    for y in args.years:
        for posture in args.postures:
            key = f"{posture}_{y}"
            try:
                out[key] = build(y, posture)
                r = out[key]
                if args.diagnostic_solar_substitution:
                    r["diagnostic_solar_substitution"] = True
                print(
                    key,
                    "eia860",
                    r["eia860_dir"],
                    "thermal",
                    r["thermal_mw"],
                    "bin",
                    r["bin_mw"],
                    flush=True,
                )
            except Exception as e:  # report, never hide
                out[key] = {"error": f"{type(e).__name__}: {e}"}
                print(key, "ERROR", type(e).__name__, str(e)[:500], flush=True)
            p.write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
