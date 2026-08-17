"""neiso-99 — re-verify the NEISO ``frontier`` and ``complete`` declarations on the NEW keeper.

Read-only, committed-artifact-only. **No LP is constructed and no year is
solved, scored or registered.** The neiso-98 probe applied to the neiso-99
keeper: neiso-98's verification is NOT carried forward, because the keeper has
changed and the change is not a no-op — it moves the scored basis off the
archived P2 pass and repairs a measured availability input.

It **imports neiso-98's helpers verbatim** rather than restating them, so the
tail definition stays pinned to ``render_calibration_html._tail_hours`` (max
across zones, NaN → −inf) and the two sessions' numbers are one measurement.

The two load-bearing legs, both re-derived from the NEW keeper's own bytes:

  1. **C3c model tail** — hours whose MAX zonal LMP exceeds the NEISO
     $300/MWh threshold, per year and per PERSISTED pass, cross-checked
     against the registered payload's ``ordc.hoursGt200.model``. The new
     keeper persists ``["P1"]`` alone, so "on every persisted pass" now means
     the production basis — which is the point of the promotion, and the
     reason the declaration must be re-measured rather than assumed.
  2. **Reserve-family dormancy** — ``shortfall_mw`` and ``held_mw`` vs
     ``requirement_mw`` per family-hour, with each family's requirement checked
     against its PUBLISHED static value (``NEISO_RCPF_PRODUCTS``: 1,800 /
     1,200 / 600 MW) rather than read off the artifact.
     ``reserve_family_<year>.parquet`` is the ONLY artifact in which a
     locational reserve family's binding is observable (CLAUDE.md rule 15).

Rule 22 ``[R-HOLDOUT]``: only 2023-2025 artifacts are read.

Usage::

    uv run python scripts/probes/neiso99_declaration_recheck.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.probes.neiso98_declaration_recheck import (  # noqa: E402
    PUBLISHED_STATIC_MW,
    THRESHOLD,
    YEARS,
    payload_tail,
    price_extremes,
    reserve_rows,
    tail_hours,
)

KEEPER_ID = "2026-08-17-neiso-99-joint-p1"
KEEPER_BUNDLE = REPO / "results/calibration/neiso99_joint_B"
#: The superseded keeper, re-measured alongside so "no C3c evidence moved" is a
#: MEASUREMENT rather than a recollection.
PRIOR_ID = "2026-08-17-neiso-97-dstrepair"
PRIOR_BUNDLE = REPO / "results/calibration/neiso97_dstrepair_A"

OUT = REPO / "results/calibration/_neiso99_declaration_recheck.json"


def legs(bundle: Path, run_id: str) -> dict:
    """Re-derive both load-bearing declaration legs from one bundle's own bytes."""
    out: dict = {
        "run_id": run_id,
        "bundle": str(bundle.relative_to(REPO)),
        "c3c_tail": [],
        "price_extremes": [],
        "reserve_families": [],
    }
    for year in YEARS:
        sysy = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
        for pl in sorted(sysy["pass"].unique()):
            out["c3c_tail"].append(
                {
                    "year": year,
                    "pass": str(pl),
                    "model_hours_gt_threshold": tail_hours(sysy, str(pl), THRESHOLD),
                }
            )
            out["price_extremes"].append(
                {"year": year, "pass": str(pl), **price_extremes(sysy, str(pl))}
            )
        out["reserve_families"] += reserve_rows(bundle, year)
    out["payload_cross_check"] = payload_tail(run_id)
    return out


