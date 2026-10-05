# FINDING — closeout-chp-transfer (ZERO LP): the three MISO/CAISO CHP corrections, censused on every other ISO

**Lane:** `closeout-chp-transfer`, chartered by the backcast close-out desk (session_01ERkBTm23ZAP4CTZnJVD9Ss).
**Owner direction:** "There are definitely uncalibrated ISOs that should be being rerun and tested."
No LP was solved. No solve-affecting code, matrix shard or rubric file was touched.

- **Probes.**
  - `scripts/probes/_closeout_chp_transfer_census.py` writes `results/phase0/governance/_closeout_chp_transfer_census.json`.
  - `scripts/probes/_closeout_chp_transfer_score.py` writes `results/phase0/governance/_closeout_chp_transfer_score.json`.
- **Inputs.**
  - Each keeper's committed bundle: bench parts `frontend/data/backcast/bench/<ISO>/`, `hourly/unit_marginal_<y>.parquet`, and the C1 records in `status/<ISO>.js`.
  - EIA-923 Schedules 6/7 (`data/raw/eia-923-disposition/`), EIA-923 page 1, and CAMPD hourly.
- **Scope.**
  - The five NOT-YET ISOs: ERCOT, PJM, SPP, SOCO and NWPP.
  - NYISO and NEISO are CALIBRATED, so they were censused for PASS→FAIL risk only.
- **The three corrections (MISO w3e/w3f, CAISO w6):**
  - **(1)** `*_chp_btm_measured`: the measured CHP behind-the-meter share.
  - **(2)** `chp_startup_covered`.
  - **(3)** `mustrun_chp_btm_holdout`.

## 0. Method (static; read the caveats in §4)

**(a) Share census.**
- The plant set is every keeper-bench plant whose `bench.plants[code].group` is a CHP group. That is the same plant→group map `_btm_frame` keys on.
- The measured share is pooled over CY2022–24 from Schedules 6/7, exactly as `derive_caiso_chp_btm_share.py` defines it: grid = resale + tolling + outgoing.
- Two quantities follow from it:
  - **dE (bench).** dE = EIA-923 class net × (bench share − measured share). This is how much the bench CHP actual rises.
  - **Model reach.** Each covered plant's grid MW is scaled by (1−m)/(1−d) at its own solved utilisation, then walked down the solved stack at or below the hour's marginal offer (the w3d walk).
- The bench share is the sector default everywhere except NYISO, which uses its Gold Book artifact (nyiso-149).

**Reconcile re-check (`reconcile_vintage_classes`, deadband 0.97).** The re-check runs on two bases:
- with the fold-in deflation;
- with the ISO in `EIA930_GAS_FOLD_REFUTED`.

How the pre-scale family is obtained:
- **Unscaled years:** it is exact, because the committed family is the pre-scale family.
- **Scaled years:** it is estimated, via the ratio of the non-CHP gas classes to raw 923, referenced to the ISO's own unscaled years.

The fold test is SOCO-60's: EIA-930 gas minus the EIA-923 gas FULL of member plants, compared with F.

**(b) Commitment.**
- **Census:** CEMS online share and starts vs the keeper's, per CHP plant with CEMS output. A plant is online when it runs above 5 % of its series max.
- **Release of `chp_startup_covered`:** the w3f reach. It is the committed-tranche headroom in hours when the econ-low tranche is at cap and the committed offer sits more than $0.5 above it.
- **Realisation:** the release is scaled by MISO w3f arm A's realised/static ratio, 0.40.

**(c) Holdout.**
- **Reach:** the chp=Y biomass/OTHER rows the holdout drops, from `_eia923_frame` itself, compared against EIA-930 OTH.
- **Take-up:** a flat-MW up-walk, filling the cheapest headroom first.

**(d) Scoring.**
- Each of the keeper's C1 records is rescored under four cumulative arms:
  - **M:** the measured share pinned on the bench (nyiso-149: it lands whenever an artifact exists);
  - **A1:** M + the run carve;
  - **A2:** A1 + startup release × 0.40;
  - **A3:** A2 + the holdout.
- **Bench bases:** each arm is scored on both bases (an `r` suffix marks fold-refuted). A further arm, **R**, is the fold refuted on its own, with no CHP change.
- **Pass rule:** |miss| ≤ the record's own band, and |share| ≤ 3 pp.

