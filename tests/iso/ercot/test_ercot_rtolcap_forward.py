"""Tests for the ERCOT forward RTOLCAP/RTOFFCAP reserve-supply cap (WS-A).

Covers the four required behaviours (docs/handoffs/ercot-rtolcap-forward-2026-07.md):
trivial case first, formula responds to the net-load driver, backcast is
byte-identical with the flag off, and the coverage-ratio gate. The formula is a
pure function of forecast net-load + fleet capacity — it never reads the LP's own
commitment/output state (anti-F3/F4) and never a price (honesty gate).
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from market_sim.config.constants import (
    ERCOT_RTOLCAP_FWD_ONLINE_SHARE,
)
from market_sim.results.scarcity import (
    _ercot_rtolcap_fwd_decile,
    ercot_rtolcap_forward_supply_cap_mw,
    ercot_rtolcap_supply_cap_mw,
)


def _cfg(**kw):
    base = dict(
        mode="backcast",
        weather_year=2024,
        ercot_reserve_supply_cap=True,
        ercot_reserve_supply_forward=True,
        ercot_reserve_supply_cap_from_year=2023,
        ercot_multiproduct_as_coopt=True,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _fleet(groups, caps):
    return SimpleNamespace(
        plant_group=np.array(groups), pmax=np.array(caps, dtype=float)
    )


# --------------------------------------------------------------------------- #
# 1. Trivial case: 1 gen, 1 zone, 24 hours.
# --------------------------------------------------------------------------- #
def test_trivial_single_gen_24h():
    """One CC unit, flat net-load, 24 hours: a well-formed positive cap."""
    fleet = _fleet(["CC_REGULAR"], [1000.0])
    cfg = _cfg(ercot_multiproduct_as_coopt=False)  # single lumped product → 1 row
    net_load = np.full(24, 5000.0)
    cap = ercot_rtolcap_forward_supply_cap_mw(
        cfg, fleet, 24, net_load=net_load, storage_reserve=np.zeros(24)
    )
    assert cap.shape == (1, 24)
    assert np.all(cap >= 0.0)
    assert np.all(np.isfinite(cap))
    # A CC unit clears a fraction of its 1 GW as on-line headroom reserve.
    assert 0.0 < cap[0].mean() < 1000.0


def test_trivial_multiproduct_two_rows():
    """Multi-product stack: two rows, all-tier ≥ fast tier everywhere."""
    fleet = _fleet(["CC_REGULAR", "CT_PEAKER"], [1000.0, 500.0])
    cap = ercot_rtolcap_forward_supply_cap_mw(
        _cfg(), fleet, 24, net_load=np.full(24, 5000.0), storage_reserve=np.zeros(24)
    )
    assert cap.shape == (2, 24)
    # All tier (RTOLCAP + RTOFFCAP) is never below the fast tier (RTOLCAP).
    assert np.all(cap[1] >= cap[0] - 1e-9)


# --------------------------------------------------------------------------- #
# 2. Formula responds to the driver: tighter (higher net-load) → lower cap.
# --------------------------------------------------------------------------- #
def test_driver_response_tighter_lower_cap():
    """Higher-net-load (tight) hours get a strictly lower cap than loose hours.

    RTOLCAP is on-line headroom, so a tighter system (units more loaded) clears
    less reserve — the direction that makes scarcity fire on the tight evenings.
    """
    fleet = _fleet(["COAL", "CC_REGULAR", "CT_PEAKER"], [12700.0, 38700.0, 10200.0])
    rng = np.random.default_rng(0)
    net_load = rng.permutation(np.linspace(30000.0, 70000.0, 8760))
    cap = ercot_rtolcap_forward_supply_cap_mw(
        _cfg(), fleet, 8760, net_load=net_load, storage_reserve=np.zeros(8760)
    )
    tight = net_load > np.percentile(net_load, 90)
    loose = net_load < np.percentile(net_load, 10)
    assert cap[0][tight].mean() < cap[0][loose].mean()


def test_driver_response_not_constant():
    """The cap varies with net-load — it is not a degenerate flat series."""
    fleet = _fleet(["CC_REGULAR"], [10000.0])
    rng = np.random.default_rng(1)
    net_load = rng.permutation(np.linspace(20000.0, 60000.0, 8760))
    cap = ercot_rtolcap_forward_supply_cap_mw(
        _cfg(ercot_multiproduct_as_coopt=False),
        fleet,
        8760,
        net_load=net_load,
        storage_reserve=np.zeros(8760),
    )
    assert cap[0].std() > 0.0


def test_online_share_decreases_with_net_load():
    """The derived on-line share falls from low to high net-load for the big classes.

    Verified on the baked constant so a bad re-derivation that inverts the sign
    is caught. Checked on the capacity-dominant thermal classes (COAL,
    CC_REGULAR) whose headroom drives RTOLCAP; the CHP classes follow steam
    demand, not net-load, so they are not required to be monotone."""
    for cls in ("COAL", "CC_REGULAR"):
        tbl = np.array(ERCOT_RTOLCAP_FWD_ONLINE_SHARE[cls])  # (N_SEASON, N_DECILE)
        season_avg = tbl.mean(axis=0)
        # The low-net-load third holds more on-line headroom than the high third.
        assert season_avg[:3].mean() > season_avg[-3:].mean()


# --------------------------------------------------------------------------- #
# 3. Backcast byte-identical with the flag OFF (measured parquet unchanged).
# --------------------------------------------------------------------------- #
def test_backcast_flag_off_uses_measured():
    """Flag off + backcast → the measured cap; forward args do not perturb it."""
    pd = pytest.importorskip("pandas")
    from market_sim.config.paths import RAW_DATA_DIR

    path = RAW_DATA_DIR / "ercot" / "ercot_2024_ordc_reserves_hourly.parquet"
    if not path.exists():
        pytest.skip("measured ORDC reserves parquet not available")
    df = pd.read_parquet(path)
    rtol = df["rtolcap"].to_numpy(dtype=float)[:8760]
    rtoff = df["rtoffcap"].to_numpy(dtype=float)[:8760]
    exp0 = np.where(np.isnan(rtol), 1e9, rtol)
    exp1 = np.where(np.isnan(rtol + rtoff), 1e9, rtol + rtoff)

    cfg = _cfg(ercot_reserve_supply_forward=False)
    measured = ercot_rtolcap_supply_cap_mw(cfg, 8760)
    assert np.array_equal(measured[0], exp0)
    assert np.array_equal(measured[1], exp1)

    # Threading forward inputs must NOT change the measured backcast result.
    fleet = _fleet(["COAL"], [12700.0])
    with_args = ercot_rtolcap_supply_cap_mw(
        cfg,
        8760,
        fleet,
        system_load=np.full(8760, 50000.0),
        wind_gen=np.zeros(8760),
        solar_gen=np.zeros(8760),
    )
    assert np.array_equal(measured[0], with_args[0])


def test_forward_flag_selects_formula():
    """Flag on → the seam returns the formula (a different, driver-shaped cap)."""
    fleet = _fleet(["COAL", "CC_REGULAR", "CT_PEAKER"], [12700.0, 38700.0, 10200.0])
    rng = np.random.default_rng(2)
    system_load = rng.permutation(np.linspace(40000.0, 80000.0, 8760))
    cap = ercot_rtolcap_supply_cap_mw(
        _cfg(ercot_reserve_supply_forward=True),
        8760,
        fleet,
        system_load=system_load,
        wind_gen=np.full(8760, 15000.0),
        solar_gen=np.full(8760, 8000.0),
    )
    assert cap is not None and cap.shape[0] == 2
    assert cap[0].std() > 0.0  # driver-shaped, not the flat measured tail


def test_forward_missing_inputs_returns_none():
    """Forward path without the threaded inputs → None (co-opt runs uncapped)."""
    assert ercot_rtolcap_supply_cap_mw(_cfg(), 8760) is None


def test_cap_disabled_returns_none():
    """The whole lever gates on ercot_reserve_supply_cap."""
    fleet = _fleet(["COAL"], [12700.0])
    cfg = _cfg(ercot_reserve_supply_cap=False)
    assert (
        ercot_rtolcap_supply_cap_mw(
            cfg,
            24,
            fleet,
            system_load=np.full(24, 5e4),
            wind_gen=np.zeros(24),
            solar_gen=np.zeros(24),
        )
        is None
    )


# --------------------------------------------------------------------------- #
# 4. Coverage-ratio gate: RTOLCAP ÷ AS requirement ~2×, never the 1.0× artifact.
# --------------------------------------------------------------------------- #
def test_coverage_ratio_is_about_two_not_one():
    """A realistic fleet + net-load yields ~2× coverage of a ~7.5 GW AS need.

    The ercot27 exact-coverage artifact is a construction landing near 1.0×; the
    headroom-share construction must sit near 2× (the measured RTOLCAP-vs-AS-plan
    coverage), which is what makes reserve tighten without pinning to the need.
    """
    fleet = _fleet(
        ["COAL", "CC_REGULAR", "CC_CHP", "CT_PEAKER", "ST_GAS"],
        [12700.0, 29700.0, 9000.0, 8000.0, 10000.0],
    )
    rng = np.random.default_rng(3)
    net_load = rng.permutation(np.linspace(28000.0, 72000.0, 8760))
    cap = ercot_rtolcap_forward_supply_cap_mw(
        _cfg(), fleet, 8760, net_load=net_load, storage_reserve=np.full(8760, 2000.0)
    )
    as_requirement = 7500.0  # ~ measured ERCOT total up-AS (ASPLANNP433)
    coverage = np.median(cap[0] / as_requirement)
    assert coverage > 1.4, f"coverage {coverage:.2f}× — near the 1.0× artifact"
    assert coverage < 3.0, f"coverage {coverage:.2f}× — implausibly loose"


def test_decile_helper_monotone_and_bounded():
    """The net-load decile helper is a valid 0..N-1 rank bucket."""
    net_load = np.array([50.0, 10.0, 30.0, 90.0, 70.0] * 20)
    dec = _ercot_rtolcap_fwd_decile(net_load)
    assert dec.min() == 0
    assert dec.max() <= 9
    # The single lowest-net-load hour lands in the lowest bucket.
    assert dec[np.argmin(net_load)] == 0
