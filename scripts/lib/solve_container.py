"""Make the container a heavy per-plant ISO-year LP runs in safe BEFORE the solve.

**What this closes (miso-252 / miso-253 / this session, 2026-09-10..12).** A
Claude Code Remote bash cgroup is capped at **13.34 GiB** on a machine whose
``/proc/meminfo`` says 15.7 GiB — the limit lives on the NESTED memory cgroup
(``/process_api/<id>/claude-code-bash``), so ``free``, ``MemTotal`` and the ROOT
cgroup all overstate the ceiling by ~2.4 GiB. A single MISO year (plant-level,
1.03 M rows x 29.6 M cols, 86 M nnz) peaks above that inside HiGHS ``run()``.
Every MISO solve that has ever fit here fit because an **8 GiB swapfile** was
provisioned first (``scripts/prepare_solve_container.py``, added 2026-09-09 for
the pjm-fuelvintage OOM and used by the miso-250 keeper and the miso-251
replays): with swap present the kernel reclaims the cold half of the simplex
workspace instead of SIGKILLing the process. The miso-252 / miso-253 shard
prompts skipped that step — three environments, five shards, five OOMs at a
terminal anon-RSS of 13.30 GiB, all diagnosed as "MISO no longer fits".

The fix is to stop depending on a prompt remembering the step: the solve
entry points (``run_calibration_full.solve_and_persist``, which
``replay_keeper`` also calls, and ``run_calibration.main``) call
:func:`ensure_solve_container` before the first loader runs. It

1. reads the **binding** memory ceiling — the smallest ``memory.max`` /
   ``memory.limit_in_bytes`` on the process's own cgroup path (v2 and v1),
   capped by ``MemTotal`` — never ``free``;
2. provisions a swapfile when ceiling + swap is below the target (24 GiB, the
   ``prepare_solve_container`` default), bounded by free disk, idempotently
   (an already-active swapfile is kept, never re-created);
3. applies the single-thread / arena-pinned solve profile every golden and
   wallclock capture already uses (``run_isos_concurrent._CHILD_ENV_PINS``)
   as *defaults* — an explicit operator value always wins.

None of it changes the LP: swap and the thread count are workspace choices
(``model/lp/model.py`` records that the optimum is identical), so this is
not a ``ScenarioConfig`` tunable (CLAUDE.md rule 24 ``[R-REGISTRY]`` scopes
to values that can change a solve). It is opt-out through the runners'
``--no-container-preflight`` flag, and it never raises: a box where swap
cannot be provisioned gets a WARNING naming the ceiling and proceeds.

:func:`peak_memory_report` is the matching *after* measurement — the cgroup's
own high-water marks (RSS, and RSS+swap where the kernel exposes it). A
process the OOM killer stopped always reports ~the limit as its RSS, so only
a run that FINISHED with swap available can say how far over the ceiling the
LP really is; the runners log it at the end of every invocation.
"""

from __future__ import annotations

import ctypes
import logging
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger("solve_container")

GIB = 1024**3

#: The single-thread / arena-pinned profile every golden and wallclock capture
#: uses. Mirrors ``run_isos_concurrent._CHILD_ENV_PINS`` and
#: ``prepare_solve_container.SOLVE_ENV_PINS`` — keep the three equal.
SOLVE_ENV_PINS: dict[str, str] = {
    "MALLOC_ARENA_MAX": "2",
    "MARKET_SIM_HIGHS_THREADS": "1",
    "OMP_NUM_THREADS": "1",
}

#: RAM+swap floor a per-plant ISO-year solve is provisioned to. PJM's measured
#: single-solve peak is 13.0 GB and MISO's exceeds the 13.34 GiB bash cgroup;
#: 24 GiB leaves real headroom without demanding more disk than a container has.
DEFAULT_TARGET_GIB: int = 24

#: Never consume the last of the disk allowance — a solve also writes parquet.
DISK_RESERVE_GIB: int = 6

#: Where the swapfile goes. Same path ``prepare_solve_container`` has always
#: used, so a container prepared by hand and one prepared here agree.
SWAPFILE = Path("/swapfile-marketsim")

#: glibc ``mallopt`` parameter number for ``M_ARENA_MAX`` (malloc.h). Set at
#: runtime because the env var is only read at process start, and the runner
#: is already running by the time the preflight sees it.
_M_ARENA_MAX = -8

_PROC = Path("/proc")
_CGROUP_ROOT = Path("/sys/fs/cgroup")

#: cgroup limit files that mean "unlimited".
_UNLIMITED = {"max", "-1", str(2**63 - 4096), str(2**63 - 1)}


