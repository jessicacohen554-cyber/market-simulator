"""Tests for the real-data CF-profile path and the vendored shape logic.

Data-free: the "real" path is exercised against a tiny committed fixture
(``tests/fixtures/profiles/ERCOT_2024.parquet`` — one ISO, full 8760, three
resources), never the market-sim data tree, so CI needs no external data. The
synthetic path stays the default for ``iso="SAMPLE"``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from lce_portfolio.config import HOURS_PER_YEAR
from lce_portfolio.profiles import build_cf_matrix
from lce_portfolio.resources import ResourceArrays
from lce_portfolio.vendored.renewable_shapes import (
    capacity_weighted_collapse,
    derive_cf_profile,
    derive_offshore_wind_profile,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "profiles"


def _resources_with_storage() -> ResourceArrays:
    """Hand-built arrays: 3 real-shaped gens + firm clean + one storage row."""
    names = ["solar_pv", "onshore_wind", "offshore_wind", "geothermal", "battery_4h"]
    is_storage = np.array([False, False, False, False, True])
    return ResourceArrays(
        names=names,
        is_storage=is_storage,
        fixed_mwyr=np.zeros(5),
        vom=np.zeros(5),
        cap_max_mw=np.full(5, 1e6),
        cap_min_mw=np.zeros(5),
        cf_assumed=np.array([0.27, 0.35, 0.45, 0.90, 0.0]),
        duration_h=np.array([0.0, 0.0, 0.0, 0.0, 4.0]),
        rte=np.array([1.0, 1.0, 1.0, 1.0, 0.9]),
    )


# --- real-data path (fixture-backed) ---------------------------------------


def test_real_path_shape_and_bounds() -> None:
    """Fixture ISO returns an (n_res, 8760) matrix, all CF in [0, 1]."""
    res = _resources_with_storage()
    cf = build_cf_matrix(res, "ERCOT", 2024, profiles_dir=FIXTURE_DIR)
    assert cf.shape == (res.n_res, HOURS_PER_YEAR)
    assert cf.min() >= 0.0 and cf.max() <= 1.0


def test_real_path_storage_rows_zero() -> None:
    """Storage rows carry no CF ceiling (all-zero)."""
    res = _resources_with_storage()
    cf = build_cf_matrix(res, "ERCOT", 2024, profiles_dir=FIXTURE_DIR)
    for r in res.storage_idx:
        assert np.all(cf[r] == 0.0)


def test_real_path_solar_is_daytime_shaped() -> None:
    """Real solar row is zero at night and peaks midday (sanity of the shape)."""
    res = _resources_with_storage()
    cf = build_cf_matrix(res, "ERCOT", 2024, profiles_dir=FIXTURE_DIR)
    solar = cf[res.names.index("solar_pv")]
    hod = np.arange(HOURS_PER_YEAR) % 24
    night = solar[(hod < 4) | (hod > 22)].mean()
    noon = solar[(hod >= 11) & (hod <= 14)].mean()
    assert night < 0.02  # essentially dark
    assert noon > night + 0.2  # a real midday bump


def test_real_path_firm_clean_flat_at_cf() -> None:
    """A resource absent from the file (geothermal) stays flat at cf_assumed."""
    res = _resources_with_storage()
    cf = build_cf_matrix(res, "ERCOT", 2024, profiles_dir=FIXTURE_DIR)
    geo = cf[res.names.index("geothermal")]
    assert np.allclose(geo, 0.90)


def test_unknown_iso_falls_back_to_synthetic_with_warning() -> None:
    """A missing profile file warns and returns the synthetic matrix, not a crash."""
    res = _resources_with_storage()
    with pytest.warns(UserWarning, match="falling back to synthetic"):
        cf = build_cf_matrix(res, "NOWHERE", 2024, profiles_dir=FIXTURE_DIR)
    assert cf.shape == (res.n_res, HOURS_PER_YEAR)
    assert cf.min() >= 0.0 and cf.max() <= 1.0
    # synthetic solar is also daytime-shaped -> nonzero variance, storage zero.
    assert cf[res.names.index("solar_pv")].std() > 0.0
    for r in res.storage_idx:
        assert np.all(cf[r] == 0.0)


def test_sample_iso_uses_synthetic_without_touching_disk() -> None:
    """iso='SAMPLE' is always synthetic (no file lookup), even with a real dir."""
    res = _resources_with_storage()
    cf = build_cf_matrix(res, "SAMPLE", 2024, profiles_dir=FIXTURE_DIR)
    assert cf.shape == (res.n_res, HOURS_PER_YEAR)
    # Firm clean flat at its cf, storage zero — the synthetic contract.
    assert np.allclose(cf[res.names.index("geothermal")], 0.90)


# --- vendored capacity-weighted collapse (ADR 0011) ------------------------


def test_capacity_weighted_collapse_hand_computed() -> None:
    """2-zone collapse: cf_iso[t] = Σ cap[z]*cf[z,t] / Σ cap[z] (hand-checked)."""
    # Zone A: 3000 MW, flat 0.2. Zone B: 1000 MW, flat 0.6.
    zonal_cf = np.array([[0.2, 0.2, 0.2], [0.6, 0.6, 0.6]])
    cap = np.array([3000.0, 1000.0])
    # weighted mean = (3000*0.2 + 1000*0.6) / 4000 = (600 + 600)/4000 = 0.30
    got = capacity_weighted_collapse(zonal_cf, cap)
    assert np.allclose(got, 0.30)


def test_capacity_weighted_collapse_time_varying() -> None:
    """Weights apply per-hour, not just to the mean."""
    zonal_cf = np.array([[0.0, 1.0], [1.0, 0.0]])
    cap = np.array([1.0, 3.0])  # zone B four-times... actually 3:1
    # hour0: (1*0 + 3*1)/4 = 0.75 ; hour1: (1*1 + 3*0)/4 = 0.25
    got = capacity_weighted_collapse(zonal_cf, cap)
    assert np.allclose(got, [0.75, 0.25])


def test_capacity_weighted_collapse_zero_weight_falls_back_to_mean() -> None:
    """No capacity anywhere -> documented simple-mean fallback."""
    zonal_cf = np.array([[0.2, 0.4], [0.6, 0.8]])
    cap = np.array([0.0, 0.0])
    got = capacity_weighted_collapse(zonal_cf, cap)
    assert np.allclose(got, [0.4, 0.6])  # column means


def test_capacity_weighted_collapse_rejects_bad_shapes() -> None:
    """Guardrails: 1-D input and mismatched weight length both raise."""
    with pytest.raises(ValueError):
        capacity_weighted_collapse(np.array([0.1, 0.2]), np.array([1.0]))
    with pytest.raises(ValueError):
        capacity_weighted_collapse(np.zeros((2, 3)), np.array([1.0]))


# --- vendored pure functions (identical outputs, NOT via market_sim) -------


def test_derive_cf_profile_matches_hardcoded_expectation() -> None:
    """A normalized distribution scales to the target annual mean, clipped [0,1].

    Hand computation: a uniform distribution of ``1/T`` over ``T`` hours scaled
    by ``avg_cf * T`` yields a flat ``avg_cf`` series. A single spike above 1.0
    clips to 1.0.
    """
    T = 8760
    uniform = np.full(T, 1.0 / T)
    cf = derive_cf_profile(uniform, 0.35, T)
    assert np.allclose(cf, 0.35)
    assert abs(cf.mean() - 0.35) < 1e-12

    spike = np.zeros(4)
    spike[0] = 1.0  # sums to 1 over 4 "hours"
    # value*avg*T = 1 * 0.9 * 4 = 3.6 -> clips to 1.0 at the spike, 0 elsewhere.
    out = derive_cf_profile(spike, 0.9, 4)
    assert np.allclose(out, [1.0, 0.0, 0.0, 0.0])


def test_derive_offshore_wind_profile_properties() -> None:
    """Offshore derivation hits the target mean, smooths, and stays in [0,1]."""
    onshore = np.abs(np.sin(np.arange(240) / 3.0)) * 0.5  # deterministic, spiky
    off = derive_offshore_wind_profile(onshore, target_avg_cf=0.45)
    assert off.min() >= 0.0 and off.max() <= 1.0
    assert abs(off.mean() - 0.45) < 1e-9  # rescaled to the target mean
    # Smoothing reduces variability: normalize both to the same mean and compare.
    onshore_norm = onshore * (0.45 / onshore.mean())
    assert off.std() < onshore_norm.std()
