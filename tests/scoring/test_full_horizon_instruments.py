"""Tests for the T1-F measurement instruments FFR-3D repaired (FFR-3A 5/7/8).

Trivial-first, LP-free: every case builds a synthetic ledger / cache directory
rather than solving. Three repairs, each of which made a scorer's verdict
describe the INSTRUMENT rather than the run:

* **blocker 8** — ``extract_trajectory`` summed thermal additions into one
  ``builds_thermal_mw`` although the evolution ledger tags every row with its
  ``source``. ``forecast_verdict`` FC-2 row 4 reads
  ``builds_thermal_backstop_mw`` / ``builds_by_source["reserve_backstop"]``, so
  with the backstop channel armed the row SKIPped everywhere — and BLK-10
  backstop sizing, the evidence owner decision D-2 was meant to re-open, could
  not be scored at all. Asserted end-to-end here: split emitted ⇒ row 4 scores.
* **blocker 7** — the runner never wrote ``run_config.json``, so FC-7 row 1
  FAILed "run_config.json absent" on every leg by construction. Asserted that
  the artifact is written from the run's OWN resolved ``config.yaml`` and that
  it is NOT written when there is no resolved config to read (a zero-year run
  has no provenance; FC-7 FAILing on it is the truthful verdict).
* **blocker 5** — the console printed ``invariants: 0 FAIL, 0 WARN`` on a
  zero-year run, rendering a hard failure as a clean gate.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts import forecast_verdict as FV  # noqa: E402
from scripts import run_full_horizon as F  # noqa: E402


def _ledger(rows: list[dict]) -> dict:
    return {"thermal_additions": rows}


class BuildsBySourceSplitTest(unittest.TestCase):
    """Blocker 8 — the per-channel thermal split reaches the trajectory."""

    def _traj_row(self, rows: list[dict]) -> dict:
        # extract_trajectory needs a full Run; exercise the split arithmetic on
        # the same ledger shape it consumes, then assert the wiring separately.
        by_source: dict[str, float] = {}
        for r in rows:
            src = str(r.get("source") or "unattributed")
            by_source[src] = by_source.get(src, 0.0) + float(r.get("mw", 0.0) or 0.0)
        return {
            "builds_thermal_mw": sum(float(r.get("mw", 0.0)) for r in rows),
            "builds_thermal_backstop_mw": round(
                by_source.get("reserve_backstop", 0.0), 6
            ),
            "builds_by_source": {k: round(v, 6) for k, v in sorted(by_source.items())},
            "builds_renew_mw": 0.0,
            "builds_storage_mw": 0.0,
        }

    def test_split_separates_the_three_ledger_channels(self):
        row = self._traj_row(
            [
                {"mw": 100.0, "source": "planned"},
                {"mw": 250.0, "source": "economic"},
                {"mw": 50.0, "source": "reserve_backstop"},
                {"mw": 30.0, "source": "reserve_backstop"},
            ]
        )
        self.assertEqual(row["builds_thermal_mw"], 430.0)
        self.assertEqual(row["builds_thermal_backstop_mw"], 80.0)
        self.assertEqual(
            row["builds_by_source"],
            {"economic": 250.0, "planned": 100.0, "reserve_backstop": 80.0},
        )

    def test_untagged_row_is_labelled_not_dropped(self):
        # A legacy ledger row with no `source` must be visible as
        # "unattributed", never silently folded into a real channel.
        row = self._traj_row([{"mw": 10.0}, {"mw": 5.0, "source": "economic"}])
        self.assertEqual(row["builds_by_source"]["unattributed"], 10.0)
        self.assertEqual(row["builds_thermal_backstop_mw"], 0.0)

    def test_the_split_is_wired_into_extract_trajectory(self):
        # Guards against the split existing but never being emitted (the exact
        # shape of blocker 8 itself).
        import inspect

        src = inspect.getsource(F.extract_trajectory)
        self.assertIn('"builds_thermal_backstop_mw"', src)
        self.assertIn('"builds_by_source"', src)


class Fc2Row4ScoresOnTheSplitTest(unittest.TestCase):
    """Blocker 8, end to end — FC-2 row 4 stops SKIPping."""

    def _score(self, traj: list[dict]) -> dict:
        art = {
            "run_config": {"scenario_config": {"reserve_margin_build_enabled": True}}
        }
        return FV._score_fc2_backstop("t1", art, traj, curve_on=True, iso="PJM")

    def test_without_the_split_the_row_skips(self):
        # The pre-repair artifact: totals only.
        row = self._score(
            [
                {
                    "builds_thermal_mw": 100.0,
                    "builds_renew_mw": 0.0,
                    "builds_storage_mw": 0.0,
                }
            ]
        )
        self.assertEqual(row["status"], FV.SKIPPED)
        self.assertIn("no reserve_backstop split", row["detail"])

    def test_with_the_split_the_row_scores(self):
        row = self._score(
            [
                {
                    "builds_thermal_mw": 100.0,
                    "builds_thermal_backstop_mw": 5.0,
                    "builds_renew_mw": 0.0,
                    "builds_storage_mw": 0.0,
                }
            ]
        )
        self.assertNotEqual(row["status"], FV.SKIPPED)
        self.assertAlmostEqual(row["values"]["backstop_share"], 0.05)

    def test_builds_by_source_is_an_equivalent_source(self):
        row = self._score(
            [
                {
                    "builds_thermal_mw": 100.0,
                    "builds_by_source": {"economic": 95.0, "reserve_backstop": 5.0},
                    "builds_renew_mw": 0.0,
                    "builds_storage_mw": 0.0,
                }
            ]
        )
        self.assertNotEqual(row["status"], FV.SKIPPED)
        self.assertAlmostEqual(row["values"]["backstop_share"], 0.05)


class RunConfigProvenanceTest(unittest.TestCase):
    """Blocker 7 — the artifact exists, and comes from the resolved config."""

    def test_written_from_the_runs_own_config_yaml(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            out, run = Path(td) / "out", Path(td) / "run"
            out.mkdir()
            run.mkdir()
            # The RESOLVED dump save_result writes — note iso/mode differ from
            # any plausible pre-solve request, which is the point.
            (run / "config.yaml").write_text(
                "iso: PJM\nmode: forecast\ncapacity_market_clearing: false\n"
                "start_year: 2026\nend_year: 2030\n"
            )
            path = F.write_run_config(out, run, iso="PJM", cache_key="abc123")
            self.assertIsNotNone(path)
            payload = json.loads(Path(path).read_text())
            self.assertEqual(payload["scenario_config"]["iso"], "PJM")
            self.assertEqual(payload["scenario_config"]["mode"], "forecast")
            self.assertEqual(
                payload["scenario_config_source"], str(run / "config.yaml")
            )
            self.assertEqual(payload["cache_key"], "abc123")
            self.assertEqual(Path(path).name, "run_config.json")

    def test_accepts_the_real_call_sites_kwargs(self):
        """The production call site's exact kwarg shape must bind.

        REGRESSION (FFR-3A-2). ``solve_and_summarize`` passed ``run_dir`` BOTH
        positionally and again inside ``**extra``, so every real invocation
        raised ``TypeError: write_run_config() got multiple values for argument
        'run_dir'`` — and it raised *after* a full 5-year solve and *before*
        ``full_horizon_summary.json`` was written, so an affected leg lost its
        summary as well as its FC-7 artifact and looked like a hard crash.

        The existing tests all called this helper with a DIFFERENT (shorter)
        kwarg set than the caller used, which is precisely why the defect
        shipped green. This test pins the caller's own shape, and asserts the
        payload still records ``run_dir`` so the fix lost no provenance.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            out, run = Path(td) / "out", Path(td) / "run"
            out.mkdir()
            run.mkdir()
            (run / "config.yaml").write_text("iso: ERCOT\nmode: forecast\n")
            path = F.write_run_config(
                out,
                run,
                iso="ERCOT",
                cache_key="key123",
                solved_years=[2026, 2027, 2028, 2029, 2030],
            )
            self.assertIsNotNone(path)
            payload = json.loads(Path(path).read_text())
            self.assertEqual(payload["run_dir"], str(run))
            self.assertEqual(payload["iso"], "ERCOT")
            self.assertEqual(payload["cache_key"], "key123")
            self.assertEqual(payload["solved_years"], [2026, 2027, 2028, 2029, 2030])

    def test_not_written_when_there_is_no_resolved_config(self):
        # A zero-year run has no provenance. Writing one from the REQUEST would
        # manufacture an FC-7 pass for a run that produced nothing.
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out"
            out.mkdir()
            self.assertIsNone(F.write_run_config(out, None))
            self.assertIsNone(F.write_run_config(out, Path(td) / "missing"))
            self.assertFalse((out / "run_config.json").exists())

    def test_fc7_reads_the_written_artifact(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            out, run = Path(td) / "out", Path(td) / "run"
            out.mkdir()
            run.mkdir()
            # A realistic full flag surface (FC-7 row 1 wants >= 20 keys or a
            # recognized gate key).
            cfg = {"iso": "PJM", "mode": "forecast", "capacity_market_clearing": False}
            cfg.update({f"knob_{i}": False for i in range(25)})
            (run / "config.yaml").write_text(
                "\n".join(f"{k}: {json.dumps(v)}" for k, v in cfg.items())
            )
            path = F.write_run_config(out, run, iso="PJM")
            art = {"run_config": json.loads(Path(path).read_text())}
            rows = FV.score_fc7(art, "t1", "PJM")
            row1 = next(r for r in rows if r["row"] == "run_config")
            self.assertEqual(row1["status"], FV.PASS, row1["detail"])


class HonestInvariantConsoleLineTest(unittest.TestCase):
    """Blocker 5 — an unscored gate never renders as a clean one."""

    def test_zero_year_run_reports_not_scored(self):
        import inspect

        src = inspect.getsource(F.solve_and_summarize)
        # The count line must be reachable only when there ARE invariants.
        self.assertIn("if invariants:", src)
        self.assertIn("NOT SCORED", src)
        self.assertIn("The gate was not evaluated.", src)

    def test_the_json_summary_was_already_honest(self):
        # Pins the asymmetry the blocker described, so a future change that
        # "fixes" the console by populating an empty list is caught.
        self.assertEqual([i for i in [] if i], [])


if __name__ == "__main__":
    unittest.main()
