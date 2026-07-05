"""One-command regression gate for the orchestrator-unification stages.

Every stage of ``docs/handoffs/orchestrator-unification-plan-2026-07.md`` must
prove it did not move a dispatched number before it merges. This script is that
proof, run identically by each stage's session:

    python scripts/regression_gate.py \
        --before results/regression-goldens/stageN-before \
        --after  results/regression-goldens/stageN-after \
        --mode byte            # pure code motion (Stages 1-4/7): --atol 0 --rtol 0
        # or --mode builder    # builder swap (Stages 5-6): --atol 1e-9 --rtol 1e-9

It runs four checks and prints a single PASS/FAIL with exit code 0/1:

1. **Golden bundle diff** (when ``--before``/``--after`` given) — for every ISO
   present in both golden sets, compare each result parquet
   (``dispatch/<year>_P1.parquet``, ``system.parquet``, ``flows.parquet``,
   ``storage.parquet``) column-by-column via ``scripts/regression_check`` at the
   stage tolerance. Byte-identity (``--mode byte``) is the pure-code-motion
   standard from plan §7.2; ``--mode builder`` permits ≤1e-9 float
   reassociation for the interchange/fleet builder swaps.
2. **Reshuffle localization** — ``scripts/diff_warmstart_bundles.py`` per year,
   to show any marginal-tie reshuffle per ``plant_code`` (informational; helps
   confirm a builder-stage diff is tie-only).
3. **Trivial-case smoke tests** — ``pytest tests/test_regression_smoke.py``
   (fast, CI-able; the per-ISO 1-gen/1-zone/24-h LP guard).
4. **Quarantine + registry gates** — ``scripts/legitimacy_diagnostics.py
   --keepers`` (holdout quarantine: no solve year outside 2023-2025) and
   ``scripts/audit_keepers.py`` (no off-registry knob / drift).

Checks 3-4 always run; check 1-2 run only when both golden dirs are supplied
(so the script doubles as the fast CI guard when no goldens are captured yet).
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))


def _load_regression_check():
    """Import the existing column-diff engine without reinventing it."""
    spec = importlib.util.spec_from_file_location(
        "regression_check", REPO / "scripts" / "regression_check.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Result parquet files a calibration bundle carries (relative to the bundle dir).
# dispatch/*.parquet is expanded per year; the rest are top-level singletons.
_TOPLEVEL_FILES = ("system.parquet", "flows.parquet", "storage.parquet")


def _bundle_files(iso_dir: Path) -> list[str]:
    """Relative paths of every result parquet in a golden ISO bundle."""
    files = [
        str(p.relative_to(iso_dir))
        for p in sorted((iso_dir / "dispatch").glob("*.parquet"))
    ]
    files += [f for f in _TOPLEVEL_FILES if (iso_dir / f).is_file()]
    return files


def diff_goldens(
    before: Path, after: Path, atol: float, rtol: float
) -> tuple[bool, list[str]]:
    """Compare two golden roots ISO-by-ISO, file-by-file, column-by-column.

    Returns ``(passed, log_lines)``.
    """
    rc = _load_regression_check()
    log: list[str] = []
    passed = True

    # ISO bundle dirs only; skip bundle-io scratch (``_shared``) and any other
    # underscore-prefixed helper dir.
    isos_before = {
        p.name for p in before.iterdir() if p.is_dir() and not p.name.startswith("_")
    }
    isos_after = {
        p.name for p in after.iterdir() if p.is_dir() and not p.name.startswith("_")
    }
    only_before = isos_before - isos_after
    only_after = isos_after - isos_before
    if only_before:
        log.append(f"FAIL  ISOs only in before: {sorted(only_before)}")
        passed = False
    if only_after:
        log.append(f"FAIL  ISOs only in after: {sorted(only_after)}")
        passed = False

    common_isos = sorted(isos_before & isos_after)
    if not common_isos:
        log.append(f"FAIL  no common ISO golden dirs in {before} / {after}")
        return False, log

    for iso in common_isos:
        b_dir, a_dir = before / iso, after / iso
        files_b = set(_bundle_files(b_dir))
        files_a = set(_bundle_files(a_dir))
        if files_b != files_a:
            log.append(
                f"FAIL  {iso}: file set differs "
                f"(only-before={sorted(files_b - files_a)}, "
                f"only-after={sorted(files_a - files_b)})"
            )
            passed = False
        iso_ok = True
        n_cols = 0
        for rel in sorted(files_b & files_a):
            results = rc.compare_parquet(b_dir / rel, a_dir / rel, atol, rtol)
            n_cols += len(results)
            for col, col_ok, max_dev, metric in results:
                if not col_ok:
                    iso_ok = False
                    passed = False
                    log.append(
                        f"FAIL  {iso}/{rel}:{col}  max_dev={max_dev:.3e} ({metric})"
                    )
        if iso_ok:
            log.append(
                f"PASS  {iso}: {len(files_b & files_a)} files, {n_cols} "
                f"numeric columns within tolerance (atol={atol}, rtol={rtol})"
            )
    return passed, log


def localize_reshuffle(before: Path, after: Path) -> list[str]:
    """Run diff_warmstart_bundles.py per year for each common ISO (informational)."""
    log: list[str] = []
    script = REPO / "scripts" / "diff_warmstart_bundles.py"
    isos = sorted(
        {p.name for p in before.iterdir() if p.is_dir() and not p.name.startswith("_")}
        & {p.name for p in after.iterdir() if p.is_dir() and not p.name.startswith("_")}
    )
    for iso in isos:
        b_dir, a_dir = before / iso, after / iso
        years = sorted(
            int(p.stem.split("_")[0]) for p in (b_dir / "dispatch").glob("*_P1.parquet")
        )
        for year in years:
            try:
                out = subprocess.run(
                    [sys.executable, str(script), str(b_dir), str(a_dir), str(year)],
                    capture_output=True,
                    text=True,
                    cwd=REPO,
                    timeout=600,
                )
                tail = [
                    ln
                    for ln in out.stdout.splitlines()
                    if "reshuffle" in ln or "total annual gen" in ln
                ]
                for ln in tail:
                    log.append(f"  {iso} {year}: {ln.strip()}")
            except Exception as exc:  # informational only, never fatal
                log.append(f"  {iso} {year}: reshuffle localization skipped ({exc})")
    return log


def _run(cmd: list[str], label: str) -> tuple[bool, str]:
    """Run a subprocess gate; return (passed, one-line summary)."""
    try:
        proc = subprocess.run(
            cmd, cwd=REPO, capture_output=True, text=True, timeout=1800
        )
    except Exception as exc:
        return False, f"{label}: ERROR ({exc})"
    ok = proc.returncode == 0
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    last = tail[-1] if tail else ""
    return ok, f"{label}: {'PASS' if ok else 'FAIL'} (rc={proc.returncode}) {last}"


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, help="baseline golden root")
    parser.add_argument("--after", type=Path, help="new golden root")
    parser.add_argument(
        "--mode",
        choices=["byte", "builder"],
        default="byte",
        help="byte (pure code motion, atol=rtol=0) or builder (swap, 1e-9). "
        "Overridden by explicit --atol/--rtol.",
    )
    parser.add_argument("--atol", type=float, default=None, help="override abs tol")
    parser.add_argument("--rtol", type=float, default=None, help="override rel tol")
    parser.add_argument(
        "--skip-smoke", action="store_true", help="skip pytest smoke suite"
    )
    parser.add_argument(
        "--skip-quarantine",
        action="store_true",
        help="skip legitimacy/audit keeper gates",
    )
    args = parser.parse_args()

    atol = (
        args.atol if args.atol is not None else (0.0 if args.mode == "byte" else 1e-9)
    )
    rtol = (
        args.rtol if args.rtol is not None else (0.0 if args.mode == "byte" else 1e-9)
    )

    print("=" * 72)
    print(f"REGRESSION GATE  (mode={args.mode}, atol={atol}, rtol={rtol})")
    print("=" * 72)

    summary: list[tuple[str, bool]] = []

    # 1-2. Golden diff + reshuffle localization (only when goldens supplied).
    if args.before and args.after:
        if not args.before.is_dir() or not args.after.is_dir():
            print(f"ERROR: golden dir missing ({args.before} / {args.after})")
            return 1
        print("\n[1] Golden bundle diff")
        ok, log = diff_goldens(args.before, args.after, atol, rtol)
        for ln in log:
            print("   ", ln)
        summary.append(("golden-diff", ok))

        print("\n[2] Reshuffle localization (informational)")
        for ln in localize_reshuffle(args.before, args.after):
            print(ln)
    else:
        print("\n[1-2] Golden diff skipped (no --before/--after supplied)")

    # 3. Trivial-case smoke suite.
    if not args.skip_smoke:
        print("\n[3] Trivial-case smoke tests")
        ok, line = _run(
            [sys.executable, "-m", "pytest", "tests/test_regression_smoke.py", "-q"],
            "smoke",
        )
        print("   ", line)
        summary.append(("smoke", ok))

    # 4. Quarantine + registry gates.
    if not args.skip_quarantine:
        print("\n[4] Quarantine + registry gates")
        ok1, line1 = _run(
            [sys.executable, "scripts/legitimacy_diagnostics.py", "--keepers"],
            "legitimacy(--keepers)",
        )
        print("   ", line1)
        summary.append(("legitimacy", ok1))
        ok2, line2 = _run([sys.executable, "scripts/audit_keepers.py"], "audit_keepers")
        print("   ", line2)
        summary.append(("audit_keepers", ok2))

    print("\n" + "=" * 72)
    all_ok = all(ok for _, ok in summary)
    for name, ok in summary:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print("=" * 72)
    print("RESULT:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
