"""Tests for ``ScenarioConfig.coal_sync_floor_release`` (lane UC-2-SPP-B, owner ruling D-5b).

The release removes the step-3a synchronization FORCING on the coal
``_mustrun`` / ``_sync`` min-load bands: ``_compose_min_gen_floors`` composes
no ``MECH_COAL_MUSTRUN`` floor. Everything else the band carries stays as
``coal_sync_srmc_tranche`` built it -- the split, its pricing and the
``coal_sync_pmin_mw`` stamp that selects the band's availability basis. Off,
the fleet is byte-identical to a config that never names the field: the flag
is read at one site only.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, bins_to_fleet, generators_to_fleet_arrays
from market_sim.data.floor_mechanisms import MECH_COAL_MUSTRUN

ZONES = ["AEP"]
HOURS = 8760
# Gavin 8102 is 100 % contracted (take-or-pay), Miami Fort 2832 is 0 % (all
# spot) in the PJM artifact: the two extremes of the split, both exercised.
_GAVIN, _MIAMI = 8102, 2832


def _coal_row(code: int, name: str) -> dict:
    """One synthetic COAL_PRB bin row (one plant) at a 27 % online-Pmin floor."""
    return {
        "Plant_Group": "COAL_PRB",
        "ERCOT_Zone": "AEP",
        "Bin_Number": 1,
        "Bin_Label": name,
        "Plant_Code": code,
        "Plant_Name": name,
        "Turbine_Class": "",
        "capacity_mw": 1000.0,
        "hr_weighted": 10.0,
        "pct_mr": 27.0,
        "pct_mc": 5.0,
        "pct_econ": 66.0,
        "pct_peak": 2.0,
        "min_run": 0,
        "min_down": 0,
        "hr_mr": 10.5,
        "hr_mc": 10.2,
        "hr_econ": 10.0,
        "hr_peak": 12.0,
        "plant_count": 1,
        "plant_codes": [code],
        "fuel": "coal",
    }


def _cfg(**over) -> ScenarioConfig:
    kw = dict(
        iso="PJM",
        weather_year=2024,
        mode="backcast",
        hours=HOURS,
        coal_takeorpay_from_data=True,
        coal_mustrun_online_pmin=True,
        coal_sync_srmc_tranche=True,
    )
    kw.update(over)
    return ScenarioConfig(**kw)


def _fleet(cfg: ScenarioConfig) -> list[Generator]:
    bins = pd.DataFrame([_coal_row(_GAVIN, "Gavin"), _coal_row(_MIAMI, "Miami Fort")])
    return bins_to_fleet(bins, ZONES, cfg)[0]


def _arrays(cfg: ScenarioConfig):
    return generators_to_fleet_arrays(
        _fleet(cfg), ZONES, hours=HOURS, iso="PJM", config=cfg
    )


def _suffix(unit_id: str) -> str:
    return unit_id.rsplit("_", 1)[1]


def _snapshot(fleet: list[Generator]) -> list[dict]:
    return [
        dataclasses.asdict(g) if dataclasses.is_dataclass(g) else dict(vars(g))
        for g in fleet
    ]


def test_default_off_is_byte_identical_to_a_config_that_never_names_the_field():
    """Explicit False == absent: every Generator field and every LP array equal."""
    absent, explicit = _cfg(), _cfg(coal_sync_floor_release=False)
    assert _snapshot(_fleet(absent)) == _snapshot(_fleet(explicit))
    fa0, fa1 = _arrays(absent), _arrays(explicit)
    assert list(fa0.unit_ids) == list(fa1.unit_ids)
    assert np.array_equal(np.asarray(fa0.min_gen), np.asarray(fa1.min_gen))
    assert np.array_equal(np.asarray(fa0.availability), np.asarray(fa1.availability))
    assert np.array_equal(np.asarray(fa0.pmax), np.asarray(fa1.pmax))
    # the forcing is present off: the min-load bands carry a MECH 3 floor
    ids = [str(u) for u in fa0.unit_ids]
    band = [i for i, u in enumerate(ids) if _suffix(u) in ("mustrun", "sync")]
    assert band, "the fixture must build _mustrun/_sync bands"
    mg = np.asarray(fa0.min_gen)
    assert float(mg[band].max()) > 0.0
    assert set(np.unique(np.asarray(fa0.min_gen_mechanism)[band])) >= {
        MECH_COAL_MUSTRUN
    }


def test_release_removes_only_the_forcing():
    """True: no MECH 3 floor; the Generators, the split and every other array are unchanged."""
    off, on = _cfg(coal_sync_floor_release=False), _cfg(coal_sync_floor_release=True)
    # the assembled fleet is IDENTICAL (the stamp, the split and the pricing stay)
    f_off, f_on = _fleet(off), _fleet(on)
    assert _snapshot(f_off) == _snapshot(f_on)
    assert {_suffix(g.unit_id) for g in f_on} >= {"mustrun", "sync", "committed"}
    assert all(
        g.coal_sync_pmin_mw > 0.0
        for g in f_on
        if _suffix(g.unit_id) in ("mustrun", "sync")
    )
    sync = {g.plant_code: g.pmax_mw for g in f_on if _suffix(g.unit_id) == "sync"}
    assert np.isclose(sync[_MIAMI], 270.0)  # 27 % of 1,000 MW, 0 % contracted
    assert _GAVIN not in sync  # 100 % contracted: no spot band either way
    # the arrays: only min_gen moves, and it moves to zero on the band
    fa_off, fa_on = _arrays(off), _arrays(on)
    assert list(fa_off.unit_ids) == list(fa_on.unit_ids)
    for name in ("pmax", "pmin", "availability", "heat_rate", "vom", "emission_rate"):
        assert np.array_equal(
            np.asarray(getattr(fa_off, name)), np.asarray(getattr(fa_on, name))
        ), name
    ids = [str(u) for u in fa_on.unit_ids]
    band = [i for i, u in enumerate(ids) if _suffix(u) in ("mustrun", "sync")]
    rest = [i for i in range(len(ids)) if i not in band]
    mg_off = np.asarray(fa_off.min_gen)
    assert float(mg_off[band].max()) > 0.0
    if fa_on.min_gen is None:
        # the band was the only floor in this fleet: no floor array at all
        assert not rest or float(np.abs(mg_off[rest]).max()) == 0.0
    else:
        mg_on = np.asarray(fa_on.min_gen)
        assert float(np.abs(mg_on[band]).max()) == 0.0
        if rest:
            assert np.array_equal(mg_off[rest], mg_on[rest])
        assert MECH_COAL_MUSTRUN not in set(
            np.unique(np.asarray(fa_on.min_gen_mechanism))
        )


def test_release_without_the_tranche_is_inert():
    """Where coal_sync builds no floor the flag has nothing to release."""
    base = _cfg(coal_sync_srmc_tranche=False)
    rel = _cfg(coal_sync_srmc_tranche=False, coal_sync_floor_release=True)
    assert _snapshot(_fleet(base)) == _snapshot(_fleet(rel))
    fa0, fa1 = _arrays(base), _arrays(rel)
    assert np.array_equal(np.asarray(fa0.min_gen), np.asarray(fa1.min_gen))


def test_cache_key_registration():
    """Default drops out of the hash (nyiso-119 discipline); armed keys distinctly."""
    base = ScenarioConfig(iso="SPP", mode="backcast")
    explicit = ScenarioConfig(iso="SPP", mode="backcast", coal_sync_floor_release=False)
    assert base.cache_key() == explicit.cache_key()
    armed = base.with_overrides(coal_sync_floor_release=True)
    assert armed.cache_key() != base.cache_key()
