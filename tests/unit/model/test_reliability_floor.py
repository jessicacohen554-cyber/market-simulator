"""Unit tests for the generic reliability-floor engine.

Trivial fleet (one unit per fossil class, one zone, short horizon) exercising
the full-day temperature gate, the byte-identical no-op paths, and the steam-gas
multi-day event bridge. Weather is injected by patching
``market_sim.data.eia_loader.iso_zone_tmax`` so the flagged days are controlled
exactly (the engine imports the loader inside the function, so the patch on the
loader module's attribute takes effect).
"""

import importlib.util
import types
import unittest
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.config.plant_taxonomy import artifact_class
from market_sim.config.constants import MIN_STABLE_PCT_PHYSICAL
from market_sim.config.iso_configs import (
    NYISO_PEAK_WINDOW_FLOORS_OFF,
    RELIABILITY_FLOOR_REGISTRY,
    ReliabilityFloorSpec,
    apply_reliability_floor_overrides,
    apply_reliability_floor_plant_exclusions,
)
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model import transmission as T
from tests.helpers import REPO_ROOT

# The derivation lives under scripts/ (not an importable package); load by path
# so the coefficient-magnitude and enable-gate logic can be unit-tested directly.
_REPO = REPO_ROOT
_spec = importlib.util.spec_from_file_location(
    "derive_reliability_coeffs",
    str(_REPO / "scripts" / "data" / "derive_reliability_coeffs.py"),
)
drc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(drc)

# Loader symbol the engine resolves at call time (``from ... import
# iso_zone_tmax`` inside inject_reliability_floor).
_LOADER = "market_sim.data.eia_loader.iso_zone_tmax"

# Fossil classes the trivial fleet carries, one unit each, all in zone "Z".
_FLEET_SPEC = [
    ("st", "gas_st", "ST_GAS", 100.0, 10.0),
    ("ct", "gas_ct", "CT_PEAKER", 80.0, 11.0),
    # A coal unit carries its subclass (COAL-SUB); the registry limbs below
    # name the coal FAMILY token "COAL", which spans every subclass.
    ("coal", "coal", "COAL_BIT", 300.0, 9.5),
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
    # Keyed by class FAMILY (plant_taxonomy.artifact_class), the vocabulary the
    # registry limbs use: rows["COAL"] is the COAL_BIT unit.
    rows = {artifact_class(g.plant_group): i for i, g in enumerate(gens)}
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

    def test_netload_high_day_floors_all_24h(self):
        # Day 0: peak net-load 30 GW (> 27 threshold) -> floored all 24h.
        # Day 1: peak net-load 20 GW (< 27 threshold) -> stays at pmin (0).
        H = 48
        n_zones = 1
        fa, rows = _build_fleet(H)
        # Demand 35 GW day 0, 25 GW day 1; wind+solar eat 5 GW -> net 30, 20.
        demand = np.full((n_zones, H), 25000.0)
        demand[0, :24] = 35000.0
        wind_cf = np.ones((n_zones, H))
        wind_cap = np.array([2500.0])
        solar_cf = np.ones((n_zones, H))
        solar_cap = np.array([2500.0])
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="CT_PEAKER",
            driver="netload",
            threshold=27.0,
            floor_pct=0.5,
        )
        applied = T.inject_reliability_floor(
            fa,
            "TEST",
            2024,
            [spec],
            ["Z"],
            demand=demand,
            wind_cf=wind_cf,
            wind_cap=wind_cap,
            solar_cf=solar_cf,
            solar_cap=solar_cap,
        )
        self.assertTrue(applied)
        ct = rows["CT_PEAKER"]
        expected = 0.5 * fa.pmax[ct] * fa.availability[ct, :]
        np.testing.assert_allclose(fa.min_gen[ct, :24], expected[:24])
        np.testing.assert_allclose(fa.min_gen[ct, 24:48], 0.0)

    def test_netload_low_day_no_floor_byte_identical(self):
        # Both days below threshold -> no floor, min_gen stays None.
        H = 48
        n_zones = 1
        fa, _ = _build_fleet(H)
        demand = np.full((n_zones, H), 20000.0)
        wind_cf = np.ones((n_zones, H))
        wind_cap = np.array([2500.0])
        solar_cf = np.ones((n_zones, H))
        solar_cap = np.array([2500.0])
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="CT_PEAKER",
            driver="netload",
            threshold=27.0,
            floor_pct=0.5,
        )
        applied = T.inject_reliability_floor(
            fa,
            "TEST",
            2024,
            [spec],
            ["Z"],
            demand=demand,
            wind_cf=wind_cf,
            wind_cap=wind_cap,
            solar_cf=solar_cf,
            solar_cap=solar_cap,
        )
        self.assertFalse(applied)
        self.assertIsNone(fa.min_gen)

    def test_netload_without_exogenous_inputs_is_noop(self):
        # No demand/wind/solar passed -> netload limb is skipped (byte-identical).
        H = 48
        fa, _ = _build_fleet(H)
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="CT_PEAKER",
            driver="netload",
            threshold=27.0,
            floor_pct=0.5,
        )
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

    def test_netload_threshold_percentile_recomputes_from_engine_basis(self):
        """When threshold_percentile is set, the engine ignores the CSV's fixed
        threshold and computes the p-th percentile of daily-peak net-load from
        its own inputs — closing the EIA-930-vs-model basis mismatch."""
        H = 72  # 3 days
        n_zones = 1
        fa, rows = _build_fleet(H)
        # Daily peaks in GW: day0=30, day1=20, day2=25. p50 = 25 GW.
        demand = np.zeros((n_zones, H))
        demand[0, :24] = 35000.0  # net-load peak = 35k - 5k = 30 GW
        demand[0, 24:48] = 25000.0  # net-load peak = 25k - 5k = 20 GW
        demand[0, 48:72] = 30000.0  # net-load peak = 30k - 5k = 25 GW
        wind_cf = np.ones((n_zones, H))
        wind_cap = np.array([2500.0])
        solar_cf = np.ones((n_zones, H))
        solar_cap = np.array([2500.0])
        # Fixed threshold=99 would flag nothing; but percentile=50 -> p50=25 GW
        # flags day0 (30>25). Day2 (25) is NOT > 25, so unflagged.
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="CT_PEAKER",
            driver="netload",
            threshold=99.0,
            floor_pct=0.5,
            threshold_percentile=50.0,
        )
        applied = T.inject_reliability_floor(
            fa,
            "TEST",
            2024,
            [spec],
            ["Z"],
            demand=demand,
            wind_cf=wind_cf,
            wind_cap=wind_cap,
            solar_cf=solar_cf,
            solar_cap=solar_cap,
        )
        self.assertTrue(applied)
        ct = rows["CT_PEAKER"]
        expected = 0.5 * fa.pmax[ct] * fa.availability[ct, :]
        np.testing.assert_allclose(fa.min_gen[ct, :24], expected[:24])
        np.testing.assert_allclose(fa.min_gen[ct, 24:72], 0.0)

    def test_netload_without_percentile_uses_fixed_threshold(self):
        """Without threshold_percentile the engine uses the CSV's fixed GW
        threshold — byte-identical to the pre-fix behaviour."""
        H = 48
        n_zones = 1
        fa, rows = _build_fleet(H)
        demand = np.full((n_zones, H), 35000.0)
        demand[0, 24:48] = 25000.0
        wind_cf = np.ones((n_zones, H))
        wind_cap = np.array([2500.0])
        solar_cf = np.ones((n_zones, H))
        solar_cap = np.array([2500.0])
        # threshold=27 -> day0 net 30>27 flagged, day1 net 20<27 not.
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="CT_PEAKER",
            driver="netload",
            threshold=27.0,
            floor_pct=0.5,
        )
        applied = T.inject_reliability_floor(
            fa,
            "TEST",
            2024,
            [spec],
            ["Z"],
            demand=demand,
            wind_cf=wind_cf,
            wind_cap=wind_cap,
            solar_cf=solar_cf,
            solar_cap=solar_cap,
        )
        self.assertTrue(applied)
        ct = rows["CT_PEAKER"]
        expected = 0.5 * fa.pmax[ct] * fa.availability[ct, :]
        np.testing.assert_allclose(fa.min_gen[ct, :24], expected[:24])
        np.testing.assert_allclose(fa.min_gen[ct, 24:48], 0.0)


