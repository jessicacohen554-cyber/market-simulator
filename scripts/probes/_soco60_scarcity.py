"""SOCO-60 phase 0 step 3 (ZERO LP): ex-ante sizing of 2025 unserved energy.

The arm removes ~0.40 TWh of 2025 water and reshapes it (January halved, June
x2.5). This bounds what that does to unserved energy WITHOUT a solve, from the
control leg's committed per-unit hourly sidecar (``unit_hourly_2025``: ``mw``
and the hourly availability ceiling ``cap_mw``).

Construction (a relaxation of the LP, validated by reproducing the control):

* Everything in the SOCO energy balance that is not a unit in
  ``unit_hourly`` (storage net, renewables not carried as units, interchange)
  is held at the control's own hourly value: ``other_t = demand + dump - slack
  - sum(unit mw)``.
* Non-hydro units may rise to their hourly ceiling ``cap_mw`` (their floors
  only matter for over-generation, never for unserved energy).
* Run-of-river hydro is fixed at the side's flat monthly level; reservoir
  hydro has the side's monthly reservoir energy and its nameplate as an hourly
  cap. Within each month the minimum-unserved allocation is water-filling:
  ``need_t = demand_t - other_t - thermal_cap_t - ror_t``;
  ``UE_m = sum_t max(0, need_t - P_res) + max(0, sum_t min(need_t^+, P_res) - E_res_m)``.
* SOCO's three zones are pooled (intra-SOCO transmission ignored — optimistic),
  storage is frozen at the control's dispatch (conservative). The net bias is
  measured by applying the SAME construction to the control's own water and
  comparing with the control's actual 287 MWh.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

LEG = _ROOT / "results/calibration/soco_h4_ror_2025"


def month_of_hour() -> np.ndarray:
    """0-based month index for each of the 8760 hours (non-leap)."""
    from market_sim.data.hydro import hours_per_month

    return np.repeat(np.arange(12), hours_per_month().astype(int))


def unserved(need: np.ndarray, p_res: float, e_res: np.ndarray, mon: np.ndarray) -> tuple[float, pd.Series]:
    """Minimum unserved MWh per month under water-filling; returns (total, per-hour UE)."""
    ue = np.zeros_like(need)
    for m in range(12):
        idx = np.where(mon == m)[0]
        n = need[idx]
        over = np.clip(n - p_res, 0, None)  # beyond reservoir nameplate: unavoidable
        coverable = np.clip(n, 0, p_res)
        short = coverable.sum() - e_res[m]
        ue_m = over.copy()
        if short > 0:
            # Water goes to the deepest needs first; the unmet remainder falls on
            # the shallowest positive-need hours (the allocation minimises the sum,
            # the per-hour placement is one optimum among many).
            order = np.argsort(coverable)
            left = short
            for j in order:
                if left <= 0:
                    break
                take = min(coverable[j], left)
                ue_m[j] += take
                left -= take
        ue[idx] = ue_m
    return float(ue.sum()), pd.Series(ue)


def main(ctl_npz: Path, arm_npz: Path) -> None:
    """Size 2025 unserved energy for the control's and the arm's water."""
    from market_sim.data.hydro import hours_per_month

    hpm = hours_per_month().astype(float)
    mon = month_of_hour()
    u = pd.read_parquet(LEG / "hourly/unit_hourly_2025.parquet")
    s = pd.read_parquet(LEG / "hourly/system_2025.parquet").groupby("hour")[["demand", "slack", "dump"]].sum()
    hyd = u["plant_group"].eq("hydro")
    mw_all = u.groupby("hour")["mw"].sum()
    other = s["demand"] + s["dump"] - s["slack"] - mw_all
    therm_cap = u[~hyd].groupby("hour")["cap_mw"].sum()
    demand = s["demand"].to_numpy()
    base_need = demand - other.to_numpy() - therm_cap.to_numpy()
    print(f"control actual unserved: {s['slack'].sum():.1f} MWh in {(s['slack'] > 0.5).sum()} zone-hours")
    out = {}
    for side, npz in (("ctl", ctl_npz), ("arm", arm_npz)):
        z = np.load(npz)
        b, f, pmax = z["2025_budget"], z["2025_flat"], z["2025_pmax"]
        ror = ~np.isnan(f[:, 0])
        ror_mw = f[ror].sum(0)  # MW by month (already nameplate-clipped)
        e_res = b[~ror].sum(0)
        p_res = float(pmax[~ror].sum())
        need = base_need - ror_mw[mon]
        tot, per = unserved(need, p_res, e_res, mon)
        out[side] = per
        hrs = per[per > 0.5]
        print(
            f"{side}: RoR flat MW Jan/Jul {ror_mw[0]:.0f}/{ror_mw[6]:.0f}; reservoir "
            f"{p_res:.0f} MW, energy Jan/Jul {e_res[0] / 1e3:.0f}/{e_res[6] / 1e3:.0f} GWh; "
            f"min unserved {tot:.1f} MWh in {len(hrs)} h; months "
            f"{sorted({int(mon[i]) + 1 for i in hrs.index})}; hours {list(hrs.index)[:12]}"
        )
        # Thinnest positive-need margin: how close each month comes to a shortfall.
        for m in range(12):
            idx = mon == m
            cov = np.clip(need[idx], 0, p_res).sum()
            print(f"    m{m + 1:02d} reservoir water needed at peak {cov / 1e3:8.1f} GWh of {e_res[m] / 1e3:7.1f}"
                  f"  max need {need[idx].max():8.0f} MW vs P_res {p_res:.0f}") if side == "arm" else None
    d = out["arm"] - out["ctl"]
    print(f"arm - ctl unserved: {d.sum():+.1f} MWh")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
