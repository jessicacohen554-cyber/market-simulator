# ERCOT close-out wave 1: zero-LP censuses (L1 coal fuel, L2 West import, step-6 hygiene)

Lane `closeout-ERCOT` wave 1, 2026-10-02, branch `claude/closeout-ercot-wave1` from `origin/main` 4d459da3.
Charter: `docs/backcast-closeout-plan-2026-10.md` §3.5 steps 0b, 2 and 6. **No LP was run.** Every
number below reads committed files: the keeper bundle `results/calibration/r_ercot24_span`
(keeper `2026-10-02-r-24-ordc-published`, P1 `hourly/unit_marginal_<Y>.parquet`, all seven years
present), EIA-923 Page 2 / Page 5 (`data/raw/coal-stocks`, `data/raw/coal-receipts`, 2018–2024),
EIA-923 generation-and-fuel, the NP6-86 SCED binding-constraint archive (2019 zips, 2020–2025
parquets), the ERCOT network-model settlement-point list, and the 60-Day DAM Gen Resource
disclosures (2019–2025).

Step 0a checked: R-ERCOT-24b is promoted on `main` (PR #7017; `frontend/data/backcast/keepers/ERCOT.json`
`keeper = 2026-10-02-r-24-ordc-published`). No other `claude/*ercot*` branch or open ERCOT PR exists,
so no step here duplicates another live session.

## Verdict table

| Step | Pre-fixed reading (charter) | Measured | Verdict |
|---|---|---|---|
| 0b L1 | Martin Lake and Coleto bind in 2022 | Under the cumulative pile identity (form B, `stock_min` = 0): **Martin Lake 2022 binds by 3.34 TWh, Coleto 2022 by 1.40 TWh** | **HOLDS** |
| 0b L1 | Nothing else binds, except Coleto Sep 2021 | Coleto 2021 binds (0.42 TWh, Sep–Dec) ✓. **Smaller PRB binds also show up:** Parish 2022 0.30, Sandy Creek 2022 0.31, Limestone 2021/22/23 0.10/0.19/0.20, Coleto 2019 0.24, Martin Lake 2023 0.07. **Lignite:** Oak Grove 2021–24 0.25–0.70 and Twin Oaks every year 0.07–0.35 TWh | **PARTIAL.** The "nothing else" half fails: the other binds are small, ≤ 0.70 TWh per plant-year |
| 0b L1 | (charter formula, form A) | Form A as written, `(R_m + S_{m−1} − stock_min)/HR` per month on its own, **does not bind Martin Lake 2022 at all** at `stock_min` = 0 | Form A is not a physical identity (see §1.2). The PRECOMMIT uses form B |
| 2 L2 | ≥ 70 % of > $5 West-premium hours coincide with a measured West-import bind → build | West-import (seam) binds cover **0.7–14.2 %** of premium hours, 2019–2025. In base hours the rate is about the same (no lift). Even counting every unmapped West element as a seam element gives at most 59.5 % | **FAILS → record and close. No build, no PRECOMMIT** |
| 6 | DAM site with p98 HSL and no accepted EIA plant (the Fusco class) | **0** accepted sites point at a plant missing from the year's fleet. One **definite fleet miss** was found outside the crosswalk: **Decker Creek ST1/ST2 (3548), 724 MW in 2019–20 and 404 MW in 2021 to Mar-2022, absent from the 2019–2022 fleet.** The rest are crosswalk-coverage gaps (§3) | Routed to W0 |
| 6 | CDR / Capacity-Changes COD cross-check vs 860M | Neither CDR nor the Capacity-Changes-by-Fuel-Type workbook is on disk (`find data/raw` finds no match). The research's G8 download is still owed | **DATA-BLOCKED (owner download G8)** |

## 1. L1: coal fuel-delivery ceiling census

Script: `scripts/probes/_ercot_closeout_l1_coal_fuel_census.py`. Outputs:
`data/l1_coal_census_plant_month.csv` and `data/l1_coal_census_plant_year.csv`.

### 1.1 Construction (fixed before the read)

- **Model energy:** keeper P1 coal MWh per plant-month from `unit_marginal_<Y>` (`fuel == coal`). Hour `h` is placed at `Jan-1 + h`.
- **HR:** plant-year coal heat rate from EIA-923 generation-and-fuel (`elec_fuel_mmbtu / net_generation_mwh` over coal fuel codes).
- **hc:** plant-year quantity-weighted receipt heat content.
- **Receipts:** EIA-923 Page 5, every lot, by month. Owner ruling R-3 (2026-10-02, plan §5.0) admits the year's own receipts and stocks as a backcast take *ceiling*. That supersedes the older `coal_receipts.py` / `coal-stocks/README.md` posture, which allowed prior-years receipts only.
- **`stock_min`, declared ex ante:** arm **0 = zero tons**. This is the codebase's declared minimum operating stock (`src/market_sim/data/coal_fuel_inventory.py` module docstring: "Minimum operating stock = ZERO … a floor may be added later only from a cited days-of-burn source"). It is also the identity `build_coal_monthly_pile` already implements. Arm **P** (sensitivity only, never the PRECOMMIT value) is the plant's own minimum measured month-end stock over Y−3..Y−1.

