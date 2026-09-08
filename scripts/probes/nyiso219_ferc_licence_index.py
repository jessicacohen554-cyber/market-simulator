"""nyiso-219 — the FERC licence index for NYISO's hydro fleet, and what it is for.

The pondage measurement (``FINDING-nyiso219-pondage-duration-2026-09-07.md``) left
one thing outstanding: a per-plant **period length** needs the **licensed operating
range**, which NID does not carry. The range lives in each project's FERC licence
articles, and those are keyed by **FERC project (docket) number**.

**Those docket numbers are already in the repo.** ORNL EHA FY2024 carries ``FC_Dock``
with ``FcIssue`` / ``FcExpire`` (the sheet's own Field Descriptions give the source as
"EHA, FERC"), covering **99.08 % of NYISO hydro MW**. This probe assembles them into
one retrieval index, joined to everything already measured for the same plant --
nameplate, EHA operating mode, EIA-860 water source, NID dam, storage and the pondage
upper bound -- and orders it by MW so the cost of a licence pull is obvious:
**two dockets cover 71 % of the fleet.**

**Why this is an index and not the ranges themselves.** FERC document text could not be
retrieved from this container and the failure is recorded rather than worked around:

* ``www.ferc.gov`` and ``cms.ferc.gov`` return **403** to this network, with a normal
  browser User-Agent as well -- FERC's own edge, not the session proxy (the proxy
  reports ``selective: false`` and no relay failures);
* ``elibrary.ferc.gov`` loads, but it is a client-rendered Angular app with no public
  API. Candidate REST paths that appeared to return 200 were the SPA's **catch-all
  serving index.html**, confirmed by diffing the body against the shell -- they are
  **not** endpoints, and are recorded here so nobody re-discovers them as one;
* the pre-installed Chromium cannot reach **any** host from this container
  (``example.com`` resets identically), so driving the SPA is not available either.

So the licence articles need either a session with working browser egress or a human
with a browser. This index is what makes that pull cheap and targeted.

ZERO LP. Nothing armed, no ``ScenarioConfig`` field, keeper untouched.
Charter: ``docs/CHARTER-nyiso219-hydro-budget-period-2026-09-07.md``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

EHA = REPO / "data" / "raw" / "ornl-eha" / "ORNL_EHAHydroPlant_PublicFY2024.xlsx"
HILARRI = REPO / "data" / "raw" / "hilarri" / "HILARRI_v4.csv"
NID = REPO / "data" / "raw" / "nid" / "nid_nyiso_hydro_dams.csv"
PLANT_860 = REPO / "data" / "raw" / "eia-860" / "eia860_plant.parquet"

OUT_CSV = REPO / "results" / "calibration" / "_nyiso219_ferc_licence_index.csv"
OUT_JSON = REPO / "results" / "calibration" / "_nyiso219_ferc_licence_index.json"

# eLibrary's per-docket landing page. Recorded as the retrieval target for whoever
# has browser egress; it is NOT fetched here (see the module docstring).
ELIBRARY_DOCKET_URL = "https://elibrary.ferc.gov/eLibrary/search?docket={docket}"

_MWH_PER_ACREFT_FOOT: float = 1000.0 * 9.81 * 1233.4818 * 0.3048 / 3.6e9


def main() -> None:
    from market_sim.data.hydro import _load_hydro_nameplate

    nameplate = _load_hydro_nameplate("NYISO")
    fleet_mw = float(sum(nameplate.values()))

    eha = pd.read_excel(EHA, sheet_name="Operational")
    eha["EIA_PtID"] = pd.to_numeric(eha["EIA_PtID"], errors="coerce")
    eha = eha[eha.EIA_PtID.isin(nameplate.keys())]
    # A single EIA plant id can carry several EHA powerhouses (54580 = Palmer +
    # Curtis). They share one FERC docket, so collapse to the first non-null.
    eha = eha.groupby(eha.EIA_PtID.astype(int)).agg(
        {"PtName": "first", "FC_Dock": "first", "FcIssue": "first",
         "FcExpire": "first", "Mode": "first"}
    )

    plants = pd.read_parquet(PLANT_860)
    plants["Plant Code"] = pd.to_numeric(plants["Plant Code"], errors="coerce")
    plants = plants.drop_duplicates("Plant Code").set_index("Plant Code")

    hil = pd.read_csv(HILARRI, low_memory=False)
    hil["eia_ptid"] = pd.to_numeric(hil["eia_ptid"], errors="coerce")
    hil = hil[hil.eia_ptid.isin(nameplate.keys())]

    nid = pd.read_csv(NID, low_memory=False)
    nid["NID ID"] = nid["NID ID"].astype(str).str.strip()
    # Project-level aggregation -- a NID ID names a project, not a structure, and
    # its rows repeat the project storage (see data/raw/nid/README.md trap 1).
    nid = nid.groupby("NID ID").agg(
        {"Normal Storage (Acre-Ft)": "max", "Max Storage (Acre-Ft)": "max",
         "Hydraulic Height (Ft)": "max", "Dam Height (Ft)": "max"}
    )

    rows = []
    for plant_id, mw in sorted(nameplate.items(), key=lambda kv: -kv[1]):
        rec = eha.loc[plant_id] if plant_id in eha.index else None
        dams = [
            d for d in hil[hil.eia_ptid == plant_id].nidid.dropna().astype(str).str.strip()
            if d in nid.index
        ]
        storage = float(nid.loc[dams, "Max Storage (Acre-Ft)"].fillna(0).sum()) if dams else 0.0
        hyd = nid.loc[dams, "Hydraulic Height (Ft)"].max() if dams else None
        dam_h = nid.loc[dams, "Dam Height (Ft)"].max() if dams else None
        head = float(hyd) if pd.notna(hyd) and hyd else float(dam_h) if pd.notna(dam_h) else 0.0
        docket = None
        if rec is not None and pd.notna(rec.FC_Dock) and str(rec.FC_Dock).strip().lower() != "nan":
            docket = str(rec.FC_Dock).strip()
        rows.append(
            {
                "plant_id": plant_id,
                "plant_name": str(rec.PtName) if rec is not None else "",
                "nameplate_mw": round(mw, 1),
                "pct_fleet_mw": round(100.0 * mw / fleet_mw, 3),
                "ferc_docket": docket,
                "ferc_licence_issued": str(rec.FcIssue) if rec is not None else "",
                "ferc_licence_expires": str(rec.FcExpire) if rec is not None else "",
                "eha_mode": str(rec.Mode) if rec is not None else "",
                "water_source": str(plants.loc[plant_id, "Name of Water Source"])
                if plant_id in plants.index
                else "",
                "nid_ids": ";".join(dams),
                "max_storage_acreft": round(storage, 1),
                "head_ft": round(head, 1),
                "head_basis": "hydraulic_height"
                if pd.notna(hyd) and hyd
                else ("dam_height_PROXY" if head else "none"),
                "pondage_hours_upper_bound": round(
                    _MWH_PER_ACREFT_FOOT * storage * head / mw, 3
                )
                if mw > 0 and storage and head
                else None,
                "elibrary_url": ELIBRARY_DOCKET_URL.format(docket=docket) if docket else None,
            }
        )

    frame = pd.DataFrame(rows)
    frame["cum_pct_fleet_mw"] = frame.pct_fleet_mw.cumsum().round(3)
    frame.to_csv(OUT_CSV, index=False)

    with_docket = frame[frame.ferc_docket.notna()]
    dockets = sorted(set(with_docket.ferc_docket))
    # How many DISTINCT dockets a pull must cover to reach each MW threshold.
    def dockets_for(pct: float) -> int:
        seen, cum = set(), 0.0
        for r in frame.itertuples():
            if cum >= pct:
                break
            if r.ferc_docket:
                seen.add(r.ferc_docket)
            cum += r.pct_fleet_mw
        return len(seen)

    record = {
        "session": "nyiso-219",
        "purpose": "retrieval index for the LICENSED OPERATING RANGE (the period "
        "length a shortened hydro budget row would need); the ranges themselves "
        "are NOT here — see the module docstring for why FERC text was unreachable",
        "zero_lp": True,
        "coverage": {
            "plants_with_ferc_docket": int(with_docket.plant_id.nunique()),
            "pct_fleet_mw_with_docket": round(
                100.0 * float(with_docket.nameplate_mw.sum()) / fleet_mw, 2
            ),
            "distinct_dockets": len(dockets),
        },
        "retrieval_cost": {
            "dockets_to_cover_50pct_mw": dockets_for(50.0),
            "dockets_to_cover_75pct_mw": dockets_for(75.0),
            "dockets_to_cover_90pct_mw": dockets_for(90.0),
        },
        "top_projects": [
            {
                k: r[k]
                for k in (
                    "plant_id", "plant_name", "nameplate_mw", "pct_fleet_mw",
                    "cum_pct_fleet_mw", "ferc_docket", "ferc_licence_issued",
                    "ferc_licence_expires", "eha_mode", "water_source",
                    "pondage_hours_upper_bound",
                )
            }
            for r in frame.head(10).to_dict("records")
        ],
        "ferc_access": {
            "www.ferc.gov": "403 to this container, browser User-Agent included",
            "cms.ferc.gov": "403 (the issued-licences spreadsheet)",
            "elibrary.ferc.gov": "reachable, but a client-rendered SPA with no public "
            "API; candidate REST paths returning 200 are the Angular catch-all "
            "serving index.html, confirmed by body diff — NOT endpoints",
            "chromium": "cannot reach any host from this container (example.com "
            "resets identically), so driving the SPA is unavailable",
            "session_proxy": "open and healthy (selective:false, no relay failures) "
            "— the 403 is FERC's edge, not ours",
        },
        "csv": str(OUT_CSV.relative_to(REPO)),
    }
    OUT_JSON.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
