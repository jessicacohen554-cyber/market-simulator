# SOCO delivered-to-electric-power gas price proxies

`eia_delivered_gas_{AL,GA,MS}_monthly_2023-2025.csv` — EIA monthly **Natural Gas
Price Sold to Electric Power Consumers** ($/Mcf) for the three states the SOCO
(Southern Company) footprint's gas fleet burns in, 2023-01 .. 2025-12. Landed by
lane SOCO-12 (`docs/handoffs/FINDING-soco-12-2026-09-13.md`;
`docs/multi-iso/soco-addition-plan-2026-09.md` §6 row 4).

Schema is the committed `eia_delivered_gas_{OK,KS,TX,NM}_monthly_2023-2025.csv`
(SPP-11) convention: `period, series, description, area-name, process-name,
value, units`; `value` is `NA` where EIA publishes no figure.

## Source

EIA series `N3045<ST>3`, pulled **2026-09-13** from the key-free dnav history
workbooks (this environment carries no `EIA_API_KEY`, so the API v2
`natural-gas/pri/sum` route the MISO citygate files used is unavailable — the
same block SPP-11 recorded and the plan's §2.4 predicted):

| State | Series | URL |
|---|---|---|
| AL | `N3045AL3` | `https://www.eia.gov/dnav/ng/hist_xls/N3045AL3m.xls` |
| GA | `N3045GA3` | `https://www.eia.gov/dnav/ng/hist_xls/N3045GA3m.xls` |
| MS | `N3045MS3` | `https://www.eia.gov/dnav/ng/hist_xls/N3045MS3m.xls` |

The three workbooks as published on that date are committed beside the CSVs as
`eia_N3045<ST>3m_2026-09-13.xls` — the `eia_N3045<ST>3m_2026-09-06.xls` (SPP-11)
and `eia_N3050CA3m_2026-09-04.xls` (caiso-246) evidence precedent. Each
workbook's `Data 1` sheet spans 2002-01 .. 2026-06; the CSVs are its 2023-01 ..
2025-12 window transcribed cell for cell (`Sourcekey` → `series`, the sheet title
→ `description`, the date serial → `period`, the value column → `value`).
Re-fetch the xls and re-cut the window to regenerate. Public domain (EIA).

**Cross-checked at intake against the committed all-state table**
`eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv` (SPP-49):
**108 of 108 state-months agree exactly, 0 mismatches** — including which months
are `NA`. The per-state files add nothing the all-state table lacks; they exist
because the per-ISO consumer convention reads them, and the cross-check is the
evidence that the two routes are the same numbers.

## What this is, and what it is not

This is EIA's **survey of what electric generators actually paid**, delivered,
per state — a measured delivered-fuel price of exactly the class rule 13
`[R-MEASURED]` admits and the same product family the model already consumes for
the other seven regions. It is **not** a trading-hub index: it is a monthly
volume-weighted average across every generator in the state, so it is
mean-preserving and cannot form a within-month cold-snap tail. That caveat is
load-bearing for SOCO specifically, because the footprint's two most recent
annual peaks are **January** events (see the FINDING §1.3 and
`../soco-planning/README.md` §3).

$/Mcf ≈ $/MMBtu within ~3 % for pipeline-quality gas (HHV ≈ 1.037 MMBtu/Mcf).

**No zone mapping is asserted here.** Which state series proxies which SOCO zone's
gas hub is SOCO-32's derivation (the `caiso_zonal_gas_hub.csv` pattern). These
three files are its input.

## Coverage, and the one real gap

| State | 2023 n | 2024 n | 2025 n | 2023 mean | 2024 mean | 2025 mean | last published month |
|---|---:|---:|---:|---:|---:|---:|---|
| AL | 12 | 12 | 12 | 3.083 | 2.817 | 4.242 | 2025-12 |
| GA | 12 | 12 | **0** | 3.233 | 2.971 | — | **2024-12** |
| MS | 12 | 12 | **0** | 2.830 | 2.711 | — | **2024-12** |

$/Mcf, computed over published months only. **Georgia and Mississippi publish
nothing for 2025** — the same class of gap SPP-11 recorded for Oklahoma, and it
falls inside the 2023–2025 backcast span. Two consequences, stated rather than
patched: a 2025 SOCO solve has a measured delivered-gas price for **Alabama
only**; and whatever SOCO-32 does about GA/MS 2025 (hold-last, the `N3045US3`
national series the SPP-49 consumer already uses as its documented fallback, or
the AL series as the in-footprint neighbour) is a **declared modelling choice**
that belongs in its own derivation, not an invisible fill here. Nothing is
interpolated in this directory.

## The pipeline basis the footprint actually prices against — and the daily-index answer

**Basis.** The Southern Company footprint's own gas transporter is **Southern
Natural Gas Company, L.L.C. ("SNG")** — Southern Company Gas holds a **50 %
equity interest** in it (Southern Company FY2025 Form 10-K, Item 1, "Southern
Company Gas … Southern Natural Gas Company, L.L.C., a pipeline system in which
Southern Company Gas has a 50% ownership interest";
`https://www.sec.gov/Archives/edgar/data/92122/000009212226000006/so-20251231.htm`).
**Transcontinental Gas Pipe Line ("Transco")** reaches the northern half of the
Georgia Power zone through the jointly-owned **Dalton Pipeline**, a 115-mile
Transco extension into northwest Georgia in which Southern Company Gas leases a
50 % undivided interest through 2042 (same 10-K, PROPERTIES, note (e)). So the
plan's "Transco Zone 4 / Southern Natural Gas" naming is **correct on both legs**
and neither is redundant: SNG is the system-wide transporter, Transco Z4 the
north-Georgia path.

**Is a public daily or monthly index for that basis reachable? NO — measured,
not assumed.** Both free EIA routes that carry daily hub prints for the other
ISOs were checked on 2026-09-13 and neither carries a Southeast hub:

- **EIA Natural Gas Weekly Update** compact "Spot Prices ($/MMBtu)" table
  (`https://www.eia.gov/naturalgas/weekly/`) — the table the committed
  `miso_citygate_daily.csv` ("Chicago"), `caiso_citygate_daily.csv`
  ("Cal. Comp. Avg") and `transco_z6_ny_daily.csv` ("New York") are all built
  from — carries exactly four rows: **Henry Hub, New York, Chicago,
  Cal. Comp. Avg.** No SNG, no Transco Zone 4, no Southeast row. The narrative
  quotes **Florida Gas Zone 3** for the region, which is Florida's receipt point,
  not SOCO's.
- **EIA daily "Select Spot Prices for Delivery Today"**
  (`https://www.eia.gov/todayinenergy/prices.php`) — its published region→gas-point
  map is New England/Algonquin Citygate, New York City/Transco Zone 6-NY,
  Mid-Atlantic/TETCO-M3, Midwest/Chicago Citygate, Louisiana/Henry Hub,
  Houston/Houston Ship Channel, Southwest/El Paso San Juan. **No Southeast
  region at all.**

This is the `SOURCES_miso_citygate.md` "MichCon daily is NOT available free"
finding, one footprint over: the daily index at SOCO's own basis is a paywalled
ICE/NGI product. The monthly EIA state delivered-to-EP series above is the
reachable measured input, and a SOCO winter-gas tail overlay — if one is ever
wanted — has **no free daily source** behind it today. Recorded for owner review
alongside the licensing note in `README.md` / `docs/data-licensing.md` §5.
