# RESULT — R-ERCOT-18: prior-year overnight-commitment allocation of the ST_GAS drag

PRECOMMIT: `docs/records/ercot/r-ercot/PRECOMMIT-r-ercot-18-drag-overnight-index-2026-09-30.md` (pinned SHA `0bd29417487453cfa33392dab17fd2dce8fc10c2`). The arm run `2026-09-30-r-18-drag-index` (`results/calibration/r_ercot18_span`, 2019–2025) is compared against keeper `2026-09-29-r-17-south-texas`.

## Headline

- **2022 is back to CALIBRATED.** The plant-3452 `st_netload_drag` D-4 conduct FAIL is gone. C8 ST_GAS reads 30.4 % FAIL → 30.1 %, which is a grounded PASS through the rule-21 escape.
- **No year flips worse.** 2025 C3a moves off its edge (−9.9 → −9.6 %).
- **PROMOTED** under the standing instruction ("Is it an improvement? Then promote"), on PRECOMMIT §8's rule. The ISO stays NOT-YET: the 2023 carve-out (owner hold k=33) and 2024 C3a −10.7 % remain.

## Per year (keeper r-17 → arm r-18, P1)

| Year | C3a | C3b | C3c | C8 ST_GAS | C1 CC_REG | C1 COAL_PRB | C1 ST_GAS | South merchant TWh | LW $/MWh | Slack MWh | h > $1k | Determination |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | +23.9 % (=) | 0.538 (=) | 121 h PASS | 18.1 % (=) | +9.70 | −9.48 | +3.06 | 13.60 | 57.67 | 0 | 41 | NOT-YET (byte-identical, fail-closed) |
| 2020 | +5.7 → +5.6 % | 0.229 | 39 h PASS | 21.9 → 24.5 % | +12.41 → +12.39 | −11.57 → −11.61 | +2.55 → +2.62 | 10.88 | 26.84 → 26.83 | 0 | 3 | NOT-YET (unch.) |
| 2021 | +4.6 % | 0.066 → 0.067 | 667 h CAVEAT | 22.4 → 22.7 % | −0.55 → −0.54 | −1.52 → −1.51 | −0.17 → −0.22 | 11.05 | 173.52 → 173.56 | 4,145 | 123 | CALIBRATED (unch.) |
| 2022 | −8.9 → −8.7 % | 0.168 → 0.167 | 97 h CAVEAT | **30.4 % FAIL → 30.1 % PASS** | −7.84 → −7.69 | +5.89 → +5.93 | −0.75 → −1.08 | 13.29 → 13.31 | 68.39 → 68.54 | 0 | 19 | **NOT-YET → CALIBRATED** |
| 2023 | −19.9 → −19.8 % | 0.290 → 0.289 | 155 h PASS | 18.5 → 19.6 % | +3.67 → +3.72 | −2.17 → −2.18 | −1.00 → −1.14 | 13.72 → 13.68 | 52.05 → 52.12 | 0 | 38 | NOT-YET (hold) |
| 2024 | −10.8 → −10.7 % | 0.190 | 13 h CAVEAT | 15.4 → 16.5 % | −1.29 → −1.28 | −1.21 | −1.40 → −1.39 | 12.78 → 12.77 | 27.82 → 27.83 | 0 | 1 | NOT-YET (unch.) |
| 2025 | −9.9 → **−9.6 %** | 0.130 → 0.129 | 0 h CAVEAT | 22.8 → 21.9 % | (prelim. 923) | +3.74 → +3.77 | (prelim. 923) | 13.56 → 13.59 | 32.90 → 32.99 | 0 | 0 | CALIBRATED (unch.) |

**D-4 `st_netload_drag` unit-conduct FAILs fall 9 → 8.**

| Plant | Year(s) | Keeper → arm |
|---|---|---|
| 3452 | 2022 | **cleared** |
| 3452 | 2020 / 2021 / 2023 | shrink to 0.047 / 0.009 / 0.053 TWh, still convicted |
| 3628 | 2020 | 0.117 → 0.068 TWh |
| 3491 | 2024 | 0.406 → 0.316 TWh |
| 3491 | 2025 | 0.615 → 0.123 TWh |
| 2019 rows | 2019 | unchanged (fail-closed) |

The rider's test is binary: the median of the meter over the plant's own binding hours. So even a small residual floor still convicts when it binds in the unit's off hours.

## Prediction scorecard (PRECOMMIT §7)

| Prediction | Outcome |
|---|---|
| 2019 identical | **HIT** (byte-identical diagnostics) |
| 2022 C8 26–33 %, D-4 1 → 0, NOT-YET → CALIBRATED | **HIT** (30.1 %, cleared, CALIBRATED) |
| 2020/2021/2023/2025 D-4 st_netload_drag → 0 | **MISS**: residual small floors still convict (see above) |
| 2024 D-4 1 → 0 or 1 | HIT (1) |
| C8 2021/2023/2024/2025 within stated bands | HIT (22.7 / 19.6 / 16.5 / 21.9) |
| 2020 C8 19–24 % | **MISS**: 24.5 %, a rise, not a fall |
| C3a moves < 0.5 pp, LW ±0.3 $/MWh | HIT everywhere |
| ST_GAS energy +0–0.3 TWh | **MISS**: mixed. The class fell 0.14–0.32 TWh in 2022/2023/2025 and rose 0.07 in 2020. The concentrated floor lands on plants the LP already dispatches, which displaces other ST_GAS output. |

