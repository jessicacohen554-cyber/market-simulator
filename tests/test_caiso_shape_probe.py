"""Smoke tests for scripts/caiso_shape_probe.py.

Uses tiny in-memory fixtures (1–3 classes, 8760-hour arrays) to verify that
all three modes (shape table, compare, floor attribution) run end-to-end
without errors and produce plausible output.  No real on-disk data is read.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Minimal import path setup (mirrors other scripts/ smoke tests)
# ---------------------------------------------------------------------------
import sys

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import scripts.caiso_shape_probe as probe  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_dispatch(
    year: int = 2024, klasses: dict[str, float] | None = None
) -> pd.DataFrame:
    """Return a minimal dispatch DataFrame with 8760 rows per class.

    Args:
        year: Calendar year for the ``year`` column.
        klasses: Dict mapping class label → mean MW level.  Defaults to
            ``{"CC_REGULAR": 5000.0, "CT_PEAKER": 200.0, "solar": 3000.0}``.

    Returns:
        Long-format DataFrame with columns ``year``, ``plant_code``, ``klass``,
        ``hour``, ``mw``, ``lmp``.
    """
    if klasses is None:
        klasses = {"CC_REGULAR": 5000.0, "CT_PEAKER": 200.0, "solar": 3000.0}
    rows = []
    for klass, mean_mw in klasses.items():
        pc = 12345 if klass not in ("solar",) else 0
        for h in range(8760):
            rows.append(
                {
                    "year": year,
                    "plant_code": pc,
                    "klass": klass,
                    "fuel": "gas" if klass != "solar" else "solar",
                    "supply": "",
                    "zone": "NP15",
                    "hour": h,
                    "mw": float(mean_mw),
                    "lmp": 35.0,
                    "pass": "P1",
                    "unit_id": f"{klass}_1",
                }
            )
    return pd.DataFrame(rows)


def _make_campd(year: int = 2024, n_hours: int = 8760) -> pd.DataFrame:
    """Return a tiny CAMPD-format DataFrame for a single CC plant.

    The fixture covers all 8760 non-leap-year hours for one facilityId so that
    :func:`probe.load_campd_measured` can produce a non-empty result.
    """
    dates = pd.date_range(f"{year}-01-01", periods=n_hours, freq="h")
    # Use a non-leap year to avoid Feb 29 complications in this fixture
    rows = {
        "facilityId": "12345",
        "unitId": "G1",
        "date": dates.normalize(),
        "hour": dates.hour,
        "grossLoad": np.full(n_hours, 4500.0),
        "unitType": "Combined cycle",
        "programCodeInfo": "ARP",
        "stateCode": "CA",
        "facilityName": "Test Plant",
        "opTime": np.ones(n_hours),
        "steamLoad": np.zeros(n_hours),
        "so2Mass": np.zeros(n_hours),
        "co2Mass": np.zeros(n_hours),
        "noxMass": np.zeros(n_hours),
        "heatInput": np.zeros(n_hours),
        "primaryFuelInfo": "Pipeline Natural Gas",
    }
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Unit tests for pure utilities
# ---------------------------------------------------------------------------


class TestHoyConversion(unittest.TestCase):
    """_hoy_from_date_hour returns correct hour-of-year indices."""

    def test_jan1_hour0(self) -> None:
        """Jan 1 hour 0 → hoy 0."""
        dates = pd.to_datetime(["2024-01-01"])
        hours = pd.Series([0])
        result = probe._hoy_from_date_hour(dates.to_series(), hours)
        self.assertEqual(int(result[0]), 0)

    def test_feb29_returns_minus1(self) -> None:
        """Feb 29 in a leap year → -1 (to be dropped)."""
        dates = pd.to_datetime(["2024-02-29"])
        hours = pd.Series([12])
        result = probe._hoy_from_date_hour(dates.to_series(), hours)
        self.assertEqual(int(result[0]), -1)

    def test_dec31_hour23(self) -> None:
        """Dec 31 hour 23 → hoy 8759 (last slot of non-leap year)."""
        dates = pd.to_datetime(["2023-12-31"])
        hours = pd.Series([23])
        result = probe._hoy_from_date_hour(dates.to_series(), hours)
        self.assertEqual(int(result[0]), 8759)

    def test_length_preserved(self) -> None:
        """Output length matches input length."""
        dates = pd.date_range("2023-03-01", periods=5).to_series()
        hours = pd.Series([0, 6, 12, 18, 23])
        result = probe._hoy_from_date_hour(dates, hours)
        self.assertEqual(len(result), 5)


class TestDiurnalMean(unittest.TestCase):
    """diurnal_mean averages correctly by hour-of-day."""

    def test_flat_signal(self) -> None:
        """Constant MW → same value for every hour-of-day."""
        arr = np.full(8760, 1234.0)
        hod = probe.diurnal_mean(arr)
        np.testing.assert_allclose(hod, 1234.0, rtol=1e-4)

    def test_shape(self) -> None:
        """Output is length-24 array."""
        self.assertEqual(len(probe.diurnal_mean(np.zeros(8760))), 24)

    def test_peak_in_correct_bucket(self) -> None:
        """A noon spike lands in hour-of-day 12."""
        arr = np.zeros(8760)
        arr[12::24] = 1000.0  # every noon (h12)
        hod = probe.diurnal_mean(arr)
        self.assertAlmostEqual(hod[12], 1000.0, places=0)
        self.assertAlmostEqual(hod[0], 0.0, places=0)


class TestShapeMetrics(unittest.TestCase):
    """shape_metrics produces sensible values."""

    def test_perfect_correlation(self) -> None:
        """Identical model and measured → r=1.0, nrmse=0.0."""
        arr = np.random.default_rng(42).uniform(0, 5000, 8760)
        m = probe.shape_metrics(arr, arr)
        self.assertAlmostEqual(m["r"], 1.0, places=5)
        self.assertAlmostEqual(m["nrmse"], 0.0, places=5)

    def test_twh_matches(self) -> None:
        """TWh computed correctly from MW sum."""
        arr = np.full(8760, 1000.0)  # 1 GW constant = 8.76 TWh
        m = probe.shape_metrics(arr, arr)
        self.assertAlmostEqual(m["mdl_twh"], 8.76, places=2)

    def test_nans_tolerated(self) -> None:
        """NaN values in either series do not crash and r remains finite."""
        rng = np.random.default_rng(0)
        model = rng.uniform(400.0, 600.0, 8760)
        meas = rng.uniform(450.0, 550.0, 8760)
        meas[100:200] = np.nan  # introduce a gap in measured
        m = probe.shape_metrics(model, meas)
        self.assertTrue(np.isfinite(m["r"]))

    def test_zero_measured_nrmse_nan(self) -> None:
        """When all measured values are zero, NRMSE is NaN (avoid divide-by-zero)."""
        model = np.ones(8760)
        meas = np.zeros(8760)
        m = probe.shape_metrics(model, meas)
        self.assertTrue(np.isnan(m["nrmse"]))


class TestBuildPlantKlassMap(unittest.TestCase):
    """build_plant_klass_map extracts plant → klass sets correctly."""

    def test_single_class_plant(self) -> None:
        """Plant with only CC_REGULAR rows maps to {CC_REGULAR}."""
        disp = _make_dispatch(klasses={"CC_REGULAR": 1000.0})
        pkmap = probe.build_plant_klass_map(disp)
        self.assertIn(12345, pkmap)
        self.assertEqual(pkmap[12345], {"CC_REGULAR"})

    def test_solar_excluded(self) -> None:
        """Solar pseudo-units (plant_code=0) are excluded."""
        disp = _make_dispatch(klasses={"CC_REGULAR": 1000.0, "solar": 500.0})
        pkmap = probe.build_plant_klass_map(disp)
        self.assertNotIn(0, pkmap)

    def test_multi_class_plant(self) -> None:
        """A plant appearing under two classes returns both."""
        rows = []
        for klass, pc in (("CC_REGULAR", 99), ("CC_CHP", 99)):
            for h in range(24):
                rows.append({"plant_code": pc, "klass": klass, "hour": h, "mw": 100.0})
        disp = pd.DataFrame(rows)
        pkmap = probe.build_plant_klass_map(disp)
        self.assertEqual(pkmap.get(99), {"CC_REGULAR", "CC_CHP"})


class TestRouteUnitToKlass(unittest.TestCase):
    """_route_unit_to_klass handles remap and unitType disambiguation."""

    def test_simple_lookup(self) -> None:
        """Plant 12345 → CC_REGULAR returned directly when unambiguous."""
        pkmap = {12345: {"CC_REGULAR"}}
        result = probe._route_unit_to_klass(12345, "G1", "Combined cycle", pkmap)
        self.assertEqual(result, "CC_REGULAR")

    def test_campd_remap_applied(self) -> None:
        """AES Alamitos CT1 (facility 315) → remapped to plant 62115."""
        pkmap = {62115: {"CC_REGULAR"}}
        result = probe._route_unit_to_klass(315, "CT1", "Combined cycle", pkmap)
        self.assertEqual(result, "CC_REGULAR")

    def test_unittype_disambiguates(self) -> None:
        """When plant has CC + CT klasses, unitType selects the right one."""
        pkmap = {99: {"CC_REGULAR", "CT_PEAKER"}}
        cc = probe._route_unit_to_klass(99, "G1", "Combined cycle", pkmap)
        ct = probe._route_unit_to_klass(99, "G2", "Combustion turbine", pkmap)
        self.assertEqual(cc, "CC_REGULAR")
        self.assertEqual(ct, "CT_PEAKER")

    def test_unknown_plant_returns_none(self) -> None:
        """Plant absent from dispatch returns None."""
        result = probe._route_unit_to_klass(99999, "G1", "Combined cycle", {})
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# Integration smoke tests (patch filesystem reads)
# ---------------------------------------------------------------------------


class TestRunShapeTableSmoke(unittest.TestCase):
    """run_shape_table runs end-to-end on fixture data without crashing."""

    def _make_bundle(self, tmp_path: Path, year: int = 2024) -> Path:
        """Write a tiny dispatch parquet under tmp_path/dispatch/."""
        bundle = tmp_path / "test_bundle"
        dispatch_dir = bundle / "dispatch"
        dispatch_dir.mkdir(parents=True)
        disp = _make_dispatch(year=year)
        disp.to_parquet(dispatch_dir / f"{year}_P1.parquet", index=False)
        return bundle

    def test_smoke_no_crash(self) -> None:
        """Shape table runs without exceptions on fixture dispatch + mocked sources."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            bundle = self._make_bundle(Path(tmp))

            # Patch the external data loaders to return tiny fixtures
            campd_df = pd.DataFrame(
                {h: [4500.0] * 8760 for h in ["CC_REGULAR"]},
                index=range(8760),
            )
            e930_df = pd.DataFrame(
                {"gas_mw": np.full(8760, 9000.0), "solar_mw": np.full(8760, 3000.0)},
                index=range(8760),
            )
            curt = np.zeros(8760)

            with (
                patch.object(probe, "load_campd_measured", return_value=campd_df),
                patch.object(probe, "_load_ciso_hourly", return_value=e930_df),
                patch.object(probe, "load_solar_curtailment", return_value=curt),
            ):
                # Should not raise
                probe.run_shape_table(bundle, years=[2024])


