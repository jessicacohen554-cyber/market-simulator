"""Stamp the holdout comparison block onto a 2022 touchpoint's registry sidecar.

The run explorer renders a dedicated **Validation Touchpoint** panel for any
run whose sidecar carries a ``holdout`` block. This writes that block by
scoring BOTH runs with ``scripts/calibration_verdict.py`` from committed
artifacts only — no LP is constructed, no bundle is re-solved — so the panel
shows the one comparison a touchpoint exists to make:

    the keeper's IN-SAMPLE determination (2023-2025, the tuned window)
    vs
    the same frozen recipe's HOLDOUT determination (2022, never tuned on)

criterion by criterion, with each criterion's status on both sides. A criterion
that passes in-sample and fails on the holdout is the signal; one that fails on
both is a known limitation travelling, not a new discovery. The panel labels
which is which rather than leaving the reader to diff two verdicts by eye.

The block also carries the rule-22 tier semantics verbatim, because the single
most misusable number on this dashboard is a validation-tier result quoted as a
certified out-of-sample skill number. The panel states it is not one.

Usage:
    python scripts/stamp_touchpoint_holdout.py \
        --run-id 2026-08-05-neiso-2022-touchpoint \
        --keeper-id 2026-08-05-neiso-83-ca1-reclass
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "frontend" / "data" / "backcast" / "registry"

# Rule 22's own words, carried onto the page so the panel cannot be read as a
# skill claim. Kept here (not in the JS) so every touchpoint says it identically.
TIER_CAVEAT = (
    "Validation tier: ITERABLE model-SELECTION evidence. This is NOT a "
    "certified out-of-sample skill number and must never be quoted as one — "
    "the year may be re-spent after the open availability-envelope defect "
    "lands. The touch-once locked test (2019 / H1-2026) is NOT spent here."
)

ENVELOPE_CAVEAT = (
    "Scored against a known-imperfect availability envelope: the CAMPD "
    "unit-outage detector still books sustained economic layup as mechanical "
    "outage, and a residual over-count survives the 2026-07-26 merit-order "
    "guard. Every miss below is measured against a fleet whose availability "
    "is about to change, so none of them is attributable to forecast error "
    "alone until the run is repeated after that fix."
)


def score(run_id: str) -> dict:
    """Return calibration_verdict's machine verdict for one registered run."""
    out = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "calibration_verdict.py"),
            "--run-id",
            run_id,
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    if out.returncode != 0 and not out.stdout.strip():
        raise SystemExit(f"scoring {run_id} failed:\n{out.stderr[-2000:]}")
    return json.loads(out.stdout)


def criterion_rows(holdout: dict, keeper: dict) -> list[dict]:
    """Pair the two verdicts criterion by criterion, classifying each pair.

    ``verdict`` is the reader's takeaway, not a re-score:
      * ``held``      — passes in-sample AND on the holdout
      * ``degraded``  — passes in-sample, misses on the holdout (THE signal)
      * ``carried``   — misses on both (a known limitation travelling)
      * ``improved``  — misses in-sample, passes on the holdout
    """
    hc = holdout.get("criteria", {})
    kc = keeper.get("criteria", {})
    passish = {"PASS"}
    rows = []
    for key in [k for k in hc if k in kc]:
        h_stat = hc[key].get("status", "")
        k_stat = kc[key].get("status", "")
        h_ok, k_ok = h_stat in passish, k_stat in passish
        if k_ok and h_ok:
            verdict = "held"
        elif k_ok and not h_ok:
            verdict = "degraded"
        elif not k_ok and h_ok:
            verdict = "improved"
        else:
            verdict = "carried"
        rows.append(
            {
                "key": key,
                "label": hc[key].get("label", key),
                "tier": hc[key].get("tier", ""),
                "inSample": k_stat,
                "holdout": h_stat,
                "verdict": verdict,
            }
        )
    order = {"degraded": 0, "carried": 1, "improved": 2, "held": 3}
    rows.sort(key=lambda r: (order.get(r["verdict"], 9), r["key"]))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", required=True, help="the touchpoint run id")
    ap.add_argument("--keeper-id", required=True, help="the ISO's keeper run id")
    ap.add_argument("--holdout-year", type=int, default=2022, help="default 2022")
    args = ap.parse_args()

    sidecar_path = REGISTRY / f"{args.run_id}.json"
    if not sidecar_path.exists():
        raise SystemExit(f"no sidecar at {sidecar_path} — register the run first")

    holdout_v = score(args.run_id)
    keeper_v = score(args.keeper_id)
    rows = criterion_rows(holdout_v, keeper_v)

    degraded = [r for r in rows if r["verdict"] == "degraded"]
    carried = [r for r in rows if r["verdict"] == "carried"]

    sidecar = json.loads(sidecar_path.read_text())
    sidecar["holdout"] = {
        "tier": "validation",
        "year": args.holdout_year,
        "keeper": args.keeper_id,
        "keeperDetermination": keeper_v.get("determination"),
        "keeperYears": keeper_v.get("scorable_years", []),
        "holdoutDetermination": holdout_v.get("determination"),
        "criteria": rows,
        "nDegraded": len(degraded),
        "nCarried": len(carried),
        "tierCaveat": TIER_CAVEAT,
        "envelopeCaveat": ENVELOPE_CAVEAT,
    }
    sidecar_path.write_text(json.dumps(sidecar, indent=1) + "\n")

    print(f"stamped holdout block onto {sidecar_path.relative_to(REPO)}")
    print(
        f"  keeper {args.keeper_id}: {keeper_v.get('determination')} "
        f"on {keeper_v.get('scorable_years')}"
    )
    print(f"  holdout {args.holdout_year}: {holdout_v.get('determination')}")
    for r in rows:
        print(
            f"    {r['verdict']:9s} {r['key']:14s} "
            f"in-sample {r['inSample']:12s} holdout {r['holdout']}"
        )


if __name__ == "__main__":
    main()