class TestReliabilityFloorRamp(unittest.TestCase):
    """Continuous temperature-ramp families interpolate ``(threshold, floor_pct)``
    knots instead of firing each knot as an independent step."""

    def _ramp_knots(self, **overrides):
        # Legacy NYISO downstate CT ramp: base 0.132 at T0=25C, cap 0.679 at
        # 35.22C, evening-only (HB14-21), pro-rata. Two knots, one family.
        base = dict(
            zone="Z",
            plant_class="CT_PEAKER",
            driver="tmax",
            distribution="pro_rata",
            start_hour=14,
            end_hour=21,
            ramp_group="Z_CT_ev",
        )
        base.update(overrides)
        return [
            ReliabilityFloorSpec(threshold=25.0, floor_pct=0.132, **base),
            ReliabilityFloorSpec(threshold=35.22, floor_pct=0.679, **base),
        ]

    def test_ramp_interpolates_between_knots_in_window(self):
        # A 30C day sits mid-ramp: floor = 0.132 + (30-25)/(35.22-25)*(0.679-0.132)
        # = 0.132 + 0.4892*0.547 = 0.3996. Applied only in the HB14-21 window.
        H = 24
        fa, rows = _build_fleet(H)
        loader = _weather_from_daily([30.0], [20.0], H)
        with mock.patch(_LOADER, loader):
            applied = T.inject_reliability_floor(
                fa, "TEST", 2024, self._ramp_knots(), ["Z"]
            )
        self.assertTrue(applied)
        ct = rows["CT_PEAKER"]
        pmax = fa.pmax[ct]
        avail = fa.availability[ct, :]
        interp_pct = np.interp(30.0, [25.0, 35.22], [0.132, 0.679])
        # Evening window HB14-21 floored at the interpolated pct; else pmin (0).
        np.testing.assert_allclose(
            fa.min_gen[ct, 14:22], interp_pct * pmax * avail[14:22]
        )
        np.testing.assert_allclose(fa.min_gen[ct, 0:14], 0.0)
        np.testing.assert_allclose(fa.min_gen[ct, 22:24], 0.0)

    def test_ramp_clamps_flat_below_and_above_end_knots(self):
        # Cool day (18C) clamps to the base knot 0.132 (persistent evening base);
        # extreme day (40C) clamps to the cap knot 0.679 — never over/undershoots.
        H = 48
        fa, rows = _build_fleet(H)
        loader = _weather_from_daily([18.0, 40.0], [10.0, 25.0], H)
        with mock.patch(_LOADER, loader):
            T.inject_reliability_floor(fa, "TEST", 2024, self._ramp_knots(), ["Z"])
        ct = rows["CT_PEAKER"]
        pmax, avail = fa.pmax[ct], fa.availability[ct, :]
        # Day 0 cool → base 0.132 in the evening window.
        np.testing.assert_allclose(fa.min_gen[ct, 14:22], 0.132 * pmax * avail[14:22])
        # Day 1 extreme → cap 0.679 in the evening window.
        np.testing.assert_allclose(fa.min_gen[ct, 38:46], 0.679 * pmax * avail[38:46])

    def test_ramp_binds_every_day_no_threshold_gate(self):
        # Unlike a step limb, the ramp's base knot floors EVERY evening (its base
        # is the persistent floor), so even a mild day carries the base floor.
        H = 24
        fa, rows = _build_fleet(H)
        loader = _weather_from_daily([10.0], [2.0], H)  # cold, well below base knot
        with mock.patch(_LOADER, loader):
            applied = T.inject_reliability_floor(
                fa, "TEST", 2024, self._ramp_knots(), ["Z"]
            )
        self.assertTrue(applied)
        ct = rows["CT_PEAKER"]
        np.testing.assert_allclose(
            fa.min_gen[ct, 14:22], 0.132 * fa.pmax[ct] * fa.availability[ct, 14:22]
        )

    def test_disabled_ramp_knot_dropped_from_family(self):
        # A disabled knot is excluded; with only the base knot left the ramp is a
        # flat base floor (np.interp of a single point returns that point).
        H = 24
        fa, rows = _build_fleet(H)
        loader = _weather_from_daily([40.0], [25.0], H)
        knots = self._ramp_knots()
        knots[1] = ReliabilityFloorSpec(
            zone="Z",
            plant_class="CT_PEAKER",
            driver="tmax",
            distribution="pro_rata",
            start_hour=14,
            end_hour=21,
            ramp_group="Z_CT_ev",
            threshold=35.22,
            floor_pct=0.679,
            enabled=False,
        )
        with mock.patch(_LOADER, loader):
            T.inject_reliability_floor(fa, "TEST", 2024, knots, ["Z"])
        ct = rows["CT_PEAKER"]
        # Only the base knot survives → flat 0.132 even on a 40C day.
        np.testing.assert_allclose(
            fa.min_gen[ct, 14:22], 0.132 * fa.pmax[ct] * fa.availability[ct, 14:22]
        )


