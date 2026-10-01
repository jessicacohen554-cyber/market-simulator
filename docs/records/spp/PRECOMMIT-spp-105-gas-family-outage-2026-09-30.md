# PRECOMMIT — SPP-105: gas-family outage carriers A and B

Lane: SPP-105. Owner card **"Build carrier a and b"** (2026-09-30), over the DESIGN's recommendation to
record a model-class limit.
Design, phase 0 and built census: `docs/records/spp/DESIGN-spp-105-gas-family-outage-2026-09-30.md` (§4, §7).
Keeper / control: `2026-09-28-spp-100-chp-scope`, bundle `results/calibration/spp100_arm_span` (git `11b72265`).
**Written before any solve. Nothing below is chosen from a solved number.**

## 1. What is solved: two arms, each the keeper plus exactly one carrier

| arm | set on the keeper recipe | what it does |
|---|---|---|
| **A** | `wefor_residual = 0.0`, `wefor_residual_groups = [CC_CHP, CC_REGULAR, ST_CHP, ST_GAS]` (existing fields) | removes the statistical WEFOR from the CAMPD-covered gas classes (the rule-19 repair); CT is untouched |
| **B** | `spp_gas_crow_residual_outage = true` (new field, default off) | replaces every gas row's statistical WEFOR / POF with SPP's published gas outage minus the CAMPD events, allocated on the incumbent class key |

- **Zero free parameters in either arm.** A's 0.0 is the carrier's definition (no statistical residual),
  not a value selected by any criterion.
- **B's rule-13 status, declared.** In 41–94 % of hours B sets the model's gas outage equal to SPP's
  published total. That is the pin the charter named. It is built on the owner's override and recorded as
  such.

## 2. Prediction (zero LP; DESIGN §7)

Re-clear instrument, Δ$/MWh all hours / upper tercile:

| arm | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| A | −0.17 / −0.28 | −0.16 / −0.24 | −0.47 / −0.35 | −0.24 / −0.49 | −0.17 / −0.30 | −0.30 / −0.56 | −0.31 / −0.58 |
| B | +0.28 / +0.60 | +0.12 / +0.32 | +4.09 (Uri) / −0.05 | −0.13 / −0.14 | +0.13 / +0.31 | **+1.30 / +3.20** | +0.18 / +0.48 |

- **Arm B, 2024:** the instrument finds 17 short hours.
- **Direction of the train-tier C3a** (keeper −6.7 / −8.6 / −5.4 %):
  - A worsens all three years. 2024 risks crossing the −10 % band.
  - B improves 2024 materially; 2023 and 2025 barely move.

## 3. G-DRIFT (rule 29(b), form 4): keeper `11b72265` → this PR's base `457fa8fa`

- **Up to `264dbb2a`:** audited all INERT by SPP-104 (its PRECOMMIT §3 and Addenda A / B). No SPP-104
  change is armed in either arm; `spp_ct_lole_efor` stays at its default False.
