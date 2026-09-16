"""EIA-930 ``NG:`` unit-slip screen at the loader seam (lane SPP-41).

Covers :func:`market_sim.data.eia930.actuals._screen_fuel_spike_columns` — the
ONE mechanism (rule 19 ``[R-ONE-MECH]``) that repairs EIA-930 unit-slip hours in
the per-fuel ``NG: <CODE>`` columns. It replaces the builder-local
``build_calibration_reference._screen_fuel_spikes`` (SPP-31), which reached the
``calibration_reference.json`` artifact and nothing else (SPP-31 §3.3).

**The seam is the frame CONSTRUCTOR** (lane NWPP-37, 2026-09-16), not the
reader: ``frames._eia_hourly_frame``, ``frames._eia_hourly_frame_filled``'s
reconstruction branch, and ``actuals.load_eia_hourly_benchmark``'s own parquet
read. SPP-41 applied it at three call sites that were ALL inside
``eia930.actuals``, so the benchmark path, the delivered-profile path and the
ERCOT readers inherited it while the six readers that call ``frames`` directly
— the hydro envelopes, the gas floor, the CAISO solar fraction and the two
neighbour net-load shapes — did not. ``TestScreenOnTheEnvelopePath`` is the
regression pin for that half.

Motivating measurement (SPP-31 §3.2, reproduced by SPP-41 table 0a/0b): the
``SWPP hourly`` extract posts ``NG: WND`` = 3,589,445 MW at h3907 of 2023
(a ~100x unit slip against a 22,597 MW p99.9), inflating SPP 2023 wind by
3.5857 TWh on the bench AND on the model's wind input.

Every fixture is synthetic and lives in a tempdir, so the file runs unchanged
under CI's sparse checkout; the two live pins are ``fulldata``-marked.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import EIA_HOURLY_DIR
from market_sim.data import eia_loader
from market_sim.data.eia930 import actuals
from market_sim.data.eia930.demand import _DEMAND_SPIKE_THRESHOLD
from market_sim.data.eia930.frames import (
    _eia_hourly_frame,
    _eia_hourly_frame_filled,
    _ercot_hourly_frame,
)
from tests.helpers.base import requires_raw

_YEAR = 2023
_SPIKE_HOUR = 4000
_SPIKE_MW = 3_589_445.0  # the measured SWPP 2023 h3907 value
# A second slip, in the hydro column, for the envelope readers (lane NWPP-37).
# The magnitude is the measured NWPP 2025 pooled ``NG: WAT`` artifact hour.
_HYDRO_SPIKE_HOUR = 6817
_HYDRO_SPIKE_MW = 817_202.0


def _wind() -> np.ndarray:
    """A wind-like series: never zero, diurnal + synoptic swing, ~2-18 GW."""
    h = np.arange(HOURS_PER_YEAR)
    return (
        10_000.0
        + 6_000.0 * np.sin(2 * np.pi * h / 24.0)
        + 2_000.0 * np.sin(2 * np.pi * h / 720.0)
    )


def _solar() -> np.ndarray:
    """A solar-like series: zero at night, peaked midday — legitimately spiky."""
    h = np.arange(HOURS_PER_YEAR)
    return np.clip(15_000.0 * np.sin(np.pi * ((h % 24) - 6) / 12.0), 0.0, None) * (
        (h % 24 >= 6) & (h % 24 <= 18)
    )


def _hydro() -> np.ndarray:
    """A hydro-like series: a broad seasonal freshet on a diurnal shape."""
    h = np.arange(HOURS_PER_YEAR)
    return (
        8_000.0
        + 4_000.0 * np.sin(2 * np.pi * (h - 2_000) / HOURS_PER_YEAR)
        + 1_500.0 * np.sin(2 * np.pi * h / 24.0)
    )


def _frame(*, spike: bool, overflow_total: bool = False) -> pd.DataFrame:
    times = pd.date_range(f"{_YEAR}-01-01", periods=HOURS_PER_YEAR, freq="h")
    wind = _wind()
    if spike:
        wind[_SPIKE_HOUR] = _SPIKE_MW
    hydro = _hydro()
    if spike:
        hydro[_HYDRO_SPIKE_HOUR] = _HYDRO_SPIKE_MW
    total = wind + _solar() + 20_000.0
    if overflow_total:
        # PJM 2021 h6981-6983: int32 overflow in the NG total with ordinary
        # NG: fuel cells (SPP-31 §3.2) — the total must NOT be screened.
        total[6981:6984] = 2_147_480_064.0
    return pd.DataFrame(
        {
            "UTC time": times,
            "Local date": times,
            "Local time": times + pd.Timedelta(hours=1),
            "Demand": total + 5.0,
            "NG: WND": wind,
            "NG: SUN": _solar(),
            "NG: WAT": hydro,
            "NG: NG": np.full(HOURS_PER_YEAR, 6_000.0),
            "Net generation": total,
            "Total interchange": np.full(HOURS_PER_YEAR, -5.0),
        }
    )


class _SyntheticExtract(unittest.TestCase):
    ba = "SWPP"
    iso = "SPP"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._dir = Path(self._tmp.name)
        self._patch = mock.patch.object(eia_loader, "EIA_HOURLY_DIR", self._dir)
        self._patch.start()
        _eia_hourly_frame.cache_clear()
        _eia_hourly_frame_filled.cache_clear()
        _ercot_hourly_frame.cache_clear()

    def tearDown(self) -> None:
        self._patch.stop()
        self._tmp.cleanup()
        _eia_hourly_frame.cache_clear()
        _eia_hourly_frame_filled.cache_clear()
        _ercot_hourly_frame.cache_clear()

    def _write(self, frame: pd.DataFrame, ba: str | None = None) -> None:
        frame.to_parquet(self._dir / f"{ba or self.ba} hourly.parquet", index=False)


class TestScreenOnTheBenchmarkPath(_SyntheticExtract):
    """``load_eia_hourly_benchmark`` repairs the slip and nothing else."""

    def test_spike_hour_is_interpolated_from_its_neighbours(self):
        self._write(_frame(spike=True))
        with self.assertLogs("market_sim.data.eia930.actuals", level="WARNING") as cm:
            bench = actuals.load_eia_hourly_benchmark(self.iso, _YEAR)
        self.assertIn("NG: WND", cm.output[0])
        self.assertIn(str(_SPIKE_HOUR), cm.output[0])
        wind = bench["wind"]
        expected = 0.5 * (_wind()[_SPIKE_HOUR - 1] + _wind()[_SPIKE_HOUR + 1])
        self.assertAlmostEqual(wind[_SPIKE_HOUR], expected, places=6)
        # Every other hour is byte-identical to the raw extract.
        mask = np.ones(HOURS_PER_YEAR, dtype=bool)
        mask[_SPIKE_HOUR] = False
        np.testing.assert_array_equal(wind[mask], _wind()[mask])

    def test_clean_series_are_returned_unchanged(self):
        self._write(_frame(spike=False))
        bench = actuals.load_eia_hourly_benchmark(self.iso, _YEAR)
        np.testing.assert_array_equal(bench["wind"], _wind())
        np.testing.assert_array_equal(bench["solar"], _solar())

    def test_legitimately_peaked_solar_is_not_repaired(self):
        """The median limb alone WOULD flag real midday solar; the peak limb
        is what keeps the screen from fabricating a benchmark (SPP-31 §3.1)."""
        self._write(_frame(spike=True))
        solar = _solar()
        median_only = int((solar > _DEMAND_SPIKE_THRESHOLD * np.median(solar)).sum())
        self.assertGreater(median_only, 1_000)  # the limb is load-bearing
        bench = actuals.load_eia_hourly_benchmark(self.iso, _YEAR)
        np.testing.assert_array_equal(bench["solar"], solar)

    def test_net_generation_and_interchange_are_never_screened(self):
        """Scope is the ``NG:`` fuel columns exactly as P9 ruled: the NG total
        (``Net generation``) and TI (``Total interchange``) pass through, so a
        PJM-2021-style overflow in the total is reported, not repaired here."""
        self._write(_frame(spike=False, overflow_total=True))
        bench = actuals.load_eia_hourly_benchmark(self.iso, _YEAR)
        self.assertEqual(float(bench["net_gen"][6982]), 2_147_480_064.0)
        np.testing.assert_array_equal(
            bench["interchange"], np.full(HOURS_PER_YEAR, -5.0)
        )
        np.testing.assert_array_equal(bench["wind"], _wind())


class TestScreenOnTheDeliveredProfilePath(_SyntheticExtract):
    """``load_eia_hourly_renewable_gen`` — the series ``renewables.py`` turns
    into the LP's wind/solar bound — inherits the same repair (SPP-40 §4)."""

    def test_input_path_matches_the_benchmark_path_hour_for_hour(self):
        self._write(_frame(spike=True))
        gen = actuals.load_eia_hourly_renewable_gen(self.iso, _YEAR)
        bench = actuals.load_eia_hourly_benchmark(self.iso, _YEAR)
        np.testing.assert_array_equal(gen["wind"], bench["wind"])
        np.testing.assert_array_equal(gen["solar"], bench["solar"])
        self.assertLess(gen["wind"].max(), 2 * _wind().max())

    def test_the_frame_loader_itself_returns_the_repair(self):
        """The seam is the frame CONSTRUCTOR, not the reader (lane NWPP-37).

        This is the property whose absence was the defect: before that lane
        ``_eia_hourly_frame_filled`` returned the raw column and only the three
        readers in ``actuals`` screened, so every other consumer — the hydro
        envelopes, the gas floor, the neighbour net-load shapes — read the slip.
        """
        self._write(_frame(spike=True))
        frame = _eia_hourly_frame_filled(self.ba, _YEAR)
        self.assertTrue(np.isnan(float(frame["NG: WND"].iloc[_SPIKE_HOUR])))
        # The strict loader and the ERCOT wrapper share the one seam.
        self.assertTrue(
            np.isnan(
                float(_eia_hourly_frame(self.ba, _YEAR)["NG: WND"].iloc[_SPIKE_HOUR])
            )
        )

    def test_re_reading_the_frame_does_not_cascade(self):
        """The screen is NOT idempotent, so it must be applied exactly once.

        Re-running it on an already-screened series recomputes the p99.9 anchor
        with the flagged hours gone, which LOWERS it and can flag further hours
        (measured on live data: PGE 2023 ``NG: OTH`` 81 MW, NEVP 2025
        ``NG: NG`` 20,354 MW, SOCO 2024 ``NG: OIL`` 155 MW). Repeated reads of
        the same (BA, year) must therefore be stable, and the un-flagged hours
        must equal the raw extract exactly.
        """
        self._write(_frame(spike=True))
        first = _eia_hourly_frame_filled(self.ba, _YEAR)["NG: WND"].to_numpy(float)
        _eia_hourly_frame_filled.cache_clear()
        second = _eia_hourly_frame_filled(self.ba, _YEAR)["NG: WND"].to_numpy(float)
        np.testing.assert_array_equal(first, second)
        mask = np.ones(HOURS_PER_YEAR, dtype=bool)
        mask[_SPIKE_HOUR] = False
        np.testing.assert_array_equal(first[mask], _wind()[mask])
        self.assertEqual(int(np.isnan(first).sum()), 1)

    def test_the_pool_cache_is_not_written_through(self):
        """The screen COPIES before it edits, which stays load-bearing.

        ``_pool_hourly_frame`` is itself ``lru_cache``d and its return is
        screened on the way out of ``_eia_hourly_frame``; a repair written in
        place would corrupt the pool cache for every later reader.
        """
        pool = pd.DataFrame({"NG: WND": _wind()})
        pool.loc[_SPIKE_HOUR, "NG: WND"] = _SPIKE_MW
        before = pool["NG: WND"].to_numpy(float).copy()
        out = actuals._screen_fuel_spike_columns(pool, ba_code="POOL", year=_YEAR)
        self.assertIsNot(out, pool)
        np.testing.assert_array_equal(pool["NG: WND"].to_numpy(float), before)
        self.assertTrue(np.isnan(float(out["NG: WND"].iloc[_SPIKE_HOUR])))