def verdict(block: dict) -> dict:
    """Compute (never assert) the declaration verdict for one bundle."""
    tails = {
        (r["year"], r["pass"]): r["model_hours_gt_threshold"] for r in block["c3c_tail"]
    }
    rf = block["reserve_families"]
    # The helper resolves each family's requirement against
    # model/reserves/spec.py::NEISO_RCPF_PRODUCTS, not against the artifact.
    req_ok = all(
        r["requirement_is_static"] and r["matches_published_static"] for r in rf
    )
    return {
        "c3c_model_tail_zero_all_years_every_persisted_pass": all(
            v == 0 for v in tails.values()
        ),
        "passes_covered": sorted({p for _, p in tails}),
        "tail_by_year_pass": {f"{y}:{p}": v for (y, p), v in sorted(tails.items())},
        "closest_approach_usd_mwh": max(r["max"] for r in block["price_extremes"]),
        "min_margin_to_threshold_usd_mwh": min(
            r["margin_to_threshold"] for r in block["price_extremes"]
        ),
        "annual_max_by_year_pass": {
            f"{r['year']}:{r['pass']}": r["max"] for r in block["price_extremes"]
        },
        "reserve_dormant_no_shortfall": all(r["shortfall_hours"] == 0 for r in rf),
        "reserve_dormant_held_ge_requirement": all(
            r["held_lt_requirement_hours"] == 0 for r in rf
        ),
        "reserve_requirements_equal_published_statics": req_ok,
        "reserve_dual_abs_max": max(r["dual_abs_max"] for r in rf),
        "reserve_family_hours_total": sum(r["family_hours"] for r in rf),
    }


def main() -> None:
    """Re-verify the declaration on the new keeper, with the prior as control."""
    result: dict = {
        "probe": "neiso99_declaration_recheck",
        "keeper": KEEPER_ID,
        "prior_keeper": PRIOR_ID,
        "threshold_usd_mwh": THRESHOLD,
        "published_static_mw": PUBLISHED_STATIC_MW,
        "years": list(YEARS),
        "solve_performed": False,
    }
    for tag, bundle, rid in (
        ("keeper", KEEPER_BUNDLE, KEEPER_ID),
        ("prior_keeper", PRIOR_BUNDLE, PRIOR_ID),
    ):
        block = legs(bundle, rid)
        block["verdict"] = verdict(block)
        result[tag + "_legs"] = block

    kv = result["keeper_legs"]["verdict"]
    pv = result["prior_keeper_legs"]["verdict"]
    result["declaration_holds"] = bool(
        kv["c3c_model_tail_zero_all_years_every_persisted_pass"]
        and kv["reserve_dormant_no_shortfall"]
        and kv["reserve_dormant_held_ge_requirement"]
        and kv["reserve_requirements_equal_published_statics"]
    )
    result["c3c_evidence_moved"] = bool(
        kv["tail_by_year_pass"] != {}
        and any(v != 0 for v in kv["tail_by_year_pass"].values())
    )

    print("=" * 74)
    print(f"neiso-99 declaration re-check — NEW keeper {KEEPER_ID}")
    print("=" * 74)
    for tag, v in (("NEW keeper", kv), (f"prior ({PRIOR_ID})", pv)):
        print(f"\n{tag}")
        print(f"  passes persisted            : {v['passes_covered']}")
        print(f"  C3c model tail (h > $300)   : {v['tail_by_year_pass']}")
        print(f"  annual max by year:pass     : {v['annual_max_by_year_pass']}")
        print(
            f"  closest approach            : ${v['closest_approach_usd_mwh']:.4f} "
            f"(short of $300 by ${v['min_margin_to_threshold_usd_mwh']:.4f})"
        )
        print(f"  reserve: no shortfall       : {v['reserve_dormant_no_shortfall']}")
        print(
            f"  reserve: held >= requirement: {v['reserve_dormant_held_ge_requirement']}"
        )
        print(
            f"  reserve: reqs == published  : {v['reserve_requirements_equal_published_statics']}"
        )
        print(f"  reserve |dual| max          : {v['reserve_dual_abs_max']:.3e}")
        print(f"  reserve family-hours        : {v['reserve_family_hours_total']}")
    print(
        f"\npayload ordc cross-check (new keeper): {result['keeper_legs']['payload_cross_check']}"
    )
    print(f"\nDECLARATION HOLDS ON THE NEW KEEPER: {result['declaration_holds']}")
    print(f"C3c evidence moved: {result['c3c_evidence_moved']}")

    OUT.write_text(json.dumps(result, indent=1, sort_keys=True, default=str))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
