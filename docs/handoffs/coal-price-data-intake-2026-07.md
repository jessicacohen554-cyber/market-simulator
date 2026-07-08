# Coal price data intake — 2026-07-08

**Scope: collection + intake only.** No sigmoid re-derivation, no offer-curve
change, no re-solve, on any ISO. Every `COAL_SIGMOID_DEFAULTS` entry
(`src/market_sim/config/scenarios.py`) stays byte-identical (rule 23:
measured-behaviour parameters re-derive only when their source data updates,
and re-derivation itself — plus any resulting offer change — is a separate
per-ISO owner keeper decision, per the task's explicit instruction).

**Trigger:** issue #1347 / gap G-26 — the coal-vs-gas passthrough sigmoid
`floor`/`ceil`/`gas_mid`/`gas_slope` parameters are hand-tuned per (ISO,
supply) with no real coal commodity price behind them, and MISO's entries are
byte-copies of ERCOT's `gas_mid`/`gas_slope` (rule-24 wart — a curve tuned on
one ISO's residual is supposed to stay that ISO's, generic fallbacks carry
neutral bands, but MISO literally reuses ERCOT's `2.85`/`2.5`). This session
collects the free public-domain coal commodity data that a future
re-derivation needs, for **every** coal-producing region and **every** ISO's
coal fleet — not just MISO.

## (a) What was collected, coverage, cadence

Three raw sources, all free/public-domain, none S&P Global/Argus/McCloskey:

| Source | Route/series | Rows | Years | Cadence | Script |
|---|---|---|---|---|---|
| EIA Annual Coal Report | `coal/market-sales-price` (region x market-type CAP/OM/TOT, all ranks) | 2,781 | 2001–2024 | annual | `scripts/fetch_eia_coal_prices.py` |
| EIA Annual Coal Report | `coal/price-by-rank` (region x rank BIT/SUB/LIG/ANT/TOT) | 2,843 | 2001–2024 | annual | `scripts/fetch_eia_coal_prices.py` |
| BLS PPI | `WPU051` (commodity, national) + `PCU2121--2121--` (industry, national) | 394 | 2010–2026 | monthly | `scripts/fetch_bls_coal_ppi.py` |

Both EIA routes cover **every** EIA-published producing region: Appalachia
Central/Northern/Southern, Illinois Basin, Powder River Basin, Uinta Basin,
every individual coal-producing state (TX, ND, LA, MS, MT, WV split
Northern/Southern, KY split East/West, ...), and every U.S. Census Bureau
division aggregate EIA groups non-dedicated states under (verified: every
aggregate used by the crosswalk below — APP, ENC, ESC, WNC, WSC — carries its
own rank-level rows for the years used). All three regenerate automatically
each publication cycle by re-running the fetch scripts — both are free API
pulls with no manual step (a repo-committed rate-limited `EIA_API_KEY` is
already in `.env` per the existing `fetch-eia-gas-prices.yml` convention; BLS
needs no key at all).

Curated into two new schema-validated datatypes (`data/dictionary/schema/
coal-basin-price.schema.yaml`, `coal-mining-ppi.schema.yaml`) via
`scripts/curate_coal_basin_price.py` / `scripts/curate_coal_mining_ppi.py`,
both through the `write_clean` seam. Both registered in
`scripts/regenerate_clean.py`'s `DATATYPES` tuple and the rendered data
dictionary.

**Item 4 (optional, pre-2023 legacy weekly spot archive) — checked, confirmed
NOT free.** EIA's own current "Coal Markets" weekly report (the five-basin
daily/weekly spot series) was fetched and inspected directly: it is licensed
**"With permission, S&P Global"**; EIA's own page states the historical data
**"are proprietary" and "cannot be released by EIA."** Its archive
(`includes/archive2.cfm`) is the same S&P-sourced series at older vintages —
not a separate free source. This closes the item as a confirmed (not
assumed) gap; see `data/raw/coal-prices/SOURCES.md` for the full citation.

**Item 2 (EIA-923 Schedule 2 coverage confirmation) — no new fetch needed.**
The repo already carries EIA-923 delivered-fuel-cost data for coal plants in
every ISO with a coal fleet (ERCOT, PJM, MISO, NEISO; CAISO has one small
cogen); this session did not re-pull it (item 2 asked to confirm coverage,
not intake new data) and made no change to it.

## (b) Region -> coal-plant crosswalk, per ISO

`scripts/derive_coal_region_crosswalk.py` resolves every coal plant across
all six ISOs (via each plant's already-resolved `coal_supply_class` —
`market_sim.data.coal.coal_supply_class`, the same tag the passthrough
sigmoids key off) onto its EIA producing region, and writes
`data/raw/reference/coal_region_crosswalk.csv` (110 plants). Curated into the
existing `reference` datatype (`market=coal-region-crosswalk`) alongside
`plant-registry` / `bin-assignments`, via a new builder in
`scripts/curate_reference.py` — no new schema needed (the `reference`
datatype's `allow_additional_columns=true` design absorbs it).

Resolution logic (documented in the script's docstring, no fitting — every
rule is a physical/contract fact):

1. `prb` / `subbituminous` supply tag → region **PRB** always, regardless of
   the plant's own state (PRB-by-rail delivery, per `coal.py`/`fuel.py`'s own
   docstrings).
2. `lignite` → the plant's own state (mine-mouth, never railed).
3. `bituminous` → the plant's own state if EIA publishes a dedicated code,
   else its Census-division aggregate (documented per-state table).
