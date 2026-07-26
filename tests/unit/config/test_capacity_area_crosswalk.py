"""Tests for the capacity-area → model-zone crosswalk.

Covers the trivial 1-area→1-zone mapping, the nesting/aggregation rules that
prevent double-counting (PJM MAAC ⊇ EMAAC+SWMAAC, MISO LRZ→region, NYISO G-J,
ISO-NE SENE), and the completeness invariant: every capacity AREA that appears
in the real clean data must either map to a genuine ``iso_configs`` zone or be
explicitly classified as ``system``/``unmapped``. The completeness check
regenerates the clean tree into a tmp CLEAN_DIR from the committed raw CSVs, so
it exercises the true area labels without touching the real derived tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from market_sim.config.capacity_area_crosswalk import (
    AreaMapping,
    aggregate_by_zone,
    map_area,
)
from market_sim.config.iso_configs import get_iso_config
from scripts.data import curate_capacity_deliverability as curate_cd
from scripts.lib import clean_io
from scripts.lib.clean_io import read_clean

# Model ISO name for each clean-partition ISO label (NEISO ≙ ISONE).
_MODEL_ISO = {
    "PJM": "PJM",
    "MISO": "MISO",
    "NYISO": "NYISO",
    "ISONE": "NEISO",
    "CAISO": "CAISO",
}
_VALID_KINDS = {
    "leaf",
    "component",
    "seam",
    "nested",
    "aggregate",
    "system",
    "unmapped",
}


class TestCrosswalkUnit(unittest.TestCase):
    def test_trivial_leaf_maps_one_to_one(self) -> None:
        m = map_area("PJM", "COMED")
        self.assertEqual(m.zones, ("PJM_ComEd",))
        self.assertTrue(m.contributes)

    def test_pjm_maac_is_aggregate_excluded(self) -> None:
        m = map_area("PJM", "MAAC")
        self.assertEqual(m.kind, "aggregate")
        self.assertFalse(m.contributes)
        self.assertGreater(len(m.zones), 1)

    def test_pjm_nested_subldas_excluded(self) -> None:
        for area in ("PSEG", "JCPL", "BGE", "ATSI-Cleveland"):
            self.assertFalse(map_area("PJM", area).contributes, area)

    def test_no_double_count_pjm_emaac(self) -> None:
        # EMAAC (leaf) + its nested children + MAAC (aggregate): only EMAAC
        # contributes to PJM_EMAAC, so the rollup equals the EMAAC value alone.
        values = {"EMAAC": 2740.0, "PSEG": 2000.0, "JCPL": 1000.0, "MAAC": 9999.0}
        by_zone, skipped = aggregate_by_zone("PJM", values)
        self.assertEqual(by_zone["PJM_EMAAC"], 2740.0)
        self.assertEqual({m.area for m in skipped}, {"PSEG", "JCPL", "MAAC"})

    def test_miso_lrz_sums_into_region(self) -> None:
        # LRZ 8/9/10 → MISO-South; the "South" subregion superset is excluded.
        values = {"LRZ 8": 100.0, "LRZ 9": 200.0, "LRZ 10": 50.0, "South": 999.0}
        by_zone, _ = aggregate_by_zone("MISO", values)
        self.assertEqual(by_zone["MISO-South"], 350.0)
        self.assertNotIn("South", by_zone)

    def test_caiso_branch_group_is_seam_to_import_node(self) -> None:
        m = map_area("CAISO", "Palo Verde", "branch_group")
        self.assertEqual(m.kind, "seam")
        self.assertEqual(m.zones, ("WECC_import",))
        self.assertTrue(m.contributes)

    def test_caiso_unresolved_local_area_is_unmapped(self) -> None:
        for area in ("Stockton", "Kern"):
            self.assertEqual(map_area("CAISO", area, "local_area").kind, "unmapped")

    def test_neiso_alias_and_nesting(self) -> None:
        self.assertEqual(map_area("NEISO", "NNE").zones, ("North",))
        self.assertFalse(map_area("NEISO", "Maine").contributes)  # ⊂ NNE

    def test_unknown_area_is_unmapped_not_error(self) -> None:
        m = map_area("PJM", "TOTALLY_MADE_UP_LDA")
        self.assertEqual(m.kind, "unmapped")
        self.assertEqual(m.zones, ())


class TestCrosswalkCompleteness(unittest.TestCase):
    """Every real clean area maps to a real zone or is logged unmapped."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = Path(self._tmp.name) / "clean"
        # Regenerate the clean tree from the committed raw CSVs into the tmp dir.
        curate_cd.curate()

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_every_area_maps_or_is_logged_unmapped(self) -> None:
        for clean_iso, model_iso in _MODEL_ISO.items():
            try:
                df = read_clean("capacity-deliverability", iso=clean_iso)
            except FileNotFoundError:
                continue  # ISO intake not landed
            zone_names = set(get_iso_config(model_iso).zone_names)
            pairs = set(zip(df["area"].astype(str), df["area_type"].astype(str)))
            for area, area_type in pairs:
                m = map_area(model_iso, area, area_type)
                self.assertIsInstance(m, AreaMapping)
                self.assertIn(m.kind, _VALID_KINDS, f"{clean_iso}:{area}")
                # A contributing area maps to exactly one REAL model zone.
                if m.contributes:
                    self.assertEqual(len(m.zones), 1, f"{clean_iso}:{area}")
                    self.assertIn(m.zones[0], zone_names, f"{clean_iso}:{area}")
                else:
                    # Non-contributing: every named zone must still be real.
                    for z in m.zones:
                        self.assertIn(z, zone_names, f"{clean_iso}:{area}->{z}")


if __name__ == "__main__":
    unittest.main()