- **`264dbb2a → 457fa8fa`,** over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`,
  `scripts/replay_keeper.py`, `data/raw/_validation-source` and `data/raw/reference`:

| commit(s) | files | verdict | reason |
|---|---|---|---|
| R-CAISO-16 `b8eade78`, R-CAISO-17 `ca84177c` | `eia930/frames.py`, `eia930/demand.py`, `eia930/caiso_hydro_backfill.py`, `renewables.py`, `model/storage.py`, `constants.py`, `scenarios.py`, `solve_surface_declared.py` | INERT | CISO clock windows registered under `caiso_eia930_clock_repair` (CAISO-only, absent from SPP's recipe). The reorganised `_ciso_clock_windows` is read only on the CISO path |
| R-ERCOT-18 `0bd29417` | `fleet/floors.py`, `scenarios.py`, `reference/ercot_stgas_overnight_commitment.csv` | INERT | `netload_drag_prior_year_commitment_index`: default False, absent from SPP's recipe; the artifact is ERCOT-only |
| NYISO-NEXT-15 `f2547c8b` | `scripts/lib/forecast_parity_registry.py` | INERT | forecast-parity declaration only |
| **this lane** | `paths.py`, `scenarios.py`, `data/fleet/arrays.py`, `data/spp_gas_outage.py`, `data/raw/spp-gen-outage/` | **LIVE only under `spp_gas_crow_residual_outage`** | Default off. `crow_rate_out=None` on every unarmed call, so no gas row leaves its branch; `check_cache_key_registration` is clean |

All rows are INERT for the keeper recipe, so **the committed keeper is the control** and no control solve
is spent.

## 4. Solve plan (rule 36)

- **Fourteen shards: arms A and B × 2019–2025, one year per shard.** All are pinned to this PR's merge SHA
  and launched in one message.
- Each shard runs `replay_keeper.py results/calibration/spp100_arm_span --years <Y> <arm --set flags>
  --out-dir results/calibration/spp105<arm>_<Y>`.
- It then runs `scripts/probes/_spp105_shard_check.py --arm <arm>` and pushes its full bundle, including
  `dispatch/<Y>_P1.parquet`, to `claude/spp105<arm>-<Y>` (lowercase arm).
- **The parent solves nothing.** For each arm it composes the seven legs, regenerates the legitimacy
  diagnostics, attests, registers locally and scores.

## 5. Expectations (fixed before any solve; each arm is scored separately)

| # | expectation |
|---|---|
| E1 | Shard check PASS on all 7 legs |
| E2 | Every year solves Optimal within the shard budget |
| E3 | No year's unserved energy rises by more than 500 MWh over the keeper |
| E4 | D-4: no FAIL row the keeper does not carry (keeper: 7) |
| E5 | Train tier 2023–25 stays CALIBRATED; no C1/C3a/C3b/C4 status flip in 2023–25 |
| E6 | Rule-14 cross-check: the arm's gas outage-type is within SPP's published gas outage (\|gap\| ≤ keeper's \|gap\|) in a majority of years |

E6 is already measured at zero LP (DESIGN §4 / §7):
- **Arm A FAILS it.** Its \|gap\| is worse in 5 of 7 years.
- **Arm B PASSES it by construction** (5 of 7 years: 2019 / 20 / 22 / 23 / 24). That pass is the pin itself
  and is **not evidence** of structure.

**Reported, not gated:** per-year ΔC3a, ΔC3b, ΔC3c, class TWh (CT_PEAKER, CC_REGULAR, ST_GAS, COAL_PRB),
Δprice, and the carrier's own logged events / residual / binding share.

## 6. Recommendation rule (fixed)

- **Arm A:** RECOMMEND AGAINST, since E6 is known to fail (rule 14: SPP's own data contradicts removing
  the WEFOR). If E1–E5 hold, that is reported and the recommendation does not change.
- **Arm B:** RECOMMEND PROMOTE iff E1–E5 hold, with E6 and the rule-13 pin stated as the owner's override
  on record. Otherwise AGAINST.
- The owner decides (rule 31). 2019–22 movement is reported at full magnitude and is never the basis.

## 7. Year set (rule 35(b))

SPP's registered years are 2019–2025, all on keeper `2026-09-28-spp-100-chp-scope`. Each arm solves all
seven.

## 8. Shard check, tested before launch

`scripts/probes/_spp105_shard_check.py` was run on five synthetic 2021 legs built from the keeper:

| synthetic leg | expected | result |
|---|---|---|
| A recipe, perturbed price | PASS | **PASS** |
| B recipe, perturbed price | PASS | **PASS** (DATA CHECK passes on the CSV sha) |
| B recipe + stray `hydro_pondage_bound` | FAIL | **FAIL** (RECIPE) |
| B recipe, leg identical to the keeper | FAIL | **FAIL** (ARMED) |
| B recipe checked as arm A | FAIL | **FAIL** (RECIPE) |

Prompt: `docs/records/spp/spp105/shard_prompt_template.txt`.

## Addendum A (2026-09-30, before any solve): G-DRIFT over the `main` merged into this PR

`origin/main` moved to `fd1269a7` while this PR was open, so it was merged in. The only conflicts were
matrix anchor digits. The shards pin the resulting merge SHA, so the audit extends over
`457fa8fa → fd1269a7` on the rule-29(b) path set:

| commit(s) | files | verdict | reason |
|---|---|---|---|
| NYISO-NEXT-17 `1f4793ae` `4ddb0ae4` | `topology_variant.py`, `zone_assignment.py`, `eia930/envelopes.py`, `eia930/zonal_shares.py`, `pipeline/ttc.py`, `interchange/spec.py`, `nyiso_*`, `iso_configs.py`, `constants.py`, `scenarios.py`, `run_calibration*.py`, `reference/nyiso-market-solar-capacity-fgsplit.csv` | INERT | `nyiso_fg_split`: default False, set only when `iso == "NYISO"`. Every new branch reads `nyiso_fg_split_active()`, which is False for SPP |
| R-CAISO-18 `d757b216` | `interchange/caiso.py`, `import_nodes.py`, `neighbor_price.py`, `fuel/electric_power.py` (new function only), `scenarios.py`, `runner.py` | INERT | `caiso_intertie_unprinted_year_measured_gas`: default False, CAISO intertie-hub path only |
| miso-292 `13b721ea` | `_validation-source/actual_lmp.json` (MISO `rt_lw` keys), `scripts/lib` scoring | INERT for the solve | MISO benchmark keys only; SPP's entries and the solve path are untouched |

All rows are INERT, so the committed keeper remains the control. After the merge,
`check_cache_key_registration` is ok, the matrix guard with `--base origin/main` reports "1 new field(s)
all registered", and `tests/iso/spp` passes (65 tests).
