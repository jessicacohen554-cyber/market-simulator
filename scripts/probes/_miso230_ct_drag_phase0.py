"""miso-230 phase 0 — what the CT net-load drag REPLACES and what it ADDS. Zero LP.

Rule 29 clause 0: an arm with a computable pre-solve gate does not reach a solve
until that gate passes. This probe answers the two questions the miso-229 finding
named as the honest risks of arming ``ct_netload_drag`` on MISO, both without
spending an LP minute:

  1. **Rule 19 ``[R-ONE-MECH]`` — does it stack or replace?** MISO's
     ``reliability_floor`` already carries net-load-driven CT_PEAKER limbs in all
     six zones (``data/raw/reference/reliability_floor_coeffs_MISO.csv``,
     ``enabled=True``, driver "MISO system p70 daily-peak net-load", window
     h15-21), and the keeper's own D-2 attributes **100 %** of CT_PEAKER's forced
     energy to that mechanism. ``iso_configs.drop_drag_owned_reliability_specs``
     removes exactly those limbs when the drag is armed, so the swap is
     machine-enforced — this probe MEASURES that it happened rather than
     asserting it, by rebuilding the fleet both ways and reading the
     per-mechanism ``min_gen``.
  2. **Rule 18 ``[R-FORCED-BUDGET]`` — how big is the replacement?** The drag's
     floor MW are compared against the dropped limbs' floor MW and against the
     keeper's own committed CT_PEAKER dispatch, giving the pre-solve energy
     prediction the screen's G-1 gate checks the realized LP response against.

Both fleets are built through ``run_calibration.run_year(fleet_only=True)`` on
the keeper's own recipe (read from its ``meta.json`` via
``replay_keeper.build_kwargs``), so the comparison is the keeper's exact
configuration with a single delta. No LP is solved, nothing is fitted, nothing
is promoted. Rule 22: 2023 only (the screen year).

Writes ``results/calibration/_miso230_ct_drag_phase0.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts import replay_keeper as rk  # noqa: E402
from scripts import run_calibration as rc  # noqa: E402
from scripts import run_calibration_full as rcf  # noqa: E402
from market_sim.data.floor_mechanisms import (  # noqa: E402
    MECH_CT_NETLOAD_DRAG,
    MECH_RELIABILITY_FLOOR,
)

KEEPER = REPO / "results/calibration/miso220_nonsteamlift_B"
OUT = REPO / "results/calibration/_miso230_ct_drag_phase0.json"
YEAR = 2023
HOURS = 8760

# The MISO-derived curve. Sourced ONLY from the frozen derive's committed
# artifact so this probe cannot carry a number the derive did not produce
# (rule 23 [R-FROZEN-DERIVE]; rule 25 [R-ISO-SCOPE] — the artifact is ISO-stamped
# and is checked below).
DRAG_JSON = REPO / "data/raw/reference/miso_ct_netload_drag.json"


def load_drag_coeffs() -> dict:
    """Read the frozen MISO drag coefficients, asserting the rule-25 ISO stamp."""
    rec = json.loads(DRAG_JSON.read_text())
    if rec.get("iso") != "MISO":
        raise SystemExit(f"{DRAG_JSON} is stamped {rec.get('iso')!r}, not MISO")
    return rec["coefficients"]


def build_fleet(extra: dict | None) -> dict:
    """Build the keeper's fleet for *YEAR*, optionally with a single config delta.

    Args:
        extra: ScenarioConfig overrides layered onto the keeper recipe through
            the generic ``prb_overrides`` channel, or ``None`` for the keeper as
            committed.

    Returns:
        The ``run_year(fleet_only=True)`` state dict.
    """
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = HOURS
    if extra:
        prb = dict(kwargs.get("prb_overrides") or {})
        prb.update(extra)
        kwargs["prb_overrides"] = prb
        if "ct_netload_drag" in extra:
            kwargs["ct_netload_drag"] = extra["ct_netload_drag"]
    sig = set(rc.run_year.__code__.co_varnames[: rc.run_year.__code__.co_argcount])
    call = {k: v for k, v in kwargs.items() if k in sig}
    call["year"] = YEAR
    call["iso"] = meta["iso"]
    call["hours"] = HOURS
    call["fleet_only"] = True
    # Positional-required args the solve driver supplies itself
    # (run_calibration_full.solve_and_persist: gas_price from the per-year
    # meta record, ttc_overrides always empty on the calibration path).
    call["gas_price"] = float(meta["gas_prices"][str(YEAR)])
    call["ttc_overrides"] = {}
    call.pop("years", None)
    return rc.run_year(**call)


def floor_stats(state: dict, mech_id: int) -> dict:
    """Floor MW/energy carried by one mechanism on CT_PEAKER rows."""
    fa = state["fleet_arrays"]
    gens = state["fleet"]
    mg = np.asarray(fa.min_gen, dtype=float)
    mech = np.asarray(fa.min_gen_mechanism, dtype=int)
    is_ct = np.array([g.plant_group == "CT_PEAKER" for g in gens], dtype=bool)
    sel = is_ct[:, None] & (mech == mech_id)
    mw = np.where(sel, mg, 0.0)
    hod = np.arange(mw.shape[1]) % 24
    by_hod = [round(float(mw[:, hod == h].sum(axis=0).mean()), 1) for h in range(24)]
    return {
        "floor_twh": round(float(mw.sum()) / 1e6, 4),
        "peak_floor_mw": round(float(mw.sum(axis=0).max()), 1),
        "mean_floor_mw": round(float(mw.sum(axis=0).mean()), 1),
        "binding_hours": int((mw.sum(axis=0) > 0).sum()),
        "mean_floor_mw_by_hod": by_hod,
    }


def main() -> int:
    """Run the zero-LP replace-vs-stack and floor-size measurement."""
    coeffs = load_drag_coeffs()
    print(f"MISO derived drag coefficients (frozen artifact): {coeffs}")

    print("\n--- building KEEPER fleet (no drag) ---")
    base = build_fleet(None)
    print("--- building ARM fleet (drag armed, MISO-derived curve) ---")
    arm = build_fleet({"ct_netload_drag": True, **coeffs})

    keeper_relfloor = floor_stats(base, MECH_RELIABILITY_FLOOR)
    arm_relfloor = floor_stats(arm, MECH_RELIABILITY_FLOOR)
    arm_drag = floor_stats(arm, MECH_CT_NETLOAD_DRAG)
    keeper_drag = floor_stats(base, MECH_CT_NETLOAD_DRAG)

    # Total CT_PEAKER floor either way — the number rule 18 actually cares
    # about, since the LP is floored by the max-composition of every mechanism.
    def total_ct_floor(state: dict) -> float:
        fa, gens = state["fleet_arrays"], state["fleet"]
        is_ct = np.array([g.plant_group == "CT_PEAKER" for g in gens], dtype=bool)
        return float(np.asarray(fa.min_gen, dtype=float)[is_ct].sum()) / 1e6

    tot_base, tot_arm = total_ct_floor(base), total_ct_floor(arm)

    # PRE-SOLVE ENERGY PREDICTION (the G-1 gate's operand). The floor is a
    # MINIMUM the LP already exceeds in many hours, so the lift is not the
    # floor's integral: it is the hourly shortfall of the keeper's own
    # committed CT_PEAKER dispatch against the arm's floor. Computed on the
    # CLASS aggregate from the keeper's committed class_hourly sidecar, which
    # is a LOWER BOUND on the per-unit lift (per-unit shortfalls cannot cancel
    # against per-unit surpluses at the class level).
    import pandas as pd

    ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{YEAR}.parquet")
    ct = ch[(ch["klass"] == "CT_PEAKER") & (ch["pass"] == "P1")]
    disp_h = ct.groupby("hour")["mw"].sum().reindex(range(HOURS), fill_value=0.0)
    disp_h = disp_h.to_numpy(dtype=float)

    fa_arm = arm["fleet_arrays"]
    is_ct = np.array([g.plant_group == "CT_PEAKER" for g in arm["fleet"]], dtype=bool)
    floor_h = np.asarray(fa_arm.min_gen, dtype=float)[is_ct].sum(axis=0)
    lift_h = np.maximum(0.0, floor_h - disp_h)
    prediction = {
        "keeper_ct_dispatch_twh": round(float(disp_h.sum()) / 1e6, 4),
        "arm_ct_floor_twh": round(float(floor_h.sum()) / 1e6, 4),
        "predicted_lift_twh_class_lower_bound": round(float(lift_h.sum()) / 1e6, 4),
        "hours_floor_binds_above_keeper_dispatch": int((lift_h > 0).sum()),
        "actual_ct_twh_2023_eia923": 17.038,
        "keeper_c1_gap_twh": round(17.038 - float(disp_h.sum()) / 1e6, 4),
    }
    print("\n=== PRE-SOLVE ENERGY PREDICTION (G-1 operand) ===")
    for k, v in prediction.items():
        print(f"  {k}: {v}")

    rec = {
        "presolve_prediction": prediction,
        "probe": (
            "miso-230 phase 0 — ct_netload_drag replace-vs-stack (rule 19) and "
            "floor size (rule 18), zero LP, keeper recipe + one delta"
        ),
        "keeper": "2026-09-05-miso-220-nonsteam-lift (miso220_nonsteamlift_B)",
        "year": YEAR,
        "drag_coefficients": coeffs,
        "keeper_reliability_floor_on_CT_PEAKER": keeper_relfloor,
        "arm_reliability_floor_on_CT_PEAKER": arm_relfloor,
        "keeper_ct_netload_drag": keeper_drag,
        "arm_ct_netload_drag": arm_drag,
        "total_CT_PEAKER_min_gen_twh": {
            "keeper": round(tot_base, 4),
            "arm": round(tot_arm, 4),
            "delta": round(tot_arm - tot_base, 4),
        },
        "rule19_replacement_verified": (
            arm_relfloor["floor_twh"] == 0.0 and keeper_relfloor["floor_twh"] > 0.0
        ),
    }
    print("\n=== RULE 19 [R-ONE-MECH]: replace, not stack ===")
    print(
        f"  keeper reliability_floor x CT_PEAKER : {keeper_relfloor['floor_twh']:.4f} TWh "
        f"floor, {keeper_relfloor['binding_hours']} h"
    )
    print(
        f"  ARM    reliability_floor x CT_PEAKER : {arm_relfloor['floor_twh']:.4f} TWh "
        f"(must be 0.0000 — drop_drag_owned_reliability_specs)"
    )
    print(f"  ARM    ct_netload_drag              : {arm_drag['floor_twh']:.4f} TWh "
          f"floor, {arm_drag['binding_hours']} h")
    print(f"  replacement verified: {rec['rule19_replacement_verified']}")
    print("\n=== RULE 18 [R-FORCED-BUDGET]: floor size ===")
    print(f"  total CT_PEAKER min_gen  keeper {tot_base:.4f} -> arm {tot_arm:.4f} TWh "
          f"(delta {tot_arm - tot_base:+.4f})")
    print("\n  mean floor MW by hour-of-day (arm drag):")
    print("   " + "  ".join(f"{h:02d}:{v:.0f}" for h, v in
                            enumerate(arm_drag["mean_floor_mw_by_hod"])))

    OUT.write_text(json.dumps(rec, indent=1))
    print(f"\n-> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
