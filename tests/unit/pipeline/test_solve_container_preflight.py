"""Guards for scripts/lib/solve_container.py — the solve-container preflight.

The defect it closes (miso-252/253, 2026-09-10): every probe read the ROOT
memory cgroup (unlimited) and fell back to ``MemTotal`` (15.7 GiB), while the
limit that binds a CCR bash session sits on the NESTED cgroup
(``/process_api/<id>/claude-code-bash``, 13.34 GiB). These tests build a fake
``/proc`` + ``/sys/fs/cgroup`` tree and check the reader picks the nested
limit under cgroup v1 and v2, treats the v1 "unlimited" sentinel as no limit,
and that the dry-run / no-provision paths never write anything.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib import solve_container as sc

GIB = 1024**3
V1_UNLIMITED = "9223372036854771712"
NESTED = "process_api/01a09332-8518-73fd-a2d7-d8b1f2cf0d9f/claude-code-bash"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _fake_proc(tmp_path: Path, cgroup_lines: str, mem_total_gib: float = 15.7) -> Path:
    proc = tmp_path / "proc"
    _write(proc / "self" / "cgroup", cgroup_lines)
    _write(
        proc / "meminfo",
        f"MemTotal:       {int(mem_total_gib * GIB / 1024)} kB\n"
        "MemFree:        12000000 kB\n"
        "SwapTotal:             0 kB\n",
    )
    _write(proc / "swaps", "Filename\tType\tSize\tUsed\tPriority\n")
    return proc


def _v1_lines() -> str:
    return (
        "9:name=systemd:/\n8:pids:/\n7:blkio:/\n6:freezer:/\n5:devices:/\n"
        f"4:memory:/{NESTED}\n3:cpuset:/\n2:cpuacct:/\n1:cpu:/\n0::/\n"
    )


def test_v1_nested_limit_binds_over_unlimited_root_and_memtotal(tmp_path: Path) -> None:
    """The CCR case: root v1 cgroup unlimited, nested cgroup 13.34 GiB, MemTotal 15.7."""
    proc = _fake_proc(tmp_path, _v1_lines())
    cg = tmp_path / "cgroup"
    _write(cg / "memory" / "memory.limit_in_bytes", V1_UNLIMITED)
    _write(cg / "memory" / NESTED / "memory.limit_in_bytes", str(14327676928))
    # The root v2 file exists too and reads "max" — must not confuse the reader.
    _write(cg / "memory.max", "max")

    ceiling = sc.memory_ceiling(proc=proc, cgroup_root=cg)

    assert ceiling.bytes == 14327676928
    assert ceiling.gib == pytest.approx(13.3437, abs=1e-3)
    assert ceiling.source.endswith(f"memory/{NESTED}/memory.limit_in_bytes")


def test_v1_unlimited_everywhere_falls_back_to_memtotal(tmp_path: Path) -> None:
    proc = _fake_proc(tmp_path, _v1_lines(), mem_total_gib=15.7)
    cg = tmp_path / "cgroup"
    _write(cg / "memory" / "memory.limit_in_bytes", V1_UNLIMITED)
    _write(cg / "memory" / NESTED / "memory.limit_in_bytes", V1_UNLIMITED)

    ceiling = sc.memory_ceiling(proc=proc, cgroup_root=cg)

    assert ceiling.source == "/proc/meminfo MemTotal"
    assert ceiling.gib == pytest.approx(15.7, abs=1e-3)


def test_v2_ancestor_limit_binds(tmp_path: Path) -> None:
    """cgroup v2: the limit may sit on an ANCESTOR of the process's own cgroup."""
    proc = _fake_proc(tmp_path, "0::/a/b/c\n", mem_total_gib=32.0)
    cg = tmp_path / "cgroup"
    _write(cg / "memory.max", "max")
    _write(cg / "a" / "memory.max", str(20 * GIB))
    _write(cg / "a" / "b" / "memory.max", "max")
    _write(cg / "a" / "b" / "c" / "memory.max", str(24 * GIB))

    ceiling = sc.memory_ceiling(proc=proc, cgroup_root=cg)

    assert ceiling.bytes == 20 * GIB
    assert ceiling.source.endswith("a/memory.max")


