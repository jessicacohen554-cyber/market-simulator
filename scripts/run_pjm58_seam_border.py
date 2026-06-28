"""Driver: PJM 58 — NYISO border re-anchor (seam over-export fix), 2023-2025.

Builds on pjm 57 (measured hydro + CC inframarginal lift) with ONE structural
seam fix: re-anchor NYISO's hr_by_year from the system-average RT LMP to the
WEST zone (Zone A) border-proxy RT LMP.

Why (pjm 57 residuals):

  pjm 57 still over-exports, worst in 2025 (model +43.2 vs actual +18.0 TWh).
  Per-neighbor: NYISO grew from +9.7 (2023) to +29.0 (2025), driven by the
  hr_by_year (9.66/12.92/14.67) being anchored to NYISO's NYC-weighted SYSTEM-
  average RT LMP. PJM-NY exports physically clear at the west-NY (Zone A)
  border, not the system average — the NYC (Zone J/K) congestion premium
  inflates the system average relative to the actual border clearing price.

  Same-month matching (NYISO DART monthly zonal CSVs for months with hourly
  Zone A data vs the system-avg parquet for the same months) gives WEST/system
  ratios of 0.895 (2023), 0.840 (2024), 0.790 (2025). The discount deepens
  in tight years — structurally consistent with NYC congestion widening. Applied
  to system-avg HRs: 9.66*0.895=8.65, 12.92*0.840=10.85, 14.67*0.790=11.59.

  Source: data/raw/lmp-data/NYISO/*realtime_zone_csv.zip → Zone A ("WEST")
  hourly RT LMP. A physical-market-structure correction with a forward analogue
  (border nodal LMP will always differ from system avg in a congested network),
  not tuned to PJM's net-MWh target (CLAUDE.md rule #12).

All other levers — CC inframarginal lift, measured hydro, coal sigmoids — are
pjm 57 verbatim.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import (  # noqa: E402
    _load_reference,
    report_run,
    solve_and_persist,
)

# pjm-57 recipe verbatim (CC inframarginal lift from pjm-56 + measured hydro).
OFFER_CURVE_OVERRIDES = {
    "CC_REGULAR": {
        "committed": 0.75,
        "econ_low": 0.92,
        "econ_high": 1.38,
        "peak": 3.40,
        "econ_low_share": 0.5,
    },
    "CC_CHP": {
        "committed": 0.6624,
        "econ_low": 0.684,
        "econ_high": 0.8208,
        "peak": 1.62,
        "econ_low_share": 0.5,
        "pct_peaking": 8.0,
    },
    "CT_CHP": {
        "committed": 0.864,
        "econ_low": 0.864,
        "econ_high": 0.864,
        "peak": 1.008,
        "econ_low_share": 0.5,
    },
    "CT_PEAKER": {
        "committed": 0.8784,
        "econ_low": 0.8792,
        "econ_high": 1.4656,
        "peak": 4.0,
        "econ_low_share": 0.526,
        "pct_peaking": 7.0,
    },
    "ST_GAS": {
        "committed": 0.4752,
        "econ_low": 0.6552,
        "econ_high": 0.9,
        "peak": 3.024,
        "econ_low_share": 0.5,
        "pct_peaking": 15.0,
    },
    "COAL_LIGNITE": {
        "committed": 0.684,
        "econ_low": 0.8208,
        "econ_high": 0.828,
        "peak": 1.116,
        "econ_low_share": 0.556,
    },
    "COAL_PRB": {
        "committed": 0.684,
        "econ_low": 0.5544,
        "econ_high": 0.80,
        "peak": 1.0656,
        "econ_low_share": 0.556,
    },
    "COAL_BIT": {
        "committed": 0.548,
        "econ_low": 0.6556,
        "econ_high": 1.2664,
        "peak": 1.044,
        "econ_low_share": 0.55,
    },
    "COAL_WC": {
        "committed": 0.512,
        "econ_low": 0.548,
        "econ_high": 0.6344,
        "peak": 0.764,
        "econ_low_share": 0.55,
    },
    "COAL": {
        "committed": 0.648,
        "econ_low": 0.684,
        "econ_high": 0.792,
        "peak": 1.044,
        "econ_low_share": 0.55,
    },
}

PRB_OVERRIDES = {
    "wefor_residual": 0.015,
    "coal_sub_passthrough_sigmoid": True,
    "coal_sub_passthrough_floor": 1.10,
}

BIT_OVERRIDES = {"coal_bit_passthrough_floor": 0.55}


def main() -> int:
    out_dir = Path("results/calibration/pjm58_seam_border")
    reference = _load_reference()
    run_dir = solve_and_persist(
        [2023, 2024, 2025],
        "PJM",
        8760,
        reference,
        commitment=False,
        screen_coal=True,
        run_dir=out_dir,
        outage_source="historic",
        coal_prb_passthrough=1.0,
        coal_prb_passthrough_sigmoid=True,
        coal_mustrun_per_plant=True,
        retiree_cems_cap=True,
        coal_drop_pof=True,
        coal_prb_passthrough_tiered=True,
        prb_overrides=PRB_OVERRIDES,
        coal_bit_sigmoid=True,
        bit_overrides=BIT_OVERRIDES,
        coal_mustrun_online_pmin=True,
        coal_sync_srmc_tranche=True,
        gas_monthly_actuals=True,
        pjm_zonal_gas_basis=True,
        pjm_congestion=True,
        reference_price_interface=True,
        priced_interchange=True,
        cc_derate_from_top=True,
        hydro_eia930_monthly=True,
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 12.0,
        },
        note=(
            "pjm 58 seam-border: NYISO hr_by_year re-anchored from system-avg "
            "RT LMP to WEST zone (Zone A) border-proxy RT LMP. WEST/system "
            "same-month ratios 0.895/0.840/0.790 (2023/24/25) applied to prior "
            "sys-avg HRs: 9.66->8.65, 12.92->10.85, 14.67->11.59. Source: "
            "NYISO DART zonal CSVs (data/raw/lmp-data/NYISO/*realtime_zone*). "
            "Physical market-structure fix: PJM-NY exports clear at west-NY "
            "border, not congestion-inflated NYC system average. Forward "
            "analogue: border congestion discount is persistent structural "
            "feature of NYISO network (rule #12). All other levers pjm 57 "
            "verbatim."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
