"""Process-heap helpers: returning already-freed memory to the kernel.

Dependency-free (``ctypes`` only) and read/free-side only — nothing here can
observe or alter a solve, so every caller is byte-identical by construction.

Lives in ``utils`` rather than next to any one caller because both the
orchestrator's year loop (``scripts/run_calibration_full.py``) and the P0->P1
seam (``market_sim.pipeline.solve.run_energy_solve``) need the same trim at the
two moments a multi-GB HiGHS workspace is released.
"""

from __future__ import annotations

__all__ = ["malloc_trim"]


def malloc_trim() -> bool:
    """Return freed glibc heap to the OS. ``True`` if the trim ran.

    A per-plant ISO-year peaks well over 10 GB inside HiGHS's C++ allocator.
    Dropping the last Python reference frees that memory back to glibc, but
    glibc keeps large fragmented arenas rather than unmapping them, so process
    RSS stays elevated into whatever is built next even though nothing
    Python-visible is retained. That residual — not any accumulated per-year
    frame, which measures well under 0.1 GB/year — is what pushes a solve into
    the OOM killer on a fixed-memory box.

    ``malloc_trim(0)`` releases the free top-of-heap and any fully-free arenas
    back to the kernel. It frees only memory the allocator already considers
    free, so it cannot affect any live object or any solve result. glibc-only;
    a no-op returning ``False`` on musl/macOS or if libc cannot be loaded.
    """
    try:
        import ctypes

        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(ctypes.c_size_t(0))
        return True
    except (OSError, AttributeError):
        return False
