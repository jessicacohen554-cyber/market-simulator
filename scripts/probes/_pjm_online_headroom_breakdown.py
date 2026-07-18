"""Locate the model's online-reserve headroom by class in PJM peak hours.

Phase-1 (commitment-posture) targeting for the reserve-pricing campaign: the
honesty gate shows ~14 GW of plant-level online headroom vs PJM's ~3 GW. This
breaks that headroom down by class and by how loaded online plants are, in the
summer afternoon peak, so the commitment build targets the real cause.

Usage: python scripts/probes/_pjm_online_headroom_breakdown.py [year]
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
import json

from derive_pjm_ordc_overlay import _run_year_kwargs  # noqa: E402

BUNDLE = Path("results/calibration/pjm_27_aswh")


def main(year: int) -> None:
    from run_calibration import run_year  # heavy import

    meta = json.loads((BUNDLE / "meta.json").read_text())
    state = run_year(
        year,
        meta["iso"],
        meta["hours"],
        meta["gas_prices"][str(year)],
        **_run_year_kwargs(meta),
    )
    fa = state["fleet_arrays"]
    avail = fa.pmax[:, None] * fa.availability  # (n_unit, T)
    uids = np.asarray(fa.unit_ids, dtype=object)
    klass = np.asarray(fa.plant_group, dtype=object)
    pc = np.asarray(fa.plant_code)

    d = pd.read_parquet(BUNDLE / "dispatch" / f"{year}_P1.parquet")
    dmat = (
        d.pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="sum")
        .reindex(uids)
        .fillna(0.0)
        .to_numpy()
    )

    # Summer-afternoon peak hours: Jul/Aug (hours 4344-5831), HE 16-19 -> h 15-18.
    hod = np.arange(meta["hours"]) % 24
    summer = (np.arange(meta["hours"]) >= 4344) & (np.arange(meta["hours"]) < 5832)
    peak = summer & np.isin(hod, [15, 16, 17, 18, 19])
    print(
        f"=== {year}: PJM summer afternoon peak (Jul/Aug HE16-20, {peak.sum()} h) ==="
    )

    # Online = plant has any tranche dispatching that hour (group by plant_code).
    codes, inv = np.unique(pc, return_inverse=True)
    n_codes = len(codes)
    plant_disp = np.zeros((n_codes, meta["hours"]))
    plant_avail = np.zeros((n_codes, meta["hours"]))
    np.add.at(plant_disp, inv, dmat)
    np.add.at(plant_avail, inv, avail)
    online = plant_disp > 0.5

    # Per-class online headroom (only online plants), averaged over peak hours.
    rows = []
    for cls in sorted(set(klass)):
        umask = klass == cls
        cmask = np.isin(codes, np.unique(pc[umask]))
        on = online[cmask][:, peak]
        a = plant_avail[cmask][:, peak]
        dp = plant_disp[cmask][:, peak]
        hr = np.where(on, a - dp, 0.0)
        n_online = on.sum(axis=0).mean()
        head_gw = hr.sum(axis=0).mean() / 1e3
        disp_gw = np.where(on, dp, 0.0).sum(axis=0).mean() / 1e3
        load_pct = 100 * disp_gw / (disp_gw + head_gw) if (disp_gw + head_gw) else 0
        if head_gw > 0.05 or disp_gw > 0.05:
            rows.append((cls, n_online, disp_gw, head_gw, load_pct))
    rows.sort(key=lambda r: -r[3])
    print(
        f"{'class':12s} {'#online':>8s} {'disp GW':>8s} {'head GW':>8s} {'load%':>6s}"
    )
    th = td = 0.0
    for cls, n, dp, hd, lp in rows:
        print(f"{cls:12s} {n:8.0f} {dp:8.2f} {hd:8.2f} {lp:6.0f}")
        th += hd
        td += dp
    print(f"{'TOTAL':12s} {'':>8s} {td:8.2f} {th:8.2f} {100 * td / (td + th):6.0f}")
    print(f"\nonline headroom {th:.1f} GW vs PJM Primary req ~3 GW")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2024)
