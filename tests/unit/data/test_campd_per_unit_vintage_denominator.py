"""Tests for the NWPP-NEXT-14 vintage denominator of the per-unit tranche companion.

``ScenarioConfig.campd_per_unit_vintage_denominator`` is a sub-gate of
``campd_per_unit_attribution``: armed together they select
``thermal_tranches-perunit-vintage-<ISO>.csv``, written by
``derive_thermal_tranches.py --per-unit-attribution --vintage-denominator``.
Trivial cases first (the selector, the path resolver), then the committed NWPP
companion: it must differ from the ``-perunit-`` companion only in rows whose
bin nameplate moves across the 2023-2025 EIA-860 vintages.
"""

from __future__ import annotations

import pandas as pd
import pytest

import market_sim.data.fleet.campd_bins as cb
from market_sim.config.scenarios import ScenarioConfig
from tests.helpers import REPO_ROOT

PROC = REPO_ROOT / "data" / "raw" / "_processed-legacy"
PERUNIT = PROC / "thermal_tranches-perunit-NWPP.csv"
VINTAGE = PROC / "thermal_tranches-perunit-vintage-NWPP.csv"


def test_selector_is_a_sub_gate_of_per_unit_attribution():
    """The tag needs per-unit attribution; alone the flag is inert."""
    assert cb.campd_fuel_split_selector(ScenarioConfig()) is False
    assert (
        cb.campd_fuel_split_selector(
            ScenarioConfig(campd_per_unit_vintage_denominator=True)
        )
        is False
    )
    assert (
        cb.campd_fuel_split_selector(ScenarioConfig(campd_per_unit_attribution=True))
        is False
    )
    armed = ScenarioConfig(
        campd_per_unit_attribution=True, campd_per_unit_vintage_denominator=True
    )
    assert cb.campd_fuel_split_selector(armed) == cb.PER_UNIT_VINTAGE_TAG


def test_selector_refuses_the_merit_guard():
    """No merit-guarded vintage companion exists, so the pair raises."""
    cfg = ScenarioConfig(
        campd_per_unit_attribution=True,
        campd_per_unit_vintage_denominator=True,
        campd_outage_merit_order_guard=True,
    )
    with pytest.raises(ValueError, match="merit_order_guard"):
        cb.campd_fuel_split_selector(cfg)


def test_path_resolver_selects_and_falls_back():
    """NWPP resolves the vintage companion; an ISO without one keeps -perunit-."""
    tag = cb.PER_UNIT_VINTAGE_TAG
    assert cb.thermal_tranche_csv_for_iso("NWPP", True, False, tag) == VINTAGE
    assert cb.thermal_tranche_csv_for_iso("NWPP", True, False, False) == PERUNIT
    assert cb.thermal_tranche_csv_for_iso("NWPP", False, False, tag) == (
        PROC / "thermal_tranches_NWPP.csv"
    )
    nyiso = cb.thermal_tranche_csv_for_iso("NYISO", True, False, tag)
    assert nyiso == cb.thermal_tranche_csv_for_iso("NYISO", True, False, False)


def test_fuel_split_readers_treat_the_tag_as_no_split():
    """The by-year / p25 / oom readers keep their own artifact under the tag."""
    base = PROC / "thermal_tranches_online_frac_by_year_NWPP.csv"
    assert cb._fuel_split_companion(base, cb.PER_UNIT_VINTAGE_TAG) == base


def test_committed_nwpp_companion_moves_only_vintage_rows():
    """Only bins whose nameplate differs across 2023-2025 vintages move."""
    a = pd.read_csv(PERUNIT).set_index(["plant_code", "plant_group"])
    b = pd.read_csv(VINTAGE).set_index(["plant_code", "plant_group"])
    assert list(a.index) == list(b.index)
    cols = [c for c in a.columns if c != "name"]
    moved = {
        k
        for k in a.index
        if not a.loc[k, cols].fillna(-1).equals(b.loc[k, cols].fillna(-1))
    }
    assert moved == {
        (7605, "CC_REGULAR"),
        (7953, "CT_PEAKER"),
        (8066, "COAL"),
        (8224, "COAL"),
        (55179, "CC_REGULAR"),
        (55733, "CT_PEAKER"),
        (57028, "CC_REGULAR"),
    }
    # The two coal conversions: the row nameplate is the largest vintage bin.
    assert b.loc[(8066, "COAL"), "nameplate_mw"] == 2119.0
    assert b.loc[(8224, "COAL"), "nameplate_mw"] == 522.0
    assert b.loc[(8224, "COAL"), "mustrun_pct"] == 24.5
    # CHP rows are byte-identical, so the CHP-only readers (which take no
    # selector) cannot mix two artifacts inside one LP.
    chp = [k for k in a.index if k[1] in ("CC_CHP", "CT_CHP", "ST_CHP")]
    assert chp and not (moved & set(chp))
