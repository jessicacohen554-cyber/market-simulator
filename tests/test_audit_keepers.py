"""Tests for scripts/audit_keepers.py's non-ablation surface.

test_audit_keepers_ablation.py already covers the E9/ablation-twin gate; this
file targets H1 (the D-6 holdout-quarantine sweep,
``holdout_quarantine_failures``) and the D-6/legitimacy_diagnostics parity
that H1 depends on. Both ``audit_keepers`` and (indirectly, for the parity
check) ``scripts.legitimacy_diagnostics`` are loaded fresh so the tests never
touch the real committed registry.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "audit_keepers_h1", str(_REPO / "scripts" / "audit_keepers.py")
)
ak = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ak)

# Snapshot the real (never-mutated-by-tests) module globals once, before any
# test method below monkeypatches them, so the parity test always compares
# against the actual production configuration regardless of test order.
_REAL_REGISTRY_DIR = ak.cv.REGISTRY_DIR
_REAL_MARKER_FILE = ak.MARKER_FILE


class HoldoutQuarantineTests(unittest.TestCase):
    """H1: holdout_quarantine_failures (CLAUDE.md rule 22 / audit D-6)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.reg = root / "registry"
        self.reg.mkdir()
        self.marker = root / "calibration-complete.json"
        ak.cv.REGISTRY_DIR = self.reg
        ak.MARKER_FILE = self.marker

    def tearDown(self):
        ak.cv.REGISTRY_DIR = _REAL_REGISTRY_DIR
        ak.MARKER_FILE = _REAL_MARKER_FILE
        self._tmp.cleanup()

    def _write_sidecar(self, run_id, iso, years):
        (self.reg / f"{run_id}.json").write_text(
            json.dumps({"iso": iso, "years": years})
        )

    def _write_marker(self, complete):
        self.marker.write_text(json.dumps({"complete": complete}))

    def test_in_window_years_never_flag(self):
        self._write_sidecar("r1", "CAISO", [2023, 2024, 2025])
        self.assertEqual(ak.holdout_quarantine_failures(), [])

    def test_out_of_window_year_flags_without_marker(self):
        self._write_sidecar("r1", "CAISO", [2022, 2023])
        fails = ak.holdout_quarantine_failures()
        self.assertEqual(len(fails), 1)
        self.assertIn("2022", fails[0])
        self.assertIn("CAISO", fails[0])
        self.assertIn("r1", fails[0])

    def test_missing_marker_file_defaults_to_no_authorization(self):
        # No calibration-complete.json at all (not even an empty one) must
        # default to "not authorized" -- never silently pass an unmarked ISO.
        self._write_sidecar("r1", "NYISO", [2026])
        fails = ak.holdout_quarantine_failures()
        self.assertEqual(len(fails), 1)

    def test_marker_authorizes_the_holdout_year(self):
        self._write_sidecar("r1", "CAISO", [2022])
        self._write_marker({"CAISO": {"declared": "2026-08-01"}})
        self.assertEqual(ak.holdout_quarantine_failures(), [])

    def test_marker_is_scoped_per_iso(self):
        # A marker for CAISO must not silently authorize a DIFFERENT unmarked
        # ISO's holdout-year breach (a completeness/gating bug of the same
        # shape as the fuelmix/sysvol map: one flag must not blanket-cover
        # every ISO).
        self._write_sidecar("r1", "CAISO", [2022])
        self._write_sidecar("r2", "PJM", [2026])
        self._write_marker({"CAISO": {"declared": "2026-08-01"}})
        fails = ak.holdout_quarantine_failures()
        self.assertEqual(len(fails), 1)
        self.assertIn("PJM", fails[0])
        self.assertIn("r2", fails[0])

    def test_probes_are_swept_not_just_keepers(self):
        # H1 sweeps EVERY registry sidecar (keeper or probe) -- a probe run
        # that never made it into keepers.json still quarantines.
        self._write_sidecar("probe-2026-diagnostic", "MISO", [2026])
        fails = ak.holdout_quarantine_failures()
        self.assertTrue(any("probe-2026-diagnostic" in f for f in fails))

    def test_in_window_year_alongside_breach_only_flags_the_breach(self):
        # In-window years (2023-2025) sitting next to a holdout year must not
        # themselves get reported as part of the breach -- only [2026] does.
        self._write_sidecar("r1", "ERCOT", [2023, 2024, 2025, 2026])
        fails = ak.holdout_quarantine_failures()
        self.assertEqual(len(fails), 1)
        self.assertIn("solve year(s) [2026]", fails[0])

    def test_no_registered_bundles_is_clean(self):
        self.assertEqual(ak.holdout_quarantine_failures(), [])


class D6ParityTests(unittest.TestCase):
    """audit_keepers' stdlib-inline H1 constants must match
    scripts.legitimacy_diagnostics' D-6 gate exactly -- H1 and
    ``legitimacy_diagnostics --keepers`` are two independent implementations
    of the SAME quarantine and must never silently diverge."""

    def test_calibration_years_match(self):
        from scripts import legitimacy_diagnostics as ld

        self.assertEqual(ak.CALIBRATION_YEARS, ld.D6_CALIBRATION_YEARS)

    def test_marker_path_matches(self):
        from scripts import legitimacy_diagnostics as ld

        self.assertEqual(_REAL_MARKER_FILE, (_REPO / ld.D6_MARKER_FILE).resolve())

    def test_years_are_actually_2023_2024_2025(self):
        # Pins the literal window (not just cross-module equality) so a typo
        # introduced identically in both modules would still be caught.
        self.assertEqual(ak.CALIBRATION_YEARS, frozenset({2023, 2024, 2025}))


if __name__ == "__main__":
    unittest.main()
