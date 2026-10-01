"""Tests for the NWPP-NEXT-14 combined-cycle physical floor on eGRID plant heat rates.

``ScenarioConfig.cc_subfloor_eia923_heat_rates`` arms
``data/fleet/eia860.py::_apply_cc_subfloor_eia923_hr``: a combined-cycle part
(prime mover CT / CA / CS / CC) whose plant-grain eGRID rate sits below
``EGRID_CC_HR_PHYSICAL_FLOOR`` takes the plant's own EIA-923 CC prime-mover rate,
and the floor only where that measured rate is unusable. Trivial frames first,
then the committed EIA-923 filing at Clark 2322.
"""

from __future__ import annotations

import pandas as pd
import pytest

import market_sim.data.fleet.eia860 as e860
from market_sim.config.constants import (
    EGRID_CC_HR_PHYSICAL_CEILING,
    EGRID_CC_HR_PHYSICAL_FLOOR,
    HEAT_RATE_BINS,
)
from market_sim.config.scenarios import ScenarioConfig


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "plant_id": [1, 1, 1, 2, 3, 4, 5],
            "prime_mover": ["CT", "CA", "GT", "CT", "GT", "CT", "CT"],
            "heat_rate": [3.0, 3.0, 3.0, 3.0, 3.0, 7.1, 3.0],
            "chp": ["N", "N", "N", "Y", "N", "N", "N"],
        }
    )


def test_floor_is_the_cited_h_class_bin():
    """An alias of an existing cited constant, no new number."""
    assert EGRID_CC_HR_PHYSICAL_FLOOR == HEAT_RATE_BINS["gas_cc"]["h_class"]
    assert EGRID_CC_HR_PHYSICAL_FLOOR < EGRID_CC_HR_PHYSICAL_CEILING


def test_default_off():
    assert ScenarioConfig().cc_subfloor_eia923_heat_rates is False


def test_cc_parts_take_the_measured_rate(monkeypatch):
    """Only non-CHP CC-part rows below the floor move; GT rows are SPP-49's."""
    monkeypatch.setattr(
        e860, "eia923_cc_prime_mover_heat_rates", lambda year=None: {1: 9.4, 5: 30.0}
    )
    df = _frame()
    out = e860._apply_cc_subfloor_eia923_hr(df, 2023)
    assert list(out["heat_rate"]) == [
        9.4,  # plant 1 CT: measured
        9.4,  # plant 1 CA: measured (same CC block)
        3.0,  # plant 1 GT: not a CC part
        3.0,  # plant 2: CHP, owned by the CHP chain
        3.0,  # plant 3: all-GT, the simple-cycle floor's object
        7.1,  # plant 4: above the floor
        EGRID_CC_HR_PHYSICAL_FLOOR,  # plant 5: measured outside the band
    ]
    assert list(df["heat_rate"]) == [3.0, 3.0, 3.0, 3.0, 3.0, 7.1, 3.0]  # not mutated


def test_missing_measured_rate_falls_back_to_the_floor(monkeypatch):
    monkeypatch.setattr(e860, "eia923_cc_prime_mover_heat_rates", lambda year=None: {})
    out = e860._apply_cc_subfloor_eia923_hr(_frame(), None)
    assert out.loc[0, "heat_rate"] == EGRID_CC_HR_PHYSICAL_FLOOR


def test_frame_without_columns_is_unchanged():
    df = pd.DataFrame({"plant_id": [1], "heat_rate": [3.0]})
    assert e860._apply_cc_subfloor_eia923_hr(df) is df


def test_clark_eia923_cc_rate():
    """Clark 2322's own EIA-923 CC fuel over CC net (CT + CA), 2023 and pooled."""
    rates = e860.eia923_cc_prime_mover_heat_rates(2023)
    if 2322 not in rates:
        pytest.skip("EIA-923 generation-fuel file not hydrated")
    assert rates[2322] == pytest.approx(4100891 / (297245 + 135539), rel=1e-6)
    pooled = e860.eia923_cc_prime_mover_heat_rates(None)[2322]
    assert EGRID_CC_HR_PHYSICAL_FLOOR <= pooled <= EGRID_CC_HR_PHYSICAL_CEILING
