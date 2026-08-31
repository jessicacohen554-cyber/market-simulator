# benchmark-corridor (raw)

External forecast-corridor anchors for the **FC-5 external-corridor** context
check (`docs/forecast-determination-rubric.md` §2 FC-5 / §6). One immutable raw
subdirectory per external source; the curation script
(`scripts/curate_benchmark_corridor.py`) reconciles them onto the tidy schema
`data/dictionary/schema/benchmark-corridor.schema.yaml` and writes ONE combined
clean partition. Per-source parsing registers in
`scripts/lib/benchmark_corridor/<source>.py`.

**Context, never a fit target (CLAUDE.md rule 13).** Nothing in the model is
tuned toward a value here; FC-5 gates the *explanation* of a divergence, never
its size. And per rule 5 every committed value is a real primary-source number —
a source not yet retrievable is a `DATA NEEDED` row below, **never** a guessed
or placeholder value in the data.

## Layout

```
benchmark-corridor/
  aeo2025/       aeo2025_electricity_corridor.csv   ← FETCHED + COMMITTED (sha-pinned)
  SHA256SUMS.txt                                    ← identity record for the fetched raw
  stdscen2024/   stdscen2024.csv                    ← DATA NEEDED (manual)
  ercot-cdr-2025/      ercot-cdr-2025.csv           ← DATA NEEDED (manual)
  pjm-load-2026/       pjm-load-2026.csv            ← DATA NEEDED (manual)
  nyiso-goldbook-2026/ nyiso-goldbook-2026.csv      ← DATA NEEDED (manual)
  isone-celt-2026/     isone-celt-2026.csv          ← DATA NEEDED (manual)
  caiso-iepr-2025/     caiso-iepr-2025.csv          ← DATA NEEDED (manual)
  miso-futures/        miso-futures.csv             ← DATA NEEDED (manual)
```

Each manual `<source>.csv` has exactly the canonical columns (`source, iso,
region, vintage, scenario, target_year, quantity, tech, value, unit,
source_doc, source_page, note`); the generic reader
(`scripts.lib.benchmark_corridor.parse_unified_csv`) picks it up with no code
change. Lines whose `source` starts with `#` are treated as comments.

## AEO2025 — fetchable (on disk)

`aeo2025/aeo2025_electricity_corridor.csv` is pulled from the **EIA Open Data
API v2 `aeo` route** (the same route as `scripts/fetch_eia_aeo.py`) — no scrape.
It is **COMMITTED and sha-pinned** (`SHA256SUMS.txt`), 1,009 lines / 172 KB. The
fetcher remains the source of the bytes (values verbatim from the API, never
hand-transcribed — the rule-5 hazard), but the *output* is committed so the
rubric §0 committed-artifacts contract holds: `data/clean/` is gitignored, so
ignoring this file too left FC-5 with nothing to read (it scored SKIPPED for
every ISO with "no committed benchmark-corridor table"). It also needs a
rate-limited EIA API key to regenerate, so committing it makes the datatype
*more* reproducible, not less — `curate_benchmark_corridor.py` now runs offline
from committed raw. Two tables carry the corridor quantities per Electricity
Market Module (EMM) region:

- **Table 54** (API `tableId=62`) — Electric Power Projections by EMM Region:
  capacity by fuel, generation by fuel, power-sector CO2.
- **Table 56** (API `tableId=67`) — Renewable Energy Generation by Fuel: the
  renewable *capacity* split (solar/wind/offshore/geothermal/hydro/biomass/
  municipal waste) the Table-54 "Renewable Sources" aggregate lacks.

