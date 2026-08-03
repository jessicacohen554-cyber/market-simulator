"""Tests for the FR-27 forecast DOF-ledger STUB.

The load-bearing property is negative: emitting the skeleton must NEVER improve
a verdict. A config walk that attests nothing is not attestation, so FC-7 has to
score an all-``unattested`` ledger exactly as it scores an absent one. If that
ever stops holding, the stub has become the artifact rule 21 exists to prevent —
a ledger that looks attested and is not.
"""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import forecast_verdict as fv  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "build_forecast_dof_ledger_under_test",
    str(REPO_ROOT / "scripts" / "build_forecast_dof_ledger.py"),
)
bl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bl)


class SkeletonNeverImprovesAVerdictTests(unittest.TestCase):
    """The stub's whole contract, pinned.

    NOTE on the fixture values below: the ledger deliberately EXCLUDES fields
    sitting at their shipped default ("an un-armed mechanism flag is not a free
    parameter OF THIS RUN"), so every fixture here has to supply a genuinely
    NON-default value or it produces no entries at all. These fixtures used
    ``entry_rate_limits: True`` / ``entry_commissioning_lag: True`` until owner
    decision D-2 armed both by default on 2026-08-02 (FFR-3A), which inverted
    which value is the non-default one — hence ``False`` now. The assertions
    are unchanged: nothing here depends on WHICH value is armed, only that the
    value differs from the shipped default.
    """

    def _skeleton(self, sc):
        return bl.build_ledger({"scenario_config": sc})

    def test_all_unattested_scores_exactly_as_an_absent_ledger(self):
        led = self._skeleton({"iso": "PJM", "entry_rate_limits": False})
        self.assertTrue(led["entries"], "skeleton produced no entries to test")
        for tier in ("t1", "t2", "t3"):
            with self.subTest(tier=tier):
                absent = fv._score_dof_ledger({}, tier)
                skeleton = fv._score_dof_ledger({"dof_ledger": led}, tier)
                self.assertEqual(skeleton["status"], absent["status"])

    def test_the_caveat_detail_names_what_must_be_attested(self):
        # The gain over an absent ledger is specificity, not status.
        led = self._skeleton({"iso": "PJM", "entry_rate_limits": False})
        row = fv._score_dof_ledger({"dof_ledger": led}, "t1")
        self.assertIn("UNATTESTED SKELETON", row["detail"])
        self.assertIn("entry_rate_limits", row["detail"])

    def test_builder_writes_only_the_unattested_token(self):
        led = self._skeleton({"iso": "MISO", "entry_commissioning_lag": False})
        self.assertTrue(led["entries"])
        for e in led["entries"]:
            self.assertEqual(e["identification"], bl.UNATTESTED)
        self.assertEqual(led["n_unattested"], led["n_entries"])

    def test_a_filled_entry_can_pass(self):
        # The form must actually be fillable: replacing the token with a real
        # identification + source is what retires an entry.
        led = self._skeleton({"iso": "PJM", "entry_rate_limits": False})
        for e in led["entries"]:
            e["identification"] = "published"
            e["source"] = "NREL ReEDS documentation, growth-constraint bound"
        row = fv._score_dof_ledger({"dof_ledger": led}, "t1")
        self.assertEqual(row["status"], fv.PASS)

    def test_a_filled_residual_without_a_root_cause_still_fails(self):
        # Rule 21 is not weakened by the new branch: a residual entry with no
        # open root cause is malformed, whatever else the ledger contains.
        led = self._skeleton({"iso": "PJM", "entry_rate_limits": False})
        led["entries"][0]["identification"] = "residual"
        for e in led["entries"][1:]:
            e["identification"] = "published"
        row = fv._score_dof_ledger({"dof_ledger": led}, "t1")
        self.assertEqual(row["status"], fv.FAIL)
        self.assertIn("root_cause", row["detail"])

    def test_a_partly_filled_ledger_still_caveats(self):
        led = self._skeleton(
            {"iso": "PJM", "entry_rate_limits": False, "entry_commissioning_lag": False}
        )
        self.assertGreaterEqual(len(led["entries"]), 2)
        led["entries"][0]["identification"] = "published"
        led["entries"][0]["source"] = "NREL ReEDS documentation"
        row = fv._score_dof_ledger({"dof_ledger": led}, "t1")
        self.assertEqual(row["status"], fv.CAVEAT)


class SkeletonScopeTests(unittest.TestCase):
    """What the skeleton enumerates, and what it deliberately does not."""

    def test_scenario_selectors_are_not_free_parameters(self):
        led = bl.build_ledger(
            {"scenario_config": {"iso": "PJM", "start_year": 2026, "end_year": 2030}}
        )
        names = {e["name"] for e in led["entries"]}
        self.assertNotIn("start_year", names)
        self.assertNotIn("iso", names)

    def test_default_valued_fields_are_excluded_when_defaults_resolve(self):
        # An un-armed mechanism flag is not a free parameter OF THIS RUN.
        defaults = {"entry_rate_limits": False, "entry_commissioning_lag": False}
        entries = bl.skeleton_entries(
            {"entry_rate_limits": False, "entry_commissioning_lag": True}, defaults
        )
        self.assertEqual([e["name"] for e in entries], ["entry_commissioning_lag"])

    def test_without_defaults_the_wider_scope_is_declared_not_hidden(self):
        real = bl._defaults
        bl._defaults = lambda: None
        try:
            led = bl.build_ledger({"scenario_config": {"entry_rate_limits": False}})
        finally:
            bl._defaults = real
        self.assertFalse(led["defaults_available"])
        self.assertIn("WIDER", led["scope"])

    def test_grouping_assigns_every_entry_exactly_one_group(self):
        led = bl.build_ledger(
            {
                "scenario_config": {
                    # Deliberately non-default (the shipped default is 3), so the
                    # default-value filter keeps it.
                    "retirement_years_coal": 7,
                    "entry_rate_limits": False,
                    "ercot_gas_commitment_bridge": True,
                }
            }
        )
        groups = {e["name"]: e["group"] for e in led["entries"]}
        self.assertEqual(groups.get("retirement_years_coal"), "retirement")
        self.assertEqual(groups.get("entry_rate_limits"), "entry")
        self.assertEqual(
            groups.get("ercot_gas_commitment_bridge"), "dispatch_mechanism"
        )

    def test_n_scalars_matches_the_backcast_census_convention(self):
        # Booleans are decisions, not magnitudes — they must not inflate the
        # tuned-scalar count the backcast ledger reports the same way.
        self.assertEqual(bl._count_scalars(True), 0)
        self.assertEqual(bl._count_scalars({"a": 1.0, "b": {"c": 2}}), 2)


class CliTests(unittest.TestCase):
    def test_writes_a_ledger_next_to_the_run_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            (bundle / "run_config.json").write_text(
                json.dumps(
                    {"scenario_config": {"iso": "PJM", "entry_rate_limits": False}}
                )
            )
            self.assertEqual(bl.main([str(bundle)]), 0)
            led = json.loads((bundle / "dof_ledger.json").read_text())
            self.assertEqual(led["schema"], "dof-ledger/v1")
            self.assertEqual(led["status"], "SKELETON — UNATTESTED")

    def test_missing_config_is_an_explicit_error_not_an_empty_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                bl.main([tmp])


if __name__ == "__main__":
    unittest.main()
