"""Persisted year-1 cross-year warm-start basis cache (wall-clock plan §7 H2).

The backcast calibrate-iterate loop re-solves the same ISO-years over and over
while an offer-curve knob is tuned. Cross-year warm-start already makes years ≥2
of a single run cheap (each P0 warm-starts from the adjacent year's optimal
basis), but the **first** year of every run pays a full cold P0 — 135–235 s on
the plant-level ERCOT / co-optimized MISO LPs (``docs/handoffs/wallclock-
baseline-2026-07.md``). Nothing carries a basis into it because it is the first
solve of the process.

This module closes that gap by persisting each solved year's exported basis to
disk, keyed by ``(iso, year, T)``, so the *next* invocation for the same ISO-year
can seed its year-1 ``xyear_cache`` and warm-start the otherwise-cold P0.

Neutrality
----------
An LP's optimum is independent of the starting basis, so applying a persisted
basis can only change the solve *path*, never the cleared prices, objective, or
per-unit annual generation — exactly the guarantee the in-run cross-year
warm-start already relies on (``pipeline.solve``,
``docs/cross-year-warmstart.md``). ``DispatchModel.apply_cross_year_basis``
remaps surviving units by ``unit_id``, copies the index-stable per-hour blocks,
and hands HiGHS an *alien* basis it repairs — so a basis captured under a
slightly different fleet or an older code SHA is still safe: a stale basis costs
solver iterations, never correctness.

Disposability (compat clause 4)
-------------------------------
The cache is **disposable** and never a frozen surface:

* **NPZ only, never pickle.** Only the compact int8 status vectors, the
  fixed-width ``unit_ids`` string array, and the small set of integer layout /
  row-count scalars are stored — all natively serializable by ``numpy.savez``
  with ``allow_pickle=False``. :func:`load_latest_basis` loads with
  ``allow_pickle=False`` so a pickle can never re-enter the solve path.
* **Schema-keyed, delete-and-recapture on mismatch.** Each file records
  :data:`SCHEMA_KEY`; a file whose key differs (a format change) or that fails to
  load is unlinked and treated as absent — the next bundle close recaptures it.
  Bump :data:`SCHEMA_KEY` whenever the stored array set changes.

Gate
----
Active only when the cross-year warm-start is on for the process
(:func:`basis_cache_enabled` mirrors ``pipeline.solve``'s ``_xwarm`` exactly).
The calibration CLIs default it ON; the goldens/replay determinism env pins
``MARKET_SIM_WARMSTART_XYEAR=0``, so the cache is hard-OFF there — never read,
never written — and the solve path stays byte-identical.
"""

from __future__ import annotations

import hashlib
import logging
import os
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from market_sim.config.paths import DATA_ROOT, REPO_ROOT

if TYPE_CHECKING:
    from market_sim.model.lp import CrossYearBasis

logger = logging.getLogger(__name__)

#: On-disk format version. Any change to the stored array set MUST bump this so
#: older files self-evict (delete-and-recapture) instead of mis-loading.
SCHEMA_KEY = "basis-cache/v1"

#: Disposable cache root, ``results/basis-cache/`` (gitignored). Anchored to
#: ``DATA_ROOT`` like ``config.paths.STRUCTURAL_PRIOR_ARTIFACT_DIR``; folds into
#: a ``config.paths.RESULTS_ROOT`` entry when the results-path lane (plan §7 4D)
#: lands.
BASIS_CACHE_DIR: Path = DATA_ROOT / "results" / "basis-cache"

#: The integer fields that fully reconstruct a frozen ``VariableLayout``. Every
#: column/row offset ``apply_cross_year_basis`` reads is a derived property of
#: these, so preserving them reproduces the in-memory layout exactly.
_LAYOUT_FIELDS = (
    "n_gen",
    "n_zones",
    "n_storage",
    "n_links",
    "T",
    "n_reserve",
    "n_reserve_classes",
    "n_ordc_steps",
    "n_storage_reserve",
    "n_posture",
    "n_rec_acp",
)


def basis_cache_enabled() -> bool:
    """Return whether the persisted year-1 basis cache is active this process.

    Mirrors ``pipeline.solve``'s cross-year gate exactly: the intra-year warm
    start must be on (there is a persistent ``DispatchModel`` whose basis can be
    exported/applied) AND the cross-year gate ``MARKET_SIM_WARMSTART_XYEAR`` must
    be set. The goldens/replay determinism env pins
    ``MARKET_SIM_WARMSTART_XYEAR=0``, so this is hard-OFF there — the cache is
    neither read nor written and the solve path is byte-identical.
    """
    warm = os.environ.get("MARKET_SIM_WARMSTART", "1") != "0"
    xyear = os.environ.get("MARKET_SIM_WARMSTART_XYEAR", "0") != "0"
    return warm and xyear


