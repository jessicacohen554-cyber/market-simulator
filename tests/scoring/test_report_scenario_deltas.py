"""Fixture-driven tests for ``scripts/report_scenario_deltas.py`` (SCN-WS0).

No LP solves: per-case synthetic ``DispatchResult``\\ s are cached through the
real ``cache.save_result`` path, a genuine matrix bundle is written with
``matrix.write_matrix_outputs``, evolution ledgers are fabricated on the real
schema, and the report runs end-to-end over the lot.

The fixture is deliberately trivial (2 cases x 2 years, 3 units, 24 h) so
every number in the delta tables is hand-checkable, which is what the charter
asks of these tables: they must reproduce the arithmetic, not merely run.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from market_sim import matrix
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition
from market_sim.model.dispatch import DispatchResult
from market_sim.results import cache
from market_sim.results.evolution_ledger import ledger_path, write_ledger
from market_sim.results.outputs import FleetContext
from scripts import report_scenario_deltas as R

# A full 8760 at ISO-scale MW, so every quantity under test sits far above
# the summary's declared rounding grain (emissions_mt at 4 dp Mt, the by-fuel
# and by-zone dicts at 6 dp) and the assertions can stay tight.
HOURS = 8760
YEARS = (2026, 2027)
ISO = "NEISO"
GAS_RATE = 0.37

# Gas MW per hour by case: the "carbon" arm displaces 2,000 MW of gas.
GAS_MW = {"REF": 5000.0, "CARB": 3000.0}
GAS_DISPLACED_MW = GAS_MW["REF"] - GAS_MW["CARB"]
NUCLEAR_MW = 3000.0
IMPORT_MW = 1000.0
WIND_MW = 800.0


def _result(gas_mw: float) -> DispatchResult:
    """One synthetic year: nuclear flat, gas set by the case, one import rung."""
    return DispatchResult(
        dispatch=np.vstack(
            [
                np.full(HOURS, NUCLEAR_MW),  # nuclear
                np.full(HOURS, gas_mw),  # gas_cc
                np.full(HOURS, IMPORT_MW),  # import tranche (LP rate 0)
            ]
        ),
        wind_dispatched=np.full((1, HOURS), WIND_MW),
        solar_dispatched=np.zeros((1, HOURS)),
        slack=np.zeros((1, HOURS)),
        dump=np.zeros((1, HOURS)),
        prices=np.full((1, HOURS), 40.0),
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
        fuel_types=["nuclear", "gas_cc", "import"],
        pmax_mw=[3000.0, 6000.0, 1500.0],
        emission_rate=[0.0, GAS_RATE, 0.0],
        efficiency_bins=["default", "h_class", "default"],
        heat_rates=[10.4, 6.4, 0.0],
        zones=["ME", "SEMA", "HQ_import"],
        unit_ids=["NUC1", "CC1", "HQ_import_import_scarcity"],
        wind_cap_mw=1000.0,
        solar_cap_mw=0.0,
        wind_potential_mwh=WIND_MW * HOURS * 1.1,
        solar_potential_mwh=0.0,
        storage_energy_cap_mwh=0.0,
    )


class ScenarioFixture(unittest.TestCase):
    """Cache a REF and a CARB case, write a matrix bundle, fabricate ledgers."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self._original_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = tmp / "results"

        matrix_yaml = tmp / "cases.yaml"
        matrix_yaml.write_text(
            yaml.safe_dump(
                {
                    "mode": "cases",
                    "cases": {"REF": {}, "CARB": {"carbon_price_delta": 25.0}},
                }
            )
        )

        base = ScenarioConfig(iso=ISO, mode="forecast")
        sweep = SweepDefinition.from_yaml(matrix_yaml)
        self.configs = sweep.case_configs(base)
        self.members: dict[str, str] = {}
        for case, config in self.configs.items():
            for year in YEARS:
                path = cache.save_result(
                    _result(GAS_MW[case]),
                    config,
                    iso=ISO,
                    year=year,
                    context=_context(),
                )
                write_ledger(
                    ledger_path(path),
                    {
                        "iso": ISO,
                        "year": year,
                        "retirements": [
                            {
                                "unit_id": "OIL1",
                                "fuel": "oil",
                                "mw": 100.0 if case == "REF" else 250.0,
                                "reason": "economic",
                            }
                        ],
                        "thermal_additions": [],
                        "renewable_additions": [],
                        "storage_additions": [],
                        "ccs_retrofits": [],
                    },
                )
            self.members[case] = config.cache_key()

        self.matrix_dir = matrix.write_matrix_outputs(
            ISO, base, matrix_yaml, self.members, tmp / "matrix_out"
        )
        self.out_dir = tmp / "scenario_report"

    def tearDown(self):
        cache.CACHE_ROOT = self._original_root
        self._tmp.cleanup()

    def _run(self, *extra: str) -> Path:
        R.main(
            [
                "--matrix-dir",
                str(self.matrix_dir),
                "--reference-case",
                "REF",
                "--output-dir",
                str(self.out_dir),
                *extra,
            ]
        )
        return self.out_dir

    def _csv(self, name: str) -> pd.DataFrame:
        return pd.read_csv(self.out_dir / f"neiso_{name}.csv")


