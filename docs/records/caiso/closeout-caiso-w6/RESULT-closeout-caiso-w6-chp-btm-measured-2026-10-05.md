# RESULT closeout-CAISO-w6: measured CAISO CHP behind-the-meter share (2026-10-05)

**Records.**
- `PRECOMMIT-closeout-caiso-w6-chp-btm-measured-2026-10-05.md` (bars, kills, G-DRIFT, declared side effects).
- `FINDING-closeout-caiso-w6-d2-reach-2026-10-05.md` (D2 closed; Addendum A, Schedules 6/7).

**Runs.**
- **Control:** the w3 probe `2026-10-04-closeout-caiso-w3-own`. It was scored twice:
  - on the old bench parts (`scratchpad verdict_w3`);
  - on the new parts this registration rendered (`_verdict_w3_newbench.json`).
- **Arm A1:** probe **`2026-10-05-closeout-caiso-w6-a1`** (bundle `results/calibration/closeout_caiso_w6_a1_span`,
  `_verdict_w6.json`).
  - Recipe: the w3 recipe + `measured_ct_heat_rates_crosswalk_remap` (D1) + `caiso_chp_btm_measured`.
- **Registration:** on `claude/closeout-caiso-w6` only (E13).

**Verdict: T1 MET; kills K1–K6 clear (K6 by 0.002 TWh); NOT PROMOTED (request a slot, §6).**

- C1 CC_REGULAR 2020 moves from +5.00 to **+4.00 TWh** (band ±4.60): FAIL → **PASS**. Every C1 cell in every year now
  passes.
- The only load-bearing FAIL left is **C3a 2021 (+11.0 %, was +12.0 %)**.
- The determination stays NOT-YET.
  - On the probe this reads "governance UNATTESTED", which every unattested probe reads.
  - On the metrics, C3a 2021 is the remaining load-bearing blocker, with C3c 2021 and 2024 at supporting tier.

## Solves

**Pin and checks.** Seven year-isolated shards, pinned to `23762bedebbc589c4503ef1fff01693f1de26539`. Each leg was
fetched and verified before its shard was archived:
- parent `23762bed`;
- 17 files, including `dispatch/<y>_P1.parquet`;
- `caiso_chp_btm_measured = true`, D3 and D4 off.

**Compose.** The legs were composed by `_closeout_caiso_w1_compose_span.py`: keeper `closeout_caiso_w1_a2_span` plus 5
arm fields, one solve surface, one source SHA.

| Year | A1 shard commit (provenance; branch `claude/closeout-caiso-w6-a1-<y>`) |
|---|---|
| 2019 | `ac0b297f41a8451231e25c692ec7164387ffe0d8` |
| 2020 | `a97649be8a1862feb2203dffca39a4a4615e6a17` |
| 2021 | `8251547b6ac614b611dcf6322a5b1fa1eb2520c8` |
| 2022 | `57d956d60a8a775a9aacfd559177c0c17542865e` |
| 2023 | `1a0b3fedfc360f7f98aeb4f31e44d5fd233a1d23` |
| 2024 | `ccbd8e8212117efe9c1d8565b40fff6c4b544264` |
| 2025 | `2911e0fb7cc1e5553fbd9ecb0337865ca1d4a21d` |

**Unserved energy** is 0 in every leg.

## 1. Gate table (w3 → w6, both on the new bench parts; every scored record that moved)

