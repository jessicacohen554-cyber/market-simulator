"""pjm_45: PJM keeper recipe + MEASURED take-or-pay (coal_takeorpay_from_data).

Isolates rebuild step 1: the coal must-run tranche's sunk fraction becomes the
measured EIA-923 Schedule-5 take-or-pay (contract) share per plant
(``coal_takeorpay_<ISO>.csv`` → ``campd_tranche_fuel_frac`` returns
``1 - contract_share`` for ``_mustrun`` coal) instead of the hardcoded 100%-sunk
(``0.0``). Everything else is the pjm_42_campdfix keeper, unchanged — the
gas-keyed bituminous sigmoid, the per-plant CAMPD must-run floors, the retiree
CEMS cap. So the only difference vs the keeper is that the contracted base bids
``heat_rate × fuel × (1 - share)`` of its fuel and the spot remainder bids full
delivered cost (e.g. Miami Fort 2832 share 0% → its must-run bids full fuel;
Gavin/Harrison 100% → unchanged from the keeper's fuel-free floor).

This is the physically-honest, forward-reproducible version of the calibrated
sub-cost must-run (CLAUDE.md #11). It is rebuild STEP 1 only — the floor
re-sizing to the CEMS online-Pmin (step 2) and the SRMC-bid synchronization layer
(step 3) + reserve co-opt (price formation) are NOT in this run; see
docs/multi-iso/pjm-coal-operations-firstprinciples-2026-06.md. Expect a modest
effect (PJM is still ~86% contracted tons-weighted), measured here as the step-1
baseline for the fuller rebuild.

One year per invocation (PJM per-plant LP is GB-heavy); merge with
scripts/probes/_pjm_aswh_merge.py.

Usage: python scripts/probes/_pjm_takeorpay_run.py <year> <out_dir>
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
        coal_takeorpay_from_data=True,  # the probe lever: measured Sch-5
        #   take-or-pay share sizes the coal must-run sunk fraction
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
        note=f"pjm_45_takeorpay: pjm_42_campdfix keeper + coal_takeorpay_from_data "
        f"(coal must-run sunk fraction = measured EIA-923 Sch-5 contract share "
        f"per plant, 1 - share passed through, vs the hardcoded 100%-sunk). "
        f"Everything else unchanged. Rebuild step 1 only, {year} only",
    )
    print(f"DONE {year} -> {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
