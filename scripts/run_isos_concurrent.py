"""Launch several per-ISO calibration backcasts concurrently, within rule 12.

This is the standing-tool version of the "hand-launched multi-ISO concurrency"
the refactor-consolidation plan (§7 H, item "Operational") calls out: instead
of manually opening N shells and eyeballing memory, this scheduler runs a set
of ``(iso, out-dir)`` calibration jobs as background subprocesses under one
supervisor that **enforces** the CLAUDE.md rule-12 memory discipline rather
than trusting the operator to.

What it enforces
----------------
* **Concurrency cap** (``--cap``, default 2): never more than ``cap`` child
  solves run at once. Rule 12 caps simultaneous per-plant multi-zone LPs at
  ~2 on a typical box; the default matches.
* **No two heavy ISOs together.** Each ISO carries a memory class derived from
  ``docs/handoffs/wallclock-baseline-2026-07.md`` (measured peak RSS). The two
  memory-heavy families — **per-plant** fleets and **reserve co-optimization**
  LPs — cannot share a 16 GB host: MISO alone peaks ≈10.8-11.5 GB and a PJM
  per-plant year ≈13 GB, so co-scheduling either with ERCOT's ≈6 GB per-plant
  solve OOMs mid-year (the baseline doc's operational note records exactly that
  kill). The scheduler therefore refuses to *ever* run two ``HEAVY``-class ISOs
  concurrently, independent of the numeric cap.
* **Combined-peak budget** (``--host-gb``, default 16): a secondary guard that
  also refuses a co-schedule whose summed estimated peak RSS would exceed the
  host budget (with a safety margin), so a heavy ISO does not get paired with a
  light one that would still tip the box over.

Every child inherits the single-thread / arena-pinned environment the goldens
and every wallclock capture use (``MALLOC_ARENA_MAX=2``,
``MARKET_SIM_HIGHS_THREADS=1``, ``OMP_NUM_THREADS=1``) so a concurrent run's
per-solve memory and determinism match a solo run. Each job's combined
stdout+stderr is **tee'd**: written verbatim to ``<out-dir>/run.log`` (or
``--log-dir/<iso>.log``) *and* mirrored to this process's stdout with an
``[ISO]`` prefix so interleaved progress stays readable.

A child that exits non-zero — including an OOM kill, which surfaces as
termination by ``SIGKILL`` (return code ``-9``) — is reported **loudly** and,
unless ``--keep-going`` is passed, aborts the whole batch: the supervisor stops
launching new jobs, terminates the survivors, and exits non-zero. Silent
partial success is never the outcome.

This is **pure orchestration and in-session only** (CLAUDE.md "GitHub Actions —
never offload work to CI"): it shells out to ``scripts/run_calibration_full.py``
and does no solving, scoring, or dashboard IO of its own. Years within each job
stay sequential (the child's own ``--year`` loop; rule 12 forbids parallelizing
a single invocation's years); this scheduler only parallelizes *separate*
invocations.

Usage
-----
::

    # Two light ISOs together (allowed, under the cap):
    python scripts/run_isos_concurrent.py \
        --job CAISO results/calibration/caiso-run \
        --job NYISO results/calibration/nyiso-run

    # A heavy + a light ISO: allowed only if the combined peak fits --host-gb.
    python scripts/run_isos_concurrent.py --cap 2 \
        --job ERCOT out/ercot --job CAISO out/caiso

    # Two heavy ISOs: refused up front (rule 12), before any solve starts.
    python scripts/run_isos_concurrent.py --job ERCOT out/e --job MISO out/m
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# --- Per-ISO memory classes (docs/handoffs/wallclock-baseline-2026-07.md) ----
# ``heavy`` marks the per-plant-fleet and/or reserve-co-optimization ISOs whose
# LPs are multi-GB and cannot share a 16 GB host with another heavy ISO. The
# ``peak_gb`` estimates are the measured peak RSS from the baseline doc where it
# captured them (ERCOT ≈5.7-5.9 GB plant-level; MISO ≈10.8-13.2 GB co-opt; a PJM
# per-plant year ≈13 GB per the run_calibration_full results-write note) and a
# conservative zonal estimate otherwise. These are the two "per-plant / co-opt"
# families rule 12 says to keep to one at a time.


@dataclass(frozen=True)
class IsoMemoryClass:
    """One ISO's memory profile for the concurrency scheduler.

    Attributes:
        iso: Canonical ISO name.
        peak_gb: Estimated single-solve peak RSS in GB (measured where the
            baseline doc captured it, else a conservative zonal estimate).
        per_plant: Whether the ISO's calibrated fleet is per-plant (CAMPD
            binning) — the ERCOT/PJM multi-GB fleet class.
        co_opt: Whether the ISO's keeper co-optimizes energy and reserves —
            the MISO/PJM (and NYISO/NEISO variant) reserve-row class.
    """

    iso: str
    peak_gb: float
    per_plant: bool
    co_opt: bool

    @property
    def heavy(self) -> bool:
        """Return whether this ISO is in the memory-heavy (per-plant/co-opt) class."""
        return self.per_plant or self.co_opt


# Measured/estimated per baseline doc. ERCOT & PJM are per-plant; MISO/PJM
# co-optimize reserves at scale (the big-co-opt family the doc flags). CAISO,
# NYISO and NEISO are zonal (≤5 zones); their keepers may enable reserve
# co-optimization but on far smaller LPs than MISO/PJM, so they are treated as
# light — their measured peaks are well under the heavy family's.
_ISO_MEMORY_CLASSES: dict[str, IsoMemoryClass] = {
    "ERCOT": IsoMemoryClass("ERCOT", peak_gb=6.0, per_plant=True, co_opt=False),
    "PJM": IsoMemoryClass("PJM", peak_gb=13.0, per_plant=True, co_opt=True),
    "MISO": IsoMemoryClass("MISO", peak_gb=11.5, per_plant=False, co_opt=True),
    "CAISO": IsoMemoryClass("CAISO", peak_gb=4.5, per_plant=False, co_opt=False),
    "NYISO": IsoMemoryClass("NYISO", peak_gb=4.0, per_plant=False, co_opt=False),
    "NEISO": IsoMemoryClass("NEISO", peak_gb=4.0, per_plant=False, co_opt=False),
    # SPP (registered 2026-09-06, lane SPP-20): per-plant class by design (the
    # CAMPD binning path unlocks when SPP-30 lands its tranche artifact), no
    # reserve co-optimisation (owner ruling P4 defers it to SPP-56). peak_gb is
    # an ESTIMATE, MEASURED IN SPP-40: ERCOT's measured 6.0 GB is the nearest
    # per-plant / no-co-opt analogue (SPP: 715 plants / 1,646 generators at 2
    # zones vs ERCOT's 7 zones), so SPP should sit at or below it.
    "SPP": IsoMemoryClass("SPP", peak_gb=6.0, per_plant=True, co_opt=False),
    # NWPP (registered 2026-09-14, lane NWPP-20): ZONAL class by owner ruling
    # N8 — legacy heat-rate bins for the first keeper (use_campd_bins=False;
    # NWPP is absent from CAMPD_BINNING_ISOS), which SUPERSEDES the plan §3
    # recorded default per_plant=True; no reserve co-optimisation (no
    # market-cleared AS exists in the pool). peak_gb is an ESTIMATE, MEASURED
    # IN NWPP-40: CAISO's measured 4.5 GB is the nearest zonal / no-co-opt
    # analogue (4 zones incl. the import node) and NWPP has one zone more plus
    # a 288-plant monthly hydro-budget row family (~3,456 rows), so it should
    # sit modestly above it. Gate G21 stands whatever this reads.
    "NWPP": IsoMemoryClass("NWPP", peak_gb=5.5, per_plant=False, co_opt=False),
}

# Env pins every child inherits — the single-thread / arena-pinned profile the
# goldens and every wallclock capture use, so concurrent per-solve memory and
# determinism match a solo run (baseline doc §H2; rule 12).
_CHILD_ENV_PINS: dict[str, str] = {
    "MALLOC_ARENA_MAX": "2",
    "MARKET_SIM_HIGHS_THREADS": "1",
    "OMP_NUM_THREADS": "1",
}

_DEFAULT_YEARS: tuple[int, ...] = (2023, 2024, 2025)


@dataclass
class Job:
    """One calibration invocation: an ISO and where its bundle goes."""

    iso: str
    out_dir: Path
    log_path: Path


def memory_class(iso: str) -> IsoMemoryClass:
    """Return the memory class for ``iso`` (KeyError-safe with a clear message).

    Raises:
        SystemExit: When ``iso`` has no registered memory class — the scheduler
            refuses to guess a heavy/light classification for an unknown ISO.
    """
    try:
        return _ISO_MEMORY_CLASSES[iso.upper()]
    except KeyError:
        known = ", ".join(sorted(_ISO_MEMORY_CLASSES))
        raise SystemExit(
            f"unknown ISO {iso!r}: no memory class registered "
            f"(known: {known}). Add one to _ISO_MEMORY_CLASSES with a "
            "baseline-doc citation before scheduling it concurrently."
        )


def _tee_reader(proc: "subprocess.Popen[str]", log_path: Path, tag: str) -> None:
    """Stream a child's combined output to its log file and this stdout (prefixed).

    Runs on its own thread per job so several children can tee at once without
    blocking each other. Line-buffered: each child line is written to the log
    file and echoed to the supervisor's stdout with a ``[tag]`` prefix.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as fh:
        assert proc.stdout is not None
        for line in proc.stdout:
            fh.write(line)
            fh.flush()
            sys.stdout.write(f"[{tag}] {line}")
            sys.stdout.flush()


