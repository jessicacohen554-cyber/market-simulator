"""Repro + regression detector for the EIA-860 vintage leak (fast-tier pollution family).

The bisect record (2026-07-27)
------------------------------
The order-dependent fast-tier pollution family (fast-tier-triage-2026-07-26.md
§6.2; path-registry-routing-2026-07.md §5.1's 13-test ``test_storage`` member)
was bisected to ONE mechanism:

* ``config.paths.set_eia860_vintage`` mutates the process-global
  ``_ACTIVE_EIA_860_DIR``, and ``runner.run_scenario_iso`` calls it with the
  scenario's ``eia860_vintage_year`` on every backcast/hindcast solve —
  deliberately leaving the vintage active afterwards (post-solve reporting
  reads the vintage the solve used).
* The minimal polluting pair:
  ``tests/scoring/test_crossover_harness.py::TestCrossoverRunnerPath::
  test_forward_year_demand_not_from_realized_loader`` (a fake-solve hindcast
  ``run_scenario_iso`` with ``eia860_vintage_year=2023``) ahead of ANY test
  that reads eia860-fed data through ``paths.active_eia860_dir()`` with no
  explicit directory. After the polluter, those reads silently resolve to
  ``data/raw/eia-860/vintage_2023/`` instead of the canonical 2025ER snapshot.
* Confirmed victims (each passes alone, fails when paired behind the
  polluter in one process): the ``test_storage`` EIA-860 battery / pumped /
  vintage-ramp family, ``test_fleet``'s planned-additions and
  retired-within-window tests, ``test_outages``'s NEISO floor-outage-exempt
  test, ``test_coal_sync_tranche``'s scope-set freeze, and
  ``test_derive_coal_sigmoid``'s MISO provenance freeze. Membership flapped
  run-to-run because xdist workers are separate processes: a victim fails
  iff it lands on the polluter's worker after it, with no intervening
  ``run_scenario_iso`` whose config carries ``eia860_vintage_year=None``
  (which resets the global) — exactly the coin toss the triage observed.
  (``test_cache_control``'s largest-retained-frames flap did NOT reproduce
  with this polluter — GC-graph ambient state, a separate open observation.)

The fix is at the leak, not the schedule:
``tests/conftest.py::_reset_eia860_vintage`` resets the global after every
test (landed independently by the fast-tier-escalation lane, PR #2970, whose
own bisect converged on the same polluter), and the polluting test also
resets it via ``addCleanup`` (landed with this script) so the file stays
hermetic under bare ``unittest``. The same lane closed the
``test_cache_control`` flap noted above — a legitimately cached frame plus an
assertion that assumed process-global frame state; fixed at the assertion.

What this script does
---------------------
1. Demonstrates the raw mechanism in-process (no pytest involved):
   ``set_eia860_vintage(2023)`` flips ``active_eia860_dir()`` to the vintage
   directory for every subsequent implicit-path eia860 read.
2. Runs the minimal polluting pair through pytest in a subprocess and reports
   whether the leak is CONTAINED (victims green behind the polluter) or LIVE
   (victims red). Exit code 1 on a live leak, so this doubles as a standing
   regression detector for the guard fixture.

Usage::

    python scripts/diagnostics/repro_eia860_vintage_leak.py          # fast pair
    python scripts/diagnostics/repro_eia860_vintage_leak.py --full   # all victims
"""

from __future__ import annotations

import argparse
import subprocess
import sys

from market_sim.config.paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))

POLLUTER = (
    "tests/scoring/test_crossover_harness.py::TestCrossoverRunnerPath::"
    "test_forward_year_demand_not_from_realized_loader"
)

#: Fastest confirmed victim (0.1 s alone) — the default pair partner.
FAST_VICTIM = (
    "tests/unit/data/test_coal_sync_tranche.py::TestCommittedTakeorpayRegulated::"
    "test_scope_set_membership_freeze"
)

#: The full confirmed-victim set (--full), for a comprehensive re-check.
FULL_VICTIMS = (
    FAST_VICTIM,
    "tests/unit/model/test_storage.py::TestEIA860CAISOBatteryFleet",
    "tests/unit/model/test_storage.py::TestEIA860NYISOBatteryFleet",
    "tests/unit/model/test_storage.py::TestEIA860NEISOBatteryFleet",
    "tests/unit/model/test_storage.py::TestEIA860PumpedStorage",
    "tests/unit/model/test_storage.py::TestStorageVintageRamp",
    "tests/unit/data/test_fleet.py::TestLoadPlannedAdditions::test_ercot_planned_units",
    "tests/unit/data/test_fleet.py::TestLoadRetiredWithinWindow",
    "tests/unit/data/test_outages.py::NEISOFloorOutageExemptTest",
    "tests/curation/test_derive_coal_sigmoid.py::TestProvenanceFreeze::"
    "test_miso_defaults_match_derive",
)


def demonstrate_mechanism() -> None:
    """Show the raw global flip (and restore it) without touching pytest."""
    from market_sim.config import paths

    prior = paths._ACTIVE_EIA_860_DIR
    canonical = paths.active_eia860_dir()
    try:
        flipped = paths.set_eia860_vintage(2023)
        print(f"canonical active_eia860_dir : {canonical}")
        print(f"after set_eia860_vintage(2023): {flipped}")
        if flipped == canonical:
            print("  (vintage_2023/ not present on this checkout — flip is a no-op)")
        else:
            print("  -> every implicit-path eia860 read in this process now resolves")
            print("     to the vintage tree until something calls set_eia860_vintage")
            print("     again. This is the whole leak.")
    finally:
        paths._ACTIVE_EIA_860_DIR = prior


def run_pair(victims: tuple[str, ...]) -> int:
    """Run [polluter, *victims] in one pytest process; return the exit code."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        POLLUTER,
        *victims,
    ]
    print(f"\nrunning polluting pair ({len(victims)} victim node(s)) ...")
    proc = subprocess.run(cmd, cwd=REPO_ROOT)
    return proc.returncode


def main() -> int:
    """CLI entry: demonstrate the mechanism, then detect the leak."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--full",
        action="store_true",
        help="run the polluter against the full confirmed-victim set "
        "(several minutes) instead of the fastest single victim",
    )
    args = parser.parse_args()

    demonstrate_mechanism()
    rc = run_pair(FULL_VICTIMS if args.full else (FAST_VICTIM,))
    if rc == 0:
        print(
            "\nLEAK CONTAINED: victims stay green behind the polluter "
            "(the conftest vintage guard is doing its job)."
        )
        return 0
    print(
        "\nLEAK LIVE: victims fail behind the polluter — the "
        "_reset_eia860_vintage guard (tests/conftest.py) is missing or "
        "broken, or a new unguarded vintage mutation exists."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