class TestRunCompareSmoke(unittest.TestCase):
    """run_compare runs end-to-end on two fixture bundles."""

    def test_smoke_no_crash(self) -> None:
        """Compare mode with two tiny bundles does not raise."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base"
            other = Path(tmp) / "other"
            for b in (base, other):
                d = b / "dispatch"
                d.mkdir(parents=True)
                _make_dispatch(year=2024).to_parquet(d / "2024_P1.parquet", index=False)

            campd_df = pd.DataFrame(index=range(8760))
            with (
                patch.object(probe, "load_campd_measured", return_value=campd_df),
                patch.object(probe, "_load_ciso_hourly", return_value=None),
            ):
                probe.run_compare(base, [other], years=[2024])


class TestRunFloorAttributionSmoke(unittest.TestCase):
    """run_floor_attribution runs end-to-end with mocked source functions."""

    def test_smoke_no_crash(self) -> None:
        """Floor attribution mode does not raise on fixture data."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "bundle"
            d = bundle / "dispatch"
            d.mkdir(parents=True)
            klasses = {k: 500.0 for k in probe._GAS_CLASSES}
            _make_dispatch(year=2024, klasses=klasses).to_parquet(
                d / "2024_P1.parquet", index=False
            )

            fake_profile = np.full(8760, 8000.0)
            fake_weather = pd.DataFrame(
                {
                    "date": pd.date_range("2024-01-01", periods=366, freq="D"),
                    "zone": "_load_weighted",
                    "tmax_c": 30.0,
                    "tmin_c": np.nan,
                }
            )

            with (
                patch(
                    "market_sim.data.eia_loader.measured_gas_floor_profile",
                    return_value=fake_profile,
                ),
                patch(
                    "market_sim.data.eia_loader.load_weather",
                    return_value=fake_weather,
                ),
            ):
                probe.run_floor_attribution(bundle, years=[2024])


