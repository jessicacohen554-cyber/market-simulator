"""Tests for scripts/audit_keepers.py's non-ablation surface.

test_audit_keepers_ablation.py already covers the E9/ablation-twin gate; this
file targets the keeper-text integrity checks. (The H1 holdout-quarantine
sweep is GONE: ``[R-HOLDOUT]`` was removed 2026-09-09.) ``audit_keepers`` is
loaded fresh so the tests never touch the real committed registry.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from tests.helpers import REPO_ROOT

_REPO = REPO_ROOT
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


class MarkerCurrencyTests(unittest.TestCase):
    """M1: marker_currency_failures (owner decision D-5(b), signed 2026-08-02).

    The `complete`-block marker must name the ISO's CURRENT designated keeper
    (M1a) and its recorded determination must still re-verify against that run
    (M1b), so a promotion can never transfer a determination onto a run it was
    never scored against. Both halves are stubbed here (keeper shard + live
    verdict) so the test never touches the committed registry or solves.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.marker = Path(self._tmp.name) / "calibration-complete.json"
        ak.MARKER_FILE = self.marker
        self._real_keeper_ids = ak.keeper_store.keeper_ids
        self._real_determine = ak.cv.determine

    def tearDown(self):
        ak.MARKER_FILE = _REAL_MARKER_FILE
        ak.keeper_store.keeper_ids = self._real_keeper_ids
        ak.cv.determine = self._real_determine
        self._tmp.cleanup()

    def _stub(self, keepers, determinations):
        ak.keeper_store.keeper_ids = lambda: keepers
        ak.cv.determine = lambda rid: {"determination": determinations[rid]}

    def _write_marker(self, complete):
        self.marker.write_text(json.dumps({"complete": complete}))

    def test_current_marker_with_matching_determination_passes(self):
        self._stub({"PJM": "run-b"}, {"run-b": "CALIBRATED"})
        self._write_marker(
            {"PJM": {"keeper": "run-b", "determination": "CALIBRATED on run-b."}}
        )
        self.assertEqual(ak.marker_currency_failures(), [])

    def test_stale_marker_keeper_flags_m1a(self):
        self._stub({"PJM": "run-b"}, {"run-b": "CALIBRATED"})
        self._write_marker(
            {"PJM": {"keeper": "run-a", "determination": "CALIBRATED on run-a."}}
        )
        fails = ak.marker_currency_failures()
        self.assertEqual([f[1] for f in fails], ["M1a"])
        self.assertIn("run-b", fails[0][2])

    def test_determination_that_no_longer_holds_flags_m1b(self):
        # The dangerous case the owner's "re-verify, don't just re-key" clause
        # targets: the field was updated but the determination was not re-scored.
        self._stub({"PJM": "run-b"}, {"run-b": "NOT-YET"})
        self._write_marker(
            {"PJM": {"keeper": "run-b", "determination": "CALIBRATED on run-b."}}
        )
        fails = ak.marker_currency_failures()
        self.assertEqual([f[1] for f in fails], ["M1b"])
        self.assertIn("NOT-YET", fails[0][2])

    def test_iso_without_a_complete_entry_is_not_checked(self):
        # An ISO with no `complete` marker (e.g. ERCOT) has nothing to re-key.
        self._stub({"ERCOT": "run-x"}, {"run-x": "NOT-YET"})
        self._write_marker({})
        self.assertEqual(ak.marker_currency_failures(), [])

    def test_scoping_to_isos_isolates_lanes(self):
        self._stub(
            {"PJM": "run-b", "NEISO": "run-d"},
            {"run-b": "CALIBRATED", "run-d": "CALIBRATED"},
        )
        self._write_marker(
            {
                "PJM": {"keeper": "run-a", "determination": "CALIBRATED on run-a."},
                "NEISO": {"keeper": "run-c", "determination": "CALIBRATED on run-c."},
            }
        )
        self.assertEqual(len(ak.marker_currency_failures()), 2)
        self.assertEqual([f[0] for f in ak.marker_currency_failures(["PJM"])], ["PJM"])

    def test_underscore_keys_are_metadata_not_isos(self):
        # The `final` block carries a "_note" key; the same shape must never be
        # read as an ISO in `complete`.
        self._stub({"PJM": "run-b"}, {"run-b": "CALIBRATED"})
        self._write_marker(
            {
                "_note": "block documentation",
                "PJM": {"keeper": "run-b", "determination": "CALIBRATED on run-b."},
            }
        )
        self.assertEqual(ak.marker_currency_failures(), [])


class AssertedDeterminationTests(unittest.TestCase):
    """The token a marker/sidecar ASSERTS is the one its prose LEADS with.

    Pins the 2026-08-17 positional fix. The scan used to run token-list-first
    (longest token first, anywhere in the text), so a determination named in a
    marker's deliberately preserved genealogy outranked the entry's own leading
    claim -- an accurate marker could not be written without deleting history.
    Rubric v3.3 made that live: NYISO's and NEISO's markers now lead with
    CALIBRATED over prior text recording the superseded with-caveats reading.
    """

    def test_leading_token_wins_over_preserved_prior_text(self):
        text = (
            "CALIBRATED on run-b, re-verified under rubric v3.3. "
            "|| PRIOR TEXT, preserved: CALIBRATED-WITH-CAVEATS on run-a."
        )
        self.assertEqual(ak._asserted_determination(text), "CALIBRATED")

    def test_longest_token_still_wins_at_the_same_position(self):
        # The earliest position matches both "CALIBRATED" (a prefix) and the
        # full token; positional scanning must not regress into reading the
        # prefix. This is the case the old longest-first ordering existed for.
        text = "CALIBRATED-WITH-CAVEATS on run-b. Prior: CALIBRATED on run-a."
        self.assertEqual(ak._asserted_determination(text), "CALIBRATED-WITH-CAVEATS")

    def test_not_yet_leading_is_read_as_not_yet(self):
        text = "NOT-YET on run-b (C3a fails). Prior text: CALIBRATED on run-a."
        self.assertEqual(ak._asserted_determination(text), "NOT-YET")

    def test_naming_another_runs_recipe_is_not_an_assertion(self):
        # The conservative tail filter is unchanged: a token immediately
        # followed by recipe/keeper/run/step names something else, and the scan
        # falls through to the next surviving match.
        text = "Re-solved the CALIBRATED-WITH-CAVEATS recipe; determination NOT-YET."
        self.assertEqual(ak._asserted_determination(text), "NOT-YET")

    def test_no_token_returns_none(self):
        self.assertIsNone(ak._asserted_determination("no determination named here"))


if __name__ == "__main__":
    unittest.main()
