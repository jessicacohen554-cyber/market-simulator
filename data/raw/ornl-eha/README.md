# ORNL Existing Hydropower Assets (EHA) Plant Database, FY2024

Per-plant U.S. hydropower asset inventory from ORNL HydroSource — the
authoritative per-plant **operational mode** source (`Mode`: Run-of-river /
Canal/Conduit / Peaking / Intermediate Peaking / hybrids) keyed to the EIA
plant id (`EIA_PtID`), used by the `hydro-plant-modes` curated datatype
(caiso-126 RoR-split classifier intake).

## Files

- `ORNL_EHAHydroPlant_PublicFY2024.xlsx` — the public FY2024 plant database
  (sheets: Summary, Acronyms and Nomenclature, Field Descriptions,
  Operational). 2,273 plants; the `Operational` sheet is the data table.

## Source

- Landing page: https://hydrosource.ornl.gov/dataset/EHA2024
- Direct file:
  https://hydrosource.s3.us-east-2.amazonaws.com/files/data/datasets/EHA2024/ORNL_EHAHydroPlant_PublicFY2024.xlsx
- DOI: https://doi.org/10.21951/EHA_FY2024/2344934
- Citation: ORNL Existing Hydropower Assets (EHA) Plant Database, FY2024.
  Oak Ridge National Laboratory, HydroSource.

## Known coverage gap (why HILARRI is also intaken)

`Mode` is populated for only ~66 % of plants nationally; for the CISO
balancing authority it is NaN on 100 of 201 plants (4.66 of ~6.7 GW,
including every large reservoir plant). The FY2023 vintage carries the
IDENTICAL gap (checked 2026-07-27), so earlier vintages cannot complete it.
The documented completion rule for Mode-NaN plants lives in
`scripts/data/curate_hydro_plant_modes.py` (HILARRI reservoir association +
canal/conduit project type + dam ownership; every decision cited there).

DATA NEEDED: none for CAISO. Other ISOs' lanes must review the completion
rule against their own labeled subset before registering their BA.
