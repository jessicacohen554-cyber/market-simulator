"""Pins that the IRA §45U credit is structurally unreachable in a backcast.

The F1-45U charter (docs/handoffs/f1-45u-ordering-2026-08-08.md) changes the
§45U credit curve, and the claim that no backcast keeper metric can move
rests on a reachability argument, not on a measured re-solve:

  1. ``policy.ira.section_45u_credit_per_mwh`` has exactly ONE production
     call site -- ``apply_economic_retirements`` in
     ``model/capacity_evolution/retirements.py``.
  2. ``apply_economic_retirements`` runs only inside ``evolve_fleet``.
  3. ``evolve_fleet`` has exactly ONE call site in the whole repo:
     ``runner.py::run_scenario_iso``, the forecast-scenario path.
  4. A backcast solve never enters ``run_scenario_iso``. It reaches the LP
     through ``scripts/run_calibration.py::run_year`` and
     ``pipeline.solve.run_energy_solve`` -- independently established and
     documented at ``run_calibration.py`` ("WHY THIS CALL SITE EXISTS
     (caiso-162): the mechanism was previously wired ONLY into
     runner.py::run_scenario_iso ... so a BACKCAST solve, which reaches the
     LP through this module and pipeline.solve.run_energy_solve, silently
     ignored the flag").

This test pins links 1 and 3, the two that a future refactor could break
silently. If it fails, the backcast-inertness argument no longer holds and
any §45U change needs a measured backcast re-solve before it can land.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _call_sites(symbol: str, roots: tuple[str, ...]) -> list[str]:
    """Return the repo-relative file of every call of ``symbol``, with repeats.

    Definitions, imports and comment mentions are excluded -- only actual
    ``symbol(`` invocations count. Files, not line numbers, so that editing
    unrelated lines above a call site cannot fail this test.

    Args:
        symbol: Function name to search for.
        roots: Repo-relative directories to scan.

    Returns:
        Sorted repo-relative path strings, one entry per call site.
    """
    pattern = re.compile(rf"(?<![\w.]){re.escape(symbol)}\s*\(")
    hits: list[str] = []
    for root in roots:
        for path in sorted((_REPO_ROOT / root).rglob("*.py")):
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith(("#", "def ", "async def ", "from ", "import ")):
                    continue
                if pattern.search(stripped):
                    hits.append(str(path.relative_to(_REPO_ROOT)))
    return sorted(hits)


class TestSection45UBackcastInertness(unittest.TestCase):
    """The §45U -> evolve_fleet -> runner chain has no backcast branch."""

    def test_45u_is_called_from_exactly_one_production_module(self):
        # scripts/probes is the calibration record, not production, and the
        # F1-45U stage-1 probe calls the function directly by design.
        #
        # DISTINCT MODULES, not raw call count (F2-45U). The reachability
        # argument in this module's docstring is about which MODULE can reach
        # §45U -- link 1 fails only if some OTHER module gains a call, which is
        # exactly what a set of files pins. Owner decision D-28 gave the
        # retirement screen TWO calls inside the one function
        # ``apply_economic_retirements``: §45U(b)(2)(B) has two branches with
        # two different gross-receipts bases (the state-contract branch (iii)
        # excludes the attribute payment, the compliance-certificate branch (i)
        # includes it), so both are evaluated and the unit takes the better
        # route. Two calls in the same already-forecast-only function weaken
        # nothing -- link 2 (only ``evolve_fleet`` runs it) and link 3 (only
        # ``runner.py`` calls that) are untouched, and link 3 is pinned below.
        sites = {
            s
            for s in _call_sites("section_45u_credit_per_mwh", ("src",))
            if "probes/" not in s
        }
        self.assertEqual(
            sites,
            {"src/market_sim/model/capacity_evolution/retirements.py"},
            "§45U gained a call site in a new module -- re-verify backcast inertness",
        )

    def test_evolve_fleet_is_called_only_from_the_forecast_runner(self):
        sites = _call_sites("evolve_fleet", ("src", "scripts"))
        self.assertEqual(
            sites,
            ["src/market_sim/runner.py"],
            "capacity evolution gained a call site -- a backcast lane may now "
            "reach the retirement screen, and with it §45U",
        )


if __name__ == "__main__":
    unittest.main()