@dataclass(frozen=True)
class MemoryCeiling:
    """The binding memory ceiling and which file it came from."""

    bytes: int
    source: str

    @property
    def gib(self) -> float:
        """Ceiling in GiB."""
        return self.bytes / GIB


@dataclass
class ContainerRecord:
    """What the preflight found and did — logged, and returned for reports."""

    ceiling_gib: float
    ceiling_source: str
    swap_before_gib: float
    swap_added_gib: float
    swap_after_gib: float
    target_gib: float
    env_pins: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def total_gib(self) -> float:
        """Ceiling + swap after provisioning."""
        return self.ceiling_gib + self.swap_after_gib

    def as_dict(self) -> dict:
        """Plain dict for JSON / logging."""
        return asdict(self)


# --------------------------------------------------------------------------
# Reading the ceiling
# --------------------------------------------------------------------------


def _read_int(path: Path) -> int | None:
    """Parse a cgroup limit file; ``None`` when absent or unlimited."""
    try:
        text = path.read_text().strip()
    except OSError:
        return None
    if text in _UNLIMITED:
        return None
    try:
        value = int(text)
    except ValueError:
        return None
    # cgroup v1 reports "unlimited" as the page-rounded max int64.
    if value >= 2**62:
        return None
    return value


def _meminfo_kb(key: str, proc: Path = _PROC) -> int:
    """One ``/proc/meminfo`` field in kB (0 when absent)."""
    try:
        for line in (proc / "meminfo").read_text().splitlines():
            name, _, rest = line.partition(":")
            if name == key:
                return int(rest.strip().split()[0])
    except OSError:
        pass
    return 0


def _cgroup_paths(proc: Path = _PROC) -> tuple[str | None, str | None]:
    """Return ``(v2_path, v1_memory_path)`` from ``/proc/self/cgroup``."""
    v2: str | None = None
    v1: str | None = None
    try:
        lines = (proc / "self" / "cgroup").read_text().splitlines()
    except OSError:
        return None, None
    for line in lines:
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue
        hier, controllers, path = parts
        if hier == "0" and controllers == "":
            v2 = path
        elif "memory" in controllers.split(","):
            v1 = path
    return v2, v1


def _walk_limits(base: Path, rel_path: str, filename: str) -> list[tuple[int, Path]]:
    """Every finite limit on ``rel_path`` and its ancestors under ``base``."""
    found: list[tuple[int, Path]] = []
    rel = rel_path.strip("/")
    parts = rel.split("/") if rel else []
    # Deepest first, then each ancestor, then the root itself.
    for depth in range(len(parts), -1, -1):
        directory = base.joinpath(*parts[:depth]) if depth else base
        value = _read_int(directory / filename)
        if value is not None:
            found.append((value, directory / filename))
    return found


def memory_ceiling(
    proc: Path = _PROC, cgroup_root: Path = _CGROUP_ROOT
) -> MemoryCeiling:
    """The binding memory ceiling for THIS process.

    The minimum over ``MemTotal`` and every finite cgroup limit on the
    process's own path (cgroup v2 ``memory.max`` and cgroup v1
    ``memory.limit_in_bytes``, each walked from the process's cgroup up to
    the root). A limit on a NESTED cgroup — the CCR ``claude-code-bash``
    case — binds even though the root reads unlimited, which is exactly the
    reading every earlier probe got wrong.

    ``proc`` / ``cgroup_root`` exist so tests can point at a fake tree.
    """
    candidates: list[tuple[int, str]] = []
    mem_total_kb = _meminfo_kb("MemTotal", proc)
    if mem_total_kb:
        candidates.append((mem_total_kb * 1024, "/proc/meminfo MemTotal"))

    v2_path, v1_path = _cgroup_paths(proc)
    if v2_path is not None:
        for value, path in _walk_limits(cgroup_root, v2_path, "memory.max"):
            candidates.append((value, str(path)))
    if v1_path is not None:
        v1_base = cgroup_root / "memory"
        for value, path in _walk_limits(v1_base, v1_path, "memory.limit_in_bytes"):
            candidates.append((value, str(path)))

    if not candidates:
        return MemoryCeiling(0, "unknown")
    value, source = min(candidates, key=lambda item: item[0])
    return MemoryCeiling(value, source)


def swap_total_bytes(proc: Path = _PROC) -> int:
    """``SwapTotal`` from ``/proc/meminfo`` in bytes."""
    return _meminfo_kb("SwapTotal", proc) * 1024


# --------------------------------------------------------------------------
# Provisioning
# --------------------------------------------------------------------------


