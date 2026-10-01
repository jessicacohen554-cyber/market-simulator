# PRECOMMIT — R-ERCOT-14: Oklaunion membership (A) and the pre-2022 SWCAP vintage (B)

Keeper at open: `2026-09-28-r-13-2019-reserve` (`results/calibration/r_ercot13_span`, 2019–2025), ISO NOT-YET.
Written before any solve. Nothing here is selected against a residual. Offer multipliers are untouched (rule 1(c)).

## 1. Phase 0 (zero LP)

### 1a. Oklaunion (ORIS 127) is an ERCOT resource missing from the model

| Evidence | Value |
|---|---|
| ERCOT 60-Day DAM Gen Resource data | `OKLA_OKLA_G1_J01..J05` (jointly-owned shares, type CLLIG) in every file 2019-01 → operating day **2020-09-30** |
| EIA-930 ERCO coal, 2019 hourly OLS on CAMPD gross | Oklaunion coefficient **0.973** (ERCOT-10 plants 0.960); residual-without-127 vs 127 correlation 0.725. 2020: 0.715 / 0.600 (930 gaps, n = 6,576) |
| EIA-860 | NERC region **TRE**, BA code **SWPP**, 720 MW nameplate / 650 MW summer, SUB, min load 215 MW, op. year 1986, retired 9/2020 |
| Model today | absent from the 2019 and 2020 LP fleets (the curated bin sheet never carried it; the EIA-860 path filters BA=ERCO) |
| CAMPD net (gross × 0.91) | 2.57 TWh (2019), 1.10 TWh (2020, May 18 – Sep 26 only; Jan–Apr 2020 seasonal layup) |

The model's demand is EIA-930 demand + interchange = net generation, so Oklaunion's output is already in the load the model serves. The fleet is short a plant that the load includes. Rule 14: a membership boundary mismatch, not a fit.

### 1b. The rest of the coal shortfall is conduct, and is routed

- Per-plant, model vs CAMPD net: Martin Lake −2.72 / −5.93 TWh (2019/2020), Sam Seymour −3.50 / −3.57, Sandy Creek −1.77 / −1.24, Parish −0.22 / −1.83.
- **Not availability:** Martin Lake has 17.8 / 18.3 TWh-cap available. The model parks it at 5–30 % CF for 4,608 / 5,936 hours; the real plant is below 30 % for only 652 / 1,120 hours.
- **Not subclass:** Martin Lake burns 66–76 % SUB (EIA-923), so COAL_PRB is correct. Sam Seymour burns refined coal (RC).
- The coal conduct machinery is all K and fenced: `coal_min_load_floor`, `coal_mustrun_per_plant`, the passthrough sigmoids, `coal_offer_net_revenue_margin`, and `coal_offer_level_rebasis` R.
- The residual is cheap-gas-year stay-on conduct, which only an offer-side object or the declined 2019–22 SCED corpus could identify. **Routed** (§6).

### 1c. The SWCAP is half-vintaged before 2022 (R1)

- ercot-253 vintaged `ordc_voll` to the published HCAP ($9,000 through 2021). It left `voll` at the post-2022 $5,000.
- ERCOT's energy-only design sets offer cap = ORDC VOLL = value of shed. With `voll` stale, in 2019–2021:
  - (a) the LP sheds firm load at $5,000 while the rigid RRS/Reg-Up step it could release costs $9,000. That is the reverse of the EEA order (RRS released in EEA2, shed in EEA3).
  - (b) `ercot_offer_swcap_clip` caps thermal offers at $4,999.99 in years whose real cap was $9,000.
- Zero-LP offer delta (2019 fleet, voll 5k vs 9k): `mc_base` is unchanged; the move is at the P1 clip. The x433.95 CT_PEAKER and x151 CC_REGULAR peak bands, now clipped at $5k, could bid up to $8,999.99.
- Keeper shed: 2019 17.1 MWh in 1 zone-hour; 2021 4,390.9 MWh in 6 zone-hours; 2020 0.

