# FINDING — closeout-SPP-w2 (zero LP): step 2 NOT CHARTERED, 0b closed, co-opt re-measured, queue exhausted

- **Lane:** closeout-SPP-w2, desk `session_01ERkBTm23ZAP4CTZnJVD9Ss`. Branch `claude/closeout-spp-w2`, cut from
  `1e3e4177e5fcee0757adfab2dabbd69ded9fe2e0`.
- **Keeper (control, read only):** `2026-10-03-closeout-spp-nuc-keeper`, bundle
  `results/calibration/closeout_spp_nuc_span`. Rubric as on main. Determination **NOT-YET**.
- **LP spent:** zero. Nothing was armed, solved, registered or deleted. No PRECOMMIT is written, because no
  step cleared phase 0.
- **Probes (zero LP):**
  - `scripts/probes/_closeoutsppw2_0b_residual.py` → `results/phase0/spp/_closeoutsppw2_0b_residual.json`
  - `scripts/probes/_closeoutsppw2_coopt_headroom.py` → `results/phase0/spp/_closeoutsppw2_coopt_headroom.json`

## 0. The keeper's failing rows (scored here with `calibration_verdict.py`)

| year | C3a | C3b | other FAIL |
|---|---:|---:|---|
| 2019 | **+12.3 %** | 0.160 | — |
| 2020 | **+27.7 %** | **0.345** | — |
| 2021 | +7.1 % | 0.176 | C1 CC −8.92 / PRB +10.98 TWh |
| 2022 | −4.8 % | 0.175 | C1 CC −9.16 / PRB +10.75 TWh; C4 gas NRMSE 0.313 |
| 2023 | −6.4 % | 0.176 | C3c 0 h vs 42 h |
| 2024 | **−11.2 %** | **0.216** | C3c 0 h vs 59 h |
| 2025 | −4.3 % | 0.153 | C3c 0 h vs 68 h |

The train tier (2023–25) fails on C3a/C3b 2024 and on C3c. 2024 is **under**-priced. 2019/20 are **over**-priced.
The two errors point in opposite directions.

## 1. Step 2 (pairing span `spp_commitment_posture` + SPP-107): **NOT CHARTERED**

`PRECOMMIT-spp-pair-posture-exr-2026-10-02.md` §4 sets the launch gate. Here it is evaluated on the current
keeper:

- **K1 clears.** EXR (SPP-107) was promoted and is already in the keeper (`spp_mmu_offer_unavailability` and
  `spp_mmu_offer_repair` are both true in `run_config_2024.json`).
- So the "pair" re-bases (PRECOMMIT §5) to **posture alone on top of the keeper**. Its effect is SPP-102's
  posture Δ, the same column PRECOMMIT §3 used.

| year | keeper C3a | posture ΔC3a (pts, SPP-102) | **PAIR C3a (pred.)** | posture Δupper $ |
|---|---:|---:|---:|---:|
| 2019 | +12.3 % | −1.5 | **+10.8 %** | −0.04 |
| 2020 | +27.7 % | −2.6 | **+25.1 %** | −0.05 |
| 2021 | +7.1 % | −1.0 | +6.1 % | +0.04 |
| 2022 | −4.8 % | −1.3 | −6.1 % | −0.04 |
| 2023 | −6.4 % | −1.5 | −7.9 % | −0.00 |
| 2024 | **−11.2 %** | −1.7 | **−12.9 %** | −0.01 |
| 2025 | −4.3 % | −1.3 | −5.6 % | −0.03 |

- **K2 fires.** The plan's step-2 bar is "2024 C3a within ±10 %". The keeper is already 1.2 pts outside it, and
  the posture moves 2024 a further 1.7 pts away.
  - The direction does not depend on the size. The posture's mechanism is to cut the over-priced body: thermal
    held online at min load, displacing marginal supply. It cannot raise a mean price.
- **K3 fires.** With EXR already in the control, nothing in the arm moves the upper tercile. The posture's
  Δupper is ≤ +0.04 $/MWh in every year. SPP-79/103's pairing condition has nothing to test.
- **2020 C3b would fall** (direction: posture alone took 0.343 → 0.320 on SPP-102). But E5 forbids any train
  flip, and 2024 C3a is already FAIL, moving the wrong way.
- **Cell `spp_commitment_posture` stays R**, with this evidence appended. The R-12 pairing route is closed: the
  pair's upper-tercile half was promoted on its own (SPP-107 → `w0-spp107r` → the nuc keeper). What remains is
  the posture alone, which is the unpaired R of SPP-102/103.

## 2. Step 0b (CT pmax basis vs `SUMMER_CLASS_DERATE`): **CLOSED, no fix (0 MW on the keeper)**

- Wave 1 (`closeout/FINDING-spp-closeout-wave1-2026-10-02.md` §1) measured a double count of about 2 GW on
  keeper spp100. It predicted that the double count is **INERT for fossil rows** once
  `spp_mmu_offer_unavailability` is on: `arrays.py` skips the flat derate on every `_mmu_fossil` row.
- Measured on the loader the solve calls, per vintage year 2019–25: of the 20.9–22.4 GW in the
  `SUMMER_CLASS_DERATE` classes (CC_REGULAR, CC_CHP, CT_PEAKER, CT_CHP), **0.0 MW** sits outside
  `_MMU_FOSSIL_FUELS`. The flat derate reaches **no SPP row** on the keeper recipe.
