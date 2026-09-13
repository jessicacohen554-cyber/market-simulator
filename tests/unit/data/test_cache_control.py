"""Tests for :mod:`market_sim.data.cache_control`.

The heap-attribution helper exists to stop successive sessions *guessing* what
the calibration runner's cross-year resident floor consists of. A telemetry
tool that silently under-reports is worse than none, so the tests below pin the
two ways this one could lie:

* a plain numeric ndarray is **not GC-tracked**, so a naive
  ``gc.get_objects()`` scan reports 0 GB of arrays no matter how many are live
  (the bug this module was written with, caught in review);
* array *views* share their base's buffer, so counting each view's ``nbytes``
  inflates the total.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd
import pytest

from market_sim.data import cache_control


# --------------------------------------------------------------------------
# retained_footprint
# --------------------------------------------------------------------------
def test_counts_untracked_numeric_arrays_passed_as_a_root():
    """A numeric ndarray inside an untracked dict must be counted.

    Both the array and the dict holding it are untracked by CPython (a dict
    whose values are all untracked stays untracked), so a plain
    ``gc.get_objects()`` scan cannot see either. Passing the holder as a root
    must find it, and the transitive walk must descend into the dict.
    """
    holder = {"big": np.zeros(25_000_000)}  # 200 MB
    before = cache_control.retained_footprint()
    after = cache_control.retained_footprint(holder)
    delta = after["ndarray_gb"] - before["ndarray_gb"]
    assert delta > 0.15, f"untracked array not counted (delta {delta:.4f} GB)"
    assert holder["big"].nbytes == 200_000_000


def test_running_frame_locals_are_the_documented_blind_spot():
    """Pins the limitation the docstring warns about, so it cannot regress
    silently into a false 'we measured everything' claim.

    CPython 3.11 materialises frame objects lazily, so a 200 MB array held ONLY
    in a running function's local is unreachable from the GC graph. The tool
    must therefore under-report it when it is not passed as a root — which is
    exactly why callers are required to pass their accumulators.
    """
    before = cache_control.retained_footprint()
    holder = {"big": np.zeros(25_000_000)}  # local-only, untracked
    unrooted = cache_control.retained_footprint()
    rooted = cache_control.retained_footprint(holder)
    assert unrooted["ndarray_gb"] - before["ndarray_gb"] < 0.01
    assert rooted["ndarray_gb"] - before["ndarray_gb"] > 0.15


def test_roots_are_deduplicated_against_the_graph():
    """Passing an object that is ALSO graph-reachable must not double-count."""
    import market_sim.data.cache_control as mod

    mod._TEST_ROOT = {"big": np.zeros(12_500_000)}  # module state = reachable
    try:
        graph_only = cache_control.retained_footprint()
        with_root = cache_control.retained_footprint(mod._TEST_ROOT)
        assert abs(with_root["ndarray_gb"] - graph_only["ndarray_gb"]) < 0.001
    finally:
        del mod._TEST_ROOT


def test_views_are_not_double_counted():
    before = cache_control.retained_footprint()
    base_arr = np.zeros(12_500_000)  # one 100 MB buffer
    holder = [base_arr[:100], base_arr[100:200], base_arr[200:300]]
    after = cache_control.retained_footprint()
    delta = after["ndarray_gb"] - before["ndarray_gb"]
    # Three views of ONE 100 MB buffer must add ~100 MB (0.093 GB), not ~300.
    assert 0.05 < delta < 0.15, f"views double-counted (delta {delta:.4f} GB)"
    assert len(holder) == 3


def test_pandas_is_a_slice_of_the_array_total_not_an_addition():
    before = cache_control.retained_footprint()
    df = pd.DataFrame({"x": np.zeros(10_000_000)})  # 80 MB
    after = cache_control.retained_footprint()
    d_arr = after["ndarray_gb"] - before["ndarray_gb"]
    d_pd = after["pandas_gb"] - before["pandas_gb"]
    assert d_pd > 0.05, f"frame not counted ({d_pd:.4f} GB)"
    # The frame's block IS an ndarray, so it appears in both figures; the array
    # total must therefore be at least as large as the pandas slice.
    assert d_arr >= d_pd - 1e-6, f"array total {d_arr:.4f} < pandas {d_pd:.4f}"
    assert len(df) == 10_000_000


def test_report_keys_are_stable():
    rep = cache_control.retained_footprint()
    for key in (
        "ndarray_gb",
        "n_ndarray",
        "pandas_gb",
        "n_pandas",
        "sparse_gb",
        "n_sparse",
    ):
        assert key in rep
        assert isinstance(rep[key], float)


# --------------------------------------------------------------------------
# cache enumeration / clearing
# --------------------------------------------------------------------------
def test_enumerates_and_clears_a_real_package_cache():
    """Round-trip against a genuine package cache rather than a stub.

    The example is ``_iso_plant_capacity_cached`` rather than the public
    ``_iso_plant_capacity``: since SPP-38 the vintage-sensitive loaders are
    UNCACHED shims over a directory-keyed core, so the cache lives on the core
    (rule 14 ``[R-ACCURATE]``; ``FINDING-spp-37-order-sensitivity-2026-09-12``).
    What this test is about — that the walker finds, reports and clears a real
    package cache — is unchanged.
    """
    from market_sim.data import outages

    outages._iso_plant_capacity_cached.cache_clear()
    names = {e.qualname for e in cache_control.iter_cached_functions()}
    assert "market_sim.data.outages._iso_plant_capacity_cached" in names

    outages._iso_plant_capacity("MISO")
    populated = {e.qualname: e for e in cache_control.cache_report()}
    entry = populated.get("market_sim.data.outages._iso_plant_capacity_cached")
    assert entry is not None and entry.currsize >= 1

    n_caches, n_entries = cache_control.clear_all_caches()
    assert n_caches >= 1 and n_entries >= 1
    assert cache_control.cache_report() == []


def test_only_walks_imported_modules(monkeypatch):
    """A module that was never imported must not be imported to be asked."""
    import sys

    before = set(sys.modules)
    list(cache_control.iter_cached_functions())
    assert set(sys.modules) == before


def test_ignores_unrelated_packages():
    @lru_cache(maxsize=None)
    def _local(x):
        return x

    _local(1)
    names = {e.qualname for e in cache_control.iter_cached_functions()}
    assert not any(n.endswith("_local") for n in names)


@pytest.mark.parametrize("pkg", ["market_sim", "market_sim.data"])
def test_package_filter_scopes_the_walk(pkg):
    names = {e.qualname for e in cache_control.iter_cached_functions(pkg)}
    assert all(n.startswith(pkg + ".") or n == pkg for n in names)


def test_largest_retained_frames_identifies_the_holding_site():
    """The frame reporter must name a frame well enough to recognise its producer.

    ``retained_footprint`` answers "how much pandas payload is retained"; this
    answers "which frame", which is the question a memory lane has to close.
    Size alone is not an identifier, so the column list is part of the contract.
    """
    frame = pd.DataFrame(
        {"unit_id": np.zeros(1_500_000), "gross_load_mw": np.zeros(1_500_000)}
    )
    rows = cache_control.largest_retained_frames(5, frame)
    assert rows, "a 24 MB rooted frame must be reported"
    mb, nrows, ncols, cols = rows[0]
    assert mb > 20.0, f"payload under-reported ({mb:.1f} MB)"
    assert (nrows, ncols) == (1_500_000, 2)
    assert cols == ["unit_id", "gross_load_mw"]


def test_largest_retained_frames_is_sorted_and_limited():
    """Callers log only the top N, so ordering and the limit are load-bearing.

    Asserted WITHOUT assuming these two frames are the biggest alive in the
    process. ``largest_retained_frames`` enumerates EVERY live frame by design —
    the test right below pins exactly that — so "the top row is my frame" is a
    property of the whole session, not of this function. It held only by luck of
    collection order: bisected 2026-07-27, the fast tier's last order-dependent
    failure was this assertion losing to a 22.9 MB / 126,342 x 20 EIA-923
    plant-level frame that ``tests/scoring/test_calibration_reference_guard.py``
    leaves memoized in an ``lru_cache`` — a legitimately cached loader frame,
    not leaked mutable state, so there is nothing at the other end to reset.
    (Contrast the EIA-860 vintage global fixed in tests/conftest.py, which WAS
    a leak and was fixed at its polluter.)

    The two real invariants are pinned directly instead: the limit is honoured,
    the returned list is sorted by payload descending, and within it ``big``
    outranks ``small``.
    """
    small = pd.DataFrame({"a": np.zeros(200_000)})
    big = pd.DataFrame({"a": np.zeros(2_000_000)})

    assert len(cache_control.largest_retained_frames(1, small, big)) == 1, (
        "limit not honoured"
    )

    rows = cache_control.largest_retained_frames(500, small, big)
    payloads = [r[0] for r in rows]
    assert payloads == sorted(payloads, reverse=True), (
        "not sorted by payload descending"
    )
    ranks = {r[1]: i for i, r in enumerate(rows)}
    assert 2_000_000 in ranks, "the 2M-row frame was not reported at all"
    assert 200_000 in ranks, "the 200k-row frame was not reported at all"
    assert ranks[2_000_000] < ranks[200_000], (
        "the larger frame must outrank the smaller one"
    )


def test_largest_retained_frames_sees_frames_without_a_root():
    """Frames are GC-TRACKED, so this reporter has no running-locals blind spot.

    ``retained_footprint`` under-reports a bare ndarray held only in a running
    function's local, which is why its callers must pass roots. A DataFrame is
    different: it is a tracked object, so ``gc.get_objects()`` enumerates it
    directly. Pinned because the telemetry's claim to list the COMPLETE set of
    live frames rests on it — if this ever regresses, the logged frame list
    silently becomes a subset and the next memory read draws a wrong conclusion.
    """
    frame = pd.DataFrame({"a": np.zeros(3_000_000)})  # local-only, never rooted
    unrooted = cache_control.largest_retained_frames(50)
    assert any(r[1] == 3_000_000 for r in unrooted), (
        "a live frame was invisible without being passed as a root"
    )
    assert len(frame) == 3_000_000


def test_largest_retained_frames_does_not_double_count_a_root():
    """A frame that is both graph-reachable and passed as a root appears once."""
    frame = pd.DataFrame({"a": np.zeros(1_000_000)})
    rows = cache_control.largest_retained_frames(50, frame)
    assert sum(1 for r in rows if r[1] == 1_000_000) == 1


def test_largest_retained_frames_counts_series_like_retained_footprint():
    """Series must be reported, because ``retained_footprint`` counts them.

    Regression test for a real miss: the first version of the walk matched only
    ``DataFrame``, so against a solve whose retained pandas payload was mostly
    Series it returned an EMPTY list while ``retained_footprint`` reported 17
    objects / 0.68 GB — the telemetry printed nothing and looked merely quiet
    rather than broken. The two reporters must agree on what "pandas" means.
    """
    series = pd.Series(np.zeros(2_000_000), name="gross_load_mw")
    rows = cache_control.largest_retained_frames(50, series)
    hit = [r for r in rows if r[1] == 2_000_000]
    assert hit, "a 16 MB Series was invisible to the frame reporter"
    mb, nrows, ncols, cols = hit[0]
    assert mb > 12.0
    assert ncols == 1
    assert cols == ["Series:gross_load_mw"], cols

    # And the pair must not disagree about whether that payload exists.
    fp = cache_control.retained_footprint(series)
    assert fp["n_pandas"] >= 1
