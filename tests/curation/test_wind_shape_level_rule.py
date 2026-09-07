"""Tests for the shared per-zone wind-shape construction (``scripts/lib/wind_shape``).

These pin R-LEVEL — each zone's hourly series is the capacity-weighted mean over
its WHOLE operable fleet — and the property that makes it the right rule: the
construction is **partition-consistent**, so re-cutting one zone's boundary
cannot move any other zone's redistribution weight. That is the defect
``docs/handoffs/FINDING-spp-54-2026-09-07.md`` §4.2 (C-4) measured under the old
six-largest-plants sampling rule, and the reason SPP-54's C-3 stopped at h8509.

Every test here is offline: the reanalysis fetch is replaced by a deterministic
synthetic wind field, so nothing touches NASA POWER or the network.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from scripts.lib import wind_shape  # noqa: E402

# One plant per row: (lat, lon, nameplate MW, hub height m). The capacities are
# deliberately unequal and unequally distributed between the two halves so a
# size-selected subsample would give a different level than the whole fleet.
_FLEET_A: list[tuple[float, float, float, float]] = [
    (35.0, -101.0, 300.0, 100.0),
    (35.5, -101.5, 40.0, 80.0),
    (36.0, -102.0, 25.0, 80.0),
]
_FLEET_B: list[tuple[float, float, float, float]] = [
    (39.0, -99.0, 250.0, 95.0),
    (39.5, -99.5, 120.0, 85.0),
    (40.0, -100.0, 15.0, 80.0),
]


def _synthetic_speed(lat: float, lon: float, year: int, **_kwargs) -> pd.Series:
    """Return a deterministic, location-dependent 50 m wind-speed series.

    Stands in for :func:`scripts.lib.wind_shape.fetch_nasa_power_ws50m` so the
    tests are offline and reproducible. The field varies with both latitude and
    hour so that different plants really do carry different levels and different
    diurnal shapes — otherwise the partition test would pass trivially.

    Args:
        lat: Latitude (deg N).
        lon: Longitude (deg E).
        year: Model calibration year (selects the UTC index).
        **_kwargs: Ignored (the real fetch takes a ``cache_dir``).

    Returns:
        Hourly wind speed (m/s) indexed by UTC timestamp.
    """
    idx = pd.date_range(f"{year}-01-01", periods=HOURS_PER_YEAR, freq="h")
    hod = np.arange(HOURS_PER_YEAR) % 24
    base = 5.0 + 0.25 * (lat - 35.0) + 0.1 * (lon + 101.0)
    diurnal = 2.0 * np.sin(2 * np.pi * (hod + lat) / 24.0)
    seasonal = 1.5 * np.cos(2 * np.pi * np.arange(HOURS_PER_YEAR) / HOURS_PER_YEAR)
    return pd.Series(np.clip(base + diurnal + seasonal, 0.0, None), index=idx)


@pytest.fixture()
def offline_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the reanalysis fetch with the deterministic synthetic field."""
    monkeypatch.setattr(wind_shape, "fetch_nasa_power_ws50m", _synthetic_speed)


@pytest.fixture()
def utc_index() -> pd.DatetimeIndex:
    """Return a plain 8760-hour UTC clock for the synthetic year."""
    return pd.DatetimeIndex(
        pd.date_range("2024-01-01", periods=HOURS_PER_YEAR, freq="h")
    )


def _direct_fleet_cf(
    fleet: list[tuple[float, float, float, float]],
    utc_index: pd.DatetimeIndex,
    year: int,
) -> np.ndarray:
    """Compute a zone's capacity-weighted fleet CF straight from the definition.

    Deliberately does not reuse :func:`scripts.lib.wind_shape.build_zone_shape`,
    so the test compares the builder against the written rule rather than
    against itself.

    Args:
        fleet: ``(lat, lon, cap_mw, hub_m)`` per plant.
        utc_index: The model clock.
        year: Model calibration year.

    Returns:
        The ``(HOURS_PER_YEAR,)`` capacity-weighted fleet capacity factor.
    """
    num = np.zeros(HOURS_PER_YEAR)
    den = 0.0
    for lat, lon, cap, hub in fleet:
        speed = _synthetic_speed(lat, lon, year).reindex(utc_index).to_numpy()
        num += cap * wind_shape.power_curve_cf(wind_shape.hub_height_speed(speed, hub))
        den += cap
    return num / den


