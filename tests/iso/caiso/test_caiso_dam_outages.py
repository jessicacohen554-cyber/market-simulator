"""Tests for the CAISO DAM-outage availability overlay (caiso-104 stage 3).

Covers the resource->plant crosswalk scoring/loading and the availability-derate
math that overrides the CAMPD fallback for covered CAISO thermal plants. Uses
small synthetic frames per the repo's trivial-case-first convention.
"""

import importlib
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
import market_sim.data.caiso_outages as co


class CrosswalkScoreTest(unittest.TestCase):
    """Name-token matcher used to propose the crosswalk."""

    def setUp(self):
        self.builder = importlib.import_module(
            "scripts.data.build_caiso_resource_crosswalk"
        )

    def test_exact_common_name_scores_high(self):
        self.assertGreaterEqual(
            self.builder._score(
                "Moss Landing Power Plant", "Dynegy Moss Landing Power Plant Hybrid"
            ),
            0.6,
        )

    def test_unrelated_names_score_low(self):
        self.assertLess(self.builder._score("Adera Solar", "Ormond Beach"), 0.3)

    def test_nonthermal_names_are_flagged(self):
        # Solar/storage co-located at a thermal site must never crosswalk on.
        self.assertTrue(self.builder._is_nonthermal("Pastoria Solar"))
        self.assertTrue(self.builder._is_nonthermal("Gateway Energy Storage"))
        self.assertFalse(self.builder._is_nonthermal("La Paloma Generating Plant"))


