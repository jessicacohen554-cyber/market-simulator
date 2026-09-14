# NWPP Data-Acquisition Audit (Phase 0)

Lane **NWPP-10** · 2026-09-13 · branch `claude/nwpp-10-audit-raq015` · MODEL Opus
`claude-opus-5` · DATA PROFILE `shared` · base sha **`4d9c3251`**.

Charter: `docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-10. Templates:
`docs/multi-iso/spp-data-audit.md` and `miso-data-audit.md`. Process authority:
`docs/multi-iso/05-backcast-playbook.md` §1 (Phase 0) and §8.

**This lane RECOMMENDS. It decides nothing.** No topology is chosen here; no file under
`src/`, `scripts/`, `configs/`, `tests/`, `frontend/` or `data/` is touched; no parameter is
derived (rule 23 `[R-FROZEN-DERIVE]`); no mechanism is tested and no mechanism-matrix cell
moves (rule 28). Every number below is either **measured off a committed repo artifact**
(reproduction commands in §11) or **cited to a primary published source**. A cell with
neither reads `pending NWPP-11/12/13` — never a guess (rules 5 `[R-NO-MAGIC]`,
13 `[R-MEASURED]`, 14 `[R-ACCURATE]`).

The desk serves cards **N5** (topology), **N7** (adequacy / seasonal peak) and **N8** (CEMS
scope) from §5, §7, §8 and §9 of this document.

---

## 0. Headline

1. **The fleet census reconciles to the charter exactly at the headline and corrects it in
   three technology rows.** EIA-860 over the 17 candidate BAs gives **1,082 plant-table rows
   / 940 plants with an operable generator / 1,932 generators / 98,738.1 MW nameplate** —
   the charter's four headline numbers confirmed to the 0.1 MW. Hydro 35,799.5 MW over 288
   plants, eight ≥ 1 GW holding 17,821.8 MW; nuclear 1,200.0; coal 8,910.2 over 32 units;
   Electric Utility 68,860.0 MW by plant `Sector Name` — all confirmed exactly. **Corrected:
   gas ST is 2,393.0 MW (not 2,163.0), gas ICE 737.5 (not 732.7), solar PV 10,051.3 (not
   10,049.9)**, and the charter's elided "other" residual of 365.7 MW resolves to a measured
   **129.5 MW** across four technologies (§2.4). The total is unchanged.
2. **The TRE row is a SOURCE DEFECT and is REJECTED — and it is not alone.** Plant **68906
   "Pine Forest Solar I"**, Hopkins County **TX** (33.101 N, −95.392 W), NERC **TRE**, BA code
   `DOPD`, 200 MW battery + 300 MW PV = 500.0 MW, cannot be in a Western-Interconnection BA:
   ERCOT and WECC are **asynchronously separated**, so this is a physical impossibility, not
   a preference. The rule applied is a **two-key interconnection test** (§2.8). The same sweep
   found **two more** rows the charter did not name: `WAUW`'s **Sand Creek Wind Farm** (MRO,
   eastern Montana — *not* a defect: WAUW genuinely straddles the Eastern/Western seam, and
   the row is canceled so it is inert), and `DOPD`'s **Desert Bloom** (Maricopa County AZ,
   WECC, proposed-only — inert today, **live the moment it enters service**).
3. **`eia860_generators.parquet` MUST be extended, and the blocker is not the file — it is
   `ISO_TO_BA_CODE`.** The curated file is the fleet loader's own source
   (`data/fleet/eia860.py`, `EIA_860_PARQUET_NAME`), and `data/hydro.py`, `model/storage.py`
   and `data/announced_retirements.py` read it too; a missing NWPP fleet raises
   `FileNotFoundError`. Extending it is one line plus a re-run of the existing producer. But
   `ISO_TO_BA_CODE` is the **inverse dict comprehension** of `BA_CODE_TO_ISO`, so a 17→1
   `BA_CODE_TO_ISO` silently collapses `ISO_TO_BA_CODE["NWPP"]` to **one arbitrary BA** — and
   nine live `src/` call sites compare against it with `==`, including the hydro-budget
   nameplate builder that is card N3's own machinery. **That, not `zone_assignment.py`, is the
   genuinely novel code change in W2** (§3).
4. **`Demand (MW) (Adjusted)` is the convention, and the screen that would be applied on top
   of it is the hazard.** The Adjusted column reproduces the charter's cleaned peaks
   **49,290 / 52,564 / 50,953 MW to the MW** and repairs all 30 artifact hours. The charter's
   energy row (283.97 / 291.56 / 294.86 TWh) is measured on the **raw** column while its peak
   and load-factor rows are measured on the **Adjusted** column; the internally consistent
   Adjusted figures are **284.208 / 291.343 / 293.390 TWh** (§4). The charter's hour counts are
   ~9 h short in 2023 because the first UTC hours of 2023 live in the *2022* half-file; read
   2022–2026 and the window is **447,168 rows = 17 BAs × 26,304 hours, zero gaps**.
5. **A 2.5×-median screen is WRONG for this footprint and would delete a real annual peak.**
   The charter's 30 flagged hours are confirmed exactly (AVA 10, NWMT 11, NEVP 6, PACE 1,
   SCL 2). The same screen also flags **54 CHPD hours in 12–16 January 2024** which are **not**
   artifacts: they are the January-2024 Pacific-Northwest cold snap, EIA's Adjusted column
   leaves every one unchanged, the daily maxima trace a textbook ramp-and-decay, and the block
   contains **CHPD's annual peak — and the whole NWPP-NW zone's 2024 annual peak.** CHPD's
   peak/median ratio is **2.29 / 2.83 / 2.50**, so the `_screen_demand_spikes` docstring's
   stated basis — *"every legitimate demand series has max/median ≤ 2.1"* — is **falsified by
   measurement** here (NEVP also, at 2.20–2.37). Separately, **17 exactly-zero NEVP demand
   hours in 2025 survive into the Adjusted column** and the charter did not find them (§4.4).
6. **The footprint is seasonally SPLIT, measured, and one zone flips.** NWPP-NW is **winter**-
   peaking in all three years; NWPP-EAST and NWPP-SNV **summer** in all three (SNV decisively,
   summer/winter ≈ 1.9–2.1); NWPP-INLAND summer; **NWPP-OR flips — summer 2023, summer 2024,
   winter 2025.** Per BA the split is 8 winter / 6 summer / 1 flipping. A single scalar
   `PLANNING_RESERVE_MARGIN_BY_ISO["NWPP"]` cannot express this (§5, §7).
7. **The timezone question is CLOSED by measurement and the convention is UTC.** 14 BAs
   Pacific (−8/−7), 3 Mountain (−7/−6: NWMT, PACE, WAUW), stable across all three years, all
   **six** DST transitions present and correctly signed, IPCO confirmed filing **Pacific**.
   Every BA has 26,304 unique **UTC** hours and exactly **3 duplicated LOCAL** timestamps (the
   fall-back repeats) — so the local column is ambiguous by construction and **UTC is the only
   admissible join key** (§6).
8. **CEMS reaches ~31 % of nameplate but ~42–44 % of energy.** The charter's ~32 % estimate is
   confirmed as an **upper bound** (32.63 % of nameplate); the measured recall-adjusted
   expectation after NWPP-11 lands ID/OR/UT/WA is **30.98 %**, against **15.32 % reachable
   today**. On energy the same path reaches **41.8–43.6 % of EIA-923 footprint net generation**
   — materially better than the nameplate figure implies (§8).
9. **Two seam facts that will break a naive derive.** (a) **BPAT's balance identity fails
   structurally** — `Demand ≠ NetGen − TotalInterchange` in **81.5 %** of hours, mean residual
   **−3,206 MW** (BPA wheels energy it neither generates nor serves), so summing per-BA
   `Total Interchange` over the 17 does **not** give the footprint's external position (it is
   off by 35.4 / 35.8 / 12.9 TWh). (b) **`GRID` is a hard source conflict**: EIA-930 `GRID`
   net generation peaks at **3,208 MW = 4.65× the 689.4 MW EIA-860 assigns to that BA**, an
   implied capacity factor of **2.93**. The two sources do not describe the same resources, and
   GRID is ~6 % of footprint net generation (§4.6, §9).
10. **The EIA-930 fuel taxonomy changes mid-window, at 2024-07.** Read literally,
    `Net Generation (MW) from Hydropower and Pumped Storage` gives 104.2 TWh in 2023, 55.4 in
    2024 and **0.0 in 2025** — the hydro appears to vanish. The old and new column families
    must be **unioned**; done so, the mix reconciles to published net generation within
    **0.04 % / 0.00 % / 0.08 %**. One Adjusted column carries an EIA **spelling error**
    (`Solar witho Integrated Battery Storage`) that will break any programmatic
    `f"{base} (Adjusted)"` construction (§4.5).

---

## 1. Status table

| # | Item | Source | Status | File path | Notes |
|---|------|--------|--------|-----------|-------|
| 1 | NWPP fleet census (plants / MW by BA, state, technology, sector) | EIA-860 2025 Early Release, `Balancing Authority Code ∈ {17 BAs}` | **got** | `data/raw/eia-860/eia860_plant.parquet` + `eia860_generator_operable.parquet` | 1,082 plant rows / 940 with operable gens / 1,932 gens / 98,738.1 MW nameplate (92,199.2 summer, 96,596.1 winter). Charter headline confirmed; three technology rows corrected (§2.4) |
| 2 | Footprint admissibility adjudications | same | **got** | — | Pine Forest Solar I REJECTED (−500.0 MW, −2 gens); Sand Creek Wind (MRO) and Desert Bloom (AZ) named and inert (§2.8) |
| 3 | Curated seven-ISO fleet parquet | `scripts/data/process_eia860.py` | **blocked → NWPP-20** | `data/raw/eia-860/eia860_generators.parquet` | 19,725 rows, exactly `{CISO ERCO ISNE MISO NYIS PJM SWPP}`, **zero NWPP rows**. It is the fleet loader's own source. RECOMMENDATION: extend via the producer, and fix `ISO_TO_BA_CODE` first (§3) |
| 4 | EIA-930 hourly demand / net generation / interchange × 17 BAs | EIA Hourly Electric Grid Monitor, wide BALANCE extract | **got** | `data/raw/eia-930/EIA930_BALANCE_<yr>_<half>.parquet` | All 17 BAs present. Window 2023–2025 = **447,168 rows, 26,304 UTC hours per BA, zero gaps** once the 2022 half-file is read for the January boundary (§4.1) |
| 5 | Per-BA `<BA> hourly.parquet` derived extracts | derived from item 4 | **absent → NWPP-11** | `data/raw/eia-930-hourly/` | Only CISO ERCO FLA ISNE MISO NYIS PJM SOCO SWPP exist. **No fetch and no `EIA_API_KEY` needed** — this is a derive from committed bytes |
| 6 | Demand-defect screen + convention | this audit | **got** | — | 30 artifact hours confirmed; **54 CHPD hours are REAL load, not artifacts**; 17 zero-demand NEVP hours survive into Adjusted. Convention: read `Demand (MW) (Adjusted)`; do **not** apply `_screen_demand_spikes` on top (§4.4) |
| 7 | Seasonal peak per candidate zone | item 4 | **got** | — | NW winter ×3; OR summer/summer/**winter**; INLAND summer ×3; EAST summer ×3; SNV summer ×3 (§5) |
| 8 | Timezone per BA + DST | item 4 (`Local Time` vs `UTC Time`) | **got** | — | 14 Pacific / 3 Mountain, stable, 6/6 DST transitions correct, IPCO files Pacific. Convention: **UTC is the join key** (§6) |
| 9 | Per-counterparty (DIBA) interchange | EIA-930 INTERCHANGE product | **partial → NWPP-11** | `data/raw/eia-930-interchange/` (no NWPP files) | BALANCE carries `Total Interchange` + `Sum(Valid DIBAs)` only. **Neither can separate internal from external flow** — and BPAT's identity failure means the scalar cannot be summed (§4.6) |
| 10 | CAMPD unit-level, footprint states | `data/raw/campd-unit-level/` | **partial → NWPP-11** | MT, NV, WY, CA present; **ID, OR, UT, WA, CO absent** | Gap is worth **17.3 pp of nameplate** and **~25 pp of energy**. CO needs none — its single footprint plant is **hydro**, not solar (§8) |
| 11 | EIA-923 monthly net generation, footprint plants | EIA-923 | **got (2025 preliminary)** | `data/raw/_processed-legacy/eia923_monthly_generation.parquet` | 848 / 879 / **260** footprint plant-rows for 2023/24/25 — the 2025 vintage is a preliminary release. **VERIFIED by NWPP-31, 2026-09-14**: the BA total is **235.5113 TWh against EIA-930's 298.8295 = 0.7881**, below the builder's 0.90 vintage bar, so the NWPP 2025 block carries `eia923_incomplete: true`; wind (923/930 = **0.5746**) and hydro (**0.6796**) are sourced from EIA-930 instead, solar is not (0.9796, above the 0.80 per-fuel bar), and the **gas split has no EIA-930 equivalent and stays under-counted** (gas_cc 58.12 against 73.87 / 75.03 in the complete years). 2023/2024 clear both bars (923/930 = 1.0757 / 1.0698, inside the ERCOT/MISO/NEISO spread). The SPP audit's item 9 caveat therefore holds and is now quantified |
| 12 | EIA-923 monthly delivered fuel cost, footprint plants | EIA-923 Schedule 2 | **got (coal partial)** | `data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet` | Gas 30–32 plants/yr, petroleum 7–10, **coal only 8 plants** — the four mine-mouth/captive plants (**Colstrip, Centralia, TS Power, Hardin**, 2,911.7 MW = 32.7 % of coal) carry **zero** fuel-cost rows (§7 row 9) |
| 13 | Nuclear monthly CF, Columbia Generating Station | EIA-923 monthly, plant 371 | **got** | same as item 11 | Annual CF **0.802 / 0.948 / 0.737**; biennial refuelling outages visible in May–Jun 2023 and Apr–Jun 2025, none in 2024. A measured, rule-13-admissible input — **not** pending (§7 row 10) |
| 14 | `actual_lmp.json` NWPP block + hourly LMP | — | **absent → card N2 / NWPP-13** | `data/raw/_validation-source/actual_lmp.json` | Keys are exactly `ERCOT PJM CAISO NYISO NEISO MISO SPP`. **The Northwest Power Pool publishes no LMP**; this audit takes no position beyond recording the absence (plan §2.6 is card N2's, not this lane's) |
| 15 | `NWPP_<yr>_renewable_capacity.csv` + `calibration_reference.json` NWPP block | `scripts/data/build_calibration_reference.py` | **LANDED 2026-09-14, lane NWPP-31** | `data/raw/_validation-source/` | Was: *"No NWPP file of any kind exists there"*. Now 2023–2025: demand off the pool frame's own `Demand` column (the array the LP dispatches — peaks **49,290 / 52,564 / 50,953 MW**), EIA-860 renewables (wind 12,486.6 → 14,457.1 MW, solar 6,513.3 → 9,952.0 MW), EIA-923 by fuel with hydro as the declared extra (**106.9 / 107.9 / 110.3 TWh**), eGRID 2023 over 880 of 881 PLNT23 rows. Gate **G9 passes: non-NWPP diff exactly zero** on all 7 regions and all 36 pre-existing CSVs. `FINDING-nwpp-31-2026-09-14.md` |
| 16 | Gas pipeline per plant (basis attribution) | EIA-860 `Natural Gas Pipeline Name 1` | **got (76.3 %)** | `eia860_plant.parquet` | 17,787.3 MW of 23,305.3 MW of gas names a pipeline; **5,518.0 MW names none**. Per-zone attribution measured in §7 row 8 |
| 17 | WECC published path ratings | wecc.org | **pending NWPP-12** | `data/raw/nwpp-planning/` (does not exist) | Card N5's dispositive evidence. This audit's zoning recommendation is explicitly conditional on it (§9) |
| 18 | WRAP binding-season date, PRM by season, IRPs, LTLF, NRC | westernpowerpool.org, participant IRPs, NRC | **pending NWPP-12** | `data/raw/nwpp-planning/`, `load-forecast/nwpp/`, `nuclear-license-status/nwpp.csv` | The LTLF edition + vintage is a **W2 precondition** (gate G12) |
| 19 | eGRID vintage | `data/zone_assignment._EGRID_VINTAGE` | **got — no action** | `data/fleet/egrid2023_data_rev2.xlsx` | A module-level scalar (`2023`), **not** a per-ISO dict. NWPP needs no entry, exactly as SPP needed none |

---

## 2. The fleet census

Join: `eia860_plant.parquet` (carries `Balancing Authority Code`, `NERC Region`, `State`,
`Sector Name`) → `eia860_generator_operable.parquet` on `Plant Code`, over
`BPAT PACE PACW PGE PSEI AVA IPCO NWMT CHPD DOPD GCPD SCL TPWR AVRN GRID WAUW NEVP`.
Zero duplicate `(Plant Code, Generator ID)` keys.

### 2.1 Headline — the charter's four numbers, confirmed

| Measure | Charter | Measured | Verdict |
|---|---:|---:|---|
| Plant-table rows carrying a footprint BA | 1,082 | **1,082** | ✅ |
| Plants with ≥ 1 operable generator | 940 | **940** | ✅ |
| Operable generators | 1,932 | **1,932** | ✅ |
| Nameplate | 98,738.1 MW | **98,738.1 MW** | ✅ |
| Summer capacity | — | 92,199.2 MW | new |
| Winter capacity | — | 96,596.1 MW | new |
| NERC split | WECC 98,238.1 / 1,930 · TRE 500.0 / 2 | **identical** | ✅ (and one MRO plant-table row with no operable generator — §2.8) |

142 of the 1,082 plant-table rows carry no operable generator (WA 30, OR 29, NV 26, UT 20,
MT 11, WY 11, ID 8, CA 5, **AZ 2**).

### 2.2 By balancing authority

Plants · generators · MW (operable), sorted by MW:

| BA | Plants | Gens | MW | | BA | Plants | Gens | MW |
|---|---:|---:|---:|---|---|---:|---:|---:|
| BPAT | 130 | 388 | 30,513.9 | | AVA | 30 | 79 | 2,309.0 |
| PACE | 173 | 313 | 18,737.4 | | SCL | 9 | 31 | 2,068.1 |
| NEVP | 106 | 261 | 15,656.9 | | CHPD | 3 | 32 | 2,037.8 |
| IPCO | 134 | 204 | 4,871.8 | | DOPD | 2 | 12 | **1,366.8** |
| NWMT | 52 | 119 | 4,265.1 | | GCPD | 1 | 10 | 1,220.0 |
| PGE | 100 | 149 | 4,219.7 | | WAUW | 22 | 46 | 1,128.3 |
| PSEI | 34 | 81 | 3,339.0 | | TPWR | 7 | 21 | 724.8 |
| AVRN | 19 | 25 | 2,848.7 | | GRID | 1 | 3 | 689.4 |
| PACW | 117 | 158 | 2,741.4 | | | | | |

Every row confirms the charter exactly. **DOPD's 1,366.8 MW is 866.8 MW of real Wells hydro
plus the 500.0 MW Texas defect** (§2.8); after rejection DOPD is **1 plant / 10 generators /
866.8 MW** and the footprint is **939 plants / 1,930 generators / 98,238.1 MW**.

### 2.3 By state

| State | Plants | Gens | MW | | State | Plants | Gens | MW |
|---|---:|---:|---:|---|---|---:|---:|---:|
| WA | 139 | 422 | 31,711.8 | | MT | 63 | 152 | **6,939.6** |
| OR | 300 | 504 | 19,035.4 | | ID | 153 | 265 | 6,431.3 |
| NV | 104 | 253 | 15,638.3 | | **TX** | 1 | 2 | **500.0** |
| UT | 117 | 221 | 9,769.3 | | CA | 10 | 19 | 50.8 |
| WY | 52 | 92 | 8,654.1 | | CO | 1 | 2 | 7.5 |

Charter confirmed except **MT = 6,939.6 MW (charter 6,940.4, −0.8)**. The `TX 500.0` row is the
defect. **CO is one plant — `James W. Broderick Hydropower Plant`, Pueblo County, 7.5 MW over
2 generators, BA `PACE`, NERC WECC — and it is HYDRO, not solar** as the charter states. The
charter's *conclusion* (skip CO CAMPD) is right; its *reason* is wrong, and the corrected reason
is stronger: a hydro plant is not CEMS-eligible at any size. CA's 50.8 MW is PacifiCorp's
Klamath-area and NV Energy's Truckee-area assets plus ~6 MW of small Kern/San Joaquin County
solar filed under `PACW` — flagged in §2.8 as immaterial but of the same family as the defects.

### 2.4 By technology — three rows corrected

| Technology | Plants | Gens | MW | % | Charter | Δ |
|---|---:|---:|---:|---:|---:|---:|
| Conventional Hydroelectric | 288 | 807 | 35,799.5 | 36.26 | 35,799.5 | ✅ |
| Natural Gas Fired Combined Cycle | 34 | 112 | 15,609.3 | 15.81 | 15,609.3 | ✅ |
| Onshore Wind Turbine | 152 | 169 | 14,460.3 | 14.65 | 14,460.3 | ✅ |
| Solar Photovoltaic | 296 | 313 | **10,051.3** | 10.18 | 10,049.9 | **+1.4** |
| Conventional Steam Coal | 17 | 32 | 8,910.2 | 9.02 | 8,910.2 | ✅ |
| Natural Gas Fired Combustion Turbine | 34 | 86 | 4,565.5 | 4.62 | 4,565.5 | ✅ |
| Batteries | 32 | 34 | 2,522.0 | 2.55 | 2,522.0 | ✅ |
| Natural Gas Steam Turbine | 9 | 17 | **2,393.0** | 2.42 | 2,163.0 | **+230.0** |
| Nuclear | 1 | 1 | 1,200.0 | 1.22 | 1,200.0 | ✅ |
| Geothermal | 31 | 68 | 972.6 | 0.99 | 972.6 | ✅ |
| Natural Gas Internal Combustion Engine | 16 | 100 | **737.5** | 0.75 | 732.7 | **+4.8** |
| Wood/Wood Waste Biomass | 25 | 41 | 629.7 | 0.64 | 629.7 | ✅ |
| Hydroelectric Pumped Storage | 1 | 6 | 314.0 | 0.32 | 314.0 | ✅ |
| Solar Thermal (w/ + w/o storage) | 3 | 3 | 202.2 | 0.20 | 202.2 | ✅ |
| Petroleum Liquids | 15 | 39 | 87.7 | 0.09 | 87.7 | ✅ |
| Landfill Gas | 18 | 75 | 85.8 | 0.09 | 85.8 | ✅ |
| Petroleum Coke | 1 | 1 | 68.0 | 0.07 | 68.0 | ✅ |
| All Other | 5 | 5 | 76.2 | 0.08 | *(in "other")* | — |
| Municipal Solid Waste | 1 | 1 | 26.0 | 0.03 | *(in "other")* | — |
| Other Waste Biomass | 10 | 17 | 22.0 | 0.02 | *(in "other")* | — |
| Other Gases | 3 | 5 | 5.3 | 0.01 | *(in "other")* | — |
| **TOTAL** | **940** | **1,932** | **98,738.1** | 100.00 | 98,738.1 | ✅ |

The three deltas sum to **+236.2 MW** and the charter's elided "other" residual (98,738.1 minus
its listed rows = 365.7 MW) falls to a measured **129.5 MW**, so the total is unchanged. Each
delta happens to equal one planned-retirement cohort exactly (solar PV 1.4 MW dated 2035; gas ST
230.0 MW dated 2028; gas ICE 4.8 MW dated 2026), which is suggestive of how the charter's tally
was cut but is **not** a rule: coal's own 229.5 MW 2027 cohort is *not* netted out there. The
table above is the committed file's contents, unconditioned.

### 2.5 By sector — confirmed, and the two `Sector Name` columns agree

| Plant `Sector Name` | Plants | Gens | MW | % |
|---|---:|---:|---:|---:|
| Electric Utility | 332 | 1,020 | **68,860.0** | **69.74** |
| IPP Non-CHP | 531 | 734 | 26,962.3 | 27.31 |
| IPP CHP | 16 | 35 | 1,568.8 | 1.59 |
| Industrial CHP | 33 | 69 | 1,028.8 | 1.04 |
| Industrial Non-CHP | 7 | 28 | 175.1 | 0.18 |
| Commercial CHP | 10 | 25 | 73.6 | 0.07 |
| Commercial Non-CHP | 11 | 21 | 69.5 | 0.07 |

Charter's 68,860.0 MW confirmed exactly. Worth stating for the PJM `retirement_sector_gate`
precedent the charter flags (plan §2.1 fact 4): the **generator-level and plant-level
`Sector Name` agree in every footprint row** (identical MW in both groupings), so a sector
partition here is unambiguous — it does not need the plant-level disambiguation PJM's D53/D78
lane needed.

### 2.6 Hydro

**288 plants / 807 generators / 35,799.5 MW (36.26 %).** Eight plants ≥ 1 GW hold
**17,821.8 MW = 49.8 % of all hydro** — charter confirmed:

| Plant | Code | State | BA | MW | Gens |
|---|---:|---|---|---:|---:|
| Grand Coulee | 6163 | WA | BPAT | 6,495.0 | 27 |
| Chief Joseph | 3921 | WA | BPAT | 2,456.2 | 27 |
| John Day | 3082 | OR | BPAT | 2,160.0 | 16 |
| The Dalles | 3895 | OR | BPAT | 1,819.7 | 24 |
| Rocky Reach | 3883 | WA | CHPD | 1,349.2 | 11 |
| Wanapum | 3888 | WA | GCPD | 1,220.0 | 10 |
| Bonneville | 3075 | OR | BPAT | 1,162.0 | 20 |
| Boundary | 6433 | WA | SCL | 1,159.7 | 6 |

Next: McNary 990.5 · Priest Rapids 950.0 · **Wells 866.8 (DOPD — the BA's entire real fleet)** ·
Little Goose / Lower Monumental / Lower Granite 810.0 each · Brownlee 675.0 (IPCO) ·
Rock Island 629.4 · Ice Harbor 603.0 · Libby 525.0 · Noxon Rapids 487.8 (AVA) · Dworshak 465.0.
**141 plants below 10 MW hold 504.1 MW between them — 1.41 % of hydro** (charter confirmed).
Pumped storage is one plant, 314.0 MW, BPAT.

The hydraulic-chain fact card N3 rests on is visible in the BA column: of the ten largest
plants, **eight are on the Columbia/Snake mainstem** and four different BAs own them
(BPAT, CHPD, GCPD, DOPD) — so the chain **crosses candidate-zone boundaries** under any grouping
in §9, which is a constraint on NWPP-36 as much as on NWPP-32.

### 2.7 Coal, nuclear, petcoke

**Coal: 17 plants / 32 units / 8,910.2 MW.** Charter's unit count and total confirmed.

| Plant | State | BA | Units | MW |
|---|---|---|---:|---:|
| Colstrip | MT | NWMT | 2 | 1,647.4 |
| Hunter | UT | PACE | 3 | 1,472.2 |
| Jim Bridger | WY | PACE | 2 | 1,161.9 |
| Huntington | UT | PACE | 2 | 1,015.5 |
| Dave Johnston | WY | PACE | 4 | 816.7 |
| Transalta Centralia Generation | WA | BPAT | 1 | 729.9 |
| Bonanza | UT | PACE | 1 | 499.5 |
| Naughton | WY | PACE | 2 | 380.8 |
| Wyodak | WY | PACE | 1 | 362.1 |
| North Valmy | NV | NEVP | 1 | 289.8 |
| TS Power Plant | NV | NEVP | 1 | 242.0 |
| Hardin Generator Project | MT | NWMT | 1 | 115.7 |
| Sunnyside Cogen Associates | UT | PACE | 1 | 58.1 |
| Colstrip Energy LP | MT | NWMT | 1 | 46.1 |
| Genesis Alkali | WY | PACE | 6 | 41.0 |
| General Chemical | WY | PACE | 2 | 30.0 |
| Western Sugar Cooperative – Billings | MT | NWMT | 1 | 1.5 |

One correction: the charter's *"five units < 60 MW"* is **five PLANTS / eleven units**
(176.7 MW). **Nuclear**: Columbia Generating Station, plant 371, 1,200.0 MW, 1 unit, BPAT, WA,
operating 1984 — confirmed. **Petcoke**: Yellowstone Energy LP, 68.0 MW, NWMT, MT.

**EIA-860 planned retirements on operable rows** (the full table the charter quotes one row of):

| Year | Technology | Gens | MW |
|---:|---|---:|---:|
| 2026 | Landfill gas · gas ICE · other gases | 6 | 9.0 |
| 2027 | **Conventional steam coal** · hydro · landfill gas | 6 | **235.0** (coal **229.5**) |
| 2028 | Gas ST · petroleum liquids · hydro | 6 | 238.8 |
| 2030 | Gas CC · hydro | 5 | 106.2 |
| 2032 | Gas CC | 7 | 222.0 |
| 2035 | Gas CT · solar PV | 2 | 63.2 |
| 2043 | Gas CC | 3 | 593.3 |

The charter's *"only one [coal plant] carries an EIA-860 planned retirement inside the visible
horizon (229.5 MW of coal dated 2027)"* is confirmed **for coal**; the non-coal cohorts above are
new and matter for NWPP-12's confirmed-retirement item and for step 1b.

### 2.8 The adjudications

#### (a) The TRE row — **REJECTED as a source defect**

| Field | Value |
|---|---|
| Plant Code | **68906** |
| Plant Name | **Pine Forest Solar I** |
| Location | Pickton / Hopkins County, **TX** 75471; **33.100779 N, −95.392287 W** |
| NERC Region | **TRE** |
| Balancing Authority Code / Name | **`DOPD`** / *PUD No. 1 of Douglas County* |
| Owner / T&D owner | Pine Forest Solar I, LLC (Utility ID 67151) / *4 Rivers Electric Cooperative, Inc.* (state **KS**) |
| Grid voltage | 345 kV |
| Generators | `PFBA` **200.0 MW** Batteries + `PFPV` **300.0 MW** Solar PV, both COD **2025** |

**The rule applied — a two-key INTERCONNECTION test, not a size threshold and not geography
alone:**

> A plant self-reporting a NWPP `Balancing Authority Code` is admitted to the footprint only
> when **both** (i) its `NERC Region` is **`WECC`** — the interconnection every NWPP balancing
> authority operates in — **and** (ii) its coordinates fall inside the Western Interconnection.
> A row failing **either** key is a mis-entry in EIA-860's respondent-entered BA field, not a
> footprint member.

Key (i) is **dispositive on physics, not on preference**: ERCOT (`TRE`) and the Western
Interconnection are **asynchronously separated** — they exchange power only through DC ties, and
no generator is simultaneously inside both. A Washington public utility district cannot balance
a resource inside ERCOT. Key (ii) is corroborating: Hopkins County is ~1,900 km east of the
nearest NWPP asset, and every independent locator in the same committed row (state, county,
lat/lon, NERC region, T&D owner) agrees against the one BA-code field. DOPD's real fleet is the
866.8 MW Wells hydro project, which the row does not resemble.

Rejecting it costs **500.0 MW (0.51 % of the fleet) and 2 of 1,932 generators**, and it removes
the footprint's only `TRE` row and only `TX` row. **Consequence for NWPP-20:** the footprint
predicate is `Balancing Authority Code ∈ NWPP_BAS` **AND** `NERC Region == "WECC"`, encoded so
the next EIA-860 vintage's mis-entry is caught rather than silently zoned. That predicate is
cheap, mechanical and catches this class by construction; it is what this audit recommends over
a hard-coded plant-code exclusion (which would be an off-registry per-plant dict, rule 24
`[R-REGISTRY]`).

#### (b) Sand Creek Wind Farm — **NOT a defect; WAUW straddles the interconnection seam**

| Field | Value |
|---|---|
| Plant Code | 60595 |
| Plant Name | Sand Creek Wind Farm |
| Location | McCone County, **MT**; 47.911 N, **−105.498 W** |
| NERC Region | **MRO** |
| BA | `WAUW` (*Western Area Power Administration UGP West*) |
| Status | **canceled** (`CN`, 75.0 MW) — present in `eia860_generator_retired_and_canceled.parquet`, **zero operable generators** |

This row fails key (i) but **is not a mis-entry**: WAPA Upper Great Plains West genuinely
operates on both sides of the Eastern/Western interconnection seam, which runs through eastern
Montana — **Fort Peck (plant 6623) is in the same county, at −106.412 W, and is WECC**. The row
is therefore a real WAUW resource that would sit in the *Eastern* Interconnection.

It is **inert today** (canceled; contributes nothing to the 1,932 or the 98,738.1 MW), and the
§2.8(a) predicate would exclude it correctly and for the right reason. But NWPP-20 should record
that **the predicate's key (i) is doing real work for WAUW, not just catching a typo** — WAUW's
22 operable plants (1,128.3 MW) are all WECC today, and a future WAUW addition on the Eastern
side must not enter the NWPP LP. WAUW is 0.27–0.29 % of footprint load, so the exposure is small
but the mechanism is not hypothetical.

#### (c) Desert Bloom — **named, inert today, LIVE on the next vintage**

| Field | Value |
|---|---|
| Plant Code | 69290 · **Desert Bloom** · RE Desert Bloom LLC |
| Location | Maricopa County, **AZ** (Phoenix metro); NERC **WECC** |
| BA | **`DOPD`** — the same Washington PUD |
| Status | **proposed only** — `DSBLM` 150.0 MW Batteries, status `V`; zero operable generators |

This one **passes** the §2.8(a) predicate (it is WECC) and is caught only by geography. A Douglas
County PUD balancing a battery in Phoenix is the same implausibility as (a) in a different
interconnection, and `DOPD`'s three plant-table rows are Wells (real), Pine Forest (TX defect)
and Desert Bloom (AZ) — **two of three are suspect**, which suggests a respondent-side data
problem at this utility rather than three unrelated slips. It contributes **nothing** to this
census, but it enters the footprint the moment its status flips to operable. **Routed to
NWPP-20:** either extend the predicate with a Western-Interconnection bounding test, or add an
explicit, cited exclusion review at each 860 re-vintage. This audit recommends the former and
does not decide it.

#### (d) The small out-of-region rows that are **KEPT**

`PACW` carries three small California plants outside PacifiCorp's Klamath-area footprint —
Bakersfield 111 (1.4 MW, Kern County), Blue Skies Solar (1.0 MW, Kern County) and Foothill
Sanitary Landfill Solar (3.6 MW, San Joaquin County), **6.0 MW total, all WECC**. They pass the
predicate, they are inside the Western Interconnection, and remote-BA scheduling of small
merchant resources is a real arrangement rather than an impossibility. They are kept, named
here so they are not rediscovered as anomalies, and they are immaterial (0.006 % of the fleet).
`PACE`'s James W. Broderick (7.5 MW hydro, Pueblo County CO) is the same class and is kept.

---

## 3. The curated-fleet seam — **EXTEND the file, and fix `ISO_TO_BA_CODE` first**

### 3.1 What the file is, measured

`data/raw/eia-860/eia860_generators.parquet`: **19,725 rows, 15 columns**
(`plant_id`, `generator_id`, `plant_name`, `state`, `balancing_authority_code`, `technology`,
`energy_source`, `prime_mover`, `nameplate_capacity_mw`, `net_summer_capacity_mw`,
`operating_year`, `planned_retirement_year`, `planned_retirement_month`, `status`, `heat_rate`).
`balancing_authority_code` is exactly `{CISO, ERCO, ISNE, MISO, NYIS, PJM, SWPP}` — **zero NWPP
rows** — and its `state` list carries **no ID, OR or WA** (MT, NV, WY, CA, CO, AZ, NM appear only
because SPP/MISO/CAISO reach into them). The charter's description is confirmed in full.

### 3.2 It is NOT optional — it is the fleet loader's own source

| Reader | Path | What breaks without NWPP rows |
|---|---|---|
| **The fleet loader** | `data/fleet/eia860.py` (`EIA_860_PARQUET_NAME`, lines 606 / 2176 / 2424 / 2740) — `load_fleet_from_csv` → `_load_fleet_from_parquet` | **`FileNotFoundError`**: *"No EIA-860 data for NWPP: expected a per-ISO override CSV … or the generator parquet at …"*. There is no raw-pair fallback |
| **The hydro budget** | `data/hydro.py:680` | Card N3's own nameplate-per-plant table comes back **empty** |
| **Storage** | `model/storage.py:1235` | no storage fleet |
| **Announced retirements** | `data/announced_retirements.py:158/385` | step 1/1b sees nothing |
| Reserve MSSC (SPP-only today) | `model/reserves/spec.py:4403` | degrades gracefully (`return {}`) |
| CAMPD oil-primary screen | `data/fleet/campd_bins.py:165` | returns an **empty frozenset** — silently, see §3.3 |

**Recommendation, unambiguous as the charter requires: EXTEND `eia860_generators.parquet`, and
extend it THROUGH THE EXISTING PRODUCER.** `scripts/data/process_eia860.py` builds it and filters
on exactly one line:

```python
# scripts/data/process_eia860.py:203 (and :340 for the retired-window twin)
df = df[df["balancing_authority_code"].isin(BA_CODE_TO_ISO)]
```

So adding the 17 NWPP codes to `data/fleet/models.BA_CODE_TO_ISO` and re-running the producer
extends the file, its retired-window twin and the `iso` column together, with **no new script and
no bespoke read path**. Reading the raw `eia860_plant` + `eia860_generator_operable` pair instead
would require rewriting four solve-path modules and would leave every other ISO on a different
source — a rule-14 `[R-ACCURATE]` regression, not an improvement.

### 3.3 The blocker the charter located in the wrong module

`BA_CODE_TO_ISO` handles 17→1 correctly everywhere it is read — always as `.map()`, `.isin()` or
`{ba for ba, i in BA_CODE_TO_ISO.items() if i == iso}` (`scripts/score_capacity_hindcast.py:1327`,
`scripts/data/build_capacity_actuals.py:113`). **The inverse is where it breaks:**

```python
# src/market_sim/data/fleet/models.py:221
ISO_TO_BA_CODE: dict[str, str] = {iso: ba for ba, iso in BA_CODE_TO_ISO.items()}
```

With 17 NWPP entries in `BA_CODE_TO_ISO`, `ISO_TO_BA_CODE["NWPP"]` becomes **one arbitrary BA —
whichever is inserted last** — and every consumer compares against it with `==`:

| Call site | Effect for NWPP |
|---|---|
| `data/hydro.py:607, 639, **684**` | the hydro nameplate/budget tables cover **one BA's** plants — card N3's machinery, silently 1/17 of the fleet |
| `data/fleet/eia860.py:1653, 2574, 2748` | fleet-side BA filters wrong |
| `data/fleet/campd_bins.py:168` | oil-primary screen returns **empty**, indistinguishable from "no oil-primary plants" |
| `data/zone_assignment._ISO_TO_BA_CODE` (its own 1:1 dict) `:1092, :1120, :1325` | the plant→zone splitter sees one BA |
| `scripts/data/curate_fleet.py:106`, `curate_hydro_plant_modes.py:218`, `derive_egrid_family_heat_rates.py:147`, `scripts/lib/wind_shape.py:178` | same |

**Every one of these fails silently** — an empty or 1/17 result, never an exception. That is the
genuinely novel W2 code change, and it is in **at least five modules**, not the one
(`data/zone_assignment.py`) the charter's §2.3 names.

**Recommended shape for NWPP-20** (recommendation only): make the ISO→BA direction a
**codes-tuple** (`dict[str, tuple[str, ...]]`, or a parallel `ISO_TO_BA_CODES` with the scalar
retained for the seven 1:1 ISOs), move all 13 call sites from `== ba_code` to membership, and pin
it with a unit test asserting `len(ba_codes("NWPP")) == 17` **and** that a loaded NWPP fleet
reproduces the §2.1 census (939 plants / 1,930 generators / 98,238.1 MW after the §2.8(a)
rejection). The two existing set-comprehension call sites show the intended idiom already.

---

## 4. The load spine

### 4.1 It is on disk, and the window is complete once the 2022 half-file is read

`data/raw/eia-930/EIA930_BALANCE_<yr>_<half>.parquet` is committed for **2019-01 → 2026-06** and
carries **all 17 NWPP balancing authorities**, confirmed. 44 columns in three published variants
per series — **raw**, **(Imputed)** and **(Adjusted)**.

| | Charter | Measured (this audit) |
|---|---|---|
| Rows, 2023–2025 × 17 BAs | 394,424 non-null demand hours | **447,168 rows = 17 × 26,304** |
| Hours per BA per year | 8,751 / 8,784 / 8,760 | **8,760 / 8,784 / 8,760 — zero gaps** |
| Load-carrying rows | — | 394,560, of which **4** are null-demand (CHPD 1, GCPD 1, SCL 2, all 2024) → **394,556 non-null** |

The charter's shortfall is **not missing data**. The BALANCE files are split by *local* date, so
the first 8–9 **UTC** hours of 2023 sit in `EIA930_BALANCE_2022_Jul_Dec.parquet`. Reading 2022–2026
and then filtering on UTC year closes it exactly (15 load-carrying BAs × ~9 h = the charter's 136-row
gap). **Convention for NWPP-11:** read the adjacent half-files, never pad. The three Mountain BAs
show one *more* 2023 hour than the Pacific fourteen in the naive read — itself a corroboration of §6.

### 4.2 Energy, peak and load factor — the charter mixes two columns

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| Footprint demand, **raw** `Demand (MW)` | 284.265 TWh | 291.557 | 294.861 |
| Footprint demand, **`Demand (MW) (Adjusted)`** | **284.208 TWh** | **291.343** | **293.390** |
| *Charter* | *283.97* | *291.56* | *294.86* |
| Coincident peak, **raw** | 95,188 MW | 100,754 | **835,464** |
| Coincident peak, **Adjusted** | **49,290 MW** | **52,564** | **50,953** |
| *Charter* | *49,290* | *52,564* | *50,953* |
| Peak hour (Adjusted, UTC) | 2023-08-16 01:00 | 2024-07-10 01:00 | 2025-08-13 01:00 |
| Load factor (Adjusted) | 0.658 | 0.631 | 0.657 |
| Footprint net generation (Adjusted) | 277.590 TWh | 288.186 | 298.809 |

**The charter's peaks are confirmed to the MW** — and they are Adjusted-column peaks. Its
**energy row is the raw column** (2024 and 2025 match raw to 0.01 TWh) while its **load-factor
row is only consistent with the Adjusted energy** (2025: 293.390/8760/50,953 = 0.657, the
charter's value; the raw 294.86 gives 0.661). So the charter's own table mixes two series. The
internally consistent figures are the **Adjusted** row above, and they are what this audit
recommends every downstream NWPP series carry.

### 4.3 AVRN and GRID carry no load — confirmed, in all three variants

| BA | Rows | `Demand` null | `(Imputed)` null | `(Adjusted)` null | Net generation, 3 yr |
|---|---:|---:|---:|---:|---:|
| AVRN | 26,304 | **26,304** | 26,304 | **26,304** | 25.323 TWh |
| GRID | 26,304 | **26,304** | 26,304 | **26,304** | 53.131 TWh |

Confirmed exactly as the charter states, and in the Adjusted column too (the charter checked
only one). For both, `Total Interchange (MW) (Adjusted)` **equals** `Net Generation (MW)
(Adjusted)` in every hour to 0.0 MW — they generate and export everything.

**Consequence for zoning, stated as card N5 needs it:** they are **supply-side members and not
zone candidates**. A zone's *load* is the sum of its load-carrying BAs' Adjusted demand; AVRN's
and GRID's generation must be assigned to whichever zone their physical injection sits in
(AVRN's 19 plants are Oregon/Washington Columbia-Gorge wind and solar; GRID's single EIA-860
plant is Hermiston, Oregon) **without** adding a demand row. Note §4.6(b): GRID's EIA-930
generation is *not* the 689.4 MW EIA-860 assigns it, and that conflict has to be resolved before
its energy is placed anywhere.

### 4.4 The defect screen — 30 artifacts CONFIRMED, 54 REAL hours that a 2.5× screen would destroy, and 17 the charter missed

Screen applied: the repo's own basis — `|D| > _DEMAND_SPIKE_THRESHOLD × annual median` (2.5,
`data/eia930/demand.py:407`) **or** `D < 0` — per BA per year on the raw `Demand (MW)` column.
**84 hours flag. They are two different populations.**

**(a) The 30 artifact hours — the charter's list, confirmed exactly.**

| BA | 2023 | 2024 | 2025 | total |
|---|---:|---:|---:|---:|
| AVA | 0 | 7 | 3 | **10** |
| NWMT | 1 | 5 | 5 | **11** |
| NEVP | 0 | 1 | 5 | **6** |
| PACE | 1 | 0 | 0 | **1** |
| SCL | 0 | 1 | 1 | **2** |
| **Total** | | | | **30** |

The worst, with the charter's two named rows confirmed to the MW:

| BA | UTC hour | raw MW | Adjusted MW | × median |
|---|---|---:|---:|---:|
| AVA | **2025-10-12 10:00** | **810,948** | 1,064 | 558.1 |
| AVA | 2025-10-12 11:00 | 191,180 | 1,003 | 131.6 |
| NWMT | 2025-10-14 20:00 | 100,285 | 1,344 | 76.0 |
| NEVP | 2025-07-01 04:00 | 69,812 | 7,053 | 16.6 |
| NWMT | 2024-08-27 20:00 | 66,960 | 1,416 | 49.5 |
| PACE | 2023-08-07 19:00 | 65,826 | 6,911 | 11.5 |
| AVA | **2024-01-05 16:00** | **−58,286** | 1,692 | −40.4 |
| SCL | 2025-06-27 18:00 | −54,511 | 997 | −51.5 |

**`Demand (MW) (Adjusted)` repairs all 30**, every one landing back inside band. Unscreened they
put the 2025 coincident peak at **835,464 MW** against a true 50,953 — the charter's figure,
confirmed.

**(b) The 54 CHPD hours — REAL LOAD, and the reason a 2.5× screen must not be applied here.**

The remaining 54 flagged hours are **all CHPD, all in 12–16 January 2024**, and **`Adjusted`
leaves every one byte-identical to raw** — EIA's own verdict that they are measurements. The
daily maxima trace a cold snap, not a spike:

```
Jan 2024 CHPD daily max (MW, Adjusted):
05→367  06→323  07→357  08→371  09→376  10→349  11→408
12→524  13→583  14→573  15→572  16→560  17→487  18→478  19→433  20→394  21→366
```

**583 MW on 2024-01-13 is CHPD's annual peak**, and the same block contains the **whole NWPP-NW
zone's 2024 annual peak** (21,560 MW at 2024-01-13 19:00 UTC, §5) — the January-2024 Pacific
Northwest cold snap, region-wide. Peak/median ratio per BA-year on the Adjusted column:

| BA-year | median MW | peak MW | peak/median |
|---|---:|---:|---:|
| CHPD 2023 | 212 | 486 | **2.29** |
| **CHPD 2024** | **206** | **583** | **2.83** |
| CHPD 2025 | 210 | 525 | **2.50** |
| NEVP 2023 / 2024 / 2025 | 4,006 / 4,130 / 4,195 | 9,249 / 9,797 / 9,239 | **2.31 / 2.37 / 2.20** |
| every other BA-year | — | — | 1.39 – 2.09 |

`_screen_demand_spikes`'s docstring justifies its 2.5 factor on the claim that *"every legitimate
demand series has max/median ≤ 2.1"*. **Two of the fifteen load-carrying NWPP BAs falsify that in
every year**, and one crosses 2.5. The reason is structural, not accidental: CHPD is a small
(median 206 MW), winter-peaking, hydro-county BA whose load factor is low — the exact profile the
threshold was never calibrated against, because every ISO it *was* calibrated against is a large
aggregated system.

**(c) 17 exactly-zero NEVP demand hours, 2025 — NOT repaired by `Adjusted`, and not in the
charter.**

All NEVP, all 2025, in 06:00/07:00 UTC pairs (≈ 22:00–00:00 local Pacific) on 2025-04-18, 04-25,
05-15, 05-23, 06-20, 07-18, 08-22, 09-19, 11-21. Raw **and** Adjusted are both exactly `0.0`. This
is the class `_screen_demand_dropouts` exists for (a reporting gap posted as a *value*, not an
absent row) — a whole BA's metered demand is never 0 MW — and it is **live for NWPP** where it was
not for most registered ISOs.

**THE CONVENTION, as the charter asks this lane to establish it:**

> 1. **`Demand (MW) (Adjusted)` is the series every downstream NWPP demand read must use** — the
>    LP's demand, the zonal disaggregation, the benchmarks, the peak, the load factor, the
>    capacity-screen peak. It is EIA's own reconciled publication, it repairs all 30 artifact
>    hours, and it leaves the 54 real CHPD hours alone. Nothing in it is padded, interpolated or
>    rescaled **by this audit** (rule 13 `[R-MEASURED]`).
> 2. **Do NOT apply `_screen_demand_spikes` on top of it for NWPP.** At 2.5 it would delete
>    CHPD's 2024 annual peak and 53 neighbouring hours of a documented regional cold snap and
>    interpolate over them — a rule-14 `[R-ACCURATE]` violation by construction, burying a real
>    measurement inside a repair. If a belt-and-braces screen is wanted, the admissible form is
>    the **fuel-series two-statistic test** (`data/eia930/actuals.py`: `> 2.5 × median` **AND**
>    `> 2.5 × p99.9`), which passes all 54 CHPD hours (their p99.9 is their own peak) and still
>    catches every one of the 30 artifacts (all ≥ 11.5× median and far above p99.9). **This audit
>    recommends that form and NWPP-20 decides.**
> 3. **`_screen_demand_dropouts` IS needed** — the 17 NEVP zero hours survive `Adjusted`.
> 4. **`Demand (MW) (Imputed)` is NOT a series.** It is **447,133-of-447,168 null** — a sparse
>    patch column carrying only the ~35 imputed values, totalling 0.008 / 0.028 / 0.043 TWh. A
>    lane that reads it as a demand series gets essentially nothing.

### 4.5 The generation columns — a mid-window taxonomy change and an EIA spelling error

The screen was also run across **all 19 `Net Generation (MW) from …` columns**. It flags **28
hours**, every one co-located with a §4.4(a) demand artifact (AVA hydro 810,113 MW at the same
2025-10-12 10:00; NWMT hydro; NEVP gas; AVA "other"), plus three sub-10 MW rows that are noise.
No *new* defect population. But two structural facts fall out and both are first-order:

**(a) The fuel taxonomy changes at 2024-07.** Measured first/last non-zero month, footprint-wide:

| Column family | Non-zero span |
|---|---|
| `Hydropower and Pumped Storage`, `Solar`, `Wind` | 2023-01 → **2024-07** |
| `Hydropower Excluding Pumped Storage`, `Solar without Integrated Battery Storage`, `Solar with Integrated Battery Storage`, `Wind without Integrated Battery Storage` | **2024-07** → 2025-12 |
| `Battery Storage`, `Geothermal` | **2024-11** → 2025-12 |
| `Pumped Storage`, `Wind with Integrated Battery Storage`, `Other Energy Storage`, `Unknown Energy Storage`, `Unknown Fuel Sources` | **never non-zero** anywhere in the footprint |

Read literally, footprint hydro is 104.2 TWh (2023) → 55.4 (2024) → **0.0 (2025)**. **Union the
old and new families** and the mix reconciles to the published `Net Generation (Adjusted)` within
**−0.104 / +0.001 / −0.241 TWh (0.04 % / 0.00 % / 0.08 %)**:

| TWh (Adjusted, unioned) | 2023 | 2024 | 2025 | share 2024 |
|---|---:|---:|---:|---:|
| Hydro (+ PS) | 104.228 | 105.298 | 110.303 | **36.5 %** |
| Natural gas | 70.155 | 73.328 | 71.253 | 25.4 % |
| Coal | 42.278 | 38.370 | 42.276 | 13.3 % |
| Wind | 30.434 | 34.986 | 38.205 | 12.1 % |
| Solar | 13.001 | 17.218 | 20.129 | 6.0 % |
| Nuclear | 8.448 | 9.970 | 7.772 | 3.5 % |
| Other fuel sources | 8.452 | 8.512 | 8.060 | 3.0 % |
| Oil | 0.491 | 0.382 | 0.459 | 0.1 % |
| Battery / geothermal | 0.000 | 0.124 | 0.111 | 0.0 % |
| **TOTAL** | **277.486** | **288.187** | **298.568** | |

**Pumped storage is unobservable** in EIA-930 for this footprint in every year, though EIA-860
carries 314.0 MW of it — the SOCO audit found the same class of gap. Per-BA never-reported
column lists are in the reproduction output (§11); `DOPD`, `GCPD`, `SCL`, `TPWR` and `WAUW` report
**only** hydro, which is correct — they are hydro-only BAs.

**(b) An EIA spelling error in an Adjusted column name.** The raw column is
`Net Generation (MW) from Solar with Integrated Battery Storage`; its Adjusted twin is committed as
`Net Generation (MW) from Solar **witho** Integrated Battery Storage (Adjusted)`. Any code
building the Adjusted name as `f"{base} (Adjusted)"` **raises `KeyError` or silently drops the
column**. Named here so NWPP-11 does not lose it.

**Negative readings** are widespread and mostly legitimate (station service / metering):
solar 7,783 h, battery 11,523 h (charging), wind 2,574 h, gas 1,783 h, nuclear 516 h. Two are not:
`Other Fuel Sources` min **−59,867 MW** and `Hydropower Excluding Pumped Storage` min
**−55,156 MW**, both inside the §4.4(a) artifact hours. `Adjusted` repairs the hydro one and
leaves 4,186 of 4,187 negative "other" hours — the small ones are real.

### 4.6 Two seam facts that will break a naive derive

**(a) BPAT's balance identity fails structurally.** Testing
`Demand = NetGen − TotalInterchange` on the Adjusted columns, per BA over 2023–2025:

| BA | mean residual MW | σ | fraction of hours \|resid\| > 1 MW |
|---|---:|---:|---:|
| **BPAT** | **−3,206.4** | 1,770.0 | **81.5 %** |
| GCPD | −4.2 | 3.0 | 89.6 % |
| NEVP | +13.9 | 380.8 | 5.1 % |
| IPCO | −0.6 | 1.0 | 28.6 % |
| PACW, PSEI, TPWR | 0.000 | 0.000 | 0.0 % |
| the remaining eight | \|mean\| ≤ 0.03 | ≤ 19.6 | ≤ 2.0 % |

BPA's reported net export exceeds (net generation − demand) by **3.2 GW on average** — it moves
energy it neither generates nor serves (third-party transmission service across the federal
system). The consequence is arithmetic and unavoidable:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| Σ per-BA `Total Interchange (Adjusted)` | +28.819 TWh | +32.674 | +18.272 |
| Footprint `NetGen − Demand` | **−6.618 TWh** | **−3.157** | **+5.418** |
| gap | +35.437 | +35.830 | +12.854 |

**Summing the 17 BAs' `Total Interchange` does NOT give the footprint's external position.** The
identity to use for the footprint boundary is `NetGen − Demand`; a signed external schedule needs
the per-counterparty DIBA product (`pending NWPP-11`). This is a direct input to card N4 and a
hard constraint on NWPP-34.

**(b) `GRID` is a source conflict, not a rounding difference.**

| | EIA-860 (`Balancing Authority Code == "GRID"`) | EIA-930 (`Balancing Authority == "GRID"`) |
|---|---|---|
| Fleet | **1 plant** — Hermiston Power Partnership (55328), OR, **689.4 MW** | — |
| Max hourly net generation | ≤ 689.4 MW by construction | **3,208 MW = 4.65× nameplate** |
| Annual net generation | ≤ 6.04 TWh | **16.79 / 18.62 / 17.72 TWh** |
| Implied capacity factor on the 860 fleet | ≤ 1.00 | **2.93** |

Gridforce Energy Management provides balancing-authority *services* to third-party resources, so
its EIA-930 BA covers generation whose EIA-860 `Balancing Authority Code` points elsewhere. **The
two sources do not describe the same set of resources**, and GRID is ~6 % of footprint net
generation (17.7 TWh/yr against 298.8). Taking GRID's energy from EIA-930 risks double-counting
resources EIA-860 attributes to another BA — possibly outside the footprint; taking it from
EIA-860 yields 689.4 MW and a 6 % hole in the mix. **This has to be adjudicated before NWPP-33
places GRID's generation anywhere.** By contrast **AVRN is clean**: 2,536 MW peak against
2,848.7 MW nameplate (0.89×), implied CF 0.34 — exactly a wind/solar portfolio.

---

## 5. Seasonal peak by candidate zone — **MEASURED**

Card N5's five candidate groups, on committed hourly `Demand (MW) (Adjusted)`, coincident zone
peak. Winter = Nov–Mar, summer = Jun–Sep. Peak hours are **UTC** (§6).

| Zone | Year | Annual peak MW | Peak hour (UTC) | Winter peak | Summer peak | **Verdict** | S/W |
|---|---:|---:|---|---:|---:|---|---:|
| **NWPP-NW** | 2023 | 19,790 | 2023-01-30 16:00 | 19,790 | 17,015 | **WINTER** | 0.86 |
| | 2024 | 21,560 | **2024-01-13 19:00** | 21,560 | 17,326 | **WINTER** | 0.80 |
| | 2025 | 21,186 | 2025-02-12 16:00 | 21,186 | 17,379 | **WINTER** | 0.82 |
| **NWPP-OR** | 2023 | 8,377 | 2023-08-17 01:00 | 7,660 | 8,377 | **SUMMER** | 1.09 |
| | 2024 | 8,342 | 2024-07-10 01:00 | 7,854 | 8,342 | **SUMMER** | 1.06 |
| | 2025 | 7,997 | **2025-02-12 16:00** | 7,997 | 7,838 | **WINTER** | 0.98 |
| **NWPP-INLAND** | 2023 | 8,000 | 2023-07-21 00:00 | 7,189 | 8,000 | **SUMMER** | 1.11 |
| | 2024 | 8,389 | 2024-07-23 01:00 | 7,547 | 8,389 | **SUMMER** | 1.11 |
| | 2025 | 8,230 | 2025-07-02 02:00 | 7,509 | 8,230 | **SUMMER** | 1.10 |
| **NWPP-EAST** | 2023 | 8,941 | 2023-07-23 01:00 | 7,236 | 8,941 | **SUMMER** | 1.24 |
| | 2024 | 9,562 | 2024-08-07 00:00 | 7,111 | 9,562 | **SUMMER** | 1.34 |
| | 2025 | 9,717 | 2025-07-15 01:00 | 7,493 | 9,717 | **SUMMER** | 1.30 |
| **NWPP-SNV** | 2023 | 9,249 | 2023-07-22 01:00 | 4,750 | 9,249 | **SUMMER** | **1.95** |
| | 2024 | 9,797 | 2024-07-11 01:00 | 4,765 | 9,797 | **SUMMER** | **2.06** |
| | 2025 | 9,239 | 2025-07-15 01:00 | 4,941 | 9,239 | **SUMMER** | **1.87** |

**Per balancing authority** (summer/winter peak ratio; > 1 = summer-peaking):

| BA | 2023 | 2024 | 2025 | verdict |
|---|---:|---:|---:|---|
| CHPD | 0.60 | 0.50 | 0.55 | **WINTER** |
| TPWR | 0.80 | 0.72 | 0.75 | **WINTER** |
| SCL | 0.82 | 0.71 | 0.81 | **WINTER** |
| DOPD | 0.81 | 0.66 | 0.72 | **WINTER** |
| BPAT | 0.85 | 0.82 | 0.82 | **WINTER** |
| PSEI | 0.89 | 0.79 | 0.83 | **WINTER** |
| AVA | 0.95 | 0.92 | 0.95 | **WINTER** |
| NWMT | 0.96 | 0.97 | 0.89 | **WINTER** |
| PACW | 0.98 | **1.01** | 0.85 | **FLIPS** |
| GCPD | 1.10 | 1.06 | 1.07 | **SUMMER** |
| WAUW | 1.17 | 1.07 | 1.08 | **SUMMER** |
| PGE | 1.23 | 1.10 | 1.13 | **SUMMER** |
| PACE | 1.24 | 1.35 | 1.30 | **SUMMER** |
| IPCO | 1.41 | 1.38 | 1.34 | **SUMMER** |
| NEVP | 1.95 | 2.06 | 1.87 | **SUMMER** |

**8 winter · 6 summer · 1 flipping.** The result is measured, not inferred from regional
reputation, and it is not the simple "the Northwest is winter-peaking" story: **the footprint's
own coincident peak is a SUMMER peak in all three years** (§4.2) because the summer-peaking east
and south are large enough to carry it, while its largest zone peaks in winter.

**What this does to card N7.** `PLANNING_RESERVE_MARGIN_BY_ISO` is `dict[str, float]` — **one
scalar per ISO**. A footprint in which NWPP-NW peaks in January and NWPP-SNV peaks in July at
twice its own winter load cannot be sized by one number against one peak, and neither can the
reliability floor that reads it (`accredited_firm_capacity_mw` vs `peak × (1 + PRM)`). NWPP-INLAND
is worse than a scalar: it **mixes** winter-peaking AVA (0.92–0.95) and NWMT with summer-peaking
IPCO (1.34–1.41) and WAUW, so even a per-zone seasonal PRM is an average over two regimes inside
that one zone. This is a structural finding for NWPP-20 and card N7, surfaced here rather than in
W3; it is **not** this lane's to decide.

---

## 6. Timezone — **CLOSED by measurement; the convention is UTC**

Measured by differencing `Local Time at End of Hour` against `UTC Time at End of Hour` for all
447,168 rows.

| Class | BAs | Offsets observed | Hours at each |
|---|---|---|---|
| **Pacific** | AVA, AVRN, BPAT, CHPD, DOPD, GCPD, GRID, **IPCO**, NEVP, PACW, PGE, PSEI, SCL, TPWR (**14**) | −8 / −7 | 9,171 / 17,133 |
| **Mountain** | **NWMT, PACE, WAUW** (**3**) | −7 / −6 | 9,171 / 17,133 |

The charter's split is **confirmed exactly**, and this audit adds four checks it did not run:

1. **Stable across years.** Every BA shows the same offset pair in 2023, 2024 and 2025
   independently. No BA changes class.
2. **All six DST transitions present and correctly signed** — 17 BAs × 6 = **102** transitions,
   at exactly the right UTC instants, with the 14 Pacific BAs flipping **one hour after** the 3
   Mountain BAs in both directions:

   | UTC instant | Mountain (3 BAs) | Pacific (14 BAs) |
   |---|---|---|
   | 2023-03-12 09:00 / 10:00 | −7 → −6 | −8 → −7 |
   | 2023-11-05 08:00 / 09:00 | −6 → −7 | −7 → −8 |
   | 2024-03-10 09:00 / 10:00 | −7 → −6 | −8 → −7 |
   | 2024-11-03 08:00 / 09:00 | −6 → −7 | −7 → −8 |
   | 2025-03-09 09:00 / 10:00 | −7 → −6 | −8 → −7 |
   | 2025-11-02 08:00 / 09:00 | −6 → −7 | −7 → −8 |

3. **The IPCO reconciliation, recorded as the charter asks.** Idaho Power files **Pacific**,
   although southern Idaho (including Boise, its load centre) is legally **Mountain**. Measured
   directly: at UTC `2023-07-28 08:00`, IPCO stamps local `01:00` (−7) while PACE stamps `02:00`
   (−6). This is not an error to repair — it is Idaho Power's filed convention and the EIA-930
   `Local Time` column is self-consistent with it. It matters only if a downstream series is
   built on IPCO's *local* clock and then compared to a Mountain-clock artifact (an Idaho Power
   IRP table, say); **NWPP-12 must state the clock of every transcribed IPCO value.**
4. **Local timestamps are NOT unique; UTC timestamps are.** Every BA has **26,304 unique UTC
   hours** and exactly **3 duplicated LOCAL timestamps** across 2023–2025 — the three fall-back
   repeats. The local column cannot key a join.

**THE CONVENTION, as the charter asks this lane to state it:**

> **`UTC Time at End of Hour` is the canonical hour and the only admissible join key** for every
> NWPP series — the load spine, the derived per-BA files, the fuel mix, the interchange, the
> benchmarks and any price series card N2 produces. It is unique, gap-free (§4.1), uniform
> across the two-timezone footprint, and immune to the fall-back ambiguity.
> `Local Time at End of Hour` is **provenance only**: every derived artifact states which clock
> its source used, and no artifact is keyed on it. The desk's recommended *reporting* zone
> (`America/Los_Angeles`, 81.6 % of load) is a presentation choice that does not change any join
> and is card N6's to rule on.
> `scripts/data/fetch_eia930_hourly.BA_TIMEZONE` carries **no entry for any of the 17** and gains
> them in W1 (NWPP-11, additive): fourteen `America/Los_Angeles`, three
> (`NWMT`, `PACE`, `WAUW`) `America/Denver`. Those are the DST-aware zone names matching the
> measured offset pairs; **`IPCO` takes `America/Los_Angeles`**, per the reconciliation above,
> not `America/Boise`.

Gate **G19** is therefore closed on the data side. What remains is card N6's convention choice,
which this measurement constrains rather than answers.

---

## 7. The registry-values table

One row per value NWPP-20 needs. **Every cell is a cited value, a repo-measured value, or
`pending`** (rules 5 `[R-NO-MAGIC]`, 13 `[R-MEASURED]`). Where this lane can supply the
*identification basis* but not the number, the basis is given and the number stays pending —
inventing a plausible value is the failure mode these rules exist to stop.

| # | Registry target | Value | Basis / citation |
|---|---|---|---|
| 1 | `PLANNING_RESERVE_MARGIN_BY_ISO["NWPP"]` | **pending NWPP-12** | The footprint has **no single peak season** (§5): NWPP-NW winter ×3, NWPP-EAST/SNV summer ×3, NWPP-OR flips. The registry is one scalar per ISO, so the shape is wrong before the value is. Source is the participants' own IRP planning reserve margins (PacifiCorp, PGE, Idaho Power, Avista, NorthWestern, Puget, NV Energy), **by season**, transcribed with URL + page by NWPP-12. **Do not** carry another ISO's value (rule 25 `[R-ISO-SCOPE]`) |
| 1b | Seasonal peak per zone (the requirement's operand) | **MEASURED — §5** | This audit. NW winter / OR flips / INLAND summer / EAST summer / SNV summer, with peak hours and S/W ratios per year |
| 2 | `ISOConfig.voll` | **pending NWPP-12 — and the object is different from every registered ISO's** | See §7.1 below. This is a *recommendation on sourcing*, which is the only rule-13-compliant thing this lane can supply |
| 3 | BA → zone map (`_NWPP_BA_ZONES`) | **candidate MEASURED — §9** | Keyed on `Balancing Authority Code`, never state (a state holds several BAs and a BA holds several states). Zone shares 2023/24/25 measured in §9. **Dispositive evidence is NWPP-12's WECC path ratings** |
| 4 | `TRANSMISSION_BASE_STATIC_VINTAGE["NWPP"]` | **pending NWPP-12** | An `int` year = the vintage of the WECC path-rating catalogue NWPP-12 transcribes. SPP took 2026; ERCOT 2024; NEISO/CAISO 2023 |
| 5 | Inter-zone TTC | **pending NWPP-12** | WECC published path ratings where a boundary maps to a rated path; a documented Tier-3 non-binding placeholder where none does. §9 names which boundaries the desk should expect to have no rating |
| 6 | `MARKET_DESIGN` / `_CURVE_ISOS` / `_CAPACITY_ISOS` | **NWPP ABSENT from all three** | No capacity market anywhere in the footprint → `DEFAULT_MARKET_DESIGN`, `capacity_market=False`, the ERCOT/SPP branch. The absence is deliberate and documented (card N7) |
| 7 | `QUEUE_CAP_PER_TECH_GW["NWPP"]` | **MEASURED basis, value is NWPP-20's rounding** | Demonstrated peak annual COD, EIA-860 `Operating Year`, footprint, 2019–2025 (GW/yr) — the **same identification ERCOT's own entry uses** (*"modestly above demonstrated peak annual COD"*, `capacity_market.py` QUEUE_CAP_GW): **wind 1.484** (2020) · **solar 1.953** (2024) · **storage 0.919** (2025) · **gas_ct 0.456** (2024) · **geothermal 0.048** (2019) · **gas_cc 0.000** · **nuclear 0.000** · hydro 0.125 (2020). Full seven-year series in §11's output |
| 8 | Gas basis proxy per zone | **MEASURED attribution, prices pending NWPP-12** | `eia860_plant.parquet` `Natural Gas Pipeline Name 1` per plant → gas MW by zone × pipeline (§7.2). **5,518.0 MW of 23,305.3 (23.7 %) names no pipeline.** The *backcast* fuel input is per-plant EIA-923 delivered gas, **already committed** (30–32 plants/yr, §7.3) — the hub series is a forecast-side need |
| 9 | Coal price basis | **MEASURED for 6,0 GW, ABSENT for 2.9 GW** | `eia923_monthly_fuel_costs.parquet` carries delivered $/MMBtu for **8 coal plants** 2023–2025 (§7.3). The **four mine-mouth / captive-mine plants carry ZERO rows** — Colstrip (1,647.4 MW), Centralia (729.9), TS Power (242.0), Hardin (115.7) = **2,911.7 MW = 32.7 % of coal**, including the footprint's largest coal plant at ~9–11 TWh/yr. Basin labels (PRB / Uinta / Colstrip mine-mouth) are **pending NWPP-12** |
| 10 | Nuclear monthly CF, Columbia Generating Station | **MEASURED — not pending** | EIA-923 monthly net generation, plant **371**, ÷ (1,200.0 MW × hours): annual CF **0.802 / 0.948 / 0.737** for 2023/24/25; monthly CF series in §11's output. **Biennial refuelling** is visible and is the whole of the variance — deep outages May–Jun 2023 (CF 0.10 / 0.30) and Apr–Jun 2025 (0.27 / −0.00 / 0.12), **none in 2024** (min monthly CF 0.92). NRC licence/SLR status is separately `pending NWPP-12` |
| 11 | State RPS / CES floors | **statutes cited, SCHEDULES pending NWPP-12** | §7.4 — the seven footprint states differ sharply and three have **no** mandate at all |
| 12 | LTLF edition + vintage | **pending NWPP-12 — W2 PRECONDITION (gate G12)** | `scripts/lib/load_forecast/` requires a declared edition **and** vintage (`test_specs_declare_an_edition_and_a_vintage`). No footprint-wide long-term load forecast is committed; assembling one from the IRPs must document the assembly |
| 13 | eGRID vintage | **2023 — NO ACTION NEEDED** | `data/zone_assignment._EGRID_VINTAGE = 2023` is a **module-level scalar, not a per-ISO dict** (`data/fleet/egrid2023_data_rev2.xlsx`). NWPP needs no entry, exactly as SPP needed none |
| 14 | `TAIL_THRESHOLD["NWPP"]` (×3 files) | **SKIPPED — the condition failed (NWPP-13 read NO); executed by NWPP-31, 2026-09-14** | Card N2's condition was *"only if a price series exists"*, and NWPP-13's pre-registered STOP gate refused the WEIM candidate (on-peak price **22.6 / 23.6 / 37.5 %** below the Mid-C Peak index against a ±10 % bar). So **no key in any of the three copies** — `calibration_verdict.py`, `derive_actual_tail.py`, `derive_actual_amplitude.ISOS` — with the skip and its reason documented in the latter two at the table a future lane would edit (**gate G6**). Verified by execution: both derives re-run emit **zero** NWPP rows. No threshold was invented from the model's own output (rule 1 `[R-STRUCT]`), and a neighbouring hub stays refused (gate **G17**). The run reads `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` off exactly this absence |
| 15 | `ISO_STATES["NWPP"]` (CAMPD) | **ID, MT, NV, OR, UT, WA, WY** | Measured §8. **CO excluded** — its one footprint plant is 7.5 MW of **hydro** (§2.3), zero CEMS-eligible units. **CA excluded** — 50.8 MW, of which 15.0 MW is combustion and **none** appears in `CA_2024` CAMPD among footprint plants. **TX excluded** by the §2.8(a) rejection |
| 16 | Offer-curve band multipliers | **1.0, all bands** | Gate G5 and rule 25 `[R-ISO-SCOPE]`: no ISO's fitted multiplier transfers. Most of this footprint dispatches cost-based against IRPs rather than offering into a market, so a band ≠ 1.0 needs a much stronger story here than in an RTO. The desk's stated posture is bands stay 1.0 |

### 7.1 VOLL — why FERC Order 831's $2,000 is the wrong object here

The registered ISOs' `voll` values are **market offer caps**: ERCOT $5,000 (the DA system-wide
offer cap), CAISO $2,000 (the administrative price cap), SPP $2,000 (Tariff Attachment AF §3.2 /
the Order 831 verification ceiling), ISO-NE $2,000 (Tariff §III.1.10.1A). Each is a number that
*exists* because its market has an offer-based clearing engine and a regulator that capped it.

**FERC Order 831 (Offer Caps in Markets Operated by Regional Transmission Organizations and
Independent System Operators, 157 FERC ¶ 61,115, 2016; codified at 18 C.F.R. §35.28(g)(11))
applies by its own terms to RTOs and ISOs.** The Northwest Power Pool is neither: there is no
pool-wide day-ahead market, no clearing engine, no incremental energy offers to cap and no
$1,000/MWh cost-verification threshold for anything to sit above. Importing $2,000 here would put
a **market-design artifact from a market that does not exist in this footprint** into the LP's
scarcity ceiling. That is precisely the rule-13 `[R-MEASURED]` failure — a value with no forward
analogue in the region being modelled — and the fact that four registered ISOs happen to use it
makes it a rule-25 `[R-ISO-SCOPE]` transfer as well.

**What VOLL actually is in this LP** is the price on the slack variable — the economic cost of a
lost MWh to the customers who lose it. That object exists in a cost-based footprint just as much
as in an RTO; it simply is not published as a cap. **This lane therefore proposes a SOURCING
RULE, not a number** (proposing a number would be the invention these rules forbid):

> `ISOConfig(name="NWPP").voll` is identified from **customer-damage-function evidence for this
> footprint**, in this order of preference, whichever NWPP-12 can cite with URL + page:
> 1. a **loss-of-load cost or unserved-energy penalty stated in the participants' own IRPs** —
>    several Western IRPs state one explicitly for their resource-adequacy economics, and it is
>    the same object, for the same customers, in the same window;
> 2. failing that, the **LBNL Interruption Cost Estimate (ICE) Calculator**
>    (`icecalculator.com`, Lawrence Berkeley National Laboratory / US DOE — the standard US
>    customer-damage-function tool, built on ~35 utility interruption-cost surveys), evaluated on
>    the footprint's own residential / commercial / industrial customer mix and its measured
>    average interruption duration;
> 3. failing both, **WECC's or the Western Resource Adequacy Program's own published planning
>    VOLL**, if one exists (`pending NWPP-12`).
>
> Whatever value lands is a **ledgered free parameter** in the keeper's DOF ledger (rule 21
> `[R-DOF]`) with its identification source named, and it is **never swept against a gate**.

Two things NWPP-20 should know about the mechanics while the value is pending. VOLL cannot be
left absent — `ISOConfig.voll` is `Field(gt=0.0)`, so the config will not validate. And it cannot
be set low: in this LP `VOLL × Slack` is the last term in the objective, so a VOLL below the most
expensive real unit's marginal cost makes shedding load cheaper than running that unit, and the
LP will shed rather than dispatch. Any interim value must therefore be **declared as interim, in
the run's attestation**, not quietly adopted as the answer.

### 7.2 Gas basis — which pipeline serves which zone, measured

Gas nameplate (CC + CT + ST + ICE = 23,305.3 MW) by candidate zone × `Natural Gas Pipeline Name 1`:

| Pipeline | NWPP-NW | NWPP-OR | NWPP-INLAND | NWPP-EAST | NWPP-SNV | Total MW |
|---|---:|---:|---:|---:|---:|---:|
| Kern River Gas Transmission | — | — | — | 217.0 | **4,747.1** | 4,964.1 |
| Southwest Gas (LDC) | — | — | — | — | **3,419.1** | 3,419.1 |
| TransCanada – Gas Transmission NW (GTN) | 906.1 | **1,490.2** | 554.3 | — | — | 2,950.6 |
| Northwest Pipeline GP | **2,036.8** | — | 762.2 | 144.0 | — | 2,943.0 |
| "Pacific Gas" | — | 1,319.3 | — | — | — | 1,319.3 |
| *Other – see pipeline notes* | 329.3 | — | 7.2 | **1,174.1** | — | 1,510.6 |
| NorthWestern Energy (LDC) | — | — | 261.6 | — | — | 261.6 |
| Questar Pipeline | — | — | — | 152.4 | — | 152.4 |
| Puget Sound Energy (LDC) | 128.5 | — | — | — | — | 128.5 |
| Tuscarora Gas Transmission | — | — | — | — | 117.6 | 117.6 |
| Intermountain Gas (LDC) | — | — | 12.7 | 5.6 | — | 18.3 |
| Colorado Interstate Gas | — | — | — | 2.2 | — | 2.2 |
| **Named total** | **3,400.7** | **2,809.5** | **1,598.0** | **1,695.3** | **8,283.8** | **17,787.3** |
| **No pipeline named** | | | | | | **5,518.0** |

This confirms the charter's instinct that NWPP is **not one gas hub**, and it says which hub each
zone should price against rather than leaving it to judgement:

- **NWPP-SNV** → **Kern River** (4,747.1 MW direct, plus Southwest Gas as the LDC downstream of
  Kern River / El Paso). Unambiguous.
- **NWPP-NW** → **Northwest Pipeline** (2,036.8 MW), whose Canadian-border receipt point is
  **Sumas** — the charter's candidate, corroborated.
- **NWPP-OR** → **GTN** (1,490.2 MW), whose interconnect with Northwest Pipeline is **Stanfield** —
  the charter's candidate, corroborated.
- **NWPP-INLAND** → **split** NWP 762.2 / GTN 554.3. A single hub misprices roughly a third of it.
- **NWPP-EAST (PACE)** → **Rockies**, i.e. **Opal** — but 1,174.1 MW of its 1,695.3 MW is filed as
  *"Other – please explain in pipeline notes"*, so the attribution is **provisional**. NWPP-12
  should read `Pipeline Notes` for those plants before fixing the basis. Questar (152.4 MW) is the
  Rockies corroboration.

The 5,518.0 MW naming no pipeline is 23.7 % of gas and is a genuine gap, not an artifact of this
audit; it is concentrated in older and smaller units. **The backcast does not depend on any of
this**: the rule-13 measured fuel input is per-plant EIA-923 delivered gas, which is committed
(§7.3). The hub attribution is a **forecast-side** need, and saying so keeps W4 unblocked.

### 7.3 Measured delivered fuel — what is already on disk

`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`, footprint plants, per plant per
month `price_per_mmbtu` + `quantity`:

| Fuel group | 2023 | 2024 | 2025 |
|---|---|---|---|
| Coal | 94 rows / **8 plants** | 96 / 8 | 92 / 8 |
| Natural gas | 354 rows / **30 plants** | 373 / 32 | 339 / 30 |
| Petroleum | 62 rows / 9 plants | 52 / 9 | 62 / 7 |

Mean delivered **coal** $/MMBtu — the basin structure is visible in the price without needing the
basin label:

| Plant | State | BA | 2023 | 2024 | 2025 |
|---|---|---|---:|---:|---:|
| Dave Johnston | WY | PACE | 1.14 | 1.20 | 1.24 |
| Wyodak | WY | PACE | 1.36 | 1.37 | 1.40 |
| Naughton | WY | PACE | 2.48 | 2.67 | 2.66 |
| Bonanza | UT | PACE | 2.46 | 3.36 | 3.38 |
| Hunter | UT | PACE | 2.71 | 3.46 | 3.56 |
| Jim Bridger | WY | PACE | 3.42 | 3.00 | 3.12 |
| Huntington | UT | PACE | 2.31 | 3.66 | 3.81 |
| North Valmy | NV | NEVP | 5.00 | 4.61 | 5.65 |

**Colstrip, Centralia, TS Power and Hardin have no rows in any year** (their *generation* is
present — Colstrip 10.81 / 9.02 / 9.16 TWh, Centralia 4.14 / 2.82 / 3.14 TWh). These are
mine-mouth or captive-mine arrangements that do not generate a purchased-fuel receipt of the kind
EIA-923 Schedule 2 collects. **NWPP-12's coal item must supply a cited fuel cost for Colstrip
specifically** — it is the footprint's largest coal plant and its marginal cost is otherwise
undefined.

Gas ranges from **$1.09/MMBtu** (Carty, PGE, 2024) to **$10.09** (Naughton, PACE, 2025), with the
2023 → 2024 collapse (typically $5–8 → $2–3) visible at every plant — the measured input the
playbook §0.5 requires, already committed.

### 7.4 State RPS / CES — the statutes, with the schedules pending

The footprint spans seven states whose mandates differ more sharply than in any registered ISO —
**three have a binding decarbonization target, two have a modest RPS, and two have none.** This
lane cites the **instrument**; the **numeric schedule** is `pending NWPP-12`, to be transcribed
against the statute and cross-checked on DSIRE (`dsireusa.org`, NC Clean Energy Technology
Center), because a mis-transcribed percentage is exactly the kind of magic number rule 5 forbids.

| State | Footprint MW | Instrument | Character | Schedule |
|---|---:|---|---|---|
| **WA** | 31,711.8 | **Clean Energy Transformation Act**, RCW 19.405 (Laws of 2019 ch. 288, SB 5116) | Coal-free, then GHG-neutral, then 100 % clean — a **CES**, not an RPS. Also RCW 19.285 (I-937) for the legacy RPS | **pending NWPP-12** |
| **OR** | 19,035.4 | **HB 2021 (2021)**, ORS 469A.400–.475; legacy RPS ORS 469A.052 | Emissions-reduction schedule on retail electricity providers, to 100 % | **pending NWPP-12** |
| **NV** | 15,638.3 | **NRS 704.7801–704.7828** (SB 358, 2019) | Percentage RPS with a statutory end-state goal | **pending NWPP-12** |
| **UT** | 9,769.3 | **UCA 54-17-601 to -603** (SB 202, 2008) | **Non-binding goal, cost-effectiveness-conditioned** — not a mandate | **pending NWPP-12** |
| **WY** | 8,654.1 | — | **NO RPS or CES** | n/a |
| **MT** | 6,939.6 | **MCA 69-3-2001 to -2010** | Modest RPS; applicability narrowed in recent sessions | **pending NWPP-12** |
| **ID** | 6,431.3 | — | **NO RPS or CES** | n/a |

Two consequences NWPP-20 should carry rather than discover. **RPS enters this model as an annual
LP constraint whose dual is the REC price** (CLAUDE.md, capacity evolution §1.4) — one constraint
per ISO. A footprint where WA (32 % of nameplate) is under a 100 % CES, WY and ID (15 %) are under
nothing, and PACE's own fleet straddles UT/WY/ID **cannot be expressed by one ISO-level RPS
fraction** without averaging across a legal boundary. And the obligations attach to **retail
providers**, not to balancing authorities or to plants, so the mapping from statute to LP
constraint is a modelling choice that needs stating — PacifiCorp serves load in six states under
six different regimes from one interconnected system. Flagged, not decided.

---

## 8. CEMS coverage arithmetic (card N8)

**State coverage today**, `data/raw/campd-unit-level/` at this base sha:

| Footprint state | CAMPD years present |
|---|---|
| **MT** | 2019–2026 |
| **NV** | 2019–2026 |
| **CA** | 2019–2026 |
| **WY** | 2023–2026 |
| **ID** | **none** |
| **OR** | **none** |
| **UT** | **none** |
| **WA** | **none** |
| **CO** | **none** — and **none needed** (§2.3: one 7.5 MW *hydro* plant, not solar as the charter says) |

**The eligibility construction**, so the arithmetic is checkable rather than asserted: a Part-75
proxy of *fossil-combustion technology* (coal, gas CC/CT/ST/ICE, petroleum liquids, petroleum
coke) at a plant whose fossil nameplate exceeds 25 MW. **Validated against the four states where
CAMPD is present**: it predicts 30 plants, of which **21 actually appear in the 2024 extracts —
100 % precision (every CAMPD footprint facility is predicted), 70 % plant recall, 94.9 % MW
recall.** The nine predicted-but-absent plants are 804.9 MW of small cogeneration and
industrial ICE/CT sites (Colstrip Energy LP, Yellowstone Energy, Shute Creek, Basin Creek,
Yellowstone County, Western 102, Nevada Cogen 2, General Chemical, Genesis Alkali) — the expected
non-Part-75 residue.

**Nameplate coverage** (on the WECC-filtered footprint, 98,238.1 MW):

| | MW | % of footprint |
|---|---:|---:|
| Fossil-combustion nameplate (the ceiling CAMPD could ever reach) | 32,371.2 | 32.95 % |
| Part-75 proxy, all nine states — **the charter's ~32 % estimate** | **32,059.5** | **32.63 %** |
| **Measured reachable TODAY** (MT/NV/WY/CA only) | **15,048.5** | **15.32 %** |
| **Recall-adjusted expectation AFTER NWPP-11 lands ID/OR/UT/WA** | **30,431.8** | **30.98 %** |

Per state:

| State | CAMPD | Footprint MW | Fossil MW | Part-75 proxy MW | Proxy plants |
|---|---|---:|---:|---:|---:|
| WA | **no** | 31,711.8 | 4,792.7 | 4,738.2 | 15 |
| OR | **no** | 19,035.4 | 4,359.9 | 4,332.0 | 10 |
| NV | yes | 15,638.3 | 9,098.8 | 9,084.2 | 16 |
| UT | **no** | 9,769.3 | 6,058.4 | 5,905.8 | 15 |
| WY | yes | 8,654.1 | 4,435.0 | 4,427.0 | 7 |
| MT | yes | 6,939.6 | 2,349.8 | 2,342.2 | 7 |
| ID | **no** | 6,431.3 | 1,261.6 | 1,230.1 | 5 |
| CA | yes | 50.8 | 15.0 | 0.0 | 0 |
| CO | — | 7.5 | 0.0 | 0.0 | 0 |

**Energy coverage** — the figure that actually matters for the LP, and it is materially better
than the nameplate figure:

| Year | Footprint EIA-923 net generation | CAMPD today | Part-75 proxy bound |
|---|---:|---:|---:|
| 2023 | 297.66 TWh (848 plants) | 52.16 TWh = **17.5 %** | 129.75 TWh = **43.6 %** |
| 2024 | 307.35 TWh (879 plants) | 51.91 TWh = **16.9 %** | 128.42 TWh = **41.8 %** |
| 2025 | 235.48 TWh (**260 plants — preliminary vintage**) | 50.65 TWh = 21.5 % | 109.21 TWh = 46.4 % |

**So: ~31 % of nameplate, ~42–44 % of energy.** The charter's ~32 % nameplate estimate is
confirmed as an upper bound; its implicit worry — that the per-plant binning path covers "far
less of the fleet here than in ERCOT or SPP" — is correct on nameplate and **overstated on
energy**, because this footprint's fossil fleet runs at a higher capacity factor than its
hydro/VRE/nuclear nameplate implies. Two caveats on the denominator: the 2025 EIA-923 vintage is
**preliminary** (260 reporting plants against 848–879), so the 2025 row is not comparable and
NWPP-30/31/32 must verify it before use; and EIA-923's footprint total (297.66 TWh, 2023) exceeds
the EIA-930 metered net generation (277.59 TWh) because the two attribute plants differently —
against the EIA-930 denominator the same shares read **18.8 % / 18.0 % today** and
**46.7 % / 44.6 % at the bound** for 2023/2024.

**Recommendation for card N8**, unchanged in direction from the charter and now quantified:
fetch **ID, OR, UT, WA × 2023–2025 (+2026 partial) = 16 files**; skip **CO** (documented: one
7.5 MW hydro plant, zero CEMS-eligible units) and **CA** (documented: 50.8 MW, of which 15.0 MW
is combustion, and **zero** footprint facilities appear in the committed `CA_2024` extract — the
`CA_*` files are already on disk and are **inert for NWPP**, exactly as `WY_*` was inert for SPP).
`ISO_STATES["NWPP"]` = `("ID", "MT", "NV", "OR", "UT", "WA", "WY")`.

---

## 9. Zone recommendation (RECOMMEND — the desk serves card N5)

### 9.1 The constraint that binds before any preference

**There is no EIA-930 sub-BA product for any of the 17 balancing authorities.** Every load
observation this footprint has is at whole-BA granularity, so **a zone may not split a BA** — not
because it would be inelegant but because the demand series to disaggregate it does not exist.
**BPAT alone is 20.3–20.8 % of footprint load** and is therefore indivisible on this data;
`NWPP-NW` as scoped below is 37.4–37.9 %, i.e. **more than a third of the pool in one LP zone**.
That is the ceiling on topology fidelity, and it is a data fact, not a modelling choice.

### 9.2 Measured zone shares (`Demand (MW) (Adjusted)`)

| Zone | Member BAs | 2023 | 2024 | 2025 | 2024 TWh |
|---|---|---:|---:|---:|---:|
| **NWPP-NW** | BPAT · PSEI · SCL · TPWR · CHPD · DOPD · GCPD (+ AVRN gen) | 37.78 % | **37.41 %** | 37.88 % | 108.99 |
| **NWPP-EAST** | PACE | 17.85 % | **18.11 %** | 18.27 % | 52.76 |
| **NWPP-INLAND** | IPCO · AVA · NWMT · WAUW | 15.53 % | **15.29 %** | 15.17 % | 44.54 |
| **NWPP-OR** | PGE · PACW (+ GRID gen) | 15.29 % | **15.09 %** | 14.91 % | 43.98 |
| **NWPP-SNV** | NEVP | 13.55 % | **14.10 %** | 13.76 % | 41.08 |

The charter's 2024 figures are confirmed within 0.04 pp everywhere; the small differences are
because the charter measured on the **raw** column and these are **Adjusted** (§4.2). Per-BA 2024
shares: BPAT 20.27 · PACE 18.11 · NEVP 14.10 · PSEI 8.54 · PGE 7.79 · PACW 7.30 · IPCO 6.44 ·
AVA 4.44 · NWMT **4.13** (charter 4.18 — the one row that moves, NWMT having five 2024 artifact
hours) · SCL 3.24 · GCPD 2.29 · TPWR 1.56 · DOPD 0.82 · CHPD 0.68 · WAUW 0.27 · AVRN 0.00 ·
GRID 0.00.

### 9.3 What the data this lane can see supports

**Five groups are supportable and three would lose something real.** The evidence is hourly
demand correlation (2024, Adjusted) plus the §5 seasonal verdicts:

| | NWPP-EAST | NWPP-INLAND | NWPP-NW | NWPP-OR | NWPP-SNV |
|---|---:|---:|---:|---:|---:|
| NWPP-EAST | 1.000 | 0.879 | 0.488 | 0.662 | 0.775 |
| NWPP-INLAND | 0.879 | 1.000 | 0.708 | 0.826 | 0.650 |
| NWPP-NW | 0.488 | 0.708 | 1.000 | **0.916** | **0.048** |
| NWPP-OR | 0.662 | 0.826 | **0.916** | 1.000 | 0.329 |
| NWPP-SNV | 0.775 | 0.650 | **0.048** | 0.329 | 1.000 |

1. **NWPP-SNV must be its own zone.** Its correlation with NWPP-NW is **0.048** — the two are
   essentially independent load regions — and it is the only zone whose summer peak is ~2× its
   winter peak. Collapsing Nevada into anything would average two unrelated load shapes.
2. **NWPP-NW and NWPP-OR correlate at 0.916** and are the pair a three-zone cut would merge
   first. But they **diverge seasonally** (NW winter in all three years; OR summer, summer,
   winter — §5), so merging them buys a smaller LP at the cost of the one seasonal distinction
   the fleet's own dispatch turns on. This lane recommends keeping them separate and notes the
   merge is the least-bad three-zone cut if the desk wants one.
3. **NWPP-INLAND is the weakest group and the desk should hear why.** Its within-group mean
   correlation is **0.682** against a vs-rest mean of **0.631** — barely distinguished — because
   it mixes winter-peaking AVA (0.95 with BPAT) and NWMT with summer-peaking IPCO and WAUW. It is
   a residual grouping, not a coherent one.
4. **GCPD is the one BA whose placement the load data actively disputes.** Grant County PUD sits
   in NWPP-NW but correlates **0.90 with IPCO, 0.80 with NEVP and 0.72 with PACE**, against
   **0.16 with PSEI, 0.13 with SCL and 0.08 with TPWR** — the very BAs it is grouped with — and it
   is **summer**-peaking (1.06–1.10) in a winter-peaking zone. On load shape it belongs with
   INLAND. **This lane does NOT recommend moving it**, for a reason that should be stated
   plainly: **load correlation is not a transmission constraint.** GCPD is a mid-Columbia BA
   physically embedded in BPA's system, and a zone is an electrical object. The flag is raised so
   NWPP-12's path ratings are read with this question in hand, and the desk decides.

**RECOMMENDATION: five zones as the charter scopes them, with (3) and (4) declared as open and
routed to the path ratings.** The cut this lane would defend hardest is `NWPP-SNV`; the one it
would defend least is `NWPP-INLAND`.

### 9.4 What NWPP-12 must supply before card N5 can be ruled

Zones are transmission objects and this lane can measure load, not transfer capability. **The
dispositive evidence is the WECC published path ratings**, and specifically whether a rated path
corresponds to each of the four internal boundaries:

| Boundary | Candidate rated path | Expectation |
|---|---|---|
| NWPP-INLAND ↔ NWPP-NW | **Path 14** (Idaho–Northwest) | likely maps |
| NWPP-EAST ↔ NWPP-INLAND / NWPP-NW | **Path 20 ("Path C")**, **Path 35 (TOT 2C)** | likely maps |
| NWPP-EAST ↔ NWPP-SNV | **Path 27 (IPP DC)** and the Utah–Nevada paths | likely maps |
| **NWPP-NW ↔ NWPP-OR** | **none expected** | a dense multi-point interconnection, not a rated path — **a documented absence here is worth more than a plausible number** (Tier-3, non-binding, per `04-transmission-zones-and-congestion.md`) |

Also pending and material: **Path 8 (Montana–Northwest)** for the NWMT half of NWPP-INLAND, and
**Path 65/66 (PDCI / COI)** which are *external* — they are the CAISO seam card N4 owns, not an
internal boundary.

### 9.5 Two placement questions that are NOT zoning questions and must not be answered as if they were

- **AVRN and GRID hold generation and no load (§4.3).** Their injection must land in a zone
  without creating a demand row. AVRN's 19 plants are Columbia-Gorge wind and solar in Oregon and
  Washington (Klondike, Leaning Juniper, Montague, Big Horn, Lund Hill …); GRID's single EIA-860
  plant is Hermiston, Oregon. On geography both sit on the **NW/OR boundary**, which is exactly
  the boundary §9.4 expects to have no rated path — so their placement is nearly inconsequential
  *if* that link is non-binding, and consequential if it is not.
- **GRID's energy is unresolved before it can be placed at all** (§4.6b): EIA-930 says 17.7 TWh/yr
  and EIA-860 says a 689.4 MW plant. Assigning EIA-930's GRID generation to a zone would inject
  ~6 % of footprint energy whose physical location this audit cannot establish. **Routed to the
  desk as a precondition on card N5, not a detail of it.**
- **The hydraulic chain crosses every candidate boundary** (§2.6): eight of the ten largest hydro
  plants are on the Columbia/Snake mainstem across BPAT, CHPD, GCPD and DOPD, so NWPP-36's
  cascade coupling will couple units **inside** NWPP-NW under this grouping but would couple
  across a zone boundary under a finer one. A zoning change after W3b is therefore not free.

---

## 10. Manual manifest — items this lane could not source

Copy-paste block. Every row is something **this audit could not obtain from the committed tree**,
with the exact route. Nothing here is a value this lane guessed.

```
NWPP PHASE-0 MANUAL MANIFEST (lane NWPP-10, 2026-09-13, base sha 4d9c3251)
Fetch first; the manual fallback fires only on a documented 403/404 with the URL recorded.

