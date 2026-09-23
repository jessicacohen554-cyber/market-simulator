"""soco-60 (ZERO LP): compose the merged-hydro per-year legs into one span bundle.

Owner ruling 2026-09-23 (option 3): SOCO's two owner-promoted hydro repairs are
merged into ONE recipe before any CC_REGULAR work --

* SOCO hydro-4's ``hydro_ror_split=True`` (the keeper on ``main``,
  ``2026-09-22-soco-h4-hydro-ror``), which already carries
  ``hydro_backfill_year=2024``; and
* SOCO-59's ``hydro_eia930_monthly=True`` with
  ``EIA930_PS_SPLIT_COMPLETE_FROM["SOCO"] = 2025`` (the registry row is on
  ``main``; the run never reached it).

Rule 19 ``[R-ONE-MECH]``: the two are ONE pipeline, not stacked -- the EIA-930
repin sets each plant's monthly budget, and the run-of-river flat level is read
off that same budget (``hydro.build_hydro_fleet``). Rule 36 puts each year in its
own shard; this module asserts every leg carries BOTH halves and every inherited
posture, then composes through :mod:`scripts.probes.soco55_compose_span`.

Usage::

    python3 scripts/probes/soco60b_compose_span.py --expect-arm true \\
        --legs results/calibration/soco60_arm_{2023,2024,2025} \\
        --out  results/calibration/soco60_hydro_merged
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

#: The merged recipe's two solve_and_persist kwargs, as meta.json records them.
ARM_META = {"hydro_backfill_year": 2024, "hydro_eia930_monthly": True}
#: The control (keeper soco-h4-hydro-ror) legs. Its 2023/2024 legs were solved
#: with NO backfill (the repair is array-equal there; its composite meta carries
#: 2024 span-wide), so the control's backfill is checked for 2025 only.
CONTROL_META = {"hydro_backfill_year": 2024, "hydro_eia930_monthly": False}

#: The control legs were solved at 4b6c6d96 (183 rows); a leg solved at a HEAD
#: carrying SOCO's EIA930_PS_SPLIT_COMPLETE_FROM row records 184. Arm B
#: (PRECOMMIT addendum B) also carries ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE:
#: 185 rows, that row MOVED off its declaration.
SURFACE_ROWS = {True: 184, False: 183, "b": 185}
ARM_B_MOVED = {"ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE"}

INHERITED_MEASURED_BASIS = True  # SOCO-55, positional in soco55 compose

#: Every resolved posture, pinned to keeper 2026-09-22-soco-h4-hydro-ror.
INHERITED_FIELDS: dict[str, bool] = {
    "hydro_ror_split": True,  # SOCO hydro-4
    "hydro_min_flow_floor": False,  # SOCO hydro-4 ARM 1, never stacked (rule 19)
    "coal_warm_committed": True,  # SOCO-58
    "campd_per_unit_attribution": True,  # SOCO-56
    "measured_cc_heat_rates": True,  # SOCO-57
    "measured_coal_heat_rates": True,  # SOCO-53f
    "gas_plant_monthly_fuel_pricing": False,  # SOCO-54
}

#: The classifier snapshot the control consumed (45 plants, 17 RoR-class).
HYDRO_MODES_SNAPSHOT = "../_shared/SOCO/hydro_plant_modes-ea00e49bf5be.parquet"


def assert_delta(legs: list[Path], expect_arm: "bool | str") -> None:
    """Fail loud if any leg solved the wrong side of this lane's A/B."""
    want_meta = ARM_META if expect_arm else CONTROL_META
    print(
        f"expecting {want_meta} and solve_surface rows {SURFACE_ROWS[expect_arm]} on every leg"
    )
    for leg in legs:
        meta = json.loads((leg / "meta.json").read_text())
        cfg = json.loads((leg / "run_config.json").read_text())
        (year,) = meta["years"]
        for k, v in want_meta.items():
            if expect_arm is False and k == "hydro_backfill_year" and year < 2025:
                continue
            if meta.get(k) != v:
                raise SystemExit(
                    f"{leg.name}: meta {k}={meta.get(k)!r}, expected {v!r}"
                )
        rows = (cfg.get("solve_surface") or {}).get("rows")
        if rows != SURFACE_ROWS[expect_arm]:
            raise SystemExit(
                f"{leg.name}: solve_surface rows {rows!r}, expected {SURFACE_ROWS[expect_arm]}"
            )
        moved = set((cfg.get("solve_surface") or {}).get("moved") or {})
        if expect_arm == "b" and moved != ARM_B_MOVED:
            raise SystemExit(
                f"{leg.name}: solve_surface moved {sorted(moved)}, expected {sorted(ARM_B_MOVED)}"
            )
        sc = cfg.get("scenario_config") or {}
        for f, want in INHERITED_FIELDS.items():
            if bool(sc.get(f)) != want:
                raise SystemExit(f"{leg.name}: {f} is {sc.get(f)!r}, expected {want}")
        if sc.get("coal_prb_sigmoid_overrides") not in (None, {}):
            raise SystemExit(
                f"{leg.name}: resolved coal_prb_sigmoid_overrides is not null"
            )
        snap = (meta.get("shared_inputs") or {}).get("hydro_plant_modes")
        if snap != HYDRO_MODES_SNAPSHOT:
            raise SystemExit(
                f"{leg.name}: hydro_plant_modes {snap!r}, expected {HYDRO_MODES_SNAPSHOT}"
            )
        print(
            f"  {leg.name}: {want_meta}  surface rows {rows}  inherited + classifier OK"
        )


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect-arm", required=True, choices=("true", "false", "b"))
    ap.add_argument("--check-only", action="store_true", help="assert, do not compose")
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    assert_delta(legs, {"true": True, "false": False, "b": "b"}[a.expect_arm])
    if not a.check_only:
        _compose(legs, out, INHERITED_MEASURED_BASIS)


if __name__ == "__main__":
    main()
