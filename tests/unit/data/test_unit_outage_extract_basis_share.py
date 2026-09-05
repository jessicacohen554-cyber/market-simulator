"""Unit tests for the extract-own-basis unit-outage share (nyiso-196).

``ScenarioConfig.unit_outage_extract_basis_share`` takes a COMBINED-CYCLE bin's
removed FRACTION on the committed extract's own capacity basis
(``unit_capacity_mw / plant_capacity_mw`` at a single-group facility — the
published ``unit_pct_of_plant``; the group's distinct-unit sum at a multi-group
facility) instead of over the fleet's net-summer bin sum, so the share no longer
depends on how the extract's per-unit capacity relates to the fleet bin. The
defect it repairs was measured at Cricket Valley 57185, where the CAMPD stack
ids collide with the EIA-860 STEAM generator ids and each 1x1 block is written
at 174.2 MW against a 1,016.8 MW bin (17.1 % removed per block instead of
33.3 %; 48.6 % of a dark plant left available).

Every property is asserted on a SYNTHETIC extract/fleet so a change to a
committed extract can never quietly turn a test green:

* the Cricket Valley arithmetic — a single-group CC facility's block share is
  the row's own ``unit / plant_capacity_mw``, and a full concurrent stop lands
  on EXACTLY 0.0 availability whatever the fleet bin says;
* the multi-group fallback — a facility carrying two model groups uses the
  group's distinct-unit sum, never the facility-wide ``plant_capacity_mw``;
* scope — steam bins never move (they belong to ``unit_outage_st_capacity_basis``,
  rule 19), ERCOT never moves, a bin absent from the index keeps the fleet
  denominator, and the flag is byte-inert while off;
* the rule-19 mutual exclusion with ``unit_outage_lp_capacity_basis``;
* the ``per_unit_clip`` interaction (the clip's ceiling and the share use the
  same denominator);
* registration, so the field cannot repeat the caiso-184 / nyiso-128 failure of
  landing unregistered and moving the pinned default cache key.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.data import outages
from market_sim.data.outages import (
    _CC_NAMEPLATE_BASIS_GROUPS,
    _extract_basis_index,
    _unit_outage_factors_from_events,
)

HOURS = 8760
YEAR = 2024


def _events(rows, start="2024-03-01", end="2024-03-20"):
    """Build a minimal extract frame: (plant, unit, group, unit_cap, plant_cap)."""
    return pd.DataFrame(
        [
            {
                "facility_id": p,
                "unit_id": u,
                "plant_group": g,
                "unit_capacity_mw": uc,
                "plant_capacity_mw": pc,
                "outage_start": start,
                "outage_end": end,
                "duration_days": 19.0,
            }
            for p, u, g, uc, pc in rows
        ]
    )


@pytest.fixture
def cc_fleet_cap(monkeypatch):
    """A synthetic fleet denominator: Cricket Valley's shape (bin 1016.8 MW)."""

    def _cap(iso, cc_steam_part_reclass=False, cc_nameplate_basis=False):
        return {
            (57185, "CC_REGULAR"): 1016.8,
            (777, "CC_REGULAR"): 800.0,
            (777, "ST_GAS"): 600.0,
            (2516, "ST_GAS"): 1500.0,
            (999, "CC_CHP"): 300.0,
        }

    monkeypatch.setattr(outages, "_iso_plant_capacity", _cap)
    monkeypatch.setattr(outages, "_fleet_status_index", lambda iso: None)
    return _cap


def _factors(df, iso="NYISO", **kw):
    basis = kw.pop("extract_basis", None)
    return _unit_outage_factors_from_events(
        df,
        YEAR,
        HOURS,
        "unused.csv",
        iso,
        per_unit_crosswalk=True,
        extract_basis=basis,
        **kw,
    )


def _window_hours(avail: np.ndarray) -> np.ndarray:
    return avail < 1.0 - 1e-12


def test_index_single_group_and_multi_group_bases():
    df = _events(
        [
            (57185, "U001", "CC_REGULAR", 174.2, 522.6),
            (57185, "U002", "CC_REGULAR", 174.2, 522.6),
            (777, "A", "CC_REGULAR", 200.0, 1000.0),
            (777, "B", "CC_REGULAR", 200.0, 1000.0),
            (777, "S1", "ST_GAS", 600.0, 1000.0),
        ]
    )
    idx = _extract_basis_index(df)
    # single-group facility: flagged, distinct-unit sum carried for completeness
    assert idx[(57185, "CC_REGULAR")] == (True, pytest.approx(348.4))
    # multi-group facility: NOT single-group; the group sum excludes the steam unit
    assert idx[(777, "CC_REGULAR")] == (False, pytest.approx(400.0))
    assert idx[(777, "ST_GAS")] == (False, pytest.approx(600.0))


