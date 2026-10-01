# FF-0F — FC-5 external-corridor benchmark intake (2026-07)

**Session.** FF-0F of `docs/forecast-development-plan-2026-07.md` (Wave 0 follow-on,
L-INP/L-VAL seam). **Data-prep only — no LP solved, nothing registered on any
dashboard, no holdout year touched (rule 22).** Delivers the `benchmark-corridor`
clean datatype the FC-5 external-corridor check needs (forecast determination
rubric `docs/forecast-determination-rubric.md` §2 FC-5 / §6), wires
`scripts/forecast_verdict.py`'s FC-5 category to read it as **context only**, and
files the remaining source gaps as intake rows.

**Context, never a fit target (CLAUDE.md rule 13).** Nothing in the model is tuned
toward a value in this table. FC-5 gates the *explanation* of a model-vs-benchmark
divergence (the `cross-model-corridor-2026-07-13.md` discipline — "divergence is
not failure; unexplained divergence is"), never its size. Every committed value is
a real primary-source number (rule 5); a source not yet retrievable is a
`DATA NEEDED` row, never a guess.

---

## 1. What landed

| Deliverable | Path |
|---|---|
| Schema (the contract) | `data/dictionary/schema/benchmark-corridor.schema.yaml` |
| Registry + per-source modules | `scripts/lib/benchmark_corridor/{__init__,aeo,stdscen,iso_planning}.py` |
| AEO fetch CLI | `scripts/data/fetch_aeo_electricity.py` |
| Curate script (+ `--emit-corridor-json`) | `scripts/data/curate_benchmark_corridor.py` |
| Loader (model/scorer seam) | `src/market_sim/data/benchmark_corridor.py` |
| Raw home + README + template | `data/raw/benchmark-corridor/` |
| Fetched data (gitignored, regenerates via the fetcher) | `data/raw/benchmark-corridor/aeo2025/aeo2025_electricity_corridor.csv` (1,008 rows → 1,008 clean) |
| FC-5 scorer wiring | `scripts/forecast_verdict.py` (`--benchmark-corridor`, `score_fc5`) |
| Tests | `tests/test_curate_benchmark_corridor.py` (13, trivial-first, tmp CLEAN_DIR) |
| Registration | `scripts/regenerate_clean.py` `DATATYPES`; `scripts/render_data_dictionary.py` (`DATATYPE_ORDER` + narrative — the dictionary's source of truth; the committed `data-dictionary.md` snapshot is deferred to a clean render, see §5 note 2) |

The datatype is one tidy (long) frame, key `(source, iso, region, scenario,
target_year, quantity, tech)`, written as ONE combined clean partition (rubric §6
"FC-5 reads one parquet"). `quantity ∈ {capacity, generation, co2}`; `tech` is a
canonical union covering AEO's granularity and the ISO-document/model granularity.

## 2. Source status (rubric §6)

| # | Source id | Status | How it lands |
|---|---|---|---|
| 1 | `AEO2025` | **ON DISK (fetched)** | EIA AEO2025 Table 54 + Table 56 via the API v2 `aeo` route |
| 2 | `StdScen2024` | DATA NEEDED (M9) | NREL Scenario Viewer CSV export (API proxy-blocked) |
| 3 | `ERCOT_CDR_2025` | DATA NEEDED (M10) | ERCOT CDR Dec 2025 (PDF) |
| 4 | `PJM_LOAD_2026` | DATA NEEDED (M11) | PJM 2026 Load Forecast + 4R (PDF/XLSX) |
| 5 | `NYISO_GOLDBOOK_2026` | DATA NEEDED (M12) | NYISO 2026 Gold Book (XLSX) |
| 6 | `ISONE_CELT_2026` | DATA NEEDED (M13) | ISO-NE 2026 CELT (XLSX/PDF) |
| 7 | `CAISO_IEPR_2025` | DATA NEEDED (M14) | CEC IEPR 2025 + CPUC PSP/TPP (XLSX/PDF) |
| 8 | `MISO_FUTURES` | DATA NEEDED (M15) | MISO Futures / OMS survey (PDF) |

Gaps filed as intake rows in `docs/handoffs/ff-inputs-currency-audit-2026-07.md`
§6 (concrete inventory) + §7.3 (M9–M15). The intake is **self-enforcing**: each
registered-but-absent source is reported `missing`, the FC-5 scorer surfaces the
list, and FC-5 SKIPs-with-context (holding any T2 promotion) until it lands
(rubric §3/§6). A manual source lands with **no code change** — drop its unified
CSV (canonical columns, from `data/raw/benchmark-corridor/_TEMPLATE.csv`) into
`data/raw/benchmark-corridor/<subdir>/<subdir>.csv` and re-run curate.

## 3. AEO2025 — the reproducible source

Pulled from the EIA Open Data API v2 `aeo` route (the same route as
`scripts/data/fetch_eia_aeo.py`, which pulls fuel prices — this is the
capacity/generation/emissions extension rubric §6 called for):

- **Table 54** (API `tableId=62`, "Electric Power Projections by Electricity
  Market Module Region") — capacity by fuel, generation by fuel, power-sector CO2.
- **Table 56** (API `tableId=67`, "Renewable Energy Generation by Fuel") — the
  renewable **capacity** split (solar PV/thermal, on/offshore wind, geothermal,
  hydro, biomass, municipal waste) the Table-54 "Renewable Sources" aggregate lacks.

Reference case, target years 2030/2035/2040, the 14 EMM regions crosswalked to the
six ISOs. **1,008 curated rows** (capacity 15 techs, generation 6, CO2 total ×
regions × years). Every value verbatim from the API; the parser maps by the AEO
series **name** and **asserts the native API unit** (fail-loud on an AEO
label/unit change — no silent guess).

Units recorded as the source publishes: capacity **GW**, generation **TWh** (AEO
"BkWh" billion-kWh ≡ TWh, a label change with no numeric conversion), CO2 **MMst_co2**
(million short tons). Sanity anchors (Reference, 2030): ERCOT power CO2 99.8 MMst,
PJM 256, MISO 239 — consistent with the corridor memo's "AEO2025 power CO2 falls
steeply" narrative and PJM's near-total coal exit by 2035 (PJM coal ≈ 0.6 GW).

### Boundary caveat (rule 11 — real data, misalignment documented)

AEO's EMM regions **approximate but do not equal** the ISO/RTO footprints. Every
AEO row carries this in `note`, and `iso` is the ISO an EMM region crosswalks to
(`AEO_EMM_TO_ISO` in `scripts/lib/benchmark_corridor/aeo.py`): ERCOT←TRE;
PJM←{East, West, ComEd, Dominion}; MISO←{West, Central, East, South};
NYISO←{NYC+LI, Upstate}; NEISO←NPCC/New England; CAISO←{CA North, CA South}. An
ISO total is the **sum over its region rows** (`iso_totals()` — capacity /
generation / CO2 are extensive). This is FC-5 context; no ISO-exact number was
guessed to force the EMM footprint onto the market footprint.

**Documented limitation:** the AEO regional tables publish **generation** only at
the renewable *aggregate* grain (no per-renewable-fuel TWh regionally), so the
energy-mix rows are coal/gas/nuclear/oil/renewables/total; the renewable split is
capacity-only (Table 56).

## 4. FC-5 scorer wiring (context only)

`scripts/forecast_verdict.py` gains a `--benchmark-corridor <json>` input (the
committed anchor table, emitted by `curate_benchmark_corridor.py
--emit-corridor-json`). `score_fc5` reads it as **CONTEXT**:

- Anchor rows carry **no `verdict`** — they are external values, never a proximity
  target. The scorer never computes a divergence from them.
- What FC-5 **gates** is unchanged: the per-row *disposition* authored by the
  scoring session on the `--corridor` table — `UNEXPLAINED ⇒ FAIL`,
  `EXPLAINED DIVERGENCE ⇒ CAVEAT`, `IN CORRIDOR ⇒ PASS` (rubric §2 FC-5). All four
  pre-existing FC-5 tests still pass.
- **Anchors present, no disposition authored ⇒ SKIPPED-with-context** (holds a T2
  promotion per §3), listing sources/years/missing-sources — never a FAIL from the
  context itself. This is the "read it as CONTEXT ONLY — a divergence is reported
  with an explanation, NEVER scored as a miss" contract.

Data flow for a scoring session: `curate_benchmark_corridor.py` (raw→clean, from
committed raw) → `--emit-corridor-json` (the committed anchor table) → author the
`--corridor` disposition against the model snapshots → `forecast_verdict.py --tier
t2 --benchmark-corridor <anchors> --corridor <dispositions>`. The clean parquet is
gitignored but regenerates deterministically from committed raw, so the scorer's
committed-artifacts contract (rubric §0) holds.

## 5. Rule compliance & scope

- **Rule 5 (no guessed numbers).** Only AEO2025 landed — verbatim API values
  with per-value provenance (`source_doc` = the API route + tables; `source_page` =
  the exact series id). The fetched raw CSV is **gitignored and regenerated by the
  deterministic fetcher** (`scripts/data/fetch_aeo_electricity.py`; pjm-energy-offers
  precedent): the fetcher pulls values verbatim, so it — not a hand-reproduced
  1,008-row copy that could fat-finger a value — is the reproducible, rule-5-safe
  committed source. Every unretrievable source is a `DATA NEEDED` row, not a
  placeholder value; `value` is non-nullable, so the clean table has no placeholder
  rows. Regenerate the clean tree with `python scripts/data/fetch_aeo_electricity.py &&
  python scripts/data/curate_benchmark_corridor.py` (needs a free EIA API key).
- **Rule 13 (context, never a fit target).** Enforced in the schema header, the
  loader, and `score_fc5`; a divergence is only ever reported via an authored
  explanation. No model parameter references this table.
- **Rule 22 (quarantine).** No solve, no scoring, no holdout contact. All target
  years are forward (2030/2035/2040); no measured 2019/2022/H1-2026 actual is
  intaken or referenced as a benchmark.
- **Rules 12/19/25 (registry/ISO-agnostic).** Per-source parsing registers in the
  shared registry; no `if source ==` ladder in shared code; AEO's EMM→ISO crosswalk
  and series map live in the AEO module only.
- **Scope.** Imported none of the truncated `capacity.py`; did not touch
  `capacity.py`, `constants.py`, `scenarios.py`, `policy/*`, or `runner.py`. Tests
  are scoped to the new loader/schema (trivial-first, tmp CLEAN_DIR); no dispatch/
  forecast/hindcast solve or `check_forecast_invariants` was run.

### Two notes for the reviewer

1. **`parameter-citations.md` not hand-edited (deliberate).** That file is
   auto-generated from `frontend/data/parameters.json` by
   `scripts/generate_parameter_registry.py` and is scoped to `constants.py` /
   `ScenarioConfig` defaults ("edit citations in the JSON… not here"). This intake
   adds **no** config parameter (constants/scenarios are frozen for this session),
   so it registers nothing there. The benchmark values' primary-source citations
   live in the data contract itself — the `source_doc` / `source_page` columns of
   every row — plus the schema header, the raw README, and §3 above, which
   collectively satisfy rule 5 more rigorously than a hand-edit the generator would
   overwrite.
2. **`data-dictionary.md` snapshot deferred to a clean render (rule 27 + scope).**
   `benchmark-corridor` is registered in `scripts/render_data_dictionary.py`
   (`DATATYPE_ORDER` + narrative) — the dictionary's **source of truth** — so it
   renders into the doc on the next `python scripts/render_data_dictionary.py`. The
   committed `data-dictionary.md` was deliberately **not** regenerated here: a full
   render in this checkout reverts two other in-flight lanes' committed narrative
   (the 2026-07-17 unit-grain `outages` text and the NYISO
   `capacity-market-demand-curve` `icap_ucap_translation_factor`/`fraction` rows,
   whose schema/narrative updates are not in this checkout — out of scope to touch),
   and hand-transcribing the 1,630-line **generated** file is the large-file
   full-content rewrite CLAUDE.md rule 27 exists to prevent. Consequence: with the
   renderer now listing `benchmark-corridor`,
   `test_data_dictionary_sync.py::test_coverage_matrix_lists_every_datatype` reports
   it *pending* until that regeneration — the **same class** as the pre-existing
   `dam-public-bids` gap (`test_every_schema_has_a_section`, already red on
   `origin/main`) and the `outages`/`capacity-market` per-column drift. All clear
   together in **one** cross-lane `render_data_dictionary.py` reconciliation (a
   dictionary pass, not a `benchmark-corridor` data-prep change).

## 6. What this session did / did not do

- **Did:** created the `benchmark-corridor` datatype end-to-end (schema → registry
  → fetch → curate → loader → FC-5 wiring → tests → dictionary registration); fetched AEO2025
  Tables 54+56 (1,008 rows); wired FC-5 as context-only; filed the 7 manual-download
  gaps (M9–M15) and rewrote FF-0D §6.
- **Did not:** solve any LP; register anything on any dashboard; touch any
  parameter/threshold/curve; intake or reference any 2019/2022/H1-2026 actual;
  edit `capacity.py`/`constants.py`/`scenarios.py`/`policy/*`/`runner.py`.

*Produced 2026-07-18 (FF-0F, Opus, data-prep). External source fetched: EIA AEO2025
via Open Data API v2. Feeds FC-5 scoring at T2/T3 (FF-2D onward).*
