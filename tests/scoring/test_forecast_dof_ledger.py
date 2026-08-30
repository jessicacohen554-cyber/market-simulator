"""Tests for the FC-7 forecast DOF-ledger INSTRUMENT (capx-D8).

Grew out of the FR-27 stub tests. The load-bearing properties, in order:

1. **An UNIDENTIFIED entry never improves a verdict.** It carries the literal
   ``unattested`` token, and FC-7 scores a ledger holding one exactly as it
   scores an absent ledger. If that stops holding, the instrument has become
   the artifact rule 21 exists to prevent — a ledger that looks attested and
   is not.
2. **The instrument reports identification, it never supplies one** (rule 21):
   a curated row is applied only when its cross-check gate passes — the run
   value must match the registered override / the row's expected value — and
   a refused row leaves the entry UNIDENTIFIED with the refusal recorded.
3. The enumeration scope is unchanged from the stub: non-default
   solve-affecting fields only, selectors excluded, representation
   (tuple/list) normalized.
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


def _ledger(sc, **kw):
    """Trivial-fixture builder: wrap a bare scenario dict, no git context."""
    kw.setdefault("use_git", False)
    return bl.build_ledger({"scenario_config": sc}, **kw)


class UnidentifiedNeverImprovesAVerdictTests(unittest.TestCase):
    """Property 1 — the honesty pin carried over from the stub.

    NOTE on fixture values: the ledger excludes fields sitting at their
    shipped default, so every fixture supplies a genuinely NON-default value
    (``entry_rate_limits``/``entry_commissioning_lag`` ship ``True`` since
    owner decision D-2, 2026-08-02 — hence ``False`` here). Nothing depends on
    WHICH value is armed, only that it differs from the shipped default and
    carries no committed identification.
    """

    def test_an_unidentified_entry_scores_exactly_as_an_absent_ledger(self):
        led = _ledger({"iso": "PJM", "entry_rate_limits": False})
        self.assertTrue(led["entries"], "instrument produced no entries to test")
        self.assertEqual(led["n_unidentified"], led["n_entries"])
        for tier in ("t1", "t2", "t3"):
            with self.subTest(tier=tier):
                absent = fv._score_dof_ledger({}, tier)
                got = fv._score_dof_ledger({"dof_ledger": led}, tier)
                self.assertEqual(got["status"], absent["status"])

    def test_the_caveat_detail_names_what_must_be_attested(self):
        led = _ledger({"iso": "PJM", "entry_rate_limits": False})
        row = fv._score_dof_ledger({"dof_ledger": led}, "t1")
        self.assertIn("entry_rate_limits", row["detail"])

    def test_unidentified_entries_carry_only_the_unattested_token(self):
        led = _ledger({"iso": "MISO", "entry_commissioning_lag": False})
        self.assertTrue(led["entries"])
        for e in led["entries"]:
            self.assertEqual(e["identification"], bl.UNATTESTED)
            self.assertEqual(e["status"], "UNIDENTIFIED")
            self.assertIn("attestation_question", e)
        self.assertEqual(led["n_unattested"], led["n_entries"])

    def test_a_mixed_ledger_still_caveats(self):
        # One identified entry (the D-10 posture) + one unidentified: the
        # unidentified row must keep the CAVEAT.
        led = _ledger(
            {
                "iso": "PJM",
                "forecast_xyear_warmstart": False,
                "entry_rate_limits": False,
            }
        )
        self.assertEqual(led["n_identified"], 1)
        self.assertEqual(led["n_unidentified"], 1)
        row = fv._score_dof_ledger({"dof_ledger": led}, "t1")
        self.assertEqual(row["status"], fv.CAVEAT)

    def test_a_fully_identified_ledger_can_pass_fc7(self):
        # The design intent, pinned: identification drawn from committed
        # evidence CAN retire the CAVEAT on a chartered re-score.
        led = _ledger({"iso": "PJM", "forecast_xyear_warmstart": False})
        self.assertEqual(led["n_unidentified"], 0)
        self.assertTrue(led["entries"])
        row = fv._score_dof_ledger({"dof_ledger": led}, "t1")
        self.assertEqual(row["status"], fv.PASS)

    def test_a_residual_without_a_root_cause_still_fails(self):
        led = _ledger({"iso": "PJM", "forecast_xyear_warmstart": False})
        led["entries"][0]["identification"] = "residual"
        led["entries"][0].pop("root_cause", None)
        row = fv._score_dof_ledger({"dof_ledger": led}, "t1")
        self.assertEqual(row["status"], fv.FAIL)
        self.assertIn("root_cause", row["detail"])


class AttributionCrossCheckTests(unittest.TestCase):
    """Property 2 — a curated row applies only when its gate passes."""

    def test_the_d10_warmstart_posture_is_identified_as_design_decision(self):
        led = _ledger({"iso": "NYISO", "forecast_xyear_warmstart": False})
        (e,) = led["entries"]
        self.assertEqual(e["name"], "forecast_xyear_warmstart")
        self.assertEqual(e["identification"], "design-decision")
        self.assertEqual(e["status"], "IDENTIFIED")
        self.assertIn("D-10", e["source"])
        self.assertEqual(e["provenance"], "runner-posture")

    def test_a_value_mismatch_refuses_the_curated_identification(self):
        # forecast_xyear_warmstart=True is non-default AND fails the curated
        # row's expected-value gate (D-10 says False) — the entry must stay
        # UNIDENTIFIED with the refusal recorded, never be identified anyway.
        defaults = {"forecast_xyear_warmstart": False}
        entries, _ = bl.build_entries(
            {"forecast_xyear_warmstart": True},
            defaults,
            iso="NYISO",
            use_git=False,
        )
        (e,) = entries
        self.assertEqual(e["identification"], bl.UNATTESTED)
        self.assertEqual(e["status"], "UNIDENTIFIED")
        self.assertIn("refused", e["curation_refused"])

    def test_neiso_registry_overrides_identify_only_at_the_registered_value(self):
        overrides = bl._iso_registry_overrides("NEISO")
        if not overrides:
            self.skipTest("market_sim ISO registry not importable here")
        self.assertIn("ordc_voll", overrides)
        registered = overrides["ordc_voll"]
        # At the registered value: identified, published, iso-registry.
        led = _ledger({"iso": "NEISO", "ordc_voll": registered})
        (e,) = led["entries"]
        self.assertEqual(e["identification"], "published")
        self.assertEqual(e["provenance"], "iso-registry")
        self.assertIn("iso_configs", e["where"])
        # At any other value the registry match fails, the curated row's
        # requires-gate refuses, and the entry stays UNIDENTIFIED.
        led = _ledger({"iso": "NEISO", "ordc_voll": registered + 123.0})
        (e,) = led["entries"]
        self.assertEqual(e["identification"], bl.UNATTESTED)
        self.assertIn("registry", e["curation_refused"])

    def test_another_isos_run_never_borrows_neiso_curation(self):
        # Rule 25 [R-ISO-SCOPE]: the NEISO ordc rows are NEISO's. The same
        # field/value in a PJM run must stay UNIDENTIFIED (PJM registers no
        # such override).
        overrides = bl._iso_registry_overrides("NEISO")
        if not overrides:
            self.skipTest("market_sim ISO registry not importable here")
        led = _ledger({"iso": "PJM", "ordc_voll": overrides["ordc_voll"]})
        (e,) = led["entries"]
        self.assertEqual(e["identification"], bl.UNATTESTED)

    def test_design_decision_never_identifies_a_numeric_magnitude(self):
        entry = {
            "name": "x",
            "identification": bl.UNATTESTED,
            "status": "UNIDENTIFIED",
            "source": "",
            "evidence": "",
        }
        row = {"identification": "design-decision", "source": "s", "evidence": "e"}
        bl.CURATED_IDENTIFICATIONS[("*", "x")] = row
        try:
            bl._apply_curation(entry, 3.14, None, registry_matched=False)
        finally:
            del bl.CURATED_IDENTIFICATIONS[("*", "x")]
        self.assertEqual(entry["identification"], bl.UNATTESTED)
        self.assertIn("magnitude", entry["curation_refused"])


class EnumerationScopeTests(unittest.TestCase):
    """Property 3 — what the ledger enumerates, and what it deliberately does not."""

    def test_scenario_selectors_are_not_free_parameters(self):
        led = _ledger({"iso": "PJM", "start_year": 2026, "end_year": 2030})
        names = {e["name"] for e in led["entries"]}
        self.assertNotIn("start_year", names)
        self.assertNotIn("iso", names)

    def test_default_valued_fields_are_excluded_when_defaults_resolve(self):
        # An un-armed mechanism flag is not a free parameter OF THIS RUN.
        defaults = {"entry_rate_limits": False, "entry_commissioning_lag": False}
        entries, _ = bl.build_entries(
            {"entry_rate_limits": False, "entry_commissioning_lag": True},
            defaults,
            use_git=False,
        )
        self.assertEqual([e["name"] for e in entries], ["entry_commissioning_lag"])

    def test_tuple_vs_list_representation_is_not_a_free_parameter(self):
        # The FFR-3B stub compared raw and mis-listed every tuple-valued
        # default (the offer-surface families) as non-default. Pinned fixed.
        defaults = {"pjm_offer_surface_netload_pcts": (0.8, 0.9, 0.97)}
        entries, _ = bl.build_entries(
            {"pjm_offer_surface_netload_pcts": [0.8, 0.9, 0.97]},
            defaults,
            use_git=False,
        )
        self.assertEqual(entries, [])

    def test_a_null_where_head_ships_a_default_is_reported_not_scored(self):
        defaults = {"capacity_market_clearing_by_iso": {"PJM": True}}
        entries, drift = bl.build_entries(
            {"capacity_market_clearing_by_iso": None},
            defaults,
            use_git=False,
        )
        self.assertEqual(entries, [])
        (d,) = drift
        self.assertEqual(d["name"], "capacity_market_clearing_by_iso")
        self.assertIsNone(d["run_value"])

    def test_without_defaults_the_wider_scope_is_declared_not_hidden(self):
        real = bl._defaults
        bl._defaults = lambda: None
        try:
            led = _ledger({"entry_rate_limits": False})
        finally:
            bl._defaults = real
        self.assertFalse(led["defaults_available"])
        self.assertIn("WIDER", led["scope"])

    def test_grouping_assigns_every_entry_exactly_one_group(self):
        led = _ledger(
            {
                # Deliberately non-default (the shipped default is 3), so the
                # default-value filter keeps it.
                "retirement_years_coal": 7,
                "entry_rate_limits": False,
                "ercot_gas_commitment_bridge": True,
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
            self.assertEqual(bl.main([str(bundle), "--no-git"]), 0)
            led = json.loads((bundle / "dof_ledger.json").read_text())
            self.assertEqual(led["schema"], "dof-ledger/v1")
            self.assertIn("INSTRUMENT", led["status"])
            self.assertIn("UNIDENTIFIED", led["status"])

    def test_missing_config_is_an_explicit_error_not_an_empty_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                bl.main([tmp, "--no-git"])


if __name__ == "__main__":
    unittest.main()
