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
    gross = np.concatenate([np.zeros(6), np.full(18, 100.0),  # day 1: off then on
                            np.full(24, 100.0)])              # day 2: on
    return pd.DataFrame({
        "stateCode": "TX",
        "facilityName": "Test Plant",
        "facilityId": plant_id,
        "date": dates,
        "hour": hours,
        "grossLoad": gross,
        "steamLoad": np.nan,
        "so2Mass": np.where(gross > 0, 2.0, 0.0),     # lbs
        "co2Mass": np.where(gross > 0, 60.0, 0.0),    # short tons
        "noxMass": np.where(gross > 0, 1.0, 0.0),     # lbs
        "heatInput": np.where(gross > 0, 1000.0, 0.0),
    })


class TestHourIndex(unittest.TestCase):
    """``_hour_index_8760`` maps a calendar timestamp to a non-leap index."""

    def test_anchor_and_bounds(self):
        m = np.array([1, 1, 1, 12, 2])
        d = np.array([1, 1, 2, 31, 29])
        h = np.array([0, 5, 0, 23, 10])
        idx = campd._hour_index_8760(m, d, h)
        self.assertEqual(idx[0], 0)        # Jan 1 00:00
        self.assertEqual(idx[1], 5)        # Jan 1 05:00
        self.assertEqual(idx[2], 24)       # Jan 2 00:00
        self.assertEqual(idx[3], 8759)     # Dec 31 23:00
        self.assertEqual(idx[4], -1)       # Feb 29 dropped


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
        self.assertEqual(row["gross_mwh"], 42 * 100.0)   # 42 on-hours × 100 MW
        self.assertEqual(row["op_hours"], 42)


class TestParasiticFactors(unittest.TestCase):
    """Net/gross in band is measured; otherwise the class default applies."""

    def _campd_annual(self, gross):
        return pd.DataFrame({
            "plant_id": [1], "year": [2023], "gross_mwh": [gross],
            "heat_mmbtu": [0.0], "co2_kg": [0.0], "nox_kg": [0.0],
            "so2_kg": [0.0], "facility_name": ["P"], "op_hours": [10],
        })

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
        gen = pd.DataFrame({
            "plant_id": [1, 1, 2],
            "year": [2023, 2023, 2023],
            "fuel_type": ["NG", "WND", "SUB"],
            "netgen_annual_mwh": [100.0, 50.0, 200.0],
        })
        out = campd.eia923_combustion_net(gen)
        self.assertEqual(out[out.plant_id == 1]["net_mwh"].iloc[0], 100.0)  # wind dropped
        self.assertEqual(out[out.plant_id == 2]["net_mwh"].iloc[0], 200.0)


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
        self.assertEqual(series[0], 0.0)            # Jan 1 00:00 was offline
        self.assertAlmostEqual(series[6], 100.0 * 0.9)  # first on-hour, scaled
        self.assertAlmostEqual(series.sum(), 42 * 100.0 * 0.9)


class TestApplyPlantEmissionRates(unittest.TestCase):
    """The LP override swaps fuel-class rates for plant-specific ones (tonnes)."""

    def test_override_converts_kg_to_tonnes(self):
        rates = pd.DataFrame({
            "plant_id": [1001], "year": [0],
            "co2_kg_per_mwh_net": [900.0],
            "nox_kg_per_mwh_net": [0.8],
            "so2_kg_per_mwh_net": [0.5],
        })
        gens = [
            Generator(unit_id="a_p1001", name="a", zone="Z", fuel_type="coal",
                      pmax_mw=100.0, emission_rate_co2=1.0, nox_rate=0.001,
                      plant_code=1001),
            Generator(unit_id="b_p9999", name="b", zone="Z", fuel_type="gas_cc",
                      pmax_mw=50.0, emission_rate_co2=0.4, nox_rate=0.00008,
                      plant_code=9999),  # not in artifact -> unchanged
        ]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "rates.parquet"
            rates.to_parquet(p)
            n = apply_plant_emission_rates(gens, p)
        self.assertEqual(n, 1)
        self.assertAlmostEqual(gens[0].emission_rate_co2, 0.9)   # 900 kg -> 0.9 t
        self.assertAlmostEqual(gens[0].nox_rate, 0.0008)
        self.assertAlmostEqual(gens[0].so2_rate, 0.0005)
        self.assertAlmostEqual(gens[1].emission_rate_co2, 0.4)   # untouched

    def test_missing_artifact_is_noop(self):
        gens = [Generator(unit_id="a_p1", name="a", zone="Z", fuel_type="coal",
                          pmax_mw=1.0, plant_code=1)]
        n = apply_plant_emission_rates(gens, Path("/nonexistent/x.parquet"))
        self.assertEqual(n, 0)


if __name__ == "__main__":
    unittest.main()
