"""``unit_outage_exit_cohort_repair``: the exit-cohort repair of the CAMPD outage layer (PJM-NEXT-8).

Selects the ``-rederive-peakerkeep-exitfix-unitfuel-`` companion on top of the
PJM-NEXT-6 chain (raising when armed and not derived), and keys a row whose
``exit_ym`` names a dated exit bin to that bin over its own capacity share.
"""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from market_sim.config.scenarios import ScenarioConfig, cache_key_drop_defaults


class TestRegistration:
    """Registered, default-off, key-stable at its default."""

    def test_defaults_off(self):
        assert ScenarioConfig().unit_outage_exit_cohort_repair is False

    def test_dropped_from_the_cache_key_at_its_default(self):
        assert cache_key_drop_defaults()["unit_outage_exit_cohort_repair"] is False

    def test_arming_it_changes_the_cache_key(self):
        base = ScenarioConfig()
        armed = base.with_overrides(unit_outage_exit_cohort_repair=True)
        assert base.cache_key() != armed.cache_key()


_FAMILY = (
    "campd-unit-outages-memberrepair-PJM.csv",
    "campd-unit-outages-memberrepair-unitfuel-PJM.csv",
    "campd-unit-outages-rederive-unitfuel-PJM.csv",
    "campd-unit-outages-rederive-peakerkeep-unitfuel-PJM.csv",
    "campd-unit-outages-rederive-peakerkeep-exitfix-unitfuel-PJM.csv",
)
_ARMED = dict(
    membership_repair=True,
    unit_fuel_routing=True,
    full_rederive=True,
    rederive_peaker_windows=True,
)


def _lay(tmp_path, monkeypatch, *names):
    import market_sim.data.outages as om

    monkeypatch.setattr(om, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
    for n in names:
        (tmp_path / n).write_text("x\n")
    return om


def test_selects_the_companion(tmp_path, monkeypatch):
    om = _lay(tmp_path, monkeypatch, *_FAMILY)
    path = om.unit_outage_csv_for_iso("PJM", exit_cohort_repair=True, **_ARMED)
    assert path.name == _FAMILY[-1]


def test_off_keeps_the_peakerkeep_file(tmp_path, monkeypatch):
    om = _lay(tmp_path, monkeypatch, *_FAMILY)
    assert om.unit_outage_csv_for_iso("PJM", **_ARMED).name == _FAMILY[3]


def test_raises_when_armed_and_not_derived(tmp_path, monkeypatch):
    om = _lay(tmp_path, monkeypatch, *_FAMILY[:4])
    with pytest.raises(FileNotFoundError):
        om.unit_outage_csv_for_iso("PJM", exit_cohort_repair=True, **_ARMED)


def _gen(code, uid, mw, ry=None):
    return SimpleNamespace(
        plant_code=code,
        plant_group="COAL_BIT",
        unit_id=uid,
        pmax_mw=mw,
        retirement_year=ry,
    )


def test_dated_shares_and_factor():
    from market_sim.data.fleet.arrays import _dated_exit_bin_shares, _dated_exit_factor

    gens = [
        _gen(6094, "COAL_X_p6094_r201902_econc00", 1660.0, 2019),
        _gen(6094, "COAL_X_p6094_r201911_econc00", 830.0, 2019),
        _gen(7, "COAL_X_p7_econc00", 100.0),
    ]
    shares = _dated_exit_bin_shares(gens)
    ((key, rows),) = shares
    assert key == (6094, "COAL")
    assert [(a, b, round(c, 4)) for a, b, c in rows] == [
        (2019, 2, 0.6667),
        (2019, 11, 0.3333),
    ]
    own = np.full(4, 0.0)
    ufac = {(6094, "COAL", 2019, 11): own}
    # Dated tranche with a window on its own bin reads it; the other reads none.
    assert _dated_exit_factor(ufac, key, gens[1], shares, None) is own
    assert _dated_exit_factor(ufac, key, gens[0], shares, None) is None
    # Undated tranche is untouched.
    assert _dated_exit_bin_shares([gens[2]]) is None


def test_row_routes_to_its_dated_bin_over_its_share():
    import market_sim.data.outages as om

    df = pd.DataFrame(
        {
            "facility_id": [6094],
            "unit_id": ["3"],
            "plant_group": ["COAL"],
            "unit_capacity_mw": [913.7],
            "outage_start": ["2019-03-01"],
            "outage_end": ["2019-03-10"],
            "duration_days": [10.0],
            "exit_ym": ["2019-11"],
        }
    )
    shares = (((6094, "COAL"), ((2019, 2, 2 / 3), (2019, 11, 1 / 3))),)
    om_cap = {(6094, "COAL"): 2741.1}
    orig = om._iso_plant_capacity
    try:
        om._iso_plant_capacity = lambda *a, **k: om_cap
        out = om._unit_outage_factors_from_events(
            df, 2019, 8760, "", "PJM", dated_bin_shares=shares
        )
        off = om._unit_outage_factors_from_events(df, 2019, 8760, "", "PJM")
    finally:
        om._iso_plant_capacity = orig
    dated = out[(6094, "COAL", 2019, 11)]
    # The unit is the whole dated bin: fully out in its window.
    assert dated.min() == 0.0
    assert (6094, "COAL") not in out
    # Off: diluted over the whole plant (the defect).
    assert round(float(off[(6094, "COAL")].min()), 3) == round(1 - 913.7 / 2741.1, 3)
