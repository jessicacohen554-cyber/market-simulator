# RESULT — R-ERCOT-17: pooled South-Texas gas basis, all seven years

PRECOMMIT: `docs/handoffs/PRECOMMIT-r-ercot-17-south-texas-pool-2026-09-29.md` (pinned SHA `4aaa1a1f0f44b89f3fb57fa55a2293711a2ecb7a`). Arm run `2026-09-29-r-17-south-texas` (`results/calibration/r_ercot17_span`, 2019–2025) vs keeper `2026-09-28-r-16-oklaunion-hr`.

## Headline

- **The pool fixes the object it was ruled for.** South merchant gas: 2020 1.32 → **10.88 TWh** (actual 10.68), 2021 15.98 → **11.05** (actual 10.46). Prices barely move (C3a within 0.3 pp every year).
- **One train-year determination flips worse: 2022 CALIBRATED → NOT-YET**, on C8 alone. ST_GAS forced share goes 28.7 % → **30.4 %** (cap 30 %). The above-cap escape fails on a **pre-existing** D-4 conduct defect: `st_netload_drag` floors plant 3452 in hours its meter reads zero (76 %), present identically in the keeper (0.4255 TWh floored, D-4 FAIL there too). The keeper sat 1.3 pp under the cap; the arm trims ST_GAS energy 12.54 → 12.19 TWh and crosses it.
- Per the PRECOMMIT §7 decision rule the session did not self-promote. It put a decision card to the owner, answer verbatim: **"Promote; fix 3452 next (Recommended)"**. **PROMOTED 2026-09-30.**

## Per year (keeper r-16 → arm r-17, P1)

| Year | C3a | C3b | C3c h > $200 | C1 CC_REGULAR | C1 COAL_PRB | C1 ST_GAS | C8 ST_GAS | South merchant TWh (actual) | LW $/MWh | Slack MWh | h > $1k | Determination |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | +24.0 → +23.9 % | 0.539 → 0.538 | 121 PASS | +8.71 → **+9.70** | −9.28 → −9.48 | +4.17 → +3.06 | — | 8.37 → 13.60 (11.74) | 57.71 → 57.67 | 0 | 41 → 41 | NOT-YET (unch.) |
| 2020 | +6.0 → +5.7 % | 0.241 → **0.229** | 39 PASS | +9.11 → **+12.41** | −13.11 → **−11.57** | +6.91 → **+2.55** | — | **1.32 → 10.88** (10.68) | 26.93 → 26.84 | 0 | 3 → 3 | NOT-YET (unch.) |
| 2021 | +4.6 → +4.6 % | 0.067 → 0.066 | 667 CAVEAT | −1.52 → −0.55 | −1.33 → −1.52 | −0.60 → −0.17 | 24.7 → 22.4 % | **15.98 → 11.05** (10.46) | 173.60 → 173.52 | 4,145 → 4,145 | 123 → 123 | CALIBRATED (unch.) |
| 2022 | −8.7 → −8.9 % | 0.167 → 0.168 | 97 CAVEAT | −7.96 → −7.84 | +5.90 → +5.89 | −0.41 → −0.75 | 28.7 → **30.4 % FAIL** | 10.53 → 13.29 (11.23) | 68.54 → 68.39 | 0 | 19 → 19 | **CALIBRATED → NOT-YET** |
| 2023 | −20.0 → −19.9 % | 0.293 → 0.290 | 155 PASS | +2.50 → +3.67 | −1.86 → −2.17 | −0.40 → −1.00 | — | 10.31 → 13.72 (11.29) | 52.02 → 52.05 | 0 | 38 | NOT-YET (hold) |
| 2024 | −10.7 → −10.8 % | 0.189 → 0.190 | 13 CAVEAT | −1.35 → −1.29 | −1.22 → −1.21 | −1.27 → −1.40 | — | 12.21 → 12.78 (11.28) | 27.83 → 27.82 | 0 | 1 | NOT-YET (unch.) |
| 2025 | −9.6 → **−9.9 %** | 0.127 → 0.130 | 0 CAVEAT | skipped | +3.72 → +3.74 | skipped | — | 11.82 → 13.56 (10.92) | 32.98 → 32.90 | 0 | 0 | CALIBRATED (unch.; 0.1 pp from the edge) |

Keeper South merchant TWh are R-ERCOT-16's; the arm's are computed here the same way (P1 dispatch, zone South, gas classes, CHP excluded).

**New pattern:** South now **over**-runs in five of seven years (1.13–1.24×; 2020/2021 now ~1.0–1.06×). The thin-sample row had been masking a separate South over-dispatch in the ordinary years. 2020's CC_REGULAR excess grows (+9.1 → +12.4) because the displaced energy is ST_GAS and coal-adjacent, not CC elsewhere.

