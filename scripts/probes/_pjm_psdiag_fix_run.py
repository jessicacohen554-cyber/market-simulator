"""pjm_47: PJM keeper (pjm_46 online-pmin) with the PS dispatch adder RETIRED.

Identical to scripts/probes/_pjm_online_pmin_run.py (the pjm_46 keeper: campdfix
+ coal_takeorpay_from_data + coal_mustrun_online_pmin) in every flag. The ONLY
difference is the structural fix landed in constants.py: the PJM pumped-storage
dispatch adder was retired from PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO (was $10,
now resolves to 0.0), so PJM PS arbitrages on its physical RTE 0.80 instead of
being suppressed by a knob that had been fitted to a mis-measured PS
*net*-generation figure (the round-trip loss read as gross discharge).

See docs/multi-iso/pjm-ps-cycling-diagnosis-2026-06.md. No per-run flag encodes
this — it is a code change to the per-ISO default — so the runner is the keeper
runner verbatim; the adder retirement flows from the edited constant.

One year per invocation (PJM per-plant LP is GB-heavy; this 15 GB box OOMs at 2
concurrent — run strictly serially). Merge with _pjm_aswh_merge.py.

Usage: python scripts/probes/_pjm_psdiag_fix_run.py <year> <out_dir>
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
        coal_takeorpay_from_data=True,  # keeper step 1
        coal_mustrun_online_pmin=True,  # keeper step 2
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
        note=f"pjm_47_psdiag: pjm_46 online-pmin keeper, PS DISPATCH ADDER RETIRED "
        f"(PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO PJM $10 -> {{}}; resolves to 0.0). "
        f"The $10 had been fitted to a mis-measured EIA-923 PS *net* figure "
        f"(round-trip loss ~2.6 TWh) read as gross discharge; true discharge "
        f"throughput is ~7-10 TWh (net*RTE/(1-RTE); PJM Hydro - conventional HY). "
        f"PS now arbitrages on physical RTE 0.80. All other flags = keeper. {year} only",
    )
    print(f"DONE {year} -> {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
