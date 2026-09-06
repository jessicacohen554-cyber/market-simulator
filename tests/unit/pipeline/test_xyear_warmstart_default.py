"""Cross-year LP warm-start default gate (calibration ON, forecast cold-only).

``MARKET_SIM_WARMSTART_XYEAR`` defaults OFF globally (``pipeline.solve``), and
the calibration CLIs flip it ON via ``resolve_xyear_warmstart_default`` unless
``--no-xyear-warmstart`` is passed or the env var is set explicitly. The
forecast path (``runner.py``) passes ``xyear_cache=None`` and therefore cannot
consume the basis no matter what the env var says — that cold-only invariant is
asserted here so a future edit can't silently wire the new default into the
forecast trajectory (docs/cross-year-warmstart.md "Why the forecast path is not
wired").

Since wave 2a item B this file also pins the SAME-YEAR P1 basis seed
(``MARKET_SIM_P1_BASIS_SEED`` / ``--no-p1-basis-seed``), which rides the same
switch family: it is resolved by the sibling
``resolve_p1_basis_seed_default`` with identical precedence, and inside
``run_energy_solve`` it is gated on the cross-year gate AND on the caller having
left ``xyear_warmstart`` at ``None``. Both of those are asserted below, because
they are what keeps the goldens/replay determinism pin and the forecast lane
cold (docs/cross-year-warmstart.md "same-year P1 seed"; owner memo
docs/handoffs/p1-basis-seed-decision-memo-2026-09.md, signed 2026-09-06).
"""

from __future__ import annotations

import ast

import numpy as np

from scripts.run_calibration import (
    resolve_p1_basis_seed_default,
    resolve_xyear_warmstart_default,
)
from tests.helpers import REPO_ROOT

