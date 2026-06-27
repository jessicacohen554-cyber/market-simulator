"""Driver: PJM 53 — zonal (regional) gas basis, 2023-2025 bundle.

Continuation of the pjm-52 coal-BIT sticky-online stack (verbatim — the full
keeper lever stack incl. the MISO coal 3-lever set is preserved below), adding
ONE structural lever: a PJM per-zone gas basis (``pjm_zonal_gas_basis``).

THE DIAGNOSIS (from the pjm-52 regional decomposition): PJM clears as a SINGLE
COPPER-PLATE — all 8 zones at one LMP ($25.34 in 2024, 0.000 zonal spread in
every one of 8760 hours). The internal transmission topology exists
(ComEd→AEP, AEP→Dominion, Central_PA→EMAAC, SWMAAC→EMAAC, …) but never binds.
Root cause: gas is priced ISO-WIDE (one delivered EIA-923 monthly series), so
every gas-CC has the same marginal cost → every zone clears identically → no
flow pressure → no congestion. The unified miss that follows: eastern PJM
(EMAAC/SWMAAC/Dominion, ~38% of load) burns DEAR Transco Z6 / TETCO M3 gas but
is priced at the cheap ISO average → eastern CC_REGULAR over-runs (+54 TWh
ISO-wide) and pins the price low → western bituminous coal (94% of PJM bit lives
in AEP_Ohio + West_APS) is undercut → coal under-runs (-15 TWh) → PJM clears
below MISO/NYISO/Southeast → over-exports (+63 vs +32.7 actual). C3a LMP 2024
-10.9% / 2025 -14.9%.

THE LEVER (the structural fix, rule #1): mirror the ERCOT/NYISO zonal gas basis.
``pjm_zonal_gas_basis`` shifts each gas unit by its zone's measured
delivered-to-electric-power basis vs Henry Hub (data/raw/pjm_zonal_gas_hub.csv —
EIA N3045<ST>3M by the zone's primary state, a forward-reproducible measured
series), anchored to a gas-capacity-weighted mean of ZERO so the calibrated PJM
fleet-aggregate gas level is preserved and ONLY the cross-zonal spread opens
(west coal belt cheap, EMAAC/SWMAAC/Dominion dear). Expectation: dear east gas →
eastern zones want cheap western power → west→east flows rise → the
Central_PA→EMAAC / SWMAAC→EMAAC TTCs bind → eastern LMP separates UP (dear gas +
congestion premium), western LMP stays low. ONE lever for four symptoms: lifts
PJM load-weighted price toward actual (C3a), backs out eastern CC_REGULAR (the
+54 over-run), lets western coal run to serve the east up to TTC (the -15 coal
under-run), and shrinks the over-export toward +32.7. The coal-sigmoid reference
stays on the ISO mean (no level shift), so the pjm-52 coal stack is undisturbed.

The full pjm-52 coal-bituminous 3-lever stack is kept verbatim below:

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
    out_dir = Path("results/calibration/pjm53_zonalgas")
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
        pjm_zonal_gas_basis=True,  # pjm-53 lever: open the west-cheap/east-dear spread
        reference_price_interface=True,
        priced_interchange=True,
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        note=(
            "pjm 53 zonal gas basis: pjm-52 coal-bit sticky stack base (verbatim) "
            "+ ONE structural lever, pjm_zonal_gas_basis. Shifts each PJM gas unit "
            "by its zone's measured EIA delivered-to-electric-power basis vs Henry "
            "Hub (data/raw/pjm_zonal_gas_hub.csv, N3045<ST>3M by primary state), "
            "capacity-weighted mean-zero anchored so the calibrated PJM aggregate "
            "gas level is preserved and ONLY the cross-zonal spread opens (west "
            "coal belt cheap: ComEd/AEP_Ohio/ATSI/West_APS/Central_PA; east dear: "
            "Dominion/SWMAAC/EMAAC). Opens the west→east flows so the "
            "Central_PA→EMAAC / SWMAAC→EMAAC TTCs bind: PJM stops clearing as a "
            "single copper-plate (0.000 zonal spread), eastern LMP separates up, "
            "eastern CC_REGULAR backs off the +54 TWh over-run, western coal runs "
            "to serve the east, and the +63 over-export shrinks toward +32.7. "
            "Measured, forward-reproducible, no residual tuning (C6-clean)."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