class TestPhysicalFloorMagnitude(unittest.TestCase):
    """The floor magnitude is the physical Pmin/Pmax, not the must-run share."""

    def test_min_stable_pct_matches_physical_table(self):
        # Merchant priority classes carry a NON-ZERO physical floor (the bug was
        # that Pct_Must_Run = 0 zeroed them); values are NREL WWSIS-2 Table 7.
        self.assertEqual(drc._min_stable_pct("ST_GAS"), 0.12)
        self.assertEqual(drc._min_stable_pct("CT_PEAKER"), 0.38)
        self.assertEqual(drc._min_stable_pct("CC_REGULAR"), 0.52)
        self.assertEqual(drc._min_stable_pct("COAL"), 0.40)
        self.assertEqual(drc._min_stable_pct("oil"), 0.12)
        self.assertEqual(
            drc._min_stable_pct("ST_GAS"), MIN_STABLE_PCT_PHYSICAL["ST_GAS"]
        )

    def test_coal_subclasses_fall_back_to_coal(self):
        for sub in ("COAL_PRB", "COAL_BIT", "COAL_LIGNITE", "COAL_WC"):
            self.assertEqual(drc._min_stable_pct(sub), 0.40)

    def test_unknown_class_has_no_physical_floor(self):
        self.assertEqual(drc._min_stable_pct("NUCLEAR"), 0.0)


def _limb_df(temps, online_frac, cf):
    """Build the ``(cf, online_frac)`` daily frame + temp series _fit_limb wants."""
    idx = pd.date_range("2024-01-01", periods=len(temps), freq="D")
    df = pd.DataFrame({"cf": cf, "online_frac": online_frac}, index=idx)
    return df, pd.Series(np.asarray(temps, dtype=float), index=idx)


class TestEnableGateLikeForLike(unittest.TestCase):
    """Plan C: enable on commit_frac > baseline_commit (online share), not CF."""

    def test_temperature_responsive_commitment_passes_gate(self):
        # 20 mild days (online 0.3) + 20 hot days (online 0.9, CF rising with temp):
        # flagged-day commit share (0.9) exceeds mild-day share (0.3) -> the gate's
        # third clause is True and rho is strongly positive.
        mild_t = list(range(0, 20))  # < 25 -> mild
        hot_t = list(range(26, 46))  # >= 25 -> flagged, distinct so rho is defined
        online = [0.3] * 20 + [0.9] * 20
        cf = [0.2] * 20 + [0.2 + 0.01 * i for i in range(20)]
        df, temp = _limb_df(mild_t + hot_t, online, cf)
        fit = drc._fit_limb(df, temp, threshold=25.0, cold=False)
        self.assertAlmostEqual(fit["commit_frac"], 0.9)
        self.assertAlmostEqual(fit["baseline_commit"], 0.3)
        self.assertGreater(fit["rho"], 0.3)
        self.assertGreater(fit["commit_frac"], fit["baseline_commit"])  # gate clause

    def test_always_online_unit_fails_gate(self):
        # A unit online every day (mild AND hot) shows no temperature-driven
        # commitment: commit_frac == baseline_commit, so the like-for-like clause
        # is False even though it would pass the old floor_pct > baseline test.
        mild_t = list(range(0, 20))
        hot_t = list(range(26, 46))
        online = [1.0] * 40
        cf = [0.5] * 20 + [0.6] * 20
        df, temp = _limb_df(mild_t + hot_t, online, cf)
        fit = drc._fit_limb(df, temp, threshold=25.0, cold=False)
        self.assertAlmostEqual(fit["commit_frac"], 1.0)
        self.assertAlmostEqual(fit["baseline_commit"], 1.0)
        self.assertFalse(fit["commit_frac"] > fit["baseline_commit"])  # gate clause


class TestThresholdAnchors(unittest.TestCase):
    """Plan D: physical onset anchors, not flat 25 °C / 0 °C priors."""

    def _zt(self):
        # A spread of daily temps so percentiles are well-defined.
        n = 200
        return pd.DataFrame(
            {
                "tmax_c": np.linspace(-5.0, 40.0, n),
                "tmin_c": np.linspace(-25.0, 20.0, n),
            }
        )

    def test_pjm_cold_uses_operational_anchors(self):
        zt = self._zt()
        thr, basis = drc._limb_threshold("PJM", "ST_GAS", "tmin", zt)
        self.assertEqual(thr, drc.PJM_COLD_ALERT_C)  # -12 C
        self.assertIn("Cold Weather Alert", basis)
        thr_ct, basis_ct = drc._limb_threshold("PJM", "CT_PEAKER", "tmin", zt)
        self.assertEqual(thr_ct, drc.PJM_COLD_CT_MOBILIZE_C)  # -20.5 C (CT tier)
        self.assertIn("CT-mobilization", basis_ct)

    def test_non_pjm_cold_uses_zone_percentile(self):
        zt = self._zt()
        thr, basis = drc._limb_threshold("NYISO", "ST_GAS", "tmin", zt)
        self.assertAlmostEqual(
            thr, float(np.percentile(zt["tmin_c"], drc.COLD_PERCENTILE)), places=6
        )
        self.assertIn("p1 tmin", basis)

    def test_hot_uses_zone_percentile_for_all_isos(self):
        zt = self._zt()
        for iso in ("PJM", "ERCOT", "NYISO"):
            thr, basis = drc._limb_threshold(iso, "CT_PEAKER", "tmax", zt)
            self.assertAlmostEqual(
                thr, float(np.percentile(zt["tmax_c"], drc.HOT_PERCENTILE)), places=6
            )
            self.assertIn("p95 tmax", basis)


