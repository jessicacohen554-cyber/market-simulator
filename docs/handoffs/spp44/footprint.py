"""SPP-44 phase 0 (zero-LP): the mechanism's measured FOOTPRINT by year, which
names the rule-29(a) screen year — never the year with the biggest residual.

Construction (declared in PRECOMMIT-spp-44 §2 before this ran):

* For every bridge-eligible plant with a CAMPD series (the plant-basis derive's
  45 facilities), the plant's hourly ONLINE state in each year is its summed
  CEMS gross load >= max(_ONLINE_MW, 0.05 x HSL_plant) — the derive's own
  threshold, so the state is the one the min-load statistic was measured on.
* The measured COMMITTED-STATE floor of a class in hour t is
  F(t) = sum over online plants of LSL_plant (the plant-basis p5-of-online
  minimum stable load, MW). It is what a minimum-load hold on the REAL
  commitment pattern would force.
* The model's economic dispatch D(t) is keeper-2's committed
  ``hourly/class_hourly_<year>.parquet`` P1 series for the class.
* Footprint(year, class) = sum_t max(0, F(t) - D(t)) [GWh] and the hour count
  with F > D: the volume by which the measured committed state exceeds the
  keeper's economic dispatch — the room a commitment floor has to act in.
  The bridge itself anchors on the model's OWN P0 pattern, so this is the
  measured-conduct proxy for its footprint, not the floor it will write.

Also reported, per year: the CAMPD idle-gap population of the eligible plants
(gaps between plant runs that are < the plant's class min-down, and <= 24 h),
which is the population the bridge's two gap legs act on in the real record.

Writes docs/handoffs/spp44/campd_online_<year>.parquet (plant x hour bool) for
the post-solve gate-(i) window grading, and footprint.csv.

Usage: uv run python docs/handoffs/spp44/footprint.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
from derive_campd_gas_commitment_params import (  # noqa: E402
    _HSL_PCTILE,
    _ONLINE_FRAC,
    UNIT_LEVEL_DIR,
    unit_run_lengths,
)
from market_sim.data.campd import _ONLINE_MW, states_for_iso  # noqa: E402
from market_sim.model.commitment import find_runs  # noqa: E402

OUT = REPO / "docs/handoffs/spp44"
PROC = REPO / "data/raw/_processed-legacy"
BUNDLE = REPO / "results/calibration/spp42_crosswalk_B"
YEARS = (2023, 2024, 2025)
# Class min-down for the physical-gap census: the keeper fleet's resolved
# values (census_eligibility.py): CC 4/6 h, ST_GAS 8/12 h — the LOWER of each
# pair is used so the physical-gap count is the conservative (smaller) one.
MIN_DOWN = {"CC_REGULAR": 4, "ST_GAS": 8}
DA_HORIZON = 24


def plant_series(codes: set[int], year: int) -> dict[int, np.ndarray]:
    """Return {plant_code: summed hourly gross load (8760,)} for *codes* in *year*."""
    out: dict[int, pd.DataFrame] = {}
    for state in states_for_iso("SPP"):
        path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(
            path, columns=["facilityId", "date", "hour", "grossLoad"]
        )
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(codes)]
        if df.empty:
            continue
        g = df.groupby(["facilityId", "date", "hour"], as_index=False)["grossLoad"].sum()
        for fid, sub in g.groupby("facilityId"):
            out.setdefault(int(fid), []).append(sub)
    series = {}
    for fid, chunks in out.items():
        s = pd.concat(chunks).sort_values(["date", "hour"])
        s["ts"] = pd.to_datetime(s["date"].astype(str)) + pd.to_timedelta(
            s["hour"], unit="h"
        )
        s = s.groupby("ts")["grossLoad"].sum()
        idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
        series[fid] = s.reindex(idx).fillna(0.0).to_numpy(dtype=float)
    return series


def main() -> None:
    plant = pd.read_csv(PROC / "campd_gas_commitment_params_plant_SPP_units.csv")
    elig = pd.read_csv(OUT / "eligibility_rows.csv")
    elig = elig[elig.eligible]
    klass_of = elig.groupby("plant_code")["plant_group"].first()
    codes = set(int(c) for c in plant.plant_code) & set(int(c) for c in klass_of.index)
    print(f"eligible plants with a CAMPD series: {len(codes)}")
    lsl = plant.set_index("plant_code")["lsl_mw"]
    hsl = plant.set_index("plant_code")["hsl_mw"]
    rows = []
    for year in YEARS:
        ser = plant_series(codes, year)
        ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        online = {}
        gap_phys = {k: 0 for k in MIN_DOWN}
        gap_phys_h = {k: 0 for k in MIN_DOWN}
        gap_da = {k: 0 for k in MIN_DOWN}
        gap_da_h = {k: 0 for k in MIN_DOWN}
        runs_n = {k: 0 for k in MIN_DOWN}
        for fid, load in ser.items():
            thresh = max(_ONLINE_MW, _ONLINE_FRAC * float(hsl[fid]))
            on = load >= thresh
            online[fid] = on
            k = klass_of[fid]
            runs = find_runs(on)
            runs_n[k] += len(runs)
            for (_, e0), (s1, _) in zip(runs[:-1], runs[1:]):
                gap = s1 - e0
                if gap < MIN_DOWN[k]:
                    gap_phys[k] += 1
                    gap_phys_h[k] += gap
                elif gap <= DA_HORIZON:
                    gap_da[k] += 1
                    gap_da_h[k] += gap
        on_df = pd.DataFrame({str(f): v for f, v in online.items()})
        on_df.to_parquet(OUT / f"campd_online_{year}.parquet", index=False)
        for k in MIN_DOWN:
            plants_k = [f for f in online if klass_of[f] == k]
            F = np.zeros(8760)
            for f in plants_k:
                F += online[f] * float(lsl[f])
            D = (
                ch[ch.klass == k].sort_values("hour")["mw"].to_numpy(dtype=float)
            )
            assert D.size == 8760, (k, D.size)
            excess = np.maximum(0.0, F - D)
            rows.append(
                {
                    "year": year,
                    "class": k,
                    "campd_plants": len(plants_k),
                    "plant_online_hours": int(sum(online[f].sum() for f in plants_k)),
                    "F_mean_mw": round(float(F.mean()), 1),
                    "D_mean_mw": round(float(D.mean()), 1),
                    "footprint_gwh": round(float(excess.sum()) / 1e3, 1),
                    "hours_F_gt_D": int((F > D).sum()),
                    "runs": runs_n[k],
                    "gaps_lt_min_down": gap_phys[k],
                    "gaps_lt_min_down_hours": gap_phys_h[k],
                    "gaps_min_down_to_24h": gap_da[k],
                    "gaps_min_down_to_24h_hours": gap_da_h[k],
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "footprint.csv", index=False)
    pd.set_option("display.width", 250)
    print(df.to_string(index=False))
    tot = df.groupby("year")["footprint_gwh"].sum()
    print("\nfootprint by year (both classes, GWh):", tot.to_dict())
    print("SCREEN YEAR (largest footprint):", int(tot.idxmax()))


if __name__ == "__main__":
    main()
