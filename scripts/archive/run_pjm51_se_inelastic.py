"""Driver: PJM 51 — Southeast gas-inelastic seam, 2023-2025 bundle.

Reproduces the pjm-49/50 seam-diagnostic BASE config (the pjm-48 coal keeper +
pjm-49 per-year MISO/NYISO HR anchors + pjm-50 firm-export floor / losses hurdle /
TVA-LGEE seams, both now in src) and adds the ONE new lever this run studies: the
Southeast (Carolinas/TVA/LGEE) gas-INELASTIC affine reference price
(neighbor_price._HR_GAS_ELASTIC, derive_southeast_inelastic_hr.py).

The keeper lever set is taken verbatim from pjm-49's committed
run_config.json calibration_flags (the seam-diagnostic base), so this is an
apples-to-apples continuation of the seam series — only the Southeast pricing
changed. Years are solved sequentially in one process (a PJM per-plant year peaks
~13 GB in HiGHS; one at a time stays under the box's 15 GB).
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

# pjm-49 base recipe (results/calibration/pjm49_seam_hr/run_config.json),
# verbatim — the seam-diagnostic base. Only the Southeast _HR_GAS_ELASTIC entry
# (in src) is new this run.
OFFER_CURVE_OVERRIDES = {
    "CC_REGULAR": {
        "committed": 0.6624,
        "econ_low": 0.7644,
        "econ_high": 1.1428,
        "peak": 2.77,
        "econ_low_share": 0.5,
        "pct_peaking": 8.0,
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
        "econ_high": 0.8568,
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

# prb_overrides channel (recipe coal_prb_sigmoid_overrides + the non-None toggles
# main() routes through this dict). coal_plant_monthly_pricing stays at PJM's
# internal default (True) by leaving it unset.
PRB_OVERRIDES = {
    "wefor_residual": 0.015,
    "coal_sub_passthrough_sigmoid": True,
}
BIT_OVERRIDES = {"coal_bit_passthrough_floor": 0.76}


def main() -> int:
    out_dir = Path("results/calibration/pjm51_se_inelastic")
    reference = _load_reference()
    run_dir = solve_and_persist(
        [2023, 2024, 2025],
        "PJM",
        8760,
        reference,
        commitment=False,
        screen_coal=True,  # commitment_screen_coal
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
        gas_monthly_actuals=True,
        reference_price_interface=True,
        priced_interchange=True,
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        note=(
            "pjm 51 SE-inelastic: pjm-49/50 seam base (pjm-48 coal keeper + "
            "MISO/NYISO hr_by_year + firm-export floor + losses hurdle + TVA/LGEE) "
            "+ Southeast (Carolinas/TVA/LGEE) gas-INELASTIC affine reference price "
            "(_HR_GAS_ELASTIC 5.6*gas+14.2, derive_southeast_inelastic_hr.py). "
            "Targets the 2025 wrong-direction Southeast export (+18 TWh) that fed "
            "the coal over-run."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
