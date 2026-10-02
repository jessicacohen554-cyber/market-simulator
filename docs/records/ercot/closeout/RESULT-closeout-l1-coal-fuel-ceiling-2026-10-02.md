# RESULT: ERCOT L1, coal fuel-delivery ceiling (ceiling-only monthly coal pile, measured EIA-923 receipts)

Lane `closeout-ERCOT`, plan §3.5 step 1. PRECOMMIT `PRECOMMIT-closeout-l1-coal-fuel-ceiling-2026-10-02.md`; pre-launch ADDENDUM `ADDENDUM-closeout-l1-preflight-w0-2026-10-02.md` (written before any shard).

- **Control** (rule 29): the W0 keeper `2026-10-02-w0-settlement` (`results/calibration/w0_ercot_span`).
- **Arm:** run `2026-10-02-closeout-l1-coal-fuel`, bundle `results/calibration/closeout_ercot_l1_span`, 2019–2025, solved at `106d6bb737488f4086151907b4dbc4a45ee17306`, one year-isolated shard per year (rule 36).
- **Scorecard:** `data/l1_scorecard.json`, produced by `scripts/probes/_r_ercot24_scorecard.py` (span-restricted `calibration_verdict` per year).

## 1. Headline

**ISO determination: NOT-YET → NOT-YET.** Two more years now read CALIBRATED, and no year or criterion worsens:

- **2022: NOT-YET → CALIBRATED.** C1 fuel-mix FAIL → PASS: CC_REGULAR **−10.12 → −3.47 TWh**, COAL_PRB +5.79 → −1.38.
- **2025: NOT-YET → CALIBRATED.** C3a price-mean FAIL → PASS: **−10.0 % → −9.2 %**; COAL_PRB +3.53 → +0.87.

The ISO stays NOT-YET on 2019/2020 (coal conduct, DATA-LIMITED; FINDING §5 draft ledger row) and 2024 (C3a −11.3 %, West basis + ECRS; FINDING §2).

## 2. Per year (keeper → arm, P1)

| Year | Det. | C3a | C3b | C1 CC_REG | C1 COAL_PRB | C1 COAL_LIG | LW $/MWh | slack MWh | h > $1k |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | NOT-YET (=) | +6.1 → +6.2 % | 0.216 (=) | +8.81 → +9.21 F | −10.50 → −10.79 F | −0.33 → −0.48 | 49.37 → 49.41 | 0 | 30 |
| 2020 | NOT-YET (=) | +2.5 % (=) | 0.208 (=) | +10.17 F (=) | −11.85 F (=) | −1.16 (=) | 26.03 | 0 | 3 |
| 2021 | CAL (=) | +0.6 → +0.8 % | 0.066 | −1.94 → −0.83 | −1.67 → −2.01 | +0.48 → −0.44 | 167.02 → 167.20 | 3,012.6 (=) | 112 |
| **2022** | **NOT-YET → CAL** | −10.0 → **−8.4 %** | 0.182 → 0.178 | **−10.12 F → −3.47** | +5.79 → −1.38 | +0.61 → +0.13 | 67.59 → 68.76 | 0 | 17 |
| 2023 (carve-out) | CAL (=) | −24.8 → −24.7 % (caveat, R-6) | 0.393 | +0.66 → +1.38 | −2.17 → −2.47 | +1.40 → +0.90 | 48.89 → 48.98 | 0 | 31 |
| 2024 | NOT-YET (=) | −11.4 → −11.3 % F | 0.198 | −4.63 → −4.45 | −1.04 → −0.97 | +1.24 → +0.96 | 27.63 → 27.65 | 0 | 0 |
| **2025** | **NOT-YET → CAL** | **−10.0 F → −9.2 %** | 0.132 → 0.125 | skip (EIA-923 vintage) | +3.53 → +0.87 | +0.69 → +0.43 | 32.84 → 33.13 | 0 | 0 |

