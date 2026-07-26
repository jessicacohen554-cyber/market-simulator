"""An unresolvable prior-bundle SHA must REFUSE ``--reuse-solved`` reuse.

The 2026-07-22 history rewrite orphaned the ``git.sha`` recorded by every
pre-rewrite bundle, and no old-to-new mapping was saved
(docs/governance/rule-history.md §6). ``plan_reuse_solved`` proves code
identity with ``git diff <prior_sha> HEAD`` over src/scripts/data; when the
recorded commit does not resolve, that proof cannot be produced, so the only
sound behaviour is refusal — no year reused, every requested year solved
fresh, never a warn-and-proceed or a heuristic fallback. These tests pin the
*decision* (plan/record shape), not the message wording: an
identically-configured control run whose prior SHA does resolve reuses
cleanly, isolating unresolvability as the sole cause of the refusal.
"""

import dataclasses
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from scripts import run_calibration_full as rcf

_CUR_SHA = "aaa1111"
_PRIOR_SHA = "feedbee"  # recorded by the prior bundle; never equal to _CUR_SHA


@dataclasses.dataclass
class _FakeCfg:
    """Stand-in for the per-year recorded ScenarioConfig."""

    year: int

    def cache_key(self) -> str:
        return f"ck-{self.year}"


def _fake_git(*, verify_ok):
    """Fake ``rcf._git``: clean tree, empty diff, prior-SHA resolvability knob."""

    def fake(*args):
        if args[:2] == ("rev-parse", "--short"):
            return _CUR_SHA
        if args[:2] == ("rev-parse", "--verify"):
            return "resolved" if verify_ok else ""
        return ""

    return fake


class TestUnresolvablePriorSha(unittest.TestCase):
    years = [2024]
    gas_prices = {2024: 2.5}

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.prior = Path(tmp.name) / "prior"
        (self.prior / "dispatch").mkdir(parents=True)
        (self.prior / "dispatch" / "2024_P1.parquet").touch()
        pd.DataFrame({"year": [2024], "pass": "P1", "price": 30.0}).to_parquet(
            self.prior / "system.parquet", index=False
        )
        (self.prior / "meta.json").write_text(
            json.dumps(
                {
                    "iso": "ERCOT",
                    "years": list(self.years),
                    "hours": 8760,
                    "passes": ["P1"],
                    "gas_prices": {"2024": 2.5},
                    "timestamp": "2026-07-01T12:00:00",
                    "git_sha": _PRIOR_SHA,
                    "highspy_version": "1.7.2",
                }
            )
        )
        (self.prior / "run_config.json").write_text(
            json.dumps(
                {
                    "git": {"sha": _PRIOR_SHA, "dirty": False},
                    "scenario_config": dataclasses.asdict(_FakeCfg(2024)),
                }
            )
        )
        # Isolate the git-identity gate: the recipe channel (replay_keeper)
        # and every other environment gate are held constant and passing.
        stub_rk = types.SimpleNamespace(build_kwargs=lambda meta: {})
        patches = [
            mock.patch.dict(sys.modules, {"replay_keeper": stub_rk}),
            mock.patch.object(rcf, "_untracked_data_newest_mtime", lambda: (0.0, "")),
            mock.patch.object(rcf, "_highspy_version", lambda: "1.7.2"),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def _plan(self, *, verify_ok):
        with mock.patch.object(rcf, "_git", _fake_git(verify_ok=verify_ok)):
            return rcf.plan_reuse_solved(
                self.prior,
                iso="ERCOT",
                hours=8760,
                years=self.years,
                gas_prices=self.gas_prices,
                current_kwargs={},
                recorded_config_for_year=_FakeCfg,
            )

    def test_unresolvable_sha_refuses_reuse_entirely(self):
        plan, record = self._plan(verify_ok=False)
        self.assertEqual(plan, {})  # refuse: nothing may be byte-copied
        self.assertEqual(record["reused_years"], {})
        self.assertEqual(record["fresh_years"], self.years)  # solves fresh
        self.assertIn("bundle", record["refusals"])
        # The refusal must name the offending commit (interpolation contract;
        # the prose around it is free to change).
        self.assertIn(_PRIOR_SHA, record["refusals"]["bundle"])

    def test_control_resolvable_sha_reuses(self):
        # Identical bundle and kwargs; the ONLY difference is that the prior
        # SHA resolves (and diffs clean against HEAD). Reuse must proceed —
        # proving the refusal above is caused by unresolvability alone.
        plan, record = self._plan(verify_ok=True)
        self.assertEqual(sorted(plan), self.years)
        self.assertEqual(record["fresh_years"], [])
        self.assertEqual(record["refusals"], {})


if __name__ == "__main__":
    unittest.main()
