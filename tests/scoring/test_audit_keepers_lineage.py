"""Tests for audit_keepers E11 (keeper-lineage recipe fidelity, full kwarg surface).

The nyiso-108→155 incident class
(``docs/FINDING-nyiso-hydro-truncation-repair-2026-08.md`` §2): the hydro
repair pair (``hydro_backfill_year`` / ``hydro_eia930_monthly``) are
``solve_and_persist`` kwargs, NOT ``ScenarioConfig`` fields, so lineage checks
that verified "all scenario_config fields identical" were structurally blind
to them and an armed keeper mechanism left the lineage with no de-arm decision
anywhere. E11 diffs the current keeper bundle's FULL recorded recipe
(run_config scenario block ∪ meta.json kwarg surface) against the former
keeper's, whenever the shard records ``superseded.former_keeper``.

Exercises the pure ``lineage_recipe_finding`` helper against temp bundles, and
pins ``E11_META_PROVENANCE`` against ``replay_keeper._IGNORE`` so the two
provenance surfaces (duplicated because audit_keepers is stdlib-only) cannot
drift apart.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "audit_keepers", str(REPO_ROOT / "scripts" / "audit_keepers.py")
)
ak = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ak)


def _write_bundle(root: Path, name: str, meta: dict, scenario: dict) -> str:
    """Write a minimal bundle dir and return its repo-relative path."""
    b = root / "results" / name
    b.mkdir(parents=True)
    (b / "meta.json").write_text(json.dumps(meta))
    (b / "run_config.json").write_text(json.dumps({"scenario_config": scenario}))
    return f"results/{name}"


class TestLineageRecipeFinding(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.registry = self.root / "registry"
        self.registry.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def _register(self, run_id: str, bundle_rel: str) -> None:
        (self.registry / f"{run_id}.json").write_text(
            json.dumps({"id": run_id, "bundle": bundle_rel})
        )

    def _shard(self, prose: str = "") -> dict:
        return {
            "iso": "NYISO",
            "keeper": "cur-run",
            "promotion_note": prose,
            "superseded": {"former_keeper": "old-run"},
        }

    def _pair(self, old_meta, new_meta, old_sc=None, new_sc=None):
        self._register(
            "old-run", _write_bundle(self.root, "old", old_meta, old_sc or {})
        )
        self._register(
            "cur-run", _write_bundle(self.root, "new", new_meta, new_sc or {})
        )

    def test_the_incident_case_fails_undeclared(self):
        # THE nyiso-108→144 de-arm, replayed: an armed solve kwarg reverts to
        # its default with no declaration anywhere. Solve kwargs record
        # resolved values, so the loss shows as a value change, not absence.
        self._pair(
            {"hydro_backfill_year": 2024, "hydro_eia930_monthly": True},
            {"hydro_backfill_year": None, "hydro_eia930_monthly": False},
        )
        level, msg = ak.lineage_recipe_finding(
            self._shard("promoted for unrelated reasons"), self.registry, self.root
        )
        self.assertEqual(level, "FAIL")
        self.assertIn("hydro_backfill_year", msg)
        self.assertIn("hydro_eia930_monthly", msg)
        self.assertIn("UNDECLARED", msg)

    def test_declared_change_passes_and_is_reported(self):
        self._pair({"hydro_backfill_year": None}, {"hydro_backfill_year": 2024})
        level, msg = ak.lineage_recipe_finding(
            self._shard("armed the pair: hydro_backfill_year=2024"),
            self.registry,
            self.root,
        )
        self.assertEqual(level, "OK")
        self.assertIn("hydro_backfill_year", msg)

    def test_scenario_field_change_is_also_visible(self):
        # The diff must cover BOTH surfaces — a ScenarioConfig flip is caught
        # through the run_config scenario block.
        self._pair({}, {}, {"some_flag": False}, {"some_flag": True})
        level, msg = ak.lineage_recipe_finding(self._shard(), self.registry, self.root)
        self.assertEqual(level, "FAIL")
        self.assertIn("some_flag", msg)

    def test_provenance_keys_never_diff(self):
        self._pair(
            {"timestamp": "a", "git_sha": "1", "basis_sha": "x", "note": "n1"},
            {"timestamp": "b", "git_sha": "2", "basis_sha": "y", "note": "n2"},
        )
        level, _ = ak.lineage_recipe_finding(self._shard(), self.registry, self.root)
        self.assertEqual(level, "OK")

    def test_deleted_kwarg_warns_undeclared(self):
        # Field recorded by the former solve, gone from the current surface —
        # the rule-26 codebase-deletion class: visible, not blocking.
        self._pair({"retired_flag": True}, {})
        level, msg = ak.lineage_recipe_finding(self._shard(), self.registry, self.root)
        self.assertEqual(level, "WARN")
        self.assertIn("retired_flag", msg)

    def test_born_field_is_reported_never_failed(self):
        # A field born between the solves, recorded at its default across
        # HEAD drift (e.g. sc.ercot_adaptive_fixed_point on the live
        # 152→155 pair) must not fail the promotion.
        self._pair({}, {}, {}, {"new_field": False})
        level, msg = ak.lineage_recipe_finding(self._shard(), self.registry, self.root)
        self.assertEqual(level, "OK")
        self.assertIn("new_field", msg)

    def test_no_structured_lineage_is_not_applicable(self):
        level, msg = ak.lineage_recipe_finding(
            {"iso": "PJM", "keeper": "cur-run"}, self.registry, self.root
        )
        self.assertEqual(level, "OK")
        self.assertIn("not applicable", msg)

    def test_missing_former_bundle_warns(self):
        self._register("cur-run", _write_bundle(self.root, "new", {}, {}))
        self._register("old-run", "results/pruned-away")
        level, msg = ak.lineage_recipe_finding(self._shard(), self.registry, self.root)
        self.assertEqual(level, "WARN")
        self.assertIn("former", msg)

    def test_declaration_searches_nested_prose(self):
        # The declaration corpus is the WHOLE shard recursively — a change
        # justified inside the superseded reason counts.
        self._pair({"some_kwarg": 1}, {"some_kwarg": 2})
        shard = self._shard("")
        shard["superseded"]["reason"] = "re-derived some_kwarg on new source data"
        level, _ = ak.lineage_recipe_finding(shard, self.registry, self.root)
        self.assertEqual(level, "OK")


class TestProvenanceParityWithReplayKeeper(unittest.TestCase):
    def test_e11_set_mirrors_replay_ignore(self):
        # audit_keepers is stdlib-only so it cannot import replay_keeper (which
        # pulls the numpy/model stack); the provenance set is duplicated and
        # THIS assertion is what keeps the two from drifting. E11 additionally
        # ignores the free-text meta ``note`` (replay restores it separately).
        from scripts import replay_keeper as rk

        self.assertEqual(ak.E11_META_PROVENANCE, rk._IGNORE | {"note"})


if __name__ == "__main__":
    unittest.main()