## Method

- Zero-LP first: CAMPD per-unit conduct, and 3452's diurnal/monthly pattern against the floor's binding hours from the R-17 leg's own floors/dispatch.
- Built after an owner decision card. The owner had previously picked cost order (merit allocation) for this defect family; the prior-year index is a new, measured-conduct option.
- Seven shards at the pinned SHA, all hard stops passed; G-DRIFT all INERT; keeper legs are the control.
- Composed with `_r_ercot_compose_span.py --side arm --chp-off` (flag added to `MUST_AGREE`). `stamp_config_partition --check` OK; the overrides are byte-equal to the keeper's.
- Attestation carried and governance re-attested. Registered `--no-prune` and scored with `calibration_verdict --years <Y>`.

## Promotion (rule 35)

- Year union before the prune (both sidecars): {2019 … 2025}. The incoming keeper covers all seven.
- Re-keyed:
  - `keepers/ERCOT.json` (all three configs + `r_ercot18_extension`)
  - `calibration-complete.json` (`keeper_rekey_2026_09_30_r18`; the marker stays withdrawn)
  - `forecast/program-status.json`, ERCOT gate (a) only
  - `status/ERCOT.js`
  - ERCOT matrix shard (keeper stamp + `netload_drag_floors` cell)
  - `mechanism-testing-matrix.md` §5.1
- `audit_keepers` between promotion and prune: E1 resolved, only the expected E13 failed. `prune_iso_runs --iso ERCOT --force-uncite` then removed r-17.
- After the prune:
  - `audit_keepers`: 0/0.
  - `check_promotion_completeness --iso ERCOT`: OK.
  - `check_mechanism_matrix --base origin/main`: OK.
  - `check_registry_payload_parity`: RED locally, only on the seven gitignored `r_ercot18_arm_*` legs (rule 31, local-only; CI sees none).

## Where the bytes are (rule 34(e))

- **On `main` with the promotion:** `results/calibration/r_ercot18_span` (slim bundle incl. hourly sidecars), its registry sidecar and run payload.
- **Legs (provenance only, rule 33(d); shard branches are transport):**

| Year | Commit |
|---|---|
| 2019 | `cf1d0acce8b56bdfb78ede1b5bb861e9a5098125` |
| 2020 | `2d716c1eb4aeead323e0113e17a10fbac0b9bb3f` |
| 2021 | `acd1f38992b37e71bb754e1b9e6cb83c5563df5d` |
| 2022 | `832e8e7f49d9d3c46d38957c134bfafe180bc482` |
| 2023 | `7b1be416d8a4af52392b4b14e2a881e3177f08f6` |
| 2024 | `4a4f63c69f23678979a7ce960872caa571fa432f` |
| 2025 | `511cad258e6a032acbf00059c5a7968db098cc3f` |

- Leg recovery is costed as a re-solve (~25 min per shard).

## Task 2 — zero-LP characterization (no lever pulled)

**South merchant over-run (1.13–1.24×).** Looked at 2019/2022/2024 with the R-17 per-plant dispatch against CAMPD.

- It is a **commitment-frequency** effect, not a level or heat-rate one. Model South CCs are online 63–97 % of hours against 20–67 % metered, and their MW-when-on sits at or below the meter's.
- It is uniform across the day (model/meter 1.13–1.50 by hour).
- It is **not** floor-driven: bridge forcing is ≤ 0.16 TWh per plant.
- Caveat found at registration: 3559 Silas Ray, 3631 Sam Rayburn and 55086 Gregory carry the benchmark's CT-only CEMS flag (EIA-923 net > 1.1× CAMPD gross). So the CAMPD comparison overstates their over-run, and the next lane must redo this on the EIA-923 monthly basis before any lever.
- The efficient 55123 under-runs, so the pattern points at the merit order within South CCs. Offers are fenced here.

**Not started, routed forward:**

- The 2024/2025 member-row vintage refresh (a rule-23 data update).
- West Waha 2020/2021 (only if every row is citable).
- The South CHP shortfall.

## Routed

- Residual `st_netload_drag` D-4 rows:
  - 3452 in 2020/2021/2023 and 3628 in 2019/2020 are small floors that still bind in off hours.
  - 3491 in 2024/2025 (Handley, a weekly cycler on unit 3).
  - None is rubric-visible (all years below the 30 % cap).
  - A structural answer would need the floor to be hour-eligible by the plant's own diurnal commitment, which is a new design and needs an owner call.
- All items from the handoff's ROUTE list stand unchanged.
