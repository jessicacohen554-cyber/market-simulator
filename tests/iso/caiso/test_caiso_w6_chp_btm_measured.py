"""closeout-CAISO-w6: the measured CAISO CHP behind-the-meter share.

``caiso_chp_btm_measured`` replaces the sector-keyed CHP BTM default in the
capacity carve with the plant's own EIA-923 Schedules 6/7 on-site-use share
(pooled CY2022-2024). Off (the default), the carve never reads the artifact;
the flag is CAISO-scoped (rule 25).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from market_sim.config.paths import PROCESSED_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.chp import (
    chp_btm_measured_armed,
    measured_chp_btm_pct_caiso,
    measured_chp_btm_pct_for_iso,
)
from scripts.data.derive_caiso_chp_btm_share import derive

ARTIFACT = Path(PROCESSED_DIR) / "chp_btm_share_measured_CAISO.csv"


def _cfg(iso: str, **kw) -> ScenarioConfig:
    return ScenarioConfig(mode="backcast", iso=iso, **kw)


def test_off_by_default():
    """The shipping default never arms the measured carve."""
    assert ScenarioConfig().caiso_chp_btm_measured is False
    assert chp_btm_measured_armed(_cfg("CAISO")) is False


def test_flag_is_iso_scoped():
    """Each measured flag arms only its own ISO."""
    assert chp_btm_measured_armed(_cfg("CAISO", caiso_chp_btm_measured=True))
    assert not chp_btm_measured_armed(_cfg("NYISO", caiso_chp_btm_measured=True))
    assert not chp_btm_measured_armed(_cfg("ERCOT", caiso_chp_btm_measured=True))
    assert chp_btm_measured_armed(_cfg("NYISO", nyiso_chp_btm_measured=True))
    assert not chp_btm_measured_armed(_cfg("CAISO", nyiso_chp_btm_measured=True))


def test_no_artifact_for_other_isos():
    """ISOs without a measured artifact get an empty map (the default stands)."""
    assert measured_chp_btm_pct_for_iso("PJM") == {}


def _disposition(**over) -> pd.DataFrame:
    row = dict(
        year=2023,
        plant_id=1,
        plant_name="Host Cogen",
        plant_state="CA",
        sector_code=7,
        chp="Y",
        gross_mwh=1100.0,
        incoming_mwh=0.0,
        station_use_mwh=100.0,
        direct_use_mwh=0.0,
        retail_sales_mwh=0.0,
        sales_for_resale_mwh=0.0,
        tolling_mwh=0.0,
        outgoing_mwh=0.0,
    )
    row.update(over)
    return pd.DataFrame([row])


def test_derive_wholesale_is_grid_retail_is_host():
    """Grid = resale + tolling + outgoing over net; retail counts as host supply."""
    out = derive(
        _disposition(
            sales_for_resale_mwh=500.0, tolling_mwh=100.0, retail_sales_mwh=300.0
        ),
        {1},
    )
    assert out.loc[0, "grid_share"] == pytest.approx(0.6)
    assert out.loc[0, "btm_pct"] == pytest.approx(40.0)


def test_derive_clips_and_pools_and_scopes():
    """The share is clipped to [0, 100], pooled over 2022-24, and BA-scoped."""
    frames = pd.concat(
        [
            _disposition(year=2022, sales_for_resale_mwh=2000.0),
            _disposition(year=2023, sales_for_resale_mwh=0.0),
            _disposition(year=2019, sales_for_resale_mwh=0.0),
            _disposition(plant_id=2, sales_for_resale_mwh=0.0),
        ]
    )
    out = derive(frames, {1})
    assert list(out["plant_code"]) == [1]
    # pooled 2022+2023: grid 2000 / net 2000 -> share 1.0, BTM 0 (2019 excluded)
    assert out.loc[0, "years_pooled"] == "2022-2023"
    assert out.loc[0, "btm_pct"] == pytest.approx(0.0)


@pytest.mark.skipif(not ARTIFACT.exists(), reason="artifact not hydrated")
def test_artifact_refutes_the_sector_default():
    """The committed artifact carries the measured shares the design cites."""
    m = measured_chp_btm_pct_caiso()
    assert m[52109] > 95.0  # Richmond Cogen: refinery self-supply
    assert m[55084] < 10.0  # Crockett Cogen: sells ~all of its net
    assert 0.0 <= min(m.values()) and max(m.values()) <= 100.0
