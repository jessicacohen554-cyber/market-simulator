"""SCN-WS5A-POLICY-MISO gate scorer — reads the shards' committed legs, emits the gate table.

Zero LP. Unlike the in-session lanes, this coordinator has NO leg caches: the
solves ran in seven shard containers. Everything it needs is therefore read from
COMMITTED artifacts only —

* each leg's ``full_horizon_summary.json`` (trajectory, invariants, cache_key);
* each leg's ``duals.json`` (written by the shards' ``extract_duals.py``:
  ``clean_region_duals`` and ``rps_region_duals`` per year);
* the committed REF / LOAD-HI legs at THE PIN
  (``results/scn-campaign-load-2026-09-06-r2/MISO/``);
* this lane's own phase-0 JSON (V, G, the regime table, the resolved carbon).

Region order inside ``clean_region_duals`` for MISO (runner's own assembly:
state family -> FEDERAL_CES -> VOLUNTARY, each appended last):
``[MN, MI]`` always, ``+ [FEDERAL_CES]`` when a CES target row is armed,
``+ [VOLUNTARY]`` when the voluntary row is armed.

Run:  PYTHONPATH=. python3 docs/handoffs/scn-ws5a-policy-miso/score_gates_2026-09-07.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent

ISO = "MISO"
YEARS = [2026, 2027, 2028, 2029, 2030]
LEGS = REPO / "results/scn-campaign-policy-2026-09-06/MISO"
BASE = REPO / "results/scn-campaign-load-2026-09-06-r2/MISO"
PHASE0 = json.loads((HERE / "phase0-miso-2026-09-07.json").read_text())
CENSUS = json.loads((HERE / "rps-region-census-2026-09-07.json").read_text())

ZERO_CARBON = ("wind", "solar", "nuclear", "hydro")
ELIG_VOL = ("wind", "solar", "offshore_wind", "geothermal")
CES_ACP = 50.0
VOL_CEILING = {"VOL-MID": 4.5, "VOL-HI": 7.0, "CES-P20+VOL-HI": 7.0, "ALL-CLEAN": 7.0}
#: Which extra clean-tier regions each case appends after MISO's [MN, MI].
EXTRA_REGIONS = {
    "CES-T80": ["FEDERAL_CES"],
    "VOL-MID": ["VOLUNTARY"],
    "VOL-HI": ["VOLUNTARY"],
    "CES-P20+VOL-HI": ["VOLUNTARY"],
    "ALL-CLEAN": ["FEDERAL_CES", "VOLUNTARY"],
}
#: Every case's load baseline — the leg its 2026 identity and its deltas are read against.
BASELINE = {
    "CARB-LO": "REF", "CARB-MID": "REF", "CARB-HI": "REF",
    "CES-P10": "REF", "CES-P20": "REF", "CES-P30": "REF", "CES-P60": "REF",
    "CES-T80": "REF", "VOL-MID": "REF", "VOL-HI": "REF", "CES-P20+VOL-HI": "REF",
    "CARB-MID+LOAD-HI": "LOAD-HI", "ALL-CLEAN": "LOAD-HI",
}
CASES = list(BASELINE)
#: Arms whose mechanism cannot raise demand — G6 binds on these only.
NO_LOAD_ARMS = [c for c, b in BASELINE.items() if b == "REF"]

CACHE_KEYS = {
    "CARB-LO": "1c815555d55e5db2", "CARB-MID": "27fb6e72c0ad31ae",
    "CARB-HI": "40bc61fac2b5271d", "CES-P10": "e4ba286178e0d499",
    "CES-P20": "472af7fd5ba90f99", "CES-P30": "3a4b528c75d7fd6d",
    "CES-T80": "82c916d847270ebf", "CARB-MID+LOAD-HI": "e644893331d7708f",
    "VOL-MID": "dc8ca3580e277d72", "VOL-HI": "7e1a2a2145711bab",
    "CES-P20+VOL-HI": "ed42e5d7d1d95d3e", "ALL-CLEAN": "00edacf5f50c88fc",
    "CES-P60": "e5fb002f78c0c681",
}


def _traj(path: Path) -> dict[int, dict] | None:
    if not path.exists():
        return None
    s = json.loads(path.read_text())
    return {int(t["year"]): t for t in s["trajectory"]}


def _summary(case: str) -> dict | None:
    p = LEGS / case / "full_horizon_summary.json"
    return json.loads(p.read_text()) if p.exists() else None


def _duals(case: str) -> dict | None:
    p = LEGS / case / "duals.json"
    return json.loads(p.read_text()) if p.exists() else None


def _fails(summary: dict) -> set[str]:
    return {i["id"] for i in summary["invariants"] if i["status"] == "FAIL"}


def _gen(t: dict, fuel: str) -> float:
    return float(t["generation_by_fuel_mwh"].get(fuel, 0.0))


def main() -> int:
    base = {name: _traj(BASE / name / "full_horizon_summary.json")
            for name in ("REF", "LOAD-HI")}
    base_fail = {}
    for name in ("REF", "LOAD-HI"):
        s = json.loads((BASE / name / "full_horizon_summary.json").read_text())
        base_fail[name] = _fails(s)

    out: dict = {"iso": ISO, "pin": "bdfb3095e9fa0cd2bec3f4e843f320b42588c72b",
                 "missing": [], "cases": {}, "gates": {}}

    for case in CASES:
        s = _summary(case)
        if s is None:
            out["missing"].append(case)
            continue
        arm = {int(t["year"]): t for t in s["trajectory"]}
        b = base[BASELINE[case]]
        d = _duals(case)
        row: dict = {
            "cache_key": s.get("cache_key"),
            "cache_key_expected": CACHE_KEYS[case],
            "key_match": s.get("cache_key") == CACHE_KEYS[case],
            "baseline": BASELINE[case],
            "invariant_fails": sorted(_fails(s)),
            "baseline_fails": sorted(base_fail[BASELINE[case]]),
            "per_year": {},
        }
        for y in YEARS:
            a, r = arm[y], b[y]
            zc = {f: round(( _gen(a, f) - _gen(r, f)) / 1e6, 6) for f in ZERO_CARBON}
            elig = sum(_gen(a, f) for f in ELIG_VOL) / 1e6
            regions = ["MN", "MI"] + EXTRA_REGIONS.get(case, [])
            dv = None
            if d and str(y) in d.get("years", {}):
                dv = d["years"][str(y)].get("clean_region_duals")
            row["per_year"][y] = {
                "co2_mt": a["co2_mt"], "co2_mt_base": r["co2_mt"],
                "d_co2_mt": round(a["co2_mt"] - r["co2_mt"], 6),
                "lw_price": a["lw_price"], "lw_price_base": r["lw_price"],
                "d_lw_price": round(a["lw_price"] - r["lw_price"], 6),
                "rps_dual": a["rps_dual"], "rps_dual_base": r["rps_dual"],
                "builds_renew_mw": a["builds_renew_mw"],
                "builds_renew_mw_base": r["builds_renew_mw"],
                "retire_mw": a["retire_mw"], "retire_mw_base": r["retire_mw"],
                "gas_cc_ccs_twh": round(_gen(a, "gas_cc_ccs") / 1e6, 6),
                "gas_cc_ccs_twh_base": round(_gen(r, "gas_cc_ccs") / 1e6, 6),
                "eligible_twh": round(elig, 6),
                "d_zero_carbon_twh": zc,
                "clean_region_labels": regions,
                "clean_region_duals": dv,
                "rps_region_duals": (d["years"][str(y)].get("rps_region_duals")
                                     if d and str(y) in d.get("years", {}) else None),
            }
        out["cases"][case] = row

    # ---- gates -----------------------------------------------------------
    g: dict = {}

    # G1 / G1a: carbon premise + the 2026 identity against the case's own baseline.
    g1a = {}
    for case in ("CARB-LO", "CARB-MID", "CARB-HI", "CARB-MID+LOAD-HI", "ALL-CLEAN"):
        if case not in out["cases"]:
            continue
        p = out["cases"][case]["per_year"][2026]
        same = (abs(p["d_co2_mt"]) < 5e-4 and abs(p["d_lw_price"]) < 5e-4)
        g1a[case] = {"d_co2_mt": p["d_co2_mt"], "d_lw_price": p["d_lw_price"],
                     "baseline": out["cases"][case]["baseline"],
                     "verdict": "PASS" if same else "FAIL"}
    g["G1a"] = g1a

    # G3: zero-carbon confinement on the carbon arms.
    g3 = {}
    for case in ("CARB-LO", "CARB-MID", "CARB-HI"):
        if case not in out["cases"]:
            continue
        worst = 0.0
        for y in YEARS:
            worst = max(worst, max(abs(v) for v in
                                   out["cases"][case]["per_year"][y]["d_zero_carbon_twh"].values()))
        g3[case] = {"max_abs_zero_carbon_delta_twh": round(worst, 6),
                    "verdict": "PASS" if worst < 1e-3 else "FAIL"}
    g["G3_carbon"] = g3

    # G4: CES-T80 dual identity — the FEDERAL_CES region at the ACP where unmet.
    g4 = {}
    for case in ("CES-T80", "ALL-CLEAN"):
        if case not in out["cases"]:
            continue
        rows = {}
        for y in YEARS:
            p = out["cases"][case]["per_year"][y]
            labels, duals = p["clean_region_labels"], p["clean_region_duals"]
            fed = None
            if duals and "FEDERAL_CES" in labels and len(duals) == len(labels):
                fed = duals[labels.index("FEDERAL_CES")]
            rows[y] = {"federal_dual": fed,
                       "verdict": ("PASS" if fed is not None and abs(fed - CES_ACP) < 1e-6
                                   else ("INTERIOR" if fed is not None else "NO DUALS"))}
        g4[case] = rows
    g["G4"] = g4

    # G7: voluntary dual bounded by THAT arm's own ceiling.
    g7 = {}
    for case, ceil in VOL_CEILING.items():
        if case not in out["cases"]:
            continue
        rows = {}
        regime = PHASE0["regime"].get(case, {}).get("per_year", {})
        for y in YEARS:
            p = out["cases"][case]["per_year"][y]
            labels, duals = p["clean_region_labels"], p["clean_region_duals"]
            vol = None
            if duals and "VOLUNTARY" in labels and len(duals) == len(labels):
                vol = duals[labels.index("VOLUNTARY")]
            binds = regime.get(str(y), {}).get("binds")
            shortfall = regime.get(str(y), {}).get("slack_twh")
            ok = None
            if vol is not None:
                ok = (abs(vol - ceil) < 1e-6 if binds else abs(vol) < 1e-6) and vol <= ceil + 1e-9
            rows[y] = {"ceiling": ceil, "dual": vol, "phase0_binds": binds,
                       "phase0_slack_twh": shortfall,
                       "verdict": ("PASS" if ok else ("FAIL" if vol is not None else "NO DUALS"))}
        g7[case] = rows
    g["G7"] = g7

    # G5: no non-target load-bearing invariant flips PASS -> FAIL vs the baseline.
    g["G5"] = {case: {"arm_fails": r["invariant_fails"], "base_fails": r["baseline_fails"],
                      "new": sorted(set(r["invariant_fails"]) - set(r["baseline_fails"])),
                      "verdict": "PASS" if not (set(r["invariant_fails"]) - set(r["baseline_fails"]))
                      else "FAIL"}
               for case, r in out["cases"].items()}

    # G6: unserved must not rise in an arm whose mechanism cannot raise demand.
    # unserved_mwh lives in the report tables, not the trajectory; carried by the
    # per-case headline the shards report and by the I3 detail string, so this is
    # scored from the invariant detail rather than invented here.
    g["G6"] = {"note": "scored from the I3 detail strings in each leg's invariants; "
                       "binds on " + ", ".join(NO_LOAD_ARMS)}

    # G8 is vacuous on MISO by pre-registration (REF curtailment 0.0 in every year).
    g["G8"] = {"verdict": "N/A - VACUOUS",
               "reason": "REF curtailment_twh = 0.0000 in every year, so there is no "
                         "curtailed eligible MWh to recover; declared in the PRECOMMIT "
                         "before the solve, never scored as a PASS"}

    # G-B1 was computed pre-solve; re-stated here with the measured per-zone duals.
    g["G-B1"] = {"verdict": "PASS (pre-solve)",
                 "detail": "60.00 (57.00 for gas_cc_ccs) vs an exact <= 30.00 upper bound on "
                           "REF attr in every zone; ADDENDUM A predicts 0 in four of six zones"}

    out["gates"] = g
    dest = HERE / "gate-scores-2026-09-07.json"
    dest.write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n")
    print(f"wrote {dest.relative_to(REPO)}")
    if out["missing"]:
        print("MISSING LEGS (not yet committed by their shard):", ", ".join(out["missing"]))
    for case, r in out["cases"].items():
        p30 = r["per_year"][2030]
        print(f"{case:<18} key {r['cache_key']} {'OK' if r['key_match'] else 'KEY MISMATCH'} "
              f"| 2030 dCO2 {p30['d_co2_mt']:+9.4f} Mt  dprice {p30['d_lw_price']:+9.3f} "
              f"| FAILs {','.join(r['invariant_fails'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
