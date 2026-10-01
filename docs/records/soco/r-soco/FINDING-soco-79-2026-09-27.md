# FINDING — SOCO-79 (2026-09-27): the fleet-grain census for owner question (3). In SOCO the eGRID family vintage moves nothing, because a measured CAMPD channel now overwrites every row the family mechanism covers. A class-default fall-back reaches McDonough but closes neither failing row. Zero LP.

**Lane** SOCO-79 · **DATA PROFILE** soco (plus the CAISO and NYISO bundles, read only) · **Model** Opus (rule 27).
**Keeper:** `2026-09-27-soco76-egrid-identity-hr`, unchanged. `origin/main` is at `571147d0`, and PR #6784 (soco-78) is merged as `439e872c`.
**Owner rulings:** `docs/calibration-log/soco.md` has no ruling on (1) soco-75's two-sided coal bound, (2) soco-77's `tranche_startup_amortization`, or (3) soco-78's family-vintage scoping. So the zero-LP census ran and nothing was built.
**Probe:** `scripts/probes/_soco79_family_vintage.py` (`census --iso`, `greedy`). It monkeypatches `eia860.egrid_family_heat_rates_for` and makes no `src` edit.
**Outputs:** `soco79_family_vintage_{ISO}.json`, `soco79_family_vintage_units_{ISO}.csv.gz` and `soco79_family_vintage_greedy.json`.

## 1. Arms (each is a `fleet_only` rebuild via `bundle_fleet.reconstruct_bundle_fleet`, using the keeper's own recipe)

| arm | family rate applied |
|---|---|
| **A**, today | the 2023 applied artifact, `flag == ok` rows (shipped loader) |
| **B**, year-matched | `_vintages.csv` at `egrid_vintage_for_year(year)` (2025 → 2024), `flag == ok` |
| **C**, B + class default | as B, plus any family `out_of_window` at that vintage takes the row loop's `HEAT_RATE_BINS` class default instead of the plant blend |

Keepers rebuilt, all with `egrid_family_heat_rates: true`: SOCO `soco76_span` (2019–2025); CAISO `rcaiso5_XE_span` (2022–25) with its fold `rcaiso5_XE_tp_2019_2021`; NYISO **`nyisonext6_span`** (2022–25) with its fold `nyisonext6_2021`. NYISO's keeper moved from nyisonext3 to nyisonext6 today (PR #6786). Self-check: in 2023, arm B equals arm A in all three ISOs, because the vintage equals the applied vintage.

## 2. Census: rows and MW whose heat rate moves