def _swapfile_active(swapfile: Path, proc: Path = _PROC) -> bool:
    """Is ``swapfile`` already listed in ``/proc/swaps``?"""
    try:
        lines = (proc / "swaps").read_text().splitlines()[1:]
    except OSError:
        return False
    return any(line.split()[:1] == [str(swapfile)] for line in lines)


def provision_swap(
    target_gib: float,
    *,
    ceiling_bytes: int | None = None,
    swapfile: Path = SWAPFILE,
    disk_reserve_gib: float = DISK_RESERVE_GIB,
    dry_run: bool = False,
    proc: Path = _PROC,
) -> tuple[int, list[str]]:
    """Add a swapfile so ceiling + swap reaches ``target_gib``.

    Returns ``(gib_added, warnings)``. Idempotent: an active swapfile at
    ``swapfile`` is kept as it is (sized when it was made). Never raises —
    a box that cannot swap (not root, no ``fallocate``/``swapon``, no disk)
    gets a warning naming why, and the caller proceeds on RAM alone.
    """
    warnings: list[str] = []
    ceiling = ceiling_bytes if ceiling_bytes is not None else memory_ceiling(proc).bytes
    swap = swap_total_bytes(proc)
    deficit_gib = target_gib - (ceiling + swap) / GIB
    if deficit_gib <= 0.5:
        return 0, warnings
    if _swapfile_active(swapfile, proc):
        warnings.append(
            f"swap: {swapfile} is already active ({swap / GIB:.1f} GiB) but "
            f"ceiling+swap is still {deficit_gib:.1f} GiB short of the "
            f"{target_gib:g} GiB target; leaving it as it is"
        )
        return 0, warnings

    try:
        free_gib = shutil.disk_usage(str(swapfile.parent)).free / GIB
    except OSError as exc:
        warnings.append(f"swap: cannot read free disk for {swapfile.parent}: {exc}")
        return 0, warnings
    add_gib = int(min(deficit_gib, max(0.0, free_gib - disk_reserve_gib)))
    if add_gib < 1:
        warnings.append(
            f"swap: CANNOT provision — need {deficit_gib:.1f} GiB but only "
            f"{free_gib:.1f} GiB free disk (reserving {disk_reserve_gib:g} GiB "
            "for solve output). A per-plant ISO-year LP may be OOM-killed."
        )
        return 0, warnings
    if dry_run:
        logger.info("swap: WOULD add %d GiB at %s (--check)", add_gib, swapfile)
        return add_gib, warnings
    if os.geteuid() != 0:
        warnings.append(
            f"swap: not root (uid {os.geteuid()}), cannot provision {add_gib} GiB; "
            f"run `sudo python3 scripts/prepare_solve_container.py` first"
        )
        return 0, warnings

    try:
        if swapfile.exists():
            # Stale file from an earlier container life — not active, so
            # re-create it at the size this box needs.
            subprocess.run(["swapoff", str(swapfile)], check=False, capture_output=True)
            swapfile.unlink()
        subprocess.run(
            ["fallocate", "-l", f"{add_gib}G", str(swapfile)],
            check=True,
            capture_output=True,
        )
        swapfile.chmod(0o600)
        subprocess.run(["mkswap", str(swapfile)], check=True, capture_output=True)
        subprocess.run(["swapon", str(swapfile)], check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = ""
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            detail = ": " + exc.stderr.decode(errors="replace").strip()
        warnings.append(
            f"swap: provisioning {add_gib} GiB at {swapfile} failed ({exc}{detail})"
        )
        return 0, warnings
    return add_gib, warnings


def _apply_env_pins() -> dict[str, str]:
    """Default the solve-profile pins; an explicit operator value wins.

    ``MALLOC_ARENA_MAX`` is also applied to the live allocator through
    ``mallopt`` — the environment variable alone is only read at process
    start, and the runner is already running.
    """
    applied: dict[str, str] = {}
    for key, value in SOLVE_ENV_PINS.items():
        os.environ.setdefault(key, value)
        applied[key] = os.environ[key]
    try:
        arenas = int(applied["MALLOC_ARENA_MAX"])
        libc = ctypes.CDLL("libc.so.6")
        libc.mallopt(_M_ARENA_MAX, arenas)
    except (OSError, ValueError, AttributeError):
        pass
    return applied


_PREFLIGHT_RECORD: ContainerRecord | None = None


def ensure_solve_container(
    target_gib: float = DEFAULT_TARGET_GIB,
    *,
    provision: bool = True,
    log: logging.Logger | None = None,
) -> ContainerRecord:
    """Read the binding ceiling, provision swap up to ``target_gib``, pin the profile.

    Runs once per process (later calls return the first record). Never
    raises. ``provision=False`` reports and pins but writes nothing.

    **Call it before the process's first HiGHS solve** — which is where both
    runners call it. HiGHS refuses a ``threads`` change once its scheduler is
    initialised, so a process that has already solved with the default thread
    count and THEN picks up ``MARKET_SIM_HIGHS_THREADS=1`` gets status
    "Not Set" from every later solve (measured in the pytest process,
    2026-09-12). An explicit pre-set value is left alone, so a caller that
    solved first can protect itself by exporting the pin it already used.
    """
    global _PREFLIGHT_RECORD
    if _PREFLIGHT_RECORD is not None:
        return _PREFLIGHT_RECORD
    out = log or logger

    ceiling = memory_ceiling()
    swap_before = swap_total_bytes()
    mem_total_gib = _meminfo_kb("MemTotal") * 1024 / GIB
    out.info(
        "container preflight: memory ceiling %.2f GiB (%s; MemTotal %.2f GiB), "
        "swap %.1f GiB, target ceiling+swap %g GiB",
        ceiling.gib,
        ceiling.source,
        mem_total_gib,
        swap_before / GIB,
        target_gib,
    )
    added = 0
    warnings: list[str] = []
    if provision:
        added, warnings = provision_swap(target_gib, ceiling_bytes=ceiling.bytes)
        if added:
            out.info(
                "container preflight: provisioned %d GiB swap at %s — ceiling %.2f + "
                "swap %.1f = %.1f GiB",
                added,
                SWAPFILE,
                ceiling.gib,
                swap_total_bytes() / GIB,
                ceiling.gib + swap_total_bytes() / GIB,
            )
    for message in warnings:
        out.warning("container preflight: %s", message)
    pins = _apply_env_pins()
    out.info(
        "container preflight: solve profile %s",
        " ".join(f"{k}={v}" for k, v in pins.items()),
    )
    record = ContainerRecord(
        ceiling_gib=round(ceiling.gib, 3),
        ceiling_source=ceiling.source,
        swap_before_gib=round(swap_before / GIB, 3),
        swap_added_gib=float(added),
        swap_after_gib=round(swap_total_bytes() / GIB, 3),
        target_gib=float(target_gib),
        env_pins=pins,
        warnings=warnings,
    )
    if record.total_gib + 0.5 < target_gib:
        out.warning(
            "container preflight: ceiling+swap %.1f GiB is below the %g GiB target; "
            "a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here",
            record.total_gib,
            target_gib,
        )
    _PREFLIGHT_RECORD = record
    return record


# --------------------------------------------------------------------------
# After the solve: the honest peak
# --------------------------------------------------------------------------


def peak_memory_report(
    proc: Path = _PROC, cgroup_root: Path = _CGROUP_ROOT
) -> dict[str, float]:
    """High-water marks in GiB: process ``VmHWM`` and the cgroup's own peaks.

    cgroup v1 exposes ``memory.max_usage_in_bytes`` (RSS + page cache) and
    ``memory.memsw.max_usage_in_bytes`` (the same plus swap); v2 exposes
    ``memory.peak`` and ``memory.swap.peak`` on recent kernels. Whatever is
    readable is returned; absent files are simply omitted.
    """
    report: dict[str, float] = {}
    try:
        for line in (proc / "self" / "status").read_text().splitlines():
            if line.startswith("VmHWM"):
                report["process_vmhwm_gib"] = int(line.split()[1]) * 1024 / GIB
            elif line.startswith("VmSwap"):
                report["process_vmswap_now_gib"] = int(line.split()[1]) * 1024 / GIB
    except (OSError, ValueError, IndexError):
        pass
    v2_path, v1_path = _cgroup_paths(proc)
    if v1_path is not None:
        base = cgroup_root / "memory" / v1_path.strip("/")
        for name, key in (
            ("memory.max_usage_in_bytes", "cgroup_peak_rss_gib"),
            ("memory.memsw.max_usage_in_bytes", "cgroup_peak_rss_plus_swap_gib"),
        ):
            value = _read_int(base / name)
            if value is not None:
                report[key] = value / GIB
    if v2_path is not None:
        base = cgroup_root / v2_path.strip("/")
        for name, key in (
            ("memory.peak", "cgroup_peak_rss_gib"),
            ("memory.swap.peak", "cgroup_peak_swap_gib"),
        ):
            value = _read_int(base / name)
            if value is not None:
                report[key] = value / GIB
    return report


def log_peak_memory(log: logging.Logger | None = None) -> dict[str, float]:
    """Log :func:`peak_memory_report` on one line and return it."""
    out = log or logger
    report = peak_memory_report()
    if report:
        out.info(
            "memory peak: %s",
            ", ".join(f"{k}={v:.2f}" for k, v in sorted(report.items())),
        )
    return report
