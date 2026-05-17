"""Tests for the EIA-860 ownership pipeline."""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from market_sim.data.ownership import (
    attribute_emissions,
    build_parent_mapping,
    load_eia860_ownership,
    summarize_fleet_by_parent,
    validate_percent_owned,
)
from market_sim.data.ownership_config import OwnershipChange


def _write_eia860_dir(path: Path) -> None:
    """Write a minimal EIA-860 parquet trio into ``path``.

    Two generators: plant 100 is wholly operator-owned (absent from the
    owner sheet); plant 200 is jointly owned 60/40 and present in it.
    """
    generators = pd.DataFrame(
        {
            "Plant Code": [100, 200],
            "Generator ID": ["1", "1"],
            "Utility ID": [195, 5416],
            "Utility Name": ["Alabama Power Co", "Duke Energy Carolinas"],
            "Nameplate Capacity (MW)": [500.0, 1000.0],
            "Energy Source 1": ["NG", "NUC"],
            "Prime Mover": ["CC", "ST"],
            "Status": ["OP", "OP"],
        }
    )
    owners = pd.DataFrame(
        {
            "Plant Code": [200, 200],
            "Generator ID": ["1", "1"],
            "Owner Utility ID": [5416, 19876],
            "Owner Name": ["Duke Energy Carolinas", "Virginia Electric"],
            "Percent Owned": [0.60, 0.40],
            "Status": ["OP", "OP"],
        }
    )
    plants = pd.DataFrame(
        {
            "Plant Code": [100, 200],
            "Balancing Authority Code": ["SOCO", "DUK"],
            "State": ["AL", "NC"],
        }
    )
    generators.to_parquet(path / "eia860_generator_operable.parquet", index=False)
    owners.to_parquet(path / "eia860_owner.parquet", index=False)
    plants.to_parquet(path / "eia860_plant.parquet", index=False)


