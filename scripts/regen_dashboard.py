"""Deterministically regenerate the backcast dashboard from the run registry.

This is the heavy, LOCAL full rebuild: it globs every registry sidecar and
re-renders the whole curated set in one pass via ``render_backcast.generate``
— rewriting every ``runs/<id>.js``, every ``bench/<ISO>/<year>.json.gz`` part
and the local preview ``manifest.js``/``benchmark.js``. It needs every bundle
present plus the model package, so it is for full refreshes after
deleting/relabelling bundles or changing the payload schema. View the result
through ``docs/codebase-site/backcast-runs.html``.

CI never runs it: the Pages deploy assembles the shared files from the
committed sidecars + bench parts with the stdlib-only
``scripts/build_manifest.py`` (seconds, no bundles needed). To register a
single new run, use ``scripts/dashboard_add_run.py`` instead.

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
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location(
    "render_backcast", str(REPO / "scripts" / "render_backcast.py")
)
rb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rb)

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
        bundle = (
            REPO / rec["bundle"]
            if not Path(rec["bundle"]).is_absolute()
            else Path(rec["bundle"])
        )
        if not (bundle / "meta.json").exists():
            print(
                f"  skip {path.name}: bundle {rec['bundle']} not found "
                "(missing meta.json)",
                file=sys.stderr,
            )
            continue
        entries.append({**rec, "_bundle_path": bundle})
    entries.sort(key=lambda e: (e.get("id", ""), e.get("label", "")))
    return entries


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--registry-dir", default=str(REGISTRY_DIR))
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=None,
        help="Restrict to these calendar years (default: all).",
    )
    args = ap.parse_args()

    registry_dir = Path(args.registry_dir)
    if not registry_dir.exists():
        sys.exit(f"registry dir {registry_dir} does not exist; nothing to regenerate.")
    entries = _load_registry(registry_dir)
    if not entries:
        sys.exit(
            "registry is empty (no usable bundles); refusing to wipe the dashboard."
        )
    runs = [(e["label"], e["_bundle_path"]) for e in entries]
    print(f"regenerating dashboard from {len(runs)} registry entries:")
    for e in entries:
        print(f"  - {e['label']!r} <- {e['bundle']}")
    rb.generate(runs, years=set(args.years) if args.years else None)


if __name__ == "__main__":
    main()
