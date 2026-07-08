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

34 states (the ISO footprints in `campd.ISO_STATES`): AR CA CT DC DE IA IL IN KS
KY LA MA MD ME MI MN MO MS MT NC ND NH NJ NY OH PA RI SD TN TX VA VT WI WV.

| Years | Status |
|---|---|
| 2023–2025 | complete (34 states each) — the calibration window |
| 2018–2021 | **complete** (34 states each, 2026-07-05) — the forward CO2-rate history (`docs/handoffs/emissions-co2-rate-plan-2026-07.md` §4); all files committed in per-batch pushes |
| 2022, H1-2026 | **QUARANTINED** (CLAUDE.md rule 22) — do not intake until the ISO is calibration-complete. |

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