class TestScreenOnTheEnvelopePath(_SyntheticExtract):
    """The readers that go through ``frames`` DIRECTLY, never through
    ``actuals`` — the six that were unscreened until lane NWPP-37.

    This class is the regression pin for that lane. Each of these calls
    ``frames._eia_hourly_frame_filled`` itself and reads an ``NG:`` column off
    the result; before the screen moved to the frame constructor, every one of
    them returned the raw slip. Measured consequence for the NWPP pool: one AVA
    hour put +1,166 GWh (14.1 %) into October 2025's pooled hydro, which
    ``measured_monthly_hydro`` handed straight to the hydro budget
    (FINDING-nwpp-32 §7 item 1).
    """

    def test_measured_monthly_hydro_excludes_the_slip(self):
        from market_sim.data.eia930 import envelopes

        self._write(_frame(spike=True))
        got = envelopes.measured_monthly_hydro(self.iso, _YEAR)
        self.assertIsNotNone(got)
        clean = _hydro()
        month = pd.date_range(
            f"{_YEAR}-01-01", periods=HOURS_PER_YEAR, freq="h"
        ).month.to_numpy()
        expect = np.array(
            [float(clean[month == m].sum()) for m in range(1, 13)], dtype=float
        )
        # The flagged hour is dropped (nansum), not interpolated, on this path.
        spike_month = int(month[_HYDRO_SPIKE_HOUR])
        expect[spike_month - 1] -= float(clean[_HYDRO_SPIKE_HOUR])
        np.testing.assert_allclose(got, expect, rtol=0, atol=1e-6)
        self.assertLess(float(got.sum()), float(clean.sum()))

    def test_hydro_envelope_and_min_flow_exclude_the_slip(self):
        from market_sim.data.eia930 import envelopes

        self._write(_frame(spike=True))
        env = envelopes.measured_hydro_hourly_envelope(self.iso, _YEAR, HOURS_PER_YEAR)
        floor = envelopes.measured_hydro_min_flow_level(self.iso, _YEAR)
        self.assertIsNotNone(env)
        self.assertIsNotNone(floor)
        # A percentile ceiling built from a series carrying an 817 GW hour can
        # never exceed the clean fleet's own maximum.
        self.assertLessEqual(float(np.nanmax(env)), float(_hydro().max()))
        self.assertLessEqual(float(np.nanmax(floor)), float(_hydro().max()))

    def test_gas_floor_profile_is_built_off_the_screened_column(self):
        from market_sim.data.eia930 import envelopes

        self._write(_frame(spike=True))
        prof = envelopes.measured_gas_floor_profile(self.iso, _YEAR, HOURS_PER_YEAR)
        self.assertIsNotNone(prof)
        np.testing.assert_allclose(prof, 6_000.0, rtol=0, atol=1e-6)

    def test_the_frames_seam_is_the_only_unscreened_door(self):
        """No reader may reach a raw ``NG:`` column through a public loader.

        ``_eia_hourly_frame_raw`` is the single unscreened constructor and is
        private by contract; both of its callers screen. If a future lane adds
        a loader that returns an unscreened frame, this fails.
        """
        from market_sim.data.eia930 import frames

        self._write(_frame(spike=True))
        raw = frames._eia_hourly_frame_raw(self.ba, _YEAR)
        self.assertEqual(float(raw["NG: WND"].iloc[_SPIKE_HOUR]), _SPIKE_MW)
        for loader in (frames._eia_hourly_frame, frames._eia_hourly_frame_filled):
            frame = loader(self.ba, _YEAR)
            self.assertTrue(
                np.isnan(float(frame["NG: WND"].iloc[_SPIKE_HOUR])),
                f"{loader.__name__} returned an unscreened NG: column",
            )
            self.assertTrue(
                np.isnan(float(frame["NG: WAT"].iloc[_HYDRO_SPIKE_HOUR])),
                f"{loader.__name__} returned an unscreened NG: column",
            )


