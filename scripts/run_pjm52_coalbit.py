"""Driver: PJM 52 — coal-BIT sticky-online stack, 2023-2025 bundle.

Continuation of the pjm-51 Southeast-inelastic seam BASE (verbatim), adding the
MISO coal-bituminous 3-lever stack (all ISO-agnostic, already on main) to fix
the structural bit under-run that has dogged every PJM keeper: COAL_BIT model vs
actual was 85.3 vs 110.9 (-23%) 2023, 86.7 vs 111.7 (-22%) 2024, 122.9 vs 133.7
(-8%) 2025, with the mirror-image gas-CC over-run (+40 TWh). Root cause = the
merit-order triangle: at full delivered cost PJM bituminous sits out-of-merit vs
the cheap gas-CC swing in cheap-gas years, so the dispatchable bands cycle DOWN
(2023/24 under) and over-respond in dear 2025. The real fleet ran FLAT (~111 TWh,
heavily take-or-pay / must-run).

Three levers, on top of the pjm-51 base:

  Lever 1 (the big one) — sticky online-sync floor. ``coal_mustrun_online_pmin``
    sizes the coal must-run band to the measured online-net-MW Pmin (PJM
    thermal_tranches: ~31% nameplate mean vs the all-hours ~16% mustrun_pct, so
    the forced-on floor roughly doubles) and ``coal_sync_srmc_tranche`` splits it
    into a fuel-free contracted floor + a full-SRMC sync band, both forced on.
    The 2026-06-27 erosion fix holds the coal_sync_pmin_mw tranches at
    availability=1.0 so the statistical WEFOR derate cannot pull the floor below
    its measured cap; real outages still relax it. This is what makes PJM
    bituminous hold flat across the gas cycle.

  Lever 2 — coal min-run / min-down 36/16 (NREL baseload class), the default for
    coal on CAMPD-binning ISOs with no Min_Run column (PJM included). Active only
    when the commitment screen runs with coal screened, so P2 runs with
    ``screen_coal=True`` (already in the pjm-51 base) — bit cannot cycle with
    peaker agility.

  Lever 3 — gas-keyed bituminous BID sigmoid (``coal_bit_sigmoid``). PJM bit is
    way under in cheap gas, so the COAL_SIGMOID_DEFAULTS[("PJM","bituminous")]
    floor 0.76 is dropped to 0.68 — a deeper cheap-gas take-or-pay / stay-running
    bid discount — while the dear-gas ceiling (1.32) is left put. Conservative
    end of the plan's 0.60-0.68 range because Lever 1 already forces substantially
    more coal on; stacking an aggressive floor on top risks overshoot. It marks
    the BID gas-keyed (discounts the offer, NOT the delivered coal price);
    forward-reproducible (rule #12, C6-clean).

Everything else is the pjm-51 seam base unchanged (pjm-48 coal keeper + pjm-49
MISO/NYISO HR anchors + pjm-50 firm-export floor / losses hurdle / TVA-LGEE +
pjm-51 Southeast gas-INELASTIC affine reference price). Years are solved
sequentially in one process (a PJM per-plant year peaks ~13 GB in HiGHS; one at a
time stays under the box's 15 GB).
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

# pjm-51 base recipe (results/calibration/pjm51_se_inelastic/run_config.json),
# verbatim — the seam-diagnostic base. Coal levers are new this run.
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
# Lever 3: deepen the bituminous cheap-gas BID discount. PJM default floor 0.76
# -> 0.68 (conservative end of the 0.60-0.68 plan range; Lever 1 also forces more
# coal on, so this stays mild to avoid overshoot). Dear-gas ceiling left at the
# table default (1.32).
BIT_OVERRIDES = {"coal_bit_passthrough_floor": 0.68}


def main() -> int:
    out_dir = Path("results/calibration/pjm52_coalbit")
    reference = _load_reference()
    run_dir = solve_and_persist(
        [2023, 2024, 2025],
        "PJM",
        8760,
        reference,
        commitment=False,
        screen_coal=True,  # commitment_screen_coal -> Lever 2 (coal 36/16) fires in P2
        run_dir=out_dir,
        outage_source="historic",
        coal_prb_passthrough=1.0,
        coal_prb_passthrough_sigmoid=True,
        coal_mustrun_per_plant=True,
        retiree_cems_cap=True,
        coal_drop_pof=True,
        coal_prb_passthrough_tiered=True,
        prb_overrides=PRB_OVERRIDES,
        coal_bit_sigmoid=True,  # Lever 3
        bit_overrides=BIT_OVERRIDES,  # Lever 3 floor 0.76 -> 0.68
        coal_mustrun_online_pmin=True,  # Lever 1: size must-run to online-net-MW Pmin
        coal_sync_srmc_tranche=True,  # Lever 1: split into fuel-free floor + full-SRMC sync band
        gas_monthly_actuals=True,
        reference_price_interface=True,
        priced_interchange=True,
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        note=(
            "pjm 52 coal-bit sticky stack: pjm-51 SE-inelastic seam base + MISO "
            "coal-bituminous 3-lever stack. Lever 1 sticky online-sync floor "
            "(coal_mustrun_online_pmin + coal_sync_srmc_tranche; sizes coal "
            "must-run to the measured ~31% online-net-MW Pmin vs ~16% all-hours, "
            "split into fuel-free floor + full-SRMC sync band, both forced on, "
            "erosion fix at availability=1.0). Lever 2 coal min-run/min-down "
            "36/16 (NREL baseload) firing in the P2 coal screen. Lever 3 "
            "bituminous BID sigmoid floor 0.76 -> 0.68 (deeper cheap-gas "
            "take-or-pay discount, dear-gas ceiling 1.32 put). Targets the "
            "structural COAL_BIT under-run (-23%/-22%/-8%) and the mirror gas-CC "
            "over-run / seam over-export — one unified merit-order fix."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
