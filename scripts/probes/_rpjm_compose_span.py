#!/usr/bin/env python3
"""Compose R-PJM's seven per-year corrected-inputs legs into one 2019-2025 bundle.

Rule 36 ``[R-YEAR-ISOLATION]`` solved each year in its own shard; composition is
the parent's zero-LP job (rule 32 ``[R-SHARD]`` (d)). The mechanical half is
``_hydro5_compose_span.py``'s (``compose`` / ``regenerate_diagnostics``), reused
unchanged. Only the recipe check differs: this lane's delta against the
incumbent is FOUR flags, not one (PRECOMMIT-r-pjm-corrected-inputs §2):
``eia860_vintage_tracks_solve_year`` and ``measured_{coal,st,cc}_heat_rates``
False -> True, with ``measured_{ct,chp}_heat_rates`` already True in the
incumbent. Anything else differing aborts, so a control leg or a wrong-recipe
leg can never compose in. The offer-curve block must be byte-equal to the
incumbent's (rule 1(c): input correction, no re-tune).

Usage::

    python scripts/probes/_rpjm_compose_span.py \\
        --leg 2019=rpjm_inputs_2019 ... --leg 2025=rpjm_inputs_2025 \\
        --out results/calibration/rpjm_inputs_span
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts" / "probes")):
    if p not in sys.path:
        sys.path.insert(0, p)

from _hydro5_compose_span import compose, regenerate_diagnostics  # noqa: E402

CAL = REPO / "results" / "calibration"
EXPECTED_DELTA = {
    "eia860_vintage_tracks_solve_year": (False, True),
    "measured_coal_heat_rates": (False, True),
    "measured_st_heat_rates": (False, True),
    "measured_cc_heat_rates": (False, True),
}
MUST_BE_TRUE = (
    "eia860_vintage_tracks_solve_year",
    "measured_ct_heat_rates",
    "measured_coal_heat_rates",
    "measured_st_heat_rates",
    "measured_cc_heat_rates",
    "measured_chp_heat_rates",
)


def _incumbent(year: int) -> Path:
    """Return the incumbent bundle whose recipe year ``year`` replays."""
    return CAL / ("pjm_h19_dbs_touchpoint" if year <= 2022 else "pjm_h19_dbs_span")


def check_recipes(legs: dict[str, list[int]]) -> None:
    """Abort unless every leg is the incumbent recipe plus exactly EXPECTED_DELTA."""
    from market_sim.config.scenarios import ScenarioConfig

    defaults = {
        f.name: f.default
        for f in dataclasses.fields(ScenarioConfig)
        if f.default is not dataclasses.MISSING
    }
    surfaces: set = set()
    for name, years in legs.items():
        if len(years) != 1:
            raise SystemExit(f"ABORT: {name} claims {years}; legs are single-year")
        (year,) = years
        cfg = json.loads((CAL / name / "run_config.json").read_text())
        inc = json.loads((_incumbent(year) / "run_config.json").read_text())
        a, k = cfg["scenario_config"], inc["scenario_config"]
        diff = {x: (k[x], a[x]) for x in set(a) & set(k) if a[x] != k[x]}
        new = {
            x: a[x]
            for x in set(a) - set(k)
            if x in defaults
            and json.dumps(a[x]) != json.dumps(defaults[x], default=str)
        }
        # Fields absent from the incumbent's echo are judged by value.
        new = {x: v for x, v in new.items() if x not in EXPECTED_DELTA}
        diff_core = {x: v for x, v in diff.items() if x not in EXPECTED_DELTA}
        if diff_core or new:
            raise SystemExit(f"ABORT: {name} diff={diff_core} non-default new={new}")
        off = [x for x in MUST_BE_TRUE if a.get(x) is not True]
        if off:
            raise SystemExit(f"ABORT: {name} has {off} not True")
        ocf, ocf_inc = (
            cfg["calibration_flags"].get("offer_curve_overrides"),
            inc["calibration_flags"].get("offer_curve_overrides"),
        )
        if json.dumps(ocf, sort_keys=True) != json.dumps(ocf_inc, sort_keys=True):
            raise SystemExit(
                f"ABORT: {name} offer_curve_overrides differ from incumbent"
            )
        recorded = sorted(cfg.get("calibration_flags", {}).get("years") or [])
        if recorded != [year]:
            raise SystemExit(f"ABORT: {name} records years {recorded}, claims [{year}]")
        surfaces.add((cfg.get("solve_surface") or {}).get("fingerprint"))
        ri = cfg.get("resolved_inputs", {}).get("campd_unit_outages", {})
        print(
            f"  {name:22s} year={year} delta={sorted(diff)} outages sha={ri.get('sha256', '?')[:12]}"
        )
    if len(surfaces) != 1:
        raise SystemExit(
            f"ABORT: legs disagree on solve-surface fingerprint: {surfaces}"
        )
    print(
        "  OK — every leg is incumbent + the four F1 flags; offers unchanged; one surface."
    )


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--leg", action="append", required=True, help="YEAR=bundle_name")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    legs: dict[str, list[int]] = {}
    for spec in args.leg:
        ys, _, name = spec.partition("=")
        legs[name] = sorted(int(y) for y in ys.split(","))
    out = Path(args.out)
    out = out if out.is_absolute() else REPO / out
    check_recipes(legs)
    compose(legs, out)
    years = sorted({y for ys in legs.values() for y in ys})
    return regenerate_diagnostics(out, "PJM", years)


if __name__ == "__main__":
    raise SystemExit(main())