- One-line fix or none: **none**. If a future SPP recipe disarms the MMU carrier, wave 1's 2 GW double count
  returns, and W0 E.1's deletion for plant-level fleets is the route. That is recorded on the cell.

## 3. Retest `energy_reserve_coopt` (I) on the current keeper: **stays I**

- **New evidence premise.** SPP-96's T2 (0–11 bind h/yr) was measured on keeper spp94. Since then thermal
  availability on the keeper has moved: MMU offer-side bands (SPP-106/107), W0, and ST_GAS `wefor_residual` 0.0.
- **Construction.** The same as SPP-96's T2, read from the committed `unit_marginal_<y>` sidecar with no fleet
  rebuild: eligible headroom = Σ (cap_mw − mw) over `RESERVE_FUEL_TYPES` rows, compared against SPP's measured
  cleared up-reserve (regup + spin + supp + rampup + uncup).
- **Bar.** ≥ 88 bind hours in a year (SPP-96 PRECOMMIT §4(a)).

| year | req median MW | headroom min / p1 / median MW | bind hours | hours headroom < 2× req |
|---|---:|---:|---:|---:|
| 2019 | 1,834 | 2,872 / 7,537 / 17,191 | **0** | 3 |
| 2020 | 1,884 | 4,849 / 8,513 / 17,438 | **0** | 0 |
| 2021 | 1,898 | 6,378 / 8,476 / 17,931 | **0** | 0 |
| 2022 | 2,216 | 3,415 / 8,046 / 18,970 | **0** | 3 |
| 2023 | 2,419 | 3,988 / 7,003 / 17,805 | **0** | 7 |
| 2024 | 2,511 | 2,360 / 6,566 / 18,227 | **0** | 30 |
| 2025 | 3,016 | 3,357 / 7,887 / 18,144 | **0** | 33 |

- No year binds, so the bar is not met. The cell **stays I** on new evidence.
- 2024's tightest hour leaves 252 MW of margin. The co-opt cannot move 2024's mean.
- The posture-bundle variant the plan names is moot, because step 2 does not launch (§1).

## 4. Remaining queue (plan §3.4)

| row | state |
|---|---|
| 0a, 1, 1a, 1b, 1c, 3 | DONE / FAILED (earlier lanes) |
| 0b | **CLOSED here** (0 MW) |
| 2 | **NOT CHARTERED here** (K2, K3) |
| 4 West/East partition (SPP-93) | **owner-gated**. The 2026-09-27 ruling stands: "A West/East solve is NOT authorized; a later lane re-opens it only with a new ruling". Its gate is the validation tier only (zonal spread, the C3b 2020 floor half). Asked of the desk. |
| 5 ledger | **zero LP; DRAFT below, for the owner's signature.** Ledgering changes no number and is not applied here. |

**The admissible lever queue for SPP is exhausted at zero LP.** The do-not-redo list stays as the plan sets it:
curtailment ceiling, gas bridge, offer-band retunes. The ST_GAS-only field is refused (SPP-109).

## 5. DRAFT step-5 ledger rows (not ledgered, not applied)

| rows | proposed class | evidence | route to re-open |
|---|---|---|---|
| C3a 2024 −11.2 %, C3b 2024 0.216 (train) | **data-limited** | SPP-109: the sub-5-day ST_GAS outage the statistical WEFOR carried is ≈ 0.24–0.35 GW (37–49 % of what R-29 removed). No admissible per-event source covers it; CAMPD windows < 5 d fail Z1/Z2. 1c: the RT level residual is uniform across setter classes (+13.8/+17.1/+20.9) with no forward driver. Posture and co-opt cannot reach it (§1, §3). | SPP-published unit-level short-outage data, or an owner ruling on a measured ST_GAS sub-5-day carrier |
| C3a 2019 +12.3 %, 2020 +27.7 %; C3b 2020 0.345 (validation) | **model-class** (commitment state) | MMU: 36/31/30 % of 2020–22 energy self-committed; 2020 RT negative intervals ~11 %. Only the posture moves the body down, and it breaks 2024 (§1). | a commitment mechanism that also lifts 2023–25 (none known) |
| C1 CC 2021/22 −8.92/−9.16, PRB +10.98/+10.75; C4 gas 2022 0.313 (validation) | **data-limited / basis** | SPP-108: PRB passes on the 930-aligned basis; CC 2021 −8.03 pro rata; STB rail 2022 anomalous but not buildable at zero DOF. W5 is held under the owner's "measure all ISOs". | W5 basis ruling |
| C3c 2023–25 | **model-class** (5-min scarcity + RT markup) | wave-1 §2: 100/76/100 % of tail hours clear ≤ $200 in DA, with ≥ 95 % of the premium in the energy component | reverts to the rule-22 caveat once the train C3a/C3b rows close |

## 6. Rules

- **1 / 13 / 14:** no value was chosen on a residual. Every reading comes from the committed keeper bundle, the
  loader the solve calls, and SPP market prints.
- **28:** only `mechanism-matrix/SPP.js` was edited, and no cell moved. Evidence was appended to
  `spp_commitment_posture` (R), `energy_reserve_coopt` (I) and `summer_derate_basis_aware` (U).
- **29 / 32:** zero-LP phase 0, and no shard was launched.
- **31:** nothing was deleted.
