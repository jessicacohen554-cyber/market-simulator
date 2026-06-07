"""EIA-923 is the single source of truth for per-plant model class.

These tests pin the durable classification contract introduced to stop the
three independent class-assignment paths (ERCOT curated bins, the non-ERCOT
EIA-860 fleet, and the EIA-923 benchmark) from drifting:

* The canonical :func:`classify_plant` buckets a plant the same way the
  benchmark always did (gas by prime mover + CHP flag; coal by supply rank).
* The ERCOT bin override re-derives each gas bin's class from the EIA-923
  dominant class, so a curated bin can never silently disagree with what the
  plant actually burned — the three historically hand-fixed plants come out
  right with no hardcoding, and every active gas bin matches EIA-923.
"""

import unittest

from market_sim.config.plant_taxonomy import classify_plant
from market_sim.data.fleet import (
    _coal_class_for,
    _GAS_BIN_GROUPS,
    eia923_dominant_class_by_plant,
    load_campd_bins,
)

BINS_CSV = "inputs/custom-bin-assignments.csv"
# The base calibration year the ERCOT fleet is built for; EIA-923 covers it.
YEAR = 2024


class TestClassifyPlant(unittest.TestCase):
    """The canonical classifier reproduces the benchmark's bucketing."""

    def test_gas_by_prime_mover_and_chp(self):
        # Combined-cycle blocks report CA/CS/CT/CC; peakers GT/IC; boilers ST.
        self.assertEqual(classify_plant("NG", "CA", False, 1), "CC_REGULAR")
        self.assertEqual(classify_plant("NG", "CT", False, 1), "CC_REGULAR")
        self.assertEqual(classify_plant("NG", "CA", True, 1), "CC_CHP")
        self.assertEqual(classify_plant("NG", "GT", False, 1), "CT_PEAKER")
        self.assertEqual(classify_plant("NG", "IC", False, 1), "CT_PEAKER")
        self.assertEqual(classify_plant("NG", "GT", True, 1), "CT_CHP")
        self.assertEqual(classify_plant("NG", "ST", False, 1), "ST_GAS")
        self.assertEqual(classify_plant("NG", "ST", True, 1), "ST_CHP")

    def test_non_gas_classes(self):
        self.assertEqual(classify_plant("WND", "WT", False, 1), "wind")
        self.assertEqual(classify_plant("SUN", "PV", False, 1), "solar")
        self.assertEqual(classify_plant("NUC", "ST", False, 1), "nuclear")
        self.assertEqual(classify_plant("OG", "GT", False, 1), "OTHER")

    def test_coal_resolves_to_supply_rank(self):
        # Coal codes route through the supply-rank resolver, never bare gas.
        self.assertEqual(
            classify_plant("BIT", "ST", False, 999, _coal_class_for), "COAL_BIT"
        )
        # No resolver: straight from the fuel code.
        self.assertEqual(classify_plant("LIG", "ST", False, 999), "COAL_LIGNITE")
        self.assertEqual(classify_plant("SUB", "ST", False, 999), "COAL_PRB")


class TestEia923Override(unittest.TestCase):
    """Every active ERCOT gas bin carries its EIA-923 dominant class."""

    @classmethod
    def setUpClass(cls):
        cls.dominant = eia923_dominant_class_by_plant(YEAR)
        cls.bins = load_campd_bins(BINS_CSV, year=YEAR)

    def test_eia923_present_for_year(self):
        # Guards the whole contract: without 923 data the override no-ops.
        self.assertTrue(self.dominant, "EIA-923 dominant-class map is empty")

    def test_every_gas_bin_matches_eia923_dominant(self):
        """No gas bin disagrees with the plant's EIA-923 dominant class.

        This is the drift tripwire: if a curated bin (or the override) ever
        diverges from what EIA-923 says the plant predominantly generated, this
        fails. Coal bins keep their curated supply class and are exempt; gas
        plants EIA-923 doesn't cover keep their curated class.
        """
        mismatches = []
        for code, group in zip(self.bins["Plant_Code"], self.bins["Plant_Group"]):
            if group not in _GAS_BIN_GROUPS:
                continue
            derived = self.dominant.get(int(code))
            if derived in _GAS_BIN_GROUPS and derived != group:
                mismatches.append((int(code), group, derived))
        self.assertEqual(mismatches, [], f"gas bins disagree with EIA-923: {mismatches}")

    def test_known_drifted_plants_resolve_automatically(self):
        """The three historically hand-fixed plants come out right unhardcoded.

        Lost Pines (merchant CC, not CHP), San Jacinto (gas peaker, not CHP)
        and Union Carbide Seadrift (a GT-dominant cogen, not a steam cogen) are
        each derived purely from EIA-923 — no plant-code special-casing.
        """
        expected = {
            55154: "CC_REGULAR",  # Lost Pines 1 Power Project
            7325: "CT_PEAKER",    # San Jacinto Steam Electric Station
            50150: "CT_CHP",      # Union Carbide Seadrift Cogen
        }
        by_code = dict(zip(
            self.bins["Plant_Code"].astype(int), self.bins["Plant_Group"]
        ))
        for code, want in expected.items():
            self.assertEqual(by_code.get(code), want, f"plant {code}")
            # And it falls straight out of the EIA-923 dominant class.
            self.assertEqual(self.dominant.get(code), want, f"923 dominant {code}")

    def test_override_only_moves_among_gas_classes(self):
        """Override never reclasses a coal bin or invents a non-bin group."""
        curated = load_campd_bins(BINS_CSV)  # no year -> no override
        cur = dict(zip(curated["Plant_Code"].astype(int), curated["Plant_Group"]))
        for code, group in zip(
            self.bins["Plant_Code"].astype(int), self.bins["Plant_Group"]
        ):
            if group != cur[code]:
                # A change only ever swaps one gas class for another.
                self.assertIn(cur[code], _GAS_BIN_GROUPS)
                self.assertIn(group, _GAS_BIN_GROUPS)


if __name__ == "__main__":
    unittest.main()
