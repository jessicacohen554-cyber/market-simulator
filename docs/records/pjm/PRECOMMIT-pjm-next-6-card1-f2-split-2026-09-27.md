# PRECOMMIT — PJM-NEXT-6 card 1: the F2 re-derive "Split" (listed-peaker dead-period windows kept) (2026-09-27)

Keeper `2026-09-27-pjm-next-5-shape` (bundle `results/calibration/pjmnext5_sh_span`, solved at `2111658c`).
Owner ruling 2026-09-27: **"Split"** the F2 outage re-derive. Written and pushed **before any solve**. No offer is
touched and no `offer_curve_by_group` multiplier moves.

## 1. What the split is

- **F2** (`unit_outage_full_rederive`, PJM-NEXT-5, not promoted) re-derived the standard CAMPD extract at HEAD. It also
  applied the `ST_GAS_PEAKER_PLANTS` unit skip, so the listed gas-steam peakers lost **every** window, including spans
  where the unit is dark (CF < `ST_GAS_CF_PEAK` = 0.02) for ≥ 5 days through the revealed high-load hours. Result:
  ST_GAS 2023/24 +8.3/+8.1 TWh (C1 FAIL).
- **The split:** the same HEAD derivation with the skip **not** applied to the listed peakers
  (`derive_campd_unit_outages.py --keep-listed-peaker-dead-periods`, new, default off). A unit dark for the whole
  window is an availability event, not economic idleness. Every other F2 correction is kept: year-consistent CC
  windows (Bergen / Hay Road / Brunot Island / Hunterstown / Ironwood), membership union, COAL-SUB fix, unit-scoped
  peaker skip scope, per-unit fuel routing.
- **Construction** (`scripts/probes/_pjmnext6_build_peakerkeep_companion.py`): the F2 recipe step for step with the
  one switch. **Control:** the same builder without the switch reproduces the committed F2 companion
  **byte-for-byte** (sha256 `a77386d8…`), so the switch is the only difference.
- **Artifact:** `data/raw/campd-unit-outages-rederive-peakerkeep-unitfuel-PJM.csv`, 14,121 rows, sha256
  `5171a5fb37bbd2a535a7f8cbde5ae06d735186d520a4620fcfe84f9f1e8d1ae9` (+ `.meta.json`). Relative to F2: +1,052 rows,
  all `ST_GAS`, all at listed plants (Edge Moor 239, Joliet 29 216, Martins Creek 156, Clinch River 156, Chalk Point
  119, Eddystone 94, Montour 32, Yorktown 16, McKee Run 13, Joliet 9 11); zero F2 rows dropped.
- **Flag:** `unit_outage_rederive_peaker_windows` (default off, zero DOF, cache-key optional), meaningful only with
  `unit_outage_full_rederive` (replaces that file, rule 19). Matrix row + every shard cell added (rule 28c).
- Short-coal layer: unchanged from F2 (`-short-rederive-`, coal-only scope, the skip never applied there).

## 2. Zero-LP census (fleet-only rebuild, keeper recipe ± both flags)

`scripts/probes/pjm_next6_card1_split_census.py`. Offers (`mc_base`) byte-identical in every year.
Δ available capacity-hours, TWh (arm − keeper):

| year | rows | CC_REGULAR | CC_CHP | COAL_BIT | ST_GAS | Δ min_gen |
|---|---|---|---|---|---|---|
| 2019 | 258 | −16.06 | −1.13 | +0.06 | −28.28 | −2.75 |
| 2020 | 190 | −19.11 | −0.74 | 0.00 | −32.54 | −2.11 |
| 2021 | 212 | −17.36 | −1.02 | −2.15 | −26.38 | −2.57 |
| 2022 | 176 | −13.21 | −1.34 | −0.05 | −24.31 | −1.86 |
| 2023 | 178 | −7.24 | −1.39 | −14.06 | −19.80 | −2.23 |
| 2024 | 161 | −4.45 | −0.76 | −5.80 | −12.38 | −0.94 |
| 2025 | 153 | −6.05 | −0.83 | −2.64 | −22.98 | −1.29 |

