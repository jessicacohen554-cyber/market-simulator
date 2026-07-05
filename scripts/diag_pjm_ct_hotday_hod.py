"""THROWAWAY DIAG (rule 15): ground the CT_PEAKER reliability-floor window.

Measured CAMPD pure-play PJM CT_PEAKER fleet CF by hour-of-day, split by
hot-day (EMAAC design-cooling gate tmax > 33.3C, the reliability-floor limb's
own threshold) vs the rest. Confirms the reliability-floor CT_PEAKER limb's
justified window is the afternoon-evening cooling peak and that overnight CF is
near-zero (so the current all-24h binding is off-window per rule 17).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.data.eia_loader import iso_zone_tmax  # noqa: E402
from scripts.derive_pjm_ct_netload_drag import (  # noqa: E402
    measured_ct_mw,
    model_ct_peaker_plants,
)

YEAR = 2024
EMAAC_TMAX_GATE = 33.3  # reliability_floor_coeffs_PJM.csv EMAAC CT_PEAKER tmax


def main() -> None:
    plants, nameplate = model_ct_peaker_plants(YEAR)
    ct_mw = measured_ct_mw(YEAR, set(plants))
    cf = ct_mw / nameplate  # fleet CF per hour (8760,)
    hours = cf.size
    hod = np.arange(hours) % 24

    temp = iso_zone_tmax("PJM", YEAR, hours, zone="PJM_EMAAC")
    tmax, _tmin = temp
    tmax = np.asarray(tmax, dtype=float)
    hot_day = tmax > EMAAC_TMAX_GATE  # broadcast hourly (constant within a day)
    n_hot_days = int(hot_day.reshape(-1, 24)[:, 0].sum())

    print(
        f"PJM CT_PEAKER {YEAR}: {len(plants)} pure-play plants, "
        f"nameplate {nameplate / 1000:.2f} GW; annual fleet CF {cf.mean():.4f}"
    )
    print(f"EMAAC hot days (tmax>{EMAAC_TMAX_GATE}C): {n_hot_days}")
    print("\nhour  CF_hotday  CF_otherday")
    for h in range(24):
        m = hod == h
        cf_hot = cf[m & hot_day].mean() if (m & hot_day).any() else float("nan")
        cf_oth = cf[m & ~hot_day].mean() if (m & ~hot_day).any() else float("nan")
        star = " <-- window [15,22)" if 15 <= h < 22 else ""
        print(f"{h:>4}  {cf_hot:8.4f}   {cf_oth:8.4f}{star}")

    # Off-window vs in-window share of measured hot-day CT energy.
    win = (hod >= 15) & (hod < 22)
    hot = hot_day
    e_in = ct_mw[hot & win].sum()
    e_off = ct_mw[hot & ~win].sum()
    print(
        f"\nhot-day measured CT energy: in-window [15,22) {e_in / 1e3:.1f} GWh, "
        f"off-window {e_off / 1e3:.1f} GWh "
        f"({100 * e_off / (e_in + e_off):.1f}% off-window)"
    )
    # Overnight (h0-6) hot-day CF vs afternoon peak
    on = (hod >= 0) & (hod < 6)
    print(
        f"hot-day overnight (h0-6) CF {cf[hot & on].mean():.4f} vs "
        f"afternoon-peak (h15-19) CF {cf[hot & (hod >= 15) & (hod < 20)].mean():.4f}"
    )


if __name__ == "__main__":
    main()
