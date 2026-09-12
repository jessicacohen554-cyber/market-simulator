"""Make an ephemeral solve container safe for a heavy per-plant ISO LP.

**The defect this closes.** A Claude Code Remote bash cgroup is capped at
**13.34 GiB** (the limit lives on the NESTED memory cgroup
``/process_api/<id>/claude-code-bash``; ``free`` / ``MemTotal`` / the root
cgroup all read ~15.7 GiB and are wrong by ~2.4 GiB), with **zero swap**. A
PJM year peaks at 13.0 GB measured and a MISO year above the cap inside HiGHS
``run()``, so without a backstop the kernel OOM-kills the solve (SIGKILL,
child return code -9) instead of paging. Session pjm-fuelvintage-1 hit it at
13.75 GiB RSS on 2026-09-09; miso-252 / miso-253 lost five shards to it on
2026-09-10 because their prompts skipped this step.

Two things fix it, and this script does both — through the shared
:mod:`scripts.lib.solve_container`, which the solve entry points
(``run_calibration_full.solve_and_persist``, hence ``replay_keeper``, and
``run_calibration.main``) now also call automatically before the first
loader runs, so a prompt no longer has to remember it:

1. **Swap.** A swapfile turns a fatal peak into a slow one. Verified working in
   the CCR container class (``fallocate`` + ``mkswap`` + ``swapon`` all succeed
   as root). Sized to bring the binding ceiling + swap to ``--target-gb``,
   bounded by free disk; an already-active swapfile is kept.
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
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.lib.solve_container import (  # noqa: E402
    DEFAULT_TARGET_GIB,
    GIB,
    SOLVE_ENV_PINS,
    SWAPFILE,
    memory_ceiling,
    provision_swap,
    swap_total_bytes,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("prepare_solve_container")

#: Kept as a public name — earlier prompts and docs import it from here.
DEFAULT_TARGET_GB: int = DEFAULT_TARGET_GIB


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

    ceiling = memory_ceiling()
    swap_gib = swap_total_bytes() / GIB
    logger.info(
        "before: memory ceiling %.2f GiB (%s), swap %.1f GiB, %.1f GiB free disk, %d cpus",
        ceiling.gib,
        ceiling.source,
        swap_gib,
        shutil.disk_usage("/").free / GIB,
        os.cpu_count() or 0,
    )
    added, warnings = provision_swap(
        args.target_gb, ceiling_bytes=ceiling.bytes, dry_run=args.check
    )
    for message in warnings:
        logger.warning(message)
    swap_gib = swap_total_bytes() / GIB
    if added and not args.check:
        logger.info(
            "swap: added %d GiB at %s — ceiling %.2f + swap %.1f = %.1f GiB total",
            added,
            SWAPFILE,
            ceiling.gib,
            swap_gib,
            ceiling.gib + swap_gib,
        )
    elif not added and not warnings:
        logger.info(
            "swap: none needed (ceiling %.2f + swap %.1f >= target %d GiB)",
            ceiling.gib,
            swap_gib,
            args.target_gb,
        )
    logger.info("env pins for every solve (they do NOT change the LP optimum):")
    for key, value in SOLVE_ENV_PINS.items():
        marker = "OK" if os.environ.get(key) == value else "MISSING"
        logger.info("  %-26s = %-2s  [%s in this shell]", key, value, marker)
    logger.info('  eval "$(python3 scripts/prepare_solve_container.py --emit-exports)"')


if __name__ == "__main__":
    main()
