"""R-ERCOT: year-matched heat-rate resolution for ERCOT's curated bin sheet.

AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24 §5.3.2 (b). Guards the
hierarchy (measured -> year-matched eGRID -> sheet -> class default) and that
the default call (no ``heat_rate_year``) is byte-identical to the sheet.
"""

from __future__ import annotations

import pandas as pd
import pytest

from market_sim.config.paths import CAMPD_BINS_CSV
from market_sim.data.fleet import campd_bins as cb


def _detail() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Plant_Code": [1, 2, 3, 4, 5],
            "Plant_Group": ["COAL_PRB", "CC_REGULAR", "CT_PEAKER", "CC_CHP", "ST_GAS"],
            "Plant_Avg_HR_MMBtu_MWh": [10.0, 7.0, float("nan"), 6.0, float("nan")],
        }
    )


def test_hierarchy_measured_then_egrid_then_sheet_then_default(monkeypatch):
    """Each row takes the first source that covers it, in the fixed order."""
    monkeypatch.setattr(cb, "measured_coal_heat_rates", lambda iso, y: {1: 11.0})
    monkeypatch.setattr(cb, "measured_cc_heat_rates", lambda iso, y: {})
    monkeypatch.setattr(cb, "measured_ct_heat_rates", lambda iso, y: {})
    monkeypatch.setattr(cb, "measured_st_heat_rates", lambda iso, y: {})
    monkeypatch.setattr(
        cb, "measured_chp_heat_rates", lambda iso, y: {(4, "CC_CHP"): 8.5}
    )
    import market_sim.data.egrid as eg

    def fake_resolve(codes, vintage):
        return pd.Series(
            [float("nan"), 7.3, float("nan"), 5.0, float("nan")], index=codes.index
        ), None

    monkeypatch.setattr(eg, "resolve_plant_heat_rates", fake_resolve)
    flags = {n: True for n in set(cb._BIN_GROUP_MEASURED_FAMILY.values())}
    hr, src = cb.resolve_bin_heat_rates(_detail(), "ERCOT", 2021, flags, True)
    assert list(src) == ["measured", "egrid", "default", "measured", "default"]
    assert hr[0] == 11.0 and hr[1] == 7.3 and hr[3] == 8.5
    assert hr[[2, 4]].isna().all()


def test_egrid_step_off_falls_to_sheet(monkeypatch):
    """With every flag off the sheet value survives untouched."""
    hr, src = cb.resolve_bin_heat_rates(_detail(), "ERCOT", 2021, {}, False)
    assert list(src) == ["sheet", "sheet", "default", "sheet", "default"]
    assert hr[0] == 10.0 and hr[1] == 7.0


@pytest.mark.skipif(not CAMPD_BINS_CSV.exists(), reason="bin sheet not hydrated")
def test_default_call_is_byte_identical_to_sheet():
    """No heat_rate_year -> the pre-R-ERCOT frame (forecast/tooling path)."""
    cb._CAMPD_BINS_CACHE.clear()
    a = cb.load_campd_bins(CAMPD_BINS_CSV)
    cb._CAMPD_BINS_CACHE.clear()
    b = cb.load_campd_bins(
        CAMPD_BINS_CSV,
        heat_rate_year=None,
        measured_flags={"measured_cc_heat_rates": True},
        egrid_year_match=True,
    )
    pd.testing.assert_frame_equal(a, b)


def _split_detail() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Plant_Code": [3470, 34702, 4939, 49392, 34520],
            "Plant_Name": [
                "W A Parish [COAL]",
                "W A Parish [ST]",
                "Barney M Davis [CC]",
                "Barney M Davis [ST]",
                "Ordinary Plant",
            ],
            "Plant_Group": ["COAL_PRB", "ST_GAS", "CC_REGULAR", "ST_GAS", "ST_GAS"],
            "Plant_Avg_HR_MMBtu_MWh": [10.76, 10.76, 7.0, 10.7, 12.0],
        }
    )


def test_split_child_parent_codes_needs_both_tags():
    """Only a tagged row whose code // 10 is a tagged row is a split child."""
    assert cb.split_child_parent_codes(_split_detail()) == {34702: 3470, 49392: 4939}
    assert cb.split_child_parent_codes(_detail()) == {}


def test_split_child_reads_parent_entry_of_its_own_family(monkeypatch):
    """R-ERCOT-11: a split child that misses on its own code reads its parent's
    entry in its own family's map; an untagged code never does."""
    monkeypatch.setattr(cb, "measured_coal_heat_rates", lambda iso, y: {3470: 10.5})
    monkeypatch.setattr(cb, "measured_cc_heat_rates", lambda iso, y: {4939: 7.8})
    monkeypatch.setattr(cb, "measured_ct_heat_rates", lambda iso, y: {})
    monkeypatch.setattr(
        cb, "measured_st_heat_rates", lambda iso, y: {3470: 11.6, 4939: 12.6, 3452: 9.9}
    )
    monkeypatch.setattr(cb, "measured_chp_heat_rates", lambda iso, y: {})
    flags = {n: True for n in set(cb._BIN_GROUP_MEASURED_FAMILY.values())}
    hr, src = cb.resolve_bin_heat_rates(_split_detail(), "ERCOT", 2022, flags, False)
    assert list(hr) == [10.5, 11.6, 7.8, 12.6, 12.0]
    assert list(src) == ["measured", "measured", "measured", "measured", "sheet"]
