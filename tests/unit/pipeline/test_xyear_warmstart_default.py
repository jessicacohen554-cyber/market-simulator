"""Cross-year LP warm-start default gate (calibration ON, forecast cold-only).

``MARKET_SIM_WARMSTART_XYEAR`` defaults OFF globally (``pipeline.solve``), and
the calibration CLIs flip it ON via ``resolve_xyear_warmstart_default`` unless
``--no-xyear-warmstart`` is passed or the env var is set explicitly. The
forecast path (``runner.py``) passes ``xyear_cache=None`` and therefore cannot
consume the basis no matter what the env var says — that cold-only invariant is
asserted here so a future edit can't silently wire the new default into the
forecast trajectory (docs/cross-year-warmstart.md "Why the forecast path is not
wired").

The same-year P1 basis seed (``MARKET_SIM_P1_BASIS_SEED``, wallclock desk item
B; owner memo ``docs/handoffs/p1-basis-seed-decision-memo-2026-09.md`` §6) is
the switch family's third member and is pinned here too: the sibling resolver's
precedence, the seed firing on its OWN env var INDEPENDENT of the cross-year
gate (PERF-C S1, 2026-09-20 — ``docs/handoffs/FINDING-perfc-s1-p1-seed-2026-09-20.md``),
never on the forecast path (an explicit ``xyear_warmstart`` bool), the
adaptive-pass leg (``export_p1_basis`` → ``reuse_p0_from.p1_basis``), the
optimality guard that discards a seeded basis whose solve did not reach
``Optimal``, the CLI flag on both calibration parsers, and the
``getattr``-tolerant contract on the capturing test double.

Both resolvers default **OFF** (rule 36 ``[R-YEAR-ISOLATION]``, owner ruling
2026-09-19, miso-262). Un-nesting the seed did not change that default — it
made the two knobs independently settable, which is the decision the owner now
has in front of them.
"""

from __future__ import annotations

import ast
import os

import numpy as np

from scripts.run_calibration import (
    resolve_p1_basis_seed_default,
    resolve_xyear_warmstart_default,
)
from tests.helpers import REPO_ROOT

REPO = REPO_ROOT


class TestResolveDefault:
    """Precedence: --no-xyear-warmstart > explicit env var > default OFF."""

    def test_default_off_when_unset(self, monkeypatch):
        """Rule 36 [R-YEAR-ISOLATION] (owner ruling 2026-09-19, miso-262)
        flipped this default ON -> OFF; the assertion had not been updated
        with it and was red at HEAD (found by PERF-C S1)."""
        monkeypatch.delenv("MARKET_SIM_WARMSTART_XYEAR", raising=False)
        assert resolve_xyear_warmstart_default(disable=False) is False
        import os

        assert os.environ["MARKET_SIM_WARMSTART_XYEAR"] == "0"

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


class TestResolveP1BasisSeedDefault:
    """Precedence: --no-p1-basis-seed > explicit env var > default OFF.

    PERF-C S1 un-nested the seed from the cross-year gate in ``pipeline.solve``
    and left this resolver's default exactly where rule 36 put it: OFF. The
    owner decides whether to flip it; this shard does not.
    """

    def test_default_off_when_unset(self, monkeypatch):
        """Rule 36 flipped this default ON -> OFF; the assertion had not been
        updated with it and was red at HEAD (found by PERF-C S1)."""
        monkeypatch.delenv("MARKET_SIM_P1_BASIS_SEED", raising=False)
        assert resolve_p1_basis_seed_default(disable=False) is False
        assert os.environ["MARKET_SIM_P1_BASIS_SEED"] == "0"

    def test_flag_forces_off_over_default(self, monkeypatch):
        monkeypatch.delenv("MARKET_SIM_P1_BASIS_SEED", raising=False)
        assert resolve_p1_basis_seed_default(disable=True) is False
        assert os.environ["MARKET_SIM_P1_BASIS_SEED"] == "0"

    def test_flag_forces_off_over_explicit_env_on(self, monkeypatch):
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        assert resolve_p1_basis_seed_default(disable=True) is False
        assert os.environ["MARKET_SIM_P1_BASIS_SEED"] == "0"

    def test_explicit_env_off_honored(self, monkeypatch):
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "0")
        assert resolve_p1_basis_seed_default(disable=False) is False

    def test_explicit_env_on_honored(self, monkeypatch):
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        assert resolve_p1_basis_seed_default(disable=False) is True

    def test_flag_present_on_both_calibration_parsers(self):
        """Static guard: ``--no-p1-basis-seed`` is declared beside
        ``--no-xyear-warmstart`` in BOTH calibration CLIs, and both resolve it
        through the shared resolver on the fresh-solve path."""
        for rel in ("scripts/run_calibration.py", "scripts/run_calibration_full.py"):
            src = (REPO / rel).read_text()
            assert '"--no-p1-basis-seed"' in src, rel
            assert "resolve_p1_basis_seed_default(args.no_p1_basis_seed)" in src, rel


