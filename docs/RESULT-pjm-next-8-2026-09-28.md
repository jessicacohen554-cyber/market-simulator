# RESULT — PJM-NEXT-8: exit-cohort repair of the CAMPD outage layer (PROMOTED on structure), 2026-09-28

**New keeper: `2026-09-28-pjm-next8-exitfix`.**
- **Bundle:** `results/calibration/pjmnext8_xf_span`, 2019–2025; one shard per year at `e9fc1a5e`, composed at zero LP.
- **Prior keeper:** `2026-09-28-pjm-next-7-virtual`, pruned (rule 35). Year set before and after: 2019–2025.
- **Control:** the prior keeper's committed bundle plus G-DRIFT, every hunk INERT (rule 29(b)); PRECOMMIT §4.
- **Records:** pre-registration `docs/PRECOMMIT-pjm-next-8-exitfix-2026-09-28.md`; card-1 phase 0 `docs/FINDING-pjm-next-8-cc2023-phase0-2026-09-28.md`.
- **Owner cards:** card 1 *"Diagnose east price"*; card 2 *"Build + solve"*; promotion *"Promote on structure"*.

## 1. What changed (one flag, zero DOF)

`unit_outage_exit_cohort_repair` reads `campd-unit-outages-rederive-peakerkeep-exitfix-unitfuel-PJM.csv` (sha256 `02d565cd`). Its control reproduces the prior keeper's file byte-for-byte.
- (a) unit capacity from the solve year's own EIA-860 vintage (Chalk Point coal 16/35 → 364 MW);
- (a′) no window for a unit whose EIA prime mover cannot belong to its routed bin (Possum Point oil ST unit 5 off the CC bin);
- (b) dated exit bins derated over their own capacity (Mansfield unit 3);
- (c) full-year windows for exit-cohort units dark all year (Mansfield 1–2, Sammis 1–2).

## 2. Prediction check (pre-registered)

| row | predicted | measured |
|---|---|---|
| COAL_BIT 2019 (C1) | +10.5 to +13.6 | **+10.61** |
| ΔCOAL_BIT 2020 | −0.4 to −0.6 | −0.67 |
| \|ΔCOAL_BIT\| 2021–2023 | ≤ 0.3 | 0.03 / 0.32 / 0.22 |
| 2024, 2025 | byte-identical | **0.000 MW max** |
| ΔCC_REGULAR 2019 | +1 to +4 | +3.94 |

No falsifier fired (2022's 0.32 is a hair over the 0.3 bar set for 2023; 2023 itself is 0.22).

## 3. Headline

| | prior keeper | **PJM-NEXT-8** |
|---|---|---|
| Training span 2023–25 alone | NOT-YET (CC_REGULAR 2023 +8.40) | NOT-YET (CC_REGULAR 2023 +8.48) |
| Run-level failing rows | 12 | **14** |
| COAL_BIT 2019 | +17.81 F | **+10.61 F** |
| CC_REGULAR 2019 | +6.9 pass | **+10.86 F (new)** |
| C3a 2019 | pass | **+11.8 % F (new)** |

Why promoted: rule 14 — the accurate outage input stays. The 2019 CC and price rows were being masked by ~7 TWh of phantom coal on capacity that was actually offline; they are existing defects, not caused by this repair.

## 4. Card 1 (zero LP): CC_REGULAR 2023 is structural

The +8.4 is EMAAC +9.0 / Central_PA +5.1 / ComEd +5.5 against Dominion −12.8. Real 2023 prices fall east→south (NJ −$5.6 congestion → Dominion +$2.8); the reduced network has no binding east-to-south boundary, so model EMAAC rides the system price (~$7 too high). No measured input in the repo fixes it. Detail: FINDING §§1–5.

## 5. Retrievability (rule 34(e))

- Keeper bundle, sidecar and payload: on `main` via this lane's PR.
- Per-year legs: gitignored, not on `main`. Provenance only (not a recovery route): 2019 `be56b20c`, 2020 `0b1e6e56`, 2021 `af82f990`, 2022 `d872a54e`, 2023 `4783e8ff`, 2024 `d7256fa4`, 2025 `4c5cf336`. Any leg = a re-solve (~45 min per shard).

## 6. Next (PJM-NEXT-9)

1. The missing east-to-south congestion boundary (CC_REGULAR 2023 and the every-year Central_PA/ComEd over, Dominion under): fetch 2023–2024 PJM binding constraints, rank facilities by NJ-hub congestion — zero LP first.
2. 2019 CC_REGULAR +10.86 and C3a +11.8 %, now unmasked.
3. COAL_BIT 2021 (commitment-structure, design card first), CT_PEAKER 2021, CC_REGULAR 2020/2022, C3a 2020/2022, C3b 2022.
