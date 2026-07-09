"""MISO miso-51: re-solve the miso-49 keeper recipe with the gas-side daily
granularity + 2025 hydro completeness fixes the miso-50 probe indicted.

This reproduces the ``2026-07-08-miso-49-tempderate`` keeper's exact
``calibration_flags`` (read from its run_config.json) for all three years
2023-2025 in one bundle (rule 16), on top of the re-derived measured MISO coal
sigmoid already at HEAD (the miso-50 surface — kept per rule 11). Three
deliberate changes, all measured inputs, zero fitted parameters:

1. ``gas_daily_shape`` now includes MISO (backcast_config): the measured daily
   Henry Hub within-month swing rides mean-preserving on the per-plant
   EIA-923 monthly gas level, resolving the coal-vs-gas flip days the
   miso-50 handoff isolated as the substitution root cause
   (docs/handoffs/coal-sigmoid-rederive-2026-07.md).
2. ``apply_plant_monthly_fuel_prices`` re-carries those factors onto
   overwritten gas plant-months (the flat overwrite used to erase them).
3. ``--hydro-backfill-year 2024 --hydro-eia930-monthly`` (the PJM/NEISO
   keeper pattern): the 2025 EIA-923 early release carries 14 of 160 MISO
   hydro plants (0.97 of ~9.9 TWh) — the missing zero-MC inflow was being
   served by coal.

Usage:
    python scripts/probes/_miso51_gasdaily_hydro.py main
    python scripts/probes/_miso51_gasdaily_hydro.py ablation   # after main
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso49_tempderate"

# calibration_flags key -> solve_and_persist kwarg name (the 4 non-identity
# renames). Every other mappable key passes through under its own name.
_RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# calibration_flags keys that solve_and_persist does NOT take as a kwarg: the
# positional/identity args, and the keys backcast_config resolves internally.
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
    out = ROOT / ("miso51_gasdaily_hydro" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    kwargs = {}
    for k, v in cf.items():
        if k in _DROP:
            continue
        kwargs[_RENAME.get(k, k)] = v

    # The two explicit input-completeness deltas vs the miso-49 recipe (the
    # gas_daily_shape delta is code-resolved in backcast_config and shows in
    # the recorded scenario_config).
    kwargs["hydro_backfill_year"] = 2024
    kwargs["hydro_eia930_monthly"] = True

    solve_and_persist(
        cf["years"],  # 2023 2024 2025 — one bundle (rule 16)
        cf["iso"],
        cf["hours"],
        _load_reference(),
        run_dir=out,
        zero_forcing_ablation=ablate,
        ablation_of=(out.parent / "miso51_gasdaily_hydro").name if ablate else None,
        note=(
            f"miso-51 gas-daily + hydro completeness ({mode}) — miso-49 keeper "
            "config on the re-derived measured coal sigmoid (miso-50 surface), "
            "+ gas_daily_shape[MISO] (measured HH daily swing over F923 "
            "plant-month gas) + hydro 2024-backfill/EIA-930 monthly repin "
            "(2025 early-release gap), 2023-2025"
        ),
        **kwargs,
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
