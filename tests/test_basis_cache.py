"""Persisted year-1 cross-year warm-start basis cache (``pipeline.basis_cache``).

The cache stores each solved ISO-year's exported optimal basis as a disposable
NPZ so the next calibrate-iterate run for the same ISO-year can seed a warm
year-1 P0 (otherwise the one remaining cold solve). These tests pin the four
properties the feature rests on:

* **Round-trip fidelity** — a basis reconstructed from NPZ is field-identical to
  the exported one, so applying it is indistinguishable from carrying the live
  object across runs.
* **Neutrality** — applying the reconstructed basis reproduces the cold solve's
  objective, prices and per-unit annual generation exactly (the LP optimum is
  basis-independent), even across a changed fleet.
* **Never pickle / self-healing** — files load with ``allow_pickle=False``, and a
  schema-mismatched or corrupt file is deleted-and-recaptured (compat clause 4).
* **Gate** — the cache is inert unless the cross-year warm-start env is set, so
  the goldens/replay determinism pin (``MARKET_SIM_WARMSTART_XYEAR=0``) keeps the
  solve path byte-identical.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import DispatchModel
from market_sim.pipeline import basis_cache as bc

T = 168
ZONES = ["Z"]
_ZERO_CF = np.zeros((1, T))
_ZERO_CAP = np.array([0.0])


def _fleet(specs):
    gens = [
        Generator(
            unit_id=u,
            name=u,
            zone="Z",
            fuel_type="gas_cc",
            pmax_mw=p,
            pmin_mw=0.0,
            heat_rate=h,
            eford=0.0,
        )
        for (u, p, h) in specs
    ]
    return generators_to_fleet_arrays(gens, ZONES, hours=T)


def _demand(scale=1.0):
    return np.array([[scale * (500 + 200 * np.sin(t / 12)) for t in range(T)]])


def _build(fleet, demand):
    return DispatchModel(
        fleet, demand, _ZERO_CF, _ZERO_CAP, _ZERO_CF, _ZERO_CAP, voll=5000.0, T=T
    )


def _mc(fleet, mult):
    return np.broadcast_to((fleet.heat_rate * mult)[:, None], (fleet.n_gen, T)).copy()


@pytest.fixture
def solved_basis():
    """A solved 10-unit basis to persist (year-A of the neutrality tests)."""
    fleet_a = _fleet([(f"U{i}", 100 + 5 * i, 7.0 + 0.1 * i) for i in range(10)])
    model = _build(fleet_a, _demand())
    model.solve(mc=_mc(fleet_a, 3.0))
    basis = model.export_cross_year_basis()
    assert basis is not None
    return basis


@pytest.fixture
def gate_on(monkeypatch):
    """Turn the cross-year gate on (calibration-CLI default)."""
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
    monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")


# --------------------------------------------------------------------------- #
# Round-trip fidelity
# --------------------------------------------------------------------------- #


def test_roundtrip_reconstructs_equivalent_basis(tmp_path, solved_basis):
    path = bc.store_basis(solved_basis, "TEST", 2023, T, "abc123", cache_dir=tmp_path)
    assert path is not None and path.exists()
    assert path.name == "TEST_2023_T168.npz"

    reb = bc.load_latest_basis("TEST", 2023, T, cache_dir=tmp_path)
    assert reb is not None
    # Frozen VariableLayout reconstructs field-for-field (every offset the apply
    # reads is a derived property of these ints).
    assert reb.layout == solved_basis.layout
    assert reb.unit_ids == solved_basis.unit_ids
    assert np.array_equal(reb.col_status, solved_basis.col_status)
    assert np.array_equal(reb.row_status, solved_basis.row_status)
    assert reb.col_status.dtype == np.int8 and reb.row_status.dtype == np.int8
    assert (reb.n_rows, reb.n_energy_rows, reb.n_storage_rows) == (
        solved_basis.n_rows,
        solved_basis.n_energy_rows,
        solved_basis.n_storage_rows,
    )


def test_store_overwrites_newest(tmp_path, solved_basis):
    # Two stores for the same (iso, year, T) key leave exactly one file (the
    # newest), matching the "apply the newest stored basis" contract.
    bc.store_basis(solved_basis, "TEST", 2023, T, "sha1", cache_dir=tmp_path)
    bc.store_basis(solved_basis, "TEST", 2023, T, "sha2", cache_dir=tmp_path)
    files = sorted(p.name for p in tmp_path.glob("*.npz"))
    assert files == ["TEST_2023_T168.npz"]
    with np.load(tmp_path / "TEST_2023_T168.npz", allow_pickle=False) as z:
        assert z["git_sha"].item() == "sha2"
    # No temp files left behind.
    assert not list(tmp_path.glob(".*tmp*"))


# --------------------------------------------------------------------------- #
# Neutrality — applying the reconstructed basis == cold, across a changed fleet
# --------------------------------------------------------------------------- #


def test_apply_reconstructed_basis_is_price_and_gen_neutral(tmp_path, solved_basis):
    bc.store_basis(solved_basis, "TEST", 2023, T, "abc123", cache_dir=tmp_path)
    reb = bc.load_latest_basis("TEST", 2023, T, cache_dir=tmp_path)

    # Year B: retire U0/U1, add U10/U11, lift demand and costs (same scenario as
    # test_cross_year_warmstart, but the basis has made a disk round-trip).
    fleet_b = _fleet([(f"U{i}", 100 + 5 * i, 7.0 + 0.1 * i) for i in range(2, 12)])
    demand_b = _demand(1.05)
    mc_b = _mc(fleet_b, 3.2)

    cold = _build(fleet_b, demand_b).solve(mc=mc_b.copy())

    warm_model = _build(fleet_b, demand_b)
    assert warm_model.apply_cross_year_basis(reb) is True
    warm = warm_model.solve(mc=mc_b.copy())

    assert cold.objective_value == pytest.approx(warm.objective_value, abs=1e-3)
    assert float(np.abs(cold.prices - warm.prices).max()) < 1e-6
    cold_gen = cold.dispatch.sum(axis=1)
    warm_gen = warm.dispatch.sum(axis=1)
    assert float(np.abs(cold_gen - warm_gen).max()) < 1e-3


def test_reconstructed_apply_matches_live_object(tmp_path, solved_basis):
    # The reconstructed basis must behave identically to carrying the live
    # in-memory object: same installed col/row status vectors after remap.
    bc.store_basis(solved_basis, "TEST", 2023, T, "abc123", cache_dir=tmp_path)
    reb = bc.load_latest_basis("TEST", 2023, T, cache_dir=tmp_path)

    fleet_b = _fleet([(f"U{i}", 100 + 5 * i, 7.0 + 0.1 * i) for i in range(2, 12)])
    demand_b = _demand(1.05)

    m_live = _build(fleet_b, demand_b)
    assert m_live.apply_cross_year_basis(solved_basis) is True
    live_basis = m_live._h.getBasis()

    m_reb = _build(fleet_b, demand_b)
    assert m_reb.apply_cross_year_basis(reb) is True
    reb_basis = m_reb._h.getBasis()

    assert list(live_basis.col_status) == list(reb_basis.col_status)
    assert list(live_basis.row_status) == list(reb_basis.row_status)


# --------------------------------------------------------------------------- #
# Never pickle / self-healing (compat clause 4)
# --------------------------------------------------------------------------- #


def test_stored_file_loads_without_pickle(tmp_path, solved_basis):
    path = bc.store_basis(solved_basis, "TEST", 2023, T, "abc123", cache_dir=tmp_path)
    # allow_pickle=False must succeed — a pickle (object array) can never enter
    # the solve path. Assert no stored array is object-dtype.
    with np.load(path, allow_pickle=False) as z:
        for key in z.files:
            assert z[key].dtype != object, key


def test_object_unit_ids_skip_persist_never_pickle(tmp_path, solved_basis):
    # A non-string/heterogeneous unit_ids list would need allow_pickle=True to
    # round-trip; store_basis refuses (returns None) rather than pickle.
    solved_basis.unit_ids = [object(), object()]
    assert (
        bc.store_basis(solved_basis, "TEST", 2023, T, "x", cache_dir=tmp_path) is None
    )
    assert not list(tmp_path.glob("*.npz"))


def test_schema_mismatch_self_evicts(tmp_path):
    path = bc._cache_path(tmp_path, "TEST", 2023, T)
    np.savez_compressed(
        str(path)[:-4],  # np.savez appends .npz
        schema_key=np.asarray("basis-cache/v0-old"),
        col_status=np.zeros(3, np.int8),
    )
    assert path.exists()
    assert bc.load_latest_basis("TEST", 2023, T, cache_dir=tmp_path) is None
    assert not path.exists()  # deleted -> next bundle close recaptures


def test_corrupt_file_self_evicts(tmp_path):
    path = bc._cache_path(tmp_path, "TEST", 2023, T)
    path.write_bytes(b"not a real npz")
    assert bc.load_latest_basis("TEST", 2023, T, cache_dir=tmp_path) is None
    assert not path.exists()


def test_missing_file_returns_none(tmp_path):
    assert bc.load_latest_basis("TEST", 1999, T, cache_dir=tmp_path) is None


# --------------------------------------------------------------------------- #
# Fingerprint
# --------------------------------------------------------------------------- #


def test_fingerprint_is_sensitive_to_each_input():
    base = bc.layout_fingerprint(["A", "B"], 3, T, "sha")
    assert base == bc.layout_fingerprint(["A", "B"], 3, T, "sha")  # stable
    assert base != bc.layout_fingerprint(["A", "C"], 3, T, "sha")  # unit_ids
    assert base != bc.layout_fingerprint(["A", "B"], 4, T, "sha")  # n_zones
    assert base != bc.layout_fingerprint(["A", "B"], 3, T + 1, "sha")  # T
    assert base != bc.layout_fingerprint(["A", "B"], 3, T, "sha2")  # git sha
    # No cross-boundary collision from delimiter-free concatenation.
    assert bc.layout_fingerprint(["A", "BC"], 3, T, "s") != bc.layout_fingerprint(
        ["AB", "C"], 3, T, "s"
    )


# --------------------------------------------------------------------------- #
# Gate + seed
# --------------------------------------------------------------------------- #


def test_gate_off_without_xyear_env(monkeypatch):
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
    monkeypatch.delenv("MARKET_SIM_WARMSTART_XYEAR", raising=False)
    assert bc.basis_cache_enabled() is False


def test_gate_off_under_determinism_pin(monkeypatch):
    # capture_keeper_goldens.py / replay_keeper.py pin XYEAR=0.
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
    monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "0")
    assert bc.basis_cache_enabled() is False


def test_gate_off_when_intra_year_warmstart_off(monkeypatch):
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "0")
    monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
    assert bc.basis_cache_enabled() is False


def test_gate_on_with_xyear_env(monkeypatch):
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
    monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
    assert bc.basis_cache_enabled() is True


def test_seed_populates_empty_cache_when_enabled(
    tmp_path, monkeypatch, gate_on, solved_basis
):
    monkeypatch.setattr(bc, "BASIS_CACHE_DIR", tmp_path)
    bc.store_basis(solved_basis, "TEST", 2023, T, "abc123", cache_dir=tmp_path)
    cache: list = []
    assert bc.seed_year1_basis(cache, "TEST", 2023, T) is True
    assert len(cache) == 1
    assert np.array_equal(cache[0].col_status, solved_basis.col_status)


def test_seed_noop_when_cache_already_carries_basis(
    tmp_path, monkeypatch, gate_on, solved_basis
):
    monkeypatch.setattr(bc, "BASIS_CACHE_DIR", tmp_path)
    bc.store_basis(solved_basis, "TEST", 2023, T, "abc123", cache_dir=tmp_path)
    sentinel = object()
    cache = [sentinel]
    assert bc.seed_year1_basis(cache, "TEST", 2023, T) is False
    assert cache == [sentinel]  # adjacent-year in-run basis untouched


def test_seed_noop_when_gate_off(tmp_path, monkeypatch, solved_basis):
    monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "0")
    monkeypatch.setattr(bc, "BASIS_CACHE_DIR", tmp_path)
    bc.store_basis(solved_basis, "TEST", 2023, T, "abc123", cache_dir=tmp_path)
    cache: list = []
    assert bc.seed_year1_basis(cache, "TEST", 2023, T) is False
    assert cache == []


def test_seed_noop_when_nothing_cached(tmp_path, monkeypatch, gate_on):
    monkeypatch.setattr(bc, "BASIS_CACHE_DIR", tmp_path)
    cache: list = []
    assert bc.seed_year1_basis(cache, "TEST", 2023, T) is False
    assert cache == []


def test_persist_year_basis_gate_off_writes_nothing(
    tmp_path, monkeypatch, solved_basis
):
    monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "0")
    assert (
        bc.persist_year_basis([solved_basis], "TEST", 2023, T, cache_dir=tmp_path)
        is None
    )
    assert not list(tmp_path.glob("*.npz"))


def test_persist_year_basis_writes_when_enabled(
    tmp_path, monkeypatch, gate_on, solved_basis
):
    path = bc.persist_year_basis([solved_basis], "TEST", 2024, T, cache_dir=tmp_path)
    assert path is not None and path.name == "TEST_2024_T168.npz"
    # Round-trips back to an equivalent basis.
    reb = bc.load_latest_basis("TEST", 2024, T, cache_dir=tmp_path)
    assert reb is not None and reb.unit_ids == solved_basis.unit_ids


def test_persist_year_basis_noop_on_empty_or_none_cache(tmp_path, gate_on):
    assert bc.persist_year_basis([], "TEST", 2023, T, cache_dir=tmp_path) is None
    assert bc.persist_year_basis(None, "TEST", 2023, T, cache_dir=tmp_path) is None
    assert not list(tmp_path.glob("*.npz"))
