"""SOCO hydro-4 (ZERO LP): compose one arm's per-year legs into one span bundle.

Rule 36 ``[R-YEAR-ISOLATION]`` (a) solves each year in its own shard; rule 34
``[R-SHARD-PROMOTABLE]`` (a) makes each shard push its full bundle, so the legs
compose without a re-solve. The composition itself is
:func:`scripts.probes.soco55_compose_span.compose` (reused, not forked), which
also asserts the SOCO keeper posture on every leg. This module adds:

* the arm's single delta (``hydro_min_flow_floor`` or ``hydro_ror_split``),
  asserted on the RESOLVED ``scenario_config`` of every leg, with the other
  member of the family asserted OFF (rule 19 ``[R-ONE-MECH]``: never stacked);
* the inherited SOCO-58 posture (``coal_warm_committed`` and the measured
  heat-rate / attribution fields), so no leg composes against an older control;
* the 2025 SOCO-53b repair, ``hydro_backfill_year=2024``. It is a
  ``solve_and_persist`` kwarg, not a ``ScenarioConfig`` field, so it lives in
  ``meta.json`` only and ``soco55_compose_span`` (which copies the first leg's
  meta) would drop it. It is carried SPAN-WIDE here, which is faithful because
  it is a measured no-op on 2023 and 2024: ``build_hydro_fleet('SOCO', y,
  backfill_year=2024)`` returns a budget array-equal to the unrepaired one for
  y in {2023, 2024} (42 plants each; only plants absent from ``y``'s EIA-923
  census are carried in, and there are none). Re-asserted here at compose time.

Usage::

    python3 scripts/probes/soco_h4_compose_span.py --arm mff \\
        --legs results/calibration/soco_h4_mff_{2023,2024,2025} \\
        --out  results/calibration/soco_h4_mff_span
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.probes.soco55_compose_span import ROOT, compose as _compose  # noqa: E402

#: arm tag -> (the arm's delta field, the family member that must stay OFF).
ARMS: dict[str, tuple[str, str]] = {
    "mff": ("hydro_min_flow_floor", "hydro_ror_split"),
    "ror": ("hydro_ror_split", "hydro_min_flow_floor"),
}

#: Posture of the designated keeper 2026-09-22-soco58-warm-committed.
INHERITED_FIELDS: dict[str, bool] = {
    "coal_warm_committed": True,  # SOCO-58
    "campd_per_unit_attribution": True,  # SOCO-56
    "measured_cc_heat_rates": True,  # SOCO-57
    "measured_coal_heat_rates": True,  # SOCO-53f
    "gas_plant_monthly_fuel_pricing": False,  # SOCO-54
}

#: The SOCO-53b repair year carried by the 2025 leg (PRECOMMIT addendum A).
REPAIR_BACKFILL_YEAR = 2024
SOCO_ZONES = ["SOCO_AL", "SOCO_GA", "SOCO_MS"]


def assert_legs(legs: list[Path], arm: str) -> None:
    """Fail loud on a leg that solved the wrong arm, control or 2025 budget."""
    field, other = ARMS[arm]
    for leg in legs:
        sc = json.loads((leg / "run_config.json").read_text())["scenario_config"]
        meta = json.loads((leg / "meta.json").read_text())
        if sc.get(field) is not True or sc.get(other) is not False:
            raise SystemExit(
                f"{leg.name}: {field}={sc.get(field)!r} {other}={sc.get(other)!r} "
                f"-- expected {field}=True, {other}=False (rule 19, never stacked)"
            )
        for f, want in INHERITED_FIELDS.items():
            if bool(sc.get(f)) != want:
                raise SystemExit(f"{leg.name}: {f}={sc.get(f)!r}, expected {want}")
        (year,) = meta["years"]
        bf = meta.get("hydro_backfill_year")
        if year == 2025 and bf != REPAIR_BACKFILL_YEAR:
            raise SystemExit(f"{leg.name}: 2025 leg hydro_backfill_year={bf!r}")
        print(f"  {leg.name}: {field}=True {other}=False posture OK, backfill={bf}")


def assert_backfill_noop(years: list[int]) -> None:
    """Re-prove the span-wide repair changes no budget outside 2025."""
    from market_sim.data.hydro import build_hydro_fleet

    for y in years:
        if y >= 2025:
            continue
        _, a = build_hydro_fleet("SOCO", y, SOCO_ZONES)
        _, b = build_hydro_fleet("SOCO", y, SOCO_ZONES, backfill_year=REPAIR_BACKFILL_YEAR)
        if a is None or b is None or not np.array_equal(a, b):
            raise SystemExit(f"{y}: hydro_backfill_year={REPAIR_BACKFILL_YEAR} is NOT a no-op")
        print(f"  {y}: hydro_backfill_year={REPAIR_BACKFILL_YEAR} budget array-equal (no-op)")


def main() -> None:
    """Assert, compose, then carry the 2025 repair into the composite meta."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True, choices=sorted(ARMS))
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    legs = [Path(p) if Path(p).is_absolute() else ROOT / p for p in a.legs]
    out = Path(a.out) if Path(a.out).is_absolute() else ROOT / a.out
    assert_legs(legs, a.arm)
    years = sorted(json.loads((leg / "meta.json").read_text())["years"][0] for leg in legs)
    assert_backfill_noop(years)
    _compose(legs, out, True)
    meta_p = out / "meta.json"
    meta = json.loads(meta_p.read_text())
    meta["hydro_backfill_year"] = REPAIR_BACKFILL_YEAR
    meta_p.write_text(json.dumps(meta, indent=2, sort_keys=True))
    print(f"meta.json: hydro_backfill_year -> {REPAIR_BACKFILL_YEAR} (span-wide, no-op pre-2025)")


if __name__ == "__main__":
    main()
