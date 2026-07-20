# eia-aeo — raw

Source root for the `eia-aeo-fuel-prices` clean datatype
(`data/dictionary/schema/eia-aeo-fuel-prices.schema.yaml`). Fetched by
`scripts/fetch_eia_aeo.py` from the EIA Open Data API v2 `aeo` route (not a
scrape of the AEO table-browser HTML) and curated by
`scripts/curate_eia_aeo_fuel_prices.py`, which reads
`eia_aeo2025_fuel_prices.csv` in this directory and writes schema-valid
Parquet to `data/clean/eia-aeo-fuel-prices/eia-aeo-fuel-prices.parquet`.

## Why this exists

`constants.py:914` has carried a standing `TODO: verify against AEO Table 13`
since `HENRY_HUB_TRAJECTORIES` was hand-typed from "published AEO2025 charts
and text" rather than the AEO data tables themselves. This directory resolves
that TODO with the real API-fetched series, plus coal and oil trajectories
the model didn't previously have any AEO-cited source for (coal currently
escalates at a flat, uncited 1%/yr; oil is a flat scalar). See
`docs/handoffs/aeo-verification-<date>.md` for the hardcoded-vs-fetched diff
report — **this session intentionally does not change
`HENRY_HUB_TRAJECTORIES`**; re-deriving it (and adding the new
`COAL_PRICE_TRAJECTORIES` / oil path) from this data is P-1D's job (CLAUDE.md
rule 23: a derive script cites the data change that triggered it).

## Expected file

`eia_aeo2025_fuel_prices.csv` — one row per (fuel, metric, region, scenario,
year), columns:

```
fuel,metric,region,scenario,scenario_name,year,value,unit,series_id,table_id,table_name
```

- `fuel`: `gas` | `coal` | `oil`.
- `metric`: `henry_hub_spot` (gas); `wti_spot_crude` |
  `electric_power_distillate` | `electric_power_residual` (oil);
  `delivered_electric_power` | `minemouth_average` | `minemouth_by_region`
  (coal).
- `region`: `usa` for every national series, else an EIA coal supply-region
  code (`appalachia`, `east_of_mississippi`, `interior`, `west`,
  `west_of_mississippi`) for `minemouth_by_region`.
- `scenario`: AEO2025 scenario id — `ref2025` (Reference, -> model "mid"
  `gas_price_path`), `highogs` (High Oil and Gas Supply, -> model "low",
  more supply/lower price), `lowogs` (Low Oil and Gas Supply, -> model
  "high"). Same scenario/path mapping as the comment block above
  `HENRY_HUB_TRAJECTORIES` in `constants.py`.
- `value` / `unit`: real (2024-dollar) terms throughout — `2024 $/MMBtu`
  (gas Henry Hub; coal delivered-to-electric-power and national minemouth),
  `2024 $/b` (WTI crude), `2024 $/gal` (electric-power distillate/residual
  fuel oil), `2024 $/st` (coal minemouth by region — AEO's Table 65 regional
  breakout has no $/MMBtu figure, only $/short-ton; national coal is
  available in $/MMBtu instead, so both units appear in this file by design,
  never conflated).

## Authoritative source

