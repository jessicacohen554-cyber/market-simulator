"""Cross-year LP warm-start default gate (calibration ON, forecast cold-only).

``MARKET_SIM_WARMSTART_XYEAR`` defaults OFF globally (``pipeline.solve``), and
the calibration CLIs flip it ON via ``resolve_xyear_warmstart_default`` unless
``--no-xyear-warmstart`` is passed or the env var is set explicitly. The
forecast path (``runner.py``) passes ``xyear_cache=None`` and therefore cannot
consume the basis no matter what the env var says — that cold-only invariant is
asserted here so a future edit can't silently wire the new default into the
forecast trajectory (docs/cross-year-warmstart.md "Why the forecast path is not
wired").
"""

from __future__ import annotations

import ast
from pathlib import Path


from scripts.run_calibration import resolve_xyear_warmstart_default

REPO = Path(__file__).resolve().parents[1]


class TestResolveDefault:
    """Precedence: --no-xyear-warmstart > explicit env var > default ON."""

    def test_default_on_when_unset(self, monkeypatch):
        monkeypatch.delenv("MARKET_SIM_WARMSTART_XYEAR", raising=False)
        assert resolve_xyear_warmstart_default(disable=False) is True
        import os

        assert os.environ["MARKET_SIM_WARMSTART_XYEAR"] == "1"

    def test_flag_forces_off_over_default(self, monkeypatch):
        monkeypatch.delenv("MARKET_SIM_WARMSTART_XYEAR", raising=False)
        assert resolve_xyear_warmstart_default(disable=True) is False
        import os

        assert os.environ["MARKET_SIM_WARMSTART_XYEAR"] == "0"

    def test_flag_forces_off_over_explicit_env_on(self, monkeypatch):
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        # --no-xyear-warmstart wins even when the env explicitly asked for ON.
        assert resolve_xyear_warmstart_default(disable=True) is False
        import os

        assert os.environ["MARKET_SIM_WARMSTART_XYEAR"] == "0"

    def test_explicit_env_off_honored(self, monkeypatch):
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "0")
        # An explicit OFF is honored — the default does not override it.
        assert resolve_xyear_warmstart_default(disable=False) is False

    def test_explicit_env_on_honored(self, monkeypatch):
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        assert resolve_xyear_warmstart_default(disable=False) is True


class TestForecastStaysColdOnly:
    """runner.py must pass xyear_cache=None — the forecast can't warm-start."""

    def test_runner_passes_xyear_cache_none_literal(self):
        """Static guard: the runner's per-year solve call pins the cache None.

        The forecast's energy solve now goes through the shared per-year body
        (``pipeline.year.run_year_solve``, which forwards ``xyear_cache``
        verbatim into ``run_energy_solve``). Parses runner.py and asserts every
        ``run_year_solve(...)`` (or residual ``run_energy_solve(...)``) call
        passes ``xyear_cache`` as a literal ``None`` keyword — so the
        calibration default-ON gate can never reach the forecast loop,
        whatever the env var.
        """
        src = (REPO / "src" / "market_sim" / "runner.py").read_text()
        tree = ast.parse(src)
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in ("run_year_solve", "run_energy_solve")
        ]
        assert calls, "no run_year_solve/run_energy_solve call found in runner.py"
        for call in calls:
            kw = {k.arg: k.value for k in call.keywords}
            assert "xyear_cache" in kw, "runner must pin xyear_cache explicitly"
            val = kw["xyear_cache"]
            assert isinstance(val, ast.Constant) and val.value is None, (
                "runner.py must pass xyear_cache=None so the forecast path stays "
                "cold-only (docs/cross-year-warmstart.md)"
            )

    def test_year_body_forwards_xyear_cache_verbatim(self):
        """Static guard: pipeline/year.py forwards its ``xyear_cache`` param.

        The runner-side literal-None guard above is only sound if the shared
        per-year body passes its own ``xyear_cache`` parameter through to
        ``run_energy_solve`` unmodified — assert exactly that.
        """
        src = (REPO / "src" / "market_sim" / "pipeline" / "year.py").read_text()
        tree = ast.parse(src)
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "run_energy_solve"
        ]
        assert calls, "no run_energy_solve call found in pipeline/year.py"
        for call in calls:
            kw = {k.arg: k.value for k in call.keywords}
            assert "xyear_cache" in kw
            val = kw["xyear_cache"]
            assert isinstance(val, ast.Name) and val.id == "xyear_cache", (
                "pipeline/year.py must forward its xyear_cache parameter "
                "verbatim into run_energy_solve"
            )

    def test_none_cache_never_applies_even_with_env_on(self, monkeypatch):
        """Behavioural guard: env ON + None cache → no apply, solve is fine."""
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        from market_sim.pipeline.solve import run_energy_solve
        from tests.test_pipeline_solve import _Cfg, _trivial_inputs

        gens, fa, demand, mc_base, dk = _trivial_inputs()
        got = run_energy_solve(gens, fa, demand, mc_base, dk, _Cfg(), xyear_cache=None)
        assert got.p1.status == "Optimal"
