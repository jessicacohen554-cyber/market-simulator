"""Register one calibration bundle on the dashboard, conflict-free.

A single calibration run adds itself to the dashboard by writing only files in
namespaces unique to this run (or byte-deterministic per-ISO parts) — hence
any number of runs landing at once, across any mix of ISOs, never conflict:

  * ``frontend/data/backcast/registry/<id>.json`` — the sidecar: the COMPLETE
    manifest entry (id, label, date, shorthand, definition, years, iso, file)
    plus the bundle path. ``scripts/build_manifest.py`` assembles
    ``manifest.js`` from sidecars alone, so edit the sidecar to refine a
    label/definition.
  * ``frontend/data/backcast/runs/<id>.js`` — this run's own payload.
  * ``frontend/data/backcast/bench/<ISO>/<year>.json.gz`` — the per-(ISO, year)
    benchmark parts for this run's years (newest run covering a year supplies
    it; unchanged content re-renders to identical bytes, so these only appear
    in the diff when the benchmark genuinely changed).

The shared ``manifest.js`` / ``benchmark.js`` are GENERATED — rebuilt from
sidecars + parts by ``scripts/build_manifest.py`` locally and at deploy time
(the deploy workflow is their single writer). Never hand-commit them. The
results surface is the codebase site: ``docs/codebase-site/backcast-runs.html``
(run explorer) and ``calibration-status.html`` (all-ISO keeper summary).

Commit: the bundle dir, the sidecar, ``runs/<id>.js``, and anything changed
under ``bench/``. Prints ``RUN_ID=<id>`` on stdout so callers can stage by id.

Usage:
    python scripts/dashboard_add_run.py --label "ct sweep 1.5" \
        --bundle results/calibration/ct_sweep_15
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
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

DATA_DIR = REPO / "frontend" / "data" / "backcast"
REGISTRY_DIR = DATA_DIR / "registry"
RUNS_DIR = DATA_DIR / "runs"
KEEPERS_PATH = DATA_DIR / "keepers.json"
CALIB_ROOT = REPO / "results" / "calibration"

# Retention rule (2026-06-21, user-set; supersedes the 10-run rule): the
# dashboard keeps the top-15 runs per ISO. When a registration pushes an ISO
# over the cap, ``prune_iso`` drops the displaced OLDEST runs — deleting the
# registry sidecar, the ``runs/<id>.js`` payload AND the mapped
# ``results/calibration/<bundle>/`` dir together, so the three stores can never
# drift into orphans (keepers and ablation-referenced twins are never pruned).
KEEP_PER_ISO = 15


def _protected_run_ids() -> set[str]:
    """Return run ids retention must never prune, whatever their age.

    * Every current keeper in ``keepers.json`` — dropping its bundle would break
      the all-ISO Calibration Status page (whose verdicts read the bundle).
    * Any run referenced by a surviving sidecar's ``ablation_twin`` /
      ``ablation_of`` link — pruning it would dangle the cross-reference that
      ``check_registry_payload_parity.py`` enforces.
    """
    protected: set[str] = set()
    if KEEPERS_PATH.exists():
        keepers = json.loads(KEEPERS_PATH.read_text())
        protected.update(keepers.get("keepers", []))
        # the per-ISO convenience keys (CAISO/ERCOT/...) duplicate the list;
        # collect any id-shaped top-level value defensively.
        protected.update(
            v for v in keepers.values() if isinstance(v, str) and v.startswith("20")
        )
    for path in REGISTRY_DIR.glob("*.json"):
        try:
            rec = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        for field in ("ablation_twin", "ablation_of"):
            ref = rec.get(field)
            if isinstance(ref, str) and ref.startswith("20"):
                protected.add(ref)
    return protected


def _bundle_dir(rec: dict) -> Path | None:
    """Resolve a sidecar's ``bundle`` field to a path under
    ``results/calibration`` (None if absent or — as a hard safety guard —
    outside that root, so retention can never delete an arbitrary path)."""
    raw = rec.get("bundle")
    if not raw:
        return None
    p = Path(raw)
    p = p if p.is_absolute() else REPO / p
    try:
        p.resolve().relative_to(CALIB_ROOT.resolve())
    except ValueError:
        return None
    return p


def prune_iso(
    iso: str, *, keep: int = KEEP_PER_ISO, dry_run: bool = False
) -> list[str]:
    """Enforce the top-``keep``-per-ISO retention rule across all three stores.

    Keeps the ``keep`` newest runs for ``iso`` (by date, then id) plus every
    protected id, and for each displaced run deletes its registry sidecar,
    ``runs/<id>.js`` payload and mapped ``results/calibration/<bundle>/`` dir
    together. A bundle shared by a surviving sidecar is left in place (only its
    orphaned sidecar/payload go). Returns the pruned ids; caller stages the
    deletions with the rest of the commit.
    """
    protected = _protected_run_ids()
    entries: list[tuple[str, str, dict, Path]] = []
    for path in sorted(REGISTRY_DIR.glob("*.json")):
        try:
            rec = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if rec.get("iso") != iso:
            continue
        entries.append((rec.get("date", ""), rec.get("id", path.stem), rec, path))
    # Newest first (date, then id); the oldest beyond the cap fall off the end.
    entries.sort(key=lambda e: (e[0], e[1]), reverse=True)

    to_prune = [
        (rid, rec, sidecar)
        for _, rid, rec, sidecar in entries[keep:]
        if rid not in protected
    ]
    pruned_ids = {rid for rid, _, _ in to_prune}
    # Bundle paths still referenced by any run that is NOT being pruned — never
    # delete a directory another sidecar still points at.
    kept_bundles: set[Path] = set()
    for path in REGISTRY_DIR.glob("*.json"):
        try:
            rec = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if rec.get("id", path.stem) in pruned_ids:
            continue
        b = _bundle_dir(rec)
        if b is not None:
            kept_bundles.add(b.resolve())

    pruned: list[str] = []
    for rid, rec, sidecar in to_prune:
        payload = RUNS_DIR / f"{rid}.js"
        bundle = _bundle_dir(rec)
        drop_bundle = (
            bundle if (bundle and bundle.resolve() not in kept_bundles) else None
        )
        targets = [sidecar, payload] + ([drop_bundle] if drop_bundle else [])
        existing = [t for t in targets if t.exists()]
        note = " [dry-run]" if dry_run else ""
        print(
            f"  prune {rid}: "
            + (
                ", ".join(str(t.relative_to(REPO)) for t in existing)
                or "(nothing on disk)"
            )
            + note
        )
        if not dry_run:
            sidecar.unlink(missing_ok=True)
            payload.unlink(missing_ok=True)
            if drop_bundle and drop_bundle.exists():
                shutil.rmtree(drop_bundle)
        pruned.append(rid)
    return pruned


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--label", required=True, help="Dashboard display label / shorthand source."
    )
    ap.add_argument(
        "--bundle", required=True, help="Bundle dir, e.g. results/calibration/<name>."
    )
    ap.add_argument(
        "--no-prune",
        action="store_true",
        help="Skip the top-15-per-ISO retention sweep after registering.",
    )
    ap.add_argument(
        "--keep-per-iso",
        type=int,
        default=KEEP_PER_ISO,
        help=f"Retention cap per ISO (default {KEEP_PER_ISO}).",
    )
    args = ap.parse_args()

    bundle = Path(args.bundle)
    if not (bundle / "meta.json").exists():
        sys.exit(f"bundle {bundle} is missing meta.json; nothing to register.")

    # Derive the full manifest entry exactly as render_backcast.generate does,
    # so the sidecar id matches the runs/<id>.js it writes and build_manifest
    # can list the run without ever opening the bundle.
    entry = rb.manifest_entry(args.label, bundle)
    rid, iso = entry["id"], entry["iso"]

    # Store the bundle path relative to the repo root so the sidecar is portable
    # across checkouts (CI clones to a different absolute path).
    try:
        rel_bundle = str(bundle.resolve().relative_to(REPO))
    except ValueError:
        rel_bundle = str(bundle)

    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    sidecar = REGISTRY_DIR / f"{rid}.json"
    sidecar.write_text(json.dumps({**entry, "bundle": rel_bundle}, indent=2) + "\n")

    # Render this single run: writes its runs/<id>.js + the bench/<ISO>/<year>
    # parts for its years, and refreshes the LOCAL preview manifest/benchmark.
    # Commit the bundle, the sidecar, runs/<id>.js and any changed bench parts
    # — never the shared manifest.js/benchmark.js (deploy-workflow-owned).
    rb.generate([(args.label, bundle)])

    print(f"registered {rid!r} (iso={iso}, bundle={rel_bundle})")
    print(f"RUN_ID={rid}")

    # Re-determination trigger (docs/calibration-determination-rubric.md §6):
    # registering a run re-runs the scorer on its freshly-written committed
    # artifacts, so every registered run prints its calibration determination.
    # Also writes the plaintext metrics.json sidecar (G-49,
    # docs/verifying-dashboard-numbers.md) into the bundle so a verifier can
    # read the headline scored metrics without decoding runs/<id>.js.
    # Best-effort — a scorer error must never block registration.
    try:
        sys.path.insert(0, str(REPO / "scripts"))
        import calibration_verdict as cv

        verdict = cv.determine(rid)
        print(cv.headline(verdict))
        metrics_path = cv.write_metrics_sidecar(bundle, verdict)
        print(f"wrote {metrics_path.relative_to(REPO)}")
    except Exception as exc:  # pragma: no cover - defensive
        print(f"determination: unavailable ({exc})")

    # Retention: enforce the top-15-per-ISO cap for the ISO we just registered
    # into, deleting the sidecar + payload + bundle of any displaced oldest run
    # together (see KEEP_PER_ISO / prune_iso). Keepers and ablation-referenced
    # twins are never pruned. The caller stages the deletions with the commit.
    if not args.no_prune:
        pruned = prune_iso(iso, keep=args.keep_per_iso)
        if pruned:
            print(
                f"pruned {len(pruned)} run(s) beyond top-{args.keep_per_iso} "
                f"{iso} retention: {pruned}"
            )


if __name__ == "__main__":
    main()
