#!/usr/bin/env python3
"""nyiso-173 addendum — does the armed CC outage overlay DELIVER, and is the
model's CC over-production even availability-limited?

ZERO SOLVE. Reported **in addition to** the pre-registered P1-P4 gates of
``PREREG-nyiso173-cc-availability-anatomy.md``, never in place of them (the
nyiso-171 A5b / nyiso-172 S7-S10 discipline). These measurements were taken
BECAUSE P1a failed: the armed >= 5-day overlay already carries ~56 % of the
measured CC shortfall in the violation hours, so the 5-day floor named by
nyiso-172 section 3.4 is not the carrier and the question becomes where the
model's excess CC comes from instead.

Three measurements:

* **S1 ROUTING DELIVERY.** Every CC row of ``campd-unit-outages-NYISO.csv`` is
  routed through the engine's own :func:`~market_sim.data.outages
  ._generic_unit_outage_target` against the engine's own per-bin capacity map,
  and the rows that land on no fleet bin (silently skipped by the accumulator —
  the Ravenswood-2500 failure mode ``_FLEET_GROUP_OVERRIDE`` exists to fix) are
  counted and named.

* **S2 THE REALIZED CC ENVELOPE.** The overlay's own availability multipliers
  (:func:`~market_sim.data.outages.unit_outage_derate_factors`, the engine's
  function, not a reimplementation) against the nameplate-raised bin capacities
  the LP actually carries, giving the CC availability envelope by hour.

* **S3 UTILISATION.** Is the model's CC output anywhere near that envelope in
  the violation hours? This is the decisive one. If the model runs its CC well
  BELOW a correctly-derated envelope, then no availability input can move it —
  the excess is a dispatch choice inside an envelope that is not binding, and
  the object is not an availability object at all.

The envelope here is a deliberate UPPER bound on the LP's true CC ceiling: it
omits the statistical WEFOR the backcast still applies on top of the measured
overlay (``wefor_residual`` is null on this keeper) and the Jun-Sep summer
derate. Utilisation against an upper-bound envelope is therefore a LOWER bound
on true utilisation, which is the conservative direction for S3's reading.

Rule 13 [R-MEASURED]: CAMPD enters as conduct identification only; nothing is
pinned and no statistic is tuned to a residual. Rule 22 [R-HOLDOUT]: 2023-2025
only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    UNIT_OUTAGE_MIN_DAYS,
    _generic_unit_outage_target,
    _iso_plant_capacity,
    unit_outage_derate_factors,
)

sys.path.insert(0, str(REPO / "scripts" / "probes"))
from nyiso173_cc_availability_anatomy import (  # noqa: E402
    CC_CLASSES,
    YEARS,
    campd_cc_units,
    chp_plants,
    model_cc,
    month_of_hour,
    unit_matrix,
)

UNIT_OUTAGE_CSV = RAW_DATA_DIR / "campd-unit-outages-NYISO.csv"
OUT = REPO / "results/calibration/_nyiso173b_overlay_delivery.json"


def s1_routing() -> dict:
    """S1 — which CC extract rows land on a model fleet bin, and which are dropped."""
    cap = _iso_plant_capacity("NYISO", False, False)
    df = pd.read_csv(UNIT_OUTAGE_CSV)
    df = df[df["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]
    df = df[df["plant_group"].isin(CC_CLASSES)]
    landed, dropped = 0, 0
    dropped_plants: dict[str, int] = {}
    for r in df.itertuples(index=False):
        tgt = _generic_unit_outage_target(
            int(r.facility_id), r.unit_id, r.plant_group
        )
        if tgt is not None and tgt in cap:
            landed += 1
        else:
            dropped += 1
            key = f"{int(r.facility_id)}:{r.plant_group}"
            dropped_plants[key] = dropped_plants.get(key, 0) + 1
    return {
        "cc_rows_ge_min_days": int(len(df)),
        "rows_landing_on_a_fleet_bin": landed,
        "rows_dropped": dropped,
        "dropped_share": round(dropped / len(df), 4) if len(df) else 0.0,
        "dropped_by_plant_group": dict(
            sorted(dropped_plants.items(), key=lambda kv: -kv[1])
        ),
        "cc_bins_in_fleet": {
            f"{k[0]}:{k[1]}": round(v, 1) for k, v in cap.items() if k[1] in CC_CLASSES
        },
    }


def cc_envelope(year: int) -> tuple[np.ndarray, float]:
    """``(envelope_mw[8760], total_cc_capacity_mw)`` from the engine's own loader.

    ``cc_nameplate_basis=True`` reproduces ``fleet_to_bins``' nameplate raise
    exactly (the caiso-184 identity), so this is the CC capacity the LP carries
    under the keeper's ``cc_nameplate_summer_derate=True``. Deliberately omits
    the statistical WEFOR and the Jun-Sep summer derate, so it is an UPPER bound
    on the LP's true CC ceiling.
    """
    cap = _iso_plant_capacity("NYISO", False, True)
    fac = unit_outage_derate_factors(
        year, iso="NYISO", cc_steam_part_reclass=False, cc_nameplate_basis=True
    )
    env = np.zeros(8760)
    total = 0.0
    for key, mw in cap.items():
        if key[1] not in CC_CLASSES:
            continue
        total += mw
        env += mw * fac.get(key, np.ones(8760))
    return env, total


def main() -> None:
    chpset = chp_plants()
    mon = month_of_hour()
    result: dict = {
        "prereg": "results/calibration/PREREG-nyiso173-cc-availability-anatomy.md",
        "note": (
            "S1-S3 are NOT pre-registered gates. They were measured because P1a "
            "failed, and are reported IN ADDITION to P1-P4."
        ),
        "keeper": "2026-08-30-nyiso-159-loss-surface",
        "solves": 0,
        "S1_routing": s1_routing(),
        "by_year": {},
    }
    print(
        f"S1 routing: {result['S1_routing']['rows_landing_on_a_fleet_bin']} of "
        f"{result['S1_routing']['cc_rows_ge_min_days']} CC rows land on a fleet "
        f"bin; {result['S1_routing']['rows_dropped']} dropped "
        f"({result['S1_routing']['dropped_share']:.2%})"
    )

    for year in YEARS:
        d = campd_cc_units(year, chpset)
        gen, _ = unit_matrix(d)
        me = gen.sum(axis=0)
        mo = model_cc(year)
        env, total = cc_envelope(year)

        bound = np.zeros(8760)
        for m in range(1, 13):
            sel = mon == m
            bound[sel] = float(me[sel].max())
        viol = mo > bound

        util = np.divide(mo, env, out=np.zeros_like(mo), where=env > 0)

        # ROBUSTNESS. The envelope above omits the statistical CC WEFOR the
        # backcast still applies on top of the measured overlay
        # (``wefor_residual`` is null on this keeper — the caiso-186 rule 19
        # [R-ONE-MECH] double count, named there at 3.5 % for CC). Re-state the
        # violation-hour headroom net of it, so S3's reading does not rest on
        # the omission.
        wefor = 0.035
        env_w = env * (1.0 - wefor)

        # VALIDITY. Does the MEASURED fleet ever exceed this envelope? A
        # measured hour above it would mean the overlay asserts an incapability
        # the CEMS record refutes (the caiso-185 failure mode). Reported both
        # with and without East River (2493), which is in the measured CC series
        # but is ST_CHP in the model artifact (nyiso-171 section 5).
        er = d["_fid"].to_numpy() == 2493
        me_er = np.zeros(8760)
        np.add.at(
            me_er,
            d["_h"].to_numpy(dtype=int)[er],
            d["grossLoad"].to_numpy(float)[er],
        )
        y = {
            "wefor_assumed": wefor,
            "headroom_mean_in_violation_hours_net_of_wefor_mw": round(
                float((env_w - mo)[viol].mean()) if viol.any() else float("nan"), 1
            ),
            "hours_model_at_or_above_envelope_net_of_wefor": int(
                (mo >= env_w - 1e-6).sum()
            ),
            "measured_hours_above_envelope": int((me > env).sum()),
            "measured_hours_above_envelope_ex_east_river": int(
                ((me - me_er) > env).sum()
            ),
            "cc_capacity_mw_nameplate_basis": round(total, 1),
            "envelope_mean_mw": round(float(env.mean()), 1),
            "envelope_mean_availability": round(float(env.mean() / total), 4),
            "overlay_derated_hours_share": round(float((env < total).mean()), 4),
            "model_utilisation_mean": round(float(util.mean()), 4),
            "model_utilisation_in_violation_hours": round(
                float(util[viol].mean()) if viol.any() else float("nan"), 4
            ),
            "model_utilisation_p95": round(float(np.percentile(util, 95)), 4),
            "model_utilisation_max": round(float(util.max()), 4),
            "hours_model_at_or_above_envelope": int((mo >= env - 1e-6).sum()),
            "envelope_mean_in_violation_hours_mw": round(
                float(env[viol].mean()) if viol.any() else float("nan"), 1
            ),
            "model_mean_in_violation_hours_mw": round(
                float(mo[viol].mean()) if viol.any() else float("nan"), 1
            ),
            "measured_mean_in_violation_hours_mw": round(
                float(me[viol].mean()) if viol.any() else float("nan"), 1
            ),
            "headroom_mean_in_violation_hours_mw": round(
                float((env - mo)[viol].mean()) if viol.any() else float("nan"), 1
            ),
        }
        result["by_year"][str(year)] = y
        print(
            f"\n=== {year}  CC capacity {y['cc_capacity_mw_nameplate_basis']:.0f} MW"
            f"  overlay-derated in {y['overlay_derated_hours_share']:.1%} of hours"
            f"  mean availability {y['envelope_mean_availability']:.3f}"
        )
        print(
            f"  model utilisation of its own CC envelope: mean "
            f"{y['model_utilisation_mean']:.3f}  p95 {y['model_utilisation_p95']:.3f}"
            f"  max {y['model_utilisation_max']:.3f}"
            f"  hours AT the envelope {y['hours_model_at_or_above_envelope']}"
        )
        print(
            f"  in violation hours: envelope "
            f"{y['envelope_mean_in_violation_hours_mw']:.0f}  model "
            f"{y['model_mean_in_violation_hours_mw']:.0f}  measured "
            f"{y['measured_mean_in_violation_hours_mw']:.0f}"
            f"  -> UNUSED headroom {y['headroom_mean_in_violation_hours_mw']:.0f} MW"
            f" (utilisation {y['model_utilisation_in_violation_hours']:.3f})"
        )
        print(
            f"  robustness: headroom net of a {wefor:.1%} CC WEFOR "
            f"{y['headroom_mean_in_violation_hours_net_of_wefor_mw']:.0f} MW, "
            f"hours at that envelope "
            f"{y['hours_model_at_or_above_envelope_net_of_wefor']}"
            f"; MEASURED hours above the envelope {y['measured_hours_above_envelope']}"
            f" (ex-East-River {y['measured_hours_above_envelope_ex_east_river']})"
        )

    OUT.write_text(json.dumps(result, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