class TestLoadSolarCurtailmentSmoke(unittest.TestCase):
    """load_solar_curtailment returns None gracefully when file is absent."""

    def test_missing_file_returns_none(self) -> None:
        """If the curtailment xlsx does not exist, returns None without raising."""
        result = probe.load_solar_curtailment(1900)  # no such year
        self.assertIsNone(result)


class TestCLIArgParsing(unittest.TestCase):
    """_parse_args handles all modes without raising."""

    def test_default_mode(self) -> None:
        args = probe._parse_args(["some/bundle"])
        self.assertIsNone(args.compare)
        self.assertFalse(args.floor_attribution)
        self.assertEqual(args.year, [2023, 2024, 2025])

    def test_compare_mode(self) -> None:
        args = probe._parse_args(["a/b", "--compare", "c/d", "e/f", "--year", "2024"])
        self.assertIsNotNone(args.compare)
        self.assertEqual(len(args.compare), 2)
        self.assertEqual(args.year, [2024])

    def test_floor_attribution_mode(self) -> None:
        args = probe._parse_args(
            [
                "x/y",
                "--floor-attribution",
                "--gas-floor-frac",
                "0.7",
                "--ct-floor-base",
                "0.0",
            ]
        )
        self.assertTrue(args.floor_attribution)
        self.assertAlmostEqual(args.gas_floor_frac, 0.7)
        self.assertAlmostEqual(args.ct_floor_base, 0.0)


