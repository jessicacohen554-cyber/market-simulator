# nyiso-renewable-curtailment — raw

NYISO's own coarse **annual + monthly, NYCA-wide and zonal** economic/real-time
wind (and, from 2022, FTM solar) curtailment estimates, hand-transcribed from
NYISO's annual "NYCA Renewables" presentation deck to Market Issues Working
Group / Installed Capacity Working Group. This is **not** a per-plant hourly
uncurtailed-potential (HSL) series — NYISO does not publish one comparable to
ERCOT NP6 or CAISO's Production-and-Curtailment workbooks (see
`data/raw/nyiso-hsl/` and `market_sim.data.renewables` module docstring, which
remain the stubbed/empty hourly-HSL marker). This datatype is the coarse
annual/monthly/zonal diagnostic aggregate that *does* exist, landed so it shows
up on the data-completeness register instead of living only as inline code
comments.

## Files

- `nyiso_curtailment_annual.csv` — one row per (resource_type, geographic_scope,
  year): `curtailed_energy_gwh`, `curtailed_pct` (NYCA rows only — zones don't
  publish their own percent-of-production), `source_doc` (presentation
  filename), `source_page` (slide number(s)), `notes`.
- `nyiso_curtailment_monthly.csv` — one row per (resource_type,
  geographic_scope, year, month): `curtailed_pct` for NYCA-wide rows (percent
  of that month's wind production), `curtailed_energy_gwh` for zone rows
  (West / Central / North / Mohawk Valley — NYISO's four highest-wind-density
  zones; zones don't publish a monthly percent).

`geographic_scope="NYCA"` is the system-wide aggregate; the other values are
the specific curtailment-reporting zone.

## Source

NYISO annual "NYCA Renewables" presentation (Cameron McPherson / NYISO
Operations Analysis & Services), presented to ICAPWG/MIWG, published at
nyiso.com/reports-information:

| Deck | URL |
|---|---|
| 2020-nyca-renewables-presentation.pdf | `https://www.nyiso.com/documents/20142/20078222/4%202020%20NYCA%20Renewables%20Presentation%20Final.pdf/655aaa4d-bf68-2875-023a-e0cd4dcbd096` |
| 2021-nyca-renewables-presentation.pdf | `https://www.nyiso.com/documents/20142/29607069/5%202021%20NYCA%20Renewables%20Presentation%20FINAL.pdf/6aea8337-b7ef-4e10-a4e8-d34dcef54ccf` |
| 2022-nyca-renewables-presentation.pdf | `https://www.nyiso.com/documents/20142/36845856/2022%20NYCA%20Renewables%20Presentation%20FINAL.pdf/65f48ad8-cf06-4a7f-8d1a-2cd716380063` |
| 2023-nyca-renewables-presentation.pdf | `https://www.nyiso.com/documents/20142/29609937/2023-NYCA-Renewables-Presentation.pdf/b4b189e8-e213-baf1-9f81-ac425342a2ea` |
| 2025-nyca-renewables-presentation.pdf | `https://www.nyiso.com/documents/20142/57614757/2025%20NYCA%20Renewables%20Presentation%20FINAL.pdf/ba816875-47ba-b13d-6495-2043bd8b12ca` (presented 2026-04-08; covers full-year 2025 with trailing 3-year 2022-2024 comparison charts) |

Each deck reports a **trailing multi-year window** (annual GWh/% tables) plus
**zonal annual + monthly detail for its own current year only** — so a single
deck never gives the full history; the years above were cross-checked against
every deck whose trailing window overlaps (e.g. 2020's wind curtailment % is
printed in the 2020, 2021, and 2022 decks alike, and all three agree). PDFs are
not committed here (consistent with the `gas-prices/nyiso_downstate_*`
convention of citing the exact source URL rather than storing the multi-MB
deck) — refetch with the URLs above if re-verification is needed.

## DATA NEEDED (documented gaps — do not fabricate)

- **No standalone 2024 deck found.** Search of nyiso.com/reports-information
  and web search turned up no "2024 NYCA Renewables Presentation." The 2024
  NYCA-wide annual GWh/% figures used here come from the 2025 deck's trailing
  4-year comparison chart (which is how NYISO itself reports 2024 alongside
  2025) — but no 2024 zonal or monthly breakdown exists anywhere; a 2024 row is
  therefore absent from the zonal/monthly tables, not zero.
- **No pre-2020 zonal/monthly breakdown.** The 2020 deck is the earliest found
  and gives zonal/monthly detail only for its own year (2020); NYCA-wide annual
  wind curtailment reaches back to 2017 (trailing-window table in the 2020
  deck), but 2017-2019 zonal/monthly rows do not exist in any found source.
- **No FTM solar curtailment reported before 2022** — NYISO's FTM solar fleet
  was small enough before then that the presentations don't track it
  separately (first appears as a distinct "RT Market Curtailments: FTM Solar"
  section in the 2025 deck's trailing chart, covering 2022-2025).
- **No zonal/monthly breakdown for FTM solar at all** — only the NYCA-wide
  annual/monthly aggregate is published for solar.
- **No H1 2026 curtailment data published yet** — the 2025 deck (presented
  April 2026) covers only calendar-year 2025; NYISO's unrelated net-load "duck
  curve" charts in the same deck extend into early 2026 but carry no
  curtailment content.
- **Percent-of-production not printed for FTM solar 2022/2023** — only GWh
  figures were published for those two years; `curtailed_pct` is left blank
  rather than back-computed, so it is never confused with a directly-printed
  source figure.

## Regeneration

Hand-transcribed from the primary-source PDFs above (no automated fetcher —
NYISO does not expose this as a machine-readable API/CSV). Re-verify against
the cited URLs if the deck is superseded or a new year's deck is published.

## Consumer

`scripts/curate_nyiso_renewable_curtailment.py` -> `market_sim.data.nyiso_renewable_curtailment`
(a labeled coarse-aggregate diagnostic; does **not** feed the hourly HSL/
uncurtailed-potential path used by dispatch — see that module's docstring).
