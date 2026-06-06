"""Deterministically regenerate the backcast dashboard from the run registry.

The dashboard's shared files — ``frontend/data/backcast/manifest.js``,
``benchmark.js`` and the ``backcast-results.html`` shell — are NOT hand-edited
by any single calibration run (that would make concurrent runs race on a shared
file and silently drop each other). Instead each run drops a tiny, per-run
*registry sidecar* at ``frontend/data/backcast/registry/<id>.json`` recording
just its display label and bundle path. This script is the single deterministic
reducer: it globs every sidecar, renders the whole curated set in one pass via
``render_backcast.generate`` and rewrites the shared files plus every
``runs/<id>.js``. Because it consumes *all* sidecars present, the output is the
same regardless of the order runs landed — so concurrent merges to main never
lose a run.

It is invoked in a post-merge step on ``main`` (the ``regenerate-dashboard``
workflow) and at the end of the bulk-merge workflow. Run it locally to refresh
the dashboard after adding/removing bundles.

Usage:
    python scripts/regen_dashboard.py [--registry-dir DIR] [--years 2023 2024]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location(
    "render_backcast", str(REPO / "scripts" / "render_backcast.py"))
rb = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(rb)

REGISTRY_DIR = REPO / "frontend" / "data" / "backcast" / "registry"


def _load_registry(registry_dir: Path) -> list[dict]:
    """Return the registry entries sorted deterministically by id then label.

    Each entry is ``{"id", "label", "bundle", "iso"}``. Entries whose bundle
    directory is missing or incomplete are dropped with a warning so a
    half-synced checkout still produces a valid dashboard rather than crashing
    (the run reappears on the next regen once its bundle is present).
    """
    entries: list[dict] = []
    for path in sorted(registry_dir.glob("*.json")):
        try:
            rec = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            print(f"  skip {path.name}: invalid JSON ({exc})", file=sys.stderr)
            continue
        bundle = REPO / rec["bundle"] if not Path(rec["bundle"]).is_absolute() \
            else Path(rec["bundle"])
        if not (bundle / "meta.json").exists():
            print(f"  skip {path.name}: bundle {rec['bundle']} not found "
                  "(missing meta.json)", file=sys.stderr)
            continue
        entries.append({**rec, "_bundle_path": bundle})
    entries.sort(key=lambda e: (e.get("id", ""), e.get("label", "")))
    return entries


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--registry-dir", default=str(REGISTRY_DIR))
    ap.add_argument("--out", default=str(REPO / "backcast-results.html"))
    ap.add_argument("--years", nargs="+", type=int, default=None,
                    help="Restrict to these calendar years (default: all).")
    args = ap.parse_args()

    registry_dir = Path(args.registry_dir)
    if not registry_dir.exists():
        sys.exit(f"registry dir {registry_dir} does not exist; nothing to "
                 "regenerate.")
    entries = _load_registry(registry_dir)
    if not entries:
        sys.exit("registry is empty (no usable bundles); refusing to wipe the "
                 "dashboard.")
    runs = [(e["label"], e["_bundle_path"]) for e in entries]
    print(f"regenerating dashboard from {len(runs)} registry entries:")
    for e in entries:
        print(f"  - {e['label']!r} <- {e['bundle']}")
    rb.generate(runs, Path(args.out),
                years=set(args.years) if args.years else None)


if __name__ == "__main__":
    main()
