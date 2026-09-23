"""soco-60 (ZERO LP): compose the per-year legs into one span bundle.

The SOCO-59 composition (:mod:`scripts.probes.soco59_compose_span`) with the
hydro-4 keeper's posture added. Rule 36 ``[R-YEAR-ISOLATION]`` (a) puts each
backcast year in its own shard; rule 34 ``[R-SHARD-PROMOTABLE]`` (a) makes each
shard push its FULL bundle, so the legs compose without a re-solve. The
composition itself is :func:`scripts.probes.soco55_compose_span.compose`.

**THE DELTA** over the keeper ``2026-09-22-soco-h4-hydro-ror`` is
``hydro_eia930_monthly=True`` (a ``solve_and_persist`` kwarg, so it lives in
``meta.json``, not the resolved ``scenario_config``), solved at a HEAD carrying
``EIA930_PS_SPLIT_COMPLETE_FROM["SOCO"] = 2025`` — ``solve_surface.rows == 184``
against the keeper legs' 183. In 2023/2024 the registration REFUSES the pin, so
the surface row count and the meta flag are the only things that distinguish an
armed leg from a control leg there (``_soco60_phase0.py``: byte-identical hydro
fleet, zero fleet keys moved).

**THE INHERITED POSTURE** now includes ``hydro_ror_split=True`` (the keeper's
own delta) with its family member ``hydro_min_flow_floor`` asserted OFF (rule 19
``[R-ONE-MECH]``: never stacked), plus every SOCO-53f … SOCO-58 posture.

Verify the assert in BOTH directions before composing::

    python3 scripts/probes/soco60_compose_span.py --expect-arm false --check-only \\
        --legs results/calibration/soco_h4_ror_{2023,2024,2025}
    python3 scripts/probes/soco60_compose_span.py --expect-arm true --check-only \\
        --legs results/calibration/soco_h4_ror_{2023,2024,2025}      # must REFUSE
    python3 scripts/probes/soco60_compose_span.py --expect-arm true \\
        --legs results/calibration/soco60_arm_{2023,2024,2025} \\
        --out  results/calibration/soco60_hydro_ror_span
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

#: This lane's delta as ``meta.json`` records it. The control's 2023/2024 legs
#: carry backfill None (a measured no-op there) and its 2025 leg carries 2024.
ARM_META = {"hydro_backfill_year": 2024, "hydro_eia930_monthly": True}
CONTROL_EIA930 = False

#: Solve-surface rows: keeper legs 183 (solved before the SOCO registry row).
SURFACE_ROWS = {True: 184, False: 183}

INHERITED_MEASURED_BASIS = True  # SOCO-55, positional in soco55 compose

#: Every posture of the keeper 2026-09-22-soco-h4-hydro-ror.
INHERITED_FIELDS: dict[str, bool] = {
    "hydro_ror_split": True,  # SOCO hydro-4 (the keeper's delta)
    "hydro_min_flow_floor": False,  # its family member, never stacked (rule 19)
    "coal_warm_committed": True,  # SOCO-58
    "campd_per_unit_attribution": True,  # SOCO-56
    "measured_cc_heat_rates": True,  # SOCO-57
    "measured_coal_heat_rates": True,  # SOCO-53f
    "gas_plant_monthly_fuel_pricing": False,  # SOCO-54
}

#: Content hash of the curated SOCO hydro-plant-modes partition the keeper read.
MODES_HASH = "ea00e49bf5be"


def assert_delta(legs: list[Path], expect_arm: bool) -> None:
    """Fail loud if any leg solved the wrong side of this lane's A/B."""
    print(f"expecting arm={expect_arm}: solve_surface rows {SURFACE_ROWS[expect_arm]} on every leg")
    for leg in legs:
        meta = json.loads((leg / "meta.json").read_text())
        cfg = json.loads((leg / "run_config.json").read_text())
        if expect_arm:
            for k, v in ARM_META.items():
                if meta.get(k) != v:
                    raise SystemExit(f"{leg.name}: meta {k}={meta.get(k)!r}, expected {v!r}")
        elif bool(meta.get("hydro_eia930_monthly")) != CONTROL_EIA930:
            raise SystemExit(f"{leg.name}: control leg carries hydro_eia930_monthly=True")
        rows = (cfg.get("solve_surface") or {}).get("rows")
        if rows != SURFACE_ROWS[expect_arm]:
            raise SystemExit(
                f"{leg.name}: solve_surface rows {rows!r}, expected {SURFACE_ROWS[expect_arm]}"
            )
        sc = cfg.get("scenario_config") or {}
        for f, want in INHERITED_FIELDS.items():
            if bool(sc.get(f)) != want:
                raise SystemExit(f"{leg.name}: {f} is {sc.get(f)!r}, expected {want}")
        if sc.get("coal_prb_sigmoid_overrides") is not None:
            raise SystemExit(f"{leg.name}: resolved coal_prb_sigmoid_overrides is not null")
        modes = str((meta.get("shared_inputs") or {}).get("hydro_plant_modes", ""))
        if MODES_HASH not in modes:
            raise SystemExit(f"{leg.name}: hydro_plant_modes partition is not {MODES_HASH}")
        print(f"  {leg.name}: meta {[meta.get(k) for k in ARM_META]} surface {rows} posture OK")


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out")
    ap.add_argument("--expect-arm", required=True, choices=("true", "false"))
    ap.add_argument("--check-only", action="store_true", help="assert, do not compose")
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    assert_delta(legs, a.expect_arm == "true")
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    _compose(legs, out, INHERITED_MEASURED_BASIS)


if __name__ == "__main__":
    main()