## 1. Per-ISO census (2019–2025 ranges; TWh)

| ISO (status) | CHP plants in Sched 6/7 | bench BTM: default → measured | dE bench (by class) | top movers (default → measured) | reconcile, deflated basis → refuted basis | fold test: 930 gas − 923 FULL vs F | CHP online, CEMS vs model; starts | startup release (static) | holdout: chp=Y injected vs 930 OTH (total injected) |
|---|---|---|---|---|---|---|---|---|---|
| **ERCOT** (NOT-YET) | 11–13 of 11–13 | 14.9–17.7 → 10.8–12.5 | **+3.9…+5.1** (CC_CHP +4.6…+5.5, CT_CHP −0.2…−1.1) | Deer Park 55464 0.35→0.03; Pasadena 55047 0.35→0.00; Altura 50815 0.35→0.18; Sweeny 55015 0.35→0.85; Channelview 55187 0.35→0.48 | **fires 2020–25** (1.031–1.046) → fires 2020/24/25 (1.034/1.042/1.042) | **−33…−40 vs 0.2–2.4: REFUTED** | 0.96–0.99 vs 0.97–1.00; 1–3 vs 1 | **0** (no committed CHP band; CAMPD bins) | 1.9–2.4 vs 0.27–1.85 (1.4–3.2) |
| **PJM** (NOT-YET) | 20–23 of 20–23 | 5.9–7.9 → 3.8–4.3 | **+2.0…+3.5** (CC_CHP +2.0…+3.4) | Marcus Hook 55801 0.35→0.02; Shell Monaca 58933 0.70→0.34; Grays Ferry 54785 0.35→0.03; Delaware City 52193 0.70→0.37; Morris 55216 0.35→0.76 | no fire (0.985–1.018) on either basis | −6…−24 vs 0–3.0: REFUTED | 0.73–0.89 vs 0.76–0.90; 8.5–20 vs 3–16.5 | 0.25–0.77 | 5.4–6.4 vs **9.6–13.2 ≥ total (9.6–11.7): CONTRA** |
| **SPP** (NOT-YET) | 2 of 2–4 | 1.2–1.4 → 0.9–1.1 | +0.26…+0.31 | Black Hawk 55064 CT_CHP 0.35→0.04; Eastman 55176 0.35→0.39 | 2021/22 0.972/0.973 no fire; 2023–25 committed fired up → **refuted: 2021/22 fire up (0.963/0.965)** | −4.0…+0.2 vs 1.1–1.7: REFUTED | 0.94–0.99 vs 0.95–0.99; 1–8 vs 1–10 | ≤ 0.07 | **1.2–1.6 vs 0.3–0.6 (1.6–2.0): SUPPORTED** |
| **SOCO** (NOT-YET) | 1–3 of 5–8 (0.1–0.7 TWh covered) | 1.4–1.9 → 1.3–2.0 | −0.06…+0.08 | Mid-Georgia 55040 0.35→0.00 | fold already refuted; no change | (in registry) | 0.84–0.93 vs 0.85–0.93; 5–7 vs 3–5 | 0.09–0.40 | 7.1–8.8 vs 1.9–2.7: supported; **cell O, solved in closeout-SOCO-w3** |
| **NWPP** (NOT-YET) | 2–4 of 5–7 | 2.7–4.2 → 1.0–1.6 | **+1.7…+2.6** (all CC_CHP) | Hermiston 54761 0.35→0.00; Klamath 55103 0.35→0.01 | committed fires every year (est. pre 1.06–1.14 × raw, no unscaled year to anchor) | −12…−17 vs 0–0.9 (multi-BA membership caveat) | 0.81–0.92 vs 0.81–0.92; 5–33 vs 3–44 | 0.6–1.5 | 2.8–3.5 vs 7.8–8.5 (7.9–8.8): **CONTRA** (holdout leaves ≈ 3 below 930 OTH) |
| NYISO (CAL) | 19–20 of 21–22 | Gold Book 1.8–2.1 → Sched 6/7 0.9–1.3 | +0.8…+0.9 | Linden 50006 GB 0.22→0.00; RED-Rochester ST_CHP 0.98→0.38; Stony Brook 0.00→0.69 | no fire either basis | F = 0 already | 0.84–0.91 vs 0.80–0.87; **15–21 vs 52–107** | ≈ 0 | 0.7–0.8 vs 2.9–5.0 (2.4–2.8): CONTRA |
| NEISO (CAL) | 4–8 of 4–9 | 0.7–1.0 → 0.15–0.32 | +0.5…+0.7 | Kendall Square 1595 0.35→0.00 | **deflated: fires 2020/22 (1.033/1.034)** → refuted: no fire (1.013/1.012) | −1.2…−1.5 vs 0.8–1.2: REFUTED | **0.78–0.93 vs 0.25–0.59; 16–30 vs 17–137** | ≤ 0.06 | 1.0–1.6 vs 4.7–5.9 (5.8–6.9): CONTRA |