def test_cricket_valley_block_share_and_full_stop_is_zero(cc_fleet_cap):
    """One block out = 33.3 % of the plant; three blocks out = 0.0 available."""
    df = _events(
        [
            (57185, "U001", "CC_REGULAR", 174.2, 522.6),
            (57185, "U002", "CC_REGULAR", 174.2, 522.6),
            (57185, "U003", "CC_REGULAR", 174.2, 522.6),
        ]
    )
    off = _factors(df)[(57185, "CC_REGULAR")]
    on = _factors(df, extract_basis=_extract_basis_index(df))[(57185, "CC_REGULAR")]
    w = _window_hours(off)
    assert w.any()
    # production construction: 3 x 174.2 / 1016.8 -> 0.486 left at a dark plant
    assert off[w].min() == pytest.approx(1.0 - 3 * 174.2 / 1016.8, abs=1e-9)
    # extract-own basis: 3 x (174.2 / 522.6) = 1.0 removed -> exactly 0.0
    assert on[w].max() == pytest.approx(0.0, abs=1e-9)
    # one block alone: the published unit_pct_of_plant (33.3 %), not 17.1 %
    one = _factors(df.iloc[:1], extract_basis=_extract_basis_index(df.iloc[:1]))[
        (57185, "CC_REGULAR")
    ]
    assert one[w].min() == pytest.approx(1.0 - 174.2 / 522.6, abs=1e-9)
    # outside the window both are 1.0
    assert on[~w].min() == 1.0 and off[~w].min() == 1.0


def test_multi_group_facility_uses_group_sum_not_facility_capacity(cc_fleet_cap):
    df = _events(
        [
            (777, "A", "CC_REGULAR", 200.0, 1000.0),
            (777, "B", "CC_REGULAR", 200.0, 1000.0),
            (777, "S1", "ST_GAS", 600.0, 1000.0),
        ]
    )
    on = _factors(df.iloc[:1], extract_basis=_extract_basis_index(df))
    cc = on[(777, "CC_REGULAR")]
    w = _window_hours(cc)
    # A out: 200 / (200 + 200) = 50 % of the CC bin, NOT 200 / 1000 = 20 %
    assert cc[w].min() == pytest.approx(0.5, abs=1e-9)


def test_steam_bins_ercot_and_unindexed_bins_never_move(cc_fleet_cap):
    df = _events(
        [
            (2516, "1", "ST_GAS", 400.0, 1200.0),
            (777, "S1", "ST_GAS", 600.0, 1000.0),
            (777, "A", "CC_REGULAR", 200.0, 1000.0),
        ]
    )
    idx = _extract_basis_index(df)
    off = _factors(df)
    on = _factors(df, extract_basis=idx)
    for key in ((2516, "ST_GAS"), (777, "ST_GAS")):
        assert key[1] not in _CC_NAMEPLATE_BASIS_GROUPS
        np.testing.assert_array_equal(on[key], off[key])
    # a CC bin the index does not carry keeps the fleet denominator
    partial_idx = {k: v for k, v in idx.items() if k != (777, "CC_REGULAR")}
    np.testing.assert_array_equal(
        _factors(df, extract_basis=partial_idx)[(777, "CC_REGULAR")],
        off[(777, "CC_REGULAR")],
    )
    # flag off is the identity with the un-indexed call
    np.testing.assert_array_equal(
        _factors(df, extract_basis=None)[(777, "CC_REGULAR")], off[(777, "CC_REGULAR")]
    )


def test_mutually_exclusive_with_lp_capacity_basis(cc_fleet_cap):
    df = _events([(57185, "U001", "CC_REGULAR", 174.2, 522.6)])
    with pytest.raises(ValueError, match="mutually exclusive"):
        _factors(df, extract_basis=_extract_basis_index(df), cc_nameplate_basis=True)
    # st_capacity_basis acts on disjoint bins and may coexist (no raise)
    _factors(df, extract_basis=_extract_basis_index(df), st_capacity_basis=True)


def test_per_unit_clip_shares_the_denominator(cc_fleet_cap):
    """The clip's ceiling and the share divide by the SAME extract basis."""
    df = pd.concat(
        [
            _events(
                [(57185, "U001", "CC_REGULAR", 174.2, 522.6)],
                "2024-03-01",
                "2024-03-10",
            ),
            _events(
                [(57185, "U001", "CC_REGULAR", 174.2, 522.6)],
                "2024-03-10",
                "2024-03-20",
            ),
        ],
        ignore_index=True,
    )
    idx = _extract_basis_index(df)
    clipped = _factors(df, extract_basis=idx, per_unit_clip=True)[(57185, "CC_REGULAR")]
    unclipped = _factors(df, extract_basis=idx)[(57185, "CC_REGULAR")]
    # the boundary day is double-counted unclipped (2 x 33.3 %), clipped at 33.3 %
    assert clipped.min() == pytest.approx(1.0 - 174.2 / 522.6, abs=1e-9)
    assert unclipped.min() == pytest.approx(1.0 - 2 * 174.2 / 522.6, abs=1e-9)
    assert (clipped >= unclipped - 1e-12).all()


def test_field_registered_and_default_off():
    assert ScenarioConfig().unit_outage_extract_basis_share is False
    assert "unit_outage_extract_basis_share" in _CACHE_KEY_OPTIONAL_FIELDS
    assert (
        _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["unit_outage_extract_basis_share"] == "False"
    )
    assert ScenarioConfig(
        unit_outage_extract_basis_share=True
    ).unit_outage_extract_basis_share
