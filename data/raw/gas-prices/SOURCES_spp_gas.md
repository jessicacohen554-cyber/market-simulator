# SPP delivered-to-electric-power gas price proxies

`eia_delivered_gas_{OK,KS,TX,NM}_monthly_2023-2025.csv` — EIA monthly
**Natural Gas Price Sold to Electric Power Consumers** ($/Mcf) for the four
states the SPP footprint's gas fleet burns in, 2023-01 .. 2025-12. Landed by
lane SPP-11 (`docs/handoffs/FINDING-spp-11-2026-09-06.md`;
`docs/multi-iso/spp-addition-plan-2026-09.md` §6 row 4).

Schema is the committed `eia_citygate_IL_MI_monthly_2023-2025.csv`
convention: `period, series, description, area-name, process-name, value,
units`; `value` is `NA` where EIA publishes no figure.

## Source

EIA series `N3045<ST>3`, pulled **2026-09-06** from the key-free dnav history
workbooks (this environment carries no `EIA_API_KEY`, so the API v2
`natural-gas/pri/sum` route the MISO citygate files used is unavailable):

| State | Series | URL |
|---|---|---|
| OK | `N3045OK3` | `https://www.eia.gov/dnav/ng/hist_xls/N3045OK3m.xls` |
| KS | `N3045KS3` | `https://www.eia.gov/dnav/ng/hist_xls/N3045KS3m.xls` |
| TX | `N3045TX3` | `https://www.eia.gov/dnav/ng/hist_xls/N3045TX3m.xls` |
| NM | `N3045NM3` | `https://www.eia.gov/dnav/ng/hist_xls/N3045NM3m.xls` |

The four workbooks as published on that date are committed beside the CSVs as
`eia_N3045<ST>3m_2026-09-06.xls` — the `eia_N3050CA3m_2026-09-04.xls`
evidence precedent (caiso-246). Each workbook's `Data 1` sheet spans 2002-01
.. 2026-06; the CSVs are its 2023-01 .. 2025-12 window transcribed cell for
cell (`Sourcekey` → `series`, the sheet title → `description`, the date
serial → `period`, the value column → `value`). Re-fetch the xls and re-cut
the window to regenerate. Public domain (EIA).

## What this is, and what it is not

This is EIA's **survey of what electric generators actually paid**, delivered,
per state — a measured delivered-fuel price of exactly the class rule 13
`[R-MEASURED]` admits and the same product family the model already consumes
for other ISOs. It is **not** a trading-hub index: it is a monthly
volume-weighted average across every generator in the state, so it is
mean-preserving and cannot form a within-month cold-snap tail (the same
caveat `SOURCES_miso_citygate.md` records for its monthly proxy, and the
reason MISO added a daily series alongside).

$/Mcf ≈ $/MMBtu within ~3 % for pipeline-quality gas (HHV ≈ 1.037 MMBtu/Mcf).

**No zone mapping is asserted here.** Which state series proxies which SPP
zone's gas hub is SPP-32's derivation (`data/raw/spp_zonal_gas_hub.csv`, the
`caiso_zonal_gas_hub.csv` pattern) against the Panhandle Eastern / NGPL
Mid-Continent hubs the plan's §5 row names. These four files are its input.

## Coverage, and the one real gap

| State | 2023 n | 2024 n | 2025 n | 2023 mean | 2024 mean | 2025 mean | last published month |
|---|---|---|---|---|---|---|---|
| OK | 12 | 12 | **0** | 2.95 | 3.05 | — | **2024-12** |
| KS | 12 | 12 | 12 | 3.32 | 2.92 | 4.66 | 2026-06 |
| TX | 12 | 12 | 12 | 2.63 | 2.18 | 3.18 | 2026-06 |
| NM | 12 | 12 | 12 | 1.99 | 0.81 | 2.40 | 2026-06 |

**OKLAHOMA STOPS AT 2024-12.** Every month of 2025 is blank in EIA's own
published `N3045OK3` series while KS/TX/NM run through 2026-06 — so all twelve
2025 rows of `eia_delivered_gas_OK_monthly_2023-2025.csv` are `NA`. This is
the source's gap, not the fetch's: it is visible in the committed workbook and
on the dnav page `hist/n3045ok3m.htm`. It matters more than its size suggests,
because Oklahoma is the single most SPP-relevant of the four (OKGE + CSWS +
WFEC + GRDA are 36 % of SWPP demand), and 2025 is a scored calibration year.
**A consumer must not silently fall back to a national or Henry-Hub figure for
those months** — either use a neighbouring state's series with the
substitution documented, or use the pipeline-hub route (rule 14
`[R-ACCURATE]`: prefer the accurate input, document the misalignment). Flagged
for SPP-32.

**New Mexico prints negative delivered prices** — 2024-08 −0.16, 2025-10 −0.80
(and −2.77 / −3.26 / −2.88 in 2026-03/04/05, outside these files). These are
real Permian/Waha negative-basis episodes, not data errors: San Juan and
Permian gas has cleared below zero when takeaway is constrained. They are
carried verbatim. Any consumer that floors fuel cost at zero should do so
explicitly and say why, rather than treating the print as bad data.

## Back years

2019-2022 and 2026 are available in the same workbooks (they span 2002-01
onward) and are a later rule-22 intake, not this lane's. Nothing here is
solved or scored.
