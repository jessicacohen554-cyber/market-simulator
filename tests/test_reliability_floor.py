"""Unit tests for the generic reliability-floor engine.

Trivial fleet (one unit per fossil class, one zone, short horizon) exercising
the full-day temperature gate, the byte-identical no-op paths, and the steam-gas
multi-day event bridge. Weather is injected by patching
``market_sim.data.eia_loader.iso_zone_tmax`` so the flagged days are controlled
exactly (the engine imports the loader inside the function, so the patch on the
loader module's attribute takes effect).
"""

import unittest
from unittest import mock

import numpy as np

from market_sim.config.iso_configs import ReliabilityFloorSpec
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model import transmission as T

# Loader symbol the engine resolves at call time (``from ... import
# iso_zone_tmax`` inside inject_reliability_floor).
_LOADER = "market_sim.data.eia_loader.iso_zone_tmax"

# Fossil classes the trivial fleet carries, one unit each, all in zone "Z".
_FLEET_SPEC = [
    ("st", "gas_st", "ST_GAS", 100.0, 10.0),
    ("ct", "gas_ct", "CT_PEAKER", 80.0, 11.0),
    ("coal", "coal", "COAL", 300.0, 9.5),
    ("cc", "gas_cc", "CC_REGULAR", 200.0, 7.0),
    ("oil", "oil", "oil", 60.0, 12.0),
]


def _build_fleet(hours, pmin_mw=0.0):
    """Return ``(FleetArrays, {class: row_index})`` for the trivial fleet."""
    gens = [
        Generator(
            unit_id=uid,
            name=uid,
            zone="Z",
            fuel_type=fuel,
            pmax_mw=pmax,
            pmin_mw=pmin_mw,
            heat_rate=hr,
            plant_group=grp,
        )
        for uid, fuel, grp, pmax, hr in _FLEET_SPEC
    ]
    fa = generators_to_fleet_arrays(gens, ["Z"], hours=hours)
    rows = {g.plant_group: i for i, g in enumerate(gens)}
    return fa, rows


def _weather_from_daily(daily_tmax, daily_tmin, hours):
    """Return an ``iso_zone_tmax`` stand-in broadcasting daily temps to hourly."""
    tmax = np.repeat(np.asarray(daily_tmax, dtype=float), 24)[:hours]
    tmin = np.repeat(np.asarray(daily_tmin, dtype=float), 24)[:hours]

    def _loader(iso, year, hours, zone=None):
        return (tmax.copy(), tmin.copy())

    return _loader