**Model-side static reach of the measured carve (A1), TWh/yr.**

| ISO | Model CHP added | Displaced (largest first) |
|---|---|---|
| ERCOT | +3.0…+4.3 | CC_REGULAR 1.4–2.3, COAL_PRB 0.25–0.95, ST_GAS 0.5–0.8 |
| PJM | +2.5…+3.4 | CC_REGULAR 1.0–1.4, COAL_BIT 0.3–0.6, CT_PEAKER 0.3–0.6 |
| NWPP | +1.7…+2.3 | CC_REGULAR ≈ 0.7, COAL 0.5–1.3 |
| NYISO | +1.3…+1.7 | CC_REGULAR / ST_GAS / imports |
| NEISO | ≈ +0.45 | mostly CC_REGULAR |
| SPP | ≈ +0.45 | spread thin |
| SOCO | ≈ 0 | — |

## 2. C1 records moved (static), per ISO

Records are shown as miss → arm miss, against the band. "r" marks the fold-refuted bench. Only records whose status changes, or keeper FAILs, are listed.

| ISO | Keeper FAIL (C1) | Best arm | FAIL→PASS | PASS→FAIL | Net (static) |
|---|---|---|---|---|---|
| **ERCOT** | CC_REG 2019/20, COAL_PRB 2019/20 | **A1r** (measured carve on the fold-refuted bench) | CC_REG 2019 +9.21 → **+7.51** (±8.0; needs ≥ 71 % LP realisation of the static 1.70 TWh CC_REG displacement) | none | **+1** (fragile) |
| PJM | COAL_BIT 2019/20/21, CC_REG 2022 | A1 / A1r | CC_REG 2022 +8.96 → +7.74 (margin 0.26) | **CT_PEAKER 2021 −7.92 → −8.27** (margin 0.27) | 0 |
| SPP | CC_REG 2021/22, COAL_PRB 2021/22 | **R** (bench only, no CHP arm) | COAL_PRB 2021 +10.98 → +7.93 (±7.98, margin 0.05; exact, unscaled year); COAL_PRB 2022 +10.75 → +7.89 (margin 0.11; exact) | CC_REG 2025 −7.86 → −8.16 (estimated pre-scale, scaled year) | +2 / −1 → **+1** (knife-edge) |
| SOCO | CC_REG 2019 | none | — | A3 = the solved w3 result (CC_REG 2021/23 flipped; static also flags 2020/24) | 0 |
| NWPP | CC_REG 2024 | none | — | M: CC_REG 2019 +7.50 → +8.27; A3: CC_REG 2019/2025 | 0 |
| NYISO (CAL) | — | none | — | **A1: ST_GAS 2021 −3.44 → −3.79 (share −3.05 pp)** | do not arm |
| NEISO (CAL) | — | none | — | A3: CC_REG 2020 +0.52 → +2.97 (±2.78); M on the deflated basis fires the reconcile in 2020/22 | do not arm |

