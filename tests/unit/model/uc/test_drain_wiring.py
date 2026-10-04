"""Both persisting orchestrators drain the UC artifacts into the bundle (source-level).

The two regions UC-DESK granted lane UC-1 (review of DESIGN b974d2c9, point
3): ``scripts/run_calibration_full.py`` (the hourly-sidecar block) and
``src/market_sim/runner.py`` (the forecast result write). Each carries the
two-line drain ``take_uc_artifacts`` → ``write_uc_artifacts`` under the
``unit_commitment_milp`` gate, so the sidecars land in the bundle (rule 34)
and the gate-off path runs no statement. Source-level, like
``test_p1_prep_wiring.py``: the thing that would break is a missing call.
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.helpers import REPO_ROOT

_ORCHESTRATORS = ("scripts/run_calibration_full.py", "src/market_sim/runner.py")


def _calls(tree: ast.AST) -> set[str]:
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            out.add(f.id if isinstance(f, ast.Name) else getattr(f, "attr", ""))
    return out


def test_both_orchestrators_write_the_uc_artifacts_under_the_gate():
    for rel in _ORCHESTRATORS:
        src = (Path(REPO_ROOT) / rel).read_text()
        tree = ast.parse(src)
        called = _calls(tree)
        assert "take_uc_artifacts" in called and "write_uc_artifacts" in called, rel
        # the drain sits under an `if ... unit_commitment_milp` test
        gated = any(
            isinstance(n, ast.If)
            and "unit_commitment_milp" in ast.unparse(n.test)
            and "write_uc_artifacts" in ast.unparse(n)
            for n in ast.walk(tree)
        )
        assert gated, f"{rel}: the UC drain is not gated on unit_commitment_milp"
