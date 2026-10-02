# INTAKE — closeout-NEISO wave 1, step 2: rule-14 accuracy repairs (no gate claim)

Lane `closeout-neiso-wave1`, 2026-10-02. Zero LP. **No keeper input changes**: the NEISO keeper
(`neiso119_span`) reads none of the new rows (ULSD daily parity is off; dynamic requirements are off; the dashboard
AGT series is read by no code). Every change below is cited to its data (rule 23), never to a residual.

## 1. NY Harbor ULSD daily → 2019-01-01

| | before | after |
|---|---|---|
| `data/raw/oil-prices/ny_harbor_ulsd_daily.csv` | 2022-01-03 .. 2025-12-31, 996 rows | **2019-01-02 .. 2025-12-31, 1,748 rows** (2019 249, 2020 252, 2021 251) |
| 2022–2025 rows | — | **byte-identical** (re-fetched and diffed) |
| sha256 | — | `94f7c47b755b88614f97a14b0469793710aaf61d812f9be2f2bdfef12ae118fc` |

Source: EIA `EER_EPD2DXL0_PF4_Y35NY_DPG` (daily workbook), `scripts/data/fetch_ny_harbor_distillate_daily.py
--start-year 2019` (default window moved to 2019; its rule-22 holdout text removed — rule 22's holdout regime was
removed 2026-09-09). New `data/raw/oil-prices/README.md`.

**Cross-ISO effect (flagged to the desk, not acted on).** The **NYISO keeper** `2026-10-01-nyisonext26p-tslprint-span`
arms `dual_fuel_oil_daily_parity` (`results/calibration/nyisonext26p_span/run_config.json`). Its 2019–2021 legs read
an empty year (all-ones shape, i.e. the flat monthly receipt). A replay after this lands reads the measured daily
shape there: a **LIVE** G-DRIFT hunk for NYISO 2019–2021. It is the more accurate input (rule 14), but it is NYISO's
lane to account for. 2022–2025 are unaffected (byte-identical rows; the staircase is built per year).

## 2. ISO-NE hourly reserve requirements 2019–2022 (+ 2023–2025 regenerated)

175 fifteen-day windows fetched (`scripts/data/fetch_neiso_reserve_requirements.py`, default now 2019–2025; the
windows stay gitignored). Measured in the raw data:

| year | ROS hours | curated? | defect |
|---|---:|---|---|
| 2019 | 5,139 | partial (2019-05-31 →) | **the report publishes nothing before 2019-05-31** (Jan–May windows are 256-byte header-only files) |
| 2020 | 8,778 | **refused** | **2020-12-10..17: 142 ROS hours publish 0 / 0 / 830 MW** (zero spin and ten-minute — a publication outage) + one duplicated row (2020-12-16 HE 11) |
| 2021–2025 | full | yes | 2023/2024/2025 carry 1–2 single-hour holes (step-filled, as before) |

**Parser repairs** (`scripts/lib/reserve_requirements/neiso.py`, tests in
`tests/curation/test_curate_reserve_requirements.py`): an exact repeat of the row just consumed on a day whose hour
sequence does not repeat that label is dropped; a ROS zero ten-minute value becomes a source hole (it counts against
`MAX_GAP_HOURS`, so 2020 is refused instead of reaching the LP as a zero requirement); local zones keep their
legitimate zeros. **2021–2025 parsed frames are byte-identical before/after** (`DataFrame.equals`, all five years).
`curate_reserve_requirements.py` now refuses a year whose parser hard-errors (`[refuse]` line) and continues with
the rest. Without that, the 2020 defect aborted the run before 2021–2025 were written. The loader still hard-errors
on an absent or partial year, so nothing degrades silently.

**Structure (zero LP, `reserve_requirement_recon.py`).** Nested in the source (spin ⊆ ten-minute ⊆ TOTAL). The spin
share of ten-minute is 0.31 to mid-2022 and 0.25 after. Annual means: spin 544/528/515/456/387/395/394 MW, ten-minute
1,751/1,702/1,661/1,667/1,544/1,578/1,573, TOTAL 2,539/2,478/2,449/2,458/2,301/2,329/2,328 (2019→2025; 2019 is Jun–Dec only). Against
the static 600 / 1,200 / 1,800 that is a **tightening** of ten-minute and thirty-minute and a loosening of spin. The LP
families are nested as well (`lp/reserve_rows.py`), so the plan's "static rows overstate by 1,246 MW" is not an LP
quantity (matrix cell corrected).

