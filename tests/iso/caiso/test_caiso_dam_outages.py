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
