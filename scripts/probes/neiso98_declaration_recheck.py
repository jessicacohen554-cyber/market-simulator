"""neiso-98 — re-verify the NEISO `frontier` and `complete` declarations on the NEW keeper.

Read-only, committed-artifact-only. **No LP is constructed and no year is solved,
scored or registered.** Every number below comes from files already in the repo:

  * the keeper bundle's own hourly sidecars
    (``results/calibration/neiso97_dstrepair_A/hourly/{system,reserve_family}_<year>.parquet``),
    and
  * the committed run payload (``frontend/data/backcast/runs/<id>.js``).

Why this probe exists even though neiso-97 already re-verified the declaration:
that promotion established the frontier basis **by bit-identity** to the
superseded ``2026-08-14-neiso-93-envelope`` sidecars. That is a sound transitive
argument, but the superseded bundle was PRUNED from the site at the same
promotion, so the chain now terminates in an artifact that is no longer in the
repo. This session re-establishes the declaration **directly on the current
keeper's own committed bytes**, closing the loop — the neiso-95 pattern applied
to the neiso-97 keeper.

  1. **C3c model tail** — hours whose MAX zonal LMP exceeds the NEISO $300/MWh
     threshold, per year and per pass. The definition is pinned to
     ``render_calibration_html._tail_hours`` (max across zones, NaN -> -inf) so
     the recomputation is comparable to the payload's ``ordc.hoursGt200.model``,
     which is cross-checked here.
  2. **Reserve-family binding** — ``shortfall_mw`` and ``held_mw`` vs
     ``requirement_mw`` per family-hour, and whether each family's requirement
     equals its PUBLISHED STATIC value (``NEISO_RCPF_PRODUCTS``: 1,800 / 1,200 /
     600 MW). ``reserve_family_<year>.parquet`` is the ONLY artifact in which a
     locational reserve family's binding is observable (CLAUDE.md rule 15):
     ``system``'s ``reserve_price`` is the cross-family SUM broadcast identically
     to every zone.

Rule 22 ``[R-HOLDOUT]``: only 2023-2025 artifacts are read. Nothing here touches
2019-2022 or H1-2026.

Usage::

    uv run python scripts/probes/neiso98_declaration_recheck.py
"""

from __future__ import annotations

import base64
import gzip
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER_ID = "2026-08-17-neiso-97-dstrepair"
KEEPER_BUNDLE = REPO / "results/calibration/neiso97_dstrepair_A"
YEARS = (2023, 2024, 2025)
THRESHOLD = 300.0  # NEISO C3c tail threshold, calibration_verdict.TAIL_THRESHOLD

# Published ISO-NE RCPF static requirements, model/reserves/spec.py
# NEISO_RCPF_PRODUCTS. The frontier note's "dormant at the published static
# requirements" claim is checked against these, not against whatever the
# artifact happens to carry.
PUBLISHED_STATIC_MW = {
    "ne_30min_total": 1800.0,
    "ne_10min_total": 1200.0,
    "ne_10min_spin": 600.0,
}

OUT = REPO / "results/calibration/_neiso98_declaration_recheck.json"


def tail_hours(sys_year: pd.DataFrame, pass_label: str, threshold: float) -> int:
    """Hours whose max zonal LMP exceeds ``threshold`` (the C3c model tail).

    Reproduces ``render_calibration_html._tail_hours`` over the same per-zone
    hourly price arrays the renderer builds from ``system_<year>.parquet``.
    """
    sel = sys_year[sys_year["pass"] == pass_label]
    if sel.empty:
        return -1
    hours = int(sel["hour"].max()) + 1
    stack = []
    for _zone, zg in sel.groupby("zone", observed=True):
        full = np.full(hours, np.nan)
        full[zg["hour"].to_numpy()] = zg["price"].to_numpy(float)
        stack.append(full)
    arr = np.nan_to_num(np.vstack(stack), nan=-np.inf)
    return int((arr.max(axis=0) > threshold).sum())


def price_extremes(sys_year: pd.DataFrame, pass_label: str) -> dict:
    """Max/p99.9 of the max-across-zones hourly price — how far the tail is from $300."""
    sel = sys_year[sys_year["pass"] == pass_label]
    wide = sel.pivot_table(index="hour", columns="zone", values="price")
    mx = wide.max(axis=1)
    return {
        "max": round(float(mx.max()), 4),
        "p99_9": round(float(mx.quantile(0.999)), 4),
        "p99": round(float(mx.quantile(0.99)), 4),
        "mean": round(float(mx.mean()), 4),
        "hours": int(len(mx)),
        "margin_to_threshold": round(float(threshold_margin(mx)), 4),
    }


def threshold_margin(mx: pd.Series) -> float:
    """How far the whole-year maximum sits BELOW the $300 tail threshold."""
    return THRESHOLD - float(mx.max())


def payload_tail(run_id: str) -> dict:
    """``ordc.hoursGt200`` per year from the committed dashboard run payload."""
    path = REPO / f"frontend/data/backcast/runs/{run_id}.js"
    if not path.exists():
        return {"_missing": str(path.relative_to(REPO))}
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', path.read_text())
    if m is None:
        return {}
    pay = json.loads(gzip.decompress(base64.b64decode(m.group(1))).decode())
    return {
        y: (d.get("ordc") or {}).get("hoursGt200")
        for y, d in pay.get("years", {}).items()
    }