class TestNetloadDerivation(unittest.TestCase):
    """Tests for the net-load regression helpers in derive_reliability_coeffs."""

    def _nl_df(self, peak_gw_values):
        idx = pd.date_range("2024-01-01", periods=len(peak_gw_values), freq="D")
        return pd.DataFrame({"date": idx, "peak_nl_gw": peak_gw_values})

    def test_netload_threshold_is_p70(self):
        vals = list(range(100))
        nl = self._nl_df(vals)
        thr, basis = drc._netload_threshold_gw(nl)
        self.assertAlmostEqual(thr, float(np.percentile(vals, 70)), places=4)
        self.assertIn("p70", basis)

    def test_fit_netload_limb_responsive_commitment(self):
        n = 40
        mild_nl = [20.0] * 20
        high_nl = [30.0 + 0.1 * i for i in range(20)]
        online = [0.2] * 20 + [0.8] * 20
        cf = [0.05] * 20 + [0.05 + 0.005 * i for i in range(20)]
        idx = pd.date_range("2024-01-01", periods=n, freq="D")
        cf_df = pd.DataFrame({"cf": cf, "online_frac": online}, index=idx)
        daily_nl = pd.DataFrame({"date": idx, "peak_nl_gw": mild_nl + high_nl})
        fit = drc._fit_netload_limb(cf_df, daily_nl, threshold_gw=25.0)
        self.assertIsNotNone(fit)
        self.assertAlmostEqual(fit["commit_frac"], 0.8)
        self.assertAlmostEqual(fit["baseline_commit"], 0.2)
        self.assertGreater(fit["commit_frac"], fit["baseline_commit"])
        self.assertEqual(fit["n"], 20)

    def test_fit_netload_limb_no_flagged_days(self):
        n = 20
        idx = pd.date_range("2024-01-01", periods=n, freq="D")
        cf_df = pd.DataFrame({"cf": [0.1] * n, "online_frac": [0.3] * n}, index=idx)
        daily_nl = pd.DataFrame({"date": idx, "peak_nl_gw": [20.0] * n})
        fit = drc._fit_netload_limb(cf_df, daily_nl, threshold_gw=25.0)
        self.assertIsNone(fit)

    def test_group_daily_cf_offline_day_is_zero_not_missing(self):
        """A day whose CAMPD rows are all-NaN grossLoad is OFFLINE (cf=0,
        online_frac=0), never dropped — the single-plant saturation fix.

        Trivial case first: one plant, four days — two operating, two with
        reported rows but no positive load. Without the fix the offline days
        vanish from the frame and commit_frac conditions on "was operating"
        (the 2026-06-30 NEISO ST_GAS commit_frac=baseline_commit=1.0 artifact).
        """
        days = pd.date_range("2024-01-01", periods=4, freq="D")
        rows = []
        for i, d in enumerate(days):
            gl = 50.0 if i < 2 else np.nan  # days 3-4: reported, not operating
            rows.append({"facilityId": 546, "date": d, "grossLoad": gl})
        campd = pd.DataFrame(rows)
        out = drc._group_daily_cf(campd, {546: 100.0}, 100.0)
        self.assertEqual(len(out), 4)  # offline days retained
        self.assertAlmostEqual(out["cf"].iloc[2], 0.0)
        self.assertAlmostEqual(out["cf"].iloc[3], 0.0)
        self.assertAlmostEqual(out["online_frac"].iloc[0], 1.0)
        self.assertAlmostEqual(out["online_frac"].iloc[2], 0.0)
        self.assertAlmostEqual(out["online_frac"].iloc[3], 0.0)

    def test_shipped_neiso_st_gas_owned_by_component_b(self):
        """NEISO ST_GAS carries NO enabled reliability limb: its commitment is
        owned entirely by the winter fuel-security must-run (Component B).

        The lone 81 MW ST_GAS unit sits inside a mixed CAMPD facility (code 546),
        so no clean pure-play commitment signal exists; the CSV keeps ST_GAS as
        visible, disabled overnight-windowed placeholders (rule 12) while
        Component B floors the model ST_GAS all-day on cold days (rule 14/19,
        neiso-54 consolidation replacing the old contaminated all-24h netload
        limb). Because no ST_GAS netload limb is enabled, run_calibration keeps
        ST_GAS inside the winter fuel-security scope."""
        from market_sim.config.iso_configs import RELIABILITY_FLOOR_REGISTRY

        st = [
            s
            for s in RELIABILITY_FLOOR_REGISTRY.get("NEISO", [])
            if s.plant_class == "ST_GAS"
        ]
        self.assertTrue(st, "NEISO ST_GAS placeholder rows must stay visible")
        self.assertTrue(
            all(not s.enabled for s in st),
            "no NEISO ST_GAS reliability limb may be enabled (owned by Component B)",
        )
        # The placeholders window to the overnight pre-positioning block [0,6].
        for s in st:
            self.assertEqual((s.start_hour, s.end_hour), (0, 6))

    def test_shipped_neiso_ct_peaker_evening_ramp_limbs(self):
        """NEISO CT_PEAKER carries enabled EVENING-windowed [15,21] reliability
        limbs (the local-RA net-load-ramp commitment) — never all-24h, so the
        floor never binds overnight where CT CF ~0 (rule 12/18; neiso-54 replaces
        the 2026-07-05 scrubbed all-day limbs)."""
        from market_sim.config.iso_configs import RELIABILITY_FLOOR_REGISTRY

        ct = [
            s
            for s in RELIABILITY_FLOOR_REGISTRY.get("NEISO", [])
            if s.plant_class == "CT_PEAKER"
        ]
        enabled = [s for s in ct if s.enabled]
        self.assertTrue(enabled, "at least one CT_PEAKER evening limb must ship")
        for s in enabled:
            self.assertEqual((s.start_hour, s.end_hour), (15, 21))
            self.assertIn(s.driver, ("tmax", "netload"))


class DropDragOwnedSpecsTest(unittest.TestCase):
    """Rule 19: a net-load drag owns its class's reliability-floor commitment."""

    @staticmethod
    def _specs():
        from market_sim.config.iso_configs import ReliabilityFloorSpec

        return [
            ReliabilityFloorSpec(
                zone="PJM_EMAAC",
                plant_class="CT_PEAKER",
                driver="tmax",
                threshold=33.3,
                floor_pct=0.28,
            ),
            ReliabilityFloorSpec(
                zone="PJM_West_APS",
                plant_class="CT_PEAKER",
                driver="tmax",
                threshold=31.7,
                floor_pct=0.32,
            ),
            ReliabilityFloorSpec(
                zone="PJM_ComEd",
                plant_class="COAL",
                driver="tmax",
                threshold=32.8,
                floor_pct=0.38,
            ),
            ReliabilityFloorSpec(
                zone="PJM_EMAAC",
                plant_class="ST_GAS",
                driver="tmax",
                threshold=33.3,
                floor_pct=0.09,
            ),
        ]

    def test_ct_drag_drops_only_ct_peaker_limbs(self):
        from market_sim.config.iso_configs import drop_drag_owned_reliability_specs

        cfg = types.SimpleNamespace(ct_netload_drag=True, gas_st_netload_drag=False)
        out = drop_drag_owned_reliability_specs(self._specs(), cfg)
        classes = sorted(s.plant_class for s in out)
        self.assertEqual(classes, ["COAL", "ST_GAS"])  # CT_PEAKER limbs dropped
        self.assertEqual(len(out), 2)

    def test_no_drag_is_byte_identical(self):
        from market_sim.config.iso_configs import drop_drag_owned_reliability_specs

        cfg = types.SimpleNamespace(ct_netload_drag=False, gas_st_netload_drag=False)
        specs = self._specs()
        out = drop_drag_owned_reliability_specs(specs, cfg)
        self.assertIs(out, specs)  # same object, no-op

    def test_gas_st_drag_drops_st_gas(self):
        from market_sim.config.iso_configs import drop_drag_owned_reliability_specs

        cfg = types.SimpleNamespace(ct_netload_drag=True, gas_st_netload_drag=True)
        out = drop_drag_owned_reliability_specs(self._specs(), cfg)
        self.assertEqual(sorted(s.plant_class for s in out), ["COAL"])


