# MISO wind curtailment — provenance

`misoenergy.org` / `cdn.misoenergy.org` (MISO's own Market Reports site, which
would carry the primary hourly wind & solar curtailment workbooks analogous to
CAISO's "Production and Curtailments data") remain HTTP 403 from this
environment's outbound allowlist as of 2026-07-08 (re-checked; same result as
the 2026-06-22/2026-07-05 audits in `docs/multi-iso/miso-data-audit.md`).

## Alternate reproducible source found and used here

**Potomac Economics** is MISO's FERC-designated Independent Market Monitor
(IMM) and publishes its **State of the Market (SOM)** annual reports and
**IMM Quarterly Reports** on its own site, `potomaceconomics.com`, which *is*
reachable. These reports quantify MISO-system-wide wind curtailment (annual
average MW, peak single-hour MW, and — from the quarterly decks — a seasonal
average MW). This is a real, citable, reproducible-on-a-lag public data
source (a new SOM report lands every June/July for the prior year; a new IMM
Quarterly report lands roughly 6-8 weeks after each quarter ends), so it is
admissible as a backcast-only overlay per CLAUDE.md rule #12 the same way the
existing `data/raw/miso-pra/` secondary-sourced auction prices are.

**Important granularity caveat:** unlike CAISO's 5-minute interval workbook
(`scripts/build_caiso_hsl.py`), Potomac Economics' MISO reports give only
**annual and quarterly average/peak MW figures**, not an hourly time series.
This is coarser than CAISO/ERCOT's HSL sources — closer to the "NYISO only
publishes a coarse annual curtailment aggregate" case already documented in
`docs/data-register-2026-07.md` (#27-analogue). Building an
`miso_<year>_hsl_hourly.parquet` per the `ercot-hsl`/`caiso-hsl` pattern is
**not done here** — it would require spreading these aggregate MW figures
across hours using a physically motivated shape (e.g. the existing
`data/raw/miso-wind-shape/` reanalysis), which is a distinct engineering/
methodology decision left for a follow-up, not a "collect the source data"
task. `market_sim.data.renewables._hsl_file` still falls back to the EIA-930
delivered profile for MISO until that follow-up lands.

## Files in this directory

- `miso_wind_curtailment_annual.csv` — one row per year 2018-2025: wind
  nameplate capacity, average RT/DA output, average/peak curtailment MW where
  the SOM report states it, and the source page. 2018-2020 have no
  curtailment figure at all — those reports simply don't quantify it (wind
  penetration/curtailment wasn't yet a headline concern); this is a genuine
  source gap, not an extraction miss (confirmed by full-text search of all
  three PDFs for "curtail" near any MW/GW/% figure).
- `miso_wind_curtailment_quarterly.csv` — the "Wind and Solar Output in Real
  Time" panel's seasonal avg/max/min MW, 2023 Winter through 2026 Spring
  (i.e. through the most recent published quarter, Mar-May 2026 — H1 2026 is
  the touch-once locked-test year per CLAUDE.md rule #22; June 2026 is not
  yet covered by any published quarterly report). Each report shows the
  current quarter plus its prior-year and prior-quarter comparisons, so most
  quarters are cross-validated from 2-3 independent report editions; small
  (1-10 MW) discrepancies between editions are kept and flagged rather than
  silently reconciled, and two 2023/2024 Spring rows are flagged as
  suspicious exact duplicates of the adjacent Winter row (likely a
  stale/unrefreshed template cell in Potomac Economics' own deck).
- `miso_wind_curtailment_quarterly_forecast_method.csv` — a *second, distinct*
  curtailment metric Potomac Economics reports on the "Wind Forecast and
  Actual Output" page of the same quarterly decks (average MW curtailed above
  the 2-3-hour-ahead forecast). It does not match the real-time-output
  panel's figure quarter-for-quarter (e.g. Spring 2026: 936 MW real-time-panel
  vs. 798 MW forecast-method), so the two are kept as separate series rather
  than merged — they are evidently measuring curtailment two different ways
  and neither is obviously "the" curtailment number.

## Primary documents (all fetched 2026-07-08, all currently reachable at these URLs)

State of the Market annual reports:
- 2018: https://www.potomaceconomics.com/wp-content/uploads/2019/06/2018-MISO-SOM_Report_Final2.pdf
- 2019: https://www.potomaceconomics.com/wp-content/uploads/2020/06/2019-MISO-SOM_Report_Final_6-16-20r1.pdf
- 2020: https://www.potomaceconomics.com/wp-content/uploads/2021/05/2020-MISO-SOM_Report_Body_Compiled_Final_rev-6-1-21.pdf
- 2021: https://www.potomaceconomics.com/wp-content/uploads/2022/06/2021-MISO-SOM_Report_Body_Final.pdf
- 2022: https://www.potomaceconomics.com/wp-content/uploads/2023/06/2022-MISO-SOM_Report_Body-Final.pdf
- 2023: https://www.potomaceconomics.com/wp-content/uploads/2024/06/2023-MISO-SOM_Report_Body-Final.pdf
- 2024: https://www.potomaceconomics.com/wp-content/uploads/2025/06/2024-MISO-SOM_Report_Body_Final.pdf
- 2025: https://www.potomaceconomics.com/wp-content/uploads/2026/07/2025-State-of-the-Market-Report.pdf (published 2026-07, the newest keeper-eligible year)

IMM Quarterly Reports (used for the 2025 and H1-2026 seasonal breakdown, since
the 2025 SOM report dropped the annual curtailment-MW sentence it carried in
2021-2024):
- Winter 2025 (Dec24-Feb25): https://www.potomaceconomics.com/wp-content/uploads/2025/03/IMM-Quarterly-Report_Winter-2025.pdf
- Spring 2025 (Mar-May25): https://www.potomaceconomics.com/wp-content/uploads/2025/06/IMM-Quarterly-Report_Spring-2025-MSC.pdf
- Summer 2025 (Jun-Aug25): https://www.potomaceconomics.com/wp-content/uploads/2025/11/IMM-Quarterly-Report_Summer-2025-MSC.pdf
- Fall 2025 (Sep-Nov25): https://www.potomaceconomics.com/wp-content/uploads/2025/12/IMM-Quarterly-Report_Fall-2025_MSC.pdf
- Winter 2026 (Dec25-Feb26): https://www.potomaceconomics.com/wp-content/uploads/2026/03/IMM-Quarterly-Report_Winter-2026-MSC.pdf
- Spring 2026 (Mar-May26): https://www.potomaceconomics.com/wp-content/uploads/2026/07/2026-IMM-Quarterly-Report-Spring.pdf

PDFs themselves are not committed to the repo (they are large, third-party
copyrighted documents, and every figure used is transcribed into the CSVs
above with a page citation) — re-download from the URLs above to re-verify.

## Holdout-quarantine note (CLAUDE.md rule #22)

This directory now carries transcribed figures for 2018-2022 (pre-2023
validation/pre-2020 tiers) and Winter/Spring 2026 (part of the H1-2026 locked
test), which are out-of-training years. Per rule #22's standing quarantine
clause, out-of-training data intake requires "explicit, session-logged owner
authorization." That authorization was given directly in this session
(2026-07-08): the owner asked to "collect designated MISO renewable HSL /
curtailment data for all the years we need," then explicitly widened scope to
"anything missing between 2018 and 2026 first half." No LP solve, backcast
run, or scoring was performed against any of this data (rule #22's "no-LP"
constraint) — this commit is data collection only.