def test_zone_shape_is_the_capacity_weighted_fleet_cf(offline_fetch, utc_index) -> None:
    """P1: the built series IS the zone's capacity-weighted fleet CF.

    Under R-LEVEL there is no subsample and no size selection, so the per-zone
    level bias is 1 by construction rather than by identification.
    """
    built = wind_shape.build_zone_shape(_FLEET_A, utc_index, 2024, cache_dir=None)
    assert built is not None
    np.testing.assert_allclose(
        built, _direct_fleet_cf(_FLEET_A, utc_index, 2024), rtol=0.0, atol=1e-15
    )


def test_partition_consistency(offline_fetch, utc_index) -> None:
    """P2: splitting a zone leaves every other zone's weight untouched.

    With ``C_z = Σ_{i∈z} cap_i``, zones ``A`` and ``B`` partitioning an old zone
    ``C`` over the same plant set must satisfy, in every hour,

        ``C_A·SHAPE_A(t) + C_B·SHAPE_B(t) == C_C·SHAPE_C(t)``

    because the redistribution weights each zone by ``cap_z·SHAPE_z``. This is
    the identity the old six-largest-plants rule violated — ``top-6(A) ∪
    top-6(B) ≠ top-6(A ∪ B)`` — which is how a boundary change confined to the
    south moved SPP-North's annual potential by 1.4–1.9 TWh at an identical
    system total (FINDING-spp-54 §4.2 C-4).
    """
    shape_a = wind_shape.build_zone_shape(_FLEET_A, utc_index, 2024, cache_dir=None)
    shape_b = wind_shape.build_zone_shape(_FLEET_B, utc_index, 2024, cache_dir=None)
    shape_c = wind_shape.build_zone_shape(
        _FLEET_A + _FLEET_B, utc_index, 2024, cache_dir=None
    )
    cap_a = sum(p[2] for p in _FLEET_A)
    cap_b = sum(p[2] for p in _FLEET_B)
    split = cap_a * shape_a + cap_b * shape_b
    whole = (cap_a + cap_b) * shape_c
    assert np.max(np.abs(split - whole) / np.maximum(whole, 1e-12)) <= 1e-12


def test_six_largest_sampling_would_violate_partition_consistency(
    offline_fetch, utc_index
) -> None:
    """The counterfactual: the retired rule fails P2, and by how much.

    Guards against a silent re-introduction of size-selected sampling — if some
    later change made the two constructions agree, this test would fail and say
    so. Six is the retired ``_SAMPLES_PER_ZONE``; the fleets here are three
    plants each, so the subsample is taken at two per zone to reproduce the same
    selection effect on a small fixture.
    """

    def top_k(fleet, k):
        return sorted(fleet, key=lambda p: -p[2])[:k]

    def sampled(fleet, k):
        sub = top_k(fleet, k)
        shape = wind_shape.build_zone_shape(sub, utc_index, 2024, cache_dir=None)
        return sum(p[2] for p in fleet) * shape  # zone weight uses FULL capacity

    split = sampled(_FLEET_A, 2) + sampled(_FLEET_B, 2)
    whole = sampled(_FLEET_A + _FLEET_B, 2)
    rel = np.max(np.abs(split - whole) / np.maximum(whole, 1e-12))
    assert rel > 1e-3, "the retired sampling rule must NOT be partition-consistent"


def test_level_rule_moves_the_level_not_only_the_shape(
    offline_fetch, utc_index
) -> None:
    """The defect in one assertion: sampling changes a zone's LEVEL, which is read.

    ``_redistribute_preserving_total`` weights each zone by ``cap_z·SHAPE_z``, so
    a per-zone level shift is a per-zone share shift. Here the whole-fleet mean
    and the two-largest-plants mean differ materially — that difference was an
    unidentified free parameter multiplying the split.
    """
    whole = wind_shape.build_zone_shape(_FLEET_A, utc_index, 2024, cache_dir=None)
    sub = wind_shape.build_zone_shape(
        sorted(_FLEET_A, key=lambda p: -p[2])[:2], utc_index, 2024, cache_dir=None
    )
    assert abs(float(whole.mean()) / float(sub.mean()) - 1.0) > 1e-4


def test_empty_zone_returns_none(offline_fetch, utc_index) -> None:
    """A zone with no operable wind plant yields ``None`` (the caller fills it)."""
    assert wind_shape.build_zone_shape([], utc_index, 2024, cache_dir=None) is None


