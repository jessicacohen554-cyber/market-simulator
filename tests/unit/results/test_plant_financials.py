"""Tests for plant-level financial reporting."""

import unittest

import numpy as np
import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.results.plant_financials import (
    PlantBinAssignment,
    compute_company_summary,
    compute_plant_annual_summary,
    compute_plant_hourly_financials,
    compute_trajectory_npv,
    disaggregate_dispatch,
)


def _plant(
    plant_code: int,
    *,
    bin_label: str = "gas_cc_h_class",
    zone: str = "North",
    nameplate_mw: float = 100.0,
    heat_rate_btu_kwh: float = 6500.0,
    fuel_type: str = "gas_cc",
    vom_per_mwh: float = 2.0,
    fom_per_kw_yr: float = 12.0,
    emission_rate_tco2_mwh: float = 0.36,
    nox_rate_tonnes_mwh: float = 0.0001,
) -> PlantBinAssignment:
    """Return a :class:`PlantBinAssignment` with test-friendly defaults."""
    return PlantBinAssignment(
        plant_code=plant_code,
        generator_id="1",
        unit_id=f"{fuel_type}_h_class_{zone}",
        bin_label=bin_label,
        nameplate_mw=nameplate_mw,
        heat_rate_btu_kwh=heat_rate_btu_kwh,
        zone=zone,
        fuel_type=fuel_type,
        vom_per_mwh=vom_per_mwh,
        fom_per_kw_yr=fom_per_kw_yr,
        emission_rate_tco2_mwh=emission_rate_tco2_mwh,
        nox_rate_tonnes_mwh=nox_rate_tonnes_mwh,
    )


def _bin_dispatch(bin_label: str, zone: str, mw: np.ndarray) -> pd.DataFrame:
    """Return a long-format bin-dispatch frame for one bin over ``len(mw)`` h."""
    hours = np.arange(len(mw))
    return pd.DataFrame(
        {
            "bin_label": bin_label,
            "zone": zone,
            "hour": hours,
            "dispatch_mw": mw.astype(float),
        }
    )


class TestDisaggregation(unittest.TestCase):
    """Disaggregation conserves bin dispatch across its plants."""

    def test_pro_rata_conserves_dispatch_every_hour(self):
        plant_map = [
            _plant(1, nameplate_mw=100.0),
            _plant(2, nameplate_mw=200.0),
            _plant(3, nameplate_mw=300.0),
        ]
        bin_mw = np.array([60.0, 120.0, 300.0, 0.0, 540.0])
        bd = _bin_dispatch("gas_cc_h_class", "North", bin_mw)

        plant_dispatch = disaggregate_dispatch(bd, plant_map, "pro_rata_capacity")

        per_hour = plant_dispatch.groupby("hour")["dispatch_mw"].sum()
        np.testing.assert_allclose(per_hour.to_numpy(), bin_mw)

    def test_pro_rata_splits_by_capacity_share(self):
        plant_map = [
            _plant(1, nameplate_mw=100.0),
            _plant(2, nameplate_mw=300.0),
        ]
        bd = _bin_dispatch("gas_cc_h_class", "North", np.array([400.0]))

        plant_dispatch = disaggregate_dispatch(bd, plant_map, "pro_rata_capacity")

        by_plant = plant_dispatch.set_index("plant_code")["dispatch_mw"]
        self.assertAlmostEqual(by_plant.loc[1], 100.0)  # 1/4 of 400
        self.assertAlmostEqual(by_plant.loc[2], 300.0)  # 3/4 of 400

    def test_merit_order_conserves_dispatch(self):
        plant_map = [
            _plant(1, nameplate_mw=100.0, heat_rate_btu_kwh=6000.0),
            _plant(2, nameplate_mw=100.0, heat_rate_btu_kwh=9000.0),
        ]
        bin_mw = np.array([50.0, 100.0, 150.0])
        bd = _bin_dispatch("gas_cc_h_class", "North", bin_mw)

        plant_dispatch = disaggregate_dispatch(bd, plant_map, "merit_order_within_bin")

        per_hour = plant_dispatch.groupby("hour")["dispatch_mw"].sum()
        np.testing.assert_allclose(per_hour.to_numpy(), bin_mw)
        # The efficient plant (plant 1) fills first.
        hour0 = plant_dispatch[plant_dispatch["hour"] == 0].set_index("plant_code")[
            "dispatch_mw"
        ]
        self.assertAlmostEqual(hour0.loc[1], 50.0)
        self.assertAlmostEqual(hour0.loc[2], 0.0)

    def test_unknown_method_raises(self):
        with self.assertRaises(ValueError):
            disaggregate_dispatch(
                _bin_dispatch("gas_cc_h_class", "North", np.array([1.0])),
                [_plant(1)],
                method="not_a_method",
            )