REPO = REPO_ROOT


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

    def test_forecast_cache_holder_is_gated_on_the_flag(self):
        """Static guard: the year-loop holder is conditional on the flag.

        ``forecast_xyear_cache`` must be initialized as a conditional on
        ``config.forecast_xyear_warmstart``, with a literal ``None`` on the
        opt-out branch — so a run that sets the field ``False`` neither applies
        nor exports a basis and reproduces the pre-D-9 cold forecast exactly.
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
            "the opt-out branch must be a literal None (strictly cold forecast)"
        )

    def test_opt_out_config_leaves_forecast_cold(self):
        """Behavioural guard: the field is the ONLY forecast cross-year switch.

        The shipped default is ON (D-9 flip); a config that opts out reproduces
        the pre-flip cold forecast. What must stay true either way is that the
        env var does not decide it — pinned by the static guard above.
        """
        from market_sim.config.scenarios import ScenarioConfig

        assert ScenarioConfig().forecast_xyear_warmstart is True
        assert (
            ScenarioConfig(forecast_xyear_warmstart=False).forecast_xyear_warmstart
            is False
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
        from tests.unit.pipeline.test_pipeline_solve import _Cfg, _trivial_inputs

        gens, fa, demand, mc_base, dk = _trivial_inputs()
        got = run_energy_solve(gens, fa, demand, mc_base, dk, _Cfg(), xyear_cache=None)
        assert got.p1.status == "Optimal"


class TestResolveP1SeedDefault:
    """Precedence: --no-p1-basis-seed > explicit env var > default ON."""

    def test_default_on_when_unset(self, monkeypatch):
        monkeypatch.delenv("MARKET_SIM_P1_BASIS_SEED", raising=False)
        assert resolve_p1_basis_seed_default(disable=False) is True
        import os

        assert os.environ["MARKET_SIM_P1_BASIS_SEED"] == "1"

    def test_flag_forces_off_over_default(self, monkeypatch):
        monkeypatch.delenv("MARKET_SIM_P1_BASIS_SEED", raising=False)
        assert resolve_p1_basis_seed_default(disable=True) is False
        import os

        assert os.environ["MARKET_SIM_P1_BASIS_SEED"] == "0"

    def test_flag_forces_off_over_explicit_env_on(self, monkeypatch):
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        assert resolve_p1_basis_seed_default(disable=True) is False
        import os

        assert os.environ["MARKET_SIM_P1_BASIS_SEED"] == "0"

    def test_explicit_env_off_honored(self, monkeypatch):
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "0")
        assert resolve_p1_basis_seed_default(disable=False) is False

    def test_explicit_env_on_honored(self, monkeypatch):
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        assert resolve_p1_basis_seed_default(disable=False) is True

    def test_both_cli_parsers_expose_the_opt_out(self):
        """Both calibration CLIs must carry ``--no-p1-basis-seed``.

        Static guard: the flag is the documented opt-out, and a CLI that
        silently lacks it would leave an operator with no way to reach the
        cold path short of the env var.
        """
        for rel in ("scripts/run_calibration.py", "scripts/run_calibration_full.py"):
            src = (REPO / rel).read_text()
            assert '"--no-p1-basis-seed"' in src, f"{rel} is missing the opt-out flag"
            assert "resolve_p1_basis_seed_default(" in src, (
                f"{rel} must resolve the seed default on its fresh-solve path"
            )


def _seeded_cold_inputs():
    """The trivial fleet plus a floor hook that routes P1 down the cold path."""
    from tests.unit.pipeline.test_pipeline_solve import _floor_hook, _trivial_inputs

    gens, fa, demand, mc_base, dk = _trivial_inputs()
    prep, _calls = _floor_hook(fa)
    return gens, fa, demand, mc_base, dk, prep


class TestP1BasisSeedGate:
    """The seed fires on the calibration cold-P1 route and nowhere else."""

    def test_seed_is_inert_under_the_goldens_pin(self, monkeypatch):
        """XYEAR=0 (the determinism pin) forces the seed off, seed env or not.

        This is the invariant the byte gate rests on: under the pin the new
        code is dead, so every golden, replay and merge-base control capture is
        byte-identical to the pre-change tree (memo §5).
        """
        from market_sim.model import lp as lp_mod
        from market_sim.pipeline.solve import run_energy_solve

        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "0")
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        seen: list = []
        _real = lp_mod.solve_dispatch

        def _spy(*args, **kwargs):
            seen.append(kwargs.get("basis_seed", "absent"))
            return _real(*args, **kwargs)

        monkeypatch.setattr("market_sim.pipeline.solve.solve_dispatch", _spy)
        gens, fa, demand, mc_base, dk, prep = _seeded_cold_inputs()
        from tests.unit.pipeline.test_pipeline_solve import _Cfg

        got = run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            _Cfg(),
            xyear_cache=[],
            p1_fleet_prep=prep,
        )
        assert got.p1_cold is True
        # The cold P1 ran, and it was handed no basis keyword at all.
        assert seen == ["absent"]
        assert got.p1_basis is None

    def test_seed_is_inert_on_the_forecast_path(self, monkeypatch):
        """An explicit ``xyear_warmstart`` bool keeps the seed off.

        ``runner.py`` always passes one (D-9/D-10), so the forecast lane is
        cold by construction — not by the current value of the config field.
        """
        from market_sim.model import lp as lp_mod
        from market_sim.pipeline.solve import run_energy_solve
        from tests.unit.pipeline.test_pipeline_solve import _Cfg

        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        seen: list = []
        _real = lp_mod.solve_dispatch

        def _spy(*args, **kwargs):
            seen.append(kwargs.get("basis_seed", "absent"))
            return _real(*args, **kwargs)

        monkeypatch.setattr("market_sim.pipeline.solve.solve_dispatch", _spy)
        gens, fa, demand, mc_base, dk, prep = _seeded_cold_inputs()
        got = run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            _Cfg(),
            xyear_cache=[],
            p1_fleet_prep=prep,
            # Even the PERMISSIVE explicit value must not arm the seed.
            xyear_warmstart=True,
        )
        assert got.p1_cold is True
        assert seen == ["absent"]
        assert got.p1_basis is None

    def test_seed_fires_on_the_calibration_cold_p1_route(self, monkeypatch):
        """Calibration gate armed → the second model is handed the P0 basis."""
        from market_sim.model import lp as lp_mod
        from market_sim.pipeline.solve import run_energy_solve
        from tests.unit.pipeline.test_pipeline_solve import _Cfg

        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        seen: list = []
        _real = lp_mod.solve_dispatch

        def _spy(*args, **kwargs):
            seen.append(kwargs.get("basis_seed", "absent"))
            return _real(*args, **kwargs)

        monkeypatch.setattr("market_sim.pipeline.solve.solve_dispatch", _spy)
        gens, fa, demand, mc_base, dk, prep = _seeded_cold_inputs()
        got = run_energy_solve(
            gens, fa, demand, mc_base, dk, _Cfg(), xyear_cache=[], p1_fleet_prep=prep
        )
        assert got.p1_cold is True
        assert len(seen) == 1 and seen[0] is not None and seen[0] != "absent"
        # Not retained unless the caller asked for it.
        assert got.p1_basis is None

    def test_seed_does_not_move_the_answer(self, monkeypatch):
        """Seeded and unseeded cold P1 clear the same LP to the same optimum.

        The trivial LP is small enough to be non-degenerate, so this is an
        exact check. On a real ISO the standard is the bundle-level neutrality
        gate (``diff_warmstart_bundles.py``), not this.
        """
        from market_sim.pipeline.solve import run_energy_solve
        from tests.unit.pipeline.test_pipeline_solve import _Cfg

        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        gens, fa, demand, mc_base, dk, prep = _seeded_cold_inputs()

        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "0")
        cold = run_energy_solve(
            gens, fa, demand, mc_base, dk, _Cfg(), xyear_cache=[], p1_fleet_prep=prep
        )
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        seeded = run_energy_solve(
            gens, fa, demand, mc_base, dk, _Cfg(), xyear_cache=[], p1_fleet_prep=prep
        )
        assert np.array_equal(cold.p1.dispatch, seeded.p1.dispatch)
        assert np.array_equal(cold.p1.prices, seeded.p1.prices)
        assert cold.p1.status == seeded.p1.status == "Optimal"

    def test_retain_exports_the_p1_basis_and_a_reused_pass_seeds_from_it(
        self, monkeypatch
    ):
        """``retain_p1_basis`` chains the adaptive pass onto the previous P1.

        Pass 1 retains its P1 basis; pass 2 (handed it as ``reuse_p0_from``,
        the C-1b route, which has no P0 model of its own to export from) is
        seeded with exactly that object, and clears the identical P1.
        """
        from market_sim.model import lp as lp_mod
        from market_sim.pipeline.solve import run_energy_solve
        from tests.unit.pipeline.test_pipeline_solve import _Cfg

        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        gens, fa, demand, mc_base, dk, prep = _seeded_cold_inputs()
        cache: list = []
        first = run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            _Cfg(),
            xyear_cache=cache,
            p1_fleet_prep=prep,
            retain_p1_basis=True,
        )
        assert first.p1_cold is True
        assert first.p1_basis is not None, "retain_p1_basis must export the P1 basis"

        seen: list = []
        _real = lp_mod.solve_dispatch

        def _spy(*args, **kwargs):
            seen.append(kwargs.get("basis_seed", "absent"))
            return _real(*args, **kwargs)

        monkeypatch.setattr("market_sim.pipeline.solve.solve_dispatch", _spy)
        second = run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            _Cfg(),
            xyear_cache=cache,
            p1_fleet_prep=prep,
            reuse_p0_from=first,
        )
        assert second.p0_reused is True
        assert seen == [first.p1_basis], "pass 2 must seed from pass 1's P1 basis"
        assert np.array_equal(second.p1.dispatch, first.p1.dispatch)

    def test_reused_pass_falls_back_to_the_p0_basis(self, monkeypatch):
        """No retained P1 basis → the reused pass seeds from the P0 basis.

        Safe degradation: a route that forgets ``retain_p1_basis`` still gets a
        seed (the same year's P0 basis, which the previous pass left in the
        cross-year holder), just a slightly less close one.
        """
        from market_sim.model import lp as lp_mod
        from market_sim.pipeline.solve import run_energy_solve
        from tests.unit.pipeline.test_pipeline_solve import _Cfg

        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        gens, fa, demand, mc_base, dk, prep = _seeded_cold_inputs()
        cache: list = []
        first = run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            _Cfg(),
            xyear_cache=cache,
            p1_fleet_prep=prep,
        )
        assert first.p1_basis is None and cache, "the P0 basis must be in the holder"

        seen: list = []
        _real = lp_mod.solve_dispatch

        def _spy(*args, **kwargs):
            seen.append(kwargs.get("basis_seed", "absent"))
            return _real(*args, **kwargs)

        monkeypatch.setattr("market_sim.pipeline.solve.solve_dispatch", _spy)
        second = run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            _Cfg(),
            xyear_cache=cache,
            p1_fleet_prep=prep,
            reuse_p0_from=first,
        )
        assert seen == [cache[0]], "pass 2 must fall back to the P0 basis"
        assert np.array_equal(second.p1.dispatch, first.p1.dispatch)
