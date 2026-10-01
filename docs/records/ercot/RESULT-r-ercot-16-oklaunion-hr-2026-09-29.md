# RESULT — R-ERCOT-16: Oklaunion measured coal heat rate, PROMOTED (data hygiene); ISO still NOT-YET

PRECOMMIT: `docs/handoffs/PRECOMMIT-r-ercot-15-phase0-oklaunion-hr-2026-09-29.md` (pinned SHA `3c398753b12f139f7c082720556ac64b0618de2e`).
New keeper `2026-09-28-r-16-oklaunion-hr` (`results/calibration/r_ercot16_span`, 2019–2025) supersedes `2026-09-28-r-14-oklaunion-swcap`.
Promoted under the owner's standing instruction carried in the handoff, verbatim: **"Is it an improvement? Then promote"**.

## Headline

- **A data-hygiene promotion, not a calibration move.** One rule-14 input correction: Oklaunion (127) now carries its measured CAMPD operating heat rate (net 11.77 in 2019, 11.47 in 2020 MMBtu/MWh) instead of the eGRID fallback (11.90 / 11.70). Zero DOF (ledger 12 / 7), recipe, flags and offer multipliers unchanged.
- **Every per-year determination is identical.** Numbers move in the second or third decimal only. 2021–2025 are byte-identical (every hourly sidecar `DataFrame.equals` the prior keeper's).
- **ISO stays NOT-YET**: 2023 carve-out (owner hold, k = 33) and 2024 C3a −10.7 %, both unchanged.

## Per year (keeper r-14 → r-16, P1; same scorer, same bench)

| Year | C3a | C3b | C3c h > $200 (model / RT) | C1 CC_REGULAR | C1 COAL_PRB | C1 ST_GAS | LW price $/MWh | Slack MWh | h > $1k | Determination |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | +24.0 → +24.0 % | 0.539 → 0.539 | 121 / 106 PASS | +8.72 → +8.71 | −9.30 → −9.28 | +4.18 → +4.17 | 57.715 → 57.713 | 0 → 0 | 41 → 41 | NOT-YET (unch.) |
| 2020 | +6.0 → +6.0 % | 0.242 → **0.241** | 39 / 56 PASS | +9.12 → +9.11 | −13.12 → −13.11 | +6.92 → +6.91 | 26.935 → 26.931 | 0 → 0 | 3 → 3 | NOT-YET (unch.) |
| 2021 | +4.6 % | 0.067 | 667 / 258 CAVEAT | −1.52 | −1.33 | −0.60 | identical | identical | identical | CALIBRATED |
| 2022 | −8.7 % | 0.167 | 97 / 196 CAVEAT | −7.96 | +5.90 | −0.41 | identical | 0 | — | CALIBRATED |
| 2023 | −20.0 % | 0.293 | 155 / 181 PASS | +2.50 | −1.86 | −0.40 | identical | 0 | — | NOT-YET (owner hold) |
| 2024 | −10.7 % | 0.189 | 13 / 53 CAVEAT | −1.35 | −1.22 | −1.27 | identical | 0 | — | NOT-YET |
| 2025 | −9.6 % | 0.127 | 0 / 31 CAVEAT | skipped (prelim. 923) | +3.72 | skipped | identical | 0 | — | CALIBRATED |

Oklaunion P1 generation in the arm: 2.1215 TWh (2019), 1.0599 TWh (2020). COAL_PRB class P1: +0.0205 / +0.0132 TWh vs the keeper.

## Prediction scorecard (PRECOMMIT §6)

| Prediction | Outcome |
|---|---|
| Oklaunion offer falls < $1/MWh | **HIT** — mc −0.21 (2019) / −0.34 (2020) $/MWh (PRECOMMIT §8, four rows only) |
| Oklaunion P1 TWh +0 to +0.15 per year; COAL_PRB gap narrows by at most that | **HIT** — COAL_PRB +0.021 / +0.013 TWh; gap −9.30 → −9.28, −13.12 → −13.11 |
| C3a moves < 0.5 pp | **HIT** — 0.0 pp at one decimal (LW price −0.002 / −0.004 $/MWh) |
| C3b moves < 0.01 | **HIT** — 0.000 / −0.001 |
| C3c hour counts ± a few | **HIT** — unchanged (121, 39) |
| No determination flips; 2020 C3b stays FAIL | **HIT** |
| 2021–2025 byte-identical | **HIT** — every hourly sidecar equal |

## Method

- Two shards (rule 36), one per year, at the pinned SHA, `replay_keeper.py results/calibration/r_ercot14_span --years <Y>` with no overrides. Both passed the input-sha, config-signature and Oklaunion-presence hard stops.
- G-DRIFT (rule 29(b)): INERT, established by R-ERCOT-15 (PRECOMMIT §5). No control solve; the keeper's committed 2019/2020 legs are the control (form 4).
- Composed with `scripts/probes/_r_ercot_compose_span.py --side arm --chp-off` over the two arm legs + the keeper's own legs (B-2021 `9a8f3408…`; R-ERCOT-12 2022–2025 `e7a4832b…`, `3d4a4904…`, `41061da2…`, `6ad0a04b…`), all fetched by full SHA — **zero re-solves**.
- `stamp_config_partition --check`: OK. The re-derived overrides differ from the prior keeper's only by four post-keeper, default-off `ScenarioConfig` fields now recorded explicitly `False` in 2019/2020 (`unit_outage_exit_cohort_repair`, `coal_fuel_inventory_monthly_pile`, `chp_steam_floor_conduct_scope`, `coal_monthly_pile_measured_receipts`) — absent from the recipe, inert by the G-DRIFT audit.
- Attestation carried from the prior keeper (governance block re-attested for R-ERCOT-16; DOF ledger unchanged).

## Promotion (rule 35)

- Year set before prune (both sidecars): {2019 … 2025}; the incoming keeper covers all seven.
- Re-keyed: `keepers/ERCOT.json` (keeper, notes, all three config_partition configs, `r_ercot16_extension`), `calibration-complete.json` (keeper + `keeper_rekey_2026_09_29_r16`; marker stays withdrawn), `forecast/program-status.json` gate (a) (status stays fail), `status/ERCOT.js` rebuilt, ERCOT matrix shard keeper stamp + `measured_coal_heat_rates` evidence, `mechanism-testing-matrix.md` §5.1 header.
- `prune_iso_runs.py --iso ERCOT --force-uncite` removed the r-14 sidecar, payload and bundle.
- Gates: `audit_keepers --iso ERCOT` 0 failures / 0 warnings; `check_promotion_completeness --iso ERCOT` OK; `check_mechanism_matrix --base origin/main` OK. `check_registry_payload_parity` is RED **locally only** on this session's own gitignored per-year legs (rule 31's documented local RED); nothing unmapped is committed.
- calibration-keeper-auditor (ERCOT): 0 failures; repaired one drift — the sidecar `definition` was stale text inherited from an R-ERCOT-12 leg.