class TestScreenOnTheErcotReaders(_SyntheticExtract):
    """The ERCOT-specific readers (``run_calibration_full._eia930_frame``'s
    ERCOT branch) obtain their frame through the same seam."""

    ba = "ERCO"
    iso = "ERCOT"

    def test_ercot_renewable_reader_inherits_the_repair(self):
        self._write(_frame(spike=True))
        renew = actuals.load_ercot_renewable_gen(_YEAR)
        expected = 0.5 * (_wind()[_SPIKE_HOUR - 1] + _wind()[_SPIKE_HOUR + 1])
        self.assertAlmostEqual(renew["wind"][_SPIKE_HOUR], expected, places=6)
        np.testing.assert_array_equal(renew["solar"], _solar())


class TestScreenIsParameterFree(unittest.TestCase):
    """Rule 24 ``[R-REGISTRY]``: nothing here is a tunable."""

    def test_factor_is_the_demand_screens_own(self):
        """No second threshold (SPP-31 §3.2): the factor IS the demand screen's."""
        self.assertIs(actuals._FUEL_SPIKE_RATIO, _DEMAND_SPIKE_THRESHOLD)

    def test_scale_anchor_is_the_series_robust_peak(self):
        self.assertEqual(actuals._FUEL_SPIKE_SCALE_PCT, 99.9)

    def test_only_ng_columns_are_in_scope(self):
        frame = pd.DataFrame(
            {
                "Demand": np.r_[np.full(HOURS_PER_YEAR - 1, 100.0), 1e9],
                "NG: WND": np.r_[np.full(HOURS_PER_YEAR - 1, 100.0), 1e9],
            }
        )
        out = actuals._screen_fuel_spike_columns(frame, ba_code="TEST", year=_YEAR)
        self.assertEqual(float(out["Demand"].iloc[-1]), 1e9)
        self.assertTrue(np.isnan(out["NG: WND"].iloc[-1]))
        # And the input frame is untouched.
        self.assertEqual(float(frame["NG: WND"].iloc[-1]), 1e9)


@requires_raw(
    EIA_HOURLY_DIR / "SWPP hourly.parquet", EIA_HOURLY_DIR / "NYIS hourly.parquet"
)
class TestLivePins(unittest.TestCase):
    """The SPP-31 §3.2 two-series table, reproduced from the seam (SPP-41 0a/0b).

    Exactly two benchmark series move across all seven ISOs x 2021-2025, and
    one delivered-profile series; these pin the moved values so a regression
    of the screen — or a silent re-extraction — is caught.
    """

    def test_spp_2023_wind_on_both_paths(self):
        bench = actuals.load_eia_hourly_benchmark("SPP", 2023)
        gen = actuals.load_eia_hourly_renewable_gen("SPP", 2023)
        self.assertAlmostEqual(float(bench["wind"].sum()) / 1e6, 103.0488, places=4)
        self.assertAlmostEqual(float(gen["wind"].sum()) / 1e6, 103.0488, places=4)
        self.assertLess(float(bench["wind"].max()), 30_000.0)

    def test_nyiso_2024_other(self):
        bench = actuals.load_eia_hourly_benchmark("NYISO", 2024)
        self.assertAlmostEqual(float(bench["other"].sum()) / 1e6, 3.3197, places=4)
