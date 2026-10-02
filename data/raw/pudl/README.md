# pudl — raw

PUDL (Catalyst Cooperative) tables taken as **raw inputs**, byte-for-byte as
published. W0 EIA-860 settlement (owner ruling R-2 / Q7, 2026-10-02): together
with EPA's CAMD-EIA crosswalk (`data/raw/reference/camd-eia-crosswalk/`) this is
the **CAMPD <-> EIA crosswalk of record**; `CAMPD_UNIT_PLANT_REMAP` keeps only
rows the crosswalk confirms or that carry a cited override
(`src/market_sim/data/campd_crosswalk.py`).

| File | Table | Fetched |
|---|---|---|
| `core_epa__assn_eia_epacamd_subplant_ids.parquet` | `core_epa__assn_eia_epacamd_subplant_ids` (45,175 rows: `plant_id_eia, plant_id_epa, subplant_id, unit_id_pudl, emissions_unit_id_epa, generator_id`) | 2026-10-02 from `https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/stable/` (object Last-Modified 2026-09-12) |

Checksums: `SHA256SUMS.txt`. Licence: PUDL data is CC-BY-4.0 (Catalyst
Cooperative; DOI 10.5281/zenodo.4127026); attribution in `docs/data-licensing.md`.

**Consumer:** the zero-LP crosswalk audit only (`campd_crosswalk.classify_remap_rows`,
`tests/unit/data/test_campd_crosswalk.py`). No curated `data/clean` datatype:
nothing on the solve path reads this file, so no schema/curation step is owed
until a consumer does (data-intake recipe steps 1, 3-6 then apply).

**Rule 23 freeze (E.9):** re-fetch only on a PUDL release that moves this table;
the commit cites the release.

DATA NEEDED: `core_eia860__scd_generators`, `core_eia860__scd_plants`,
`core_eia860__scd_ownership`, `core_epa__assn_eia_epacamd` (audit §F 5) — not
yet consumed; EPA NEEDS rev 11-28-2025 (§F 4) — the EPA URL returned 404 from
this container on 2026-10-02 and needs a manual download.