--- OWNED BY NWPP-11 (fetch/derive) ---
[1] CAMPD hourly CEMS, 4 states x 4 years = 16 files  -> data/raw/campd-unit-level/<ST>_<yr>.parquet
    https://api.epa.gov/easey/bulk-files/emissions/hourly/state/emissions-hourly-<YYYY>-<st>.csv
      st in {id, or, ut, wa}; YYYY in {2023, 2024, 2025, 2026}
    SKIP co (one 7.5 MW HYDRO plant, zero CEMS-eligible units - nwpp-data-audit.md §2.3)
    SKIP ca (already on disk 2019-2026; zero NWPP-footprint facilities in CA_2024 - §8)
[2] Per-BA hourly extracts x 17         -> data/raw/eia-930-hourly/"<BA> hourly.parquet"
    NO FETCH. Derive from committed data/raw/eia-930/EIA930_BALANCE_<yr>_<half>.parquet.
    READ 2022_Jul_Dec THROUGH 2026_Jan_Jun, then filter on UTC year, or 2023 loses ~9 h (§4.1).
    Use Demand (MW) (Adjusted); Demand (MW) (Imputed) is a sparse patch column, not a series (§4.4).
    Union the pre-/post-2024-07 fuel column families, and handle the EIA spelling error
    "Solar witho Integrated Battery Storage (Adjusted)" (§4.5).
