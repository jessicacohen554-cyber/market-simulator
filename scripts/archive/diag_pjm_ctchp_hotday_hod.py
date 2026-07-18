"""THROWAWAY DIAG (rule 15): ground the PJM CT_CHP reliability-floor window.

Measured CAMPD PJM CT_CHP fleet CF by hour-of-day, split by hot-day
(EMAAC design-cooling gate tmax > 33.3C, the enabled EMAAC CT_CHP tmax limb's
own threshold) vs the rest. The CT_CHP tmax limb models a hot-day *cooling*
commitment INCREMENT above the class's round-the-clock steam-host baseline
(the baseline is chp_steam's mechanism, not the reliability floor's — rule 19).
This diag measures where in the day that increment actually lives, so the
limb's sub-daily window can be set from its own driver evidence (rule 17)
instead of binding all 24 h (the pjm-77 D-4 CT_CHP failure, 70.8% off-window;
docs/FINDING-pjm-burndown-2026-07.md §6).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.eia_loader import iso_zone_tmax  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

HOURS = 8760
EMAAC_TMAX_GATE = 33.3  # reliability_floor_coeffs_PJM.csv EMAAC CT_CHP tmax
# Same pure-play screen as derive_pjm_ct_netload_drag / the CT_PEAKER diag:
# CAMPD extracts are plant-summed by ORIS, so mixed sites would contribute
# non-CT_CHP units' generation to the class signature.
PURE_PLAY_SHARE = 0.90
# CAMPD gross -> net (campd.DEFAULT_PARASITIC_LOAD_PCT["CT_CHP"] = 0.010).
NET_OF_GROSS = 0.99


def model_ctchp_plants(year: int, zone: str | None = None) -> tuple[dict, float]:
    """Pure-play PJM CT_CHP plants (optionally one zone) + class nameplate MW."""
    cfg = get_iso_config("PJM")
    gens = load_fleet_from_csv("PJM", cfg, year=year)
    plant_cap: dict[int, float] = {}
    chp_cap: dict[int, float] = {}
    for g in gens:
        pc = int(g.plant_code)
        if pc <= 0:
            continue
        plant_cap[pc] = plant_cap.get(pc, 0.0) + float(g.pmax_mw)
        if g.plant_group == "CT_CHP" and (zone is None or g.zone == zone):
            chp_cap[pc] = chp_cap.get(pc, 0.0) + float(g.pmax_mw)
    plants = {
        pc: cap for pc, cap in chp_cap.items() if cap / plant_cap[pc] >= PURE_PLAY_SHARE
    }
    return plants, float(sum(plants.values()))


def measured_mw(year: int, plant_codes: set[int]) -> np.ndarray:
    """Measured CT_CHP fleet net MW per hour (8760), from CAMPD CEMS."""
    states = campd.states_for_iso("PJM")
    df = campd.load_campd_hourly(states, [year])
    net = campd.plant_hourly_net(
        df, {pid: NET_OF_GROSS for pid in plant_codes}, year, hours=HOURS
    )
    fleet = np.zeros(HOURS)
    for pid, series in net.items():
        if pid in plant_codes:
            fleet[: series.shape[0]] += series[:HOURS]
    return fleet


def main() -> None:
    for zone in ("PJM_EMAAC", None):
        label = zone or "PJM all zones"
        for year in (2023, 2024, 2025):
            plants, nameplate = model_ctchp_plants(year, zone)
            if not plants:
                print(f"\n=== {label} {year}: no pure-play CT_CHP plants")
                continue
            mw = measured_mw(year, set(plants))
            cf = mw / nameplate
            hod = np.arange(HOURS) % 24

            tmax, _tmin = iso_zone_tmax("PJM", year, HOURS, zone="PJM_EMAAC")
            tmax = np.asarray(tmax, dtype=float)
            hot = tmax > EMAAC_TMAX_GATE
            n_hot = int(hot.reshape(-1, 24)[:, 0].sum())

            print(
                f"\n=== {label} {year}: {len(plants)} pure-play CT_CHP plants, "
                f"nameplate {nameplate / 1000:.2f} GW; annual CF {cf.mean():.4f}; "
                f"EMAAC hot days (tmax>{EMAAC_TMAX_GATE}C): {n_hot}"
            )
            print("hour  CF_hot  CF_other  increment")
            incr = np.zeros(24)
            for h in range(24):
                m = hod == h
                c_h = cf[m & hot].mean() if (m & hot).any() else float("nan")
                c_o = cf[m & ~hot].mean() if (m & ~hot).any() else float("nan")
                incr[h] = c_h - c_o
                star = " <-- window [15,22)" if 15 <= h < 22 else ""
                print(f"{h:>4}  {c_h:6.4f}  {c_o:8.4f}  {incr[h]:+9.4f}{star}")

            # Share of the positive hot-day increment inside the [15,22) window
            pos = np.clip(incr, 0.0, None)
            w = pos[15:22].sum()
            tot = pos.sum()
            if tot > 0:
                print(
                    f"hot-day CF increment inside [15,22): {100 * w / tot:.1f}% "
                    f"(in-window {w:.4f} / total {tot:.4f} CF-hours)"
                )


if __name__ == "__main__":
    main()
