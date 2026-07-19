"""Copy the backcast data into the codebase-site directory.

Copies EVERY registered run from the assembled manifest — the codebase-site
pages (``backcast-runs.html`` / ``calibration-status.html``) are THE results
dashboard, so all runs on the registry flow through (the top-15-per-ISO
retention rule is enforced at registration, not here). Payloads/registry/bench
land in ``docs/codebase-site/data/backcast/`` (or the equivalent path under a
staging directory) so the codebase explorer pages serve self-contained
backcast data without reaching into ``../../frontend/data/backcast/``.

Run AFTER ``build_manifest.py`` so the manifest/benchmark files are fresh.

Usage::

    # Local preview (writes into docs/codebase-site/data/backcast/)
    python scripts/build_codebase_site_backcast.py

    # Deploy staging (writes into _site/docs/codebase-site/data/backcast/)
    python scripts/build_codebase_site_backcast.py --site-dir _site
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.lib import backcast_artifacts as ba  # noqa: E402  (stdlib-only)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--site-dir",
        default=str(REPO),
        help="Root directory (repo root or Pages staging root).",
    )
    args = ap.parse_args()
    site = Path(args.site_dir)

    src_data = site / "frontend" / "data" / "backcast"
    dst_data = site / "docs" / "codebase-site" / "data" / "backcast"

    manifest_js = src_data / "manifest.js"
    if not manifest_js.exists():
        sys.exit(
            f"manifest.js not found at {manifest_js} — run build_manifest.py first"
        )

    try:
        meta, entries = ba.parse_manifest_js(manifest_js)
    except ValueError as exc:
        sys.exit(str(exc))
    # Every registered run flows through — registration enforces the
    # top-15-per-ISO retention, so the manifest is already the curated set.
    selected = entries
    selected_ids = {e["id"] for e in selected}

    # Create output directories
    for sub in ("runs", "registry", "bench"):
        (dst_data / sub).mkdir(parents=True, exist_ok=True)

    # Write filtered manifest.js
    ba.write_manifest_js(dst_data / "manifest.js", meta, selected, sort_keys=True)

    # Copy shared data files. keepers/ + status/ are the per-ISO sharded
    # stores (2026-07-19); the monolithic status.js / keepers.json are retired
    # but still copied when present so a historical checkout previews cleanly.
    for name in ("benchmark.js", "completeness.js", "status.js", "keepers.json"):
        src = src_data / name
        if src.exists():
            shutil.copy2(src, dst_data / name)
    for sub in ("keepers", "status"):
        src = src_data / sub
        if src.is_dir():
            shutil.copytree(src, dst_data / sub, dirs_exist_ok=True)

    # Copy selected run payloads and registry sidecars
    copied_runs = 0
    for rid in sorted(selected_ids):
        run_src = src_data / "runs" / f"{rid}.js"
        reg_src = src_data / "registry" / f"{rid}.json"
        if run_src.exists():
            shutil.copy2(run_src, dst_data / "runs" / f"{rid}.js")
            copied_runs += 1
        if reg_src.exists():
            shutil.copy2(reg_src, dst_data / "registry" / f"{rid}.json")

    # Copy bench directory (all ISOs — small, ~6 MB total)
    bench_src = src_data / "bench"
    bench_dst = dst_data / "bench"
    if bench_src.exists():
        if bench_dst.exists():
            shutil.rmtree(bench_dst)
        shutil.copytree(bench_src, bench_dst)

    isos = sorted({e["iso"] for e in selected})
    print(
        f"codebase-site backcast: {copied_runs} run payloads copied across {isos} "
        f"({len(entries)} registered runs)"
    )


if __name__ == "__main__":
    main()
