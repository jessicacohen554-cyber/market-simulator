"""pjm_47: PJM keeper + take-or-pay (step 1) + online-Pmin (step 2) + SRMC
synchronization tranche (step 3a).

Cumulative rebuild step 3a stacked on steps 1-2. Step 3a
(``coal_sync_srmc_tranche``) completes the three-layer coal structure of
Thread D: the coal min-load band (sized to the measured online-net-MW Pmin by
step 2) is split by the measured EIA-923 Sch-5 contract share into

  1. ``_mustrun`` — the contracted (take-or-pay, sunk) share, fuel-free
     (VOM + carbon + NOx), and
  2. ``_sync`` — the spot (avoidable-fuel) remainder, priced at its REAL SRMC
     (full delivered fuel + VOM + reagents),

and BOTH are forced on (synchronized) via FleetArrays.min_gen. So coal HOLDS
volume at min-load (fixing the step-2 residual: 2024 coal under / units backing
down too far in cheap-gas hours) while the full-delivered-cost dispatchable
tranches above still price-follow (CEMS low/hi ~0.63), and the forced band bids
SRMC rather than fuel-free so it does not re-suppress the LMP coal sets when
marginal. Steps 1+2 stay on (the contract share now SIZES the fuel-free vs SRMC
split; the online Pmin sizes the forced band). Everything else is the
pjm_42_campdfix keeper, unchanged.

This is rebuild STEP 3a (cumulative steps 1-3a). The energy+reserve
co-optimization (step 3b / the afternoon $75-200 price) is NOT in this run — it
remains memory-blocked at PJM plant scale (per-gen R[g] reserve columns OOM the
15 GB box); see docs/multi-iso/pjm-reserve-ordc.md (Phase 2) and Thread D.

One year per invocation (PJM per-plant LP is GB-heavy); merge with
scripts/probes/_pjm_aswh_merge.py.

Usage: python scripts/probes/_pjm_sync_srmc_run.py <year> <out_dir>
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "pjm_28"


def main(year: int, out: Path) -> None:
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    meta = json.loads((KEEPER / "meta.json").read_text())
    cf["gas_monthly_actuals"] = meta["gas_monthly_actuals"]  # not in calib_flags
    out.mkdir(parents=True, exist_ok=True)

    solve_and_persist(
        [year],
        "PJM",
        8760,
        _load_reference(),
        commitment=cf["commitment"],
        screen_coal=cf["commitment_screen_coal"],
        run_dir=out,
        coal_lignite_mustrun=cf["coal_lignite_mustrun"],
        coal_prb_mustrun=cf["coal_prb_mustrun"],
        coal_prb_passthrough=cf["coal_prb_passthrough"],
        outage_source=cf["outage_source"],
        coal_prb_passthrough_sigmoid=cf["coal_prb_passthrough_sigmoid"],
        coal_mustrun_per_plant=cf["coal_mustrun_per_plant"],
        retiree_cems_cap=True,
        coal_drop_pof=cf["coal_drop_pof"],
        coal_prb_passthrough_tiered=cf["coal_prb_passthrough_tiered"],
        prb_overrides=cf["coal_prb_sigmoid_overrides"],
        coal_bit_sigmoid=cf["coal_bit_passthrough_sigmoid"],
        bit_overrides=cf["coal_bit_sigmoid_overrides"],
        coal_takeorpay_from_data=True,  # step 1: measured Sch-5 sunk fraction
        coal_mustrun_online_pmin=True,  # step 2: online-Pmin must-run band size
        coal_sync_srmc_tranche=True,  # step 3a: forced SRMC synchronization band
        gas_monthly_actuals=cf["gas_monthly_actuals"],
        offer_curve_overrides=cf["offer_curve_overrides"],
        offer_curve_deltas=cf["offer_curve_deltas"],
        curve_smoothing={
            "offer_curve_smoothing_n": None,
            "offer_curve_smoothing_exp": None,
            "offer_curve_smoothing_mid": 0.45,
        },
        priced_interchange=True,
        reference_price_interface=True,
        as_reserve_withholding=cf.get("as_reserve_withholding", False),
        note=f"pjm_47_sync_srmc: pjm_42_campdfix keeper + coal_takeorpay_from_data "
        f"(step 1) + coal_mustrun_online_pmin (step 2) + coal_sync_srmc_tranche "
        f"(step 3a: split the online-Pmin coal min-load band by the measured "
        f"contract share into a fuel-free _mustrun floor + a full-SRMC _sync band, "
        f"both forced on/synchronized via min_gen, so coal holds volume at min-load "
        f"while dispatchable tranches above price-follow). Everything else "
        f"unchanged. Rebuild steps 1-3a, {year} only",
    )
    print(f"DONE {year} -> {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
