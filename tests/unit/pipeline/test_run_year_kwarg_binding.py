"""Every ``run_year(...)`` keyword the solve path passes must be a ``run_year`` parameter.

**The incident this guard exists for (2026-09-12, lane SPP-36).** Commit ``3497a1d8``
added ``unit_outage_window_hour_grain`` to ``ScenarioConfig`` and to
``run_calibration_full.solve_and_persist``'s **unconditional** ``run_year(...)``
call, but never to ``run_year`` itself, which lives in the *other* runner
(``scripts/run_calibration.py``) and accepts **no** ``**kwargs``. The result was a
``TypeError: run_year() got an unexpected keyword argument
'unit_outage_window_hour_grain'`` raised on **every** invocation, for every ISO
and every year, before any LP work — so both production entry points
(``run_calibration_full.main`` and ``replay_keeper.main``) were dead at HEAD. The
introducing commit shipped its own feature test
(``tests/unit/data/test_unit_outage_window_hour_grain.py``, 15 cases, all green)
and none of them called the solve path, so nothing caught it. Found by an SPP-36
span shard, which stopped and reported instead of patching.

Why an AST test rather than a call. ``run_year`` binds ~300 keyword arguments
across two 7-to-14-thousand-line runner modules that no unit test can invoke
cheaply — a solve is minutes of LP. The failure mode is purely a **signature
binding** one, and that is statically decidable: parse both modules, collect the
keywords at every ``run_year`` call site, and require each to be a declared
parameter. Stdlib only (``ast``), no import of either runner, milliseconds.

This is the rule 19 ``[R-ONE-MECH]`` discipline applied to plumbing: a flag added
to the caller and not the callee is not a half-wired feature, it is a broken
production path.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
CALLEE = REPO / "scripts" / "run_calibration.py"
CALLERS = (
    REPO / "scripts" / "run_calibration.py",
    REPO / "scripts" / "run_calibration_full.py",
)


def _run_year_def() -> ast.FunctionDef:
    """Return the single ``run_year`` definition, or fail loudly."""
    tree = ast.parse(CALLEE.read_text(encoding="utf-8"))
    defs = [
        n
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "run_year"
    ]
    assert len(defs) == 1, f"expected exactly one run_year def, found {len(defs)}"
    return defs[0]


def _accepted(fn: ast.FunctionDef) -> set[str]:
    """Return the parameter names ``fn`` accepts by keyword."""
    return {a.arg for a in fn.args.args} | {a.arg for a in fn.args.kwonlyargs}


def _call_sites() -> list[tuple[Path, ast.Call]]:
    """Return every literal ``run_year(...)`` call in the runner modules."""
    out: list[tuple[Path, ast.Call]] = []
    for path in CALLERS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "run_year"
            ):
                out.append((path, node))
    return out


def test_run_year_has_no_kwargs_catchall() -> None:
    """``run_year`` must keep binding by name — a ``**kwargs`` would hide this class of bug."""
    fn = _run_year_def()
    assert fn.args.kwarg is None, (
        "run_year grew a **kwargs catch-all. That silently swallows a misspelled or "
        "unwired flag instead of failing at the call, which is exactly the defect "
        "this guard exists to catch (lane SPP-36, 2026-09-12)."
    )


def test_run_year_call_sites_exist() -> None:
    """Fail if the call sites move, rather than passing vacuously."""
    sites = _call_sites()
    assert sites, (
        "no literal run_year(...) call found in either runner — this guard has gone "
        "vacuous; re-point CALLERS at wherever the solve path now calls it."
    )


@pytest.mark.parametrize(
    "path,call", _call_sites(), ids=lambda v: getattr(v, "name", "")
)
def test_every_run_year_kwarg_is_accepted(path: Path, call: ast.Call) -> None:
    """Every keyword passed to ``run_year`` is a parameter ``run_year`` declares."""
    accepted = _accepted(_run_year_def())
    passed = {k.arg for k in call.keywords if k.arg is not None}
    unbound = sorted(passed - accepted)
    assert not unbound, (
        f"{path.name}:{call.lineno} passes {len(unbound)} keyword(s) that "
        f"run_year (scripts/run_calibration.py) does not accept: {unbound}. "
        "run_year takes no **kwargs, so this is a TypeError on EVERY solve, for "
        "every ISO and every year — a dead production path, not a partial feature. "
        "Add the parameter to run_year AND thread it to the config the way its "
        "siblings are (the `if <flag> is not None: config = config.with_overrides(...)` "
        "block), or stop passing it."
    )
