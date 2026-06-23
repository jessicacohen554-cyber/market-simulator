"""pjm_43: PJM bituminous = marginal/price-responsive swing fuel.

Clones the pjm_42_campdfix keeper (``_pjm_retiree_run.py`` recipe: pjm_28 config
+ ``retiree_cems_cap``) and turns OFF the PRB-style take-or-pay treatment for
BITUMINOUS coal only — two coupled, contract-physics changes, neither tuned to
the coal/LMP residual (claude.md #1/#11):

1. ``coal_bit_passthrough_floor`` 0.76 -> 1.0: the above-must-run bituminous
   tranches carry the FULL measured delivered cost (EIA-923 ~$3.03/MMBtu x
   physical HR ~10.5 => SRMC ~$32) instead of the 0.76 cheap-gas discount.
2. ``coal_bit_dispatchable`` = True: a bituminous-ranked plant's per-plant CAMPD
   must-run floor is ZEROED, so all of its capacity enters the rising offer
   curve (committed/econ/peak, Pmin=0) and is dispatched by price. PJM bit buys
   coal on spot/market terms (not mine-mouth take-or-pay), so it is the marginal
   swing fuel that backs down when gas is cheap — not held flat as discounted
   baseload. PRB / lignite / waste keep their take-or-pay must-run floors.

The bit must-run floors were already the CAMPD-observed P5-of-all-hours minimum
sustained level (Cardinal 60% / Kyger 48% / Gavin 48% / Amos 37%), so lowering
them would be anti-data; making bit fully dispatchable is the faithful
expression of "it backs down when uneconomic". A faithful model then holds bit
up only when it is economic — any under-run it shows is a price-formation signal
(PJM's suppressed afternoon LMP), not a coal-cost fault.

One year per invocation (PJM per-plant LP is GB-heavy); merge with
scripts/probes/_pjm_aswh_merge.py.

Usage: python scripts/probes/_pjm_coalbit_marginal_run.py <year> <out_dir>
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

    bit_overrides = dict(cf["coal_bit_sigmoid_overrides"])
    bit_overrides["coal_bit_passthrough_floor"] = 1.0  # full delivered-cost bid
    bit_overrides["coal_bit_dispatchable"] = True  # zero the bit must-run floor

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
        note=f"pjm_43_coalbit_marginal: pjm_42_campdfix keeper + bituminous made "
        f"marginal/price-responsive — coal_bit_passthrough_floor 0.76->1.0 (full "
        f"delivered-cost bid on above-must-run tranches) AND coal_bit_dispatchable "
        f"(bit per-plant CAMPD must-run floor zeroed; all capacity dispatchable, "
        f"Pmin=0). PRB/lignite/waste keep take-or-pay floors. Spot-coal contract "
        f"physics, not tuned to the coal/LMP residual, {year} only",
    )
    print(f"DONE {year} -> {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
