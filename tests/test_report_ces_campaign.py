"""Fixture-driven end-to-end tests for ``scripts/report_ces_campaign.py`` (W2-B).

No LP solves (plan §8 W2-B: synthetic cached fixtures): per-case synthetic
``DispatchResult``\\ s are cached through the real ``cache.save_result`` path,
a genuine matrix bundle is written with ``matrix.write_matrix_outputs`` from
the committed first-campaign ladder ``configs/ces_premium_matrix.yaml``,
evolution ledgers and financial report parquets are fabricated on the real
schemas, and the report script runs end-to-end over the lot. The dispatch is
shaped so the CES direction is checkable: a rising premium displaces gas,
raises delivered wind, and deepens negative-price epochs.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim import matrix
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition
from market_sim.model.dispatch import DispatchResult
from market_sim.results import cache
from market_sim.results.evolution_ledger import ledger_path, write_ledger
from market_sim.results.outputs import FleetContext
from scripts import report_ces_campaign as R

REPO = Path(__file__).resolve().parent.parent
MATRIX_YAML = REPO / "configs" / "ces_premium_matrix.yaml"
MATRIX_CI_YAML = REPO / "configs" / "ces_premium_matrix_ci.yaml"

HOURS = 24
YEARS = (2026, 2027)
ISO = "ERCOT"

# Premium per first-campaign case (mirrors configs/ces_premium_matrix.yaml).
PREMIUMS = {"BAU": 0.0, "CES-10": 10.0, "CES-20": 20.0, "CES-30": 30.0}


def _result(premium: float) -> DispatchResult:
    """One synthetic year: higher premium ⇒ less gas, more wind, deeper negatives."""
    nuclear = np.full(HOURS, 80.0)
    gas = np.full(HOURS, 100.0 - premium)
    prices = np.full((1, HOURS), 40.0)
    n_negative = int(premium / 10.0)  # 0..3 negative hours across the ladder
    if n_negative:
        prices[0, :n_negative] = -5.0
    return DispatchResult(
        dispatch=np.vstack([nuclear, gas]),
        wind_dispatched=np.full((1, HOURS), 20.0 + premium / 2.0),
        solar_dispatched=np.zeros((1, HOURS)),
        slack=np.zeros((1, HOURS)),
        dump=np.zeros((1, HOURS)),
        prices=prices,
        storage_charge=None,
        storage_discharge=None,
        storage_soc=None,
        flows=None,
        objective_value=0.0,
        status="Optimal",
        build_time=0.0,
        solve_time=0.0,
    )


def _context() -> FleetContext:
    return FleetContext(
        fuel_types=["nuclear", "gas_cc"],
        pmax_mw=[100.0, 150.0],
        emission_rate=[0.0, 0.37],
        efficiency_bins=["default", "h_class"],
        heat_rates=[10.4, 6.4],
        zones=["Z", "Z"],
        unit_ids=["NUC1", "CC1"],
        wind_cap_mw=50.0,
        solar_cap_mw=0.0,
        wind_potential_mwh=1200.0,
        solar_potential_mwh=0.0,
        storage_energy_cap_mwh=0.0,
    )


def _plant_annual(premium: float, year: int) -> pd.DataFrame:
    """Fabricate a plant_annual report parquet frame (the W2-B contract)."""
    gen = [80.0 * HOURS, (100.0 - premium) * HOURS]
    price = [40.0, 40.0 - premium / 10.0]
    return pd.DataFrame(
        {
            "plant_code": [1, 2],
            "generator_id": ["1", "1"],
            "zone": ["Z", "Z"],
            "fuel_type": ["nuclear", "gas_cc"],
            "year": year,
            "generation_mwh": gen,
            "revenue": [g * p for g, p in zip(gen, price)],
            "attribute_revenue": [gen[0] * premium, 0.0],
            "net_operating_income": [1000.0 + premium * 10.0, 500.0 - premium],
            "avg_price_captured": price,
        }
    )


def _company_annual(premium: float, year: int) -> pd.DataFrame:
    """Fabricate a company_annual report parquet frame."""
    plant = _plant_annual(premium, year)
    return pd.DataFrame(
        {
            "parent_company": ["NukeCo", "GasCo"],
            "year": year,
            "owned_revenue": plant["revenue"].tolist(),
            "owned_attribute_revenue": plant["attribute_revenue"].tolist(),
            "owned_generation_mwh": plant["generation_mwh"].tolist(),
        }
    )


class CampaignFixture(unittest.TestCase):
    """Cache four ladder cases + bundle + ledgers + financial parquets."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self._original_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = tmp / "results"

        base = ScenarioConfig(iso=ISO, mode="forecast")
        sweep = SweepDefinition.from_yaml(MATRIX_YAML)
        self.configs = sweep.case_configs(base)
        self.members: dict[str, str] = {}
        for case, config in self.configs.items():
            premium = PREMIUMS[case]
            for year in YEARS:
                path = cache.save_result(
                    _result(premium), config, iso=ISO, year=year, context=_context()
                )
                write_ledger(
                    ledger_path(path),
                    {
                        "iso": ISO,
                        "year": year,
                        "retirements": [
                            {
                                "unit_id": "COAL1",
                                "fuel": "coal",
                                "mw": 100.0 + premium,
                                "reason": "economic",
                            }
                        ],
                        "thermal_additions": [],
                        "renewable_additions": (
                            [{"zone": "Z", "tech": "solar", "mw": premium * 10.0}]
                            if premium
                            else []
                        ),
                        "storage_additions": [],
                        "ccs_retrofits": (
                            [
                                {
                                    "unit_id": "CC1",
                                    "mw": premium,
                                    "from_fuel": "gas_cc",
                                    "to_fuel": "gas_cc_ccs",
                                }
                            ]
                            if premium
                            else []
                        ),
                    },
                )
            self.members[case] = config.cache_key()

        self.matrix_dir = matrix.write_matrix_outputs(
            ISO, base, MATRIX_YAML, self.members, tmp / "matrix_out"
        )

        self.reports_root = tmp / "reports"
        for case, key in self.members.items():
            report_dir = self.reports_root / key
            report_dir.mkdir(parents=True)
            for year in YEARS:
                _plant_annual(PREMIUMS[case], year).to_parquet(
                    report_dir / f"plant_annual_{year}.parquet", index=False
                )
                _company_annual(PREMIUMS[case], year).to_parquet(
                    report_dir / f"company_annual_{year}.parquet", index=False
                )

        self.out_dir = tmp / "ces_report"

    def tearDown(self):
        cache.CACHE_ROOT = self._original_root
        self._tmp.cleanup()

    def _run(self, *extra: str) -> Path:
        R.main(
            [
                "--matrix-dir",
                str(self.matrix_dir),
                "--financial-reports-root",
                str(self.reports_root),
                "--output-dir",
                str(self.out_dir),
                *extra,
            ]
        )
        return self.out_dir


