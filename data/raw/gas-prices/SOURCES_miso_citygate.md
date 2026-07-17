# MISO gas-basis citygate proxies

## Monthly (EIA state citygate)

`eia_citygate_IL_MI_monthly_2023-2025.csv` — EIA monthly Natural Gas Citygate
Price ($/Mcf), 2023-01 .. 2025-12.
  - Illinois citygate (series N3050IL3)  -> Chicago Citygate proxy
  - Michigan citygate (series N3050MI3)  -> MichCon proxy

Source: EIA API v2 `natural-gas/pri/sum` (monthly). Pulled 2026-06-22.

Caveat: these are EIA utility-citygate state averages, NOT the ICE
Chicago-Citygate / MichCon daily trading-hub spot indices. $/Mcf ~= $/MMBtu
within ~3% for pipeline-quality gas (HHV ~1.037 MMBtu/Mcf).

## Daily (Chicago Citygate — EIA NG Weekly spot table)

`miso_citygate_daily.csv` — daily Chicago Citygate delivered-gas spot, 2023-2025
(680 weekday prints), columns `date, chicago_citygate_usd_mmbtu,
henry_hub_usd_mmbtu, source`.

Source: the **"Chicago"** row of the EIA Natural Gas Weekly Update compact
"Spot Prices ($/MMBtu)" table, `https://www.eia.gov/naturalgas/weekly/
archivenew_ngwu/YYYY/MM_DD/` (one page per publication Thursday). Regeneration:
`scripts/fetch_miso_citygate_daily.py` (default rebuild 2023-2025; `--merge`
freezes committed in-sample rows while densifying a holdout year). This is the
MISO analogue of `caiso_citygate_daily.csv` ("Cal. Comp. Avg" row) and
`transco_z6_ny_daily.csv` ("New York" row) — the same free EIA-displayed table.

**Why daily:** the monthly proxy (above) is mean-preserving and cannot form a
cold-snap tail. The daily series captures the within-month blowout on its true
calendar day — e.g. Winter Storm Heather's Friday **2024-01-12 Chicago Citygate
$25.82/MMBtu** (+$12.74 over Henry Hub $13.08), the day that priced storm-weekend
delivery — which both the flat monthly basis (+$1.82) and national Henry-Hub
`gas_daily_shape` miss. Consumed by the `miso_winter_citygate_daily` winter
fuel-security overlay in `src/market_sim/data/fuel.py` (flow-date placement:
Friday's print prices the Sat-Mon-holiday weekend package).

**MichCon daily is NOT available free:** the EIA compact table carries no
MichCon/Michigan row and the narrative never quotes a MichCon daily print
(verified across the 2023-2025 archive), so lower-Michigan's citygate daily
remains the paywalled ICE manual-download item (`docs/multi-iso/miso-data-audit.md`
Item 4). Chicago Citygate is the representative MISO North/Central winter gas hub
for the overlay (rule-11 reconciliation: use the accessible measured regional
hub; document the sub-source limit).

**Licensing:** the Chicago spot print is NGI's Daily Gas Price Index compiled by
Bloomberg that EIA merely *displays* — the same proprietary-index provenance
flagged for the sibling AGT/CA/NY daily files (`README.md` licensing note;
`docs/data-licensing.md` §5). Not resolved here; carried forward for owner review.