EIA Annual Energy Outlook 2025, via the EIA Open Data API v2 `aeo` route
(`https://api.eia.gov/v2/aeo/2025/data/`; API docs
<https://www.eia.gov/opendata/documentation.php>). Series pulled (verified
present via the API's own `tableId`/`seriesId` facets, not guessed):

| Series (AEO table) | series_id |
|---|---|
| Table 13 Henry Hub spot | `prce_hhp_NA_NA_ng_NA_usa_y13dlrpmmbtu` |
| Table 12 WTI crude spot | `prce_NA_NA_NA_cr_wti_usa_y13dlrpbbl` |
| Table 12 electric power distillate | `prce_NA_elep_NA_dfo_NA_usa_y13dlrpgln` |
| Table 12 electric power residual | `prce_NA_elep_NA_rfo_NA_usa_y13dlrpgln` |
| Table 15 coal delivered to electric power | `prce_NA_elep_NA_cl_NA_NA_y13dlrpmmbtu` |
| Table 15 coal minemouth (US average) | `prce_NA_NA_NA_cl_mnmth_NA_y13dlrpmmbtu` |
| Table 65 coal minemouth by region (x5) | `prce_NA_NA_NA_cl_mnmth_{aplch,eom,intr,west,wom}_y13dlrptn` |

**On-disk layout note:** `eia_aeo2025_fuel_prices.csv` is committed as
numbered, header-repeating parts (`eia_aeo2025_fuel_prices.part00.csv`,
`.part01.csv`, ...) rather than one file — an artifact of this session's
push tooling (the git-API push path used here caps individual file-content
size), not a change to the data. `scripts/curate_eia_aeo_fuel_prices.py`
reads the single-file name if present, else concatenates the parts (same
convention as `data/raw/coal-prices/`, see that directory's README); both
layouts are byte-identical once joined. A future `fetch_eia_aeo.py` re-run
writes a single file again, which the curate script also reads fine.

## Regeneration

```
EIA_API_KEY=your_key python scripts/fetch_eia_aeo.py
python scripts/curate_eia_aeo_fuel_prices.py     # raw CSV (or its .part*.csv pieces) -> clean Parquet
```

Falls back to the public rate-limited `DEMO_KEY` if no key is configured
(verified working for this route during this intake), but the repo's own
`.env` already carries a registered `EIA_API_KEY` that
`scripts/fetch_eia_aeo.py` picks up automatically (same env-var-then-`.env`
lookup as `scripts/fetch_eia_coal_prices.py`). Re-running against a future
AEO edition (`--aeo-year 2026`) is a forward-regenerating fetch, not a
one-off transcription — rule-13 admissible.

## DATA (landed)

- [x] `eia_aeo2025_fuel_prices.csv` — 891 rows: 11 series x 3 scenarios x 27
      years (2024-2050). No years withheld or quarantined — AEO trajectories
      are forward projections, not measured actuals for a solve/scoring year,
      so CLAUDE.md rule 22's 2022/H1-2026 holdout quarantine does not apply
      here (unlike the `rggi-co2-budgets`/`carb-cap-schedule` measured-anchor
      datatypes).

## AEO2026 (landed FF-G2, 2026-07-20)

`eia_aeo2026_fuel_prices.csv` — 858 rows (11 series × 3 scenarios × 26 years,
2025-2050), fetched by `fetch_eia_aeo.py --aeo-year 2026` and committed as
header-repeating parts (`eia_aeo2026_fuel_prices.part00.csv` …) per the on-disk
layout note above; `derive_fuel_trajectories.py` reads the single file if
present, else concatenates the parts. Two edition
differences from AEO2025: (a) real **2025$** (AEO2025 was 2024$); (b) the
central case is `cb2026` ("Counterfactual Baseline", formerly Reference) —
`SCENARIOS_BY_AEO[2026]` in the fetch script maps `highogs`→low, `cb2026`→mid,
`lowogs`→high. Consumed by `derive_fuel_trajectories.py --aeo-year 2026` to
refresh `HENRY_HUB_TRAJECTORIES` / `COAL_PRICE_TRAJECTORIES` /
`OIL_PRICE_TRAJECTORIES` (forecast years only; gas keeps its ≤2025 historical
actuals). Full grounding: `docs/fuel-forward-methodology-2026-07.md`.

## What this doesn't cover

- **Gas forward strips (N13)** — CME Henry Hub futures for a near-term blend —
  snapshotted (STEO) and flagged MANUAL (current CME strip) in the FF-G2
  benchmark datatype `data/raw/fuel-forward-benchmarks/`; benchmarks/context
  only, never fit targets.

## Consumer

Landed P-1D (2026-07) via `scripts/derive_fuel_trajectories.py`:
`HENRY_HUB_TRAJECTORIES` (all three paths, 2026-2050) re-derived from this
data; new `COAL_PRICE_TRAJECTORIES` and `OIL_PRICE_TRAJECTORIES` constants
added, consumed by `data.fuel.resolve_annual_coal_price` /
`resolve_annual_oil_price` in forecast mode. See
`docs/handoffs/aeo-verification-2026-07-11.md` §6 for the execution note.
