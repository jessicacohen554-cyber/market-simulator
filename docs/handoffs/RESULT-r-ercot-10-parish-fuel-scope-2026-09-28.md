# RESULT — R-ERCOT-10: W A Parish partial-outage derate fuel-scoped — PROMOTED, ISO reads NOT-YET

**Session:** R-ERCOT-10, 2026-09-27/28. **PRECOMMIT:** `docs/handoffs/PRECOMMIT-r-ercot-10-parish-fuel-scope-2026-09-27.md`, merged in PR #6808, pinned SHA `a33eeb3a6444d646965a9090ee840c8fdb8a8c1e`.

**Keeper:** `2026-09-27-r-10-parish-fuelscope` (bundle `results/calibration/r_ercot10_parish_span`, 2019–2025). It supersedes `2026-09-27-r-8-fusco`. Owner instruction, verbatim: *"Is it an improvement? Then promote"*.

## Headline

- **ERCOT is still NOT-YET, on the 2023 carve-out only.** The owner's hold on k=33 (R-ERCOT-9) stands.
- **The forward config (2024–2025) stays CALIBRATED.**
- **The repair is a small, real improvement, and no determination flips** against the keeper on the same scoring basis.
- **2020 C1 CC_REGULAR now PASSES.** The coal gap narrows: 2019 −11.17 → −10.13 TWh, 2020 −14.56 → −14.15 TWh.
- **What was wrong:** the partial-outage derate for W A Parish was built from the facility-summed CEMS series, which included the gas steam units WAP1–4, and was then applied to the coal-only bin (rule 14, misaligned boundary).

## Per year (keeper → arm, P1; C3a on the R-ERCOT-9 repaired clock for both)

C3b before is the keeper's registered, old-basis value.

| year | tier | LW $/MWh | C3a | C3b | h > $1k | slack MWh | COAL_PRB TWh | C1 fails (arm) | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | val | 59.11 → 58.81 | +27.0 → +26.3 % | 0.683 → 0.695 | 38 → 38 | 2,033 → 2,033 | 47.30 → 48.34 | COAL_PRB −10.13, CC_REG +8.17 | NOT-YET → NOT-YET |
| 2020 | val | 27.32 → 27.23 | +7.6 → +7.2 % | 0.285 → 0.274 | 3 → 3 | 0 → 0 | 34.92 → 35.33 | COAL_PRB −14.15 | NOT-YET → NOT-YET |
| 2021 | val | 168.30 → 168.24 | +1.4 → +1.4 % | 0.137 → 0.102 | 122 → 122 | 3,117 → 4,250 | 54.64 → 55.02 | — | CALIBRATED |
| 2022 | val | 67.14 → 67.31 | −10.6 → −10.4 % | 0.184 → 0.185 | 14 → 14 | 0 → 0 | 58.96 → 58.43 | CC_REG −9.72 | NOT-YET → NOT-YET |
| **2023** | **train** | 51.61 → 52.09 | −20.6 → −19.9 % | 0.290 → 0.291 | 37 → 38 | 0 → 0 | 42.68 → 42.70 | — | NOT-YET → NOT-YET |
| 2024 | train | 28.44 → 28.43 | −8.8 → −8.8 % | 0.143 → 0.149 | 1 → 1 | 3 → 3 | 41.09 → 41.18 | — | CALIBRATED |
| 2025 | train | 33.13 → 33.07 | −9.2 → −9.4 % | 0.120 → 0.125 | 0 → 0 | 0 → 0 | 49.10 → 49.56 | — | CALIBRATED |

- **C3c:** unchanged in kind. The ledgered caveat applies in 2021, 2022, 2024 and 2025; 2019, 2020 and 2023 PASS.
- **Scoring-basis change (R-ERCOT-9 clock repair), reported at full magnitude:**
  - 2022 C3a now FAILS (−10.4 %). The keeper reads −10.6 % on the same basis, so this comes from the actuals re-derivation, not from this arm.
  - The 2021 C3b improvement 0.137 → 0.102 is also mostly the basis change.

## Prediction scorecard (PRECOMMIT §5)

- **P1 met.** Parish P1 moves in the direction of its capability change and by no more than its size: 2019 +1.04 TWh coal (class), 2020 +0.41, 2022 −0.53.
- **P2 met.** 2019/2020 COAL_PRB narrows by 1.04 / 0.41 TWh and stays a FAIL. CC_REGULAR narrows: the 2020 CC failure clears, and 2022 CC narrows by 0.33.
- **P3 partly MISSED.** 2023 LW rose +0.9 % against a bound of +0.3 %. 2022 rose +0.3 % (inside its window). All other years were inside their windows.
- **P4 MISSED.** 2021 slack rose from 3,117 to 4,250 MWh. 2023 h > $1k went 37 → 38. Both are knife-edge tight hours at an unchanged level of scarcity formation. The 2021 rise is in the scarcity week of February 2021.
- **P5 met.** 2023 C3a −19.9 % sits inside [−22.0, −20.0] only at its edge: it is 0.1 pts above the band, so it is a marginal miss read strictly. 2024 −8.8 % and 2025 −9.4 % are inside their bands, and C3b moved ≤ 0.02.
- **P6 met.** No C8 gate changed a determination.

## Decision