class TestSparseOwnershipJoin(unittest.TestCase):
    """``load_eia860_ownership`` honors the sparse Schedule-4 rule."""

    def test_operator_is_full_owner_when_absent_from_schedule_4(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_eia860_dir(Path(tmp))
            df = load_eia860_ownership(Path(tmp), year=2024)

        plant_100 = df[df["plant_code"] == 100]
        self.assertEqual(len(plant_100), 1)
        self.assertEqual(plant_100.iloc[0]["percent_owned"], 1.0)
        self.assertEqual(plant_100.iloc[0]["owner_utility_id"], 195)

    def test_jointly_owned_generator_uses_schedule_4_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_eia860_dir(Path(tmp))
            df = load_eia860_ownership(Path(tmp), year=2024)

        plant_200 = df[df["plant_code"] == 200]
        self.assertEqual(len(plant_200), 2)
        self.assertAlmostEqual(plant_200["percent_owned"].sum(), 1.0)
        self.assertEqual(
            set(plant_200["owner_utility_id"]), {5416, 19876}
        )

    def test_schedule_4_generator_inherits_schedule_3_capacity(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_eia860_dir(Path(tmp))
            df = load_eia860_ownership(Path(tmp), year=2024)

        plant_200 = df[df["plant_code"] == 200]
        # Nameplate from Schedule 3 flows onto every Schedule 4 owner row.
        self.assertTrue(
            (plant_200["nameplate_capacity_mw"] == 1000.0).all()
        )


class TestMnaOverlay(unittest.TestCase):
    """M&A overlays reassign parents only on or after the effective date."""

    def setUp(self):
        self.ownership = pd.DataFrame(
            {
                "plant_code": [1],
                "generator_id": ["1"],
                "owner_utility_id": pd.array([777], dtype="Int64"),
                "nameplate_capacity_mw": [800.0],
                "percent_owned": [1.0],
            }
        )
        self.lookup = {777: "Calpine"}
        self.overlay = OwnershipChange(
            effective_date="2026-01-07",
            description="Constellation acquires Calpine",
            plant_codes=None,
            from_parent="Calpine",
            to_parent="Constellation Energy",
            source_utility_ids=[],
            status="closed",
        )

    def test_before_effective_date_keeps_old_parent(self):
        result = build_parent_mapping(
            self.ownership,
            as_of_date="2025-12-31",
            parent_lookup=self.lookup,
            mna_overlays=[self.overlay],
        )
        self.assertEqual(result.iloc[0]["parent_company"], "Calpine")

    def test_after_effective_date_applies_new_parent(self):
        result = build_parent_mapping(
            self.ownership,
            as_of_date="2026-02-01",
            parent_lookup=self.lookup,
            mna_overlays=[self.overlay],
        )
        self.assertEqual(
            result.iloc[0]["parent_company"], "Constellation Energy"
        )

    def test_pending_deal_flags_without_reassigning(self):
        pending = OwnershipChange(
            effective_date="2026-03-31",
            description="NRG acquires LS Power portfolio",
            plant_codes=None,
            from_parent="Calpine",
            to_parent="NRG Energy",
            source_utility_ids=[],
            status="pending",
        )
        result = build_parent_mapping(
            self.ownership,
            as_of_date="2026-06-01",
            parent_lookup=self.lookup,
            mna_overlays=[pending],
        )
        self.assertEqual(result.iloc[0]["parent_company"], "Calpine")
        self.assertIn("pending", str(result.iloc[0]["pending_change"]))

    def test_unknown_owner_maps_to_other_unknown(self):
        result = build_parent_mapping(
            self.ownership,
            as_of_date="2026-02-01",
            parent_lookup={},  # no entry for utility 777
            mna_overlays=[],
        )
        self.assertEqual(result.iloc[0]["parent_company"], "Other/Unknown")

    def test_ownership_mw_scales_by_percent_owned(self):
        ownership = self.ownership.copy()
        ownership["percent_owned"] = [0.75]
        result = build_parent_mapping(
            ownership,
            parent_lookup=self.lookup,
            mna_overlays=[],
        )
        self.assertAlmostEqual(result.iloc[0]["ownership_mw"], 600.0)


class TestPercentOwnedValidation(unittest.TestCase):
    """``validate_percent_owned`` flags generators whose shares miss 1.0."""

    def test_consistent_shares_pass(self):
        df = pd.DataFrame(
            {
                "plant_code": [1, 1],
                "generator_id": ["1", "1"],
                "percent_owned": [0.6, 0.4],
            }
        )
        self.assertTrue(validate_percent_owned(df).empty)

    def test_inconsistent_shares_are_flagged(self):
        df = pd.DataFrame(
            {
                "plant_code": [1, 1, 2],
                "generator_id": ["1", "1", "1"],
                "percent_owned": [0.6, 0.3, 1.0],
            }
        )
        bad = validate_percent_owned(df)
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad.iloc[0]["plant_code"], 1)
        self.assertAlmostEqual(bad.iloc[0]["share_total"], 0.9)


class TestSummarizeFleet(unittest.TestCase):
    """``summarize_fleet_by_parent`` rolls capacity up to parents."""

    def test_capacity_aggregates_by_parent(self):
        parent_df = pd.DataFrame(
            {
                "parent_company": ["Duke Energy", "Duke Energy", "Entergy"],
                "ownership_mw": [100.0, 250.0, 400.0],
            }
        )
        summary = summarize_fleet_by_parent(parent_df)
        duke = summary[summary["parent_company"] == "Duke Energy"].iloc[0]
        self.assertAlmostEqual(duke["ownership_mw"], 350.0)
        self.assertEqual(duke["generator_count"], 2)
        # Sorted descending — Entergy (400) outranks Duke (350).
        self.assertEqual(summary.iloc[0]["parent_company"], "Entergy")


class TestAttributeEmissions(unittest.TestCase):
    """``attribute_emissions`` allocates emissions by ``percent_owned``."""

    def test_joint_ownership_splits_emissions_proportionally(self):
        # Plant 1: wholly owned by A. Plant 2: jointly owned 50/50 A/B.
        dispatch = pd.DataFrame(
            {
                "plant_code": [1, 1, 2, 2],
                "generator_id": ["1", "1", "1", "1"],
                "hour": [0, 1, 0, 1],
                "dispatch_mw": [10.0, 10.0, 20.0, 20.0],
                "emission_rate": [0.5, 0.5, 1.0, 1.0],
            }
        )
        parent_df = pd.DataFrame(
            {
                "plant_code": [1, 2, 2],
                "generator_id": ["1", "1", "1"],
                "parent_company": ["Company A", "Company A", "Company B"],
                "percent_owned": [1.0, 0.5, 0.5],
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dispatch.parquet"
            dispatch.to_parquet(path, index=False)
            result = attribute_emissions(path, parent_df, year=2026)

        annual = result[result["granularity"] == "annual"].set_index(
            "parent_company"
        )
        # A: plant 1 = 2×10×0.5 = 10; plant 2 = 2×20×1.0×0.5 = 20 → 30 tCO2.
        self.assertAlmostEqual(annual.loc["Company A", "emissions_tco2"], 30.0)
        # B: plant 2 only = 2×20×1.0×0.5 = 20 tCO2.
        self.assertAlmostEqual(annual.loc["Company B", "emissions_tco2"], 20.0)
        # A generation = 20 (plant 1) + 20 (half of plant 2) = 40 MWh.
        self.assertAlmostEqual(annual.loc["Company A", "generation_mwh"], 40.0)

    def test_intensity_is_emissions_over_generation(self):
        dispatch = pd.DataFrame(
            {
                "plant_code": [1, 1],
                "generator_id": ["1", "1"],
                "hour": [0, 1],
                "dispatch_mw": [100.0, 100.0],
                "emission_rate": [0.4, 0.4],
            }
        )
        parent_df = pd.DataFrame(
            {
                "plant_code": [1],
                "generator_id": ["1"],
                "parent_company": ["Company A"],
                "percent_owned": [1.0],
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dispatch.parquet"
            dispatch.to_parquet(path, index=False)
            result = attribute_emissions(path, parent_df, year=2026)

        annual = result[result["granularity"] == "annual"].iloc[0]
        self.assertAlmostEqual(
            annual["emissions_intensity_tco2_per_mwh"], 0.4
        )
        # Hourly and monthly granularities are also present.
        self.assertEqual(
            set(result["granularity"]), {"hourly", "monthly", "annual"}
        )


if __name__ == "__main__":
    unittest.main()
