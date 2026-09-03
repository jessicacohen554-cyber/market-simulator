"""nyiso-180 — POST-HOC REPORT on the per-group ramp envelopes. NOT A GATE.

Written and run AFTER the pre-registered gates of
``PREREG-nyiso180-st-gas-undispatch.md`` had been committed and scored. It
moves no bar and changes no verdict; G2 stands where its own bar left it
(``INCONCLUSIVE - PENDING SIDECAR``). Its only job is to quantify the
one-sidedness G2 declared in advance: WHY a class aggregate cannot see a
per-group ramp row bind.

The ``ramp_limits`` rows are one two-sided row per (plant, CC/CT/ST bucket)
group per hour transition. The committed artifact is a class aggregate over 11
such groups, so per-group clipping averages out inside it — the identical
structure that made nyiso-113's K3/K4 gates invalid against ``system``'s summed
``reserve_price``. What CAN be measured with zero solves is how TIGHT each
group's envelope is relative to its own capacity, i.e. how many hours a cold
group needs to reach its own bound. A group needing several hours to traverse
its range can sit in the money and below its bound for the whole of a short
price spike, entirely optimally, with the ramp row's dual (not the zonal price)
carrying its reduced cost.

Run: PYTHONPATH=.:src python scripts/probes/nyiso180_ramp_report.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes.nyiso178_offer_side_idling import ISO, lp_fleet  # noqa: E402
from scripts.probes.nyiso180_st_gas_undispatch import _cfg_obj  # noqa: E402

OUT = REPO / "results/calibration/_nyiso180_ramp_report.json"
KLASS = "ST_GAS"


def _withholding_persistence() -> dict:
    """Is the withholding TRANSIENT or SUSTAINED? The ramp hypothesis' own test.

    A ramp envelope binds on TRANSITIONS. Every ST_GAS group can traverse its
    full range in 1.5-3.0 h (above), so a ramp row can hold a group below its
    bound for a few hours after a step up in value — and then cannot. If the
    withheld capacity is instead SUSTAINED over long unbroken runs, the ramp
    rows cannot be its dominant cause, whatever the per-group duals do.

    Measures the run-length distribution of ``model < 0.9 x ITM`` per year.
    """
    from scripts.probes.nyiso179_st_gas_offer_position import build_year
    from scripts.probes.nyiso178_offer_side_idling import YEARS, model_hourly

    out = {}
    for year in YEARS:
        st = build_year(year, _cfg_obj())
        itm = (
            (st["mc"] <= st["p_model"]) * st["pmax"][:, None] * st["avail"]
        ).sum(axis=0)
        mw = model_hourly(year, KLASS)
        w = mw < 0.9 * itm
        runs, cur = [], 0
        for flag in w:
            if flag:
                cur += 1
            elif cur:
                runs.append(cur)
                cur = 0
        if cur:
            runs.append(cur)
        r = np.array(runs) if runs else np.array([0])
        out[str(year)] = {
            "hours_withholding_gt10pct": int(w.sum()),
            "share_of_year": float(w.mean()),
            "n_runs": int(r.size),
            "median_run_length_h": float(np.median(r)),
            "p90_run_length_h": float(np.percentile(r, 90)),
            "max_run_length_h": float(r.max()),
            "share_of_withheld_hours_in_runs_gt_6h": float(
                r[r > 6].sum() / r.sum()
            ),
        }
    return out


def main() -> None:
    from market_sim.data.fleet.campd_bins import build_ramp_groups

    _g, fa = lp_fleet(2024, _cfg_obj())
    gen_idx, group_col, ru, rd = build_ramp_groups(fa, ISO)
    pg = np.asarray(fa.plant_group, dtype=object)
    pmax = np.asarray(fa.pmax, dtype=float)
    gen_idx = np.asarray(gen_idx, dtype=int)
    group_col = np.asarray(group_col, dtype=int)

    rows = []
    for gid in np.unique(group_col):
        m = group_col == gid
        members = gen_idx[m]
        groups_here = {str(pg[i]) for i in members}
        if KLASS not in groups_here:
            continue
        cap = float(pmax[members].sum())
        up = float(np.asarray(ru)[gid])
        rows.append(
            {
                "group_id": int(gid),
                "classes_in_group": sorted(groups_here),
                "group_pmax_mw": cap,
                "ramp_up_mw_per_h": up,
                "ramp_up_frac_of_cap": up / cap if cap else None,
                "hours_cold_to_full": cap / up if up else None,
            }
        )
    fr = np.array([r["ramp_up_frac_of_cap"] for r in rows], dtype=float)
    hrs = np.array([r["hours_cold_to_full"] for r in rows], dtype=float)
    res = {
        "note": "POST-HOC REPORT. Not a gate. Moves no bar, changes no verdict.",
        "n_groups_with_ST_GAS": len(rows),
        "ramp_up_frac_of_cap": {
            "min": float(fr.min()),
            "median": float(np.median(fr)),
            "max": float(fr.max()),
        },
        "hours_cold_to_full": {
            "min": float(hrs.min()),
            "median": float(np.median(hrs)),
            "max": float(hrs.max()),
        },
        "groups": sorted(rows, key=lambda r: r["ramp_up_frac_of_cap"]),
    }
    res["persistence"] = _withholding_persistence()
    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k != "groups"}, indent=2))
    print("\nper-group (tightest first):")
    for r in res["groups"]:
        print(
            "  grp %3d  %-28s cap %7.1f MW  RU %7.1f MW/h  "
            "frac %.3f  cold->full %.2f h"
            % (
                r["group_id"],
                "+".join(r["classes_in_group"]),
                r["group_pmax_mw"],
                r["ramp_up_mw_per_h"],
                r["ramp_up_frac_of_cap"],
                r["hours_cold_to_full"],
            )
        )


if __name__ == "__main__":
    main()