def test_memory_ceiling_without_any_source_is_zero_unknown(tmp_path: Path) -> None:
    proc = tmp_path / "proc"
    proc.mkdir()
    assert sc.memory_ceiling(
        proc=proc, cgroup_root=tmp_path / "cg"
    ) == sc.MemoryCeiling(0, "unknown")


def test_provision_swap_dry_run_writes_nothing_and_sizes_to_deficit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proc = _fake_proc(tmp_path, _v1_lines())
    swapfile = tmp_path / "swapfile"
    monkeypatch.setattr(
        sc.shutil,
        "disk_usage",
        lambda _p: type("du", (), {"free": 100 * GIB})(),
    )

    added, warnings = sc.provision_swap(
        24,
        ceiling_bytes=int(13.34 * GIB),
        swapfile=swapfile,
        dry_run=True,
        proc=proc,
    )

    assert added == 10  # int(24 - 13.34 - 0) with ample disk
    assert warnings == []
    assert not swapfile.exists()


def test_provision_swap_no_deficit_is_a_noop(tmp_path: Path) -> None:
    proc = _fake_proc(tmp_path, _v1_lines())
    added, warnings = sc.provision_swap(
        24, ceiling_bytes=30 * GIB, swapfile=tmp_path / "swapfile", proc=proc
    )
    assert (added, warnings) == (0, [])


def test_provision_swap_reports_when_disk_is_too_small(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proc = _fake_proc(tmp_path, _v1_lines())
    monkeypatch.setattr(
        sc.shutil, "disk_usage", lambda _p: type("du", (), {"free": 6 * GIB})()
    )
    added, warnings = sc.provision_swap(
        24, ceiling_bytes=int(13.34 * GIB), swapfile=tmp_path / "swapfile", proc=proc
    )
    assert added == 0
    assert len(warnings) == 1 and "CANNOT provision" in warnings[0]


def test_active_swapfile_is_kept_not_recreated(tmp_path: Path) -> None:
    proc = _fake_proc(tmp_path, _v1_lines())
    swapfile = tmp_path / "swapfile"
    _write(
        proc / "swaps",
        "Filename\tType\tSize\tUsed\tPriority\n"
        f"{swapfile}\tfile\t{8 * 1024 * 1024}\t0\t-2\n",
    )
    added, warnings = sc.provision_swap(
        24, ceiling_bytes=int(13.34 * GIB), swapfile=swapfile, proc=proc
    )
    assert added == 0
    assert len(warnings) == 1 and "already active" in warnings[0]


def test_env_pins_default_but_never_override(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in sc.SOLVE_ENV_PINS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MARKET_SIM_HIGHS_THREADS", "4")

    applied = sc._apply_env_pins()

    assert applied["MARKET_SIM_HIGHS_THREADS"] == "4"
    assert applied["MALLOC_ARENA_MAX"] == "2"
    assert applied["OMP_NUM_THREADS"] == "1"


def test_pins_agree_with_prepare_solve_container_and_run_isos_concurrent() -> None:
    """Three copies of the profile exist by design; they must stay equal."""
    from scripts import prepare_solve_container, run_isos_concurrent

    assert prepare_solve_container.SOLVE_ENV_PINS == sc.SOLVE_ENV_PINS
    assert run_isos_concurrent._CHILD_ENV_PINS == sc.SOLVE_ENV_PINS


def test_ensure_solve_container_no_provision_never_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sc, "_PREFLIGHT_RECORD", None)
    calls: list[str] = []
    monkeypatch.setattr(
        sc, "provision_swap", lambda *a, **k: calls.append("provision") or (0, [])
    )

    record = sc.ensure_solve_container(provision=False)

    assert calls == []
    assert record.swap_added_gib == 0
    assert record.ceiling_gib > 0
    # Second call is the cached record, not a re-run.
    assert sc.ensure_solve_container(provision=True) is record
