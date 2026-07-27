# ORNL HILARRI v4 — Hydropower Infrastructure: LAkes, Reservoirs, and RIvers

Linkage table connecting U.S. hydropower plants (EHA `eha_ptid` / EIA
`eia_ptid`) to their dams (NID), reservoirs (GRanD / NHD waterbodies /
HydroLAKES / LAGOS) and river network features. Used by the
`hydro-plant-modes` curated datatype (caiso-126 RoR-split classifier intake)
for its Mode-NaN completion rule: the `dataset` field states whether a plant
is associated with an inventoried **reservoir** at all, and `prjct_type`
identifies **canal/conduit** projects — both categorical, no numeric
thresholds.

## Files

- `HILARRI_v4.csv` — the linkage table (one row per dam/plant/reservoir
  linkage; a plant can carry several rows).
- `HILARRI_v4_Field_Descriptions.csv` — column dictionary.
- `HILARRI_v4_Readme.txt` — ORNL's release notes.

## Source

- Landing page: https://hydrosource.ornl.gov/data/datasets/hilarri-v4/
- Direct files:
  https://hydrosource.s3.us-east-2.amazonaws.com/files/data/datasets/hilarri-v4/HILARRI_v4.csv
  https://hydrosource.s3.us-east-2.amazonaws.com/files/data/datasets/hilarri-v4/HILARRI_v4_Field_Descriptions.csv
  https://hydrosource.s3.us-east-2.amazonaws.com/files/data/datasets/hilarri-v4/HILARRI_v4_Readme.txt
- Citation: HILARRI: Hydropower Infrastructure - LAkes, Reservoirs, and
  RIvers, v4. Oak Ridge National Laboratory, HydroSource.

DATA NEEDED: none for the CAISO hydro-mode completion. NID storage volumes
(not carried by HILARRI, only NID ids) were deliberately NOT intaken: a
storage-per-MW threshold would be a free numeric parameter (CLAUDE.md rule 24
`[R-REGISTRY]` / rule 13 `[R-MEASURED]`), whereas the categorical
reservoir-association / canal-type / dam-ownership evidence is threshold-free.
