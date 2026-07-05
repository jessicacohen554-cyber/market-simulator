"""Tests for the CAMPD loader, parasitic factors and plant emission rates."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data import campd
from market_sim.data.fleet import Generator, apply_plant_emission_rates


def _raw_extract(plant_id: str = "1001", year: int = 2023) -> pd.DataFrame:
    """Return a tiny raw CAMPD-shaped frame: two days, one unit."""
    dates = pd.to_datetime([f"{year}-01-01"] * 24 + [f"{year}-01-02"] * 24)
    hours = list(range(24)) * 2
    gross = np.concatenate(
        [
            np.zeros(6),
            np.full(18, 100.0),  # day 1: off then on
            np.full(24, 100.0),
        ]
    )  # day 2: on
    return pd.DataFrame(
        {
            "stateCode": "TX",
            "facilityName": "Test Plant",
            "facilityId": plant_id,
            "date": dates,
            "hour": hours,
            "grossLoad": gross,
            "steamLoad": np.nan,
            "so2Mass": np.where(gross > 0, 2.0, 0.0),  # lbs
            "co2Mass": np.where(gross > 0, 60.0, 0.0),  # short tons
            "noxMass": np.where(gross > 0, 1.0, 0.0),  # lbs
            "heatInput": np.where(gross > 0, 1000.0, 0.0),
        }
    )


class TestHourIndex(unittest.TestCase):
    """``_hour_index_8760`` maps a calendar timestamp to a non-leap index."""

    def test_anchor_and_bounds(self):
        m = np.array([1, 1, 1, 12, 2])
        d = np.array([1, 1, 2, 31, 29])
        h = np.array([0, 5, 0, 23, 10])
        idx = campd._hour_index_8760(m, d, h)
        self.assertEqual(idx[0], 0)  # Jan 1 00:00
        self.assertEqual(idx[1], 5)  # Jan 1 05:00
        self.assertEqual(idx[2], 24)  # Jan 2 00:00
        self.assertEqual(idx[3], 8759)  # Dec 31 23:00
        self.assertEqual(idx[4], -1)  # Feb 29 dropped


class TestLoadCampdHourly(unittest.TestCase):
    """``load_campd_hourly`` normalizes units and the calendar."""

    def test_units_and_columns(self):
        with tempfile.TemporaryDirectory() as d:
            _raw_extract().to_parquet(Path(d) / "TX_2023.parquet")
            df = campd.load_campd_hourly(["TX"], [2023], raw_dir=d)
        self.assertEqual(df["plant_id"].iloc[0], 1001)
        on = df[df["gross_mw"] > 0].iloc[0]
        self.assertAlmostEqual(on["co2_kg"], 60.0 * campd.SHORT_TON_TO_KG)
        self.assertAlmostEqual(on["nox_kg"], 1.0 * campd.LB_TO_KG)
        self.assertAlmostEqual(on["so2_kg"], 2.0 * campd.LB_TO_KG)
        self.assertIn("hour_of_year", df.columns)

    def test_missing_file_returns_empty(self):
        self.assertTrue(campd.load_campd_hourly(["ZZ"], [1999]).empty)


class TestAnnualTotals(unittest.TestCase):
    def test_gross_and_op_hours(self):
        with tempfile.TemporaryDirectory() as d:
            _raw_extract().to_parquet(Path(d) / "TX_2023.parquet")
            df = campd.load_campd_hourly(["TX"], [2023], raw_dir=d)
        ann = campd.annual_plant_totals(df)
        row = ann.iloc[0]
        self.assertEqual(row["gross_mwh"], 42 * 100.0)  # 42 on-hours × 100 MW
        self.assertEqual(row["op_hours"], 42)


class TestParasiticFactors(unittest.TestCase):
    """Net/gross in band is measured; otherwise the class default applies."""

    def _campd_annual(self, gross):
        return pd.DataFrame(
            {
                "plant_id": [1],
                "year": [2023],
                "gross_mwh": [gross],
                "heat_mmbtu": [0.0],
                "co2_kg": [0.0],
                "nox_kg": [0.0],
                "so2_kg": [0.0],
                "facility_name": ["P"],
                "op_hours": [10],
            }
        )

    def test_measured_in_band(self):
        net = pd.DataFrame({"plant_id": [1], "year": [2023], "net_mwh": [930.0]})
        out = campd.compute_parasitic_factors(self._campd_annual(1000.0), net)
        row = out[(out.plant_id == 1) & (out.year == 2023)].iloc[0]
        self.assertEqual(row["source"], "measured")
        self.assertAlmostEqual(row["parasitic_factor"], 0.93)
        self.assertAlmostEqual(row["parasitic_load_pct"], 0.07)

    def test_out_of_band_uses_class_default(self):
        # net/gross = 1.2 -> implausible -> COAL class default (7%).
        net = pd.DataFrame({"plant_id": [1], "year": [2023], "net_mwh": [1200.0]})
        out = campd.compute_parasitic_factors(
            self._campd_annual(1000.0), net, plant_groups={1: "COAL"}
        )
        row = out[(out.plant_id == 1) & (out.year == 2023)].iloc[0]
        self.assertEqual(row["source"], "class_default")
        self.assertAlmostEqual(
            row["parasitic_load_pct"],
            campd.DEFAULT_PARASITIC_LOAD_PCT["COAL"],
        )

    def test_missing_net_uses_class_default(self):
        net = pd.DataFrame({"plant_id": [], "year": [], "net_mwh": []})
        out = campd.compute_parasitic_factors(
            self._campd_annual(1000.0), net, plant_groups={1: "CC_REGULAR"}
        )
        row = out[(out.plant_id == 1) & (out.year == 0)].iloc[0]
        self.assertEqual(row["flag"], "no_net")


class TestEia923CombustionNet(unittest.TestCase):
    def test_excludes_non_combustion(self):
        gen = pd.DataFrame(
            {
                "plant_id": [1, 1, 2],
                "year": [2023, 2023, 2023],
                "fuel_type": ["NG", "WND", "SUB"],
                "netgen_annual_mwh": [100.0, 50.0, 200.0],
            }
        )
        out = campd.eia923_combustion_net(gen)
        self.assertEqual(
            out[out.plant_id == 1]["net_mwh"].iloc[0], 100.0
        )  # wind dropped
        self.assertEqual(out[out.plant_id == 2]["net_mwh"].iloc[0], 200.0)


class TestCoalShare(unittest.TestCase):
    def test_flags_blended_plant(self):
        gen = pd.DataFrame(
            {
                "plant_id": [1, 1, 2],
                "year": [2023, 2023, 2023],
                "fuel_type": ["SUB", "NG", "SUB"],
                "netgen_annual_mwh": [850.0, 150.0, 1000.0],
            }
        )
        shares = campd.coal_share_by_plant(gen, [2023])
        self.assertAlmostEqual(shares[1], 0.85)  # blended -> mixed band
        self.assertAlmostEqual(shares[2], 1.0)  # pure coal


class TestPlantEmissionRates(unittest.TestCase):
    def test_rates_per_mwh_net_and_starts(self):
        with tempfile.TemporaryDirectory() as d:
            _raw_extract().to_parquet(Path(d) / "TX_2023.parquet")
            df = campd.load_campd_hourly(["TX"], [2023], raw_dir=d)
        rates = campd.plant_emission_rates(df, {1001: 0.9})
        pooled = rates[rates.year == 0].iloc[0]
        gross = 42 * 100.0
        net = gross * 0.9
        # 42 on-hours × 60 short tons CO2 each.
        expected_co2 = 42 * 60.0 * campd.SHORT_TON_TO_KG / net
        self.assertAlmostEqual(pooled["co2_kg_per_mwh_net"], round(expected_co2, 6))
        self.assertEqual(pooled["co2_source"], "measured")
        self.assertEqual(pooled["starts"], 1)  # one off->on transition on day 1

    def test_co2_backfilled_from_heat_when_unmonitored(self):
        raw = _raw_extract()
        raw["co2Mass"] = np.nan  # gas peaker reporting NOx + heat but not CO2
        with tempfile.TemporaryDirectory() as d:
            raw.to_parquet(Path(d) / "TX_2023.parquet")
            df = campd.load_campd_hourly(["TX"], [2023], raw_dir=d)
        rates = campd.plant_emission_rates(df, {1001: 1.0})
        pooled = rates[rates.year == 0].iloc[0]
        self.assertEqual(pooled["co2_source"], "heat_backfilled")
        self.assertGreater(pooled["co2_kg_per_mwh_net"], 0.0)


class TestPlantHourlyNet(unittest.TestCase):
    def test_maps_to_hour_of_year_and_scales(self):
        with tempfile.TemporaryDirectory() as d:
            _raw_extract().to_parquet(Path(d) / "TX_2023.parquet")
            df = campd.load_campd_hourly(["TX"], [2023], raw_dir=d)
        net = campd.plant_hourly_net(df, {1001: 0.9}, 2023, hours=8760)
        series = net[1001]
        self.assertEqual(series.shape, (8760,))
        self.assertEqual(series[0], 0.0)  # Jan 1 00:00 was offline
        self.assertAlmostEqual(series[6], 100.0 * 0.9)  # first on-hour, scaled
        self.assertAlmostEqual(series.sum(), 42 * 100.0 * 0.9)

    def test_nan_unit_hour_does_not_poison_multi_unit_plant(self):
        """An offline unit (NaN gross) must not zero a multi-unit plant-hour.

        Regression: ``np.add.at`` propagates NaN, so on the unit-level extracts
        a single down unit (NaN gross) used to poison the whole plant-hour and
        then vanish downstream, undercounting multi-unit coal plants ~2x. NaN
        gross must be floored to 0 MW before accumulation so the running unit's
        output still counts.
        """
        # One plant (1001), two units sharing hour-of-year 0 and 1: in hour 0
        # unit B is offline (NaN gross) while unit A runs; both run in hour 1.
        df = pd.DataFrame(
            {
                "plant_id": [1001, 1001, 1001, 1001],
                "year": np.int16(2023),
                "hour_of_year": [0, 0, 1, 1],
                "gross_mw": [100.0, np.nan, 100.0, 50.0],
            }
        )
        net = campd.plant_hourly_net(df, {1001: 1.0}, 2023, hours=8760)
        series = net[1001]
        self.assertAlmostEqual(series[0], 100.0)  # unit A counts despite B NaN
        self.assertAlmostEqual(series[1], 150.0)  # both units sum
        self.assertAlmostEqual(series.sum(), 250.0)  # no NaN leaked into total
        self.assertFalse(np.isnan(series).any())


class TestPlantHourlyGrid(unittest.TestCase):
    """``plant_hourly_grid`` gap-fills offline hours on a contiguous clock."""

    def test_gap_filled_and_contiguous(self):
        with tempfile.TemporaryDirectory() as d:
            _raw_extract().to_parquet(Path(d) / "TX_2023.parquet")
            df = campd.load_campd_hourly(["TX"], [2023], raw_dir=d)
        grid = campd.plant_hourly_grid(df, 1001, 2023)
        # Two full days reported -> 48 contiguous hours, no gaps.
        self.assertEqual(len(grid), 48)
        self.assertEqual(int((grid["gross_mw"] == 0).sum()), 6)  # day-1 off hours
        self.assertEqual(int((grid["gross_mw"] > 0).sum()), 42)

    def test_absent_plant_year_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            _raw_extract().to_parquet(Path(d) / "TX_2023.parquet")
            df = campd.load_campd_hourly(["TX"], [2023], raw_dir=d)
        self.assertTrue(campd.plant_hourly_grid(df, 9999, 2023).empty)


class TestApplyPlantEmissionRates(unittest.TestCase):
    """The LP override swaps fuel-class rates for plant-specific ones (tonnes)."""

    def test_override_converts_kg_to_tonnes(self):
        rates = pd.DataFrame(
            {
                "plant_id": [1001],
                "year": [0],
                "co2_kg_per_mwh_net": [900.0],
                "nox_kg_per_mwh_net": [0.8],
                "so2_kg_per_mwh_net": [0.5],
            }
        )
        gens = [
            Generator(
                unit_id="a_p1001",
                name="a",
                zone="Z",
                fuel_type="coal",
                pmax_mw=100.0,
                emission_rate_co2=1.0,
                nox_rate=0.001,
                plant_code=1001,
            ),
            Generator(
                unit_id="b_p9999",
                name="b",
                zone="Z",
                fuel_type="gas_cc",
                pmax_mw=50.0,
                emission_rate_co2=0.4,
                nox_rate=0.00008,
                plant_code=9999,
            ),  # not in artifact -> unchanged
        ]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "rates.parquet"
            rates.to_parquet(p)
            n = apply_plant_emission_rates(gens, p)
        self.assertEqual(n, 1)
        self.assertAlmostEqual(gens[0].emission_rate_co2, 0.9)  # 900 kg -> 0.9 t
        self.assertAlmostEqual(gens[0].nox_rate, 0.0008)
        self.assertAlmostEqual(gens[0].so2_rate, 0.0005)
        self.assertAlmostEqual(gens[1].emission_rate_co2, 0.4)  # untouched

    def test_mixed_plant_is_skipped(self):
        rates = pd.DataFrame(
            {
                "plant_id": [3470],
                "year": [0],
                "co2_kg_per_mwh_net": [898.0],
                "nox_kg_per_mwh_net": [0.48],
                "so2_kg_per_mwh_net": [2.08],
                "mixed": [True],
            }
        )
        gens = [
            Generator(
                unit_id="c_p3470",
                name="c",
                zone="Z",
                fuel_type="coal",
                pmax_mw=100.0,
                emission_rate_co2=1.076,
                plant_code=3470,
            )
        ]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "rates.parquet"
            rates.to_parquet(p)
            n = apply_plant_emission_rates(gens, p)
        self.assertEqual(n, 0)
        self.assertAlmostEqual(gens[0].emission_rate_co2, 1.076)  # fuel default kept

    def test_missing_artifact_is_noop(self):
        gens = [
            Generator(
                unit_id="a_p1",
                name="a",
                zone="Z",
                fuel_type="coal",
                pmax_mw=1.0,
                plant_code=1,
            )
        ]
        n = apply_plant_emission_rates(gens, Path("/nonexistent/x.parquet"))
        self.assertEqual(n, 0)


class TestApplyPlantEmissionRatesV2NoxSo2(unittest.TestCase):
    """The v2 override now books CO2, NOx and SO2 at the measured plant rate."""

    def _v2(self) -> pd.DataFrame:
        # A coal + gas unit sharing plant 3470 (Parish-style); gas SO2 == 0.
        rows = []
        for year in (2023, 2024):
            rows += [
                ("ERCOT", 3470, "WAP5", year, "Coal", 1000.0, 1e6, 800.0, 900.0),
                ("ERCOT", 3470, "WAP1", year, "Gas", 1000.0, 4e5, 200.0, 0.0),
            ]
        return pd.DataFrame(
            rows,
            columns=[
                "iso",
                "plant_id",
                "unit_id",
                "year",
                "primary_fuel",
                "net_mwh",
                "co2_kg",
                "nox_kg",
                "so2_kg",
            ],
        )

    def test_books_measured_nox_and_so2(self):
        from market_sim.data.fleet import (
            _measured_plant_rate_map_v2,
            apply_plant_emission_rates_v2,
        )

        _measured_plant_rate_map_v2.cache_clear()
        coal = Generator(
            unit_id="coal_p3470",
            name="coal",
            zone="Z",
            fuel_type="coal",
            pmax_mw=100.0,
            emission_rate_co2=1.05,
            nox_rate=0.001,
            so2_rate=0.001,
            plant_code=3470,
        )
        gas = Generator(
            unit_id="gas_p3470",
            name="gas",
            zone="Z",
            fuel_type="gas_cc",
            pmax_mw=50.0,
            emission_rate_co2=0.4,
            nox_rate=0.0002,
            so2_rate=0.0002,
            plant_code=3470,
        )
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "v2.parquet"
            self._v2().to_parquet(p)
            apply_plant_emission_rates_v2(
                [coal, gas], p, iso="ERCOT", year=2024, mode="backcast"
            )
        # Coal unit books its measured coal-class rates (tonnes/MWh net).
        self.assertAlmostEqual(coal.emission_rate_co2, 1.0)  # 1e6 kg / 1000 -> 1 t
        self.assertAlmostEqual(coal.nox_rate, 0.0008)
        self.assertAlmostEqual(coal.so2_rate, 0.0009)
        # Gas unit books the gas-class rates; its measured SO2 is a genuine 0.
        self.assertAlmostEqual(gas.emission_rate_co2, 0.4)
        self.assertAlmostEqual(gas.nox_rate, 0.0002)
        self.assertAlmostEqual(gas.so2_rate, 0.0)


def _heat_only_hourly(plant_id: int, year: int) -> pd.DataFrame:
    """A grossLoad-blank coal unit: one full year of hourly heat, no gross.

    Heat is a flat 1000 MMBtu/h for 8760 hours, so at heat rate ``hr`` the
    annual net generation is ``8760 * 1000 / hr`` MWh, spread evenly across
    the twelve months.
    """
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    n = len(idx)
    df = pd.DataFrame(
        {
            "plant_id": plant_id,
            "facility_name": "CFB Coal",
            "state": "PA",
            "year": np.int16(year),
            "date": idx.normalize(),
            "hour": idx.hour,
            "gross_mw": np.full(n, np.nan),
            "steam_load": np.full(n, 500.0),
            "co2_kg": np.full(n, 100.0),
            "nox_kg": np.full(n, 1.0),
            "so2_kg": np.full(n, 1.0),
            "heat_mmbtu": np.full(n, 1000.0),
        }
    )
    df["hour_of_year"] = campd._hour_index_8760(
        df["date"].dt.month, df["date"].dt.day, df["hour"]
    )
    return df[df["hour_of_year"] >= 0].reset_index(drop=True)


def _eia_monthly_row(plant_id: int, year: int, annual_mwh: float, fuel: str = "BIT"):
    """One EIA-923 monthly-generation row: ``annual_mwh`` split evenly by month."""
    per_month = annual_mwh / 12.0
    row = {
        "plant_id": plant_id,
        "fuel_type": fuel,
        "prime_mover": "ST",
        "chp": "N",
        "year": year,
        "netgen_annual_mwh": annual_mwh,
    }
    for c in campd._EIA923_MONTH_COLUMNS:
        row[c] = per_month
    return row


class TestHeatInputProxy(unittest.TestCase):
    """The heat-input -> MWh proxy for grossLoad-blank coal units."""

    def setUp(self):
        self.year = 2023  # non-leap: 8760 hours, no Feb-29 drop
        # Annual heat = 8760 * 1000 = 8.76e6 MMBtu; pick netgen so HR = 11.0.
        self.heat_annual = 8760 * 1000.0
        self.hr = 11.0
        self.netgen = self.heat_annual / self.hr
        self.df = _heat_only_hourly(3130, self.year)
        self.eia = pd.DataFrame([_eia_monthly_row(3130, self.year, self.netgen)])

    def test_report_accepts_reconciling_coal_plant(self):
        rep = campd.heatinput_proxy_report(self.df, self.eia, self.year)
        self.assertEqual(len(rep), 1)
        row = rep.iloc[0]
        self.assertTrue(bool(row["accepted"]))
        self.assertAlmostEqual(float(row["heat_rate"]), self.hr, places=2)
        # Reconciles within tolerance (residual is only month-length variation).
        self.assertLess(float(row["recon_wmae"]), campd.HEATPROXY_RECONCILE_TOL)
        self.assertGreaterEqual(float(row["coal_share"]), 0.99)

    def test_fill_reconstructs_net_anchored_mwh(self):
        filled, ids = campd.fill_heatinput_proxy(self.df, self.eia, self.year)
        self.assertEqual(ids, {3130})
        proxy = filled[filled["mw_source"] == "heat_proxy"]
        self.assertEqual(len(proxy), len(filled))
        # Annual reconstructed MWh anchors to the EIA-923 netgen (level anchor).
        self.assertAlmostEqual(
            float(proxy["gross_mw"].sum()), self.netgen, delta=self.netgen * 1e-6
        )
        # Per-hour MW = 1000 / 11.0.
        self.assertTrue(np.allclose(proxy["gross_mw"], 1000.0 / self.hr))

    def test_non_coal_heat_only_plant_left_blank(self):
        eia_gas = pd.DataFrame([_eia_monthly_row(3130, self.year, self.netgen, "NG")])
        filled, ids = campd.fill_heatinput_proxy(self.df, eia_gas, self.year)
        self.assertEqual(ids, set())
        self.assertTrue(filled["gross_mw"].isna().all())
        self.assertTrue((filled["mw_source"] == "measured").all())

    def test_coverage_gap_plant_rejected(self):
        # CAMPD heat only Jan-Jun, but EIA-923 reports netgen all year: the
        # annual HR over-reconstructs the covered months and zeros the rest, so
        # the monthly reconciliation must reject it (the Eastman pattern).
        gap = self.df.copy()
        gap.loc[gap["date"].dt.month > 6, "heat_mmbtu"] = 0.0
        rep = campd.heatinput_proxy_report(gap, self.eia, self.year)
        self.assertFalse(bool(rep.iloc[0]["accepted"]))
        filled, ids = campd.fill_heatinput_proxy(gap, self.eia, self.year)
        self.assertEqual(ids, set())

    def test_measured_gross_untouched(self):
        # A plant that already reports grossLoad is never a candidate.
        measured = self.df.copy()
        measured["gross_mw"] = 90.0
        rep = campd.heatinput_proxy_report(measured, self.eia, self.year)
        self.assertEqual(len(rep), 0)
        filled, ids = campd.fill_heatinput_proxy(measured, self.eia, self.year)
        self.assertEqual(ids, set())
        self.assertTrue((filled["gross_mw"] == 90.0).all())


if __name__ == "__main__":
    unittest.main()
