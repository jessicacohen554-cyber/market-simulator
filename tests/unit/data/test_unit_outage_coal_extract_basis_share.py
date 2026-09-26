"""Unit tests for the coal-scope extract-own-basis unit-outage share (SPP-86).

``ScenarioConfig.unit_outage_coal_extract_basis_share`` widens nyiso-196's
extract-basis construction (``unit_outage_extract_basis_share``, combined-cycle
bins only) to the COAL bins. The defect it repairs was measured on the SPP keeper:
Holcomb 108 is a SINGLE-unit coal plant whose extract row carries 348.7 MW
against a 358.9 MW fleet bin, so every full stop left 2.6-2.9 % of the plant
available and the ``coal_mustrun`` floor survived on that residual
(``docs/handoffs/FINDING-spp-86-coal-floor-conduct-2026-09-26.md``).

Every property is asserted on a SYNTHETIC extract/fleet:

* Holcomb's arithmetic -- a single-unit coal plant fully out lands on EXACTLY 0.0;
* the other direction -- a unit at a plant whose extract basis exceeds its bin
  removes its own share, not its nameplate MW;
* scope -- the coal flag never moves a CC bin and the CC flag never moves a coal
  bin; both together compose over disjoint groups; ERCOT never moves;
* the rule-19 mutual exclusion with the dispatched-bin denominator is kept, and
  the lp-capacity-basis exclusion no longer fires on a coal-only arm;
* registration, and byte-inertness while off.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.plant_taxonomy import COAL_ARTIFACT_FAMILY
from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.data import outages
from market_sim.data.outages import (
    _CC_NAMEPLATE_BASIS_GROUPS,
    _extract_basis_groups,
    _extract_basis_index,
    _unit_outage_factors_from_events,
)

HOURS = 8760
YEAR = 2021


def _events(rows, start="2021-03-01", end="2021-03-20"):
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
def fleet_cap(monkeypatch):
    """Synthetic fleet denominators: Holcomb's and Jeffrey's shapes plus a CC bin."""

    def _cap(iso, cc_steam_part_reclass=False, cc_nameplate_basis=False):
        return {
            (108, COAL_ARTIFACT_FAMILY): 358.9,
            (6068, COAL_ARTIFACT_FAMILY): 2010.6,
            (55, "CC_REGULAR"): 1016.8,
        }

    monkeypatch.setattr(outages, "_iso_plant_capacity", _cap)
    monkeypatch.setattr(outages, "_fleet_status_index", lambda iso: None)
    return _cap


ROWS = [
    (108, "SGU1", COAL_ARTIFACT_FAMILY, 348.7, 348.7),
    (6068, "1", COAL_ARTIFACT_FAMILY, 720.0, 2160.0),
    (55, "U001", "CC_REGULAR", 174.2, 522.6),
]


def _factors(df, groups, iso="SPP", **kw):
    basis = _extract_basis_index(df) if groups else None
    return _unit_outage_factors_from_events(
        df,
        YEAR,
        HOURS,
        "unused.csv",
        iso,
        extract_basis=basis,
        extract_basis_groups=groups or _CC_NAMEPLATE_BASIS_GROUPS,
        **kw,
    )


def _min(f, key):
    return float(np.asarray(f[key]).min())


def test_groups_helper():
    assert _extract_basis_groups(False, False) == ()
    assert _extract_basis_groups(True, False) == _CC_NAMEPLATE_BASIS_GROUPS
    assert _extract_basis_groups(False, True) == (COAL_ARTIFACT_FAMILY,)
    assert set(_extract_basis_groups(True, True)) == {
        *_CC_NAMEPLATE_BASIS_GROUPS,
        COAL_ARTIFACT_FAMILY,
    }


def test_holcomb_full_stop_lands_on_zero(fleet_cap):
    df = _events(ROWS)
    off = _factors(df, ())
    on = _factors(df, _extract_basis_groups(False, True))
    # fleet basis: 1 - 348.7/358.9 of the plant survives the full stop
    assert _min(off, (108, COAL_ARTIFACT_FAMILY)) == pytest.approx(1 - 348.7 / 358.9)
    assert _min(on, (108, COAL_ARTIFACT_FAMILY)) == 0.0


def test_unit_removes_its_own_share_where_basis_exceeds_bin(fleet_cap):
    df = _events(ROWS)
    off = _factors(df, ())
    on = _factors(df, _extract_basis_groups(False, True))
    assert _min(off, (6068, COAL_ARTIFACT_FAMILY)) == pytest.approx(1 - 720.0 / 2010.6)
    assert _min(on, (6068, COAL_ARTIFACT_FAMILY)) == pytest.approx(1 - 720.0 / 2160.0)


def test_scopes_are_disjoint(fleet_cap):
    df = _events(ROWS)
    off = _factors(df, ())
    coal = _factors(df, _extract_basis_groups(False, True))
    cc = _factors(df, _extract_basis_groups(True, False))
    both = _factors(df, _extract_basis_groups(True, True))
    ccb = (55, "CC_REGULAR")
    hol = (108, COAL_ARTIFACT_FAMILY)
    assert np.array_equal(coal[ccb], off[ccb])  # coal flag never moves a CC bin
    assert np.array_equal(cc[hol], off[hol])  # CC flag never moves a coal bin
    assert np.array_equal(both[ccb], cc[ccb])
    assert np.array_equal(both[hol], coal[hol])


def test_dispatched_denominator_still_exclusive(fleet_cap):
    df = _events(ROWS)
    with pytest.raises(ValueError, match="mutually exclusive"):
        _factors(
            df,
            _extract_basis_groups(False, True),
            lp_bin_capacity=(((108, COAL_ARTIFACT_FAMILY), 358.9),),
        )


def test_coal_only_arm_composes_with_cc_nameplate_basis(fleet_cap):
    # cc_nameplate_basis acts on CC bins only, so a coal-only extract-basis arm
    # is a different object and must not trip the CC-share exclusion.
    df = _events(ROWS)
    _factors(df, _extract_basis_groups(False, True), cc_nameplate_basis=True)
    with pytest.raises(ValueError, match="mutually exclusive"):
        _factors(df, _extract_basis_groups(True, False), cc_nameplate_basis=True)


def test_field_registered_and_default_off():
    assert ScenarioConfig().unit_outage_coal_extract_basis_share is False
    assert "unit_outage_coal_extract_basis_share" in _CACHE_KEY_OPTIONAL_FIELDS
    assert (
        _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["unit_outage_coal_extract_basis_share"]
        == "False"
    )
    base = ScenarioConfig()
    armed = base.with_overrides(unit_outage_coal_extract_basis_share=True)
    assert armed.unit_outage_coal_extract_basis_share is True
    assert base.cache_key() != armed.cache_key()
