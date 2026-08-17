"""``ScenarioConfig.forecast_xyear_warmstart`` — the D-9 forecast warm-start gate.

Owner decision D-9 (``docs/refactor-consolidation-plan-2026-07.md`` §9, wall-clock
lever §7 H-3) wires cross-year LP warm start into the forecast year loop behind a
registry field instead of the ``MARKET_SIM_WARMSTART_XYEAR`` env var the backcast
uses. This file pins the three properties that make that safe:

1. **Cache-neutral at the default.** The field is registered in
   ``_CACHE_KEY_OPTIONAL_FIELDS``, so the pinned default ``cache_key`` does not
   move; an armed run gets a DISTINCT key, which is what keeps a warm-started
   forecast from colliding with a cold one in the on-disk results cache (and is
   what makes the D-9 A/B's two arms independent).
2. **The explicit gate overrides the env var, both ways.** ``run_energy_solve``
   defers to ``MARKET_SIM_WARMSTART_XYEAR`` only when ``xyear_warmstart`` is
   ``None`` (every backcast caller — byte-identical to before). A bool is the
   caller's authoritative decision, so the calibration CLIs' default-ON env var
   cannot reach a forecast that did not arm the field, and an armed forecast does
   not need the env var set.
3. **An explicitly-gated caller bypasses the persisted year-1 basis NPZ cache.**
   That cache is keyed ``(iso, weather_year, hours)`` with no sim-year, so
   seeding a 25-year forecast horizon from it would make a run depend on whatever
   solved before it.

The neutrality claim itself — that warm start changes only how fast the LP
converges, never what it converges to — is the retirement screen's
basis-independence, pinned by ``tests/regression/test_forecast_warmstart_tie_invariance.py``
and measured end-to-end by the D-9 full-horizon A/B recorded in
``docs/handoffs/wallclock-baseline-2026-07.md``.
"""

from __future__ import annotations

import market_sim.pipeline.solve as solve_mod
from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS, ScenarioConfig
from market_sim.pipeline.solve import run_energy_solve

from tests.unit.pipeline.test_pipeline_solve import _Cfg, _trivial_inputs

# The default cache_key literal pinned by tests/regression/test_persisted_identity.py. A new
# default-off field must not move it. (2026-07-27: advanced edbc1b103207170a ->
# 603c2498bf71d21d by the owner-authorized path-portability cache-epoch bump —
# rationale and provenance live on the pin in test_persisted_identity.py.)
_PINNED_DEFAULT_CACHE_KEY = "603c2498bf71d21d"


class TestFieldRegistration:
    """The field is default-ON (post-D-9 flip) and cache-neutral at its default."""

    def test_default_is_on(self):
        """Flipped ON 2026-07-26 under D-9's identical-trajectory guardrail."""
        assert ScenarioConfig().forecast_xyear_warmstart is True

    def test_registered_cache_key_optional(self):
        assert "forecast_xyear_warmstart" in _CACHE_KEY_OPTIONAL_FIELDS

    def test_default_cache_key_unmoved(self):
        """The pin survives the flip: the field drops at whatever the default is."""
        assert ScenarioConfig().cache_key() == _PINNED_DEFAULT_CACHE_KEY

    def test_opt_out_run_gets_a_distinct_cache_key(self):
        """A strictly-cold forecast is a distinct scenario, not a cache collision."""
        cold = ScenarioConfig(forecast_xyear_warmstart=False)
        assert cold.cache_key() != _PINNED_DEFAULT_CACHE_KEY


class TestSolveCoreGate:
    """``xyear_warmstart``: None defers to the env var, a bool overrides it."""

    def _spy_seed(self, monkeypatch):
        """Record every ``seed_year1_basis`` / ``persist_year_basis`` call."""
        calls: list[str] = []
        monkeypatch.setattr(
            solve_mod, "seed_year1_basis", lambda *a, **k: calls.append("seed")
        )
        monkeypatch.setattr(
            solve_mod, "persist_year_basis", lambda *a, **k: calls.append("persist")
        )
        return calls

    def test_explicit_off_beats_env_on(self, monkeypatch):
        """Env ON + explicit False ⇒ no basis is applied or exported."""
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        self._spy_seed(monkeypatch)
        gens, fa, demand, mc_base, dk = _trivial_inputs()
        holder: list = []
        got = run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            _Cfg(),
            xyear_cache=holder,
            xyear_warmstart=False,
        )
        assert got.p1.status == "Optimal"
        # PERF-B: the export follows the cross-year gate. Explicit False means
        # no consumer exists — not the next year's apply (this gate) and not
        # the persisted NPZ cache (explicitly-gated callers bypass it) — so
        # nothing is exported. Supersedes the pre-PERF-B "export is
        # unconditional on a live warm model" pin.
        assert holder == [], "no consumer ⇒ no export under explicit False"

    def test_explicit_on_without_env(self, monkeypatch):
        """Explicit True + env unset ⇒ the cross-year apply is live."""
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.delenv("MARKET_SIM_WARMSTART_XYEAR", raising=False)
        self._spy_seed(monkeypatch)
        gens, fa, demand, mc_base, dk = _trivial_inputs()
        holder: list = []
        first = run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            _Cfg(),
            xyear_cache=holder,
            xyear_warmstart=True,
        )
        assert first.p1.status == "Optimal"
        assert holder, "year 1 must export a basis for year 2"
        # Year 2 of the same horizon: the holder is non-empty, so the gate now
        # applies it. The optimum is basis-independent — same solution.
        second = run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            _Cfg(),
            xyear_cache=holder,
            xyear_warmstart=True,
        )
        assert second.p1.status == "Optimal"
        assert second.p1.objective_value == first.p1.objective_value

    def test_explicit_gate_bypasses_the_disk_basis_cache(self, monkeypatch):
        """A bool caller never seeds/persists the (iso, weather_year, T) NPZ."""
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        calls = self._spy_seed(monkeypatch)
        gens, fa, demand, mc_base, dk = _trivial_inputs()
        run_energy_solve(
            gens,
            fa,
            demand,
            mc_base,
            dk,
            _Cfg(),
            xyear_cache=[],
            xyear_warmstart=True,
        )
        assert calls == [], f"disk basis cache must stay out of a gated run: {calls}"

    def test_none_gate_still_uses_the_disk_basis_cache(self, monkeypatch):
        """The backcast path (gate None) is unchanged — seed + persist both run."""
        monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
        monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
        calls = self._spy_seed(monkeypatch)
        gens, fa, demand, mc_base, dk = _trivial_inputs()
        run_energy_solve(gens, fa, demand, mc_base, dk, _Cfg(), xyear_cache=[])
        assert calls == ["seed", "persist"]
