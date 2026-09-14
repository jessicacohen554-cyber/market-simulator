"""Fixture tests for ``scripts/collate_scenario_campaign.py`` (SCN-WS0).

No LP solves: the campaign tree is fabricated on the real
``full_horizon_summary.json`` shape, with real cached year parquets behind two
of the runs so the side lines are reconstructed through the same
``_summarize_year`` seam the rest of the report set uses, and one run whose
cache is deliberately absent so the "blank, never zero" rule is exercised.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.model.dispatch import DispatchResult
from market_sim.results.outputs import FleetContext
from scripts import collate_scenario_campaign as C

HOURS = 8760
YEARS = (2026, 2027)
GAS_RATE = 0.37
# NEISO burns 2,000 MW of gas in REF and 1,000 in CARB; PJM 6,000 and 5,000.
GAS_MW = {
    "NEISO": {"REF": 2000.0, "CARB": 1000.0},
    "PJM": {"REF": 6000.0, "CARB": 5000.0},
}
IMPORT_MW = 500.0
UNSERVED_MW = 2.0


def _result(gas_mw: float) -> DispatchResult:
    return DispatchResult(
        dispatch=np.vstack([np.full(HOURS, gas_mw), np.full(HOURS, IMPORT_MW)]),
        wind_dispatched=np.zeros((1, HOURS)),
        solar_dispatched=np.zeros((1, HOURS)),
        slack=np.full((1, HOURS), UNSERVED_MW),
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
        fuel_types=["gas_cc", "import"],
        pmax_mw=[8000.0, 900.0],
        emission_rate=[GAS_RATE, 0.0],
        efficiency_bins=["h_class", "default"],
        heat_rates=[6.4, 0.0],
        zones=["Z", "HQ_import"],
        unit_ids=["CC1", "HQ_import_import_scarcity"],
        wind_cap_mw=0.0,
        solar_cap_mw=0.0,
        wind_potential_mwh=0.0,
        solar_potential_mwh=0.0,
        storage_energy_cap_mwh=0.0,
    )


def _co2_mt(gas_mw: float) -> float:
    return round(gas_mw * HOURS * GAS_RATE / 1e6, 4)


class CampaignTree(unittest.TestCase):
    """<root>/<iso>/<case>/full_horizon_summary.json, two ISOs x two cases."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "campaign"
        self.out_dir = Path(self._tmp.name) / "rollup"
        for iso, by_case in GAS_MW.items():
            for case, gas_mw in by_case.items():
                case_dir = self.root / iso.lower() / case
                case_dir.mkdir(parents=True)
                # PJM/CARB deliberately has NO cached run dir: its side lines
                # must come back blank rather than zero.
                run_dir = None
                if not (iso == "PJM" and case == "CARB"):
                    run_dir = case_dir / "cache"
                    run_dir.mkdir()
                    for year in YEARS:
                        _result(gas_mw).to_parquet(
                            run_dir / f"year_{year}.parquet", context=_context()
                        )
                (case_dir / "full_horizon_summary.json").write_text(
                    json.dumps(
                        {
                            "iso": iso,
                            "cache_key": f"{iso.lower()}_{case}",
                            "run_dir": str(run_dir) if run_dir else None,
                            "trajectory": [
                                {"year": y, "co2_mt": _co2_mt(gas_mw)} for y in YEARS
                            ],
                        }
                    )
                )

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, *extra: str) -> Path:
        C.main(
            [
                "--root",
                str(self.root),
                "--reference-case",
                "REF",
                "--out-dir",
                str(self.out_dir),
                *extra,
            ]
        )
        return self.out_dir

    def _csv(self, name: str) -> pd.DataFrame:
        return pd.read_csv(self.out_dir / f"{name}.csv")


