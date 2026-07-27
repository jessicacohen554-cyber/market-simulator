"""--reuse-solved eligibility planning and labeling (run_calibration_full).

``plan_reuse_solved`` is the correctness crux of the opt-in reuse path: a year
may be byte-copied from a prior bundle ONLY when the effective per-year config,
the full solve recipe, and the code + data state all provably match — anything
ambiguous solves fresh. These tests pin every refusal gate, the per-year
mixed-plan behavior, the meta labeling block, and that ``replay_keeper``
treats the new ``"reuse"`` meta key as provenance (never a recipe kwarg).
"""

import dataclasses
import json
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from scripts import run_calibration_full as rcf
from scripts.replay_keeper import build_kwargs

_TS = "2026-07-10T12:00:00"
_SHA = "abc1234"


@dataclasses.dataclass
class _FakeCfg:
    """Stand-in for the per-year recorded ScenarioConfig."""

    year: int
    foo: str = "bar"

    def cache_key(self) -> str:
        return f"ck-{self.year}"


def _fake_git(status="", cur_sha=_SHA, diff="", verify_ok=True):
    def fake(*args):
        if args[0] == "rev-parse" and args[1] == "--short":
            return cur_sha
        if args[0] == "rev-parse" and args[1] == "--verify":
            return "resolved" if verify_ok else ""
        if args[0] == "status":
            return status
        if args[0] == "diff":
            return diff
        if args[0] == "ls-files":
            return ""
        return ""

    return fake