- CC columns equal F2's (the split touches no CC row).
- ST_GAS flips sign vs F2 (+13 to +24 → −12 to −33): the HEAD derivation gives dead-period windows to all eleven
  listed plants, more than the keeper's older extract carried (Eddystone, Clinch River, Joliet 9 had few or none).
- COAL_BIT 2024 −5.80 vs F2 −1.30: Montour unit-1 windows derived as ST_GAS are re-tagged to the coal slice by the
  per-unit fuel routing (unit 1 is coal in the 2024 EIA-860 vintage).
- Removed availability sits in hours the unit was measured dark, so the energy effect is bounded by what the keeper
  dispatched there — far below the capacity-hours.

## 3. Predictions (stated before the solve)

- **CC_REGULAR falls in every year**, 2–5 TWh in 2019–2022 (moves the +11.1 / +16.9 / +13.5 over-runs toward pass),
  1–3 TWh in 2023–2025. Risk: 2024 (keeper −4.92) may widen toward the C1 band.
- **ST_GAS falls 0.5–3 TWh** in every year (the keeper runs listed peakers inside measured-dark spans). No ST_GAS
  training-span FAIL (the F2 +8 TWh defect does not recur).
- **COAL_BIT:** 2023 falls 0.5–3, 2024 falls 0.5–2 (Montour). Pre-2023 coal may **rise** 0–3 TWh as displaced CC /
  ST_GAS energy is back-filled — against interest for 2019/2021/2022.
- **C3a:** 0 to +2 pts pre-2023 (less cheap supply).
- **Determination:** 2023–2025 stay CALIBRATED unless 2024 CC crosses its band; run-level stays NOT-YET on the
  pre-2023 rows (card 2 finds the joint CC+coal surplus is carried by the DA virtual layer, not outages).

Why it is solved: owner ruling; rule 14 (one construction per year on a measured input). Rule 1: the residual does
not select the input.

## 4. G-DRIFT (rule 29(b)): form 4 holds, no control solves

`git diff 2111658c origin/main` over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`,
`data/raw/_validation-source`, `data/raw/reference` (38 files): **every hunk INERT** for the PJM backcast — new flags
absent from the keeper recipe (`campd_unit_fuel_split`, `coal_econ_marginal_hr_two_sided`, `spp_zone_partition`,
`caiso_intertie_partial_year_measured`, `nyiso_li_seam_posted_limit_cap`), coal take-floor columns off for PJM, NYISO /
CAISO / SPP / ERCOT branches behind ISO guards, the one constant change CAISO-only, reference/validation CSV changes
ERCOT/SPP-only, provenance/metadata hunks. No default flip. This session's own edits are byte-inert with the flag off.

## 5. Execution (rules 32/34/36)

- One shard per year 2019–2025, pinned to the full SHA of the commit carrying this doc:
  `replay_keeper.py results/calibration/pjmnext5_sh_span --years <y> --out-dir results/calibration/pjmnext6_sp_<y>
  --set unit_outage_full_rederive=true --set unit_outage_rederive_peaker_windows=true`.
- Hard stops: HEAD = pin; companion sha256 = §1; leg `scenario_config` shows both flags plus
  `unit_outage_membership_repair` and `unit_outage_unit_fuel_routing` true.
- Push the full bundle (incl. `dispatch/<y>_P1.parquet`) to `claude/pjmnext6-sp-<y>` via `.gitignore` negation +
  plain `git add`.
- Parent: compose, rebuild the benchmark, score vs keeper, attest (DOF ledger carried, zero entries added,
  `authorized_price_tuning.used = false`, deltas `unit_outage_full_rederive` and
  `unit_outage_rederive_peaker_windows` False → True), register `--no-prune`, update matrix, promotion question.
