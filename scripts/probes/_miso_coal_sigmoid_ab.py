"""MISO miso-50 probe: re-solve the miso-49 keeper recipe with the coal-vs-gas
passthrough sigmoid RE-DERIVED from #1803 coal-commodity price data.

This reproduces the ``2026-07-08-miso-49-tempderate`` keeper's exact
``calibration_flags`` (read from its run_config.json) for all three years
2023-2025 in one bundle (rule 16). NOTHING in the flags changes — the only
difference from miso-49 is the code change to ``COAL_SIGMOID_DEFAULTS[("MISO",
…)]`` in config/scenarios.py, re-derived by scripts/derive_coal_sigmoid.py from
the EIA Annual Coal Report region f.o.b. + BLS PPI series intaked in #1803
(rule-23 source-data trigger). The MISO passthrough fields in the keeper config
are all None, so the solve resolves the (now re-derived) region-grounded MISO
sigmoid automatically.

Registered as a PROBE at miso-50 (main) + its rule-20 zero-forcing ablation
twin — NOT promoted to keeper (owner decision after reviewing before/after
deltas). Do not edit keepers.json.

Usage:
    python scripts/probes/_miso_coal_sigmoid_ab.py main
    python scripts/probes/_miso_coal_sigmoid_ab.py ablation   # after main exists
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
# positional/identity args, and the keys backcast_config resolves internally
# (P1-only passes; per-year gas prices; coal_plant_monthly_pricing default
# True; td_loss_factor default 0.0) — exactly as they were when miso-49 itself
# was produced by this same entry point.
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
    out = ROOT / ("miso50_coalsigmoid" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    kwargs = {}
    for k, v in cf.items():
        if k in _DROP:
            continue
        kwargs[_RENAME.get(k, k)] = v

    solve_and_persist(
        cf["years"],  # 2023 2024 2025 — one bundle (rule 16)
        cf["iso"],
        cf["hours"],
        _load_reference(),
        run_dir=out,
        zero_forcing_ablation=ablate,
        ablation_of=(out.parent / "miso50_coalsigmoid").name if ablate else None,
        note=(
            f"miso-50 coal-sigmoid re-derive ({mode}) — miso-49 keeper config, "
            "COAL_SIGMOID_DEFAULTS[MISO] re-derived from #1803 region f.o.b./PPI "
            "(scripts/derive_coal_sigmoid.py), 2023-2025"
        ),
        **kwargs,
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
