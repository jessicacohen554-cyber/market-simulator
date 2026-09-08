# EIA delivered-to-electric-power gas price, EVERY state + US (`N3045<ST>3`, monthly)

`eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv` — EIA monthly
**Natural Gas Price Sold to Electric Power Consumers** ($/Mcf) for all 50 states,
DC and the US aggregate, 2018-01 .. 2026-06, on a complete state x month grid
(`NA` where EIA publishes no figure). Landed by lane SPP-49
(`docs/handoffs/FINDING-spp-49-2026-09-08.md`; owner ruling P19, 2026-09-08).

Schema: `state, series, year, month, price_usd_mcf`.

## Source

EIA series `N3045<ST>3` and `N3045US3`, pulled **2026-09-08** from the key-free
dnav history workbooks `https://www.eia.gov/dnav/ng/hist_xls/N3045<ST>3m.xls`
(the SPP-11 route; this environment carries no `EIA_API_KEY`). Each workbook's
`Data 1` sheet is transcribed cell for cell (date serial -> `year`/`month`,
value column -> `price_usd_mcf`). The 52 workbooks are NOT committed (52 x
~40 KB); their identity is recorded in
`SHA256SUMS_N3045_state_workbooks_2026-09-08.txt` and re-fetching the URL above
regenerates the file. The four SPP-state files committed by SPP-11/SPP-15
(`eia_delivered_gas_{OK,KS,TX,NM}_monthly_*.csv`) reproduce from this table
value for value over their windows (checked at intake). Public domain (EIA).

## Consumer

`src/market_sim/data/fuel/plant_prices.py` — the EIA-923 own-month gas-price
plausibility screen (`ScenarioConfig.f923_gas_price_plausibility_screen`,
SPP-46 R-1): a plant's own-reported month is read against ITS OWN STATE's series
here ($/Mcf / 1.036); a month outside [0.5, 2.0] x the reference falls back to
the reference. Where a state-month is `NA` the consumer uses `N3045US3` for that
month (documented fallback, counted in the run log); where the reference is
<= 0 (real Waha / Permian negative-basis months — NM 2024-08, 2025-10; AZ
2026-04; WY 2022-02) the band is undefined and the month is left unscreened.

## Coverage, 2018-2026 (months published per year)

Complete (12/12) for 2022-2024 in every state except DC, HI and VT (never
published) and DE (2 months in 2022, otherwise never). 2025 is thin in many
states — OK, CO, FL, GA, KY, ME, MN, MS, NC, NH, OR, RI, WA, AL(12), AR(1),
MO(1), WV(1), WY(4) — and pre-2022 is thin or absent for AL, AR, CO, FL, KY,
LA, ME, MN, MO, MS, NH, OK, OR, WA, WV, WY. The US series is complete
throughout. **New Mexico prints negative delivered prices** (2024-08 -0.16,
2025-10 -0.80, 2026-03/04/05) and so do AZ 2026-04 and WY 2022-02; these are
real negative-basis episodes, carried verbatim (see `SOURCES_spp_gas.md`).