## 2. The code (one commit, pinned below)

**A — Oklaunion membership. Ungated, zero DOF (the Frontera precedent).**
- `data/raw/reference/custom-bin-assignments.csv`: `COAL_PRB,North,5,N_COAL5,127,Oklaunion,720.0,11.9,…`. The shares are the PRB sheet defaults (25/20/50/5, 36/16 h); zone North (the DC-North tie's zone, Wilbarger County).
- `constants.ISO_PLANT_EXITS = {"ERCOT": {127: "2020-10-01 06:00"}}` (last ERCOT DAM operating day 2020-09-30 → HE01 CDT). Read by `ba_membership.plant_exit_first_outside_row`, which feeds the fleet hour mask. The mask is needed because the 2020 EIA-860 vintage has already dropped 127 from the operable sheet the COD ramp reads, which would leave it online all 12 months.
  - Declared in `solve_surface_declared.py` at the pre-arm hash, so ERCOT re-keys (237 → 238 rows). Pin advanced with a cause block.
- The artifacts gain the plant, each from its own source:
  - `coal_min_config_ERCOT.csv` +1 row: 215/650 MW. The deriver now falls back to the newest native vintage that still lists a retired plant; the other 10 rows are byte-identical.
  - `campd-unit-outages-hourgrain.csv` +4 rows: 2019-04-05..04-27, 2019-10-23..12-31, **2020-01-01..05-19 layup**, 2020-09-26..12-31. The re-derive reproduces every other row value-for-value; only the 127 rows were inserted (the R-ERCOT-8 Fusco precedent). The short and short-gas hour-grain files gain no 127 window.
  - `ercot-dam-plant-crosswalk.csv` +5 rows: `OKLA_OKLA_G1_J01..J05` → 127, accepted. The ratings are the site p98 ratings (355/102/51/66/76 MW, summing to 650 = EIA-860 summer).
    - **Why it is required, measured:** without it, 127 is the one unmapped COAL_PRB plant. The keeper's DAM plant-grain overlay (`ercot_thermal_dam_availability_plant`) then water-fills the class-hour remainder onto it, and 127 absorbs every other plant's rating mismatch: 1.12 TWh-cap in 2019, with June–August near zero, against 2.57 TWh actually generated.
    - With the crosswalk, 127 is pinned to its own measured series: 4.62 TWh-cap in 2019 (April outage, off Nov–Dec) and 2.23 in 2020 (Jan–Apr layup, gone after September).
    - Every non-127 fleet row stays byte-identical to the keeper recipe's fleet (zero-LP rebuild, 2019 and 2020).
  - `COAL_PLANT_SUPPLY[127] = "prb"`.
  - `COAL_PLANT_COMMISSION_YEAR[127] = 1986`.
- Stated fallbacks:
  - **Heat rate:** year-matched eGRID 11.90 / 11.70. The measured CAMPD deriver builds its population from the BA-filtered fleet, so it excludes 127. eGRID sits above measured for the other plants, so this biases Oklaunion's dispatch down, not up.
  - **Must-run:** the sheet's 25 %. `COAL_MUSTRUN_BY_PLANT` is derived from 2023–2025 CAMPD, after the retirement.
- Benchmark: the CAMPD backfill books 127 as COAL_PRB once the bin sheet carries it (EIA-923 has no ERCO row). So the benchmark gains Oklaunion's actual output too, on the same boundary as 930.

**B — `ScenarioConfig.ercot_swcap_vintage` (default off, ERCOT-gated, zero DOF).**
- `__post_init__` sets `voll = ordc_voll` for ERCOT.
- `pipeline.spec.shed_penalty_voll` makes the LP slack cost read it (runner and run_calibration).
- The clip and the 0.95 × VOLL surface caps follow automatically.
- Byte-identical off, and byte-identical armed wherever the published cap is $5,000 (2022+).
- Matrix row plus a cell in every shard (rule 28(c)).

**G-DRIFT** (`git diff 2af9ab74 origin/main` and `dac2fa2c origin/main` over the rule-29(b) paths): every hunk is INERT for an ERCOT 2019–2021 backcast. The changes are other-ISO gates, default-off flags absent from the recipe, the SOCO scoring block, and value-identical refactors. The committed keeper bundle is the control (form 4).

## 3. Shards (rule 36: one year, one container)

All shards run at the pinned SHA and replay `results/calibration/r_ercot13_span`.

| shard | years | extra `--set` | role |
|---|---|---|---|
| A-2019, A-2020 | 2019, 2020 | none (A is ungated at this SHA) | **candidate A** |
| B-2019, B-2020, B-2021 | 2019, 2020, 2021 | `ercot_swcap_vintage=true` | **candidate B** (= A + SWCAP) |

2021–2025 under A: 127 is masked all year, so its columns are fixed at zero and presolve removes them. The keeper's committed 2021–2025 legs compose unchanged.

## 4. Predictions (vs keeper; registered before any solve)

**A:**
- **PA1:** model coal +1.5 to +2.5 TWh in 2019 and +0.6 to +1.1 TWh in 2020. CC_REGULAR falls by a similar amount.
- **PA2:** C1 CC_REGULAR improves (2019 +9.63 → +7.5 to +8.5; 2020 +9.56 → +8.6 to +9.2). C1 COAL_PRB does NOT close, because the benchmark gains 127's actual output too: 2019 −8.15 → −8.1 to −9.0; 2020 −12.73 → −12.5 to −13.0.
- **PA3:** price falls slightly. C3a 2019 +41.4 % → +35 to +41 %; 2020 +11.3 % → +8 to +11 %. C3b moves < 0.05.
- **PA4:** no train-year determination moves (2023–2025 are untouched).

**B** (vs A):
- **PB1:** 2019–2021 hours ≥ $1k rise and C3a rises. 2019 C3a: +5 to +30 pts above A. 2021 (Uri) C3a rises and may flip 2021 CALIBRATED → NOT-YET.
- **PB2:** shed ≤ keeper in every year (2019 ≤ 17 MWh, 2021 ≤ 4,391 MWh).
- **PB3:** annual C1 energy moves < 0.5 TWh on every class (the clip binds only in scarcity hours).
- **PB4:** 2020 moves least (fewest scarcity hours).

## 5. Decision rule (fixed now)

- **A:** recommend promotion if (i) the legs compose with the keeper's 2021–2025 legs and (ii) no train-year determination moves. The basis is rule 14; a worse 2019/2020 price is reported, not reverted.
- **B:** the structure is rule-14 correct (the published cap). But it lets the x33 peak bands, identified in-sample on 2023 under a $5k cap, bid in a $9k regime where they were never identified. A fit change there cannot be read as evidence for or against B. So **B goes to the owner as a decision card** with its numbers, whatever they are. If the owner declines B, A alone is promoted.

## 6. Routed, not in this session

- R3/R4 residual: the cheap-gas-year coal stay-on conduct (Martin Lake / Sam Seymour / Sandy Creek; §1b). It needs an offer-side identification that the fenced cells and the declined SCED corpus do not provide.
- R2: scored price above HCAP (overlay/cap composition).
- **SPP carries Oklaunion too** (SPP-48 `mid_vintage_exit_carry`, SPP keeper `spp98_remap_span`). ERCOT market data says it was an ERCOT resource. SPP's lane decides its own fleet (rule 25).
- `COAL_PLANT_COMMISSION_YEAR` keys Sandy Creek as 56257 while the bin sheet uses 56611, so Sandy Creek falls back to 2010. Pre-existing; it feeds age-based availability.
- `derive_campd_coal_heat_rates.py` excludes bin-sheet plants absent from the BA-filtered fleet (127).
- The mislabelled `60d_DAM_Gen_Resource_Data_2020_Jul-Dec_Oct-Dec.parquet` holds 2019 Nov–Dec rows.
