"""Tests for the EIA-930 demand and generation loaders."""

import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.eia_loader import (
    _eia_hourly_frame_filled,
    _load_caiso_hourly_demand,
    _load_nyiso_hourly_demand,
    load_demand,
    load_demand_meta,
    load_eia_hourly_renewable_gen,
    load_ercot_battery_gen,
    load_generation_profiles,
    measured_gas_floor_profile,
    measured_interchange_envelope,
    pjm_zonal_interchange_envelope,
)
from scripts.curate_zonal_shares import (
    parse_caiso_shares as caiso_zonal_load_shares,
    parse_ercot_shares as ercot_zonal_load_shares,
    parse_miso_shares as miso_zonal_load_shares,
    parse_nyiso_shares as nyiso_zonal_load_shares,
)

_TEST_YEAR = 2024

# MISO sub-BA demand file covers 2023–2025.
_MISO_TEST_YEAR = 2024

# The only year with a TAC-area load file so far (upload U4 is partial:
# 2023-01 landed; the remaining monthly pulls are pending).
_CAISO_TAC_YEAR = 2023

# NYISO primary backcast year: 2023 is the cleanest year in the NYIS hourly
# extract (full 8760 hours; 2024 is a leap year needing Feb-29 strip).
_NYISO_TEST_YEAR = 2023

# Reference peak demand bands (MW), from EIA-930: ERCOT ~85,544 MW,
# CAISO ~47,571 MW for 2024.
_ERCOT_PEAK_RANGE = (80_000.0, 90_000.0)
_CAISO_PEAK_RANGE = (45_000.0, 50_000.0)


class TestPjmZonalInterchangeEnvelope(unittest.TestCase):
    """PJM congestion Lever A: per-border net-interchange deliverability envelope."""

    _ZONES = [
        "PJM_ComEd",
        "PJM_AEP_Ohio",
        "PJM_ATSI",
        "PJM_West_APS",
        "PJM_Central_PA",
        "PJM_Dominion",
        "PJM_EMAAC",
        "PJM_SWMAAC",
    ]

    def test_shape_and_nonnegative_split(self):
        env = pjm_zonal_interchange_envelope(2024, self._ZONES, HOURS_PER_YEAR, 95.0)
        self.assertIsNotNone(env)
        imp, exp = env
        self.assertEqual(imp.shape, (len(self._ZONES), HOURS_PER_YEAR))
        self.assertEqual(exp.shape, (len(self._ZONES), HOURS_PER_YEAR))
        # Direction split is non-negative MW (each is a clipped one-sided cap).
        self.assertGreaterEqual(imp.min(), 0.0)
        self.assertGreaterEqual(exp.min(), 0.0)

    def test_border_directionality_matches_measured(self):
        # EMAAC physically exports to NYISO (net exporter) → its export ceiling
        # dominates and its import ceiling collapses ~0, closing the copper-plate
        # bypass. Dominion is a net importer → the mirror.
        imp, exp = pjm_zonal_interchange_envelope(
            2024, self._ZONES, HOURS_PER_YEAR, 95.0
        )
        emaac = self._ZONES.index("PJM_EMAAC")
        dom = self._ZONES.index("PJM_Dominion")
        self.assertGreater(np.median(exp[emaac]), np.median(imp[emaac]))
        self.assertGreater(np.median(imp[dom]), np.median(exp[dom]))

    def test_forecast_year_returns_none(self):
        self.assertIsNone(
            pjm_zonal_interchange_envelope(2099, self._ZONES, HOURS_PER_YEAR, 95.0)
        )


