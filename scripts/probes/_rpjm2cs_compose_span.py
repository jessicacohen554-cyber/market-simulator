#!/usr/bin/env python3
"""Compose R-PJM2-CS's seven per-year legs into one 2019-2025 bundle.

Lane R-PJM2-CS (``docs/handoffs/r-pjm2-coalsub/PRECOMMIT.md``) replays the
designated PJM keeper ``rpjm2_span`` unchanged at a HEAD carrying COAL-SUB.
Rule 36 ``[R-YEAR-ISOLATION]`` solved each year in its own shard; composition
is the parent's zero-LP job (rule 32 ``[R-SHARD]`` (d)), reusing
``_hydro5_compose_span.compose`` / ``regenerate_diagnostics`` unchanged.

The recipe check: every leg's ``scenario_config`` must equal the keeper's own
``run_config_<year>.json`` field for field (NO expected delta — the treatment is
code, not config), and its ``offer_curve_overrides`` must equal the keeper's
after the legacy bare ``"COAL"`` key is folded the way ``replay_keeper`` folds
it (``fold_legacy_coal_key(covered=COAL_CLASSES)``). Anything else aborts.

Usage::

    python scripts/probes/_rpjm2cs_compose_span.py \\
        --leg 2019=rpjm2cs_2019 ... --leg 2025=rpjm2cs_2025 \\
        --out results/calibration/rpjm2cs_span
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts" / "probes")):
    if p not in sys.path:
        sys.path.insert(0, p)

from _hydro5_compose_span import compose, regenerate_diagnostics  # noqa: E402

CAL = REPO / "results" / "calibration"
KEEPER = CAL / "rpjm2_span"
#: Fields whose value legitimately differs between a fresh solve and the
#: keeper's echo (provenance, not recipe).
PROVENANCE_ONLY: set[str] = set()


def check_recipes(legs: dict[str, list[int]]) -> None:
    """Abort unless every leg is the keeper's own per-year recipe."""
    from market_sim.config.plant_taxonomy import COAL_CLASSES, fold_legacy_coal_key

    surfaces: set = set()
    for name, years in legs.items():
        if len(years) != 1:
            raise SystemExit(f"ABORT: {name} claims {years}; legs are single-year")
        (year,) = years
        cfg = json.loads((CAL / name / "run_config.json").read_text())
        inc = json.loads((KEEPER / f"run_config_{year}.json").read_text())
        a, k = cfg["scenario_config"], inc["scenario_config"]
        diff = {
            x: (k.get(x), a.get(x))
            for x in set(a) | set(k)
            if x not in PROVENANCE_ONLY
            and json.dumps(a.get(x), sort_keys=True, default=str)
            != json.dumps(k.get(x), sort_keys=True, default=str)
        }
        if diff:
            raise SystemExit(f"ABORT: {name} scenario_config differs: {diff}")
        ocf = cfg["calibration_flags"].get("offer_curve_overrides")
        ocf_inc = fold_legacy_coal_key(
            dict(inc["calibration_flags"].get("offer_curve_overrides") or {}),
            covered=COAL_CLASSES,
        )
        if json.dumps(ocf, sort_keys=True) != json.dumps(ocf_inc, sort_keys=True):
            raise SystemExit(f"ABORT: {name} offer_curve_overrides differ from keeper")
        recorded = sorted(cfg.get("calibration_flags", {}).get("years") or [])
        if recorded != [year]:
            raise SystemExit(f"ABORT: {name} records years {recorded}, claims [{year}]")
        surfaces.add((cfg.get("solve_surface") or {}).get("fingerprint"))
        ri = cfg.get("resolved_inputs", {}).get("campd_unit_outages", {})
        print(f"  {name:16s} year={year} outages sha={ri.get('sha256', '?')[:12]}")
    if len(surfaces) != 1:
        raise SystemExit(f"ABORT: legs disagree on solve-surface fingerprint: {surfaces}")
    print("  OK — every leg is the keeper recipe; offers unchanged (COAL folded); one surface.")


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--leg", action="append", required=True, help="YEAR=bundle_name")
    ap.add_argument("--out", required=True)
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    legs: dict[str, list[int]] = {}
    for spec in args.leg:
        ys, _, name = spec.partition("=")
        legs[name] = sorted(int(y) for y in ys.split(","))
    check_recipes(legs)
    if args.check_only:
        return 0
    out = Path(args.out)
    out = out if out.is_absolute() else REPO / out
    compose(legs, out)
    years = sorted({y for ys in legs.values() for y in ys})
    return regenerate_diagnostics(out, "PJM", years)


if __name__ == "__main__":
    raise SystemExit(main())
