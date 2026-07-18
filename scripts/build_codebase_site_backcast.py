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

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _parse_manifest_js(path: Path) -> tuple[dict, list[dict]]:
    """Extract meta and manifest array from a manifest.js file.

    Anchors ``json.JSONDecoder.raw_decode`` at each assignment's opening bracket
    rather than a non-greedy ``\\{.*?\\};`` / ``\\[.*?\\];`` regex. A run's
    ``definition``/``market_story`` string may legitimately contain ``];`` or
    ``};`` (e.g. the C3c ``[7,9]`` band notation), which the non-greedy match
    truncated at — breaking the whole deploy with a JSONDecodeError and freezing
    the LIVE dashboard at the last successful build. ``raw_decode`` consumes
    exactly one well-formed JSON value from the bracket and ignores the trailing
    ``;`` and everything after, so any string content is safe.
    """
    text = path.read_text()
    dec = json.JSONDecoder()

    def _decode_after(marker: str):
        i = text.find(marker)
        if i < 0:
            sys.exit(f"Cannot parse manifest from {path}: missing {marker!r}")
        j = i + len(marker)
        while j < len(text) and text[j] not in "{[":
            j += 1
        if j >= len(text):
            sys.exit(f"Cannot parse manifest from {path}: no value after {marker!r}")
        obj, _ = dec.raw_decode(text, j)
        return obj

    return _decode_after("window.BC.meta="), _decode_after("window.BC.manifest=")


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

    meta, entries = _parse_manifest_js(manifest_js)
    # Every registered run flows through — registration enforces the
    # top-15-per-ISO retention, so the manifest is already the curated set.
    selected = entries
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
        f"codebase-site backcast: {copied_runs} run payloads copied across {isos} "
        f"({len(entries)} registered runs)"
    )


if __name__ == "__main__":
    main()
