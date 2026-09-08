"""The clean-tier / mass-cap duals reach ``full_horizon_summary.json`` (SCN-FIX3 item 3).

Trivial-first and LP-free: every case builds a one-year synthetic ``Run`` and
reads ``run_full_horizon.extract_trajectory``, never a solve.

**The defect.** ``clean_region_duals`` and ``co2_cap_price`` were written only to
the cached year bundle (``results/<ISO>/<key>/``, gitignored) and the solver log.
The slim summary carried ``rps_dual`` alone and the registry sidecar carried
neither, so under owner ruling **S16** — each campaign shard's bundles die with
its container — a policy campaign's duals were unrecoverable from its COMMITTED
artifacts and the dual limbs of gates G4 and G7 were unscorable at the
coordinator by construction. Reported by ``SCN-WS5A-POLICY-NYISO`` §9 item 4.

**The contract these tests pin**, all of it additive:

* both keys ride the trajectory row beside ``rps_dual``;
* a missing dual is ``None``, **NEVER** ``0.0`` and never ``[]`` — a zero dual
  (the row is slack) and an unrecorded dual (nothing was measured) are different
  facts, and the invariant checker reads ``rps_dual`` by ``is not None``;
* a ZERO dual is still recorded, as ``0.0``, so the two cases stay separable;
* a year restored from an older cached bundle, whose ``DispatchResult`` may not
  carry the attributes at all, reports "not measured" rather than raising;
* every pre-existing trajectory key keeps its name and meaning, and a summary
  written before this change stays readable — the keys are simply absent, which
  every consumer must treat exactly as ``None``.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np  # noqa: E402

from scripts import check_forecast_invariants as C  # noqa: E402
from scripts import run_full_horizon as F  # noqa: E402

#: Keys the trajectory carried BEFORE this change. Guards the additive promise:
#: the repair may only add, so every one of these must survive unchanged.
LEGACY_KEYS = (
    "year",
    "lw_price",
    "max_hourly_price",
    "co2_mt",
    "peak_demand_mw",
    "reserve_margin",
    "rps_dual",
    "thermal_mw",
    "firm_clean_mw",
    "vre_mw",
    "total_cap_mw",
)

HOURS = 24


def _run(
    *,
    clean_region_duals: object = None,
    co2_cap_price: object = None,
) -> "C.Run":
    """One-year ``Run`` carrying the requested duals; ``context=None`` (trivial)."""
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.dispatch import DispatchResult

    result = DispatchResult(
        dispatch=np.full((1, HOURS), 100.0),
        wind_dispatched=None,
        solar_dispatched=None,
        slack=np.zeros((1, HOURS)),
        dump=np.zeros((1, HOURS)),
        prices=np.full((1, HOURS), 30.0),
        storage_charge=None,
        storage_discharge=None,
        storage_soc=None,
        flows=None,
        objective_value=0.0,
        status="optimal",
        build_time=0.0,
        solve_time=0.0,
        emissions=None,
        clean_region_duals=clean_region_duals,
        co2_cap_price=co2_cap_price,
    )
    yd = C.YearData(
        year=2026,
        result=result,
        demand=np.full((1, HOURS), 100.0),
        context=None,
    )
    run = C.Run(run_dir=Path("."), config=ScenarioConfig(iso="ERCOT"), iso="ERCOT")
    run.years = {2026: yd}
    run.ledgers = {2026: {"iso": "ERCOT", "year": 2026, "rps_dual": 0.0}}
    return run


def _row(**kw) -> dict:
    return F.extract_trajectory(_run(**kw))[0]


class PolicyDualsReachTheSummaryTest(unittest.TestCase):
    """The two duals ride the trajectory row, beside ``rps_dual``."""

    def test_clean_region_duals_are_emitted_as_a_list(self) -> None:
        row = _row(clean_region_duals=np.array([12.5, 0.0, 3.25]))
        self.assertEqual(row["clean_region_duals"], [12.5, 0.0, 3.25])

    def test_co2_cap_price_is_emitted_as_a_list(self) -> None:
        row = _row(co2_cap_price=[41.75])
        self.assertEqual(row["co2_cap_price"], [41.75])

    def test_both_sit_beside_rps_dual(self) -> None:
        row = _row(clean_region_duals=np.array([1.0]), co2_cap_price=[2.0])
        for key in ("rps_dual", "clean_region_duals", "co2_cap_price"):
            self.assertIn(key, row)

    def test_values_survive_the_json_round_trip(self) -> None:
        # The summary is written as JSON, so a numpy scalar leaking through
        # would break the artifact rather than this assertion.
        row = _row(clean_region_duals=np.array([7.5]), co2_cap_price=[1.5])
        again = json.loads(json.dumps(row))
        self.assertEqual(again["clean_region_duals"], [7.5])
        self.assertEqual(again["co2_cap_price"], [1.5])


class MissingIsNullNeverZeroTest(unittest.TestCase):
    """An unrecorded dual and a zero dual are different facts, and stay so."""

    def test_absent_families_record_none(self) -> None:
        row = _row()
        self.assertIsNone(row["clean_region_duals"])
        self.assertIsNone(row["co2_cap_price"])

    def test_absent_is_not_zero_and_not_empty(self) -> None:
        row = _row()
        for key in ("clean_region_duals", "co2_cap_price"):
            self.assertNotEqual(row[key], 0.0, f"{key} must not be 0.0 when absent")
            self.assertNotEqual(row[key], [], f"{key} must not be [] when absent")

    def test_a_zero_dual_is_recorded_not_dropped(self) -> None:
        # The row exists and priced at zero (slack) -- that is a MEASUREMENT.
        row = _row(clean_region_duals=np.array([0.0]), co2_cap_price=[0.0])
        self.assertEqual(row["clean_region_duals"], [0.0])
        self.assertEqual(row["co2_cap_price"], [0.0])
        self.assertIsNotNone(row["clean_region_duals"])
        self.assertIsNotNone(row["co2_cap_price"])

    def test_is_not_none_separates_the_two_cases(self) -> None:
        # The contract every consumer of `rps_dual` already uses.
        measured = _row(clean_region_duals=np.array([0.0]))
        unmeasured = _row()
        self.assertTrue(measured["clean_region_duals"] is not None)
        self.assertTrue(unmeasured["clean_region_duals"] is None)


class BackwardCompatibilityTest(unittest.TestCase):
    """Older bundles and older summaries stay readable."""

    def test_a_result_lacking_the_attributes_reads_as_not_measured(self) -> None:
        # A `DispatchResult` restored from a bundle written before the fields
        # existed. Deleting the dataclass attribute does NOT reproduce this
        # (it falls back to the class default), so the stand-in is an object
        # that genuinely never had them -- which is what `getattr` guards.
        stub = SimpleNamespace(prices=np.zeros((1, HOURS)))
        self.assertFalse(hasattr(stub, "clean_region_duals"))
        self.assertFalse(hasattr(stub, "co2_cap_price"))
        yd = SimpleNamespace(result=stub)
        self.assertEqual(F._policy_duals(yd), (None, None))

    def test_a_year_without_a_result_reads_as_not_measured(self) -> None:
        self.assertEqual(F._policy_duals(SimpleNamespace(result=None)), (None, None))

    def test_every_legacy_key_survives(self) -> None:
        row = _row(clean_region_duals=np.array([1.0]))
        missing = [k for k in LEGACY_KEYS if k not in row]
        self.assertEqual(missing, [], f"additive change dropped keys: {missing}")

    def test_a_pre_change_summary_reads_as_not_measured(self) -> None:
        # The 63 Stage-A legs and every earlier forecast bundle predate the
        # keys entirely; a consumer must read an ABSENT key exactly as `None`.
        legacy_row = {"year": 2026, "rps_dual": 0.0}
        self.assertIsNone(legacy_row.get("clean_region_duals"))
        self.assertIsNone(legacy_row.get("co2_cap_price"))


if __name__ == "__main__":
    unittest.main()
