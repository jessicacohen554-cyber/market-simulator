"""PJM energy+reserve co-optimization run: one year -> its own bundle dir.

Reproduces the pjm_28 keeper's exact calibration_flags but swaps the
reduced-form reserve *withholding* (``as_reserve_withholding``) for the in-LP
energy+reserve *co-optimization* (``energy_reserve_coopt``): the structural
1.5x-MSSC Primary Reserve requirement + the published ORDC demand curve clear
inside the LP, so the reserve clearing price emerges as a dual and lifts the
energy LMP endogenously (it also replaces the post-solve ORDC overlay). The two
reserve mechanisms are mutually exclusive (running both double-counts), so
withholding is turned off here.

One year per invocation so the three years run as parallel background jobs to
separate out-dirs (claude.md #45); merge with scripts/_pjm_aswh_merge.py.

Usage: python scripts/_pjm_coopt_run.py <year> <out_dir>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[1] / "results" / "calibration"
KEEPER = ROOT / "pjm_28"


def main(year: int, out: Path) -> None:
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    meta = json.loads((KEEPER / "meta.json").read_text())
    cf["gas_monthly_actuals"] = meta["gas_monthly_actuals"]  # not in calib_flags
    out.mkdir(parents=True, exist_ok=True)

    solve_and_persist(
        [year], "PJM", 8760, _load_reference(),
        commitment=cf["commitment"],
        screen_coal=cf["commitment_screen_coal"],
        run_dir=out,
        coal_lignite_mustrun=cf["coal_lignite_mustrun"],
        coal_prb_mustrun=cf["coal_prb_mustrun"],
        coal_prb_passthrough=cf["coal_prb_passthrough"],
        outage_source=cf["outage_source"],
        coal_prb_passthrough_sigmoid=cf["coal_prb_passthrough_sigmoid"],
        coal_mustrun_per_plant=cf["coal_mustrun_per_plant"],
        coal_drop_pof=cf["coal_drop_pof"],
        coal_prb_passthrough_tiered=cf["coal_prb_passthrough_tiered"],
        prb_overrides=cf["coal_prb_sigmoid_overrides"],
        coal_bit_sigmoid=cf["coal_bit_passthrough_sigmoid"],
        bit_overrides=cf["coal_bit_sigmoid_overrides"],
        gas_monthly_actuals=cf["gas_monthly_actuals"],
        offer_curve_overrides=cf["offer_curve_overrides"],
        offer_curve_deltas=cf["offer_curve_deltas"],
        curve_smoothing={"offer_curve_smoothing_n": None,
                         "offer_curve_smoothing_exp": None,
                         "offer_curve_smoothing_mid": 0.45},
        priced_interchange=cf["priced_interchange"],
        as_reserve_withholding=False,   # replaced by in-LP co-optimization
        energy_reserve_coopt=True,
        note=f"pjm_29_coopt: keeper pjm_28 config + in-LP energy+reserve "
             f"co-optimization (replaces withholding + ORDC overlay), "
             f"{year} only",
    )
    print(f"DONE {year} -> {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
