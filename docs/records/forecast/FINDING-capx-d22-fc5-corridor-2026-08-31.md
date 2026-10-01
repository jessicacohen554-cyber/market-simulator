# FINDING — D22: the FC-5 benchmark corridor tables now exist on disk (2026-08-31)

**Session.** D22 of the capacity-expansion (Forecast Finalization) track. **Data
contract + intake only — no LP solved, no mechanism, no `ScenarioConfig` field,
no matrix cell, no verdict file, no board block, no keeper/shard/marker, nothing
in the backcast namespace, no holdout year touched (rule 22).** The FC-5 read
path in `scripts/forecast_verdict.py` was **not edited** (out of scope by
charter; lane D8-V is re-scoring through that file byte-for-byte in this batch).

**Context, never a fit target (rule 13 `[R-MEASURED]`, plan §7.6, rubric §FC-5
rationale).** Nothing intaken here may become a target any model quantity is
moved toward. The rubric deliberately makes FC-5 conformance non-numeric: what
gates is the **explanation** discipline of
`docs/handoffs/cross-model-corridor-2026-07-13.md` ("divergence is not failure;
unexplained divergence is"), never closeness. No numeric conformance band was
added, no ISO is ranked by corridor distance, and ReEDS' practice of adjusting
cost coefficients until generation matches history — explicitly rejected by the
rubric's methodology section — was not imported.

---

## 1. The headline

FC-5 scored `SKIPPED` for every ISO with *"no committed benchmark-corridor
table"*. It no longer does: **1,025 committed anchor rows from 3 sources**, and
the scorer reads 72–294 anchors per ISO as CONTEXT.

| | before D22 | after D22 |
|---|---|---|
| Committed artifacts in the raw→clean→scorer chain | **none** | raw CSVs + anchor JSON |
| Corridor rows | 0 on disk | **1,025** |
| Sources landed | 0 | **3 of 8** (AEO2025, ERCOT_CDR_2025, PJM_LOAD_2026) |
| Missing-source list | 8 | **5** |
| FC-5 detail string | "no committed benchmark-corridor table" | "N external anchors present as CONTEXT" |

FC-5 still reports `SKIPPED` — **correctly, and by design**. Anchors alone are
context; what FC-5 gates is the per-row *disposition* (`IN CORRIDOR` /
`EXPLAINED DIVERGENCE` / `UNEXPLAINED`) authored by a scoring session against
model snapshots on the separate `--corridor` table. Landing the anchors changes
`SKIPPED`-because-nothing-exists into `SKIPPED`-with-context, which is the state
the rubric intends until dispositions are written. That wiring is its own charter.

## 2. Root cause: why the tables did not exist

FF-0F (`docs/handoffs/ff-0f-fc5-benchmark-intake-2026-07.md`) built the entire
machinery — schema, registry, per-source modules, fetcher, curate script, loader,
FC-5 scorer wiring, 13 tests — and fetched 1,008 AEO rows. **The defect was not
missing code; it was that nothing was committed.**

`data/raw/benchmark-corridor/.gitignore` ignored `aeo2025/`, on the reasoning
that the deterministic fetcher (not a hand-reproduced copy that could fat-finger
a value) is the rule-5-safe source. But repo `.gitignore` §5 also ignores
`data/clean/`. With **both ends of the chain ignored, no artifact was committed
at all**, so the rubric §0 committed-artifacts contract could not hold and FC-5
had nothing to read. FF-0F §4's claim that "the clean parquet is gitignored but
regenerates deterministically from **committed raw**" — and the loader
docstring's identical claim — were false: there was no committed raw.

Two further facts made the ignore strictly counterproductive:

1. **The file is small.** 1,009 lines / 172 KB — four orders of magnitude below
   the "large fetched corpora (`pjm-energy-offers`)" precedent cited for it.
2. **It needed a key to regenerate.** The fetch requires an EIA API key, and no
   `.env` exists in a fresh session. So ignoring the output made the scoring
   input *less* reproducible, not more.

**Fix:** commit the raw CSV, sha-pinned (`SHA256SUMS.txt`). Curation now runs
offline from committed raw, which is what the loader already claimed.

## 3. The AEO fetch is now key-free (and independently verified)

`fetch_raw` issued **28 keyed requests** (14 EMM regions × 2 tables), which
exceeds the public `DEMO_KEY` budget of ~30/hour — so without a registered key
the fetch could not complete, and the "regenerate it yourself" recovery route
did not actually work.

Dropping the `regionId` facet returns **every EMM region in one response**, so
the fetch is now **6 requests** (2 tables × 3 years) and completes on `DEMO_KEY`.
The facet only filters server-side, so values are identical. The fetcher also
now **refuses a truncated response**: the API silently caps JSON at 5,000 rows,
which would drop regions or series with no error (rule 5).

**Verified equivalent by re-fetch.** The rebuilt table reproduces FF-0F's
published anchors exactly:

| anchor | FF-0F (2026-07, 28-request fetch) | D22 (6-request fetch) |
|---|---|---|
| rows | 1,008 | **1,008** |
| 2030 power CO2, ERCOT | 99.8 MMst | **99.8** |
| 2030 power CO2, PJM | 256 MMst | **256.0** |
| 2030 power CO2, MISO | 239 MMst | **239.1** |
| 2035 coal capacity, PJM | ≈0.6 GW | **0.58** |

## 4. Per-source coverage record (rubric §6's eight)

**IN — 3 of 8.**

| # | Source | Rows | Years | What landed |
|---|---|---|---|---|
| 1 | `AEO2025` | 1,008 | 2030/35/40 | capacity by fuel (714), generation by fuel (252), power-sector CO2 (42), across 14 EMM regions → 6 ISOs |
| 3 | `ERCOT_CDR_2025` | 11 | **2030 only** | firm peak load, total capacity, reserve margin, planned additions by tech (gas/wind/solar/storage) |
| 4 | `PJM_LOAD_2026` | 6 | 2030/35/40 | RTO summer peak load (Table B-1), annual net energy (Table E-1) |

Per-ISO anchor counts: PJM 294, MISO 288, CAISO 144, NYISO 144, ERCOT 83, NEISO 72.

**OUT — 5 of 8, with the reason each is out.** Reachability was re-probed this
session; none was merely skipped.

| # | Source | Status | Why |
|---|---|---|---|
| 2 | `StdScen2024` | **UNREACHABLE** | Every `nrel.gov` host is refused by the egress proxy with a **policy denial** (`connect_rejected`, 502 to CONNECT): `scenarioviewer.nrel.gov`, `data.nrel.gov`, `www.nrel.gov`. The OEDI S3 mirror carries **no** Standard Scenarios (`nrel-std-scenarios/` → `KeyCount=0`; the bucket's top-level prefixes are ATB, dgen, PR100, SMART-DS … with no ReEDS/StdScen). **No in-session route exists.** |
| 5 | `NYISO_GOLDBOOK_2026` | un-fetched | Host reachable (200); the document list is a JavaScript (Liferay) portal and no static file URL appears in the served HTML. |
| 6 | `ISONE_CELT_2026` | un-fetched | Host reachable (200); the CELT file list renders client-side (served HTML says "no results with this choice of filter(s)"). Asset paths are not guessable — and guessing is not an intake method. |
| 7 | `CAISO_IEPR_2025` | un-fetched | `efiling.energy.ca.gov` and `docs.cpuc.ca.gov` reachable (200); the forecast tables are proceeding attachments behind a docket-search UI, not a stable file URL. |
| 8 | `MISO_FUTURES` | un-fetched | `misoenergy.org` returns **403** to this session (bot filtering) on both the root and the MISO Futures page. |

**The distinction that matters for the director:** only `StdScen2024` is
*unreachable* (a proxy policy denial plus a genuinely absent mirror — no amount
of session effort will get it). The other four are *un-fetched*: their hosts
answer, and a session that can obtain the file (a human download, or a route
past the JS portal / 403) can land them with **no new code** — the fetcher takes
a new extractor, or the file drops in as a unified CSV.

## 5. What was built

| Deliverable | Path |
|---|---|
| Schema (extended, v1) | `data/dictionary/schema/benchmark-corridor.schema.yaml` |
| Dictionary entry | `data/dictionary/data-dictionary.md` (`## benchmark-corridor`) |
| Committed AEO raw + sha | `data/raw/benchmark-corridor/aeo2025/…csv`, `SHA256SUMS.txt` |
| ISO planning fetcher (new) | `scripts/data/fetch_iso_planning_benchmarks.py` |
| ERCOT CDR / PJM raw + sha | `data/raw/benchmark-corridor/{ercot-cdr-2025,pjm-load-2026}/` |
| **The committed FC-5 anchor table** | **`results/ff-corridor/benchmark-corridor-anchors.json`** |
| Contract + loader | `scripts/lib/benchmark_corridor/`, `src/market_sim/data/benchmark_corridor.py` |
| Tests | `tests/curation/test_curate_benchmark_corridor.py` (13 → **18**) |

The anchor table lives in `results/ff-*/`, a forecast-validation namespace named
by rubric §0 — never the backcast registry.

### 5.1 Contract extension: the ISO planning quantities

`QUANTITY_VOCAB` was `{capacity, generation, co2}` — outlook-style quantities. But
**an ISO load forecast publishes peak MW and annual GWh, not a capacity mix**, so
under the old vocabulary most of §6's ISO sources had *nothing they could legally
land as* (the vocab guard is fail-loud). Added: `peak_demand`, `energy_demand`,
`reserve_margin`.

`reserve_margin` is a **ratio**, so a new `INTENSIVE_QUANTITIES` marks it and
`iso_totals()` now **raises** rather than summing it across regions — two regions
at 0.15 are not 0.30. Extensive quantities aggregate as before; a single-region
intensive row passes through unchanged.

### 5.2 Values are machine-extracted, never typed

The raw README's original path for a manual source was "transcribe its
primary-source table into `<subdir>/<subdir>.csv`". For hundreds of cells that is
precisely the rule-5 fat-finger hazard that kept AEO on a deterministic fetcher.
`fetch_iso_planning_benchmarks.py` instead downloads the published workbook and
reads the named sheet/row/column, emitting the canonical unified CSV the generic
reader already parses — with each row's exact locator (sheet + row label + column
header) stamped into `source_page`. It fails loud if a layout changes rather than
extracting the wrong cell.

The extraction is self-verifying where the source permits: the CDR's own
identity holds on the extracted values — (115,501 − 132,240)/132,240 = **−0.1266**,
the published 2030 reserve margin.

### 5.3 Basis caveat recorded, not silently mixed (rule 11)

The CDR's wind/solar/storage capacities are the **peak-hour contribution**
(ELCC/seasonal-derated), **not** the nameplate GW AEO reports. They are therefore
not directly comparable without reconciliation. This rides in every CDR row's
`note`, in the raw README, and here — rather than being quietly stacked into the
same `capacity` column as if the bases matched. Likewise the CDR horizon ends at
Summer 2030, so it anchors 2030 **only**; no value was extrapolated to 2035/2040.

Per the charter, where a source is retrievable only at a coarser grain than the
model's ISO regions, **the limitation is recorded rather than downscaled** — an
invented regional split would be a fabricated benchmark. AEO's EMM→ISO crosswalk
carries that caveat in every row's `note` (inherited from FF-0F); PJM's rows are
an RTO total, labelled as such.

## 6. What FC-5 will be able to score once its read path is wired

The scorer already accepts `--benchmark-corridor`; it needs no change to consume
this table (verified by calling `score_fc5` directly against the committed JSON —
read-only, no edit). Once a scoring session authors dispositions, FC-5 can
confront the model against:

- **Capacity mix** by fuel at 2030/2035/2040, all six ISOs (AEO2025) — the
  headline capacity-expansion corridor: coal exit path, gas CC/CT build,
  renewable and storage build.
- **Energy mix** at coal/gas/nuclear/oil/renewables/total, all six ISOs (AEO2025).
  *Documented limit: AEO's regional tables publish generation only at the
  renewable aggregate grain, so the per-renewable-fuel split is capacity-only.*
- **Power-sector CO2** at all three years, all six ISOs (AEO2025) — the FC-5 row
  most directly comparable to the model's own CO2 trajectory.
- **Load trajectory** — PJM RTO summer peak and annual net energy at all three
  years; ERCOT firm peak at 2030. This is the anchor for the demand-growth
  divergence that dominates current capacity-expansion disagreement.
- **Adequacy** — ERCOT's own 2030 reserve margin and planned-additions-by-tech.

**Not yet scoreable:** NEISO, NYISO, MISO and CAISO have **only** the AEO
outlook — no ISO-planning second opinion, so a divergence there cannot be
triangulated against the ISO's own view. That is the strongest argument for
landing sources 5–8, and it is a coverage gap, not a defect.

## 7. Verification & rule compliance

- **Tests.** `tests/curation/test_curate_benchmark_corridor.py` 13 → **18 pass**
  (added: the three new quantities in vocab; a unified CSV carrying peak+energy;
  `iso_totals` sums extensive; `iso_totals` **raises** on multi-region
  `reserve_margin`; single-region passthrough). One pre-existing test asserting
  "only AEO is fetchable" was updated — it encoded a fact this session changed.
- **Regression.** `tests/curation` (5 failures) and `tests/scoring` (6 failures)
  were run; **every failure reproduces on a clean stashed tree** — 4
  `test_curate_reference` + 5 `test_ff_readiness_battery` + 1
  `test_forecast_parity` (unhydrated data / keeper bundles absent under
  `DATA PROFILE: code`) and 1 `test_data_dictionary_sync` subfailure for
  `capacity-market-demand-curve` (another lane's drift). **None is attributable
  to this change.** The `benchmark-corridor` dictionary subfailure my schema edit
  introduced was fixed by regenerating **only** that datatype's column table
  (2-line diff), leaving the other lane's stale section untouched.
- **Rule 5 / 23.** Every value is a primary-source number with `source_doc` +
  `source_page`; every fetched artifact is sha-pinned. No source not yet
  retrievable is represented by a placeholder — `value` is non-nullable and the
  absent sources are a machine-readable `missing_sources` list.
- **Rule 13.** No conformance band, no distance ranking, no tuning. Anchor rows
  carry **no** `verdict` by construction.
- **Rule 27.** Every pushed file ≥300 lines was blob-verified against the remote
  (anchors JSON 12,320 lines; fetcher 382; loader 185; tests 321; registry 280;
  dictionary 1,984; AEO raw 1,009; `aeo.py` 494) — all byte-identical.
- **No new GitHub Actions workflow**; both fetches ran in-session.
- **Rule 28 not triggered** — no solve-affecting mechanism, so no matrix cell.

## 8. Open items for the director

1. **`StdScen2024` is unreachable from a Claude session, not un-fetched.** If the
   corridor needs a second *outlook* (as opposed to ISO planning) opinion, it
   requires either an egress-policy change for `nrel.gov` or an out-of-session
   download. Everything else in §6 is obtainable.
2. **Four ISOs have no ISO-planning benchmark** (NEISO, NYISO, MISO, CAISO). All
   four sources are behind a JS portal, a docket UI, or a 403 — none needs new
   code once the file is in hand.
3. **FC-5 remains `SKIPPED` until dispositions are authored.** That is the
   rubric's design, not an unfinished intake: anchors are context; the gate is
   the explanation. Wiring the disposition-authoring step is the next charter.
4. **The `capacity-market-demand-curve` dictionary drift is still open** —
   pre-existing, another lane's, deliberately not touched here.

---

*Produced 2026-08-31 (D22, Opus, data contract + intake). External sources
fetched in-session: EIA AEO2025 via Open Data API v2; ERCOT CDR December 2025;
PJM 2026 Load Forecast Report. Feeds FC-5 scoring at T2/T3.*