class TestHourlyFinancials(unittest.TestCase):
    """Hourly financials follow revenue = price × quantity."""

    def _inputs(self, dispatch_mw, *, price=50.0, fuel=3.0, plant=None):
        """Build the (plant_dispatch, prices, fuel_prices, plant_map) inputs."""
        plant = plant or _plant(1)
        hours = np.arange(len(dispatch_mw))
        plant_dispatch = pd.DataFrame(
            {
                "plant_code": 1,
                "generator_id": "1",
                "hour": hours,
                "dispatch_mw": np.asarray(dispatch_mw, dtype=float),
                "bin_label": plant.bin_label,
                "zone": plant.zone,
            }
        )
        zonal_prices = pd.DataFrame(
            {"zone": plant.zone, "hour": hours, "price_per_mwh": price}
        )
        fuel_prices = pd.DataFrame(
            {"fuel_type": plant.fuel_type, "hour": hours, "price_per_mmbtu": fuel}
        )
        return plant_dispatch, zonal_prices, fuel_prices, [plant]

    def test_revenue_is_price_times_generation(self):
        dispatch = np.full(24, 80.0)
        pd_, zp, fp, pm = self._inputs(dispatch, price=50.0)

        hourly = compute_plant_hourly_financials(
            pd_, zp, fp, carbon_price=0.0, nox_price=0.0, plant_map=pm
        )
        np.testing.assert_allclose(hourly["revenue"], 80.0 * 50.0)
        self.assertAlmostEqual(hourly["revenue"].sum(), 24 * 80.0 * 50.0)

    def test_fuel_cost_uses_plant_heat_rate(self):
        # heat_rate 6500 BTU/kWh = 6.5 MMBtu/MWh; fuel 3 $/MMBtu.
        dispatch = np.array([100.0])
        pd_, zp, fp, pm = self._inputs(dispatch, fuel=3.0)

        hourly = compute_plant_hourly_financials(
            pd_, zp, fp, carbon_price=0.0, nox_price=0.0, plant_map=pm
        )
        # fuel_mmbtu = 100 MWh × 6500 / 1000 = 650 MMBtu.
        self.assertAlmostEqual(hourly.iloc[0]["fuel_mmbtu"], 650.0)
        self.assertAlmostEqual(hourly.iloc[0]["fuel_cost"], 650.0 * 3.0)

    def test_carbon_cost_applies_emission_rate(self):
        dispatch = np.array([100.0])
        pd_, zp, fp, pm = self._inputs(dispatch)

        hourly = compute_plant_hourly_financials(
            pd_, zp, fp, carbon_price=20.0, nox_price=0.0, plant_map=pm
        )
        # 100 MWh × 0.36 tCO2/MWh × 20 $/t = 720.
        self.assertAlmostEqual(hourly.iloc[0]["carbon_cost"], 720.0)

    def test_nox_cost_converts_tonnes_rate_to_lb(self):
        # R7/EM-2: the plant rate is canonical tonnes/MWh; the NOx price is
        # $/lb. A known coal-like unit: 0.001 tonnes/MWh NOx = 2.2046 lb/MWh.
        from market_sim.results.plant_financials import LB_PER_TONNE

        plant = _plant(1, nox_rate_tonnes_mwh=0.001)
        pd_, zp, fp, pm = self._inputs(np.array([100.0]), plant=plant)
        hourly = compute_plant_hourly_financials(
            pd_, zp, fp, carbon_price=0.0, nox_price=2.0, plant_map=pm
        )
        row = hourly.iloc[0]
        # nox_cost = 100 MWh × (0.001 × LB_PER_TONNE) lb/MWh × 2 $/lb.
        self.assertAlmostEqual(row["nox_cost"], 100.0 * 0.001 * LB_PER_TONNE * 2.0)
        # emissions in lb, not the ~2205× low tonnes-as-lb figure.
        self.assertAlmostEqual(row["nox_emissions_lbs"], 100.0 * 0.001 * LB_PER_TONNE)


