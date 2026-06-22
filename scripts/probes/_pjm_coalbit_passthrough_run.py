"""Probe #2: PJM marginal-coal-offer lever, measured-anchored.

Clones the pjm_38 keeper runner (``_pjm_retiree_run.py``, retiree_cems_cap=True)
and changes ONLY the COAL_BIT fuel-passthrough floor 0.76 -> 1.0, so the
above-must-run coal tranches (committed / econ / peak) carry the FULL measured
delivered bituminous cost (EIA-923 ~$3.03/MMBtu in 2024) x heat rate instead of
the 0.76 discount. The must-run base tranche is untouched (take-or-pay
preserved). The anchor is the measured delivered fuel cost — NOT the coal-MWh or
LMP residual (claude.md #11): floor=1.0 means "the incremental coal bids its full
delivered variable cost", a physically-pinned value, not a number tuned to the
target.

This empirically gates probe #0's prediction that the coal lever is structurally
BOUNDED (coal is the sole price-setter in only ~5-9% of zone-hours; the over is
~92% take-or-pay base; the over-run is export-driven). One year per invocation.

Usage: python scripts/probes/_pjm_coalbit_passthrough_run.py <year> <out_dir>
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
    cf["gas_monthly_actuals"] = meta["gas_monthly_actuals"]
    out.mkdir(parents=True, exist_ok=True)

    bit_overrides = dict(cf["coal_bit_sigmoid_overrides"])
    bit_overrides["coal_bit_passthrough_floor"] = 1.0  # the probe lever: full
    #   measured delivered-cost passthrough on the above-must-run coal tranches

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
        note=f"probe #2: pjm_38 keeper + COAL_BIT passthrough floor 0.76->1.0 "
        f"(full measured delivered-cost passthrough on above-must-run coal "
        f"tranches; base take-or-pay preserved), {year} only",
    )
    print(f"DONE {year} -> {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
