"""Tests for audit_keepers E12 (referential integrity of LIVE shard run-id pointers).

The neiso-102 / pjm-166 incident class: a keeper shard carried a hand-authored
``holdout_touchpoint`` block naming a run that had since been PRUNED under rule
15's keeper-only retention. ``build_status.py`` copies that block into
``status/<ISO>.js`` without validating it and ``calibration-status.js`` renders
it as a run link, so the live Calibration Status card showed the held-out year
TWICE with different determinations — the stale hand-authored panel above the
auto-derived ``holdout_ladder`` — the upper one linking to a run that is not
there. Rule 30 [R-TOUCHPOINT-FOLD](b) is what the block breaches.

The check's scope is the load-bearing part, and both halves are pinned here:

* LIVE POINTERS fail — the fields the site resolves into a Run Explorer link.
* HISTORICAL CITATIONS never fail — keeper genealogy (``superseded`` and its
  ``chain``, ``de_designation_history``, ``frontier_withdrawn_*``,
  ``config_partition.configs[].source_run_id``) and narrative prose cite pruned
  runs BY DESIGN and are explicitly not retracted, so checking them would fight
  the retention discipline and red every lane.
"""

import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

from tests.helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "audit_keepers", str(REPO_ROOT / "scripts" / "audit_keepers.py")
)
ak = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ak)


