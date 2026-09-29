"""``unit_outage_exit_ym_from_eia860``: EIA-860 exit-month routing of the CAMPD outage layer (NWPP-NEXT-10).

Stamps each outage row's ``exit_ym`` from EIA-860's own per-unit retirement
month, only where that month is one of its facility's dated exit bins, and
activates PJM-NEXT-8's dated-bin routing only at plants with a stamped row in
the solved year.
"""

import pandas as pd
import pytest

import market_sim.data.outages as om
from market_sim.config.scenarios import ScenarioConfig, cache_key_drop_defaults


class TestRegistration:
    """Registered, default-off, key-stable at its default."""

    def test_defaults_off(self):
        assert ScenarioConfig().unit_outage_exit_ym_from_eia860 is False

    def test_dropped_from_the_cache_key_at_its_default(self):
        assert cache_key_drop_defaults()["unit_outage_exit_ym_from_eia860"] is False

    def test_arming_it_changes_the_cache_key(self):
        base = ScenarioConfig()
        armed = base.with_overrides(unit_outage_exit_ym_from_eia860=True)
        assert base.cache_key() != armed.cache_key()


# Colstrip-shaped: units 1-2 retire 2020-01 into a dated bin, 3-4 survive.
_DATED = (((6076, "COAL"), ((2020, 1, 0.293),)),)
_EXITS = {(6076, "1"): (2020, 1), (6076, "2"): (2020, 1), (9, "1"): (2020, 1)}


def _rows(*rows):
    return pd.DataFrame(
        rows, columns=["facility_id", "unit_id", "outage_start", "outage_end"]
    )


@pytest.fixture
def exits(monkeypatch):
    monkeypatch.setattr(om, "_eia860_unit_exit_ym", lambda _d: dict(_EXITS))


def test_stamps_only_a_retiree_whose_month_is_a_dated_bin(exits):
    df = _rows(
        (6076, "1", "2020-01-02", "2020-12-31"),
        (6076, "3", "2020-05-02", "2020-05-10"),
        (9, "1", "2020-03-01", "2020-03-20"),  # retires, but no dated bin
    )
    out = om.stamp_exit_ym_from_eia860(df, _DATED, eia860_dir="x")
    got = [v if isinstance(v, str) else None for v in out["exit_ym"]]
    assert got == ["2020-01", None, None]


def test_an_existing_exit_ym_column_is_never_overwritten(exits):
    df = _rows((6076, "1", "2020-01-02", "2020-12-31")).assign(exit_ym="1999-01")
    out = om.stamp_exit_ym_from_eia860(df, _DATED, eia860_dir="x")
    assert out["exit_ym"].tolist() == ["1999-01"]


def test_routing_is_live_only_where_a_stamped_row_overlaps_the_year(exits):
    df = om.stamp_exit_ym_from_eia860(
        _rows((6076, "1", "2020-01-02", "2020-12-31")), _DATED, eia860_dir="x"
    )
    assert om.routable_dated_shares(df, _DATED, 2020, 8784) == _DATED
    assert om.routable_dated_shares(df, _DATED, 2019, 8760) is None


def test_a_plant_with_no_stamp_keeps_the_incumbent_routing(exits):
    # Centralia-shaped: CAMPD ids BW21/BW22 never match EIA-860's 1/2.
    dated = _DATED + (((3845, "COAL"), ((2020, 12, 0.49),)),)
    df = om.stamp_exit_ym_from_eia860(
        _rows(
            (6076, "1", "2020-01-02", "2020-12-31"),
            (3845, "BW21", "2020-03-21", "2020-07-15"),
        ),
        dated,
        eia860_dir="x",
    )
    assert om.routable_dated_shares(df, dated, 2020, 8784) == _DATED
