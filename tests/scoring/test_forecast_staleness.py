"""Tests for the FR-21 staleness machinery.

Covers ``scripts/lib/forecast_provenance.py`` (the stamp) and
``scripts/check_forecast_staleness.py`` (the WARN-level detector). Both are
stdlib-only, so these tests build synthetic board artifacts in a temp dir and
never touch the committed namespace, git, or an LP.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import REPO_ROOT


def _load(name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(name, str(REPO_ROOT / relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fp = _load("forecast_provenance_under_test", "scripts/lib/forecast_provenance.py")
cs = _load("check_forecast_staleness_under_test", "scripts/check_forecast_staleness.py")


class ProvenanceStampTests(unittest.TestCase):
    """The stamp is total: it never raises and always carries every field."""

    def test_stamp_carries_every_field(self):
        s = fp.stamp({})
        for field in fp.PROVENANCE_FIELDS:
            self.assertIn(field, s)
        self.assertEqual(s["schema"], fp.SCHEMA)

    def test_cache_epoch_is_read_not_recomputed(self):
        self.assertEqual(fp.cache_epoch_from({"cache_key": "abc123"}), "abc123")
        self.assertEqual(
            fp.cache_epoch_from({"meta": {"cache_key": "deadbeef"}}), "deadbeef"
        )
        self.assertEqual(
            fp.cache_epoch_from({"scenario_config": {"cache_key": "cafe"}}), "cafe"
        )

    def test_absent_epoch_is_none_never_guessed(self):
        self.assertIsNone(fp.cache_epoch_from({}, None, "not-a-dict"))
        self.assertIsNone(fp.stamp({})["cache_epoch"])

    def test_first_artifact_with_an_epoch_wins(self):
        self.assertEqual(
            fp.cache_epoch_from({}, {"cache_key": "second"}, {"cache_key": "third"}),
            "second",
        )

    def test_read_stamp_accepts_wrapped_and_bare(self):
        wrapped = {fp.PROVENANCE_KEY: {"scored_at_sha": "a" * 12}}
        self.assertEqual(fp.read_stamp(wrapped)["scored_at_sha"], "a" * 12)
        bare = {"scored_at_sha": "b" * 12, "scored_at_date": "2026-08-02T00:00:00Z"}
        self.assertEqual(fp.read_stamp(bare)["scored_at_sha"], "b" * 12)

    def test_read_stamp_survives_a_hand_edited_board(self):
        # A `provenance` value that is not a dict must read as unstamped, not
        # raise — the detector has to survive any file a human edited.
        self.assertIsNone(fp.read_stamp({fp.PROVENANCE_KEY: "oops"}))
        self.assertIsNone(fp.read_stamp("not a dict"))
        self.assertIsNone(fp.read_stamp(None))


class CollectStampsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, name, obj):
        p = self.root / name
        p.write_text(json.dumps(obj))
        return p

    def _stamp(self, sha, date, epoch=None):
        return {
            "schema": fp.SCHEMA,
            "scored_at_sha": sha,
            "scored_at_date": date,
            "cache_epoch": epoch,
        }

    def test_collects_top_level_and_nested_stamps(self):
        # A registry sidecar holds ONE stamped object; ff-verdicts.json holds a
        # mapping of them. Both shapes must be walked.
        self._write("sidecar.json", {fp.PROVENANCE_KEY: self._stamp("a" * 12, "d1")})
        self._write(
            "verdicts.json",
            {
                "pjm-t1f": {fp.PROVENANCE_KEY: self._stamp("b" * 12, "d2")},
                "miso-t1f": {fp.PROVENANCE_KEY: self._stamp("c" * 12, "d3")},
            },
        )
        self.assertEqual(len(fp.collect_stamps([self.root])), 3)

    def test_unreadable_and_unstamped_files_are_skipped_silently(self):
        self._write("fine.json", {fp.PROVENANCE_KEY: self._stamp("a" * 12, "d1")})
        self._write("unstamped.json", {"id": "x"})
        (self.root / "broken.json").write_text("{not json")
        self.assertEqual(len(fp.collect_stamps([self.root])), 1)


class StalenessEvaluationTests(unittest.TestCase):
    """The detector's verdict logic, with git distance stubbed out."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._real_distance = cs.solve_affecting_commits_since
        self._real_head = cs.fp.head_sha

    def tearDown(self):
        cs.solve_affecting_commits_since = self._real_distance
        cs.fp.head_sha = self._real_head
        self._tmp.cleanup()

    def _board(self, stamps):
        for i, s in enumerate(stamps):
            (self.root / f"run{i}.json").write_text(json.dumps({fp.PROVENANCE_KEY: s}))

    def _stamp(self, sha, date, epoch=None):
        return {
            "schema": fp.SCHEMA,
            "scored_at_sha": sha,
            "scored_at_date": date,
            "cache_epoch": epoch,
        }

    def test_empty_board_warns_that_nothing_is_stamped(self):
        rep = cs.evaluate(paths=[self.root])
        self.assertTrue(rep["stale"])
        self.assertIn("NO provenance stamps", rep["warnings"][0])

    def test_unscored_board_warns_and_does_not_read_as_fresh(self):
        # This is the repo's ACTUAL state until FFR-3A re-scores: stamps exist,
        # but none records a scored-at sha. It must warn, not pass.
        self._board([self._stamp(None, None, "epoch1")])
        rep = cs.evaluate(paths=[self.root])
        self.assertTrue(rep["stale"])
        self.assertIn("UNSCORED", rep["warnings"][0])

    def test_fresh_board_within_threshold_is_ok(self):
        cs.solve_affecting_commits_since = lambda sha: 3
        self._board([self._stamp("a" * 12, "2026-08-02T00:00:00Z", "e1")])
        rep = cs.evaluate(max_commits=10, paths=[self.root])
        self.assertFalse(rep["stale"])
        self.assertEqual(rep["solve_affecting_commits_since_scored"], 3)

    def test_distance_past_threshold_warns(self):
        cs.solve_affecting_commits_since = lambda sha: 25
        self._board([self._stamp("a" * 12, "2026-07-20T00:00:00Z", "e1")])
        rep = cs.evaluate(max_commits=10, paths=[self.root])
        self.assertTrue(rep["stale"])
        self.assertIn("25 solve-affecting commit(s)", rep["warnings"][0])

    def test_newest_stamp_wins_not_the_oldest(self):
        # A board holding both a fresh and a stale run is measured from the
        # FRESHEST evidence — otherwise every board is permanently stale.
        cs.solve_affecting_commits_since = lambda sha: 0 if sha == "n" * 12 else 99
        self._board(
            [
                self._stamp("o" * 12, "2026-07-01T00:00:00Z"),
                self._stamp("n" * 12, "2026-08-01T00:00:00Z"),
            ]
        )
        rep = cs.evaluate(max_commits=10, paths=[self.root])
        self.assertEqual(rep["position"]["newest_scored_at_sha"], "n" * 12)
        self.assertFalse(rep["stale"])

    def test_unreachable_sha_reports_unknown_not_zero(self):
        cs.solve_affecting_commits_since = lambda sha: None
        self._board([self._stamp("a" * 12, "2026-08-02T00:00:00Z")])
        rep = cs.evaluate(paths=[self.root])
        self.assertTrue(rep["stale"])
        self.assertIn("UNKNOWN", rep["warnings"][0])
        self.assertIsNone(rep["solve_affecting_commits_since_scored"])

    def test_epoch_spread_is_reported_but_never_alone_a_warning(self):
        cs.solve_affecting_commits_since = lambda sha: 0
        self._board(
            [
                self._stamp("a" * 12, "2026-08-02T00:00:00Z", "e1"),
                self._stamp("a" * 12, "2026-08-02T00:00:00Z", "e2"),
            ]
        )
        rep = cs.evaluate(paths=[self.root])
        self.assertFalse(rep["stale"])
        self.assertIn("epoch_spread_note", rep["position"])

    def test_render_never_raises_on_any_report(self):
        for maker in (
            lambda: cs.evaluate(paths=[self.root]),
            lambda: (
                self._board([self._stamp("a" * 12, "d")])
                or cs.evaluate(paths=[self.root])
            ),
        ):
            self.assertIsInstance(cs.render(maker()), str)


