# RESULT closeout-CAISO-w3: 2021 own DSW clean depths + daily-shaped unprinted hub gas (2026-10-04)

**Records.** PRECOMMIT `PRECOMMIT-closeout-caiso-w3-own-depth-daily-shape-2026-10-04.md`, including Addendum A (G-DRIFT
clean, arm-scope fingerprint). Phase 0: `FINDING-closeout-caiso-w3-phase0-2026-10-04.md`.

**Runs.**
- Control: the w2 probe `2026-10-04-closeout-caiso-w2-unprinted` (keeper + R-63 arm; bundle
  `closeout_caiso_w2_a1_span`; registration on `claude/closeout-caiso-w2` @ `d292a159`).
- Arm: probe **`2026-10-04-closeout-caiso-w3-own`** (bundle `results/calibration/closeout_caiso_w3_a1_span`). It is
  the w2 recipe plus `caiso_dsw_clean_depth_own_year` plus `caiso_intertie_unprinted_daily_gas_shape`, and it is
  registered on `claude/closeout-caiso-w3` only (E13).

**Verdict: every kill rule clears; T1 is met; three fold FAILs flip to PASS. The probe beats the w2 probe on
structure and on gates.**
- Flips: C1 CC_REGULAR 2021, C4 gas 2020, C4 gas 2021.
- The determination stays **NOT-YET** on one gated FAIL, C1 CC_REGULAR 2020, at +5.00 TWh against a ±4.60 band
  (0.40 TWh over).

## Solves

Seven year-isolated shards, all pinned to `519dbd84dc2805193a1182d0101f67acb8ac231b`. Every leg was fetched,
extracted and verified before its shard was archived: parent `519dbd84`, 17 files including
`dispatch/<y>_P1.parquet`, and all three flags true.

The 2025 shard's worker restarted mid-P1. It re-ran the identical command at the same SHA, and the per-unit dispatch
it produced is byte-identical to the w2 2025 leg.

`_closeout_caiso_w1_compose_span.py` composed the legs: keeper + 3 arm fields, solve-surface fingerprint
`7293a431a6884d7d`, one source SHA.

| Year | Shard commit (provenance; branch `claude/closeout-caiso-w3-a1-<y>`) |
|---|---|
| 2019 | `61cbb6d233dd41eaa3ec48c7b76cb570ef94b0d2` |
| 2020 | `02a3554252e2280b0083d6f30cde67c398553fed` |
| 2021 | `0d0bf0fa835cab31e27a463613d8e9d103f0e908` |
| 2022 | `acd07317cce3c0edc1e34c28d3af950b8cb007f1` |
| 2023 | `85df2615e6548e33845a24ccbda3d07cf5b62ef4` |
| 2024 | `dcd9dd6f00a168d37c69ffba36318d0585b005fc` |
| 2025 | `108a9d3f9bbce76d151e30aa005b4068489b6cce` |

## Gate table (w2 probe → w3; every record that moved)

| Criterion | Year | w2 | w3 | Status |
|---|---|---|---|---|
| **C1 CC_REGULAR (T1)** | **2021** | +4.98 FAIL | **+3.47** | **FAIL → PASS** (band ±4.83) |
| C1 CC_REGULAR (T2) | 2020 | +5.39 FAIL | +5.00 | FAIL → FAIL (0.40 over ±4.60) |
| C1 CC_REGULAR (watch) | 2019 | −1.75 | −2.04 | PASS → PASS (band ±4.84) |
| **C4 gas r / NRMSE** | **2020** | 0.884 / 0.317 FAIL | **0.909 / 0.288** | **FAIL → PASS** |
| **C4 gas r / NRMSE** | **2021** | 0.877 / 0.321 FAIL | **0.894 / 0.294** | **FAIL → PASS** |
| C4 gas r / NRMSE | 2019 | 0.897 / 0.291 | 0.900 / 0.288 | PASS → PASS |
| C1 CT_PEAKER | 2019 / 20 / 21 | −1.46 / −2.06 / +2.06 | −1.53 / −1.91 / +1.63 | PASS |
| C1 CC_CHP / ST_GAS | 2019–21 | | moves ≤ 0.11 TWh | PASS |
| C2 gas | 2021 | C1 flags CC_REGULAR | "all classes in band" | PASS |
| C3a (covered window) | 2021 | +12.6 % | **+12.0 %** | improves |
| C3b NRMSE | 2021 | 0.147 | 0.141 | improves |
| C8 CC_REGULAR forced | 2019 / 20 / 21 | 11.3 / 8.6 / 7.3 % | 11.7 / 9.1 / 8.1 % | ≤ 30 % PASS |
| every record | 2022–2025 | | | **identical** |

The C3a 2021 and C3c rows read FAIL on both unattested probes at the same magnitudes. The R-40 / R-34 / C3c-2024
caveats enter through attestation, which `promote_keeper.py` carries forward (as in the w2 RESULT).

## DSW / PNW net import vs EIA-930 (TWh, model − measured)

| | DSW w2 → w3 | PNW w2 → w3 |
|---|--:|--:|
| 2019 | +0.99 → +1.17 | +7.22 → +7.35 |
| 2020 | −2.91 → −2.85 | +2.88 → +2.91 |
| 2021 | **−7.00 → −5.09** | +2.01 → +2.12 |

**2021 tranche change (TWh):** DSW_daytime_clean +1.04, DSW_surplus_clean +0.71, DSW_overnight_clean +0.30,
DSW_lateevening_clean +0.13, DSW_CCGT −0.26.

**Attribution:**
- L1 (2021 own depths) carries the 2021 move. The surplus and printed-hour daytime rungs are L1-only.
- L2 (daily gas shape) moved 2019 and 2020 only by ±0.1–0.4 TWh of CC, well below its first-order +1.5 / +2.1. The
  daily shape mostly re-times imports within the month, which is where C4 gains: 2020 NRMSE 0.317 → 0.288.

## Kill rules (PRECOMMIT §3)

| Kill | Result |
|---|---|
| K1 any C1 PASS→FAIL | **clear**; 2019 CC −2.04, inside ±4.84 |
| K2 \|DSW error\| grows by > 1.0 TWh in any fold year | **clear**: 2019 +0.18, 2020 −0.06, 2021 −1.91 |
| K3 C4 NRMSE worse by > 0.02 | **clear**: improves in all three |
| K4 C3a 2021 above +13.6 % / C3b above 0.157 | **clear** (+12.0 % / 0.141) |
| K5 any 2022–25 record moves | **clear**: per-unit dispatch byte-identical in 2022–25 |
| K6 C2 leaves band | **clear** |

**Targets:** T1 met (2021 C1 PASS). T2 missed by 0.40 TWh. T3 (C4 2020/21), reported and not claimed: both now PASS.

**Decision rule §4:** request a promotion slot. It supersedes the w2 probe's pending card, which this run stacks on.
The attestation declares L1 and L2 as rule-14 measured inputs alongside the R-63 ruling-authorised transfer.

## DOF / retrievability

- **DOF:** zero fitted parameters.
- **Bundles:**
  - The span `results/calibration/closeout_caiso_w3_a1_span` and the seven legs are local and gitignored.
  - Their bytes are in the shard commits above.
  - A promotion needs **no re-solve**: re-compose from the leg SHAs, then run `promote_keeper.py`.
- **Registration:** sidecar and payload are on `claude/closeout-caiso-w3` only.
