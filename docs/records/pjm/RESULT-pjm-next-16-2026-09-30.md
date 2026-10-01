# RESULT — PJM-NEXT-16: OVEC fleet boundary PROMOTED; PJM CC commitment bridge REJECTED

**Keeper:** `2026-09-28-pjm-next8-exitfix` → **`2026-09-30-pjm-next16-ovec`** (bundle `pjmnext16_A_span`, 2019–2025).
- Owner card: *"Promote A (Recommended)"*.
- Determination: run-level NOT-YET, training tier 2023–2025 NOT-YET, ISO (v3.13) NOT-YET.

**Records:**
- `docs/records/pjm/FINDING-pjm-next-16-cc-loading-and-the-ovec-boundary-2026-09-30.md` (cards 1/1b, zero LP)
- `docs/records/pjm/PRECOMMIT-pjm-next-16-2026-09-30.md` (arms, predictions, decision rule, G-DRIFT, two B re-pins)

**Solves:** 14 year-isolated shards (rule 36). The parent ran zero LP.
- Arm A: pin `6d4c7749`.
- Arm B: pin `42e87bcd`, after the §6 and §7 re-pins.

## 1. Arm A — OVEC (`ISO_BA_JOINS["PJM"] = {"OVEC": (2019, 1)}`) — PROMOTED

Every mechanism prediction held:

| | pre-registered | measured |
|---|---|---|
| OVEC model gen 2019 / 2020 (actual 11.24 / 9.03 TWh) | 9–14 / 8–13 | **12.67 / 11.86** |
| C1 CC_REGULAR 2019 (keeper +10.86) | +5 to +8, PASS | **+6.27 PASS** |
| C1 CC_REGULAR 2020 (keeper +14.08) | +9 to +12, FAIL | **+9.84 FAIL** |
| C1 COAL_BIT 2019 (keeper +10.61) | +15 to +20 | **+18.71** |
| C1 COAL_BIT 2020 (keeper +3.91) | +8 to +12, new FAIL | **+11.92 new FAIL** |
| 2021–2025 | identical | **byte-identical class energy** (A2025 vs keeper: zero class deltas) |
| C3a 2019 / 2020 (keeper +11.8 / +15.9 %) | −0.5 to −2 pts | **+5.8 % PASS / +12.4 %** — a larger drop than predicted |

- The C3a miss of the prediction is reported, not explained away. OVEC's ~12 TWh of $20s coal displaced more marginal CC/CT hours than the keeper's average displacement shares implied.
- Run-level failing cells: **11 → 10**. Training span unchanged.

## 2. Arm B — `pjm_gas_commitment_bridge` replacing `cc_mustrun_per_plant` — REJECTED

The decision rule fixed in advance was: B is a keeper candidate only if B1 and B3 hold. **B1 fails.**

CC plant-hour partition, model minus CAMPD, TWh. The census is `_pjmnext16_cc_loading.py` on each run's payload.

| year | ON keeper → B (model on, real off) | OFF keeper → B (real on, model off) | LOAD keeper → B |
|---|---|---|---|
| 2019 | 8.49 → 8.12 | −5.49 → **−23.69** | 7.99 → 11.11 |
| 2020 | 10.25 → 9.72 | −5.08 → **−18.92** | 8.95 → 12.12 |
| 2021 | 10.13 → 10.30 | −7.64 → **−20.81** | −1.52 → 3.02 |
| 2022 | 10.40 → 9.91 | −6.41 → **−17.06** | 7.33 → 10.67 |
| 2023 | 9.80 → 10.38 | −5.97 → **−29.94** | 4.47 → 10.83 |
| 2024 | 7.78 → 7.00 | −4.67 → **−11.76** | −3.68 → −1.91 |
| 2025 | 6.76 → 5.77 | −6.81 → **−17.41** | −7.83 → −1.72 |

- **B1:** the error the bridge targeted (ON) does not move.
- Removing `cc_mustrun_per_plant` instead drops real-on CC plant-hours 2.5–5×, and loads the units that stay on harder.
- The CC_REGULAR C1 passes B buys (2019/2020/2022) come from concentration, not from better placement.
- **B3:** the window-level D-4 check passes, and C8 forcing is 0.39–2.04 TWh/yr (0.2–0.8 % of class energy). But the per-unit conduct rider fails on **51 plant-years (0.90 TWh)**, against the keeper's 19 (0.23 TWh): the P0 run pattern floors units whose meters read offline.
- **Gates:**
  - 12 failing cells vs the keeper's 11.
  - COAL_BIT is worse in every year (2019 +26.4, 2020 +16.2, 2021 +22.5, 2022 +10.8).
  - 2023 breaks: CC −8.49, C3a +11.6 %, C3b 0.236.
- **Reading:** `cc_mustrun_per_plant` is holding real commitment. The rule-17 window question stays OPEN, for a plant-conduct construction rather than a P0-pattern one.

## 3. What remains (all OPEN, none called a model-class limit)

| row | value (new keeper) | note |
|---|---|---|
| C1 COAL_BIT 2019 / 2020 / 2021 | +18.71 / +11.92 / +17.14 | Now flat across 2019–2021 with OVEC counted. The NEXT-11 audit says it is RESPONSE, not price; the next lane works the night coal/CC ordering and coal's ladder vs replacement cost. |
| C1 CC_REGULAR 2020 / 2022 / 2023 | +9.84 / +10.94 / +8.48 | Loading shape (night/low load), FINDING card 1. 2023 is the training-span blocker. |
| C1 CT_PEAKER 2021 | −9.59 | Unchanged. |
| C3a 2020 / 2022 | +12.4 % / −11.5 % | |
| C3b 2022 | 0.253 | |
| C3c 2019 / 2021 / 2022 | caveat | |

## 4. Retrievability (rule 34(e))

- The keeper bundle `results/calibration/pjmnext16_A_span` is on `main` with its registry sidecar and payload.
- The per-year leg dirs are gitignored. The arm B composite was pruned at promotion (rule 35; owner ruled on promotion, B declined), and its numbers are this doc.
- Recovering B costs a 7-shard re-solve (~35 min per shard).
- Leg provenance SHAs, not recovery routes: B 2023 `09b96225`, A 2025 `843493f7`; the rest are in the lane's shard ledger.
