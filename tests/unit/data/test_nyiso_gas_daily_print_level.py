"""NYISO-NEXT-25: ``nyiso_gas_daily_print_level`` prices each day at its own Z6 print.

Reads the committed measured series ``data/raw/gas-prices/transco_z6_ny_daily.csv``
(January 2025, whose $97.90 MLK package print is the worked case).
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fuel import hubs

YEAR = 2025
JAN = slice(0, 31)


def _cfg(**kw) -> ScenarioConfig:
    return ScenarioConfig(iso="NYISO", mode="backcast", **kw)


def _jan(cfg: ScenarioConfig) -> np.ndarray:
    arr = hubs._nyiso_hub_daily_gas_prices(cfg, YEAR)
    if arr is None:
        pytest.skip("NYISO monthly hub series unavailable in this checkout")
    return arr[: 365 * 24 : 24][JAN]


@pytest.mark.parametrize("flow", [False, True])
def test_priced_day_is_level_times_print_over_trade_mean(flow):
    """Armed: a priced trading day equals hub_level * print / trade-day print mean."""
    on = _jan(_cfg(nyiso_gas_daily_print_level=True, nyiso_gas_flow_date=flow))
    monthly = hubs.iso_hub_monthly_gas_prices(_cfg(), YEAR)
    dated = hubs._transco_z6_daily_dated(hubs.TRANSCO_Z6_NY_DAILY_PATH)[YEAR][1]
    mean = float(np.mean(list(dated.values())))
    if not flow:
        # trade-date placement: Tue 1/7 carries its own print
        assert on[6] == pytest.approx(monthly[0] * dated[7] / mean, rel=1e-9)
    else:
        # flow-date placement: Tue 1/7's trade flows Wed 1/8
        assert on[7] == pytest.approx(monthly[0] * dated[7] / mean, rel=1e-9)


@pytest.mark.parametrize("flow", [False, True])
def test_spike_month_ordinary_days_rise_and_month_mean_rises(flow):
    """Off rescales Jan-2025 ordinary days by trade/calendar mean < 1; armed undoes it."""
    off = _jan(_cfg(nyiso_gas_flow_date=flow))
    on = _jan(_cfg(nyiso_gas_daily_print_level=True, nyiso_gas_flow_date=flow))
    ratio = on / off
    assert np.allclose(ratio, ratio[0])  # one month-wide factor, shape untouched
    assert ratio[0] > 1.2  # the MLK package inflates the calendar mean
    assert on.mean() > off.mean()


def test_off_is_byte_identical_default():
    """The default config and an explicit False build the same array."""
    a = hubs._nyiso_hub_daily_gas_prices(_cfg(), YEAR)
    b = hubs._nyiso_hub_daily_gas_prices(_cfg(nyiso_gas_daily_print_level=False), YEAR)
    if a is None:
        pytest.skip("NYISO monthly hub series unavailable in this checkout")
    assert np.array_equal(a, b, equal_nan=True)