class TestHeatRateMatters(unittest.TestCase):
    """A less-efficient plant in the same bin earns a lower margin."""

    def test_higher_heat_rate_means_higher_cost_lower_margin(self):
        efficient = _plant(1, heat_rate_btu_kwh=6000.0)
        inefficient = _plant(2, heat_rate_btu_kwh=10000.0)
        hours = np.arange(10)
        plant_dispatch = pd.DataFrame(
            {
                "plant_code": np.repeat([1, 2], 10),
                "generator_id": "1",
                "hour": np.tile(hours, 2),
                "dispatch_mw": 50.0,
                "bin_label": "gas_cc_h_class",
                "zone": "North",
            }
        )
        zonal_prices = pd.DataFrame(
            {"zone": "North", "hour": hours, "price_per_mwh": 40.0}
        )
        fuel_prices = pd.DataFrame(
            {"fuel_type": "gas_cc", "hour": hours, "price_per_mmbtu": 4.0}
        )
        plant_map = [efficient, inefficient]

        hourly = compute_plant_hourly_financials(
            plant_dispatch,
            zonal_prices,
            fuel_prices,
            carbon_price=0.0,
            nox_price=0.0,
            plant_map=plant_map,
        )
        annual = compute_plant_annual_summary(hourly, plant_map)
        eff = annual[annual["plant_code"] == 1].iloc[0]
        ineff = annual[annual["plant_code"] == 2].iloc[0]

        self.assertGreater(ineff["avg_marginal_cost"], eff["avg_marginal_cost"])
        self.assertLess(ineff["gross_margin"], eff["gross_margin"])
        self.assertLess(ineff["spark_spread"], eff["spark_spread"])


class TestAnnualSummary(unittest.TestCase):
    """Annual summary handles NPV discounting and zero-dispatch plants."""

    def _annual(self, dispatch_mw, year=2026, base_year=2026):
        """Run hourly + annual for a single plant with the given dispatch."""
        plant = _plant(1)
        hours = np.arange(len(dispatch_mw))
        plant_dispatch = pd.DataFrame(
            {
                "plant_code": 1,
                "generator_id": "1",
                "hour": hours,
                "dispatch_mw": np.asarray(dispatch_mw, dtype=float),
                "bin_label": plant.bin_label,
                "zone": plant.zone,
            }
        )
        zonal_prices = pd.DataFrame(
            {"zone": "North", "hour": hours, "price_per_mwh": 50.0}
        )
        fuel_prices = pd.DataFrame(
            {"fuel_type": "gas_cc", "hour": hours, "price_per_mmbtu": 3.0}
        )
        hourly = compute_plant_hourly_financials(
            plant_dispatch,
            zonal_prices,
            fuel_prices,
            carbon_price=0.0,
            nox_price=0.0,
            plant_map=[plant],
            year=year,
            base_year=base_year,
        )
        return compute_plant_annual_summary(
            hourly, [plant], year=year, base_year=base_year
        )

    def test_discount_factor_is_one_at_base_year(self):
        annual = self._annual(np.full(24, 50.0), year=2026, base_year=2026)
        self.assertAlmostEqual(annual.iloc[0]["discount_factor"], 1.0)

    def test_discount_factor_compounds_over_ten_years(self):
        annual = self._annual(np.full(24, 50.0), year=2036, base_year=2026)
        self.assertAlmostEqual(
            annual.iloc[0]["discount_factor"], 1.0 / 1.08**10, places=6
        )
        self.assertAlmostEqual(annual.iloc[0]["discount_factor"], 0.46319, places=4)

    def test_npv_is_noi_times_discount_factor(self):
        annual = self._annual(np.full(24, 50.0), year=2036, base_year=2026)
        row = annual.iloc[0]
        self.assertAlmostEqual(
            row["npv_net_operating_income"],
            row["net_operating_income"] * row["discount_factor"],
        )

    def test_zero_dispatch_plant_has_no_revenue_and_nan_metrics(self):
        annual = self._annual(np.zeros(24))
        row = annual.iloc[0]
        self.assertEqual(row["generation_mwh"], 0.0)
        self.assertEqual(row["revenue"], 0.0)
        self.assertEqual(row["total_variable_cost"], 0.0)
        self.assertTrue(np.isnan(row["avg_price_captured"]))
        self.assertTrue(np.isnan(row["avg_marginal_cost"]))
        self.assertTrue(np.isnan(row["spark_spread"]))
        self.assertTrue(np.isnan(row["co2_intensity"]))

    def test_fom_cost_scales_with_nameplate(self):
        annual = self._annual(np.full(24, 50.0))
        # 100 MW × 1000 kW/MW × 12 $/kW-yr = 1.2e6.
        self.assertAlmostEqual(annual.iloc[0]["fom_cost"], 1_200_000.0)