class TestDeltaArithmetic(ScenarioFixture):
    """Every delta table reproduces the fixture's hand arithmetic."""

    def setUp(self):
        super().setUp()
        self._run()

    def test_every_listed_output_is_written(self):
        for name in (
            "neiso_headline_deltas.csv",
            "neiso_by_fuel_deltas.csv",
            "neiso_emissions_by_zone_deltas.csv",
            "neiso_cumulative_co2_deltas.csv",
            "neiso_evolution_deltas.csv",
            "neiso_captured_price_by_tech.csv",
            "neiso_curtailment_by_tech.csv",
            "neiso_scenario_deltas_report.md",
        ):
            self.assertTrue((self.out_dir / name).exists(), name)

    def test_headline_co2_delta_is_the_displaced_gas(self):
        # 2,000 MW x 8,760 h x 0.37 t/MWh = 6.4824 Mt, negative.
        expected = -GAS_DISPLACED_MW * HOURS * GAS_RATE / 1e6
        head = self._csv("headline_deltas")
        carb = head[head["case"] == "CARB"]
        self.assertEqual(len(carb), len(YEARS))
        for delta in carb["emissions_mt_delta"]:
            self.assertAlmostEqual(delta, expected, places=4)
        # The reference differences to zero against itself.
        ref = head[head["case"] == "REF"]
        self.assertTrue((ref["emissions_mt_delta"] == 0.0).all())

    def test_headline_carries_the_widened_scalar_set(self):
        head = self._csv("headline_deltas")
        for col in (
            "unserved_mwh",
            "import_co2_mt_reported",
            "clean_share",
            "curtailment_twh",
            R.AVG_PRICE_COL,
            "generation_twh",
        ):
            self.assertIn(col, head.columns, col)
            self.assertIn(f"{col}_delta", head.columns, col)

    def test_by_fuel_delta_lands_on_gas_alone(self):
        by_fuel = self._csv("by_fuel_deltas")
        carb = by_fuel[(by_fuel["case"] == "CARB") & (by_fuel["year"] == YEARS[0])]
        gas = carb[carb["fuel"] == "gas_cc"].iloc[0]
        self.assertAlmostEqual(
            gas["generation_twh_delta"], -GAS_DISPLACED_MW * HOURS / 1e6, places=4
        )
        self.assertAlmostEqual(
            gas["emissions_mt_delta"],
            -GAS_DISPLACED_MW * HOURS * GAS_RATE / 1e6,
            places=6,
        )
        for fuel in ("nuclear", "wind", "import"):
            row = carb[carb["fuel"] == fuel].iloc[0]
            self.assertEqual(row["emissions_mt_delta"], 0.0, fuel)

    def test_by_zone_delta_lands_on_the_gas_zone_alone(self):
        by_zone = self._csv("emissions_by_zone_deltas")
        carb = by_zone[(by_zone["case"] == "CARB") & (by_zone["year"] == YEARS[0])]
        sema = carb[carb["zone"] == "SEMA"].iloc[0]
        self.assertAlmostEqual(
            sema["emissions_mt_delta"],
            -GAS_DISPLACED_MW * HOURS * GAS_RATE / 1e6,
            places=6,
        )
        self.assertEqual(carb[carb["zone"] == "ME"].iloc[0]["emissions_mt_delta"], 0.0)

    def test_cumulative_co2_delta_is_the_running_sum(self):
        cum = self._csv("cumulative_co2_deltas")
        carb = cum[cum["case"] == "CARB"].sort_values("year")
        per_year = -GAS_DISPLACED_MW * HOURS * GAS_RATE / 1e6
        self.assertAlmostEqual(
            carb.iloc[0]["cumulative_emissions_mt_delta"], per_year, places=4
        )
        self.assertAlmostEqual(
            carb.iloc[-1]["cumulative_emissions_mt_delta"],
            per_year * len(YEARS),
            places=4,
        )

    def test_import_line_is_reported_and_never_in_the_co2_delta(self):
        cum = self._csv("cumulative_co2_deltas")
        # The import rung runs identically in both cases, so its reported CO2
        # is nonzero in level and exactly zero in delta — and it never enters
        # the emissions delta, which is the displaced gas alone.
        # 1,000 MW x 8,760 h x the CARB unspecified 0.428 t/MWh = 3.74928 Mt.
        self.assertAlmostEqual(
            cum["import_co2_mt_reported"].max(),
            IMPORT_MW * HOURS * 0.428 / 1e6,
            places=6,
        )
        self.assertTrue((cum["import_co2_mt_reported_delta"] == 0.0).all())
        self.assertNotEqual(cum["emissions_mt_delta"].min(), 0.0)

    def test_evolution_deltas_vs_reference(self):
        evo = self._csv("evolution_deltas")
        carb = evo[(evo["case"] == "CARB") & (evo["event"] == "retirement")]
        self.assertTrue((carb["mw_delta"] == 150.0).all())
        ref = evo[evo["case"] == "REF"]
        self.assertTrue((ref["mw_delta"] == 0.0).all())

    def test_captured_price_covers_the_vre_pools_without_financials(self):
        captured = self._csv("captured_price_by_tech")
        self.assertEqual(set(captured["tech"]), {"wind"})
        self.assertTrue((captured["captured_price_usd_per_mwh"] == 40.0).all())

    def test_markdown_names_the_reference_and_carries_the_disclosure(self):
        md = (self.out_dir / "neiso_scenario_deltas_report.md").read_text()
        self.assertIn("Scenario delta report", md)
        self.assertIn("REF", md)
        self.assertIn("Cumulative CO2 delta", md)
        self.assertIn("NEVER added into emissions_mt", md)

    def test_unknown_reference_case_rejected(self):
        with self.assertRaises(SystemExit):
            R.main(
                [
                    "--matrix-dir",
                    str(self.matrix_dir),
                    "--reference-case",
                    "NOPE",
                    "--output-dir",
                    str(self.out_dir),
                ]
            )


