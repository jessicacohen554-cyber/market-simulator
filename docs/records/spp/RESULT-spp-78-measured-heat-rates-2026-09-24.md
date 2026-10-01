# RESULT — SPP-78: SPP's measured CAMPD heat rates armed on all seven years

**PROMOTED 2026-09-24 on the owner's ruling, verbatim: 'Promote'** (after 'Is it a keeper candidate?' was answered yes on rule-14 fidelity). New keeper `2026-09-24-spp78-hr-span`, rung `2026-09-24-spp78-hr-rung` stamped to it; `2026-09-22-hydro-5-spp-floor` / `-rung` pruned (rule 35). Originally: **Recommendation: PROMOTE (rule 14).** All four pre-registered promotion
conditions hold. The span stays **CALIBRATED**. The rung stays **NOT-YET**: one rung row newly passes,
one newly fails, and one moves further out of band as predicted.

Record chain: PRECOMMIT `PRECOMMIT-spp-78-measured-heat-rates-2026-09-24.md` (`fe318fd8`) → ADDENDUM
`ADDENDUM-spp-78-rung-years-are-on-bin-centres-2026-09-24.md` → shards pinned at
`1e6c50da798f918a9f013b151c74998e444061d0`. Both docs were pushed before any solve. Phase-0 numbers are in
`results/calibration/_spp78_phase0.json`.

## 1. What was armed

- **Fields:** `measured_cc_heat_rates`, `measured_st_heat_rates`, `measured_coal_heat_rates`. All three
  already existed and default off. There is no new field and no new free parameter: `build_dof_ledger --check`
  returns "current" on both composites.
- **Artifacts:** the existing derives at their default 2023–25 window, committed under
  `data/raw/_processed-legacy/campd_{cc,st,coal}_heat_rates_SPP{,_units}.csv`.

| class | applied plants | MW | eGRID → measured |
|---|---:|---:|---:|
| CC_REGULAR | 16 / 20 | 8,114 | 7.802 → 7.576 (−2.89 %) |
| ST_GAS | 25 / 27 | 9,669 | 11.628 → 11.297 (−2.85 %) |
| COAL | 26 / 26 | 18,810 | 10.834 → 10.651 (−1.69 %) |

**The measured rate replaces a different base in the two windows** (ADDENDUM §1):

- **2023–25:** the arm replaces eGRID rates.
- **2019–22:** the arm replaces `HEAT_RATE_BINS` bin centres. The committed EIA-860 `vintage_2019/2021/2022`
  generator tables have no `heat_rate` column, and `vintage_2020`'s column is empty.

Offer heat rates, arm vs control, capacity-weighted:

| window | CC_REGULAR | ST_GAS | COAL_PRB |
|---|---:|---:|---:|
| 2019–22 | **+3.2 %** | **+9.8 %** | +1.4 % |
| 2023–25 | −2.3 % | −2.0 to −2.6 % | −1.7 % |

## 2. Solved result (scorer basis, arm vs control at the same SHA)

- **Controls reproduce the committed keeper and rung** to max |Δ class TWh| = 0.000.
- **Benchmark drift on `main` since the keeper is immaterial:** eia923 −4.9 GWh of 858.7 TWh on the span and
  −65 GWh of 1,082 TWh on the rung. Arm and control are both scored on the current frame.

**Determinations** (control → arm):

| | span 2023–25 | rung 2019–22 |
|---|---|---|
| control | CALIBRATED | NOT-YET |
| arm | **CALIBRATED** | NOT-YET |

**Demand-weighted mean price, arm − control ($/MWh):**

| 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---:|---:|---:|---:|---:|---:|---:|
| +0.30 | +0.26 | +0.61 | +0.74 | −0.40 | −0.34 | −0.45 |

**Class TWh, arm − control:**

