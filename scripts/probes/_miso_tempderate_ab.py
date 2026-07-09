"""Full-keeper A/B probe: MISO 48 (stgas-srmc) keeper config vs the same
recipe with ``temp_dependent_derate=True``, all three train years
(2023-2025) in one bundle, per
``docs/handoffs/temp-derate-keeper-rerun-playbook-2026-07.md``.

Reproduces the miso_48_stgas_srmc keeper's exact recorded config (its own
``meta.json`` -- the exhaustive flat kwarg record; ``run_config.json``'s
``calibration_flags`` is a curated subset that is missing several MISO
structural flags this keeper turns on, e.g. ``miso_zonal_reserves``,
``miso_seam_measured_ladder``, ``st_gas_intermediate``, ``coal_econ_srmc_bound``)
and flips only ``temp_dependent_derate`` -- the flat EIA-860 net-summer/
``_SUMMER_CLASS_DERATE`` capacity treatment vs the per-class dry-bulb
temperature curve (``fleet.generators_to_fleet_arrays``). Kwargs are mapped
from ``meta.json`` programmatically and checked against
``solve_and_persist``'s own signature so no flag is silently dropped.

Also solves the rule-20 zero-forcing ablation twin (``mode=ablation``):
same config, ``zero_forcing_ablation=True``.

Usage: python scripts/probes/_miso_tempderate_ab.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "MISO" / "miso_48_stgas_srmc"
OUT_NAME = "miso49_tempderate"

# meta.json keys that use a different name than the solve_and_persist kwarg.
RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# recorded for provenance only / not a solve_and_persist kwarg / handled
# explicitly below.
SKIP = {
    "iso",
    "years",
    "hours",
    "git_sha",
    "timestamp",
    "passes",
    "gas_prices",
    "coal_plant_monthly_pricing",
    "td_loss_factor",
    "highspy_version",
    "shared_inputs",
    "commitment",
    "commitment_screen_coal",
}


def main(mode: str) -> None:
    meta = json.loads((KEEPER / "meta.json").read_text())
    ablate = mode == "ablation"
    out = ROOT / (OUT_NAME + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    sig = inspect.signature(solve_and_persist).parameters
    kwargs = {}
    unmapped = []
    for k, v in meta.items():
        if k in SKIP:
            continue
        mapped = RENAME.get(k, k)
        if mapped in sig:
            kwargs[mapped] = v
        else:
            unmapped.append(k)
    if unmapped:
        print(f"NOTE: meta.json keys not bound to solve_and_persist: {unmapped}")

    solve_and_persist(
        meta["years"],  # all three train years in one bundle (rule 16)
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        screen_coal=meta["commitment_screen_coal"],
        run_dir=out,
        **kwargs,
        temp_dependent_derate=True,
        zero_forcing_ablation=ablate,
        ablation_of=(OUT_NAME if ablate else None),
        note=(
            f"temp-derate full-keeper {mode} -- miso-48-stgas-srmc config + "
            "temp_dependent_derate, 2023-2025 (docs/handoffs/"
            "temp-derate-keeper-rerun-playbook-2026-07.md)"
        ),
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