### 1.2 Why form A is not the test

Form A gives each month `S_{m−1}` (the measured stock carried in) plus `R_m` on its own. The same ton then funds the burn in every month it sits on the pile, because month m's budget ignores what months 1..m−1 already drew. Martin Lake 2022 shows the problem: under form A it never binds at `stock_min` = 0. But its December-2021 stock (0.90 Mt) plus 2022 receipts (8.22 Mt) cannot fund the model's 16.69 TWh × 11.42 MMBtu/MWh.

The physical identity is the **cumulative pile**: `Σ_{t ≤ end of m} HR·P ≤ (S_dec(Y−1) − stock_min)·hc + cumR_Y(m)`. This is form B. It is exactly the row `build_coal_monthly_pile(..., measured=...)` writes, with `floor_parts=None`. The census reports form A too, so the charter's formula is not hidden. The verdict rests on form B.

### 1.3 Results (form B, `stock_min` = 0, max cumulative excess, TWh)

| Plant (EIA) | Class | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|---|
| Martin Lake (6146) | PRB | 0 | 0 | 0 | **3.34** | 0.07 | 0 |
| Coleto Creek (6178) | PRB | 0.24 | 0 | **0.42** | **1.40** | 0 | 0 |
| W A Parish (3470) | PRB | 0 | 0 | 0 | 0.30 | 0 | 0 |
| Sandy Creek (56611) | PRB | 0 | 0 | 0 | 0.31 | 0 | 0 |
| Limestone (298) | PRB | 0 | 0 | 0.10 | 0.19 | 0.20 | 0 |
| Fayette (6179), J K Spruce (7097), Oklaunion (127) | PRB | 0 | 0 | 0 | 0 | 0 | 0 |
| Oak Grove (6180) | LIG | 0 | 0 | 0.57 | 0.25 | 0.70 | 0.67 |
| Twin Oaks / Major Oak (7030) | LIG | 0.10 | 0 | 0.07 | 0.20 | 0.16 | 0.35 |
| San Miguel (6183) | LIG | 0 | 0 | 0 | 0 | 0 | 0 |

Sum over 2022: PRB 5.54 TWh, lignite 0.45 TWh. Annual footing for 2022: Martin Lake model 16.69 TWh, burn identity 12.55 TWh, receipts 11.89 TWh. Coleto model 4.31 TWh, identity 2.69 TWh, receipts 2.56 TWh. Both reproduce the research note's numbers (16.64 / 12.59 and 4.32 / 2.7).

**2025.** The opening stock (Dec 2024) is on disk. EIA-923 Final 2025 has landed (plan §4 ★2), but its Page 5 receipts are not curated yet. Without them, the existing code keeps every yard on the prior-years ratable rate (NEXT-9: "a missing input is never substituted"). Read on the 2023–24 mean rate, 2025 binds at **Parish 2.58 TWh and Limestone 1.00 TWh** (Twin Oaks 0.29). That direction matches 2025 C1 COAL_PRB +3.64 TWh.

**Fayette caveat.** Fayette's stock reads 0 t in Apr–Jun 2022, a reporting gap per the research note. Form A flags Jul-2022 because of it. Form B does not bind, because the annual identity has slack. Fayette is unconstrained in every arm.

## 2. L2: West import-direction rating census

Script: `scripts/probes/_ercot_closeout_l2_west_import_census.py`. Outputs: `data/l2_summary.json` and
`data/l2_top_seam_elements.csv`.

### 2.1 Definitions (written into the script docstring before the first read)

- **Premium hour:** `rt(LZ_WEST) − rt(HB_HUBAVG) > $5`.
- **West-import bind:** a binding NP6-86 element (ShadowPrice > 0, any SCED interval in the hour) with exactly one terminal in LZ_WEST and the other in a known non-West load zone. Terminals are mapped with ERCOT's network-model `SUBSTATION → SETTLEMENT_LOAD_ZONE`, which covers 771 of 860 stations. WESTEX is excluded because it limits West export.
- **Intra-West elements** (both terminals in LZ_WEST, plus MCCAMY, CULBSN and TRDWEL) are reported but never counted, under ERCOT-117 (G).

### 2.2 Results

