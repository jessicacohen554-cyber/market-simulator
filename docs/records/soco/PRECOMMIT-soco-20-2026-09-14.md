# PRECOMMIT — SOCO-20: the pin flip (SOCO registered as the eighth region)

**Lane** SOCO-20 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-14 ·
**Branch** `claude/soco-20-register-fvj01g` · **Base** `origin/main` `d083b0b1` (the charter pinned
`39a1c9a1`, an ancestor 30 commits back; every SOCO precondition landed between the two, so the lane
builds on the tip) · **Data profile** `shared` (this lane creates `soco`) · **Charter**
`docs/multi-iso/soco-addition-plan-2026-09.md` §2.3 (the checklist), §3 (the ruled cards), §7 gates
G1–G3, G5–G12, G19, G22; `docs/multi-iso/soco-data-audit.md` §5 (the registry-values table);
`FINDING-spp-20-2026-09-06.md` + `iso_configs._spp_config` (the worked template).

Written and pushed BEFORE any registry is edited. Every value below is fixed here with its source, so
the implementation cannot be shaped to a result. **Zero LP** — this lane runs no solve (rule 32).

## 0. Preconditions — each verified on `origin/main` `d083b0b1`

| precondition | evidence |
|---|---|
| S1, S3–S8, S9, S11, S12 ruled | plan §3 rows (verbatim quotes in §1 below); ledger §2 O-1…S12 |
| SOCO-10, SOCO-11 merged | PR #6091 (`docs/multi-iso/soco-data-audit.md`), PR #6083 (`campd-unit-level/{AL,GA}_*`, `zone-specific-demand/SOCO/`, `SOCO interchange hourly.parquet`) |
| manifest row 7 / gate G12 | `data/raw/load-forecast/soco/soco.csv`: 60 rows, edition `Budget 2025 (B2025) / 2025 IRP`, vintage 2025, metrics `winter_peak_mw` / `summer_peak_mw` / `energy_gwh`, area Georgia Power Company (SOCO-12 §0.1) |
| SOCO-15 COD seam on main | `9398000d` (PR #6127), FINDING-soco-15 §2: keys byte-identical for all seven |
| SOCO-22 rubric v3.8 on main | `1b6ce1fd`; `scripts/calibration_verdict.py::PHYSICALLY_CALIBRATED` present |
| SOCO-13 STOP gate | **NO** (FINDING-soco-13 §0): no `actual_lmp_hourly_SOCO.parquet`, no `actual_lmp.json` block → gate G6 / card S9: `TAIL_THRESHOLD["SOCO"]` is SKIPPED in all three files, documented in place |
| SOCO-21 shard | `docs/codebase-site/data/mechanism-matrix/SOCO.js` on main; `mech_matrix.ISO_ORDER` / `ISO_EV_KEY["SOCO"]="O"` already landed — **not this lane's** |
| G22 | discharged for the FIVE-respondent set only (FINDING-soco-14 §0: 107 YES, 210 YES, 186 NO); desk r#5 re-ruled S3 on five respondents — quoted from this lane's charter, since the committed ledger stops at r#4 |

## 1. The rulings this lane implements (verbatim)

- **S1** — *"SOCO (Recommended) — The EIA-930/EIA-860 balancing-authority code. Already the on-disk filename convention (`SOCO hourly.parquet`, `SOCO_fueltype.parquet`), so no crosswalk is invented. Lets every doc say 'balancing authority' rather than 'ISO'."* → key `SOCO`; `ISO_EV_KEY["SOCO"]="O"` (landed by SOCO-21).
- **S3** (r#3) — *"3 zones now on the six-respondent sum"*; conditions (i) G22, (ii) zones named geographically, (iii) never sold as improving accuracy. **RE-RULED r#5 (charter text): the load side rests on FIVE FERC-714 respondents — Alabama Power (2), Georgia Power (183), Mississippi Power (184), Oglethorpe (107), MEAG (210). Southern Power (186) is EXCLUDED; residual 3.03 / 2.92 / 1.26 %; 186's 1.3–1.4 % is named on the first keeper's determination basis. The share DERIVE is SOCO-32's.**
- **S4** — *"Served measured EIA-930 interchange for the first keeper (Recommended)"*; priced `NeighborInterface`s default-off for SOCO-56, SOCO-12's published transfer capability as their input.
- **S5** — *"DOE/LBNL ICE calculator, SERC/Southeast mix (Recommended)"*; $2,000 only as a documented fallback; Brattle as method, never value.
- **S6** — *"Register winter 26.0% as the scalar, misalignment documented (Recommended)"*.
- **S7** — *"Map to a gas CT at the 25 MW rating (Recommended)"*.
- **S8** — answered and superseded by **S12** (*"Charter a cross-ISO repair lane BEFORE SOCO-20"*, executed by SOCO-15).
- **S9** — deferred behind SOCO-13; SOCO-13 read NO → the three `TAIL_THRESHOLD` copies are skipped.
- **S11** — *"This desk charters it as SOCO-22 [FABLE]"* (landed, v3.8).

## 2. Topology — `_soco_config`

| object | value | source |
|---|---|---|
| zones | `SOCO_AL` / `SOCO_GA` / `SOCO_MS` (geographic, never an OpCo name; card S3 (ii)) | FIPS 1 → AL, 13 → GA, 28 → MS, **12 (FL) → SOCO_AL** (the SERC panhandle interconnects west, audit §6.4); **no key for 25 (MA)** — plant 67241 is an EIA-860 BA-field mis-entry REJECTED under the audit §2.6(a) two-key rule, and the splitter FAILS LOUD on it |
| static `load_share` fallback | `SOCO_GA 0.5842 / SOCO_AL 0.3510 / SOCO_MS 0.0648` | the audit §5 row 4 **fleet-MW share, the fallback of last resort and NOT a load share**: EIA-860 nameplate 41,284.4 / (24,494.0 + 309.6) / 4,577.7 of 70,665.7 MW. Registered as the static fallback ONLY because (a) the FERC-714 load derive and the respondent→zone construction are SOCO-32's by ruling, and (b) with Tier-3 non-binding TTCs the fallback cannot move the dispatch (copperplate until a link binds) |
| links | `SOCO_AL↔SOCO_GA` **24,400 MW**; `SOCO_AL↔SOCO_MS` **4,300 MW**; no GA↔MS link (Mississippi Power connects through Alabama, audit §6.4) | **Tier-3 PLACEHOLDERS THAT CANNOT BIND** (the SPP-20 48,700 MW precedent): each is the smaller-side EIA-860 2025 ER **winter** capability rounded to 100 (AL+FL 24,446.3; MS 4,324.6) — an upper bound on flow in either direction (the sending side cannot inject more than its own capability; the receiving side cannot absorb more than its own load, which is smaller). Winter because SOCO is winter-peaking (S6). Misalignment stated on the link exactly as `_spp_config` states SPP's: no public inter-OpCo limit exists **structurally** — the OpCos are one pooled dispatch under the IIC (SOCO-12 README §4b) — and the real value is lever SOCO-54 |
| `voll` | **61,900 $/MWh** | §3 below |
| `default_scenario_overrides` | `{}` | no reserve co-opt, no scarcity seed (SOCO clears no AS market — S5; SOCO-21 class (c)) |

## 3. VOLL — card S5, the construction fixed before the number is written

**Source (the ruling's):** LBNL / DOE *ICE Calculator 2: Final Report for Phase 1 and 2 of the National
Initiative to Update the Interruption Cost Estimate (ICE) Calculator* — Larsen, Carney, Eto et al.,
2026-02-27, OSTI 3021993 (`https://www.osti.gov/servlets/purl/3021993`, escholarship
`3s61v105`), **ES Table 3 / Table 3.5 / Table 4.6 (2025$)**, "Cost per Unserved kWh":

| duration | residential | non-residential |
|---|---:|---:|
| momentary | $20.59 | $358 |
| **2 hours** | **$5.03** | **$100** |
| 8 hours | $3.07 | $52 |
| 24 hours | $2.18 | $31 |

**Class mix (the "SERC/Southeast" leg):** EIA-861 2024 `Sales_Ult_Cust_2024.xlsx`, every utility row
with `BA Code == SOCO` (85 rows; GA 54 / AL 21 / FL 7 / MS 3): residential 89.686 TWh, commercial
74.213, industrial 59.650, transportation 0.152 → **residential 0.4009 / non-residential 0.5991**.

**Duration rule, declared here and not swept:** the **2-hour** column. An LP slack increment is a
one-hour firm curtailment; the 2-hour event is the shortest *sustained* interruption ICE tabulates and
its nearest published analogue. The momentary column prices a sub-minute event's fixed cost per kWh
(not an energy price); the 8- and 24-hour columns amortise over multi-hour events the LP never treats
as one event. The other columns are reported beside the value as the honest width, never selected on:
8 h → $32,384/MWh, 24 h → $19,447/MWh.

**VOLL = 0.4009 × 5,030 + 0.5991 × 100,000 = 2,016.5 + 59,910 = $61,927 → 61,900 $/MWh** (nearest
100). **Misalignment stated on the field:** ICE 2's CDFs are national pooled models (participating
utilities include Duke Energy Carolinas / Florida, none of Southern's OpCos); the report itself defers
regional variation to Phase 3. The Southeast leg here is the customer-class MIX, not a regional
CDF. $2,000 is NOT carried: it is FERC Order 831's OFFER cap and SOCO takes no offers.

## 4. Registry values (every one from the audit §5 table, SOCO-11/12 FINDINGs, or measured here)

| registry | SOCO value | source |
|---|---|---|
| `PLANNING_RESERVE_MARGIN_BY_ISO` | 0.26 | S6; 2024 Reserve Margin Study, Exec. Summary RECOMMENDATIONS: winter TRM 26.00 %, summer 20.00 % (short-term −0.5). Seasonal structure stated on the field; winter-peaking 2024-01-17 47,368 MW / 2025-01-22 46,490 MW vs 2023-08-25 45,558 MW |
| `ADEQUACY_EXTERNAL_TIE_FIRM_MW` | 0.0 | the 2024 RMS sets the TRM WITH market assistance modelled (Tables I.1/I.2 Avg TC + CBM), so counting ties again double-counts; explicit, cited, same posture as SPP |
| `QUEUE_CAP_GW` | 3.5 | demonstrated peak all-tech COD 2023 = 3.348 GW (EIA-860, BA SOCO: gas_cc 1.507 + nuclear 1.114 + solar 0.690 + …), 2015–2025 series 0.192…3.348 |
| `QUEUE_CAP_PER_TECH_GW` | wind 0.0 · solar 1.0 · gas_cc 1.5 · gas_ct 0.5 · nuclear 1.5 · geothermal 0.0 · offshore_wind 0.0 | smallest 0.5 GW step ≥ demonstrated peak annual COD (EIA-860 2025 ER, BA SOCO, `Operating Year`): solar 0.870 (2021), gas_cc 1.507 (2023: Barry A3 774.0 + Lowman Energy Center 732.7), gas_ct 0.050 (2019, Kimberly-Clark Mobile CHP; the 2021-25 window records 0.005), nuclear 1.114 (2023 and 2024, Vogtle 3 then 4); **wind has ZERO COD in any year and zero fleet** (audit R-12), so its cap is the honest 0.0 |
| `STORAGE_BASE_FLEET_MW` | low 110 / mid 150 / high 920 | EIA-860 2025 ER energy-storage schedule, BA SOCO, **EXCLUDING the McIntosh CAES row** (card S7: it is a gas CT): OP batteries 148.7 → 150; + proposed U/V 775.0 → 923.7 → 920; ×0.75 = 111.5 → 110 |
| `STORAGE_DEPLOYMENT_CEILING_MW` | 23,700 | ~50 % of the 47,368 MW measured peak (2024-01-17) |
| `STORAGE_ANNUAL_BUILD_CAP_MW` | 500 | smallest 0.5 GW step ≥ demonstrated peak annual battery COD 0.065 GW (2024) |
| `STATE_RPS_FLOORS` | all 0.0 | DSIRE AL/GA/MS: no RPS (audit §5 row 10) |
| `DEMAND_GROWTH_RATES` | near 0.100707 / long 0.012559, low=mid=high | `soco.csv` `energy_gwh` (Georgia Power B2025): 2026 102,557.4 → 2031 165,701.5 → 2044 194,890.0 GWh; CAGR 2026→2031, 2031→2044 (the SPP era rule). Rule-14 misalignment stated: **Georgia Power only** (System column redacted; Alabama files no IRP) |
| `DATACENTER_ADDITIONS_MW` | `{}` | B2025's large-load block is chart-borne, not transcribed (SOCO-12 §7 item 4) |
| `ELECTRIFICATION_LAYERS` | `{"heat_pump": {}, "ev": {}}` | no published component |
| `RENEWABLE_AVG_CF` | wind 0.0 · solar 0.23 | solar: EIA-930 2024 `NG: SUN` 10.141 TWh / (mean YE-2023 4,689.9 & YE-2024 5,484.9 MW OP solar = 5,087.4 × 8,784 h) = 0.2269; wind: empty class |
| `RENEWABLE_INSTALLED_MW` | wind 0.0 · solar 5,820 | EIA-860 2025 ER solar schedule OP, BA SOCO, MA row excluded: 5,824.4 → 5,820 (nearest 10) |
| `RENEWABLE_ZONE_ALLOCATION` | wind SOCO_GA · solar SOCO_GA | GA 5,000.7 of 5,824.4 MW OP solar |
| `NUCLEAR_MONTHLY_CF` / `_BY_YEAR` | derived by the frozen script at registration | `derive_nuclear_monthly_cf.py --isos SOCO --years 2023 2024 2025`, **with the denominator made COD-aware** (§5) |
| `WEATHER_YEAR_POOL_BY_ISO` | (2023, 2024, 2025) if the end-to-end check passes | `load_demand` + `load_renewable_profiles` for each year; 2025's 7 trailing hours (audit §3.2) named on the row |
| `VOLUNTARY_BASELINE_ISO_WEIGHT` | None | same EIA-861 needs-intake as the seven |
| `GAS_BASIS_DIFFERENTIAL` | +0.64 | EIA-923 delivered gas to SOCO plants 2024 $2.832 − HH $2.192 (2023 +0.49, 2025 +0.65; 26/27/27 plants) |
| `COAL_PRICE_BASE` | 3.2 | EIA-923 SOCO plant-weighted delivered coal 2024 $3.168 (2023 3.548, 2025 2.928; 6/6/5 plants) |
| `COAL_SIGMOID_BACKCAST_GAS_MIN_MMBTU` | 2.83 | cheapest delivered-gas year 2024 = HH 2.192 + 0.64 |
| `TRANSMISSION_BASE_STATIC_VINTAGE` | 2025 | the link placeholders are built from the EIA-860 2025 ER |
| `campd.ISO_STATES` | ("AL","GA","MS","FL") | audit §2.3 |
| `_ISO_TO_BA_CODE` / `BA_CODE_TO_ISO` / `_ISO_TO_HOURLY_BA` | "SOCO" | the BA code IS the key |
| `_LARGEST_ZONE` | SOCO_GA | 58.4 % of fleet MW |
| `_SCALAR_INTERCHANGE_ISOS` | `soco_net_interchange` (EIA-930 `Total interchange`, +ve = export; net +10.156 / +10.807 / +13.032 TWh on the model clock) | S4; SOCO-11 §4 |
| `INTERFACE_NEIGHBORS["SOCO"]` | 8 default-off blocks, one per SOCO-11 DIBA except SEPA: TVA, MISO, DUK, SCEG, SC, FPL, FPC, TAL; `interface_limit_mw` = the 2024 RMS winter Avg TC (S4's named input) with the measured envelope recorded as the rule-14 misalignment for SOCO-56; anchors Tier-3 (MISO: the MISO-South zonal RT mean over HH+basis, the same construction SPP-51 used; no-LMP neighbours: the 11.6 flat PJM's registry carries for the same TVA/Carolinas); names prefixed `SOCO_` so no `_HR_GAS_ELASTIC` key can ever be shared (gate G10) | S4; SOCO-12 README §4c; SOCO-11 §4.3 |
| `INTERCHANGE_INJECTIONS["SOCO"]` | `(apply_reference_price_seam_injections,)` | self-gates on `reference_price_interface` (off) — byte-identical no-op |
| `MARKET_DESIGN` / `_CURVE_ISOS` / `_CAPACITY_ISOS` / `CAMPD_BINNING_ISOS` / `CAP_AND_TRADE_PROGRAMS` / `IMPORT_*` / `TAIL_THRESHOLD` / `_HR_GAS_ELASTIC` / `EIA930_PS_FOLDED_INTO_WAT` | **ABSENT, documented in place** | S6 (no capacity market); SOCO-30 (tranche artifact); no carbon program; G7 (no import node); G6/S9 (no price); G10; audit §3.3 (PS was never folded into WAT) |
| offer-curve bands | **identity (1.0) on EVERY class** via `_SOCO_OFFER_CURVE` | gate G5 / rule 25: SOCO takes no market offers |
| `_MULTI_YEAR_ISOS`, memory class `per_plant=True, co_opt=False, peak_gb=6.0 (ESTIMATE, measured in SOCO-40)`, `calibration-solve.yml`, data profile `soco` | as the plan's defaults | rule 16; SOCO-21 class (c); G11; G3 |

## 5. Two seams this lane repairs on the way, each inert for the seven

1. **The nuclear monthly-CF denominator.** `_nuclear_monthly` sets a nuclear unit's availability to the
   fleet-month CF and the SOCO-15 COD mask then multiplies it. The frozen derive divides EIA-923 net
   generation by the WHOLE fleet's pmax, so a month in which Vogtle 3/4 (2,228 MW) are not yet online
   would hand the six online units a CF scaled by 6,054 / 8,282 — a −27 % bias on H1-2023 nuclear
   (~−7 TWh on a 52.4 TWh year), the mirror image of the phantom SOCO-15 removed. The derive's
   denominator becomes the month's ONLINE pmax (each unit's own EIA-860 operating year/month, the same
   grain SOCO-15 serves the LP). No nuclear unit of the seven changes COD inside its window, so
   `--check` must reproduce every committed table byte-for-byte; a mismatch STOPS the lane.
2. **The storage loader and the McIntosh CAES row.** The energy-storage schedule carries plant 7063's
   CAES at 110 MW; the generator schedule carries the same unit (prime mover `CE`, 110 MW nameplate,
   **25 MW summer/winter**), which `_map_fuel_type` already routes to `gas_ct` and the loader already
   caps at the 25 MW summer rating. Card S7 therefore needs the storage loader to SKIP compressed-air
   rows (one physical unit, one representation — rule 19), and it is the only such row on the national
   schedule, so every other ISO is byte-identical.

## 6. The G8 proof, pre-registered

`scripts/solve_surface_register.py --diff origin/main HEAD` must show **0 moved / 0 added / 0 removed**
for ERCOT / CAISO / MISO / PJM / NYISO / NEISO / SPP; SOCO's rows in the by-ISO tables are NEW rows
(undeclared, the SPP-20 R-1 state — a new ISO row inside a declared table cannot be declared through
`--declare`). Baseline keys at `d083b0b1`, re-derived from each keeper's `run_config.json` before any
edit: caiso `bab5e9b08681e54c` · ercot `0f89d4c5f45043f7` · miso `b35a8f20b73a5fbf` · neiso
`28266b333667e16f` · nyiso `93be4aeb93d78283` (keeper `2026-09-13-nyiso-232-st-gas`, promoted after
SOCO-15's `7e0dc0344f297fc2` was measured on nyiso-231) · pjm `b05e09c319c2c5f5` · spp
`6d6205e381e982c2`. All seven must be byte-identical after the flip. No `ScenarioConfig` field, no
default flip, no `results/cache.py` edit. Pre-existing on main and NOT this lane's: `moved_rows` already
names `NUCLEAR_MONTHLY_CF_BY_YEAR` for ERCOT and `NUCLEAR_MONTHLY_CF_BY_YEAR` + `STATE_CARBON_PRICE_BY_ISO`
for CAISO at the base.

## 7. Files this lane will NOT touch

`frontend/data/forecast/**`; any keeper shard, log or matrix shard; `docs/codebase-site/data/mechanism-matrix/**`;
`scripts/calibration_verdict.py` beyond `PINNED_CLASSES_BY_ISO["SOCO"]` and the documented `TAIL_THRESHOLD` skip;
the plan; the ledger; `docs/calibration-log/soco.md`; `results/cache.py`; `ScenarioConfig`.
