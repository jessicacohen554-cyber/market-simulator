# RESULT — PJM close-out R-13: `gas_offer_margin_anchor_vintage` retest on the W0 keeper — REJECTED (R)

Lane `closeout-PJM`, 2026-10-02.
- **PRECOMMIT:** `PRECOMMIT-pjm-closeout-r13-anchor-vintage-2026-10-02.md`, plus the post-W0 addendum `…-addendum-w0-2026-10-02.md`.
- **Control:** keeper `2026-10-02-w0-pjm-fix2` (`results/calibration/w0_pjm_span`). G-DRIFT found every hunk INERT, so there was no control solve.
- **Arm:** one `--set gas_offer_margin_anchor_vintage=true`, one shard per year, pinned at `8463c768f174bbd8216fdab53dccd10c3717f3c1`.
- **Desk ruling:** **R**. Nothing goes toward promotion.

## Legs (transport only; recorded by full SHA, rule 33)

| year | branch @ commit | memory peak (rss+swap) |
|---|---|---|
| 2019 | `claude/closeout-pjm-r13-2019` @ `e77fd189b75244af3fe56a2dce65c725fd8f7cc1` | 18.11 GiB |
| 2020 | `claude/closeout-pjm-r13-2020` @ `458e87e70b1e25e121355f02ba047fd1a62b5592` | 17.88 GiB |
| 2021 | **not solved.** OOM (exit 137) twice in a 23.4 GiB container, once in the P1 rebuild and once in the P0 build. The desk ruled not to relaunch after the kill. | — |
| 2022 | `claude/closeout-pjm-r13-2022` @ `2202e7b0650e693dae0191b9095c94914942c52d` | 17.86 GiB |
| 2023 | `claude/closeout-pjm-r13-2023` @ `993a9174de6a72b9c8511317b79c5053691e3fb2` | 17.46 GiB |
| 2024 | `claude/closeout-pjm-r13-2024` @ `2e5fd5bb54a33de1367c03ef8fe39a29231f08f2` | 17.06 GiB |
| 2025 | `claude/closeout-pjm-r13-2025` @ `db4fe57bc315464a614da5801ffde311f4f2d9ff` | 16.96 GiB |

Because 2021 is unsolved, this span is not registrable (rule 16), and no dashboard entry was made. The bundles are not on `main` (`.gitignore`, rule 29c), and promoting them would require re-solving 2021 first.

Shard-infrastructure lessons, now carried in every PJM shard prompt:
- **Step 0:** `git checkout --detach <sha>`. The platform ignored `source_revision` and booted the shards at `main`.
- **Virtual bids:** `fetch_pjm_da_virtuals.py --years <y> --feeds hrl_da_incs_decs` fetches the gitignored DataMiner2 virtual-bid parquets.
- **Swap ordering:** run `prepare_solve_container.py` first, so swap is sized while disk is still free.

## STOP gates (fixed before any solve; probe `scripts/probes/_pjmco_r13_gates.py` → `results/phase0/pjm/_pjmco_r13_gates.json`)

| year | pred. shift $/MWh | S3 median gas Δmc | S4a max non-gas Δmc | S4b(i) | S4b(ii) Δdisplaced / ΔCC+CT TWh | S4b(iii) flip-band | S4b(iv) ΔCOAL / ΔGAS TWh |
|---|---|---|---|---|---|---|---|
| 2019 | −0.40 | 0.000 (PASS, inert) | 13.46 **FAIL** | PASS | +0.27 / −0.30 PASS | 1.00 PASS | +0.07 / −0.11 PASS |
| 2020 | −2.42 | −0.065 **FAIL** | 18.45 **FAIL** | PASS | +1.24 / −1.32 PASS | 1.00 PASS | −0.51 / +0.44 **FAIL** |
| 2022 | +10.58 | +0.353 **FAIL** | 4.92 **FAIL** | PASS | −1.35 / +1.14 PASS | 1.00 PASS | +1.54 / −1.75 PASS |
| 2023 | −0.26 | 0.000 (PASS, inert) | 50.00 **FAIL** | PASS | +1.19 / −1.21 PASS | 1.00 PASS | −0.45 / +0.43 **FAIL** |
| 2024 | −1.38 | 0.000 **FAIL** | 50.00 **FAIL** | PASS | +1.65 / −1.44 PASS | 1.00 PASS | −0.89 / +1.09 PASS |
| 2025 | +1.71 | 0.000 **FAIL** | 6.67 **FAIL** | PASS | −0.37 / +0.30 PASS | 1.00 PASS | +0.29 / −0.36 PASS |

S1 and S2 are construction identities covered by pjm-169's unit tests and were not re-scored. S5 was not scored, because the span is not registrable. **The kill rule fires on S4a in every year, and on S3 in 2020, 2022, 2024 and 2025.**

## What the gates found

1. **S4a's breach is a charter-wording defect, not an anchor leak.** Every non-gas Δmc sits on a coal **committed** rung as a month-constant adder per unit. In 2020 that is 26 % of committed-rung hours. Coal econ, mustrun, peak and sync rungs are byte-identical between arm and control. The committed rung's monthly cost follows the P0 run pattern, so any change to the gas offer moves it endogenously. S4a as written ("every non-gas unit's P1 mc identical") could never pass on this keeper. **A re-charter starts from an S4a that exempts that endogenous committed-rung adder** (desk ruling).
2. **The anchor's footprint has shrunk since pjm-169.** The predicted median gas shift assumed pjm-169's 2022 population, where 981 compressed tranches moved +$10.57. On the W0 keeper, the 2022 median gas Δmc is +$0.35. About half of all gas units are untouched; among the 851 units moved in 2020, the median is −$7.0.
   - The reason: since PJM-NEXT-5 (2026-09-27) the CC_LIKE midcurve **shape form** prices the CC econ rows directly.
   - The gas-offer margin term now reaches mainly CT/ST tranches, so the S3 prediction's population no longer exists. The gate fails as written.
3. **The arm is near-inert on price.** Load-weighted mean price, arm vs keeper, against the committed actual RT mean (`results/phase0/pjm/_pjmco_r13_c3a_readout.json`):
   - This is a plain time-mean actual, **not** the rubric's C3a basis, and is reported only. The arm−keeper difference is the readable part.
   - 2020: +17.8 % → +17.4 %.
   - 2022: −4.1 % → −3.1 %.
   - Every other year moves ≤ 0.5 pp.
   - The pre-fixed reading (C3a 2022 ≥ −10 %, 2020 ≤ +10 % on the rubric basis) cannot be scored: the span is not registrable.
4. **Side observations from the legs, recorded but not adjudicated:**
   - 2025: 1,086 MWh unserved, and legitimacy D-2 CT_PEAKER plus D-4 `cc_mustrun_per_plant` FAIL.
   - 2023: rule 20 CT_PEAKER forced share 0.161 > 0.15 (all from `ct_netload_drag`).
   - 2019: 206 MWh unserved.
   - These come from the arm's legs and were not compared against the keeper's own diagnostics.

## Matrix

`gas_offer_margin_anchor_vintage` PJM stays **R**, with this evidence prepended. Re-test condition: a new PRECOMMIT whose S4a exempts the endogenous committed-rung adder and whose S3 population is the tranches the margin term actually reaches on the incumbent keeper.
