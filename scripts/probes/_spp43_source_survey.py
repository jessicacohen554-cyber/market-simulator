"""SPP-43 phase 0: does the CAMPD unit-level corpus support a 2019-2022
unit-outage derivation for SPP?

Zero-LP source survey (CLAUDE.md rule 29 ``[R-SCREEN]`` step 0). Measures, per
year over 2019-2025 and per SPP detection state:

  * whether the ``{STATE}_{YEAR}.parquet`` extract exists at all,
  * its row count, unique facilities/units and calendar completeness,
  * how much of the SPP MODEL FLEET (the ``group_by_code`` map the deriver
    itself builds) files CEMS in that year,
  * coverage of the 21 floored ST_GAS plant-groups the keeper's
    ``st_gas_mustrun_per_plant`` floor acts on, which is where SPP-40's
    held-out C8 breach and card R-be's D-4 residue both land.

Reports 2019-2022 against the 2023-2025 baseline the committed extract was
derived from, so "can the detector produce these years at all" is answered by
measurement rather than assumption.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    load_fleet_from_csv,
    load_retired_within_window,
)

ISO = "SPP"
YEARS = list(range(2019, 2026))
UNIT_DIR = REPO / "data" / "raw" / "campd-unit-level"


def fleet_group_by_code() -> tuple[dict[int, str], dict[int, str]]:
    """The deriver's own plant->group map, rebuilt exactly as it builds it."""
    cfg = get_iso_config(ISO)
    fleet = load_fleet_from_csv(ISO, cfg) + load_retired_within_window(ISO, cfg)
    group: dict[int, str] = {}
    name: dict[int, str] = {}
    for g in fleet:
        if int(g.plant_code) > 0 and g.plant_group:
            group[int(g.plant_code)] = g.plant_group
            name[int(g.plant_code)] = g.name
    return group, name


def main() -> None:
    states = campd.states_for_iso(ISO)
    group_by_code, name_by_code = fleet_group_by_code()
    st_gas = {c for c, g in group_by_code.items() if g == "ST_GAS"}
    coal = {c for c, g in group_by_code.items() if str(g).startswith("COAL")}

    print(f"SPP detection states ({len(states)}): {', '.join(states)}")
    print(f"SPP model fleet plant codes: {len(group_by_code)}"
          f"  (ST_GAS {len(st_gas)}, COAL* {len(coal)})")
    print()

    # --- A. file presence -------------------------------------------------
    print("=== A. state x year extract presence ===")
    missing_states = []
    for st in states:
        marks = []
        for y in YEARS:
            marks.append("Y" if (UNIT_DIR / f"{st}_{y}.parquet").exists() else "-")
        print(f"  {st}: " + " ".join(f"{y}{m}" for y, m in zip(YEARS, marks)))
        if all(m == "-" for m in marks):
            missing_states.append(st)
    print(f"  states absent in EVERY year (so also absent from the committed "
          f"2023-2025 derive): {missing_states or 'none'}")
    print()

    # --- B/C. per-year corpus + fleet coverage ----------------------------
    print("=== B/C. per-year corpus and SPP fleet CEMS coverage ===")
    out = {}
    for y in YEARS:
        rows = 0
        facs: set[int] = set()
        units: set[tuple[int, str]] = set()
        dmin, dmax = None, None
        for st in states:
            f = UNIT_DIR / f"{st}_{y}.parquet"
            if not f.exists():
                continue
            df = pq.read_table(
                f, columns=["facilityId", "unitId", "date", "grossLoad"]
            ).to_pandas()
            rows += len(df)
            # a unit "files" only if it reported any non-null gross load
            live = df[df["grossLoad"].notna()]
            facs.update(int(x) for x in live["facilityId"].unique())
            units.update(
                (int(a), str(b))
                for a, b in zip(live["facilityId"], live["unitId"])
            )
            d = pd.to_datetime(df["date"])
            dmin = d.min() if dmin is None else min(dmin, d.min())
            dmax = d.max() if dmax is None else max(dmax, d.max())
        fleet_seen = facs & set(group_by_code)
        stgas_seen = facs & st_gas
        coal_seen = facs & coal
        out[y] = dict(
            rows=rows,
            facilities=len(facs),
            units=len(units),
            date_min=str(dmin.date()) if dmin is not None else None,
            date_max=str(dmax.date()) if dmax is not None else None,
            fleet_plants_seen=len(fleet_seen),
            st_gas_seen=len(stgas_seen),
            coal_seen=len(coal_seen),
        )
        print(
            f"  {y}: rows={rows:>9,}  facilities={len(facs):>4}  units={len(units):>4}  "
            f"span={out[y]['date_min']}..{out[y]['date_max']}  "
            f"fleet_plants={len(fleet_seen):>3}/{len(group_by_code)}  "
            f"ST_GAS={len(stgas_seen):>2}/{len(st_gas)}  COAL={len(coal_seen):>2}/{len(coal)}"
        )
    print()

    # --- D. the floored ST_GAS plant-groups, per plant ---------------------
    print("=== D. ST_GAS fleet plants: which years does each file CEMS in? ===")
    seen_by_year = {}
    for y in YEARS:
        s: set[int] = set()
        for st in states:
            f = UNIT_DIR / f"{st}_{y}.parquet"
            if not f.exists():
                continue
            df = pq.read_table(f, columns=["facilityId", "grossLoad"]).to_pandas()
            live = df[df["grossLoad"].notna()]
            s.update(int(x) for x in live["facilityId"].unique())
        seen_by_year[y] = s
    for c in sorted(st_gas):
        marks = "".join("Y" if c in seen_by_year[y] else "." for y in YEARS)
        print(f"  {c:>6} {name_by_code.get(c,''):<34} {marks}   ({'-'.join(str(YEARS[0])[2:])}..)")
    print(f"  legend: one char per year {YEARS[0]}..{YEARS[-1]}")
    print()

    (REPO / "results" / "calibration").mkdir(parents=True, exist_ok=True)
    dest = REPO / "results" / "calibration" / "_spp43_source_survey.json"
    dest.write_text(json.dumps(out, indent=2, sort_keys=True))
    print(f"wrote {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