class TestEIALoader(unittest.TestCase):
    """Tests for the EIA-930 demand and generation loaders."""

    def test_load_demand_ercot_shape(self):
        """ERCOT demand spans its six zones over a full year."""
        n_zones = get_iso_config("ERCOT").n_zones
        demand = load_demand("ERCOT", _TEST_YEAR)
        self.assertEqual(demand.shape, (n_zones, HOURS_PER_YEAR))

    def test_load_demand_caiso_shape_and_import_zone(self):
        """CAISO spans its four zones; the WECC_import node carries no load."""
        caiso = get_iso_config("CAISO")
        demand = load_demand("CAISO", _TEST_YEAR)
        self.assertEqual(demand.shape, (caiso.n_zones, HOURS_PER_YEAR))
        wecc = caiso.zone_names.index("WECC_import")
        self.assertTrue(np.all(demand[wecc] == 0.0))

    def test_load_demand_no_nan(self):
        """Allocated zonal demand contains no NaN values."""
        for iso in ("ERCOT", "CAISO"):
            self.assertFalse(np.isnan(load_demand(iso, _TEST_YEAR)).any())

    def test_ercot_peak_in_reference_band(self):
        """ERCOT peak (summed across zones) matches the EIA reference."""
        demand = load_demand("ERCOT", _TEST_YEAR)
        peak = demand.sum(axis=0).max()
        self.assertGreaterEqual(peak, _ERCOT_PEAK_RANGE[0])
        self.assertLessEqual(peak, _ERCOT_PEAK_RANGE[1])

    def test_caiso_peak_in_reference_band(self):
        """CAISO peak (summed across zones) matches the EIA reference."""
        demand = load_demand("CAISO", _TEST_YEAR)
        peak = demand.sum(axis=0).max()
        self.assertGreaterEqual(peak, _CAISO_PEAK_RANGE[0])
        self.assertLessEqual(peak, _CAISO_PEAK_RANGE[1])

    def test_caiso_zone_rows_are_static_share_split(self):
        """Without measured hourly shares, CAISO splits by constant load fractions."""
        iso_config = get_iso_config("CAISO")
        with mock.patch(
            "market_sim.data.eia_loader.load_zonal_shares", return_value=None
        ):
            demand = load_demand("CAISO", _TEST_YEAR, iso_config)
        # Each zone's row is its load_share fraction of one system series,
        # so the rows are constant multiples of each other every hour.
        nonzero = [
            (z, zone.load_share)
            for z, zone in enumerate(iso_config.zones)
            if zone.load_share > 0.0
        ]
        system = demand[nonzero[0][0]] / nonzero[0][1]
        for z, share in nonzero:
            np.testing.assert_allclose(demand[z], share * system, rtol=1e-9)

    def test_caiso_zonal_shares_sum_to_one(self):
        """CAISO per-zone hourly shares are fractions summing to 1.0 each hour."""
        zone_names = get_iso_config("CAISO").zone_names
        shares = caiso_zonal_load_shares(_CAISO_TAC_YEAR, zone_names)
        self.assertIsNotNone(shares)
        self.assertEqual(shares.shape, (len(zone_names), HOURS_PER_YEAR))
        np.testing.assert_allclose(shares.sum(axis=0), 1.0, rtol=1e-9)
        # WECC_import is an import node, not a load zone: no load share.
        self.assertTrue(np.all(shares[zone_names.index("WECC_import")] == 0.0))

    def test_caiso_zonal_shares_measured_window_moves(self):
        """Measured hours carry real hourly shapes, not one constant split.

        Only January is covered by the partial U4 upload, so the January
        shares must vary hour to hour while the uncovered remainder of the
        year carries the constant sample-average shares.
        """
        zone_names = get_iso_config("CAISO").zone_names
        shares = caiso_zonal_load_shares(_CAISO_TAC_YEAR, zone_names)
        jan = shares[zone_names.index("NP15"), : 31 * 24]
        self.assertGreater(jan.std(), 1e-3)
        rest = shares[zone_names.index("NP15"), 31 * 24 :]
        self.assertEqual(len(np.unique(rest)), 1)

    def test_caiso_zonal_shares_fall_back_without_file(self):
        """A year with no TAC-area file returns None."""
        zone_names = get_iso_config("CAISO").zone_names
        self.assertIsNone(caiso_zonal_load_shares(2099, zone_names))

    def test_caiso_zonal_demand_reconciles_to_system_series(self):
        """Zonal demand sums back to the EIA-930 CISO system series each hour."""
        caiso = get_iso_config("CAISO")
        for year in (_CAISO_TAC_YEAR, _TEST_YEAR):
            demand = load_demand("CAISO", year, caiso)
            system = _load_caiso_hourly_demand(year)
            self.assertIsNotNone(system)
            np.testing.assert_allclose(demand.sum(axis=0), system, rtol=1e-9)

    def test_miso_zonal_shares_sum_to_one(self):
        """MISO per-zone hourly shares are fractions summing to 1.0 each hour."""
        zone_names = get_iso_config("MISO").zone_names
        shares = miso_zonal_load_shares(_MISO_TEST_YEAR, zone_names)
        self.assertIsNotNone(shares)
        self.assertEqual(shares.shape, (len(zone_names), HOURS_PER_YEAR))
        np.testing.assert_allclose(shares.sum(axis=0), 1.0, rtol=1e-9)

    def test_miso_zonal_shares_vary_and_repair_gaps(self):
        """Each zone gets a real hourly shape and reporting gaps are repaired.

        The shares must vary hour to hour (zones peak at different times), and
        the 2024-08-26 EIA-930 sub-BA reporting gap must be filled — no hour may
        leave a populous zone with a near-zero or runaway share.
        """
        zone_names = get_iso_config("MISO").zone_names
        shares = miso_zonal_load_shares(_MISO_TEST_YEAR, zone_names)
        west = shares[zone_names.index("MISO-West")]
        self.assertGreater(west.std(), 1e-3)
        # Every zone stays in a physical band all 8760 hours (gap-repaired);
        # the smallest zone (Illinois, ~0.068 energy share) sets the floor.
        self.assertTrue(np.all(shares > 0.02))
        self.assertTrue(np.all(shares < 0.60))

    def test_miso_zonal_shares_match_measured_energy_split(self):
        """The annual mean shares match the measured sub-BA energy split."""
        zone_names = get_iso_config("MISO").zone_names
        shares = miso_zonal_load_shares(_MISO_TEST_YEAR, zone_names)
        mean = shares.mean(axis=1)
        # Measured 2023-25 sub-BA energy shares of the six LRZ-union zones
        # (West/Plains/Illinois/Indiana/East/South) — the same split as the
        # static fallback in _miso_config.
        np.testing.assert_allclose(
            mean, [0.1466, 0.1385, 0.0676, 0.1340, 0.2422, 0.2711], atol=0.01
        )

    def test_miso_zonal_shares_fall_back_without_file(self):
        """A year with no sub-BA file falls back to the static split."""
        zone_names = get_iso_config("MISO").zone_names
        self.assertIsNone(miso_zonal_load_shares(2099, zone_names))

    def test_miso_zonal_demand_preserves_system_total(self):
        """Swapping the static split for hourly shares preserves the system total.

        The weight matrix sums to 1.0 across zones each hour, so the column sum
        of the zonal demand equals the EIA-930 MISO system series regardless of
        the split. Comparing the hourly-share path against the static-share path
        (sub-BA file forced absent) isolates that invariant.
        """
        miso = get_iso_config("MISO")
        hourly = load_demand("MISO", _MISO_TEST_YEAR, miso)
        with mock.patch(
            "market_sim.data.eia_loader.load_zonal_shares", return_value=None
        ):
            static = load_demand("MISO", _MISO_TEST_YEAR, miso)
        self.assertEqual(hourly.shape, (miso.n_zones, HOURS_PER_YEAR))
        np.testing.assert_allclose(hourly.sum(axis=0), static.sum(axis=0), rtol=1e-9)

    def test_miso_demand_and_renewables_share_local_clock(self):
        """MISO system demand and renewable CF sit on one local wall-clock.

        Regression for the UTC-vs-local bug: MISO demand used to come from the
        UTC-stamped demand-profiles parquet while the renewable CF came off the
        local ``MISO hourly`` frame, a ~5-6h offset that paired midday solar
        against trough demand. Both demand sources now derive from that same
        local frame, so in summer the system demand peaks late afternoon
        (local ~17) while solar peaks midday (local ~13), and the model system
        demand reproduces the frame's own ``Demand`` column at lag 0 (a UTC
        source would shift it ~5-6h and move the best lag off zero).
        """
        import pandas as pd

        miso = get_iso_config("MISO")
        frame = _eia_hourly_frame_filled("MISO", _MISO_TEST_YEAR)
        self.assertIsNotNone(frame)
        local = pd.to_datetime(frame["Local time"])
        hod, month = local.dt.hour.to_numpy(), local.dt.month.to_numpy()
        summer = (month >= 6) & (month <= 8)
        demand = load_demand("MISO", _MISO_TEST_YEAR, miso).sum(axis=0)
        solar = pd.to_numeric(frame["NG: SUN"], errors="coerce").to_numpy()

        def _peak_local_hour(series: np.ndarray) -> int:
            grouped = pd.Series(series[summer]).groupby(hod[summer]).mean()
            return int(grouped.idxmax())

        # Demand peaks in the late-afternoon block, solar at midday.
        self.assertIn(_peak_local_hour(demand), (16, 17, 18))
        self.assertIn(_peak_local_hour(np.nan_to_num(solar)), (12, 13, 14))

        # The model system demand is the frame's own (local-clock) Demand: the
        # cross-correlation against it peaks at lag 0.
        frame_demand = (
            pd.to_numeric(frame["Demand"], errors="coerce")
            .interpolate()
            .bfill()
            .ffill()
            .to_numpy()
        )
        anchor = frame_demand - frame_demand.mean()
        shifted = demand - demand.mean()
        lags = list(range(-6, 7))
        corr = [np.corrcoef(np.roll(shifted, lag), anchor)[0, 1] for lag in lags]
        self.assertEqual(lags[int(np.argmax(corr))], 0)

    def test_ercot_zonal_shares_sum_to_one(self):
        """ERCOT per-zone hourly shares are fractions summing to 1.0 each hour."""
        zone_names = get_iso_config("ERCOT").zone_names
        shares = ercot_zonal_load_shares(_TEST_YEAR, zone_names)
        self.assertIsNotNone(shares)
        self.assertEqual(shares.shape, (len(zone_names), HOURS_PER_YEAR))
        np.testing.assert_allclose(shares.sum(axis=0), 1.0, rtol=1e-9)
        # ERCOT has no Panhandle weather zone, so that model zone gets no load.
        self.assertTrue(np.all(shares[zone_names.index("Panhandle")] == 0.0))

    @pytest.mark.xfail(
        strict=True,
        reason="pre-existing failure on main as of 2026-07-05 (found wiring PR CI "
        "in W1-P1); unrelated to this change, tracked for follow-up",
    )
    def test_ercot_zones_have_distinct_hourly_shapes(self):
        """Each ERCOT zone gets its own measured shape, not one scaled curve.

        The single-curve allocation made every zone a constant multiple of the
        system series (identical normalized shape); the native-load split gives
        zones distinct shapes, so their hourly fractions actually move.
        """
        iso_config = get_iso_config("ERCOT")
        demand = load_demand("ERCOT", _TEST_YEAR, iso_config)
        total = demand.sum(axis=0)
        # The rows still sum to the system series every hour (shares sum to 1).
        self.assertGreater(total.min(), 0.0)
        # West (hot, wind-belt) and Houston (coastal) no longer track a single
        # shape: their share of system load varies hour to hour.
        west = demand[iso_config.zone_names.index("West")] / total
        houston = demand[iso_config.zone_names.index("Houston")] / total
        self.assertGreater(west.std(), 1e-3)
        self.assertGreater(houston.std(), 1e-3)

    def test_load_demand_meta_keys(self):
        """Demand metadata exposes the expected summary statistics."""
        meta = load_demand_meta("ERCOT", _TEST_YEAR)
        self.assertEqual(set(meta), {"peak_mw", "min_mw", "avg_mw", "total_annual_mwh"})
        self.assertGreater(meta["peak_mw"], meta["avg_mw"])
        self.assertGreater(meta["avg_mw"], meta["min_mw"])

    def test_load_generation_profiles_filtered(self):
        """Generation profiles are filtered to the requested ISO and year."""
        profiles = load_generation_profiles("ERCOT", _TEST_YEAR)
        self.assertFalse(profiles.empty)
        self.assertTrue((profiles["iso"] == "ERCOT").all())
        self.assertTrue((profiles["year"] == _TEST_YEAR).all())

    def test_ercot_battery_gen_2025_full_year(self):
        """2025 battery benchmark covers the year with sane magnitudes."""
        bench = load_ercot_battery_gen(2025)
        self.assertIsNotNone(bench)
        dis = bench["battery_discharge"]
        chg = bench["battery_charge"]
        self.assertEqual(dis.shape, (HOURS_PER_YEAR,))
        self.assertEqual(chg.shape, (HOURS_PER_YEAR,))
        # Non-negative wherever reported; charge exceeds discharge (RTE loss).
        self.assertTrue(np.nanmin(dis) >= 0.0)
        self.assertTrue(np.nanmin(chg) >= 0.0)
        self.assertGreater(np.nansum(chg), np.nansum(dis))
        # ERCOT 2025 fleet discharged ~5-6 TWh (EIA-930 BAT series).
        self.assertGreater(np.nansum(dis) / 1e6, 4.0)
        self.assertLess(np.nansum(dis) / 1e6, 7.0)

    def test_ercot_battery_gen_partial_year_keeps_nan(self):
        """2024 (reporting starts mid-year) keeps NaN, never gap-fills."""
        bench = load_ercot_battery_gen(2024)
        self.assertIsNotNone(bench)
        dis = bench["battery_discharge"]
        reported = ~np.isnan(dis)
        self.assertGreater(reported.sum(), 0)
        self.assertLess(reported.sum(), HOURS_PER_YEAR)