class TestEndToEnd(CampaignFixture):
    """The full §5.4 output set is produced and directionally correct."""

    def test_every_listed_output_is_written(self):
        out = self._run("--nominal")
        for name in (
            "clean_share_vs_premium.csv",
            "capacity_by_fuel_deltas.csv",
            "evolution_deltas.csv",
            "captured_price_by_tech.csv",
            "curtailment_by_tech.csv",
            "premium_capture.csv",
            "plant_revenue_deltas.csv",
            "company_revenue_deltas.csv",
            "ces_campaign_report.md",
        ):
            self.assertTrue((out / f"ercot_{name}").exists(), name)

    def test_clean_share_vs_premium_curve(self):
        out = self._run()
        curve = pd.read_csv(out / "ercot_clean_share_vs_premium.csv")
        y0 = curve[curve["year"] == YEARS[0]].set_index("case")
        # Premium levels come from each case's cached config.
        for case, premium in PREMIUMS.items():
            self.assertAlmostEqual(y0.loc[case, "premium_usd_per_mwh"], premium)
        # BAU anchors at its real physical clean share, not zero...
        self.assertGreater(y0.loc["BAU", "clean_share"], 0.0)
        # ...and clean share rises monotonically along the ladder.
        shares = [
            y0.loc[c, "clean_share"] for c in ("BAU", "CES-10", "CES-20", "CES-30")
        ]
        self.assertTrue(all(a < b for a, b in zip(shares, shares[1:])), shares)
        # The premium deepens negative-price epochs (delta vs BAU > 0).
        self.assertGreater(y0.loc["CES-30", "negative_price_hours_delta"], 0.0)
        self.assertEqual(y0.loc["BAU", "negative_price_hours_delta"], 0.0)

    def test_capacity_and_generation_deltas(self):
        out = self._run()
        by_fuel = pd.read_csv(out / "ercot_capacity_by_fuel_deltas.csv")
        y0 = by_fuel[by_fuel["year"] == YEARS[0]]
        gas30 = y0[(y0["case"] == "CES-30") & (y0["fuel"] == "gas_cc")].iloc[0]
        # Same fixture fleet in every case: capacity delta is exactly zero...
        self.assertEqual(gas30["capacity_gw_delta"], 0.0)
        # ...while the premium displaces gas energy (30 MW × 24 h = 0.00072 TWh).
        self.assertAlmostEqual(gas30["generation_twh_delta"], -0.0007, places=4)

    def test_evolution_deltas_vs_bau(self):
        out = self._run()
        evo = pd.read_csv(out / "ercot_evolution_deltas.csv")
        y0 = evo[evo["year"] == YEARS[0]]
        coal30 = y0[
            (y0["case"] == "CES-30")
            & (y0["event"] == "retirement")
            & (y0["tech"] == "coal")
        ].iloc[0]
        self.assertAlmostEqual(coal30["mw_delta"], 30.0)
        solar30 = y0[
            (y0["case"] == "CES-30")
            & (y0["event"] == "build")
            & (y0["tech"] == "solar")
        ].iloc[0]
        # BAU built no solar: the baseline is a genuine zero, not NaN.
        self.assertAlmostEqual(solar30["mw_bau"], 0.0)
        self.assertAlmostEqual(solar30["mw_delta"], 300.0)
        retrofit30 = y0[(y0["case"] == "CES-30") & (y0["event"] == "retrofit")].iloc[0]
        self.assertAlmostEqual(retrofit30["mw_delta"], 30.0)

    def test_premium_capture_rate(self):
        out = self._run()
        cap = pd.read_csv(out / "ercot_premium_capture.csv")
        y0 = cap[cap["year"] == YEARS[0]].set_index("case")
        # Credited fleet: nuclear (100 MW nameplate, 80 MW dispatched) + wind
        # (1200 MWh potential) — capture sits strictly inside (0, 1) and the
        # premium raises delivered wind, so capture rises along the ladder.
        for case in PREMIUMS:
            self.assertGreater(y0.loc[case, "premium_capture_rate"], 0.0)
            self.assertLess(y0.loc[case, "premium_capture_rate"], 1.0)
        self.assertGreater(
            y0.loc["CES-30", "premium_capture_rate"],
            y0.loc["BAU", "premium_capture_rate"],
        )

    def test_curtailment_by_tech(self):
        out = self._run()
        curt = pd.read_csv(out / "ercot_curtailment_by_tech.csv")
        wind = curt[(curt["tech"] == "wind") & (curt["year"] == YEARS[0])].set_index(
            "case"
        )
        # 1200 MWh potential; BAU delivers 480 MWh, CES-30 delivers 840 MWh.
        self.assertAlmostEqual(wind.loc["BAU", "curtailed_mwh"], 720.0)
        self.assertAlmostEqual(wind.loc["CES-30", "curtailed_mwh_delta"], -360.0)

    def test_captured_price_by_tech(self):
        out = self._run()
        captured = pd.read_csv(out / "ercot_captured_price_by_tech.csv")
        y0 = captured[captured["year"] == YEARS[0]]
        nuke = y0[(y0["case"] == "BAU") & (y0["tech"] == "nuclear")].iloc[0]
        self.assertAlmostEqual(nuke["captured_price_usd_per_mwh"], 40.0)
        self.assertEqual(nuke["source"], "plant_financials")
        wind = y0[(y0["case"] == "CES-30") & (y0["tech"] == "wind")].iloc[0]
        self.assertEqual(wind["source"], "dispatch_cache")
        # Three −$5 hours drag the flat-dispatch wind capture below $40.
        self.assertLess(wind["captured_price_usd_per_mwh"], 40.0)
        self.assertLess(wind["captured_price_usd_per_mwh_delta"], 0.0)

    def test_revenue_delta_tables_follow_compare_conventions(self):
        out = self._run()
        company = pd.read_csv(out / "ercot_company_revenue_deltas.csv")
        self.assertIn("owned_revenue_BAU", company.columns)
        self.assertIn("owned_revenue_delta_CES-30", company.columns)
        self.assertNotIn("owned_revenue_delta_BAU", company.columns)
        row = company.set_index("parent_company").loc["NukeCo"]
        self.assertAlmostEqual(
            row["owned_revenue_delta_CES-30"],
            row["owned_revenue_CES-30"] - row["owned_revenue_BAU"],
        )
        # The attribute line rides along: nuclear earns premium × generation.
        self.assertAlmostEqual(
            row["owned_attribute_revenue_delta_CES-30"],
            80.0 * HOURS * 30.0 * len(YEARS),
        )

        plant = pd.read_csv(out / "ercot_plant_revenue_deltas.csv")
        self.assertIn("attribute_revenue_delta_CES-10", plant.columns)
        gas = plant[plant["fuel_type"] == "gas_cc"].iloc[0]
        # Gas loses energy revenue and earns no certificates.
        self.assertLess(gas["revenue_delta_CES-30"], 0.0)
        self.assertEqual(gas["attribute_revenue_delta_CES-30"], 0.0)

    def test_nominal_columns_optional(self):
        out = self._run("--nominal")
        curve = pd.read_csv(out / "ercot_clean_share_vs_premium.csv")
        self.assertIn("premium_usd_per_mwh_nominal", curve.columns)
        y1 = curve[(curve["year"] == 2027) & (curve["case"] == "CES-10")].iloc[0]
        # 2027 nominal = real × (1 + inflation); 2026 anchors real == nominal.
        self.assertGreater(y1["premium_usd_per_mwh_nominal"], 10.0)
        company = pd.read_csv(out / "ercot_company_revenue_deltas.csv")
        self.assertIn("owned_revenue_nominal_CES-10", company.columns)
        # Without the flag, no nominal columns anywhere.
        out2 = self._run()
        curve2 = pd.read_csv(out2 / "ercot_clean_share_vs_premium.csv")
        self.assertNotIn("premium_usd_per_mwh_nominal", curve2.columns)

    def test_markdown_report_content(self):
        out = self._run()
        text = (out / "ercot_ces_campaign_report.md").read_text()
        self.assertIn("Clean-share vs premium", text)
        self.assertIn("CES-30", text)
        self.assertIn("Notes & definitions", text)
        # The matrix label rides through so nobody quotes this as probability.
        self.assertIn("deterministic scenario range", text)

    def test_unknown_bau_case_rejected(self):
        with self.assertRaises(SystemExit):
            self._run("--bau-case", "NOPE")