Further notes:
- **ERCOT CC_REG 2020** worsens in every arm: +10.17 → +12.95 under A1r, because the reconcile fires in 2020 on both bases. The record is already a FAIL, so no status changes.
- **ERCOT COAL_PRB** moves a further −0.3…−1.0 under A1 and stays FAIL. The carve displaces coal in a class the model already under-runs.
- **ERCOT A3:** stacking the holdout puts CC_REG 2019 back to FAIL (+8.44). Do not stack it.
- **ERCOT A2 = A1:** the startup release has zero reach.
- **PJM COAL_BIT** moves −0.3…−0.6 under A1, against needs of −4.7 to −11.7. It stays FAIL.
- **SPP CHP arms:** A1–A3 move every record by ≤ 0.5 TWh, against the 1–3 TWh that each FAIL needs.
- **SPP A3 direction:** the holdout's take-up is about 35 % coal (COAL_PRB), the wrong direction for the COAL_PRB FAILs.
- **SPP Mr / A1r:** stacking measured shares on the refuted bench pushes COAL_PRB 2021 back to 8.11 / 7.99. The +2 survives only with the default shares (arm R), or by 0.01 TWh (A1r).
- **SOCO CHP:** it is too small to matter, and the measured shares are already near default (dE ≤ ±0.11 TWh).
- **SOCO holdout:** the static walk over-assigns its take-up to CC relative to the solved w3 run, a useful calibration of A3's static bias (§4).
- **NWPP CC_REG 2024** (+12.15): no arm moves it toward the band. M rescales the family down by about 1 TWh, which makes it worse.
- **NYISO measured shares:** Schedules 6/7 is the wrong meter for NYISO. Linden sells to the PJM side as well, so Sched 6/7 "grid" is not NYISO delivery. The Gold Book (nyiso-147/149) is the ISO-boundary meter, and rule 14 keeps it.
- **NEISO M:** on the deflated basis the reconcile fires in 2020/22. That is MISO's cancelling-error pattern in miniature.

## 3. Answers to the charter

**(a) Measured share vs the sector default.**
- The default (merchant 35 %) overstates host self-use at the big merchant cogens in four ISOs:
  - ERCOT +3.9…+5.1 TWh/yr of grid CHP;
  - PJM +2.0…+3.5;
  - NWPP +1.7…+2.6;
  - NEISO +0.5…+0.7.
- It is roughly right in SPP and SOCO.
- In every ISO a few hosts go the other way: Sweeny, Channelview, Morris, Eastman, Stony Brook.

**The fold-in deflation fails SOCO-60's test wherever it is non-zero.** In every ISO measured, EIA-930 gas sits below the EIA-923 gas FULL of member plants, leaving no room for a fold:

| ISO | 930 gas − 923 gas FULL (TWh) |
|---|---|
| ERCOT | −33…−40 |
| PJM | −6…−24 |
| SPP | −4…+0.2, always < F |
| NEISO | −1.2…−1.5 |
| NWPP | −12…−17, with a membership caveat |

The negative gap is unmetered host and private-use-network output. This is MISO-w3e's finding generalised: the deflation is invalid for every ISO that carries one.

**How this interacts with the measured share:**
- **ERCOT:** the measured share alone fires the deflated-basis reconcile in 2020–25. The fold ruling cures 2021–23. In 2020/24/25 the measured-basis family exceeds raw 930 by 3.4–4.2 % on both bases, so the reconcile scales ERCOT fossil down about ×0.96–0.97 in those years.
- **NEISO:** the measured share fires the deflated basis in 2020/22 only; the refuted basis cures both years.
- **PJM:** no fire on either basis.
- **SPP:** refuting the fold makes the reconcile fire upward in 2021/22. That is what moves the COAL_PRB records.

**(b) Commitment.**
- **NEISO** is the only ISO with MISO's signature:
  - CHP online share 0.25–0.59 in the model against 0.78–0.93 metered;
  - starts up to 137 against 16–30.
  - The startup release reaches ≤ 0.06 TWh, because the inversion is not what keeps NEISO CHP off. NEISO is CALIBRATED in any case.
- **NYISO** cycles its CHP 3–5× too often (52–107 starts against 15–21), with no release reach.
- **ERCOT, PJM, SPP, SOCO and NWPP** already match CEMS online share within 0.03–0.04. The static release is 0 (ERCOT) to 1.5 TWh (NWPP), and after the 0.40 realisation it moves no record.
- `chp_startup_covered` is therefore not a lever for any NOT-YET ISO.
- What it would displace (largest first):
  - PJM: CC_REGULAR, then COAL_BIT;
  - NWPP: CC_REGULAR, then coal.

**(c) Holdout.**
- **Supported by 930 OTH** (the injection exceeds 930 OTH by about the chp=Y block):
  - SPP: 1.2–1.6 TWh;
  - SOCO: 7–9 TWh, already solved, cell O;
  - ERCOT: partly; 1.9–2.4 TWh, over-removing in 2024–25.