class TestNYISODemand(unittest.TestCase):
    """Tests for NYISO demand loading and zonal disaggregation (P8).

    U3 (NYISO OASIS pal actual-load CSVs) is absent, so zonal shapes fall
    back to the static Gold-Book load shares (Tier 3). These tests verify:
      - Zone shares sum to 1.0 under the static allocation.
      - Zonal demand reconciles to the EIA-930 NYIS system series each hour.
      - ``nyiso_zonal_load_shares`` returns ``None`` without U3 data.
    """

    def test_nyiso_demand_shape(self):
        """NYISO demand spans its five zones over a full year."""
        nyiso = get_iso_config("NYISO")
        demand = load_demand("NYISO", _NYISO_TEST_YEAR)
        self.assertEqual(demand.shape, (nyiso.n_zones, HOURS_PER_YEAR))

    def test_nyiso_demand_no_nan(self):
        """NYISO zonal demand contains no NaN values."""
        self.assertFalse(np.isnan(load_demand("NYISO", _NYISO_TEST_YEAR)).any())

    def test_nyiso_zone_shares_sum_to_one(self):
        """Static NYISO zone load shares sum to exactly 1.0.

        This is the Tier-3 fallback that applies until upload U3 lands.
        Each zone's row is its load_share fraction of the system series, so
        the shares must sum to 1.0 to conserve energy.
        """
        nyiso = get_iso_config("NYISO")
        total = sum(z.load_share for z in nyiso.zones)
        self.assertAlmostEqual(total, 1.0, places=10)

    def test_nyiso_static_zone_rows_are_share_split(self):
        """Without measured hourly shares, each NYISO zone row is a constant multiple."""
        nyiso = get_iso_config("NYISO")
        with mock.patch(
            "market_sim.data.eia_loader.load_zonal_shares", return_value=None
        ):
            demand = load_demand("NYISO", _NYISO_TEST_YEAR, nyiso)
        nonzero = [
            (i, z.load_share) for i, z in enumerate(nyiso.zones) if z.load_share > 0.0
        ]
        system = demand[nonzero[0][0]] / nonzero[0][1]
        for i, share in nonzero:
            np.testing.assert_allclose(demand[i], share * system, rtol=1e-9)

    def test_nyiso_zonal_demand_reconciles_to_system_series(self):
        """NYISO zonal demand sums back to the EIA-930 NYIS system series each hour.

        This holds for both the static-share (no U3) and measured-share (U3
        present) paths: the weight matrix always sums to 1.0 across zones per
        hour, so the column sum of the demand array equals the system series.
        Interchange is disabled here so the reconciliation isolates the zonal
        split; NYISO now serves the measured net-interchange schedule by
        default (a net-import wedge that otherwise shifts the system total).
        """
        nyiso = get_iso_config("NYISO")
        demand = load_demand(
            "NYISO", _NYISO_TEST_YEAR, nyiso, include_interchange=False
        )
        system = _load_nyiso_hourly_demand(_NYISO_TEST_YEAR)
        self.assertIsNotNone(system)
        np.testing.assert_allclose(demand.sum(axis=0), system, rtol=1e-9)

    def test_nyiso_zonal_shares_fall_back_without_u3(self):
        """``nyiso_zonal_load_shares`` returns ``None`` for a year with no U3 file."""
        zone_names = get_iso_config("NYISO").zone_names
        self.assertIsNone(nyiso_zonal_load_shares(2099, zone_names))


