"""nyiso-113 probe D — WHY the Zone-K reserve ladder is inert: measure the
headroom, don't infer it.

The nyiso-113 pre-registration argued from a **capacity-vs-demand** screen that
Long Island reserve headroom must collapse at peak: Zone-K thermal nameplate is
5,146.5 MW against an LI peak demand of 5,537 MW (2025). The arm then solved
**INERT** — the LI families never bind in any hour of any year. This probe
measures the quantity the screen should have measured, on the arm's own
unit-hourly sidecar, and states the correction.

The binding condition for `li_10min_total` is NOT "Long Island is short of
energy". Reserve class 1 is **idle-allowed**: its headroom counts
`cap_mw - mw` over EVERY quick-start unit in the zone, dispatched or not. So the
family binds only when Zone K has **less than 120 MW of un-dispatched
quick-start capacity** — and a zone that imports a large share of its own peak
load never drives its local peakers to that state, because the imports serve the
load the peakers would otherwise have had to.

Reported per year:
  * Zone-K quick-start headroom (`Σ cap_mw − mw` over gas_ct/oil units) —
    minimum, p1, and the count of hours below the 120 MW requirement;
  * Zone-K FULL thermal headroom against the 540 MW on-peak 30-minute
    requirement;
  * the same statistics restricted to the hours that actually price the tail
    (LI price > $250), which is where the screen expected the collapse.

Governance: reads the arm's committed sidecars only; no price residual enters
any test. The output is a methodological correction, not a re-tuning.

Usage:
    PYTHONPATH=.:src python scripts/probes/_nyiso113_zonek_headroom.py
Writes: results/calibration/_nyiso113_zonek_headroom.json
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ARM = REPO / "results/calibration/nyiso113_lilocational_B"
OUT = REPO / "results/calibration/_nyiso113_zonek_headroom.json"
YEARS = (2023, 2024, 2025)

LI_10MIN_REQ_MW = 120.0
LI_30MIN_ONPEAK_REQ_MW = 540.0
QUICK_FUELS = ("gas_ct", "oil")
QUICK_GROUPS = ("CT_PEAKER", "CT_CHP")


def main() -> None:
    import numpy as np  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415

    result: dict = {"probe": "nyiso-113 Zone-K reserve headroom", "arm": str(ARM.relative_to(REPO))}
    per_year: dict = {}

    for year in YEARS:
        u = pd.read_parquet(ARM / f"hourly/unit_hourly_{year}.parquet")
        u = u[(u["pass"] == "P1") & (u.zone == "Long_Island")]
        sysd = pd.read_parquet(ARM / f"hourly/system_{year}.parquet")
        sysd = sysd[(sysd["pass"] == "P1") & (sysd.zone == "Long_Island")]
        price = sysd.sort_values("hour").price.to_numpy()

        u = u.assign(headroom=(u.cap_mw - u.mw).clip(lower=0.0))
        quick = u[u.fuel.isin(QUICK_FUELS) | u.plant_group.isin(QUICK_GROUPS)]

        h_quick = quick.groupby("hour").headroom.sum().reindex(range(len(price)), fill_value=0.0).to_numpy()
        h_full = u.groupby("hour").headroom.sum().reindex(range(len(price)), fill_value=0.0).to_numpy()
        disp = u.groupby("hour").mw.sum().reindex(range(len(price)), fill_value=0.0).to_numpy()
        cap = u.groupby("hour").cap_mw.sum().reindex(range(len(price)), fill_value=0.0).to_numpy()

        tail = price > 250.0
        per_year[year] = {
            "n_units_zone_k": int(u.unit_id.nunique()),
            "n_quick_start_units": int(quick.unit_id.nunique()),
            "quick_start_headroom_mw": {
                "min": round(float(h_quick.min()), 1),
                "p1": round(float(np.percentile(h_quick, 1)), 1),
                "median": round(float(np.median(h_quick)), 1),
                "hours_below_requirement": int((h_quick < LI_10MIN_REQ_MW).sum()),
                "requirement_mw": LI_10MIN_REQ_MW,
                "min_as_multiple_of_requirement": round(float(h_quick.min() / LI_10MIN_REQ_MW), 1),
            },
            "full_thermal_headroom_mw": {
                "min": round(float(h_full.min()), 1),
                "p1": round(float(np.percentile(h_full, 1)), 1),
                "hours_below_onpeak_requirement": int((h_full < LI_30MIN_ONPEAK_REQ_MW).sum()),
                "requirement_mw": LI_30MIN_ONPEAK_REQ_MW,
                "min_as_multiple_of_requirement": round(float(h_full.min() / LI_30MIN_ONPEAK_REQ_MW), 1),
            },
            "in_tail_hours_price_gt_250": {
                "n_hours": int(tail.sum()),
                "min_quick_start_headroom_mw": round(float(h_quick[tail].min()), 1) if tail.any() else None,
                "min_full_headroom_mw": round(float(h_full[tail].min()), 1) if tail.any() else None,
            },
            "zone_k_dispatch_at_own_peak_hour": {
                "peak_hour": int(np.argmax(price)),
                "thermal_dispatched_mw": round(float(disp[np.argmax(price)]), 1),
                "thermal_available_mw": round(float(cap[np.argmax(price)]), 1),
                "utilisation": round(float(disp[np.argmax(price)] / max(cap[np.argmax(price)], 1e-9)), 4),
            },
        }

    result["per_year"] = per_year
    result["correction"] = (
        "The pre-registration inferred a headroom collapse from a "
        "capacity-vs-demand comparison (Zone-K thermal nameplate 5,146.5 MW vs "
        "LI peak demand 5,537 MW). That inference is invalid for two reasons the "
        "measurement makes plain: (1) reserve class 1 is IDLE-ALLOWED, so its "
        "headroom counts un-dispatched capacity and the binding condition is "
        "'fewer than 120 MW of Zone-K quick-start is idle', not 'Zone K is short "
        "of energy'; (2) Long Island IMPORTS a large share of its own peak load, "
        "so its local peakers never reach the utilisation the nameplate "
        "comparison implies. A capacity-vs-demand screen is not a headroom "
        "screen for any importing zone with an idle-allowed reserve class."
    )
    OUT.write_text(json.dumps(result, indent=2, default=str))

    for year in YEARS:
        b = per_year[year]
        q, f, t, pk = (
            b["quick_start_headroom_mw"],
            b["full_thermal_headroom_mw"],
            b["in_tail_hours_price_gt_250"],
            b["zone_k_dispatch_at_own_peak_hour"],
        )
        print(f"=== {year} (Zone K: {b['n_units_zone_k']} units, {b['n_quick_start_units']} quick-start) ===")
        print(
            f"  quick-start headroom: min {q['min']} MW = {q['min_as_multiple_of_requirement']}x the "
            f"{q['requirement_mw']} MW requirement; hours below it: {q['hours_below_requirement']}"
        )
        print(
            f"  full thermal headroom: min {f['min']} MW = {f['min_as_multiple_of_requirement']}x the "
            f"{f['requirement_mw']} MW on-peak requirement; hours below it: {f['hours_below_onpeak_requirement']}"
        )
        print(
            f"  in the {t['n_hours']} tail hours (>$250): min quick-start headroom "
            f"{t['min_quick_start_headroom_mw']} MW, min full headroom {t['min_full_headroom_mw']} MW"
        )
        print(
            f"  at LI's own peak-price hour h{pk['peak_hour']}: thermal {pk['thermal_dispatched_mw']} / "
            f"{pk['thermal_available_mw']} MW = {pk['utilisation']:.1%} utilisation"
        )
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
