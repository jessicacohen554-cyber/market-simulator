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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--label", required=True, help="Dashboard display label / shorthand source."
    )
    ap.add_argument(
        "--bundle", required=True, help="Bundle dir, e.g. results/calibration/<name>."
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
    # Best-effort — a scorer error must never block registration.
    try:
        sys.path.insert(0, str(REPO / "scripts"))
        import calibration_verdict as cv

        print(cv.headline(cv.determine(rid)))
    except Exception as exc:  # pragma: no cover - defensive
        print(f"determination: unavailable ({exc})")


if __name__ == "__main__":
    main()
