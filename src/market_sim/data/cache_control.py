"""Enumerate and clear the package's module-level ``lru_cache`` memoizations.

Why this exists
---------------
The calibration runner solves years strictly sequentially and releases each
year's LP before building the next (``scripts/run_calibration_full.py``, the
``del`` + :func:`gc.collect` + ``malloc_trim(0)`` block). What that block cannot
reach is the *module-level* memoization: this package carries ~26
``@lru_cache(maxsize=None)`` loaders, several of them keyed by ``(iso, year)``
over full-year hourly arrays (``data/miso_outages.py`` alone has four). Those
entries are reachable from the module object, so they are live by definition —
``gc`` will never collect them and ``malloc_trim`` will never return their
pages. They accumulate across the year loop and raise the resident floor every
subsequent year builds on top of.

This module exposes that state so it can be measured rather than guessed, and
cleared at a seam where nothing needs it.

Safety contract
---------------
Clearing a cache is only sound if every cached value is *reconstructible* —
i.e. callers treat the returned object as read-only. That holds for the loader
caches here (they return freshly-built frames/arrays from on-disk data), but it
is not something this module can enforce, so:

* :func:`clear_all_caches` is **explicit** — nothing calls it implicitly.
* It is intended for a **between-years seam**, where the next year rebuilds
  everything it needs anyway, never mid-solve.
* It reports what it cleared, so a caller can log the decision.

Only modules **already imported** are walked. A loader that was never imported
holds nothing, and importing it to ask would allocate the very memory this is
meant to reclaim.
"""

from __future__ import annotations

import sys
from typing import Callable, Iterator, NamedTuple

PACKAGE = "market_sim"


class CacheEntry(NamedTuple):
    """One memoized function and the size of its live cache."""

    qualname: str
    func: Callable
    currsize: int
    hits: int
    misses: int


def iter_cached_functions(package: str = PACKAGE) -> Iterator[CacheEntry]:
    """Yield every ``lru_cache``-wrapped function in the imported package.

    Walks ``sys.modules`` (never imports), so the result reflects exactly the
    loaders this process has actually touched.
    """
    seen: set[int] = set()
    for mod_name, mod in list(sys.modules.items()):
        if mod is None:
            continue
        if mod_name != package and not mod_name.startswith(package + "."):
            continue
        for attr_name in dir(mod):
            try:
                obj = getattr(mod, attr_name)
            except Exception:  # pragma: no cover - defensive on odd descriptors
                continue
            if not callable(obj):
                continue
            info = getattr(obj, "cache_info", None)
            clear = getattr(obj, "cache_clear", None)
            if info is None or clear is None:
                continue
            if id(obj) in seen:
                continue
            seen.add(id(obj))
            try:
                ci = info()
            except Exception:  # pragma: no cover - defensive
                continue
            yield CacheEntry(
                qualname=f"{mod_name}.{attr_name}",
                func=obj,
                currsize=ci.currsize,
                hits=ci.hits,
                misses=ci.misses,
            )


def cache_report(package: str = PACKAGE, min_entries: int = 1) -> list[CacheEntry]:
    """Return the populated caches, largest first by entry count."""
    entries = [e for e in iter_cached_functions(package) if e.currsize >= min_entries]
    return sorted(entries, key=lambda e: -e.currsize)


def clear_all_caches(package: str = PACKAGE) -> tuple[int, int]:
    """Clear every populated ``lru_cache`` in the imported package.

    Returns ``(n_caches_cleared, n_entries_dropped)``. Safe to call when no
    solve is in flight; see this module's safety contract.

    NOTE (miso-90, measured): on the MISO data path these caches together hold
    ~0.02 GB, so clearing them is **not** a remedy for the cross-year resident
    floor — see :func:`retained_footprint`, which is what actually locates it.
    Kept as a measurement/diagnostic tool, deliberately not wired into the
    year loop.
    """
    n_caches = 0
    n_entries = 0
    for entry in list(iter_cached_functions(package)):
        if entry.currsize == 0:
            continue
        entry.func.cache_clear()
        n_caches += 1
        n_entries += entry.currsize
    return n_caches, n_entries


