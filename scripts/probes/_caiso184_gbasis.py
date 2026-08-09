"""caiso-184 G-BASIS — does the repaired basis actually remove the f_CEMS > 1 excess?

PRECHECK §8, verbatim: *"the repaired basis must REDUCE measured `f_CEMS > 1`
capacity-year by >= 50 % without pushing any bin's `f_CEMS` materially BELOW its
measured demonstrated output (over-correction is as wrong as under-correction)."*

Both halves are measured against the SAME denominator the shipped loader uses, off
and on, so the gate scores the repair rather than a reconstruction of it.

* **REDUCTION leg** — ``X = Sum_t (CEMS_gross - D)^+`` over every CAISO bin, with D the
  shipped ``_iso_plant_capacity`` unarmed vs armed. Bar: >= 50 % reduction, every year.
* **OVER-CORRECTION leg** — the armed denominator against the extract's OWN
  ``plant_capacity_mw``, which the deriver builds from the same ``derate_mw``
  capacities as the numerator, over single-``plant_group`` facilities. A denominator
  raised materially ABOVE that is capacity the plant never demonstrated. Bar: the
  median ratio must stay within 5 % of 1.0 and must not FALL below 0.95 (the armed
  denominator exceeding demonstrated capability by > 5 % on the median bin).

Usage::

    python scripts/probes/_caiso184_gbasis.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.data.outages import (  # noqa: E402
    UNIT_OUTAGE_MIN_DAYS,
    _generic_unit_outage_target,
    _iso_plant_capacity,
    unit_outage_csv_for_iso,
)

from scripts.probes._caiso184_capacity_basis_census import _bin_cems  # noqa: E402

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
OUT = REPO / "results" / "calibration" / "_caiso184_gbasis.json"
REDUCTION_BAR = 0.50
OVERCORRECTION_FLOOR = 0.95


def main() -> None:
    off = _iso_plant_capacity(ISO)
    on = _iso_plant_capacity(ISO, False, True)
    rec: dict = {"reduction": {}, "bars": {
        "reduction": REDUCTION_BAR, "overcorrection_floor": OVERCORRECTION_FLOOR}}

    for year in YEARS:
        cems = _bin_cems(year)
        x_off = x_on = 0.0
        h_off = h_on = 0
        for tgt, gross in cems.items():
            if tgt not in off:
                continue
            x_off += float(np.clip(gross - off[tgt], 0.0, None).sum())
            x_on += float(np.clip(gross - on[tgt], 0.0, None).sum())
            h_off += int((gross > off[tgt]).sum())
            h_on += int((gross > on[tgt]).sum())
        rec["reduction"][str(year)] = {
            "f_cems_gt_1_mwh_unarmed": round(x_off, 1),
            "f_cems_gt_1_mwh_armed": round(x_on, 1),
            "reduction": round(1.0 - x_on / x_off, 6) if x_off else 0.0,
            "bin_hours_unarmed": h_off,
            "bin_hours_armed": h_on,
        }

    # Over-correction: armed denominator vs the extract's own same-basis capacity.
    df = pd.read_csv(unit_outage_csv_for_iso(ISO))
    df = df[df["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]
    gpf = df.groupby("facility_id")["plant_group"].nunique()
    single = set(gpf[gpf == 1].index)
    ratios, seen, worst = [], set(), []
    for r in df.itertuples(index=False):
        tgt = _generic_unit_outage_target(int(r.facility_id), r.unit_id, r.plant_group)
        if tgt is None or tgt in seen or tgt not in on or int(r.facility_id) not in single:
            continue
        seen.add(tgt)
        ext = float(r.plant_capacity_mw)
        if ext <= 0:
            continue
        ratios.append(ext / on[tgt])
        worst.append({"bin": f"{tgt[0]}:{tgt[1]}", "capacity_source": str(r.capacity_source),
                      "extract_mw": ext, "armed_denominator_mw": round(on[tgt], 3),
                      "ratio": round(ext / on[tgt], 4)})
    worst.sort(key=lambda d: d["ratio"])
    med = float(np.median(ratios)) if ratios else 0.0
    rec["overcorrection"] = {
        "n_bins": len(ratios),
        "median_extract_over_armed_denominator": round(med, 4),
        "mean": round(float(np.mean(ratios)), 4) if ratios else 0.0,
        "n_bins_below_floor": sum(1 for x in ratios if x < OVERCORRECTION_FLOOR),
        "lowest_5_bins": worst[:5],
    }
    red_pass = all(v["reduction"] >= REDUCTION_BAR for v in rec["reduction"].values())
    over_pass = med >= OVERCORRECTION_FLOOR
    rec["verdict"] = {
        "reduction_leg": "PASS" if red_pass else "FAIL",
        "overcorrection_leg": "PASS" if over_pass else "FAIL",
        "G_BASIS": "PASS" if (red_pass and over_pass) else "FAIL",
    }
    OUT.write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps({"reduction": rec["reduction"], "overcorrection": {
        k: v for k, v in rec["overcorrection"].items() if k != "lowest_5_bins"},
        "verdict": rec["verdict"]}, indent=1))
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
