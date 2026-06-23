"""pjm_44: PJM bituminous dispatchable WITH the gas-keyed sigmoid retained.

Tests the refinement of the pjm_43 probe: bituminous is made fully dispatchable
(``coal_bit_dispatchable=True`` zeros its per-plant CAMPD must-run floor, Pmin=0)
but its offer KEEPS the existing gas-keyed bituminous sigmoid
(``coal_bit_passthrough_floor`` left at the keeper's 0.76, ceil 1.32, mid 3.40)
instead of being flattened to full delivered cost (floor 1.0).

The distinction the pjm_43 run conflated: pjm_43 changed TWO things — zeroed the
must-run AND set floor 1.0 — and the floor 1.0 flattened the sigmoid to
full-cost, removing exactly the cheap-gas discount that holds bituminous in merit
when gas is cheap. This run isolates DISPATCHABILITY with the gas-tied offer
intact: when gas is cheap (below mid 3.40) bit discounts toward 0.76 and stays in
merit at its observed baseload level; when gas is dear it marks up toward 1.32
and backs down — the "buys coal on market terms, price-responsive to gas"
behaviour, now as a true marginal (can-back-down) unit rather than a forced
floor.

One year per invocation (PJM per-plant LP is GB-heavy); merge with
scripts/probes/_pjm_aswh_merge.py.

Usage: python scripts/probes/_pjm_coalbit_sigmoid_run.py <year> <out_dir>
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "pjm_28"


def main(year: int, out: Path) -> None:
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    meta = json.loads((KEEPER / "meta.json").read_text())
    cf["gas_monthly_actuals"] = meta["gas_monthly_actuals"]  # not in calib_flags
    out.mkdir(parents=True, exist_ok=True)

    bit_overrides = dict(cf["coal_bit_sigmoid_overrides"])  # keeps floor 0.76
    bit_overrides["coal_bit_dispatchable"] = True  # zero the bit must-run floor;
    #   the gas-keyed sigmoid (floor 0.76 -> ceil 1.32) is retained, NOT flattened

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
        bit_overrides=bit_overrides,
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
        note=f"pjm_44_coalbit_sigmoid_dispatchable: pjm_42_campdfix keeper + "
        f"coal_bit_dispatchable (bit per-plant must-run floor zeroed, Pmin=0) but "
        f"the gas-keyed bituminous sigmoid RETAINED (floor 0.76 -> ceil 1.32, mid "
        f"3.40), NOT flattened to full cost. Isolates dispatchability with the "
        f"gas-tied offer intact: cheap gas discounts bit to hold merit, dear gas "
        f"marks it up to back down, {year} only",
    )
    print(f"DONE {year} -> {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
