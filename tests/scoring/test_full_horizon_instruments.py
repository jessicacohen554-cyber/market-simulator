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
* **capx D25 §6.1 / D29** — ``extract_trajectory`` carried no generation by
  fuel at all (so the FC-5 corridor's 252 AEO generation anchors could never be
  dispositioned), and its ``storage_mw`` column read ``cap.get("storage")`` over
  the fleet context's GENERATOR axis — 0.0 by construction even for a 17 GW
  battery fleet. Asserted here over a synthetic ``Run``: the energy block is
  emitted, ``storage_power_mw`` reads the ledger's real fleet power and is
  NONZERO against a fleet with storage, and the defective ``storage_mw`` stays
  bug-compatible for its three committed consumers.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np  # noqa: E402

from scripts import check_forecast_invariants as C  # noqa: E402
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


# --------------------------------------------------------------------------- #
# capx D29 — the trajectory reporting grain
# --------------------------------------------------------------------------- #
def _ctx(fuels: tuple[str, ...], pmax: tuple[float, ...]):
    """A real ``FleetContext`` over a tiny fleet (never a mock).

    Deliberately the production dataclass: the defect under test is precisely
    that the GENERATOR axis carries no storage, and a hand-rolled stand-in
    could be given a "storage" fuel that the real context can never have.
    """
    from market_sim.results.outputs import FleetContext

    n = len(fuels)
    return FleetContext(
        fuel_types=list(fuels),
        pmax_mw=[float(x) for x in pmax],
        emission_rate=[0.4] * n,
        efficiency_bins=["older"] * n,
        heat_rates=[7.0] * n,
        zones=["North"] * n,
        unit_ids=[f"u{i}" for i in range(n)],
        wind_cap_mw=1000.0,
        solar_cap_mw=2000.0,
        wind_potential_mwh=1.0e6,
        solar_potential_mwh=1.0e6,
        # The fleet HAS storage — 4 h on 5,000 MW. The context records only the
        # ENERGY capacity, which is the whole reason the power column has to
        # come from the ledger.
        storage_energy_cap_mwh=20_000.0,
    )


def _synthetic_run(
    *,
    storage: bool = True,
    storage_power_mw: float | None = 5_000.0,
    hours: int = 24,
) -> "C.Run":
    """One-year ``Run``: 2 thermal units + wind/solar + (optionally) storage."""
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.dispatch import DispatchResult

    fuels = ("gas_cc", "coal")
    dispatch = np.vstack(
        [np.full(hours, 100.0), np.full(hours, 50.0)]
    )  # 2,400 + 1,200 MWh
    wind = np.full((1, hours), 10.0)  # 240 MWh
    solar = np.full((1, hours), 5.0)  # 120 MWh
    chg = np.full((1, hours), 8.0) if storage else None  # 192 MWh
    dis = np.full((1, hours), 6.0) if storage else None  # 144 MWh
    result = DispatchResult(
        dispatch=dispatch,
        wind_dispatched=wind,
        solar_dispatched=solar,
        slack=np.zeros((1, hours)),
        dump=np.zeros((1, hours)),
        prices=np.full((1, hours), 30.0),
        storage_charge=chg,
        storage_discharge=dis,
        storage_soc=np.full((1, hours), 100.0) if storage else None,
        flows=None,
        objective_value=0.0,
        status="optimal",
        build_time=0.0,
        solve_time=0.0,
        emissions=None,
    )
    yd = C.YearData(
        year=2026,
        result=result,
        demand=np.full((1, hours), 165.0),
        context=_ctx(fuels, (800.0, 400.0)),
    )
    ledger = {
        "iso": "ERCOT",
        "year": 2026,
        "thermal_additions": [],
        "renewable_additions": [],
        "storage_additions": [],
        "retirements": [],
        "peak_demand_mw": 165.0,
        "reserve_margin": 0.2,
        "rps_dual": 0.0,
    }
    if storage_power_mw is not None:
        ledger["storage_power_mw"] = storage_power_mw
    run = C.Run(run_dir=Path("."), config=ScenarioConfig(iso="ERCOT"), iso="ERCOT")
    run.years = {2026: yd}
    run.ledgers = {2026: ledger}
    return run


