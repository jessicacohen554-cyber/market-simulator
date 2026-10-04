"""NWPP BAL-002-WECC requirement basis (session NWPP-NEXT-28, 2026-10-04).

``envelopes.nwpp_ba_contingency_basis`` sums each member BA's own measured load
and net generation into its model zone. Pins: (1) the key ships off; (2) the
member terms are the pool frame's own construction (sum of member demand IS the
pool's ``Demand (Adjusted)``), placed by ``_NWPP_BA_ZONES``; (3) a member whose
zone is not a model zone is refused rather than dropped.
"""

from __future__ import annotations

from unittest import mock

import numpy as np
import pytest

from market_sim.config.constants import HOURS_PER_YEAR

_ZONES = ["NWPP-NW", "NWPP-OR", "NWPP-INLAND", "NWPP-EAST", "NWPP-SNV"]


def test_default_off():
    from market_sim.config.scenarios import ScenarioConfig

    assert ScenarioConfig().nwpp_ba_contingency_reserve is False


def _fake_series():
    from market_sim.data.zone_assignment import _NWPP_BA_ZONES

    return {
        m: (np.full(HOURS_PER_YEAR, 100.0 + i), np.full(HOURS_PER_YEAR, -5.0 if i == 0 else 50.0))
        for i, m in enumerate(_NWPP_BA_ZONES)
    }


def test_members_land_in_their_zones():
    from market_sim.data.eia930 import envelopes
    from market_sim.data.zone_assignment import _NWPP_BA_ZONES

    series = _fake_series()
    with mock.patch(
        "market_sim.data.eia930.frames.pool_member_balance_series", return_value=series
    ):
        load, gen = envelopes.nwpp_ba_contingency_basis(2024, _ZONES)
    for z, zone in enumerate(_ZONES):
        members = [m for m, mz in _NWPP_BA_ZONES.items() if mz == zone]
        assert load[z, 0] == pytest.approx(sum(series[m][0][0] for m in members))
        # Negative net generation (a pumping / station-service hour) counts 0.
        assert gen[z, 0] == pytest.approx(sum(max(series[m][1][0], 0.0) for m in members))


def test_unknown_zone_refused():
    from market_sim.data.eia930 import envelopes

    with mock.patch(
        "market_sim.data.eia930.frames.pool_member_balance_series",
        return_value=_fake_series(),
    ):
        with pytest.raises(ValueError, match="not a model zone"):
            envelopes.nwpp_ba_contingency_basis(2024, _ZONES[:-1])


@pytest.mark.fulldata
def test_member_demand_sums_to_pool_frame():
    from market_sim.data.eia930.frames import _pool_hourly_frame, pool_member_balance_series

    series = pool_member_balance_series("NWPP", 2024)
    pool = _pool_hourly_frame("NWPP", 2024)
    if series is None or pool is None:
        pytest.skip("NWPP EIA-930 member extracts not hydrated")
    d = sum(v[0] for v in series.values())
    ng = sum(v[1] for v in series.values())
    np.testing.assert_allclose(d, pool["Demand (Adjusted)"].to_numpy(float))
    np.testing.assert_allclose(ng, pool["Net generation (Adjusted)"].to_numpy(float))
