"""nyiso-200 PHASE 0 (ZERO LP) — the bridge's P0-pattern dependence, measured
before any solve, and the nyiso-199 §8.3 STOP re-attributed on the scorer's
own rules.

Three records, none of which reads a residual:

1. **The scorer artifact.** nyiso-199's 2025 screen stopped on two NEW D-4
   unit-conduct rows (7314, 50978). Both plants carry the benchmark's
   ``ct_only`` flag (EIA-923 net > 1.1x CAMPD gross => hourly CAMPD series
   incomplete, the rider must not convict on it) in the complete 2023 / 2024
   vintages and lose it only in the preliminary 2025 vintage — the nyiso-145
   §3 artifact. The span keeper's scorer restores the flag by union over its
   three scored years; a ONE-YEAR screen bundle had a one-year union, so the
   rider convicted exactly the plants the span scorer skips. This record
   reproduces both unions from the committed benches and names which of the
   nyiso-199 2025 failures the span guard would have skipped.

2. **The keeper's own committed bridge footprint** (D-2 / D-4 rows of
   ``legitimacy_diagnostics.json``): the bridge floor volume per year and per
   plant. The commitment-real run screen can only REMOVE floor, so this is
   the repair's pre-solve reachability bound per year — the rule-29 footprint
   measure, meter-free and residual-free. It also records the production C8
   posture: ``CC_REGULAR`` forced share against the 30 % cap, i.e. whether
   ``calibration_verdict._d4_provenance`` would ever have been consulted.

3. **The eligible population and the screen's bar**, from an on-recipe
   ``run_year(fleet_only=True)`` rebuild: every row the detector admits
   (``_ra_bridge_unit_params``: gas_cc / gas_st, non-cogen, base tranche with
   a startup cost), net of the keeper's two armed membership exclusions, with
   the per-MW startup cost that IS the screen's bar — the same published
   NREL/CAMPD-bin value the economic bridge already prices, so the repair
   selects no number (rule 21 [R-DOF]).

Writes ``results/calibration/_nyiso200_bridge_phase0.json``.

Usage::

    python scripts/probes/nyiso200_bridge_phase0.py [--no-rebuild]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    sys.path.insert(0, str(p))

import legitimacy_diagnostics as ld  # noqa: E402
from scripts.lib.bundle_fleet import (  # noqa: E402
    bundle_gas_price,
    clear_fleet_caches,
    ensure_probe_path,
    full_run_year_kwargs,
)

KEEPER_ID = "2026-09-06-nyiso-196-extract-basis"
BUNDLE = ROOT / "results/calibration/nyiso196_extract_basis"
NYISO199_2025 = ROOT / "results/calibration/_nyiso199_screen_gates_2025.json"
OUT = ROOT / "results/calibration/_nyiso200_bridge_phase0.json"
MECH = "nyiso_gas_commitment_bridge"
CONVICTED = ("7314", "50978")
YEARS = (2023, 2024, 2025)


def _r(x, n=4):
    return round(float(x), n)


def scorer_artifact() -> dict:
    per_year = {}
    for y in YEARS:
        pv = ld.bench_plant_view(ld.load_bench(ROOT, "NYISO", y))
        per_year[str(y)] = {
            pid: {
                "ct_only": bool(pv[pid]["ct_only"]),
                "npl_mw": _r(pv[pid]["npl"], 1),
                "measured_cf": _r(pv[pid]["mw"].sum() / (pv[pid]["npl"] * 8760.0)),
                "measured_zero_share": _r((pv[pid]["mw"] <= 0).mean()),
            }
            for pid in CONVICTED
            if pid in pv
        }
    one_year = sorted(ld._ct_only_union_over(ROOT, "NYISO", [2025]))
    span = sorted(ld._ct_only_union_over(ROOT, "NYISO", list(YEARS)))
    g = json.loads(NYISO199_2025.read_text())
    screen_fail = g["gates"]["C8_D4"]["screen"]["D4_failures_this_year"]
    keeper_fail = g["gates"]["C8_D4"]["keeper"]["D4_failures_this_year"]

    def _plant(msg: str) -> str:
        return msg.split("plant ")[1].split(" ")[0] if "plant " in msg else ""

    skipped_by_span = [f for f in screen_fail if _plant(f) in set(span) - set(one_year)]
    survivors = [f for f in screen_fail if f not in skipped_by_span]
    return {
        "convicted_plants_by_year": per_year,
        "ct_only_union_2025_only": one_year,
        "ct_only_union_train_span": span,
        "restored_by_span_union": sorted(set(span) - set(one_year)),
        "nyiso199_2025_screen_D4_failures": screen_fail,
        "nyiso199_2025_keeper_D4_failures": keeper_fail,
        "screen_failures_the_span_guard_skips": skipped_by_span,
        "screen_failures_surviving_the_span_guard": survivors,
        "stop_would_have_fired_under_span_guard": len(survivors) > len(keeper_fail),
        "guard_years_after_nyiso200": ld.ct_only_guard_years(ROOT, "NYISO", [2025]),
        "note": (
            "the nyiso-199 §8.3 C8/D-4 STOP fired on rows the span scorer skips by "
            "construction (nyiso-150 union guard, nyiso-145 §3 artifact); the "
            "one-year screen bundle's union was {2025} alone. Scorer-only repair in "
            "legitimacy_diagnostics.ct_only_guard_years; keeper re-scores identically."
        ),
    }


def keeper_footprint() -> dict:
    legit = json.loads((BUNDLE / "legitimacy_diagnostics.json").read_text())
    d2 = legit["diagnostics"]["D2"]["rows"]
    d4 = legit["diagnostics"]["D4"]["rows"]
    out = {}
    for y in YEARS:
        forced = {
            r["class"]: {
                "forced_twh": r["forced_twh"],
                "class_total_twh": r["class_total_twh"],
                "share_of_class": r["share_of_class"],
            }
            for r in d2
            if int(r["year"]) == y and r["mechanism"] == MECH
        }
        plants = [
            {
                "class": r["floor"].split("× ")[-1],
                "plant": r["plant"],
                "floored_twh": r["floored_twh"],
                "binding_hours": r["binding_hours"],
                "measured_median_mw": r["measured_median_mw"],
                "measured_zero_share": r["measured_zero_share"],
                "verdict": r["verdict"],
            }
            for r in d4
            if int(r["year"]) == y
            and r["check"] == "unit-conduct"
            and MECH in r["floor"]
        ]
        bound = sum(v["forced_twh"] for v in forced.values())
        out[str(y)] = {
            "bridge_forced_twh_by_class": forced,
            "repair_reachability_bound_twh": _r(bound),
            "cc_regular_forced_share_vs_cap": {
                "share": forced.get("CC_REGULAR", {}).get("share_of_class"),
                "cap": 0.30,
                "d4_consulted_by_calibration_verdict": bool(
                    (forced.get("CC_REGULAR", {}).get("share_of_class") or 0.0) > 0.30
                ),
            },
            "unit_conduct_rows": plants,
        }
    return out


def population_census(rebuild: bool) -> dict:
    if not rebuild:
        return {"skipped": True}
    ensure_probe_path()
    from market_sim.data.bridge_layup_exclusions import load_layup_exclusions
    from market_sim.data.reserve_duty import load_reserve_duty_cc
    from market_sim.model.commitment import _ra_bridge_unit_params
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = full_run_year_kwargs(meta)
    excluded = set(load_layup_exclusions("NYISO")) | set(load_reserve_duty_cc("NYISO"))
    out = {"excluded_membership_plant_codes": sorted(int(c) for c in excluded)}
    for y in YEARS:
        clear_fleet_caches()
        st = run_year(
            y, meta["iso"], int(meta["hours"]), bundle_gas_price(meta, y), **kwargs
        )
        fleet, fa = st["fleet"], st["fleet_arrays"]
        rows = []
        for g, gen in enumerate(fleet):
            if gen.plant_group.endswith("_CHP") or gen.fuel_type not in (
                "gas_cc",
                "gas_st",
            ):
                continue
            res = _ra_bridge_unit_params(gen, float(fa.heat_rate[g]))
            if res is None:
                continue
            min_down, startup = res
            rows.append(
                {
                    "plant_code": int(getattr(gen, "plant_code", 0) or 0),
                    "fuel": gen.fuel_type,
                    "group": gen.plant_group,
                    "pmax_mw": _r(fa.pmax[g], 2),
                    "min_down_h": min_down,
                    "startup_per_mw": startup,
                    "in_population": int(getattr(gen, "plant_code", 0) or 0)
                    not in excluded,
                }
            )
        by_fuel = defaultdict(lambda: {"rows": 0, "mw": 0.0, "startup_values": set()})
        for r in rows:
            if not r["in_population"]:
                continue
            b = by_fuel[r["fuel"]]
            b["rows"] += 1
            b["mw"] += r["pmax_mw"]
            b["startup_values"].add(r["startup_per_mw"])
        out[str(y)] = {
            "eligible_rows_total": len(rows),
            "in_population": {
                f: {
                    "rows": v["rows"],
                    "mw": _r(v["mw"], 1),
                    "startup_per_mw_values": sorted(v["startup_values"]),
                }
                for f, v in by_fuel.items()
            },
            "rows": rows,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-rebuild", action="store_true")
    a = ap.parse_args()
    res = {
        "session": "nyiso-200",
        "keeper": KEEPER_ID,
        "scorer_artifact": scorer_artifact(),
        "keeper_bridge_footprint": keeper_footprint(),
        "population_census": population_census(rebuild=not a.no_rebuild),
    }
    OUT.write_text(json.dumps(res, indent=2))
    sa = res["scorer_artifact"]
    print(
        f"wrote {OUT}\n  span union restores {sa['restored_by_span_union']}\n"
        f"  nyiso-199 2025 failures skipped by span guard: {len(sa['screen_failures_the_span_guard_skips'])}"
        f" of {len(sa['nyiso199_2025_screen_D4_failures'])}; STOP under span guard: "
        f"{sa['stop_would_have_fired_under_span_guard']}"
    )
    for y, v in res["keeper_bridge_footprint"].items():
        print(
            f"  {y}: bridge forced {v['bridge_forced_twh_by_class']} bound {v['repair_reachability_bound_twh']} TWh"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
