# PRECOMMIT — R-ERCOT-13: bring 2019 onto the keeper's measured reserve inputs

**Session:** R-ERCOT-13, 2026-09-28. **Keeper (control):** `2026-09-28-r-12-frontera-membership`,
bundle `results/calibration/r_ercot12_frontera_span` (committed; rule 29(b) form 4 — no control solve).
**Lever queue:** item 1 of the handoff (2019/2020 over-scarcity), item 2 tested jointly.

## 1. Phase 0 (zero LP, from the keeper's committed hourlies + EIA-930 + NP6-905)

Script: session scratchpad `p0.py` (keeper `hourly/system_2019`, `class_hourly_2019`,
`reserve_family_2019` against `actual_lmp_hourly_ERCOT`, `EIA930_BALANCE_2019_*`,
`ercot_2019_ordc_reserves_hourly`). Clock alignment: model hour 0 ends 07:00 UTC (r = 0.9995 vs 930 demand).

| check (2019) | finding |
|---|---|
| Demand | Model demand = 930 demand + 930 total interchange (corr 0.9999; annual 383.08 vs 383.67 TWh). **DC-tie imports are already netted — not the gap.** |
| Coal / wind / solar in the model's 48 h ≥ $1k | Match 930 within ~±0.3 GW (coal 12.97 vs 13.01 GW; wind 4.00 vs 3.76). **Not the gap.** |
| Gas in those hours | Model 44.8 GW vs 930 45.9 GW — **~1.1 GW short**, up to 1.8 GW in shed hours. |
| Reserves in the 8 shed hours | Model holds **exactly 3,395 MW** (its floor) while shedding up to 1,460 MW. Actual PRC 2,287–2,727 MW, RTOLCAP 2,349–3,078 MW, system lambda $1,071–5,289 — the real market ran reserves below the model's floor and did not shed. |
| Hour 5391 (2019-08-13 HE16) | Model scored $12,961 = energy dual $5,000 (shed) + ORDC dual $2,394 + measured RTORDPA $5,568; actual $8,803 = λ $1,071 + RTORPA $2,152 + RTORDPA $5,568. |
| Price decomposition | ~22 of the +27 $/MWh LW excess sits in the 54 hours either side is ≥ $1k (Aug LW $343 vs $165). A separate year-round +$2–4 median offset exists in BOTH 2019 and 2020 (routed, §6). |

**Root cause.** The keeper recipe carries `ercot_load_resource_reserve_from_year = 2020` and
`ercot_reserve_supply_cap_from_year = 2020` (ercot-253 D1). In 2019 the model therefore
(a) makes generators hold the RRS that Load Resources actually supplied (measured 2019 LR RRS
awards: mean 698 MW; 412–596 MW in the shed hours), and (b) lets cleared reserve exceed the
measured online responsive capability (RTOLCAP/RTOFFCAP). 2019 was excluded **only** because its
LR series was "deliberately left unbuilt (locked-test tier)" (ercot-252; `data/raw/ercot-AS/README.md`).
That regime was removed 2026-09-09 (rule 22 coda). Every other year 2020–2025 solves with both inputs.

## 2. The arm (one delta, zero DOF)

`ercot_load_resource_reserve_from_year` 2020 → **2019** and `ercot_reserve_supply_cap_from_year`
2020 → **2019**, with the new measured input `data/raw/ercot-AS/ercot_2019_as_up_mw.parquet`
(built by the unchanged `build_ercot_as_backyear.py --year 2019`; sha256 `6e220631…c965`).

- Rule 14: measured inputs replacing an omission; no misalignment exception applies.
- Rule 13: both are reproducible physical/market inputs already admitted in 2020–2025.
- Rule 21: zero new free parameters; the DOF ledger is unchanged (12 entries).
- Rule 1(c): offer multipliers untouched.
- Rule 19: no new mechanism — the same two gates, extended one year.
- **Byte-identity:** both gates are monotone `year >= from_year`, so 2020–2025 are unchanged by construction. Only 2019 re-solves.

