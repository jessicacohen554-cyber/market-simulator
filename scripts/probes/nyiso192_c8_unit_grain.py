"""nyiso-192 — the C8 forced-energy share of `ST_GAS` at UNIT grain, on a solved bundle.

nyiso-181 §6 measured that the committed D-2 row under-counts forced energy by
~1 TWh/yr because ``aggregate_floors_by_plant`` tests the PLANT total against the
PLANT floor, so a unit pinned at its own floor inside a plant whose other units
run freely disappears from the count; it escalated the consequence for C8 to the
scorer lane and did not act. This probe re-measures the exposure on ANY solved
bundle that carries its gitignored ``hourly/unit_hourly_<year>.parquet`` and
``floors/<year>_P1.npz`` (both written by every solve), using D-2's own
``at_floor_mask`` and tolerances, at unit grain — so the current keeper's
exposure is a number rather than an inference from a superseded keeper.

Usage:
    python scripts/probes/nyiso192_c8_unit_grain.py results/calibration/<bundle> [--label NAME]

Diagnostic only (rule 13): nothing is re-scored; C8's committed verdict stands
until the scorer lane re-bases the grain.
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
CLASSES = ("ST_GAS", "CC_REGULAR", "CT_PEAKER", "CC_CHP")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle")
    ap.add_argument("--label", default=None)
    args = ap.parse_args()
    bundle = Path(args.bundle)
    if not bundle.is_absolute():
        bundle = REPO / bundle
    rec = {
        "session": "nyiso-192",
        "bundle": str(bundle.relative_to(REPO)),
        "by_year": {},
    }
    for year in YEARS:
        uh = pd.read_parquet(
            bundle / "hourly" / f"unit_hourly_{year}.parquet",
            columns=["pass", "unit_id", "plant_group", "hour", "mw", "cap_mw"],
        )
        uh = uh[uh["pass"] == "P1"]
        fl = np.load(bundle / "floors" / f"{year}_P1.npz", allow_pickle=True)
        unit_ids = [str(u) for u in fl["unit_ids"]]
        idx = {u: i for i, u in enumerate(unit_ids)}
        piv = uh.pivot(index="unit_id", columns="hour", values="mw")
        piv = piv.reindex(columns=range(fl["min_gen"].shape[1])).fillna(0.0)
        groups = uh.groupby("unit_id", observed=True).plant_group.first()
        yrec = {}
        for klass in CLASSES:
            units = [u for u in piv.index if groups.get(u) == klass and u in idx]
            if not units:
                continue
            disp = piv.loc[units].to_numpy(dtype=float)
            mg = fl["min_gen"][[idx[u] for u in units]].astype(float)
            mask = at_floor_mask(disp, mg)
            forced = float((disp * mask).sum()) / 1e6
            total = float(disp.sum()) / 1e6
            yrec[klass] = {
                "units": len(units),
                "class_twh": round(total, 4),
                "unit_grain_forced_twh": round(forced, 4),
                "unit_grain_forced_share": round(forced / total, 4)
                if total > 0
                else None,
            }
        rec["by_year"][str(year)] = yrec
        print(
            year,
            {
                k: (v["unit_grain_forced_share"], v["unit_grain_forced_twh"])
                for k, v in yrec.items()
            },
        )
    label = args.label or bundle.name
    out = REPO / "results" / "calibration" / f"_nyiso192_c8_unit_grain_{label}.json"
    out.write_text(json.dumps(rec, indent=2))
    print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
