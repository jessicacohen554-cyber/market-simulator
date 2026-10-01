"""R-ERCOT-20 D-4 design phase 0 (zero LP): off-stretch structure of the residual st_netload_drag FAIL plants.

For each residual D-4 unit-conduct FAIL (plant-year) and a passing comparator set,
reads CAMPD hourly gross load, forms the plant total, finds every all-units-off
stretch, and classifies the plant's zero-output hours by stretch length:
< 24 h (intra-day cycling), 1-5 days (short shutdown), >= 5 days (lay-up / outage
scale). Also reports how many zero hours the existing >= 5-day masks (the
economic-lay-up companion + the outage extract) already cover, and the unit
structure (a plant can read zero only when EVERY unit is off, so a one-unit-on
plant never reads zero). Solves nothing.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

FAILS = {3452: (2019, 2020, 2021, 2023), 3628: (2019, 2020), 3491: (2024, 2025)}
PASSES = {3452: (2022, 2024, 2025), 3628: (2021, 2022, 2023, 2024, 2025), 3491: (2019, 2020, 2021, 2022, 2023)}


def plant_hours(pid: int, year: int) -> tuple[np.ndarray, int]:
    """Plant-total hourly gross MW (8760, Jan 1 00h start) and its unit count."""
    c = pd.read_parquet(RAW_DATA_DIR / f"campd-unit-level/TX_{year}.parquet",
                        columns=["facilityId", "unitId", "date", "hour", "grossLoad"])
    c = c[c.facilityId.astype(str) == str(pid)]
    ts = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"].astype(int), unit="h")
    h = ((ts - pd.Timestamp(f"{year}-01-01")) / pd.Timedelta(hours=1)).astype(int).to_numpy()
    out = np.zeros(8784)
    np.add.at(out, h[(h >= 0) & (h < 8784)], c["grossLoad"].fillna(0).to_numpy()[(h >= 0) & (h < 8784)])
    return out[:8760], c.unitId.nunique()


def masked_hours(pid: int, year: int) -> np.ndarray:
    """Hours in which ALL of the plant's units sit inside a >= 5-day lay-up or outage window."""
    cov = []
    for f in ("campd-unit-outages-layup.csv", "campd-unit-outages.csv"):
        p = RAW_DATA_DIR / f
        if not p.exists():
            continue
        d = pd.read_csv(p)
        d = d[(d.facility_id.astype(str) == str(pid)) & (d.duration_days >= 5)]
        cov.append(d)
    d = pd.concat(cov) if cov else pd.DataFrame()
    t0 = pd.Timestamp(f"{year}-01-01")
    per_unit: dict = {}
    for _, r in d.iterrows():
        s = max(0, int((pd.Timestamp(r.outage_start) - t0) / pd.Timedelta(hours=1)))
        e = min(8760, int((pd.Timestamp(r.outage_end) - t0) / pd.Timedelta(hours=1)) + 24)
        if e <= 0 or s >= 8760:
            continue
        m = per_unit.setdefault(str(r.unit_id), np.zeros(8760, bool))
        m[s:e] = True
        n = int(r.total_units_at_plant)
    if not per_unit:
        return np.zeros(8760, bool)
    stack = np.vstack(list(per_unit.values()))
    return stack.all(axis=0) if len(per_unit) >= n else np.zeros(8760, bool)


def census(pid: int, year: int) -> dict:
    """Zero-hour split by off-stretch length, plus existing-mask coverage."""
    mw, nunits = plant_hours(pid, year)
    z = mw <= 0
    lens = np.zeros(8760)
    i = 0
    while i < 8760:
        if z[i]:
            j = i
            while j < 8760 and z[j]:
                j += 1
            lens[i:j] = j - i
            i = j
        else:
            i += 1
    nz = int(z.sum())
    mk = masked_hours(pid, year)
    return {"plant": pid, "year": year, "units": nunits, "zero_h": nz,
            "lt1d": int((z & (lens < 24)).sum()), "d1_5": int((z & (lens >= 24) & (lens < 120)).sum()),
            "ge5d": int((z & (lens >= 120)).sum()), "ge5d_masked": int((z & (lens >= 120) & mk).sum()),
            "on_days_share": round(float((mw.reshape(365, 24).max(axis=1) > 0).mean()), 3)}


def main() -> None:
    """Print and record the census."""
    rows = [dict(census(p, y), verdict="FAIL") for p, ys in FAILS.items() for y in ys]
    rows += [dict(census(p, y), verdict="pass") for p, ys in PASSES.items() for y in ys]
    t = pd.DataFrame(rows)
    print(t.to_string(index=False))
    with open("docs/handoffs/r-ercot/r_ercot20_d4_gap_census.json", "w") as f:
        json.dump(rows, f, indent=1)


if __name__ == "__main__":
    main()


def file_cover(pid: int, year: int, files: tuple[str, ...]) -> np.ndarray:
    """Hours in which every one of the plant's units in ``files`` is inside a listed window."""
    d = pd.concat([pd.read_csv(RAW_DATA_DIR / f) for f in files])
    d = d[d.facility_id.astype(str) == str(pid)]
    if d.empty:
        return np.zeros(8760, bool)
    t0 = pd.Timestamp(f"{year}-01-01")
    per_unit: dict = {}
    for _, r in d.iterrows():
        s = max(0, int((pd.Timestamp(r.outage_start) - t0) / pd.Timedelta(hours=1)))
        e = min(8760, int((pd.Timestamp(r.outage_end) - t0) / pd.Timedelta(hours=1)) + 24)
        if e > 0 and s < 8760:
            per_unit.setdefault(str(r.unit_id), np.zeros(8760, bool))[s:e] = True
    n = int(d.total_units_at_plant.max())
    return np.vstack(list(per_unit.values())).all(axis=0) if len(per_unit) >= n else np.zeros(8760, bool)


def short_cover_table() -> pd.DataFrame:
    """Share of each FAIL row's 1-5 day zero hours covered by the unread short lay-up companion."""
    long_f = ("campd-unit-outages-layup.csv", "campd-unit-outages.csv")
    short_f = long_f + ("campd-unit-outages-layup-shortgas.csv", "campd-unit-outages-shortgas.csv")
    rows = []
    for p, ys in FAILS.items():
        for y in ys:
            mw, _ = plant_hours(p, y)
            z = mw <= 0
            a, b = file_cover(p, y, long_f), file_cover(p, y, short_f)
            rows.append({"plant": p, "year": y, "zero_h": int(z.sum()),
                         "covered_now": int((z & a).sum()), "covered_with_short_layup": int((z & b).sum()),
                         "gain_h": int((z & b & ~a).sum()), "uncovered_zero_h": int((z & ~b).sum())})
    return pd.DataFrame(rows)
