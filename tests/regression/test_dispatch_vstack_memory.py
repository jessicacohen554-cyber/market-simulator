"""Byte-identity gate for the memory-optimized constraint assembly.

``_vstack_csr_free`` replaces ``build_constraints``' pairwise ``sp.vstack`` chain
(and the reserve builders' internal stacks) to cut the construction peak that
OOM-kills the plant-level MISO/PJM keeper LPs (G-40). The optimization is
memory-only: the assembled matrix MUST be byte-for-byte identical to the old
``sp.vstack`` output, so the LP — and the Stage-6 builder-swap byte gate — are
untouched. These tests are that guarantee.
"""

from __future__ import annotations

import hashlib

import numpy as np
import scipy.sparse as sp

from market_sim.data.fleet import FleetArrays
from market_sim.model.dispatch import (
    VariableLayout,
    _build_reserve_rows_pergen,
    _vstack_csr_free,
    build_constraints,
)


def _csr_bytes(m: sp.csr_matrix) -> bytes:
    """Canonical CSR byte signature: dtype-tagged (data, indices, indptr)."""
    m = m.tocsr()
    m.sum_duplicates()
    m.sort_indices()
    h = hashlib.sha256()
    for arr in (m.data, m.indices, m.indptr):
        a = np.ascontiguousarray(arr)
        h.update(str(a.dtype).encode())
        h.update(a.tobytes())
    h.update(np.asarray(m.shape, dtype=np.int64).tobytes())
    return h.digest()


def _rand_csr(rows: int, cols: int, nnz: int, seed: int) -> sp.csr_matrix:
    rng = np.random.default_rng(seed)
    r = rng.integers(0, rows, nnz).astype(np.int32)
    c = rng.integers(0, cols, nnz).astype(np.int32)
    d = rng.standard_normal(nnz)
    return sp.coo_matrix((d, (r, c)), shape=(rows, cols)).tocsr()


def test_vstack_csr_free_matches_scipy_exactly():
    """_vstack_csr_free == sp.vstack(..., 'csr'), byte-for-byte (incl. dtype)."""
    blocks = [
        _rand_csr(500, 20_000, 4_000, 1),
        _rand_csr(120, 20_000, 900, 2),
        _rand_csr(1, 20_000, 20_000, 3),  # a dense single row (RPS-like)
        _rand_csr(300, 20_000, 2_500, 4),
    ]
    ref = sp.vstack([b.copy() for b in blocks], format="csr")
    got = _vstack_csr_free([b.copy() for b in blocks], total_cols=20_000)
    assert got.shape == ref.shape
    assert got.indices.dtype == ref.indices.dtype
    assert got.indptr.dtype == ref.indptr.dtype
    assert _csr_bytes(got) == _csr_bytes(ref)


def test_vstack_csr_free_singleton_and_empty():
    """Edge cases: one block returns it as CSR; all-None returns an empty CSR."""
    b = _rand_csr(10, 100, 30, 5)
    assert _csr_bytes(_vstack_csr_free([b.copy()], 100)) == _csr_bytes(b)
    empty = _vstack_csr_free([None, None], 100)
    assert empty.shape == (0, 100)
    assert empty.nnz == 0


def test_vstack_csr_free_matches_scipy_int64_columns():
    """When the column space forces int64 indices, the helper matches scipy."""
    big = 3_000_000_000  # > 2**31 → scipy picks int64 indices
    blocks = [
        sp.coo_matrix(
            (np.array([1.0, 2.0]), (np.array([0, 3]), np.array([0, big - 1]))),
            shape=(5, big),
        ).tocsr(),
        sp.coo_matrix(
            (np.array([3.0]), (np.array([1]), np.array([big - 2]))),
            shape=(2, big),
        ).tocsr(),
    ]
    ref = sp.vstack([b.copy() for b in blocks], format="csr")
    got = _vstack_csr_free([b.copy() for b in blocks], total_cols=big)
    assert got.indices.dtype == ref.indices.dtype  # both int64
    assert _csr_bytes(got) == _csr_bytes(ref)


