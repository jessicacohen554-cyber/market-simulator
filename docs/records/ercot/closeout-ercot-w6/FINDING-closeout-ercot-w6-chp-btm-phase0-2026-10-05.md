# FINDING closeout-ERCOT-w6 (ZERO LP): the measured ERCOT CHP behind-the-meter share, phase 0 (2026-10-05)

**Lane** `closeout-ercot-w6`, chartered by the backcast close-out desk (session_01ERkBTm23ZAP4CTZnJVD9Ss) from the
transfer census (`docs/records/governance/closeout-2026-10/FINDING-closeout-chp-transfer-2026-10-05.md`, rank 1).
Owner direction: "There are definitely uncalibrated ISOs that should be being rerun and tested." ERCOT is NOT-YET.
No LP was solved in this session.

- **Keeper.** `2026-10-02-closeout-l1-coal-fuel` (bundle `results/calibration/closeout_ercot_l1_span`, all seven legs at
  `106d6bb737488f4086151907b4dbc4a45ee17306`, a per-year composite recipe).
- **Artifact.** `data/raw/_processed-legacy/chp_btm_share_measured_ERCOT.csv`, written by
  `scripts/data/derive_ercot_chp_btm_share.py`, which calls `derive_caiso_chp_btm_share.derive` unchanged with plant
  scope EIA-860 BA = ERCO (669 filers; every ERCOT CHP bin but one carries a row — 41 of 42 in 2019, 43 of 44 in 2023; Robert Mueller 56374 keeps the default).
- **Probes.** The census probe `scripts/probes/_closeout_chp_transfer_census.py --isos ERCOT` re-run here against the
  keeper bundle reproduces the committed `_closeout_chp_transfer_census.json` ERCOT block **byte-identically** (all seven
  years). The static C1 arms are `_closeout_chp_transfer_score.json`.

## 1. Census numbers, confirmed on the keeper bundle

| Year | CHP net (923, TWh) | BTM default → measured | dE bench (CC_CHP / CT_CHP) | model reach A1 (CC_CHP / CT_CHP) | static CC_REGULAR displaced |
|---|--:|---|---|---|--:|
| 2019 | 38.67 | 14.92 → 10.78 | +4.14 (+4.99 / −0.85) | +3.53 (+4.74 / −1.21) | 1.70 |
| 2020 | 39.08 | 15.07 → 11.18 | +3.89 (+4.98 / −1.09) | +3.00 (+4.71 / −1.71) | 1.41 |
| 2021 | 40.06 | 16.14 → 12.06 | +4.08 (+4.65 / −0.57) | +3.96 (+5.10 / −1.14) | 2.31 |
| 2022 | 37.30 | 15.08 → 10.68 | +4.39 (+4.80 / −0.41) | +4.04 (+5.35 / −1.30) | 2.27 |
| 2023 | 40.86 | 16.30 → 11.45 | +4.86 (+5.10 / −0.25) | +4.01 (+5.01 / −1.00) | 1.80 |
| 2024 | 44.53 | 17.67 → 12.53 | +5.14 (+5.55 / −0.41) | +4.30 (+5.52 / −1.22) | 1.51 |
| 2025 | 42.87 | 17.11 → 12.03 | +5.08 (+5.55 / −0.46) | +4.02 (+5.31 / −1.29) | 1.54 |

**Movers (default → measured, %).**
- Down (more grid): Deer Park 55464 35 → 2.9, Pasadena 55047 35 → 0.0, Texas City 52088 35 → 3.0, C R Wing 52176 35 → 2.7,
  Altura 50815 35 → 18.4, Ingleside 55313 70 → 3.1, Bayou 10298 70 → 37.7.
- Up (less grid): Sweeny 55015 35 → 84.9, Oyster Creek 54676 35 → 94.1, Formosa 10554 70 → 98.1, Freeport 52120 70 → 100.

**Fold test (SOCO-60).** EIA-930 ERCO gas minus the EIA-923 gas FULL of member plants is −32.9 / −36.6 / −32.9 / −32.3 /
−36.4 / −40.2 / −40.1 TWh (2019–2025) against a fold F of 2.43 / 1.36 / 2.13 / 1.93 / 1.25 / 0.17 / 1.10 TWh: no room for a
fold in any year. **REFUTED**, the same reading as SOCO, CAISO (R-33) and MISO (w3e).

## 2. The three bench bases (static, census method)

Reconcile = `reconcile_vintage_classes` (deadband 0.97). Ratio = family / target.

| Year | (a) original: ratio, fires? | (b) measured share: ratio, fires? scale | (c) reconciled (measured + ERCOT fold refuted): ratio, fires? |
|---|---|---|---|
| 2019 | 1.014, no | 1.0303, **no (margin 0.16 TWh)** | 1.021, no |
| 2020 | 1.024, no | 1.040, **yes ×0.962** | 1.034, **yes** |
| 2021 | 1.014, no | 1.031, **yes ×0.970** | 1.022, no |
| 2022 | 1.014, no | 1.032, **yes ×0.969** | 1.024, no |
| 2023 | 1.015, no | 1.034, **yes ×0.968** | 1.029, no |
| 2024 | 1.023, no | 1.043, **yes ×0.959** | 1.042, **yes** |
| 2025 | 1.027, no | 1.046, **yes ×0.956** | 1.042, **yes** |

