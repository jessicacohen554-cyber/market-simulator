"""Tests for the shared NET-load commitment-floor window.

``ScenarioConfig.commitment_floor_window_netload`` (SPP-66, owner ruling
"Shared gate" 2026-09-20) changes only WHICH series the commitment floors shape
themselves on: net load (demand less available wind/solar) instead of system
load. Size, level and membership of each floor are untouched (rule 19
``[R-ONE-MECH]``) — and crucially it is resolved ONCE, so all four floors that
read it move together rather than being windowed on different drivers.

The driver evidence is rule 17 ``[R-FLOOR-WINDOW]`` (a): in a high-VRE ISO a
cycler runs in the high-NET-load hours, not the high-gross-load ones. Measured
on EIA-930 SWPP actuals, SPP coal correlates with net load at +0.948/+0.948/
+0.932 (2023/24/25) against +0.716/+0.661/+0.613 with system load.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.data.fleet import Generator, generators_to_fleet_arrays

ZONES = ["SPP-North"]
HOURS = 8760
_COAL_CODE = 2956
_FRAC = 0.25


def _load(hours: int = HOURS) -> np.ndarray:
    """Diurnal + seasonal system load, peaking on summer afternoons."""
    t = np.arange(hours, dtype=float)
    season = 1.0 + 0.30 * np.sin(2.0 * np.pi * (t / hours) - np.pi / 2.0)
    diurnal = 1.0 + 0.35 * np.sin(2.0 * np.pi * ((t % 24) - 8.0) / 24.0)
    return 30_000.0 * season * diurnal


def _vre(hours: int = HOURS) -> np.ndarray:
    """Wind-dominated VRE, anti-correlated with load (windy nights/winter).

    This is what makes net load a genuinely different ranking: the gross peak
    hours are often windy, and the tightest net hours are calm ones.
    """
    t = np.arange(hours, dtype=float)
    season = 1.0 + 0.40 * np.sin(2.0 * np.pi * (t / hours) + np.pi / 2.0)
    diurnal = 1.0 - 0.30 * np.sin(2.0 * np.pi * ((t % 24) - 8.0) / 24.0)
    return 12_000.0 * season * diurnal


def _coal_gen() -> Generator:
    return Generator(
        unit_id="COAL_SPP-North_p2956_sync",
        name="prb cycler sync band",
        zone="SPP-North",
        fuel_type="coal",
        pmax_mw=300.0,
        plant_group="COAL_BIT",
        plant_code=_COAL_CODE,
        is_campd_bin=True,
        coal_sync_pmin_mw=150.0,
        coal_sync_online_frac=_FRAC,
    )


def _floor(netload: bool, netload_shape: np.ndarray | None) -> np.ndarray:
    cfg = ScenarioConfig(
        iso="SPP",
        weather_year=2024,
        mode="backcast",
        hours=HOURS,
        commitment_floor_window_netload=netload,
    )
    fa = generators_to_fleet_arrays(
        [_coal_gen()],
        ZONES,
        hours=HOURS,
        iso="SPP",
        config=cfg,
        load_shape=_load(),
        netload_shape=netload_shape,
    )
    return np.asarray(fa.min_gen)[0]


class TestCommitmentFloorWindowNetload(unittest.TestCase):
    def test_default_is_off(self) -> None:
        """Shipped default keeps the historical system-load window."""
        self.assertFalse(ScenarioConfig().commitment_floor_window_netload)

    def test_registered_for_cache_key_stability(self) -> None:
        """Registered at its default so every pre-existing bundle keeps its key."""
        self.assertIn("commitment_floor_window_netload", _CACHE_KEY_OPTIONAL_FIELDS)
        self.assertEqual(
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["commitment_floor_window_netload"],
            "False",
        )

    def test_off_ignores_netload_entirely(self) -> None:
        """Unarmed, passing a net-load series changes nothing at all."""
        base = _floor(False, None)
        with_series = _floor(False, _load() - _vre())
        np.testing.assert_array_equal(base, with_series)

    def test_on_selects_a_different_hour_set_of_the_same_size(self) -> None:
        """Rule 19: the window MOVES; its size and level do not."""
        off = _floor(False, None)
        on = _floor(True, _load() - _vre())
        self.assertGreater(int((off > 0).sum()), 0)
        # Same number of floored hours (same k) and same level ...
        self.assertEqual(int((off > 0).sum()), int((on > 0).sum()))
        self.assertEqual(round(float(off.max()), 6), round(float(on.max()), 6))
        # ... but a genuinely different hour set.
        self.assertGreater(int(np.count_nonzero((off > 0) != (on > 0))), 0)

    def test_on_ranks_by_net_load(self) -> None:
        """The armed window is exactly the top-k hours by NET load."""
        load, vre = _load(), _vre()
        net = load - vre
        on = _floor(True, net)
        k = int(round(_FRAC * HOURS))
        expected = set(np.argsort(-net, kind="stable")[:k].tolist())
        self.assertEqual(set(np.flatnonzero(on > 0).tolist()), expected)

    def test_missing_netload_falls_back_rather_than_dropping_the_floor(self) -> None:
        """A plumbing gap must never silently un-floor an armed run."""
        off = _floor(False, None)
        np.testing.assert_array_equal(_floor(True, None), off)
        np.testing.assert_array_equal(_floor(True, np.zeros(7)), off)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