| ISO | year | A → B (year-matched) | B → C (class-default fall-back) |
|---|---|---|---|
| SOCO | 2019–2025 | **0 rows in every year** | 2019, 2022: 3 rows / 64 MW (McDonough 710 CT tranches, 6.83 / 6.73 → 11.50). 2024, 2025: 2 rows / 64 MW (`710_3A/3B`, 6.74 → 13.50). 2020, 2021, 2023: 0 |
| CAISO | 2019, 2020, 2023–25 | 0 | 0 |
| CAISO | 2021 / 2022 | 3 rows / 225.8 MW, AES Huntington Beach 335 ST_GAS, +0.25 / +0.41 MMBtu/MWh (MW-weighted); econ offer +$1.09 / +$3.50/MWh | 0 |
| NYISO | 2021 | 2 rows / 24.7 MW: Northport 2516 GT 10.75 → **24.74** (the 2021 vintage flags it `ok`) and Port Jefferson 2517 GT 10.41 → 10.87 | 0 |
| NYISO | 2022 / 2024 / 2025 | 1 row / 12.9 MW, Port Jefferson GT −0.10 / −0.17 / −0.17 | 0 |
| NYISO | 2023 | 0 | 1 row / 11.8 MW, Northport GT 10.89 → 13.50 (soco-78's NYISO move) |

Every NYISO row that moves is a ~12 MW GT offered at $176–401/MWh. Neither the CAISO nor the NYISO numbers are entered in those ISOs' matrix shards (rule 28(d)). Each lane owns its own census.

**Why SOCO does not move at all.** Rebuilding with the family mechanism turned off (`{}`) also moves 0 rows in 2019, 2021, 2023 and 2025. Every plant the family mechanism covers (Barry 3, Greene County 10, Jack Watson 2049, Victor J Daniel Jr 6073) now takes its rate from the measured CAMPD channels: `measured_{cc,coal,st,ct}_heat_rates`, which F1 flipped on for backcast on 2026-09-24, after SOCO-53c's promotion on 09-19. Two examples: Barry CC_REGULAR sits at 7.190 (family 7.821) and Daniel COAL_PRB at 12.121 (family 12.895). The precedence is structural (measured > family > blend, SOCO-53c), so rule 19 holds and nothing is stacked. **For SOCO the mechanism is fully shadowed at fleet grain, and question (3) has no SOCO stake.** It matters only in CAISO and NYISO, whose lanes would have to answer it.

## 3. McDonough 710 CT rows (the soco-76 §2b target)

| year | 710 CT rows | A | B | C |
|---|---|---|---|---|
| 2019 | 3 CAMPD tranches, 64 MW | blend 6.828 | **blend** 6.828 (GT is `out_of_window` in its own vintage, so there is no family rate) | class default 11.50, mc $21.9 → $34.5 |
| 2020 | same | blend 6.821 | blend (no GT family row in the 2020 vintage) | **blend** (no row, so the fall-back cannot reach it) |
| 2021 | same | blend 6.703 | blend (no row) | **blend** |
| 2022 | same | blend 6.727 | blend (`out_of_window`) | 11.50, mc $52.4 → $87.1 |
| 2023 | `710_3A/3B` | 6.724 ($154) | same | same (no row) |
| 2024 / 2025 | `710_3A/3B` | 6.739 ($155 / $147) | same | 13.50 ($307 / $291), already dispatching 0 |

Year-matching alone never removes the blend from McDonough, and neither does a fall-back scoped to `out_of_window`, in 2020 and 2021. A repair that reaches all four years would have to key on "GT family absent from a multi-family plant", which is a different construction (rule 19), and was not built.

## 4. Greedy on the soco76 legs (arm C; soco-77 construction; scorer-exact C1 and C4)

| year | CT_PEAKER Δ TWh | refill | C1 COAL_BIT | C4 coal NRMSE |
|---|---|---|---|---|
| 2019 | −0.289 | COAL_PRB +0.108, COAL_BIT +0.060, CC_REG +0.057, ST_GAS +0.041 | **−4.16 → −4.13 pp, still FAIL** | 0.2500 → 0.2482 |
| 2020 | 0 (no move) | — | — | **0.301 unchanged, still FAIL** |
| 2022 | −0.375 | CC_REG +0.284, ST_GAS +0.050, COAL_BIT +0.032 | +1.16 → +1.18 PASS | 0.2401 → 0.2403 |
| 2024 / 2025 | 0 (already out of merit) | — | unchanged | unchanged |

In 2022, CT_PEAKER goes from −0.98 to −1.14 pp (still PASS). **Verdict: arm C is not a lever for either failing row.** The row that does fail (2019 COAL_BIT) is the class-level CT price-elasticity and coal-offer object from soco-78 §2 and soco-73. McDonough's 0.29 TWh is 5 % of 2019's 5.4 TWh CT over-run on the C1 basis (11.50 vs 6.10 TWh).

## 5. Owner questions (carried; none new)

1. soco-75: two-sided `coal_econ_marginal_hr_bound` for must-run-floored plants.
2. soco-77: arm `tranche_startup_amortization` for SOCO as the objective start. This is still the only registered carrier with reach on the CT level.
3. Family vintage scoping. **The measured evidence is now in:** year-matching is inert for SOCO, touches 1 CAISO plant (225.8 MW, 2021–22) and 2 NYISO GTs (≤ 24.7 MW), and does not reach McDonough. SOCO does not need a ruling on it. It is a CAISO / NYISO data-accuracy question (for example, the 2021 Northport GT at 24.74 flagged `ok`).

## 6. Retrievability (rule 34(e))

No solve, so there is nothing to retrieve. The soco76 legs were read at `9b15f842` (2019), `9fd776ab` (2022), `b5651d90` (2024) and `67df0807` (2025). They are gitignored and not committed. If the refs go, recovering them costs a re-solve.
