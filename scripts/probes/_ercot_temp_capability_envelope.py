"""Measure the ERCOT gas fleet's hot-hour capability envelope from CEMS.

Tests whether the ``temp_dependent_derate`` per-class temperature curves
(literature slopes: CT 1.26 %/degC, CC 0.76 %/degC, ST_GAS 0.54 %/degC above
the 15 degC ISO rating point) have any signature in the ERCOT fleet's own
measured hourly output — the same admissibility test the coal summer-derate
investigation applied (2026-07-08 calibration-log entry: no CEMS signature ->
no admissible driver).

Method, per class and summer (Jun-Sep), from CAMPD hourly unit gross load
joined to hourly zone dry-bulb TMAX (the exact temperature series the derate
consumes):

* **Envelope**: p98 of ``grossLoad / ref`` within each temperature bin, where
  ``ref`` is the unit's p99.5 gross load at benign 26-32 degC summer hours
  (or, stricter, its global summer maximum). On 40+ degC afternoons ERCOT
  prices are high enough that every available unit runs flat out, so the
  upper envelope of realized output IS deliverable capability (net of the
  separately-modeled forced outages).
* **Top-output temperature**: the zone TMAX at each unit's top-20 summer
  output hours. A real hot-hour capability cut would cluster the maxima at
  moderate temperatures; the ERCOT fleet instead hits its summer maxima ON
  hot hours.

Result (2023 + 2024, TX fleet, 108 CC / 88 CT / 40 ST units): the envelope is
FLAT — CC 0.99-1.01 and CT 0.98-1.09 of reference at 40-46 degC (global-ref:
0.98-1.00), ST_GAS 1.00 — where the model's raw curves predict 0.77-0.93.
The measured incremental hot-hour derate beyond EIA-860 net-summer is ~1-2 %,
not 9-23 %: Texas units are equipped/rated for Texas summers (inlet
evaporative cooling/chillers), so net-summer capability already IS the
hot-day rating and no further temperature cut is admissible for this fleet.

Diagnostic analysis only — no LP, no solve. Usage:
    python scripts/probes/_ercot_temp_capability_envelope.py [YEAR ...]
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia_loader import iso_zone_tmax  # noqa: E402

BINS_CSV = REPO / "data" / "raw" / "reference" / "custom-bin-assignments.csv"
CAMPD_DIR = REPO / "data" / "raw" / "campd-unit-level"
TBINS = [(26, 32), (32, 36), (36, 38), (38, 40), (40, 42), (42, 46)]
MODEL_SLOPES = {
    "CC_REGULAR": 0.0076,
    "CC_CHP": 0.0076,
    "CT_PEAKER": 0.0126,
    "ST_GAS": 0.0054,
}
GROUPS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP")


def _summer_frame(year: int) -> pd.DataFrame:
    """CAMPD TX hourly gross load, class/zone-joined, TMAX-tagged, Jun-Sep."""
    bins = pd.read_csv(BINS_CSV)
    p2g = bins.drop_duplicates("Plant_Code").set_index("Plant_Code")[
        ["Plant_Group", "ERCOT_Zone"]
    ]
    d = pd.read_parquet(
        CAMPD_DIR / f"TX_{year}.parquet",
        columns=["facilityId", "unitId", "date", "hour", "grossLoad"],
    )
    d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce").astype("Int64")
    d["grossLoad"] = d["grossLoad"].fillna(0.0)
    d = d.merge(p2g, left_on="facilityId", right_index=True, how="inner")
    d["doy"] = pd.to_datetime(d["date"]).dt.dayofyear
    d["hoy"] = (d["doy"] - 1) * 24 + d["hour"].astype(int)
    tmax = {}
    for z in d["ERCOT_Zone"].unique():
        t = iso_zone_tmax("ERCOT", year, 8760, zone=z)
        if t is not None and t[0] is not None:
            tmax[z] = np.asarray(t[0], dtype=float)
    d = d[d["ERCOT_Zone"].isin(tmax)].copy()
    tcol = np.full(len(d), np.nan)
    hoy = d["hoy"].to_numpy()
    for z, arr in tmax.items():
        m = (d["ERCOT_Zone"] == z).to_numpy() & (hoy < 8760)
        tcol[m] = arr[hoy[m]]
    d["T"] = tcol
    return d[(d["doy"] >= 152) & (d["doy"] <= 273)].dropna(subset=["T"])


def main(years: list[int]) -> None:
    """Print the measured envelope vs the model curve for each year/class."""
    for year in years:
        summer = _summer_frame(year)
        key = ["facilityId", "unitId"]
        ref = (
            summer[(summer["T"] >= 26) & (summer["T"] <= 32)]
            .groupby(key)["grossLoad"]
            .quantile(0.995)
            .rename("ref")
        )
        summer = summer.merge(ref.reset_index(), on=key)
        summer = summer[summer["ref"] >= 20.0]
        summer["ratio"] = summer["grossLoad"] / summer["ref"]
        print(f"== {year} measured capability envelope (p98 ratio per TMAX bin) ==")
        print("   T bins: " + " | ".join(f"{lo}-{hi}" for lo, hi in TBINS))
        for grp in GROUPS:
            g = summer[summer["Plant_Group"] == grp]
            cells = []
            for lo, hi in TBINS:
                s = g[(g["T"] >= lo) & (g["T"] < hi)]
                cells.append(
                    f"{s['ratio'].quantile(0.98):.3f}" if len(s) > 500 else "  -- "
                )
            n = g.groupby(key).ngroups
            print(f"   {grp:11s} ({n:3d} units): " + " | ".join(cells))
        for grp, slope in MODEL_SLOPES.items():
            mids = [(lo + hi) / 2 for lo, hi in TBINS]
            ref_m = 1.0 - slope * (29.0 - 15.0)
            row = " | ".join(f"{(1 - slope * (m - 15)) / ref_m:.3f}" for m in mids)
            print(f"   model {grp:11s} (slope {slope}): " + row)


if __name__ == "__main__":
    main([int(y) for y in sys.argv[1:]] or [2023, 2024])
