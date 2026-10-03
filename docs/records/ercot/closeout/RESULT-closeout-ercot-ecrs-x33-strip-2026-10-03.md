# RESULT — closeout-ERCOT-ECRS: the ×33 peak bands removed from 2019–2023 (R-42 + R-46)

Lane `closeout-ERCOT-ecrs`, branch `claude/closeout-ercot-ecrs`.

- Owner rulings: **R-39** (design a 2023 config that reflects ECRS), **R-42** (*"A: Remove ×33 from 2023"*), **R-46** (*"Strip the ×33 bands from 2019–22 after the 2023 result"*).
- Records: `FINDING-closeout-ercot-ecrs-phase0-2026-10-03.md` and `PRECOMMIT-closeout-ercot-ecrs-2023-structural-2026-10-03.md`, with Addenda 1–2 pushed before each launch.
- **NOT PROMOTED — owner ruling R-51 (2026-10-03, relayed by the desk): option B, "Keep the ×33 keeper".** The incumbent keeper `2026-10-02-closeout-l1-coal-fuel` and its CALIBRATED 2023 scope are unchanged.
- The span was registered in session as probe `2026-10-02-closeout-ecrs-x33-strip` (bundle `results/calibration/closeout_ercot_ecrs_span`, 2019–2025). That registration is **kept off main**: `audit_keepers --iso ERCOT --check` E13 refuses a non-keeper run stamped to no keeper (the SOCO-3 precedent). The evidence lives on the five leg branches and in this record, and the composite re-builds at zero LP (§1).

## 0. Answer

The ×33 `peak` / `phys_peak` / `peak_ladder` multipliers are gone from every carve-out and validation year. They were a gate-swept residual band (ercot-236 §4, min |C3a-2023|), not a market mechanism.

2023's ECRS regime is now carried only by its real, date-keyed mechanism, `ercot_ecrs_conservative_deployment`, which was already armed. The design's one new element (an ORDC reserve net of ECRS) was killed at phase 0 by ERCOT's published RTORPA.

- **All three pre-registered kills (K1 recipe, K2 shed, K3 governance) pass in all five re-solved years.**
- The legs are solved at the keeper's own leg code (`106d6bb7`), with zero code drift.
- 2024 and 2025 are byte-identical to the keeper.
- The ISO determination stays **NOT-YET**.
- Fit gets better in two years (2019 and 2020 C3b go to PASS) and worse in three (2021 C3b, 2022 C3a/C3b, 2023 C3c).

**2023 against the IMM benchmark:** the model now prints $36.95. That is +5.6 % against the IMM's ECRS-neutral counterfactual (≈ $35), against +39.9 % for the keeper. The 2023 tail the model no longer prints is the ECRS artificial-shortage premium, which the energy-only LP does not represent (Door D). The ×33 band had been standing in for it.

**Recommendation (rule fixed in PRECOMMIT §5 before any solve):** K1–K3 pass in every year, so **promote on structure** (rule 1), whatever the direction of the fit.

**Ruling: not promoted (R-51, option B).** The keeper keeps the ×33 carve-out.

## 1. Legs (rule 34/36: one shard per year, each pinned at its own leg commit; parent `106d6bb7` for all)

| Year | Pin (leg commit) | Leg replayed | Strip commit / branch | LP wall |
|---|---|---|---|---|
| 2019 | `f4e5be97…` | `closeout_ercot_l1_2019` | `bc54614b` `claude/closeout-ercot-ecrs-2019` | ≈ 19.5 min |
| 2020 | `199c5d82…` | `closeout_ercot_l1b_2020` | `5027714e` `claude/closeout-ercot-ecrs-2020` | 14.5 min |
| 2021 | `211c34cb…` | `closeout_ercot_l1b_2021` | `ac01fd92` `claude/closeout-ercot-ecrs-2021` | 15.0 min |
| 2022 | `cacafbfd…` | `closeout_ercot_l1b_2022` | `5160b3ac` `claude/closeout-ercot-ecrs-2022` | 22.8 min |
| 2023 | `2e5d93a2…` | `closeout_ercot_l1b_2023` | `3783ae77` `claude/closeout-ercot-ecrs-2023` | 13.2 min |
| 2024 | — | keeper leg `e8a29b96` | unchanged (sha-identical sidecars) | — |
| 2025 | — | keeper leg `86ce1db5` | unchanged (sha-identical sidecars) | — |

- Every strip leg was verified by the parent before its shard was archived:
  - 19 files in the pushed tree
  - `dispatch/<Y>_P1.parquet` present
  - `unit_marginal_<Y>.parquet` present