def _child_command(job: Job, years: tuple[int, ...], extra: list[str]) -> list[str]:
    """Build the ``run_calibration_full.py`` command for one job."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_calibration_full.py"),
        "--iso",
        job.iso,
        "--year",
        *[str(y) for y in years],
        "--out-dir",
        str(job.out_dir),
    ]
    cmd.extend(extra)
    return cmd


def _child_env() -> dict[str, str]:
    """Return the child environment: the current env plus the rule-12 pins."""
    env = dict(os.environ)
    env.update(_CHILD_ENV_PINS)
    return env


def can_coschedule(
    running: list[str],
    candidate: str,
    cap: int,
    host_gb: float,
    margin_gb: float,
) -> tuple[bool, str]:
    """Return whether ``candidate`` may start given the currently ``running`` ISOs.

    Enforces, in order: the concurrency ``cap``; the rule-12 refusal of two
    memory-heavy (per-plant/co-opt) ISOs at once; and the combined-peak budget
    against ``host_gb`` (minus ``margin_gb`` headroom).

    Returns:
        ``(True, "")`` when the candidate may start now, else ``(False, why)``
        with a human-readable reason (a transient one — a later completion may
        make it schedulable).
    """
    if len(running) >= cap:
        return False, f"cap {cap} reached (running: {', '.join(running) or 'none'})"

    cand = memory_class(candidate)
    if cand.heavy:
        heavy_running = [r for r in running if memory_class(r).heavy]
        if heavy_running:
            return (
                False,
                f"{candidate} is memory-heavy (per_plant={cand.per_plant}, "
                f"co_opt={cand.co_opt}) and a heavy ISO is already running "
                f"({', '.join(heavy_running)}); rule 12 refuses two heavy ISOs "
                "together",
            )

    projected = cand.peak_gb + sum(memory_class(r).peak_gb for r in running)
    budget = host_gb - margin_gb
    if projected > budget:
        return (
            False,
            f"combined peak ≈{projected:.1f} GB (adding {candidate} "
            f"@{cand.peak_gb:.1f} GB to {', '.join(running) or 'none'}) exceeds "
            f"the {budget:.1f} GB budget (host {host_gb:.0f} GB − {margin_gb:.0f} "
            "GB margin)",
        )
    return True, ""


def preflight(jobs: list[Job], cap: int, host_gb: float, margin_gb: float) -> None:
    """Validate the batch is schedulable at all before any solve starts.

    Fails loudly up front (rather than mid-batch) when the batch can never make
    progress: any single job that cannot run even alone, i.e. its own peak
    exceeds the host budget. The pairwise heavy/heavy and combined-peak checks
    are enforced dynamically at launch by :func:`can_coschedule`; here we only
    reject the impossible-alone case so the operator learns immediately.
    """
    budget = host_gb - margin_gb
    for job in jobs:
        mc = memory_class(job.iso)
        if mc.peak_gb > budget:
            raise SystemExit(
                f"{job.iso} peak ≈{mc.peak_gb:.1f} GB alone exceeds the "
                f"{budget:.1f} GB budget; cannot schedule it on this host "
                f"(raise --host-gb or run it elsewhere)."
            )


def run_jobs(
    jobs: list[Job],
    years: tuple[int, ...],
    cap: int,
    host_gb: float,
    margin_gb: float,
    extra: list[str],
    keep_going: bool,
    poll_seconds: float = 1.0,
) -> int:
    """Schedule and supervise the batch. Return a process exit code.

    Launches jobs subject to :func:`can_coschedule`, tees each child's output,
    and watches for completion. A non-zero child (including an OOM ``SIGKILL``,
    return code ``-9``) is reported loudly; unless ``keep_going`` is set the
    supervisor then stops launching, terminates survivors, and returns non-zero.

    Returns:
        ``0`` when every job succeeded, else ``1``.
    """
    preflight(jobs, cap, host_gb, margin_gb)

    pending = list(jobs)
    running: dict[str, dict] = {}  # iso -> {proc, thread, job, started}
    failures: list[str] = []
    aborting = False

    def _running_isos() -> list[str]:
        return list(running)

    while pending or running:
        # Launch as many pending jobs as the constraints currently allow.
        if not aborting:
            progressed = True
            while progressed and pending:
                progressed = False
                for idx, job in enumerate(pending):
                    ok, why = can_coschedule(
                        _running_isos(), job.iso, cap, host_gb, margin_gb
                    )
                    if not ok:
                        continue
                    proc = subprocess.Popen(
                        _child_command(job, years, extra),
                        cwd=str(REPO_ROOT),
                        env=_child_env(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                    )
                    thread = threading.Thread(
                        target=_tee_reader,
                        args=(proc, job.log_path, job.iso),
                        daemon=True,
                    )
                    thread.start()
                    running[job.iso] = {
                        "proc": proc,
                        "thread": thread,
                        "job": job,
                        "started": time.time(),
                    }
                    print(
                        f"[supervisor] launched {job.iso} -> {job.out_dir} "
                        f"(log {job.log_path}); running: "
                        f"{', '.join(_running_isos())}",
                        flush=True,
                    )
                    del pending[idx]
                    progressed = True
                    break

            # If nothing is running and nothing could launch, we are stuck
            # (should not happen after preflight, but never spin forever).
            if pending and not running:
                stuck = pending[0]
                _, why = can_coschedule(
                    _running_isos(), stuck.iso, cap, host_gb, margin_gb
                )
                raise SystemExit(
                    f"[supervisor] deadlock: cannot schedule {stuck.iso} and "
                    f"nothing is running ({why})."
                )

        # Reap any finished children.
        finished: list[str] = []
        for iso, rec in running.items():
            ret = rec["proc"].poll()
            if ret is None:
                continue
            rec["thread"].join(timeout=10)
            finished.append(iso)
            elapsed = time.time() - rec["started"]
            if ret == 0:
                print(
                    f"[supervisor] ✓ {iso} finished OK in {elapsed:.0f}s "
                    f"-> {rec['job'].out_dir}",
                    flush=True,
                )
            else:
                oom = ret < 0 and ret == -9
                detail = (
                    "OOM-killed (SIGKILL) — reduce --cap/--host-gb or the "
                    "co-scheduled set"
                    if oom
                    else f"exit code {ret}"
                )
                msg = (
                    f"[supervisor] ✗ {iso} FAILED after {elapsed:.0f}s: {detail}. "
                    f"See {rec['job'].log_path}"
                )
                print(msg, file=sys.stderr, flush=True)
                failures.append(f"{iso} ({detail})")
                if not keep_going:
                    aborting = True

        for iso in finished:
            del running[iso]

        if aborting and running:
            # Stop the survivors so a real failure aborts the batch promptly.
            for iso, rec in running.items():
                print(
                    f"[supervisor] terminating {iso} (batch aborting)",
                    file=sys.stderr,
                    flush=True,
                )
                rec["proc"].terminate()

        if running:
            time.sleep(poll_seconds)

    if failures:
        print(
            f"[supervisor] BATCH FAILED: {len(failures)} job(s) failed: "
            + "; ".join(failures),
            file=sys.stderr,
            flush=True,
        )
        return 1
    print(
        f"[supervisor] batch complete: {len(jobs)} job(s) succeeded.",
        flush=True,
    )
    return 0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="run_isos_concurrent",
        description=(
            "Run several per-ISO calibration backcasts concurrently under the "
            "rule-12 memory cap (per-plant / co-opt heavy-ISO refusal)."
        ),
    )
    parser.add_argument(
        "--job",
        action="append",
        nargs=2,
        metavar=("ISO", "OUT_DIR"),
        default=[],
        help="An (ISO, out-dir) job. Repeatable. E.g. --job ERCOT out/ercot.",
    )
    parser.add_argument(
        "--year",
        nargs="+",
        type=int,
        default=list(_DEFAULT_YEARS),
        help="Years passed to every child --year (kept sequential inside each "
        "child). Default: 2023 2024 2025.",
    )
    parser.add_argument(
        "--cap",
        type=int,
        default=2,
        help="Max concurrent child solves (rule 12). Default 2.",
    )
    parser.add_argument(
        "--host-gb",
        type=float,
        default=16.0,
        help="Host RAM budget in GB for the combined-peak guard. Default 16.",
    )
    parser.add_argument(
        "--margin-gb",
        type=float,
        default=1.0,
        help="Headroom subtracted from --host-gb before the combined-peak "
        "check. Default 1.",
    )
    parser.add_argument(
        "--log-dir",
        default=None,
        help="Directory for per-ISO tee logs (<ISO>.log). Default: each job's "
        "own out-dir/run.log.",
    )
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Do not abort the batch on a child failure; run every job and "
        "report all failures at the end.",
    )
    parser.add_argument(
        "--extra",
        nargs=argparse.REMAINDER,
        default=[],
        help="Everything after --extra is forwarded verbatim to every child "
        "run_calibration_full.py invocation (e.g. keeper flags).",
    )
    return parser.parse_args(argv)


def _build_jobs(args: argparse.Namespace) -> list[Job]:
    if not args.job:
        raise SystemExit("no jobs: pass at least one --job ISO OUT_DIR")
    log_dir = Path(args.log_dir).resolve() if args.log_dir else None
    jobs: list[Job] = []
    seen: set[str] = set()
    for iso_raw, out_raw in args.job:
        iso = iso_raw.upper()
        memory_class(iso)  # validate early
        if iso in seen:
            raise SystemExit(
                f"duplicate ISO {iso} in --job list; give each ISO one job "
                "(this scheduler keys running jobs by ISO)."
            )
        seen.add(iso)
        out_dir = Path(out_raw).resolve()
        log_path = (log_dir / f"{iso}.log") if log_dir else (out_dir / "run.log")
        jobs.append(Job(iso=iso, out_dir=out_dir, log_path=log_path))
    return jobs


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Return a process exit code."""
    args = _parse_args(argv)
    jobs = _build_jobs(args)
    years = tuple(int(y) for y in args.year)

    print(
        "[supervisor] plan: "
        + "; ".join(
            f"{j.iso}({'heavy' if memory_class(j.iso).heavy else 'light'}, "
            f"≈{memory_class(j.iso).peak_gb:.1f} GB)"
            for j in jobs
        )
        + f" | cap={args.cap} host={args.host_gb:.0f} GB years={list(years)}",
        flush=True,
    )
    return run_jobs(
        jobs,
        years=years,
        cap=args.cap,
        host_gb=args.host_gb,
        margin_gb=args.margin_gb,
        extra=list(args.extra),
        keep_going=args.keep_going,
    )


if __name__ == "__main__":
    raise SystemExit(main())
