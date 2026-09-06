"""Stamp the holdout comparison block onto a 2022 touchpoint's registry sidecar.

The ``holdout`` block is what FOLDS a touchpoint into its keeper: the run
explorer hides the stamped run from the run list, offers its years in the
keeper's own year selector, and renders them as ORDINARY YEAR COLUMNS in the
keeper's report — no separate panel, no tier badge (owner instruction
2026-09-06, rule 30 amendment; the dedicated "Validation Touchpoint" panel this
docstring used to describe was removed then, since a folded touchpoint IS the
keeper's recipe on another year and reading one configuration should not take
two panels). Rule 22's tier caveat survives as a single footnote naming the
held-out years. This writes that block by scoring BOTH runs with
``scripts/calibration_verdict.py`` from committed artifacts only — no LP is
constructed, no bundle is re-solved — so the stamped block records the one
comparison a touchpoint exists to make:

    the keeper's IN-SAMPLE determination (2023-2025, the tuned window)
    vs
    the same frozen recipe's HOLDOUT determination (2022, never tuned on)

criterion by criterion, with each criterion's status on both sides. A criterion
that passes in-sample and fails on the holdout is the signal; one that fails on
both is a known limitation travelling, not a new discovery. The block records
which is which so a later reader need not diff two verdicts by eye, and the
per-year determinations it carries are what the Calibration Status page's
holdout ladder renders (rule 30(b)).

The block also carries the rule-22 tier semantics verbatim, because the single
most misusable number on this dashboard is a validation-tier result quoted as a
certified out-of-sample skill number. The run explorer's rule-22 footnote and
the status ladder both state that it is not one.

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

# Rule 22's own words, carried onto the page so a folded held-out year cannot
# be read as a skill claim. Kept here (not in the JS) so every touchpoint says
# it identically.
TIER_CAVEAT = (
    "Validation tier: ITERABLE model-SELECTION evidence. This is NOT a "
    "certified out-of-sample skill number and must never be quoted as one — "
    "the year may be re-spent after the open availability-envelope defect "
    "lands. The touch-once locked test (2019 / H1-2026) is NOT spent here."
)

ENVELOPE_CAVEAT = (
    "Availability-envelope PARITY IS CONFIRMED, so this caveat is narrower "
    "than it first appears. 2022 is built from the SAME uniform CAMPD "
    "detector regeneration as 2023-2025 (one 2018-2026 pass, not a separate "
    "holdout-year derive), with the SAME merit-order guard applied — "
    "layup-reclassified windows are disjoint from the standard extract in "
    "every year — and this run consumed the BYTE-IDENTICAL layup artifact the "
    "keeper did. The 2022 envelope is quantitatively in family with the tuned "
    "years on window count, capacity-weighted MW-days and median duration. "
    "The residual over-count that keeps the holdout freeze active is "
    "therefore baked into the TUNED years too: it is a reason to hold the "
    "in-sample AND holdout numbers at arm's length in ABSOLUTE terms, but NOT "
    "a reason to discount the in-sample-to-holdout DELTA this table reports, "
    "which is measured on a like-for-like envelope. Re-running after the "
    "envelope fix would be expected to move the level of both sides, not "
    "obviously their difference."
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
    ap.add_argument(
        "--reset-caveats",
        action="store_true",
        help="Overwrite an authored tierCaveat/envelopeCaveat with this "
        "script's defaults (they are preserved across a re-stamp otherwise).",
    )
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
    prior = sidecar.get("holdout") or {}
    block = {
        "tier": prior.get("tier", "validation"),
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
    # AUTHORED KEYS SURVIVE A RE-STAMP. Everything above is DERIVED from the two
    # verdicts and is meant to be overwritten every time the scorer moves; the
    # keys below are written by a human (or a session) about THIS rung and are
    # not reproducible from a re-score, so clobbering them would silently delete
    # curation. This is what makes rule 30 [R-TOUCHPOINT-FOLD] (a) safe to
    # re-run after a rubric amendment — the sole way to keep the folded panel
    # honest is to re-stamp, and re-stamping must not cost the notes that
    # explain the rung. An authored `tierCaveat`/`envelopeCaveat` (one that
    # differs from this script's default) is likewise preserved; pass
    # --reset-caveats to take the defaults back.
    for key in ("perYear", "supersedes", "supersedesNote", "basisNote"):
        if key in prior:
            block[key] = prior[key]
    if not args.reset_caveats:
        for key, default in (
            ("tierCaveat", TIER_CAVEAT),
            ("envelopeCaveat", ENVELOPE_CAVEAT),
        ):
            if prior.get(key) and prior[key] != default:
                block[key] = prior[key]
    sidecar["holdout"] = block
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