class TestR1SignFlipDisablement(unittest.TestCase):
    """R1 (B-LIMB-1) permanent disablement of unidentified sign-flip limbs.

    The three limbs whose temperature->commitment Spearman ρ flips sign between
    the 2023-24 train fit and the 2025 holdout (D-8 §2B) must ship disabled and
    must survive a derive-script regeneration (decision rule R1; CLAUDE.md
    rule 17). The guard lives in ``derive_reliability_coeffs.R1_DISABLED_LIMBS``
    (forces ``enabled=False`` at re-derive) and is honoured by the loader via the
    ``r1_disabled`` CSV column.
    """

    _LIMBS = [
        ("PJM", "PJM_ComEd", "CC_REGULAR", "tmax"),
        ("CAISO", "SP15", "ST_GAS", "tmax"),
        ("CAISO", "SP15", "CC_REGULAR", "tmax"),
    ]

    def test_derive_constant_lists_exactly_the_three_limbs(self):
        self.assertEqual(drc.R1_DISABLED_LIMBS, frozenset(self._LIMBS))
        for iso, zone, cls, drv in self._LIMBS:
            self.assertTrue(drc._r1_disabled(iso, zone, cls, drv))
        # A sibling cold limb of the same (zone, class) is NOT R1-disabled.
        self.assertFalse(drc._r1_disabled("CAISO", "SP15", "CC_REGULAR", "tmin"))

    def test_shipped_registry_has_the_three_limbs_disabled(self):
        from market_sim.config.iso_configs import RELIABILITY_FLOOR_REGISTRY

        for iso, zone, cls, drv in self._LIMBS:
            match = [
                s
                for s in RELIABILITY_FLOOR_REGISTRY[iso]
                if s.zone == zone and s.plant_class == cls and s.driver == drv
            ]
            self.assertEqual(len(match), 1, f"{iso} {zone}/{cls}/{drv} missing")
            self.assertFalse(
                match[0].enabled, f"{iso} {zone}/{cls}/{drv} must ship disabled"
            )

    def test_loader_r1_column_overrides_enabled_true(self):
        # A row whose ``enabled`` column is True is still forced off by r1_disabled.
        import csv as _csv
        import io

        from market_sim.config import iso_configs as ic

        text = (
            "zone,plant_class,driver,threshold,floor_pct,enabled,r1_disabled\n"
            "SP15,CC_REGULAR,tmax,26.7,0.32,True,True\n"
            "SP15,CC_REGULAR,tmin,5.66,0.30,True,False\n"
        )
        rows = list(_csv.DictReader(io.StringIO(text)))
        enabled = [
            ic._coerce_bool(r.get("enabled", "True"))
            and not ic._coerce_bool(r.get("r1_disabled", ""))
            for r in rows
        ]
        self.assertEqual(enabled, [False, True])


class TestPjmCtChpScrubLocked(unittest.TestCase):
    """Lock the L-13 CT_CHP reliability-limb scrub in the committed PJM CSV.

    The EMAAC/Central_PA CT_CHP ``tmax`` limbs were disabled 2026-07-06 (L-13
    step 1): each carried no sub-daily window, so on a hot day it floored CT_CHP
    all 24 h and bound 70.8 % of its floored MWh **outside** the justified
    evening window (the pjm-77 D-4 failure). The measured hot-day lift is an
    all-hours steam-host intensification owned by ``chp_steam`` (rule 19: one
    mechanism per phenomenon), and no sub-daily re-window matches the driver, so
    the limb is scrubbed rather than re-windowed. This test fails if any PJM
    CT_CHP reliability limb is silently re-enabled — a disabled fitted limb that
    still binds is a re-armable answer key (rule 26: deleted means deleted).
    """

    def test_pjm_ct_chp_reliability_limbs_all_disabled(self):
        from market_sim.config.iso_configs import RELIABILITY_FLOOR_REGISTRY

        pjm = RELIABILITY_FLOOR_REGISTRY.get("PJM", [])
        ct_chp = [s for s in pjm if s.plant_class == "CT_CHP"]
        # The scrubbed limbs must still be present in the registry (documented,
        # not deleted rows) but every one disabled — so CT_CHP never receives an
        # all-24h temperature floor and stays owned by chp_steam.
        self.assertTrue(ct_chp, "expected PJM CT_CHP limbs in the registry")
        for spec in ct_chp:
            self.assertFalse(
                spec.enabled,
                f"PJM CT_CHP limb {spec.zone}:{spec.driver} must stay scrubbed "
                "(L-13 step 1; rule 17/19/26) — re-enabling reintroduces the "
                "all-24h off-window D-4 failure.",
            )

    def test_disabled_pjm_ct_chp_limb_injects_no_floor(self):
        # End-to-end: the committed (disabled) PJM CT_CHP limbs produce no
        # min_gen even on a hot day — byte-identical to no floor for CT_CHP.
        from market_sim.config.iso_configs import RELIABILITY_FLOOR_REGISTRY

        pjm = RELIABILITY_FLOOR_REGISTRY.get("PJM", [])
        ct_chp = [s for s in pjm if s.plant_class == "CT_CHP"]
        H = 48
        gens = [
            Generator(
                unit_id="ctchp",
                name="ctchp",
                zone="Z",
                fuel_type="gas_ct",
                pmax_mw=90.0,
                pmin_mw=0.0,
                heat_rate=11.0,
                plant_group="CT_CHP",
            )
        ]
        fa = generators_to_fleet_arrays(gens, ["Z"], hours=H)
        # Re-home each scrubbed CT_CHP spec onto the trivial zone at a very low
        # threshold so it WOULD flag every hour if enabled — proving the disable
        # (not a missed gate) is what suppresses it.
        specs = [
            ReliabilityFloorSpec(
                zone="Z",
                plant_class="CT_CHP",
                driver="tmax",
                threshold=-50.0,
                floor_pct=s.floor_pct,
                enabled=s.enabled,
            )
            for s in ct_chp
        ]
        loader = _weather_from_daily([35.0, 36.0], [20.0, 22.0], H)
        with mock.patch(_LOADER, loader):
            applied = T.inject_reliability_floor(fa, "PJM", 2024, specs, ["Z"])
        self.assertFalse(applied)
        self.assertIsNone(fa.min_gen)


