"""Tests for the "backstop-built" column of ``scripts/report_scenario_deltas.py``.

SCN-WS4b (plan §3 WS-4 item 3). Trivial-first, no LP: the pure ledger walk is
checked on hand-built ledger dicts, then the column runs end-to-end through the
real ``cache.save_result`` / matrix-bundle path on a 24-hour, three-unit fixture
whose every number is hand-checkable — the way SCN-WS0 tested the generic delta
tables (``test_report_scenario_deltas.py``).

The fixture pairs a REF with a LOAD-HI case. LOAD-HI's ledger records one
reserve-backstop gas_ct in each year (500 MW in 2026, 300 MW more in 2027) and
its cached fleet carries those units dispatching flat, so:

* ``backstop_built_mw``  is cumulative on the books: 500 then 800;
* ``backstop_built_mwh`` is the units' dispatch: 200 MW x 24 h, then
  (200 + 100) MW x 24 h;
* REF carries neither, so the deltas equal the LOAD-HI levels.
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

HOURS = 24
YEARS = (2026, 2027)
ISO = "PJM"
GAS_RATE = 0.37

NUCLEAR_MW = 3000.0
GAS_MW = 5000.0
# Backstop units: built (ledger) and dispatched (cache) per LOAD-HI year.
BACKSTOP_BUILD_MW = {2026: 500.0, 2027: 300.0}
BACKSTOP_DISPATCH_MW = {"gas_ct_adequacy_2026": 200.0, "gas_ct_adequacy_2027": 100.0}


class TestBackstopUnitsByYear(unittest.TestCase):
    """The pure ledger walk, on hand-built dicts."""

    def test_empty_in_empty_out(self):
        self.assertEqual(R.backstop_units_by_year({}), {})

    def test_only_reserve_backstop_rows_count(self):
        ledgers = {
            2026: {
                "thermal_additions": [
                    {
                        "unit_id": "gas_cc_new",
                        "fuel": "gas_cc",
                        "mw": 900.0,
                        "source": "economic",
                    },
                    {
                        "unit_id": "eia_plant",
                        "fuel": "gas_ct",
                        "mw": 100.0,
                        "source": "planned",
                    },
                    {
                        "unit_id": "gas_ct_adequacy_2026",
                        "fuel": "gas_ct",
                        "mw": 500.0,
                        "source": "reserve_backstop",
                    },
                ]
            }
        }
        self.assertEqual(
            R.backstop_units_by_year(ledgers), {2026: {"gas_ct_adequacy_2026": 500.0}}
        )

    def test_cumulative_and_netted_by_retirement(self):
        ledgers = {
            2026: {
                "thermal_additions": [
                    {
                        "unit_id": "gas_ct_adequacy_2026",
                        "mw": 500.0,
                        "source": "reserve_backstop",
                    }
                ]
            },
            2027: {
                "thermal_additions": [
                    {
                        "unit_id": "gas_ct_adequacy_2027",
                        "mw": 300.0,
                        "source": "reserve_backstop",
                    }
                ]
            },
            2028: {
                "retirements": [
                    {
                        "unit_id": "gas_ct_adequacy_2026",
                        "mw": 500.0,
                        "reason": "economic",
                    }
                ],
                "thermal_additions": [],
            },
            2029: {},
        }
        out = R.backstop_units_by_year(ledgers)
        self.assertEqual(out[2026], {"gas_ct_adequacy_2026": 500.0})
        self.assertEqual(
            out[2027], {"gas_ct_adequacy_2026": 500.0, "gas_ct_adequacy_2027": 300.0}
        )
        # The 2026 unit leaves the books in 2028; the 2027 unit stays.
        self.assertEqual(out[2028], {"gas_ct_adequacy_2027": 300.0})
        self.assertEqual(out[2029], {"gas_ct_adequacy_2027": 300.0})

    def test_on_books_lookup_falls_back_to_prior_ledger_year(self):
        by_year = {2026: {"a": 1.0}, 2028: {"a": 1.0, "b": 2.0}}
        self.assertEqual(R._backstop_on_books(by_year, 2025), {})
        self.assertEqual(R._backstop_on_books(by_year, 2026), {"a": 1.0})
        self.assertEqual(R._backstop_on_books(by_year, 2027), {"a": 1.0})
        self.assertEqual(R._backstop_on_books(by_year, 2028), {"a": 1.0, "b": 2.0})


def _result(n_units: int, dispatch_mw: list[float]) -> DispatchResult:
    """One synthetic year of flat dispatch, one row per unit."""
    assert len(dispatch_mw) == n_units
    return DispatchResult(
        dispatch=np.vstack([np.full(HOURS, mw) for mw in dispatch_mw]),
        wind_dispatched=np.zeros((1, HOURS)),
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


def _context(backstop_ids: list[str]) -> FleetContext:
    """Nuclear + gas_cc, plus one gas_ct row per backstop unit on the books."""
    n = 2 + len(backstop_ids)
    return FleetContext(
        fuel_types=["nuclear", "gas_cc"] + ["gas_ct"] * len(backstop_ids),
        pmax_mw=[3000.0, 6000.0]
        + [BACKSTOP_BUILD_MW[int(u[-4:])] for u in backstop_ids],
        emission_rate=[0.0, GAS_RATE] + [0.55] * len(backstop_ids),
        efficiency_bins=["default"] * n,
        heat_rates=[10.4, 6.4] + [11.0] * len(backstop_ids),
        zones=["PJM_Dominion"] * n,
        unit_ids=["NUC1", "CC1"] + list(backstop_ids),
        wind_cap_mw=0.0,
        solar_cap_mw=0.0,
        wind_potential_mwh=0.0,
        solar_potential_mwh=0.0,
        storage_energy_cap_mwh=0.0,
    )


def _ledger(year: int, backstop_mw: float | None) -> dict:
    rows = []
    if backstop_mw is not None:
        rows.append(
            {
                "unit_id": f"gas_ct_adequacy_{year}",
                "fuel": "gas_ct",
                "mw": backstop_mw,
                "zone": "PJM_Dominion",
                "source": "reserve_backstop",
                "eia860_id": None,
            }
        )
    return {
        "iso": ISO,
        "year": year,
        "retirements": [],
        "thermal_additions": rows,
        "renewable_additions": [],
        "storage_additions": [],
        "ccs_retrofits": [],
    }


class BackstopFixture(unittest.TestCase):
    """Cache REF and LOAD-HI, write the matrix bundle and the ledgers."""

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
                    "cases": {
                        "REF": {},
                        "LOAD-HI": {
                            "demand_growth_path": "high",
                            "datacenter_load_path": "high",
                        },
                    },
                }
            )
        )
        base = ScenarioConfig(iso=ISO, mode="forecast")
        sweep = SweepDefinition.from_yaml(matrix_yaml)
        self.configs = sweep.case_configs(base)
        self.members: dict[str, str] = {}
        for case, config in self.configs.items():
            on_books: list[str] = []
            for year in YEARS:
                if case == "LOAD-HI":
                    on_books.append(f"gas_ct_adequacy_{year}")
                dispatch = [NUCLEAR_MW, GAS_MW] + [
                    BACKSTOP_DISPATCH_MW[u] for u in on_books
                ]
                path = cache.save_result(
                    _result(2 + len(on_books), dispatch),
                    config,
                    iso=ISO,
                    year=year,
                    context=_context(on_books),
                )
                write_ledger(
                    ledger_path(path),
                    _ledger(
                        year, BACKSTOP_BUILD_MW[year] if case == "LOAD-HI" else None
                    ),
                )
            self.members[case] = config.cache_key()

        self.matrix_dir = matrix.write_matrix_outputs(
            ISO, base, matrix_yaml, self.members, tmp / "matrix_out"
        )
        self.out_dir = tmp / "scenario_report"
        R.main(
            [
                "--matrix-dir",
                str(self.matrix_dir),
                "--reference-case",
                "REF",
                "--output-dir",
                str(self.out_dir),
            ]
        )

    def tearDown(self):
        cache.CACHE_ROOT = self._original_root
        self._tmp.cleanup()

    def _headline(self) -> pd.DataFrame:
        return pd.read_csv(self.out_dir / "pjm_headline_deltas.csv")


class TestBackstopBuiltColumn(BackstopFixture):
    """The column reproduces the fixture's hand arithmetic end-to-end."""

    def test_columns_and_their_deltas_are_present(self):
        head = self._headline()
        for col in (R.BACKSTOP_MW_COL, R.BACKSTOP_MWH_COL):
            self.assertIn(col, head.columns, col)
            self.assertIn(f"{col}_bau", head.columns, col)
            self.assertIn(f"{col}_delta", head.columns, col)

    def test_mw_is_cumulative_on_the_books(self):
        head = self._headline().set_index(["case", "year"])
        self.assertEqual(head.loc[("LOAD-HI", 2026), R.BACKSTOP_MW_COL], 500.0)
        self.assertEqual(head.loc[("LOAD-HI", 2027), R.BACKSTOP_MW_COL], 800.0)
        self.assertEqual(head.loc[("REF", 2026), R.BACKSTOP_MW_COL], 0.0)
        self.assertEqual(head.loc[("REF", 2027), R.BACKSTOP_MW_COL], 0.0)

    def test_mwh_is_the_backstop_units_dispatch(self):
        head = self._headline().set_index(["case", "year"])
        self.assertAlmostEqual(
            head.loc[("LOAD-HI", 2026), R.BACKSTOP_MWH_COL], 200.0 * HOURS, places=3
        )
        self.assertAlmostEqual(
            head.loc[("LOAD-HI", 2027), R.BACKSTOP_MWH_COL], 300.0 * HOURS, places=3
        )
        self.assertEqual(head.loc[("REF", 2026), R.BACKSTOP_MWH_COL], 0.0)

    def test_delta_vs_reference_equals_the_level(self):
        head = self._headline()
        hi = head[head["case"] == "LOAD-HI"]
        self.assertTrue(
            (hi[f"{R.BACKSTOP_MW_COL}_delta"] == hi[R.BACKSTOP_MW_COL]).all()
        )
        self.assertTrue(
            (hi[f"{R.BACKSTOP_MWH_COL}_delta"] == hi[R.BACKSTOP_MWH_COL]).all()
        )
        ref = head[head["case"] == "REF"]
        self.assertTrue((ref[f"{R.BACKSTOP_MW_COL}_delta"] == 0.0).all())

    def test_backstop_energy_is_inside_the_scored_totals_not_beside_them(self):
        # The column is a disclosure of a share of generation_twh / emissions_mt,
        # never a separate stream: the gas_ct rows ARE in the by-fuel totals.
        by_fuel = pd.read_csv(self.out_dir / "pjm_by_fuel_deltas.csv")
        ct = by_fuel[(by_fuel["case"] == "LOAD-HI") & (by_fuel["fuel"] == "gas_ct")]
        self.assertAlmostEqual(
            ct[ct["year"] == 2027]["generation_twh"].iloc[0],
            300.0 * HOURS / 1e6,
            places=6,
        )
        self.assertAlmostEqual(
            ct[ct["year"] == 2027]["capacity_gw"].iloc[0], 0.8, places=6
        )

    def test_markdown_carries_the_columns_and_the_definition(self):
        md = (self.out_dir / "pjm_scenario_deltas_report.md").read_text()
        self.assertIn(R.BACKSTOP_MW_COL, md)
        self.assertIn(R.BACKSTOP_MWH_COL, md)
        self.assertIn("reserve_backstop", md)
        self.assertIn("energy-only ERCOT", md)
        self.assertIn("understated by", md)

    def test_no_unmatched_note_when_ledger_and_fleet_agree(self):
        md = (self.out_dir / "pjm_scenario_deltas_report.md").read_text()
        self.assertNotIn("absent from the cached fleet", md)


