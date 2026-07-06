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
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.config.constants import MIN_STABLE_PCT_PHYSICAL
from market_sim.config.iso_configs import ReliabilityFloorSpec
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model import transmission as T

# The derivation lives under scripts/ (not an importable package); load by path
# so the coefficient-magnitude and enable-gate logic can be unit-tested directly.
_REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "derive_reliability_coeffs", str(_REPO / "scripts" / "derive_reliability_coeffs.py")
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

    def test_shipped_neiso_registry_has_the_st_gas_netload_limb(self):
        """The committed NEISO CSV carries the Connecticut ST_GAS netload limb
        (enabled, all-24h, 48h steam event bridging) and keeps the two
        temperature ST_GAS limbs it re-grounds disabled (rule 19)."""
        from market_sim.config.iso_configs import RELIABILITY_FLOOR_REGISTRY

        st = [
            s
            for s in RELIABILITY_FLOOR_REGISTRY.get("NEISO", [])
            if s.plant_class == "ST_GAS"
        ]
        by_driver = {s.driver: s for s in st}
        self.assertIn("netload", by_driver)
        nl = by_driver["netload"]
        self.assertTrue(nl.enabled)
        self.assertEqual(nl.zone, "Connecticut")
        self.assertIsNone(nl.start_hour)
        self.assertIsNone(nl.end_hour)
        self.assertEqual(nl.min_event_hours, 48)
        self.assertFalse(by_driver["tmax"].enabled)
        self.assertFalse(by_driver["tmin"].enabled)


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


if __name__ == "__main__":
    unittest.main()