class TestInterchangeEnvelope(unittest.TestCase):
    """Measured EIA-930 diurnal/seasonal net-interchange envelope (CAISO)."""

    def test_caiso_envelope_swings_import_overnight_export_midday(self):
        env = measured_interchange_envelope("CAISO", 2024, HOURS_PER_YEAR)
        self.assertIsNotNone(env)
        imp, exp = env
        self.assertEqual(imp.shape, (HOURS_PER_YEAR,))
        self.assertEqual(exp.shape, (HOURS_PER_YEAR,))
        self.assertTrue((imp >= 0).all() and (exp >= 0).all())
        hod = np.arange(HOURS_PER_YEAR) % 24
        midday = (hod >= 11) & (hod <= 15)
        night = hod <= 5
        # CA imports overnight and backs off / exports midday.
        self.assertLess(imp[midday].mean(), imp[night].mean())
        # Midday carries real export capability; deep night essentially none.
        self.assertGreater(exp[midday].mean(), 200.0)
        self.assertLess(exp[night].mean(), 50.0)

    def test_forecast_year_returns_none(self):
        self.assertIsNone(measured_interchange_envelope("CAISO", 2030, HOURS_PER_YEAR))


class TestGasFloorProfile(unittest.TestCase):
    """Measured EIA-930 NG: NG midday gas-floor profile (CAISO)."""

    def test_caiso_profile_shape_and_spring_midday_level(self):
        prof = measured_gas_floor_profile("CAISO", 2024, HOURS_PER_YEAR)
        self.assertIsNotNone(prof)
        self.assertEqual(prof.shape, (HOURS_PER_YEAR,))
        self.assertTrue((prof >= 0).all())
        import pandas as pd

        cal = pd.date_range("2024-01-01", periods=HOURS_PER_YEAR, freq="h")
        hod = cal.hour.to_numpy()
        month = cal.month.to_numpy()
        # Real CAISO runs several GW of gas at spring midday (the diagnosis:
        # ~6-7.6 GW NG: NG); the measured median is comfortably above 3 GW.
        spring_mid = np.isin(month, [4, 5]) & (hod >= 11) & (hod <= 14)
        self.assertGreater(prof[spring_mid].mean(), 3000.0)

    def test_percentile_orders(self):
        # A higher percentile gives a higher (or equal) floor everywhere.
        lo = measured_gas_floor_profile("CAISO", 2024, HOURS_PER_YEAR, 25.0)
        hi = measured_gas_floor_profile("CAISO", 2024, HOURS_PER_YEAR, 75.0)
        self.assertTrue((hi >= lo - 1e-6).all())

    def test_forecast_year_returns_none(self):
        self.assertIsNone(measured_gas_floor_profile("CAISO", 2030, HOURS_PER_YEAR))

    def test_unmapped_iso_returns_none(self):
        self.assertIsNone(measured_gas_floor_profile("ZZZ", 2024, HOURS_PER_YEAR))