class TestUnmatchedBackstopUnitIsReported(unittest.TestCase):
    """A ledger naming a backstop unit the cached fleet lacks is a note, not a silent 0."""

    def test_note_is_appended_and_mw_still_counted(self):
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            original = cache.CACHE_ROOT
            cache.CACHE_ROOT = tmp / "results"
            try:
                config = ScenarioConfig(iso=ISO, mode="forecast")
                path = cache.save_result(
                    _result(2, [NUCLEAR_MW, GAS_MW]),
                    config,
                    iso=ISO,
                    year=2026,
                    context=_context([]),  # no gas_ct row in the fleet
                )
                write_ledger(ledger_path(path), _ledger(2026, 500.0))
                key = config.cache_key()
                notes: list[str] = []
                units = R.backstop_units_for_cases(ISO, {"X": key})
                frames = R.collect_case_year_frames(
                    ISO,
                    {"X": key},
                    {"X": config},
                    None,
                    backstop_units=units,
                    notes=notes,
                )
            finally:
                cache.CACHE_ROOT = original
        head = frames["headline"]
        self.assertEqual(head[R.BACKSTOP_MW_COL].iloc[0], 500.0)
        self.assertEqual(head[R.BACKSTOP_MWH_COL].iloc[0], 0.0)
        self.assertEqual(len(notes), 1)
        self.assertIn("gas_ct_adequacy_2026", notes[0])

    def test_omitting_the_map_keeps_the_pre_ws4b_frame(self):
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            original = cache.CACHE_ROOT
            cache.CACHE_ROOT = tmp / "results"
            try:
                config = ScenarioConfig(iso=ISO, mode="forecast")
                cache.save_result(
                    _result(2, [NUCLEAR_MW, GAS_MW]),
                    config,
                    iso=ISO,
                    year=2026,
                    context=_context([]),
                )
                frames = R.collect_case_year_frames(
                    ISO, {"X": config.cache_key()}, {"X": config}, None
                )
            finally:
                cache.CACHE_ROOT = original
        self.assertNotIn(R.BACKSTOP_MW_COL, frames["headline"].columns)


if __name__ == "__main__":
    unittest.main()