def test_cache_round_trip_changes_no_value(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, utc_index: pd.DatetimeIndex
) -> None:
    """P7: the reanalysis memo is policy-free — warm output equals cold output.

    The first call goes to the (stubbed) API and writes the memo; the second
    reads the memo with the API stub disarmed, and the two series must agree
    exactly.
    """
    calls: list[tuple[float, float, int]] = []

    def fake_get(url, params, timeout):  # noqa: ANN001, ANN202 — requests stub
        calls.append((float(params["latitude"]), float(params["longitude"]), 2024))
        idx = pd.date_range("2024-01-01", periods=48, freq="h")
        block = {t.strftime("%Y%m%d%H"): 4.0 + i * 0.1 for i, t in enumerate(idx)}

        class _Resp:
            @staticmethod
            def raise_for_status() -> None:
                return None

            @staticmethod
            def json() -> dict:
                return {"properties": {"parameter": {"WS50M": block}}}

        return _Resp()

    monkeypatch.setattr(wind_shape.requests, "get", fake_get)
    cold = wind_shape.fetch_nasa_power_ws50m(35.0, -101.0, 2024, cache_dir=tmp_path)
    assert len(calls) == 1

    def boom(*_a, **_k):  # noqa: ANN002, ANN003, ANN202
        raise AssertionError("warm read must not hit the API")

    monkeypatch.setattr(wind_shape.requests, "get", boom)
    warm = wind_shape.fetch_nasa_power_ws50m(35.0, -101.0, 2024, cache_dir=tmp_path)
    pd.testing.assert_series_equal(cold, warm)


def test_cache_key_separates_distinct_requests(tmp_path: Path) -> None:
    """Distinct point-years must never share a memo entry."""
    seen = {
        wind_shape._cache_path(lat, lon, yr, tmp_path)
        for lat, lon, yr in (
            (35.0, -101.0, 2024),
            (35.0, -101.0, 2025),
            (35.1, -101.0, 2024),
            (35.0, -101.1, 2024),
        )
    }
    assert len(seen) == 4


def test_sampling_knob_is_gone() -> None:
    """Rule 26 ``[R-DELETE]``: no sample-count knob survives anywhere.

    A zeroed or renamed sample cap would be a re-armable answer key for exactly
    the channel R-LEVEL closes, so the constant is deleted rather than raised.
    """
    for module in ("scripts/lib/wind_shape.py",):
        assert "_SAMPLES_PER_ZONE" not in (REPO / module).read_text()
    for builder in (
        "scripts/data/build_spp_wind_shape.py",
        "scripts/data/build_miso_wind_shape.py",
    ):
        text = (REPO / builder).read_text()
        assert "_SAMPLES_PER_ZONE" not in text
        assert "samples-per-zone" not in text
        assert "nlargest" not in text


def test_physics_constants_are_shared_and_unchanged() -> None:
    """The repair touches the level rule only — the physics is byte-unchanged.

    The shear exponent, reference height, hub-height default and power-curve
    breakpoints are shared across ISOs by intent (rule 21 ``[R-DOF]``); a
    per-ISO value would be an unmotivated degree of freedom.
    """
    assert wind_shape.SHEAR_EXPONENT == pytest.approx(1.0 / 7.0)
    assert wind_shape.REANALYSIS_HEIGHT_M == 50.0
    assert wind_shape.DEFAULT_HUB_HEIGHT_M == 90.0
    assert (wind_shape.CUT_IN_MS, wind_shape.RATED_MS, wind_shape.CUT_OUT_MS) == (
        3.0,
        12.0,
        25.0,
    )


def test_shared_module_names_no_iso() -> None:
    """Rule 25 ``[R-ISO-SCOPE]``: no ISO's number can reach another through it.

    The shared construction must carry no ISO name, no per-ISO constant and no
    ISO branch — every ISO-specific quantity is resolved from that ISO's own
    registry entry and its own EIA-860 rows.
    """
    code = "\n".join(
        line
        for line in (REPO / "scripts/lib/wind_shape.py").read_text().splitlines()
        if not line.lstrip().startswith("#")
    )
    body = code.split('"""', 2)[-1]  # drop the module docstring, which cites ISOs
    for iso in ("SPP", "MISO", "ERCOT", "CAISO", "PJM", "NYISO", "NEISO"):
        assert iso not in body, f"{iso} must not appear in the shared construction"