**G-DRIFT** (`git diff 2af9ab74 HEAD -- src/market_sim scripts/run_calibration*.py scripts/replay_keeper.py scripts/lib data/raw/_validation-source data/raw/reference`):
every hunk is INERT for ERCOT —
- CAISO `caiso_tac_shares_standard_time` (default off, other ISO);
- SOCO ST_GAS campaign-floor partition (other ISO);
- PJM virtual settlement (default off, other ISO);
- SPP CAMD→EIA remap rows (SPP plant ids 1416/3006/762/63628);
- `ISO_PLANT_ENTRIES` reformat (value-identical);
- `ferc714.py` / `seam_neighbour_price` (new, not on the ERCOT backcast path);
- `scenarios.py` (new default-off fields).

Form 4 is valid; the keeper is the control.

## 3. Shards (rule 36: one year, one container)

| shard | command (after `git rev-parse HEAD` == pinned SHA) | role |
|---|---|---|
| **A** `claude/r-ercot13-arm-2019` | `replay_keeper.py results/calibration/r_ercot12_frontera_span --years 2019 --set ercot_load_resource_reserve_from_year=2019 --set ercot_reserve_supply_cap_from_year=2019 --out-dir results/calibration/r_ercot13_arm_2019` | **the candidate** |
| **B** `claude/r-ercot13-lr-2019` | same, with the LR credit `--set` only; `--out-dir results/calibration/r_ercot13_lr_2019` | **attribution diagnostic only — never promotable, never registered.** It exists to split A's movement between the two inputs. Its result cannot select A's config; A is fixed here. |

## 4. Predictions (2019, vs keeper; registered before any solve)

- **P1 — shed falls.** Shed 4,662 MWh → ≤ 1,500 MWh. The 8 shed hours are freed by 0.4–0.6 GW of LR credit plus the cap.
- **P2 — deep tail falls.** Hours ≥ $1k 48 → 20–40 (actual 26).
- **P3 — C3a improves but still FAILS.** +53.6 % → +25 % to +45 %. The year-round median offset (~+19 % excluding ≥ $1k hours) is untouched by this arm.
  - **Caveat on direction:** in 2022 (run252) the cap *raised* mid-band price (ORDC shortfall hours 199 → 811). A net C3a rise is possible. If C3a rises, P3 is MISSED and reported as such.
- **P4 — C3b falls.** 1.228 → 0.5–0.9.
- **P5 — C1 moves by < 1.5 TWh on every class.** The freed MW is scarcity-hour headroom, too few hours to move annual energy. So CC_REGULAR stays FAIL (+9.63) and COAL_PRB stays FAIL (−8.15). **Consequence:** lever item 2 is NOT the same object as item 1. It is routed as its own object (§6).
- **P6 — 2020–2025 unchanged.** Train-year determinations do not move. The ISO stays NOT-YET on 2023 (owner hold) and 2024.

## 5. Decision rule (fixed now)

- **Recommend promotion if both hold:**
  - (i) A's 2019 leg composes with the keeper's committed 2020–2025 legs;
  - (ii) no train-year determination moves.
- The basis is rule 14 (measured input replaces an omission), **not** the residual. If 2019 price gets worse, it is still recommended and reported at full magnitude.
- B never enters the decision.

## 6. Routed, not in this arm

- **R1 — shed-penalty vintage inversion.** `iso_config.voll` = $5,000 in every year, while 2019–2021 HCAP is $9,000 (`ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR`). So the rigid RRS/Reg-Up step ($9,000) prices ABOVE firm-load shed ($5,000), and the LP sheds before deploying RRS. ERCOT's EEA sequence deploys RRS first (EEA2) and sheds last (EEA3). This is a structural ordering defect in 2019–2021. It is the next object; it needs its own PRECOMMIT and touches 2021 too.
- **R2 — the scored price can exceed HCAP.** Model λ at VOLL + ORDC dual + measured RTORDPA reached $12,961 against a $9,000 cap. This is an overlay/cap composition question.
- **R3 — year-round +$2–4 median offset** in 2019 and 2020, below the scarcity range. Candidates: gas delivered price or basis, the 2019 `gas_prices` override of $2.57 (HH), and the margin anchor. Offer multipliers stay frozen.
- **R4 — C1 CC_REGULAR overshoot / COAL_PRB shortfall** in 2019–2020 (+9.6 / −8 to −13 TWh). This is energy-volume merit order across all hours, not scarcity hours.