class WarnOnlyContractTests(unittest.TestCase):
    """The check must not block the build unless explicitly asked to."""

    def test_exit_code_is_zero_on_a_stale_board_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            real = cs.board_position
            cs.board_position = lambda paths=None: {
                "n_stamps": 0,
                "n_scored": 0,
                "newest_scored_at_sha": None,
                "newest_scored_at_date": None,
                "cache_epochs": [],
                "head_sha": "a" * 12,
            }
            try:
                self.assertEqual(cs.main([]), 0)
                self.assertEqual(cs.main(["--fail-on-stale"]), 1)
            finally:
                cs.board_position = real
                Path(tmp)  # keep the tmp dir referenced until teardown

    def test_ci_invokes_the_check_without_fail_on_stale(self):
        # The WARN-only contract lives in ci.yml as much as in the script: a
        # future edit adding --fail-on-stale would silently make forecast-board
        # freshness block backcast velocity.
        ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text()
        self.assertIn("scripts/check_forecast_staleness.py", ci)
        line = next(
            ln
            for ln in ci.splitlines()
            if "check_forecast_staleness.py" in ln and "run:" in ln
        )
        self.assertNotIn("--fail-on-stale", line)


class BoardInputPresenceTests(unittest.TestCase):
    """An ABSENT board must never read as an UNSTAMPED board.

    The FR-21 provenance-restore session opened on a reading of "0 stamped, 0
    scored — the board carries NO provenance stamps at all" taken against a tree
    that did not hold the board files. Direct measurement on the same commit,
    from the commit's own tree, read 39 stamped / 8 scored: the stamps were
    never lost. These tests keep the two states distinguishable.
    """

    def test_absent_input_is_a_measurement_failure_not_an_unstamped_board(self):
        with tempfile.TemporaryDirectory() as tmp:
            ghost = Path(tmp) / "not-here.json"
            rep = cs.evaluate(paths=[ghost])
        self.assertTrue(rep["stale"])
        self.assertEqual(rep["position"]["n_stamps"], 0)
        joined = " ".join(rep["warnings"])
        self.assertIn("BOARD INPUT(S) MISSING", joined)
        # The false claim must be suppressed, not merely out-ranked.
        self.assertNotIn("NO provenance stamps", joined)

    def test_present_but_empty_board_still_reads_as_unstamped(self):
        with tempfile.TemporaryDirectory() as tmp:
            rep = cs.evaluate(paths=[Path(tmp)])
        self.assertEqual(rep["position"]["missing_inputs"], [])
        self.assertIn("NO provenance stamps", " ".join(rep["warnings"]))

    def test_generated_inputs_are_never_reported_missing(self):
        # registry/ is gitignored and the Pages deploy is its single writer, so
        # it is absent in a normal checkout. That must stay silent.
        self.assertIn("frontend/data/forecast/registry", cs.BOARD_INPUTS_GENERATED)
        absent = cs.missing_inputs(
            [cs.REPO / g for g in cs.BOARD_INPUTS_GENERATED]
        )
        self.assertEqual(absent, [])

    def test_the_records_lane_file_is_watched(self):
        # program-status.json is what a gate-(a) re-key rewrites. Watching it is
        # what makes a re-key that drops its stamp visible instead of silent.
        self.assertIn(
            "frontend/data/forecast/program-status.json", cs.BOARD_INPUTS_COMMITTED
        )

    def test_this_checkout_holds_every_committed_board_input(self):
        # The standing regression guard: a records-lane edit that deletes or
        # relocates a tracked board input fails here instead of silently
        # reappearing as "the board has no stamps".
        for rel in cs.BOARD_INPUTS_COMMITTED:
            self.assertTrue((cs.REPO / rel).exists(), f"missing board input: {rel}")


if __name__ == "__main__":
    unittest.main()
