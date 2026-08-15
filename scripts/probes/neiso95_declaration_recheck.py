"""neiso-95 — re-verify the NEISO `frontier` and `complete` declarations on the CURRENT keeper.

Read-only, committed-artifact-only. **No LP is constructed and no year is solved,
scored or registered.** Every number below comes from files already in the repo:

  * the keeper bundle's own hourly sidecars
    (``results/calibration/neiso93_envelope_A/hourly/{system,reserve_family}_<year>.parquet``),
  * the committed run payload (``frontend/data/backcast/runs/<id>.js``), and
  * the superseded keeper's bundle, for the carried-forward comparison.

The `frontier` declaration (2026-07-11) rests on C3c being the binding frontier
with the model scarcity tail identically 0. This probe re-establishes that from
the neiso-93 keeper's OWN artifacts rather than carrying the claim forward:

  1. **C3c model tail** — hours whose MAX zonal LMP exceeds the NEISO $300/MWh
     threshold, per year and per pass. The definition is pinned to
     ``render_calibration_html._tail_hours`` (max across zones, NaN → -inf) so
     the recomputation is comparable to the payload's ``ordc.hoursGt200.model``,
     which is cross-checked here.
  2. **Reserve-family binding** — ``shortfall_mw`` and ``held_mw`` vs
     ``requirement_mw`` per family-hour. ``reserve_family_<year>.parquet`` is the
     ONLY artifact in which a locational reserve family's binding is observable
     (CLAUDE.md rule 15): ``system``'s ``reserve_price`` is the cross-family SUM
     broadcast identically to every zone.
  3. **Delta vs the superseded keeper** — whether any C3c evidence moved.

Rule 22 ``[R-HOLDOUT]``: only 2023-2025 artifacts are read. Nothing here touches
2019-2022 or H1-2026.

Usage::

    uv run python scripts/probes/neiso95_declaration_recheck.py
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
KEEPER_ID = "2026-08-14-neiso-93-envelope"
KEEPER_BUNDLE = REPO / "results/calibration/neiso93_envelope_A"
PRIOR_ID = "2026-08-06-neiso-87-control"
PRIOR_BUNDLE = REPO / "results/calibration/neiso87_control_A"
YEARS = (2023, 2024, 2025)
THRESHOLD = 300.0  # NEISO C3c tail threshold, calibration_verdict.TAIL_THRESHOLD
OUT = REPO / "results/calibration/_neiso95_declaration_recheck.json"


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
    }


def payload_tail(run_id: str) -> dict:
    """``ordc.hoursGt200`` per year from the committed dashboard run payload."""
    src = (REPO / f"frontend/data/backcast/runs/{run_id}.js").read_text()
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', src)
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
        out.append(
            {
                "year": year,
                "pass": str(pl),
                "family": str(fam),
                "family_hours": int(len(g)),
                "requirement_mw": round(float(g["requirement_mw"].iloc[0]), 1),
                "requirement_is_static": bool(g["requirement_mw"].nunique() == 1),
                "shortfall_hours": int((g["shortfall_mw"] > 0).sum()),
                "shortfall_mw_max": round(float(g["shortfall_mw"].max()), 6),
                "held_lt_requirement_hours": int(slack.lt(-1e-6).sum()),
                "held_minus_req_min": round(float(slack.min()), 6),
                "dual_nonzero_hours": int((g["dual"].abs() > 1e-9).sum()),
                "dual_max": round(float(g["dual"].max()), 6),
            }
        )
    return sorted(out, key=lambda r: (r["pass"], r["family"]))


def main() -> None:
    result: dict = {
        "probe": "neiso95_declaration_recheck",
        "keeper": KEEPER_ID,
        "prior_keeper": PRIOR_ID,
        "threshold_usd_mwh": THRESHOLD,
        "years": list(YEARS),
        "solve_performed": False,
        "c3c_tail": [],
        "price_extremes": [],
        "reserve_families": [],
        "payload_cross_check": {},
        "prior_keeper_tail": [],
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

        prior_sys = PRIOR_BUNDLE / f"hourly/system_{year}.parquet"
        if prior_sys.exists():
            psy = pd.read_parquet(prior_sys)
            for pl in sorted(psy["pass"].unique()):
                result["prior_keeper_tail"].append(
                    {
                        "year": year,
                        "pass": str(pl),
                        "model_hours_gt_threshold": tail_hours(psy, str(pl), THRESHOLD),
                    }
                )

    result["payload_cross_check"] = {
        KEEPER_ID: payload_tail(KEEPER_ID),
        PRIOR_ID: payload_tail(PRIOR_ID),
    }

    OUT.write_text(json.dumps(result, indent=2) + "\n")

    print(f"=== C3c model tail (max zonal LMP > ${THRESHOLD:.0f}/MWh) — {KEEPER_ID} ===")
    for r in result["c3c_tail"]:
        print(f"  {r['year']} {r['pass']}: {r['model_hours_gt_threshold']} h")
    print("\n=== max-across-zones price distribution ===")
    for r in result["price_extremes"]:
        print(
            f"  {r['year']} {r['pass']}: max {r['max']:>9.2f}  p99.9 {r['p99_9']:>8.2f}"
            f"  p99 {r['p99']:>7.2f}  mean {r['mean']:>7.2f}  ({r['hours']} h)"
        )
    print("\n=== reserve families ===")
    for r in result["reserve_families"]:
        print(
            f"  {r['year']} {r['pass']} {r['family']:<16} req {r['requirement_mw']:>7.1f}"
            f" static={str(r['requirement_is_static']):<5}"
            f" shortfall_h {r['shortfall_hours']:>5} (max {r['shortfall_mw_max']})"
            f" held<req_h {r['held_lt_requirement_hours']:>5}"
            f" dual!=0_h {r['dual_nonzero_hours']:>5} (max {r['dual_max']})"
            f" [{r['family_hours']} fam-h]"
        )
    print("\n=== payload cross-check (ordc.hoursGt200) ===")
    for rid, d in result["payload_cross_check"].items():
        print(f"  {rid}: {json.dumps(d)}")
    print(f"\n=== prior keeper {PRIOR_ID} tail (same definition) ===")
    for r in result["prior_keeper_tail"]:
        print(f"  {r['year']} {r['pass']}: {r['model_hours_gt_threshold']} h")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