Re-fetch: `python scripts/data/fetch_aeo_electricity.py` (Reference case, years
2030/2035/2040, the 14 EMM regions crosswalked to the six ISOs). A free EIA key
(<https://www.eia.gov/opendata/register.php>, `EIA_API_KEY` env or `.env`) is
optional: the fetch issues **6 requests** — one per (table, year), with the
`regionId` facet omitted so each returns every EMM region at once — which fits
inside the key-free `DEMO_KEY` budget of ~30 requests/hour. (It formerly issued
28, one per region×table, which exceeded that budget and made the fetch
un-runnable without a registered key.) The facet only filters server-side, so
the values are identical either way; verified 2026-08-31 by re-fetching and
reproducing FF-0F's published anchors exactly — 1,008 rows, 2030 power CO2
ERCOT 99.8 / PJM 256.0 / MISO 239.1 MMst, PJM 2035 coal 0.58 GW. The fetcher
refuses a truncated response (the API's silent 5,000-row JSON cap) rather than
writing a partial table.

**EMM region → ISO is approximate, not exact** (`AEO_EMM_TO_ISO` in
`scripts/lib/benchmark_corridor/aeo.py`): AEO's EMM footprints do not equal the
ISO/RTO footprints. This is recorded in every AEO row's `note` (rule 11 — real
data, misalignment stated, never a guessed ISO-exact number). An ISO total is
the sum over that ISO's region rows.

*AEO regional tables publish generation only at the renewable AGGREGATE grain
(no per-renewable-fuel TWh regionally), so the energy-mix rows are
coal/gas/nuclear/oil/renewables/total; the renewable split is capacity-only.*

## ISO planning documents — fetched (on disk)

Two of rubric §6's ISO sources publish their projection tables as a **directly
downloadable XLSX**, so they are machine-extracted by
`python scripts/data/fetch_iso_planning_benchmarks.py` — never hand-transcribed
(typing hundreds of cells is the rule-5 fat-finger hazard that keeps AEO on a
deterministic fetcher). The fetcher writes the canonical unified CSV that the
generic reader already parses, stamping each row's exact sheet/row/column
locator into `source_page`. The **workbooks themselves are gitignored** with
their SHA256 recorded (corpus convention, CLAUDE.md "Cloning & session data");
the small extracted CSVs are committed, so curation still runs offline.

| Source id | Document | Corridor years | What lands |
|---|---|---|---|
| `ERCOT_CDR_2025` | ERCOT Capacity, Demand and Reserves Report, **December 2025** | **2030 only** — the CDR horizon ends at Summer 2030 | firm peak load, total capacity, reserve margin, planned additions by tech (Summer peak-load-hour column) |
| `PJM_LOAD_2026` | PJM **2026** Load Forecast Report tables | 2030 / 2035 / 2040 (horizon 2026-2046) | RTO summer peak load (Table B-1), annual net energy (Table E-1) |

**Basis caveat (rule 11 — real data, misalignment documented).** The CDR's
wind/solar/storage capacities are **peak-hour contribution** (ELCC/seasonal
derated), not nameplate, so they are not directly comparable to AEO's nameplate
GW without reconciliation. This rides in every CDR row's `note`. The CDR's
`reserve_margin` is a RATIO — `iso_totals()` refuses to sum it across regions.

## DATA NEEDED — manual downloads (proxy-blocked or table-in-PDF; never guessed)

Filed as intake rows in `docs/handoffs/ff-inputs-currency-audit-2026-07.md` §6.
Reachability re-probed 2026-08-31 (D22); a source is listed here only because
its numbers cannot be reached in-session, never because it was skipped.

| Source id | Document + exact table | Why still manual (re-probed 2026-08-31) |
|---|---|---|
| `StdScen2024` | NREL Standard Scenarios 2024 Mid-case, regional capacity/generation 2030/2035 (Scenario Viewer CSV export) | **UNREACHABLE, not merely un-fetched.** Every `nrel.gov` host is refused by the egress proxy with a policy denial (`connect_rejected`, 502 to CONNECT): `scenarioviewer.nrel.gov`, `data.nrel.gov`, `www.nrel.gov`. The OEDI S3 mirror carries no Standard Scenarios at all (`nrel-std-scenarios/` returns KeyCount=0; the bucket's top-level prefixes hold ATB, dgen, PR100 … but no ReEDS/StdScen). No in-session route exists. |
| `NYISO_GOLDBOOK_2026` | NYISO 2026 Gold Book — capacity/load forecast tables by zone | host reachable (200), but the document list is a JavaScript portal (Liferay `/documents/<id>/…`) with no static file URL in the served HTML |
| `ISONE_CELT_2026` | ISO-NE 2026 CELT — energy/peak incl. winter-flip rows | host reachable (200), but the CELT file list renders client-side ("no results with this choice of filter(s)" in the served HTML); asset paths are not guessable and guessing is not an intake method |
| `CAISO_IEPR_2025` | CEC IEPR 2025 demand + CPUC PSP (D.24-02-047) / 2025-26 TPP new-build by tech to 2035 | `efiling.energy.ca.gov` and `docs.cpuc.ca.gov` reachable (200), but the forecast tables are proceeding attachments reached through a docket search UI, not a stable file URL |
| `MISO_FUTURES` | MISO Futures / OMS-MISO survey capacity outlook | `misoenergy.org` returns **403** to this session (bot filtering) on both the root and the MISO Futures page |

When a document is obtained, prefer **extending
`scripts/data/fetch_iso_planning_benchmarks.py`** with a machine extractor over
hand-transcribing. If a table truly must be typed, put it in
`<subdir>/<subdir>.csv` (canonical columns; cite the exact table/page in
`source_doc`/`source_page`) and re-run `scripts/data/curate_benchmark_corridor.py`.