class TestAttributeRevenue(unittest.TestCase):
    """W2-B attribute (certificate) line: effective EAC price × generation.

    Resolved through ``policy/federal_ces.py::effective_unit_eac_prices``
    (max of legacy ``eac_price_*`` and federal premium × credit fraction);
    PTC/45Q tax credits are deliberately excluded from this line, and no
    pre-existing column changes.
    """

    def _annual(self, plants, dispatch_mw=50.0, hours=24, year=2026, config=None):
        """Run hourly + annual for ``plants`` at a flat dispatch level."""
        hour_arr = np.arange(hours)
        plant_dispatch = pd.concat(
            [
                pd.DataFrame(
                    {
                        "plant_code": p.plant_code,
                        "generator_id": p.generator_id,
                        "hour": hour_arr,
                        "dispatch_mw": float(dispatch_mw),
                        "bin_label": p.bin_label,
                        "zone": p.zone,
                    }
                )
                for p in plants
            ],
            ignore_index=True,
        )
        zonal_prices = pd.DataFrame(
            {"zone": "North", "hour": hour_arr, "price_per_mwh": 50.0}
        )
        fuel_prices = pd.DataFrame(
            {"fuel_type": "gas_cc", "hour": hour_arr, "price_per_mmbtu": 3.0}
        )
        hourly = compute_plant_hourly_financials(
            plant_dispatch,
            zonal_prices,
            fuel_prices,
            carbon_price=0.0,
            nox_price=0.0,
            plant_map=plants,
            year=year,
        )
        return compute_plant_annual_summary(hourly, plants, year=year, config=config)

    def test_columns_exist_and_zero_without_config(self):
        annual = self._annual([_plant(1)])
        self.assertIn("attribute_price_usd_per_mwh", annual.columns)
        self.assertIn("attribute_revenue", annual.columns)
        self.assertTrue((annual["attribute_price_usd_per_mwh"] == 0.0).all())
        self.assertTrue((annual["attribute_revenue"] == 0.0).all())

    def test_premium_times_generation_for_credited_fuel_only(self):
        config = ScenarioConfig(
            federal_ces_enabled=True, federal_ces_premium_usd_per_mwh=10.0
        )
        plants = [
            _plant(1, fuel_type="nuclear", emission_rate_tco2_mwh=0.0),
            _plant(2, fuel_type="gas_cc", emission_rate_tco2_mwh=0.37),
        ]
        annual = self._annual(plants, dispatch_mw=50.0, hours=24, config=config)
        by_fuel = annual.set_index("fuel_type")
        self.assertAlmostEqual(
            by_fuel.loc["nuclear", "attribute_price_usd_per_mwh"], 10.0
        )
        # 50 MW × 24 h × $10/MWh certificate value.
        self.assertAlmostEqual(by_fuel.loc["nuclear", "attribute_revenue"], 12_000.0)
        # Unabated gas earns nothing under clean_capture (PTC/45Q are tax
        # credits and never enter this line either).
        self.assertEqual(by_fuel.loc["gas_cc", "attribute_price_usd_per_mwh"], 0.0)
        self.assertEqual(by_fuel.loc["gas_cc", "attribute_revenue"], 0.0)

    def test_legacy_eac_price_wins_the_max(self):
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=10.0,
            eac_price_nuclear=15.0,
        )
        annual = self._annual([_plant(1, fuel_type="nuclear")], config=config)
        self.assertAlmostEqual(annual.iloc[0]["attribute_price_usd_per_mwh"], 15.0)

    def test_premium_path_follows_the_year(self):
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=10.0,
            federal_ces_premium_escalation_real=0.05,
        )
        plant = _plant(1, fuel_type="nuclear")
        annual_2026 = self._annual([plant], config=config, year=2026)
        annual_2036 = self._annual([plant], config=config, year=2036)
        self.assertAlmostEqual(annual_2026.iloc[0]["attribute_price_usd_per_mwh"], 10.0)
        self.assertAlmostEqual(
            annual_2036.iloc[0]["attribute_price_usd_per_mwh"],
            10.0 * 1.05**10,
            places=6,
        )

    def test_existing_metrics_untouched_by_attribute_line(self):
        # The attribute line is its own line item: NOI and revenue must be
        # identical with and without an enabled CES config.
        plant = _plant(1, fuel_type="nuclear")
        base = self._annual([plant])
        ces = self._annual(
            [plant],
            config=ScenarioConfig(
                federal_ces_enabled=True, federal_ces_premium_usd_per_mwh=30.0
            ),
        )
        for col in ("revenue", "net_operating_income", "gross_margin"):
            self.assertAlmostEqual(base.iloc[0][col], ces.iloc[0][col])

    def test_company_rollup_scales_owned_attribute_revenue(self):
        config = ScenarioConfig(
            federal_ces_enabled=True, federal_ces_premium_usd_per_mwh=10.0
        )
        annual = self._annual(
            [_plant(1, fuel_type="nuclear", emission_rate_tco2_mwh=0.0)],
            dispatch_mw=50.0,
            config=config,
        )
        ownership = pd.DataFrame(
            {
                "plant_code": [1],
                "generator_id": ["1"],
                "parent_company": ["A"],
                "percent_owned": [0.5],
            }
        )
        company_total, _ = compute_company_summary(annual, ownership)
        # $12,000 attribute revenue at 50% ownership.
        self.assertAlmostEqual(
            company_total.iloc[0]["owned_attribute_revenue"], 6_000.0
        )

    def test_company_rollup_accepts_pre_w2b_frames(self):
        # Parquets written before the attribute line have no such column;
        # the rollup must keep reading them unchanged.
        annual = self._annual([_plant(1)])
        legacy = annual.drop(
            columns=["attribute_revenue", "attribute_price_usd_per_mwh"]
        )
        ownership = pd.DataFrame(
            {
                "plant_code": [1],
                "generator_id": ["1"],
                "parent_company": ["A"],
                "percent_owned": [1.0],
            }
        )
        company_total, _ = compute_company_summary(legacy, ownership)
        self.assertNotIn("owned_attribute_revenue", company_total.columns)
        self.assertIn("owned_revenue", company_total.columns)


