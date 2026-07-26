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
    """The forecast's cross-year gate is the config field, never the env var."""

    def test_runner_gates_xyear_on_the_config_field(self):
        """Static guard: the runner's per-year solve call pins BOTH keywords.

        The forecast's energy solve now goes through the shared per-year body
        (``pipeline.year.run_year_solve``, which forwards ``xyear_cache``
        verbatim into ``run_energy_solve``). Parses runner.py and asserts every
        ``run_year_solve(...)`` (or residual ``run_energy_solve(...)``) call
        passes an explicit ``xyear_warmstart=config.forecast_xyear_warmstart``
        alongside its ``xyear_cache`` — so the forecast's cross-year behavior is
        the registry field (rule 24 [R-REGISTRY], owner decision D-9) and the
        calibration CLIs' default-ON ``MARKET_SIM_WARMSTART_XYEAR`` can never
        reach the forecast loop.
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
            gate = kw.get("xyear_warmstart")
            assert (
                isinstance(gate, ast.Attribute)
                and gate.attr == "forecast_xyear_warmstart"
            ), (
                "runner.py must pass xyear_warmstart=config.forecast_xyear_"
                "warmstart so the forecast's cross-year gate is the config "
                "field, not MARKET_SIM_WARMSTART_XYEAR "
                "(docs/cross-year-warmstart.md)"
            )

    def test_forecast_cache_holder_is_none_unless_flag_armed(self):
        """Static guard: the year-loop holder is None at the default.

        ``forecast_xyear_cache`` must be initialized as a conditional on
        ``config.forecast_xyear_warmstart`` — ``None`` at the default field
        value, so an un-armed forecast neither applies nor exports a basis and
        stays byte-identical to the pre-D-9 tree.
        """
        src = (REPO / "src" / "market_sim" / "runner.py").read_text()
        tree = ast.parse(src)
        holders = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            for tgt in (node.targets if isinstance(node, ast.Assign) else [node.target])
            if isinstance(tgt, ast.Name) and tgt.id == "forecast_xyear_cache"
        ]
        assert len(holders) == 1, "expected exactly one forecast_xyear_cache binding"
        value = holders[0].value
        assert isinstance(value, ast.IfExp), (
            "forecast_xyear_cache must be a conditional on the config flag"
        )
        assert isinstance(value.test, ast.Attribute)
        assert value.test.attr == "forecast_xyear_warmstart"
        assert isinstance(value.orelse, ast.Constant) and value.orelse.value is None, (
            "the un-armed branch must be a literal None (cold-only default)"
        )

    def test_default_config_leaves_forecast_cold(self):
        """Behavioural guard: the shipped default keeps the forecast cold."""
        from market_sim.config.scenarios import ScenarioConfig

        assert ScenarioConfig().forecast_xyear_warmstart is False

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