## Task 2 — phase 0 on the 2019/2020 residual (zero LP; nothing armed)

### (a) West/Panhandle Waha rows for 2019–2021 — still incomplete, NOT armed

| Input | 2019 | 2020 | 2021 |
|---|---|---|---|
| Annual Waha basis vs HH | −1.66 (EIA TIE id=53919); corroborated: Reuters/LSEG Waha 2019 annual avg $0.91 (record low) vs HH $2.56 → −1.65 | **no citable annual figure** (EIA TIE id=45037 says only "narrowed" in 1H2020) | **no citable annual figure** (and Uri's $206/MMBtu Feb 16 print would dominate any annual mean) |
| Negative-price days (`neg_day_freq`) | 17 (Reuters, settlement close) | 6 (Reuters) | 0 (Reuters enumeration skips 2021–22) |

The frequencies are citable at the same standard as the committed 2023/2025 rows. The 2020/2021 basis is not. Pre-2022 West sits at zero spread (absent zone → 0). Route: a later intake could build 2020/2021 from EIA's weekly NGWU Waha prints, which is measured but laborious.

### (b) South 2020 thin-sample basis — MATERIAL; owner decision

The South zone's basis row is the Sch5 quantity-weighted price of **three small plants** (3630, 3631, 59391; 5M MMBtu in 2020). In 2020, 59391 averaged $8.13/MMBtu delivered, which drives +3.53 over HH (South_Central, 13 plants / 151M MMBtu, reads +0.64). That row prices ~4.3 GW of South gas, including merchant CCs that report no receipts.

Measured consequence (arm legs + keeper legs, model P1 vs EIA-923 actual, South-zone gas):

| Year | South basis | Merchant (non-CHP) model / actual TWh | ratio |
|---|---|---|---|
| 2019 | +1.19 | 8.37 / 11.74 | 0.71 |
| **2020** | **+3.53** | **1.32 / 10.68** | **0.12** |
| 2021 | +4.36 | 15.98 / 10.46 | 1.53 |
| 2022 | +1.20 | 10.53 / 11.23 | 0.94 |
| 2023 | +1.23 | 10.31 / 11.29 | 0.91 |
| 2024 | +0.63 | 12.21 / 11.28 | 1.08 |
| 2025 | +0.59 | 11.82 / 10.92 | 1.08 |

2020 is the outlier: ~9.4 TWh of South merchant gas is missing. It coincides with the thin-sample basis and plausibly feeds 2020's CC_REGULAR +9.1 TWh elsewhere. South never separates in price (0 hours above other zones), so the effect is on dispatch, not a local price.

Zero-threshold alternative: pool South with South_Central into one South-Texas Sch5 basis. Pooled vs the South row today: 2019 −1.16, **2020 −2.80**, 2021 +1.83, 2022 −0.79, **2023 −0.64, 2024 −0.15, 2025 −0.57**. It moves the training years too, so it is a construction change and needs the owner. A thin-sample threshold adds a free parameter (rule 21) and is not recommended.

### (c) The coal stay-on object stays fenced

No new admissible input appeared. It stays the standing model-class limit.

## Where the bytes are (rule 34(e))

- **On `main`:** `results/calibration/r_ercot16_span` (slim, 54 files), its sidecar and payload.
- **Legs:** local, gitignored, provenance only (rule 33(d)): arm-2019 `33da37d00f717039c603125dfc907bcf3fd3b4eb`, arm-2020 `11db2df17b975c7b49ae04a0db21fda7ef686170`. A re-solve of either costs ~20 min of LP.

## Routed (unchanged)

- SPP-48 Oklaunion (SPP lane).
- CAISO gate-(a) row and FR-22 (CAISO lane).
- The Decker Creek steam retirement seam; the Decker/Silas Ray CAMPD-backfill double count.
- The split-child bench display row; Fusco in MISO.
- The COAL-SUB crosswalk coal-row drop.
- Base-red fast-tier tests; CAMPD TX 2018 off disk.
- The R2 overlay/cap composition.
- The mislabelled 2020 DAM parquet.
- The frozen `GAS_OFFER_MARGIN_ANCHOR_BY_ZONE` non-reproduction (rule 23).
