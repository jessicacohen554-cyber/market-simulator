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
            fake_tmax = np.full(8760, 30.0)

            with (
                patch(
                    "market_sim.data.eia_loader.measured_gas_floor_profile",
                    return_value=fake_profile,
                ),
                patch(
                    "market_sim.data.eia_loader.caiso_load_weighted_tmax",
                    return_value=fake_tmax,
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


if __name__ == "__main__":
    unittest.main()
