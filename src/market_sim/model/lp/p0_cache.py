"""Content-addressed cache of a cold LP solve, exact by construction (PERF-C S6).

80-96 % of a calibration year is inside HiGHS ``run()``
(``docs/handoffs/PRECOMMIT-perfc-orchestration-2026-09-20.md`` §0), and the
**P0** pass — 80 s on NEISO, 300-640 s on ERCOT / CAISO / MISO / PJM — is
re-solved from cold on every replay, every re-gate, every held-out-year
touchpoint and every knob iteration whose knob only enters **P1** (the startup
markup, the ERCOT SWCAP clip, the P1-only offer surfaces, the bid-max seam).
This module lets that pass be *replayed from disk* instead.

DEFAULT **OFF**: exact for the pass it replays, WARM-START-CLASS for the next one
--------------------------------------------------------------------------------
The key is the LP itself: a blake2b digest over the exact bytes handed to HiGHS
— the three CSR arrays, the four bound vectors, the column/row counts, the
horizon, the ordered ``unit_ids``, the cost vector, the HiGHS version and the
solver options the model sets. Single-threaded HiGHS is deterministic
(``docs/cross-year-warmstart.md``), so **the same LP bytes give the same
solution**, and a hit returns the answer the cold solve produced. That half held
on measurement: over NEISO's six keeper years a hit reproduced the cold P0's
objective to every printed digit in **0 simplex iterations**.

**What it does not buy is the state the NEXT pass starts from, and that is why
this ships default OFF.** On the route where P1 re-solves the same live model,
HiGHS enters P1's warm ``run()`` from whatever internal factorization the P0
pass left behind — and installing an optimal basis is not the same internal
state as *searching* to it over 181,129 iterations, even though the basis is
identical. Measured, NEISO keeper, all six years: P1's objective was identical
to every printed digit and total annual generation matched to four decimals
(Δ net +0.0000 GWh), but P1's iteration count moved every year (2020:
63,420 → 63,493) and its dispatch reshuffled across marginal ties by
0.079–0.131 % of annual generation, with ``system.price`` moving at 6.4e-16
relative. Same optimum, different vertex — the byte gate refuses it.

This is the **identical failure mode** PERF-C S2 measured when it tried to skip
``_marginal_emission_rate`` on P0 (``docs/handoffs/FINDING-perfc-s2-p0-slim-
2026-09-20.md`` §2), for the identical reason, and it gets the identical
disposition: available to a lane holding a warm-start-class mandate, validating
with ``scripts/diagnostics/diff_warmstart_bundles.py`` rather than
``--mode byte``, exactly as ``MARKET_SIM_P1_FLOOR_INPLACE`` is
(``pipeline/solve.py``). A **Tier-B** entry storing the solution vectors would
not rescue it: the P0 *result* is already exact — what moves is P1's path, which
no stored P0 output can restore.

Full measurement, and what a successor would need:
``docs/handoffs/FINDING-perfc-s6-p0-cache-2026-09-22.md``.

This is rule 7 ``[R-PARQUET]``'s check-before-run caching discipline applied one
level down, at the solve rather than at the bundle.

How it differs from ``pipeline.basis_cache`` (H2)
-------------------------------------------------
That module persists a basis keyed on ``(iso, year, T)`` in order to
*warm-start* a later solve: an approximate key, a path-only guarantee, and
default-OFF since rule 36 ``[R-YEAR-ISOLATION]``. This cache is different in
kind — the key is the LP's own content, so a hit is a **replay**, not a warm
start. The npz conventions are deliberately reused (int8 status vectors,
``allow_pickle=False``, a gitignored dir behind a ``config/paths.py`` constant,
delete-and-recapture on any bad read); the key is not.

Rule 24 ``[R-REGISTRY]``: this IS solve-affecting, and it is declared as such
-----------------------------------------------------------------------------
``MARKET_SIM_P0_CACHE`` (default **OFF**; ``1``/``true``/``on`` arms it) was
designed to be a pure performance switch and the measurement above says it is
not one: on the live-model P1 route it moves the reported vertex. It is
therefore **not** a free knob, and this module does not claim it is. Rule 36
``[R-YEAR-ISOLATION]`` (e) is the standing precedent — two solve-path env knobs
carried for a year on a basis-neutrality claim measurement later falsified — and
the duty it lays down applies here from the start rather than after the fact:
**a lane that arms this owes the declaration**, and a lane that wants it on by
default owes the rule-36(e) treatment, which is to promote it to
``ScenarioConfig`` plus the cache key or to delete it outright (rule 26
``[R-DELETE]``: deleted, not zeroed). It was measured before landing, not after,
and it lands OFF.

With the switch off nothing here runs at all: no digest is taken, no key is
computed, and the cache is neither read nor written.

Scope, stated honestly
----------------------
When armed, served only for the **first solve on a freshly built model** that
had no basis pre-installed:

* that is the P0 pass on the warm route, and the P1 rebuild on the cold-P1
  route — both of which HiGHS solves from nothing;
* it is **not** a second ``solve()`` on a live model, because
  ``model.lp.inplace_floor`` mutates column bounds between P0 and P1 and the
  structural digest is taken at ``__init__``: a stale digest is the one way a
  content-addressed key could lie, so that route is excluded by construction
  rather than by care;
* it is **not** a solve whose caller pre-installed a basis (the cross-year
  warm start, the same-year P1 seed). Those are warm-start-class routes that
  have chosen their own starting point; the cache neither reads nor writes
  there, so no route's vertex is moved by this module's presence.

Which workflows hit, and which never will: any re-run of an identical LP hits
(replays, re-gates, touchpoints, and every P1-only knob iteration, whose P0 LP
is byte-identical). Nothing that changes ``mc_base`` — the
``offer_curve_by_group`` band multipliers included — the fleet, outages,
demand, renewables or the network hits, because those change the LP, which is
the key.

Determinism precondition
------------------------
Entries are served and written **only** when ``MARKET_SIM_HIGHS_THREADS``
resolves to ``1``. Multi-threaded dual simplex is not bit-reproducible, so a
multi-threaded cold solve is not a value another run can be handed; with the
pin absent the cache is inert in both directions. The calibration runners set
the pin themselves (``scripts/lib/solve_container.ensure_solve_container``), and
the goldens/replay determinism env pins it explicitly.

Disposability
-------------
NPZ only, never pickle; every stored array is an int8 / float64 / int scalar
that ``numpy.savez`` serializes natively and :func:`load` reads back with
``allow_pickle=False``. Each file records :data:`SCHEMA_KEY`; a file whose key
differs, whose shapes do not match the LP, or that fails to load at all is
unlinked and reported as absent. The whole tree is deletable at any time.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from market_sim.config.paths import P0_CACHE_DIR

logger = logging.getLogger(__name__)

#: On-disk format version. Any change to the stored array set MUST bump this so
#: older files self-evict (delete-and-recapture) instead of mis-loading.
SCHEMA_KEY = "p0-cache/v1"

#: Key schema version, mixed into the digest itself. Bump whenever WHAT is
#: hashed changes, so an old key can never collide with a new one.
KEY_SCHEMA = "p0-key/v1"

#: Env switch, default **OFF**. See the module docstring: a hit reproduces the
#: cold P0 exactly, but on the live-model P1 route it moves the NEXT pass's
#: simplex path, which is warm-start-class and measured. Arming it is a
#: declarable, solve-affecting choice.
ENV_SWITCH = "MARKET_SIM_P0_CACHE"

#: The determinism pin the cache requires in both directions.
ENV_THREADS = "MARKET_SIM_HIGHS_THREADS"

#: Entries kept per LP *structure* (one directory per structural digest, i.e.
#: per ISO-year matrix). Three covers the pass shapes one iteration produces —
#: P0 base, a cold P1 bid, and one spare — so a P1-only knob sweep keeps
#: hitting its P0 entry instead of evicting it.
MAX_ENTRIES_PER_STRUCTURE = 3

#: Structure directories kept overall (evict oldest by mtime). Twelve holds a
#: six-year span under two configurations.
MAX_STRUCTURES = 12

#: Total on-disk budget. The dominant term is a Tier-B entry's solution
#: vectors (~200-400 MB on ERCOT / MISO), so the byte budget — not the entry
#: counts — is what actually protects a session's disk allowance.
MAX_CACHE_BYTES = 6 * 1024**3


def cache_switch_on() -> bool:
    """Return whether the ``MARKET_SIM_P0_CACHE`` switch is armed (default OFF).

    Default OFF is the measured posture, not a caution: see the module
    docstring. Anything other than an explicit truthy value leaves the cache
    completely inert — no digest, no key, no read, no write.
    """
    return os.environ.get(ENV_SWITCH, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def determinism_pin_ok() -> bool:
    """Return whether HiGHS is pinned to one thread.

    Multi-threaded dual simplex is not bit-reproducible
    (``docs/cross-year-warmstart.md``), so a solution captured under it is not a
    value another process may be handed. Unset counts as NOT pinned — HiGHS then
    chooses its own thread count.
    """
    raw = os.environ.get(ENV_THREADS, "").strip()
    try:
        return int(raw) == 1
    except (TypeError, ValueError):
        return False


def p0_cache_enabled() -> bool:
    """Return whether the cache may be read or written in this process."""
    return cache_switch_on() and determinism_pin_ok()


def structure_digest(
    *,
    starts: np.ndarray,
    indices: np.ndarray,
    values: np.ndarray,
    col_lower: np.ndarray,
    col_upper: np.ndarray,
    row_lower: np.ndarray,
    row_upper: np.ndarray,
    total_columns: int,
    n_rows: int,
    T: int,
    unit_ids,
) -> str:
    """Digest the LP structure exactly as HiGHS received it.

    Every argument is the array or scalar that was (or is about to be) passed to
    ``addCols`` / ``addRows``, hashed by its raw buffer so the digest is the
    bytes themselves rather than a summary of them. Arrays are hashed through
    the buffer protocol — no ``tobytes()`` copy, which at ~86 M nonzeros would be
    a gigabyte of avoidable transient at the build peak.

    Args:
        starts: CSR row-start offsets (int32) handed to ``addRows``.
        indices: CSR column indices (int32).
        values: CSR coefficients (float64).
        col_lower: Column lower bounds, post ``kHighsInf`` substitution.
        col_upper: Column upper bounds, post ``kHighsInf`` substitution.
        row_lower: Row lower bounds, post ``kHighsInf`` substitution.
        row_upper: Row upper bounds, post ``kHighsInf`` substitution.
        total_columns: ``layout.total_columns``.
        n_rows: Constraint-row count.
        T: Horizon in hours.
        unit_ids: Generator identifiers in thermal-block column order. Included
            because two fleets can share a matrix shape while meaning different
            units, and the column ORDER is what every downstream extraction
            slices by.

    Returns:
        Hex blake2b digest (32 bytes) of the structure.
    """
    h = hashlib.blake2b(digest_size=32)
    h.update(KEY_SCHEMA.encode())
    h.update(
        f"|cols={int(total_columns)}|rows={int(n_rows)}|T={int(T)}"
        f"|nnz={int(np.asarray(indices).size)}|nunits={len(unit_ids)}|".encode()
    )
    for name, arr in (
        ("starts", starts),
        ("indices", indices),
        ("values", values),
        ("col_lower", col_lower),
        ("col_upper", col_upper),
        ("row_lower", row_lower),
        ("row_upper", row_upper),
    ):
        a = np.ascontiguousarray(arr)
        h.update(f"|{name}:{a.dtype.str}:{a.shape}|".encode())
        h.update(memoryview(a).cast("B"))
    # Length-prefix + NUL-join so ids cannot collide across the delimiter.
    h.update(f"|units={len(unit_ids)}|".encode())
    h.update("\x00".join(str(u) for u in unit_ids).encode())
    return h.hexdigest()


def solve_key(structure: str, cost: np.ndarray, options: str) -> str:
    """Extend a structure digest with the objective and the solver settings.

    The three together are everything that determines the answer: the feasible
    region (``structure``), the objective (``cost``), and how HiGHS is
    configured to search it (``options`` — the version string, the thread pin
    and the options the model sets).

    Args:
        structure: The digest returned by :func:`structure_digest`.
        cost: The cost vector installed via ``changeColsCost``.
        options: The solver-settings signature (see
            ``DispatchModel._highs_option_signature``).

    Returns:
        Hex blake2b digest (32 bytes) naming this exact solve.
    """
    h = hashlib.blake2b(digest_size=32)
    h.update(KEY_SCHEMA.encode())
    h.update(f"|struct={structure}|opts={options}|".encode())
    c = np.ascontiguousarray(cost)
    h.update(f"|cost:{c.dtype.str}:{c.shape}|".encode())
    h.update(memoryview(c).cast("B"))
    return h.hexdigest()


@dataclass(frozen=True)
class CachedSolve:
    """One replayed solve: the optimal basis, and the provenance of its capture.

    The basis alone is stored, and that is a measured choice rather than a first
    step. The brief's fallback was to store the solution vectors too
    (``col_value`` / ``row_dual`` / ``col_dual`` / ``row_value``, ~200-400 MB per
    entry on ERCOT / MISO) in case a zero-iteration re-run differed from the cold
    solve at float epsilon. It does not: the replayed P0 reports the cold solve's
    objective to every printed digit in 0 iterations, over all six NEISO keeper
    years. The difference the byte gate DID find is in the state the NEXT pass
    starts from, which is not an output and which no stored vector could restore
    — so the vectors would have bought nothing and are not stored
    (``docs/handoffs/FINDING-perfc-s6-p0-cache-2026-09-22.md`` §3).

    Attributes:
        col_status: Column basis statuses (int8, ``HighsBasisStatus`` ordinals).
        row_status: Row basis statuses (int8).
        objective: The objective value the cold solve reported. Provenance only
            — the replayed ``h.run()`` recomputes it.
        simplex_iterations: Iterations the cold solve spent. Provenance only.
    """

    col_status: np.ndarray
    row_status: np.ndarray
    objective: float
    simplex_iterations: int


#: Provenance of the most recent FIRST solve in this process, as
#: ``{"key": str | None, "hit": bool}`` — set by ``DispatchModel.solve`` and read
#: by ``pipeline.solve`` right after the P0 call. A process-level record rather
#: than a return value because the cold P0 route goes through ``solve_dispatch``,
#: which builds its model internally and returns only a ``DispatchResult``;
#: widening that dataclass for a diagnostic would change the contract PERF-C S2's
#: slim-extract test pins. Diagnostic only — nothing reads it back into a solve.
_LAST_SOLVE: "dict | None" = None


def record_solve(key: "str | None", hit: bool) -> None:
    """Record this process's most recent first-solve cache provenance."""
    global _LAST_SOLVE
    _LAST_SOLVE = {"key": key, "hit": bool(hit)}


