"""PJM energy+reserve co-optimization run: one year -> its own bundle dir.

Reproduces the pjm_38 keeper recipe (``_pjm_retiree_run.py``: pjm_28 config +
reference-price interchange seam + within-window retiree CEMS cap) and adds the
in-LP energy+reserve *co-optimization* (``energy_reserve_coopt=True``): the
measured PJM_RTO Primary Reserve requirement (~3.4 GW) clears against the
published vertical two-step ORDC (Primary/RTO, $850/$300/+190 MW) inside the LP,
so the reserve clearing price emerges as the reserve-balance dual and lifts the
energy LMP endogenously (PJM RT = LMP + reserve price). Withholding is its
pre-condition (it removes the must-hold reserve MW from the energy stack), so
``as_reserve_withholding=True`` is set too; the post-solve ORDC overlay is
mutually exclusive and not used here.

Nothing is fitted to the LMP residual (claude.md #11): the requirement is the
measured reliability quantity and the curve is the cited market design.

One year per invocation so the three years run as parallel/serial background
jobs to separate out-dirs (claude.md #45); merge with
scripts/probes/_pjm_aswh_merge.py.

Usage: python scripts/probes/_pjm_coopt_run.py <year> <out_dir>
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
        retiree_cems_cap=True,  # pjm_38 keeper lever (measured-availability cap)
        coal_drop_pof=cf["coal_drop_pof"],
        coal_prb_passthrough_tiered=cf["coal_prb_passthrough_tiered"],
        prb_overrides=cf["coal_prb_sigmoid_overrides"],
        coal_bit_sigmoid=cf["coal_bit_passthrough_sigmoid"],
        bit_overrides=cf["coal_bit_sigmoid_overrides"],
        gas_monthly_actuals=cf["gas_monthly_actuals"],
        offer_curve_overrides=cf["offer_curve_overrides"],
        offer_curve_deltas=cf["offer_curve_deltas"],
        curve_smoothing={
            "offer_curve_smoothing_n": None,
            "offer_curve_smoothing_exp": None,
            "offer_curve_smoothing_mid": 0.45,
        },
        priced_interchange=True,  # implied by the reference seam
        reference_price_interface=True,
        as_reserve_withholding=True,  # co-opt pre-condition (must-hold MW off energy)
        energy_reserve_coopt=True,  # the probe lever: in-LP energy+reserve co-opt
        note=f"pjm_39_coopt: pjm_38 keeper recipe + in-LP energy+reserve "
        f"co-optimization (measured PJM_RTO Primary requirement + published "
        f"two-step ORDC clear inside the LP; replaces the post-solve overlay, "
        f"withholding on as pre-condition), {year} only",
    )
    print(f"DONE {year} -> {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