## Prediction scorecard (PRECOMMIT §6)

| Prediction | Outcome |
|---|---|
| 2019/2020 LW price up +0.3–2.0 $/MWh (recentring lifts non-South gas) | **MISS** — −0.04 / −0.09. Cheaper South CCs set price in enough hours to offset the lift. |
| 2020 C3a may cross +10 % | **MISS** — +5.7 % (down) |
| 2020 South merchant 5–9 TWh | **MISS (overshoot)** — 10.88, i.e. closed fully |
| 2021 South merchant 12–14.5 | **MISS (overshoot)** — 11.05 |
| 2022/2023 South 11–12 / 10.8–11.6 | **MISS** — 13.29 / 13.72 |
| 2020 C1 CC_REGULAR +8 to +9.5 | **MISS** — +12.41 (worse) |
| 2020 COAL_PRB −12.5 to −13.1 | **MISS (better)** — −11.57 |
| 2020 C3b 0.23–0.27 | **HIT** — 0.229 |
| 2021–2024 C3a/C3b small moves | **HIT** |
| 2025 C3a −9.0 to −9.9 | **HIT** (−9.9, at the edge) |
| No determination flips except 2025 at risk | **MISS** — 2025 held; **2022 flipped on C8**, which was not anticipated |

## Method

- Seven shards (rule 36) at the pinned SHA, `replay_keeper.py results/calibration/r_ercot16_span --years <Y> --set ercot_south_texas_pooled_basis=true`. All passed the SHA, input-sha256 and signature hard stops and pushed full bundles.
- G-DRIFT (rule 29(b)): ALL INERT; measured 2022 fleet byte-identity at the oldest leg SHA vs HEAD (PRECOMMIT §8). Keeper legs are the control (form 4).
- Composed with `_r_ercot_compose_span.py --side arm --chp-off` (flag added to `MUST_AGREE`); `stamp_config_partition --check` OK; attestation carried with governance re-attested; registered `--no-prune`; scored `calibration_verdict --years <Y> --json` for both runs.

## Promotion (rule 35)

- Year set before prune (both sidecars): {2019 … 2025}; the incoming keeper covers all seven.
- Re-keyed: `keepers/ERCOT.json` (keeper, promotion note, all three config_partition configs, `r_ercot17_extension`), `calibration-complete.json` (keeper + `keeper_rekey_2026_09_30_r17`; marker stays withdrawn), `forecast/program-status.json` ERCOT gate (a) only (status stays fail), `status/ERCOT.js` rebuilt, ERCOT matrix shard keeper stamp + `ercot_south_texas_pooled_basis` cell K, `mechanism-testing-matrix.md` §5.1 header.
- `audit_keepers --iso ERCOT` was run between the promotion and the prune: E1 resolved; only the expected E13/S1 failed. `prune_iso_runs.py --iso ERCOT --force-uncite` then removed the r-16 sidecar, payload and bundle. After the prune: `audit_keepers` 0/0; `check_promotion_completeness --iso ERCOT` OK; `check_mechanism_matrix --base origin/main` OK.

## Where the bytes are (rule 34(e))

- **On `main` with the promotion:** `results/calibration/r_ercot17_span` (slim, 54 files incl. hourly sidecars), its registry sidecar and run payload.
- **Legs (provenance only, rule 33(d)):** 2019 `9f7256a1da5c4713cdf63a0e5368e86a6a6860ed`, 2020 `80c386e7da678a547efd512d47e1d0a625fc0434`, 2021 `85edeabb4fc7bcd52d9364663e5fc9832ec3e4e4`, 2022 `f32dcdb5955aeadf26e17a98ca5099833f2b77bd`, 2023 `e1cdb013f383977e8abce1a5b33eccbd2a07a887`, 2024 `d3d81d1c118cebcab4852e381f6ef50c387ea850`, 2025 `aebe9947b7ae194245f1cd4c8fbc552925ccfb2f`.

## Routed

- **Plant 3452 `st_netload_drag` unit-conduct D-4 FAIL (2022; pre-existing in the keeper).** The floor binds 4,600+ h/yr on a unit whose CAMPD meter reads zero 76 % of the time. This is what denies 2022 the C8 escape. Next lane: characterize and fix the provenance (rule 17/19), zero-LP first.
- **South over-dispatch in the ordinary years** (1.13–1.24× in 2019, 2022–2025), now visible. Characterize before any lever.
- **2024/2025 member-row vintage refresh** (committed rows are an earlier release; the Finals now exist). Rule-23 data update.