def last_solve() -> "dict | None":
    """Return a copy of the last recorded provenance, or ``None``."""
    return dict(_LAST_SOLVE) if _LAST_SOLVE is not None else None


def reset_last_solve() -> None:
    """Clear the recorded provenance (call before the solve you want to read)."""
    global _LAST_SOLVE
    _LAST_SOLVE = None


def _bucket(cache_dir: Path, structure: str) -> Path:
    """Return the per-structure directory holding one LP's entries."""
    return Path(cache_dir) / structure[:16]


def _entry_path(cache_dir: Path, structure: str, key: str) -> Path:
    """Return the canonical NPZ path for one ``(structure, key)`` solve."""
    return _bucket(cache_dir, structure) / f"{key}.npz"


def load(
    structure: str,
    key: str,
    *,
    n_cols: int,
    n_rows: int,
    cache_dir: "Path | None" = None,
) -> "CachedSolve | None":
    """Load the cached solve for ``key`` (or ``None`` when absent/unusable).

    A missing, corrupt, schema-mismatched or wrong-shaped file is unlinked and
    reported as absent (delete-and-recapture) so the tree self-heals. The shape
    check is belt-and-braces: the key already pins the column and row counts, so
    a mismatch here means a hash collision or a hand-edited file, and either way
    the safe answer is "no entry".

    Args:
        structure: The LP's structure digest (selects the bucket directory).
        key: The full solve key.
        n_cols: Expected column count.
        n_rows: Expected constraint-row count.
        cache_dir: Override the cache root (tests); defaults to
            :data:`~market_sim.config.paths.P0_CACHE_DIR`.
    """
    cache_dir = P0_CACHE_DIR if cache_dir is None else Path(cache_dir)
    path = _entry_path(cache_dir, structure, key)
    if not path.exists():
        return None
    try:
        with np.load(path, allow_pickle=False) as data:
            stored_key = str(data["schema_key"].item())
            if stored_key != SCHEMA_KEY:
                raise ValueError(f"schema key {stored_key!r} != {SCHEMA_KEY!r}")
            if str(data["key"].item()) != key:
                raise ValueError("stored key does not match its filename")
            col_status = np.asarray(data["col_status"], dtype=np.int8)
            row_status = np.asarray(data["row_status"], dtype=np.int8)
            if col_status.size != int(n_cols) or row_status.size != int(n_rows):
                raise ValueError(
                    f"basis shape ({col_status.size}, {row_status.size}) != "
                    f"LP shape ({int(n_cols)}, {int(n_rows)})"
                )
            entry = CachedSolve(
                col_status=col_status,
                row_status=row_status,
                objective=float(data["objective"]),
                simplex_iterations=int(data["simplex_iterations"]),
            )
    except Exception as exc:  # disposable: any bad read self-evicts
        logger.info("p0-cache: discarding %s (%s)", path.name, exc)
        try:
            path.unlink()
        except OSError:
            pass
        return None
    # Touch so eviction's oldest-mtime order reflects USE, not just capture.
    try:
        os.utime(path, None)
    except OSError:
        pass
    return entry


