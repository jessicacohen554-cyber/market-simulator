"""closeout-CAISO-w8: CC_REGULAR econ tranches at the measured incremental HR.

``ScenarioConfig.cc_econ_incremental_hr`` scales a CC_REGULAR plant's econ
steps by its measured incremental/average heat-rate ratio
(``cc_incremental_hr_ratio_<ISO>.csv``). Contracts pinned here:

* OFF is byte-identical;
* ON, econ steps take the ratio ON TOP OF the band multiplier (bands unchanged);
* the committed tranche keeps the average (no-load fuel counted once, rule 19),
  and peak / must-run never move;
* only CC_REGULAR is touched;
* an ISO with no artifact is a no-op (rule 25).
"""

from __future__ import annotations

import pandas as pd
import pytest

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import bins_to_fleet
from market_sim.data.fleet.campd_bins import cc_incremental_hr_ratios

ISO = "CAISO"
ZONES = get_iso_config(ISO).zone_names
BASE_HR = 7.0
PALOMAR = 55985
BANDS = {
    "committed": 1.0,
    "econ_low": 1.066,
    "econ_high": 1.072,
    "peak": 1.386,
    "econ_low_share": 0.5,
}


def _bin(plant: int, group: str = "CC_REGULAR") -> dict:
    return {
        "Plant_Group": group,
        "ERCOT_Zone": ZONES[0],
        "Bin_Number": 1,
        "Bin_Label": f"TEST{plant}",
        "Plant_Code": plant,
        "Plant_Name": f"Test {plant}",
        "capacity_mw": 600.0,
        "hr_weighted": BASE_HR,
        "hr_mr": BASE_HR,
        "hr_mc": BASE_HR,
        "hr_econ": BASE_HR,
        "hr_peak": BASE_HR,
        "pct_mr": 0.0,
        "pct_mc": 30.0,
        "pct_econ": 62.0,
        "pct_peak": 8.0,
        "min_run": 0,
        "min_down": 0,
        "plant_count": 1,
        "plant_codes": [plant],
        "fuel": "gas",
    }


def _cfg(group: str = "CC_REGULAR", **kw) -> ScenarioConfig:
    return ScenarioConfig(
        iso=ISO, mode="backcast", offer_curve_by_group={group: dict(BANDS)}, **kw
    )


def _hrs(cfg: ScenarioConfig, plant: int = PALOMAR, group: str = "CC_REGULAR") -> dict:
    fleet, _ = bins_to_fleet(pd.DataFrame([_bin(plant, group)]), ZONES, cfg, year=2021)
    return {g.unit_id.rsplit("_", 1)[-1]: g.heat_rate for g in fleet}


@pytest.fixture(autouse=True)
def _needs_artifact():
    if not cc_incremental_hr_ratios(ISO, 2021):
        pytest.skip("cc_incremental_hr_ratio_CAISO.csv not hydrated")


def test_default_off_identical():
    assert ScenarioConfig().cc_econ_incremental_hr is False
    assert _hrs(_cfg()) == _hrs(_cfg(cc_econ_incremental_hr=False))


def test_on_scales_econ_only_keeps_committed_and_peak():
    off = _hrs(_cfg())
    on = _hrs(_cfg(cc_econ_incremental_hr=True))
    assert set(off) == set(on)
    econ = [k for k in on if k.startswith("econ")]
    assert econ, "no econ tranche built"
    lo, hi = cc_incremental_hr_ratios(ISO, 2021)[PALOMAR]
    for k in econ:
        r = on[k] / off[k]
        assert min(lo, hi) - 1e-9 <= r <= max(lo, hi) + 1e-9
    for k in on:
        if not k.startswith("econ"):
            assert on[k] == off[k], k  # committed (no-load once), peak untouched


def test_bands_are_kept_not_replaced():
    lo, _ = cc_incremental_hr_ratios(ISO, 2021)[PALOMAR]
    on = _hrs(_cfg(cc_econ_incremental_hr=True))
    off = _hrs(_cfg())
    first = sorted(k for k in on if k.startswith("econ"))[0]
    assert on[first] == pytest.approx(off[first] * lo)
    assert off[first] > BASE_HR  # the band multiplier is still in the base


def test_other_classes_untouched():
    cfg_on = _cfg("CC_CHP", cc_econ_incremental_hr=True)
    assert _hrs(cfg_on, group="CC_CHP") == _hrs(_cfg("CC_CHP"), group="CC_CHP")


def test_iso_without_artifact_is_noop():
    assert cc_incremental_hr_ratios("ERCOT", 2021) == {}
