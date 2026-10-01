# PRECOMMIT — NYISO-NEXT-8: remove the HQ double count from the import-ladder derivation

- **Session:** NYISO-NEXT-8, the orchestrator. No LP runs in this container (rule 32 (a)).
- **Written before any solve.**
- **Keeper (control, form 4):** `2026-09-27-nyisonext6-li-cap-span`, bundle `results/calibration/nyisonext6_span`, 2022–2025. The 2021 held-out run `2026-09-27-nyisonext6-li-cap-2021` is stamped to it (bundle `results/calibration/nyisonext6_2021`). Keeper `git_sha` `671fa815`.
- **Probe:** `scripts/probes/nyisonext8_hq_dedupe_phase0.py` → `results/phase0/nyiso/_nyisonext8_phase0.json` (zero LP).

## 0. The defect

`derive_nyiso_import_tranches.EXTERNAL_SEAMS["HQ"]` summed `SCH - HQ_IMPORT_EXPORT` next to `SCH - HQ - NY`. The first row is an accounting duplicate of the second, and `nyiso_par_attribution.ACCOUNTING_DUPLICATE` already excludes it. So every committed NYISO ladder was derived on a net import that counted HQ twice. The cause is the defect, not a residual (rule 23). It is a rule-14 correction to a measured input, with zero DOF.

## 1. Phase 0 (zero LP), every year the ladder carries

| year | corr dup vs HQ-NY | net import, derivation → true (MW) | offline duration RMSE, old → new (MW) | offline TWh, old / new / measured | HQ seam mean (MW) |
|---|---|---|---|---|---|
| 2018 | 0.983 | 4,050 → 3,055 | 827 → 249 | 32.58 / 26.43 / 26.76 | 1,329 |
| 2019 | 0.966 | 3,620 → 2,641 | 902 → 224 | 30.10 / 22.98 / 23.13 | 1,247 |
| 2020 | 0.955 | 3,140 → 2,280 | 861 → 204 | 26.93 / 19.95 / 19.98 | 1,136 |
| 2021 | 0.987 | 3,979 → 3,107 | 713 → 252 | 31.88 / 26.91 / 27.22 | 1,228 |
| 2022 | 0.989 | 3,786 → 3,080 | 583 → 297 | 30.00 / 26.44 / 26.98 | 1,082 |
| 2023 | 0.977 | 2,693 → 2,546 | 337 → 215 | 23.09 / 22.23 / 22.30 | 303 |
| 2024 | 0.989 | 2,146 → 2,360 | 447 → 220 | 18.46 / 20.57 / 20.67 | −153 |
| 2025 | 0.993 | 1,671 → 2,197 | 681 → 211 | 14.51 / 19.17 / 19.24 | −545 |
| pooled 2023–25 | — | — | 472 → 215 | 56.06 / 61.97 / 62.21 | — |

- The offline score is `derive_nyiso_import_tranches.offline_score`, and both ladders are scored against the **true** net import.
- Hourly correlation is unchanged (±0.04). Diurnal correlation is unchanged, except 2021 (+0.07) and 2022 (+0.07).
- **Reproduction check.** Re-running the unfixed producer today reproduces the committed rungs to ≤ $0.01, except HQ_hydro: 2018 +$0.03, 2020 +$0.08, 2022 +$0.19. HQ_hydro is a must-flow rung. This drift is disclosed and not chased.

**Rung prices, old → new** (keeper-live rungs in bold, see §2):

| year | HQ_hydro | **IESO_Ontario** | **PJM_shoulder** | PJM_west | **eastern_mid** | ISONE_tie | scarcity $ | scarcity MW |
|---|---|---|---|---|---|---|---|---|
| 2021 | 11.30 → 11.41 | 13.52 → 13.97 | 16.28 → 18.52 | 20.42 → 27.39 | 26.01 → 37.70 | 33.42 → 49.41 | 61.00 → 85.57 | 2,560 → 1,480 |
| 2022 | 25.16 → 23.77 | 34.27 → 36.06 | 41.12 → 44.21 | 46.94 → 52.55 | 53.35 → 64.64 | 62.59 → 86.91 | 126.79 → 174.89 | 2,760 → 1,575 |
| 2023 | 15.20 → 13.59 | 18.67 → 17.41 | 22.91 → 22.46 | 27.88 → 28.61 | 33.61 → 37.65 | 40.23 → 51.53 | 71.66 → 99.60 | 2,230 → 1,065 |
| 2024 | 20.97 → 17.50 | 25.70 → 22.27 | 29.85 → 26.98 | 35.02 → 33.64 | 41.83 → 44.58 | 54.38 → 68.11 | 122.71 → 138.03 | 2,120 → 1,150 |
| 2025 | 31.32 → 20.43 | 44.09 → 30.76 | 59.82 → 43.16 | 79.19 → 65.77 | 102.99 → 105.83 | 128.54 → 153.51 | 208.77 → 242.96 | 1,725 → 835 |

2018–2020 and the pooled static entry are also re-derived; see the JSON. The pooled ISONE_tie rung goes $71.46 → $104.54, which moves NYISO forecast runs.

## 2. What reaches the keeper's LP (zero-LP footprint)

