"""The content-addressed cold-solve cache (PERF-C S6, ``model/lp/p0_cache.py``).

What these tests pin is the property that makes an ON-by-default cache
admissible: **the key is the LP**, so an entry can only ever be served back to
the problem that produced it. Concretely —

* the key MOVES when any of the CSR arrays, a bound, the cost vector, the
  thread pin or the HiGHS version string moves, and is STABLE otherwise;
* a miss writes an entry and a hit reads it, on the real ``DispatchModel``
  path rather than against a stub;
* a hit's ``DispatchResult`` equals a miss's field for field, with no
  tolerance (``np.array_equal``);
* the switch **defaults OFF** — the shipped posture, because a hit moves the
  NEXT pass's simplex path on the live-model P1 route (module docstring;
  ``docs/handoffs/FINDING-perfc-s6-p0-cache-2026-09-22.md``) — and both an
  unarmed switch and a missing determinism pin
  (``MARKET_SIM_HIGHS_THREADS`` != 1) make it wholly inert;
* eviction holds the per-structure entry budget.

The identity test is about the **P0 result**, which is what the cache
reproduces and what measurement confirmed it reproduces exactly. It is
deliberately NOT a claim that a cached pass equals an uncached one end to end:
that is the byte gate's question, the byte gate answered it, and the answer is
recorded in the FINDING.

CLAUDE.md's testing pattern: the trivial 1-gen / 1-zone / 24-h LP first, then
a two-zone system with a link and storage so the basis being round-tripped has
column families beyond the generation block.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from market_sim.model.lp import DispatchResult, p0_cache
from market_sim.model.lp.model import DispatchModel
from market_sim.model.transmission import TransferLink, build_incidence_matrix
from tests.helpers.builders import make_fleet

_T = 24

#: The real determinism predicate, captured before the autouse fixture stubs it,
#: so the two tests that exercise it directly get the shipped implementation.
_REAL_PIN = p0_cache.determinism_pin_ok


@pytest.fixture(autouse=True)
def _cache_env(tmp_path, monkeypatch):
    """Arm the cache and redirect it into ``tmp_path``.

    ``p0_cache`` reads its root through the module global, so redirecting it
    here keeps every test out of the session's real ``results/p0-cache/``.

    **The determinism pin is armed by patching the PREDICATE, never by setting
    ``MARKET_SIM_HIGHS_THREADS``.** Setting that variable inside a pytest
    process that has already solved an LP is a known trap: HiGHS initializes a
    process-global scheduler on the first ``run()`` and then refuses every later
    LP whose ``threads`` option differs from it, reporting ``model status 'Not
    Set'`` — the latent, ordering-dependent CI red recorded in
    ``docs/FINDING-fast-tier-repair-2026-09.md`` §4b/§7.6 and guarded at source
    by ``capture_keeper_goldens.pin_determinism_env``. Reproduced here while
    writing these tests: with the variable set in the fixture, every solving test
    passed alone and failed the moment any other model test ran first. The pin
    is the RUNNER's job (``scripts/lib/solve_container.ensure_solve_container``
    sets it before the first loader), so what these tests owe is the behaviour
    ON EITHER SIDE of the predicate — which is what they patch. The predicate
    itself is tested directly, in tests that never solve.
    """
    monkeypatch.setenv("MARKET_SIM_P0_CACHE", "1")
    monkeypatch.setattr(p0_cache, "determinism_pin_ok", lambda: True)
    monkeypatch.setattr(p0_cache, "P0_CACHE_DIR", tmp_path / "p0-cache")
    return tmp_path / "p0-cache"


def _tiny_kwargs():
    """Return ``(fleet, demand, kwargs)`` for the trivial 1-gen / 1-zone LP."""
    fleet = make_fleet(["Z0", "Z0"], ["Z0"], _T, heat_rate=9.0)
    demand = np.full((1, _T), 120.0)
    return fleet, demand, {}


def _two_zone_kwargs():
    """Return ``(fleet, demand, kwargs)`` for a 2-zone + link + storage LP."""
    fleet = make_fleet(["Z0", "Z0", "Z1", "Z1"], ["Z0", "Z1"], _T, heat_rate=9.0)
    zones = ["Z0", "Z1"]
    links = [TransferLink(from_zone="Z0", to_zone="Z1", ttc_mw=50.0)]
    demand = np.vstack(
        [
            100.0 + 20.0 * np.sin(np.arange(_T) / 3.0),
            110.0 + 15.0 * np.cos(np.arange(_T) / 4.0),
        ]
    )
    kwargs = dict(
        incidence=build_incidence_matrix(links, zones),
        ttc=np.array([50.0]),
        storage_power_cap=np.array([20.0]),
        storage_energy_cap=np.array([80.0]),
        storage_zone_idx=np.array([0]),
    )
    return fleet, demand, kwargs


def _build(fleet, demand, kwargs):
    """Build a ``DispatchModel`` with the zero-renewable trivial-case arrays."""
    n_zones = demand.shape[0]
    zero = np.zeros((n_zones, _T))
    cap = np.zeros(n_zones)
    return DispatchModel(
        fleet,
        demand,
        wind_cf=zero,
        wind_cap=cap,
        solar_cf=zero,
        solar_cap=cap,
        **kwargs,
    )


def _mc(fleet, level: float = 20.0) -> np.ndarray:
    """A flat ``(n_gen, T)`` marginal-cost array at ``level``."""
    return np.full((len(fleet.pmax), _T), level)


# ---------------------------------------------------------------------------
# The key
# ---------------------------------------------------------------------------


def _structure_args(**over):
    """Baseline :func:`structure_digest` arguments, overridable per test."""
    args = dict(
        starts=np.array([0, 2], dtype=np.int32),
        indices=np.array([0, 1, 0, 1], dtype=np.int32),
        values=np.array([1.0, 1.0, 2.0, 3.0]),
        col_lower=np.array([0.0, 0.0]),
        col_upper=np.array([10.0, 10.0]),
        row_lower=np.array([5.0, 1.0]),
        row_upper=np.array([5.0, 9.0]),
        total_columns=2,
        n_rows=2,
        T=1,
        unit_ids=["a", "b"],
    )
    args.update(over)
    return args


def test_structure_digest_is_stable_and_moves_with_every_input():
    """The digest is a pure function of the LP bytes, and every byte counts."""
    base = p0_cache.structure_digest(**_structure_args())
    assert base == p0_cache.structure_digest(**_structure_args())

    perturbations = {
        "starts": np.array([0, 1], dtype=np.int32),
        "indices": np.array([0, 1, 1, 1], dtype=np.int32),
        "values": np.array([1.0, 1.0, 2.0, 3.0000001]),
        "col_lower": np.array([0.0, 0.5]),
        "col_upper": np.array([10.0, 11.0]),
        "row_lower": np.array([5.0, 2.0]),
        "row_upper": np.array([5.0, 8.0]),
        "total_columns": 3,
        "n_rows": 3,
        "T": 2,
        "unit_ids": ["a", "c"],
    }
    for name, value in perturbations.items():
        assert p0_cache.structure_digest(**_structure_args(**{name: value})) != base, (
            f"{name} must change the structure digest"
        )

    # Unit ORDER is identity, not a set: every downstream extraction slices the
    # generation block positionally.
    assert p0_cache.structure_digest(**_structure_args(unit_ids=["b", "a"])) != base


def test_solve_key_moves_with_cost_options_and_structure():
    """The full key is structure + objective + solver settings, all three."""
    struct = p0_cache.structure_digest(**_structure_args())
    cost = np.array([1.0, 2.0])
    base = p0_cache.solve_key(struct, cost, "highspy=1.14.0|threads=1")

    assert base == p0_cache.solve_key(struct, cost.copy(), "highspy=1.14.0|threads=1")
    assert base != p0_cache.solve_key(
        struct, np.array([1.0, 2.5]), "highspy=1.14.0|threads=1"
    )
    # A version bump and a thread-pin change both land in the options string.
    assert base != p0_cache.solve_key(struct, cost, "highspy=1.15.0|threads=1")
    assert base != p0_cache.solve_key(struct, cost, "highspy=1.14.0|threads=4")
    other = p0_cache.structure_digest(**_structure_args(total_columns=3))
    assert base != p0_cache.solve_key(other, cost, "highspy=1.14.0|threads=1")


def test_option_signature_carries_the_thread_pin_and_version(monkeypatch):
    """The model's own signature is what the key consumes — check its content.

    The model built here is never SOLVED, which is what makes it safe to move
    ``MARKET_SIM_HIGHS_THREADS`` under it (see the fixture docstring): the
    signature reads the variable at call time, and no ``h.run()`` ever sees a
    thread option this test changed.
    """
    fleet, demand, kwargs = _tiny_kwargs()
    model = _build(fleet, demand, kwargs)
    sig = model._highs_option_signature()
    assert "highspy=" in sig and "githash=" in sig and "presolve=off" in sig
    monkeypatch.setenv("MARKET_SIM_HIGHS_THREADS", "1")
    pinned = model._highs_option_signature()
    assert "threads_env=1" in pinned
    monkeypatch.setenv("MARKET_SIM_HIGHS_THREADS", "4")
    assert model._highs_option_signature() != pinned


# ---------------------------------------------------------------------------
# Miss writes, hit reads, and the two answers are equal
# ---------------------------------------------------------------------------


def _entry_files(cache_dir) -> list:
    return sorted(cache_dir.rglob("*.npz"))


def _assert_results_equal(miss: DispatchResult, hit: DispatchResult) -> None:
    """Every field equal with NO tolerance, timings excepted (wall clock)."""
    timings = {"build_time", "solve_time"}
    for f in dataclasses.fields(DispatchResult):
        if f.name in timings:
            continue
        got, ref = getattr(hit, f.name), getattr(miss, f.name)
        if ref is None:
            assert got is None, f.name
        elif isinstance(ref, np.ndarray):
            assert np.array_equal(np.asarray(got), ref), f.name
        else:
            assert got == ref, f.name


@pytest.mark.parametrize("system", ["tiny", "two_zone"])
def test_miss_writes_hit_reads_and_the_answers_are_identical(_cache_env, system):
    """The whole contract, on the real model path, on two LP shapes."""
    cache_dir = _cache_env
    fleet, demand, kwargs = _tiny_kwargs() if system == "tiny" else _two_zone_kwargs()
    mc = _mc(fleet)

    first = _build(fleet, demand, kwargs)
    r_miss = first.solve(mc=mc)
    assert first.p0_cache_key is not None
    assert first.p0_cache_hit is False
    assert len(_entry_files(cache_dir)) == 1

    second = _build(fleet, demand, kwargs)
    r_hit = second.solve(mc=mc)
    assert second.p0_cache_key == first.p0_cache_key
    assert second.p0_cache_hit is True

    _assert_results_equal(r_miss, r_hit)


def test_a_different_cost_vector_is_a_different_entry(_cache_env):
    """A P1-only knob changes the objective, so it misses — and is its own entry."""
    cache_dir = _cache_env
    fleet, demand, kwargs = _tiny_kwargs()
    _build(fleet, demand, kwargs).solve(mc=_mc(fleet, 20.0))
    model = _build(fleet, demand, kwargs)
    model.solve(mc=_mc(fleet, 25.0))
    assert model.p0_cache_hit is False
    assert len(_entry_files(cache_dir)) == 2


def test_only_the_first_solve_on_a_model_is_cached(_cache_env):
    """A second ``solve`` never touches the cache (in-place bound mutation)."""
    fleet, demand, kwargs = _tiny_kwargs()
    model = _build(fleet, demand, kwargs)
    model.solve(mc=_mc(fleet, 20.0))
    assert model.p0_cache_key is not None
    model.solve(mc=_mc(fleet, 25.0))
    assert model.p0_cache_key is None
    assert model.p0_cache_hit is False


def test_a_preinstalled_basis_makes_the_cache_inert(_cache_env):
    """A warm-start-class route is left alone in both directions."""
    cache_dir = _cache_env
    fleet, demand, kwargs = _tiny_kwargs()
    donor = _build(fleet, demand, kwargs)
    donor.solve(mc=_mc(fleet))
    basis = donor.export_cross_year_basis()
    assert len(_entry_files(cache_dir)) == 1

    warm = _build(fleet, demand, kwargs)
    assert warm.apply_cross_year_basis(basis) is True
    warm.solve(mc=_mc(fleet))
    assert warm.p0_cache_key is None
    assert warm.p0_cache_hit is False
    assert len(_entry_files(cache_dir)) == 1


# ---------------------------------------------------------------------------
# The two inert conditions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("switch", ["0", "false", "off", "", None])
def test_the_switch_defaults_off_and_only_an_explicit_value_arms_it(
    monkeypatch, switch
):
    """Default OFF is the SHIPPED posture (module docstring), so pin it."""
    if switch is None:
        monkeypatch.delenv("MARKET_SIM_P0_CACHE", raising=False)
    else:
        monkeypatch.setenv("MARKET_SIM_P0_CACHE", switch)
    assert p0_cache.cache_switch_on() is False
    assert p0_cache.p0_cache_enabled() is False
    for on in ("1", "true", "on", "YES"):
        monkeypatch.setenv("MARKET_SIM_P0_CACHE", on)
        assert p0_cache.cache_switch_on() is True


def test_switch_off_is_inert(_cache_env, monkeypatch):
    """``MARKET_SIM_P0_CACHE`` unset — nothing read, nothing written."""
    monkeypatch.setenv("MARKET_SIM_P0_CACHE", "0")
    assert p0_cache.p0_cache_enabled() is False
    fleet, demand, kwargs = _tiny_kwargs()
    model = _build(fleet, demand, kwargs)
    result = model.solve(mc=_mc(fleet))
    assert result.status == "Optimal"
    assert model.p0_cache_key is None
    assert _entry_files(_cache_env) == []


# These two exercise the REAL predicate (the autouse fixture's stub is put back
# for them) and never solve, so moving the env variable under them is safe — see
# the fixture docstring.
@pytest.mark.parametrize("threads", ["", "0", "4", "auto"])
def test_an_unpinned_thread_count_is_refused(monkeypatch, threads):
    """Multi-threaded dual simplex is not bit-reproducible, so it is refused."""
    monkeypatch.setattr(p0_cache, "determinism_pin_ok", _REAL_PIN)
    monkeypatch.setenv("MARKET_SIM_HIGHS_THREADS", threads)
    assert p0_cache.determinism_pin_ok() is False
    assert p0_cache.p0_cache_enabled() is False


def test_the_pin_must_be_exactly_one(monkeypatch):
    """Unset counts as NOT pinned: HiGHS then chooses its own thread count."""
    monkeypatch.setattr(p0_cache, "determinism_pin_ok", _REAL_PIN)
    monkeypatch.delenv("MARKET_SIM_HIGHS_THREADS", raising=False)
    assert p0_cache.determinism_pin_ok() is False
    monkeypatch.setenv("MARKET_SIM_HIGHS_THREADS", "1")
    assert p0_cache.determinism_pin_ok() is True


def test_without_the_thread_pin_the_cache_is_inert(_cache_env, monkeypatch):
    """Nothing read, nothing written, and the solve is otherwise untouched."""
    monkeypatch.setattr(p0_cache, "determinism_pin_ok", lambda: False)
    fleet, demand, kwargs = _tiny_kwargs()
    model = _build(fleet, demand, kwargs)
    result = model.solve(mc=_mc(fleet))
    assert result.status == "Optimal"
    assert model.p0_cache_key is None
    assert _entry_files(_cache_env) == []


# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------


def _entry(n: int) -> p0_cache.CachedSolve:
    return p0_cache.CachedSolve(
        col_status=np.zeros(n, dtype=np.int8),
        row_status=np.zeros(n, dtype=np.int8),
        objective=float(n),
        simplex_iterations=n,
    )


def test_eviction_keeps_three_entries_per_structure(tmp_path):
    """Oldest mtime first, at :data:`MAX_ENTRIES_PER_STRUCTURE`."""
    cache_dir = tmp_path / "cache"
    struct = "0" * 64
    paths = []
    for i in range(5):
        key = f"{i:064d}"
        path = p0_cache.store(struct, key, _entry(3), cache_dir=cache_dir)
        assert path is not None
        # Monotone mtimes so "oldest" is unambiguous on a coarse-resolution fs.
        import os as _os

        _os.utime(path, (1_700_000_000 + i, 1_700_000_000 + i))
        paths.append(path)
    p0_cache.evict(cache_dir=cache_dir)
    survivors = sorted(p.name for p in cache_dir.rglob("*.npz"))
    assert len(survivors) == p0_cache.MAX_ENTRIES_PER_STRUCTURE
    assert survivors == sorted(p.name for p in paths[-3:])


def test_store_load_roundtrip_and_self_eviction_on_a_bad_file(tmp_path):
    """A corrupt or wrong-shaped file reports absent and is unlinked."""
    cache_dir = tmp_path / "cache"
    struct, key = "a" * 64, "b" * 64
    path = p0_cache.store(struct, key, _entry(4), cache_dir=cache_dir)
    assert path is not None
    got = p0_cache.load(struct, key, n_cols=4, n_rows=4, cache_dir=cache_dir)
    assert got is not None and got.simplex_iterations == 4

    # Shape disagreement: the safe answer is "no entry", and the file goes.
    assert p0_cache.load(struct, key, n_cols=5, n_rows=4, cache_dir=cache_dir) is None
    assert not path.exists()

    path = p0_cache.store(struct, key, _entry(4), cache_dir=cache_dir)
    path.write_bytes(b"not an npz")
    assert p0_cache.load(struct, key, n_cols=4, n_rows=4, cache_dir=cache_dir) is None
    assert not path.exists()


def test_schema_key_mismatch_self_evicts(tmp_path, monkeypatch):
    """A format change makes older files absent rather than mis-read."""
    cache_dir = tmp_path / "cache"
    struct, key = "c" * 64, "d" * 64
    path = p0_cache.store(struct, key, _entry(2), cache_dir=cache_dir)
    monkeypatch.setattr(p0_cache, "SCHEMA_KEY", "p0-cache/v999")
    assert p0_cache.load(struct, key, n_cols=2, n_rows=2, cache_dir=cache_dir) is None
    assert not path.exists()