**The Morning Report is not a fill.** `data/raw/neiso-operable-capacity/` carries a daily
`total_operating_reserve_req_mw` for all of 2019, but at 0.64–1.18× the hourly ROS TOTAL (yearly medians 0.80–0.94),
`largest_first_contingency_mw` at 0.51–1.10× the hourly ten-minute value. It is a peak-hour planning basis. The
owner choice for the two unpublished windows is in the PRECOMMIT §2-D.

## 3. Algonquin Citygate event days

**The gap is in the source.** EIA published no Natural Gas Weekly Update on 2022-12-29 or 2023-01-05 (both 404), so
the narrative series has nothing between 2022-12-21 ($6.51) and 2023-01-04: Winter Storm Elliott is in the hole.

**Event-week transcription** (`agt_event_day_evidence/transcription.csv`, 63 rows, each with URL, page and verbatim
quote; `REPORT.md`; source files hashed in `SHA256SUMS`, not committed):

* Weekly-Update NGI mentions the repo scraper missed: **2023-02-02 $71.42** ("the highest daily price since January 4,
  2018"), 2022-01-25 weekly high $24.62; two undated weekly highs ($26.94 week of 2022-01-13..19, $6.75 week of
  2025-06-19..25).
* **ISO-NE IMM figures are a multi-hub composite, not Algonquin**: the $35.37 Dec 24–27 2022 average (2022 AMR, PDF
  p.36 / printed p.29) is a weighted average of ICE next-day indices across Algonquin Citygates, Algonquin Non-G,
  Portland, TGP Z6-200L, TGP North/South and M&NE. The research shard's "Algonquin daily average $35.37" is corrected
  here. Also recorded as composite: gas day 12/22 $6.66 → 12/23 $30.05, 12/24 $35.99, 2023-02-03 $76.42.
* FERC/NERC Elliott report: unreachable (ferc.gov 403/Cloudflare; nerc.com 404). Not read, nothing transcribed.

**A free near-daily source exists**: EIA's **New England Dashboard** archive (one PDF per day, the Algonquin tile
printed as text, S&P Global Market Intelligence as the stated source). New fetcher
`scripts/data/fetch_eia_ne_dashboard_agt_daily.py` → `data/raw/gas-prices/algonquin_citygate_daily_eia_ne_dashboard.csv`.

| | |
|---|---|
| file | `algonquin_citygate_daily_eia_ne_dashboard.csv`, 1,618 priced snapshots, sha256 `713858290bba65cb2fb498669dbbb00f1ccac0052db212b937e5656489d065eb` |
| priced label days | 2019 213 · 2020 243 · 2021 238 · 2022 235 · 2023 207 · 2024 239 · 2025 239 (the narrative series: 52–60/yr) |
| scrape census 2019-01-01..2025-12-31 | 2,557 days: 1,618 priced, 796 no-print (weekends, holidays, blank dashboards — 2023-07 and 2023-11/12 have weeks of `--`), 140 404, 3 known source defects (two truncated Saturday PDFs, one snapshot without the tile) |
| layouts | three (2019 "%" column, 2020 wrapped caption, 2025-07 stacked tile); parser checked against all 78 hand-verified snapshots (0 mismatches) and unit-tested per layout |
| stale snapshots | 4 snapshots repeat an earlier label (e.g. 2023-11-03/04 both print the 11-02 value); the label, not the snapshot day, keys the price |
| **date basis** (`agt_dashboard_vs_ngwu.py`) | against the NGI narrative prints shifted one business day: **corr 0.989, median \|Δ\| $0.02, 88 % within 5 %** (323 pairs); unshifted: corr 0.872, median $0.26. The label is the **flow day**; NGI prints are trade-dated. |
| Elliott | 12/22 6.54 · **12/23 30.16** · 12/24–26 no print · 12/27 35.00 · 12/28 5.90 — the narrative series has nothing from 12/22 to 01/04 |
| known disagreement | flow 2023-02-03: dashboard 26.06 vs NGI 71.42 (traded Feb 2) vs ISO-NE composite 76.42; also NGI 01-31 13.49 vs dashboard 02-01 4.85. The 10:00 snapshot can precede the final assessment on extreme days, hence NGI-first precedence (PRECOMMIT §2-A). |

**Read by no code.** Wiring it (with the NGI-first precedence rule and the flow-day basis) is limb A of the PRECOMMIT.
Adding the missed NGI mentions to `algonquin_citygate_daily.csv` would change the keeper's `gas_daily_shape` input
(armed, K), so they are recorded as evidence here and enter only through the arm.

**Licensing.** S&P Global Market Intelligence's assessment, displayed by EIA, is the same case as the NGI series
(`docs/data-licensing.md` §5, flagged for owner review and not resolved here).
