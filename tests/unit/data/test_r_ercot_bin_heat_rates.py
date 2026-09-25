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
