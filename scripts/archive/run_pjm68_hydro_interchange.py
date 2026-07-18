"""Driver: PJM 68 — hydro 2025 backfill + interchange balance.

Builds on pjm 67 (reliability floor + CC/CT calibration) with two fixes:

1. **Hydro 2025 backfill** — EIA-923 2025 is an early-release monthly-survey-only
   file carrying only 10 of PJM's ~72 conventional hydro plants (1091 of 3287 MW).
   With ``hydro_backfill_year=2024`` the 62 non-reporting plants carry their 2024
   monthly generation into the 2025 fleet; ``hydro_eia930_monthly=True`` (already
   enabled from pjm-67) then repins all monthly budgets to the measured EIA-930
   ``NG: WAT`` total (~15.5 TWh), correcting both the level and the within-month
   plant-count. This restores the full nameplate envelope so the monthly energy
   budget can clear without capacity-binding.

2. **BTM backfill 2025** — the same EIA-923 incompleteness affects the behind-the-
   meter add-back (CAMPD gross → EIA-923 net class ratios): plants absent from the
   2025 923 vintage get a zero class total, so their BTM add-back is zero. With
   ``btm_backfill_year=2024`` the missing plants borrow their 2024 class generation,
   keeping the BTM correction intact for 2025 where CAMPD confirms the plant ran.

All offer curves, coal sigmoids, congestion, seam-border levers, reliability
floor, CT intermediate split — pjm-67 verbatim.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import (  # noqa: E402
    _load_reference,
    report_run,
    solve_and_persist,
)
from scripts.archive.run_pjm61_consolidate import (  # noqa: E402
    BIT_OVERRIDES,
    PRB_OVERRIDES,
)

OFFER_CURVE_OVERRIDES = {
    "CC_REGULAR": {
        "committed": 0.95,
        "econ_low": 0.92,
        "econ_high": 1.50,
        "peak": 5.0,
        "econ_low_share": 0.55,
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
        "committed": 1.10,
        "econ_low": 1.05,
        "econ_high": 1.40,
        "peak": 4.0,
        "econ_low_share": 0.5,
        "pct_peaking": 20.0,
    },
    "CT_INTERMEDIATE": {
        "committed": 0.90,
        "econ_low": 0.92,
        "econ_high": 1.08,
        "peak": 2.0,
        "econ_low_share": 0.5,
        "pct_peaking": 5.0,
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


def main() -> int:
    out_dir = Path("results/calibration/pjm68_hydro_interchange")
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
        hydro_backfill_year=2024,
        btm_backfill_year=2024,
        reliability_floor=True,
        ct_intermediate_split=True,
        ct_intermediate_cf_threshold=30.0,
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 18.0,
            "offer_curve_smoothing_mid": 0.35,
        },
        note=(
            "pjm 68 hydro backfill + interchange balance: layers on pjm-67 "
            "(reliability floor + CC/CT calibration). Hydro 2025 backfill: "
            "hydro_backfill_year=2024 restores 62 non-reporting EIA-923 hydro "
            "plants from 2024, EIA-930 monthly repin corrects budget level. "
            "BTM backfill: btm_backfill_year=2024 carries 2024 class totals "
            "for plants absent from the 2025 EIA-923 early release. "
            "All offer curves / coal / congestion / seam levers pjm-67 verbatim."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
