# RESULT — PJM-NEXT-7: DA virtual position settled financially (PROMOTED on structure), 2026-09-28

**New keeper: `2026-09-28-pjm-next-7-virtual`.**
- **Bundle:** `results/calibration/pjmnext7_vs_span`, 2019–2025.
- **How it was solved:** one shard per year, all at `f2850356`, composed at zero LP.
- **Prior keeper:** `2026-09-28-pjm-next-6-f2`, pruned (rule 35).
- **Control:** the prior keeper's committed bundle plus G-DRIFT, with every hunk INERT (rule 29(b)).
- **Records:** design `docs/records/pjm/DESIGN-pjm-next-7-virtual-settlement-2026-09-28.md`; pre-registration `docs/records/pjm/PRECOMMIT-pjm-next-7-virtual-settle-2026-09-28.md`.
- **Owner rulings:**
  - *"Design card: settle financially"*;
  - design card: *"A′ P0-DA / P1-RT"*;
  - promotion card: *"Promote on structure"*.

## 1. What changed (one flag, zero DOF)

`pjm_da_virtual_settle_financial`.
- P0 is the DA commitment stage and keeps the measured INC/DEC layer.
- The scored P1, which is gated against RT, zeroes the virtual bounds, because PJM liquidates INC/DEC in RT.
- Every leg's P1 virtual MWh equals 0.

## 2. Headline

| | prior keeper | **PJM-NEXT-7** |
|---|---|---|
| Training span 2023–25 alone | CALIBRATED | **NOT-YET** (C1 CC_REGULAR 2023 +8.40 vs ±8.00) |
| Run-level 2019–25 failing rows | 7 | **9** |

| row (model − actual) | prior | **arm** |
|---|---|---|
| C1 COAL_BIT 2019 | +17.29 F | +17.81 F |
| C1 CC_REGULAR 2020 | +12.75 F | +13.93 F |
| C1 COAL_BIT 2021 | +18.92 F | +17.16 F |
| C1 CT_PEAKER 2021 | −5.76 | **−9.57 F (new)** |
| C1 CC_REGULAR 2022 | +11.25 F | +10.75 F |
| C1 COAL_BIT 2022 | +9.67 F | **+7.12 PASS** |
| C1 CC_REGULAR 2023 | +4.62 | **+8.40 F (new)** |
| C1 CC_REGULAR 2024 | −4.89 | −0.81 |
| C3a 2020 | +18.0 % F | +15.4 % F |
| C3a 2022 | −7.7 % | **−11.5 % F (new)** |
| C3b 2022 | 0.229 F | 0.253 F |
| C3b 2023 / 24 / 25 | 0.125 / 0.129 / 0.140 | 0.164 / 0.157 / 0.172 (pass) |

**Prediction check** (zero-LP envelope, pre-registered):

| row | predicted | measured |
|---|---|---|
| CC_REGULAR 2023 | +9.5 | +8.4 |
| CT_PEAKER 2021 | −9.1 | −9.6 |
| COAL_BIT 2022 | +6.6 (pass) | +7.1 (pass) |

- The falsifier held: in every year Δsupply has the opposite sign to the net virtual position, and |Δsupply| / |net| is 0.72–1.30.
- As predicted, the net-DEC energy came off **peakers first**, so the pre-2023 CC and coal rows barely move.

## 3. Why promoted

- The owner ruled on structure (rule 1): RT physical generation no longer serves financial virtual demand.
- The regression is reported at full magnitude and is not hidden.
- What remains pre-2023 is now a virtual-free physical question.

## 4. Card 3 (coal, zero LP): `docs/records/pjm/FINDING-pjm-next-7-coal-phase0-2026-09-28.md`

**2019.** About 8.3 TWh of phantom COAL_BIT output comes from how the CAMPD unit-outage layer handles the exit cohort. Three measured defects:
- **(a)** Chalk Point coal units carry the GT nameplates (16 / 35 MW), because the post-retirement EIA-860 snapshot has no ST rows.
- **(b)** Mansfield's dated bins dilute each unit's outage share against the whole-plant MW.
- **(c)** Mansfield 1–2 and Sammis 1–2 are dark all year with no window. The fix for this is `campd_dark_unit_year_windows`.

Expected net effect: C1 −3 to −6 TWh in 2019, which is still a FAIL; ≈0 elsewhere.

**2021.** No measured operand explains it. The surplus is loading on units that are actually online, a commitment-structure question.

## 5. Retrievability (rule 34(e))

- The keeper bundle, sidecar and payload are on `main` via this lane's PR.
- The per-year legs are gitignored and are not on `main`.
- Leg SHAs, recorded for provenance only (not a recovery route):
  - 2019 `8a3b5094`
  - 2020 `05cc491f`
  - 2021 `173b48bb`
  - 2022 `2b1ef9b3`
  - 2023 `791f1f8e`
  - 2024 `389fe37a`
  - 2025 `e9a7ab3a`
- Recovering any leg means a re-solve, about 45 min per shard.

## 6. Next

1. **CC_REGULAR 2023 (+8.40) is the only training-span failure.** It is the old +4.6 plus the ~4 TWh that net-INC virtual supply used to displace.
2. **The coal outage-layer fix, parts (a)–(c).**
3. **Pre-2023 CC_REGULAR 2020/2022 and CT_PEAKER 2021.**
