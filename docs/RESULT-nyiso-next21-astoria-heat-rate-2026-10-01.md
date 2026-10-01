# RESULT — NYISO-NEXT-21: Astoria on its merged CEMS meter — 2026-10-01

Pre-registration: `docs/PRECOMMIT-nyiso-next21-astoria-heat-rate-2026-10-01.md`, merged to `main` as pin `fdc41f36` **before** any solve. Phase 0: `docs/FINDING-nyiso-next21-d4-rows-and-astoria-heat-rate-2026-10-01.md`.

**Runs (registered, rule 15):**
- `2026-10-01-nyisonext21-astoria-hr-span`, bundle `nyisonext21_span`, 2022–2025.
- `2026-10-01-nyisonext21-astoria-hr-2021`, bundle `nyisonext21_2021`.

**The arm:** the keeper's recipe with zero `ScenarioConfig` deltas, on the re-derived `campd_st_heat_rates_NYISO.csv` (Astoria 9.449 → 11.18–12.07).

## 1. Gates — all pass in all five years

| gate | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| G-1 leg acceptance (pin, recipe, inputs) | ✓ | ✓ | ✓ | ✓ | ✓ |
| G-2 Astoria TWh: arm < keeper | 0.50 < 2.08 | 1.48 < 3.05 | 1.36 < 2.88 | 1.43 < 2.40 | 1.83 < 2.92 |
| G-3 zone demand ±0.1 GWh; slack ≤ +1 GWh | ✓ | ✓ | ✓ | ✓ | ✓ |
| G-4 C6 / C8 | ✓ | ✓ | ✓ | ✓ | ✓ |
| G-5 no new D-4 row | ✓ | ✓ | ✓ | ✓ | ✓ |

Record: `results/calibration/_nyisonext21_gates.json`.

## 2. What moved (reported, not gating)

**Astoria vs CAMPD, TWh** (arm / keeper / CAMPD): 2021 0.50 / 2.08 / 0.72; 2022 1.48 / 3.05 / 0.89; 2023 1.36 / 2.88 / 0.77; 2024 1.43 / 2.40 / 0.92; 2025 1.83 / 2.92 / 1.35. The keeper's error of +1.0 to +2.2 TWh closes to −0.2 to +0.6 TWh.

**NYC steam total (Astoria + Ravenswood + Arthur Kill), TWh** (arm / keeper / CAMPD): 2021 2.16 / 3.42 / 2.17; 2022 3.42 / 4.76 / 2.47; 2023 7.11 / 7.88 / 2.74; 2024 4.36 / 5.16 / 2.95; 2025 5.03 / 5.91 / 4.58. As predicted, the total falls less than Astoria does. The 2023 residual is Ravenswood (its +2.6 TWh is untouched).

**D-4 FAIL rows:** 11 → 9. Both Astoria bridge rows clear (2021, 2024). No new row. Danskammer, Saranac, Athens and Roseton are unchanged, as predicted.

**Criteria (arm vs keeper):**

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| C3a mean LMP | **+10.4 %** (+9.2) | +3.8 (+2.4) | +6.5 (+5.4) | −0.3 (−1.1) | −7.9 (−8.6) |
| C3b NRMSE | 0.155 (0.147) | 0.161 (0.158) | 0.138 (0.132) | 0.118 (0.117) | 0.143 (0.147) |
| C3c | PASS | CAVEAT | CAVEAT | CAVEAT | CAVEAT |

C1, C2, C4, C6 and C8 PASS in every year, both arms. 2021 ST_GAS class −1.99 → −2.99 TWh (PASS).

**Determinations:**
- span: **CALIBRATED** (unchanged; C3c the lone ledgered caveat);
- 2021: CALIBRATED → **NOT-YET**, on C3a +10.4 % against a ±10 % band.

Under rule 30 (c), promoting both runs would make the **ISO** NOT-YET.

## 3. Reading

- **The repair does what it should.** Astoria was the model's cheapest NYC steam because of a selection-biased measurement, not because of anything about the plant. On its own meter it runs within 0.6 TWh of CAMPD in every year. It was 2.2–3.7× before.
- **Prices rise everywhere by 0.7–1.4 pts.** Pricing Astoria correctly raises the cost of the NYC supply stack. The years the keeper already over-priced (2021–2023) move further over; the under-priced years (2024–2025) move toward actual.
- **Rule 14 reading.** The keeper's price level in 2021–2023 was partly carried by an underpriced Astoria. The accurate input exposes that, and it is not to be buried back in the input. The 2021 over-price is now an open root-cause object of its own.
- **Confound, stated.** The shards solved on the pinned HiGHS 1.14.0. The keeper solved on 1.15.1 (audit E14, which the handoff asked this lane to clear). Astoria's move is far outside any solver-version effect: offer +12–22 %, energy −35 to −76 %. The sub-point price moves cannot be split from the version change without a keeper re-solve on the pinned stack.

## 4. Promotion

**Pre-registered rule:** promote iff G-1 to G-5 hold — they do. **But** the PRECOMMIT also says a determination downgrade in any year goes to the owner first. **Owner decision pending.**

**Retrievability (rules 31 / 34(e)):**
- The two registered bundles, sidecars and payloads are committed to `main` with this lane's PR.
- The per-year legs are gitignored, provenance SHAs in `.gitignore`. A leg not on `main` costs a re-solve (~45 min per shard, parallel).
