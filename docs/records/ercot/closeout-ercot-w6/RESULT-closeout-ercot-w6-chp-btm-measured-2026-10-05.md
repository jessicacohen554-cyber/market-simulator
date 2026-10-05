# RESULT closeout-ERCOT-w6: measured ERCOT CHP behind-the-meter share (2026-10-05)

**Verdict: T1 MISSED; K3 TRIPPED (C3b 2024 PASS → FAIL by 0.001 NRMSE); K1, K2, K4, K5 clear. NOT PROMOTED; lane stands down
(PRECOMMIT §4 decision rule).** ERCOT stays NOT-YET on every basis.

**Records.** `PRECOMMIT-closeout-ercot-w6-chp-btm-measured-2026-10-05.md` (bars, kills, G-DRIFT, launch table) and
`FINDING-closeout-ercot-w6-chp-btm-phase0-2026-10-05.md` (phase 0 and the exact zero-LP bench addendum).

**Run.** Probe **`2026-10-02-closeout-w6-chp-btm`** (the run id takes the keeper's meta date). Bundle
`results/calibration/closeout_ercot_w6_span`, composed by `scripts/probes/_closeout_ercot_w6_compose_span.py` from seven
year-isolated legs. Every leg:
- is pinned at `60e11319cc500262ef3bb21290a377777c6bfe7e`;
- runs the keeper recipe with only `ercot_chp_btm_measured=true`, checked per leg against the keeper's run_config;
- has unserved energy 0, except 2021 (2,394 MWh against the keeper's 3,013, Uri).

Registration is on branch `claude/closeout-ercot-w6-probe` only (E13).

| Year | Leg commit (provenance; branch `claude/closeout-ercot-w6-<y>`) | Files |
|---|---|--:|
| 2019 | `43dc4499dc9237443576569aabb893463f770461` | 19 |
| 2020 | `0598a9a96697636ea74b75aeeab089c149a64038` | 19 |
| 2021 | `a2f1d328e6d575470e0c016ea4bf57cb523b8a12` | 19 |
| 2022 | `6d09ba6518d7a28a622f1eda926a037dbd9946ae` | 19 |
| 2023 | `00e40b06bc264e8d67ce82018817bf54760fd3f7` | 19 |
| 2024 | `ecbb71e6c246ce53f6d07eefd528db87d9431c08` | 19 |
| 2025 | `c66eb1d73eb7b789244a1a1b792877bb1a2f6dcc` | 19 |

**Bench check.** The registration render's `classFull` equals the zero-LP basis-(b) parts byte-for-value in all seven
years. That validates `build_bench_part_zero_lp.py` as the basis-(b)/(c) source.

## 1. Gate table — arm vs keeper, each on the same basis

Headline basis (c) = reconciled. (a) = original; (b) = measured share. C1 misses are in TWh against a band of ±8.00.

| Criterion | Year | Keeper (a) | Arm (a) | Keeper (c) | **Arm (c)** | Status on (c) |
|---|---|---|---|---|---|---|
| **C1 CC_REGULAR (T1)** | **2019** | +9.21 | +9.12 | +9.21 | **+9.12** | **FAIL → FAIL (T1 missed; needed ≤ 8.00)** |
| C1 CC_REGULAR | 2020 | +10.17 | +10.49 | +10.17 | +10.49 | FAIL → FAIL (worse by 0.32) |
| C1 CC_REGULAR | 2021 / 22 / 23 / 24 | −0.83 / −3.47 / +1.38 / −4.45 | −1.14 / −3.77 / +1.15 / −4.74 | same as (a) | same as (a) | PASS |
| C1 COAL_PRB | 2019 / 2020 | −10.79 / −11.85 | −10.87 / −11.68 | same | same | FAIL → FAIL |
| C1 CC_CHP | 2019 … 2024 | −1.54 / −2.30 / +0.53 / +1.41 / −2.23 / −1.40 | +1.72 / +0.96 / +4.28 / +5.26 / +1.27 / +2.56 | −4.51 / −5.38 / −2.28 / −1.70 / −5.19 / −5.12 | **−1.25 / −2.12 / +1.47 / +2.14 / −1.69 / −1.15** | PASS. On (c) the arm is closer to actual than the keeper in every year. |
| **C3b price shape** | **2019** | 0.216 | **0.173** | 0.216 | **0.173** | **FAIL → PASS** |
| C3b | 2020 | 0.208 | 0.202 | 0.208 | 0.202 | FAIL → FAIL (improves) |
| **C3b** | **2024** | 0.198 | **0.201** | 0.198 | **0.201** | **PASS → FAIL (K3)** |
| C3b | 2021 / 22 / 25 | 0.066 / 0.178 / 0.125 | 0.065 / 0.189 / 0.127 | same | same | PASS |
| C3b | 2023 (carve-out year) | 0.393 | 0.473 | same | same | CAVEAT → CAVEAT (worse) |
| C3a price mean | 2019 … 2025 | +6.2 / +2.5 / +0.8 / −8.4 / −24.7 / −11.3 / −9.2 % | +3.8 / +2.1 / +0.3 / −9.4 / −28.6 / −11.8 / −9.6 % | same | same | no flip; 2024 FAIL → FAIL |
| C2, C4, C3c, C5, C8 | all | — | no status change on any basis | | | |
| Determination | | NOT-YET | NOT-YET | NOT-YET | NOT-YET | |

**Basis (b)** shows the same two C3b flips and no C1 flip.

## 2. Kills (PRECOMMIT §4)

| Kill | Result |
|---|---|
| K1 C1 PASS → FAIL on (c) | clear (zero) |
| K2 C3a PASS → FAIL on (c) | clear (zero) |
| **K3 C3b PASS → FAIL on (c)** | **TRIPPED: 2024 0.198 → 0.201** (band 0.20) |
| K4 new D-4 `chp_steam` FAIL | clear. Zero new rows, zero cleared. C R Wing 52176 2019 stays pass (zero-share 0.44, 6,243 binding hours vs 0.44 / 6,264 in the keeper). All seven `chp_steam` window rows pass. |
| K5 CHP rise > static reach + 1 TWh | clear. The net CHP rise is far below reach (§3). |

## 3. Mechanism readout — P1 class sums, arm − keeper (TWh)

| Year | CC_CHP | CT_CHP | ST_CHP | **CHP net** | CC_REGULAR | COAL_PRB | ST_GAS | CT_PEAKER |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 2019 | +3.26 | −2.91 | −0.03 | **+0.32** | −0.08 | −0.08 | −0.10 | −0.05 |
| 2020 | +3.26 | −3.69 | −0.03 | **−0.46** | +0.32 | +0.17 | −0.03 | −0.03 |
| 2021 | +3.75 | −3.01 | −0.03 | **+0.71** | −0.31 | −0.05 | −0.22 | −0.12 |
| 2022 | +3.84 | −3.14 | −0.03 | **+0.67** | −0.30 | −0.03 | −0.19 | −0.15 |
| 2023 | +3.50 | −2.84 | −0.03 | **+0.62** | −0.22 | −0.01 | −0.19 | −0.18 |
| 2024 | +3.96 | −3.18 | −0.03 | **+0.75** | −0.29 | −0.07 | −0.22 | −0.16 |

**Why static over-promised.** The census reach (+3.0…+4.3 TWh net CHP, CC_REGULAR −1.4…−2.3) carried CT_CHP at
−1.0…−1.7. The solve took CT_CHP down −2.8…−3.7:
- Sweeny 55015 (572 MW, 35 → 85 %);
- the 70 % → 94–100 % refinery and chemical hosts (Formosa 10554, Oyster Creek 54676, ExxonMobil Baytown 10436/10692,
  Freeport 52120).

Those hosts lose their grid MW and export floor almost entirely. The CC_CHP gain (Deer Park, Pasadena, Texas City,
Ingleside) is therefore mostly netted out, and only ≈ 0.3–0.75 TWh/yr of new grid CHP reaches the stack. That is also
what the exact zero-LP bench showed on the actual side (net dE +0.7…+1.5, not +3.9…+5.1).

**C1 realisation.**
- 2019 CC_REGULAR −0.08 against the −1.21 T1 needed.
- 2020 CC_REGULAR rises +0.32: the lost CT_CHP energy is backfilled by in-market gas and PRB.

**Price.**
- The floored CC_CHP added in Houston is near-zero-offer energy.
- It flattens the 2019 shape: C3b 0.216 → 0.173, a FAIL → PASS on a load-bearing FAIL that rule-1 offer tuning had not
  reached.
- It nudges 2024 over the line: C3b 0.198 → 0.201.
- 2023 (the carve-out year, scored on this keeper's own 2023 leg) widens 0.393 → 0.473.

## 4. Disposition

**Decision rule.** T1 missed and K3 tripped, so the lane records the result and stands down. No promotion slot is
requested.

**Rule-14 note, for the owner.**
- The measured share is the more accurate input (the plants' own filings refute the sector default), and rule 14 forbids
  reverting to an estimate because it fits better.
- Here the measured input does not worsen C1. On the reconciled basis every CC_CHP miss moves toward actual, and no C1
  status moves.
- Price trades a load-bearing 2019 C3b FAIL → PASS against a 2024 PASS → FAIL by 0.001.
- So the result is not a rejection of the input. It is an ex-ante kill of this lane's promotion attempt.
- Adopting the measured share as ERCOT's carve (with the held bench pair, #20) is an owner decision. Its scored cost on
  the record is the C3b 2024 flip.

**Matrix.** ERCOT `chp_btm_measured` = **O** (open), with this evidence. It is not R: a measured input is not rejected
on fit (rule 14). The re-open evidence is the owner's #20 ruling plus a promotion-time decision on the carve.

**Promotion cost, if the owner wanted it anyway.**
- `promote_keeper.py` on `closeout_ercot_w6_span` (all seven years present, no re-solve). The legs are on the shard
  branches above.
- It needs:
  - the held artifact + fold-refuted pair landed (#20);
  - the render leg (per-plant BTM fields), which is a cross-ISO bench re-stamp;
  - an attestation that carries the keeper's exceptions ledger.
- The determination stays NOT-YET either way (COAL_PRB 2019/20, CC_REGULAR 2019/20, C3a 2024, C3b 2020 and 2024).

**What is left for ERCOT** is unchanged by this lane: the 2019/20 coal-offer frontier rows (ERCOT-F1, DATA-LIMITED) and
C3a 2024.