| Criterion | Year | w3 | w6 | Status |
|---|---|---|---|---|
| **C1 CC_REGULAR (T1)** | **2020** | 51.128 (+5.00) | **50.133 (+4.00)** | **FAIL → PASS** (±4.60) |
| C1 CC_REGULAR | 2019 / 21 / 22 / 23 / 24 / 25 | −2.04 / +3.47 / +0.95 / −1.07 / −1.67 / +0.81 | −2.94 / +2.67 / +0.01 / −1.94 / −2.50 / +0.06 | PASS (2019 WATCH-depth −2.94 vs ±4.84) |
| C1 CC_CHP | 2019 … 2025 | −0.48 / −0.08 / −0.02 / −0.28 / −0.29 / −0.32 / +0.08 | +0.59 / +1.09 / +1.14 / +0.92 / +0.70 / +0.82 / +0.88 | PASS (all ≤ 1.14 vs ≥ ±4.60) |
| C1 CT_PEAKER | 2019 … 2025 | 2.55 / 2.93 / 6.19 / 3.85 / 2.99 / 3.29 / 0.99 | 2.49 / 2.77 / 5.78 / 3.71 / 2.76 / 3.09 / 0.87 | PASS. 2021 moves toward actual; the others move away by 0.06–0.24 |
| C1 ST_GAS | 2019 … 2024 | 0.08 / 0.52 / 0.16 / 0.29 / 0.04 / 0.15 | 0.07 / 0.46 / 0.10 / 0.26 / 0.02 / 0.12 | PASS |
| C2 gas (model) | all | 46.4–69.5 | Δ ≤ 0.12 TWh | PASS |
| C4 gas NRMSE | 2019 … 2025 | 0.288 / 0.288 / 0.294 / 0.249 / 0.235 / 0.240 / 0.283 | 0.294 / 0.293 / 0.299 / 0.250 / 0.234 / 0.237 / 0.283 | PASS. Worst move +0.006 (K2 clear) |
| **C3a price mean** | **2021** | +12.0 % | **+11.0 %** | FAIL → FAIL (improves) |
| C3a | 2022 / 23 / 24 / 25 | +8.6 / +7.6 / +6.6 / +6.0 % | +7.1 / +6.8 / +5.5 / +5.1 % | PASS (improves) |
| C3c tail hours | 2022 / 2023 | 515 / 51 | 509 / 45 (actual 510 / 47) | PASS |
| C8 CC_REGULAR forced | 2019 … 2025 | 7.1–12.3 % | 7.5–12.7 % | PASS (cap 30 %) |

## 2. Mechanism readout (P1 unit sums, TWh, w6 − w3)

| Year | CC_REGULAR | CC_CHP | CT_CHP | CHP total | CT_PEAKER | ST_GAS |
|---|--:|--:|--:|--:|--:|--:|
| 2019 | −0.90 | +1.07 | +0.49 | +1.56 | −0.07 | −0.01 |
| 2020 | −1.00 | +1.30 | +0.49 | **+1.79** | −0.17 | −0.06 |
| 2021 | −0.81 | +1.31 | +0.76 | +2.07 | −0.41 | −0.06 |
| 2022 | −0.94 | +1.34 | +0.52 | +1.86 | −0.14 | −0.03 |
| 2023 | −0.87 | +0.99 | +0.56 | +1.56 | −0.24 | −0.01 |
| 2024 | −0.83 | +1.14 | +0.56 | +1.69 | −0.20 | −0.02 |

**Displacement.**
- About 55 % of the added CHP grid energy displaces CC_REGULAR.
- The rest displaces CT_PEAKER, steam and imports.
- The mechanism behaves as identified: the merchant cogens carved at the 35–65 % sector default now sell their measured
  grid share (Los Medanos 3.12 TWh in 2020, Watson 1.92, Crockett 1.26). The refinery hosts self-supply (Richmond
  52109, 99.7 % BTM, has no grid rows).

**Against the §2 upper bound.**
- The added CHP energy exceeds the PRECOMMIT §2 capacity-only upper bound by 0.1–0.3 TWh in most years.
- Cause: lowering the BTM share also rescales the steam floor (`pmin_cf × (1 − pct)`), and §2 counted only the capacity
  side.
- The floor-bound CHP energy (D-4 `chp_steam` window row) rises 6.89 → 8.13 TWh in 2020.
- Effect on K6: **K6 (2020 CHP rise ≤ w3 + 1.79) clears at +1.788, a 0.002 TWh margin.** This is stated plainly: K6
  is not a comfortable clear.

**Legitimacy.** The D-4 `chp_steam` unit-conduct FAILs flagged by the shards are in the w3 control too, on the same
plants (10034, 10294, 10649, …). They pre-date this lever, and CHP classes are D-2/C8-exempt (rule 20).

## 3. The bench side effect (desk, 03:42Z): what the measured subtrahend did to the rendered actuals

Registering w6 re-rendered the shared CAISO bench parts with the measured `btm_bench_twh` (nyiso-149 pin). w3 was then
re-scored on those same parts.

