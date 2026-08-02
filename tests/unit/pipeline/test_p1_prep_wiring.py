"""Every orchestrator that solves must reach every P1-native commitment bridge.

There are THREE call sites of :func:`pipeline.solve.run_energy_solve`, not two:

* ``src/market_sim/pipeline/year.py``   — the shared per-year solve core,
* ``src/market_sim/runner.py``          — the forecast orchestrator,
* ``scripts/run_calibration.py``        — the BACKCAST orchestrator, which is
  what every calibration arm and keeper actually runs.

Each maintains its own ``p1_fleet_prep=`` chain. A bridge wired into only some
of them is silently inert in the others: the flag is accepted, the run_config
records it as armed, the solve completes, and the mechanism never fires — a
failure mode with no error and no log line, which reads as "the mechanism did
nothing" rather than "the mechanism was not connected". That happened to the
NYISO bridge during nyiso-87 (wired into ``pipeline/year.py`` and ``runner.py``
but not the backcast orchestrator, so two arms solved without it).

These tests are deliberately source-level. The alternative — driving a real
solve per orchestrator per bridge — costs minutes of LP time to assert a
one-line wiring fact, and the thing that broke was literally a missing name in
an expression.
"""

import ast
import unittest
from pathlib import Path

from tests.helpers import REPO_ROOT

# Every P1-native commitment-bridge builder, and the local name each
# orchestrator binds its result to. A new bridge adds one row here and is then
# required in all three orchestrators.
_BRIDGE_BUILDERS: dict[str, str] = {
    "build_caiso_ra_p1_prep": "ra_p1_prep",
    "build_ercot_gas_bridge_p1_preps": "ercot_bridge_prep",
    "build_nyiso_gas_bridge_p1_prep": "nyiso_bridge_prep",
    # miso-113: absent from this roster, the MISO night floor repeated the
    # exact nyiso-87 failure mode this file exists to prevent — wired into
    # pipeline/year.py and runner.py but not the backcast orchestrator, so the
    # first arm solved byte-identical to its control with the flag armed.
    "build_miso_coal_night_floor_p1_prep": "miso_night_floor_prep",
}

_ORCHESTRATORS: tuple[str, ...] = (
    "src/market_sim/pipeline/year.py",
    "src/market_sim/runner.py",
    "scripts/run_calibration.py",
)


def _p1_fleet_prep_sources(tree: ast.AST) -> list[str]:
    """Return the source of every ``p1_fleet_prep=`` keyword expression."""
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg == "p1_fleet_prep":
                out.append(ast.unparse(kw.value))
    return out


class TestP1PrepWiring(unittest.TestCase):
    """Each orchestrator imports and USES every bridge builder."""

    def _tree(self, rel: str) -> tuple[ast.AST, str]:
        path = Path(REPO_ROOT) / rel
        src = path.read_text()
        return ast.parse(src), src

    def test_every_orchestrator_imports_every_bridge_builder(self):
        for rel in _ORCHESTRATORS:
            tree, _ = self._tree(rel)
            imported = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
                for alias in node.names
            }
            for builder in _BRIDGE_BUILDERS:
                self.assertIn(
                    builder,
                    imported,
                    msg=f"{rel} does not import {builder} — the bridge cannot fire there",
                )

    def test_every_orchestrator_calls_every_bridge_builder(self):
        for rel in _ORCHESTRATORS:
            tree, _ = self._tree(rel)
            called = {
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            }
            for builder in _BRIDGE_BUILDERS:
                self.assertIn(
                    builder,
                    called,
                    msg=f"{rel} imports but never calls {builder}",
                )

    def test_every_prep_reaches_the_p1_fleet_prep_chain(self):
        for rel in _ORCHESTRATORS:
            tree, _ = self._tree(rel)
            chains = _p1_fleet_prep_sources(tree)
            self.assertTrue(chains, msg=f"{rel} passes no p1_fleet_prep at all")
            joined = " ".join(chains)
            for builder, local in _BRIDGE_BUILDERS.items():
                self.assertIn(
                    local,
                    joined,
                    msg=(
                        f"{rel}: {builder}'s result ({local}) never reaches a "
                        "p1_fleet_prep= chain, so the bridge is silently inert "
                        "there — the nyiso-87 failure mode"
                    ),
                )

    def test_run_energy_solve_call_sites_are_the_known_three(self):
        """A NEW call site must be added to _ORCHESTRATORS, not left unwired."""
        found = []
        for path in list((Path(REPO_ROOT) / "src").rglob("*.py")) + [
            Path(REPO_ROOT) / "scripts" / "run_calibration.py",
            Path(REPO_ROOT) / "scripts" / "run_calibration_full.py",
        ]:
            try:
                tree = ast.parse(path.read_text())
            except (SyntaxError, OSError):
                continue
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "run_energy_solve"
                ):
                    found.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(
            sorted(set(found)),
            sorted(_ORCHESTRATORS),
            msg=(
                "run_energy_solve call sites changed. Every site owns its own "
                "p1_fleet_prep chain, so a new one must be added to "
                "_ORCHESTRATORS here and wired to every bridge builder."
            ),
        )


if __name__ == "__main__":
    unittest.main()