| Year | > $5 h | mean premium | seam cover (base) | intra-West cover (base) | premium mass in intra-only hours | HB_WEST share of LZ_WEST premium |
|---|---|---|---|---|---|---|
| 2019 | 1,912 | $54.6 | **1.7 %** (4.9 %) | 67.3 % (36.6 %) | 80.7 % | 2.6 % |
| 2020 | 1,389 | $72.1 | **7.7 %** (6.7 %) | 71.8 % (34.9 %) | 74.7 % | 1.8 % |
| 2021 | 713 | $37.4 | **0.8 %** (3.0 %) | 68.3 % (27.0 %) | 73.2 % | 26.5 % |
| 2022 | 1,380 | $38.5 | **2.8 %** (2.5 %) | 71.2 % (29.6 %) | 83.5 % | 22.7 % |
| 2023 | 2,419 | $46.4 | **0.7 %** (0.5 %) | 79.8 % (39.8 %) | 84.4 % | 24.2 % |
| 2024 | 2,847 | $32.0 | **14.2 %** (10.2 %) | 76.1 % (49.2 %) | 67.2 % | 25.1 % |
| 2025 | 3,734 | $26.1 | **10.0 %** (6.6 %) | 85.5 % (57.6 %) | 76.8 % | 22.8 % |

**Reading.** The West LZ premium is a **Permian load-pocket** phenomenon, not a West-wide zonal separation:

- Seam binds have no lift over base hours.
- The binding seam elements are small 138 kV ties with 26–149 MW limits (`HEXT_YELWJC1_1`, `FORTMA_YELWJC1_1`).
- Two-thirds to five-sixths of the premium mass sits in hours where only intra-West elements bind.
- The 345 kV West hub carries only 2–27 % of the load-zone premium.

A zonal import rating cannot reproduce a nodal pocket, and building it is the refused sub-zonal split (ERCOT-117) under another name. The step-3 build does not proceed. The ≈ +$1.3–1.5/MWh West basis stays in the ledger as the intra-zone LZ basis (plan §3.5 ledger line).

## 3. Step 6: DAM-crosswalk membership census

Script: `scripts/probes/_ercot_closeout_hygiene_membership_census.py`. Output (flagged rows only):
`data/hygiene_dam_membership_flagged.csv`.