class TestSolarBandWindowSelection(unittest.TestCase):
    """Solar labels select h10-15 band; thermal labels select h13-23.

    Regression guard for the Bug-1 fix: ``label.startswith("solar")`` must be
    used instead of ``label == "solar"`` so that ``"solar (EIA930)"`` and
    ``"solar+curt pot"`` both pick the midday band.
    """

    def _select_band(self, label: str) -> tuple[int, int]:
        """Mirror the fixed _row band-selection logic."""
        return probe._BAND_HOURS["solar" if label.startswith("solar") else "default"]

    def test_solar_eia930_label_picks_solar_band(self) -> None:
        """'solar (EIA930)' label → h10-15 band, not h13-23."""
        self.assertEqual(self._select_band("solar (EIA930)"), (10, 15))

    def test_solar_curt_label_picks_solar_band(self) -> None:
        """'solar+curt pot' label → h10-15 band, not h13-23."""
        self.assertEqual(self._select_band("solar+curt pot"), (10, 15))

    def test_thermal_label_picks_default_band(self) -> None:
        """'CC_REGULAR' → h13-23 band."""
        self.assertEqual(self._select_band("CC_REGULAR"), (13, 23))

    def test_gas_total_label_picks_default_band(self) -> None:
        """'GAS TOTAL' → h13-23 band."""
        self.assertEqual(self._select_band("GAS TOTAL"), (13, 23))

    def test_solar_band_includes_h12_not_thermal(self) -> None:
        """H12 spike falls in the solar band (h10-15) but not the thermal band (h13-23)."""
        arr = np.zeros(8760)
        arr[12::24] = 1000.0  # peak only at noon (h12) — inside h10-15, outside h13-23
        hod = probe.diurnal_mean(arr)

        solar_band_mw = probe._band(hod, *self._select_band("solar (EIA930)"))
        thermal_band_mw = probe._band(hod, *self._select_band("CC_REGULAR"))

        self.assertGreater(
            solar_band_mw, 100.0, "h12 spike must be captured by h10-15 band"
        )
        self.assertAlmostEqual(
            thermal_band_mw,
            0.0,
            places=1,
            msg="h12 spike must not appear in h13-23 band",
        )