class TestGracefulDegradation(CampaignFixture):
    """Missing ledgers / financial parquets degrade to noted, partial output."""

    def test_runs_without_financial_reports(self):
        import shutil

        shutil.rmtree(self.reports_root)
        self.reports_root.mkdir()
        out = self._run()
        text = (out / "ercot_ces_campaign_report.md").read_text()
        self.assertIn("generate_financial_reports", text)
        # Cache-derived outputs are still complete.
        curve = pd.read_csv(out / "ercot_clean_share_vs_premium.csv")
        self.assertEqual(set(curve["case"]), set(PREMIUMS))
        # Wind/solar captured prices need no financial parquets.
        captured = pd.read_csv(out / "ercot_captured_price_by_tech.csv")
        self.assertEqual(set(captured["tech"]), {"wind"})


class TestCesPremiumMatrixYamls(unittest.TestCase):
    """The committed first-campaign ladder and the parked cesa_ci variant."""

    def test_first_campaign_ladder(self):
        sweep = SweepDefinition.from_yaml(MATRIX_YAML)
        self.assertEqual(list(sweep.cases), ["BAU", "CES-10", "CES-20", "CES-30"])
        self.assertEqual(sweep.cases["BAU"], {})
        base = ScenarioConfig(iso=ISO, mode="forecast")
        configs = sweep.case_configs(base)
        for case, premium in PREMIUMS.items():
            config = configs[case]
            self.assertEqual(config.federal_ces_enabled, premium > 0.0)
            self.assertEqual(config.federal_ces_premium_usd_per_mwh, premium)
            # First campaign is clean_capture-only (owner v2.1 / D8).
            self.assertEqual(config.federal_ces_crediting, "clean_capture")

    def test_parked_ci_variant_ladder(self):
        sweep = SweepDefinition.from_yaml(MATRIX_CI_YAML)
        self.assertEqual(list(sweep.cases), ["BAU", "CI-10", "CI-20", "CI-30"])
        base = ScenarioConfig(iso=ISO, mode="forecast")
        configs = sweep.case_configs(base)
        self.assertEqual(configs["BAU"].federal_ces_enabled, False)
        for case, premium in (("CI-10", 10.0), ("CI-20", 20.0), ("CI-30", 30.0)):
            config = configs[case]
            self.assertTrue(config.federal_ces_enabled)
            self.assertEqual(config.federal_ces_premium_usd_per_mwh, premium)
            self.assertEqual(config.federal_ces_crediting, "cesa_ci")

    def test_distinct_cache_keys_per_case(self):
        base = ScenarioConfig(iso=ISO, mode="forecast")
        configs = SweepDefinition.from_yaml(MATRIX_YAML).case_configs(base)
        keys = {config.cache_key() for config in configs.values()}
        self.assertEqual(len(keys), 4)


if __name__ == "__main__":
    unittest.main()