class TestCompanySummary(unittest.TestCase):
    """Company rollup scales every quantity by ``percent_owned``."""

    def _plant_annual(self, plant_codes, revenue, generation, co2):
        """Return a minimal plant-annual frame for the given plants."""
        n = len(plant_codes)
        return pd.DataFrame(
            {
                "plant_code": plant_codes,
                "generator_id": ["1"] * n,
                "zone": ["North"] * n,
                "fuel_type": ["gas_cc"] * n,
                "bin_label": ["gas_cc_h_class"] * n,
                "year": [2026] * n,
                "nameplate_mw": [100.0] * n,
                "generation_mwh": generation,
                "revenue": revenue,
                "fuel_mmbtu": [0.0] * n,
                "fuel_cost": [0.0] * n,
                "vom_cost": [0.0] * n,
                "carbon_cost": [0.0] * n,
                "nox_cost": [0.0] * n,
                "total_variable_cost": [0.0] * n,
                "gross_margin": revenue,
                "fom_cost": [0.0] * n,
                "net_operating_income": revenue,
                "co2_emissions_tons": co2,
                "nox_emissions_lbs": [0.0] * n,
                "npv_net_operating_income": revenue,
            }
        )

    def test_joint_ownership_splits_60_40(self):
        plant_annual = self._plant_annual([1], [1000.0], [200.0], [80.0])
        ownership = pd.DataFrame(
            {
                "plant_code": [1, 1],
                "generator_id": ["1", "1"],
                "parent_company": ["Company A", "Company B"],
                "percent_owned": [0.6, 0.4],
            }
        )
        company_total, _ = compute_company_summary(plant_annual, ownership)
        by_company = company_total.set_index("parent_company")

        self.assertAlmostEqual(by_company.loc["Company A", "owned_revenue"], 600.0)
        self.assertAlmostEqual(by_company.loc["Company B", "owned_revenue"], 400.0)
        self.assertAlmostEqual(
            by_company.loc["Company A", "owned_co2_emissions_tons"], 48.0
        )
        self.assertAlmostEqual(
            by_company.loc["Company A", "owned_generation_mwh"], 120.0
        )

    def test_portfolio_metrics_computed_after_aggregation(self):
        # 3 plants, 2 companies, plant 3 jointly owned A/B.
        plant_annual = self._plant_annual(
            [1, 2, 3],
            [1000.0, 2000.0, 3000.0],
            [100.0, 200.0, 300.0],
            [40.0, 80.0, 120.0],
        )
        ownership = pd.DataFrame(
            {
                "plant_code": [1, 2, 3, 3],
                "generator_id": ["1", "1", "1", "1"],
                "parent_company": [
                    "Company A",
                    "Company B",
                    "Company A",
                    "Company B",
                ],
                "percent_owned": [1.0, 1.0, 0.5, 0.5],
            }
        )
        company_total, company_by_fuel = compute_company_summary(
            plant_annual, ownership
        )
        a = company_total.set_index("parent_company").loc["Company A"]

        # A: plant 1 (full) + plant 3 (half).
        exp_rev = 1000.0 + 0.5 * 3000.0
        exp_gen = 100.0 + 0.5 * 300.0
        self.assertAlmostEqual(a["owned_revenue"], exp_rev)
        self.assertAlmostEqual(a["owned_generation_mwh"], exp_gen)
        self.assertAlmostEqual(a["portfolio_avg_price_captured"], exp_rev / exp_gen)
        self.assertEqual(set(company_by_fuel["fuel_type"]), {"gas_cc"})


