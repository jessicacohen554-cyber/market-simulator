"""Copy a backcast data subset into the codebase-site directory.

Selects keeper + most-recent-9 runs per ISO from the assembled manifest,
copies their payloads/registry/bench into ``docs/codebase-site/data/backcast/``
(or the equivalent path under a staging directory) so the codebase explorer
pages serve self-contained backcast data without reaching into
``../../frontend/data/backcast/``.

Run AFTER ``build_manifest.py`` so the manifest/benchmark files are fresh.

Usage::

    # Local preview (writes into docs/codebase-site/data/backcast/)
    python scripts/build_codebase_site_backcast.py

    # Deploy staging (writes into _site/docs/codebase-site/data/backcast/)
    python scripts/build_codebase_site_backcast.py --site-dir _site
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNS_PER_ISO = 9


def _parse_manifest_js(path: Path) -> tuple[dict, list[dict]]:
    """Extract meta and manifest array from a manifest.js file."""
    text = path.read_text()
    m_meta = re.search(r"window\.BC\.meta\s*=\s*(\{.*?\});", text, re.DOTALL)
    m_manifest = re.search(r"window\.BC\.manifest\s*=\s*(\[.*?\]);", text, re.DOTALL)
    if not m_meta or not m_manifest:
        sys.exit(f"Cannot parse manifest from {path}")
    return json.loads(m_meta.group(1)), json.loads(m_manifest.group(1))


def _select_runs(entries: list[dict], keepers: set[str]) -> list[dict]:
    """Return keeper + most-recent RUNS_PER_ISO entries per ISO."""
    by_iso: dict[str, list[dict]] = {}
    for e in entries:
        by_iso.setdefault(e["iso"], []).append(e)

    selected_ids: set[str] = set()
    for iso in sorted(by_iso):
        runs = by_iso[iso]
        for r in runs:
            if r["id"] in keepers:
                selected_ids.add(r["id"])
        for r in runs[-RUNS_PER_ISO:]:
            selected_ids.add(r["id"])

    return [e for e in entries if e["id"] in selected_ids]


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

    keepers_path = src_data / "keepers.json"
    keeper_ids: set[str] = set()
    if keepers_path.exists():
        kj = json.loads(keepers_path.read_text())
        keeper_ids = set(kj.get("keepers", []))

    meta, entries = _parse_manifest_js(manifest_js)
    selected = _select_runs(entries, keeper_ids)
    selected_ids = {e["id"] for e in selected}

    # Create output directories
    for sub in ("runs", "registry", "bench"):
        (dst_data / sub).mkdir(parents=True, exist_ok=True)

    # Write filtered manifest.js
    meta_js = json.dumps(meta, sort_keys=True)
    manifest_arr = json.dumps(selected, sort_keys=True)
    (dst_data / "manifest.js").write_text(
        f"window.BC=window.BC||{{}};window.BC.meta={meta_js};"
        f"window.BC.manifest={manifest_arr};"
    )

    # Copy shared data files
    for name in ("benchmark.js", "completeness.js", "status.js", "keepers.json"):
        src = src_data / name
        if src.exists():
            shutil.copy2(src, dst_data / name)

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
        f"codebase-site backcast: {copied_runs} runs across {isos} "
        f"({len(selected_ids)} selected from {len(entries)} total)"
    )


if __name__ == "__main__":
    main()
