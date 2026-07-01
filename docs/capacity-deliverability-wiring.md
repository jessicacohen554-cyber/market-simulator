# Capacity-deliverability wiring (Wave 3)

Locational resource-adequacy mechanism wired behind the default-OFF
`ScenarioConfig.capacity_deliverability_limits` flag. Consumes the
`capacity-deliverability` clean datatype (PJM CETO/CETL, MISO LRR/LCR/CIL,
NYISO LCR/TSL, ISO-NE LSR/MCL, CAISO LCR/MIC) intaken in earlier waves.

This is a **structural mechanism** (repo rule #1): it makes the capacity
economics locational the way real RA markets are (a binding LCR/CETO prices
capacity where it is deliverable-short). It is **not** a backcast-fit lever and
is **never enabled in a keeper**. Preferring published limits over calibrated
scalars can move the backcast (rule #12); that is expected — keep the mechanism,
open a root-cause note, do not revert.

## Components added

- `src/market_sim/data/capacity_deliverability.py` — reader over
  `read_clean("capacity-deliverability")`. `requirement_by_area` /
  `import_limit_by_area` / `export_limit_by_area` return plain `{area: MW}`
  dicts (no Pydantic into the LP). Helpers: `resolve_delivery_year` (calendar
  year → the ISO's delivery-year label), `resolve_season` (MISO→`summer`, else
  `annual`), `area_types_by_area`. `NEISO` is translated to the `ISONE`
  partition; ERCOT / absent partitions return `{}` (graceful no-op).
- `src/market_sim/config/capacity_area_crosswalk.py` — per-ISO resolver
  registry (`_RESOLVERS`, no `if iso ==` ladder) mapping each ISO's capacity
  areas to `iso_configs` model zones. `AreaMapping.kind` ∈
  {leaf, component, seam, nested, aggregate, system, unmapped}; only
  contributing kinds (leaf/component/seam, exactly one zone) are summed by
  `aggregate_by_zone`, so nesting never double-counts. Documented granularity:
  - **PJM**: LDA→zone; MAAC ⊇ EMAAC+SWMAAC+central-PA and the sub-LDAs
    (PSEG/JCPL/BGE/ATSI-Cleveland/…) are excluded; DAY+DEOK sum into AEP_Ohio
    (partial — AEP/OVEC not filed separately); PJM_West_APS has no filed LDA.
  - **MISO**: 10 LRZs → 3 regions (North=LRZ 1/3/5, Central=2/4/6/7,
    South=8/9/10) summed; MISO subregional "North"/"South" supersets excluded;
    read at the summer peak.
  - **NYISO**: NYC(J)/LI(K) 1:1; G-J spans Capital/Hudson+Lower-Hudson+NYC
    (aggregate, excluded).
  - **ISO-NE**: NNE→North (Maine nested/excluded); SENE spans
    Central+Boston+Connecticut (aggregate, excluded — so no per-zone LSR
    resolves under the 4-zone model, logged).
  - **CAISO**: branch-group MIC → `WECC_import` seam; LCR local areas → the
    Path-15/26 hub by geography; boundary-straddling pockets (Stockton, Kern)
    left `unmapped`, never guessed.

## Wiring (all gated, default-off, byte-identical when off)

- **Part A — seam import limit** (`model/transmission.apply_deliverability_seam_limit`,
  called in `runner`): the summed per-area seam import_limit (CAISO MIC →
  WECC_import) replaces the calibrated simultaneous-import `InterfaceLimit`
  cap (structurally identified as the limit whose links all originate at the
  import node). Affects CAISO today; PJM/MISO/NYISO CETL/CIL are internal and
  feed Part B instead.
- **Part B — locational capacity gate** (`model/capacity.deliverability_headroom_by_zone`
  + `_zone_is_long`; wired into `apply_economic_retirements`,
  `apply_economic_new_entry`, and `model/storage.apply_storage_new_entry`):
  per-zone `headroom = deliverable_firm − requirement` (deliverable = accredited
  firm in-zone + crosswalked import_limit). In a **long** zone the marginal
  capacity payment collapses (RA saturated) — thermal retires more readily, new
  entry is not pulled forward, and storage capacity value is load-share-weighted
  toward **short** zones. `evolve_fleet` computes headroom once on the entering
  fleet and shares it across the screens.

## Tests

- `tests/test_capacity_area_crosswalk.py` — trivial 1:1 map, nesting/no-double-
  count, and the completeness invariant (every real clean AREA maps to a genuine
  zone or is `system`/`unmapped`), regenerating clean into a tmp CLEAN_DIR.
- `tests/test_capacity_deliverability_wiring.py` — trivial 1-area→1-zone reader,
  short/long headroom, `_zone_is_long` predicate, storage derate factor, seam
  override + no-op paths, and flag-off no-op.

## /sync-docs notes for Wave 3

Docs to reconcile once the approach is settled:

- **`model-methodology-spec.md`** — add a subsection under capacity evolution
  (§5) describing the locational deliverability gate and the seam-import
  override; note it is a gated, forecast-facing structural mechanism, off in
  keepers.
- **`CLAUDE.md`** — the "Capacity Evolution" and "Key Constraints" summaries may
  mention that capacity value is locational when
  `capacity_deliverability_limits` is on.
- **`docs/adding-new-data-types.md`** — the capacity-deliverability datatype now
  has a model consumer; the "Wiring into the model" section can cite this file
  as the worked example.
- **`docs/parameter-citations.md`** — the crosswalk mappings and the
  MIC/CETL/CIL → canonical-metric provenance are already cited in the schema
  header and raw READMEs; cross-link if a consolidated table is desired.
- **CHANGELOG** — add an entry: "Wire capacity-deliverability into the capacity
  screens behind `capacity_deliverability_limits` (default off)."
