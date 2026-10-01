# PRECOMMIT — R-ERCOT-21: Lost Pines 1 non-CHP row + EIA-923 identity CC heat rates (rule 14)

Date 2026-10-01. **Written before any solve.** The pinned SHA is the commit that carries this file.

- **Keeper and control:** `2026-09-30-r-20-gt-split`, bundle `results/calibration/r_ercot20_span` (2019–2025), basis SHA `bf7c1228`. Its committed bundle is the control for every year (G-CTRL form 4, rule 29(b)). No control solve.
- **Authority:** owner decision card, answer verbatim *"Build A+B, one arm (Recommended)"*. The evidence is in `FINDING-r-ercot-21-2022-cc-and-wharton-hr-2026-10-01.md`.
- **Rule 1(c):** `offer_curve_by_group` and every `config_partition_overrides` value are untouched. Coal offers are untouched (fenced). The 2023 k=33 owner hold stands. Promotion is the owner's (rules 31/35).

## 1. What changes (input corrections, zero free parameters, no new `ScenarioConfig` field)

### A. CC heat-rate artifact

**`scripts/data/derive_campd_cc_heat_rates.py`:**
- `_EIA923_IDENTITY_REFUSALS` gains `steam_not_metered`. This is the R-CAISO-3 mechanism, one more key (rule 19).
- New `ercot_solve_fleet_supplement`. It keeps Jack Fusco (55357, DAM-admitted, EIA-860 BA MISO) in the derive's population; the HEAD EIA-860 union had dropped it.

**`data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv`**, regenerated at HEAD. 61 of 312 rows change; every other row is byte-equal, Fusco included:
- **14 `ok` → `eia923_identity`.** These are the R-CAISO-2/3 gross-below-net catch-up; the committed artifact predated that derive change.
- **47 `steam_not_metered` → `eia923_identity`.**

### B. Lost Pines 1 (55154)

**`data/raw/reference/custom-bin-assignments.csv`** row:
- Was `1x1 / E-class (CHP) / 60-0-35-5 / 24 h / 4 h / 1.05,–,1.0,1.45`.
- Now `2x1 / F-class / 0-25-60-15 / 16 h / 6 h / –,1.08,1.0,1.55`.
- The rule is declared, not tuned: the modal CC_REGULAR 2x1 F-class sheet tuple (11 of 16 rows), matching EIA-860 (2 × 202.5 MW CT + 204 MW CA, nameplate 609 unchanged). No value was compared against any output.
- The committed-% derive cannot cover this plant: CAMPD meters only its CTs.

**`master-plant-registry.csv`:** `plant_group` CC_CHP → CC_REGULAR. The registry is read only for `year_built` and the oil-primary set, so this has no solve effect.

**Tests:**
- `tests/unit/data/test_r_ercot_bin_heat_rates.py`: +2.
- `tests/iso/caiso/test_caiso_rcaiso3_eia923_identity.py`: updated, because `steam_not_metered` now swaps.
- `tests/unit/data/test_measured_cc_heat_rates.py`: green.

## 2. Zero-LP footprint (`scripts/probes/_r_ercot21_census.py`, base vs arm, `r_ercot21_census_cc.csv`)

- **Only Lost Pines gains capacity:** CC_REGULAR pmax +365.4 MW, available energy +2.5 TWh in 2022 and 2024. Must-run, and every other plant's availability, is unchanged.

**`mc_base` median moves (2022 / 2024, $/MWh):**

| Plant | 2022 | 2024 |
|---|---|---|
| Wharton 3469 | **−14.78** | −1.96 |
| Bosque 55172 | −5.65 | −2.25 |
| Wise 55320 | −2.65 | — |
| Gregory 55086 | −1.74 | −1.26 |
| Tenaska Gateway 55132 | — | −0.81 |
| Sam Rayburn 3631 | +6.65 | +2.94 |
| Cedar Bayou 4 56806 | +1.50 | +2.21 |
| Ferguson 4937 | +0.33 | +0.26 |
| Lost Pines 55154 | ≈ 0 | ≈ 0 |

