"""Register one calibration bundle on the dashboard, conflict-free.

A single calibration run must add itself to the dashboard WITHOUT touching the
shared ``manifest.js`` / ``benchmark.js`` (those are regenerated from the whole
set by ``regen_dashboard.py``). So this script writes only two per-run files,
both in a namespace unique to this run — hence two runs landing at once never
collide:

  * ``frontend/data/backcast/registry/<id>.json`` — the sidecar the deterministic
    regen reads: ``{id, label, bundle, iso}``.
  * ``frontend/data/backcast/runs/<id>.js`` — this run's own payload, so the run
    is viewable the instant it is committed (the manifest entry that lists it
    follows from the next ``regen_dashboard`` pass on main).

It re-renders the single run via ``render_backcast.generate`` (which also rewrites
the shared manifest/benchmark/html locally) but the caller is expected to stage
ONLY the bundle dir, the sidecar and ``runs/<id>.js`` — never the shared files.

Prints ``RUN_ID=<id>`` on stdout so the workflow can locate the file to stage.

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
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location(
    "render_backcast", str(REPO / "scripts" / "render_backcast.py"))
rb = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(rb)

REGISTRY_DIR = REPO / "frontend" / "data" / "backcast" / "registry"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", required=True,
                    help="Dashboard display label / shorthand source.")
    ap.add_argument("--bundle", required=True,
                    help="Bundle dir, e.g. results/calibration/<name>.")
    args = ap.parse_args()

    bundle = Path(args.bundle)
    if not (bundle / "meta.json").exists():
        sys.exit(f"bundle {bundle} is missing meta.json; nothing to register.")

    # Derive the run id exactly as render_backcast.generate does, so the sidecar
    # id matches the runs/<id>.js it writes and the manifest entry regen builds.
    rm = rb._run_meta(bundle, rb._slug(args.label))
    rid = rm["id"]
    iso = json.loads((bundle / "meta.json").read_text()).get("iso", "ERCOT")

    # Store the bundle path relative to the repo root so the sidecar is portable
    # across checkouts (CI clones to a different absolute path).
    try:
        rel_bundle = str(bundle.resolve().relative_to(REPO))
    except ValueError:
        rel_bundle = str(bundle)

    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    sidecar = REGISTRY_DIR / f"{rid}.json"
    sidecar.write_text(json.dumps(
        {"id": rid, "label": args.label, "bundle": rel_bundle, "iso": iso},
        indent=2) + "\n")

    # Render this single run so its runs/<id>.js exists immediately. This also
    # rewrites the shared manifest/benchmark/html locally; the caller stages
    # only the sidecar + runs/<id>.js + the bundle, leaving the shared files for
    # the deterministic regen on main.
    rb.generate([(args.label, bundle)], REPO / "backcast-results.html")

    print(f"registered {rid!r} (iso={iso}, bundle={rel_bundle})")
    print(f"RUN_ID={rid}")


if __name__ == "__main__":
    main()
