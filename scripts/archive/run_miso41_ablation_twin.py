"""Driver: D-3 zero-forcing ablation twin of the miso-41 keeper (CLAUDE.md rule 20).

The ``miso-41-ct-evening`` keeper (bundle
``results/calibration/MISO/miso_41_ct_evening_window``) has no dedicated recipe
script — it was produced by a ``run_calibration_full.solve_and_persist``
invocation. Its ``meta.json`` is the faithful, committed record of the exact
arguments that call received (the meta dict is built directly from the
parameter variables; see ``run_calibration_full`` ~line 2360). So the most
faithful "keeper VERBATIM" twin replays those same arguments, adding only
``zero_forcing_ablation=True``: every merchant floor/bridge/drag neutralized via
``ScenarioConfig.as_zero_forcing_ablation`` (off-list derived from the D-2
mechanism registry), keeping the structural protected set (nuclear must-run,
CHP steam, coal take-or-pay). No parameter differs from the keeper config — the
transform is applied inside ``run_year``/``solve_and_persist``.

The MISO-specific configuration the keeper relies on (the post-deleak default
offer curve, ``reliability_floor`` with the CT_PEAKER evening window [15,21)
baked into ``reliability_floor_coeffs_MISO.csv``) is injected by
``_calibration_config`` for the MISO ISO exactly as it was for the keeper, so it
is reproduced identically without being re-passed here.

Memory note (CLAUDE.md rule 12): the MISO per-plant multi-zone LP uses ~15 GB
per year; run this SOLO (never concurrent with another per-plant solve) and with
swap headroom. Years solve sequentially inside ``solve_and_persist``.
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import (  # noqa: E402
    _load_reference,
    report_run,
    solve_and_persist,
)

_KEEPER_BUNDLE = _REPO / "results/calibration/MISO/miso_41_ct_evening_window"
_OUT_DIR = _REPO / "results/calibration/MISO/miso_41_ct_evening_window-ablation"

# meta.json key -> solve_and_persist parameter name, where they differ.
_RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# meta.json keys that are informational echoes (provenance / config defaults set
# by _calibration_config, not solve_and_persist arguments) — dropped.
_DROP = {
    "timestamp",
    "git_sha",
    "highspy_version",
    "shared_inputs",
    "passes",
    "gas_prices",  # solve_and_persist pulls Henry Hub from `reference`
    "coal_plant_monthly_pricing",  # MISO _calibration_config default
    "td_loss_factor",  # config default (0.0)
    "iso",
    "years",
    "hours",
    "commitment",
}


def _kwargs_from_meta() -> dict:
    """Rebuild the keeper's solve_and_persist kwargs from its meta.json."""
    meta = json.loads((_KEEPER_BUNDLE / "meta.json").read_text())
    sig_params = set(inspect.signature(solve_and_persist).parameters)
    out: dict = {}
    for key, value in meta.items():
        if key in _DROP:
            continue
        param = _RENAME.get(key, key)
        if param not in sig_params:
            raise KeyError(
                f"meta.json key {key!r} maps to {param!r}, not a "
                "solve_and_persist parameter — update _RENAME/_DROP"
            )
        # The *_overrides dicts are empty in the keeper; pass None so
        # solve_and_persist's `if prb_overrides:` guards are byte-identical.
        if param in ("prb_overrides", "bit_overrides") and not value:
            value = None
        out[param] = value
    return meta, out


def main() -> int:
    meta, kwargs = _kwargs_from_meta()
    reference = _load_reference()
    run_dir = solve_and_persist(
        meta["years"],
        "MISO",
        meta["hours"],
        reference,
        meta["commitment"],
        kwargs.pop("screen_coal"),
        _OUT_DIR,
        zero_forcing_ablation=True,
        ablation_of="miso_41_ct_evening_window",
        note=(
            "D-3 zero-forcing ablation twin of miso-41-ct-evening (CLAUDE.md "
            "rule 20): the miso_41_ct_evening_window keeper's meta.json config "
            "replayed VERBATIM with every merchant floor/bridge/drag "
            "neutralized (ScenarioConfig.as_zero_forcing_ablation; off-list "
            "from the D-2 mechanism registry), structural protected set kept "
            "(nuclear must-run, CHP steam, coal take-or-pay). Registered "
            "alongside the keeper for the E9 keeper-vs-twin delta."
        ),
        **kwargs,
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