def store(
    structure: str,
    key: str,
    entry: CachedSolve,
    *,
    cache_dir: "Path | None" = None,
) -> "Path | None":
    """Persist one solved LP's basis (and Tier-B vectors) to the cache.

    Written to a temp name and atomically replaced, so a concurrent reader never
    sees a half-written file. Any failure is logged and swallowed: the cache is
    a performance optimization and never a correctness dependency, so a full
    disk must not fail an otherwise-complete solve.

    Args:
        structure: The LP's structure digest (selects the bucket directory).
        key: The full solve key.
        entry: The basis/solution to store.
        cache_dir: Override the cache root (tests).

    Returns:
        The written path, or ``None`` when the entry could not be stored.
    """
    cache_dir = P0_CACHE_DIR if cache_dir is None else Path(cache_dir)
    bucket = _bucket(cache_dir, structure)
    payload: dict[str, np.ndarray] = {
        "schema_key": np.asarray(SCHEMA_KEY),
        "key": np.asarray(key),
        "structure": np.asarray(structure),
        "col_status": np.asarray(entry.col_status, dtype=np.int8),
        "row_status": np.asarray(entry.row_status, dtype=np.int8),
        "objective": np.asarray(float(entry.objective)),
        "simplex_iterations": np.asarray(int(entry.simplex_iterations)),
    }
    path = _entry_path(cache_dir, structure, key)
    tmp = bucket / f".{key[:16]}.{os.getpid()}.tmp.npz"
    try:
        bucket.mkdir(parents=True, exist_ok=True)
        # Uncompressed: an int8 status vector over 21.8 M columns has little
        # structure to exploit, and a hit must stay cheap — decompressing on the
        # read path would spend the win. Measured: 7.70-7.88 MB per NEISO year.
        np.savez(tmp, **payload)
        os.replace(tmp, path)
    except Exception as exc:
        logger.warning("p0-cache: failed to store %s (%s)", path.name, exc)
        try:
            tmp.unlink()
        except OSError:
            pass
        return None
    evict(cache_dir=cache_dir)
    return path


