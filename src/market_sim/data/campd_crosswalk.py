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
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

EPA_CROSSWALK_CSV = (
    RAW_DATA_DIR / "reference" / "camd-eia-crosswalk" / "epa_eia_crosswalk.csv"
)
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
    return load_crosswalk(EPA_CROSSWALK_CSV, PUDL_SUBPLANT_PARQUET)


def load_crosswalk(epa_csv: Path, pudl_parquet: Path) -> pd.DataFrame:
    """The crosswalk of record read from explicit paths (a missing file is skipped).

    :func:`crosswalk_of_record` is this function on the canonical raw paths; a
    derive that takes a ``raw_root`` (tests point it at a fixture tree) calls
    it on that tree's paths instead.
    """
    frames = []
    if epa_csv.exists():
        epa = pd.read_csv(
            epa_csv,
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
    if pudl_parquet.exists():
        pudl = pd.read_parquet(pudl_parquet)
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
    out = pd.concat(frames, ignore_index=True).dropna(
        subset=["camd_plant", "eia_plant"]
    )
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


def camd_to_eia_plant(
    facility: np.ndarray,
    unit: np.ndarray,
    crosswalk: pd.DataFrame,
    remap: dict[tuple[int, str], int] | None = None,
) -> np.ndarray:
    """The EIA plant code of each CEMS ``(facility, unit)`` — the fleet's plant key.

    Resolution order, per unit:

    1. the operative hand table ``campd.CAMPD_UNIT_PLANT_REMAP`` (``remap``);
    2. the crosswalk of record at UNIT grain, when it is unanimous (EPA and
       PUDL name one EIA plant). When they disagree and one of them names the
       CAMD code itself, the shared code is kept, so an ambiguous unit is never
       moved (Tinker: EPA 2953, PUDL 63628, fleet 63628; CAMD 55248
       CT4-7: EPA 55248, PUDL 2847). Otherwise the unit falls through;
    3. the crosswalk at FACILITY grain, when every row of the facility names
       the same EIA plant;
    4. the CAMD facility id itself (the two registries share most codes).

    This is the identity the fleet's own CAMPD joins rest on. Applied in any
    derive that groups CEMS units into model plants, it stops a plant whose
    CEMS id differs from its EIA id (Hidalgo: CAMD 7762, EIA 55545; Arthur von
    Rosenberg: CAMD 3612 units CT01/CT02, EIA 7512) from silently missing the
    join (FINDING-ucmilp-fix2-floor-mindown-2026-10-10 section 7).
    """
    if remap is None:
        from market_sim.data.campd import CAMPD_UNIT_PLANT_REMAP as remap
    fac = np.asarray(facility, dtype=np.int64)
    uid = np.asarray(unit).astype(str)
    out = fac.copy()
    if crosswalk is not None and len(crosswalk):
        cw = crosswalk.dropna(subset=["camd_plant", "eia_plant"])
        unit_map: dict[tuple[int, str], int] = {}
        for (cp, cu), grp in cw.groupby(["camd_plant", "camd_unit"], sort=False):
            eias = set(grp["eia_plant"].astype(int))
            if len(eias) == 1:
                unit_map[(int(cp), str(cu).strip())] = eias.pop()
            elif int(cp) in eias:
                # The sources disagree and one names the shared code: keep it.
                unit_map[(int(cp), str(cu).strip())] = int(cp)
        fac_n = cw.groupby("camd_plant")["eia_plant"].nunique()
        fac_first = cw.groupby("camd_plant")["eia_plant"].first()
        fac_map = {
            int(cp): int(fac_first[cp]) for cp in fac_n.index[fac_n.to_numpy() == 1]
        }
        keys = pd.MultiIndex.from_arrays([fac, pd.Index(uid).str.strip()])
        pairs = (
            pd.Series(
                list(unit_map.values()),
                index=pd.MultiIndex.from_tuples(list(unit_map.keys())),
            )
            if unit_map
            else pd.Series(dtype="int64")
        )
        hit_u = (
            pairs.reindex(keys).to_numpy() if len(pairs) else np.full(fac.size, np.nan)
        )
        hit_f = (
            pd.Series(fac_map).reindex(fac).to_numpy()
            if fac_map
            else np.full(fac.size, np.nan)
        )
        out = np.where(
            ~pd.isna(hit_u), hit_u, np.where(~pd.isna(hit_f), hit_f, fac)
        ).astype(np.int64)
    for (rf, ru), target in remap.items():
        out[(fac == int(rf)) & (uid == str(ru))] = int(target)
    return out