class TestRampGroupScopedOverrides(unittest.TestCase):
    """``apply_reliability_floor_overrides`` ramp-family key (nyiso-87).

    One (zone, class, driver) can mix an always-on base limb with a windowed
    ramp family — NYISO ``NYC:ST_GAS:tmax`` carries the persistent 24 h
    voltage/reliability base AND the h14-21 ``NYC_ST_ev`` knots — so the
    three-segment key cannot disable the peak window without also killing the
    base. These pin the four-segment behaviour and the unchanged three-segment
    behaviour.
    """

    def _limbs(self):
        base = ReliabilityFloorSpec(
            zone="Z",
            plant_class="ST_GAS",
            driver="tmax",
            threshold=-50.0,
            floor_pct=0.20,
        )
        knot_lo = ReliabilityFloorSpec(
            zone="Z",
            plant_class="ST_GAS",
            driver="tmax",
            threshold=25.0,
            floor_pct=0.30,
            ramp_group="Z_ST_ev",
            start_hour=14,
            end_hour=21,
        )
        knot_hi = ReliabilityFloorSpec(
            zone="Z",
            plant_class="ST_GAS",
            driver="tmax",
            threshold=38.0,
            floor_pct=0.80,
            ramp_group="Z_ST_ev",
            start_hour=14,
            end_hour=21,
        )
        return [base, knot_lo, knot_hi]

    def test_ramp_group_key_disables_only_that_family(self):
        out = apply_reliability_floor_overrides(
            self._limbs(), {"Z:ST_GAS:tmax:Z_ST_ev": {"enabled": False}}
        )
        enabled = [s for s in out if s.enabled]
        self.assertEqual(len(enabled), 1)
        self.assertIsNone(enabled[0].ramp_group)
        self.assertEqual(enabled[0].threshold, -50.0)

    def test_none_sentinel_disables_only_the_ungrouped_limbs(self):
        out = apply_reliability_floor_overrides(
            self._limbs(), {"Z:ST_GAS:tmax:_none": {"enabled": False}}
        )
        enabled = [s for s in out if s.enabled]
        self.assertEqual(len(enabled), 2)
        self.assertTrue(all(s.ramp_group == "Z_ST_ev" for s in enabled))

    def test_three_segment_key_still_matches_every_limb(self):
        out = apply_reliability_floor_overrides(
            self._limbs(), {"Z:ST_GAS:tmax": {"enabled": False}}
        )
        self.assertFalse(any(s.enabled for s in out))

    def test_ramp_group_key_wins_over_the_broad_key(self):
        out = apply_reliability_floor_overrides(
            self._limbs(),
            {
                "Z:ST_GAS:tmax": {"enabled": False},
                "Z:ST_GAS:tmax:_none": {"enabled": True},
            },
        )
        enabled = [s for s in out if s.enabled]
        self.assertEqual(len(enabled), 1)
        self.assertIsNone(enabled[0].ramp_group)

    def test_nyiso_peak_window_disable_keeps_the_persistent_bases(self):
        """The arm-A override on the real registry: windows off, bases on."""
        specs = RELIABILITY_FLOOR_REGISTRY.get("NYISO", [])
        if not specs:
            self.skipTest("NYISO reliability-floor CSV not present")
        out = apply_reliability_floor_overrides(specs, NYISO_PEAK_WINDOW_FLOORS_OFF)
        enabled = [s for s in out if s.enabled]
        # Every surviving limb is unwindowed — no h14-21 evening ramp remains.
        self.assertTrue(all(s.ramp_group is None for s in enabled))
        self.assertTrue(all(s.start_hour is None for s in enabled))
        # The in-city persistent 24 h ST_GAS bases (driver is 24 h) survive.
        surviving = {(s.zone, s.plant_class) for s in enabled}
        self.assertIn(("NYC", "ST_GAS"), surviving)
        self.assertIn(("Long_Island", "ST_GAS"), surviving)
        # CT_PEAKER's only enabled limbs were the evening ramps, so it is gone.
        self.assertNotIn(("NYC", "CT_PEAKER"), surviving)
        self.assertNotIn(("Long_Island", "CT_PEAKER"), surviving)


def _build_two_plant_st_fleet(hours):
    """Two ST_GAS units in one zone with DISTINCT plant codes, plus a CT.

    Mirrors the Long_Island ST_GAS shape the exclusion was identified on: a
    pro-rata limb floors every unit of the class in the zone, so the fixture
    needs at least two same-class units to show that exclusion is per-UNIT and
    not per-class.
    """
    gens = [
        Generator(
            unit_id="st_runs",
            name="st_runs",
            zone="Z",
            fuel_type="gas_st",
            pmax_mw=100.0,
            pmin_mw=0.0,
            heat_rate=10.0,
            plant_group="ST_GAS",
            plant_code=1111,
        ),
        Generator(
            unit_id="st_laidup",
            name="st_laidup",
            zone="Z",
            fuel_type="gas_st",
            pmax_mw=50.0,
            pmin_mw=0.0,
            heat_rate=10.5,
            plant_group="ST_GAS",
            plant_code=2517,
        ),
        Generator(
            unit_id="ct",
            name="ct",
            zone="Z",
            fuel_type="gas_ct",
            pmax_mw=80.0,
            pmin_mw=0.0,
            heat_rate=11.0,
            plant_group="CT_PEAKER",
            plant_code=3333,
        ),
    ]
    fa = generators_to_fleet_arrays(gens, ["Z"], hours=hours)
    return fa, {g.plant_code: i for i, g in enumerate(gens)}