class TestTrajectoryNpv(unittest.TestCase):
    """Trajectory NPV accumulates discounted income across years."""

    def _annual(self, year, npv):
        """Return a one-plant annual summary carrying a given NPV NOI."""
        return pd.DataFrame(
            {
                "plant_code": [1],
                "generator_id": ["1"],
                "generation_mwh": [100.0],
                "gross_margin": [500.0],
                "co2_emissions_tons": [40.0],
                "npv_net_operating_income": [npv],
            }
        )

    def test_cumulative_npv_sums_across_years(self):
        summaries = [
            self._annual(2026, 1000.0),
            self._annual(2027, 800.0),
            self._annual(2028, 600.0),
        ]
        traj = compute_trajectory_npv(summaries, [2026, 2027, 2028])
        row = traj.iloc[0]
        self.assertAlmostEqual(row["cumulative_npv_noi"], 2400.0)
        self.assertAlmostEqual(row["cumulative_generation_mwh"], 300.0)
        self.assertAlmostEqual(row["cumulative_co2_tons"], 120.0)
        self.assertAlmostEqual(row["avg_annual_margin"], 500.0)

    def test_length_mismatch_raises(self):
        with self.assertRaises(ValueError):
            compute_trajectory_npv([self._annual(2026, 1.0)], [2026, 2027])


if __name__ == "__main__":
    unittest.main()