[3] EIA-930 per-counterparty DIBA interchange 2023-2025 -> data/raw/eia-930-interchange/
    https://www.eia.gov/electricity/gridmonitor/  (Grid Monitor interchange CSV, key-free route)
    EIA API v2 route needs EIA_API_KEY (UNSET in this container).
    REQUIRED because Total Interchange cannot be summed over the 17 BAs (§4.6a).
[4] BPA balancing-authority feed (cross-check on BPAT)
    https://transmission.bpa.gov/Business/Operations/Wind/baltwg.txt
[5] EIA-923 monthly hydro by plant, 288 plants        -> data/raw/nwpp-hydro/
    Source already committed at data/raw/_processed-legacy/eia923_monthly_generation.parquet.
    VERIFY 2025 coverage first: only 260 footprint plant-rows vs 848/879 for 2023/2024 (§8).

--- OWNED BY NWPP-12 (documents; every value needs URL + page/table) ---
[6] WECC published path ratings -> data/raw/nwpp-planning/
    https://www.wecc.org/  (path rating catalogue)
    Needed: Path 3, 4, 8, 14, 20 (Path C), 27 (IPP DC), 35 (TOT 2C), 65/66 (PDCI/COI).
    For EACH: which of the five candidate zone boundaries it does or does NOT correspond to.
    A DOCUMENTED ABSENCE for NWPP-NW <-> NWPP-OR is worth more than a plausible number (§9.4).