The census covers every thermal DAM site with p98 HSL ≥ 50 MW (the crosswalk's own rating construction, all disclosure directories), labelled against the reviewed crosswalk and the keeper's year-Y fleet:

| Year | ok (accepted, in fleet) | accepted but plant absent | unaccepted, proposed plant in fleet | candidate (no row / plant absent) |
|---|---|---|---|---|
| 2019 | 56 sites / 24.8 GW | **0** | 136 / 41.1 GW | 6 / 1.54 GW |
| 2020 | 56 / 24.9 | **0** | 137 / 41.2 | 7 / 1.62 |
| 2021 | 51 / 24.6 | **0** | 140 / 42.2 | 12 / 1.57 |
| 2022 | 51 / 24.3 | **0** | 160 / 42.7 | 2 / 0.96 |
| 2023 | 51 / 24.4 | **0** | 176 / 43.9 | 0 |
| 2024 | 51 / 24.5 | **0** | 179 / 44.3 | 8 / 0.41 |
| 2025 | 50 / 23.7 | **0** | 175 / 44.0 | 12 / 0.78 |

How each candidate was adjudicated, by hand against EIA-860 and the keeper fleet:

- **Decker Creek ST1 / ST2 (`DECKER_DPG1` 320 MW, `DECKER_DPG2` 428 MW).** A **definite fleet miss.** EIA-860 retired sheet: plant 3548 gen 1 retired 2020-10 (320 MW summer), gen 2 retired 2022-03 (404 MW). The keeper's Decker Creek is 190–205 MW, i.e. the four GTs only, in every year 2019–2022. The DAM shows the steam units online 161–277 days a year until retirement. Retired-unit vintage membership is the W0 settlement's object (R-2 Q2: "Final 2025 + 2023/24 retired sheets as the vintage record"). **Routed to W0's `fleet_census_<Y>`. Not repaired here.**
- **`PSA_CC1` (≈ 530 MW, 2019–2022).** The crosswalk proposed Frontera (55098) on capacity alone (score 0.345, unaccepted). That is not membership evidence: R-ERCOT-12 measured `FRONT_EC_CC1` as Frontera's own first DAM day, 2023-04-13, and `PSA_CC1` is a different resource. **Its EIA identity is unresolved in this session.** The site leaves the disclosure after 2022, which suggests a rename. Pasadena Cogeneration (55047, CC_CHP, ≈ 500 MW in the fleet) is a plausible candidate but is not verified. **Not counted as a miss. The Frontera proposal row should be rejected at the next crosswalk re-derive, and the identity adjudicated there.**
- **`MIL_MILLERG1` (75 MW, 2019–20) and `OLINGR_OLING_1` (78 MW, 2019–21).** Unit-grain retirements inside plants the fleet carries (R W Miller 3628, Ray Olinger 3576). The model's Olinger capacity (428 MW) stays flat after unit 1 retired: at most +78 MW of over-inclusion. This is W0's unit-vintage census, not a membership miss.
- **New peaker / CC sites since the crosswalk was built:** `JAD_UNIT1–8` = Remy Jade 66604, `PES1_UNIT1–8`, `BCH_UNIT1–8`, `FLCNS_UNIT1/2`, `TGF_TGFGT_1`. Remy Jade is verified in the fleet (448–462 MW in 2024–25). The other multi-unit peaker sites are consistent with the in-fleet 8 × 60.5 MW builds of their COD years (HO Clarke and Topaz from 2021, Braes Bayou and Mark One from 2022, Brotman from 2023). The site → plant identity of `PES1` and `BCH` is not verified here. `FLCNS_UNIT1/2` (2 × 70 MW, 2025) and `TGF_TGFGT_1` (83 MW) are small single units whose identity is also unverified. **These read as crosswalk-coverage gaps: no evidence of a membership miss, but not every identity is proven.** The crosswalk's site set predates them. A rule-23 re-derive on the 2024–25 disclosures (the data-change trigger) would admit them.
- **`AMOCOOIL_CC1` (2025, 1 day) and `FORMOSA_CC2` (2020).** CHP sites, excluded by design.

**Side finding for the desk, about step 4 / R-7.** The research note (`SHARD-ERCOT-closeout-research-2026-10-02.md` L5 / G2) says the 60-Day DAM Gen Resource Data for 2019–2022 is "raw not on disk". **That is wrong.** `data/raw/ercot-AS/60d_DAM_Gen_Resource_Data_<2018–2022>_*.parquet` carry the full disclosure, including `QSE submitted Curve-MW/Price1..10`. For example, 2019 Jan–Jun has 143,104 CLLIG rows, 34.6 % with a submitted curve, across 33 coal resources. These DAM curves are a proxy for SCED TPO conduct: the ercot-168 table used SCED, and 60-Day SCED still needs the R-7 account intake. Even so, the step-4 per-plant 2019–22 coal offer table has an **account-free DAM-curve route** that the owner card did not know about. It is recorded here, not acted on.

## 4. What this session did not do

- No LP, no shard, no `src/` edit.
- No crosswalk re-derive. Rule 23 needs the data-change commit, and that belongs with W0's census.
- No R-6 rubric work (lane closeout-C).
- No 60-Day SCED intake (R-7, account-gated).

## 5. DRAFT ledger row: 2019/20 coal conduct (desk update 2026-10-02)

The owner deferred all data downloads today, R-7 included (deferred, not cancelled). The 2019/20 coal-conduct miss is therefore carried as a **DRAFT** ledger row, so the frontier statement is ready:

| Field | Value |
|---|---|
| Years / gates | 2019 C1 COAL_PRB −10.48 TWh, CC_REGULAR +8.85 TWh, C3b 0.219. 2020 C1 COAL_PRB −11.83 TWh, CC_REGULAR +10.21 TWh, C3b 0.209 (keeper r-24) |
| Object | 2019–22 coal offer conduct. The keeper prices 2019/20 coal on 2024–25 SCED conduct, which pushes coal behind gas in low-gas years. The C3b summer over-scarcity (Aug carries 73 % / 61 % of SSE) is coupled to the coal under-run (`FINDING-r-ercot-3` §2; research note §2) |
| Status | **DATA-LIMITED**, not a model-class limit and not a tuned residual (rules 13/21: closable only by measured conduct, never by a fitted value) |
| Route | The R-7 bounded intake (60-Day SCED NP3-965-ER + DAM 2019–22 + NP6-576-ER, free ERCOT account) **when it happens** → per-plant coal offer tables, ercot-168 construction, zero DOF, rule 23, full span. Prediction (research §6 step 4): PRB → −3..−6 TWh, CC mirror inside band, Aug over-price shrinks |
| Not the route | `coal_offer_level_rebasis` (R, wrong sign); L1 (this lane's ceiling binds only Coleto 0.24 TWh in 2019 and nothing in 2020, so it worsens rather than closes this row) |
| Account-free alternative (unadjudicated) | The 2019–22 60-Day DAM Gen Resource Data *with* QSE offer curves is already on disk (`data/raw/ercot-AS/`, §3 side finding). A DAM-curve proxy table needs its own charter and owner ruling (DAM ≠ SCED TPO conduct). Recorded so the frontier statement does not say "no data exists" |
| Determination effect | 2019 and 2020 read NOT-YET on C1/C3b until the route runs. The row is DRAFT until the RESULT of the post-W0 span confirms the magnitudes |