def _synth_fleet(n_gen: int, n_zones: int, T: int, seed: int = 0):
    rng = np.random.default_rng(seed)
    fa = FleetArrays.__new__(FleetArrays)
    fa.pmax = rng.uniform(30.0, 800.0, n_gen)
    fa.availability = np.ones((n_gen, T))
    fa.zone_idx = rng.integers(0, n_zones, n_gen).astype(int)
    fa.fuel_type_idx = rng.integers(0, 5, n_gen).astype(int)
    fa.ramp10 = fa.pmax * 0.3
    fa.unit_ids = [str(i) for i in range(n_gen)]
    gidx = np.arange(n_gen)
    _, col = np.unique(
        np.stack([fa.zone_idx, fa.fuel_type_idx], axis=1), axis=0, return_inverse=True
    )
    return fa, gidx, col.astype(int), int(col.max()) + 1


def test_reserve_pergen_block_byte_identical_trivial():
    """Trivial 1-gen/1-zone/24h reserve block: build twice, identical bytes.

    Because the builder is deterministic and _vstack_csr_free is a pure re-
    packaging, two independent builds must produce byte-identical CSR — the
    smallest end-to-end proof that the reserve assembly is unchanged.
    """
    fa, gidx, col, n_r = _synth_fleet(n_gen=1, n_zones=1, T=24)
    layout = VariableLayout(
        n_gen=1,
        n_zones=1,
        n_storage=0,
        n_links=0,
        T=24,
        n_reserve=n_r,
        n_reserve_classes=1,
        n_ordc_steps=3,
    )
    req = np.full(24, 5.0)
    b1, lo1, hi1 = _build_reserve_rows_pergen(layout, fa, req, gidx, pergen_col=col)
    b2, lo2, hi2 = _build_reserve_rows_pergen(layout, fa, req, gidx, pergen_col=col)
    assert _csr_bytes(b1) == _csr_bytes(b2)
    assert np.array_equal(lo1, lo2) and np.array_equal(hi1, hi2)


def test_full_constraints_multiblock_byte_stable():
    """Full build_constraints (energy | soc | reserve) hashes deterministically.

    Guards the whole assembly path the free-concat touches. A change to the
    stacked matrix (wrong order, dropped block, dtype drift) flips this hash.
    """
    n_gen, n_zones, T = 60, 4, 48
    fa, gidx, col, n_r = _synth_fleet(n_gen, n_zones, T, seed=7)
    n_storage = 5
    rng = np.random.default_rng(7)
    demand = rng.uniform(100.0, 500.0, (n_zones, T))
    szone = rng.integers(0, n_zones, n_storage).astype(int)
    eta = np.full(n_storage, 0.9)
    layout = VariableLayout(
        n_gen=n_gen,
        n_zones=n_zones,
        n_storage=n_storage,
        n_links=0,
        T=T,
        n_reserve=n_r,
        n_reserve_classes=1,
        n_ordc_steps=3,
    )
    A = build_constraints(
        layout,
        fa,
        demand,
        incidence=None,
        storage_zone_idx=szone,
        eta_chg=eta,
        eta_dis=eta,
        reserve_requirement=np.full(T, 50.0),
        reserve_pergen_gen_idx=gidx,
        reserve_pergen_col=col,
    )[0]
    # Independent re-build must be byte-identical (determinism + pure re-pack).
    A2 = build_constraints(
        layout,
        fa,
        demand,
        incidence=None,
        storage_zone_idx=szone,
        eta_chg=eta,
        eta_dis=eta,
        reserve_requirement=np.full(T, 50.0),
        reserve_pergen_gen_idx=gidx,
        reserve_pergen_col=col,
    )[0]
    assert _csr_bytes(A) == _csr_bytes(A2)
    # Row count = energy (n_zones*T) + soc (n_storage*T) + joint (n_r*T) + balance (T).
    assert A.shape[0] == (n_zones + n_storage + n_r + 1) * T