Criterion moves, all improvements (`calibration_verdict --years Y` on both bundles): 2022 `fuelmix` FAIL → PASS; 2025 `price_mean` FAIL → PASS. No other criterion changes status in any year.

## 3. Kill rules (PRECOMMIT §5)

| Rule | Result |
|---|---|
| **K1** 2022 CC_REGULAR inside ±8.0 | **PASS** (−3.47 TWh) |
| **K2** binding only where the census showed excess | **Tripped on its literal terms, then diagnosed: not a construction bug.** J K Spruce 2022 drops 0.30 TWh and Sandy Creek 2022 drops 1.09 TWh against a census excess of 0 and 0.31. A fleet-only rebuild shows every one of those yard rows binding at exactly its measured MMBtu envelope (`max cum burn / ceiling` 1.00). The census converted fuel to MWh with **EIA-923 plant heat rates** (Spruce 9.97, Sandy Creek 9.40 MMBtu/MWh); the LP rows use the **model's own unit heat rates** (≈ 11.5 / 11.7), so the same tons fund 13–20 % fewer MWh in the LP. The mirror case: Oak Grove 2024 (census excess 0.67) does not bind, because its LP rate (10.39) is below EIA's (11.36). The ceiling is in MMBtu and is right; the census's MWh conversion was the approximation. Separate finding routed below (§6) |
| **K3** no manufactured scarcity | **PASS** (slack 2021 3,012.6 MWh = keeper; every other year 0; hours above $1k unchanged) |
| **K4** no new legitimacy family | **PASS** (D-4 FAIL 114 → 115 rows, all inside existing families: +2 rows 2025 `gas_commitment_bridge × CC_REGULAR` at plants 55123/55226, −1 row 2021 at 55062; D-1/D-2/D-5/D-9/D-10 unchanged) |
| **K5** no determination or criterion worsens | **PASS** (two improve, none worsen) |
| **K6** 2025 basis | Measured 2025 Page 5 receipts on 9 yards; Sandy Creek (no 2025 receipts) on the prior-years ratable profile |

## 4. Predictions (PRECOMMIT §4 / ADDENDUM §1) vs measured

| Quantity | Predicted | Measured | |
|---|---|---|---|
| 2022 C1 CC_REGULAR | −4 to −6 TWh | **−3.47** | miss, on the favourable side |
| 2022 C1 COAL_PRB | ≈ 0 to +1 | −1.38 | miss: more PRB removed (heat-rate basis, K2) |
| 2022 C3a | −6 to −8 % | −8.4 % | narrow miss |
| 2019 C1 COAL_PRB | −10.5 to −10.8 | −10.79 | hit |
| 2021 PRB / LIG / determination | ≈ −2.2 / ≈ −0.1 / CAL | −2.01 / −0.44 / CAL | hit / miss / hit |
| 2023 LIG / PRB / C3a, C3b within 1 pt | ≈ +0.5 / ≈ −2.4 / yes | +0.90 / −2.47 / yes | miss / hit / hit |
| 2024 LIG / PRB unchanged / C3a ±0.5 pt | ≈ +0.2 / yes / yes | +0.96 / yes (+0.07) / yes (+0.1) | miss (Oak Grove slack in the LP, K2) / hit / hit |
| 2025 COAL_PRB / C3a up 0–1.5 pt | +1.0 to +2.0 / yes | +0.87 / +0.8 pt | narrow miss / hit |
| VOLL slack | unchanged | unchanged | hit |

Every miss traces to the same cause, the census-versus-LP heat-rate basis.

## 5. Recipe fidelity (desk check)

Each of the seven legs' `scenario_config` differs from the keeper's `run_config_<Y>.json` in **exactly** the three arm flags (`coal_fuel_inventory_plant_grain`, `coal_fuel_inventory_monthly_pile`, `coal_monthly_pile_measured_receipts`).