| Year | CC_CHP actual (old → new) | C2 gas actual (old → new) | Non-CHP C1 actuals |
|---|---|---|---|
| 2019 | 8.03 → 8.91 | 54.03 → 54.91 | unchanged |
| **2020** | 7.53 → 8.41 | 60.31 → 61.20 | **unchanged (CC_REGULAR 46.132 both)** |
| 2021 | 8.00 → 9.00 | 64.62 → 65.62 | unchanged |
| 2022 | 8.13 → 9.03 | 65.56 → 66.46 | unchanged |
| 2023 | 7.74 → 8.51 | 65.08 → 65.84 | unchanged |
| 2024 | 6.79 → 7.47 | 57.26 → 57.95 | unchanged |
| **2025** | 6.90 → 7.14 | 48.33 → 47.32 | **CC_REGULAR 38.573 → 37.409, CT_PEAKER 2.723 → 2.641 (uniform ×0.970)** |

**Deadband.** The combined fossil reconcile (`reconcile_vintage_classes`) newly fires in **2025 only**: a uniform
×0.970 on every fossil class.
- 2025 is CAISO's `EIA930_NG_CELL_CORRUPT` / preliminary-vintage year.
- 2019–2024 stay inside the ±3 % deadband: no non-CHP actual moves.
- Unlike MISO's COAL_PRB flip, the 2025 rescale moves no status. The C1 CC_REGULAR 2025 miss of the control (w3)
  reads −0.36 on the old parts and +0.81 on the new ones; w6 reads +0.06 on the new ones.

**T1 is scored on the bench as it renders.** The CC_REGULAR 2020 actual is the same 46.132 on both parts, so T1 does
not depend on the side effect.

## 4. Kills (PRECOMMIT §3)

| Kill | Result |
|---|---|
| K1 any C1 PASS → FAIL | clear (zero; one FAIL → PASS) |
| K2 C4 NRMSE worse by > 0.02 | clear (worst +0.006, 2019) |
| K3 C3a worse by > 1 pp | clear (improves 0.8–1.5 pp every year) |
| K4 C8 breach | clear (CC_REGULAR ≤ 12.7 %) |
| K5 C2 out of band | clear |
| K6 2020 CHP rise > 1.79 TWh | clear at +1.788 (margin 0.002; §2) |

## 5. Declared side effects, status

- **Bench subtrahend (CAISO).** As declared, the CC_CHP actual rises 0.24–1.0 TWh per year (§3). The 2025 fossil
  reconcile newly fires (×0.970). No status moves.
- **Render leg held** (`_render_leg_pending.patch`).
  - The renderer's per-plant BTM fields and the CAISO gas-family cogen anchor (C2 basis) still read the sector default
    under this run.
  - C2 passes in every year on that basis.
  - A promotion needs the render leg, which is a cross-ISO bench re-stamp event (PRECOMMIT §5).

## 6. Disposition

**Decision rule (PRECOMMIT §3).** T1 is met and K1–K6 clear, so the result is a **promotion-slot request to the desk**,
with two preconditions:
- (a) the render-leg re-stamp is scheduled;
- (b) the owner rules on the reference-construction change to the CAISO bench subtrahend. This is the same family as
  D2-c and is moot for T1 (§3).

**Matrix.** The CAISO `chp_btm_measured` cell stays **U**, with this evidence. It is promotable on a slot.

**What is left for CAISO CALIBRATED:**
- C3a 2021 (+11.0 %, load-bearing);
- C3c 2021 / 2024 (supporting, 0 h vs 27 / 35 h);
- unchanged by this lever except that C3a improves.

## 7. DOF / retrievability

**DOF:** zero fitted parameters.
- Measured inputs: the EIA-923 Schedules 6/7 filings (pooled CY2022–24) and the D1 CEMS rows.

**Where the bundles are.**
- Span `results/calibration/closeout_caiso_w6_a1_span` and its legs: local and gitignored.
- Their bytes: the seven shard commits above.

**What a promotion would cost.**
- Commit the span bundle, including `hourly/unit_marginal_<y>.parquet`, ≈ 0.4 GB.
- Run `promote_keeper.py`.
- Land the render leg with the scheduled re-stamp.
- Carry the w5 RESULT's A2 / D1 attribution forward.
