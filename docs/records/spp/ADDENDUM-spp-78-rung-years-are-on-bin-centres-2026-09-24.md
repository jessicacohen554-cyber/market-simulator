# ADDENDUM — SPP-78: in 2019–2022 SPP's thermals are on HEAT_RATE_BINS bin centres, not eGRID

**Zero LP. Pushed before any shard is launched or any solve number exists.** Amends
`PRECOMMIT-spp-78-measured-heat-rates-2026-09-24.md` (pushed at `fe318fd8`). Phase-0 numbers:
`results/calibration/_spp78_phase0.json`; instruments `scripts/probes/_spp78_arm_fleet_check.py`,
`scripts/probes/_spp76_crossover_hr.py` (unmodified).

## 1. What phase 0 found

**Artifacts (P1 PASS).** The three derives, unmodified, default window 2023–25:

| class | ok plants | covered MW | eGRID → measured (cap-wtd, net) |
|---|---:|---:|---:|
| CC_REGULAR | 16 / 20 (3 `steam_not_metered`, 1 `boundary_above_band`) | 8,114 | 7.802 → 7.576 (−2.89 %) |
| ST_GAS | 25 / 27 (2 `capacity_pairing_mismatch`) | 9,669 | 11.628 → 11.297 (−2.85 %) |
| COAL | 26 / 26 | 18,810 | 10.834 → 10.651 (−1.69 %) |

**Arm check (zero-LP fleet rebuild, control vs arm, every year): PASS.** Uncovered rows move by
exactly 0.0; every covered (plant, class) takes one ratio (spread ≤ 2e-16) — a replacement, not a
stack; 284–289 rows / 35.8–36.6 GW covered; the 0.93 band and tranche multipliers are untouched.

**But the base being replaced differs by year.** In 2023–25 the control rows carry eGRID PLHTRT (the
arm ratio equals `measured / eGRID` to 4 dp). **In 2019–22 they do not.** The committed
`data/raw/eia-860/vintage_{2019,2021,2022}/eia860_generators.parquet` have **no `heat_rate` column**
and `vintage_2020`'s is **all-null**, so the loader (`eia860.py` line ~1379) falls back to
`HEAT_RATE_BINS` bin centres for every thermal: every ST_GAS row at 10.30, CC at 7.5 / 6.7 / 6.3.
Blob hashes match `main`; this is the committed state, not a hydration artefact. (FINDING-spp-60
§D1 says 2021/2022 "carry one" — at HEAD they do not.)

Consequence, capacity-weighted offer heat rate, arm vs control:

| years | CC_REGULAR | ST_GAS | COAL_PRB |
|---|---:|---:|---:|
| 2019–22 | **+3.2 %** | **+9.7 to +9.9 %** | +1.4 % |
| 2023–25 | −2.3 % | −2.0 to −2.6 % | −1.7 % |

**SPP-76's rung-year numbers were computed on the wrong base** (it scaled by `measured / eGRID`
where the fleet carries bin centres). Its 2023–25 numbers reproduce exactly. Its conclusion for the
crossover still holds (see §2: ΔCOAL_PRB 2021/22 is −0.04 / +0.15 TWh), but "the model's eGRID heat
rates" is false for 2019–22.

**Rule 14 reading.** In the rung years the arm replaces a class-default estimate with the plant's own
meter — a larger accuracy gain than in the span, not a smaller one. The ~5–20 % of MW per class the
artifacts do not cover stays on bin centres; the missing eGRID join in the old vintages is a
**shared-data defect** (it reaches every ISO's 2019/2021/2022 vintage fleet) and is **routed, not
repaired here** (not SPP's to widen).

## 2. Zero-LP merit proxy on the TRUE base (TWh, arm − control)

| year | COAL_PRB | COAL_LIG | CC_REG | ST_GAS | CT_PEAKER | g* $/MMBtu |
|---|---:|---:|---:|---:|---:|---|
| 2019 | +0.48 | −0.32 | −0.52 | −0.43 | +0.68 | 2.80 → 2.74 |
| 2020 | +0.85 | −0.31 | −1.01 | −0.53 | +0.89 | 2.71 → 2.66 |
| 2021 | −0.04 | −0.21 | −0.29 | −0.23 | +0.68 | 2.63 → 2.59 |
| 2022 | +0.15 | −0.03 | −0.54 | −0.71 | +1.01 | 3.20 → 3.14 |
| 2023 | +0.38 | −0.06 | +0.69 | +0.19 | −1.15 | 2.95 → 2.97 |
| 2024 | +0.21 | +0.02 | +0.49 | +0.27 | −0.97 | 2.80 → 2.82 |
| 2025 | +0.53 | −0.16 | +0.50 | +0.01 | −0.84 | 2.71 → 2.73 |

ST_GAS and CT are indicative only (proxy fidelity −30 to −48 % / −3 to −16 %, SPP-76 §3).
Class mean offer moves in 2019–22: CC +$0.50–1.53/MWh, ST_GAS +$2.30–7.05/MWh, PRB +$0.30–0.35.

## 3. Amended predictions (replace PRECOMMIT §5 where named; the rest stand)

| # | amended prediction |
|---|---|
| P2 | **Superseded.** It reproduced SPP-76's proxy exactly (Δ = 0.00 every year), which is now known to be the wrong base for 2019–22. §2 above is the registered proxy. |
| P3 | Solved Δ COAL_PRB has the §2 sign in every year where \|proxy\| ≥ 0.3 (2019, 2020, 2023, 2025); \|Δ\| ≤ 1.5 TWh every year. |
| P5 | 2023–25: ΔCC_REGULAR ≥ −0.5 TWh. **2019–22: ΔCC_REGULAR ≤ +0.3 TWh** (CC gets dearer). |
| P6 | **C3a 2020 RISES** (arm − control > 0) by 0.5–5 pp. Demand-weighted mean price rises in all four rung years and falls in all three span years. |
| P6b | C3a 2023–25 falls by 0.3–3 pp each. |
| P4, P7–P10 | unchanged. |

The promotion rule (PRECOMMIT §6) is **unchanged**, and this addendum makes its "gates are not a
criterion" clause bind in practice: P6 now predicts a failing rung row (C3a 2020, +15.5 %) moves
**further out**. That is reported at full magnitude with its owner (price level: SPP-70 R-bc /
SPP-74), and is not a reason to leave a bin-centre estimate in place of a meter (rule 14).