class TestRollup(CampaignTree):
    def setUp(self):
        super().setUp()
        self._run()

    def test_every_output_is_written(self):
        for name in (
            "campaign_emissions_by_iso.csv",
            "campaign_emissions_system.csv",
            "campaign_delta_table.csv",
            "campaign_report.md",
        ):
            self.assertTrue((self.out_dir / name).exists(), name)

    def test_iso_frame_reads_co2_from_the_summary_trajectory(self):
        by_iso = self._csv("campaign_emissions_by_iso")
        self.assertEqual(len(by_iso), 2 * 2 * len(YEARS))
        neiso_ref = by_iso[(by_iso["iso"] == "NEISO") & (by_iso["case"] == "REF")]
        self.assertTrue((neiso_ref["emissions_mt"] == _co2_mt(2000.0)).all())

    def test_system_total_sums_the_isos_present(self):
        system = self._csv("campaign_emissions_system")
        ref = system[system["case"] == "REF"].iloc[0]
        self.assertAlmostEqual(
            ref["emissions_mt"], _co2_mt(2000.0) + _co2_mt(6000.0), places=4
        )
        self.assertEqual(ref["n_isos"], 2)
        self.assertEqual(ref["isos"], "PJM+NEISO")

    def test_the_sum_names_the_isos_it_is_missing(self):
        # SEVEN ISOs since SPP-20 registered SPP (2026-09-06): the fixture tree
        # carries NEISO and PJM, so `isos_missing` -- which the collator derives
        # from SUPPORTED_ISOS, never from a hand-kept list -- names the other
        # five. Extended by SPP-38 (lane charter: a six-ISO tuple becomes seven),
        # and again by NWPP-20 (2026-09-14: NWPP is the eighth region, so the
        # fixture tree now misses six).
        system = self._csv("campaign_emissions_system")
        missing = set(system.iloc[0]["isos_missing"].split("+"))
        self.assertEqual(missing, {"ERCOT", "CAISO", "MISO", "NYISO", "SPP", "NWPP"})

    def test_the_total_is_never_labelled_national(self):
        # Every summed row carries the six-ISO label, and the only place the
        # word "national" may appear is the report's own disclaimer.
        system = self._csv("campaign_emissions_system")
        self.assertTrue((system["label"] == C.SYSTEM_LABEL).all())
        self.assertEqual(C.SYSTEM_LABEL, "six-ISO modeled system")
        self.assertNotIn("national", C.SYSTEM_LABEL.lower())
        md = (self.out_dir / "campaign_report.md").read_text()
        self.assertIn(f"**{C.SYSTEM_LABEL}**, NOT a national figure", md)
        for line in md.lower().splitlines():
            if "national" in line:
                self.assertIn("not a national figure", line)

    def test_side_lines_are_reconstructed_and_stay_outside_the_total(self):
        by_iso = self._csv("campaign_emissions_by_iso")
        neiso_ref = by_iso[(by_iso["iso"] == "NEISO") & (by_iso["case"] == "REF")].iloc[
            0
        ]
        self.assertAlmostEqual(
            neiso_ref["import_co2_mt_reported"],
            IMPORT_MW * HOURS * 0.428 / 1e6,
            places=4,
        )
        self.assertAlmostEqual(neiso_ref["unserved_mwh"], UNSERVED_MW * HOURS, places=1)
        # The reported import CO2 is large, and none of it is in the total.
        self.assertAlmostEqual(neiso_ref["emissions_mt"], _co2_mt(2000.0), places=4)

    def test_a_pruned_cache_reports_blank_not_zero(self):
        by_iso = self._csv("campaign_emissions_by_iso")
        pjm_carb = by_iso[(by_iso["iso"] == "PJM") & (by_iso["case"] == "CARB")]
        self.assertTrue(pjm_carb["import_co2_mt_reported"].isna().all())
        self.assertTrue(pjm_carb["unserved_mwh"].isna().all())
        # ...and its CO2 level is still reported.
        self.assertTrue((pjm_carb["emissions_mt"] == _co2_mt(5000.0)).all())

    def test_a_partial_side_line_does_not_produce_a_total(self):
        system = self._csv("campaign_emissions_system")
        carb = system[system["case"] == "CARB"]
        # PJM/CARB has no cache, so the CARB system side lines cannot be summed.
        self.assertTrue(carb["import_co2_mt_reported"].isna().all())
        self.assertTrue(carb["unserved_mwh"].isna().all())
        # The CO2 total, which comes from the summaries, is unaffected.
        self.assertAlmostEqual(
            carb.iloc[0]["emissions_mt"], _co2_mt(1000.0) + _co2_mt(5000.0), places=4
        )

    def test_delta_table_covers_each_iso_and_the_system(self):
        deltas = self._csv("campaign_delta_table")
        self.assertEqual(set(deltas["scope"]), {"NEISO", "PJM", C.SYSTEM_LABEL})
        neiso = deltas[(deltas["scope"] == "NEISO") & (deltas["case"] == "CARB")]
        expected = _co2_mt(1000.0) - _co2_mt(2000.0)
        self.assertTrue(
            np.allclose(neiso["emissions_mt_delta"].to_numpy(), expected, atol=1e-4)
        )
        # Cumulative is the running sum across the campaign's years.
        self.assertAlmostEqual(
            neiso.sort_values("year").iloc[-1]["cumulative_emissions_mt_delta"],
            expected * len(YEARS),
            places=4,
        )

    def test_system_delta_is_the_sum_of_the_iso_deltas(self):
        deltas = self._csv("campaign_delta_table")
        carb = deltas[(deltas["case"] == "CARB") & (deltas["year"] == YEARS[0])]
        iso_sum = carb[carb["scope"] != C.SYSTEM_LABEL]["emissions_mt_delta"].sum()
        system = carb[carb["scope"] == C.SYSTEM_LABEL]["emissions_mt_delta"].iloc[0]
        self.assertAlmostEqual(system, iso_sum, places=4)

    def test_reference_rows_difference_to_zero(self):
        deltas = self._csv("campaign_delta_table")
        ref = deltas[deltas["case"] == "REF"]
        self.assertTrue((ref["emissions_mt_delta"] == 0.0).all())

    def test_markdown_carries_all_three_side_lines(self):
        md = (self.out_dir / "campaign_report.md").read_text()
        self.assertIn("Import-attributed CO2", md)
        self.assertIn("Unserved energy", md)
        self.assertIn("ISOs not modeled", md)
        self.assertIn("SPP", md)


class TestGuards(CampaignTree):
    def test_unknown_reference_case_rejected(self):
        with self.assertRaises(SystemExit):
            self._run_with_ref("NOPE")

    def _run_with_ref(self, ref: str):
        C.main(
            [
                "--root",
                str(self.root),
                "--reference-case",
                ref,
                "--out-dir",
                str(self.out_dir),
            ]
        )

    def test_empty_root_rejected(self):
        empty = self.root.parent / "empty"
        empty.mkdir()
        with self.assertRaises(SystemExit):
            C.main(["--root", str(empty), "--out-dir", str(self.out_dir)])


if __name__ == "__main__":
    unittest.main()