def _cold_route_inputs():
    """The trivial LP routed COLD at P1 (a floor hook replaces the fleet)."""
    from tests.unit.pipeline.test_pipeline_solve import (
        _Cfg,
        _floor_hook,
        _trivial_inputs,
    )

    gens, fa, demand, mc_base, dk = _trivial_inputs()
    prep, _calls = _floor_hook(fa)
    return gens, fa, demand, mc_base, dk, _Cfg(), prep


def _isolate_basis_cache(monkeypatch, tmp_path):
    """Point the persisted year-1 basis cache at a scratch dir (H2 cache)."""
    from market_sim.pipeline import basis_cache

    monkeypatch.setattr(basis_cache, "BASIS_CACHE_DIR", tmp_path / "basis-cache")


class TestP1BasisSeedGate:
    """The seed fires only inside the cross-year gate, on the backcast callers."""

    def test_seed_applies_inside_the_gate_and_is_neutral(self, monkeypatch, tmp_path):
        """XYEAR=1 + SEED=1 on a cold-P1 route: the second model is seeded, and
        the P1 it clears is the unseeded P1 (unique optimum on the trivial LP)."""
        _isolate_basis_cache(monkeypatch, tmp_path)
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        from market_sim.pipeline.solve import run_energy_solve

        gens, fa, demand, mc_base, dk, cfg, prep = _cold_route_inputs()
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "0")
        off = run_energy_solve(
            gens, fa, demand, mc_base, dk, cfg, xyear_cache=[], p1_fleet_prep=prep
        )
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        cache: list = []
        on = run_energy_solve(
            gens, fa, demand, mc_base, dk, cfg, xyear_cache=cache, p1_fleet_prep=prep
        )
        assert off.p1_cold is True and off.p1_seeded is False
        assert on.p1_cold is True and on.p1_seeded is True
        # The holder still carries the P0 basis for the next year (unchanged
        # cross-year contract); the seed reuses that export.
        assert len(cache) == 1
        # No P1 basis export unless asked for.
        assert on.p1_basis is None
        assert on.p1.status == "Optimal"
        assert np.array_equal(on.mc_bid, off.mc_bid)
        assert np.array_equal(on.p1.dispatch, off.p1.dispatch)
        assert np.array_equal(on.p1.prices, off.p1.prices)
        assert on.p1.objective_value == off.p1.objective_value

    def test_seed_fires_with_the_cross_year_gate_off(self, monkeypatch, tmp_path):
        """PERF-C S1: XYEAR=0 + SEED=1 → the seed FIRES.

        This test formerly asserted the opposite (``test_seed_inert_under_the_
        goldens_pin``): the seed used to be armed inside ``_xwarm``, so
        ``MARKET_SIM_WARMSTART_XYEAR=0`` implied it off. Un-nesting is the
        whole change, and the invariant that replaces the old one is that
        **no cross-year state leaks** — the holder must stay empty, because a
        seed-only pass has nothing to hand the next year (rule 36
        ``[R-YEAR-ISOLATION]``). The P1 it clears is still the unseeded P1.
        """
        _isolate_basis_cache(monkeypatch, tmp_path)
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "0")
        from market_sim.pipeline.solve import run_energy_solve

        gens, fa, demand, mc_base, dk, cfg, prep = _cold_route_inputs()
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "0")
        off = run_energy_solve(
            gens, fa, demand, mc_base, dk, cfg, xyear_cache=[], p1_fleet_prep=prep
        )
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        cache: list = []
        on = run_energy_solve(
            gens, fa, demand, mc_base, dk, cfg, xyear_cache=cache, p1_fleet_prep=prep
        )
        assert on.p1_cold is True
        assert on.p1_seeded is True
        assert on.p1_seed_fallback is None
        assert on.p1_basis is None  # no export unless asked for
        # The cross-year holder is NOT written: the seed took the P0 export,
        # the holder did not, because ``_xwarm`` is off.
        assert cache == []
        assert on.p1.status == "Optimal"
        assert np.array_equal(on.p1.dispatch, off.p1.dispatch)
        assert np.array_equal(on.p1.prices, off.p1.prices)
        assert on.p1.objective_value == off.p1.objective_value

    def test_seed_does_not_fire_with_its_env_off(self, monkeypatch, tmp_path):
        """The env var is the gate now, in BOTH cross-year postures: SEED=0
        never seeds, whatever ``MARKET_SIM_WARMSTART_XYEAR`` says."""
        _isolate_basis_cache(monkeypatch, tmp_path)
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "0")
        from market_sim.pipeline.solve import run_energy_solve

        for xyear in ("0", "1"):
            monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", xyear)
            gens, fa, demand, mc_base, dk, cfg, prep = _cold_route_inputs()
            got = run_energy_solve(
                gens, fa, demand, mc_base, dk, cfg, xyear_cache=[], p1_fleet_prep=prep
            )
            assert got.p1_cold is True, xyear
            assert got.p1_seeded is False, xyear
            assert got.p1_seed_fallback is None, xyear
            assert got.p1_basis is None, xyear

    def test_seed_needs_the_intra_year_warm_start(self, monkeypatch, tmp_path):
        """MARKET_SIM_WARMSTART=0 builds no live P0 model, so there is no
        same-year basis to seed from — the seed is inert however armed."""
        _isolate_basis_cache(monkeypatch, tmp_path)
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "0")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "0")
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        from market_sim.pipeline.solve import run_energy_solve

        gens, fa, demand, mc_base, dk, cfg, prep = _cold_route_inputs()
        got = run_energy_solve(
            gens, fa, demand, mc_base, dk, cfg, xyear_cache=[], p1_fleet_prep=prep
        )
        assert got.p1_cold is True
        assert got.p1_seeded is False
        assert got.p1_seed_fallback is None

    def test_seed_inert_on_the_forecast_gate_argument(self, monkeypatch, tmp_path):
        """An explicit ``xyear_warmstart`` bool (the forecast caller) keeps the
        P1 cold even with the cross-year gate armed by that argument."""
        _isolate_basis_cache(monkeypatch, tmp_path)
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        from market_sim.pipeline.solve import run_energy_solve

        gens, fa, demand, mc_base, dk, cfg, prep = _cold_route_inputs()
        for gate in (True, False):
            got = run_energy_solve(
                gens,
                fa,
                demand,
                mc_base,
                dk,
                cfg,
                xyear_cache=[],
                xyear_warmstart=gate,
                p1_fleet_prep=prep,
            )
            assert got.p1_cold is True
            assert got.p1_seeded is False, gate

    def test_seed_never_reaches_a_warm_p1(self, monkeypatch, tmp_path):
        """No floor hook → P1 re-solves the live P0 model; nothing to seed."""
        _isolate_basis_cache(monkeypatch, tmp_path)
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        from market_sim.pipeline.solve import run_energy_solve
        from tests.unit.pipeline.test_pipeline_solve import _Cfg, _trivial_inputs

        gens, fa, demand, mc_base, dk = _trivial_inputs()
        got = run_energy_solve(gens, fa, demand, mc_base, dk, _Cfg(), xyear_cache=[])
        assert got.p1_cold is False and got.p1_seeded is False

    def test_adaptive_pass_seeds_from_the_previous_p1_basis(
        self, monkeypatch, tmp_path
    ):
        """C-1b route: pass 1 exports its P1 basis on request; the reused pass
        is seeded (from it) and clears the identical P1. Without the export the
        reused pass falls back to the P0 basis in the holder and is still
        seeded. Also the regression pin for the shipped crash: a reused pass
        under XYEAR=1 used to dereference ``None`` at the cross-year export."""
        _isolate_basis_cache(monkeypatch, tmp_path)
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        from market_sim.model.lp import CrossYearBasis
        from market_sim.pipeline.solve import run_energy_solve

        gens, fa, demand, mc_base, dk, cfg, prep = _cold_route_inputs()
        cache: list = []
        first = run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            cfg,
            xyear_cache=cache,
            p1_fleet_prep=prep,
            export_p1_basis=True,
        )
        assert first.p1_seeded is True
        assert isinstance(first.p1_basis, CrossYearBasis)
        second = run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            cfg,
            xyear_cache=cache,
            p1_fleet_prep=prep,
            reuse_p0_from=first,
        )
        assert second.p0_reused is True and second.r0 is first.r0
        assert second.p1_seeded is True
        assert second.p1_basis is None  # not asked to export
        assert np.array_equal(second.p1.dispatch, first.p1.dispatch)
        assert np.array_equal(second.p1.prices, first.p1.prices)

        # Fallback: a previous pass that did not export → seeded from the P0
        # basis the previous cold route left in the holder.
        plain = run_energy_solve(
            gens, fa, demand, mc_base, dk, cfg, xyear_cache=cache, p1_fleet_prep=prep
        )
        assert plain.p1_basis is None
        third = run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            cfg,
            xyear_cache=cache,
            p1_fleet_prep=prep,
            reuse_p0_from=plain,
        )
        assert third.p0_reused is True and third.p1_seeded is True
        assert np.array_equal(third.p1.dispatch, first.p1.dispatch)

    def test_reused_pass_under_xyear_on_no_longer_crashes_with_seed_off(
        self, monkeypatch, tmp_path
    ):
        """The shipped defect, seed OFF: XYEAR=1 + reuse_p0_from → the cold
        branch guarded the export on the gate but not on the (absent) model."""
        _isolate_basis_cache(monkeypatch, tmp_path)
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "0")
        from market_sim.pipeline.solve import run_energy_solve

        gens, fa, demand, mc_base, dk, cfg, prep = _cold_route_inputs()
        cache: list = []
        first = run_energy_solve(
            gens, fa, demand, mc_base, dk, cfg, xyear_cache=cache, p1_fleet_prep=prep
        )
        second = run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            cfg,
            xyear_cache=cache,
            p1_fleet_prep=prep,
            reuse_p0_from=first,
        )
        assert second.p0_reused is True and second.p1_seeded is False
        assert np.array_equal(second.p1.dispatch, first.p1.dispatch)

    def test_seed_is_getattr_tolerant_on_a_solve_only_double(
        self, monkeypatch, tmp_path
    ):
        """A ``DispatchModel`` double implementing ``solve`` alone (the
        ``_CapturingDispatchModel`` contract) must not break the seeded cold
        route: a missing export/apply degrades to an unseeded cold P1."""
        _isolate_basis_cache(monkeypatch, tmp_path)
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        from market_sim.model.dispatch import solve_dispatch
        from market_sim.pipeline import solve as solve_mod

        gens, fa, demand, mc_base, dk, cfg, prep = _cold_route_inputs()

        class _SolveOnly:
            def __init__(self, fleet_arrays, demand, **kwargs):
                self._args = (fleet_arrays, demand, kwargs)

            def solve(self, mc=None, **_):
                fleet_arrays, demand, kwargs = self._args
                return solve_dispatch(fleet_arrays, demand, mc=mc, **kwargs)

        monkeypatch.setattr(solve_mod, "DispatchModel", _SolveOnly)
        got = solve_mod.run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            cfg,
            xyear_cache=[],
            p1_fleet_prep=prep,
            export_p1_basis=True,
        )
        assert got.p1_cold is True
        assert got.p1_seeded is False
        assert got.p1_basis is None
        assert got.p1.status == "Optimal"