def reserve_rows(bundle: Path, year: int) -> list[dict]:
    """Per-family binding summary for one year, both passes."""
    rf = pd.read_parquet(bundle / f"hourly/reserve_family_{year}.parquet")
    out = []
    for (pl, fam), g in rf.groupby(["pass", "family"], observed=True):
        slack = g["held_mw"] - g["requirement_mw"]
        req = float(g["requirement_mw"].iloc[0])
        published = PUBLISHED_STATIC_MW.get(str(fam))
        out.append(
            {
                "year": year,
                "pass": str(pl),
                "family": str(fam),
                "family_hours": int(len(g)),
                "requirement_mw": round(req, 1),
                "requirement_is_static": bool(g["requirement_mw"].nunique() == 1),
                "published_static_mw": published,
                "matches_published_static": (
                    None if published is None else bool(abs(req - published) < 1e-6)
                ),
                "shortfall_hours": int((g["shortfall_mw"] > 0).sum()),
                "shortfall_mw_max": round(float(g["shortfall_mw"].max()), 6),
                "held_lt_requirement_hours": int(slack.lt(-1e-6).sum()),
                "held_minus_req_min": round(float(slack.min()), 6),
                "dual_nonzero_hours": int((g["dual"].abs() > 1e-9).sum()),
                "dual_abs_max": float(g["dual"].abs().max()),
            }
        )
    return sorted(out, key=lambda r: (r["pass"], r["family"]))


def main() -> None:
    result: dict = {
        "probe": "neiso98_declaration_recheck",
        "keeper": KEEPER_ID,
        "bundle": str(KEEPER_BUNDLE.relative_to(REPO)),
        "threshold_usd_mwh": THRESHOLD,
        "published_static_mw": PUBLISHED_STATIC_MW,
        "years": list(YEARS),
        "solve_performed": False,
        "c3c_tail": [],
        "price_extremes": [],
        "reserve_families": [],
        "payload_cross_check": {},
    }

    for year in YEARS:
        sysy = pd.read_parquet(KEEPER_BUNDLE / f"hourly/system_{year}.parquet")
        for pl in sorted(sysy["pass"].unique()):
            result["c3c_tail"].append(
                {
                    "year": year,
                    "pass": str(pl),
                    "model_hours_gt_threshold": tail_hours(sysy, str(pl), THRESHOLD),
                }
            )
            result["price_extremes"].append(
                {"year": year, "pass": str(pl), **price_extremes(sysy, str(pl))}
            )
        result["reserve_families"] += reserve_rows(KEEPER_BUNDLE, year)

    result["payload_cross_check"] = {KEEPER_ID: payload_tail(KEEPER_ID)}

    # --- verdicts, computed not asserted -----------------------------------
    tails = {(r["year"], r["pass"]): r["model_hours_gt_threshold"] for r in result["c3c_tail"]}
    rf = result["reserve_families"]
    result["verdict"] = {
        "c3c_model_tail_zero_all_years_both_passes": all(v == 0 for v in tails.values()),
        "passes_covered": sorted({p for _, p in tails}),
        "reserve_dormant_no_shortfall": all(r["shortfall_hours"] == 0 for r in rf),
        "reserve_dormant_held_ge_requirement": all(
            r["held_lt_requirement_hours"] == 0 for r in rf
        ),
        "reserve_dual_zero_to_fp_noise": all(r["dual_abs_max"] < 1e-9 for r in rf),
        "reserve_dual_abs_max_over_all_families": max(r["dual_abs_max"] for r in rf),
        "reserve_family_hours_total": sum(r["family_hours"] for r in rf),
        "all_requirements_match_published_static": all(
            r["matches_published_static"] for r in rf
        ),
        "payload_agrees_with_recomputed_tail": {
            y: (
                (result["payload_cross_check"][KEEPER_ID].get(str(y)) or {}).get("model"),
                tails.get((y, "P1")),
            )
            for y in YEARS
        },
    }

    OUT.write_text(json.dumps(result, indent=2) + "\n")

    print(f"=== C3c model tail (max zonal LMP > ${THRESHOLD:.0f}/MWh) — {KEEPER_ID} ===")
    for r in result["c3c_tail"]:
        print(f"  {r['year']} {r['pass']}: {r['model_hours_gt_threshold']} h")
    print("\n=== max-across-zones price distribution ===")
    for r in result["price_extremes"]:
        print(
            f"  {r['year']} {r['pass']}: max {r['max']:>9.2f}  p99.9 {r['p99_9']:>8.2f}"
            f"  p99 {r['p99']:>7.2f}  mean {r['mean']:>7.2f}"
            f"  (short of $300 by {r['margin_to_threshold']:>7.2f}; {r['hours']} h)"
        )
    print("\n=== reserve families ===")
    for r in result["reserve_families"]:
        print(
            f"  {r['year']} {r['pass']} {r['family']:<16} req {r['requirement_mw']:>7.1f}"
            f" static={str(r['requirement_is_static']):<5}"
            f" =published={str(r['matches_published_static']):<5}"
            f" shortfall_h {r['shortfall_hours']:>5}"
            f" held<req_h {r['held_lt_requirement_hours']:>5}"
            f" |dual|max {r['dual_abs_max']:.3e}"
            f" [{r['family_hours']} fam-h]"
        )
    print("\n=== payload cross-check (ordc.hoursGt200) ===")
    for rid, d in result["payload_cross_check"].items():
        print(f"  {rid}: {json.dumps(d)}")
    print("\n=== verdict ===")
    for k, v in result["verdict"].items():
        print(f"  {k}: {v}")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