Basis (b) is the cancelling-error pattern MISO-w3e named: the sector default's ~4–5 TWh of phantom host supply was what
kept the deflated target inside the deadband. The fold refutation cures 2021–23; in 2020/24/25 the measured-share family
exceeds even raw 930 by 3.4–4.2 %, and the reconcile scales ERCOT fossil ≈ ×0.96–0.97 on both (b) and (c).

## 3. Keeper C1 flip table on each basis (static; FAIL records and every CC/CHP/COAL_PRB record)

Miss in TWh (band ±8.0 on every ERCOT record; share leg ≤ 3 pp). M = basis (b) bench, keeper dispatch unchanged.
A1 = basis (b) + the run's measured carve. A1r = basis (c) + the carve (the headline).

| Record | (a) keeper | (b) M (bench only) | (b) A1 | (c) R (bench only) | (c) A1r (headline) |
|---|---|---|---|---|---|
| **CC_REGULAR 2019** | +9.21 FAIL | +9.21 FAIL | +7.51 PASS | +9.21 FAIL | **+7.51 PASS** (share +2.27) |
| CC_REGULAR 2020 | +10.17 FAIL | +15.07 FAIL | +13.65 FAIL | +10.17 FAIL | +12.95 FAIL (share +3.87) |
| COAL_PRB 2019 | −10.79 FAIL | −10.79 FAIL | −11.74 FAIL | −10.79 FAIL | −11.74 FAIL |
| COAL_PRB 2020 | −11.85 FAIL | −9.91 FAIL | −10.63 FAIL | −11.85 FAIL | −10.90 FAIL |
| CC_REGULAR 2021 / 22 / 23 / 24 | −0.83 / −3.47 / +1.38 / −4.45 | +2.64 / +0.65 / +6.15 / +1.68 | +0.33 / −1.63 / +4.35 / +0.18 | unchanged | −3.14 / −5.75 / −0.42 / +0.09 |
| CC_CHP 2019 … 2024 | −1.54 / −2.30 / +0.53 / +1.41 / −2.23 / −1.40 | −6.53 / −6.01 / −3.16 / −2.45 / −6.24 / −5.48 | −1.79 / −1.31 / +1.94 / +2.89 / −1.23 / +0.04 | unchanged | −1.79 / −1.49 / +0.98 / +1.96 / −2.32 / +0.02 |
| COAL_PRB 2021 … 2025 | −2.01 / −1.38 / −2.47 / −0.97 / +0.87 | −0.26 / +0.28 / −0.99 / +0.83 / +2.97 | −0.59 / 0.00 / −1.59 / +0.22 / +2.72 | unchanged | −2.35 / −1.66 / −3.08 / +0.20 / +2.53 |

| Basis | C1 FAILs (keeper 4) | FAIL→PASS | PASS→FAIL |
|---|--:|---|---|
| (a) original, keeper | 4 | — | — |
| (b) M, keeper dispatch | 4 | none | none |
| (b) A1 | 3 | CC_REGULAR 2019 | none |
| (c) R, keeper dispatch | 4 | none | none |
| (c) A1r | 3 | CC_REGULAR 2019 | none |

**Basis (c) on the keeper alone changes no ERCOT C1 status** (R = original in every record), so the reconciled bench is
safe to score on and the T1 gain is the carve's. The +1 needs the LP to realise ≥ 1.21 of the static 1.70 TWh CC_REGULAR
displacement in 2019 (≥ 71 %).

## 4. Rule 19 and the export floor

ERCOT's keeper arms `chp_export_floor_measured`: floor = min(100, 923 class CF) × (1 − btm) × LP nameplate
(`data/fleet/assembly.py`, the formula is basis-consistent per the floor-basis FINDING §1). The measured share is the
`btm` of that formula, so the floor follows the share: one share, its existing readers (carve, floor, add-back, bench
subtrahend), no second floor and no new formula. It also raises realisation: the floored CHP energy is the measured
923 total × the measured grid share, so most of the static reach is floor-bound rather than economic.

**Floor multiplier (1 − measured)/(1 − default) on the plants the keeper's D-4 `chp_steam` rider tests.**