class TestReliabilityFloorPlantExclusions(unittest.TestCase):
    """nyiso-140: the per-unit membership correction on a pro-rata limb.

    A persistent-baseline limb is identified on a FLEET-aggregate capacity factor
    but applied per UNIT, so an economically laid-up plant would be held at the
    fleet baseline in every hour (rule 17 [R-FLOOR-WINDOW]).
    """

    def _always_on_spec(self, exclude=frozenset()):
        # threshold well below any real temperature => flagged every hour, the
        # real Long_Island shape (-50 C is never not met).
        return ReliabilityFloorSpec(
            zone="Z",
            plant_class="ST_GAS",
            driver="tmax",
            threshold=-50.0,
            floor_pct=0.262,
            distribution="pro_rata",
            exclude_plant_codes=exclude,
        )

    def test_excluded_plant_is_not_floored_others_unchanged(self):
        H = 48
        loader = _weather_from_daily([12.0, 20.0], [2.0, 8.0], H)
        fa, rows = _build_two_plant_st_fleet(H)
        with mock.patch(_LOADER, loader):
            applied = T.inject_reliability_floor(
                fa, "TEST", 2024, [self._always_on_spec(frozenset({2517}))], ["Z"]
            )
        self.assertTrue(applied)
        keep, drop = rows[1111], rows[2517]
        # The running plant carries the floor in every hour...
        np.testing.assert_allclose(
            fa.min_gen[keep, :], 0.262 * fa.pmax[keep] * fa.availability[keep, :]
        )
        # ...and the laid-up plant carries none.
        np.testing.assert_allclose(fa.min_gen[drop, :], 0.0)
        # A different class in the same zone is untouched either way.
        np.testing.assert_allclose(fa.min_gen[rows[3333], :], 0.0)

    def test_empty_exclusion_is_byte_identical_to_no_exclusion(self):
        H = 48
        loader = _weather_from_daily([12.0, 20.0], [2.0, 8.0], H)
        out = []
        for exclude in (frozenset(), None):
            fa, _ = _build_two_plant_st_fleet(H)
            spec = self._always_on_spec(frozenset())
            if exclude is None:  # a spec predating the field entirely
                spec = ReliabilityFloorSpec(
                    zone="Z",
                    plant_class="ST_GAS",
                    driver="tmax",
                    threshold=-50.0,
                    floor_pct=0.262,
                    distribution="pro_rata",
                )
            with mock.patch(_LOADER, loader):
                T.inject_reliability_floor(fa, "TEST", 2024, [spec], ["Z"])
            out.append(fa.min_gen.copy())
        np.testing.assert_array_equal(out[0], out[1])
        # and both DO floor the plant that the exclusion would have dropped
        self.assertGreater(float(out[0].sum()), 0.0)

    def test_cheapest_first_distribution_also_honours_exclusions(self):
        # The exclusion is applied to row SELECTION, so it must bind on the
        # cheapest-first path too, not only pro-rata.
        H = 24
        loader = _weather_from_daily([12.0], [2.0], H)
        fa, rows = _build_two_plant_st_fleet(H)
        spec = ReliabilityFloorSpec(
            zone="Z",
            plant_class="ST_GAS",
            driver="tmax",
            threshold=-50.0,
            floor_pct=0.262,
            distribution="cheapest_first",
            exclude_plant_codes=frozenset({2517}),
        )
        with mock.patch(_LOADER, loader):
            T.inject_reliability_floor(fa, "TEST", 2024, [spec], ["Z"])
        np.testing.assert_allclose(fa.min_gen[rows[2517], :], 0.0)

    def test_gate_clears_exclusions_unless_armed(self):
        specs = [self._always_on_spec(frozenset({2517}))]

        class _Cfg:
            def __init__(self, armed):
                self.reliability_floor_plant_exclusions = armed

        armed = apply_reliability_floor_plant_exclusions(specs, _Cfg(True))
        disarmed = apply_reliability_floor_plant_exclusions(specs, _Cfg(False))
        self.assertEqual(armed[0].exclude_plant_codes, frozenset({2517}))
        self.assertEqual(disarmed[0].exclude_plant_codes, frozenset())
        # A config that predates the field at all disarms (fail-closed).
        legacy = apply_reliability_floor_plant_exclusions(specs, object())
        self.assertEqual(legacy[0].exclude_plant_codes, frozenset())

    def test_nyiso_csv_carries_the_port_jefferson_exclusion_only(self):
        """Data contract: exactly one limb, the always-on LI base, excludes 2517."""
        specs = RELIABILITY_FLOOR_REGISTRY.get("NYISO", [])
        if not specs:
            self.skipTest("NYISO reliability-floor CSV not present")
        carrying = [s for s in specs if s.exclude_plant_codes]
        self.assertEqual(len(carrying), 1)
        limb = carrying[0]
        self.assertEqual(limb.zone, "Long_Island")
        self.assertEqual(limb.plant_class, "ST_GAS")
        self.assertEqual(limb.exclude_plant_codes, frozenset({2517}))
        # It is the ALWAYS-ON base (no ramp family, no sub-daily window), not an
        # evening ramp knot — the evening limbs are a different phenomenon.
        self.assertIsNone(limb.ramp_group)
        self.assertIsNone(limb.start_hour)

    def test_no_other_iso_carries_an_exclusion(self):
        """Rule 25 [R-ISO-SCOPE]: exclusions exist only where identified in-lane.

        Each allowlisted ISO carries its OWN CAMPD lay-up identification —
        NYISO's Port Jefferson (nyiso-140) and MISO's 15-plant census
        (miso-170, ``derive_campd_bridge_layup_exclusions --iso MISO
        --patch-reliability-coeffs``). No other ISO may carry an exclusion
        without its own derived artifact; a verdict never transfers
        (rule 28(d)). (This pin read "NYISO alone" until miso-170 landed the
        MISO census; the landed CSV made it fail at HEAD and it is corrected
        here with the census it pins.)
        """
        identified = {"NYISO", "MISO"}
        for iso, specs in RELIABILITY_FLOOR_REGISTRY.items():
            if iso in identified:
                continue
            self.assertEqual(
                [s for s in specs if s.exclude_plant_codes],
                [],
                f"{iso} must carry no plant exclusions",
            )

    def test_miso_exclusions_match_the_layup_census_at_site_grain(self):
        """Data contract: MISO limb exclusions = the census, stamped at SITE
        grain (miso-170 K-1 amendment 2026-08-19): a census plant is excluded
        from every limb whose (zone, class) contains any of the site's model
        tranches — the majority-class-only stamping left Burlington (1104)'s
        CT_PEAKER tranches floorable by the Plains CT netload limb while the
        site metered dark in 98.7 % of that floor's binding hours."""
        specs = RELIABILITY_FLOOR_REGISTRY.get("MISO", [])
        if not specs:
            self.skipTest("MISO reliability-floor CSV not present")
        expected = {
            ("MISO-South", "ST_GAS"): frozenset({170, 203, 1464, 8054, 8056}),
            ("MISO-Indiana", "ST_GAS"): frozenset({992, 6639}),
            ("MISO-Plains", "ST_GAS"): frozenset({1104, 1131, 2123}),
            ("MISO-East", "ST_GAS"): frozenset({1702, 3992}),
            ("MISO-West", "ST_GAS"): frozenset({1891}),
            ("MISO-West", "CC_REGULAR"): frozenset({6358}),
            ("MISO-South", "CC_REGULAR"): frozenset({58478}),
            # Site-grain rows: census sites' tranches in OTHER classes.
            ("MISO-Plains", "CT_PEAKER"): frozenset({1104, 2123}),
            ("MISO-South", "CT_PEAKER"): frozenset({1464}),
            ("MISO-West", "CT_PEAKER"): frozenset({6358}),
        }
        carrying = [s for s in specs if s.exclude_plant_codes]
        self.assertGreater(len(carrying), 0)
        for limb in carrying:
            self.assertEqual(
                limb.exclude_plant_codes,
                expected.get((limb.zone, limb.plant_class)),
                f"{limb.zone}:{limb.plant_class}:{limb.driver}",
            )



