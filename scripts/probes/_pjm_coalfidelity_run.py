"""PJM coal data-fidelity run: pjm_39 (local-band) config, unchanged, re-solved
with the heat-input->MWh proxy for grossLoad-blank coal units and the coal-cogen
CHP/BTM holdout engaged (both PJM-gated code changes, no new flags).

Same recipe as the pjm_39 keeper (``results/calibration/pjm_39/run_config.json``
calibration_flags, read verbatim below), so the ONLY deltas vs pjm_39 are the
two code changes under test:

  1. campd.fill_heatinput_proxy -- grossLoad-blank CFB / waste-coal / coal-cogen
     units (Virginia City, Seward, the PA culm fleet, ...) get an hourly net-MW
     series reconstructed from measured heatInput at an EIA-923-anchored heat
     rate, so they are no longer invisible to the CAMPD net series.
  2. fleet.coal_chp_overrides routing -- coal bins at EIA-860 CHP-sector hosts
     (Eastman, St Nicholas, John B Rich, Covington, Pixelle) are held out at the
     sector behind-the-meter share and carry a measured steam-following grid
     floor (btm.parquet, the existing CHP machinery) instead of clearing as a
     cheap economic COAL_BIT/WC tranche. Merchant CFB / culm (chp=N, sector 1/2)
     stay economic.

Nothing is tuned to PJM's coal/net-MWh target (claude.md #11): the proxy heat
rate is the plant's own EIA-923 netgen / CAMPD heat, and the holdout share /
steam floor are the existing CHP_BTM_PCT_BY_SECTOR constant and the plant's own
EIA-923 class CF.

One year per invocation; merge with scripts/probes/_pjm_aswh_merge.py.

Usage: python scripts/probes/_pjm_coalfidelity_run.py <year> <out_dir>
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "pjm_39"


def main(year: int, out: Path) -> None:
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
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
        retiree_cems_cap=cf["retiree_cems_cap"],
        ct_mustrun_per_plant=cf["ct_mustrun_per_plant"],
        ct_mustrun_floor_frac=cf["ct_mustrun_floor_frac"],
        coal_drop_pof=cf["coal_drop_pof"],
        coal_prb_passthrough_tiered=cf["coal_prb_passthrough_tiered"],
        prb_overrides=cf["coal_prb_sigmoid_overrides"],
        coal_bit_sigmoid=cf["coal_bit_passthrough_sigmoid"],
        bit_overrides=cf["coal_bit_sigmoid_overrides"],
        gas_monthly_actuals=True,
        offer_curve_overrides=cf["offer_curve_overrides"],
        offer_curve_deltas=cf["offer_curve_deltas"],
        curve_smoothing={
            "offer_curve_smoothing_n": None,
            "offer_curve_smoothing_exp": None,
            "offer_curve_smoothing_mid": 0.45,
        },
        priced_interchange=cf["priced_interchange"],
        reference_price_interface=True,
        as_reserve_withholding=False,
        note=f"pjm_40_coalfidelity: pjm_39 local-band config (verbatim) + the "
        f"heat-input->MWh proxy for grossLoad-blank coal + the coal-cogen "
        f"CHP/BTM holdout (Eastman/St Nicholas/John B Rich/...). Measured-"
        f"anchored, no new flags; {year} only",
    )
    print(f"DONE {year} -> {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
