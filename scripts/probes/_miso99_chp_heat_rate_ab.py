"""miso-99 A/B driver: measured POWER-ONLY CHP heat rates OFF (A) vs ON (B).

The single delta is ``ScenarioConfig.measured_chp_heat_rates``, carried on the
generic ``prb_overrides`` ScenarioConfig channel (the same channel nyiso-89 used
to arm ``measured_ct_heat_rates``, so it round-trips through ``meta.json``'s
``coal_prb_sigmoid_overrides`` and is reconstructable by
``replay_keeper.build_kwargs``). Nothing else differs: no data file is staged,
no other kwarg moves, and the benchmark is untouched by construction
(``_btm_frame`` is EIA-923 class totals x measured host shares — a heat rate
does not enter it).

Armed, 72 generators / 6,732 MW of MISO CC_CHP + CT_CHP take their plant's own
measured power-only heat rate — eGRID's ``PLHTRT`` with eGRID's own published
CHP useful-thermal heat-input allocation ``CHPCHTI`` added back over the same
``PLNGENAN`` denominator. See
``results/calibration/FINDING-miso99-chp-heat-rate-2026-07-28.md`` for the
pre-registered prediction this A/B is run against, and
``scripts/data/derive_chp_power_only_heat_rates.py`` for the measurement.

**Arm A cannot be the registered ``miso98_chp_sector_B`` bundle** — miso-92 §7
records that post-CAMPD-envelope-correction replays do not reproduce a keeper's
registered numbers, so both arms are same-HEAD replays of the keeper recipe and
only the arm-vs-arm delta is quoted.

The keeper recipe is rebuilt from ``miso98_chp_sector_B/meta.json`` rather than
from ``run_config.json``'s ``calibration_flags`` — the latter is a curated ~35-key
subset that omits ~170 non-default kwargs this keeper actually solved with, and
a mis-specified arm mis-attributes the delta rather than measuring it.

MEMORY (rule 12, FINDING-miso98 §8): ``--reuse-solved`` OOMs at 15.9 GB on the
three-year assembly stage. This driver therefore solves **one year per process
into ONE bundle dir with no reuse**, and the chain is reassembled afterwards by
``scripts/probes/pjm119_merge_year_chain.py``. Never run two MISO solves at once.

Usage (one process per year, sequentially)::

    python scripts/probes/_miso99_chp_heat_rate_ab.py --arm A --year 2023 \
        --out results/calibration/miso99_chp_hr_A
    python scripts/probes/_miso99_chp_heat_rate_ab.py --arm A --year 2024 \
        --out results/calibration/miso99_chp_hr_A
    ...
    python scripts/probes/pjm119_merge_year_chain.py results/calibration/miso99_chp_hr_A
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

RESULTS = REPO / "results" / "calibration"
KEEPER = RESULTS / "miso98_chp_sector_B"

# meta.json key -> solve_and_persist kwarg name, where they differ.
_RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# meta.json keys that are recorded provenance/derived values, not kwargs.
_SKIP = {
    "timestamp",
    "iso",
    "years",
    "hours",
    "passes",
    "commitment",  # passed explicitly below (keeper value, unchanged)
    "gas_prices",  # re-derived internally from reference + years
    "coal_plant_monthly_pricing",  # derived from backcast_config, not a kwarg
    "td_loss_factor",  # derived from backcast_config, not a kwarg
    "ercot_zonal_gas_basis",
    "ercot_west_netload_gas_shape",
    "ercot_west_gas_delivered_floor",
    "shared_inputs",
    "environment",
    "reuse",
    "git_sha",
    "highspy_version",
    "basis_sha",  # provenance hash of the solve's shared basis inputs
}


def keeper_kwargs() -> dict:
    """Rebuild the miso-98b keeper's ``solve_and_persist`` kwargs from meta.json."""
    meta = json.loads((KEEPER / "meta.json").read_text())
    sig = set(inspect.signature(solve_and_persist).parameters)
    kwargs: dict = {}
    for key, value in meta.items():
        if key in _SKIP:
            continue
        pname = _RENAME.get(key, key)
        if pname not in sig:
            raise SystemExit(f"unmapped meta.json key: {key!r}")
        kwargs[pname] = value
    return kwargs


def main() -> int:
    """Solve one year of one arm into the shared bundle directory."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=("A", "B"), required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    kwargs = keeper_kwargs()
    overrides = dict(kwargs.get("prb_overrides") or {})
    if "measured_chp_heat_rates" in overrides:
        raise SystemExit(
            "the keeper recipe already carries measured_chp_heat_rates — "
            "this A/B would not be a single delta"
        )
    # Arm A is the recipe verbatim (the field's default is False, so the key is
    # simply absent and the config is byte-identical to the keeper's).
    if args.arm == "B":
        overrides["measured_chp_heat_rates"] = True
    kwargs["prb_overrides"] = overrides
    args.out.mkdir(parents=True, exist_ok=True)

    note = (
        f"miso-99 measured CHP power-only heat-rate A/B, arm {args.arm} "
        f"(measured_chp_heat_rates={args.arm == 'B'}). SINGLE DELTA vs the "
        "other arm: that one ScenarioConfig field; no data file staged, no "
        "other kwarg moved, benchmark identical by construction. Armed, 72 "
        "generators / 6,732 MW of CC_CHP + CT_CHP take their plant's own "
        "measured power-only heat rate — eGRID PLHTRT with eGRID's published "
        "CHP useful-thermal heat-input allocation CHPCHTI added back over the "
        "same PLNGENAN denominator (no gross-to-net factor is involved). "
        "Keeper recipe (2026-07-27-miso-98b-sectormeasured) rebuilt from "
        "meta.json. Evidence: "
        "results/calibration/FINDING-miso99-chp-heat-rate-2026-07-28.md"
    )

    solve_and_persist(
        [args.year],
        "MISO",
        8760,
        _load_reference(),
        run_dir=args.out,
        commitment=False,
        note=note,
        **kwargs,
    )
    print(f"DONE arm {args.arm} year={args.year} -> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