| year | COAL_PRB | COAL_LIG | CC_REG | ST_GAS | CT_PEAKER |
|---|---:|---:|---:|---:|---:|
| 2019 | +1.07 | −0.76 | −0.60 | −0.66 | +0.85 |
| 2020 | +1.37 | −0.54 | −0.95 | −0.92 | +0.94 |
| 2021 | −0.03 | −0.31 | −0.22 | −0.28 | +0.74 |
| 2022 | +0.23 | −0.08 | −0.58 | −0.54 | +0.91 |
| 2023 | +0.31 | −0.10 | +0.61 | +0.32 | −1.10 |
| 2024 | +0.24 | −0.07 | +0.49 | +0.31 | −0.94 |
| 2025 | +0.60 | −0.27 | +0.46 | +0.09 | −0.87 |

**Gate rows that moved** (control → arm):

| row | control | arm |
|---|---|---|
| C3a 2019 / 2020 / 2021 / 2022 | +7.9 / **+15.5** / +1.9 / −4.9 % | +9.3 / **+17.1** / +3.5 / −3.2 % |
| C3a 2023 / 2024 / 2025 (load-weighted) | −1.0 / −2.5 / +0.2 % | −2.6 / −3.8 / −1.3 % |
| C3b 2020 / 2021 / 2022 | 0.257 / 0.234 / **0.208 FAIL** | 0.264 / 0.217 / **0.197 PASS** |
| C1 CC_REGULAR 2022 | −7.55 TWh (PASS) | **−8.14 TWh (FAIL, ±8.00)** |
| C1 COAL_PRB 2022 | +9.60 TWh FAIL | +9.83 TWh FAIL |
| C1 CT_PEAKER 2023 / 2024 | +2.74 / +3.02 TWh | +1.70 / +2.08 TWh |
| C4 gas 2022 NRMSE | 0.321 FAIL | 0.325 FAIL |
| C8 ST_GAS forced share 2022 | 31.5 % grounded (2.383 / 7.560 TWh) | 33.3 % grounded (2.426 / 7.286 TWh); D-1 CV ratio 1.446 → 1.013 (≥ 0.5) |

The rise in the ST_GAS forced share is mostly the denominator: ST_GAS energy falls 0.27 TWh while
floored energy rises 0.04 TWh. No floor was added (rule 19).

## 3. Predictions scored (PRECOMMIT §5, as amended by the ADDENDUM)