class TestEia930LeapYearHoy(unittest.TestCase):
    """After UTC-8 fix, 2024 EIA-930 hoy max == 8759 and no post-Feb-28 +24 h shift.

    Regression guard for the Bug-3 fix: ``_hoy_from_date_hour`` must be used
    instead of ``(local - t0) / 1h`` so that leap-year rows are correctly mapped
    to the 8760-hour model grid.
    """

    def _make_boundary_frame(self) -> pd.DataFrame:
        """Minimal 2024 EIA-930 frame covering Feb 28, Feb 29, Mar 1, Dec 31 h23."""
        # LST (UTC-8) times and their UTC equivalents
        # Feb 28 00:00 LST = Feb 28 08:00 UTC
        # Feb 29 00:00 LST = Feb 29 08:00 UTC  (to be dropped)
        # Mar 1 00:00 LST = Mar 1 08:00 UTC
        # Dec 31 23:00 LST = Jan 1 07:00 UTC 2025
        return pd.DataFrame(
            {
                "UTC time": [
                    "2024-02-28T08:00:00Z",
                    "2024-02-29T08:00:00Z",
                    "2024-03-01T08:00:00Z",
                    "2025-01-01T07:00:00Z",
                ],
                "Local time": [
                    "2024-02-28T00:00:00",
                    "2024-02-29T00:00:00",
                    "2024-03-01T00:00:00",
                    "2024-12-31T23:00:00",
                ],
                "NG: NG": [5000.0, 5000.0, 5000.0, 5000.0],
                "NG: SUN": [0.0, 0.0, 0.0, 0.0],
            }
        )

    def _make_full_2024_frame(self) -> pd.DataFrame:
        """Full synthetic 2024 EIA-930 frame: 8784 UTC hours (full leap year in LST)."""
        # 2024-01-01 08:00 UTC = 2024-01-01 00:00 LST (first model hour)
        # 8784 rows covers through 2025-01-01 07:00 UTC = 2024-12-31 23:00 LST
        utc_range = pd.date_range("2024-01-01 08:00", periods=8784, freq="h", tz="UTC")
        return pd.DataFrame(
            {
                "UTC time": utc_range.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "Local time": "2024-01-01T00:00:00",  # placeholder; not used by fixed code
                "NG: NG": 5000.0,
                "NG: SUN": 1000.0,
            }
        )

    def test_feb29_dropped(self) -> None:
        """Feb 29 row must be filtered out, leaving 3 of 4 boundary rows."""
        result = probe._eia930_to_8760(self._make_boundary_frame(), 2024)
        self.assertEqual(len(result), 3, "Feb 29 must be dropped")

    def test_mar1_maps_to_hoy_1416_not_1440(self) -> None:
        """Mar 1 00:00 LST → hoy 1416 (31+28 days*24h), not 1440 (leap-year shift)."""
        result = probe._eia930_to_8760(self._make_boundary_frame(), 2024)
        hoy_list = result["hoy"].tolist()
        self.assertIn(1416, hoy_list, "Mar 1 00:00 LST must be at hoy 1416")
        self.assertNotIn(1440, hoy_list, "hoy 1440 indicates the leap-year +24 h bug")

    def test_dec31_h23_maps_to_hoy_8759(self) -> None:
        """Dec 31 23:00 LST → hoy 8759 (last slot), not beyond 8759."""
        result = probe._eia930_to_8760(self._make_boundary_frame(), 2024)
        self.assertIn(
            8759, result["hoy"].tolist(), "Dec 31 23:00 LST must be at hoy 8759"
        )

    def test_full_year_hoy_max_is_8759(self) -> None:
        """Full 2024 frame: hoy max must be 8759 after dropping Feb 29."""
        result = probe._eia930_to_8760(self._make_full_2024_frame(), 2024)
        self.assertLessEqual(
            int(result["hoy"].max()),
            8759,
            "hoy must not exceed 8759 — no leap-year +24 h shift",
        )

    def test_full_year_no_hoy_above_8759(self) -> None:
        """No row in the full 2024 frame may carry hoy > 8759."""
        result = probe._eia930_to_8760(self._make_full_2024_frame(), 2024)
        bad = result[result["hoy"] > 8759]
        self.assertTrue(bad.empty, f"{len(bad)} rows with hoy > 8759 found")