class TestReliabilityFloorEngine(unittest.TestCase):
    def test_hot_day_floors_tmax_limb_all_24h(self):
        # Day 0 hot, day 1 normal, day 2 hot: the CT_PEAKER tmax limb floors the
        # CT at floor_pct x available capacity for ALL 24 h of each hot day and
        # leaves pmin (here 0) on the normal day; other classes are untouched.
        H = 72
        fa, rows = _build_fleet(H)
        loader = _weather_from_daily([35.0, 18.0, 36.0], [20.0, 5.0, 22.0], H)
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="CT_PEAKER",
            driver="tmax",
            threshold=25.0,
            floor_pct=0.5,
        )
        with mock.patch(_LOADER, loader):
            applied = T.inject_reliability_floor(fa, "TEST", 2024, [spec], ["Z"])
        self.assertTrue(applied)
        ct = rows["CT_PEAKER"]
        avail = fa.availability[ct, :]
        pmax = fa.pmax[ct]
        expected = 0.5 * pmax * avail
        # Hot days 0 and 2: floored every hour.
        for d in (0, 2):
            sl = slice(d * 24, d * 24 + 24)
            np.testing.assert_allclose(fa.min_gen[ct, sl], expected[sl])
        # Normal day 1: stays at pmin (0).
        np.testing.assert_allclose(fa.min_gen[ct, 24:48], 0.0)
        # Other classes carry no floor (pmin == 0 everywhere).
        for cls in ("ST_GAS", "COAL", "CC_REGULAR", "oil"):
            np.testing.assert_allclose(fa.min_gen[rows[cls], :], 0.0)

    def test_cold_day_floors_tmin_limb_all_24h(self):
        # tmin limb: a cold day (tmin below threshold) floors COAL all 24 h.
        H = 72
        fa, rows = _build_fleet(H)
        loader = _weather_from_daily([5.0, 6.0, 7.0], [-12.0, 8.0, -3.0], H)
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="COAL",
            driver="tmin",
            threshold=0.0,
            floor_pct=0.4,
        )
        with mock.patch(_LOADER, loader):
            applied = T.inject_reliability_floor(fa, "TEST", 2024, [spec], ["Z"])
        self.assertTrue(applied)
        coal = rows["COAL"]
        expected = 0.4 * fa.pmax[coal] * fa.availability[coal, :]
        # Cold days 0 and 2 floored; mild day 1 at pmin.
        for d in (0, 2):
            sl = slice(d * 24, d * 24 + 24)
            np.testing.assert_allclose(fa.min_gen[coal, sl], expected[sl])
        np.testing.assert_allclose(fa.min_gen[coal, 24:48], 0.0)

    def test_pmin_preserved_on_unflagged_hours(self):
        # With pmin > 0, unflagged hours keep pmin and flagged hours take the
        # larger floor.
        H = 48
        fa, rows = _build_fleet(H, pmin_mw=10.0)
        loader = _weather_from_daily([30.0, 18.0], [20.0, 5.0], H)
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="CT_PEAKER",
            driver="tmax",
            threshold=25.0,
            floor_pct=0.5,
        )
        with mock.patch(_LOADER, loader):
            T.inject_reliability_floor(fa, "TEST", 2024, [spec], ["Z"])
        ct = rows["CT_PEAKER"]
        expected_hot = 0.5 * fa.pmax[ct] * fa.availability[ct, 0]
        self.assertGreater(expected_hot, 10.0)
        np.testing.assert_allclose(fa.min_gen[ct, 0:24], expected_hot)
        np.testing.assert_allclose(fa.min_gen[ct, 24:48], 10.0)  # pmin

    def test_normal_day_no_floor_is_byte_identical(self):
        # No day clears the threshold -> no floor applied, min_gen untouched.
        H = 48
        fa, _ = _build_fleet(H)
        loader = _weather_from_daily([18.0, 20.0], [5.0, 6.0], H)
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="CT_PEAKER",
            driver="tmax",
            threshold=25.0,
            floor_pct=0.5,
        )
        with mock.patch(_LOADER, loader):
            applied = T.inject_reliability_floor(fa, "TEST", 2024, [spec], ["Z"])
        self.assertFalse(applied)
        self.assertIsNone(fa.min_gen)

    def test_no_weather_forecast_fallback_is_noop(self):
        # A forecast year with no pinned weather: the loader returns None and the
        # engine no-ops (byte-identical; min_gen stays None).
        H = 48
        fa, _ = _build_fleet(H)
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="CT_PEAKER",
            driver="tmax",
            threshold=25.0,
            floor_pct=0.5,
        )
        with mock.patch(_LOADER, lambda *a, **k: None):
            applied = T.inject_reliability_floor(fa, "TEST", 2099, [spec], ["Z"])
        self.assertFalse(applied)
        self.assertIsNone(fa.min_gen)

    def test_disabled_limb_is_byte_identical(self):
        # An enabled=False limb is skipped even on a flagged day.
        H = 48
        fa, _ = _build_fleet(H)
        loader = _weather_from_daily([35.0, 36.0], [20.0, 22.0], H)
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="CT_PEAKER",
            driver="tmax",
            threshold=25.0,
            floor_pct=0.5,
            enabled=False,
        )
        with mock.patch(_LOADER, loader):
            applied = T.inject_reliability_floor(fa, "TEST", 2024, [spec], ["Z"])
        self.assertFalse(applied)
        self.assertIsNone(fa.min_gen)

    def test_netload_driver_is_skipped_until_phase2(self):
        # driver="netload" is recognized but skipped (no net-load plumbing yet).
        H = 48
        fa, _ = _build_fleet(H)
        loader = _weather_from_daily([35.0, 36.0], [20.0, 22.0], H)
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="CT_PEAKER",
            driver="netload",
            threshold=1000.0,
            floor_pct=0.5,
        )
        with mock.patch(_LOADER, loader):
            applied = T.inject_reliability_floor(fa, "TEST", 2024, [spec], ["Z"])
        self.assertFalse(applied)
        self.assertIsNone(fa.min_gen)

    def test_steam_min_event_bridges_consecutive_flagged_days(self):
        # Steam classes carry min_event_hours > 24: an isolated hot day bridges
        # forward into the next day, and two consecutive hot days stay floored
        # across the whole span. Days: hot, normal, hot, normal.
        H = 96
        fa, rows = _build_fleet(H)
        loader = _weather_from_daily(
            [35.0, 18.0, 36.0, 18.0], [20.0, 5.0, 22.0, 5.0], H
        )
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="ST_GAS",
            driver="tmax",
            threshold=25.0,
            floor_pct=0.5,
            min_event_hours=48,
        )
        with mock.patch(_LOADER, loader):
            applied = T.inject_reliability_floor(fa, "TEST", 2024, [spec], ["Z"])
        self.assertTrue(applied)
        st = rows["ST_GAS"]
        expected = 0.5 * fa.pmax[st] * fa.availability[st, :]
        # Hot day 0 (h0-23) bridges 48 h -> floors normal day 1 (h24-47) too.
        np.testing.assert_allclose(fa.min_gen[st, 0:48], expected[0:48])
        # Hot day 2 (h48-71) bridges into day 3 (h72-95).
        np.testing.assert_allclose(fa.min_gen[st, 48:96], expected[48:96])

    def test_steam_bridge_does_not_floor_a_lone_isolated_normal_day(self):
        # A single hot day with NO neighbouring flagged day still floors only its
        # own 48 h bridge window, not the entire horizon.
        H = 120  # 5 days
        fa, rows = _build_fleet(H)
        loader = _weather_from_daily(
            [18.0, 35.0, 18.0, 18.0, 18.0],
            [5.0, 20.0, 5.0, 5.0, 5.0],
            H,
        )
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="ST_GAS",
            driver="tmax",
            threshold=25.0,
            floor_pct=0.5,
            min_event_hours=48,
        )
        with mock.patch(_LOADER, loader):
            T.inject_reliability_floor(fa, "TEST", 2024, [spec], ["Z"])
        st = rows["ST_GAS"]
        expected = 0.5 * fa.pmax[st] * fa.availability[st, :]
        # Day 0 (h0-23) unfloored; day 1 hot (h24-47) + bridge into day 2 (h48-71).
        np.testing.assert_allclose(fa.min_gen[st, 0:24], 0.0)
        np.testing.assert_allclose(fa.min_gen[st, 24:72], expected[24:72])
        np.testing.assert_allclose(fa.min_gen[st, 72:120], 0.0)


if __name__ == "__main__":
    unittest.main()
