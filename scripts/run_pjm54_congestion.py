"""Driver: PJM 54 — transmission congestion (break the copper-plate), 2023-2025.

Continuation of the pjm-53 zonal-gas keeper stack (verbatim — the FULL keeper
lever stack is preserved below), adding ONE structural lever family: a measured
PJM transmission-congestion model (``pjm_congestion``).

THE DIAGNOSIS (from the pjm-53 zonal decomposition): even with the measured
zonal gas basis open, PJM STILL clears as a perfect copper-plate — zonal LMP
spread is EXACTLY 0.000 in all 8760 hours of all three years. Root cause is the
reduced NETWORK never congests, for two reasons:

  1. THE EXTERNAL STAR NODE (the dominant equalizer). The priced PJM_external
     node (IMPORT_ZONE['PJM']) is a SINGLE price hub wired to 5 of 8 zones with
     ~30 GW of UNCONGESTED transfer (IMPORT_NODE_LINKS: ComEd 7500, AEP_Ohio
     4900, ATSI 5800, Dominion 6300, EMAAC 5700). Because EMAAC and Dominion (the
     dear-east load pockets) import directly from this hub, they never pull power
     through the internal west→east lines, so those lines never bind and every
     zone's energy-balance dual ties to one price.
  2. LOOSE INTERNAL TTCs. The _pjm_config interface limits are Tier-3
     order-of-magnitude estimates too loose to bind.

THE LEVER (the structural fix, rule #1 — this is the missing structure, not a
fit), ``pjm_congestion``, calibrated to MEASURED PJM transfer/interchange data
(data/raw/iso-specific-transmission/, rules #11/#12 — never tuned to the
price/export residual):

  Lever A (the dominant fix — tackle the external node FIRST) — cap each
    PJM_external→border link's signed flow, per (month × hour-of-day), at the
    measured per-border net-interchange envelope (p95;
    eia_loader.pjm_zonal_interchange_envelope from the PJM tie-flow file). The
    dominant tie direction (ComEd/AEP/EMAAC export, Dominion import) keeps a
    generous ceiling the LP clears below; the minor direction collapses toward
    ~0 (EMAAC import / Dominion export / the interior zones have no tie). The hub
    can no longer flood the east with cheap imports, so the interior dear-east
    zones must source western power across the internal interfaces — opening the
    congestion the copper-plate suppressed — and the +49-61 over-export shrinks
    toward the measured +33-40 schedule. Asymmetric per-hour interface groups
    (same machinery as the CAISO per-hub corridor caps).

  Lever B — tighten the internal interfaces with a confident named mapping to
    their measured PJM transfer-limit postings
    (constants.PJM_MEASURED_INTERNAL_TTC, pooled 2023-25 median): ComEd→AEP_Ohio
    6000→2900 (50045005), AEP_Ohio→Dominion 4069→4050 (AEP/DOM), West_APS→SWMAAC
    4453→3900 (AP-South, the dominant west→east cut), West_APS→Central_PA
    1947→1850 (Bedington-BlackOak). The rest keep their config estimate (already
    ≈ measured). With the upstream cuts binding, the interior zones cannot pull
    unlimited western coal east, so the eastern LMP separates UP.

Expectation: PJM stops clearing as a single copper-plate (>0 zonal spread in a
material share of hours), east (EMAAC/SWMAAC/Dominion) LMP > west (coal belt),
load-weighted LMP rises toward actual (C3a), and net export shrinks toward
measured. Validate with scripts/probes/_pjm53_zonal_decomp.py on the new bundle.

The full pjm-53 keeper stack is kept verbatim below (pjm-48 coal keeper +
pjm-49 MISO/NYISO HR anchors + pjm-50 firm-export floor / losses hurdle /
TVA-LGEE + pjm-51 Southeast gas-inelastic reference price + pjm-52 coal-bit
3-lever sticky-online stack + pjm-53 pjm_zonal_gas_basis). Years are solved
sequentially in one process (a PJM per-plant year peaks ~13 GB in HiGHS; one at
a time stays under the box's 15 GB).
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

# pjm-53 base recipe (results/calibration/pjm53_zonalgas/run_config.json),
# verbatim — the keeper base. The congestion lever is new this run.
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
# pjm-52 Lever 3: deepen the bituminous cheap-gas BID discount (floor 0.76→0.68).
BIT_OVERRIDES = {"coal_bit_passthrough_floor": 0.68}


def main() -> int:
    out_dir = Path("results/calibration/pjm54_congestion")
    reference = _load_reference()
    run_dir = solve_and_persist(
        [2023, 2024, 2025],
        "PJM",
        8760,
        reference,
        commitment=False,
        screen_coal=True,  # commitment_screen_coal -> pjm-52 Lever 2 (coal 36/16)
        run_dir=out_dir,
        outage_source="historic",
        coal_prb_passthrough=1.0,
        coal_prb_passthrough_sigmoid=True,
        coal_mustrun_per_plant=True,
        retiree_cems_cap=True,
        coal_drop_pof=True,
        coal_prb_passthrough_tiered=True,
        prb_overrides=PRB_OVERRIDES,
        coal_bit_sigmoid=True,  # pjm-52 Lever 3
        bit_overrides=BIT_OVERRIDES,
        coal_mustrun_online_pmin=True,  # pjm-52 Lever 1
        coal_sync_srmc_tranche=True,  # pjm-52 Lever 1
        gas_monthly_actuals=True,
        pjm_zonal_gas_basis=True,  # pjm-53 lever (kept)
        pjm_congestion=True,  # pjm-54 lever: break the copper-plate
        reference_price_interface=True,
        priced_interchange=True,
        offer_curve_overrides=OFFER_CURVE_OVERRIDES,
        note=(
            "pjm 54 transmission congestion: pjm-53 zonal-gas keeper stack "
            "(verbatim) + ONE structural lever family, pjm_congestion. (A) caps "
            "each PJM_external->border link's signed flow per (month x hod) at "
            "the MEASURED per-border net-interchange envelope (p95, "
            "eia_loader.pjm_zonal_interchange_envelope from the PJM tie-flow "
            "file) — the priced external star node can no longer wheel ~30 GW "
            "uncongested into the 5 border zones, so the dear-east pockets "
            "(EMAAC/SWMAAC/Dominion) must source western power across the "
            "internal lines instead of importing from one price hub. (B) tightens "
            "the internal interfaces with a confident named mapping to their "
            "MEASURED PJM transfer-limit postings (PJM_MEASURED_INTERNAL_TTC: "
            "ComEd->AEP 6000->2900, AEP->DOM 4069->4050, AP-South 4453->3900, "
            "Bedington-BlackOak 1947->1850). PJM stops clearing as a single "
            "copper-plate (0.000 zonal spread): eastern LMP separates up, western "
            "coal runs to serve the east, load-weighted LMP rises toward actual, "
            "and the +49-61 over-export shrinks toward the measured +33-40. "
            "Measured PJM transfer/interchange data, forward-reproducible, no "
            "residual tuning (C6-clean)."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
