# PRECOMMIT — SPP-PAIR: `spp_commitment_posture` paired with SPP-107 EXR (plan §3.4 step 2; R-12)

- **Lane:** closeout-SPP wave 1, `claude/closeout-spp-wave1`. Written 2026-10-02, **before any solve and
  before SPP-107's RESULT exists**. Nothing below is chosen from a solved number of this arm.
- **Owner authority:** §5.0 R-12, "SPP: one PRECOMMIT for SPP-107 + the commitment-posture pairing. 7 shards
  once."
  - SPP-107 is already precommitted and solved by `session_01AdnPmeuEobd5SfMxSk5FLx`
    (`docs/records/spp/spp107/PRECOMMIT-spp-107-mmu-carrier-repair-2026-10-02.md`, branch
    `claude/spp-mmu-offer-carrier-repair-gonc4e`).
  - This document is the pairing half. It adopts SPP-107's arm **by reference and unchanged**.
- **Solves:** HELD.
  - They wait for (a) the W0 lane (`claude/closeout-b-w0-foundation`) to merge, (b) the desk to release this
    lane, and (c) the §4 launch gate below.

## 1. What is solved

| arm | recipe (on the post-W0 SPP keeper) | free parameters |
|---|---|---|
| **PAIR** | `spp_commitment_posture=true` (SPP-102 construction, unchanged) + `spp_mmu_offer_unavailability=true` + `spp_mmu_offer_repair=true` (SPP-107 EXR, unchanged) | **zero new** |

**The posture (SPP-102, unchanged):**
- 23 per-plant CC pools, `cc_mlf` 0.209 (measured, frozen), min-up 15 h, min-down 8 h.
- NREL start costs, with the P1 startup markup zeroed on members.
- Members are `gas_cc` / `gas_ct` outside the CHP groups (`reserves/spec.py` posture body).

**EXR (SPP-107, unchanged):**
- MMU offer-side unavailability bands on post-outage availability.
- The economic → emergency slice is a per-zone `emergency_band` pool at shed price − ε.

**Rule 19 (D-2 enumeration for CC and CT, which the posture touches):**
- What already floors these classes on the keeper is the SPP-100 CHP-scope floor, on CHP groups only. The
  posture excludes CHP groups, so there is no stacking.
- EXR is an availability (ceiling) mechanism, not a floor. Its `emergency_band` pool is fuel code 17, outside
  the posture member set.
- The two act on different sides of the same units: a floor via commitment, a ceiling via availability.
  They are one phenomenon each.

## 2. Retest premise (rule 28: new evidence for an `R` cell)

- **Why the cell is R.** `spp_commitment_posture` is R as "tested-but-unpaired" (SPP-102 / SPP-103). The
  posture cuts the over-priced body (−$0.31 to −$0.58/MWh). That breaks C3a 2024 (−8.6 → −10.3 %), because the
  2023–25 train years pass only by SPP-79's body/upper-tercile cancellation.
- **What SPP-103 named as a valid pair.** A structural, measured upper-tercile mover whose lift is **larger in
  2023–25 than in 2019–20**.
- **The new evidence.**
  - SPP-104 (`spp_ct_lole_efor`) and SPP-106 (`spp_mmu_offer_unavailability`) have since been **solved** as
    upper-tercile movers. EX's measured upper tercile is +0.60 / +1.40 / +1.16 $/MWh in 2023/24/25
    (RESULT-spp-106 §1).
  - SPP-107 EXR is that mover with its two definitional repairs.

## 3. Pre-registered readings (zero LP, additive; plan §3.4 steps 1–2)

**Sources:**
- **Posture Δ:** SPP-102's solved legs (RESULT-spp-102 §1 / DESIGN-spp-103 §1). The C3a points are the solved
  scorer values where published (2019, 2020, 2024). Elsewhere they are Δprice ÷ the year's RT mean, from
  `_spp_closeout_c3c_decomposition.json`.
- **EXR Δ:** SPP-107's DESIGN prediction (its PRECOMMIT §2). §4 replaces it with SPP-107's **solved** Δ before
  any launch.

| year | keeper C3a | posture ΔC3a (pts) | EXR ΔC3a (pred.) | **PAIR C3a (pred.)** | posture Δupper $ | EXR Δupper $ (pred.) | **PAIR Δupper $** |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019 | +11.5 % | −1.5 | +1.6 | **+11.6 %** | −0.04 | +0.46 | +0.42 |
| 2020 | +27.5 % | −2.6 | +1.8 | **+26.7 %** | −0.05 | +0.34 | +0.29 |
| 2021 | +6.5 % | −1.0 | +3.0 | **+8.5 %** | +0.04 | +0.19 | +0.23 |
| 2022 | −5.8 % | −1.3 | +2.7 | **−4.4 %** | −0.04 | +0.67 | +0.63 |
| 2023 | −6.7 % | −1.5 | +1.4 | **−6.8 %** | −0.00 | +0.28 | +0.28 |
| 2024 | −8.6 % | −1.7 | +0.9 | **−9.4 %** | −0.01 | +0.06 | +0.05 |
| 2025 | −5.4 % | −1.3 | +2.1 | **−4.6 %** | −0.03 | +0.27 | +0.24 |