class TestReliabilityFloorLayupWindowMask(unittest.TestCase):
    """NYISO-NEXT: measured lay-up windows leave the pro_rata floor basis.

    ``ScenarioConfig.reliability_floor_layup_window_mask`` hands the engine the
    guard's plant-hour lay-up shares; a pro_rata limb then floors each unit on
    ``pmax x max(0, availability - layup_share)`` (rule 17 [R-FLOOR-WINDOW]),
    and a cheapest_first limb is untouched.
    """

    def _spec(self, distribution="pro_rata"):
        return ReliabilityFloorSpec(
            zone="Z",
            plant_class="ST_GAS",
            driver="tmax",
            threshold=-50.0,
            floor_pct=0.2,
            distribution=distribution,
        )

    def _run(self, layup, distribution="pro_rata"):
        H = 48
        loader = _weather_from_daily([12.0, 20.0], [2.0, 8.0], H)
        fa, rows = _build_two_plant_st_fleet(H)
        with mock.patch(_LOADER, loader):
            T.inject_reliability_floor(
                fa, "TEST", 2024, [self._spec(distribution)], ["Z"],
                layup_removed=layup,
            )
        return fa, rows

    def test_layup_hours_lose_only_the_laid_up_units_floor(self):
        share = np.zeros(48)
        share[:24] = 1.0  # plant 2517 fully laid up on day 0
        fa, rows = self._run({(2517, "ST_GAS"): share})
        keep, lay = rows[1111], rows[2517]
        np.testing.assert_allclose(
            fa.min_gen[keep, :], 0.2 * fa.pmax[keep] * fa.availability[keep, :]
        )
        np.testing.assert_allclose(fa.min_gen[lay, :24], 0.0)
        np.testing.assert_allclose(
            fa.min_gen[lay, 24:], 0.2 * fa.pmax[lay] * fa.availability[lay, 24:]
        )

    def test_partial_share_clips_at_zero(self):
        share = np.full(48, 0.4)
        fa, rows = self._run({(1111, "ST_GAS"): share})
        r = rows[1111]
        np.testing.assert_allclose(
            fa.min_gen[r, :],
            0.2 * fa.pmax[r] * np.maximum(fa.availability[r, :] - 0.4, 0.0),
        )

    def test_none_and_empty_are_byte_identical_to_unmasked(self):
        base, _ = self._run(None)
        for layup in ({},):
            fa, _ = self._run(layup)
            np.testing.assert_array_equal(fa.min_gen, base.min_gen)

    def test_cheapest_first_limb_is_not_masked(self):
        share = np.ones(48)
        base, _ = self._run(None, "cheapest_first")
        fa, _ = self._run({(1111, "ST_GAS"): share}, "cheapest_first")
        np.testing.assert_array_equal(fa.min_gen, base.min_gen)

    def test_mask_never_raises_a_floor(self):
        share = np.linspace(0.0, 1.0, 48)
        base, _ = self._run(None)
        fa, _ = self._run({(1111, "ST_GAS"): share, (2517, "ST_GAS"): share})
        self.assertTrue((fa.min_gen <= base.min_gen + 1e-12).all())

    def test_consumer_returns_none_when_off_or_forecast(self):
        from scripts.run_calibration import _reliability_floor_layup_shares

        cfg = types.SimpleNamespace(
            reliability_floor_layup_window_mask=False,
            mode="backcast",
            outage_source="historic",
        )
        fa, _ = _build_two_plant_st_fleet(24)
        self.assertIsNone(_reliability_floor_layup_shares(cfg, "NYISO", 2023, fa))
        cfg.reliability_floor_layup_window_mask = True
        cfg.mode = "forecast"
        self.assertIsNone(_reliability_floor_layup_shares(cfg, "NYISO", 2023, fa))
        cfg.mode = "backcast"
        cfg.outage_source = "statistical"
        self.assertIsNone(_reliability_floor_layup_shares(cfg, "NYISO", 2023, fa))

    def test_field_is_default_off_and_registered(self):
        from market_sim.config import scenarios as sc

        self.assertFalse(sc.ScenarioConfig().reliability_floor_layup_window_mask)
        self.assertIn("reliability_floor_layup_window_mask", sc._CACHE_KEY_OPTIONAL_FIELDS)
        self.assertEqual(
            sc._CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["reliability_floor_layup_window_mask"],
            "False",
        )
        self.assertIn(
            "reliability_floor_layup_window_mask", sc._BACKCAST_ONLY_OVERLAY_FIELDS
        )


class TestLayupCompanionResolver(unittest.TestCase):
    """The lay-up resolver selects the companion matching the outage extract."""

    def test_default_is_the_unsuffixed_file(self):
        from market_sim.data.outages import unit_layup_csv_for_iso

        self.assertEqual(
            unit_layup_csv_for_iso("NYISO").name, "campd-unit-outages-layup-NYISO.csv"
        )
        self.assertEqual(
            unit_layup_csv_for_iso("ERCOT", True, True, True).name,
            "campd-unit-outages-layup.csv",
        )

    def test_merit_family_selects_matching_companion(self):
        from market_sim.data.outages import unit_layup_csv_for_iso

        hour = unit_layup_csv_for_iso("NYISO", True, True, True)
        day = unit_layup_csv_for_iso("NYISO", True, True, False)
        if hour.exists():
            self.assertEqual(hour.name, "campd-unit-outages-layup-perunitmerithour-NYISO.csv")
        if day.exists():
            self.assertEqual(day.name, "campd-unit-outages-layup-perunitmerit-NYISO.csv")
        # The guard alone (no per-unit crosswalk) never selects the merit family.
        self.assertEqual(
            unit_layup_csv_for_iso("NYISO", False, True, True).name,
            "campd-unit-outages-layup-NYISO.csv",
        )

if __name__ == "__main__":
    unittest.main()