def retained_footprint(*roots: object) -> dict[str, float]:
    """Attribute live heap to object classes that dominate a solve's residual.

    Walks the GC's object graph once and sums the *payload* bytes of the
    container types this model allocates in bulk — numpy arrays (LP matrices,
    hourly series), pandas frames/series, and scipy sparse matrices. Returns
    GB per class plus ``n_*`` counts.

    This is the attribution the year-loop telemetry was missing: the release
    block reports resident and peak RSS, but nothing said *what* the resident
    consisted of, so successive sessions guessed (the ~26 module ``lru_cache``
    memoizations were the standing hypothesis until miso-90 measured them at
    ~0.02 GB). Cheap enough to run once per year at the release seam; never
    call it inside a solve.

    Reading the result: ``ndarray_gb`` is the authoritative total array
    payload. ``pandas_gb`` and ``sparse_gb`` are **attribution slices of it**,
    not additional memory — a DataFrame's blocks and a CSC matrix's
    data/indices/indptr are themselves ndarrays and are already inside
    ``ndarray_gb``.

    Implementation note — why this is a transitive walk and not a scan.
    A plain numeric ndarray is **not GC-tracked**, so ``gc.get_objects()``
    never returns one. Worse, CPython leaves a *container* untracked when all
    its values are untracked, so a ``{"x": np.zeros(...)}`` dict is invisible
    too: scanning tracked objects (even one level of referents deep) reports
    0 GB of arrays while hundreds of MB are live. The walk below therefore
    starts at the tracked set and follows :func:`gc.get_referents`
    **transitively**, which is what reaches untracked containers and the
    arrays inside them.

    KNOWN BLIND SPOT — pass your roots in. CPython 3.11 materialises a frame
    object only on demand, so the **locals of a running function are not
    reachable from the GC graph at all**. Anything held only in a caller's
    local variable (the runner's per-year accumulator lists, for instance) is
    therefore invisible unless it is also referenced from module state. Callers
    that care about such state must pass it explicitly::

        retained_footprint(system_frames, campd_frames, eia930_frames)

    Positional ``roots`` are added to the walk and deduplicated against it, so
    passing an object that is *also* reachable from the graph does not
    double-count it.
    """
    import gc

    try:
        import numpy as np
    except Exception:  # pragma: no cover - numpy is a hard dependency
        return {}

    ndarray_bytes = 0
    ndarray_n = 0
    frame_bytes = 0
    frame_n = 0
    sparse_bytes = 0
    sparse_n = 0
    seen_buffers: set[int] = set()

    def _count_array(arr) -> None:
        nonlocal ndarray_bytes, ndarray_n
        # Views share their base's buffer — count each underlying buffer once.
        base = arr
        while getattr(base, "base", None) is not None:
            base = base.base
        if not isinstance(base, np.ndarray) or id(base) in seen_buffers:
            return
        seen_buffers.add(id(base))
        ndarray_bytes += int(getattr(base, "nbytes", 0) or 0)
        ndarray_n += 1

    stack = gc.get_objects()
    visited: set[int] = {id(stack)}
    stack.extend(roots)
    while stack:
        obj = stack.pop()
        oid = id(obj)
        if oid in visited:
            continue
        visited.add(oid)
        try:
            if isinstance(obj, np.ndarray):
                _count_array(obj)
                continue  # an array's referents hold no further payload
            cls = type(obj)
            mod = getattr(cls, "__module__", "") or ""
            name = cls.__name__
            if mod.startswith("pandas") and name in ("DataFrame", "Series"):
                frame_bytes += int(obj.memory_usage(deep=False).sum())
                frame_n += 1
            elif mod.startswith("scipy.sparse"):
                sparse_n += 1
                for part in ("data", "indices", "indptr"):
                    arr = getattr(obj, part, None)
                    if isinstance(arr, np.ndarray):
                        sparse_bytes += int(arr.nbytes)
            # Modules/classes are roots for the whole program, not for this
            # year's retained state; descending them explodes the walk.
            if isinstance(obj, type):
                continue
            for ref in gc.get_referents(obj):
                if id(ref) not in visited:
                    stack.append(ref)
        except Exception:  # pragma: no cover - never let telemetry break a run
            continue

    gb = 1073741824.0
    return {
        "ndarray_gb": ndarray_bytes / gb,
        "n_ndarray": float(ndarray_n),
        "pandas_gb": frame_bytes / gb,
        "n_pandas": float(frame_n),
        "sparse_gb": sparse_bytes / gb,
        "n_sparse": float(sparse_n),
    }
