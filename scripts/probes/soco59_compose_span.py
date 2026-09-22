"""soco-59 (ZERO LP): compose the per-year legs into one span bundle.

Rule 36 ``[R-YEAR-ISOLATION]`` (a) puts each backcast year in its own shard;
rule 34 ``[R-SHARD-PROMOTABLE]`` (a) makes each shard push its FULL bundle, so
the legs compose without a re-solve. The composition itself is
:mod:`scripts.probes.soco55_compose_span` (validated across four lanes); this
module adds the assertion of **this** lane's delta and every inherited posture.

**THE DELTA IS NOT A ScenarioConfig FIELD**, so it cannot be read off the
resolved ``scenario_config`` the way SOCO-58's was. It is three things, and every
leg must carry all three:

* ``meta.json["hydro_backfill_year"] == 2024`` and
  ``meta.json["hydro_eia930_monthly"] is True`` — the two ``solve_and_persist``
  kwargs ``replay_keeper --set`` routes;
* the leg's recorded solve surface carries SOCO's
  ``EIA930_PS_SPLIT_COMPLETE_FROM`` row — ``run_config.json["solve_surface"]``
  ``rows == 184`` against the control's 183. **THIS IS THE ONLY THING THAT
  DISTINGUISHES AN ARMED 2023 / 2024 LEG FROM A CONTROL LEG.** In those years the
  registration REFUSES the EIA-930 pin, the backfill adds no plant, and
  ``_soco59_rule19.py`` measures exactly zero on every fleet grain with the unit
  list unchanged — the SOCO-58 §3 case again: all-grains-zero is the required
  signature, not an inert arm. Without the registration, an armed 2023 leg
  would instead pin hydro to a PS-folded series (8.446 vs 6.815 TWh).

The postures inherited from SOCO-54 … SOCO-58 are pinned (rule 19
``[R-ONE-MECH]``: a two-delta bundle has no attributable A/B).

Usage::

    python3 scripts/probes/soco59_compose_span.py --expect-arm true \\
        --legs results/calibration/soco59_arm_{2023,2024,2025} \\
        --out  results/calibration/soco59_hydro_split
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.probes.soco55_compose_span import ROOT, compose as _compose  # noqa: E402

#: This lane's delta, as the two solve_and_persist kwargs meta.json records.
ARM_META = {"hydro_backfill_year": 2024, "hydro_eia930_monthly": True}
CONTROL_META = {"hydro_backfill_year": None, "hydro_eia930_monthly": False}

#: Solve-surface row counts: the SOCO-58 keeper's legs record 183; a leg solved
#: at a HEAD carrying EIA930_PS_SPLIT_COMPLETE_FROM["SOCO"] records 184.
SURFACE_ROWS = {True: 184, False: 183}

INHERITED_MEASURED_BASIS = True  # SOCO-55, positional in soco55 compose

#: Every other posture inherited, pinned to the SOCO-58 keeper's values.
INHERITED_FIELDS: dict[str, bool] = {
    "coal_warm_committed": True,  # SOCO-58
    "campd_per_unit_attribution": True,  # SOCO-56
    "measured_cc_heat_rates": True,  # SOCO-57
    "measured_coal_heat_rates": True,  # SOCO-53f
    "gas_plant_monthly_fuel_pricing": False,  # SOCO-54
}


def assert_delta(legs: list[Path], expect_arm: bool) -> None:
    """Fail loud if any leg solved the wrong side of this lane's A/B."""
    want_meta = ARM_META if expect_arm else CONTROL_META
    print(f"expecting {want_meta} and solve_surface rows {SURFACE_ROWS[expect_arm]} on every leg")
    for leg in legs:
        meta = json.loads((leg / "meta.json").read_text())
        cfg = json.loads((leg / "run_config.json").read_text())
        for k, v in want_meta.items():
            if meta.get(k) != v:
                raise SystemExit(f"{leg.name}: meta {k}={meta.get(k)!r}, expected {v!r}")
        rows = (cfg.get("solve_surface") or {}).get("rows")
        if rows != SURFACE_ROWS[expect_arm]:
            raise SystemExit(
                f"{leg.name}: solve_surface rows {rows!r}, expected "
                f"{SURFACE_ROWS[expect_arm]} — solved at the wrong HEAD (the "
                "SOCO EIA930_PS_SPLIT_COMPLETE_FROM row is the only thing that "
                "separates an armed 2023/2024 leg from a control)"
            )
        sc = cfg.get("scenario_config") or {}
        for f, want in INHERITED_FIELDS.items():
            if bool(sc.get(f)) != want:
                raise SystemExit(f"{leg.name}: {f} is {sc.get(f)!r}, expected {want}")
        if sc.get("coal_prb_sigmoid_overrides") is not None:
            raise SystemExit(f"{leg.name}: resolved coal_prb_sigmoid_overrides is not null")
        print(f"  {leg.name}: {want_meta}  surface rows {rows}  inherited OK")


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect-arm", required=True, choices=("true", "false"))
    ap.add_argument("--check-only", action="store_true", help="assert, do not compose")
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    assert_delta(legs, a.expect_arm == "true")
    if not a.check_only:
        _compose(legs, out, INHERITED_MEASURED_BASIS)


if __name__ == "__main__":
    main()