[7] WRAP program documents + THE BINDING-SEASON DATE
    https://www.westernpowerpool.org/
    Answer with a citation: when is WRAP's first BINDING season; which of the 17 BAs participate
    and from when; binding forward-showing and holdback requirements.
[8] Participant IRPs -> PRM BY SEASON, peak-load history, coal exit dates, internal transfer limits
    PacifiCorp, Portland General, Idaho Power, Avista, NorthWestern Energy, Puget Sound Energy,
    NV Energy. NOTE §5: the footprint has no single peak season, so a seasonal PRM is required.
    NOTE §6: state the CLOCK of every transcribed IPCO value (Idaho Power files Pacific).
[9] VOLL - a SOURCING problem, not a lookup (nwpp-data-audit.md §7.1)
    (a) a loss-of-load / unserved-energy cost stated in a participant IRP; else
    (b) LBNL Interruption Cost Estimate Calculator, https://icecalculator.com  (LBNL / US DOE),
        on the footprint's own customer mix; else
    (c) a WECC or WRAP published planning VOLL.
    DO NOT use FERC Order 831's $2,000 - Order 831 applies to RTO/ISO markets and NWPP is neither.
[10] NRC licence expiry + SLR status, Columbia Generating Station (EIA plant 371, NRC docket 50-397)
    https://www.nrc.gov/info-finder/reactors/colu.html   -> data/raw/nuclear-license-status/nwpp.csv
    (The monthly CF itself is ALREADY MEASURED - §7 row 10 - and is not pending.)
