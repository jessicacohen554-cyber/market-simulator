# PRECOMMIT — R-ERCOT-20: simple-cycle GTs split out of three ERCOT CC plants

Date 2026-09-30. **Written before any solve.** The pinned SHA is the commit that carries this file.

- **Keeper and control:** `2026-09-30-r-19-eia-923`, bundle `results/calibration/r_ercot19a_span` (2019–2025), basis SHA `a63b8e94`. Its committed bundle is the control for every year (G-CTRL form 4, rule 29(b)). No control solve.
- **Authority:** owner decision card, verbatim *"Build 4-plant split (Recommended)"*. The evidence is in `FINDING-r-ercot-20-2024-c3a-and-gt-in-cc-2026-09-30.md` §3.
- **Scope reduced to three plants, stated.** Silas Ray (3559, 61 MW GT) is dropped. The sheet already carries it as CT_PEAKER, but an EIA-923 class override relabels the whole plant CC_REGULAR, and 3559 is also in `mixed_fossil_plants` in 2019/2022. A split child there would mismatch classes against the benchmark. Routed, not built.
- **Rule 1(c):** `offer_curve_by_group` and every `config_partition_overrides` value are untouched. The 2023 k=33 owner hold stands. Promotion is the owner's (rules 31/35).
- **D-4:** the day-grain design is held by owner ruling ("Hold the design (Recommended)"); see `DESIGN-r-ercot-20-d4-day-grain-drag-mask-2026-09-30.md`.

## 1. What changes (rule 14 boundary correction, zero free parameters, no new `ScenarioConfig` field)

**1. `data/raw/reference/custom-bin-assignments.csv`.** Each parent keeps its CC (CT + CA) nameplate and takes a `[CC]` tag. A new CT_PEAKER child `[CT]` (code `parent*10+3`, the `tag_mixed_plants` convention) carries the EIA-860 prime-mover-GT nameplate. Parent + child equals the old sheet row exactly.

| Parent → child | Zone | CC MW | GT MW (child) | GT units (CAMPD) | GT in service |
|---|---|---|---|---|---|
| 3469 T H Wharton → 34693 | Houston | 663.6 | 526.3 | THW51–56 (+ GT1 16.3 MW, not in CAMPD) | 1975 (GT1 1967) |
| 7900 Sand Hill → 79003 | South_Central | 388.0 | 308.4 | SH1–4, SH6, SH7 | 2001 / 2010 |
| 56350 Colorado Bend → 563503 | Houston | 580.1 | 74.0 | CT-4A/4B | May 2023 |

Child columns:

- **Heat rate.** The sheet HR is the measured CAMPD CT net rate (pooled). The year's own rate comes from the existing R-ERCOT-11 resolver: a tagged child reads its parent's entry in its own family's map. For CT that is `campd_ct_heat_rates_ERCOT.csv`, keyed by facility and derived from `unitType == "Combustion turbine"` only.
- **Pct / min-run / HR-mult tuple.** The modal CT_PEAKER sheet tuple for the unit-size bucket: units ≥ 40 MW (Wharton, Sand Hill) `0/45/47/8, 1, 1, –/1.15/1.0/1.08`; units < 40 MW (Colorado Bend) `0/30/25/45, 1, 1, –/1.18/1.0/1.1`.
  - HR mults are overridden by the class offer curve. `pct_peak` is overridden to 7.
  - The rule is declared, not tuned. No value was compared against any output.

**2. `data/raw/reference/master-plant-registry.csv`.** One row per child, in the 34702/49392 format. `year_built` is the GT in-service year: 1975 / 2001 / 2023. This gives Colorado Bend's GTs a 2023 COD ramp (they come online July 2023 against an actual May 2023). The old sheet had those 74 MW in service in every year back to 2019.

**3. `src/market_sim/data/outages.py`.** `_CC_SITE_SIMPLE_CYCLE_UNITS`. The outage extracts tag the GT units CC_REGULAR, so their windows derated the CC bin. They are now dropped at routing, like every CT (rule 19: the same exclusion, one more key).

**4. `src/market_sim/data/fleet/eia860.py`.** `CC_REGULAR_COMMITTED_PCT_BY_PLANT` for 3469 / 7900 / 56350 is rescaled so the committed block keeps the **same MW** on the CC-only nameplate: 8.4 → 15.06, 17.9 → 32.13, 27.3 → 30.78. This is a capacity-basis reconciliation, not a re-derive (rule 23). The measured MW is unchanged.

**Tests:** `tests/unit/data/test_r_ercot_bin_heat_rates.py` has 3 new tests: children resolve to the parent's CT entry; parent + child equals the EIA-860 nameplate; the site GTs are dropped at outage routing. `tests/unit/data` shows 93 failures both before and after the change, the identical set (other ISOs' unhydrated data).

## 2. Zero-LP footprint (`scripts/probes/_r_ercot20_gt_split_census.py` → `r_ercot20_gt_split_census.json`)

Available TWh, base → arm:

