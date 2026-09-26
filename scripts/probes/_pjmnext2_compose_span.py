#!/usr/bin/env python3
"""Compose PJM-NEXT-2's seven per-year JOINT-arm legs into one 2019-2025 bundle.

Rule 36 ``[R-YEAR-ISOLATION]``: each year was solved in its own shard; composing
is the parent's zero-LP job (rule 32 (d)). The mechanics are
``_hydro5_compose_span.py``'s (``compose`` / ``regenerate_diagnostics``), reused
unchanged. The recipe check is this lane's: every leg must equal the PJM-NEXT
keeper's own year (``pjmnext_c1_span/run_config_<y>.json``) plus EXACTLY the
three PJM-NEXT-2 flags (docs/PRECOMMIT-pjm-next-2-joint-2026-09-25.md), with the
COAL-SUB bare-``COAL`` offer-curve fold still tolerated.
Anything else differing aborts, so a control leg or a wrong-recipe leg can
never compose in.

Usage::

    python scripts/probes/_pjmnext2_compose_span.py \\
        --leg 2019=pjmnext2_joint_2019 ... --leg 2025=pjmnext2_joint_2025 \\
        --out results/calibration/pjmnext2_joint_span
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
KEEPER = CAL / "pjmnext_c1_span"
ARM_FLAGS = (
    "unit_outage_membership_repair",
    "pjm_zonal_gas_basis_skip_923_priced",
    "nuclear_dormancy_defers_to_vintage_exit",
)
MUST_BE_TRUE = (
    "eia860_vintage_tracks_solve_year",
    "measured_ct_heat_rates",
    "measured_coal_heat_rates",
    "measured_st_heat_rates",
    "measured_cc_heat_rates",
    "measured_chp_heat_rates",
    "pjm_rggi_allowance_pricing",
    "mid_vintage_exit_carry",
    "fleet_zone_vintage_coords",
    "benchmark_membership_vintage_union",
) + ARM_FLAGS


def _drop_bare_coal(d: "dict | None") -> dict:
    """The keeper's offer block minus the legacy bare ``COAL`` key (COAL-SUB fold)."""
    return {k: v for k, v in (d or {}).items() if k != "COAL"}


def check_recipes(legs: dict[str, list[int]]) -> None:
    """Abort unless every leg is the keeper's year recipe plus exactly ARM_FLAGS."""
    surfaces: set = set()
    for name, years in legs.items():
        if len(years) != 1:
            raise SystemExit(f"ABORT: {name} claims {years}; legs are single-year")
        (year,) = years
        cfg = json.loads((CAL / name / "run_config.json").read_text())
        inc = json.loads((KEEPER / f"run_config_{year}.json").read_text())
        a, k = cfg["scenario_config"], inc["scenario_config"]
        diff = {
            x
            for x in set(a) | set(k)
            if json.dumps(a.get(x), sort_keys=True, default=str)
            != json.dumps(k.get(x), sort_keys=True, default=str)
        }
        diff -= set(ARM_FLAGS)
        # Fields added to ScenarioConfig after the keeper was solved are absent
        # from its record; a leg holding the dataclass DEFAULT for them is the
        # same recipe (rule 24: a new field is default-off and key-dropped).
        from market_sim.config.scenarios import ScenarioConfig

        _dflt = ScenarioConfig()
        diff = {
            x
            for x in diff
            if not (
                x not in k
                and json.dumps(a.get(x), sort_keys=True, default=str)
                == json.dumps(getattr(_dflt, x, object()), sort_keys=True, default=str)
            )
        }
        if "offer_curve_by_group" in diff and json.dumps(
            a.get("offer_curve_by_group"), sort_keys=True
        ) == json.dumps(_drop_bare_coal(k.get("offer_curve_by_group")), sort_keys=True):
            diff.discard("offer_curve_by_group")
        if diff:
            raise SystemExit(
                f"ABORT: {name} differs from keeper {year} in {sorted(diff)}"
            )
        off = [x for x in MUST_BE_TRUE if a.get(x) is not True]
        if off:
            raise SystemExit(f"ABORT: {name} has {off} not True")
        ocf = cfg["calibration_flags"].get("offer_curve_overrides")
        ocf_k = _drop_bare_coal(inc["calibration_flags"].get("offer_curve_overrides"))
        if json.dumps(ocf, sort_keys=True) != json.dumps(ocf_k, sort_keys=True):
            raise SystemExit(f"ABORT: {name} offer_curve_overrides differ from keeper")
        recorded = sorted(cfg.get("calibration_flags", {}).get("years") or [])
        if recorded != [year]:
            raise SystemExit(f"ABORT: {name} records years {recorded}, claims [{year}]")
        surfaces.add((cfg.get("solve_surface") or {}).get("fingerprint"))
        sha = (
            cfg.get("resolved_inputs", {})
            .get("campd_unit_outages", {})
            .get("sha256", "?")
        )
        print(
            f"  {name:20s} year={year} outages sha={sha[:12]} basis={cfg['git']['basis_sha'][:8]}"
        )
    if len(surfaces) != 1:
        raise SystemExit(
            f"ABORT: legs disagree on solve-surface fingerprint: {surfaces}"
        )
    print(
        "  OK — every leg is keeper + the three PJM-NEXT-2 flags; offers unchanged; one surface."
    )


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
