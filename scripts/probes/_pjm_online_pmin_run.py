"""pjm_46: PJM keeper + take-or-pay (step 1) + online-Pmin coal floor (step 2).

Isolates rebuild STEP 2 stacked on step 1. Step 2
(``coal_mustrun_online_pmin``) re-sizes the coal must-run tranche from the
all-hours available-CF P5 (``thermal_tranches_PJM.csv`` ``mustrun_pct``, which
reads ~2x high for an always-online unit) to the measured online-net-MW
synchronization Pmin (``mustrun_online_pct``, ~20-30% of nameplate). In the
energy-only LP that band has Pmin=0, so it is not a forced floor but the SIZE
of the cheap (sunk-fuel) bid band: shrinking it moves coal capacity into the
full-delivered-cost rising tranches, so coal price-follows (backs down in cheap
hours) instead of baseloading the whole fleet under gas — the CEMS-observed
low/hi-price CF ratio of ~0.63 the keeper's flat 0.60 floor cannot produce.

Step 1 (``coal_takeorpay_from_data``) stays on, so the smaller cheap band still
bids ``1 - contract_share`` of its fuel (measured EIA-923 Sch-5 take-or-pay)
rather than the hardcoded 100%-sunk. Everything else is the pjm_42_campdfix
keeper, unchanged. So the only differences vs the keeper are the two grounded,
forward-reproducible coal layers (CLAUDE.md #11), not a coal-MWh residual tune.

This is rebuild STEP 2 (cumulative through step 2). The SRMC-bid synchronization
layer + reserve co-optimization (step 3 / price formation) are NOT in this run;
see docs/multi-iso/pjm-coal-operations-firstprinciples-2026-06.md (Thread D).

NOTE: requires ``thermal_tranches_PJM.csv`` to carry the ``mustrun_online_pct``
column (re-derive with the updated scripts/data/derive_thermal_tranches.py); coal
plants in an artifact predating the column keep ``mustrun_pct`` (no-op).

One year per invocation (PJM per-plant LP is GB-heavy); merge with
scripts/probes/_pjm_aswh_merge.py.

Usage: python scripts/probes/_pjm_online_pmin_run.py <year> <out_dir>
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
        note=f"pjm_46_online_pmin: pjm_42_campdfix keeper + coal_takeorpay_from_data "
        f"(step 1) + coal_mustrun_online_pmin (step 2: coal must-run band sized to "
        f"the measured online-net-MW synchronization Pmin / mustrun_online_pct, vs "
        f"the all-hours available-CF mustrun_pct). Everything else unchanged. "
        f"Rebuild steps 1-2, {year} only",
    )
    print(f"DONE {year} -> {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
