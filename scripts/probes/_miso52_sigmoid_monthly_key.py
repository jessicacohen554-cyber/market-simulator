"""MISO miso-52: the miso-51 recipe with the coal sigmoid's gas key held at
the MONTHLY level (contract-repricing timescale) while gas units bid daily.

Identical kwargs to miso-51 (the miso-49 keeper flags + hydro 2024-backfill /
EIA-930 monthly repin, on the re-derived measured coal sigmoid at HEAD, with
gas_daily_shape[MISO] on). The ONLY difference is the code change in
``fuel._gas_series``: the coal passthrough sigmoid no longer takes the
within-month daily Henry Hub swing — a coal fuel contract's discount posture
(take-or-pay / mine-mouth / rail) reprices monthly, not on daily spot.

miso-51 evidence for this timescale correction (zero new parameters, one
mechanism per timescale): keying the sigmoid daily made coal offers whipsaw
in lockstep with every HH trough, so (a) the coal-vs-gas flip days the daily
shape exists to resolve never opened (COAL_PRB stayed +30/+25/+27 TWh), and
(b) the whipsaw itself FAILed C4 2024 coal dispatch-corr (r=0.856) and C3b
2023/24 monthly shape (0.277/0.289) — real coal dispatch is
contract/inflexibility-smoothed.

Usage:
    python scripts/probes/_miso52_sigmoid_monthly_key.py main
    python scripts/probes/_miso52_sigmoid_monthly_key.py ablation   # after main
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso49_tempderate"

_RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
_DROP = {
    "iso",
    "years",
    "hours",
    "git_sha",
    "passes",
    "gas_prices",
    "coal_plant_monthly_pricing",
    "td_loss_factor",
}


def main(mode: str) -> None:
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    ablate = mode == "ablation"
    out = ROOT / ("miso52_sigmoid_monthly_key" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    kwargs = {}
    for k, v in cf.items():
        if k in _DROP:
            continue
        kwargs[_RENAME.get(k, k)] = v

    kwargs["hydro_backfill_year"] = 2024
    kwargs["hydro_eia930_monthly"] = True

    solve_and_persist(
        cf["years"],  # 2023 2024 2025 — one bundle (rule 16)
        cf["iso"],
        cf["hours"],
        _load_reference(),
        run_dir=out,
        zero_forcing_ablation=ablate,
        ablation_of=(out.parent / "miso52_sigmoid_monthly_key").name
        if ablate
        else None,
        note=(
            f"miso-52 sigmoid monthly gas key ({mode}) — the miso-51 recipe "
            "(gas_daily_shape[MISO] + hydro completeness on the measured coal "
            "sigmoid) with the coal sigmoid's gas key held at the monthly "
            "contract-repricing level (fuel._gas_series), 2023-2025"
        ),
        **kwargs,
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