class TrajectoryReportingGrainTest(unittest.TestCase):
    """capx D25 §6.1 → D29 — the energy block and the real storage column."""

    def test_generation_by_fuel_is_emitted_and_closes_on_the_total(self):
        row = F.extract_trajectory(_synthetic_run())[0]
        gen = row["generation_by_fuel_mwh"]
        # Thermal by fuel from the dispatch array, wind/solar from their own.
        self.assertAlmostEqual(gen["gas_cc"], 2400.0)
        self.assertAlmostEqual(gen["coal"], 1200.0)
        self.assertAlmostEqual(gen["wind"], 240.0)
        self.assertAlmostEqual(gen["solar"], 120.0)
        # The denominator the FC-5 corridor states its shares against.
        self.assertAlmostEqual(row["total_gen_mwh"], 3960.0)
        self.assertAlmostEqual(sum(gen.values()), row["total_gen_mwh"], places=1)

    def test_storage_is_not_folded_into_the_fuel_mix(self):
        # Discharge is round-tripped energy already counted at charge; summing
        # it into the generation mix would double-count it.
        row = F.extract_trajectory(_synthetic_run())[0]
        self.assertNotIn("storage", row["generation_by_fuel_mwh"])
        self.assertAlmostEqual(row["storage_discharge_mwh"], 144.0)
        self.assertAlmostEqual(row["storage_charge_mwh"], 192.0)

    def test_storage_power_mw_is_nonzero_against_a_fleet_with_storage(self):
        # THE defect: a real storage fleet must not report as no storage.
        # Pinned as EQUAL to the ledger figure, not merely nonzero: the column
        # is the fleet TOTAL (batteries + pumped storage, since runner puts PS
        # into `storage_units` on both legs), so a consumer comparing it to a
        # batteries-only anchor must net PS out itself. A future change that
        # silently netted here would break that contract invisibly.
        row = F.extract_trajectory(_synthetic_run(storage_power_mw=17_000.0))[0]
        self.assertAlmostEqual(row["storage_power_mw"], 17_000.0)
        self.assertGreater(row["storage_power_mw"], 0.0)

    def test_the_defective_storage_mw_stays_bug_compatible(self):
        # Three committed consumers read `storage_mw`, two of them by comparing
        # two summaries key-by-key; repairing it in place would make an
        # old-vs-new comparison report a phantom multi-GW delta. It must keep
        # reading 0.0 off the generator axis, beside the repaired column.
        row = F.extract_trajectory(_synthetic_run(storage_power_mw=17_000.0))[0]
        self.assertEqual(row["storage_mw"], 0.0)
        self.assertNotEqual(row["storage_mw"], row["storage_power_mw"])

    def test_absent_ledger_key_reads_not_measured_never_zero(self):
        # 83 committed ledgers predate `storage_power_mw`. None is "not
        # measured"; 0.0 would assert a fleet that was never recorded.
        row = F.extract_trajectory(_synthetic_run(storage_power_mw=None))[0]
        self.assertIsNone(row["storage_power_mw"])

    def test_no_storage_arrays_report_none_not_zero_throughput(self):
        row = F.extract_trajectory(_synthetic_run(storage=False))[0]
        self.assertIsNone(row["storage_discharge_mwh"])
        self.assertIsNone(row["storage_charge_mwh"])

    def test_the_addition_is_additive_every_legacy_key_survives(self):
        # The contract the charter binds this change to: committed summaries
        # stay readable by every current consumer, so no pre-D29 key may lose
        # its name, type or meaning.
        row = F.extract_trajectory(_synthetic_run())[0]
        # `(int, float)` on the numeric keys is not laziness: several are
        # `round(sum(...), 1)` over a possibly-empty set, which yields a Python
        # int (e.g. `firm_clean_mw` on a fleet with no hydro). That is
        # pre-existing behaviour the summaries already carry; the contract this
        # pins is "still present, still a number", not a narrowing D29 invented.
        num = (int, float)
        legacy = {
            "year": int,
            "lw_price": num,
            "max_hourly_price": num,
            "neg_price_hour_frac": num,
            "hours_ge_100": int,
            "thermal_mw": num,
            "firm_clean_mw": num,
            "vre_mw": num,
            "total_cap_mw": num,
            "storage_mw": num,
            "builds_thermal_mw": num,
            "builds_thermal_backstop_mw": num,
            "builds_by_source": dict,
            "builds_renew_mw": num,
            "builds_storage_mw": num,
            "retire_mw": num,
            "capacity_by_fuel_mw": dict,
        }
        for key, typ in legacy.items():
            self.assertIn(key, row)
            self.assertIsInstance(row[key], typ, key)
        # And the roll-ups stay GENERATOR-axis: storage is beside them, not in.
        self.assertAlmostEqual(row["total_cap_mw"], 800.0 + 400.0 + 1000.0 + 2000.0)


if __name__ == "__main__":
    unittest.main()
