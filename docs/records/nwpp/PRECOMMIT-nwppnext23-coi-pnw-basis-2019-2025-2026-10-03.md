# PRECOMMIT — NWPP-NEXT-23: COI export leg on CAISO's PNW delivered-cost basis, 2019–2025 (2026-10-03)

**Owner card (2026-10-03):** "Solve H2 PNW basis". **Phase 0:** `FINDING-nwppnext23-price-level-phase0-2026-10-03.md`
(zero LP). **Parent:** zero LP (rule 32).

**Control (rule 29(b)):** the incumbent keeper's committed bundle, `2026-10-03-nwpp-next-22b-w0`
(`results/calibration/nwppnext22b_span`). If the close-out anchor lane promotes first, its bundle becomes the control.
Its only LIVE delta is the plant-basis CSV: ≤ 0.0054 TWh/yr of requirement, which this pin carries too.

## 1. The arm

Keeper recipe + `nwpp_coi_pnw_delivery_basis=true`. There is one new key and zero fitted scalars.

- **What it prices.** CAISO_COI's NW→CA export bands at `(band − 5.0) / 1.05`, using
  `CAISO_IMPORT_DELIVERY_BASIS["PNW_midC"]`, CAISO's registered basis for the same Malin corridor. This replaces
  `band − 3.0`.
- **What stays unchanged.** The import leg, NEVP and BC.
- **Rule 19.** One physical path, one delivery basis. The 3.0 came from CAISO's inactive `WECC_PNW` interface; CAISO's
  active ladder prices PNW imports on hub + loss + wheel.
- **Rule 13.** A tariff wheel and a loss factor, forward-reproducible for any year.
- **Rule 1.** No band is tuned. The constant is CAISO's, and it was never fitted to an NWPP residual.

**Mechanism matrix.** New row `nwpp_coi_pnw_delivery_basis`, with a cell in every shard. The NWPP cell is **U**. No
R/I/G cell is re-tested.

**G-DRIFT** (pin vs the keeper legs' pin `2b8da72a`):

- The close-out anchor lane's audited drift (its PRECOMMIT §5): LIVE `nwpp_plant_basis_energy.csv`, LIVE cache-key
  SolveEpoch 2026-10-03a, everything else INERT.
- #7100: docs only.
- This lane's two commits: the key, off by default and byte-identical when off (tests).

Zero-LP arm construction at the pin reproduces NEXT-22b's printout for every year: rows, residual, seam groups and
cap means.

## 2. Shards

- Seven shards, one per year 2019–2025 (rule 36).
- Each runs `replay_keeper.py results/calibration/nwppnext22b_span --years Y --set nwpp_coi_pnw_delivery_basis=true`
  into `results/calibration/nwppnext23_<Y>`, on branch `claude/nwppnext23-<Y>`, pinned to `claude/nwppnext23-pin`.
- Hard stop (a) allows exactly the one key in the scenario_config diff; `spp_mmu_offer_repair` None→False is also
  allowed (SPP-only, inert).
- Hard stop (e) adds the log line `seam export delivery basis CAISO_COI loss 0.05 wheel 5.0`.
- Budget: 150 minutes per shard.

## 3. Readings, fixed before any number exists

**Structural gate (must hold, else HOLD):**

- (a) Every priced seam-year keeps the measured annual sign, with NEVP 2019 exempt as before, and hourly r > 0.
- (a′) Caps respected (≤ 1 MW excess).
- D-2 / C6 PASS.
- (a″) Direction: COI net export falls against the keeper in **every** year. A rise in any year is a kill: it means
  the mechanism is not what phase 0 measured.

**Prediction (price-taker on the keeper's NW price, FINDING §D).** COI TWh 10.81 / 14.01 / 14.65 / 16.70 / 3.79 /
9.62 / 6.02 (2019–25), against the keeper's realized 13.03 … / 6.57 / 12.42 / 9.03 for 2023–25. The LP response is
expected to be smaller, because NW prices rise as exports fall.

**Reported at full magnitude against the keeper,** per (criterion, year, key):

- C1 CC_REGULAR (keeper FAIL 2019 +12.69, 2024 +15.39, 2025 +8.74 TWh);
- C4 gas (FAIL 2019 r 0.661, 2023 0.538, 2024 0.796);
- C4 coal (PASS every year);
- C3a / C3b 2023–25;
- D-1 count;
- every priced-seam TWh with r.

**Decision rule.** The owner's standing ruling: promote if structural integrity improves, even if a gate regresses.

- The arm is a structural alignment (rule 19), so it is a promotion candidate if the structural gate holds.
- Every regression is reported at full magnitude.
- **HOLD** if the structural gate fails, if any criterion flips PASS→FAIL with no structural explanation in the
  seam/gas chain, or if C4 coal fails in any year.
- Promotion is serialised behind the close-out anchor lane (desk session_01ALecU5Wjde4tkbLrnMExT9).