class TestDanglingPointerFindings(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.registry = Path(self._tmp.name) / "registry"
        self.registry.mkdir(parents=True)
        self._register("2026-01-01-live-keeper")

    def tearDown(self):
        self._tmp.cleanup()

    def _register(self, run_id: str) -> None:
        (self.registry / f"{run_id}.json").write_text(json.dumps({"id": run_id}))

    def _find(self, shard: dict) -> list[str]:
        return ak.dangling_pointer_findings(shard, self.registry)

    # --- live pointers: a pruned target is a defect ----------------------- #

    def test_clean_shard_passes(self):
        self.assertEqual(
            self._find({"iso": "NEISO", "keeper": "2026-01-01-live-keeper"}), []
        )

    def test_dangling_holdout_touchpoint_fails(self):
        """The neiso-102 defect itself: a touchpoint panel naming a pruned run."""
        found = self._find(
            {
                "iso": "NEISO",
                "keeper": "2026-01-01-live-keeper",
                "holdout_touchpoint": {"year": 2022, "run_id": "2026-01-01-pruned"},
            }
        )
        self.assertEqual(len(found), 1)
        self.assertIn("holdout_touchpoint.run_id", found[0])
        self.assertIn("2026-01-01-pruned", found[0])

    def test_live_holdout_touchpoint_passes(self):
        self._register("2026-01-01-still-there")
        self.assertEqual(
            self._find(
                {
                    "iso": "NEISO",
                    "holdout_touchpoint": {"run_id": "2026-01-01-still-there"},
                }
            ),
            [],
        )

    def test_config_partition_run_id_is_checked_per_config(self):
        """ERCOT's two-config keeper shape: each config's run_id is a live link."""
        found = self._find(
            {
                "iso": "ERCOT",
                "config_partition": {
                    "configs": [
                        {"run_id": "2026-01-01-live-keeper"},
                        {"run_id": "2026-01-01-pruned"},
                    ]
                },
            }
        )
        self.assertEqual(len(found), 1)
        self.assertIn("config_partition.configs[1].run_id", found[0])

    def test_standing_note_probe_run_id_is_checked(self):
        found = self._find(
            {"iso": "ERCOT", "standing_note": {"probe_run_id": "2026-01-01-pruned"}}
        )
        self.assertEqual(len(found), 1)
        self.assertIn("standing_note.probe_run_id", found[0])

    # --- historical citations: pruned by design, never a defect ----------- #

    def test_keeper_genealogy_and_prose_are_out_of_scope(self):
        """Rule 15 makes pruned genealogy citations the NORM — E12 must ignore them."""
        shard = {
            "iso": "NYISO",
            "keeper": "2026-01-01-live-keeper",
            # narrative prose naming pruned runs, explicitly not retracted
            "note": "superseded 2026-01-01-pruned-a; see 2026-01-01-pruned-b",
            "site_retention_note": "PRUNED: 2026-01-01-pruned-c (--force-uncite)",
            # structured genealogy, all pointing at pruned runs by design
            "superseded": {
                "former_keeper": "2026-01-01-pruned-d",
                "prior_superseded": {"chain": {"former_keeper": "2026-01-01-pruned-e"}},
            },
            "de_designation_history": {"former_keeper": "2026-01-01-pruned-f"},
            "frontier_withdrawn_2026_09_05": {
                "keeper_at_withdrawal": "2026-01-01-pruned-g"
            },
            "config_partition": {
                "configs": [
                    {
                        "run_id": "2026-01-01-live-keeper",
                        "source_run_id": "2026-01-01-pruned-h",
                    }
                ]
            },
        }
        self.assertEqual(self._find(shard), [])

    def test_keeper_field_is_e1s_not_e12s(self):
        """``keeper`` is deliberately absent from the scope — E1 already fails it."""
        self.assertEqual(
            self._find({"iso": "NEISO", "keeper": "2026-01-01-pruned"}), []
        )

    # --- shape robustness ------------------------------------------------- #

    def test_malformed_blocks_do_not_raise(self):
        for shard in (
            {"iso": "X", "holdout_touchpoint": None},
            {"iso": "X", "holdout_touchpoint": "not-a-dict"},
            {"iso": "X", "holdout_touchpoint": {}},
            {"iso": "X", "holdout_touchpoint": {"run_id": ""}},
            {"iso": "X", "config_partition": {"configs": "not-a-list"}},
            {"iso": "X", "config_partition": {}},
        ):
            self.assertEqual(self._find(shard), [], shard)


class TestScopeMatchesRenderSites(unittest.TestCase):
    """Pin E12's scope against the page that actually renders the links.

    E12 is only correct while ``LIVE_RUN_POINTERS`` covers every shard field the
    Calibration Status page turns into a run link. The load-bearing direction is
    RENDERED -> SCOPED: if someone adds a new ``&run=${encodeURIComponent(...)}``
    href reading a new shard field and does not extend the tuple, a pruned run
    can silently go back to leaving a dead link — the exact hole neiso-102 and
    pjm-166 closed. So this walks the render sites out of the JS and requires
    each to be scoped or DELIBERATELY exempt, and fails loudly otherwise.
    """

    #: Rendered run-id fields that are correctly NOT E12's, with the reason.
    RENDER_EXEMPT = {
        # The keeper's own id — E1 already fails a keeper with no sidecar, and
        # build_status.py skips the ISO outright, so E12 would double-report.
        "keeper.run_id": "E1 covers the keeper's own sidecar",
        # The holdout ladder is DERIVED from the registry by build_status.py, so
        # every rung names a live run by construction and cannot go stale.
        "h.run_id@holdout_ladder": "derived from the registry, cannot dangle",
    }

    RUN_LINK = re.compile(r"&run=\$\{encodeURIComponent\((\w+)\.(\w+)\)\}")

    def _js(self) -> str:
        return (
            REPO_ROOT / "docs" / "codebase-site" / "js" / "calibration-status.js"
        ).read_text()

    def test_every_rendered_run_link_is_scoped_or_exempt(self):
        scoped_leaves = {path[-1] for path in ak.LIVE_RUN_POINTERS}
        rendered = {m.group(2) for m in self.RUN_LINK.finditer(self._js())}
        self.assertTrue(rendered, "found no run links — the regex has drifted")
        exempt_leaves = {k.split("@")[0].split(".")[-1] for k in self.RENDER_EXEMPT}
        for leaf in sorted(rendered):
            self.assertIn(
                leaf,
                scoped_leaves | exempt_leaves,
                f"calibration-status.js renders a run link from `.{leaf}` but "
                "E12 neither scopes nor exempts it — extend LIVE_RUN_POINTERS "
                "in scripts/audit_keepers.py, or add a documented exemption.",
            )

    def test_the_defect_field_is_scoped_not_exempt(self):
        """holdout_touchpoint.run_id is THE neiso-102/pjm-166 field — never exempt."""
        self.assertIn(("holdout_touchpoint", "run_id"), ak.LIVE_RUN_POINTERS)
        self.assertNotIn("holdout_touchpoint.run_id", self.RENDER_EXEMPT)

    def test_every_scoped_field_is_actually_rendered(self):
        """The reverse: scoping a field the page never renders is dead weight."""
        js = self._js()
        for path in ak.LIVE_RUN_POINTERS:
            self.assertIn(
                path[-1],
                js,
                f"{'.'.join(path)} is scoped by E12 but appears nowhere in "
                "calibration-status.js — the scope and render sites have drifted",
            )


if __name__ == "__main__":
    unittest.main()