- **Rule applied (PRECOMMIT §6):** 2024 and 2025 stayed CALIBRATED, so the fixed rule recommended promotion.
- **Owner:** answered *"Is it an improvement? Then promote"*.
- **Multipliers:** `config_partition_overrides` are byte-equal to the outgoing keeper's (`stamp_config_partition --check` OK). No multiplier moved (rule 1(c)). The DOF ledger is carried verbatim.

## Promotion

1. **Year union (rule 35(b)):** {2019..2025}, read before the prune. The new keeper covers all seven years.
2. **Re-keyed:**
   - `keepers/ERCOT.json`: the configs, the `r_ercot10_extension` block and the notes;
   - `calibration-complete.json`: ERCOT `keeper` plus `keeper_rekey_2026_09_28`, with the marker still withdrawn;
   - `program-status.json`: gate (a) identity re-keyed, status still fail;
   - `status/ERCOT.js` rebuilt;
   - the matrix shard's keeper and gates stamps, plus evidence on the `ercot_partial_outage_{shaped_derate,day_guard}` cells (both stay K);
   - the §5.1 header.
3. **Checks:**
   - `audit_keepers --iso ERCOT` before the prune: only E13 on the outgoing run.
   - `prune_iso_runs.py --iso ERCOT --force-uncite` removed `2026-09-27-r-8-fusco`.
   - After the prune: 0 failures, 0 warnings.
   - `check_gate_a_provenance --iso ERCOT` OK.

## Where the bytes are (rule 34(e))

- **On `main` once the promotion PR merges:** the keeper bundle `results/calibration/r_ercot10_parish_span` (rule-15 shape), its sidecar and its run payload.
- **Per-year shard commits** (provenance only, rule 33(d)):

  | year | commit |
  |---|---|
  | 2019 | `3a3677164b9a6d0cab4441df4c4339a5e4579233` |
  | 2020 | `007b58e345f7cfd2781a58ede044af65bb01a01c` |
  | 2021 | `cbc1169c4f9b35976729c3fad2fd6666f989e7e9` |
  | 2022 | `0b0a0a7237dff04319fad4db2209c47fa9abd722` |
  | 2023 | `3bfcec28f630f0c83d3331131b4eaa4d67a0d3ff` |
  | 2024 | `3520654f3d8951db95657b24103d3939cbb52840` |
  | 2025 | `0c3d6af846f917d0f13e90509f21621035cd26ce` |

- **Re-solve cost of any leg:** one ERCOT year, ~22–30 min of LP.
- **Leftover refs the owner must delete** (sessions cannot, rule 33(f)): `claude/r-ercot10-arm-{2019..2025}`.

## Phase-0 findings (zero LP), routed

- **(a) 2019/2020 COAL_PRB, the remaining ~10 / ~14 TWh.** The per-plant coal offer levels were measured on 2024–25 SCED and are applied, with no fuel term, to 2019–22.
  - 60-Day SCED is on disk only from 2023-03.
  - 60-Day DAM curves for 2018–22 are on disk, but W A Parish and Martin Lake submit no DAM energy curve in any year, and bridging DAM to SCED would add DOF.
  - `coal_offer_level_rebasis` is R.
  - **Owner data decision:** procure the 2019–22 60-Day SCED Gen Resource disclosures for the coal plants.
  - A secondary rule-14 item: 7 coal plants get base $1.87 fuel in 2019–22 because `COAL_PRICE_PRB_BY_YEAR` starts in 2023. It touches only `_mustrun` (< 0.5 TWh).
- **(b) 2022 CC_REGULAR −9.72 TWh.** Two parts:
  - COAL_PRB +4.8 TWh: static coal offers against HH $6.45 (Martin Lake +4.2, Coleto +1.7). Same data ask as (a).
  - A benchmark-to-load residual of about −4.4 TWh net: `classFull` is 433.5 TWh against EIA-930 generation of 428.7, so the benchmark runs 4.8 TWh above measured generation. It shows up in every year and is a scorer-side question for the owner.
  - No CC plant is missing from the fleet, and CC availability does not bind.
- **(c) Decker Creek 3548 steam 1–2.** They are in the fleet in no year, and the 206 MW CT row is relabelled ST_GAS in 2019–22.
  - The gap is ≈ 0.45 TWh/yr, 2019–21 only, and ST_GAS already overshoots in those years.
  - Not worth an arm. It needs a plant-code seam touching ≥ 5 consumers, so it is routed to a fleet lane.
  - The bench also double-counts 3548 via its CT-only CEMS flag (1.37 vs 0.69 TWh).
- **New, found this lane:** W A Parish's gas steam units WAP1–4 (about 1.1 GW; 0.9–2.2 TWh/yr of CEMS output) are not in the ERCOT fleet in any year, because the bin sheet holds one row per plant code. This is a fleet-coverage item for the next lane, of the same class as Decker. ST_GAS runs high in 2019/20 and is close to actual in 2021–25.
- **Not ERCOT's to fix:**
  - Fusco is double-counted in MISO's fleet (MISO lane, rule 25).
  - `build_ercot_dam_resource_crosswalk.py` drops the 26 coal rows on a rebuild at HEAD (COAL-SUB).
  - The base-red fast-tier tests on main.
  - CAMPD TX 2018 is off disk (BLOAT-S2), so 2018 partial-outage rows cannot be regenerated; they are carried as committed.
