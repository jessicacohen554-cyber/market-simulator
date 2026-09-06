# SPP Data-Acquisition Audit (Phase 0)

Lane **SPP-10** · 2026-09-06 · branch `claude/spp-10-miso-audit-wowrmp` · MODEL Opus
`claude-opus-5` · DATA PROFILE `shared`.

Charter: `docs/multi-iso/spp-addition-plan-2026-09.md` §5 row SPP-10. Template:
`docs/multi-iso/miso-data-audit.md`. Process authority:
`docs/multi-iso/05-backcast-playbook.md` §1 (Phase 0) and §8.

**This lane RECOMMENDS. It decides nothing.** No topology is chosen here, no
`src/`, `scripts/`, `configs/`, `tests/`, `frontend/` or `data/` file is touched, no
parameter is derived (rule 23 `[R-FROZEN-DERIVE]`), no mechanism is tested and no
mechanism-matrix cell moves (rule 28). Every number below is either **measured off a
committed repo artifact** (with the reproduction command in §7) or **cited to a
primary published source** (URL + page/table). A cell with neither is written
`pending SPP-11/12` — never a guess (rules 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`).

The desk serves cards **P1** (topology), **P6** (`TAIL_THRESHOLD`) and **P7** (screen
year) from §5–§6 of this document.

---

## 0. Headline

1. **The fleet census reconciles.** EIA-860 `Balancing Authority Code == "SWPP"`
   gives **828 plants / 715 with operable generators / 1,646 generators /
   103,330.8 MW nameplate**. SPP's own MMU publishes **102,792 MW** at year-end
   2024 and **106,291 MW** at year-end 2025. The repo's committed EIA-860 vintage
   (2025 Early Release) sits between them at **+0.5 % / −2.8 %** — the expected
   place. Every technology row reconciles with a stated reason (§1.3).
2. **The missing-CEMS list in the plan was wrong on two states — and the gap is now
   CLOSED.** The correct set is **{NE, NM, OK} × {2023, 2024, 2025} = 9 files**, not
   `{OK, NE, NM, WY} × 3`: **WY has zero SWPP plants** in EIA-860 and needs no
   extract, and **CO** is in the footprint but carries only 19.5 MW of small solar
   and **zero CEMS-eligible units**, so it needs none either. **Lane SPP-11 landed
   all of OK/NE/NM/WY × 2023–2026 on the same day** (16 parquets,
   `FINDING-spp-11-2026-09-06.md`), so the critical path is unblocked; the four
   **`WY_*` files are inert** for SPP (`load_campd_hourly` filters every loaded
   state to the ISO's own fleet, so they cost storage, not correctness). The
   census's job here is now the *forward* one: it says which states
   `campd.ISO_STATES["SPP"]` should list, and it records what the gap **was** worth —
   **44.9 % of SPP's CEMS-eligible fossil capacity**, including **61 % of the
   gas-CC fleet** and **37 % of the coal fleet** (§2).
3. **The committed EIA-930 `SWPP hourly.parquet` carries three defective hours in
   the 2023–2025 window** — one 100× demand/net-gen/wind spike (2023-06-12 21:00),
   one 94 %-low demand dropout that propagates a physically impossible 33.3 GW
   export (2025-06-21 05:00), and one 11.1 GW export outlier (2024-07-19 00:00).
   The existing `_screen_demand_spikes` catches the first; **nothing in the repo
   catches the other two** (§3.4). This is SPP-20/SPP-31 work and it is named here
   before any solve.
4. **`NG: BAT` is 100 % null for every hour of 2015–2025** in the SWPP file
   (§3.3). SPP battery output is not observable from EIA-930 in any backcast year.
5. **The measured congestion is not on the N↔S corridor.** SPP's MMU reports that
   **seven of the top ten constraints by average shadow price in 2025 were in
   Oklahoma**, with the two highest-value pockets in **northern and southern
   Oklahoma** — both entirely *inside* the proposed SPP-South zone — and names
   **Oklahoma City, Tulsa, Lubbock and Kansas City** as the 2024 Frequently
   Constrained Areas. Total congestion rent was **$1.6 bn in 2025**. §5 sets out
   what this does and does not do to card P1: the 2-zone N/S recommendation
   survives as the *first* topology, but the plan's pre-declared third-zone lever
   (SPS/Panhandle, SPP-54) ranks **below an Oklahoma pocket** on measured
   congestion value, and the audit recommends the desk hear that before freezing
   the lever queue.

---

## 1. Status table

| # | Item | Source | Status | File path | Notes |
|---|------|--------|--------|-----------|-------|
| 1 | SPP fleet census (plants / MW by fuel & prime mover & state) | EIA-860 2025 Early Release, `Balancing Authority Code == "SWPP"` | **got** | `data/raw/eia-860/eia860_plant.parquet` + `eia860_generator_operable.parquet` | 828 plants (715 with operable gens), 1,646 generators, 103,330.8 MW nameplate / 97,070.4 MW summer. Reconciles to SPP MMU SOM 2025 Fig 2–12 (§1.3). |
| 2 | CAMPD/CEMS state coverage vs the SWPP footprint | `data/raw/campd-unit-level/<ST>_<yr>.parquet` | **got** (was **partial** when this census ran) | 13 of 14 footprint states present; `CO` absent and not needed | The gap this census identified was **`NE`, `NM`, `OK` × 2023–2025 (9 files)** — **not** `WY`, which has zero SWPP plants, and **not** `CO`, which is in the footprint but has zero CEMS-eligible units. **Closed the same day by lane SPP-11**, which landed OK/NE/NM/**WY** × 2023–2026 (16 parquets, 16 columns, schema == `KS_2024`). The four `WY_*` files are **inert for SPP** but harmless. What the gap was worth: 44.9 % of CEMS-eligible fossil MW (§2.4). |
| 3 | EIA-930 SWPP hourly demand + fuel mix | EIA Hourly Electric Grid Monitor | **got (3 defective hours)** | `data/raw/eia-930-hourly/SWPP hourly.parquet` | 95,424 rows, 2015-07-01 → 2026-05-21 local; 8,760/8,784/8,760 rows for 2023/24/25. Cross-validates to SPP's published 2025 fuel mix within 0.14 pp and its published 2023 summer peak within 0.3 %. Three artifact hours + `NG: BAT` all-null (§3). |
| 4 | EIA-930 SWPP per-BA extracts | EIA API v2 | **got** | `data/raw/SWPP_fueltype.parquet` (1,527,168 rows), `SWPP_region.parquet` (381,792 rows) | Long-form twins of item 3, UTC-stamped. Same `BAT` gap. |
| 5 | SPP hourly hub LMP (RT + DA) | SPP Integrated Marketplace via `portal.spp.org` | **got (system hub only)** | `data/raw/_validation-source/actual_lmp_hourly_SPP.parquet` | 3 × 8,760 confirmed, `year/hour/rt/da`. It is the **arithmetic mean of `SPPNORTH_HUB` and `SPPSOUTH_HUB`**, not a zonal series. 6–12 null hours/yr (§4). |
| 6 | Per-hub (N / S) hourly LMP | same | **blocked → SPP-12** | `_validation-source/actual_lmp_hourly_zonal_SPP.parquet` (does not exist) | The P1/P7 hourly evidence. Portal file-browser API has moved (plan §2.4). |
| 7 | `actual_lmp.json` SPP block | `scripts/data/derive_actual_lmp.py` | **absent** | `data/raw/_validation-source/actual_lmp.json` | Keys are exactly `ERCOT, PJM, CAISO, NYISO, NEISO, MISO`. **SPP-31's job**, not this lane's. |
| 8 | EIA-923 monthly delivered fuel costs, SPP plants | EIA-923 | **got** | `data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet` | Coal: 325 / 290 / 297 rows over 30 / 29 / 27 plants for 2023/24/25. Gas: 765 / 753 / 662 rows over 66 / 65 / 57 plants. This is the rule-13 measured fuel input the playbook §0.5 requires. |
| 9 | EIA-923 monthly generation, SPP plants | EIA-923 | **got (2025 partial)** | `data/raw/_processed-legacy/eia923_monthly_generation.parquet` | SWPP plant-rows 993 (2023) / 1,031 (2024) / **361 (2025)** — the 2025 vintage is a preliminary release with far fewer reporters. Nuclear (Wolf Creek 210, Cooper 8036) is present for every year 2018–2025. **SPP-30/31 must verify 2025 coverage before relying on it.** |
| 10 | eGRID plant database | EPA eGRID 2023 | **got (national)** | `data/fleet/egrid2023_data_rev2.xlsx` | `zone_assignment._EGRID_VINTAGE = 2023` is a **module-level scalar, not a per-ISO dict** — SPP needs no entry (§4 row 17). |
| 11 | SWPP sub-BA identities (the zonal-load spine) | EIA-930 six-month sub-region extract | **got (names only)** | not committed — read from `EIA930_SUBREGION_2025_Jan_Jun.csv` | **17 sub-BAs confirmed**: CSWS EDE GRDA INDN KACY KCPL LES MPS NPPD OKGE OPPD SECI SPRM SPS WAUE WFEC WR. Annual energy per sub-BA is **SPP-11's** deliverable. |
| 12 | SPP published fleet / load / curtailment / congestion / gas | SPP MMU State of the Market 2024 & 2025; SPP Fast Facts | **got** | cited inline, PDFs not committed | The primary benchmark set. Fetched with a browser UA over `curl`; `WebFetch` gets HTTP 503 from `spp.org` (§7). |
| 13 | SPP Planning Criteria (PRM) | `spp.org` Planning Criteria Rev 4.1A and 4.7 | **got** | cited inline | PRM **15 %** for 2023–2025; **16 % summer / 36 % winter** from 2026 (§4 row 1). |
| 14 | Offer cap / VOLL | SPP MMU Order 831 Verification FAQ v4.0; SPP Tariff Att. AF §3.2 | **got** | cited inline | $1,000/MWh soft cap, **$2,000/MWh hard cap** (§4 row 2). |
| 15 | Reserve / scarcity demand curves (VRL) | SPP MMU SOM 2024 §3.2.3 | **partial** | cited inline | **Maxima cited** (regulation 6 steps → $600/MW; contingency reserve 3 steps → $1,100/MW; ramp 6 steps, monthly-updated, 2024 max $32/MW). The **step breakpoints are not in the SOM** — Market Protocols / Tariff Att. AE. **SPP-12.** |
| 16 | N↔S transfer capability, SPS tie ratings | SPP ITP report; `oasis.oati.com/SWPP` | **blocked** | — | OASIS blocked (plan §2.4). ITP transcription is **SPP-12 → SPP-20**. §6 manifest row 3. |
| 17 | SPP long-term load forecast (LTLF) edition + vintage | `spp.org` ITP / 20-Year Assessment / RSC briefings | **blocked → SPP-12** | `data/raw/load-forecast/spp/spp.csv` (does not exist) | A **W2 precondition** (plan §7 G12): `scripts/lib/load_forecast/spp.py` cannot register without a real edition and vintage ≥ 2020. Candidate URLs in §6. |
| 18 | Zonal / area hourly load | EIA-930 sub-BA (item 11); SPP Marketplace hourly-load | **got** (was **pending** when this census ran) | `data/raw/zone-specific-demand/SPP/spp_subba_demand_2023-2025.csv` + `SOURCES.md` | **Landed the same day by lane SPP-11**: 447,049 rows, 17 sub-BAs, no interior gaps, reconciling to 0.9995–0.9999 of the BA `Demand`. The load side of every topology option in §6.3 is now feasible — which is why topology is a card and not a default (plan §2.5). |
| 19 | Wind/solar curtailment (HSL analogue) | SPP MMU SOM | **partial** | cited inline | Average hourly wind curtailment **1,483 MW (2024) → 1,382 MW (2025)**, from 137 MW in 2019. No annual **percentage** is printed; 2023 is chart-only. **SPP-12** transcribes Fig 2–30/2–33. |
| 20 | Gas basis (Panhandle Eastern), coal base (PRB) | SPP MMU SOM 2024/2025 §4; EIA-923 | **got** | cited inline + item 8 | HH − Panhandle = **$0.38 (2023) / $0.26 (2024) / $0.55 (2025) per MMBtu**; PRB 8,800 Btu/lb **$0.78 (2024) → $0.81 (2025) /MMBtu** (§4 rows 8–9). |

---

## 2. Item 1/2 — the fleet census and the CEMS state diff

### 2.1 Method

`data/raw/eia-860/eia860_plant.parquet` filtered to `Balancing Authority Code ==
"SWPP"`, inner-joined on `Plant Code` to `eia860_generator_operable.parquet`. This is
the **same BA-code crosswalk the model itself uses** (`zone_assignment._ISO_TO_BA_CODE`,
`fleet.models.BA_CODE_TO_ISO`) — SPP's future entry is `"SWPP"`, already recorded in
`00-iso-addition-protocol.md` §1 Stage B. `get_iso_config("SPP")` was **not** called: it
does not exist. Vintage: the top-level (current) release, documented in
`data/raw/eia-860/README.md` as the **2025 Early Release** snapshot, i.e. end-2024
operable plus early-2025 additions.

Neighbouring BA codes were checked and deliberately **excluded**: `WAUW` (24 plants,
MT/UT/WY — WAPA Upper Great Plains *West*, a WECC balancing authority, not SPP),
`AECI` (39 plants — Associated Electric Cooperative, a non-member with >5,000 MW of AC
interties to SPP), `SPA` (34 plants — Southwestern Power Administration federal hydro,
>1,500 MW of interties). SPP's own MMU describes AECI and SPA as **intertie
counterparties, not footprint** (SOM 2025 §2.8, PDF p.70), so the BA-code filter is the
right boundary. `SPA` is the one to watch: its hydro is marketed *into* SPP and SPP-33
should say explicitly whether it is a seam or a fleet member.

### 2.2 Census — 1,646 operable generators, 103,330.8 MW nameplate

| Technology | Plants | Gens | Nameplate MW | Summer MW | Winter MW |
|---|---:|---:|---:|---:|---:|
| Onshore Wind Turbine | 231 | 255 | 35,473.4 | 35,388.0 | 35,401.4 |
| Conventional Steam Coal | 29 | 49 | 20,279.3 | 19,197.1 | 19,185.9 |
| Natural Gas Fired Combustion Turbine | 74 | 161 | 12,809.7 | 10,935.5 | 11,849.6 |
| Natural Gas Fired Combined Cycle | 23 | 73 | 11,606.0 | 10,167.3 | 10,883.6 |
| Natural Gas Steam Turbine | 41 | 70 | 11,240.4 | 10,469.5 | 10,389.8 |
| Conventional Hydroelectric | 23 | 85 | 3,103.5 | 2,930.0 | 2,929.2 |
| Petroleum Liquids | 141 | 402 | 2,374.6 | 1,901.6 | 2,121.2 |
| Nuclear | 2 | 2 | 2,097.3 | 1,945.2 | 2,023.5 |
| Natural Gas Internal Combustion Engine | 75 | 344 | 1,736.5 | 1,622.0 | 1,631.1 |
| Solar Photovoltaic | 141 | 143 | 1,441.8 | 1,438.0 | 1,424.3 |
| Batteries | 14 | 14 | 451.5 | 451.1 | 451.1 |
| Wood/Wood Waste Biomass | 4 | 8 | 294.5 | 255.8 | 255.8 |
| Hydroelectric Pumped Storage | 1 | 6 | 259.2 | 241.5 | 241.5 |
| All Other | 3 | 9 | 62.0 | 40.8 | 60.8 |
| Other Gases | 3 | 5 | 59.3 | 47.2 | 47.2 |
| Landfill Gas | 6 | 16 | 22.0 | 21.1 | 21.1 |
| Municipal Solid Waste | 1 | 1 | 16.8 | 15.6 | 15.8 |
| Other Waste Biomass | 1 | 3 | 3.0 | 3.0 | 3.0 |
| **TOTAL** | **715** | **1,646** | **103,330.8** | **97,070.4** | **98,935.8** |

By prime mover: `WT` 35,473.4 · `ST` 33,989.6 · `GT` 14,421.0 · `CT` 6,853.3 · `CA`
4,437.4 · `HY` 3,103.5 · `IC` 2,524.8 · `PV` 1,441.8 · `BA` 451.5 · `CS` 315.3 · `PS`
259.2 · `OT` 60.0 MW. The `CA`+`CT`+`CS` triple is the combined-cycle fleet; `IC` at 734
generators for 2,524.8 MW is the distributed reciprocating-engine tail (mean 3.4 MW/unit).

### 2.3 Reconciliation against SPP's published fleet

**Source:** SPP Market Monitoring Unit, *State of the Market 2025*, **Figure 2–12
"Generation nameplate capacity by technology type", report p.37 (PDF p.49)** —
<https://www.spp.org/documents/76798/2025_annual_state_of_the_market_report.pdf>. Its
2023/2024 columns overlap *State of the Market 2024* Figure 2–13, report p.29 (PDF
p.42) — <https://www.spp.org/documents/73953/2024_annual_state_of_the_market_report.pdf>
— with **one restatement SPP-30 must know about**: SOM 2024 prints `Gas, simple-cycle`
YE-2024 as **22,017 MW**, SOM 2025 restates it as **23,017 MW**, while both print the
same YE-2024 **total of 102,792 MW**. Column arithmetic settles it: SOM 2025's 2024
column sums to 102,804 (12 MW of rounding off its printed total), and its 2023 and 2025
columns to 100,453 and 106,291 (13 MW off, and exact); **SOM 2024's 2024 column sums to
101,804 — 988 MW short.** The later vintage, **23,017 MW**, is the one that reconciles.
Rule 14 `[R-ACCURATE]`: the conflict is named, not buried.

| SPP MMU technology | YE-2023 MW | YE-2024 MW | YE-2025 MW | This census (2025 ER) | Reconciliation |
|---|---:|---:|---:|---:|---|
| Wind | 33,725 | 34,808 | 35,934 | 35,473.4 | **−1.3 % vs YE-2025.** Vintage sits between the two years. ✔ |
| Coal | 22,062 | 22,065 | 21,975 | 20,279.3 | **−7.7 %.** EIA-860's *operable* sheet drops units retired before the ER cut; SPP counts the market-registered fleet at year-end. **SPP-30 must confirm against the retired sheet** before treating the difference as fleet error. |
| Gas, simple-cycle | 22,614 | 23,017 | 24,180 | 25,786.6 (GT + gas-ST + IC) | **+6.6 %.** SPP has no separate gas-steam row, so its "simple-cycle" is *all non-CC gas*. The excess is the sub-market reciprocating tail (734 `IC` units). ✔ |
| Gas, combined-cycle | 13,619 | 13,619 | 13,395 | 11,606.0 | **−13.4 %.** Direction is opposite to the row above; the pair nets to **+5.1 %** on total gas. Most likely a CC/CT classification seam (some EIA `GT` units are SPP-registered as CC blocks). **Named, not resolved — SPP-30.** |
| Hydro | 3,431 | 3,431 | 3,429 | 3,362.7 (hydro + PS) | −2.0 %. ✔ |
| Nuclear | 2,061 | 2,061 | 2,061 | 2,097.3 | +1.8 % (nameplate vs SPP's accredited-style rating). ✔ |
| Oil | 1,569 | 1,622 | 1,646 | 2,374.6 | **+44 %.** 141 plants / 402 generators averaging 5.9 MW — EIA-860 counts standby diesels SPP never registers. ✔ expected. |
| Solar | 484 | 986 | 2,114 | 1,441.8 | Between YE-2024 and YE-2025, as the vintage implies. ✔ |
| Demand response | 793 | 970 | 1,016 | — | **No EIA-860 analogue.** SPP's DR is a market product, not a generator. Flagged for SPP-20's adequacy ledger. |
| Market storage resource | 12 | 142 | 422 | 451.5 (batteries) + 259.2 (PS) | SPP counts only **market-registered** storage — 14 resources / 728 MW at YE-2025 including 6 pumped-storage (SOM 2025 §2.7, PDF p.70). EIA-860 counts all. ✔ |
| Other | 83 | 83 | 119 | 398.3 (biomass + LFG + MSW + other) | EIA-860 superset. ✔ |
| **Total** | **100,440** | **102,792** | **106,291** | **103,330.8** | **+0.5 % vs YE-2024, −2.8 % vs YE-2025.** ✔ |

**Verdict:** the census reconciles. EIA-860 `SWPP` is a **superset** of SPP's
market-registered fleet (small diesels, unregistered batteries, no DR analogue) read at
a vintage that straddles calendar 2025. Two rows carry a real open question — the coal
shortfall and the CC/CT classification seam — and both are named as **SPP-30 exit
checks**, not resolved here.

Cross-checks on the same sources: SPP Fast Facts (updated September 2026,
<https://www.spp.org/about-us/fast-facts/>) reports **1,013 generating plants** in the
East BA (this census: 828 plants in EIA-860, 715 with operable generators — SPP counts
registered market resources, which split some EIA plants), **accredited** generating
capacity of **65,639 MW** as of June 2025, and a coincident peak of **56,184 MW on
2023-08-21**. The Fast Facts "West BA" (166 plants) is **WEIS, not the Integrated
Marketplace** — it is outside the `SWPP` EIA-930 balancing authority and outside this
census. Do not add it.

### 2.4 States, and the CEMS diff — the plan's list is wrong on WY and CO

Distinct SWPP plant states, with MW (this census):

| State | Plants | Gens | Nameplate MW | Summer MW | CEMS-eligible fossil >25 MW (MW) | `campd-unit-level/<ST>_{2023,2024,2025}` |
|---|---:|---:|---:|---:|---:|---|
| OK | 131 | 280 | 32,272.3 | 30,304.9 | 17,388.3 | **MISSING** |
| KS | 190 | 503 | 20,968.9 | 19,970.8 | 8,460.4 | present |
| TX | 55 | 99 | 13,013.0 | 12,462.1 | 8,994.4 | present |
| NE | 131 | 303 | 12,089.8 | 11,440.1 | 6,753.2 | **MISSING** |
| MO | 62 | 171 | 8,785.0 | 7,895.9 | 7,026.4 | present |
| ND | 15 | 50 | 4,930.0 | 4,548.4 | 2,645.9 | present |
| SD | 31 | 68 | 4,384.7 | 4,152.4 | 853.9 | present |
| NM | 32 | 44 | 2,826.2 | 2,629.8 | 1,346.0 | **MISSING** |
| AR | 28 | 43 | 2,209.8 | 2,060.3 | 1,855.8 | present |
| LA | 4 | 7 | 1,049.5 | 901.5 | 977.0 | present |
| IA | 18 | 46 | 538.7 | 486.0 | 300.6 | present |
| MT | 3 | 9 | 168.2 | 125.0 | 108.2 | present |
| MN | 7 | 15 | 75.2 | 73.7 | 0.0 | present |
| **CO** | 8 | 8 | 19.5 | 19.5 | **0.0** | **not needed** |
| **TOTAL** | **715** | **1,646** | **103,330.8** | **97,070.4** | **56,710.1** | |

**The missing list, corrected:**

```
NE_2023.parquet  NE_2024.parquet  NE_2025.parquet
NM_2023.parquet  NM_2024.parquet  NM_2025.parquet
OK_2023.parquet  OK_2024.parquet  OK_2025.parquet
```

Nine files, not twelve. Two corrections to the expectation in the SPP-10 charter and in
`01-data-needs-and-upload-manifest.md` §3:

* **`WY` is NOT in the SPP footprint.** Zero EIA-860 plants carry
  `Balancing Authority Code == "SWPP"` in Wyoming. Wyoming SPP-adjacent generation
  (e.g. Laramie River) files under `WAUW`, a WECC balancing authority. **No `WY`
  extract is needed for SPP.** The `WY` entry in doc 01's SPP row is an error of
  provenance, corrected in this lane's doc-01 edit.
* **`CO` IS in the footprint** (8 plants) but every one is small solar — Denver Intl
  Airport IV Solar, Airport 1 Solar (DIA), Oak Leaf Solar XVIII, and five Oak Leaf CSG
  portfolio sites, 1.5–9.0 MW each, 19.5 MW total. **Zero CEMS-eligible units, so no
  `CO` extract is needed either** — but `campd.ISO_STATES["SPP"]` should list it
  anyway, exactly as `PJM` lists `NC` "for completeness" and as the NYISO `NJ` / CAISO
  `NV` precedents do: `load_campd_hourly` warns and skips a state with no file, and
  every loaded state is filtered to the ISO's own fleet, so listing it cannot leak.

**Materiality of the gap — this is the critical path (plan §4).**

| Class | SWPP total MW (fossil > 25 MW) | In NE + NM + OK | Share unobservable |
|---|---:|---:|---:|
| Conventional Steam Coal | 20,235.8 | 7,504.5 (14 plants) | **37.1 %** |
| Natural Gas Fired Combined Cycle | 11,586.2 | 7,091.4 (13 plants) | **61.2 %** |
| Natural Gas Steam Turbine | 11,026.5 | 6,627.9 (13 plants) | **60.1 %** |
| Natural Gas Fired Combustion Turbine | 12,391.4 | 3,936.6 (20 plants) | **31.8 %** |
| **All CEMS-eligible fossil** | **56,710.1** | **25,487.5** | **44.9 %** |

Across all technologies the three states hold **294 of 715 plants and 47,188.3 MW of
103,330.8 MW (45.7 %)**. Named coal units in the blind spot include Nebraska City
(1,389.6 MW), Gerald Gentleman (1,362.6), Sooner (1,138.0), GREC (594.0), Muskogee
(572.0), Northeastern (473.0), Hugo (446.0), North Omaha (353.6), River Valley (350.0),
Whelan (324.3), Sheldon (228.7), Lon Wright (130.0), Platte (109.8).

Until SPP-11 lands these nine files, **SPP-30 cannot derive unit-outage windows,
committed percentages or thermal tranches for nearly half the thermal fleet**, and any
solve before then is a copperplate with a full-year availability fallback across the
plurality of its dispatchable capacity — exactly the plan's G4 failure. The charter's
critical path `SPP-11 → SPP-20 → SPP-30 → SPP-40` is confirmed, and it is the OK/NE
CEMS pull that sets it.

---

## 3. Item 3/4 — EIA-930 SWPP

### 3.1 Shape and span

`data/raw/eia-930-hourly/SWPP hourly.parquet` — **95,424 rows**, span **2015-07-01
01:00 → 2026-05-21 00:00 local** (`2015-07-01 06:00 → 2026-05-21 05:00` UTC).
Columns (17): `UTC time`, `Local date`, `Hour`, `Local time` (all `datetime64[us]` /
`int64`), then `float32` `Demand forecast`, `Demand`, `Net generation`,
`Total interchange`, `NG: COL`, `NG: NG`, `NG: NUC`, `NG: WAT`, `NG: SUN`, `NG: WND`,
`NG: OIL`, `NG: BAT`, `NG: OTH`. Schema is identical to the six registered ISOs' files.

Rows per calendar year: 2019 8,760 · 2020 8,784 · 2021 8,760 · 2022 8,760 · **2023
8,760 · 2024 8,784 · 2025 8,760** · 2026 3,359 (partial). Full training-window
coverage, no calendar gap. The timezone map is already correct:
`fetch_eia930_hourly.py:53` and `convert_eia930.py:61` both carry
`SWPP → America/Chicago`.

### 3.2 Energy and peaks (spike hour excluded — see §3.4)

| Year | Demand TWh | Net gen TWh | COL | NG | NUC | WAT | SUN | WND | OIL | OTH |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 280.571 | 284.487 | 78.401 | 76.324 | 17.176 | 8.343 | 0.589 | 103.045 | 0.216 | 0.394 |
| 2024 | 290.007 | 291.830 | 72.538 | 83.376 | 15.468 | 8.989 | 1.200 | 109.758 | 0.101 | 0.400 |
| 2025 | 299.478 | 302.136 | 87.703 | 75.948 | 16.240 | 8.830 | 2.348 | 110.457 | 0.022 | 0.588 |

Fuel shares of net generation: 2023 wind 36.22 % / coal 27.56 % / gas 26.83 % / nuclear
6.04 % / hydro 2.93 % / solar 0.21 %; 2024 wind 37.61 / coal 24.86 / gas 28.57 / nuclear
5.30 / hydro 3.08 / solar 0.41; 2025 wind 36.56 / coal 29.03 / gas 25.14 / nuclear 5.38 /
hydro 2.92 / solar 0.78. The `NG:` columns sum to `Net generation` to within **0.6 MW
mean absolute residual** in every year — the file is internally consistent.

**Cross-validation against SPP's own published figures — this is the strongest evidence
the file is the right object:**

| Quantity | SPP published | EIA-930 SWPP (this file) | Δ |
|---|---|---|---|
| 2025 net generation | 300,382 GWh (Fast Facts) | 302,136 GWh | +0.58 % |
| 2025 fuel mix (wind/gas/coal/nuclear/hydro/solar) | 36.7 / 25.1 / 29 / 5.4 / 2.9 / 0.7 % (Fast Facts) | 36.56 / 25.14 / 29.03 / 5.38 / 2.92 / 0.78 % | ≤ 0.14 pp on every fuel |
| 2025 wind energy | ~110,200–110,400 GWh (SOM 2025, PDF p.62) | 110,457 GWh | +0.2 % |
| Summer coincident peak | 56,184 MW on **2023-08-21** (Fast Facts) | 56,010 MW at **2023-08-21 17:00** | −0.31 %, same day |
| Winter peak | 48,142 MW on **2025-02-20** (Fast Facts) | 47,946 MW at **2025-02-20 08:00** | −0.41 %, same day |
| 2025 minimum hourly load | 23,378 MW (SOM 2025 Fig 2–10, report p.35 / PDF p.47) | 24,390 MW (2nd-lowest; lowest is the §3.4 artifact) | +4.3 % |
| 2025 maximum hourly average load | 52,124 MW (SOM 2025, same page) | 54,411 MW | **+4.4 % — a convention difference, not an error** |

The last two rows are the **benchmark-convention caveat for SPP-31**: SPP's MMU counts
market-settled participant energy and an *hourly-average* load, EIA-930 counts BA
metered demand. The same gap shows on annual energy — SOM 2025 Fig 2–8 reports a
system total of **268,712 / 277,652 / 285,997 GWh** for 2023/24/25 against EIA-930's
280.6 / 290.0 / 299.5 TWh, a consistent **4.3–4.5 %**. SPP-31 must choose one basis and
say which; it must not mix them inside one benchmark.

### 3.3 Interchange convention, and the `NG: BAT` hole

**Sign convention: `Total interchange` is positive = NET EXPORT.** Verified on 2024:
`corr(Net generation − Demand, Total interchange) = 0.836`, with
`mean(NG − D) = 207.6 MW` against `mean(TI) = 188.5 MW`. Annual means are
`+447.0 / +188.5 / +269.6 MW` for 2023/24/25 — SPP is a **net exporter** in every
training year, consistent with the MMU's account of wind-driven exports. Per-year p1 /
p50 / p99: `−1,745 / +534 / +2,045` (2023), `−2,596 / +310 / +1,915` (2024),
`−2,228 / +291 / +2,515` (2025) MW. This is the scalar series that `_SCALAR_INTERCHANGE_ISOS`
would serve under card P2 (plan §3), and it is rule-13 admissible on exactly the
PJM/NYISO/NEISO precedent.

**`NG: BAT` is present as a column and 100 % NULL for every hour of 2015–2025.** The
first non-null hour is in **2026** (2026 partial-year total 0.072 TWh, 840 of 3,359
hours still null). SPP battery output is therefore **not observable from EIA-930 in any
backcast year**, which matters because SPP's registered market storage grew 12 → 142 →
422 MW over 2023–2025 (SOM 2025 Fig 2–12). Consequence, stated for SPP-31 and SPP-40:
there is **no measured storage benchmark for SPP in the training window**, so the
retired C5b/C5c storage criteria have no analogue to reinstate and the model's
451.5 MW battery + 259.2 MW pumped-storage fleet dispatches unvalidated. Not a blocker
— it is a declared blind spot.

### 3.4 THREE DEFECTIVE HOURS — and only one of them is already screened

| Local hour | Demand MW | Net gen MW | Total interchange MW | `NG: WND` MW | Diagnosis |
|---|---:|---:|---:|---:|---|
| 2023-06-12 21:00 | **3,621,097** | **3,617,992** | −537 | **3,589,445** | ~100× unit slip. Demand is 117.7× the 2023 median (30,769 MW). `NG: WND` is inflated on the same hour — the hour alone adds **+3.62 TWh to 2023 demand and +3.59 TWh to 2023 wind**. |
| 2025-06-21 05:00 | **1,505** | 34,810 | **+33,305** | — | Demand dropout. The next-lowest 2025 hour is **24,390 MW** and SPP's own published 2025 minimum is **23,378 MW**, so this reading is ~94 % low. Because `TI ≡ NG − D` in this file, it propagates a **33.3 GW net export** — six times SPP's largest real tie capability. |
| 2024-07-19 00:00 | 24,991 | 36,062 | **+11,071** | — | Partial demand dropout; an 11.1 GW export against a p99 of +1,915 MW. |
| 2024-07-10 01:00 | NaN | NaN | +344 | — | Ordinary missing-meter hour; handled by the existing `interpolate().bfill().ffill()`. |

**What the repo already catches, and what it does not:**

* `data/eia930/demand.py::_screen_demand_spikes` (threshold **2.5×** the annual median)
  **catches the 2023 hour** — 117.7× is far past the bar. No new mechanism is needed
  for it, and the screen's own docstring promise ("a no-op on any year whose peak stays
  under the threshold — every 2023–2025 training year does") stays true for the six
  registered ISOs: it fires on SPP and nowhere else. **This is a fact SPP-20 must state
  in its FINDING**, because the docstring will otherwise read as false once SPP lands.
* `_screen_demand_dropouts` flags **only readings of exactly `0.0`**, by deliberate
  design ("a whole BA's metered demand is never 0 MW, so an exactly-zero reading is an
  artifact by construction and needs no threshold"). **1,505 MW is not zero**, so
  **neither 2025-06-21 05:00 nor 2024-07-19 00:00 is caught by anything in the repo
  today.**
* **Neither screen touches the fuel-mix columns.** The 2023 `NG: WND` inflation flows
  straight into any fuel-mix benchmark built from this file — i.e. into SPP-31's
  `calibration_reference.json` generation totals and the C4 fuel-mix criterion.

**Recommendation to SPP-20 / SPP-31 (recommend, do not decide).** Three separable
questions, in this order:

1. **The 2023 wind inflation is a benchmark defect, not a demand defect**, and it is
   the one that would silently corrupt a scored criterion. The narrowest fix that
   stays inside rule 13 is to apply the *same* median-ratio test the demand screen
   already uses to the `NG:` columns when they are read for a benchmark, and to
   interpolate the flagged hour. Whoever does it must prove the six registered ISOs'
   benchmarks are **byte-identical** afterwards (plan §7 G9).
2. **The low-side demand gap is a real hole in `_screen_demand_dropouts`**, and SPP is
   the first ISO to expose it. It is *not* SPP-specific and a fix is *not* free: a
   low-side threshold is a new screen parameter with a cache-key risk (plan §7 G8),
   and the docstring's warning about ERCOT's genuine `0.0` interchange hours shows the
   care this class of screen needs. **Route it to the desk as a card**, do not let
   SPP-20 improvise it. Meanwhile the artifact is documented here and SPP-40's PRECOMMIT
   can name it as a known 1-in-8,760 defect.
3. **Do not repair the raw file.** `data/raw` is immutable (`00-iso-addition-protocol.md`
   §4, plan §5 SPP-11). Every repair belongs in the loader.

### 3.5 The per-BA extracts

`data/raw/SWPP_fueltype.parquet` — 1,527,168 rows, columns `period` (UTC-aware),
`iso`, `fueltype`, `type_name`, `value_mwh`; `data/raw/SWPP_region.parquet` — 381,792
rows, columns `period`, `iso`, `type`, `type_name`, `value_mwh` (`D` = Demand, etc.).
Long-form twins of §3.1 on the same span; the `BAT` series is null on the same hours.
No separate defect.

---

## 4. Item 5 — the price sidecar

`data/raw/_validation-source/actual_lmp_hourly_SPP.parquet` (383,004 bytes), built by
`scripts/data/build_spp_lmp_reference.py`.

**3 × 8,760 confirmed.** 26,280 rows; `year` `int16` ∈ {2023, 2024, 2025}, 8,760 rows
each; `hour` `int16` covering 0…8,759 with 8,760 distinct values in every year; `rt`
and `da` `float32`. The fixed non-leap local-clock calendar matches
`derive_actual_lmp.py`.

**It is the N/S hub MEAN, not a zonal series.** The builder's own docstring: *"System
hub = simple mean of `SPPNORTH_HUB` and `SPPSOUTH_HUB` (the two SPP trading hubs)."* It
was built for a different purpose — anchoring **MISO's** SPP-seam neighbour price
(`derive_neighbor_hr_by_year.py --iso MISO`) — and it carries no zonal information at
all. `actual_lmp_hourly_zonal_SPP.parquet` **does not exist**; producing it is **SPP-12's**
deliverable (plan §6 row 5) and it is the P1/P7 hourly evidence.

**`actual_lmp.json` has NO SPP block.** Its keys are exactly `ERCOT, PJM, CAISO, NYISO,
NEISO, MISO`. Adding one is **SPP-31's** job (plan §5), with the exit check that every
other ISO's block stays byte-identical.

Nulls: `rt` 6 / 12 / 6 hours and `da` 6 / 6 / 6 hours for 2023/24/25. In context, that
is unremarkable — CAISO carries 48 `rt` / 120 `da` nulls in 2023, NYISO 2 in 2025,
MISO 1 in 2025 — but SPP-31 should confirm `derive_actual_lmp.py`'s null handling
before scoring.

**Distribution (measured off the committed file; supplied as P5/P6 evidence).**

| Year | series | mean | p50 | p95 | p99 | max | > $100 | > $200 | > $300 | < $0 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | rt | 23.47 | 20.85 | 61.85 | 142.32 | 856.84 | 152 | **42** | 15 | **992** |
| 2023 | da | 25.60 | 23.88 | 55.44 | 81.70 | 240.55 | 43 | 6 | 0 | 483 |
| 2024 | rt | 23.31 | 18.80 | 72.83 | 172.00 | 1,077.82 | 260 | **59** | 16 | **1,172** |
| 2024 | da | 25.92 | 21.57 | 64.49 | 138.65 | 563.55 | 156 | 35 | 15 | 641 |
| 2025 | rt | 27.11 | 23.04 | 70.59 | 176.91 | 1,093.22 | 213 | **68** | 32 | **1,018** |
| 2025 | da | 28.72 | 27.63 | 62.78 | 84.09 | 176.62 | 25 | 0 | 0 | 610 |

Two readings the desk should take from this table:

* **Card P6 (`TAIL_THRESHOLD`): the evidence supports $200.** RT hours above $200 are
  42 / 59 / 68 per year — a populated, year-discriminating tail. At $300 the counts
  fall to 15 / 16 / 32, thin enough that a single storm week dominates the criterion.
  $200 also matches the ERCOT/PJM/MISO/CAISO regime peers rather than the NYISO/NEISO
  city-gate-gas pair, which is the plan's own stated rationale. **This is measured on
  the hub MEAN**; SPP-12's per-hub series may move the counts, and SPP-31 must
  regenerate `actual_tail.json` from whatever series becomes the SPP benchmark.
* **SPP is a deeply negative-price market: 992 / 1,172 / 1,018 RT hours below $0 —
  11.3 % / 13.4 % / 11.6 % of all hours.** That is the wind-curtailment signature
  (§4 row 10) showing up in price. It is structural, not a defect, and it is the single
  biggest reason SPP's price formation will not look like MISO's. SPP-40's screen gate
  should expect it; a model that produces few negative hours is wrong even if its MAE
  is good (rule 1 `[R-STRUCT]`).

---

## 5. THE REGISTRY-VALUES TABLE

One row per value **SPP-20 will need**. Every cell is a **cited value** or **pending**.
Nothing here is a decision; where a registry needs a judgment the row says whose.

| # | Registry / value | Candidate | Primary citation | Status |
|---|---|---|---|---|
| 1 | `PLANNING_RESERVE_MARGIN_BY_ISO["SPP"]` | **0.15** for the 2023–2025 backcast | SPP **Planning Criteria Rev 4.1A**, published 2023-05-12, §4 "Planning Reserve Margin", p.9: *"The Planning Reserve Margin ('PRM') shall be fifteen percent (15%)."* <https://www.spp.org/documents/69547/spp%20planning%20criteria%20v4.1a.pdf> | **cited** |
| 1b | — forecast-lane successor, **not** a W2 value | 2026 S **16 %** / W **36 %**; 2027–2028 same; 2029 S **17 %** / W **38 %** | SPP **Planning Criteria Rev 4.7**, published 2026-04-21, §4, p.11 (table reproduced verbatim). <https://www.spp.org/documents/76543/spp%20planning%20criteria%20v4.7.pdf> | **cited — ROUTE TO capx** |
| 2 | `voll` / offer cap | **$2,000/MWh** hard cap (soft cap $1,000/MWh with MMU verification) | SPP MMU **Order 831 Verification FAQ v4.0**, revised 2021-04-01, **Q25 p.5**: *"incremental energy offers above $1,000/MWh and less than or equal to $2,000/MWh that are verified by the MMU prior to market clearing and used in price formation, will be used in the settlement process."* Underlying instrument: **SPP Tariff Attachment AF §3.2**. <https://www.spp.org/documents/64402/spp%20mmu%20order%20831%20verifcation%20faq%20v4.pdf> | **cited** — matches the plan's P5 `voll=2000.0` |
| 3 | VRL / reserve demand curves — **maxima** | Regulation up **and** down: **6 steps, max $600/MW**. Contingency reserve: **3 steps, max $1,100/MW**. Ramp capability up/down: 6 steps, maximum reset monthly from three months of historical offers; **highest monthly maximum in 2024 was $32/MW** | SPP MMU **State of the Market 2024**, §3.2.3 "Scarcity pricing", **report p.98 (PDF p.111)**. <https://www.spp.org/documents/73953/2024_annual_state_of_the_market_report.pdf> | **cited (maxima only)** |
| 3b | VRL — **step breakpoints** (MW and intermediate $) | — | Not in the SOM. SPP Market Protocols / Tariff **Attachment AE**. | **pending SPP-12 PDF** |
| 4 | State→zone map candidate, `_SPP_STATE_ZONES` | **North**: ND SD NE MN MT IA KS MO (+ CO) · **South**: OK TX NM AR LA. **`WY` must be dropped** — no SWPP plant is in Wyoming (§2.4). **`CO`** carries 19.5 MW of solar; it is a defensible North member or a `_LARGEST_ZONE` fallback case | This audit §2.4 (EIA-860 census) | **measured** — but see the straddle below |
| 4b | **The straddling states, and what resolves them** | **KS and MO both straddle** the SPP North/South seam in the sense that matters: SPP's *hubs* are node clusters (row 5), not state aggregates, so a state map cannot be validated against them. **The resolving instrument is the sub-BA**, not the state: `WR`, `SECI`, `KACY`, `MPS`, `KCPL`, `EDE`, `SPRM`, `INDN` (KS/MO) vs `CSWS`, `OKGE`, `WFEC`, `GRDA`, `SPS` (OK/TX/NM/AR/LA). **`EDE` (Liberty/Empire District) is the one genuinely mixed sub-BA** — it serves MO, KS, OK and AR. **`WAUE`** spans ND SD MN NE MT IA, all North. **`CSWS` (AEP: PSO + SWEPCO)** spans OK, AR, LA and east TX, all South | EIA-930 sub-BA list (§ item 11); SPP MMU SOM 2025 Fig 2–8 (participant identities), report p.33 / PDF p.45 | **measured (names)** · **energy now landed** by SPP-11 in `zone-specific-demand/SPP/spp_subba_demand_2023-2025.csv`; SPP-20 sizes the `EDE` straddle off it |
| 5 | EIA-930 sub-BA → zone grouping candidate | **North (12)**: `EDE` `INDN` `KACY` `KCPL` `LES` `MPS` `NPPD` `OPPD` `SECI` `SPRM` `WAUE` `WR` · **South (5)**: `CSWS` `GRDA` `OKGE` `SPS` `WFEC` | 17 sub-BAs confirmed present in `EIA930_SUBREGION_2025_Jan_Jun.csv` (§ item 11). Identities are the utilities' own service territories | **candidate** — grouping is SPP-20's call, energy weights are SPP-11's |
| 6 | `load_share` fallback from sub-BA annual energy | the identifying source is now on disk: `data/raw/zone-specific-demand/SPP/spp_subba_demand_2023-2025.csv` (447,049 rows, 17 sub-BAs, landed by SPP-11) | EIA-930 sub-BA; **SPP-20 computes the shares**, this lane does not (rule 23) | **unblocked.** **Independent corroboration, from a different source**: SPP MMU SOM 2025 **Fig 2–8 "System energy consumption, by market participant"**, report p.33 (PDF p.45), gives every participant's GWh for 2023/2024/2025. Rolled up on the North/South participant identities, 2025 reads **North 143,433 GWh (50.2 %) / South 141,762 GWh (49.6 %) / unattributed marketers 801 GWh (0.3 %)** against a system total of 285,997 GWh. **This is a cross-check, NOT a `load_share`** — if SPP-20's sub-BA shares land far from ~50/50, one of the two attributions is wrong and it should be resolved before the shares are written |
| 7 | Interchange posture (`_SCALAR_INTERCHANGE_ISOS`) | Measured EIA-930 `Total interchange`, **positive = net export**, verified §3.3 | This audit §3.3 | **measured** — card P2 |
| 8 | Gas basis proxy | **Panhandle Eastern** is SPP's own reference hub. Henry Hub **minus** Panhandle Eastern = **$0.38/MMBtu (2023), $0.26 (2024), $0.55 (2025)**. Panhandle annual average **$2.16 (2023)**, **$1.98 (2024)**, **$2.97–2.98 (2025)**; Southern Star tracks Panhandle at $2.98 in 2025; Henry Hub $3.53 in 2025 | SPP MMU **SOM 2025** §4, **report p.119 (PDF p.131)**, Figure 4–4 discussion. 2023 value: SPP MMU **SOM 2024** §4, **PDF p.127**. <https://www.spp.org/documents/76798/2025_annual_state_of_the_market_report.pdf> | **cited** — ⚠ **restatement**: SOM 2024 printed Panhandle 2024 as **$1.81**; SOM 2025 restates it as **$1.98**. Use the later vintage and record the discrepancy (rule 14) |
| 8b | Gas basis — the *measured* input the backcast actually uses | Per-plant **EIA-923 monthly delivered gas cost**: 765 / 753 / 662 rows over 66 / 65 / 57 SWPP plants for 2023/24/25 | `data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet` | **got** — playbook §0.5 makes this the backcast source; row 8 is the **forecast seed** and the sanity check |
| 8c | EIA state delivered-to-EP gas series (OK KS TX NM) | `data/raw/gas-prices/eia_delivered_gas_{OK,KS,TX,NM}_monthly_2023-2025.csv` + `SOURCES_spp_gas.md` | EIA, via lane SPP-11 | **got** — landed the same day (was **pending** when this census ran) |
| 9 | Coal price base | **PRB 8,800 Btu/lb: $0.78/MMBtu (2024) → $0.81/MMBtu (2025)**, mine-mouth. Delivered, at SPP plants: EIA-923 mean **$1.919 (2023) / $1.810 (2024) / $1.786 (2025)** per MMBtu over 30 / 29 / 27 plants | Mine-mouth: SPP MMU **SOM 2025** §4, report p.119 (PDF p.131). Delivered: `eia923_monthly_fuel_costs.parquet` | **cited + measured** |
| 10 | Wind curtailment reference rate | Average hourly wind curtailment **137 MW (2019) → 1,483 MW (2024) → 1,382 MW (2025)**. Solar curtailment averages **10 MW/h**, 0.73 % of total curtailments. **2023 is chart-only** (SOM 2024 says only that 2023 was the first year curtailments fell) | SOM 2025 §2.6, **report p.54 (PDF p.66)**, Figures 2–30/2–31; SOM 2024 **report p.47 (PDF p.60)**, Figure 2–33 | **partial** — no published annual **%**. The MISO `_miso_wind_reference_curtailment_rate` pattern needs a rate; **SPP-12 transcribes the chart, SPP-32 decides**. The arithmetic a rate would come from is stated here and **deliberately not performed** (rule 23) |
| 11 | Nuclear monthly CF candidates | **Wolf Creek** (EIA plant 210, KS, 1,296.3 MW, COD 1985) and **Cooper** (EIA plant 8036, NE, 801.0 MW, COD 1974) — the only two SPP nuclear units. Annual net generation MWh: Wolf Creek 10,301,865 / 9,204,226 / 9,269,040 and Cooper 6,926,053 / 6,095,731 / 6,921,979 for 2023/24/25 | `data/raw/_processed-legacy/eia923_monthly_generation.parquet` (`ba_code == "SWPP"`) | **measured** — ⚠ the CF **basis** (nameplate vs net summer) is SPP-31's to fix; ⚠ the **2025 EIA-923 vintage is partial** (361 SWPP plant-rows vs 1,031 in 2024) |
| 12 | `QUEUE_CAP_PER_TECH_GW["SPP"]` | On the registry's **own documented convention** ("modestly above demonstrated peak annual COD", `capacity_market.py`), the demonstrated peak annual COD by tech from EIA-860 `SWPP` operating years is: **2021–2025** wind 3.416 / solar 0.563 / gas_ct 1.019 / gas_cc 0.000 / storage 0.422 GW; **2015–2025** wind 3.886 / solar 0.563 / gas_ct 1.019 / gas_cc 0.600 / storage 0.422 GW | This audit (EIA-860 census, `Operating Year` by technology) | **measured — a CANDIDATE, not a value.** The window and the step are the registry's convention and **SPP-20's call**, not this lane's |
| 12b | Queue context for the same row | End-2025 SPP GI queue **≈149 GW**, of which renewable + storage + hybrid ≈114 GW (76 %); by type **solar 25 % / gas 24 % / battery-storage 21 % / wind 17 % / hybrid 13 %**. Wind in queue 30 → 25 GW; solar 44 → 37 GW; batteries +6 GW → 31 GW; hybrid → 25 GW; **gas 14 → 35 GW** (≈9 GW of it via the FERC-approved 2025-05-06 ERAS process). On-schedule executed requests ≈35 GW, of which wind 12 GW | SPP MMU **SOM 2025** §2.5, **report p.42–43 (PDF p.54–55)**, Figures 2–17/2–18 | **cited** — a *queue*, not a throughput ceiling; the cap must stay a COD-based number (row 12) |
| 13 | `STATE_RPS_FLOORS["SPP"]` | **Recommend registering ERCOT-style all-zero for W2** and routing the real row to the forecast lane. Rationale: `pipeline.backcast_config` sets `rps_enabled=False`, so **no backcast builds an RPS row at all** — the value is inert for SPP-40's keeper (`capacity_market.py` STATE_RPS_FLOORS["CAISO"] comment block). Footprint statutes: **KS — mandate REPEALED**, converted to a voluntary 20 %-of-peak-by-2020 goal by House Sub. for SB 91 (2015), effective 2016-01-01 (<https://www.kslegislature.gov/li_2016/b2015_16/measures/documents/sb91_enrolled.pdf>); **OK / ND / SD — voluntary goals only**; **NE — none** (public power); **MO — 15 % by 2021, IOUs only** (Prop C, RSMo §393.1030); **NM — Energy Transition Act 2019 (SB 489), 50 % renewable by 2030, 80 % by 2040, 100 % zero-carbon by 2045 for IOUs** (SPS is an NM IOU); **TX — 5,880 MW goal, long met**; **AR / LA — none**; **MN / IA / MT — SPP shares are 75.2 / 538.7 / 168.2 MW, immaterial** | as cited | **recommendation with a stated cost.** An all-zero row silently asserts "no binding RPS", which is true for the backcast and **arguable for the forecast** (MO and NM are real). **Route the forecast row to the capx director with card P8**, do not let W2 invent it |
| 14 | `STATE_RPS_ACP["SPP"]` | Not needed if row 13 is all-zero — ERCOT has no ACP for exactly that reason (`capacity_market.py:4898`) | same | **follows row 13** |
| 15 | LTLF edition + vintage for `scripts/lib/load_forecast/spp.py` | — | — | **pending SPP-12.** **A W2 PRECONDITION** (plan §7 G12: `test_specs_declare_an_edition_and_a_vintage`). Candidate editions to probe, in order: the **SPP ITP load forecast** (ITP Manual v3.2, <https://spp.org/documents/76063/itp%20manual%20version%203.2.pdf>), the **20-Year Assessment Load Forecasts and Generation Retirements** deck (<https://spp.org/documents/64383/20-year%20assessment%20load%20forecasts%20and%20generation%20retirements.pdf>), and the **Joint RSC/Board stakeholder briefing 2025-11-03** (<https://spp.org/documents/75144/2025-11-03%20joint%20stakeholder%20briefing%20materials.pdf>). The MISO precedent (`load_forecast/miso.py`) is a slide deck transcribed to CSV with per-slide `source_page` provenance — expect the same shape |
| 16 | `DEMAND_GROWTH_RATES["SPP"]` | — | — | **follows row 15.** Every peer ISO's entry is cited to that ISO's LTLF |
| 17 | eGRID vintage | **No SPP entry is needed.** `zone_assignment._EGRID_VINTAGE = 2023` is a **module-level scalar shared by every ISO**, not a per-ISO dict | `src/market_sim/data/zone_assignment.py:502` | **measured — the charter's expectation of a per-ISO value is incorrect** |
| 18 | `TRANSMISSION_BASE_STATIC_VINTAGE["SPP"]` | The registry's convention is **the vintage of the ISO's own TTC source** (ERCOT 2024 = NP6-86 GTC limits; MISO 2025 = PY2025-26 LOLE CIL/CEL + JOA RDT; NYISO 2025 = measured 2024-25 DAM Central-East). SPP's TTC source is the ITP report SPP-12 transcribes, so the vintage **is** that report's year — likely **2025** (the 2025 ITP), but it must not be written before the report is in hand | `src/market_sim/data/transmission_expansion.py:65-80` | **pending SPP-12** |
| 19 | `TAIL_THRESHOLD["SPP"]` (×3 files) | **$200** — RT hours above $200 are 42 / 59 / 68 for 2023/24/25 vs 15 / 16 / 32 above $300 (§4) | this audit §4, measured off `actual_lmp_hourly_SPP.parquet` | **measured — card P6** |
| 20 | Seam capabilities (cards P2 / P3) | SPP↔MISO **>6,000 MW of AC interties**; SPP↔ERCOT **720 MW of DC ties**; SPP↔Western Interconnection **>1,000 MW of DC ties**; SPP↔SPA **>1,500 MW**; SPP↔AECI **>5,000 MW of AC** | SPP MMU **SOM 2025** §2.8, **PDF p.70** | **cited** — ⚠ **DISCREPANCY**: `constants.ERCOT_DC_TIE_ZONE_MAP["SWPP"]` carries **820 MW** (Monticello 600 + Oklaunion 220) from ERCOT's side, against SPP's published **720 MW**. The plan's card P3 assumes 820. **Reconcile explicitly (rule 14) — do not silently pick one.** Note also that **AECI at >5,000 MW is a larger AC seam than the ERCOT DC ties by a factor of seven** and appears nowhere in the plan |
| 21 | `campd.ISO_STATES["SPP"]` | `("AR","CO","IA","KS","LA","MN","MO","MT","ND","NE","NM","OK","SD","TX")` — the full footprint, **`WY` excluded**, `CO` retained for completeness on the PJM-`NC` precedent | this audit §2.4 | **measured** |
| 22 | Memory class, `run_isos_concurrent.py` | `per_plant=True, co_opt=False, peak_gb=<measured in SPP-40>` | plan §3 | **pending SPP-40** |

---

## 6. ZONE RECOMMENDATION (card P1) — recommend, do not decide

### 6.1 What the data I can see actually supports

**The N/S asymmetry is real, and SPP's own MMU states its mechanism.** SOM 2025 §4
(report p.121 / PDF p.133): *"The general pattern of higher prices in the south and
lower in the north is primarily due to fuel mix and congestion. **Coal, nuclear, and
wind are the dominant fuels in the north and west. The south and east have a much
larger share of gas generation**, hence, more exposure to changes in fuel prices."*
That is a structural statement about fleet composition, and this audit's census
corroborates it directly: both nuclear units are in KS/NE; the gas-CC fleet is
concentrated in OK/TX; wind sits across the northern and western tier. A two-zone split
is not an arbitrary cut — it separates two genuinely different marginal-cost stacks.

**The load split is almost exactly even.** SOM 2025 Fig 2–8 rolled up on participant
identity gives **North 50.2 % / South 49.6 %** of 2025 system energy (§5 row 6). A
2-zone SPP is therefore a balanced topology, not a large zone plus a pocket.

**But the two published hubs are NOT zonal aggregates, and this bounds what the hub
spread can prove.** SOM 2025 §4, same page: *"The SPP North hub represents a portion of
pricing nodes in the northern part of the SPP footprint, **generally in Nebraska**. The
SPP South hub represents a portion of pricing nodes in the south-central portion of the
footprint, **generally in central Oklahoma**."* So `SPPNORTH_HUB` − `SPPSOUTH_HUB` is a
**Nebraska-vs-central-Oklahoma two-point spread**, not a North-zone-vs-South-zone price
difference. It is still the best scorable zonal benchmark SPP publishes, and card P7's
screen statistic is still defensible — but the audit's recommendation is that **SPP-40's
PRECOMMIT state this limitation explicitly** rather than let a hub spread be read as a
zonal price validation.

**Published on-peak day-ahead hub prices** (SOM 2025 Figure 4–7, report p.122 / PDF
p.134) — the residual-blind P7 statistic, available now:

| Year | SPP North hub | SPP South hub | South − North |
|---|---:|---:|---:|
| 2023 | $32 | $34 | **+$2** |
| 2024 | $28 | $40 | **+$12** |
| 2025 | $36 | $38 | **+$2** |

**2024 is the largest-spread year by a factor of six**, and it is therefore the P7 screen-year
candidate on a published, residual-blind statistic. The MMU's own narrative agrees
(*"The spread between the North and South hubs … was around the $9/MWh range. In 2025,
the spread decreased to around $1/MWh"*). SPP-12's hourly per-hub series should confirm
this on mean and p90 |N − S| before the screen is committed; if it disagrees, SPP-12's
number wins because it is hourly and all-hours.

**The measured congestion is NOT on the N↔S corridor — this is the finding that most
affects P1.** SPP MMU SOM 2025 §5, key points, report p.152 (PDF p.164) and the
top-constraint discussion at report p.160 (PDF p.172):

* *"seven of the ten highest-valued constraints by average shadow price located in
  Oklahoma"*; the two highest-value pockets are **northern and southern Oklahoma**.
* The most congested 2025 constraint was **Osage–Webber Tap 138 kV, northern
  Oklahoma** — RT average shadow price **$75.47/MWh**, DA **$63.24/MWh**. Second was
  **Russett–South Brown 138 kV, southern Oklahoma** — RT **$61/MWh**, DA **$55/MWh**.
* The **2024 Frequently Constrained Area analysis identified Oklahoma City, Tulsa,
  Lubbock and Kansas City**; Williston ND was recommended for removal.
* Non-Oklahoma top-ten constraints: the **Edwardsville transformer (Kansas City)**, the
  **FORTIEHANWAH** market-to-market flowgate (**southeast North Dakota**, the MISO
  seam), and the **Franklin transformer (central Iowa / southeast Kansas)**.
* **Total congestion rent was $1.6 bn in 2025** ($1.9 bn 2024, $1.4 bn 2023).
* Southeast New Mexico showed price breakout in 2024, less in 2025.

Under a 2-zone N/S topology, **both of the top two constraints and three of the four
2024 FCAs sit inside a single zone** (OKC, Tulsa and Lubbock are all South; Kansas City
is North). A copperplate-within-zone model will therefore price a large share of that
$1.6 bn as zero. This is not an argument against shipping 2 zones — it is the honest
statement of what 2 zones cannot represent, which rule 1 `[R-STRUCT]` requires be said
at the gate rather than discovered in a residual.

### 6.2 Recommendation

**Register 2 zones (SPP-North / SPP-South) in W2**, as the plan proposes. The
supporting reasons are the ones above: a real fuel-mix asymmetry stated by SPP itself, a
balanced ~50/50 load split, a scorable (if narrow) published hub benchmark, and the
lowest-risk path to the first keeper. **Do not register 3 zones at W2** — the third zone
requires a second TTC that OASIS does not serve and a price series whose availability is
unverified, and a topology added without either is a magic number in disguise.

**But the audit recommends ONE amendment to the plan's card P1, and it is substantive.**
The plan pre-declares the third-zone lever as **SPP-54, the SPS / Texas-Panhandle
pocket**, promoted *"only if SPP-12 measures SPS-tie binding share ≥ N↔S share."* On the
evidence above, **the SPS pocket is not the best-supported third zone**: Lubbock is one
of four FCAs, and southeast New Mexico's price breakout **shrank** from 2024 to 2025,
while **northern and southern Oklahoma carry the two highest-valued constraints in the
market and three of the top ten are not even in the same part of Oklahoma**. The audit
therefore recommends the desk hear, as part of P1:

* **Keep SPP-54 as a pre-declared lever** — the SPS pocket is real: its own EIA-930
  sub-BA identity `SPS`, **9.6 % of 2025 system energy** on SPP's own participant table,
  a distinct wind regime, and **Lubbock is one of the four named 2024 FCAs**. (The
  state-level census upper bound, TX + NM = 15,839.2 MW or 15.3 % of fleet nameplate, is
  **not** the SPS pocket — east-Texas AEP/ETEC plant and load sit in the same states.)
  **But do not fix its rank before SPP-12's binding-constraint archive lands.**
* **Add a second pre-declared lever — an Oklahoma pocket** (an OKC/Tulsa split of
  SPP-South) — and let SPP-12's measured per-flowgate binding share choose between the
  two. The promotion test should be the same for both: measured binding share and
  shadow-price value versus the N↔S corridor's own.
* **State the ranking test in the P1 ruling itself**, so the lever queue order is set by
  SPP-12's evidence rather than by whichever lane is issued first.

### 6.3 The FIPS / sub-BA mechanics of each option

**Option A — 2 zones, state map (the plan's W2 proposal).**
`zone_assignment._SPP_STATE_ZONES` = `{ND, SD, NE, MN, MT, IA, KS, MO, CO} → SPP-North`,
`{OK, TX, NM, AR, LA} → SPP-South`, with a `_LARGEST_ZONE["SPP"]` fallback for
unlocated plants. `WY` must not appear (§2.4). Cost: **zero straddle handling** — no
SPP state has material fleet on both sides of the seam once the map is written this way,
because the seam runs along the KS/OK line and the census puts no SWPP plant in a state
that crosses it. Load split from EIA-930 sub-BA energy: `{EDE, INDN, KACY, KCPL, LES,
MPS, NPPD, OPPD, SECI, SPRM, WAUE, WR} → North`, `{CSWS, GRDA, OKGE, SPS, WFEC} → South`
(§5 row 5). **`EDE` is the one sub-BA that genuinely straddles** — Liberty/Empire
District serves MO, KS, OK and AR — but at 5,005 GWh it is **1.8 % of system energy**,
so whichever side it lands on moves the split by less than a point. `CSWS` (AEP: PSO +
SWEPCO) spans OK/AR/LA/east-TX, all South. `WAUE` spans ND/SD/MN/NE/MT/IA, all North.
Simplest option, and the only one whose load side is fully feasible today.

**Option B — 3 zones with the SPS pocket.**
Split `SPP-South` into `SPP-South` and `SPP-SPS`. On the plant side this is clean: SPS's
territory is the **Texas Panhandle + eastern New Mexico**, and `_SPP_STATE_ZONES` cannot
express it (Texas is split between SPS and the AEP/Golden Spread east-Texas footprint),
so it needs a **county-FIPS rule inside TX** — the ERCOT Houston-FIPS pattern
(`00-iso-addition-protocol.md` §1 Stage B) is the template, and NM maps whole. On the
load side it is also clean: `SPS` is its own EIA-930 sub-BA, so a third `load_share`
falls out of SPP-11's pull with no new source. What it needs and does not have is
**a second TTC** (SPS↔rest-of-South), which OASIS does not serve and the ITP report must
supply (§5 row 18), and a **price series** for the pocket, which SPP does not publish as
a hub. Golden Spread Electric Cooperative (6,508 GWh, TX Panhandle) sits in the same
electrical pocket and would move with SPS.

**Option C — 3 zones with an Oklahoma pocket (the audit's added candidate).**
Split `SPP-South` into an Oklahoma zone and a rest-of-South zone, or split Oklahoma
itself north/south along the two named constraint groups. On the plant side, Oklahoma is
a whole state (`OK`, 32,272.3 MW — the largest single state in the footprint), so a
two-way OK/rest split needs **no FIPS rule at all**; an intra-Oklahoma split needs one.
On the load side `OKGE`, `GRDA`, `WFEC` and the Oklahoma part of `CSWS` are separable at
sub-BA grain except for `CSWS`, which is the complication — AEP's `CSWS` bundles PSO
(OK) with SWEPCO (AR/LA/TX), so an OK/rest-of-South split **cannot be made from sub-BA
energy alone** and would need either a `CSWS` sub-allocation or a coarser cut. It also
needs a TTC. **This is the option with the strongest congestion evidence and the
weakest data feasibility** — which is precisely why it should be a ruled lever with a
named evidence test, not a W2 default.

**What must still be supplied before P1 can be ruled on evidence rather than on
priors** (SPP-11's two rows landed on 2026-09-06, while this audit was being written, and
are struck through; the two that decide the card are SPP-12's and are still open):

| Evidence | Lane | Why P1 needs it |
|---|---|---|
| ~~Per-sub-BA annual energy 2023–2025~~ **LANDED 2026-09-06** (`zone-specific-demand/SPP/`, 447,049 rows) | ~~SPP-11~~ → **SPP-20 computes** | The actual `load_share` for whichever option is chosen; and the `EDE` straddle's size. Cross-check it against the ~50/50 participant roll-up (§5 row 6) before writing shares |
| ~~SWPP↔DIBA interchange duration curves~~ **LANDED 2026-09-06** (`eia-930-interchange/SWPP interchange hourly.parquet`, 268,177 rows / 11 DIBAs) | ~~SPP-11~~ → **SPP-33 derives** | Cards P2/P3; and whether the AECI >5,000 MW seam (§5 row 20) needs representation at all |
| Hourly `SPPNORTH_HUB` / `SPPSOUTH_HUB`, mean and p90 \|N−S\| by year | SPP-12 | Confirms or overturns the 2024 screen-year candidate (§6.1); the only hourly zonal benchmark SPP has |
| **RT binding-hour share and shadow-price value by flowgate GROUP** — N↔S corridor vs SPS-tie vs **Oklahoma-internal** vs other, per year | SPP-12 | **The decisive P1 input.** The plan's version of this test has only two groups; on this audit's evidence it needs at least three, or it cannot see the largest object in SPP's congestion |
| N↔S transfer capability and SPS tie ratings from the ITP report | SPP-12 → SPP-20 | The link TTC itself; and `TRANSMISSION_BASE_STATIC_VINTAGE["SPP"]` |

---

## 7. Manual manifest — copy-paste block

Everything this lane could not source, with exact URLs. Rows 1–2 are **session-fetchable
and assigned**; rows 3–7 are genuinely blocked or unverified and are the owner-upload
fallback. Nothing below was guessed at, and no value from any of these documents appears
anywhere above.

```text
=== SPP-10 MANUAL MANIFEST (2026-09-06) ===

--- CLOSED WHILE THIS AUDIT WAS BEING WRITTEN (lane SPP-11 landed 2026-09-06);
--- retained so the provenance and the WY/CO correction stay on the record

1. [CLOSED 2026-09-06 by lane SPP-11 — recorded for provenance, do not re-fetch]
   EPA CAMPD hourly CEMS — the critical path. NINE files, not twelve:
      NE_2023  NE_2024  NE_2025
      NM_2023  NM_2024  NM_2025
      OK_2023  OK_2024  OK_2025
   (+ the 2026 partial for each, matching the sibling convention)
   NOT WY (zero SWPP plants) and NOT CO (zero CEMS-eligible units) — see audit S2.4.
   Route: scripts/data/fetch_campd_unit_level.py --year <Y> --states OK NE NM
   API:   https://api.epa.gov/easey/camd-services/bulk-files          (x-api-key: DEMO_KEY)
          https://api.epa.gov/easey/bulk-files/emissions/hourly/state/emissions-hourly-<YYYY>-<st>.csv
   Landing: data/raw/campd-unit-level/<ST>_<YYYY>.parquet
   Owner:  SPP-11.  Manual fallback: https://campd.epa.gov/data/bulk-data-files
   LANDED: OK/NE/NM/WY x 2023-2026, 16 parquets, 16 cols, schema == KS_2024.
   The four WY_* files are inert for SPP (no SWPP plant is in Wyoming) but harmless —
   load_campd_hourly filters every loaded state to the ISO's own fleet.

2. [CLOSED 2026-09-06 by lane SPP-11 — recorded for provenance, do not re-fetch]
   EIA-930 sub-BA hourly demand, SWPP, 2023-2025 (17 sub-BAs, names confirmed by SPP-10:
   CSWS EDE GRDA INDN KACY KCPL LES MPS NPPD OKGE OPPD SECI SPRM SPS WAUE WFEC WR)
   Key-free route: https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_SUBREGION_<YYYY>_<Jan_Jun|Jul_Dec>.csv
   NOTE: the six-month extract carries the sub-BA CODE only. SUBBA_NAMES["SPP"] display
   names must be read off EIA API v2 electricity/rto/region-sub-ba-data, never guessed.
   Landing: data/raw/zone-specific-demand/SPP/spp_subba_demand_2023-2025.csv + SOURCES.md
   Owner:  SPP-11.
   LANDED: 447,049 rows, 17 sub-BAs, no interior gaps, reconciling to 0.9995-0.9999
   of the BA Demand. Also landed by the same lane: SWPP interchange hourly.parquet
   (268,177 rows / 11 DIBAs) and eia_delivered_gas_{OK,KS,TX,NM}_monthly_2023-2025.csv.

--- BLOCKED OR UNVERIFIED — owner upload is the fallback

3. SPP Integrated Transmission Plan report — N<->S transfer capability, SPS tie ratings.
   BLOCKED: oasis.oati.com/SWPP is unreachable from the session (plan S2.4).
   Try first: https://spp.org/documents/76063/itp%20manual%20version%203.2.pdf   (ITP Manual v3.2)
              https://www.spp.org/engineering/transmission-planning/   (ITP report landing page)
   Needed for: iso_configs._spp_config link TTC; TRANSMISSION_BASE_STATIC_VINTAGE["SPP"].
   Owner:  SPP-12 -> SPP-20.  If still blocked: owner uploads the ITP report PDF.

4. SPP long-term load forecast — A W2 PRECONDITION (plan G12).
   Needs a real edition string and a vintage >= 2020 or scripts/lib/load_forecast/spp.py
   cannot register (test_specs_declare_an_edition_and_a_vintage).
   Candidates, in order:
     https://spp.org/documents/64383/20-year%20assessment%20load%20forecasts%20and%20generation%20retirements.pdf
     https://spp.org/documents/75144/2025-11-03%20joint%20stakeholder%20briefing%20materials.pdf
     https://www.spp.org/documents/74668/25-09-03%20board%20rsc%20joint%20briefing%20materials%20v3.pdf
     https://spp.org/stakeholder-groups-list/retired-groups/load-forecasting-task-force/
   Landing: data/raw/load-forecast/spp/spp.csv + the source PDF.
   Owner:  SPP-12.

5. SPP Market Protocols / Tariff Attachment AE — the VRL step BREAKPOINTS.
   The MAXIMA are already cited (audit S5 row 3: regulation 6 steps -> $600/MW;
   contingency reserve 3 steps -> $1,100/MW; ramp 6 steps, monthly, 2024 max $32/MW).
   The MW breakpoints and intermediate prices are NOT in the State of the Market report.
   Try:  https://www.spp.org/governing-documents-filings/   (Tariff, Attachment AE)
         https://www.spp.org/markets-operations/   (Market Protocols)
   Owner:  SPP-12.  Needed by: SPP-55 (scarcity design), SPP-56 (reserve co-opt) ONLY.
   NOT needed for the first keeper.

6. Per-hub hourly SPPNORTH_HUB / SPPSOUTH_HUB DA + RT, 2023-2025.
   BLOCKED: the portal.spp.org file-browser API form has moved — listings return []
   and build_spp_lmp_reference.py's download paths 404 (plan S2.4, probed 2026-09-06).
   Re-discover from page JS at:
         https://portal.spp.org/pages/rtbm-lmp-by-location
         https://portal.spp.org/pages/da-lmp-by-settlement-location
         https://portal.spp.org/pages/hourly-load
   Landing: data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet
   Owner:  SPP-12.  If the portal now requires a Marketplace login: owner supplies the
   monthly {DA-LMP,RTBM-LMP}-MONTHLY-SL-YYYYMM.csv files.

7. SPP DA / RTBM binding-constraint archive, 2023-2025 — THE DECIDING P1 EVIDENCE.
   Same portal block as row 6; fsNames da-binding-constraints, rtbm-binding-constraints.
   The audit needs RT binding-hour share AND shadow-price value grouped at least three
   ways, not two: N<->S corridor / SPS-tie / OKLAHOMA-INTERNAL / other  (audit S6.2).
   Landing: data/raw/spp-binding-constraints/
   Owner:  SPP-12.  Manual fallback: the MMU State of the Market top-constraint tables
   (SOM 2025 report p.160 / PDF p.172) give the top ten by name and shadow price but not
   the hour counts.

--- REACHABLE, NO ACTION NEEDED (recorded so no lane re-probes them)

   spp.org PDFs and pages: HTTP 200 over curl with a browser User-Agent.
   WebFetch returns HTTP 503 for every spp.org URL tried — use curl with
   -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
   Confirmed fetched by SPP-10 on 2026-09-06:
     https://www.spp.org/about-us/fast-facts/                                        (200)
     https://www.spp.org/documents/76798/2025_annual_state_of_the_market_report.pdf  (200, 220 pp)
     https://www.spp.org/documents/73953/2024_annual_state_of_the_market_report.pdf  (200, 240 pp)
     https://www.spp.org/documents/76543/spp%20planning%20criteria%20v4.7.pdf        (200, 121 pp)
     https://www.spp.org/documents/69547/spp%20planning%20criteria%20v4.1a.pdf       (200, 122 pp)
     https://www.spp.org/documents/64402/spp%20mmu%20order%20831%20verifcation%20faq%20v4.pdf (200, 6 pp)
   eia.gov six-month sub-BA extracts: HTTP 200, no key.
=== END MANIFEST ===
```

---

## 8. Reproducing the measured numbers

Every measured figure above comes from committed artifacts and a stdlib + pandas read.
`pyarrow` and `pandas` are not in the base image; `pip3 install pyarrow pandas` first.

```python
# S2 — fleet census
import pandas as pd
P = "data/raw/eia-860/"
plant = pd.read_parquet(P + "eia860_plant.parquet")
gen   = pd.read_parquet(P + "eia860_generator_operable.parquet")
sw = plant[plant["Balancing Authority Code"] == "SWPP"][["Plant Code", "Plant Name", "State"]]
g  = gen.merge(sw, on="Plant Code", how="inner", suffixes=("", "_p"))
g["MW"] = pd.to_numeric(g["Nameplate Capacity (MW)"], errors="coerce")
g.groupby("Technology")["MW"].sum().sort_values(ascending=False)   # S2.2
g.groupby("State_p")["MW"].agg(["size", "sum"])                    # S2.4

# S3 — EIA-930
d = pd.read_parquet("data/raw/eia-930-hourly/SWPP hourly.parquet")
d["yr"] = d["Local date"].dt.year
d[d["Demand"] > 60000]           # the 2023 spike hour
d[d["Total interchange"].abs() > 8000]   # the 2024/2025 interchange outliers
d.groupby("yr")["NG: BAT"].apply(lambda s: s.isna().sum())   # the BAT hole

# S4 — price sidecar
p = pd.read_parquet("data/raw/_validation-source/actual_lmp_hourly_SPP.parquet")
p.groupby("year")["rt"].agg([("gt200", lambda s: (s > 200).sum()),
                             ("gt300", lambda s: (s > 300).sum()),
                             ("neg",   lambda s: (s < 0).sum())])

# S5 rows 8b/9/11 — EIA-923
c = pd.read_parquet("data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet")
gg = pd.read_parquet("data/raw/_processed-legacy/eia923_monthly_generation.parquet")
gg[gg.plant_id.isin([210, 8036])][["plant_id", "plant_name", "year", "netgen_annual_mwh"]]

# S item 11 — the 17 SWPP sub-BAs (key-free, ~26 MB)
#   curl -A "Mozilla/5.0 (market-sim data fetch)" \
#     "https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_SUBREGION_2025_Jan_Jun.csv" \
#     | awk -F'","' '$1=="\"SWPP"{print $4}' | sort -u
```

---

## 9. What this lane changed outside this file

* `docs/multi-iso/00-iso-addition-protocol.md` — §0 SPP row and the §3 status note.
  SPP is **not registered**; the doc claimed it was.
* `docs/multi-iso/01-data-needs-and-upload-manifest.md` — the SPP CEMS row (`WY`
  removed, `CO` added, the missing list corrected to `NE, NM, OK`), the header update
  block, the SPP EIA-930 row, the SPP gas-hub row (Panhandle Eastern, cited), the SPP
  zonal-load row, the SPP hydro row, and the §8 blockers note.
* `docs/multi-iso/spp-addition-plan-2026-09.md` — the §5 SPP-10 lane cell only, marked
  LANDED with a pointer to this audit. No charter text, no other row.
* `docs/handoffs/spp-desk-ledger-2026-09.md` — the §1 scoreboard SPP-10 row only
  (status, realised branch, FINDING pointer). No sitting entry was written or amended;
  that is the desk's.
* `docs/handoffs/FINDING-spp-10-2026-09-06.md` — new; a pointer to this document.

**Concurrency note.** Lane **SPP-11** landed its four charter items on `main` while this
audit was being written. Every row it closed is marked in place above (§1 rows 2, 8c, 18;
§5 rows 4b and 6; §7 manifest rows 1–2; §6.3's evidence table) rather than deleted, so
the census's provenance findings — the `WY` / `CO` correction and the measured size of
the gap — stay on the record. **Nothing measured in this audit was re-run against the
newly landed files**; the census reads EIA-860, EIA-930 and EIA-923, none of which
SPP-11 touched.

Nothing else. No `src/`, `scripts/`, `configs/`, `tests/`, `frontend/` or `data/` file
was touched; no mechanism-matrix cell moved; no `ScenarioConfig` field exists or moved;
no solve was run.