- The keeper arms `nyiso_import_hub_prices`. That repricer overwrites **PJM_west, ISONE_tie and import_scarcity** with measured neighbour DA LMPs, so their static prices are inert in the backcast.
- HQ_hydro is firm-floored, so its price is cosmetic.
- **Live:** the IESO_Ontario, PJM_shoulder and eastern_mid prices, plus the scarcity **capacity**, which binds because the keeper arms `nyiso_import_sil_retire`.
- **Capacity footprint** (the keeper's own hourly import against the new ladder total):

  | year | ladder total, old → new (MW) | keeper max hourly import (MW) | hours above new total |
  |---|---|---|---|
  | 2021 | 6,910 → 5,830 | 5,693 | 0 |
  | 2022 | 7,110 → 5,925 | 6,021 | 4 |
  | 2023 | 6,580 → 5,415 | 5,260 | 0 |
  | 2024 | 6,470 → 5,500 | 5,428 | 0 |
  | 2025 | 6,075 → 5,185 | 5,231 | 1 |

  Every year has < 0.001 TWh above the new total. The live object is the three static rung prices, over the 7,456–8,405 h/yr the keeper imports between 900 and 4,350 MW.

## 3. The firm floor (asked; NOT tuned, routed)

**The 900 MW always-on HQ_hydro floor exceeds the measured lightest-import hour in every year:**

| year | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| share of hours measured total net import < 900 MW (%) | 1.2 | 3.7 | 3.3 | 0.5 | 3.7 | 3.2 | 6.5 | 5.9 |
| minimum hour (MW) | −331 | −354 | 0 | −97 | −611 | −377 | −852 | −640 |

- This is pre-existing and independent of this fix. The keeper's hourly import minimum is exactly 900 MW in 2023–2025, so the floor binds.
- The HQ seam alone is a net **export** on average in 2024–2025 (−153 / −545 MW; export share of hours 57 % / 82 %). So the block's "HQ firm contract" identity is falsified in those years.
- **Routed** to the NYISO lever queue as a rule-17 question (`nyiso_firm_imports`: a floor with no window, binding in hours its own driver data says the flow is below it). It is not addressed here.

## 4. Landing decision (ex ante)

**(b) chosen for the code:** the producer imports `ACCOUNTING_DUPLICATE` from `nyiso_par_attribution`, drops the row, and asserts it is never re-listed. One name for the duplicate across both modules (rule 19). A regression test reads the producer's `EXTERNAL_SEAMS` literal.

**Direct correction, not a gated field:**

- This replaces a known-wrong measured input. It does not add a mechanism.
- A default-off field would keep the double-counted ladder selectable. Rule 14 says keep the accurate input. Rule 26 says a deprecated value that still parses is re-armable.
- There is no `ScenarioConfig` field, so there is no matrix row and no DOF.
- The cost is stated: the change re-keys every NYISO run through the solve-surface fingerprint (`interchange/spec.py`), forecast included.
- If the owner declines promotion, the keeper no longer reproduces at HEAD. Then the owner's choice is to promote anyway or revert this commit. Rule 14 says keep it.

## 5. G-DRIFT (keeper `671fa815` → `origin/main` `877b7776`)

Every hunk on the backcast path is **INERT for NYISO**:

| hunk | why inert |
|---|---|
| `zone_assignment.py`, `data/raw/reference/*` | ERCOT only (NEXT-7 §0) |
| `outages.py`, `fleet/arrays.py`, `resolved_inputs.py`, `scenarios.py` (`unit_outage_full_rederive`) | default off, absent from the keeper recipe |
| `campd_bins.py`, `fleet/__init__.py`, `assembly.py`, `offer_curves.py`, `coal.py`, `reserves/spec.py` (`campd_unit_fuel_split`) | default off; also forced False under `campd_per_unit_attribution` (keeper: true); no NYISO `-fuelsplit-` companion exists |
| `interchange/spec.py` CAISO 2019–2021 rows | CAISO branch |
| `lp/{layout,bounds,costs,rows,model,__init__}.py`, `pipeline/spec.py`, `run_calibration.py`, `coal_fuel_inventory.py` (soft coal take floor) | armed only under `coal_fuel_inventory` (keeper: null) → `n_take_slack = 0`, layout unchanged |
| `scripts/lib/forecast_parity_registry.py` | not on the solve path |

**Form 4 is valid.** The only LIVE change is this lane's ladder.

## 6. Gates (fixed now; arm vs the keeper's committed bundles)

- **G-1 input identity (shard hard stop).** Each leg solves at the pinned SHA. The resolved `IMPORT_TRANCHES_BY_YEAR["NYISO"][y]` must equal `_nyisonext8_phase0.json` `ladder_new`. The recipe must be the keeper's, byte for byte (`replay_keeper.py`, no `--set`).
- **G-2 direction (structure: the LP responds to the input as the input implies).** In 2021 and 2022, all three live rungs rise, so annual import TWh must not rise: Δ ≤ +0.01 TWh. In 2023–2025 the rungs move in mixed directions, so those years are reported only.
- **G-3 protective.** C6 and C8 PASS in every year. The D-4 FAIL row set is reported against the keeper's.
- **G-4 reported, NOT a criterion:** C3a, C3b, C1, C2 per year, the determination, and load-weighted Δ price per zone.

## 7. Promotion rule (ex ante)

- **Promote iff G-1 is exact in all five legs, G-2 holds, and G-3 holds.**
- The basis is rule 1 plus rule 14: the ladder becomes the measured one. C3a moving in either direction neither promotes nor blocks.
- If G-2 fails, the response is investigated, not promoted, and the owner is asked (rule 31).
- Year set: the union over the NYISO sidecars is {2021, 2022, 2023, 2024, 2025}. All five are solved, one shard per year (rules 34 (c), 35 (b), 36).