def _seeded_model_reporting(status=None, raises=None, accept_basis=True):
    """A ``DispatchModel`` stand-in whose SEEDED solve misreports.

    Wraps the real model, so the LP, the basis apply and the export are all
    genuine; the only fiction is what HiGHS is made to say about the run of a
    model that was actually handed a basis — a ``DispatchResult.status`` other
    than ``"Optimal"``, or the ``RuntimeError`` ``DispatchModel.solve`` raises
    on an infeasible primal. That is the exact signal the optimality guard
    keys on.

    Scoping it to instances whose ``apply_cross_year_basis`` ran is what makes
    the double usable at all: ``pipeline.solve`` builds the P0 model through
    the same name, and a double that misreported unconditionally would fail
    the P0 solve before the P1 the test is about is ever reached.

    ``accept_basis=False`` additionally makes the apply DECLINE (what a real
    horizon mismatch does), which is the guard's other scope boundary: nothing
    was installed, so there is nothing to roll back.
    """
    import dataclasses

    from market_sim.model.lp.model import DispatchModel as _Real

    class _Reporting(_Real):
        _seeded = False

        def apply_cross_year_basis(self, prev):
            got = super().apply_cross_year_basis(prev)
            if not accept_basis:
                return False
            self._seeded = bool(got)
            return got

        def solve(self, *a, **kw):
            got = super().solve(*a, **kw)
            if not self._seeded:
                return got
            if raises is not None:
                raise raises
            return dataclasses.replace(got, status=status)

    return _Reporting