[11] LTLF with an EDITION and a VINTAGE (>= 2020)  -> data/raw/load-forecast/nwpp/nwpp.csv
    W2 PRECONDITION (gate G12). Footprint-wide, or assembled from [8] with the assembly documented.
[12] Gas basis series per zone -> data/raw/gas-prices/ + SOURCES_nwpp_*.md
    Zone -> hub attribution is MEASURED in §7.2; the PRICE SERIES are not:
      NWPP-SNV -> Kern River; NWPP-NW -> Northwest Pipeline (Sumas);
      NWPP-OR -> GTN (Stanfield); NWPP-INLAND -> split NWP/GTN; NWPP-EAST -> Rockies (Opal).
    ALSO: read EIA-860 "Pipeline Notes" for the 1,174.1 MW of PACE gas filed as "Other" (§7.2).
[13] Coal price basis -> data/raw/coal-prices/
    MUST cover COLSTRIP (1,647.4 MW, ~9-11 TWh/yr) - it has ZERO EIA-923 delivered-fuel rows,
    as do Centralia, TS Power and Hardin (2,911.7 MW = 32.7% of coal) (§7.3).
    Basin labels (PRB / Uinta / Colstrip mine-mouth) per plant.
[14] Confirmed retirements - enforceable public instruments with dates
    Colstrip, Centralia, Jim Bridger, North Valmy, Naughton. An IRP intention is NOT an instrument.
    See §2.7 for the full EIA-860 planned-retirement table (coal 229.5 MW dated 2027; and
    gas ST 230.0 MW dated 2028, gas CC 222.0 MW dated 2032, 593.3 MW dated 2043).
