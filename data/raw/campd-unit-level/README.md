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
| 2018–2021 | **DATA NEEDED** — intake in progress for the forward CO2-rate history (`docs/handoffs/emissions-co2-rate-plan-2026-07.md` §4). Re-fetch any missing `<ST>_<YEAR>.parquet` with the command above. |
| 2022, H1-2026 | **QUARANTINED** (CLAUDE.md rule 22) — do not intake until the ISO is calibration-complete. |

**Note on the 2018–2021 push:** these ~136 files (~0.5 GB) are large binary
parquets. `mcp__github__push_files` is text-only (would corrupt binary) and a
single git pack of this size 413s on this remote (CLAUDE.md Git section), so the
raw files are landed and **regenerated on demand** from the committed fetcher
rather than all force-pushed at once. The *consumed* products — the
`emissions-unit-annual` clean datatype and the committed
`plant_emission_rates_v2` artifact — carry the derived per-year rates.
