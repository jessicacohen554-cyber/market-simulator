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


def _dry_run(runs: list[tuple[str, Path]], years: set[int] | None) -> int:
    """Render into a throwaway dir and report parity vs the committed tree.

    Non-mutating: reroutes ``render_backcast``'s output constants to a temp dir,
    renders every registered run there, then diffs the produced
    ``runs/<id>.js`` + ``bench/<ISO>/<year>.json.gz`` against the committed
    copies under ``frontend/data/backcast/`` (``manifest.js``/``benchmark.js``
    are deploy-generated previews, so they are reported but not gated). Prints a
    per-file verdict and returns 0 when every rendered file is byte-identical to
    what is committed (full-render parity), 1 otherwise. Use it before/after a
    bundle sweep to prove the surviving runs render unchanged.
    """
    import filecmp
    import tempfile

    committed = REPO / "frontend" / "data" / "backcast"
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "backcast"
        rb.DATA_DIR, rb.RUNS_DIR, rb.BENCH_DIR = tmp, tmp / "runs", tmp / "bench"
        rb.generate(runs, years=years)
        rendered = sorted(
            p
            for p in tmp.rglob("*")
            if p.is_file() and p.name not in ("manifest.js", "benchmark.js")
        )
        identical = changed = new = 0
        for p in rendered:
            rel = p.relative_to(tmp)
            other = committed / rel
            if not other.exists():
                new += 1
                print(f"  NEW      {rel} (rendered, not committed)")
            elif filecmp.cmp(p, other, shallow=False):
                identical += 1
            else:
                changed += 1
                print(f"  CHANGED  {rel}")
    print(
        f"dry-run parity: {identical} identical, {changed} changed, {new} new "
        f"(of {len(rendered)} rendered files; manifest.js/benchmark.js excluded)"
    )
    return 0 if (changed == 0 and new == 0) else 1


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
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Render into a temp dir and report parity vs the committed tree "
        "without writing anything (exit 1 if any rendered file differs).",
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
    years = set(args.years) if args.years else None
    if args.dry_run:
        print(f"dry-run: rendering {len(runs)} registry entries into a temp dir")
        sys.exit(_dry_run(runs, years))
    print(f"regenerating dashboard from {len(runs)} registry entries:")
    for e in entries:
        print(f"  - {e['label']!r} <- {e['bundle']}")
    rb.generate(runs, years=years)


if __name__ == "__main__":
    main()
