"""C8 forced-energy share at UNIT grain, taken on D-2's own class denominator.

`nyiso192_c8_unit_grain.py` measures the unit-grain numerator correctly but
divides it by the dispatch of the FLOORED units only — the units present in
``floors/<year>_P1.npz``. C8's cap is defined against **class energy**
(``share_of_class = forced_twh / class_total_twh`` in the committed D-2 rows),
so a class whose unfloored units carry real energy has its unit-grain share
overstated by that probe: the numerator is re-attributed AND the denominator
shrinks, and only the first of those is the grain question.

This probe re-divides the same unit-grain numerator by the committed bundle's
own D-2 ``class_total_twh``, so the plant-grain and unit-grain shares are
like-for-like and the difference is attributable to grain alone.

Diagnostic only (rule 13 ``[R-MEASURED]``): nothing is re-scored, and C8's
committed plant-grain verdict stands until the scorer lane re-bases the grain
(the nyiso-193 decision card).

Usage:
    python scripts/probes/c8_unit_grain_class_basis.py \
        --replay scratch/c8grain/NYISO_replay \
        --committed results/calibration/nyiso196_extract_basis \
        --iso NYISO
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.legitimacy_diagnostics import at_floor_mask  # noqa: E402

YEARS = (2023, 2024, 2025)
CLASSES = ("ST_GAS", "CC_REGULAR", "CT_PEAKER", "CC_CHP", "CT_CHP", "ST_CHP")
CAP = 0.30


def _d2_totals(committed: Path) -> dict[tuple[int, str], dict[str, float]]:
    """Committed plant-grain D-2 rows, summed over mechanisms per (year, class)."""
    diag = json.loads((committed / "legitimacy_diagnostics.json").read_text())
    out: dict[tuple[int, str], dict[str, float]] = {}
    for row in diag["diagnostics"]["D2"]["rows"]:
        klass = row.get("class")
        if not klass:
            continue
        key = (int(row["year"]), klass)
        rec = out.setdefault(key, {"forced_twh": 0.0, "class_total_twh": 0.0})
        rec["forced_twh"] += float(row["forced_twh"])
        rec["class_total_twh"] = float(row["class_total_twh"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--replay", required=True, help="bundle carrying hourly/ + floors/")
    ap.add_argument("--committed", required=True, help="the registered keeper bundle")
    ap.add_argument("--iso", required=True)
    args = ap.parse_args()

    replay = Path(args.replay)
    committed = Path(args.committed)
    if not replay.is_absolute():
        replay = REPO / replay
    if not committed.is_absolute():
        committed = REPO / committed

    d2 = _d2_totals(committed)
    rec = {
        "iso": args.iso,
        "replay_bundle": str(replay),
        "committed_bundle": str(committed.relative_to(REPO)),
        "cap": CAP,
        "note": (
            "unit-grain numerator over the committed D-2 class denominator; "
            "plant-grain column is the committed C8 as scored"
        ),
        "by_year": {},
    }

    for year in YEARS:
        uh_path = replay / "hourly" / f"unit_hourly_{year}.parquet"
        fl_path = replay / "floors" / f"{year}_P1.npz"
        if not uh_path.exists() or not fl_path.exists():
            continue
        uh = pd.read_parquet(
            uh_path, columns=["pass", "unit_id", "plant_group", "hour", "mw"]
        )
        uh = uh[uh["pass"] == "P1"]
        fl = np.load(fl_path, allow_pickle=True)
        idx = {str(u): i for i, u in enumerate(fl["unit_ids"])}
        piv = uh.pivot(index="unit_id", columns="hour", values="mw")
        piv = piv.reindex(columns=range(fl["min_gen"].shape[1])).fillna(0.0)
        groups = uh.groupby("unit_id", observed=True).plant_group.first()

        yrec = {}
        for klass in CLASSES:
            floored = [u for u in piv.index if groups.get(u) == klass and u in idx]
            member = [u for u in piv.index if groups.get(u) == klass]
            if not floored:
                continue
            disp = piv.loc[floored].to_numpy(dtype=float)
            mg = fl["min_gen"][[idx[u] for u in floored]].astype(float)
            forced = float((disp * at_floor_mask(disp, mg)).sum()) / 1e6
            floored_twh = float(disp.sum()) / 1e6
            replay_class_twh = float(piv.loc[member].to_numpy(dtype=float).sum()) / 1e6

            d = d2.get((year, klass))
            denom = d["class_total_twh"] if d else None
            yrec[klass] = {
                "units_in_class": len(member),
                "units_with_floor_rows": len(floored),
                "replay_class_twh": round(replay_class_twh, 4),
                "d2_class_total_twh": round(denom, 4) if denom else None,
                "plant_grain_forced_twh": round(d["forced_twh"], 4) if d else 0.0,
                "plant_grain_share": round(d["forced_twh"] / denom, 4)
                if d and denom
                else 0.0,
                "unit_grain_forced_twh": round(forced, 4),
                # the number the nyiso-192 probe reports (floored-unit denominator)
                "unit_grain_share_floored_basis": round(forced / floored_twh, 4)
                if floored_twh
                else None,
                # the like-for-like number C8's cap is actually defined against
                "unit_grain_share_class_basis": round(forced / denom, 4)
                if denom
                else None,
                "breaches_cap_class_basis": bool(denom and forced / denom > CAP),
            }
        rec["by_year"][str(year)] = yrec

    out = (
        REPO / "results" / "calibration" / f"_c8_unit_grain_class_basis_{args.iso}.json"
    )
    out.write_text(json.dumps(rec, indent=2))

    print(f"{args.iso}  cap {CAP}")
    hdr = f"  {'year':<5} {'class':<11} {'plant':>7} {'unit(fl)':>9} {'unit(cls)':>10}  denom"
    print(hdr)
    for year, rows in rec["by_year"].items():
        for klass, r in rows.items():
            if (r["d2_class_total_twh"] or 0) < 1.0:
                continue
            flag = "  <-- OVER CAP" if r["breaches_cap_class_basis"] else ""
            print(
                f"  {year:<5} {klass:<11} {r['plant_grain_share']:>7.3f} "
                f"{r['unit_grain_share_floored_basis']:>9.3f} "
                f"{r['unit_grain_share_class_basis']:>10.3f}  "
                f"{r['d2_class_total_twh']:>7.2f} TWh{flag}"
            )
    print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
