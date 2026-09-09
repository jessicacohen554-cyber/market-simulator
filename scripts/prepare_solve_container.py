"""Make an ephemeral solve container safe for a heavy per-plant ISO LP.

**The defect this closes.** ``scripts/run_isos_concurrent.py``'s measured memory
registry puts PJM's single-solve peak RSS at **13.0 GB** and MISO's at 11.5 GB,
and the wallclock/RSS baseline those numbers came from was taken on a host with
a **pre-existing** ``/swapfile`` (``docs/handoffs/perf-recheck-2026-08.md`` §1.2).
A Claude Code Remote container is 15 GiB with **zero swap**, so a PJM solve runs
with a ~2 GiB margin and no backstop: the kernel OOM-kills it (SIGKILL, child
return code -9) instead of paging. Session pjm-fuelvintage-1 hit exactly this at
13.75 GiB RSS on 2026-09-09.

Two things fix it, and this script does both:

1. **Swap.** A swapfile turns a fatal peak into a slow one. Verified working in
   the CCR container class (``fallocate`` + ``mkswap`` + ``swapon`` all succeed
   as root). Sized to bring RAM+swap to ``--target-gb``, bounded by free disk.
2. **The env pins** ``MALLOC_ARENA_MAX=2``, ``MARKET_SIM_HIGHS_THREADS=1``,
   ``OMP_NUM_THREADS=1`` — the single-thread / arena-pinned profile the goldens
   and every wallclock capture use (``run_isos_concurrent._CHILD_ENV_PINS``), so
   per-solve memory and determinism match a solo run. **They do not change the
   LP optimum** (``model/lp/model.py``: thread count is a workspace choice, and
   the comment there records the OOM it exists to prevent).

Env pins cannot be exported into a parent shell from a child process, so this
prints them and, with ``--emit-exports``, prints ONLY the ``export`` lines for
``eval "$(python3 scripts/prepare_solve_container.py --emit-exports)"``.

Usage::

    python3 scripts/prepare_solve_container.py            # provision + report
    eval "$(python3 scripts/prepare_solve_container.py --emit-exports)"
    python3 scripts/prepare_solve_container.py --check    # report only, no writes
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("prepare_solve_container")

#: The single-thread / arena-pinned profile every golden and wallclock capture
#: uses. Mirrors ``run_isos_concurrent._CHILD_ENV_PINS`` — keep them equal.
SOLVE_ENV_PINS: dict[str, str] = {
    "MALLOC_ARENA_MAX": "2",
    "MARKET_SIM_HIGHS_THREADS": "1",
    "OMP_NUM_THREADS": "1",
}

#: Default RAM+swap floor. PJM peaks at 13.0 GB measured; 24 GiB leaves real
#: headroom on a 15 GiB box without demanding more disk than a container has.
DEFAULT_TARGET_GB: int = 24

#: Never consume the last of the disk allowance — a solve also writes parquet.
DISK_RESERVE_GB: int = 6

SWAPFILE = Path("/swapfile-marketsim")


def _gib(n_bytes: float) -> float:
    """Bytes -> GiB."""
    return n_bytes / (1024**3)


def _meminfo_gb() -> tuple[float, float]:
    """Return ``(total_ram_gb, total_swap_gb)`` from /proc/meminfo."""
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, _, rest = line.partition(":")
        if key in ("MemTotal", "SwapTotal"):
            values[key] = int(rest.strip().split()[0])  # kB
    return values.get("MemTotal", 0) / (1024**2), values.get("SwapTotal", 0) / (1024**2)


def provision_swap(target_gb: int, dry_run: bool = False) -> int:
    """Add a swapfile so RAM+swap reaches ``target_gb``. Returns GiB added."""
    ram_gb, swap_gb = _meminfo_gb()
    deficit = target_gb - (ram_gb + swap_gb)
    if deficit <= 0.5:
        logger.info(
            "swap: none needed (RAM %.1f + swap %.1f >= target %d GiB)",
            ram_gb,
            swap_gb,
            target_gb,
        )
        return 0

    free_gb = _gib(shutil.disk_usage("/").free)
    add_gb = int(min(deficit, max(0.0, free_gb - DISK_RESERVE_GB)))
    if add_gb < 1:
        logger.warning(
            "swap: CANNOT provision — need %.1f GiB but only %.1f GiB free disk "
            "(reserving %d GiB for solve output). A heavy ISO (PJM 13.0 GB, "
            "MISO 11.5 GB measured) may be OOM-killed; solve one year at a time "
            "and keep the env pins.",
            deficit,
            free_gb,
            DISK_RESERVE_GB,
        )
        return 0

    if dry_run:
        logger.info("swap: WOULD add %d GiB at %s (--check)", add_gb, SWAPFILE)
        return add_gb

    if SWAPFILE.exists():
        subprocess.run(["swapoff", str(SWAPFILE)], check=False, capture_output=True)
        SWAPFILE.unlink()
    subprocess.run(
        ["fallocate", "-l", f"{add_gb}G", str(SWAPFILE)],
        check=True,
        capture_output=True,
    )
    SWAPFILE.chmod(0o600)
    subprocess.run(["mkswap", str(SWAPFILE)], check=True, capture_output=True)
    subprocess.run(["swapon", str(SWAPFILE)], check=True, capture_output=True)
    ram_gb, swap_gb = _meminfo_gb()
    logger.info(
        "swap: added %d GiB at %s — RAM %.1f + swap %.1f = %.1f GiB total",
        add_gb,
        SWAPFILE,
        ram_gb,
        swap_gb,
        ram_gb + swap_gb,
    )
    return add_gb


def main() -> None:
    """Provision swap and report (or emit) the solve env pins."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-gb", type=int, default=DEFAULT_TARGET_GB)
    parser.add_argument(
        "--check", action="store_true", help="Report only; write nothing."
    )
    parser.add_argument(
        "--emit-exports",
        action="store_true",
        help="Print ONLY the shell export lines, for eval.",
    )
    args = parser.parse_args()

    if args.emit_exports:
        for key, value in SOLVE_ENV_PINS.items():
            print(f"export {key}={value}")
        return

    ram_gb, swap_gb = _meminfo_gb()
    logger.info(
        "before: RAM %.1f GiB, swap %.1f GiB, %.1f GiB free disk, %d cpus",
        ram_gb,
        swap_gb,
        _gib(shutil.disk_usage("/").free),
        os.cpu_count() or 0,
    )
    provision_swap(args.target_gb, dry_run=args.check)
    logger.info("env pins for every solve (they do NOT change the LP optimum):")
    for key, value in SOLVE_ENV_PINS.items():
        marker = "OK" if os.environ.get(key) == value else "MISSING"
        logger.info("  %-26s = %-2s  [%s in this shell]", key, value, marker)
    logger.info('  eval "$(python3 scripts/prepare_solve_container.py --emit-exports)"')


if __name__ == "__main__":
    main()