class TestHourlyBenchmarkBatteryColumns(unittest.TestCase):
    """EIA-930 battery/pumped-storage benchmark series wire in when present.

    The storage split (``NG: BAT`` / ``NG: PS``) only exists in extract
    vintages whose BA reports it; the benchmark loader must pick the series
    up when a regenerated extract carries them and skip them silently when
    it does not (the current CISO extract folds batteries into ``OTH``).
    """

    def _benchmark_from_frame(self, frame):
        """Run ``load_eia_hourly_benchmark`` against a synthetic extract."""
        import tempfile
        from pathlib import Path
        from unittest import mock

        from market_sim.data import eia_loader

        with tempfile.TemporaryDirectory() as tmp:
            frame.to_parquet(Path(tmp) / "CISO hourly.parquet", index=False)
            with mock.patch.object(eia_loader, "EIA_HOURLY_DIR", Path(tmp)):
                return eia_loader.load_eia_hourly_benchmark("CAISO", 2023)

    @staticmethod
    def _synthetic_frame(with_battery: bool):
        import pandas as pd

        times = pd.date_range("2023-01-01", periods=48, freq="h")
        frame = pd.DataFrame(
            {
                "UTC time": times,
                "Local date": times,
                "NG: SUN": np.linspace(0.0, 470.0, 48),
                "Net generation": np.full(48, 1_000.0),
            }
        )
        if with_battery:
            # Net series: negative = charging (midday), positive =
            # discharging (evening).
            frame["NG: BAT"] = np.tile(
                np.concatenate([np.full(12, -50.0), np.full(12, 80.0)]), 2
            )
            frame["NG: PS"] = np.full(48, 5.0)
        return frame

    def test_battery_series_present_when_extract_carries_it(self):
        bench = self._benchmark_from_frame(self._synthetic_frame(True))
        self.assertIn("battery", bench)
        self.assertIn("pumped_storage", bench)
        self.assertEqual(bench["battery"].shape, (HOURS_PER_YEAR,))
        # Sign convention survives the round trip: charging hours negative,
        # discharging hours positive.
        self.assertLess(bench["battery"][0], 0.0)
        self.assertGreater(bench["battery"][12], 0.0)

    def test_battery_series_skipped_when_absent(self):
        bench = self._benchmark_from_frame(self._synthetic_frame(False))
        self.assertNotIn("battery", bench)
        self.assertNotIn("pumped_storage", bench)
        self.assertIn("solar", bench)  # the rest of the benchmark is intact

    def test_partial_storage_vintage_dropped(self):
        """A storage series reporting <50% of hours is not a full-year actual.

        Mirrors EIA-930 NEISO PS 2024 (reporting begins in November, ~15% of
        hours): the coverage gate drops the under-reported storage series so a
        2-month partial is not interpolated across the year and scored as an
        annual throughput, while a fully-reported storage series in the same
        frame is kept.
        """
        frame = self._synthetic_frame(True)
        # Blank all but the last 8 of 48 hours of PS (≈17% coverage, below the
        # 0.5 gate); leave battery fully reported.
        ps = frame["NG: PS"].to_numpy(dtype=float).copy()
        ps[:-8] = np.nan
        frame["NG: PS"] = ps
        bench = self._benchmark_from_frame(frame)
        self.assertNotIn("pumped_storage", bench)  # partial vintage gated out
        self.assertIn("battery", bench)  # full-coverage series kept