@lru_cache(maxsize=1)
def _current_git_sha() -> str:
    """Return the repo's short git SHA (cached), or ``""`` if unavailable.

    Recorded in the layout fingerprint so a cached basis carries the code
    version it was captured under. Best-effort — a detached / non-git checkout
    yields ``""`` and the cache still functions (the SHA is provenance, not a
    gate).
    """
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def layout_fingerprint(unit_ids, n_zones: int, T: int, git_sha: str) -> str:
    """Return the sha256 layout fingerprint recorded beside a cached basis.

    Hashes the identity a cross-year basis is only *fresh* under: the ordered
    generator ``unit_ids`` (fleet identity), the zone count, the horizon ``T``,
    and the git SHA (code version). Provenance only — a mismatch never blocks an
    apply (``apply_cross_year_basis`` remaps and repairs), it just records how
    closely a stored basis matches the LP it is being applied to.

    Args:
        unit_ids: Generator unit identifiers in thermal-block column order.
        n_zones: LP zone count.
        T: Horizon (hours).
        git_sha: Short git SHA of the code that produced the basis (``""`` when
            unavailable).

    Returns:
        Hex sha256 digest.
    """
    h = hashlib.sha256()
    # Length-prefix + NUL-join so ids can't collide across the delimiter.
    h.update(str(len(unit_ids)).encode())
    h.update(b"\x00")
    h.update("\x00".join(str(u) for u in unit_ids).encode())
    h.update(f"|{int(n_zones)}|{int(T)}|{git_sha}".encode())
    return h.hexdigest()


def _cache_path(cache_dir: Path, iso: str, year: int, T: int) -> Path:
    """Return the canonical NPZ path for one ``(iso, year, T)`` basis."""
    return cache_dir / f"{iso}_{int(year)}_T{int(T)}.npz"


def store_basis(
    basis: "CrossYearBasis",
    iso: str,
    year: int,
    T: int,
    git_sha: str,
    *,
    cache_dir: Path | None = None,
) -> Path | None:
    """Persist one exported cross-year basis to the disposable NPZ cache.

    Overwrites any existing file for the same ``(iso, year, T)`` atomically, so
    the on-disk file is always the newest capture. Stores only natively
    serializable arrays/scalars (no pickle). Returns the written path, or
    ``None`` when the basis could not be stored without pickling (a non-string /
    heterogeneous ``unit_ids`` list — never the case for a real fleet, whose
    ``unit_ids`` is ``list[str]``).

    Args:
        basis: The basis exported by ``DispatchModel.export_cross_year_basis``.
        iso: ISO code (storage key).
        year: Backcast year (storage key).
        T: Horizon in hours (storage key; a basis is only reusable at equal T).
        git_sha: Short git SHA recorded in the layout fingerprint.
        cache_dir: Override the cache root (tests); defaults to
            :data:`BASIS_CACHE_DIR`.
    """
    layout = basis.layout
    uid_arr = np.asarray(basis.unit_ids)
    if uid_arr.dtype == object:
        # An object-dtype array would force allow_pickle=True to round-trip,
        # violating the never-pickle invariant (compat clause 4). A real fleet's
        # unit_ids is list[str], so this only guards pathological/test inputs:
        # skip caching rather than fall back to pickle.
        logger.warning(
            "basis-cache: %s %d unit_ids are not string/int-serializable; "
            "skipping persist (never pickle)",
            iso,
            year,
        )
        return None

    payload: dict[str, np.ndarray] = {
        "schema_key": np.asarray(SCHEMA_KEY),
        "col_status": np.asarray(basis.col_status, dtype=np.int8),
        "row_status": np.asarray(basis.row_status, dtype=np.int8),
        "unit_ids": uid_arr,
        "n_rows": np.asarray(int(basis.n_rows)),
        "n_energy_rows": np.asarray(int(basis.n_energy_rows)),
        "n_storage_rows": np.asarray(int(basis.n_storage_rows)),
        "fingerprint": np.asarray(
            layout_fingerprint(basis.unit_ids, layout.n_zones, T, git_sha)
        ),
        "git_sha": np.asarray(str(git_sha)),
        "iso": np.asarray(str(iso)),
        "year": np.asarray(int(year)),
    }
    for field in _LAYOUT_FIELDS:
        payload[field] = np.asarray(int(getattr(layout, field)))

    cache_dir = BASIS_CACHE_DIR if cache_dir is None else Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(cache_dir, iso, year, T)
    # Write to a distinct temp name that already ends in ``.npz`` (np.savez
    # appends ``.npz`` to any name that lacks it), then atomically replace so a
    # concurrent reader never sees a half-written file.
    tmp = cache_dir / f".{iso}_{int(year)}_T{int(T)}.{os.getpid()}.tmp.npz"
    try:
        np.savez_compressed(tmp, **payload)
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    return path