| # | prediction | outcome |
|---|---|---|
| P1 | artifacts reproduce SPP-76 to ±0.3 pp | **PASS**: exact |
| P2 | (superseded by ADDENDUM: SPP-76's rung-year proxy was on the wrong base) | — |
| P3 | ΔPRB sign matches the proxy where \|proxy\| ≥ 0.3; \|Δ\| ≤ 1.5 | **PASS**: +1.07 / +1.37 / +0.31 / +0.60; max \|Δ\| 1.37 |
| P4 | COAL_PRB 2022 stays out of band | **PASS**: +9.83 |
| P5 | ΔCC ≥ −0.5 (2023–25); ≤ +0.3 (2019–22) | **PASS** |
| P6 | C3a 2020 rises 0.5–5 pp; price up all rung years, down all span years | **PASS**: +1.6 pp; 7 / 7 signs |
| P6b | C3a 2023–25 falls 0.3–3 pp | **PASS**: −1.6 / −1.3 / −1.5 |
| P7 | C4 gas 2022 moves < 0.02 | **PASS**: +0.004 |
| P8 | C3b 2020/21/22 each move < 0.02 | **PASS**: +0.007 / −0.017 / −0.011 |
| P9 | C8 / D-4 clean | **PASS** |
| P10 | span determination unchanged | **PASS** |

The proxy under-predicted the solved COAL_PRB move by roughly 1.3–2× in 2019–20. That is inside P3's
bound, but it is the proxy's known ST_GAS / CT blind spot (the stack omits the commitment floors).

## 4. Promotion rule (PRECOMMIT §6)

| condition | result |
|---|---|
| (a) clean arm | **Holds.** Fleet check passes; the recipe diff is exactly the three flags in every leg; only `flag == ok` plants are applied. |
| (b) C8 / D-4 clean, no new floor | **Holds.** |
| (c) `audit_keepers` | **0 failures** at the lane's head. The run is not yet registered: registering an unpromoted candidate trips E13. |
| (d) DOF | **Holds.** Zero new parameters. |

**Why promote.** Fidelity improves on rule-14 grounds in both windows, and most in 2019–22, where plant
meters replace class-default bin centres. Under rule 1 a gate regression is not a criterion:

- the new C1 CC_REGULAR 2022 FAIL misses the band by 0.14 TWh;
- the worse C3a 2020 was predicted and has a named owner (§5).

## 5. Failing rung rows and their owning objects

| row (arm) | owning object |
|---|---|
| C1 COAL_PRB 2022 +9.83 | Crossover fuel-price elasticity: DA-market commitment physics with no measured driver (SPP-69 §4, SPP-75 §2, SPP-77) |
| C1 CC_REGULAR 2022 −8.14 (new) | The same crossover object: CC decommits at $6.45 gas. The Jan-2022 F923 outlier adds about +0.08 TWh and is routed to a shared-data lane. The arm exposes this row: a 7.5 bin centre had been understating CC cost. |
| C3a 2020 +17.1 % | Price level: missing tail and congestion rent (SPP-70 R-bc, SPP-74). The arm raises 2020 offers because the bin centres understated them. |
| C3b 2020 0.264 / 2021 0.217 | Price body and shape (SPP-74); gas low side (SPP-75) |
| C4 gas 2022 0.325 | Crossover object plus the Jan-2022 F923 outlier |

## 6. Routed, not built

1. **Missing eGRID join in EIA-860 `vintage_2019/2020/2021/2022`.** Every ISO's pre-2023 vintage fleet
   prices every thermal unit the measured artifacts do not cover at bin centres. In SPP that uncovered
   capacity is 1.9–2.9 GW of COAL, 0.5–0.7 GW of ST_GAS and 2.0 GW of CC.
   - This is a shared-data defect. It is not SPP's to widen.
   - It also corrects FINDING-spp-60 §D1, which says 2021/2022 carry the join; at HEAD they do not.
   - It qualifies SPP-76, whose rung-year proxy scaled bin centres by `measured / eGRID`.
2. **Jan-2022 F923 CC price outlier.** Unchanged, routed per SPP-77.

## 7. Retrievability (rules 31 / 33 / 34)

- **Composites:** `spp78_hr_span` (126 MB) and `spp78_hr_rung` (162 MB) are on this session's local disk,
  gitignored, with the four registrations staged in scratch. They are not on `main`.
  - A span composite that is registered on `main` today trips `audit_keepers` E13.
  - A registered-but-uncommitted bundle trips the parity gate.
  - So the bytes land on `main` only as part of a promotion.
- **Per-year legs:** pushed to `claude/spp78-<year>` at the SHAs below. These SHAs are provenance, not a
  recovery route: the environment cuts those branches when this lane's PR merges (rule 33(f)).

| year | leg SHA |
|---|---|
| 2019 | `5ea4b4d2f3cedd86f32eeb50d195002acb905ed3` |
| 2020 | `2d1fc65a5e81fa67137aeb204375d91627dead1e` |
| 2021 | `8e5b7ba93b7c2b3c496ac96b7ce9e68989539952` |
| 2022 | `5cb3b9e4c593502e8b1bc66dc7daa6d77443bf38` |
| 2023 | `6332b7c5c63e743fd4de178a930077c5f0677bc0` |
| 2024 | `63452b24f67524854163235c64d8d28eab6ef233` |
| 2025 | `0f2aaee523b9b67c1d2806a3332924f1b12877f4` |

- **Cost if this container is reclaimed before a ruling:** 7 arm-only shards at about 3–4 min of LP each,
  roughly 15 min wall in parallel, plus zero-LP compose and score.
- **Shards:** all 7 archived after fetch, checkout and verification.
- **Leftover refs:** the seven `claude/spp78-<year>` branches. Sessions cannot delete refs; the owner clears
  them.

## 8. If promoted (rule 35 order)

1. Year union {2019, 2020, 2021, 2022, 2023, 2024, 2025}: already recorded in this doc, which satisfies
   rule 35(b).
2. Register both arm composites via `dashboard_add_run`.
3. Promote `spp78-hr-span` in `keepers/SPP.json`.
4. Stamp `spp78-hr-rung` to the new keeper.
5. Run `audit_keepers --iso SPP` (E1 / E13).
6. Run `prune_iso_runs.py --iso SPP` to remove the hydro-5 floor and rung.
7. `build_status`.
8. Re-key `calibration-complete.json`.
9. Run the keeper auditor.
10. Flip the three matrix cells O → K.

## 9. Promotion executed (rule 35)

1. Year union {2019–2025}, recorded in §8 before any deletion.
2. Both composites registered: span **CALIBRATED**, rung **NOT-YET**. The attestation carries the SPP-78
   provenance and an `spp78` block, and the 0.93 band is held.
3. `keepers/SPP.json` points at `2026-09-24-spp78-hr-span`. The rung is stamped to it with
   `stamp_touchpoint_holdout.py`.
4. `audit_keepers --iso SPP` was run between promotion and prune. E1 passed; the only failures were the
   two expected E13s for the outgoing runs.
5. `prune_iso_runs.py --iso SPP --keep 2026-09-24-spp78-hr-rung --force-uncite` removed the hydro-5 floor
   and rung, all three stores.
6. `build_status --iso SPP` was re-run.
7. The `calibration-complete.json` SPP entry was re-keyed.
8. The three matrix cells went O → K and the SPP shard's keeper was restamped.
9. After the prune, `audit_keepers --iso SPP` reported 0 failures.
10. **Retrievability:** both keeper bundles (slim and hourly files, as the prior keeper committed) are on
    `main` under `results/calibration/spp78_hr_{span,rung}/`. The new span/rung benchmark frames
    `_shared/SPP/eia923-{3953c83ea5b8,8dd02ac893e4}` are committed with them.
    - The per-year legs and controls remain gitignored. They are no longer needed now that the owner has
      ruled (rule 31 trigger (i)), and they are not deleted.
11. **Local parity gate:** `check_registry_payload_parity` reads RED locally, but only for those gitignored
    leg and control dirs (the rule-31 correction's local-walk case); nothing else is flagged.

## 10. F1 landed in parallel — what it means for this keeper

`RESULT-f1-backcast-heatrate-vintage-2026-09-24.md` (PR #6572) merged to `main` during this lane.

**What F1 did:**
1. Repaired the vintage eGRID join. This is the defect §6.1 routed: year-matched eGRID in every ISO-year
   2019–2025.
2. Re-derived `campd_{cc,st,coal}_heat_rates_SPP.csv` as a pooled 2019–25 row plus per-year rows. The
   loader now prefers the solve year's own row.
3. Flipped `measured_{ct,coal,st,cc,chp}_heat_rates` and `eia860_vintage_tracks_solve_year` **default-on
   for backcasts**.

**Consequences:**
- **This keeper was solved on the pre-F1 inputs at `1e6c50da`.** It used the 2023–25 pooled artifact
  (sha256s in `_spp78_shard_check.py`), and its 2019–22 uncovered rows were on bin centres.
- **Replaying it at post-F1 HEAD will not reproduce these numbers.** F1 says the same of every ISO's
  keeper.
- **The promotion's direction is unaffected.** It is exactly F1's new default, so the named successor is
  a post-F1 re-solve of this recipe: seven per-year shards on defaults with no `--set`, about 15 min wall.
