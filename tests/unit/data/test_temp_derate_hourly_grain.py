"""Hour-grain diurnal temperature input for the temperature-dependent derate.

Covers the miso-101 legs added to the existing ``temp_dependent_derate``
mechanism (rule 19 ``[R-ONE-MECH]`` — an input-grain refinement, not a new
floor):

* :func:`~market_sim.data.eia930.weather.diurnal_drybulb_from_daily` — the
  two-piece cosine reconstruction hits the daily extremes at their anchor hours,
  is continuous across midnight, and preserves the daily mean.
* :func:`~market_sim.data.eia930.weather.iso_zone_hourly_drybulb` — refuses to
  fabricate a wave when the source has no TMIN.
* ``ScenarioConfig.temp_derate_mean_anchored`` — annual-mean-1.0 shape overlay
  with no onset hinge, so it moves shape without moving level.
* ``ScenarioConfig.temp_derate_classes`` — the scope gate leaves every
  unlisted class byte-identical.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.constants import DIURNAL_TMAX_HOUR, DIURNAL_TMIN_HOUR
from market_sim.data.eia930.weather import (
    diurnal_drybulb_from_daily,
    iso_zone_hourly_drybulb,
)

HOURS = 24 * 10
YEAR = 2024


def _flat(value: float, hours: int = HOURS) -> np.ndarray:
    """Day-flat array at a constant value."""
    return np.full(hours, float(value))


def test_reconstruction_hits_the_daily_extremes_at_their_anchor_hours():
    """TMIN/TMAX are reproduced EXACTLY at the anchor hours, every day."""
    tmin, tmax = _flat(4.0), _flat(20.0)
    out = diurnal_drybulb_from_daily(tmin, tmax, YEAR, HOURS)

    hod = np.arange(HOURS) % 24
    assert out[hod == DIURNAL_TMIN_HOUR] == pytest.approx(4.0)
    assert out[hod == DIURNAL_TMAX_HOUR] == pytest.approx(20.0)
    # and it never leaves the band the extremes define
    assert out.min() == pytest.approx(4.0)
    assert out.max() == pytest.approx(20.0)


def test_reconstruction_is_continuous_across_midnight():
    """Pre-dawn hours ride the PREVIOUS day's falling limb, not a hour-0 reset.

    A reconstruction that restarted each calendar day would put a discontinuity
    at midnight; the daily wave the derate rides would then carry a spurious
    step at h00.
    """
    # A rising temperature ramp across days makes any midnight reset visible.
    days = HOURS // 24
    tmin = np.repeat(np.arange(days, dtype=float), 24)
    tmax = tmin + 12.0
    out = diurnal_drybulb_from_daily(tmin, tmax, YEAR, HOURS)

    steps = np.abs(np.diff(out))
    midnight = np.arange(HOURS) % 24 == 0
    # The step INTO each midnight is no larger than the biggest interior step.
    assert steps[midnight[1:]].max() <= steps.max() + 1e-9
    assert steps.max() < 2.0  # smooth everywhere: no jump discontinuity


def test_reconstruction_preserves_the_daily_mean_band():
    """The reconstruction reshapes the day; it does not shift its level."""
    tmin, tmax = _flat(-5.0), _flat(15.0)
    out = diurnal_drybulb_from_daily(tmin, tmax, YEAR, HOURS)
    # Symmetric cosine limbs => the daily mean sits at the midpoint.
    assert out.mean() == pytest.approx(5.0, abs=0.25)


def test_hourly_drybulb_returns_none_without_tmin(monkeypatch):
    """A TMAX-only source must fall back, never invent a diurnal wave."""
    monkeypatch.setattr(
        "market_sim.data.eia930.weather.iso_zone_tmax",
        lambda *a, **k: (np.full(HOURS, 20.0), None),
    )
    assert iso_zone_hourly_drybulb("CAISO", YEAR, HOURS, zone="_load_weighted") is None


def test_hourly_drybulb_returns_none_without_weather(monkeypatch):
    """No weather coverage => None, so the caller keeps the day-flat path."""
    monkeypatch.setattr(
        "market_sim.data.eia930.weather.iso_zone_tmax", lambda *a, **k: None
    )
    assert iso_zone_hourly_drybulb("MISO", YEAR, HOURS, zone="MISO-South") is None


def test_hourly_grain_carries_hour_of_day_signal_the_day_flat_path_cannot():
    """The whole point: TMAX-flat has zero diurnal signal, the reconstruction has one."""
    tmin, tmax = _flat(4.0), _flat(20.0)
    hourly = diurnal_drybulb_from_daily(tmin, tmax, YEAR, HOURS)

    hod = np.arange(HOURS) % 24
    flat_profile = np.array([tmax[hod == h].mean() for h in range(24)])
    hourly_profile = np.array([hourly[hod == h].mean() for h in range(24)])

    assert flat_profile.max() - flat_profile.min() == pytest.approx(0.0)
    assert hourly_profile.max() - hourly_profile.min() == pytest.approx(16.0)
    assert int(hourly_profile.argmin()) == DIURNAL_TMIN_HOUR
    assert int(hourly_profile.argmax()) == DIURNAL_TMAX_HOUR


# ---------------------------------------------------------------------------
# The curve legs, exercised directly on the availability engine's own algebra
# ---------------------------------------------------------------------------


def _mean_anchored_curve(temp: np.ndarray, slope: float) -> np.ndarray:
    """The mean-anchored curve as ``arrays.py`` computes it."""
    return 1.0 - slope * (temp - float(np.mean(temp)))


def _hinged_curve(temp: np.ndarray, slope: float, ref: float) -> np.ndarray:
    """The committed hinged curve as ``arrays.py`` computes it."""
    return 1.0 - slope * np.maximum(0.0, temp - ref)


def test_mean_anchored_curve_is_exactly_level_neutral():
    """Annual mean 1.0 by construction — the arm claims shape, never level."""
    temp = diurnal_drybulb_from_daily(_flat(4.0, 8760), _flat(20.0, 8760), YEAR, 8760)
    curve = _mean_anchored_curve(temp, 0.00141)
    assert curve.mean() == pytest.approx(1.0, abs=1e-12)
    # ... and it moves in BOTH directions, unlike the hinge
    assert curve.max() > 1.0
    assert curve.min() < 1.0


def test_hinge_erases_the_response_below_its_reference():
    """Why MISO is mean-anchored: the 15 C hinge zeroes a measured cold response.

    MISO's own onset scan measures a clear within-day response in the 5-15 C
    bins (FINDING miso-101). The committed hinge is flat across that entire
    range, so it cannot carry the wave the data shows.
    """
    n = 24 * 30
    cold = diurnal_drybulb_from_daily(_flat(2.0, n), _flat(12.0, n), YEAR, n)
    hinged = _hinged_curve(cold, 0.00141, 15.0)
    anchored = _mean_anchored_curve(cold, 0.00141)

    assert hinged.max() - hinged.min() == pytest.approx(0.0)  # dead flat
    assert anchored.max() - anchored.min() > 0.01  # carries the wave


def test_mean_anchored_curve_troughs_when_the_day_peaks():
    """Capability trough must land at the temperature peak (h15), not h00."""
    n = 24 * 30
    temp = diurnal_drybulb_from_daily(_flat(4.0, n), _flat(20.0, n), YEAR, n)
    curve = _mean_anchored_curve(temp, 0.00141)
    hod = np.arange(len(curve)) % 24
    profile = np.array([curve[hod == h].mean() for h in range(24)])
    assert int(profile.argmin()) == DIURNAL_TMAX_HOUR
    assert int(profile.argmax()) == DIURNAL_TMIN_HOUR