def load_latest_basis(
    iso: str,
    year: int,
    T: int,
    *,
    cache_dir: Path | None = None,
) -> "CrossYearBasis | None":
    """Load the newest persisted basis for ``(iso, year, T)`` (or ``None``).

    Reconstructs a :class:`~market_sim.model.lp.CrossYearBasis` — including its
    frozen ``VariableLayout`` — from the stored scalars/arrays. Loads with
    ``allow_pickle=False``: a pickle (object array) can never re-enter the solve
    path. A missing, corrupt, or schema-mismatched file is unlinked and reported
    as absent (delete-and-recapture, compat clause 4) so the cache self-heals.

    Args:
        iso: ISO code.
        year: Backcast year.
        T: Horizon in hours.
        cache_dir: Override the cache root (tests); defaults to
            :data:`BASIS_CACHE_DIR`.
    """
    # Lazy import: CrossYearBasis/VariableLayout live in market_sim.model.lp; a
    # module-level import would pull the LP package in for every consumer of
    # this cache helper (and risks an import cycle through pipeline).
    from market_sim.model.lp import CrossYearBasis, VariableLayout

    cache_dir = BASIS_CACHE_DIR if cache_dir is None else Path(cache_dir)
    path = _cache_path(cache_dir, iso, year, T)
    if not path.exists():
        return None
    try:
        with np.load(path, allow_pickle=False) as data:
            stored_key = str(data["schema_key"].item())
            if stored_key != SCHEMA_KEY:
                raise ValueError(f"schema key {stored_key!r} != {SCHEMA_KEY!r}")
            layout = VariableLayout(
                **{field: int(data[field]) for field in _LAYOUT_FIELDS}
            )
            basis = CrossYearBasis(
                col_status=np.asarray(data["col_status"], dtype=np.int8),
                row_status=np.asarray(data["row_status"], dtype=np.int8),
                layout=layout,
                unit_ids=data["unit_ids"].tolist(),
                n_rows=int(data["n_rows"]),
                n_energy_rows=int(data["n_energy_rows"]),
                n_storage_rows=int(data["n_storage_rows"]),
            )
    except Exception as exc:  # disposable: any bad read self-evicts
        logger.info("basis-cache: discarding %s (%s)", path.name, exc)
        try:
            path.unlink()
        except OSError:
            pass
        return None
    return basis


def seed_year1_basis(
    xyear_cache: "list | None",
    iso: str,
    year: int,
    T: int,
) -> bool:
    """Seed an empty cross-year cache from the persisted ``(iso, year, T)`` basis.

    Called at the top of a *fresh* backcast year when no in-run basis is carried
    — year-1, or the first fresh year after a ``--reuse-solved`` gap (where the
    loop clears ``xyear_cache`` so a non-adjacent year's basis is not reused).
    A no-op when the feature is off, the holder is ``None``, the holder already
    carries an adjacent year's basis, or no basis is cached for this ISO-year.

    The apply is *opportunistic*: ``pipeline.solve`` hands the seeded basis to
    ``DispatchModel.apply_cross_year_basis`` at year-1 P0, which remaps/repairs
    and falls back cold, so a stale seed costs solver iterations, never
    correctness.

    Returns:
        ``True`` when a basis was seeded, else ``False``.
    """
    if not basis_cache_enabled() or xyear_cache is None or xyear_cache:
        return False
    basis = load_latest_basis(iso, year, T)
    if basis is None:
        return False
    xyear_cache[:] = [basis]
    logger.info(
        "basis-cache: seeded %s %d P0 from persisted basis (T=%d)", iso, year, T
    )
    return True


def persist_year_basis(
    xyear_cache: "list | None",
    iso: str,
    year: int,
    T: int,
    *,
    cache_dir: Path | None = None,
) -> "Path | None":
    """Persist the just-solved year's exported basis (per-year, best-effort).

    Called from the shared per-year core after the solve, when ``xyear_cache``
    carries this year's optimal basis (the same basis the in-run cross-year
    warm-start hands to the next year). Writing it here — rather than at bundle
    close — is crash-safe: a completed year's basis is on disk even if a later
    year fails.

    A no-op when the feature is off or the holder is ``None``/empty. Any store
    failure is logged and swallowed — the cache is a performance optimization,
    never a correctness dependency, so a full disk must not fail an
    otherwise-complete calibration year. Returns the written path (or ``None``).

    Args:
        xyear_cache: The cross-year cache holder carrying this year's basis.
        iso: ISO code.
        year: Backcast year just solved.
        T: Horizon in hours.
        cache_dir: Override the cache root (tests).
    """
    if not basis_cache_enabled() or not xyear_cache:
        return None
    try:
        return store_basis(
            xyear_cache[0], iso, year, T, _current_git_sha(), cache_dir=cache_dir
        )
    except Exception as exc:
        logger.warning("basis-cache: failed to persist %s %d (%s)", iso, year, exc)
        return None


__all__ = [
    "SCHEMA_KEY",
    "BASIS_CACHE_DIR",
    "basis_cache_enabled",
    "layout_fingerprint",
    "store_basis",
    "load_latest_basis",
    "seed_year1_basis",
    "persist_year_basis",
]
