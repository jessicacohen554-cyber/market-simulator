"""Link a registered D-3 zero-forcing ablation twin to its keeper (rule 21).

The D-3 ablation twin (``docs/model-legitimacy-audit-2026-07.md`` §7 D-3,
CLAUDE.md rule 21) is a companion run solved with every merchant floor/bridge
off (``run_calibration_full.py --zero-forcing-ablation``). Once BOTH the keeper
and its twin are registered on the dashboard, this script wires them together:
it writes ``ablation_twin`` (the twin's run id), ``ablation_delta`` (the
per-class keeper-minus-twin TWh table computed from the two committed payloads,
no solve), and an optional free-text ``market_story`` into the KEEPER's registry
sidecar. The Run Explorer renders that block; ``audit_keepers.py`` check E9
fails a keeper that has no registered twin.

This is the "step between register and commit" the calibration-report skill
runs when a run is or becomes a keeper. Stdlib-only (json) plus the scorer's
payload loader; commit the changed keeper sidecar with the twin's per-run files.

Usage::

    python scripts/link_ablation_twin.py --keeper <keeper-id> --twin <twin-id> \
        --market-story "CT_PEAKER holds its evening shape without the drag; \
the +2.1 TWh the floor bought is the unexplained overnight residual (issue #NNN)."
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts import calibration_verdict as cv  # noqa: E402 (after sys.path insert)


def _payload(run_id: str) -> dict:
    """Return a registered run's decoded payload, or raise if it is missing."""
    art = cv.load_artifacts(run_id)
    if not art.get("payload"):
        raise SystemExit(f"run {run_id!r} has no committed runs/{run_id}.js payload.")
    return art["payload"]


def link(keeper_id: str, twin_id: str, market_story: str | None) -> dict:
    """Write the twin linkage + per-class delta into the keeper's sidecar.

    Returns the updated sidecar dict. Verifies the twin's ``run_config.json``
    actually records ``ablation_of`` (so a non-ablation run cannot be linked as a
    twin by mistake), then writes ``ablation_twin`` / ``ablation_delta`` /
    ``market_story`` and re-saves the keeper sidecar.
    """
    keeper_side = cv.REGISTRY_DIR / f"{keeper_id}.json"
    twin_side = cv.REGISTRY_DIR / f"{twin_id}.json"
    if not keeper_side.exists():
        raise SystemExit(
            f"no keeper sidecar registry/{keeper_id}.json — register it first."
        )
    if not twin_side.exists():
        raise SystemExit(
            f"no twin sidecar registry/{twin_id}.json — register the twin first."
        )

    twin_meta = json.loads(twin_side.read_text())
    twin_bundle = REPO / twin_meta.get("bundle", "")
    run_config = twin_bundle / "run_config.json"
    if run_config.exists():
        rc = json.loads(run_config.read_text())
        if not rc.get("ablation_of"):
            raise SystemExit(
                f"twin {twin_id!r} run_config.json has no 'ablation_of' — it was "
                "not solved with --zero-forcing-ablation; refusing to link."
            )

    delta = cv.compute_ablation_delta(_payload(keeper_id), _payload(twin_id))
    side = json.loads(keeper_side.read_text())
    side["ablation_twin"] = twin_id
    side["ablation_delta"] = delta
    if market_story is not None:
        side["market_story"] = market_story
    keeper_side.write_text(json.dumps(side, indent=2, sort_keys=True) + "\n")
    return side


def main() -> None:
    """CLI: link a keeper to its registered ablation twin (see module docstring)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keeper", required=True, help="keeper run id")
    ap.add_argument("--twin", required=True, help="ablation twin run id")
    ap.add_argument(
        "--market-story",
        default=None,
        help="Free-text market story: what each per-class delta means. A delta "
        'explainable only as "the floor buys the residual" is an open '
        "root-cause item, not a parameter (rule 21).",
    )
    args = ap.parse_args()
    side = link(args.keeper, args.twin, args.market_story)
    n = len(side.get("ablation_delta", []))
    print(f"linked {args.keeper} -> ablation_twin {args.twin} ({n} class deltas)")


if __name__ == "__main__":
    main()