class TestP1SeedOptimalityGuard:
    """A seeded P1 that does not reach ``Optimal`` is discarded and re-solved
    COLD, so the reported P1 is always the unseeded answer (PERF-C S1)."""

    def _armed(self, monkeypatch, tmp_path):
        _isolate_basis_cache(monkeypatch, tmp_path)
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "0")
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")

    def test_non_optimal_status_falls_back_to_a_cold_resolve(
        self, monkeypatch, tmp_path, caplog
    ):
        import logging

        self._armed(monkeypatch, tmp_path)
        from market_sim.pipeline import solve as solve_mod

        gens, fa, demand, mc_base, dk, cfg, prep = _cold_route_inputs()
        # Baseline: the unseeded answer this LP has.
        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "0")
        cold = solve_mod.run_energy_solve(
            gens, fa, demand, mc_base, dk, cfg, xyear_cache=[], p1_fleet_prep=prep
        )

        monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
        monkeypatch.setattr(
            solve_mod,
            "DispatchModel",
            _seeded_model_reporting(status="Iteration limit reached"),
        )
        solve_mod.reset_pass_timing_log()
        with caplog.at_level(logging.WARNING, logger=solve_mod.logger.name):
            got = solve_mod.run_energy_solve(
                gens, fa, demand, mc_base, dk, cfg, xyear_cache=[], p1_fleet_prep=prep
            )

        # The guard fired: provenance records the offending status, and
        # ``p1_seeded`` reports the P1 that is actually being returned.
        assert got.p1_seed_fallback == "Iteration limit reached"
        assert got.p1_seeded is False
        assert got.p1_basis is None
        assert any("discarding the basis" in r.getMessage() for r in caplog.records), [
            r.getMessage() for r in caplog.records
        ]
        # ...and the answer is the unseeded one, through ``solve_dispatch``.
        assert got.p1.status == "Optimal"
        assert np.array_equal(got.p1.dispatch, cold.p1.dispatch)
        assert np.array_equal(got.p1.prices, cold.p1.prices)
        # Same provenance on the pass-timing log (no second channel).
        (entry,) = solve_mod.take_pass_timing_log()
        assert entry["p1_seeded"] is False
        assert entry["p1_seed_fallback"] == "Iteration limit reached"

    def test_a_raising_seeded_solve_also_falls_back(self, monkeypatch, tmp_path):
        """``DispatchModel.solve`` raises on an infeasible primal, which a
        corrupt alien basis can also produce — retried cold, never masked (a
        genuinely infeasible LP raises again on the re-solve)."""
        self._armed(monkeypatch, tmp_path)
        from market_sim.pipeline import solve as solve_mod

        gens, fa, demand, mc_base, dk, cfg, prep = _cold_route_inputs()
        monkeypatch.setattr(
            solve_mod,
            "DispatchModel",
            _seeded_model_reporting(raises=RuntimeError("no feasible primal")),
        )
        got = solve_mod.run_energy_solve(
            gens, fa, demand, mc_base, dk, cfg, xyear_cache=[], p1_fleet_prep=prep
        )
        assert got.p1_seeded is False
        assert got.p1_seed_fallback == "RuntimeError: no feasible primal"
        assert got.p1.status == "Optimal"

    def test_an_optimal_seeded_solve_records_no_fallback(self, monkeypatch, tmp_path):
        """The guard is silent on the ordinary path — it must not cost a
        second solve when the seeded run was fine."""
        self._armed(monkeypatch, tmp_path)
        from market_sim.pipeline import solve as solve_mod

        gens, fa, demand, mc_base, dk, cfg, prep = _cold_route_inputs()
        solve_mod.reset_pass_timing_log()
        got = solve_mod.run_energy_solve(
            gens, fa, demand, mc_base, dk, cfg, xyear_cache=[], p1_fleet_prep=prep
        )
        assert got.p1_seeded is True and got.p1_seed_fallback is None
        (entry,) = solve_mod.take_pass_timing_log()
        assert entry["p1_seed_fallback"] is None

    def test_a_declined_basis_is_not_rolled_back(self, monkeypatch, tmp_path):
        """Scope boundary: when ``apply_cross_year_basis`` DECLINES, no basis
        was installed, so the guard must not fire and the P1 must not be
        re-solved — the unseeded route is untouched by PERF-C S1."""
        self._armed(monkeypatch, tmp_path)
        from market_sim.pipeline import solve as solve_mod

        gens, fa, demand, mc_base, dk, cfg, prep = _cold_route_inputs()
        monkeypatch.setattr(
            solve_mod,
            "DispatchModel",
            _seeded_model_reporting(
                status="Iteration limit reached", accept_basis=False
            ),
        )
        got = solve_mod.run_energy_solve(
            gens, fa, demand, mc_base, dk, cfg, xyear_cache=[], p1_fleet_prep=prep
        )
        assert got.p1_seeded is False and got.p1_seed_fallback is None
        assert got.p1.status == "Optimal"
