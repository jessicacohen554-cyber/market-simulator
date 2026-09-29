# PRECOMMIT — NYISO-NEXT-13: take the NE AC node out of the monthly net-interchange band — 2026-09-29

- **Session:** NYISO-NEXT-13 (orchestrator; this container runs no LP, rule 32 (a)).
- **Control (form 4):** keeper `2026-09-29-nyisonext12-neac-node-span` (bundle `results/calibration/nyisonext12_span`, 2022–2025) + stamped `2026-09-29-nyisonext12-neac-node-2021` (bundle `results/calibration/nyisonext12_2021`).
- **Arm:** the keeper recipe + `nyiso_ne_ac_recon_detach: true`. Nothing else changes.
- **Queue item:** §5.5 "Queue after NEXT-12" item (1). Phase 0 re-routes it (§1).
- **Probe:** `scripts/probes/nyisonext13_ch_pricing_phase0.py` → `results/calibration/_nyisonext13_phase0.json`. Band and node checks below were run on the keeper's per-year dispatch parquet (fetched from the NEXT-12 leg branches, zero LP).

## 1. Phase 0 (zero LP): what puts the node at its bound

NEXT-12 read the node's over-export as Capital_Hudson under-pricing. The dispatch says otherwise.

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| months the ±2 % net-interchange band binds (lo / hi) | 9 / 2 | 11 / 1 | 7 / 4 | 0 / 11 | 1 / 10 |
| NE node TWh, keeper (measured) | −0.74 (−5.17) | −1.25 (−3.51) | −2.98 (−4.47) | −7.35 (−5.84) | −7.56 (−5.76) |
| pooled node TWh, keeper (measured, EIA-930 − NE) | 28.33 (33.06) | 29.10 (31.82) | 26.24 (27.93) | 28.06 (26.19) | 26.91 (24.84) |
| hours the node sits within one band of its own bands at its own LMP | 36.9 % | 33.7 % | 61.6 % | 33.5 % | 63.2 % |
| node TWh its own bands imply at its own LMP | −3.97 | −4.80 | −3.82 | −2.79 | −5.24 |
| node TWh its bands imply at MEASURED CAPITL DA | −4.94 | −3.41 | −4.44 | −5.78 | −5.65 |

- **The band sets the node, not the node's bands.** The monthly band (`nyiso_import_reconciliation`) pins the signed sum of every import row, the NE node included. The node is the band's only export-capable row (the pooled sink is pinned to 0 in P1). So when the pooled node misses its volume, the band's dual moves the node off its bands. The node's TWh error is the mirror of the pooled node's: 2024 pooled +1.87 / node −1.51; 2025 +2.07 / −1.80; 2021 −4.73 / +4.43.
- **The node's own construction is sound.** Fed the measured CAPITL DA price, its bands reproduce the measured tie within 0.1–0.2 TWh in every year.
- **"0–4 h at bound measured" is not the right comparator.** The bands clip at the hourly posted limit, so even measured prices put the node at its bound 311–587 h/yr. The hours-at-bound figure is reported, not gated.
- **Capital_Hudson pricing is a real but separate miss.** In the node's bound hours the keeper's CH price is 6–67 $/MWh below measured CAPITL DA on average, mostly the upstate level in 2021 and 2023–2025 and the Central-East spread in 2022. It stays on the queue as items (4)/(5).

## 2. The mechanism (zero free parameters)

`nyiso_ne_ac_recon_detach` (default off, NYISO, backcast only; requires `nyiso_ne_ac_node` and `nyiso_import_reconciliation`):

- the 16 NE AC rows leave the band's row set;
- the tie's measured P-32 monthly net schedule (`SCH - NE - NY`, import-positive) is subtracted from the band target;
- the half-width is re-taken on the new target with the same `NYISO_IMPORT_RECON_BAND_FRAC` (0.02).

**Why (rules 13, 19):** the band exists because a static pooled ladder "cannot economically derive" its flow, so its volume is pinned to the measured schedule. The NE tie's flow is now derived hourly against a measured neighbour price, so that reason no longer covers it. Detaching pins strictly fewer measured outcomes. One mechanism now sets the node's flow, not two.

**Declared misalignment (rule 14):** the target mixes the EIA-930 BA total with the P-32 tie schedule. Pooled target minus the P-32 non-NE sum: +0.67 / +1.33 / +1.16 / −0.39 / −0.16 TWh (2021–2025). This is the band's existing basis; it is not changed.

**Feasibility (zero LP):** the pooled links' posted/envelope import capacity is ≥ 1.17× the detached lower bound in every month of every year.

## 3. G-DRIFT (keeper `git_sha` 7d238cc9 → pin)

Changed on the backcast path since 7d238cc9 on `main`: `e44fd9fa` miso-286 (MISO-gated `miso_gas_ecomin_online_floor`, default off, not in the recipe; new constant + solve-surface name `MISO_GAS_ECOMIN_MIN_LOAD_FRAC`, MISO-only) and `c23608b8` spp-102 (SPP-scoped `spp_commitment_posture`). **Both INERT for NYISO.** This PR's own hunks are reached only with `nyiso_ne_ac_recon_detach` armed. Form 4 is valid; the keeper's committed bundles are the control.

## 4. Legs (rule 36)

Five year-isolated shards at the pinned `main` SHA:

`python3 scripts/replay_keeper.py results/calibration/nyisonext12_span --years <y> --out-dir results/calibration/nyisonext13_<y> --set nyiso_ne_ac_recon_detach=true` (2022–2025), and the same from `results/calibration/nyisonext12_2021` for 2021.

## 5. Gates (fixed before any solve)

- **G-1 leg acceptance.** `git rev-parse HEAD` = pin; the leg's `run_config.json` `scenario_config` equals the keeper's except `nyiso_ne_ac_recon_detach: true`; the log carries `nyiso_ne_ac_recon_detach — 16 NE AC rows out of the monthly band`.
- **G-2 (a) the node follows its own bands.** In P1, the node's net flow is within one band step of the flow its own bands imply at its own LMP in **≥ 95 %** of hours, every year (keeper: 33.5–63.2 %).
- **G-2 (b) the band holds the pooled node.** The pooled node's monthly net import lies inside the detached band in every month of every year (zero LP, from the leg's dispatch).
- **G-2 (c) two-way.** The node exports in ≥ 1 h and imports in ≥ 1 h in P1, every year.
- **G-3.** C6 PASS and C8 PASS, every year.

## 6. Promotion rule (fixed before any solve)

**Promote iff G-1, G-2 (a)(b)(c) and G-3 hold in all five years.** This is a structural promotion (rule 1). C1, C3a, C3b, C3c, the node's TWh versus measured and its hours at bound are **reported, not gating**, in either direction. If any gate fails, the run is registered (rule 15) and not promoted, and the owner is asked.

## 7. Reported (not gates)

Per year: C1 key classes, C3a, C3b, C3c, hourly price MAE, zonal load-weighted Δprice; node TWh vs measured; pooled TWh vs target; hours at the posted export bound; D-4 FAIL rows.
