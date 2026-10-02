"""CAMPD <-> EIA crosswalk of record (W0, owner ruling R-2 / Q7, audit §E.3).

The crosswalk of record for a CEMS facility/unit to its EIA-860 plant is the
union of the two published, maintained mappings already on disk:

* EPA's CAMD-EIA Power Sector Data Crosswalk
  (``data/raw/reference/camd-eia-crosswalk/epa_eia_crosswalk.csv``);
* PUDL's subplant association ``core_epa__assn_eia_epacamd_subplant_ids``
  (``data/raw/pudl/``), which resolves the CEMS facility splits the EPA file
  leaves as unmatched rows.

``campd.CAMPD_UNIT_PLANT_REMAP`` stays the operative hand table, but every row
must now be either CONFIRMED by the crosswalk of record or carried as a cited
OVERRIDE (:data:`CAMPD_REMAP_OVERRIDE_CITATIONS`) — hand remaps only as cited
overrides. :func:`classify_remap_rows` is that audit; it changes no solve.
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

EPA_CROSSWALK_CSV = RAW_DATA_DIR / "reference" / "camd-eia-crosswalk" / "epa_eia_crosswalk.csv"
PUDL_SUBPLANT_PARQUET = (
    RAW_DATA_DIR / "pudl" / "core_epa__assn_eia_epacamd_subplant_ids.parquet"
)

#: Hand remap rows the crosswalk of record does NOT confirm, each with the
#: record that justifies keeping it. Filled from the W0 audit
#: (docs/records/governance/closeout-2026-10/W0-census/crosswalk_remap_audit.json);
#: a row absent here and unconfirmed fails ``tests/unit/data/test_campd_crosswalk.py``.
_AES_REPOWER = (
    "AES repowered Alamitos (EIA 62115) / Huntington Beach (EIA 62116) with new "
    "CCGTs whose CEMS monitors kept filing under the legacy boiler ORIS codes "
    "315 / 335; neither crosswalk carries the new units (campd.py "
    "CAMPD_UNIT_PLANT_REMAP header; caiso lane)"
)
_WEST_RIVERSIDE = (
    "West Riverside (EIA 64020) CTs file CEMS under the Riverside ORIS 55641; "
    "absent from both crosswalks (FINDING-miso280-phase0-riverside-vlr-"
    "southgas-2026-09-28.md §1)"
)
CAMPD_REMAP_OVERRIDE_CITATIONS: dict[tuple[int, str], str] = {
    (315, "CT1"): _AES_REPOWER,
    (315, "CT2"): _AES_REPOWER,
    (335, "CT1"): _AES_REPOWER,
    (335, "CT2"): _AES_REPOWER,
    (55641, "CT-03"): _WEST_RIVERSIDE,
    (55641, "CT-04"): _WEST_RIVERSIDE,
}


@lru_cache(maxsize=1)
def crosswalk_of_record() -> pd.DataFrame:
    """``(camd_plant, camd_unit, eia_plant, source)`` rows from both crosswalks."""
    frames = []
    if EPA_CROSSWALK_CSV.exists():
        epa = pd.read_csv(
            EPA_CROSSWALK_CSV,
            usecols=["CAMD_PLANT_ID", "CAMD_UNIT_ID", "EIA_PLANT_ID"],
            encoding="utf-8-sig",
            dtype=str,
        )
        frames.append(
            pd.DataFrame(
                {
                    "camd_plant": pd.to_numeric(epa["CAMD_PLANT_ID"], errors="coerce"),
                    "camd_unit": epa["CAMD_UNIT_ID"].astype(str).str.strip(),
                    "eia_plant": pd.to_numeric(epa["EIA_PLANT_ID"], errors="coerce"),
                    "source": "epa",
                }
            )
        )
    if PUDL_SUBPLANT_PARQUET.exists():
        pudl = pd.read_parquet(PUDL_SUBPLANT_PARQUET)
        frames.append(
            pd.DataFrame(
                {
                    "camd_plant": pd.to_numeric(pudl["plant_id_epa"], errors="coerce"),
                    "camd_unit": pudl["emissions_unit_id_epa"].astype(str).str.strip(),
                    "eia_plant": pd.to_numeric(pudl["plant_id_eia"], errors="coerce"),
                    "source": "pudl",
                }
            )
        )
    if not frames:
        return pd.DataFrame(columns=["camd_plant", "camd_unit", "eia_plant", "source"])
    out = pd.concat(frames, ignore_index=True).dropna(subset=["camd_plant", "eia_plant"])
    out["camd_plant"] = out["camd_plant"].astype(int)
    out["eia_plant"] = out["eia_plant"].astype(int)
    return out.drop_duplicates().reset_index(drop=True)


def classify_remap_rows(
    remap: dict[tuple[int, str], int] | None = None,
) -> pd.DataFrame:
    """Classify each hand remap row against the crosswalk of record.

    Returns one row per remap entry: ``confirmed`` (a crosswalk maps the CEMS
    unit to the same EIA plant), ``contradicted`` (it maps it elsewhere only),
    or ``absent`` (no crosswalk row for the unit), with the sources that agree.
    """
    if remap is None:
        from market_sim.data.campd import CAMPD_UNIT_PLANT_REMAP as remap
    cw = crosswalk_of_record()
    rows = []
    for (plant, unit), target in sorted(remap.items()):
        hit = cw[(cw["camd_plant"] == int(plant)) & (cw["camd_unit"] == str(unit))]
        agree = sorted(set(hit.loc[hit["eia_plant"] == int(target), "source"]))
        if agree:
            status = "confirmed"
        elif hit.empty:
            status = "absent"
        else:
            status = "contradicted"
        rows.append(
            {
                "camd_plant": int(plant),
                "camd_unit": str(unit),
                "eia_plant": int(target),
                "status": status,
                "confirmed_by": ",".join(agree),
                "crosswalk_targets": ",".join(
                    str(t) for t in sorted(set(hit["eia_plant"]))
                ),
                "cited_override": (int(plant), str(unit))
                in CAMPD_REMAP_OVERRIDE_CITATIONS,
            }
        )
    return pd.DataFrame(rows)