**Readings, on these predictions:**

1. **§3.4 step-2 gate "2024 C3a within ±10 %": passes on the prediction, with only 0.6 pt of margin.**
2. **SPP-79's pairing condition (2023–25 lift > 2019–20 lift): FAILS on EXR's DESIGN prediction.**
   - EXR's mean predicted Δupper is +0.20 in 2023–25 against +0.40 in 2019–20 (PAIR: +0.19 against +0.36).
   - EXR's repairs are predicted to shrink EX's 2023–25 upper-tercile lift. That lift was the reason it
     qualified as a pair.
   - This is the decisive pre-solve risk. It is why §4 gates the launch on SPP-107's solved numbers.
3. **"2020 C3b falls" (direction only): expected.**
   - Posture alone took it 0.343 → 0.320.
   - EXR's 2020 effect is small (+0.26 $/MWh, all hours).
4. **Validation rows (reported, never the basis).**
   - C4 gas 2021 is expected to PASS: posture alone 0.307 → 0.281.
   - C1 CC_REGULAR 2021 moves toward band, from −9.65 toward about −7.6 TWh.
   - C3a 2019/20 stay FAIL. They are ledgered as commitment-state per plan §3.4 step 5 if the pair is not
     promoted, and are not chased.

## 4. Launch gate and kill rules (fixed now)

The parent evaluates these at zero LP, once SPP-107's composed RESULT exists. They are re-based on the post-W0
keeper if W0 moves SPP's keeper.

| # | rule | action if it fires |
|---|---|---|
| K1 | SPP-107 EXR is not recommended for promotion by its own §6 rule (E1–E5), **or** the owner declines it | **do not launch.** The pair requires EXR. The posture stays R, and the route goes to §3.4 step 5 (ledger). |
| K2 | Re-run §3 with SPP-107's **solved** per-year ΔC3a and Δupper. Any 2023–25 PAIR C3a falls outside ±10 % | **do not launch.** Record the computed table. |
| K3 | With solved EXR Δupper, the mean over 2023–25 ≤ the mean over 2019–20 (SPP-79 / SPP-103 condition) | **do not launch.** By SPP-103's own test the pair is not a pair. Record and route to the step-5 ledger. |
| K4 | Pre-launch shard check on a `fleet_only` rebuild of 2024: (i) no postured CC pool's min-load floor exceeds its EXR-cut availability in any hour; (ii) no `emergency_band` row is a posture member | **do not launch.** That is an interaction bug: report it and do not repair it in this lane. |

**If K1–K4 all clear, the solve plan is:**
- Seven shards, 2019–2025, one year each (rule 36). All pinned to one full 40-character SHA on this branch and
  launched in one message via `scripts/shard_prompt.py --all-years`.
- `replay_keeper.py <post-W0 SPP keeper> --years <Y> --set spp_commitment_posture=true --set
  spp_mmu_offer_unavailability=true --set spp_mmu_offer_repair=true --out-dir results/calibration/spppair_<Y>`.
- Each shard pushes its full bundle, including `dispatch/<Y>_P1.parquet` (rule 34).
- The parent composes, scores and attests, and solves nothing (rule 32).

## 5. Expectations (gated) and recommendation rule

**Control:** the incumbent keeper's committed bundle (rule 29(b)). If SPP-107 EXR is promoted first, the
control is the EXR keeper. The pair is then "+ posture" alone, and every number above re-bases to it.

| # | expectation |
|---|---|
| E1 | shard check PASS ×7 (SPP-102 posture checks + SPP-107 EXR checks, both) |
| E2 | Optimal within budget, every year |
| E3 | no year's unserved energy rises > 500 MWh over the control |
| E4 | D-4: no FAIL row the control does not carry |
| E5 | train 2023–25 stays CALIBRATED; no C1 / C3a / C3b / C4 status flip in 2023–25 |
| E6 | 2020 C3b falls (direction) |

**Recommendation rule:**
- **RECOMMEND PROMOTE iff E1–E5 hold.** The basis is rule 1: real commitment physics on measured parameters,
  plus the MMU's own classes, with zero free parameters.
- **E6 failing** is reported and does not change the recommendation.
- **Otherwise RECOMMEND AGAINST.**
- **Ledger route if the pair fails or never launches:** the C3a 2019/20 and C3b 2020 body over-price is
  ledgered as a commitment-state limit (plan §3.4 step 5; §5.2 SPP row: "accept the ledger after the pairing
  span").
- The owner decides (rule 31).

## 6. Reported, not gated

- Per-year ΔC3a / C3b / C3c, and class TWh for CC_REGULAR, COAL_PRB, CT_PEAKER and ST_GAS.
- Δprice for all hours and for the body and upper tercile.
- Online CC capacity against SPP's hourly online-capacity-by-fuel series where landed (a D-4 conduct read,
  never an input).
- **Plan row 0c:** `_spp96_reserve_coopt_phase0.py` re-run on the PAIR legs. It reports reserve-eligible
  headroom under a commitment state, against the ≥ 88 bind-hour bar. That re-opens `energy_reserve_coopt` (I)
  only if the bar is met.

## 7. Year set (rule 35)

SPP's registered years are 2019–2025. All seven are solved, and a promotion that shrinks the set is refused.
