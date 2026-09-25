"""R-ERCOT-5 zero-LP probe: CAMPD full-stop windows that cover hours the SAME unit generated.

A full-stop unit window (``campd-unit-outages*.csv``) says unit ``u`` of facility ``f``
is out from ``outage_start`` 00:00 through ``outage_end`` 23:00 (the incumbent
day-granular reconstruction, ``outages.unit_outage_event_window``). For every ERCOT
window row of the three families the ERCOT keeper arms — standard (>= 5 days),
short coal (< 5 days) and short gas (< 5 days) — this counts the hours inside the
window at which CAMPD shows that SAME unit (same facility id, same unit id) with
gross load > 0, and the MWh it produced there. A positive count is an exact
physical contradiction at unit grain: the unit cannot be both fully stopped and
generating in the same hour.

It also reports where those hours sit (the window's first day, its last day, or
interior days), because a day-granular reconstruction of a window whose unit
tripped mid-day / restarted mid-day contradicts CEMS only on the edge days.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_r_ercot5_window_edge_census.py <out.json>

Record: ``docs/handoffs/FINDING-r-ercot-5-2019-scarcity-2026-09-25.md``.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
FAMILIES = {
    "std": ("data/raw/campd-unit-outages.csv", lambda d: d >= 5),
    "short_coal": ("data/raw/campd-unit-outages-short.csv", lambda d: d < 5),
    "short_gas": ("data/raw/campd-unit-outages-shortgas.csv", lambda d: d < 5),
}


def main() -> None:
    """Run the census over 2019-2025 and write the JSON summary."""
    out = {}
    evs = {}
    for fam, (path, keep) in FAMILIES.items():
        ev = pd.read_csv(REPO / path)
        ev = ev[keep(ev["duration_days"])].copy()
        ev["outage_start"] = pd.to_datetime(ev["outage_start"])
        ev["outage_end"] = pd.to_datetime(ev["outage_end"])
        ev = ev[(ev["outage_end"].dt.year >= 2019) & (ev["outage_start"].dt.year <= 2025)]
        ev["unit_id"] = ev["unit_id"].astype(str).str.strip()
        ev["eid"] = np.arange(len(ev))
        evs[fam] = ev
        out[fam] = {}
    facs = sorted(set().union(*[set(e["facility_id"].astype(int)) for e in evs.values()]))
    for y in range(2019, 2026):
        d = pd.read_parquet(REPO / f"data/raw/campd-unit-level/TX_{y}.parquet",
                            columns=["facilityId", "unitId", "date", "hour", "grossLoad"])
        d["facilityId"] = d["facilityId"].astype(int)
        d = d[d["grossLoad"].fillna(0).gt(0) & d["facilityId"].isin(facs)]
        d["unitId"] = d["unitId"].astype(str).str.strip()
        for fam, ev in evs.items():
            m = d.merge(ev[["eid", "facility_id", "unit_id", "plant_group", "unit_capacity_mw",
                            "outage_start", "outage_end"]],
                        left_on=["facilityId", "unitId"], right_on=["facility_id", "unit_id"])
            m = m[(m["date"] >= m["outage_start"]) & (m["date"] <= m["outage_end"])]
            m["edge"] = np.where(m["date"] == m["outage_start"], "first_day",
                                 np.where(m["date"] == m["outage_end"], "last_day", "interior"))
            full = m["grossLoad"] >= 0.5 * m["unit_capacity_mw"]
            e_y = ev[(ev["outage_start"].dt.year <= y) & (ev["outage_end"].dt.year >= y)]
            out[fam][y] = {
                "windows": int(len(e_y)),
                "windows_contradicted": int(m["eid"].nunique()),
                "unit_hours_generating": int(len(m)),
                "unit_hours_ge_half_cap": int(full.sum()),
                "GWh_generated_inside_window": round(float(m["grossLoad"].sum()) / 1e3, 1),
                "by_edge_unit_hours": {k: int(v) for k, v in m.groupby("edge").size().items()},
                "by_edge_GWh": (m.groupby("edge")["grossLoad"].sum() / 1e3).round(1).to_dict(),
                "by_group_GWh": (m.groupby("plant_group")["grossLoad"].sum() / 1e3).round(1).to_dict(),
            }
            print(fam, y, json.dumps(out[fam][y], default=str), flush=True)
        del d
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