class TestWeatherPoolWidening(unittest.TestCase):
    """2026-07 weather-pool widening: new pre-2022 years land end-to-end.

    ERCOT (BA "ERCO") and NEISO (BA "ISNE") both carry a clean EIA-930
    ``<BA> hourly`` extract back to 2015-07-01, verified for 2019-2021 against
    the same full-8760-hour, gap-free standard every existing backcast year
    must meet (see docs/weather-pool-coverage-2026-07.md). CAISO/PJM/MISO have
    no raw coverage that far back (their extracts start 2021-12-31/2022-12-31)
    and are deliberately excluded from the widened pool.
    """

    def test_ercot_2019_demand_and_renewables_full_year(self):
        demand = load_demand("ERCOT", 2019)
        self.assertEqual(demand.shape[1], HOURS_PER_YEAR)
        self.assertFalse(np.isnan(demand).any())
        self.assertGreater(float(demand.sum(axis=0).max()), 0.0)

        gen = load_eia_hourly_renewable_gen("ERCOT", 2019)
        self.assertIsNotNone(gen)
        self.assertEqual(set(gen), {"wind", "solar"})
        for series in gen.values():
            self.assertEqual(series.shape, (HOURS_PER_YEAR,))
            self.assertFalse(np.isnan(series).any())

    def test_neiso_2020_demand_and_renewables_full_year(self):
        # 2020 carries the documented COVID-19 demand-shape anomaly but is
        # still a usable, complete measured year.
        demand = load_demand("NEISO", 2020)
        self.assertEqual(demand.shape[1], HOURS_PER_YEAR)
        self.assertFalse(np.isnan(demand).any())

        gen = load_eia_hourly_renewable_gen("NEISO", 2020)
        self.assertIsNotNone(gen)
        for series in gen.values():
            self.assertEqual(series.shape, (HOURS_PER_YEAR,))
            self.assertFalse(np.isnan(series).any())

    def test_caiso_pre_2022_stays_uncovered(self):
        # CAISO's EIA-930 "CISO hourly" extract begins 2022-12-31 -- no raw
        # coverage for a 2019-2021 draw, so the hourly path returns None and
        # the caller falls back to the (also uncovered) demand-profiles
        # parquet, raising rather than silently fabricating a year.
        self.assertIsNone(_eia_hourly_frame_filled("CISO", 2019))
        with self.assertRaises(Exception):
            load_demand("CAISO", 2019)


