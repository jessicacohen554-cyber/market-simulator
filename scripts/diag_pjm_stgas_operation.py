"""THROWAWAY DIAG (rule 15): characterize real PJM ST_GAS fleet operation.

Ground the steam-gas underrun fix. Measures, from CAMPD CEMS, the PJM ST_GAS
fleet's actual operation so the reliability commitment mechanism can be built
from its own driver evidence (rule 12/17) rather than guessed:

  * annual CF and total TWh (vs the model's underrun),
  * CF by hour-of-day (is the running round-the-clock or peak-only?),
  * energy share on temperature-flagged days vs the rest of the year (does the
    temp gate even capture where the energy lives?),
  * online/continuity statistics (run-lengths; do units cycle daily or hold
    across multi-day events?),
  * CF vs daily-max-temperature bins (the commitment-temperature relationship).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.eia_loader import iso_zone_tmax  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

HOURS = 8760
PURE_PLAY_SHARE = 0.90
NET_OF_GROSS = 0.99  # CAMPD gross -> net (ST_GAS parasitic ~1%)


def stgas_plants(year: int) -> tuple[dict, float]:
    """Pure-play PJM ST_GAS plants (by ORIS) + class nameplate MW."""
    cfg = get_iso_config("PJM")
    gens = load_fleet_from_csv("PJM", cfg, year=year)
    plant_cap: dict[int, float] = {}
    st_cap: dict[int, float] = {}
    for g in gens:
        pc = int(g.plant_code)
        if pc <= 0:
            continue
        plant_cap[pc] = plant_cap.get(pc, 0.0) + float(g.pmax_mw)
        if g.plant_group == "ST_GAS":
            st_cap[pc] = st_cap.get(pc, 0.0) + float(g.pmax_mw)
    plants = {
        pc: cap for pc, cap in st_cap.items() if cap / plant_cap[pc] >= PURE_PLAY_SHARE
    }
    return plants, float(sum(plants.values()))


def measured_mw(year: int, plant_codes: set[int]) -> np.ndarray:
    """Measured ST_GAS fleet net MW per hour (8760), from CAMPD CEMS."""
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


def run_lengths(online_day: np.ndarray) -> tuple[float, float, int]:
    """Mean/median online-run length (days) and count of runs >= 3 days."""
    runs = []
    n = 0
    for v in online_day.astype(int):
        if v:
            n += 1
        elif n:
            runs.append(n)
            n = 0
    if n:
        runs.append(n)
    if not runs:
        return 0.0, 0.0, 0
    r = np.array(runs)
    return float(r.mean()), float(np.median(r)), int((r >= 3).sum())


def main() -> None:
    # Zone p95 tmax gates the PJM ST_GAS hot limbs; use the load-weighted zone
    # tmax (Central_PA is the enabled ST_GAS tmax/netload zone in the CSV).
    for year in (2023, 2024, 2025):
        plants, nameplate = stgas_plants(year)
        if not plants:
            print(f"\n=== {year}: no pure-play ST_GAS plants")
            continue
        mw = measured_mw(year, set(plants))
        cf = mw / nameplate
        hod = np.arange(HOURS) % 24
        twh = mw.sum() / 1e6

        tmax_cpa, tmin_cpa = iso_zone_tmax("PJM", year, HOURS, zone="PJM_Central_PA")
        tmax_cpa = np.asarray(tmax_cpa, dtype=float)
        tmin_cpa = np.asarray(tmin_cpa, dtype=float)
        # Enabled PJM ST_GAS limbs: Central_PA tmax 32.8, tmin -12, West_APS
        # tmax 31.7; use zone p95 as the hot gate proxy.
        hot_gate = 32.8
        cold_gate = -12.0
        day_tmax = tmax_cpa.reshape(-1, 24)[:, 0]
        day_tmin = tmin_cpa.reshape(-1, 24)[:, 0]
        hot_day = day_tmax > hot_gate
        cold_day = day_tmin < cold_gate
        flagged_day = hot_day | cold_day
        flagged_hr = np.repeat(flagged_day, 24)[:HOURS]

        print(
            f"\n=== {year}: {len(plants)} pure-play ST_GAS plants, "
            f"nameplate {nameplate / 1000:.2f} GW"
        )
        print(
            f"    annual CF {cf.mean():.4f}; total {twh:.2f} TWh; "
            f"hot days {int(hot_day.sum())}, cold days {int(cold_day.sum())}, "
            f"flagged {int(flagged_day.sum())}/{len(day_tmax)}"
        )
        e_flagged = mw[flagged_hr].sum() / 1e6
        print(
            f"    energy on temp-flagged days: {e_flagged:.2f} TWh "
            f"({100 * e_flagged / twh:.1f}% of annual) "
            f"-> {100 * (twh - e_flagged) / twh:.1f}% is OFF flagged days"
        )

        # CF by hour of day
        cf_hod = np.array([cf[hod == h].mean() for h in range(24)])
        print(
            f"    CF by hour-of-day min {cf_hod.min():.3f} (h{cf_hod.argmin()}), "
            f"max {cf_hod.max():.3f} (h{cf_hod.argmax()}), "
            f"overnight h0-6 {cf_hod[:7].mean():.3f}, "
            f"afternoon h14-19 {cf_hod[14:20].mean():.3f}"
        )

        # Continuity: fleet "online" = fleet CF > 5% of nameplate on that day
        day_cf = cf.reshape(-1, 24).mean(axis=1)
        online_day = day_cf > 0.05
        mean_run, med_run, long_runs = run_lengths(online_day)
        print(
            f"    fleet online (day CF>5%): {int(online_day.sum())}/{len(day_cf)} days; "
            f"run-length mean {mean_run:.1f}d median {med_run:.1f}d; "
            f"runs>=3d: {long_runs}"
        )

        # CF vs daily tmax bins
        print("    CF vs daily-max-temp (Central_PA) bins:")
        edges = [-100, 0, 10, 20, 25, 30, 33, 100]
        for lo, hi in zip(edges[:-1], edges[1:]):
            sel_day = (day_tmax >= lo) & (day_tmax < hi)
            if not sel_day.any():
                continue
            sel_hr = np.repeat(sel_day, 24)[:HOURS]
            print(
                f"      [{lo:>4},{hi:>4})C: {int(sel_day.sum()):>3}d  "
                f"CF {cf[sel_hr].mean():.3f}"
            )


if __name__ == "__main__":
    main()