- All five shards are archived.
- Launch notes:
  - The 2023 shard was first created with a placeholder prompt, then interrupted and re-prompted before any solve (Addendum 1).
  - The 2020 and 2022 shards each had a first launch exit 127 before the solver started (a `/usr/bin/time` wrapper that isn't installed). Each relaunched in the same session rather than fresh as R-46 asks; the solve ran once per year.
- The composite (`scripts/probes/_closeout_ecrs_compose_span.py`, zero LP):
  - starts from the keeper bundle and swaps in the 2019–2023 year files
  - concatenates the root frames from the seven legs
  - carries every leg's `dispatch/` and `floors/`
  - re-stamps `config_partition_overrides` with `stamp_config_partition.py`, which `--check` confirms
  - regenerates `legitimacy_diagnostics.json` over all seven years
- 2024/2025 C8 forced shares reproduce the keeper's to the digit. A first compose without the 2024/25 `floors/` read 0 % and was corrected before the verdict.

## 2. Kills (pre-registered; all PASS)

| Year | K1: recipe diff vs keeper `run_config_<Y>` | K2: unserved MWh, new vs keeper | K3: D-2 / C8 (closest to budget) |
|---|---|---|---|
| 2019 | exactly the 17 band keys | 0 vs 0 | pass (ST_GAS 0.178) |
| 2020 | exactly the 17 band keys | 0 vs 0 | pass (ST_GAS 0.239) |
| 2021 | exactly the 17 band keys | **0 vs 3,012.6** (keeper h1074–1079) | pass (ST_GAS 0.223) |
| 2022 | exactly the 17 band keys | 0 vs 0 | pass (ST_GAS **0.291** / 0.30) |
| 2023 | exactly the 17 band keys | 0 vs 0 | pass (CT_PEAKER **0.1499** / 0.15; immaterial at C8, < 2 % of load) |

C6 governance passes on the composite. The D-4 FAIL set equals the keeper's in every year, plus one new row in 2021, 2022 and 2023: `gas_commitment_bridge × CC_REGULAR`, plant 55223, h0-23, about 0.004 TWh per year. It is reported and not gated, the same class as the keeper's existing D-4 rows.

## 3. Every criterion-year at full magnitude (keeper → strip; only rows that move, plus 2023)

| Criterion | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|
| C3a mean LMP | +6.2 % → −6.4 % (PASS) | +2.5 % → +1.1 % (PASS) | +0.8 % → −5.3 % (PASS) | −8.4 % PASS → **−10.0 % FAIL** | −24.7 % → **−43.2 %** (R-6 caveat; $36.95 vs $65.02, IMM ≈ $35) |
| C3b NRMSE | 0.216 FAIL → **0.123 PASS** | 0.208 FAIL → **0.193 PASS** | 0.066 PASS → **0.229 FAIL** | 0.178 PASS → **0.204 FAIL** | 0.393 → **0.790** (R-6 caveat) |
| C3c tail h > $200 (actual) | 90 → 73 (106) PASS | 22 → 21 (56) caveat | 651 → 619 (258) caveat | 94 → 78 (196) caveat | 138 PASS → **44 FAIL** (181) |
| C1 fuel mix | FAIL unchanged (CC_REGULAR +9.0 TWh, COAL_PRB −10.9) | FAIL unchanged | PASS | PASS | PASS |

- C2, C4, C6 and C8 statuses are unchanged in every year, with class volumes moving by at most 0.5 TWh.
- 2024 and 2025 are identical on every criterion. 2024 C3a is −11.3 % FAIL in both.
- **2025 EIA-923 data-drift label applies** to the 2025 C1/C2 rows. They are unchanged here.

**Per scope** (`iso_determination`, worst-of):

| Scope | Keeper | Strip |
|---|---|---|
| forward 2024–25 | NOT-YET (C3a 2024) | NOT-YET (unchanged) |
| carve-out 2023 | CALIBRATED (R-6 caveats) | **NOT-YET (C3c 2023)** |
| validation 2019–22 | NOT-YET (C1, C3b) | NOT-YET (C1, C3a, C3b) |
| **ISO** | **NOT-YET** | **NOT-YET** |

Why the 2023 scope flips: in `calibration_verdict.py`, `_apply_c3c_standing_rule` (rule 22, lone-C3c auto-ledger) runs at line 4272, *before* `_apply_config_exceptions` (R-6) at line 4281. When the lone-failure test runs, 2023 C3a and C3b still read FAIL, so the C3c failure is not "lone" and stays a FAIL. Whether rule 22 should see through the R-6 caveats is a **rubric-order question for the owner** (closeout-C lane). It is not changed here.

## 4. What a promotion would have cost and carried (not executed — R-51)

- `promote_keeper.py` registers, attests, designates, folds and re-keys, then prunes the outgoing keeper's three stores (own ISO only).
- The ERCOT config partition is re-keyed by hand (W0 RESULT §5 item 5):
  - the carve-out-2023 and validation scopes now carry forward bands plus `swcap_clip`
  - the forward 2024–25 scope is unchanged
- The attestation gains an explicit `authorized_price_tuning` block reading **"none under the channel"** (W4). The ×33 bands were the only two-valued band set, and they are gone. ERCOT's `offer_curve_by_group` is now single-valued across the span except for `swcap_clip` and `ep_referenced`.
- The DOF ledger loses the 17 × 5 residual-identified ×33 band values.
- Retention under R-51: the probe registration is off main (E13). The leg branches stay alive until the owner's branch-cleanup pass.
- The new keeper commits `hourly/unit_marginal_<Y>.parquet` for every year. `unit_hourly` stays off main.
- Where things live today:
  - the composite is in this container only (`results/calibration/closeout_ercot_ecrs_span`, gitignored by local exclude)
  - the five strip legs are on their shard branches
  - the 2024/25 legs are on the l1b branches
  - re-composing is zero LP (§1)

## 5. Not done, named

- The ercot-255 `ercot_zonal_spread_ep_referenced` repair on 2023 is not folded in. It remains a separate item.
- The rule-22 / R-6 ordering question (§3) is left to the owner.
- No promotion has run (R-51).
- The rule-22 / R-6 ordering question goes to a separate rubric card (rule 37, its own PR).