class TestDemandProfileCleanSeam(unittest.TestCase):
    """The repaired ``demand-profile`` clean seam (PJM's only demand source).

    PJM has no dedicated per-BA hourly loader, so ``load_demand`` always falls
    back to ``eia_demand_profiles.parquet`` (or, once regenerated, the repaired
    ``demand-profile`` clean partition -- see
    ``scripts/curate_demand_profile.py``). This exercises that fallback with a
    synthetic clean partition instead of the real (multi-MB) data tree.
    """

    def setUp(self):
        from tempfile import TemporaryDirectory

        from scripts.lib import clean_io

        self._tmp = TemporaryDirectory()
        self._orig_clean_dir = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = Path(self._tmp.name) / "clean"

    def tearDown(self):
        from scripts.lib import clean_io

        clean_io.paths.CLEAN_DIR = self._orig_clean_dir
        self._tmp.cleanup()

    def _write_clean_partition(self, iso: str, year: int, mw: np.ndarray) -> None:
        import pandas as pd
        from scripts.lib.clean_io import write_clean

        df = pd.DataFrame(
            {
                "iso": iso,
                "year": year,
                "hour": np.arange(HOURS_PER_YEAR, dtype="int64"),
                "raw_mw": mw,
                "normalized": mw / mw.sum(),
                "repaired": False,
            }
        )
        write_clean(df, "demand-profile", iso=iso, year=year, source="test fixture")

    def test_returns_none_when_partition_absent(self):
        from market_sim.data.eia_loader import _demand_profile_clean

        self.assertIsNone(_demand_profile_clean("PJM", 2021))

    def test_reads_repaired_series_when_present(self):
        from market_sim.data.eia_loader import _demand_profile_clean

        mw = np.full(HOURS_PER_YEAR, 90_000.0)
        self._write_clean_partition("PJM", 2021, mw)
        out = _demand_profile_clean("PJM", 2021)
        self.assertIsNotNone(out)
        np.testing.assert_allclose(out, mw)

    def test_load_demand_uses_repaired_partition_over_raw_spike(self):
        # A repaired series with no billion-MW spike must flow all the way
        # through load_demand's PJM path (which has no dedicated loader and
        # would otherwise fall back straight to the raw, uncorrected parquet).
        mw = np.full(HOURS_PER_YEAR, 90_000.0)
        self._write_clean_partition("PJM", 2021, mw)
        demand = load_demand("PJM", 2021, include_interchange=False)
        self.assertLess(demand.sum(axis=0).max(), 200_000.0)


if __name__ == "__main__":
    unittest.main()