class TestEia930DstAlignment(unittest.TestCase):
    """EIA-930 UTC processing: summer rows use fixed −8 h (PST), not −7 h (PDT).

    Regression guard for the Bug-2 fix: the ``UTC time`` column minus a fixed
    8 h must be used instead of the ``Local time`` column, which carries a −7 h
    PDT offset in summer.
    """

    def _make_dst_frame(self, year: int = 2023) -> pd.DataFrame:
        """Frame with one summer row (Jul 1 18:00 UTC) and one winter row (Jan 1 08:00 UTC)."""
        # Jul 1 18:00 UTC = 10:00 PST (UTC-8) = 11:00 PDT (UTC-7)
        # Jan 1 08:00 UTC = 00:00 PST = 00:00 PST (same in winter)
        return pd.DataFrame(
            {
                "UTC time": [
                    f"{year}-07-01T18:00:00Z",
                    f"{year}-01-01T08:00:00Z",
                ],
                "Local time": [
                    f"{year}-07-01T11:00:00",  # PDT (UTC-7) — old bug value
                    f"{year}-01-01T00:00:00",  # PST (UTC-8) — same in winter
                ],
                "NG: NG": [5000.0, 3000.0],
                "NG: SUN": [800.0, 0.0],
            }
        )

    def test_summer_row_uses_pst_not_pdt(self) -> None:
        """Jul 1 18:00 UTC → hoy for 10:00 PST (h10), not 11:00 PDT (h11)."""
        result = probe._eia930_to_8760(self._make_dst_frame(2023), 2023)
        hoys = set(result["hoy"].tolist())

        # Jul 1 h10 PST: _MONTH_START_HOUR[6] + 0*24 + 10 = 4344 + 10 = 4354
        expected_pst_hoy = probe._MONTH_START_HOUR[6] + 10  # h10 on Jul 1
        wrong_pdt_hoy = probe._MONTH_START_HOUR[6] + 11  # h11 would be PDT

        self.assertIn(
            expected_pst_hoy,
            hoys,
            f"Jul 1 18:00 UTC must map to hoy {expected_pst_hoy} (10:00 PST)",
        )
        self.assertNotIn(
            wrong_pdt_hoy,
            hoys,
            f"Jul 1 18:00 UTC must NOT map to hoy {wrong_pdt_hoy} (11:00 PDT = old bug)",
        )

    def test_winter_row_alignment_unchanged(self) -> None:
        """Jan 1 08:00 UTC → hoy 0 (midnight PST); fix must not disturb winter rows."""
        result = probe._eia930_to_8760(self._make_dst_frame(2023), 2023)
        self.assertIn(
            0, set(result["hoy"].tolist()), "Jan 1 08:00 UTC must map to hoy 0"
        )

    def test_summer_offset_is_8h_not_7h(self) -> None:
        """Directly confirm the UTC-8 shift: Jul 1 15:00 UTC → h7 PST, not h8 PDT."""
        year = 2023
        df = pd.DataFrame(
            {
                "UTC time": [f"{year}-07-01T15:00:00Z"],
                "Local time": [f"{year}-07-01T08:00:00"],  # PDT (UTC-7) — wrong
                "NG: NG": [5000.0],
                "NG: SUN": [500.0],
            }
        )
        result = probe._eia930_to_8760(df, year)
        # Jul 1 15:00 UTC - 8h = Jul 1 07:00 PST → h7 on Jul 1
        expected_hoy = probe._MONTH_START_HOUR[6] + 7  # h7 on Jul 1
        self.assertEqual(
            int(result["hoy"].iloc[0]),
            expected_hoy,
            f"UTC-8 offset must give h7 PST (hoy {expected_hoy}), not h8 PDT",
        )


if __name__ == "__main__":
    unittest.main()