class _PlanBase(unittest.TestCase):
    """Shared fake prior bundle + patched environment."""

    years = [2023, 2024]
    gas_prices = {2023: 3.0, 2024: 2.5}

    def setUp(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.prior = Path(self._tmp.name) / "prior"
        (self.prior / "dispatch").mkdir(parents=True)
        self.meta = {
            "iso": "MISO",
            "years": list(self.years),
            "hours": 8760,
            "passes": ["P1"],
            "commitment": False,
            "commitment_screen_coal": True,
            "gas_prices": {str(y): p for y, p in self.gas_prices.items()},
            "timestamp": _TS,
            "git_sha": _SHA,
            "highspy_version": "1.7.2",
        }
        self.run_config = {
            "git": {"sha": _SHA, "dirty": False},
            "scenario_config": dataclasses.asdict(_FakeCfg(self.years[0])),
        }
        pd.DataFrame(
            {
                "year": [y for y in self.years for _ in range(2)],
                "pass": "P1",
                "price": 30.0,
            }
        ).to_parquet(self.prior / "system.parquet", index=False)
        for y in self.years:
            (self.prior / "dispatch" / f"{y}_P1.parquet").touch()
        self._patches = [
            mock.patch.object(rcf, "_git", _fake_git()),
            mock.patch.object(rcf, "_untracked_data_newest_mtime", lambda: (0.0, "")),
            mock.patch.object(rcf, "_highspy_version", lambda: "1.7.2"),
        ]
        for p in self._patches:
            p.start()
            self.addCleanup(p.stop)

    def _write_bundle(self):
        (self.prior / "meta.json").write_text(json.dumps(self.meta))
        (self.prior / "run_config.json").write_text(json.dumps(self.run_config))

    def _plan(self, current_kwargs=None, years=None, gas_prices=None):
        self._write_bundle()
        return rcf.plan_reuse_solved(
            self.prior,
            iso="MISO",
            hours=8760,
            years=years or self.years,
            gas_prices=gas_prices or self.gas_prices,
            current_kwargs=(
                {"commitment": False, "screen_coal": True}
                if current_kwargs is None
                else current_kwargs
            ),
            recorded_config_for_year=_FakeCfg,
        )


class TestHappyPath(_PlanBase):
    def test_all_years_reused_and_labeled(self):
        plan, record = self._plan()
        self.assertEqual(sorted(plan), self.years)
        for y in self.years:
            self.assertEqual(plan[y]["passes"], ["P1"])
            self.assertEqual(plan[y]["cache_key"], f"ck-{y}")
        self.assertEqual(sorted(record["reused_years"]), [str(y) for y in self.years])
        self.assertEqual(record["fresh_years"], [])
        self.assertEqual(record["source_bundle"], str(self.prior))
        self.assertEqual(record["source_git_sha"], _SHA)
        self.assertIn("NOT fresh evidence", record["warning"])

    def test_environment_block_is_ignored_by_reuse(self):
        # The environment stamp (A6) lives at meta/run_config top level, NOT in
        # scenario_config, so the reuse comparator must ignore it entirely — a
        # prior bundle carrying it (and a different one) still reuses cleanly.
        self.meta["environment"] = {
            "python_version": "3.11.9",
            "platform": "some-other-box",
            "packages": {"highspy": "1.7.2", "numpy": "1.99"},
        }
        self.run_config["environment"] = self.meta["environment"]
        plan, record = self._plan()
        self.assertEqual(sorted(plan), self.years)
        self.assertEqual(record["fresh_years"], [])

    def test_sha_drift_without_model_diff_is_allowed(self):
        # A docs/frontend-only commit between the prior solve and now must
        # not break reuse — only src/scripts/data changes do.
        with mock.patch.object(rcf, "_git", _fake_git(cur_sha="fff9999", diff="")):
            plan, record = self._plan()
        self.assertEqual(sorted(plan), self.years)


class TestBundleLevelRefusals(_PlanBase):
    def _assert_refused_all(self, plan, record, needle):
        self.assertEqual(plan, {})
        self.assertEqual(record["fresh_years"], self.years)
        self.assertIn(needle, record["refusals"]["bundle"])

    def test_missing_metadata(self):
        plan, record = rcf.plan_reuse_solved(
            self.prior / "nope",
            iso="MISO",
            hours=8760,
            years=self.years,
            gas_prices=self.gas_prices,
            current_kwargs={},
            recorded_config_for_year=_FakeCfg,
        )
        self._assert_refused_all(plan, record, "missing meta.json")

    def test_iso_mismatch(self):
        self.meta["iso"] = "PJM"
        plan, record = self._plan()
        self._assert_refused_all(plan, record, "PJM")

    def test_hours_mismatch(self):
        self.meta["hours"] = 48
        plan, record = self._plan()
        self._assert_refused_all(plan, record, "hours")

    def test_highspy_version_mismatch(self):
        self.meta["highspy_version"] = "1.6.0"
        plan, record = self._plan()
        self._assert_refused_all(plan, record, "highspy")

    def test_solve_kwarg_mismatch_forces_fresh(self):
        plan, record = self._plan(
            current_kwargs={
                "commitment": False,
                "screen_coal": True,
                "energy_reserve_coopt": True,
            }
        )
        self._assert_refused_all(plan, record, "energy_reserve_coopt")

    def test_unreconstructable_meta_refuses(self):
        self.meta["not_a_real_kwarg_xyz"] = True
        plan, record = self._plan()
        self._assert_refused_all(plan, record, "not kwargs-reconstructable")

    def test_scenario_config_mismatch_names_the_field(self):
        self.run_config["scenario_config"]["foo"] = "DIFFERENT"
        plan, record = self._plan()
        self._assert_refused_all(plan, record, "foo")

    def test_dirty_worktree_refuses(self):
        with mock.patch.object(
            rcf, "_git", _fake_git(status=" M src/market_sim/model/dispatch.py")
        ):
            plan, record = self._plan()
        self._assert_refused_all(plan, record, "dirty")

    def test_prior_dirty_bundle_refuses(self):
        self.run_config["git"]["dirty"] = True
        plan, record = self._plan()
        self._assert_refused_all(plan, record, "dirty tree")

    def test_sha_drift_with_model_diff_refuses(self):
        with mock.patch.object(
            rcf,
            "_git",
            _fake_git(cur_sha="fff9999", diff="src/market_sim/model/dispatch.py"),
        ):
            plan, record = self._plan()
        self._assert_refused_all(plan, record, "dispatch.py")

    def test_unresolvable_prior_sha_refuses(self):
        with mock.patch.object(
            rcf, "_git", _fake_git(cur_sha="fff9999", verify_ok=False)
        ):
            plan, record = self._plan()
        self._assert_refused_all(plan, record, "not resolvable")

    def test_newer_untracked_data_refuses(self):
        with mock.patch.object(
            rcf,
            "_untracked_data_newest_mtime",
            lambda: (4102444800.0, "data/clean/miso/demand.parquet"),
        ):
            plan, record = self._plan()
        self._assert_refused_all(plan, record, "demand.parquet")

    def test_missing_system_parquet_refuses(self):
        (self.prior / "system.parquet").unlink()
        plan, record = self._plan()
        self._assert_refused_all(plan, record, "system.parquet")


class TestPerYearMixedPlan(_PlanBase):
    def test_gas_price_change_resolves_only_that_year(self):
        plan, record = self._plan(gas_prices={2023: 3.0, 2024: 9.9})
        self.assertEqual(sorted(plan), [2023])
        self.assertEqual(record["fresh_years"], [2024])
        self.assertIn("Henry Hub", record["refusals"]["2024"])

    def test_missing_dispatch_file_resolves_only_that_year(self):
        (self.prior / "dispatch" / "2024_P1.parquet").unlink()
        plan, record = self._plan()
        self.assertEqual(sorted(plan), [2023])
        self.assertIn("dispatch", record["refusals"]["2024"])

    def test_year_not_in_prior_bundle_solves_fresh(self):
        plan, record = self._plan(years=[2023, 2025], gas_prices={2023: 3.0, 2025: 4.0})
        self.assertEqual(sorted(plan), [2023])
        self.assertIn("not solved", record["refusals"]["2025"])


class TestCopyReusedYear(unittest.TestCase):
    def test_copies_dispatch_floors_and_optional_p2_state(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            prior, dest = Path(tmp) / "prior", Path(tmp) / "dest"
            (prior / "dispatch").mkdir(parents=True)
            (prior / "floors").mkdir()
            (prior / "p2_state").mkdir()
            (dest / "dispatch").mkdir(parents=True)
            (prior / "dispatch" / "2023_P1.parquet").write_bytes(b"d")
            (prior / "floors" / "2023_P1.npz").write_bytes(b"f")
            (prior / "p2_state" / "2023.pkl.gz").write_bytes(b"p")
            rcf._copy_reused_year(prior, dest, 2023, ["P1"], persist_p2_state=True)
            self.assertEqual((dest / "dispatch" / "2023_P1.parquet").read_bytes(), b"d")
            self.assertEqual((dest / "floors" / "2023_P1.npz").read_bytes(), b"f")
            self.assertEqual((dest / "p2_state" / "2023.pkl.gz").read_bytes(), b"p")

    def test_no_p2_state_copy_when_not_persisting(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            prior, dest = Path(tmp) / "prior", Path(tmp) / "dest"
            (prior / "dispatch").mkdir(parents=True)
            (prior / "p2_state").mkdir()
            (dest / "dispatch").mkdir(parents=True)
            (prior / "dispatch" / "2023_P1.parquet").write_bytes(b"d")
            (prior / "p2_state" / "2023.pkl.gz").write_bytes(b"p")
            rcf._copy_reused_year(prior, dest, 2023, ["P1"], persist_p2_state=False)
            self.assertFalse((dest / "p2_state").exists())


class TestNormalization(unittest.TestCase):
    def test_none_dict_entries_drop_and_empty_collapses_to_none(self):
        self.assertIsNone(rcf._norm_reuse_value({"a": None}))
        self.assertIsNone(rcf._norm_reuse_value({}))

    def test_json_roundtrip_shapes_are_equal(self):
        self.assertEqual(
            rcf._norm_reuse_value(("a", "b")), rcf._norm_reuse_value(["a", "b"])
        )
        self.assertEqual(
            rcf._norm_reuse_value(frozenset({"b", "a"})),
            rcf._norm_reuse_value(["a", "b"]),
        )
        self.assertEqual(
            rcf._norm_reuse_value({"x": 1, "y": None}),
            rcf._norm_reuse_value({"x": 1}),
        )

    def test_exempt_kwargs_are_real_parameters(self):
        import inspect

        params = set(inspect.signature(rcf.solve_and_persist).parameters)
        self.assertLessEqual(rcf._REUSE_KWARG_EXEMPT, params)


class TestReplayIgnoresReuseKey(unittest.TestCase):
    def test_reuse_meta_key_is_provenance_not_a_kwarg(self):
        meta = {
            "iso": "MISO",
            "years": [2023],
            "commitment": False,
            "reuse": {"reused_years": {"2023": {"cache_key": "ck"}}},
        }
        kwargs = build_kwargs(meta)
        self.assertNotIn("reuse", kwargs)
        self.assertNotIn("reuse_solved", kwargs)


if __name__ == "__main__":
    unittest.main()
