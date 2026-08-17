# CAMPD hourly unit-level extracts

`<ST>_<YEAR>.parquet` — one row per `(facility, unit, hour)` of EPA Clean Air
Markets Program Data (CEMS): `stateCode, facilityName, facilityId, unitId, date,
hour, opTime, grossLoad, steamLoad, so2Mass, co2Mass, noxMass, heatInput,
primaryFuelInfo, unitType, programCodeInfo`. Masses are in EPA source units
(SO2/NOx pounds, CO2 short tons); the model converts to kg on load
(`src/market_sim/data/campd.py`). Raw data is **immutable** — never edited in
place.

## Fetching

Reproducible via `scripts/fetch_campd_unit_level.py` (completed-year per-state
bulk files; set `EPA_API_KEY` to avoid the DEMO_KEY hourly rate limit):

```
python scripts/fetch_campd_unit_level.py --year 2019 --states TX IL OH …
```

The fetcher **refuses** the quarantined holdout years 2022 and H1-2026 unless
`--holdout-intake <ISO>` names an ISO with a `calibration-complete` marker
(CLAUDE.md rule 22).

## Layout / coverage

35 states (the ISO footprints in `campd.ISO_STATES`): AR CA CT DC DE IA IL IN KS
KY LA MA MD ME MI MN MO MS MT NC ND NH NJ **NV** NY OH PA RI SD TN TX VA VT WI
WV. NV added 2026-08-16 (caiso-197): Desert Star Energy Center (EIA 55077,
370.1 MW CAISO CC_REGULAR, Clark County NV) files CEMS under Nevada, so the
CA-only list left it unobservable — the FINDING-caiso193 §2 state-scope gap;
`ISO_STATES["CAISO"]` is now `("CA", "NV")` on the NYISO NY+NJ fleet-filtered
template. NV spans 2018–2026 (2026 = H1 quarters via `--quarters 1 2`).

| Years | Status |
|---|---|
| 2023–2025 | complete (35 states each) — the calibration window |
| 2018–2021 | **complete** (34 states 2026-07-05 + NV 2026-08-16) — the forward CO2-rate history (`docs/handoffs/emissions-co2-rate-plan-2026-07.md` §4); all files committed in per-batch pushes |
| 2022, H1-2026 | **INTAKE-ANYTIME under explicit owner authorization** (rule 22 as amended 2026-07-06, Option 2 — the fetcher records it via `--holdout-intake <ISO>`); the SPEND (solve/score/register) stays gated by the tier markers. NV 2022/H1-2026 intaken 2026-08-16 under `--holdout-intake CAISO` (caiso-197 owner brief), matching the 34-state corpus's existing 2022/2026 coverage. |

**RESOLVED 2026-07-08 — EIA-923 2018–2021 (parasitic net conversion) source gap
closed, re-derive still open.** The v2 rate artifact converts CAMPD gross → net
with per-plant parasitic factors (`scripts/derive_parasitic_load.py`, EIA-923
net ÷ CAMPD gross). The committed
`data/raw/_processed-legacy/eia923_monthly_generation.parquet` now covers
**2018–2026** (data-register intake landed the four missing `f923_2018.zip …
f923_2021.zip` releases — see `docs/data-register-2026-07.md`). The 2018–2021
v2 rows still inherit each plant's **pooled** measured parasitic factor (a
slowly-varying station-service fraction) — `derive_plant_emissions_v2.py`'s
documented fallback, physically the right prior — because the re-derive
itself has not been run yet. To refine: `derive_parasitic_load.py --years
2018 2019 2020 2021` then re-derive v2 (a separate, owner-visible operation
per rule #15 — cite this data landing as the trigger).

**Note on the 2018–2021 push:** these 136 files are large binary parquets, so
they were committed and pushed in small per-batch `git push` commits (each pack
tens of MB, base = latest main) — a single pack of the full ~0.5 GB 413s on this
remote and `mcp__github__push_files` is text-only (CLAUDE.md Git section). All
batches are on main; any missing file regenerates from the committed fetcher.

## The 2018 vintage is UNTRACKED at tip (BLOAT-S2, 2026-08-17)

The 35 `<ST>_2018.parquet` files are **gitignored** since the Stage-2
(a)-only untrack (O2 grant,
`docs/DECISION-CARD-bloat3-stage2-charter-2026-08-16.md`; evidence pass
`docs/FINDING-bloat-s2-evidence-passes-2026-08-17.md` §3). 2018 is outside
the program's working span (owner decision 2026-08-06; fail-closed
locked-test tier, unsolvable), so no solve reads it — its consumers are
derive/curation-time only (the forward CO2-rate history recipe
`derive_fossil_co2_rates.py --years 2018..2021`, the 2018–2026
`derive_campd_unit_outages.py` extract recipe and its caiso-198/199 gate
probes, `derive_correlated_outage_curve.py`, the `curate_emissions*` glob
defaults). **2019–2026 stay tracked**: they are solve-time inputs
(`campd.load_campd_hourly` / `outages._campd_availability_envelope`, keyed on
the solve year) for the training and holdout tiers, with silent-degrade
absence semantics — never untrack them.

**Recovery is re-fetch ONLY** (story (a); no pin/history route). Measured
2026-08-17: the EPA CAM-API bulk-files service served
`emissions-hourly-2018-tx.csv` (HTTP 206, `x-api-key: DEMO_KEY`) — stable
federal archive, full history. Re-fetch BEFORE running any 2018-spanning
derive:

    python scripts/data/fetch_campd_unit_level.py --year 2018 --states <ST ...>

(no holdout quarantine applies to 2018). `SHA256SUMS.txt` records the exact
removed bytes; the fetcher's sibling-schema verification keeps a re-fetched
file schema-identical, though parquet serialization may differ byte-wise.