- **Contra-indicated** (930 OTH already holds the host energy; dropping chp=Y would leave the injection below 930 OTH): PJM, NWPP, NYISO and NEISO.
- **Static reach on the records:**
  - none positive in any NOT-YET ISO;
  - PASS→FAIL risk in SOCO (solved: realised), NWPP and NEISO.

**(d) Ranking.** By expected record gain (static) under the matrix constraints (rule 28; transfers enter as U):

1. **ERCOT, arm `ercot_chp_btm_measured`.**
   - **What it is:** a new ERCOT-scoped flag on the CAISO-w6 pattern, with an ERCOT Schedules 6/7 derive. ERCOT's `chp_btm_measured` cell is U.
   - **Precondition:** ERCOT is added to `EIA930_GAS_FOLD_REFUTED`, with the fold test above as its evidence (owner decision #20 extended).
   - **Expected:** +1 record (C1 CC_REGULAR 2019), with no PASS→FAIL.
   - **Rule-19 note:** ERCOT arms `chp_export_floor_measured`, which reads the same share (floor = CF × (1 − btm) × nameplate). The carve therefore raises a floor. That should lift realisation, but D-4 must be checked.
   - **Do not stack:** the holdout (it reverses CC_REG 2019) or `chp_startup_covered` (zero reach).
   - **Determination:** ERCOT stays NOT-YET either way (COAL_PRB 2019/20, CC_REG 2020, C3a 2024, C3b 2019/20).
2. **SPP, no solve: the fold ruling alone (arm R) on the committed bench.**
   - **Records:** +2 (COAL_PRB 2021/22), exact on unscaled years but with margins of 0.05 and 0.11 TWh; −1 risk (CC_REG 2025, estimated).
   - **What it is:** a benchmark registry decision, not a lane, and it belongs with #20.
   - **Not with measured shares:** they undo the 2021 gain.
3. **PJM, A1.** Net 0 (+CC_REG 2022 / −CT_PEAKER 2021, both within 0.27 TWh). Charter it only if a CT_PEAKER cushion lands first.
4. **No charter:** SOCO (the holdout is O, CHP immaterial), NWPP (no positive reach; M and A3 PASS→FAIL risk), NYISO and NEISO (CALIBRATED; A1/A3 PASS→FAIL risk; NYISO's Gold Book is the better meter).

**Recommendation.**
- **First charter:** ERCOT, with `ercot_chp_btm_measured` on a fold-refuted ERCOT bench, as a single-arm span. The kill is any PASS→FAIL, or a D-4 CHP row.
- **Owner decision #20:** widen the MISO fold ruling into a census-wide refutation. The deflation fails SOCO-60's test in ERCOT, PJM, SPP and NEISO (NWPP with its caveat). Score that ruling zero-LP per ISO before any promotion, because SPP moves under it alone.
- **No CHP arm** is recommended for SPP, SOCO, NWPP, NYISO or NEISO.

## 4. Caveats (what static can't say)

- **Realisation is below static.** MISO w3f arm A realised about 40 % of its static CHP gain, and the displaced class was not the declared one. ERCOT's +1 needs at least 71 % realisation on CC_REGULAR. The static walk assumes the new grid CHP MW run at the plant's own solved utilisation and displace only units at or below the marginal offer.
- **A3's static take-up is biased toward CC.**
  - SOCO's static CC_REG move is about 2× the solved w3 move.
  - The share leg under A3 ignores the change in total generation, since the holdout removes the same energy from both totals.
  - A3 PASS→FAIL calls are therefore conservative (they over-call).
- **Scaled years use an estimated pre-scale family.** The estimate is the non-CHP gas classes' committed ÷ raw-923 ratio, referenced to the ISO's unscaled years. NWPP has no unscaled year, so its reconcile figures carry no anchor. Every SPP/ERCOT gain listed above is on an unscaled year. The one exception is SPP's −1, CC_REG 2025, which is on a scaled year.
- **Measured shares are a CY2022–24 pool, applied to every year** (the CAISO-w6 convention). Same-year shares are in the JSON. Pasadena 2022 is 0.13 same-year against 0.00 pooled; Sweeny's same-year 0.61 is against a pooled 0.85.
- **Only C1 is scored.** C3a/C3b moves (price) are not estimated here. On MISO the holdout carried a price lift; on the carve it was neutral.
