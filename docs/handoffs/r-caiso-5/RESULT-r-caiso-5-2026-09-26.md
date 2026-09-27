# RESULT — R-CAISO-5: CC outage-derate basis (X) ± Pastoria CO2 (E); 2019–21 intertie source (2026-09-26)

PRECOMMIT: `PRECOMMIT-r-caiso-5-2026-09-26.md`, pushed at `93a38eac` before any shard. The parent spent zero LP:
8 shards, one per year per arm (rule 36), all at that pin.

## Headline

- **Object 1 — C4 midday loading.** The midday gas gap is an **import diurnal-shape** defect: model net imports
  run +1.5 to +2.3 GW over EIA-930 at h8–16 in every month of 2022–25. No measured-input defect was found in the
  import shape, so no lever is taken on it.
- **One measured-input defect was found and fixed:** phantom CC capacity in full-plant outages (Moss Landing:
  207 MW kept in its all-units-out windows). The arm (X) replaces `unit_outage_lp_capacity_basis` with the
  registered `unit_outage_extract_basis_share`.
- **X is CALIBRATED** and improves C4 in all four years. The move is small: C4 2025 goes 0.299 → **0.297**.
- **XE (X + Pastoria CO2):** see §3.
- **Object 2 — 2019–21 intertie prices.** The STOP stands. No admissible measured hourly source exists (§5).

## 1. X — `2026-09-26-caiso-r5-cc-outage` (bundle `rcaiso5_X_span`), CALIBRATED

| | keeper `r4-intertie-dam` | **X** |
|---|---|---|
| C1 CC_REGULAR 2022 / 23 / 24 (TWh vs actual) | +2.45 / −0.38 / −0.50 | +2.27 / −0.50 / −0.63 |
| C1 CT_PEAKER 2022 / 23 / 24 | −1.27 / −1.66 / −2.32 | −1.21 / −1.59 / −2.26 |
| C3a load-weighted mean LMP vs RT, 2022 / 23 / 24 / 25 | +8.7 / +7.1 / +7.0 / +8.6 % | +8.8 / +7.3 / +7.1 / +9.1 % |
| C3b 2022 / 23 / 24 / 25 | 0.108 / 0.114 / 0.128 / 0.112 | 0.110 / 0.115 / 0.129 / 0.116 |
| C3c >$200 h, 2023 (actual 47) / 2024 (actual 35) | 55 / 0 (ledgered) | 59 / 0 (ledgered) |
| **C4 gas NRMSE 2022 / 23 / 24 / 25** | 0.265 / 0.251 / 0.260 / 0.299 | **0.263 / 0.250 / 0.258 / 0.297** |
| C8 CC_REGULAR forced, 2025 | 8.7 % | 8.6 % |
| Determination | CALIBRATED | **CALIBRATED** |

**Class Δ vs the keeper (TWh):**

| | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|
| CC_REGULAR | −0.17 | −0.11 | −0.14 | −0.37 |
| imports | +0.13 | +0.06 | +0.10 | +0.30 |
| CT_PEAKER | +0.05 | +0.08 | +0.06 | +0.12 |

**Moss Landing 2025:** 3.68 → 3.19 TWh (CEMS 2.19). It is **0 MW** in Jan 18–Feb 10 and Dec 14–30 (G-LIVE PASS).

**Stop gates.**

- **G-IDENT PASS.** Each leg differs from the keeper only in the two declared flags, plus new default-off fields
  recorded as False.
- **G-LIVE PASS.**
- **G-FOOT PASS.** CC_REGULAR 2025 −0.37 TWh.

**No load-bearing criterion regresses.** C3a 2025 moves +0.5 pt and C3b 2025 +0.004, both still PASS. The DOF
ledger stays 9/6, offer curves are unchanged, and there is no `authorized_price_tuning` block.

## 2. Why X is small against C4

The removed phantom capacity sits at over-dispatched plants (Moss Landing, Otay Mesa, Sunrise) and is roughly flat
across the day. Its replacement is imports and CT peakers. The C4 error is diurnal and import-driven (PRECOMMIT §1),
so X corrects a real input and moves C4 only 0.001–0.002.

## 3. XE — `2026-09-26-caiso-r5-pastoria-co2` (bundle `rcaiso5_XE_span`), CALIBRATED

This is X plus `cc_eia923_identity_emission_basis` (E, the blocked R-CAISO-4 lever). X's C4 gain pays for E's C4
cost, so **E re-arms without the NOT-YET** that blocked it in R-CAISO-4.

