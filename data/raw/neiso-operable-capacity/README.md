# NEISO operable-capacity / generation-outage series (ISO-NE Morning Report)

The measured **daily generation-outage and operable-capacity** series for
ISO New England — the NEISO analogue of the ERCOT measured DAM class-day
availability (`data/raw/ercot-thermal-dam-availability.csv`). Intended for a
NEISO backcast to use **in place of the CAMPD-derived unit-outage fallback**
(`campd-unit-outages-NEISO.csv`).

## Source (authoritative)

- **Report:** ISO-NE ISO Express → Operations Reports → **Morning Report**,
  **Section 3. Operable Capacity Analysis** (peak-hour operable-capacity picture
  published each morning).
- **Landing page:**
  https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/morning-report
- **Public CSV endpoint (one operating day per file):**
  `https://www.iso-ne.com/transform/csv/morningreport?start=YYYYMMDD`
  (403s without an `isox_token` session cookie; the fetch script bootstraps one
  from a public ISO Express page, the same pattern as
  `fetch_neiso_reserve_requirements.py` / `fetch_neiso_da_energy_offers.py`).
- **Coverage:** the archive begins **2018-07-01** (2018 H1 returns an empty
  placeholder) and runs to the present. The **planned/forced outage split**
  (`gen_planned_outages_mw` / `gen_forced_outages_mw`) is published only from the
  mid-2025 format change onward; it is null before that.
- **Title rename (2025-07):** ISO-NE renamed the report title "Morning Report" →
  "Operational Capacity Update Report" at the same format change (the filename
  stayed `morning_report_YYYYMMDD.csv` and Section 3 is unchanged). Both fetch
  and parse key on the stable `Operable Capacity Analysis` header, not the title.

## Layout

```
data/raw/neiso-operable-capacity/
  README.md                              (this file)
  neiso_operable_capacity_<YYYY>.csv     (COMMITTED deliverable, one file/year, one row/day)
  daily/morning_report_<YYYYMMDD>.csv     (GITIGNORED raw pulls, regenerable)
```

Regenerate end-to-end:

```
python scripts/data/fetch_neiso_morning_report.py      # -> daily/*.csv (gitignored)
python scripts/data/build_neiso_operable_capacity.py   # -> the committed per-year CSVs
#   add --parquet /tmp/neiso_oc.parquet for a single local columnar copy (not committed)
```

**Why per-year CSVs, not one parquet.** The repo's API-only push path (CLAUDE.md
"Git & Pushing") commits file content **as text** and cannot round-trip binary
(a parquet), and it carries each file's content **inline** — so one ~0.7 MB
combined file is unpushable too. The deliverable is therefore CSV (matching the
ERCOT `ercot-thermal-dam-availability.csv` precedent), **partitioned by calendar
year** (the repo's `eia-930` / `campd-unit-level` convention) so each committed
file is ~40 kB. All figures are whole MW / whole hours, stored as nullable
integers, so the CSVs are compact and git-diffable. `build_...py --parquet
<path>` emits a single columnar parquet locally on demand.

## Provenance

`iso` is constant `NEISO` and the source is constant, so neither is stored as a
column (they would triple the row width). **Source:** ISO-NE ISO Express Morning
Report, Section 3 Operable Capacity Analysis
(`https://www.iso-ne.com/transform/csv/morningreport`), per the citation at the
top of this file.

## Column contract

One row per delivery date (`report_date`). Every MW column is transcribed **as
published** by ISO-NE (no fitting, no rescaling to a residual — CLAUDE.md rules
13/14). The consumed availability *fraction* is derived downstream in
`market_sim.data.neiso_operable_capacity`, so these files stay a faithful
transcription.

| column | unit | null? | source line (Section 3 unless noted) |
|---|---|---|---|
| `report_date` | date | no | report delivery date (filename / "Report for") |
| `prior_day_peak_date` | date | yes | Section 2 Prior Day Peak |
| `prior_day_peak_hour_ending` | hour | yes | Section 2 Prior Day Peak |
| `prior_day_peak_mw` | MW | yes | Section 2 Prior Day Peak |
| `cso_mw` | MW | no | A. Capacity Supply Obligation (CSO) |
| `capacity_additions_ecomax_gt_cso_mw` | MW | yes | B. Capacity Additions EcoMax > CSO |
| `gen_outages_reductions_mw` | MW | no | **C. Generation Outages and Reductions (Planned + Forced)** |
| `gen_planned_outages_mw` | MW | yes | Generation Planned Outages and Reductions (mid-2025+) |
| `gen_forced_outages_mw` | MW | yes | Generation Forced Outages and Reductions (mid-2025+) |
| `uncommitted_available_gen_nonfast_mw` | MW | yes | D. Uncommitted Available Generation (Non-fast start) |
| `drr_capacity_mw` | MW | yes | E. DRR Capacity |
| `uncommitted_available_drr_mw` | MW | yes | F. Uncommitted Available DRR |
| `net_capacity_deliveries_mw` | MW | yes | G. Net Deliveries (net interchange) |
| `total_available_capacity_mw` | MW | no | **H. Total Available Capacity (A+B-C-D+E-F-G)** |
| `peak_load_forecast_mw` | MW | yes | I. Peak Load Forecast |
| `total_operating_reserve_req_mw` | MW | yes | J. Total Operating Reserve Requirement |
| `capacity_required_mw` | MW | yes | K. Capacity Required = I + J |
| `surplus_deficiency_mw` | MW | yes | L. Surplus (+) / Deficiency (-) (H - K) |
| `replacement_reserve_req_mw` | MW | yes | M. Replacement Reserve Requirement |
| `excess_commitment_mw` | MW | yes | N. Excess Commitment Surplus/Deficiency (L - M) |
| `largest_first_contingency_mw` | MW | yes | Section 4. Largest First Contingency |
| `ams_peak_load_exposure_mw` | MW | yes | Section 5. Annual Maintenance Schedule exposure |

Integrity check the builder validates implicitly: the identity
`H = A + B − C − D + E − F − G` reconciles to 0 MW on every parsed row.

## Grain caveat (why this is fleet-total, not per-class)

ISO-NE publishes availability only at **fleet grain** here. It does **not**
publish a per-unit or per-fuel outage/availability series (only masked-asset
day-ahead offers, already intaken for 2023–2025 under
`data/raw/NEISO-AS/da-energy-offers/`). So the ERCOT per-class DAM construction
has no ISO-NE equivalent; the consumption seam imposes one measured fleet
availability fraction on the covered dispatchable-thermal classes together
(gated `ScenarioConfig.neiso_operable_capacity_availability`, default off).

## DATA NEEDED

- None for the committed CSV — it is regenerable from the public endpoint
  above. The gitignored `daily/*.csv` are re-fetchable at any time.
