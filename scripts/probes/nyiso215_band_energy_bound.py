"""nyiso-215 POST-HOC diagnostics — declared as such, NOT pre-registered gates.

Two questions the P1-P5 record raised and could not itself answer:

**(D1) A strict lower bound on the reserve-duty cohort's MODEL energy.** The
committed ``class_band_hourly`` sidecar carries the ``CC_REGULAR`` ``peak``
band as one series, mixing the duct population with the seven cohort plants.
But the two populations' capacities are known exactly from the same rebuild
that produced P1/P2 (class peak total minus the cohort's 441.7 MW), so in any
hour where the band exceeds the duct population's whole capacity the EXCESS is
provably cohort generation. Summing it gives a lower bound on the cohort's
model energy that needs no attribution assumption at all. It is compared with
the cohort's own EIA-923 net generation — the universal filing, and the only
basis all seven share (7784 Allegany has no CAMPD facility, nyiso-214's
boundary list).

**(D2) Why P2's declared 400 MW magnitude limb missed by 2.252 MW.** With
``cc_reserve_duty_split`` off the seven do not lose their peak band entirely —
they fall back to the class curve's ordinary ``pct_peaking``. D2 measures the
retained MW so the gap is explained by arithmetic rather than asserted.

These are diagnostics on a gate that has already been reported at its literal
outcome; neither restates a gate and neither is used to move one.

Usage::

    uv run python scripts/probes/nyiso215_band_energy_bound.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

BUNDLE = ROOT / "results/calibration/nyiso213_summer_seam"
CENSUS = ROOT / "results/calibration/_nyiso215_reserve_duty_census.json"
OUT = ROOT / "results/calibration/_nyiso215_band_energy_bound.json"
YEARS = (2023, 2024, 2025)
SEVEN = [7784, 10620, 10621, 50744, 54034, 54592, 54593]


def main() -> None:
    """Measure D1 and D2 and write the machine record."""
    rec = json.loads(CENSUS.read_text())
    cohort_mw = rec["P1"]["summed_pmax_mw"]
    class_peak = rec["P2"]["class_peak_mw_keeper"]
    duct_mw = class_peak - cohort_mw

    # ---- D2 -------------------------------------------------------------
    retained = cohort_mw - rec["P2"]["class_peak_mw_fall"]
    out: dict = {
        "session": "nyiso-215",
        "kind": "POST-HOC DIAGNOSTIC — not a pre-registered gate",
        "D2_p2_gap": {
            "cohort_peak_mw_keeper": round(cohort_mw, 3),
            "class_peak_mw_fall_split_off": rec["P2"]["class_peak_mw_fall"],
            "cohort_peak_mw_retained_split_off": round(retained, 3),
            "retained_pct_of_cohort_capacity": round(100.0 * retained / cohort_mw, 3),
            "class_curve_pct_peaking": 8.0,
            "declared_bar_mw": 400.0,
            "shortfall_vs_declared_bar_mw": round(400.0 - rec["P2"]["class_peak_mw_fall"], 3),
        },
        "duct_population_mw_derived": round(duct_mw, 3),
        "nyiso214_form_A_duct_mw": 716.8,
    }

    # ---- D1 -------------------------------------------------------------
    e923 = pd.read_parquet(
        ROOT / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
    )
    per_year = {}
    for year in YEARS:
        band = pd.read_parquet(BUNDLE / "hourly" / f"class_band_hourly_{year}.parquet")
        band = band[
            (band["pass"] == "P1")
            & (band["klass"] == "CC_REGULAR")
            & (band["band"] == "peak")
        ].sort_values("hour")
        mw = band["mw"].to_numpy(dtype=float)
        excess = np.maximum(0.0, mw - duct_mw)
        meas = float(
            e923[(e923["year"] == year) & (e923["plant_id"].isin(SEVEN))][
                "netgen_annual_mwh"
            ].sum()
        )
        # EIA-923's annual column is repeated on each monthly row; de-duplicate
        # to one row per plant-year before summing.
        sub = e923[(e923["year"] == year) & (e923["plant_id"].isin(SEVEN))]
        meas = float(
            sub.drop_duplicates(subset=["plant_id", "year"])["netgen_annual_mwh"].sum()
        )
        per_year[str(year)] = {
            "band_peak_energy_gwh": round(float(mw.sum()) / 1000.0, 3),
            "cohort_lower_bound_energy_gwh": round(float(excess.sum()) / 1000.0, 3),
            "cohort_lower_bound_hours": int((excess > 0).sum()),
            "cohort_eia923_net_gwh": round(meas / 1000.0, 3),
            "lower_bound_over_measured": (
                round(float(excess.sum()) / meas, 4) if meas > 0 else None
            ),
            "cohort_capacity_mw": round(cohort_mw, 3),
            "cohort_measured_cf_from_e923": (
                round(meas / (cohort_mw * 8760.0), 5) if cohort_mw > 0 else None
            ),
        }
    out["D1_energy_bound"] = per_year
    out["D1_note"] = (
        "The lower bound is model GROSS band MW against EIA-923 NET generation, "
        "and it is a LOWER bound only: hours in which the band sits below the "
        "duct population's capacity may still carry cohort generation, so a "
        "ratio below 1 is NOT evidence the cohort under-runs."
    )
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