[15] State RPS/CES numeric schedules (§7.4) - transcribe against the statute, cross-check DSIRE
    WA RCW 19.405 (CETA) | OR ORS 469A.400-.475 (HB 2021) | NV NRS 704.7801-.7828
    UT UCA 54-17-601..603 (non-binding goal) | MT MCA 69-3-2001..2010 | ID none | WY none
    https://programs.dsireusa.org/system/program?state=<WA|OR|NV|UT|MT|ID|WY>

--- OWNED BY NWPP-13 (card N2 only; NOT this lane's) ---
[16] WEIM 15-min LMPs, footprint EIMT/CASP nodes -> data/raw/nwpp-weim/
[17] Mid-C traded index (ICE workbooks) -> data/raw/nwpp-planning/
```

---

## 11. Reproduction

Every number above was produced by reading committed artifacts only. `data/` was never written.

```bash
# Fleet census, sectors, hydro/coal/nuclear detail, planned retirements, the adjudications
python3 - <<'PY'
import pandas as pd
BAS="BPAT PACE PACW PGE PSEI AVA IPCO NWMT CHPD DOPD GCPD SCL TPWR AVRN GRID WAUW NEVP".split()
p=pd.read_parquet('data/raw/eia-860/eia860_plant.parquet')
g=pd.read_parquet('data/raw/eia-860/eia860_generator_operable.parquet')
pf=p[p['Balancing Authority Code'].isin(BAS)]
m=g.merge(pf[['Plant Code','State','NERC Region','Balancing Authority Code','Plant Name','Sector Name']],
          on='Plant Code',how='inner',suffixes=('_g','_p'))
print(len(pf), m['Plant Code'].nunique(), len(m), round(m['Nameplate Capacity (MW)'].sum(),1))
print(m.groupby('Technology')['Nameplate Capacity (MW)'].sum().sort_values(ascending=False).round(1))
print(pf[pf['NERC Region']!='WECC'][['Plant Code','Plant Name','State','NERC Region','Balancing Authority Code']])
PY

# Load spine: build the UTC-complete 2023-2025 slice (READ 2022-2026, filter on UTC year)
# then energy / peaks / defect screen / seasonal peak / timezone / interchange identity.
# Full scripts: census.py, load.py, spine.py, defect.py, defect2.py, gen3.py, zones.py, tz.py,
# seam.py, ident.py, cems.py, cems2.py, reg.py  (run from the repo root, pandas + pyarrow only).
```

Key reproduction constants, stated so a later lane gets the same numbers:

- Footprint BA list: the 17 codes above; **plus `NERC Region == "WECC"`** for the post-adjudication
  fleet (939 plants / 1,930 generators / 98,238.1 MW).
- Load window: `EIA930_BALANCE_2022_Jul_Dec` … `2026_Jan_Jun`, de-duplicated on
  `(Balancing Authority, UTC Time at End of Hour)`, filtered to UTC years 2023–2025 →
  **447,168 rows**.
- Demand column: `Demand (MW) (Adjusted)`. Net generation: `Net Generation (MW) (Adjusted)`.
  Interchange: `Total Interchange (MW) (Adjusted)`.
- Defect screen: `|D| > 2.5 × annual median` **or** `D < 0`, per BA per year, on raw `Demand (MW)`
  (`data/eia930/demand.py:407`, `_DEMAND_SPIKE_THRESHOLD`). Fuel screen:
  `> 2.5 × median` **and** `> 2.5 × p99.9` (`data/eia930/actuals.py`, `_FUEL_SPIKE_*`).
- Seasons: winter = Nov–Mar, summer = Jun–Sep, on UTC-stamped hours.
- CEMS proxy: fossil-combustion technology at a plant with > 25 MW of fossil nameplate; validated
  against MT/NV/WY/CA 2024 at 100 % precision / 94.9 % MW recall.
