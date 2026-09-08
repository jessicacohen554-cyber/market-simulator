"""nyiso-219 §5 — feasibility census for the hydro **budget-period** charter.

**NOT pre-registered, and it carries no predictions.** The nyiso-219 PREREG covered
the daily-driver data question (M1-M3); this census was taken afterwards, on the
owner's Option-C instruction, to establish what a *pondage-duration* budget period
could be identified from. It adjudicates nothing and moves no gate.

What it measures, all from sources ALREADY COMMITTED to the repo:

* **the plant -> dam linkage** (ORNL HILARRI v4): how much of NYISO's hydro fleet
  carries a National Inventory of Dams id, which is the join key to the per-dam
  storage volumes a pondage duration would be derived from;
* **the operating-mode census** (ORNL EHA FY2024 ``Operational`` sheet): the
  published per-plant ``Mode`` label, weighted by nameplate -- the evidence for
  whether the fleet's dominant plants shape on a sub-monthly horizon at all.

Reading these two sources for a CENSUS is **not** a re-test of ``hydro_ror_split``
(matrix cell **G**, governance-refused at nyiso-111) -- and the census in fact
CORROBORATES that refusal: Robert Moses Niagara's ``Mode`` is exactly the hybrid
``Run-of-river/Peaking`` label the refusal turned on. Neither that cell nor
``hydro_budget_nameplate_aware`` (**I**, nyiso-107) is re-opened.

ZERO LP. Keeper untouched. Charter:
``docs/CHARTER-nyiso219-hydro-budget-period-2026-09-07.md``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

HILARRI = REPO / "data" / "raw" / "hilarri" / "HILARRI_v4.csv"
EHA = REPO / "data" / "raw" / "ornl-eha" / "ORNL_EHAHydroPlant_PublicFY2024.xlsx"
OUT_JSON = REPO / "results" / "calibration" / "_nyiso219_pondage_feasibility_census.json"

# The two plants that carry 71.4 % of NYISO hydro MW (nyiso-219 M1). Named so the
# census reports their linkage explicitly rather than burying them in an average.
DOMINANT_PLANTS: tuple[int, ...] = (2693, 2694)


def _blank(series: pd.Series) -> pd.Series:
    """True where a text column is absent, empty or the literal string ``nan``."""
    text = series.astype(str).str.strip().str.lower()
    return series.isna() | text.isin({"", "nan", "none"})


def main() -> None:
    from market_sim.data.hydro import _load_hydro_nameplate

    nameplate = _load_hydro_nameplate("NYISO")
    fleet_mw = float(sum(nameplate.values()))

    def mw_share(plant_ids: set[int]) -> float:
        covered = sum(mw for pid, mw in nameplate.items() if pid in plant_ids)
        return round(100.0 * covered / fleet_mw, 2)

    # --- (a) plant -> dam linkage -------------------------------------------
    hil = pd.read_csv(HILARRI, low_memory=False)
    hil["eia_ptid"] = pd.to_numeric(hil["eia_ptid"], errors="coerce")
    hil = hil[hil.eia_ptid.isin(nameplate.keys())]
    linked = set(hil.eia_ptid.dropna().astype(int))
    with_nid = set(hil[~_blank(hil.nidid)].eia_ptid.dropna().astype(int))
    with_gage = set(hil[~_blank(hil.usgs_gage)].eia_ptid.dropna().astype(int))

    dominant = {}
    for pid in DOMINANT_PLANTS:
        row = hil[hil.eia_ptid == pid]
        if row.empty:
            continue
        rec = row.iloc[0]
        dominant[str(pid)] = {
            "dam_name": str(rec["dam_name"]),
            "nid_id": str(rec["nidid"]),
            "project_type": str(rec["prjct_type"]),
            "usgs_gage": None if _blank(row.usgs_gage).iloc[0] else str(rec["usgs_gage"]),
            "pct_fleet_mw": round(100.0 * nameplate[pid] / fleet_mw, 3),
        }

    # --- (b) operating-mode census ------------------------------------------
    eha = pd.read_excel(EHA, sheet_name="Operational")
    eha["EIA_PtID"] = pd.to_numeric(eha["EIA_PtID"], errors="coerce")
    eha = eha[eha.EIA_PtID.isin(nameplate.keys())].copy()
    eha["mw"] = eha.EIA_PtID.map(nameplate)
    modes = (
        eha.groupby(eha.Mode.fillna("(no Mode)"))
        .agg(mw=("mw", "sum"), n_plants=("EIA_PtID", "nunique"))
        .sort_values("mw", ascending=False)
    )
    peaking = modes.index[modes.index.str.contains("Peaking", case=False, na=False)]

    record = {
        "session": "nyiso-219",
        "charter": "docs/CHARTER-nyiso219-hydro-budget-period-2026-09-07.md",
        "post_hoc": True,
        "pre_registered": False,
        "moves_no_gate": True,
        "zero_lp": True,
        "fleet": {"n_plants": len(nameplate), "nameplate_mw": round(fleet_mw, 1)},
        "a_plant_dam_linkage": {
            "source": "data/raw/hilarri/HILARRI_v4.csv (ORNL HILARRI v4)",
            "plants_with_hilarri_row": len(linked),
            "pct_fleet_mw_linked": mw_share(linked),
            "plants_with_nid_dam_id": len(with_nid),
            "pct_fleet_mw_with_nid": mw_share(with_nid),
            "plants_with_usgs_gage": len(with_gage),
            "pct_fleet_mw_with_gage": mw_share(with_gage),
            "dominant_plants": dominant,
        },
        "b_operating_modes": {
            "source": "data/raw/ornl-eha/ORNL_EHAHydroPlant_PublicFY2024.xlsx (Operational)",
            "plants_matched": int(eha.EIA_PtID.nunique()),
            "pct_fleet_mw_with_peaking_component": round(
                100.0 * float(modes.loc[peaking, "mw"].sum()) / fleet_mw, 2
            ),
            "modes": [
                {
                    "mode": str(idx),
                    "mw": round(float(row.mw), 1),
                    "n_plants": int(row.n_plants),
                    "pct_fleet_mw": round(100.0 * float(row.mw) / fleet_mw, 3),
                }
                for idx, row in modes.iterrows()
            ],
        },
        "c_missing": {
            "storage_volume": "NOT in repo — USACE National Inventory of Dams, "
            "joinable on the NID ids above; a bounded data-intake job.",
            "head": "in none of EHA / HILARRI / NID; FERC licence documents carry it. "
            "NID dam height is a PROXY, not head, and must not be substituted silently.",
            "licensed_operating_range": "OPEN — NID 'normal storage' is a reservoir "
            "volume, not the licensed operating range; using it literally would "
            "OVERSTATE pondage (making the mechanism too weak, not too strong).",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