class StorageCrosswalkTest(unittest.TestCase):
    """The battery half of the crosswalk (R-CAISO-35, sibling file, no consumer)."""

    def setUp(self):
        self.builder = importlib.import_module(
            "scripts.data.build_caiso_resource_crosswalk"
        )

    def test_battery_selector(self):
        self.assertTrue(
            self.builder.is_battery_resource("CONDOR_2_CDRBT1", "Condor BESS")
        )
        self.assertTrue(self.builder.is_battery_resource("KRAMER_1_BX3", "Resurgence"))
        self.assertTrue(self.builder.is_battery_resource("X_1_A", "Daggett Solar BESS"))
        self.assertFalse(
            self.builder.is_battery_resource("X_1_SOLAR1", "Shafter Solar")
        )

    def test_battery_selector_reads_code_after_plant_prefix(self):
        # R-CAISO-36: the storage code follows a plant code in the final id
        # segment, and the id wins over a solar project name.
        b = self.builder.is_battery_resource
        self.assertTrue(b("ROMOLA_5_MPBBT1", "Menifee Power Bank"))
        self.assertTrue(b("RATSKE_2_WAVBT1", "Willy 9 Antelope Valley Complex"))
        self.assertTrue(b("MCFLND_5_MBSBX2", "McFarland Solar B Hybrid"))
        self.assertTrue(b("ALAMIT_7_ES1", "Alamitos Energy Storage"))
        self.assertFalse(b("LAKHDG_6_UNIT 1", "Lake Hodges Pumped Storage-Unit1"))
        self.assertFalse(b("ALAMIT_7_UNIT 3", "Alamitos 3"))

    def test_battery_resources_keep_storage_name(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "w.parquet"
            pd.DataFrame(
                {
                    "resource_id": ["R_2_WAVBT1", "R_2_WAVBT1", "G_1_UNIT 1"],
                    "resource_name": ["Willy 9 Complex", "AV BESS, LLC", "Gas 1"],
                    "resource_pmax_mw": [126.0, 125.96, 50.0],
                }
            ).to_parquet(path)
            res = self.builder.load_battery_resources(path)
        self.assertEqual(list(res["resource_id"]), ["R_2_WAVBT1"])
        self.assertEqual(res["resource_name"].iloc[0], "AV BESS, LLC")
        self.assertEqual(res["resource_pmax_mw"].iloc[0], 126.0)

    def test_review_ledger_overrides_proposal(self):
        proposed = pd.DataFrame(
            {
                "resource_id": ["A_1_ABT1", "B_1_BBT1"],
                "resource_name": ["Alpha BESS", "Beta BESS"],
                "resource_pmax_mw": [50.0, 20.0],
                "plant_code": pd.array([1, 2], dtype="Int64"),
                "plant_group": ["BATTERY", "BATTERY"],
                "plant_name": ["Wrong Plant", "Beta"],
                "plant_pmax_mw": [10.0, 20.0],
                "match_score": [0.4, 1.0],
                "match_method": ["name_token", "name_token"],
                "accepted": [0, 1],
            }
        )
        targets = pd.DataFrame(
            {
                "plant_code": [1, 2, 3],
                "plant_name": ["Wrong Plant", "Beta", "Alpha Storage"],
                "plant_pmax_mw": [10.0, 20.0, 50.0],
                "plant_group": ["BATTERY"] * 3,
                "eia_status": ["OP", "OP", "OA"],
            }
        )
        orig = self.builder.load_storage_targets
        self.builder.load_storage_targets = lambda statuses=("OP",): targets
        try:
            with TemporaryDirectory() as d:
                rev = Path(d) / "review.csv"
                pd.DataFrame(
                    {
                        "resource_id": ["A_1_ABT1", "B_1_BBT1"],
                        "plant_code": [3, None],
                        "accepted": [1, 0],
                        "review_note": ["exact MW", "no EIA plant"],
                    }
                ).to_csv(rev, index=False)
                out = self.builder.apply_storage_review(proposed, rev)
                # A review row outside the census is refused.
                pd.DataFrame(
                    {
                        "resource_id": ["Z_1_ZBT1"],
                        "plant_code": [3],
                        "accepted": [1],
                        "review_note": ["x"],
                    }
                ).to_csv(rev, index=False)
                with self.assertRaises(ValueError):
                    self.builder.apply_storage_review(proposed, rev)
        finally:
            self.builder.load_storage_targets = orig
        a = out.set_index("resource_id")
        self.assertEqual(int(a.loc["A_1_ABT1", "plant_code"]), 3)
        self.assertEqual(a.loc["A_1_ABT1", "accepted"], 1)
        self.assertEqual(a.loc["A_1_ABT1", "match_method"], "reviewed")
        self.assertTrue(pd.isna(a.loc["B_1_BBT1", "plant_code"]))
        self.assertEqual(a.loc["B_1_BBT1", "accepted"], 0)
        self.assertEqual(a.loc["B_1_BBT1", "review_note"], "no EIA plant")

    def test_storage_score_ignores_technology_tokens(self):
        # "Energy Storage" alone must not make two different plants match.
        self.assertLess(
            self.builder._score_storage("Gateway Energy Storage", "Cascade Storage"),
            0.3,
        )
        self.assertGreaterEqual(
            self.builder._score_storage("Coso Battery Storage", "Coso Battery Storage"),
            0.99,
        )

    def test_storage_output_is_a_separate_file(self):
        self.assertNotEqual(self.builder.STORAGE_OUT_CSV, self.builder.OUT_CSV)
        self.assertEqual(co.CROSSWALK_CSV.name, self.builder.OUT_CSV.name)


class DerateFactorsTest(unittest.TestCase):
    """The measured DAM curtailment -> per-plant availability multiplier."""

    def setUp(self):
        co.caiso_dam_outage_derate_factors.cache_clear()
        co.load_crosswalk.cache_clear()
        self._tmp = TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self._orig_windows = co.DAM_OUTAGE_WINDOWS_PARQUET
        self._orig_xwalk = co.CROSSWALK_CSV
        self._orig_cap = co._iso_plant_capacity
        # One plant (260 CC_REGULAR, 200 MW model capacity); two resources map
        # to it, together curtailing 150 MW over hours 0-9.
        windows = pd.DataFrame(
            {
                "resource_id": ["R_A", "R_B"],
                "start": pd.to_datetime(["2023-01-01 00:00:00", "2023-01-01 00:00:00"]),
                "end": pd.to_datetime(["2023-01-01 10:00:00", "2023-01-01 10:00:00"]),
                "curtailment_mw": [100.0, 50.0],
            }
        )
        wpath = tmp / "caiso-dam-outage-windows.parquet"
        windows.to_parquet(wpath, index=False)
        xwalk = pd.DataFrame(
            {
                "resource_id": ["R_A", "R_B", "R_C"],
                "plant_code": [260, 260, 999],
                "plant_group": ["CC_REGULAR", "CC_REGULAR", "CC_REGULAR"],
                "accepted": [1, 1, 0],  # R_C unaccepted -> ignored
            }
        )
        xpath = tmp / "xwalk.csv"
        xwalk.to_csv(xpath, index=False)
        co.DAM_OUTAGE_WINDOWS_PARQUET = wpath
        co.CROSSWALK_CSV = xpath
        co._iso_plant_capacity = lambda iso: {(260, "CC_REGULAR"): 200.0}

    def tearDown(self):
        co.DAM_OUTAGE_WINDOWS_PARQUET = self._orig_windows
        co.CROSSWALK_CSV = self._orig_xwalk
        co._iso_plant_capacity = self._orig_cap
        co.caiso_dam_outage_derate_factors.cache_clear()
        co.load_crosswalk.cache_clear()
        self._tmp.cleanup()

    def test_concurrent_curtailment_sums_and_derates(self):
        fac = co.caiso_dam_outage_derate_factors(2023, HOURS_PER_YEAR, "CAISO")
        self.assertIn((260, "CC_REGULAR"), fac)
        arr = fac[(260, "CC_REGULAR")]
        self.assertEqual(arr.shape, (HOURS_PER_YEAR,))
        # Hours 0-9 curtailed by 150/200 -> availability 0.25; rest full.
        np.testing.assert_allclose(arr[0:10], 0.25)
        np.testing.assert_allclose(arr[10:24], 1.0)

    def test_unaccepted_and_other_iso_ignored(self):
        self.assertEqual(
            co.caiso_dam_outage_derate_factors(2023, HOURS_PER_YEAR, "ERCOT"), {}
        )
        fac = co.caiso_dam_outage_derate_factors(2023, HOURS_PER_YEAR, "CAISO")
        self.assertEqual(list(fac.keys()), [(260, "CC_REGULAR")])

    def test_coverage_gate(self):
        self.assertFalse(co.has_dam_coverage(2020))
        self.assertTrue(co.has_dam_coverage(2023))


if __name__ == "__main__":
    unittest.main()
