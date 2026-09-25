# RESULT — PJM-NEXT-2: coal over-dispatch, CC_REGULAR 2024, TMI 2019 (2026-09-25)

Run **`2026-09-25-pjm-next-2-joint`** (bundle `results/calibration/pjmnext2_joint_span`, 2019–2025, one shard per
year at `d25a3ebb`, composed at zero LP). Control: the keeper `2026-09-25-pjm-next-c1`'s committed bundle (rule 29(b)
form 4; G-DRIFT byte-identical, PRECOMMIT card 1 §5). **Not promoted** — promotion is the owner's call (rule 31).

Pre-registrations: `docs/PRECOMMIT-pjm-next-2-card1-outage-membership-2026-09-25.md`,
`…-card2-basis-scope-…`, `…-card3-tmi-dormancy-…`, `…-joint-…`.

## 1. Determination (same scorer, same benchmark)

Both runs read **NOT-YET**. In 2023–2025 both fail only C1: CC_REGULAR 2024 improves from −14.68 to −10.07 TWh, but
it is still outside its band. The training-span status therefore does not change.

| criterion-year | keeper | joint | |
|---|---|---|---|
| C1 CC_REGULAR 2024 | −14.68 FAIL | **−10.07 FAIL** | better, still out of band 8 |
| C1 COAL_BIT 2019 / 20 / 21 / 22 | +28.42 / +19.40 / +32.57 / +10.33 FAIL | **+12.91 / +10.47 / +20.73 / +8.09 FAIL** | −55 / −46 / −36 / −22 % |
| C1 CT_PEAKER 2021 | −10.30 FAIL | −8.19 FAIL | better |
| C1 CC_REGULAR 2022 | +10.91 FAIL | **+14.90 FAIL** | **worse** (card 2 alone: +3.0) |
| C1 CC_REGULAR 2019 / 20 / 21 / 23 | −7.73 / −5.64 / −5.40 / −7.01 | −0.34 / +0.72 / +4.27 / −2.71 | all PASS both |
| C3a mean LMP 2019 | +6.8 % PASS | **+10.7 % FAIL** | **new fail** |
| C3a mean LMP 2020 | +15.8 % FAIL | +19.4 % FAIL | **worse** |
| C3a 2021 | −0.2 % | +3.8 % | PASS both |
| C3b NRMSE 2020 | 0.168 PASS | **0.205 FAIL** | **new fail** |
| C3b NRMSE 2019 | 0.095 | 0.126 | PASS both |
| C3a / C3b 2022–2025 | | | unchanged within ±1 pt |
| C8 CT_PEAKER forced share 2021 / 2022 | 41.5 / 24.3 % | 32.7 / 27.6 % | grounded both |
| nuclear 2019 | −5.9 TWh | −0.9 TWh | TMI-1 now 5.0 TWh |
| C2, C4, C6 | PASS | PASS | |

D-10 free-class C1: 15/16 in both runs for 2023–2025; 27/33 in both runs for 2019–2022. The count of passing
class-years is unchanged, but the size of the misses falls.

**Why prices go up in 2019–2020.** The windows withdraw ~42 TWh of 2019 coal capacity-hours that the model had been
treating as always available. The marginal unit moves up the gas stack, so the mean LMP rises. 2019–2020 prices were
already high in the keeper (+6.8 % / +15.8 %), so this pushes 2019 over the band. That is consistent with the
earlier diagnosis: the keeper's pre-2023 price level was partly held down by capacity that was really idle. By
rule 1 a structurally correct input stays even when the fit gets worse. The remaining pre-2023 price over-shoot is
a separate root cause — the reference-price interface freeze (matrix, pjm-171).

## 2. Attribution (single-flag legs, same pin)

- **Card 1** (outage membership): COAL_BIT 2019 +28.4 → +14.5, 2020 +19.4 → +10.5; CC_REGULAR 2019 −7.7 → +1.5. It
  has almost no effect in 2023–2025, as predicted.
- **Card 2** (basis skip-923): 2023 CC_REGULAR −7.0 → −2.8, 2025 −9.8 → −6.2, and 2024 mostly (joint −14.7 → −10.1).
  CT_PEAKER falls with it (2025 +8.9 → +4.1). It is inert before 2022 by construction. In 2022 it raises CC_REGULAR
  +10.9 → +13.9.
- **Card 3** (TMI): nuclear 2019 −5.9 → −0.9 TWh; COAL_BIT 2019 −1.8 TWh.

## 3. What is left

- **COAL_BIT 2021 +20.7 TWh** comes mostly from surviving plants (Zimmer 2021, Rockport, Keystone/Conemaugh). This is
  offer level versus a CC stack that 2021 gas prices ($3.72) should have made more competitive. It is not a
  membership problem.
- **CC_REGULAR 2024 −10.1 TWh**:
  - Dominion/SWMAAC under-dispatch remains.
  - The Montour per-unit fuel-routing defect remains: +4.1 TWh of cheap coal-slice output in 2024. That belongs to
    the card-4 extract family.
- **Card 4** (the F2 outage-extract overwrite) is still blocked on the owner. Two things must come first:
  - The COAL-SUB deriver fix found here is now on `main` (miso-273). Without it, a re-derive loses 83 % of coal
    outage-days.
  - The full re-derive also moves CC_REGULAR windows by +20 TWh and ST_GAS by −26 TWh of capacity-hours in 2019, which
    needs its own review.
- `retiree_cems_cap` (armed in the keeper) is inert under `eia860_vintage_tracks_solve_year`: zero caps in-run.
  Candidate for deletion or repair (rule 26); the owner's call.

## 4. Governance

- **Attestation:** DOF ledger carried verbatim, zero entries added (`scripts/gen_pjmnext2_attestation.py`).
  `authorized_price_tuning.used = false`.
- **Registered `--no-prune`.** The keeper is unchanged.
- **Retrievability (rule 34(e)):** the composite's slim set (21 MB) is committed on this branch. The seven per-year
  legs, including their dispatch parquets, are on local disk and gitignored (rule 31). Leg provenance SHAs:
  2019 79d3492c, 2020 967b4333, 2021 938daefc, 2022 11e75a4d, 2023 d91d5d13, 2024 4e40ace0, 2025 71836f90.
  Promotion from this state costs **zero re-solves** while this session is alive; after it ends, the dispatch
  parquets are gone and promotion would cost seven one-year solves (~15 min each, in parallel).
- **Shards:** all 26 launched sessions are archived. The branches listed below remain for the owner to clear:
  `claude/pjmnext2-{c1,c2,c3,joint}-*`.