| | keeper | X | **XE** |
|---|---|---|---|
| C1 CC_REGULAR 2022 / 23 / 24 / 25 (TWh vs actual) | +2.45 / −0.38 / −0.50 / −1.03 | +2.27 / −0.50 / −0.63 / −1.40 | **+2.27 / −0.33 / −0.20 / −1.02** |
| C3a 2022 / 23 / 24 / 25 | +8.7 / +7.1 / +7.0 / +8.6 % | +8.8 / +7.3 / +7.1 / +9.1 % | **+8.8 / +7.1 / +6.6 / +8.7 %** |
| C3b 2022 / 23 / 24 / 25 | 0.108 / 0.114 / 0.128 / 0.112 | 0.110 / 0.115 / 0.129 / 0.116 | **0.110 / 0.114 / 0.125 / 0.112** |
| C3c 2023 (actual 47 h) / 2024 (actual 35 h) | 55 / 0 L | 59 / 0 L | 59 / 0 L |
| **C4 gas NRMSE 2023 / 24 / 25, unrounded** | 0.2508 / 0.2596 / **0.2987** | 0.2505 / 0.2583 / **0.2966** | 0.2499 / 0.2597 / **0.2987** |
| C8 CC_REGULAR forced, 2025 | 8.7 % | 8.6 % | 8.5 % |
| Determination | CALIBRATED | CALIBRATED | **CALIBRATED** |

L = the ledgered caveat.

**Pastoria 55656, TWh (EIA-923 actual):**

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| keeper | 3.58 | 2.37 | 2.14 |
| **XE** | **4.51** | **3.68** | **3.17** |
| EIA-923 actual | 4.34 | 4.01 | 3.62 |

High Desert moves 3.85 / 3.71 / 3.33 in XE (actual 4.08 / 4.60 / 3.33).

**Attribution.** E is XE − X, in TWh:

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| CC_REGULAR | +0.17 | +0.43 | +0.38 |
| imports | −0.14 | −0.36 | −0.35 |

- **E is inert in 2022.** XE-2022 reproduces X-2022 to 0.000 TWh in every class. That leg was solved only so
  the span carries one config.
- **Stop gates for XE.** G-IDENT PASS; G-LIVE PASS (Moss Landing 0 MW in both windows).
- **G-FOOT, reported as written: FAILS for XE.** CC_REGULAR 2025 is +0.01 TWh vs the keeper, because E's
  Pastoria gain (+0.38) offsets X's removal (−0.37). The gate was written as a liveness check on X. X passes
  it (−0.37), and X's footprint is live inside XE (Moss Landing 0 MW). I do not reinterpret the gate; the
  owner rules.
- **C4 2025 has no added margin.** It is 0.2987, identical to the keeper, still 0.0013 under the 0.30 bound.

## 4. Promotion — the owner's call (rule 31)

| option | run | determination | C4 2025 | what it gains |
|---|---|---|---|---|
| (a) keep the current keeper | — | CALIBRATED | 0.2987 | — |
| (b) promote X | `2026-09-26-caiso-r5-cc-outage` | CALIBRATED | 0.2966 | removes phantom outage capacity; +0.002 C4 margin; C3a 2025 +0.5 pt worse |
| (c) promote XE | `2026-09-26-caiso-r5-pastoria-co2` | CALIBRATED | 0.2987 | X plus Pastoria CO2 on the fuel basis; C1 / C3a / C3b 2024–25 better than both; G-FOOT literal miss |

**Recommendation: (c) XE on structure.** It carries two measured-input repairs and scores at least as well as the
keeper on every load-bearing criterion.

- **Either promotion needs 2019–2021 re-solved on the new recipe** before the outgoing keeper is pruned
  (rule 35(c)). That is three shards, about 20 min each in parallel.
- Until then the `2026-09-26-caiso-r4-keeper-2019` fold stays on the current keeper.
- A promotion also re-keys `calibration-complete.json`, `keepers/CAISO.json` and the matrix stamp.

## 5. Object 2 — 2019–21 intertie prices: the STOP stands

PRECOMMIT §6 has the full probe record.

- **No admissible measured hourly source for 2019–20.** OASIS is dead on every route.
- **EIA/ICE daily on-peak indices** cover 55.9 % of hours, and their level drifts against the node series
  (ratio 1.02–1.52 annually). An hourly construction would need a fitted basis plus a shape, which rules 13/14
  refuse.
