"""ERCOT-148 Phase 0 stage 2 (no LP): capture the keeper's coal availability at the seam.

Builds the fleet availability arrays for the ERCOT keeper bundle's exact
config — every overlay layer applied in order (statistical stack, CAMPD
unit-outage windows, plant-grain partial plateaus, the DAM COP class-hour /
plant-grain rescale, forced-derate ceilings) — WITHOUT solving the LP, by
wrapping ``run_calibration.generators_to_fleet_arrays`` at its call site and
aborting once the arrays exist (the ``pjm119_summer_availability_gap``
pattern). Optionally captures a second variant with an override set (e.g.
``ercot_thermal_dam_availability_coal=False``) to isolate one layer's
contribution.

Usage:
    python scripts/probes/ercot148_availability_capture.py \
        results/calibration/ercot145_gas_daily_arm --year 2023 \
        --out /path/avail_2023_A.npz [--set ercot_thermal_dam_availability_coal=false]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

os.environ["MARKET_SIM_WARMSTART_XYEAR"] = "0"

import numpy as np  # noqa: E402

import replay_keeper as rk  # noqa: E402
import run_calibration as rc  # noqa: E402
import run_calibration_full as rcf  # noqa: E402

# run_calibration_full binds run_year from the PACKAGE-qualified module
# (``from scripts.run_calibration import run_year``), which is a DIFFERENT
# module object than the top-level ``run_calibration`` import above — patching
# only the top-level one silently lets the LP solve (this session's first
# capture attempt did exactly that). Patch BOTH module objects.
import scripts.run_calibration as rc_pkg  # noqa: E402


class _Captured(Exception):
    """Sentinel raised to abort the run once the fleet arrays exist."""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--set",
        action="append",
        default=[],
        help="KEY=JSON override applied through the replay prb channel",
    )
    args = ap.parse_args()

    bundle = Path(args.bundle)
    out = Path(args.out)
    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [int(args.year)]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = out.parent / f"_capture_{args.year}"
    overrides = {}
    for kv in args.set:
        k, v = kv.split("=", 1)
        overrides[k] = json.loads(v)
    if overrides:
        kwargs.setdefault("prb_overrides", {}).update(overrides)

    real = rc_pkg.generators_to_fleet_arrays

    def _wrapped(generators, zone_names, **kw):
        print("CAPTURE: fleet arrays intercepted", flush=True)
        fa = real(generators, zone_names, **kw)
        np.savez_compressed(
            out,
            availability=fa.availability.astype(np.float32),
            pmax=fa.pmax.astype(np.float64),
            plant_code=np.array([int(g.plant_code) for g in generators]),
            group=np.array([str(g.plant_group) for g in generators]),
            bin_label=np.array([str(getattr(g, "bin_label", "")) for g in generators]),
            name=np.array([str(g.name) for g in generators]),
        )
        raise _Captured

    rc_pkg.generators_to_fleet_arrays = _wrapped
    rc.generators_to_fleet_arrays = _wrapped
    try:
        rcf.solve_and_persist(**kwargs)
    except _Captured:
        pass
    finally:
        rc_pkg.generators_to_fleet_arrays = real
        rc.generators_to_fleet_arrays = real
    if not Path(str(out)).exists():
        raise SystemExit(f"capture FAILED: {out} was not written (wrapper never fired)")
    print(f"captured {out}")


if __name__ == "__main__":
    main()