| Year | 3469 CC | 34693 GT | 7900 CC | 79003 GT | 56350 CC | 563503 GT |
|---|---|---|---|---|---|---|
| 2019 | 9.18 → 5.13 | 3.51 | 4.22 → 2.44 | 2.28 | 3.87 → 3.26 | 0 |
| 2022 | 8.67 → 4.84 | 3.31 | 4.61 → 2.67 | 2.19 | 3.58 → 3.27 | 0 |
| 2023 | 8.98 → 5.01 | 3.52 | 4.47 → 2.51 | 2.30 | 4.08 → 3.49 | 0.28 |
| 2024 | 8.63 → 4.90 | 3.37 | 5.06 → 2.80 | 2.22 | 4.40 → 3.83 | 0.54 |
| 2025 | 8.93 → 4.99 | 3.21 | 4.19 → 2.13 | 2.14 | 4.51 → 3.92 | 0.52 |

- **The parents' per-tranche offers are byte-equal.** Only capacity moves.
- **The children sit on the CT ladder.** 2024 lowest tranche: Wharton GT $31.5, Sand Hill GT $32.8/MWh, against the Wharton CC committed block at $5.55.
- **Spillover, stated.** The class-level DAM availability scaling and the class-level floors are defined over class capacity, so other plants move. Other CC_REGULAR available energy moves +0.02 to +0.22 TWh and other CT_PEAKER +0.14 to +0.36 TWh. Class must-run moves −0.15 to 0 TWh for CC and 0 to +0.10 TWh for CT (2023 is the largest). This is the same class of effect R-ERCOT-11 §3 recorded.
- **Non-target gas mc is unchanged** (the zonal-basis recentring is class-agnostic).

## 3. G-DRIFT (keeper basis `a63b8e94` → HEAD)

- 12 commits touch 35 solve-path files. **Every hunk is INERT for an ERCOT backcast:**
  - NYISO-NEXT-17 is gated on `iso=="NYISO"`.
  - R-CAISO-17/18 are CISO-only or behind default-off flags.
  - SPP-105 is SPP-only.
  - R-ERCOT-19's two sub-gates are default-off and absent from all seven recipe years.
  - The new constants are declared at their live hash, so the ERCOT solve-surface fingerprint is unchanged.
  - `actual_lmp.json` has MISO keys only.
- The only LIVE hunks are this PRECOMMIT's four inputs. The keeper's committed bundle is the control.

## 4. Arm

- Seven shards, one per year 2019–2025 (rules 34(c) / 36). Prompts: `SHARD-PROMPTS-r-ercot-20.md`.
- Each runs `replay_keeper.py results/calibration/r_ercot19a_span --years <Y> --out-dir results/calibration/r_ercot20_arm_<Y>` at the pinned SHA, with **no `--set`**. The recipe is the keeper's and the change is in the inputs.
- Input sha256 changes: `custom-bin-assignments.csv` `d13e0014…` → `deaebee4…`; `master-plant-registry.csv` → `4e9eb134…`.

## 5. Predictions (before solving)

**Mechanism.** About 835 MW (909 MW from mid-2023) leaves the CC econ ramp ($16–27/MWh in 2024) for the CT ladder ($31/MWh and up).

- **Split plants' total dispatch** falls toward EIA-923 in every year. 2024: 11.4 TWh (the 3 plants) → 6–8 TWh, against 5.3 actual.
- **The GT children run little:** 0.1–0.6 TWh each per year. Sand Hill's efficient LM6000s run the most.

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| C1 CC_REGULAR (keeper) | +9.70 F | +12.39 F | −0.54 | −7.69 | +3.72 | −1.28 | −1.21 |
| C1 CC_REGULAR (pred.) | +8.3 to +9.2 | +11.0 to +11.9 | −1.8 to −0.9 | **−9.0 to −8.1 (FAIL expected)** | +2.3 to +3.3 | −2.7 to −1.7 | −2.6 to −1.6 |
| C3a (keeper) | +23.9 % | +5.6 % | +4.6 % | −8.7 % | −19.8 % | −10.7 % | −9.8 % |
| C3a (pred.) | +24.0 to +25.0 | +5.7 to +6.6 | +4.7 to +5.6 | −8.6 to −7.6 | −19.8 to −19.0 | **−10.5 to −9.4 (may flip CALIBRATED)** | −9.7 to −8.6 |

- **CC_REGULAR net −0.5 to −1.6 TWh/yr.** The ~2–4 TWh removed from the split plants is back-filled 50–80 % by the under-running efficient CCs (0.8–0.9×). The bench is unchanged, since EIA-923 GT rows were already CT_PEAKER.
- **CT_PEAKER +0.3 to +1.0 TWh/yr** (below the 2 % C1/C8 materiality line).
- **LW price +0.1 to +0.7 $/MWh.**
- **C3b** ±0.02. **C8 ST_GAS** ±1.5 pp. **Slack and h > $1k:** ±2 h and ±100 MWh.

**2022 risk, named.** C1 CC_REGULAR sits at −7.69 against a ±8.00 band. It is expected to cross, which would flip 2022 to NOT-YET. Under rule 30(c) (amended 2026-09-30) a held-out miss downgrades the ISO. The ISO is already NOT-YET (2023 hold, 2024).

## 6. Decision rule

- **Promote** under the standing instruction ("Is it an improvement? Then promote") only if no year's determination flips worse. The basis is rule 14 (accurate boundary), not the residual.
- **If any year flips worse** (2022 is expected to), send a decision card to the owner with the full before/after, and keep every bundle (rule 31). Rule 14 says the accurate boundary stays in the model; the card asks only whether to promote now or hold for the CC_REGULAR 2022 root cause.
- **DOF ledger:** unchanged (zero added). The CT tuple rule and the committed-MW preservation are declared input reconciliations, not free parameters.