## 3. G-DRIFT (keeper basis `bf7c1228` → HEAD)

- 43 commits. The solve-path hunks are all NWPP-NEXT-14, R-CAISO-20 or NYISO-NEXT, and each is either:
  - a new flag (`eia923_cc_family_heat_rates`, `cc_subfloor_eia923_heat_rates`, `campd_per_unit_vintage_denominator`), default off and absent from all seven recipe years; or
  - a branch that is CAISO/NWPP-only (`interchange/caiso.py`, `eia930/envelopes.py`, the per-unit fuel-split selector, gated on `campd_per_unit_attribution`, which is false in the recipe).
- `EGRID_CC_HR_PHYSICAL_FLOOR` is read only under `cc_subfloor_eia923_heat_rates` (off), and is declared at its live hash.
- **Every hunk is INERT for an ERCOT backcast.** The only LIVE inputs are this PRECOMMIT's.

## 4. Arm

- Seven shards, one per year 2019–2025 (rules 34(c) / 36). Prompts: `SHARD-PROMPTS-r-ercot-21.md`.
- Each runs `replay_keeper.py results/calibration/r_ercot20_span --years <Y> --out-dir results/calibration/r_ercot21_arm_<Y>` at the pinned SHA, with **no `--set`**.
- Input sha256 changes:
  - `custom-bin-assignments.csv` `deaebee4…` → `5550b145…`
  - `master-plant-registry.csv` `4e9eb134…` → `05584239…`
  - `campd_cc_heat_rates_ERCOT.csv` `b99a2c58…` → `1a1a79c3…`

## 5. Predictions (before solving)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| C1 CC_REGULAR (keeper) | +8.03 F | +10.81 F | −1.78 | −8.83 F | +1.53 | −3.79 | −2.67 |
| C1 CC_REGULAR (pred.) | +8.0 to +9.0 F | +10.8 to +11.8 F | −1.8 to −0.8 | **−8.4 to −7.4 (PASS possible)** | +1.5 to +2.5 | −3.8 to −2.8 | −2.7 to −1.7 |
| C3a (keeper) | +25.7 % | +7.1 % | +5.1 % | −7.7 % | −18.5 % | −9.9 % | −8.2 % |
| C3a (pred.) | +24.9 to +25.7 | +6.4 to +7.1 | +4.5 to +5.1 | −8.3 to −7.7 | −19.2 to −18.5 | **−10.5 to −9.9 (2024 likely flips NOT-YET)** | −8.8 to −8.2 |

How the CC_REGULAR numbers are built:

- **The bench rises +1.6 to +1.9 TWh/yr.** The Lost Pines BTM subtraction leaves `classFull`; `btm` CC_REGULAR goes to 0.
- **Lost Pines model output:** +1.5 to +2.2 TWh. That puts its delta on its own row near zero.
- **Wharton 2022:** +0.8 to +1.5 TWh, with about half back-filled from other CCs.
- **Bosque / Wise:** +0.2 to +0.6. **Sam Rayburn / Cedar Bayou 4:** −0.2 to −0.5.
- **2022 net CC_REGULAR delta:** +0.4 to +1.4 TWh.

Other predicted moves:

- **COAL_PRB** falls 0.2 to 0.8 TWh/yr; it is displaced by about 365 MW of cheap CC.
- **Wharton CC 2024:** 3.17 → 3.3 to 3.8 TWh (moves away from the 0.56 actual; FINDING §2.3).
- **LW price:** −0.1 to −0.6 $/MWh in every year.
- **C3b:** ±0.02. **C8 ST_GAS:** ±1.5 pp. **Slack and h > $1k:** ±2 h and ±200 MWh.

## 6. Decision rule

- **Promote** under the standing instruction ("Is it an improvement? Then promote") if no year's determination flips worse. The basis is rule 14, not the residual.
- **If any year flips worse** (2024 is expected to), send the owner a decision card with the full before/after, and keep every bundle (rule 31).
- **DOF ledger:** unchanged (zero added). The Lost Pines tuple is a declared input reconciliation, not a free parameter.