class TestMatrixFrameWidening(ScenarioFixture):
    """``build_matrix_frame`` carries every scalar; the envelope is unchanged."""

    def test_frame_carries_every_scalar_metric(self):
        df = matrix.build_matrix_frame(ISO, self.members)
        for col in (
            "emissions_mt",
            "unserved_mwh",
            "import_co2_mt_reported",
            "clean_share",
            "avg_price",
            "peak_price",
            "curtailment_twh",
        ):
            self.assertIn(col, df.columns, col)
        # The historical column order is preserved at both ends.
        self.assertEqual(list(df.columns)[:3], ["case", "year", "emissions_mt"])
        self.assertEqual(list(df.columns)[-2:], ["cache_key", "label"])
        # Dict- and string-valued summary keys stay out of the long frame.
        for col in ("generation_twh", "emissions_by_fuel_mt", "import_co2_basis"):
            self.assertNotIn(col, df.columns, col)

    def test_envelope_still_reads_emissions_only(self):
        df = matrix.build_matrix_frame(ISO, self.members)
        envelope = matrix.compute_envelope(df)
        self.assertEqual(
            list(envelope.columns),
            ["year", "min_mt", "min_case", "max_mt", "max_case", "label"],
        )
        # The carbon arm burns less gas, so it is the min in every year.
        self.assertTrue((envelope["min_case"] == "CARB").all())
        self.assertTrue((envelope["max_case"] == "REF").all())

    def test_empty_members_still_yields_the_primary_column(self):
        df = matrix.build_matrix_frame(ISO, {})
        self.assertTrue(df.empty)
        self.assertEqual(
            list(df.columns), ["case", "year", "emissions_mt", "cache_key", "label"]
        )


if __name__ == "__main__":
    unittest.main()
