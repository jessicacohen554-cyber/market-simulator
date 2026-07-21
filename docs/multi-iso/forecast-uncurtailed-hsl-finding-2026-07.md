# Forecast-uncurtailed / HSL coverage — per-ISO finding (2026-07-21)

Branch: `claude/forecast-uncurtailed-hsl`. Scope: give NYISO/MISO an
*uncurtailed-potential* renewable basis where the on-disk source data supports
it, so they stop inheriting the historical curtailment baked into the EIA-930
*delivered* CF. Rule 22 respected — **no holdout year was solved or scored**;
this is a data-loading + provenance change only, verified with `tmp` reads and
committed EIA extracts.

## Step 0 conclusion — what is actually on disk vs. what the code claimed

The `DATA NEEDED` comments in `src/market_sim/data/renewables.py` were **stale**
against the on-disk data. Per ISO:

| ISO | On-disk source | Prior loader behaviour | Finding | Action |
|-----|----------------|------------------------|---------|--------|
| **ERCOT** | `ercot-hsl/ercot_{2023,2024,2025}_hsl_hourly.parquet` + `np6/{2024,2025}/` NP6 uploads (landed 2026-07-06) | comments claimed "ERCOT 2024/25 — no NP6 upload could be sourced" → forecast fallback | **STALE comment.** All three years already carry a built HSL parquet; provenance is `measured_potential` for every ERCOT backcast year. | Corrected the module docstring / `_forecast_uncurtailed_cf` / `renewable_bound_provenance` comments. No data work needed. |
| **CAISO** | `caiso-hsl/caiso_{2019,2020,2021,2023,2024,2025}_hsl_hourly.parquet` | HSL path, `measured_potential` | Already complete. | None. |
| **MISO** | `miso-hsl/miso_wind_curtailment_annual.csv` (+ quarterly / forecast-method) — Potomac Economics IMM aggregate; `miso-wind-shape/` reanalysis | `_hsl_file` → `None` → **delivered-pinned** (L1 leakage). Comment claimed "empty / misoenergy blocked". | **Source present, but AGGREGATE (annual/quarterly MW), not hourly.** MISO wind curtailment is material (~4.9% of potential, multi-TWh/yr). A modeled hourly parquet would be *modeled-not-measured* (needs its own rule-12 methodology); the honest, rule-13-admissible move is the **reference-rate** path. | **Wired MISO wind onto the forecast-uncurtailed reference-rate path** (see below). MISO solar → honest gap (no series), stays delivered. |
| **NYISO** | `nyiso-renewable-curtailment/` (annual + monthly aggregate); `nyiso-hsl/` does not exist | delivered-pinned; comment = `DATA NEEDED` stub | **Genuine gap, deliberate.** NYISO curtailment is ~1.1% wind / ≤2% solar (well under 1 TWh/yr) AND only monthly/zonal aggregate — both below the materiality threshold and too coarse for even a reliable rate. | **Keep delivered fallback.** Corrected the comment from "reserved for future data / DATA NEEDED" to "checked genuine-gap decision"; NYISO stays OUT of `_UNCURTAILED_FALLBACK_ISOS`. |
| **NEISO** | none | delivered-pinned | Genuine gap (sub-1% curtailment, no series). | Unchanged; comment already accurate. |

## What changed for MISO wind

MISO is now in `_UNCURTAILED_FALLBACK_ISOS`. The new
`_miso_wind_reference_curtailment_rate()` reads the committed annual CSV and
returns the **training-window (2023-2025) firm (non-estimate) mean** of
`curtailed / (delivered + curtailed)`:

- 2023: 507 MW / (10 400 MW + 507) = 0.0465
- 2024: 607 MW / (11 200 MW + 607) = 0.0514
- **mean ≈ 0.0489**, tagged as-of 2024 (2025 is a source-flagged estimate, dropped).

`_reference_curtailment_rate("MISO", "wind")` returns this; `("MISO", "solar")`
returns `None`. The backcast then grosses the delivered EIA-930 wind shape up to
`delivered / (1 − 0.0489)` (`_forecast_uncurtailed_cf`), so the LP re-curtails
endogenously and MISO wind's bound is labelled `forecast_uncurtailed`.

### Why this is rule-admissible (not a residual tune)

- **Rule 13 forward analogue:** the rate is a measured aggregate curtailment %
  from the IMM's public reports — the *same quantity a forward run would assume*,
  reproducible on a lag as new SOM reports land. It is a *rate*, applied to the
  weather-year delivered *shape*; it never references any target year's price or
  volume outcome, so it cannot pin the backcast (rules 11/13).
- **Rule 24:** re-derives only when the source CSV updates.
- **Rule 22:** the rate is computed strictly within 2023-2025; no holdout year
  (2019/2022/H1-2026) is read. No solve was run in this session.
- **Not a fabricated hourly series:** MISO publishes no hourly curtailment, so
  no `miso_<year>_hsl_hourly.parquet` is built. Spreading the aggregate across
  hours would be *modeled*, mislabelled as `measured_potential`; the
  reference-rate path is correctly labelled `forecast_uncurtailed` (weaker than a
  published potential, honestly so).

## Honest remaining gaps (no proxy fabricated)

- **MISO solar** — no published curtailment series → delivered profile.
- **NYISO wind & solar** — immaterial + coarse → delivered profile (deliberate).
- **NEISO** — sub-1% curtailment, no series → delivered profile.
- **ERCOT 2018-2022 / H1-2026** — NP6 archive is credential-gated (documented in
  `data/raw/ercot-hsl/README.md`); not fetchable this session.

## Files touched

- `src/market_sim/data/renewables.py` — MISO reference-rate loader + wiring;
  stale-comment corrections (ERCOT/NYISO/MISO).
- `tests/test_miso_wind_curtailment_rate.py` — new (12 tests).
- `docs/multi-iso/miso-data-audit.md`, `data/raw/miso-hsl/README.md`,
  `data/raw/miso-hsl/SOURCES.md` — updated to reflect the wired reference-rate
  path.
