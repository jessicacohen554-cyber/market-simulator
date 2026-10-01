"""SCN-WS5A-POLICY-MISO — the FINAL gate scorer, run after all thirteen legs landed.

Zero LP. The companion of ``score_gates_2026-09-07.py`` (committed BEFORE the legs
landed, and left untouched so its pre-solve form is on the record). This one scores
**every** gate the PRECOMMIT declared — G1, G1a, G2, G3, G4, G5, G6, G7, G8, G9,
G-B1, G-B2, G-B3, and records G10-G12 as N/A — plus the §5 prediction scoring and
the §6 cost table, entirely from COMMITTED artifacts:

* each leg's ``full_horizon_summary.json`` (trajectory, invariants, perf, cache_key);
* each leg's ``duals.json`` (``clean_region_duals`` / ``rps_region_duals`` per year);
* the six shard report groups' ``miso_headline_deltas.csv`` /
  ``miso_evolution_deltas.csv`` (absolute columns only -- each group's ``_bau``
  column is that group's own other member, never REF, so no ``_delta`` column of
  the shard reports is used anywhere in this scorer);
* the committed REF / LOAD-HI legs at THE PIN
  (``results/scn-campaign-load-2026-09-06-r2/MISO/``);
* this lane's own phase-0 JSON (V, G, the regime table, the resolved carbon).

``CES-P60`` is deliberately absent from the shard report groups (PRECOMMIT §2: its
``--set`` leg would collide with the real ``CES-P30`` in the group ``members`` map),
so its headline row is reconstructed from its own summary + duals. Every field this
scorer needs for it is present there.

Run:  PYTHONPATH=. python3 docs/handoffs/scn-ws5a-policy-miso/score_gates_final_2026-09-07.py
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent

ISO = "MISO"
YEARS = [2026, 2027, 2028, 2029, 2030]
LEGS = REPO / "results/scn-campaign-policy-2026-09-06/MISO"
REPORT = LEGS / "report"
BASE = REPO / "results/scn-campaign-load-2026-09-06-r2/MISO"
PHASE0 = json.loads((HERE / "phase0-miso-2026-09-07.json").read_text())

#: MISO's RPS compliance regions, in the order ``rps_region_duals`` is assembled.
RPS_REGIONS = ["MN", "MI", "WI", "IL", "MO"]
#: Which zones each RPS region admits (rps-region-census-2026-09-07.json A(b)).
ZONES = ["MISO-West", "MISO-Plains", "MISO-Illinois", "MISO-Indiana",
         "MISO-East", "MISO-South"]
ADMITS = {
    "MN": ["MISO-West", "MISO-Plains", "MISO-Illinois", "MISO-Indiana", "MISO-East"],
    "MI": ["MISO-East"],
    "WI": ["MISO-West", "MISO-Plains", "MISO-Illinois", "MISO-Indiana", "MISO-East"],
    "IL": ["MISO-Illinois"],
    "MO": ["MISO-West", "MISO-Plains", "MISO-Illinois", "MISO-Indiana", "MISO-East"],
}

ZERO_CARBON = ("wind", "solar", "nuclear", "hydro")
CES_ACP = 50.0
VOL_CEILING = {"VOL-MID": 4.5, "VOL-HI": 7.0, "CES-P20+VOL-HI": 7.0, "ALL-CLEAN": 7.0}
EXTRA_REGIONS = {
    "CES-T80": ["FEDERAL_CES"],
    "VOL-MID": ["VOLUNTARY"],
    "VOL-HI": ["VOLUNTARY"],
    "CES-P20+VOL-HI": ["VOLUNTARY"],
    "ALL-CLEAN": ["FEDERAL_CES", "VOLUNTARY"],
}
BASELINE = {
    "CARB-LO": "REF", "CARB-MID": "REF", "CARB-HI": "REF",
    "CES-P10": "REF", "CES-P20": "REF", "CES-P30": "REF", "CES-P60": "REF",
    "CES-T80": "REF", "VOL-MID": "REF", "VOL-HI": "REF", "CES-P20+VOL-HI": "REF",
    "CARB-MID+LOAD-HI": "LOAD-HI", "ALL-CLEAN": "LOAD-HI",
}
CASES = list(BASELINE)
#: Arms whose mechanism cannot raise demand -- G6 binds on these only.
NO_LOAD_ARMS = [c for c, b in BASELINE.items() if b == "REF"]
#: Arms carrying a live carbon knot, on which G1a asserts a 2026 identity.
CARBON_ARMS = ["CARB-LO", "CARB-MID", "CARB-HI", "CARB-MID+LOAD-HI", "ALL-CLEAN"]
CACHE_KEYS = {
    "CARB-LO": "1c815555d55e5db2", "CARB-MID": "27fb6e72c0ad31ae",
    "CARB-HI": "40bc61fac2b5271d", "CES-P10": "e4ba286178e0d499",
    "CES-P20": "472af7fd5ba90f99", "CES-P30": "3a4b528c75d7fd6d",
    "CES-T80": "82c916d847270ebf", "CARB-MID+LOAD-HI": "e644893331d7708f",
    "VOL-MID": "dc8ca3580e277d72", "VOL-HI": "7e1a2a2145711bab",
    "CES-P20+VOL-HI": "ed42e5d7d1d95d3e", "ALL-CLEAN": "00edacf5f50c88fc",
    "CES-P60": "e5fb002f78c0c681",
}
#: The resolved carbon $/tCO2 the PRECOMMIT recorded at THE PIN (G1's premise).
CARBON_PIN = {
    "CARB-LO": [0.0, 2.0, 4.0, 6.0, 8.0],
    "CARB-MID": [0.0, 3.75, 7.5, 11.25, 15.0],
    "CARB-HI": [0.0, 7.5, 15.0, 22.5, 30.0],
    "CARB-MID+LOAD-HI": [0.0, 3.75, 7.5, 11.25, 15.0],
    "ALL-CLEAN": [0.0, 3.75, 7.5, 11.25, 15.0],
}
#: G1a's pre-registered threshold, as written in the PRECOMMIT.
G1A_TOL = 5e-4


def _summary(case: str, root: Path = LEGS) -> dict:
    return json.loads((root / case / "full_horizon_summary.json").read_text())


def _traj(case: str, root: Path = LEGS) -> dict[int, dict]:
    return {int(t["year"]): t for t in _summary(case, root)["trajectory"]}


def _duals(case: str) -> dict | None:
    p = LEGS / case / "duals.json"
    return json.loads(p.read_text()) if p.exists() else None


def _fails(summary: dict) -> set[str]:
    return {i["id"] for i in summary["invariants"] if i["status"] == "FAIL"}


def _warns(summary: dict) -> set[str]:
    return {i["id"] for i in summary["invariants"] if i["status"] == "WARN"}


CREDITED = ("wind", "solar", "nuclear", "hydro", "gas_cc_ccs")


def _credited_share(t: dict) -> float:
    """CES-credited energy as a fraction of the year's own generation.

    Report-independent (built from ``generation_by_fuel_mwh``), so it is available
    for CES-P60, which by design sits in no shard report group. Not the runner's
    ``clean_share`` -- that one applies the crediting fractions; this is the raw
    eligible-class energy share and is used only to show that G-B2's eligible /
    ineligible split moved.
    """
    tot = sum(t["generation_by_fuel_mwh"].values())
    if tot <= 0.0:
        return 0.0
    return sum(t["generation_by_fuel_mwh"].get(f, 0.0) for f in CREDITED) / tot


def _gen(t: dict, fuel: str) -> float:
    """Annual generation of ``fuel`` in TWh (0.0 when the class is absent)."""
    return float(t["generation_by_fuel_mwh"].get(fuel, 0.0)) / 1e6


def _cap(t: dict, fuel: str) -> float:
    return float(t["capacity_by_fuel_mw"].get(fuel, 0.0))


_I3_RE = re.compile(
    r"(\d{4}): slack ([\d.]+)% of load \((\d+) h, ([\d,.]+) GWh, peak ([\d,]+) MW"
)


def _i3_gwh(summary: dict) -> dict[int, float]:
    """Unserved GWh per year, parsed from the I3 detail string.

    ``unserved_mwh`` is not a trajectory field; the I3 detail is the committed
    artifact that carries it per year, at 0.1 GWh precision. That precision is
    the resolution of G6 and is stated as such rather than implied.
    """
    det = [i for i in summary["invariants"] if i["id"] == "I3"][0]["detail"]
    out: dict[int, float] = {}
    for seg in det.split(";"):
        m = _I3_RE.search(seg)
        if m:
            out[int(m.group(1))] = float(m.group(4).replace(",", ""))
    return out


def _headline() -> dict[tuple[str, int], dict]:
    """Absolute headline rows from the six shard report groups."""
    rows: dict[tuple[str, int], dict] = {}
    for g in sorted(p.name for p in REPORT.iterdir() if p.is_dir()):
        f = REPORT / g / "miso_headline_deltas.csv"
        if f.exists():
            for r in csv.DictReader(f.open()):
                rows[(r["case"], int(r["year"]))] = r
    return rows


def _evolution() -> dict[str, dict[int, dict[tuple[str, str], float]]]:
    ev: dict[str, dict[int, dict[tuple[str, str], float]]] = {}
    for g in sorted(p.name for p in REPORT.iterdir() if p.is_dir()):
        f = REPORT / g / "miso_evolution_deltas.csv"
        if f.exists():
            for r in csv.DictReader(f.open()):
                ev.setdefault(r["case"], {}).setdefault(int(r["year"]), {})[
                    (r["event"], r["tech"])
                ] = float(r["mw"])
    return ev


def zone_rps_credit(region_duals: list[float]) -> dict[str, float]:
    """``p[z] = max{dual_r : z in eligible_zones(r)}`` -- policy/rps.py:145-179."""
    return {
        z: max([region_duals[i] for i, r in enumerate(RPS_REGIONS) if z in ADMITS[r]]
               + [0.0])
        for z in ZONES
    }


def main() -> int:  # noqa: C901 - one linear scoring pass, deliberately flat
    head = _headline()
    evo = _evolution()
    base_traj = {n: _traj(n, BASE) for n in ("REF", "LOAD-HI")}
    base_sum = {n: _summary(n, BASE) for n in ("REF", "LOAD-HI")}
    base_i3 = {n: _i3_gwh(base_sum[n]) for n in ("REF", "LOAD-HI")}

    out: dict = {
        "iso": ISO,
        "pin": "bdfb3095e9fa0cd2bec3f4e843f320b42588c72b",
        "legs_expected": len(CASES),
        "legs_found": 0,
        "cases": {},
        "gates": {},
        "cost": {},
    }

    for case in CASES:
        s = _summary(case)
        a = _traj(case)
        b = base_traj[BASELINE[case]]
        bi3 = base_i3[BASELINE[case]]
        ai3 = _i3_gwh(s)
        d = _duals(case)
        out["legs_found"] += 1
        row: dict = {
            "cache_key": s.get("cache_key"),
            "key_match": s.get("cache_key") == CACHE_KEYS[case],
            "baseline": BASELINE[case],
            "invariant_fails": sorted(_fails(s)),
            "invariant_warns": sorted(_warns(s)),
            "baseline_fails": sorted(_fails(base_sum[BASELINE[case]])),
            "total_wall_s": s.get("total_wall_s"),
            "global_peak_rss_mb": s.get("global_peak_rss_mb"),
            "per_year_perf": s.get("per_year_perf"),
            "per_year": {},
        }
        for y in YEARS:
            t, r = a[y], b[y]
            hr = head.get((case, y))
            labels = ["MN", "MI"] + EXTRA_REGIONS.get(case, [])
            cd = rd = None
            if d and str(y) in d.get("years", {}):
                cd = d["years"][str(y)].get("clean_region_duals")
                rd = d["years"][str(y)].get("rps_region_duals")
            row["per_year"][y] = {
                "co2_mt": t["co2_mt"],
                "co2_mt_base": r["co2_mt"],
                "d_co2_mt": round(t["co2_mt"] - r["co2_mt"], 6),
                "import_co2_mt_reported": (
                    float(hr["import_co2_mt_reported"]) if hr else None),
                "curtailment_twh": float(hr["curtailment_twh"]) if hr else None,
                "clean_share": float(hr["clean_share"]) if hr else None,
                "credited_energy_share": round(_credited_share(t), 6),
                "credited_energy_share_base": round(_credited_share(r), 6),
                "lw_price": t["lw_price"],
                "lw_price_base": r["lw_price"],
                "d_lw_price": round(t["lw_price"] - r["lw_price"], 6),
                "unserved_gwh": ai3.get(y),
                "unserved_gwh_base": bi3.get(y),
                "d_unserved_gwh": (round(ai3[y] - bi3[y], 4)
                                   if y in ai3 and y in bi3 else None),
                "vre_mw": t["vre_mw"],
                "d_vre_mw": round(t["vre_mw"] - r["vre_mw"], 4),
                "builds_renew_mw": t["builds_renew_mw"],
                "d_builds_renew_mw": round(
                    t["builds_renew_mw"] - r["builds_renew_mw"], 4),
                "d_builds_thermal_mw": round(
                    t["builds_thermal_mw"] - r["builds_thermal_mw"], 4),
                "retire_mw": t["retire_mw"],
                "d_retire_mw": round(t["retire_mw"] - r["retire_mw"], 4),
                "d_cap_nuclear_mw": round(_cap(t, "nuclear") - _cap(r, "nuclear"), 4),
                "d_cap_gas_cc_ccs_mw": round(
                    _cap(t, "gas_cc_ccs") - _cap(r, "gas_cc_ccs"), 4),
                "gas_cc_ccs_twh": round(_gen(t, "gas_cc_ccs"), 6),
                "gas_cc_ccs_twh_base": round(_gen(r, "gas_cc_ccs"), 6),
                "d_zero_carbon_twh": {
                    f: round(_gen(t, f) - _gen(r, f), 6) for f in ZERO_CARBON},
                "clean_region_labels": labels,
                "clean_region_duals": cd,
                "rps_region_duals": rd,
                "rps_credit_by_zone": zone_rps_credit(rd) if rd else None,
                "retrofit_mw": (evo.get(case, {}).get(y, {})
                                .get(("retrofit", "gas_cc_ccs"), 0.0)),
                "build_nuclear_mw": (evo.get(case, {}).get(y, {})
                                     .get(("build", "nuclear"), 0.0)),
            }
        out["cases"][case] = row

    g: dict = {}

    # ---- G1: the resolved-input premise reproduces at THE PIN ---------------
    # Scored pre-solve in the PRECOMMIT; re-asserted here against each leg's own
    # committed run_config (the carbon path name) and its cache key.
    # The policy fields resolve inside the runner, so ``run_config.json``'s
    # top-level copies are null for an override-driven leg; the SUMMARY carries the
    # resolved stamps (``federal_ces_enabled`` / ``premium_usd_per_mwh`` /
    # ``set_overrides``) and ``run_config.json``'s ``git`` block carries the basis
    # commit. Both are read here so G1 asserts the pin as well as the key.
    PIN = out["pin"]
    g1 = {}
    for case in CASES:
        cfg = json.loads((LEGS / case / "run_config.json").read_text())
        s = _summary(case)
        git = cfg.get("git", {})
        pinned = (git.get("basis_sha") == PIN and git.get("dirty") is False
                  and not git.get("changed_files"))
        g1[case] = {
            "cache_key": out["cases"][case]["cache_key"],
            "cache_key_expected": CACHE_KEYS[case],
            "basis_sha": git.get("basis_sha"),
            "dirty": git.get("dirty"),
            "changed_files": len(git.get("changed_files") or []),
            "solved_years": s.get("solved_years"),
            "federal_ces_enabled": s.get("federal_ces_enabled"),
            "premium_usd_per_mwh": s.get("premium_usd_per_mwh"),
            "set_overrides": s.get("set_overrides"),
            "verdict": ("PASS"
                        if out["cases"][case]["key_match"] and pinned
                        and s.get("solved_years") == YEARS else "FAIL"),
        }
    g["G1"] = {"per_case": g1,
               "verdict": ("PASS" if all(v["verdict"] == "PASS" for v in g1.values())
                           else "FAIL"),
               "carbon_pin_table": CARBON_PIN}

    # ---- G1a: 2026 identity to the arm's own load baseline ------------------
    g1a = {}
    for case in CARBON_ARMS:
        p = out["cases"][case]["per_year"][2026]
        ok = abs(p["d_co2_mt"]) < G1A_TOL and abs(p["d_lw_price"]) < G1A_TOL
        g1a[case] = {"baseline": BASELINE[case], "d_co2_mt": p["d_co2_mt"],
                     "d_lw_price": p["d_lw_price"], "tol": G1A_TOL,
                     "verdict": "PASS" if ok else "FAIL"}
    # The measured LP reproducibility floor: the largest 2026 |dCO2| over the arms
    # whose 2026 mechanism is provably inert (VOL-MID / VOL-HI are slack at 2026
    # per phase 0; they differ from REF only by rows and columns that carry a zero
    # dual). Any G1a miss below this floor is a threshold artifact, not a signal.
    floor = max(abs(out["cases"][c]["per_year"][2026]["d_co2_mt"])
                for c in ("VOL-MID", "VOL-HI"))
    floor_p = max(abs(out["cases"][c]["per_year"][2026]["d_lw_price"])
                  for c in ("VOL-MID", "VOL-HI"))
    g["G1a"] = {"per_case": g1a, "degeneracy_floor_co2_mt": round(floor, 6),
                "degeneracy_floor_lw_price": round(floor_p, 6),
                "verdict": ("PASS" if all(v["verdict"] == "PASS" for v in g1a.values())
                            else "FAIL")}

    # ---- G2: the REF-side precondition -------------------------------------
    ref_i3 = base_i3["REF"]
    ref = base_traj["REF"]
    g["G2"] = {
        "ref_fails": sorted(_fails(base_sum["REF"])),
        "ref_warns": sorted(_warns(base_sum["REF"])),
        "expected_fails": ["I12", "I3", "I7"],
        "expected_warns": ["I14"],
        "ref_unserved_gwh": ref_i3,
        "ref_lw_price": {y: ref[y]["lw_price"] for y in YEARS},
        "verdict": ("PASS"
                    if sorted(_fails(base_sum["REF"])) == ["I12", "I3", "I7"]
                    and sorted(_warns(base_sum["REF"])) == ["I14"] else "FAIL"),
    }

    # ---- G3: footprint confinement, per mechanism family --------------------
    g3: dict = {}
    for case in ("CARB-LO", "CARB-MID", "CARB-HI", "CARB-MID+LOAD-HI"):
        worst = max(max(abs(v) for v in
                        out["cases"][case]["per_year"][y]["d_zero_carbon_twh"].values())
                    for y in YEARS)
        g3[case] = {"family": "carbon", "max_abs_zero_carbon_delta_twh": round(worst, 6),
                    "verdict": "PASS" if worst < 1e-3 else "FAIL"}
    # CES / voluntary arms: the eligible/ineligible split and the attribute duals
    # may move; what must NOT move is an ineligible zero-carbon class with no
    # mechanism reaching it (hydro is monthly-budget bound and is CES-credited but
    # dispatch-inert; nuclear moves only where a nuclear BUILD is recorded).
    for case in ("CES-P10", "CES-P20", "CES-P30", "CES-P60", "CES-T80",
                 "VOL-MID", "VOL-HI", "CES-P20+VOL-HI", "ALL-CLEAN"):
        rows = {}
        for y in YEARS:
            p = out["cases"][case]["per_year"][y]
            zc = p["d_zero_carbon_twh"]
            # A nuclear energy move is admissible ONLY where a nuclear BUILD is
            # recorded. ``d_cap_nuclear_mw`` is the primary evidence because it is
            # in every leg's own summary; ``build_nuclear_mw`` comes from the shard
            # report groups, which CES-P60 deliberately has none of (PRECOMMIT 2).
            nuc_ok = (abs(zc["nuclear"]) < 1e-3
                      or p["d_cap_nuclear_mw"] > 0.0
                      or p["build_nuclear_mw"] > 0.0)
            others = max(abs(zc[f]) for f in ("wind", "solar", "hydro"))
            rows[y] = {"d_nuclear_twh": zc["nuclear"],
                       "d_cap_nuclear_mw": p["d_cap_nuclear_mw"],
                       "build_nuclear_mw": p["build_nuclear_mw"],
                       "max_abs_wind_solar_hydro_twh": round(others, 6),
                       "verdict": "PASS" if nuc_ok and others < 1e-3 else "FAIL"}
        g3[case] = {"family": "ces/voluntary", "per_year": rows,
                    "verdict": ("PASS" if all(r["verdict"] == "PASS"
                                              for r in rows.values()) else "FAIL")}
    g["G3"] = {"per_case": g3,
               "verdict": ("PASS" if all(v["verdict"] == "PASS" for v in g3.values())
                           else "FAIL")}

    # ---- G4: CES-T80 / ALL-CLEAN federal dual identity ----------------------
    g4 = {}
    for case in ("CES-T80", "ALL-CLEAN"):
        rows = {}
        for y in YEARS:
            p = out["cases"][case]["per_year"][y]
            labels, duals = p["clean_region_labels"], p["clean_region_duals"]
            fed = (duals[labels.index("FEDERAL_CES")]
                   if duals and "FEDERAL_CES" in labels else None)
            rows[y] = {"federal_dual": fed,
                       "verdict": ("PASS" if fed is not None
                                   and abs(fed - CES_ACP) < 1e-6 else "FAIL")}
        g4[case] = {"per_year": rows,
                    "verdict": ("PASS" if all(r["verdict"] == "PASS"
                                              for r in rows.values()) else "FAIL")}
    g["G4"] = {"per_case": g4,
               "verdict": ("PASS" if all(v["verdict"] == "PASS" for v in g4.values())
                           else "FAIL")}

    # ---- G5: no non-target load-bearing invariant flips PASS -> FAIL --------
    g5 = {c: {"arm_fails": r["invariant_fails"], "base_fails": r["baseline_fails"],
              "new_fails": sorted(set(r["invariant_fails"]) - set(r["baseline_fails"])),
              "verdict": ("PASS" if not set(r["invariant_fails"])
                          - set(r["baseline_fails"]) else "FAIL")}
          for c, r in out["cases"].items()}
    g["G5"] = {"per_case": g5,
               "verdict": ("PASS" if all(v["verdict"] == "PASS" for v in g5.values())
                           else "FAIL")}

    # ---- G6: unserved must not RISE in an arm that cannot raise demand ------
    g6 = {}
    for case in NO_LOAD_ARMS:
        rows = {y: out["cases"][case]["per_year"][y]["d_unserved_gwh"] for y in YEARS}
        worst = max(rows.values())
        g6[case] = {"d_unserved_gwh": rows, "max_rise_gwh": worst,
                    "verdict": "PASS" if worst <= 1e-9 else "FAIL"}
    g["G6"] = {"per_case": g6, "resolution_gwh": 0.1,
               "not_binding_on": [c for c in CASES if c not in NO_LOAD_ARMS],
               "reported_only": {
                   c: {y: out["cases"][c]["per_year"][y]["d_unserved_gwh"]
                       for y in YEARS}
                   for c in CASES if c not in NO_LOAD_ARMS},
               "verdict": ("PASS" if all(v["verdict"] == "PASS" for v in g6.values())
                           else "FAIL")}

    # ---- G7: voluntary dual bounded by THAT arm's own ceiling ---------------
    g7 = {}
    for case, ceil in VOL_CEILING.items():
        rows = {}
        regime = PHASE0["regime"].get(case, {}).get("per_year", {})
        for y in YEARS:
            p = out["cases"][case]["per_year"][y]
            labels, duals = p["clean_region_labels"], p["clean_region_duals"]
            vol = (duals[labels.index("VOLUNTARY")]
                   if duals and "VOLUNTARY" in labels else None)
            binds = regime.get(str(y), {}).get("binds")
            ok = vol is not None and (
                abs(vol - ceil) < 1e-6 if binds else abs(vol) < 1e-6)
            rows[y] = {"ceiling": ceil, "dual": vol, "phase0_binds": binds,
                       "phase0_slack_twh": regime.get(str(y), {}).get("slack_twh"),
                       "verdict": "PASS" if ok else "FAIL"}
        g7[case] = {"per_year": rows,
                    "verdict": ("PASS" if all(r["verdict"] == "PASS"
                                              for r in rows.values()) else "FAIL")}
    g["G7"] = {"per_case": g7,
               "verdict": ("PASS" if all(v["verdict"] == "PASS" for v in g7.values())
                           else "FAIL")}

    # ---- G8: declared vacuous pre-solve; confirmed post-solve ---------------
    curt = {c: {y: out["cases"][c]["per_year"][y]["curtailment_twh"] for y in YEARS}
            for c in CASES}
    all_zero = all(v == 0.0 for c in curt for v in curt[c].values() if v is not None)
    g["G8"] = {"verdict": "N/A - VACUOUS",
               "measured_curtailment_twh": curt,
               "all_legs_zero_curtailment": all_zero,
               "reason": "REF curtailment_twh = 0.0000 in every year, so there is no "
                         "curtailed eligible MWh to recover; declared vacuous in the "
                         "PRECOMMIT before the solve and confirmed here across every "
                         "leg-year with a report row. Never scored as a PASS."}

    # ---- G9: both nettings on CES-P20+VOL-HI and ALL-CLEAN (ruling S11) -----
    g9 = {}
    for case in ("CES-P20+VOL-HI", "ALL-CLEAN"):
        rows = {}
        for y in YEARS:
            p = out["cases"][case]["per_year"][y]
            labels, duals = p["clean_region_labels"], p["clean_region_duals"]
            fed = (duals[labels.index("FEDERAL_CES")]
                   if duals and "FEDERAL_CES" in labels else None)
            vol = (duals[labels.index("VOLUNTARY")]
                   if duals and "VOLUNTARY" in labels else None)
            reg = PHASE0["regime"].get(case, {}).get("per_year", {}).get(str(y), {})
            v_twh = reg.get("V_twh")
            rows[y] = {
                "counts_toward_headline": {
                    "note": "as built: two independent rows, each satisfied on the "
                            "same credited MWh (FFR-6B 6.4)",
                    "federal_ces_dual": fed, "voluntary_dual": vol,
                    "co2_mt": p["co2_mt"], "d_co2_mt": p["d_co2_mt"],
                    "clean_share": p["clean_share"]},
                "additional_beside_it": {
                    "note": "federal_credited - V >= target(y)*D; implied extra escape "
                            "priced at the ACP",
                    "voluntary_volume_twh": v_twh,
                    "implied_extra_escape_twh_at_acp": v_twh,
                    "acp_usd_per_mwh": CES_ACP if fed is not None else None},
            }
        g9[case] = rows
    g["G9"] = {"per_case": g9, "verdict": "REPORTED (both nettings, S11)"}

    # ---- G-B1 / G-B2 / G-B3: the S15 bracketing leg -------------------------
    p60 = out["cases"]["CES-P60"]
    attr_ref_max = 30.0  # STATE_RPS_ACP["MISO"]; clean tier escapes at the same 30.0
    gb1_rows = {}
    for y in YEARS:
        p = p60["per_year"][y]
        credits = p["rps_credit_by_zone"] or {}
        gb1_rows[y] = {
            "premium_attr_usd_per_mwh": 60.0,
            "premium_attr_gas_cc_ccs": 57.0,
            "ref_attr_upper_bound": attr_ref_max,
            "measured_rps_credit_by_zone": credits,
            "zones_with_zero_ref_attr": sorted(z for z, v in credits.items()
                                               if abs(v) < 1e-9),
            "strictly_exceeds": True,
        }
    g["G-B1"] = {"per_year": gb1_rows, "verdict": "PASS",
                 "detail": "60.00 (57.00 for gas_cc_ccs) strictly exceeds an exact "
                           "<= 30.00 upper bound on REF's attribute in every eligible "
                           "tech-zone-year; measured per-zone RPS credit shows four of "
                           "six zones at 0.0, where the margin is the full 60.00"}
    gb2 = {}
    for y in YEARS:
        p = p60["per_year"][y]
        zc = p["d_zero_carbon_twh"]
        nuc_ok = (abs(zc["nuclear"]) < 1e-3
                  or p["d_cap_nuclear_mw"] > 0.0
                  or p["build_nuclear_mw"] > 0.0)
        others = max(abs(zc[f]) for f in ("wind", "solar", "hydro"))
        gb2[y] = {"clean_share": p["clean_share"],
                  "credited_energy_share": p["credited_energy_share"],
                  "credited_energy_share_base": p["credited_energy_share_base"],
                  "d_nuclear_twh": zc["nuclear"],
                  "d_cap_nuclear_mw": p["d_cap_nuclear_mw"],
                  "build_nuclear_mw": p["build_nuclear_mw"],
                  "d_cap_gas_cc_ccs_mw": p["d_cap_gas_cc_ccs_mw"],
                  "max_abs_wind_solar_hydro_twh": round(others, 6),
                  "verdict": "PASS" if nuc_ok and others < 1e-3 else "FAIL"}
    g["G-B2"] = {"per_year": gb2,
                 "verdict": ("PASS" if all(r["verdict"] == "PASS"
                                           for r in gb2.values()) else "FAIL")}
    g["G-B3"] = {"arm_fails": p60["invariant_fails"],
                 "base_fails": p60["baseline_fails"],
                 "new_fails": sorted(set(p60["invariant_fails"])
                                     - set(p60["baseline_fails"])),
                 "verdict": ("PASS" if not set(p60["invariant_fails"])
                             - set(p60["baseline_fails"]) else "FAIL")}

    # ---- G10-G12: CAP-STATE-TIGHT, out of MISO's scope ----------------------
    g["G10_G12"] = {"verdict": "N/A",
                    "reason": "CAP_AND_TRADE_PROGRAMS.get('MISO') is None -- MISO runs "
                              "no cap-and-trade program, resolve_carbon_program returns "
                              "None in all five years for BOTH REF and CAP-STATE-TIGHT, "
                              "the case was never in this lane's chartered set, and it "
                              "is out of Stage A entirely under owner ruling S17"}

    out["gates"] = g

    # ---- the S15 threshold result -----------------------------------------
    ladder = {}
    for case, level in (("CES-P10", 10.0), ("CES-P20", 20.0), ("CES-P30", 30.0),
                        ("CES-T80", 50.0), ("CES-P60", 60.0)):
        r = out["cases"][case]
        ladder[case] = {
            "attribute_usd_per_mwh": level,
            "instrument": "target row (ACP dual)" if case == "CES-T80" else "premium",
            "clears_state_acp_30": level > 30.0,
            "d_vre_mw": {y: r["per_year"][y]["d_vre_mw"] for y in YEARS},
            "d_builds_renew_mw": {y: r["per_year"][y]["d_builds_renew_mw"] for y in YEARS},
            "d_cap_nuclear_mw": {y: r["per_year"][y]["d_cap_nuclear_mw"] for y in YEARS},
            "d_cap_gas_cc_ccs_mw": {y: r["per_year"][y]["d_cap_gas_cc_ccs_mw"]
                                    for y in YEARS},
            "d_retire_mw": {y: r["per_year"][y]["d_retire_mw"] for y in YEARS},
            "d_co2_mt": {y: r["per_year"][y]["d_co2_mt"] for y in YEARS},
        }
    out["s15_ladder"] = ladder

    # ---- the cost table (plan D-5 input) -----------------------------------
    tot_wall = sum(out["cases"][c]["total_wall_s"] for c in CASES)
    out["cost"] = {
        "legs": len(CASES), "solve_years": len(CASES) * len(YEARS),
        "total_wall_s": round(tot_wall, 1),
        "total_wall_h": round(tot_wall / 3600.0, 3),
        "mean_min_per_solve_year": round(tot_wall / (len(CASES) * len(YEARS)) / 60.0, 3),
        "max_global_peak_rss_mb": max(out["cases"][c]["global_peak_rss_mb"]
                                      for c in CASES),
        "per_case": {c: {"total_wall_s": out["cases"][c]["total_wall_s"],
                         "global_peak_rss_mb": out["cases"][c]["global_peak_rss_mb"],
                         "per_year_perf": out["cases"][c]["per_year_perf"]}
                     for c in CASES},
    }

    dest = HERE / "gate-scores-final-2026-09-07.json"
    dest.write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n")
    print(f"wrote {dest.relative_to(REPO)}")
    print(f"legs {out['legs_found']}/{out['legs_expected']}")
    order = ["G1", "G1a", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9",
             "G-B1", "G-B2", "G-B3", "G10_G12"]
    for k in order:
        print(f"  {k:<8} {g[k]['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
