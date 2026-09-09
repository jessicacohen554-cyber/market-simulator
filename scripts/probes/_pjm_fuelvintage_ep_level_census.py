"""Phase-0 part 2: the OFFER-level footprint (mc_base), both sides, PJM 2023."""

from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path("/home/user/market-simulator")
sys.path.insert(0, str(ROOT))
from scripts import replay_keeper as rk
from scripts import run_calibration as rc

BUNDLE = ROOT / "results/calibration/pjm_debugb_inputclock_A"
YEAR = int(sys.argv[1])


def build(year, arm):
    """Return ``run_year``'s ``fleet_only`` payload for one year and one side.

    The armed side routes ``gas_electric_power_monthly_level`` through the
    generic ``prb_overrides`` channel — byte-identical to what
    ``replay_keeper.py --set gas_electric_power_monthly_level=true`` does, since
    the field is a ``ScenarioConfig`` field and not a ``solve_and_persist``
    parameter, so ``--set`` routes it through ``prb_overrides`` and nothing else.

    Args:
        year: Solve year to build for.
        arm: True for the armed side, False for the keeper's own recipe.

    Returns:
        The ``fleet_only`` payload dict.
    """
    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    sig = set(rc.run_year.__code__.co_varnames[: rc.run_year.__code__.co_argcount])
    call = {k: v for k, v in kwargs.items() if k in sig}
    call.update(
        year=year,
        iso=meta["iso"],
        hours=8760,
        fleet_only=True,
        gas_price=meta["gas_prices"][str(year)],
        ttc_overrides={},
    )
    if arm:
        call["prb_overrides"] = dict(call.get("prb_overrides") or {})
        call["prb_overrides"]["gas_electric_power_monthly_level"] = True
    return rc.run_year(**call)


c = build(YEAR, False)
a = build(YEAR, True)
fa = c["fleet_arrays"]
np.save(f"/tmp/mc_ctrl_{YEAR}.npy", c["mc_base"])
np.save(f"/tmp/mc_arm_{YEAR}.npy", a["mc_base"])
np.save(f"/tmp/fuel_ctrl_{YEAR}.npy", c["fuel_prices"])
np.save(f"/tmp/fuel_arm_{YEAR}.npy", a["fuel_prices"])
meta = {
    "pmax": np.asarray(fa.pmax, float).tolist(),
    "fuel_type_idx": np.asarray(fa.fuel_type_idx).tolist(),
    "unit_id": [str(u) for u in getattr(fa, "unit_ids", [])] or None,
    "plant_group": [str(g) for g in getattr(fa, "plant_group", [])] or None,
}
Path(f"/tmp/fleetmeta_{YEAR}.json").write_text(json.dumps(meta))
print("SAVED", YEAR)