4. `waste` (culm/gob) → no EIA region — correctly unpriced; not a
   commodity-traded fuel, consistent with `fuel.py`'s existing `floor=1.0`.
5. Unresolved tag (CAISO's Argus Cogen — 50 MW, `coal_supply_class` returns
   empty at HEAD) → left unmatched with a documented note, not guessed.

Per-ISO / per-region plant counts:

| Region | ISO:count |
|---|---|
| PRB | ERCOT:6, MISO:38, PJM:2 |
| TX | ERCOT:3 |
| IL | MISO:5 |
| IN | MISO:8, PJM:3 |
| KY | MISO:1, PJM:3 |
| ND | MISO:3 |
| ENC (MI/WI aggregate) | MISO:2 |
| OH | PJM:7 |
| PA | PJM:3 |
| WV | PJM:8 |
| VA | PJM:3 |
| MD | PJM:1 |
| ESC (TN aggregate) | PJM:1 |
| APP (low-confidence NH proxy) | NEISO:1 |
| *(none — waste/unresolved)* | PJM:11 (waste), CAISO:1 (unresolved) |

**NYISO has zero coal plants** at HEAD (verified via `load_fleet_from_csv`) —
explicitly excluded, mirroring the `capacity-deliverability` datatype's
ERCOT-exclusion convention rather than inventing a placeholder row.

Two low-confidence rows are flagged (`confidence=low` column): NEISO's sole
coal plant (Merrimack, NH) has no coal-producing New England census division,
so it's proxied to Appalachia Total (the historical rail-delivery source for
Northeast utility bituminous); CAISO's Argus Cogen has no `coal_supply_class`
resolution at all at HEAD, so it is left region-unmatched rather than guessed.

## (c) Rule-23 freeze

Every `COAL_SIGMOID_DEFAULTS` entry in `config/scenarios.py` is unchanged.
This intake makes the region-keyed commodity data available; a future
re-derivation session decides, per ISO, whether/how to use it (rule 25: a
tuned multiplier stays that ISO's — this datatype is deliberately
region-keyed, not ISO-keyed, so a future re-derive can give each ISO its own
region-mapped fit off the shared `coal-basin-price` table instead of copying
another ISO's constants). The next natural trigger is the ACR-2025 vintage
(published ~8 months after 2025 year-end) or a new EIA-923 delivered-cost
vintage landing — either is a genuine source-data update, not a residual
chase.

## (d) Remaining gaps vs. the ideal daily per-region index

- **No daily/weekly resolution.** The ACR f.o.b.-mine price is annual; BLS
  PPI is monthly but national-only (no regional breakout — confirmed by
  probing candidate series ids, see `SOURCES.md`). The daily basin spot
  indices (PRB 8800, ILB, NAPP, CAPP, Uinta) remain S&P/Argus/McCloskey-only;
  no free substitute exists (confirmed against EIA's own current page, not
  assumed).
- **No sub-state basin granularity for WV/KY.** EIA does publish WV
  Northern/Southern and KY East/West splits, but this session's crosswalk
  uses the whole-state code for both — assigning individual PJM/MISO plants
  to the finer split needs county-level plant siting this session did not do.
  A future pass could tighten this with EIA-860 county data.
- **Two low-confidence region assignments** (NEISO Merrimack, CAISO Argus
  Cogen) — documented above, not resolved further this session (both are
  single-plant, sub-1% fleet cases; not worth deeper sourcing work per the
  same materiality logic CLAUDE.md rule 15 applies to forced-energy budgets).
- **f.o.b.-mine, not delivered.** ACR price excludes transportation — the
  existing EIA-923 delivered-cost data (already in the repo) is the
  delivered-cost complement; this collection doesn't merge the two (that
  merge, if wanted for the sigmoid's `floor`/`ceil` fit, is re-derivation
  work, out of scope here).

## Deliverable inventory

- Raw: `data/raw/coal-prices/{eia_coal_market_sales_price,eia_coal_price_by_rank,bls_coal_ppi}.csv` + `README.md` + `SOURCES.md`
- Raw: `data/raw/reference/coal_region_crosswalk.csv`
- Fetch scripts: `scripts/fetch_eia_coal_prices.py`, `scripts/fetch_bls_coal_ppi.py`
- Derive script: `scripts/derive_coal_region_crosswalk.py`
- Curate scripts: `scripts/curate_coal_basin_price.py`, `scripts/curate_coal_mining_ppi.py`; new builder in `scripts/curate_reference.py`
- Schemas: `data/dictionary/schema/coal-basin-price.schema.yaml`, `coal-mining-ppi.schema.yaml`
- Registered: `scripts/regenerate_clean.py` `DATATYPES`; `scripts/render_data_dictionary.py` `DATATYPE_ORDER`/`NARRATIVE`/`NATIONAL_SCOPE`; rendered `data/dictionary/data-dictionary.md`
- Tests: `tests/test_curate_coal_basin_price.py`, `tests/test_curate_coal_mining_ppi.py`, extended `tests/test_curate_reference.py` (new table fixture), `tests/test_clean_io.py` (DATATYPES sync — also fixed a pre-existing unrelated gap, `nyiso-renewable-curtailment` missing from the sync list)
- Licensing: `docs/data-licensing.md` §1 extended (BLS + coal-prices dir)
- `src/market_sim/config/paths.py`: new `COAL_PRICES_DIR` constant