| Plant | floor × | keeper D-4 conduct (zero-share max; FAILs) |
|---|--:|---|
| Pasadena 55047 | 1.54 | 0.10; 0 |
| Deer Park 55464 | 1.49 | 0.004; 0 |
| Texas City 52088 | 1.49 | 0.017; 0 |
| **C R Wing 52176** | **1.50** | **1.00; FAIL 2020–23, 2025 (5 of 6 rows); 2019 passes at zero-share 0.44** |
| Altura 50815 | 1.26 | 0.013; 0 |
| Corpus Christi 55206 | 1.21 | 0.090; 0 |
| Channel 55299 | 1.17 | 0.032; 0 |
| Bayou 10298 | 2.08 | 0.107; 0 |
| Baytown 55327 / Channelview 55187 / Sweeny 55015 | 0.87 / 0.81 / 0.23 | 0; 0 |
| Petra Nova 58378 | n/a (own branch, not carved) | 0.74; FAIL 3 |

Ingleside 55313 (×3.23) and Victoria 10790 (×1.44) carry no keeper D-4 row (their floors do not bind today).
**Named ex-ante D-4 risk:** C R Wing 52176 2019. Every other floored host with a rising floor is metered on (median > 0)
in ≥ 89 % of its keeper binding hours.

## 5. What static cannot say

- Realisation (the MISO w3f carve realised ≈ 40 % of static on its declared class; CAISO w6 realised ≈ 55 % on
  CC_REGULAR). ERCOT's floor-bound share should realise higher, but the +1 is fragile.
- 2019 on basis (b) sits 0.16 TWh inside the upper deadband: a solved CHP rise above the bench's dE could fire it.
  Basis (c) has 1.0 TWh of margin.
- C3a/C3b (price) are not estimated. The carve adds near-zero-offer floored CHP in Houston; the 2019/20 C3b FAILs could
  move either way.
- The renderer's per-plant BTM fields stay on the sector default (the CAISO-w6 held render leg,
  `docs/records/caiso/closeout-caiso-w6/_render_leg_pending.patch`, covers NYISO/CAISO only and is a payload-source edit).
  C1 reads `btm.parquet`'s `btm_bench_twh`, so no C1 cell depends on it.

## Addendum — exact zero-LP bench on the three bases (supersedes the static §2/§3 reconcile estimate)

Bench parts rebuilt for all seven years by `scripts/data/build_bench_part_zero_lp.py` on the keeper's own recipe:
- basis (b) = the artifact present;
- basis (c) = (b) + `_bench_basis_reconciled.patch`.

The keeper was re-scored by `calibration_verdict.py` on each set. The committed parts were then restored, and **no bench
part was committed**.

**classFull actuals, TWh, (a) → (b) / (c).**

| Year | CC_CHP | CT_CHP | CC_REGULAR | COAL_PRB |
|---|---|---|---|---|
| 2019 | 28.60 → 31.57 / 31.57 | 4.49 → 2.22 / 2.22 | 132.20 unchanged | 61.30 unchanged |
| 2020 | 28.34 → 31.42 / 31.42 | 5.39 → 2.56 / 2.56 | 127.84 unchanged | 50.70 unchanged |
| 2021 | 27.13 → 29.95 / 29.95 | 6.13 → 3.86 / 3.86 | unchanged | unchanged |
| 2022 | 25.65 → 28.76 / 28.76 | 5.83 → 3.84 / 3.84 | unchanged | unchanged |
| 2023 | 28.51 → 31.47 / 31.47 | 5.61 → 3.63 / 3.63 | unchanged | unchanged |
| 2024 | 30.03 → 33.74 / 33.74 | 5.66 → 3.58 / 3.58 | unchanged | unchanged |
| 2025 | 29.07 → 31.68 / 32.71 | 5.65 → 3.44 / 3.55 | 148.06 → **143.38** / 148.06 | 47.68 → **46.18** / 47.68 |

**Corrections to the static estimate.**
- **Bench dE.** The exact net CHP dE is +0.7 to +1.5 TWh (CC_CHP +2.8 to +3.7, CT_CHP −2.0 to −2.8), not +3.9 to +5.1.
  The census undercounted the CT_CHP hosts that self-supply (Sweeny 55015 is CT_CHP in the bins; 35 % → 85 %).
- **Reconcile on (b).** It fires in **2025 only** (×0.968 on every fossil class; the preliminary-vintage year), not
  2020–25.
- **Reconcile on (c).** It fires **in no year**.

**Keeper re-scored, C1/C3a/C3b status.**

| | (a) | (b) | (c) |
|---|---|---|---|
| C1 FAILs | 4 | 4 | 4 |
| C1 records that move | — | CC_CHP misses only (2019 −1.54 → −4.51, 2024 −1.40 → −5.12); COAL_PRB 2025 +0.87 → +2.37 | CC_CHP only |
| C1 status flips | — | 0 | 0 |
| C3a / C3b | — | unchanged | unchanged |
| Determination | NOT-YET | NOT-YET | NOT-YET |

**T1 arithmetic is unchanged.** CC_REGULAR 2019 actual = 132.20 on every basis, so T1 needs the solved CC_REGULAR to
fall ≥ 1.21 TWh.

**The control.** The keeper on bases (b) and (c) is the control row for the RESULT (`keeper_three_bases.txt`, the lane
scratch, reproduced in the RESULT).
