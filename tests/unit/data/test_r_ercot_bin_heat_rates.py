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


def _gt_split_detail() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Plant_Code": [3469, 34693, 7900, 79003, 56350, 563503],
            "Plant_Name": [
                "T H Wharton [CC]",
                "T H Wharton [CT]",
                "Sand Hill [CC]",
                "Sand Hill [CT]",
                "Colorado Bend Energy Center [CC]",
                "Colorado Bend Energy Center [CT]",
            ],
            "Plant_Group": ["CC_REGULAR", "CT_PEAKER"] * 3,
            "Plant_Avg_HR_MMBtu_MWh": [12.99, 16.49, 7.37, 10.04, 8.02, 14.19],
        }
    )


def test_gt_split_children_read_parent_ct_entry(monkeypatch):
    """R-ERCOT-20: a CC site's simple-cycle GT child (digit 3) reads its
    parent's MEASURED CT rate (keyed by the CAMPD facility); the CC parent keeps
    its own family's resolution."""
    assert cb.split_child_parent_codes(_gt_split_detail()) == {
        34693: 3469,
        79003: 7900,
        563503: 56350,
    }
    monkeypatch.setattr(cb, "measured_coal_heat_rates", lambda iso, y: {})
    monkeypatch.setattr(cb, "measured_cc_heat_rates", lambda iso, y: {7900: 7.2})
    monkeypatch.setattr(
        cb,
        "measured_ct_heat_rates",
        lambda iso, y: {3469: 13.35, 7900: 10.03, 56350: 14.33},
    )
    monkeypatch.setattr(cb, "measured_st_heat_rates", lambda iso, y: {})
    monkeypatch.setattr(cb, "measured_chp_heat_rates", lambda iso, y: {})
    flags = {n: True for n in set(cb._BIN_GROUP_MEASURED_FAMILY.values())}
    hr, src = cb.resolve_bin_heat_rates(_gt_split_detail(), "ERCOT", 2024, flags, False)
    assert list(hr) == [12.99, 13.35, 7.2, 10.03, 8.02, 14.33]
    assert list(src) == [
        "sheet",
        "measured",
        "measured",
        "measured",
        "sheet",
        "measured",
    ]


@pytest.mark.skipif(not CAMPD_BINS_CSV.exists(), reason="bin sheet not hydrated")
def test_gt_split_rows_sum_to_eia860_plant_nameplate():
    """R-ERCOT-20: parent (CA+CT) + child (GT) = the pre-split sheet nameplate,
    i.e. EIA-860 operable nameplate by prime mover (vintage 2024)."""
    s = pd.read_csv(CAMPD_BINS_CSV).set_index("Plant_Code")["Nameplate_MW"]
    for parent, child, cc, gt, whole in (
        (3469, 34693, 663.6, 526.3, 1189.9),
        (7900, 79003, 388.0, 308.4, 696.4),
        (56350, 563503, 580.1, 74.0, 654.1),
    ):
        assert s[parent] == pytest.approx(cc) and s[child] == pytest.approx(gt)
        assert s[parent] + s[child] == pytest.approx(whole, abs=0.05)


def test_gt_split_outage_routing_drops_site_gts():
    """R-ERCOT-20: co-sited simple-cycle GTs (tagged CC_REGULAR in the outage
    extracts) are dropped at routing like every CT; the CC units still route
    to the CC parent."""
    from market_sim.data.outages import _unit_outage_target

    assert _unit_outage_target(3469, "THW51", "CC_REGULAR") is None
    assert _unit_outage_target(7900, "SH6", "CC_REGULAR") is None
    assert _unit_outage_target(56350, "CT-4A", "CC_REGULAR") is None
    assert _unit_outage_target(3469, "THW31", "CC_REGULAR") == (3469, "CC_REGULAR")
    assert _unit_outage_target(7900, "SH5", "CC_REGULAR") == (7900, "CC_REGULAR")
    assert _unit_outage_target(56350, "CT1A", "CC_REGULAR") == (56350, "CC_REGULAR")