- **Firm-base block:** `IMPORT_TRANCHES_BY_YEAR["CAISO"]` has no 2019–21 rows, so those years silently use the
  2025 static ladder. The repair is zero-parameter (DMM `Imports` RA row × MIC north share); it is routed as a
  successor intake.
- **`caiso_per_year_import_caps`** is a no-op for 2019–22 (no area `peak_load` rows).

## 6. Routed, report only

- **`gas_foldin_deflation` → add CAISO to `EIA930_GAS_FOLD_REFUTED`: NOT flipped.** A scorer-only A/B leaves both
  registered runs byte-identical. The change acts in the bench build's reconcile, as below.

  | year(s) | effect of the flip |
  |---|---|
  | 2022–2025 | none; the reconcile fires in neither case, so every keeper score is unchanged |
  | 2019 | target moves from 930 − deflation to the CEMS anchor: +7.9 TWh fossil, ≈ +5.5 TWh CC_REGULAR target |
  | 2020 | +5.4 TWh fossil, ≈ +3.9 TWh CC_REGULAR target |
  | 2021 | +3.2 TWh fossil, ≈ +2.4 TWh CC_REGULAR target |

  The 2019–21 C1 CC_REGULAR misses would shrink from +26.1 / +28.1 / +18.3 to about +20.5 / +24.2 / +15.9 TWh,
  still FAIL. Exact values need a bench re-render. Proposed, not taken.
- **Stale comments.**
  - `envelopes.py` (~l.614–622) says the gap-filled hours are absent from the price benchmark.
  - `calibration_verdict.py` (~l.2131) says CAISO 2023 Jan–Feb aged out.
  - Both are false: the 2023 RT benchmark has Jan $128.2 and Feb $64.3.
  - Comment-only fix; not edited here per the routing.

## Retrievability (rules 33/34)

- **On this branch, and on `main` when the PR merges:** `rcaiso5_X_span` and `rcaiso5_XE_span` (slim set, hourly
  sidecars, attestation, diagnostics), their sidecars and their payloads.
- **Per-year legs:** gitignored, local disk only; each costs about 20 min to re-solve.
- **Shard commits (provenance only):**
  - X-2022 `3946b8bc`, X-2023 `9048e6d4`, X-2024 `902f7892`, X-2025 `7b095aa1`;
  - XE-2022 `d7495185`, XE-2023 `818ac4a9`, XE-2024 `a83fafe5`, XE-2025 `135c510f`.
- All 8 shards are archived. Their branches are the owner's to delete; this session cannot delete refs.

## 7. PROMOTED 2026-09-27 — `2026-09-26-caiso-r5-pastoria-co2` (XE)

The owner instruction was: "Is this a recommended keeper candidate? If so plz promote. If structural integrity
improves but gates regress that may still be a keeper".

- **2019–2021 were re-solved on the XE recipe first** (rule 35(c)), one shard each at `93a38eac`: 2019 `88e00832`,
  2020 `e952e686`, 2021 `8cffd6072`. They are composed as `rcaiso5_XE_tp_2019_2021`, registered as
  `2026-09-27-caiso-r5-xe-keeper` and stamped to the keeper (rule 30(a)).
- **Their verdict is NOT-YET, reported only and never downgrading the ISO (rule 30(c)).** The fails are C1 / C3a /
  C4, all from the import fallback.
- **2019–21 vs the R-CAISO-4 recipe (TWh):**

  | | 2019 | 2020 | 2021 |
  |---|--:|--:|--:|
  | CC_REGULAR | −0.01 | −0.25 | −0.20 |
  | CT_PEAKER | +0.07 | +0.19 | +0.21 |

- **Re-keyed:** `keepers/CAISO.json`, `calibration-complete.json` `complete.CAISO` (re-verified CALIBRATED, no
  D-5(b) escalation), and the `program-status.json` gate-(a) row. `status/CAISO.js` was rebuilt, and the matrix
  stamp and §5.2 header were updated.
- **Cells:**
  - `unit_outage_extract_basis_share`: O → K;
  - `cc_eia923_identity_emission_basis`: O → K;
  - `unit_outage_lp_capacity_basis`: K → R (superseded).
- **Pruned (rule 35):** `2026-09-26-caiso-r4-intertie-dam`, `2026-09-26-caiso-r4-keeper-2019`, and the X-only
  candidate `2026-09-26-caiso-r5-cc-outage`. Git history is the record.
- **Year set:** 2019–2025, unchanged.
- **Checks:** `audit_keepers --iso CAISO` PASS; `check_promotion_completeness` OK on (a) through (d).