- **First round.** It replayed the W0 keeper's pre-fix `meta.json`, which carried no partition overlay, so 2020–2024 solved a validation-partition recipe. Those legs were rejected and re-solved as `closeout-ercot-l1b-<Y>`, with the partition keys pinned by explicit `--set`. The 2019 leg was exact and kept.
- **Composed `meta.json`.** Its base recipe is the fixed W0 keeper meta (main `089fca2c`) plus the three arm flags. `config_partition_overrides` is stamped from the legs (`stamp_config_partition --check` OK).
- **Replay guard.** `promote_keeper`'s replay-recipe preflight (step 0d) passes. That needed one infrastructure fix: `scripts/lib/replay_recipe.py` now applies `replay_keeper`'s rule-26 deletion registry to the recorded side. Without it, every bundle solved before `35ad0046` failed on the deleted `unit_outage_dispatched_bin_live_denominator`, including the W0 keeper itself. Tests were added.

## 6. Routed, not fixed

- **Coal heat-rate basis.** The model's coal unit heat rates exceed EIA-923 plant heat rates at Spruce (11.5 vs 9.97) and Sandy Creek (11.7 vs 9.40), and fall below them at Oak Grove (10.39 vs 11.36). With a fuel ceiling armed, a heat-rate error now carries straight into coal MWh. This is a measured-input question for the `measured_coal_heat_rates` derivation, not for L1.
- **Ledger.** 2019/2020 coal conduct stays a DRAFT DATA-LIMITED row (FINDING §5). 2024 C3a stays routed (FINDING §2, L2 closed).

## 7. Promotion status

**The promotion command was BLOCKED by this session's permission classifier.** `promote_keeper.py` re-points the keeper and prunes the outgoing W0 keeper's stores, which the classifier treats as modifying shared resources. Everything up to that step is done:

- the dry-run preflight passes (steps 0–1, including the replay guard);
- the run is registered;
- the scorecard and this record are written.

The command, unchanged, for the owner or desk:

```
uv run python scripts/promote_keeper.py --iso ERCOT --bundle results/calibration/closeout_ercot_l1_span --label "closeout-L1 coal fuel ceiling (ERCOT ceiling-only coal pile, measured EIA-923 receipts) on W0 keeper"
```

The composed bundle lives only in this session's container until promotion commits it (gitignored until `promote_keeper` designates it).

Where the legs are (rule 34; provenance only):

| Year | Branch | SHA |
|---|---|---|
| 2019 | `claude/closeout-ercot-l1-2019` | `f4e5be977e248eee26a2f513dec73ce3b0eac3c9` |
| 2020 | `claude/closeout-ercot-l1b-2020` | `199c5d82784732339ddb82edb0e5ef9067c1097a` |
| 2021 | `claude/closeout-ercot-l1b-2021` | `211c34cb8319e41f54d6400a2ea2af38474eae48` |
| 2022 | `claude/closeout-ercot-l1b-2022` | `cacafbfd6bb4bd4bbcfac793708e30d078ee351e` |
| 2023 | `claude/closeout-ercot-l1b-2023` | `2e5d93a24222e75b04b802ddff85b945de1699ca` |
| 2024 | `claude/closeout-ercot-l1b-2024` | `e8a29b96e6e32381e1f50fe5d7404f2390dea998` |
| 2025 | `claude/closeout-ercot-l1b-2025` | `86ce1db50bb40e7eec3ccfd13eae63db6cfd2437` |

Re-composing from them is zero LP:

1. Run `_r_ercot_compose_span.py --side arm --chp-off` with the seven legs.
2. Drop the ten partition-pinning keys from `meta.json`'s `coal_prb_sigmoid_overrides`.
3. Run `stamp_config_partition` (with `--check`).
4. Copy the attestation.

The wrong-recipe first-round legs (`claude/closeout-ercot-l1-2020…2024`, `-2023`) are evidence of the replay defect only, never a promotion basis. All 13 shards are archived.
