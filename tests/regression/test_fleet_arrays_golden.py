"""Golden byte-guard for ``generators_to_fleet_arrays`` (ERCOT 2023 fixture).

Pins every :class:`~market_sim.data.fleet.FleetArrays` field produced by the
full ERCOT 2023 CAMPD backcast fleet chain (``load_or_synthesize_bins`` →
``build_base_fleet`` → ``build_dispatch_fleet`` → ``generators_to_fleet_arrays``)
to per-field content hashes captured from the pre-split ``data/fleet.py``
monolith at the fleet-package split (refactor-consolidation plan §5 item 8,
2026-07-23). The split's sub-task (a) decomposes the ~1,800-line
``generators_to_fleet_arrays`` body into pure array helpers; this guard proves
the decomposition is byte-neutral without an LP solve (the keeper LP byte gate
— ``capture_keeper_goldens.py`` / ``regression_gate.py --mode byte`` — covers
the full solve path separately).

Regenerating the golden (``python tests/regression/test_fleet_arrays_golden.py
--capture``) is governed like every golden in this repo: never to make a
failing gate pass — only under an owner-authorized behavior change, with the
reason recorded in the commit.

REGENERATED ONCE, at ERCOT-187 (2026-08-10), for exactly one such change:
``6a8f285c`` "neiso-65: adopt guard-corrected CAMPD extracts, all six ISOs"
(2026-07-26), the merge of the merit-order guard the owner ADOPTED in
``docs/handoffs/campd-economic-layup-fix-charter-2026-07.md`` §8 — whose verdict
states that "the availability envelope every keeper reads now excludes the
reclassified economic-layup windows" (ERCOT: 1,352 windows / 3,986 GW-days).
It moved ``availability`` and ``min_gen`` and nothing else, and the golden was
simply never re-captured with it. Attribution is byte-exact rather than
inferred: HEAD code with ``data/raw/campd-unit-outages.csv`` reverted to its
pre-guard blob reproduces the ORIGINAL golden hashes on both fields, so the
model code is provably inert across the whole drift and this single authorized
data correction owns 100 % of it. Nothing about ERCOT-185's day-shaped partial
plateau is involved — both fields are byte-identical either side of it (the
mechanism is default-off, and this fixture never reads the shaped extract).
Evidence: ``results/calibration/FINDING-ercot187-golden-hash-attribution-2026-08-10.md``.

The fixture parameters below are FROZEN (they define the golden's identity):
the 2023 ERCOT backcast config from ``pipeline.backcast_config.backcast_config``
with a pinned fixture gas price — deterministic, measured-data-backed inputs,
no LP.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sys

import numpy as np
import pytest

from market_sim.config.iso_configs import get_iso_config
from market_sim.data.fleet import (
    FleetArrays,
    build_base_fleet,
    build_dispatch_fleet,
    generators_to_fleet_arrays,
    load_or_synthesize_bins,
)
from market_sim.pipeline.backcast_config import backcast_config
from tests.helpers import REPO_ROOT

GOLDEN_PATH = REPO_ROOT / "tests" / "golden" / "fleet_arrays_ercot_2023.json"

# Frozen fixture parameters. The gas price is a fixture constant (it enters
# marginal-cost assembly downstream, not the arrays), pinned so the driver is
# fully deterministic; 2.13 $/MMBtu is the 2023 Henry Hub annual average the
# ERCOT calibration lane uses (docs/parameter-citations.md).
FIXTURE_YEAR = 2023
FIXTURE_ISO = "ERCOT"
FIXTURE_GAS_PRICE = 2.13


def _build_fixture_arrays() -> FleetArrays:
    """Run the frozen ERCOT 2023 fleet chain and return its FleetArrays."""
    config = backcast_config(
        FIXTURE_YEAR, FIXTURE_ISO, 8760, gas_price=FIXTURE_GAS_PRICE
    )
    iso_config = get_iso_config(FIXTURE_ISO)
    zone_names = iso_config.zone_names
    campd_bins = load_or_synthesize_bins(config, FIXTURE_ISO, iso_config, [])
    fleet = build_base_fleet(
        campd_bins,
        FIXTURE_ISO,
        iso_config,
        zone_names,
        config,
        [],
        [],
        FIXTURE_YEAR,
    )
    dispatch_fleet, _fuel_fracs, _hydro_idx, _hydro_energy = build_dispatch_fleet(
        fleet, campd_bins, [], FIXTURE_ISO, FIXTURE_YEAR, zone_names, config
    )
    return generators_to_fleet_arrays(
        dispatch_fleet,
        zone_names,
        8760,
        iso=FIXTURE_ISO,
        config=config,
        year=FIXTURE_YEAR,
    )


def _field_hashes(arrays: FleetArrays) -> dict[str, str]:
    """Per-field content hashes: dtype+shape+bytes for ndarrays, JSON otherwise."""
    out: dict[str, str] = {}
    for f in dataclasses.fields(arrays):
        value = getattr(arrays, f.name)
        h = hashlib.sha256()
        if value is None:
            out[f.name] = "None"
            continue
        if isinstance(value, np.ndarray):
            if value.dtype == object:
                # object arrays (state / plant_group strings): hash the reprs
                h.update(repr(value.tolist()).encode())
            else:
                arr = np.ascontiguousarray(value)
                h.update(str(arr.dtype).encode())
                h.update(str(arr.shape).encode())
                h.update(arr.tobytes())
        else:
            h.update(json.dumps(value, default=repr).encode())
        out[f.name] = h.hexdigest()
    return out


@pytest.mark.slow
@pytest.mark.fulldata
@pytest.mark.golden
def test_generators_to_fleet_arrays_ercot_2023_golden() -> None:
    """Every FleetArrays field byte-matches the pre-split monolith capture."""
    golden = json.loads(GOLDEN_PATH.read_text())
    got = _field_hashes(_build_fixture_arrays())
    assert got == golden["field_hashes"], (
        "FleetArrays drift vs the pre-split golden; fields differing: "
        f"{sorted(k for k in got if got[k] != golden['field_hashes'].get(k))}"
    )


if __name__ == "__main__":
    if "--capture" not in sys.argv:
        raise SystemExit(
            "usage: python tests/regression/test_fleet_arrays_golden.py --capture"
        )
    arrays = _build_fixture_arrays()
    payload = {
        "fixture": {
            "iso": FIXTURE_ISO,
            "year": FIXTURE_YEAR,
            "gas_price": FIXTURE_GAS_PRICE,
            "hours": 8760,
        },
        "n_gen": arrays.n_gen,
        "field_hashes": _field_hashes(arrays),
    }
    GOLDEN_PATH.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(f"wrote {GOLDEN_PATH} ({arrays.n_gen} generators)")