def _entries(bucket: Path) -> "list[Path]":
    """Return a bucket's entry files, oldest mtime first."""
    try:
        # Skip the dot-prefixed temp names ``store`` writes before its atomic
        # replace — a concurrent writer's half-written file is not an entry, and
        # evicting it would race its own ``os.replace``.
        files = [
            p
            for p in bucket.iterdir()
            if p.suffix == ".npz" and not p.name.startswith(".")
        ]
    except OSError:
        return []
    return sorted(files, key=lambda p: p.stat().st_mtime)


def evict(*, cache_dir: "Path | None" = None) -> "list[Path]":
    """Enforce the three retention budgets, oldest mtime first.

    Run after every :func:`store`. The budgets are, in order: at most
    :data:`MAX_ENTRIES_PER_STRUCTURE` entries per LP structure, at most
    :data:`MAX_STRUCTURES` structure directories, and at most
    :data:`MAX_CACHE_BYTES` on disk overall.

    Returns:
        The paths removed.
    """
    cache_dir = P0_CACHE_DIR if cache_dir is None else Path(cache_dir)
    removed: list[Path] = []
    if not cache_dir.exists():
        return removed

    def _drop(path: Path) -> None:
        try:
            path.unlink()
            removed.append(path)
        except OSError:
            pass

    buckets = [p for p in cache_dir.iterdir() if p.is_dir()]
    # (1) per-structure entry count.
    for bucket in buckets:
        files = _entries(bucket)
        for path in files[: max(0, len(files) - MAX_ENTRIES_PER_STRUCTURE)]:
            _drop(path)

    # (2) structure-directory count. An empty bucket is removed outright.
    live: list[tuple[float, Path]] = []
    for bucket in buckets:
        files = _entries(bucket)
        if not files:
            try:
                bucket.rmdir()
            except OSError:
                pass
            continue
        live.append((max(p.stat().st_mtime for p in files), bucket))
    live.sort()
    for _, bucket in live[: max(0, len(live) - MAX_STRUCTURES)]:
        for path in _entries(bucket):
            _drop(path)
        try:
            bucket.rmdir()
        except OSError:
            pass

    # (3) total bytes, oldest first across every surviving bucket.
    survivors: list[Path] = []
    for bucket in cache_dir.iterdir():
        if bucket.is_dir():
            survivors.extend(_entries(bucket))
    survivors.sort(key=lambda p: p.stat().st_mtime)
    total = 0
    sizes: list[tuple[Path, int]] = []
    for path in survivors:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        sizes.append((path, size))
        total += size
    for path, size in sizes:
        if total <= MAX_CACHE_BYTES:
            break
        _drop(path)
        total -= size
    return removed


__all__ = [
    "SCHEMA_KEY",
    "KEY_SCHEMA",
    "ENV_SWITCH",
    "ENV_THREADS",
    "MAX_ENTRIES_PER_STRUCTURE",
    "MAX_STRUCTURES",
    "MAX_CACHE_BYTES",
    "CachedSolve",
    "cache_switch_on",
    "determinism_pin_ok",
    "p0_cache_enabled",
    "record_solve",
    "last_solve",
    "reset_last_solve",
    "structure_digest",
    "solve_key",
    "load",
    "store",
    "evict",
]
