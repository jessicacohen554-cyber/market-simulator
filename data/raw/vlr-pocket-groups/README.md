# vlr-pocket-groups — raw home

Units named by an ISO's voltage-and-local-reliability (VLR) operating guides,
per load pocket and per outage-study group. Curated by
`scripts/data/curate_vlr_pocket_groups.py` into `data/clean/vlr-pocket-groups/<ISO>`
(schema `data/dictionary/schema/vlr-pocket-groups.schema.yaml`). Consumer:
`market_sim.data.vlr_pocket_groups`, read only when
`ScenarioConfig.vlr_pocket_commitment` is armed (the UC stage's pocket
commitment rows).

## Layout

- `<iso>/<iso>.csv` — one row per listed unit, hand-transcribed from the source
  PDF (the canonical columns minus `uc_family`, which the curate script derives
  from the EIA-860 prime mover and energy source).

## Sources (MISO)

- **MTEP15 VLR study**, filed as PUCT Docket 46416, Exhibit CWL-5 (in
  `https://interchange.puc.texas.gov/Documents/46416_65_921352.PDF`, fetched
  2026-10-15; sha256 prefix `9fb334af75f3df11`, 5,485,919 B). CWL-5 p.7 lists
  the op-guide VLR units by pocket (~10,850 MW). Scenario 1C (pp.12–13) takes
  each group out of service in the MTEP14 2024 summer-peak model and finds
  thermal / voltage violations for every group:
  - A (Amite South): Waterford 1, 2, 4; Little Gypsy 1, 2, 3
  - B (DSG): Ninemile 3, 4, 5; Michoud 2, 3
  - C (WOTAB): Nelson 4
  - D (WOTAB): Sabine 1, 2, 3
  - E (WOTAB): Sabine 4, 5
  - F (Western): Lewis Creek 1, 2
- **EIA-860** (`data/raw/eia-860/eia860_generator_operable.parquet`,
  `..._retired_and_canceled.parquet`): each unit's prime mover, energy source and
  retirement year (transcribed into the CSV; the PDF does not carry them).

Units listed at p.7 but in no Scenario-1C group (Union Carbide, Oxy, Cypress,
Frontier, San Jacinto: industrial cogens) are not transcribed: the
requirement is stated per group.

## DATA NEEDED

- The op guides' own unit counts / MW requirements (not published; CEII). The
  model reads the groups only; the count per group is a modelling rule
  (`constants.VLR_GROUP_MIN_COMMITTED_UNITS`, owner ruling 2026-10-15),
  never a value from this table.
- Op-guide revisions after MTEP15 (e.g. the SETEX op guide, Aug 2022): no public
  unit list.
  The guides are CEII on MISO's Reliability-Authority extranet (NDA); the SETEX
  guide exists only as HSPM in PUCT 56693 (ETI response TIEC 7-2). No public
  count, MW or unit list exists for any year 2019–2025
  (`docs/records/miso/FINDING-uc-miso-coverage-2026-10-25.md`).
