"""``coal_sync_floor_release`` on the SPP keeper's own recipe (zero LP, full data).

Two ``run_year(fleet_only=True)`` rebuilds of the designated SPP keeper's 2019
leg through the sanctioned recipe reconstruction
(:func:`scripts.lib.bundle_fleet.full_run_year_kwargs`): the flag off and the
flag on. Off, every LP-visible array equals the rebuild of a recipe that never
names the field (the historical branch). On, the ONLY array that moves is
``min_gen``, and it moves only on the coal ``_mustrun`` / ``_sync`` rows,
where the step-3a synchronization forcing is released to zero; the offer
stack (``mc_base``), capacities, heat rates, labels and every other floor are
byte-identical. The owner's D-5b ruling asked for exactly this evidence
(UC-2-SPP-B, 2026-10-10).
"""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

import numpy as np
import pytest

from tests.helpers.base import requires_raw

REPO = Path(__file__).resolve().parents[3]
BUNDLE = REPO / "results/calibration/closeout_spp_nuc_span"
RAW_SPP = REPO / "data/raw/spp-hourly-load"
YEAR = 2019
T = 8760
ARRAYS = (
    "unit_ids",
    "pmax",
    "pmin",
    "min_gen",
    "availability",
    "heat_rate",
    "emission_rate",
    "vom",
    "plant_group",
    "fuel_type_idx",
    "zone_idx",
    "plant_code",
    "nox_rate",
)


def _rebuild(release: bool | None):
    from scripts import replay_keeper as rk
    from scripts.lib.bundle_fleet import clear_fleet_caches, full_run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = full_run_year_kwargs(meta)
    kw.update(rk.derived_run_year_inputs(BUNDLE, YEAR))
    kw.pop("fleet_only", None)
    ttc = kw.pop("ttc_overrides", {}) or {}
    if release is not None:
        rk.apply_config_overlay(kw, {"coal_sync_floor_release": release})
    clear_fleet_caches()
    with contextlib.redirect_stderr(io.StringIO()):
        return run_year(
            YEAR,
            meta["iso"],
            T,
            float(meta["gas_prices"][str(YEAR)]),
            ttc,
            fleet_only=True,
            **kw,
        )


def _arr(st, name):
    return np.asarray(
        st["mc_base"] if name == "mc_base" else getattr(st["fleet_arrays"], name)
    )


@pytest.mark.slow
@requires_raw(RAW_SPP, BUNDLE / "meta.json")
def test_spp_keeper_recipe_off_is_identical_and_on_releases_only_the_coal_sync_forcing():
    absent = _rebuild(None)
    off = _rebuild(False)
    on = _rebuild(True)

    # 1. off == absent on every LP-visible array (the historical branch)
    for name in ARRAYS + ("mc_base",):
        a, b = _arr(absent, name), _arr(off, name)
        assert a.shape == b.shape, name
        assert np.array_equal(a, b), f"{name} differs between absent and explicit False"
    assert np.array_equal(np.asarray(absent["demand"]), np.asarray(off["demand"]))

    # 2. on: everything but min_gen is byte-identical to off
    for name in ARRAYS + ("mc_base",):
        if name == "min_gen":
            continue
        assert np.array_equal(_arr(off, name), _arr(on, name)), (
            f"{name} moved under release"
        )

    # 3. min_gen moves ONLY on coal _mustrun / _sync rows, and there it is released
    ids = [str(u) for u in _arr(off, "unit_ids")]
    groups = [str(g) for g in _arr(off, "plant_group")]
    mg_off, mg_on = _arr(off, "min_gen"), _arr(on, "min_gen")
    assert mg_off.shape == mg_on.shape
    moved = np.where(np.any(mg_off != mg_on, axis=1))[0]
    assert len(moved) > 0, (
        "the SPP keeper forces coal sync; the release must move something"
    )
    for i in moved:
        assert groups[i].startswith("COAL"), (ids[i], groups[i])
        assert ids[i].rsplit("_", 1)[1] in ("mustrun", "sync"), ids[i]
        assert np.all(mg_on[i] <= mg_off[i]), ids[i]
    # the released rows carry no other floor in this recipe: zero everywhere
    coal_sync_rows = [
        i
        for i, (u, g) in enumerate(zip(ids, groups))
        if g.startswith("COAL") and u.rsplit("_", 1)[1] in ("mustrun", "sync")
    ]
    assert coal_sync_rows
    assert float(np.abs(mg_on[coal_sync_rows]).max()) == 0.0
    assert float(mg_off[coal_sync_rows].max()) > 0.0
