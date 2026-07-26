"""basis_sha provenance: a bundle must identify the basis of its own bytes.

caiso-122 §1 found that a committed keeper carries no field reliably dating
its bytes: ``git_sha`` may point at a destroyed session-local commit, and
``replay_keeper`` hybridizes ``timestamp`` (original date + replay
time-of-day). caiso-123 closes the defect with ``basis_sha`` — the newest
origin/main-durable ancestor of the solving tree, written fresh at every
bundle write and NEVER restored across a replay. These tests pin all three
halves of that contract:

* ``run_calibration_full._basis_sha`` resolves to a real, full-length commit
  that is an ancestor of HEAD;
* ``replay_keeper.build_kwargs`` treats ``basis_sha`` as provenance (ignored,
  never a solve kwarg, never a strict-mode error);
* ``replay_keeper._restore_display_date`` rewrites ONLY the timestamp's date
  prefix — ``basis_sha``/``git_sha`` and the replay time-of-day stay the
  replay's own.
"""

import json
import re
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.replay_keeper import _restore_display_date, build_kwargs
from scripts.run_calibration_full import _basis_sha

REPO = Path(__file__).resolve().parents[1]


def _git_ok(*args: str) -> bool:
    try:
        subprocess.check_output(["git", *args], cwd=REPO, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


class TestBasisShaValue(unittest.TestCase):
    def test_full_length_commit_ancestor_of_head(self):
        sha = _basis_sha()
        if not sha:
            self.skipTest("no git repository visible")
        self.assertRegex(sha, re.compile(r"^[0-9a-f]{40}$"), "must be a full sha")
        # Whichever branch it came from (merge-base or the HEAD fallback), it
        # must be reachable from HEAD — a bisect can anchor on it.
        self.assertTrue(
            _git_ok("merge-base", "--is-ancestor", sha, "HEAD"),
            f"basis_sha {sha} is not an ancestor of HEAD",
        )


class TestReplayIgnoresBasisSha(unittest.TestCase):
    def test_basis_sha_is_provenance_not_a_kwarg(self):
        meta = {
            "iso": "CAISO",
            "years": [2025],
            "commitment": False,
            "git_sha": "abb0fcd",
            "basis_sha": "f" * 40,
        }
        kwargs = build_kwargs(meta)  # must not raise strict-mode SystemExit
        self.assertNotIn("basis_sha", kwargs)
        self.assertNotIn("git_sha", kwargs)


class TestRestoreDisplayDate(unittest.TestCase):
    def test_restores_date_only_never_basis_sha(self):
        replay_meta = {
            "timestamp": "2026-07-26T04:05:06",
            "git_sha": "1234567",
            "basis_sha": "a" * 40,
        }
        with TemporaryDirectory() as td:
            run_dir = Path(td)
            (run_dir / "meta.json").write_text(json.dumps(replay_meta))
            written = _restore_display_date(run_dir, "2026-07-23T22:29:35")
            out = json.loads((run_dir / "meta.json").read_text())
        # Original DATE, replay TIME-OF-DAY: the dashboard id survives while
        # the timestamp still shows when these bytes were actually produced.
        self.assertEqual(written, "2026-07-23T04:05:06")
        self.assertEqual(out["timestamp"], "2026-07-23T04:05:06")
        # The replay's provenance is untouched — restoring the original
        # basis_sha here would re-open the caiso-122 §1 defect.
        self.assertEqual(out["basis_sha"], "a" * 40)
        self.assertEqual(out["git_sha"], "1234567")


if __name__ == "__main__":
    unittest.main()
