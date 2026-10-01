"""SCN-WS4c — assemble one ISO's solved arms into a matrix dir and run the report.

Each arm is solved into its OWN ``--out-dir`` so its ``full_horizon_summary.json``
survives for registration, which puts each case's LP cache under
``<out-dir>/<ISO>/<cache_key>/``. ``scripts/report_scenario_deltas.py`` reads
cases through ``market_sim.results.cache``, whose ``CACHE_ROOT`` is the single
``results/`` root, so this script links each arm's cache bundle into
``results/<ISO>/<cache_key>`` (a gitignored path — .gitignore §7, the natural
home for transient per-ISO LP caches) and writes the ``meta.json`` the report
requires (``iso`` + ``cases``).

It runs no LP and changes no solved number: it is pure assembly plus a call to
SCN-WS4b's committed report path.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def arm_cache_dir(root: Path, iso: str, case: str) -> tuple[str, Path]:
    """Return ``(cache_key, bundle_dir)`` for one solved arm.

    Args:
        root: Campaign root, e.g. ``results/scn-ws4-probe``.
        iso: ISO code, upper case.
        case: Case name, e.g. ``LOAD-HI``.

    Returns:
        The arm's cache key and the directory holding its cached years.

    Raises:
        SystemExit: When the arm has no single cache bundle on disk.
    """
    base = root / iso.lower() / case / iso.upper()
    if not base.is_dir():
        raise SystemExit(f"no cache tree for {iso} {case} at {base}")
    keys = [p for p in base.iterdir() if p.is_dir() and (p / "config.yaml").exists()]
    if len(keys) != 1:
        raise SystemExit(f"{base}: expected exactly one cache key, found {len(keys)}")
    return keys[0].name, keys[0]


def main() -> None:
    """Link the arms into the shared cache root, write meta.json, run the report."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--cases", nargs="+", required=True)
    ap.add_argument("--root", type=Path, default=Path("results/scn-ws4-probe"))
    ap.add_argument("--reference-case", default="REF")
    ap.add_argument("--years", default=None)
    args = ap.parse_args()

    iso = args.iso.upper()
    root = args.root
    cases: dict[str, str] = {}
    for case in args.cases:
        key, bundle = arm_cache_dir(root, iso, case)
        cases[case] = key
        link = REPO / "results" / iso / key
        link.parent.mkdir(parents=True, exist_ok=True)
        if link.is_symlink() or link.exists():
            if link.is_symlink():
                link.unlink()
            else:
                raise SystemExit(f"{link} exists and is not a symlink — refusing")
        link.symlink_to(bundle.resolve())
        print(f"  linked {iso} {case:16} key={key}")

    matrix_dir = root / iso.lower() / "matrix"
    matrix_dir.mkdir(parents=True, exist_ok=True)
    (matrix_dir / "meta.json").write_text(
        json.dumps(
            {
                "iso": iso,
                "cases": cases,
                "label": "SCN-WS4c LOAD-HI probe (campaign scn-ws4-probe)",
                "matrix_id": f"scn-ws4-probe-{iso.lower()}",
                "matrix_path": str(matrix_dir),
            },
            indent=1,
        )
    )
    cmd = [
        sys.executable,
        "scripts/report_scenario_deltas.py",
        "--matrix-dir",
        str(matrix_dir),
        "--reference-case",
        args.reference_case,
        "--output-dir",
        str(root / iso.lower() / "report"),
    ]
    if args.years:
        cmd += ["--years", args.years]
    print("  " + " ".join(cmd))
    raise SystemExit(subprocess.call(cmd, cwd=REPO))


if __name__ == "__main__":
    main()
