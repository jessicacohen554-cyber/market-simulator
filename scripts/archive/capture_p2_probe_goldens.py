#!/usr/bin/env python3
"""Capture P2-enabled probe baselines for the Stage-4 regression gate.

The default backcast path for most keepers is P1-only (P2 is opt-in per
CLAUDE.md), so the keeper goldens exercise the P2 commitment core only via the
CAISO RA must-offer branch. Stage 4 of the orchestrator-unification plan
(``docs/handoffs/orchestrator-unification-plan-2026-07.md`` §6) moves the WHOLE
P2 body — the economic commitment screen, the coal pin, and the ERCOT
AS-adequacy floor — into ``pipeline/commitment.py``, so its gate must also
byte-compare a P2-ENABLED probe before and after the extraction.

This script re-solves the ERCOT keeper's frozen flag set (via
``capture_keeper_goldens.build_solve_kwargs``) with a small explicit override
per probe leg, one throwaway diagnostic year (2024 — CLAUDE.md rule 15: a
single-year solve is permitted only as a diagnostic probe and is NEVER
registered on the dashboard; these bundles live under the gitignored
regression-goldens dir):

- ``p2econ``: ``commitment=True`` — the economic commitment screen +
  coal-pin + P2 re-solve (``compute_commitment`` →
  ``apply_commitment_with_coal_pin`` → P2 ``solve_dispatch``).
- ``p2asaware``: ``ercot_as_aware_commitment=True`` with
  ``ercot_ordc_total_reserve=False`` (and its dependent supply-cap gate off) —
  the AS-aware screen + AS-adequacy floor + commitment-state-aware headroom
  overrides. The lumped total-ORDC family (reserve_class -1) is turned OFF
  because Stage 4 unifies on the forecast orchestrator's documented semantics
  for all-class families (excluded from the per-product adequacy requirement);
  the pre-Stage-4 backcast body mis-indexed a -1 family onto the last product,
  so a probe WITH the total family would measure that intentional fix, not
  code-motion neutrality. See the Stage-4 gate log in the plan §7.3.

Usage (before/after a stage's refactor, same as capture_keeper_goldens):

    python scripts/archive/capture_p2_probe_goldens.py --stage-tag stage4-probe-before
    python scripts/archive/capture_p2_probe_goldens.py --stage-tag stage4-probe-after
    python scripts/regression_gate.py \
        --before results/regression-goldens/stage4-probe-before \
        --after  results/regression-goldens/stage4-probe-after --mode byte
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

# Determinism pin BEFORE any solve import (same rationale and values as
# capture_keeper_goldens.DETERMINISM_ENV).
from scripts.capture_keeper_goldens import (  # noqa: E402
    DETERMINISM_ENV,
    GOLDENS_ROOT,
    _git_dirty,
    _git_sha,
    _hash_bundle,
    build_solve_kwargs,
    resolve_keeper_bundles,
)

for _k, _v in DETERMINISM_ENV.items():
    os.environ[_k] = _v

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("capture_p2_probe_goldens")

#: Probe legs: name -> (commitment flag, solve_and_persist kwarg overrides).
#: Every override key is a real ``solve_and_persist`` parameter (the same
#: namespace ``build_solve_kwargs`` fills from the keeper's meta.json).
PROBE_LEGS: dict[str, dict] = {
    "p2econ": {
        "commitment": True,
        "overrides": {},
    },
    "p2asaware": {
        "commitment": False,
        "overrides": {
            "ercot_as_aware_commitment": True,
            # The AS-adequacy floor is per-PRODUCT; drop the all-class lumped
            # total-ORDC family (reserve_class -1) and its dependent
            # supply-cap gate so both pre- and post-Stage-4 bodies compute
            # the identical requirement (see module docstring).
            "ercot_ordc_total_reserve": False,
            "ercot_reserve_supply_cap": False,
        },
    },
}

#: Throwaway diagnostic probe year (rule 15: single-year = probe only, never
#: registered). 2024 is mid-span of the 2023-2025 calibration window.
PROBE_YEARS = [2024]


def capture_probe(leg: str, stage_tag: str, info: dict) -> dict:
    """Re-solve one P2 probe leg into the golden dir; return its manifest entry."""
    from scripts.run_calibration import _load_reference
    from scripts.run_calibration_full import solve_and_persist

    spec = PROBE_LEGS[leg]
    meta = json.loads((info["bundle"] / "meta.json").read_text())
    hours = int(meta["hours"])
    kwargs, defaulted = build_solve_kwargs(meta, solve_and_persist)
    kwargs.update(spec["overrides"])

    golden_dir = GOLDENS_ROOT / stage_tag / f"ERCOT-{leg}"
    golden_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "[%s] probe solve: ERCOT %s hours=%s commitment=%s overrides=%s",
        leg,
        PROBE_YEARS,
        hours,
        spec["commitment"],
        spec["overrides"],
    )
    reference = _load_reference()
    solve_and_persist(
        PROBE_YEARS,
        "ERCOT",
        hours,
        reference,
        commitment=spec["commitment"],
        screen_coal=bool(meta["commitment_screen_coal"]),
        run_dir=golden_dir,
        note=(
            f"regression-gate P2 probe {stage_tag}/{leg} (Stage-4 diagnostic; "
            "single-year rule-15 probe, NOT a keeper, never registered)"
        ),
        **kwargs,
    )
    return {
        "base_keeper_id": info["keeper_id"],
        "leg": leg,
        "years": PROBE_YEARS,
        "hours": hours,
        "commitment": spec["commitment"],
        "overrides": spec["overrides"],
        "defaulted_unrecorded_params": defaulted,
        "content_hashes": _hash_bundle(golden_dir),
    }


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage-tag", required=True)
    parser.add_argument(
        "--leg",
        nargs="+",
        default=sorted(PROBE_LEGS),
        choices=sorted(PROBE_LEGS),
        help="Probe leg(s) to capture (default: all).",
    )
    args = parser.parse_args()

    info = resolve_keeper_bundles()["ERCOT"]
    manifest_path = GOLDENS_ROOT / args.stage_tag / "manifest.json"
    entries = {}
    if manifest_path.is_file():
        entries = json.loads(manifest_path.read_text()).get("probes", {})
    rc = 0
    for leg in args.leg:  # sequential: one ERCOT LP at a time (rule 8)
        try:
            entries[leg] = capture_probe(leg, args.stage_tag, info)
        except Exception:
            logger.exception("[%s] probe capture failed", leg)
            rc = 1
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(
                {
                    "stage_tag": args.stage_tag,
                    "git_sha": _git_sha(),
                    "git_dirty": _git_dirty(),
                    "env": DETERMINISM_ENV,
                    "probes": entries,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
