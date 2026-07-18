"""Driver: PJM 69 — interchange caps + CC/CT rebalance.

Builds on pjm 68 (hydro backfill + BTM backfill) with two structural fixes:

1. **PJM seam flow caps** — The reference-price interface exports at full TTC
   on all 5 seams simultaneously (~16.3 GW), producing ~38 TWh net export every
   year regardless of actuals (2023=40, 2024=33, 2025=18). Enabling
   ``pjm_seam_flow_limit=True`` + ``pjm_seam_export_limit=True`` caps each
   neighbor's import/export bands at the measured per-neighbor deliverability
   envelope from the PJM tie-line file (border zones summed to neighbor level,
   per (month x hod) p90). This should pull 2025 net interchange from ~38 → ~18-22
   TWh, cascading into C2 volume and C3a price improvements.

2. **CC/CT offer curve rebalance** — 2024 CC_REGULAR over-dispatches by +19.9 TWh
   while CT_PEAKER under-dispatches by −11.6 TWh. Shift CC rightward (committed
   0.95 → 1.00) and let CTs compete earlier (committed 1.10 → 1.05) to rebalance
   the fuel-mix dispatch.

All other settings (coal sigmoids, passthrough, must-run, drop-pof, sync-srmc,
gas monthly actuals, PJM zonal gas basis, PJM congestion, reference-price
interface, priced interchange, CC derate from top, hydro EIA-930 monthly,
hydro_backfill_year=2024, btm_backfill_year=2024, reliability floor, CT
intermediate split, curve smoothing) preserved from pjm-68 verbatim.
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
        "committed": 1.00,
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
        "committed": 1.05,
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
    out_dir = Path("results/calibration/pjm69_interchange_caps")
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
        pjm_seam_flow_limit=True,
        pjm_seam_export_limit=True,
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 18.0,
            "offer_curve_smoothing_mid": 0.35,
        },
        note=(
            "pjm 69 interchange caps + CC/CT rebalance: layers on pjm-68. "
            "PJM seam flow caps: pjm_seam_flow_limit + pjm_seam_export_limit "
            "cap each of PJM's 5 reference-price seams (MISO/NYISO/Carolinas/"
            "TVA/LGEE) at the measured per-neighbor tie-line deliverability "
            "envelope (p90). Target: 2025 net interchange ~38 -> ~18-22 TWh. "
            "CC/CT rebalance: CC_REGULAR committed 0.95->1.00 (shift CC "
            "rightward), CT_PEAKER committed 1.10->1.05 (let CTs compete "
            "earlier). All other settings pjm-68 verbatim."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
