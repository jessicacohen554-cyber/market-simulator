"""Parity tests: clean-backed reference crosswalks match the raw lookups.

The model reads its reference / crosswalk tables through one of two backends,
selected by the ``MARKET_SIM_USE_CLEAN`` environment variable (default OFF):

* OFF — the raw CSVs under ``data/raw/reference`` (the long-standing path), and
* ON  — the curated clean parquet under ``data/clean/reference`` via the frozen
  ``scripts.lib.clean_io.read_clean`` seam.

Because each clean table is curated *from* the same raw CSV, both backends must
resolve to the identical lookup. These tests assert that parity for a sample of
keys on the two crosswalks consumed by the model:

* ``zone_assignment.load_reference_zone_crosswalk`` — ERCOT plant -> model zone
  (from ``bin-assignments``), and
* ``hydro.load_reference_hydro_nameplate`` — hydro plant -> nameplate MW
  (from ``plant-registry``).

Marked slow / integration: they touch the real on-disk data and (re)generate
the clean slice. The whole module is skipped when the raw reference inputs are
absent (e.g. a checkout without ``data/raw``).
"""

from __future__ import annotations

import os
import unittest

import pytest

from market_sim.config import paths

pytestmark = [pytest.mark.slow, pytest.mark.integration]

# The raw sources backing the two crosswalks under test.
_RAW_BINS = paths.CAMPD_BINS_CSV
_RAW_REGISTRY = paths.PLANT_REGISTRY_CSV

_RAW_PRESENT = _RAW_BINS.is_file() and _RAW_REGISTRY.is_file()


@unittest.skipUnless(_RAW_PRESENT, "raw reference inputs absent")
class TestConsumeReferenceParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The clean tree is gitignored / disposable; regenerate the reference
        # slice from raw if a partition is missing, so the clean backend has
        # something to read.
        from scripts.lib import clean_io

        if not (
            clean_io.clean_exists("reference", market="bin-assignments")
            and clean_io.clean_exists("reference", market="plant-registry")
        ):
            from scripts.data import curate_reference

            curate_reference.curate()

    def setUp(self):
        self._saved = os.environ.get("MARKET_SIM_USE_CLEAN")

    def tearDown(self):
        if self._saved is None:
            os.environ.pop("MARKET_SIM_USE_CLEAN", None)
        else:
            os.environ["MARKET_SIM_USE_CLEAN"] = self._saved

    def _raw(self, fn):
        """Run ``fn`` with the clean backend OFF (raw CSV path)."""
        os.environ.pop("MARKET_SIM_USE_CLEAN", None)
        return fn()

    def _clean(self, fn):
        """Run ``fn`` with the clean backend ON (clean parquet path)."""
        os.environ["MARKET_SIM_USE_CLEAN"] = "1"
        try:
            return fn()
        finally:
            os.environ.pop("MARKET_SIM_USE_CLEAN", None)

    def _assert_parity(self, raw, clean, *, almost=False):
        self.assertTrue(raw, "raw crosswalk is unexpectedly empty")
        self.assertTrue(clean, "clean crosswalk is unexpectedly empty")
        # Same key set across the two backends.
        self.assertEqual(set(raw), set(clean))
        # And the values agree for a deterministic sample of shared keys.
        sample = sorted(set(raw) & set(clean))[:25]
        self.assertTrue(sample, "no shared keys to sample")
        for key in sample:
            if almost:
                self.assertAlmostEqual(
                    raw[key], clean[key], places=6, msg=f"value mismatch for {key}"
                )
            else:
                self.assertEqual(raw[key], clean[key], f"value mismatch for {key}")

    def test_zone_crosswalk_parity(self):
        from market_sim.data.zone_assignment import load_reference_zone_crosswalk

        raw = self._raw(lambda: load_reference_zone_crosswalk("ERCOT"))
        clean = self._clean(lambda: load_reference_zone_crosswalk("ERCOT"))
        self._assert_parity(raw, clean)

    def test_hydro_nameplate_parity(self):
        from market_sim.data.hydro import load_reference_hydro_nameplate

        raw = self._raw(lambda: load_reference_hydro_nameplate("ERCOT"))
        clean = self._clean(lambda: load_reference_hydro_nameplate("ERCOT"))
        self._assert_parity(raw, clean, almost=True)


if __name__ == "__main__":
    unittest.main()
