"""NYISO-NEXT-23: ``nyiso_gas_flow_date`` places Transco Z6 NY prints on their flow days.

Reads the committed measured series ``data/raw/gas-prices/transco_z6_ny_daily.csv``
(the 2025-01-17 MLK-weekend print is the worked case).
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fuel import hubs
from market_sim.data.fuel.basis import nyiso as nyiso_basis

YEAR = 2025
JAN = slice(0, 31)


def _cfg(**kw) -> ScenarioConfig:
    return ScenarioConfig(iso="NYISO", mode="backcast", **kw)


def _daily(arr: np.ndarray) -> np.ndarray:
    return arr[: 365 * 24 : 24]


def test_off_is_inert():
    """Flag off: no flow series, no CT delta, so both consumers keep the trade-date path."""
    cfg = _cfg()
    assert hubs.nyiso_transco_z6_flow_daily(cfg, YEAR) is None
    assert nyiso_basis._z6_flow_minus_trade_hourly(cfg, YEAR, 8760) is None


def test_other_iso_is_inert():
    """The flag never reaches a non-NYISO config."""
    cfg = ScenarioConfig(iso="NEISO", mode="backcast", nyiso_gas_flow_date=True)
    assert hubs.nyiso_transco_z6_flow_daily(cfg, YEAR) is None


def test_friday_print_prices_its_weekend_package():
    """Trade Fri 1/17 ($97.90) flows Sat 1/18 - Tue 1/21 (MLK); Fri 1/17 takes Thu's trade."""
    flow = hubs.nyiso_transco_z6_flow_daily(_cfg(nyiso_gas_flow_date=True), YEAR)
    assert flow is not None and flow.shape == (365,)
    dated = hubs._transco_z6_daily_dated(hubs.TRANSCO_Z6_NY_DAILY_PATH)[YEAR][1]
    assert np.allclose(flow[17:21], dated[17])  # Jan 18..21 (0-based 17..20)
    assert flow[16] == pytest.approx(dated[16])  # Jan 17 <- trade Jan 16
    assert flow[21] == pytest.approx(dated[21])  # Jan 22 <- trade Jan 21


def test_hub_shape_stays_mean_preserving_and_moves_the_spike():
    """Armed: every January day differs, the month mean is unchanged, the spike moves to 1/18."""
    off = hubs._nyiso_hub_daily_gas_prices(_cfg(), YEAR)
    on = hubs._nyiso_hub_daily_gas_prices(_cfg(nyiso_gas_flow_date=True), YEAR)
    if off is None or on is None:
        pytest.skip("NYISO monthly hub series unavailable in this checkout")
    d_off, d_on = _daily(off)[JAN], _daily(on)[JAN]
    assert d_on.mean() == pytest.approx(d_off.mean(), rel=1e-12)
    assert int(np.argmax(d_off)) == 16  # trade date, Fri 1/17
    assert int(np.argmax(d_on)) == 17  # flow date, Sat 1/18
    assert np.allclose(d_on[17:21], d_on[17])  # one package, one price


def test_refuses_to_stack_with_gap_month_level():
    """Rule 19: both flags define the days no print sits on."""
    cfg = _cfg(nyiso_gas_flow_date=True, nyiso_hub_gap_month_level=True)
    with pytest.raises(ValueError, match="R-ONE-MECH"):
        hubs._nyiso_hub_daily_gas_prices(cfg, YEAR)


def test_ct_index_takes_the_flow_dated_commodity():
    """Armed CT delta: interpolated Z6 + delta == flow staircase on every day."""
    cfg = _cfg(nyiso_gas_flow_date=True)
    delta = nyiso_basis._z6_flow_minus_trade_hourly(cfg, YEAR, 8760)
    flow = hubs.nyiso_transco_z6_flow_daily(cfg, YEAR)
    assert delta is not None and delta.shape == (8760,)
    # 1/17 falls (spike leaves the trade day), 1/20 rises (it was priced by Friday's trade)
    assert _daily(delta)[16] < 0 < _daily(delta)[19]
    from scripts.lib.nyiso_downstate_gas import _daily_series, _interp_to_calendar
    import pandas as pd

    raw = pd.read_csv(hubs.TRANSCO_Z6_NY_DAILY_PATH)
    trade = _interp_to_calendar(_daily_series(raw, "transco_z6_ny_usd_mmbtu"), YEAR)
    trade = trade[~((trade.index.month == 2) & (trade.index.day == 29))].round(4)
    assert np.allclose(trade.to_numpy() + _daily(delta), flow)
