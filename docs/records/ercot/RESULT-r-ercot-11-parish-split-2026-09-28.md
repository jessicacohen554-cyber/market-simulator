# RESULT — R-ERCOT-11: W A Parish split repaired — PROMOTED, ISO reads NOT-YET

**Session:** R-ERCOT-11, 2026-09-28. **PRECOMMIT:** `docs/records/ercot/PRECOMMIT-r-ercot-11-parish-split-2026-09-28.md`, merged in PR #6820, pinned SHA `d6ffbda93f5ec3fdfe219416fd612a846a2caf11`.

**Keeper:** `2026-09-28-r-11-parish-split` (bundle `results/calibration/r_ercot11_parish_split_span`, 2019–2025). It supersedes `2026-09-27-r-10-parish-fuelscope`. Owner decision card, verbatim: *"Promote (Recommended)"*.

## Headline

- **ERCOT stays NOT-YET.** 2023 is the carve-out, held by the owner at k=33. **2024 now also reads NOT-YET** (C3a −8.8 % → −10.7 %). 2025 stays CALIBRATED.
- **The owner's ruling rested on a false premise, and phase 0 corrected it.** WAP1–4 were already in the fleet as the split code `34702`, which dispatched 2.4–3.7 TWh/yr. The real defects are elsewhere:
  - **The split sits on the wrong capacity boundary.** 294 MW of coal was in the gas row.
  - **The split children never read their measured gas-steam heat rate.** 34702 was using the coal row's 10.76 MMBtu/MWh.
- **Both fixes land as predicted where the physics is local:**
  - Parish gas output now tracks EIA-923 NG-ST closely: 1.60 / 1.44 / 1.74 / 1.88 / 1.78 / 2.39 / 2.45 TWh, against actual 1.18 / 1.00 / 1.88 / 1.79 / 1.63 / 2.40 / 2.61.
  - Parish coal rises 0.9–1.9 TWh/yr.
  - 2019 improves across the board: CC_REGULAR clears, COAL_PRB goes −10.13 → −8.84, C3a +26.3 → +24.8 %.
- **Why 2024 flips.** In the 74 keeper hours above $100, available capacity rises by a net **+57 MW**:
  - Parish coal +285 MW, because coal availability is high at summer peak;
  - Parish gas −248 MW;
  - other ST_GAS +19 MW.

  Those hours' price falls from $229 to $174, and that alone moves C3a by about 1.9 pts. C3b worsens as well (0.149 → 0.189), so the actual RT prices in those hours sat closer to the old, capacity-short keeper. Rule 14 applies: the accurate capacity stays, and the tight-hour under-pricing it exposes is the named next object.

## Per year (keeper → keeper-new, P1; same scorer and repaired-clock actuals for both)

| year | tier | LW $/MWh | C3a | C3b | C3c | h > $1k | slack MWh | C1 COAL_PRB | C1 CC_REG | C1 ST_GAS | C8 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | val | 58.81 → 58.11 | +26.3 → +24.8 % | 0.695 → 0.677 | PASS | 38 → 36 | 2,033 → 2,017 | −10.13 → **−8.84** F | +8.17 F → **+7.95 P** | +5.24 → +4.21 | PASS | NOT-YET |
| 2020 | val | 27.23 → 27.20 | +7.2 → +7.1 % | 0.274 → 0.272 | PASS | 3 → 3 | 0 → 0 | −14.15 → −13.28 F | +7.98 P → **+8.03 F** | +7.65 → +6.72 | PASS | NOT-YET |
| 2021 | val | 168.24 → 168.18 | +1.4 → +1.3 % | 0.102 → 0.101 | caveat | 122 → 122 | 4,250 → 4,391 | −3.08 → −1.43 | −2.60 → −3.11 | +0.22 → −0.88 | PASS | CALIBRATED |
| 2022 | val | 67.31 → 67.31 | −10.4 → −10.3 % | 0.185 → 0.185 | caveat | 14 → 14 | 0 → 0 | +4.25 → +5.81 | −9.72 → −10.26 F | +0.30 → −0.74 | PASS → **FAIL** | NOT-YET |
| **2023** | **train** | 52.09 → 52.01 | −19.9 → −20.0 % | 0.291 → 0.293 | PASS | 38 → 38 | 0 → 0 | −3.01 → −1.88 | +2.39 → +2.30 | +0.63 → −0.02 | PASS | NOT-YET |
| **2024** | **train** | 28.43 → **27.83** | −8.8 → **−10.7 %** | 0.149 → **0.189** | caveat | 1 → 1 | 3 → 0 | −2.54 → −1.22 | −1.21 → −1.35 | −0.09 → −0.95 | PASS | CALIBRATED → **NOT-YET** |
| 2025 | train | 33.07 → 32.98 | −9.4 → −9.6 % | 0.125 → 0.127 | caveat | 0 → 0 | 0 → 0 | +1.88 → +3.72 | −0.98 → −1.48 | −1.19 → −2.04 | PASS | CALIBRATED |

- **C1 band:** ±8.00 TWh. "F" and "P" mark FAIL and PASS where a cell's status changes or matters.
- **2020 CC_REGULAR:** it tips over the band by 0.03 TWh.
- **2022 C8 is a denominator effect.** ST_GAS forced energy is flat (3.73 → 3.70 TWh), while ST_GAS energy falls 13.24 → 12.21 TWh. The share therefore moves 28.1 → 30.3 %. The forcing mechanism is the `st_netload_drag` at 3452, already convicted in ercot-259.
- **2022 C3a** is a FAIL in both columns.

## Prediction scorecard (PRECOMMIT §5)

- **P1 met.** Parish coal rises inside every band: +1.43 / +0.89 / +1.73 / +1.60 / +1.15 / +1.36 / +1.91 TWh.
- **P2 met.** 34702 falls by 32–41 % in every year.
- **P3 met.** Davis ST 49392 falls in every year.
- **P4 met.**
  - COAL_PRB 2019 lands at −8.84, inside [−9.6, −7.9], and stays FAIL. That was the knife edge.
  - 2020 lands at −13.28, 2022 at +5.81 and 2025 at +3.72, all inside their bands.
- **P5 met.** ST_GAS falls by 0.65–1.10 TWh and stays PASS.
- **P6 partly MISSED.**
  - 2019 CC lands at +7.95 and flips to PASS, inside its band.
  - 2022 lands at −10.26, inside its band.
  - **2020 CC lands at +8.03, outside the [+6.0, +8.0] bound, and flips to FAIL.**
- **P7 partly MISSED.**
  - LW moves −0.00 to −1.2 % in every year except **2024 at −2.11 %, just past the −2 % bound**.
  - **The named risk materialized: 2024 C3a is −10.7 %, outside [−10.3, −8.5]**, and 2024 C3b moves +0.040, more than the 0.03 allowed.
  - 2025 C3a is −9.6 %, inside its band.
- **P8 met.** h > $1k moves by −2 to 0 per year; slack moves by at most +141 MWh.
- **P9 met.**
  - 2023 C3a is −20.0 % and C3b 0.293.
  - C8 flipped in 2022 but did not change that year's determination; 2022 was already NOT-YET.

## Decision

- **Fixed rule (§6).** A train-year flip goes to the owner with no recommendation to revert. It went as a decision card.
- **Owner's answer:** *"Promote (Recommended)"*.
- **Multipliers:** `config_partition_overrides` are byte-equal to the outgoing keeper's (`stamp_config_partition --check` OK). No multiplier moved (rule 1(c)). The DOF ledger is carried verbatim at 12 entries.

## Promotion (rule 35)

1. **Year union read before the prune:** {2019..2025}. The new keeper covers all seven years.
2. **Re-keyed:**
   - `keepers/ERCOT.json`: the configs, the `r_ercot11_extension` block and the notes;
   - `calibration-complete.json`: the ERCOT keeper plus `keeper_rekey_2026_09_28_r11`, with the marker still withdrawn;
   - `program-status.json`: gate (a), status still fail;
   - `status/ERCOT.js` rebuilt;
   - the matrix shard's keeper and gates stamps, plus evidence on `measured_st_heat_rates`, which stays K;
   - the §5.1 header.
3. **Checks:**
   - `audit_keepers --iso ERCOT` before the prune: only E13 on the outgoing run.
   - `prune_iso_runs.py --iso ERCOT --force-uncite` removed `2026-09-27-r-10-parish-fuelscope`.
   - After the prune: 0 failures.
   - `check_gate_a_provenance`: OK.
   - `check_promotion_completeness`: OK.

## Where the bytes are (rule 34(e))

- **On `main`, via the promotion PR:** the keeper bundle `results/calibration/r_ercot11_parish_split_span` (rule-15 shape), its sidecar and its run payload.
- **The per-year legs** stay on local disk only; they are gitignored.
- **Provenance only** (rule 33(d)): the leg SHAs are in `.gitignore`. Any leg re-solve costs about 20–25 min of LP.

## The other two rulings

**Ruling 2, "Fetch 2019–22 SCED": BEHIND AUTH, so this lane stopped.**
- **Public API archive:** `api.ercot.com/api/public-reports/archive/np3-965-er` returns **HTTP 401**, demanding an `Ocp-Apim-Subscription-Key`.
  - That key is a free account at apiexplorer.ercot.com.
  - The repo records the key route as owner-declined.
- **MIS:** `IceDocListJsonWS?reportTypeId=13052` lists only publications from 2024-03-24 onward.
  - Each document expires about 4 years after publication.
  - A real 2019 `doclookupId` returns "NO Results".
- **Wayback:** it captured only listing pages, never the zips.
- **Grid Status:** returns 401.
- **OSTI 2997963:** a wind-only extract.
- **Coverage gap:** there is no raw public mirror, and Yes Energy's commercial history starts only at 2021-11.
- **Size if a key were granted:** roughly 9–15 GB of zips (an estimate).
- **Derive:** `scripts/data/derive_coal_perplant_offer.py --year Y` reads `data/raw/ercot/SCED/*.parquet`, using the `CLLIG` rows and the Submitted TPO curve. It is ready to run on fetched data.
- **Owner's options:**
  1. Grant a free API key.
  2. File an ERCOT data request.
  3. Procure commercially (from 2021-11 only).

**Ruling 3, "Diagnose only": report written, no scorer change.** `docs/records/ercot/FINDING-r-ercot-11-benchmark-vs-930-2026-09-28.md`.
- **The gap is not positive every year.** It is +3.03 / +5.86 / +4.47 / +4.79 / +2.38 / +4.78 / **−1.27** TWh.
- **Largest single item: Frontera (55098)** is counted in ERCOT in 2019–22 while it was outside ERCOT, adding 2.2–3.1 TWh/yr.
  - The model fleet dispatches it in those years too.
  - This is a membership item routed to a fleet lane.
- **Hydro missing on the 930 side** accounts for 0.35–0.85 TWh.
- **Decker (3548) and Silas Ray (3559) are double-counted** in the CAMPD backfill, adding 0.07–0.73 TWh.
- **A CHP/process-gas residual** of +0.2 to +5.5 TWh.
- **The 2022 CC_REGULAR miss is mostly not a benchmark artefact:** repairing Frontera on both sides only moves it −9.72 → −8.77.

**Correction to earlier records.** R-ERCOT-3 and R-ERCOT-10 quote Parish "actual" at 14.33 TWh (2019). They read that figure from the per-plant diagnostic row `bench.plants["3470"].e_ann`, which is the whole plant, coal plus gas. C1's `classFull` books Parish NG-ST to ST_GAS correctly. The coal-only EIA-923 figures are 13.14 / 9.81 / 12.93 / 11.33 / 9.11 / 9.76 / 12.97 TWh.

## Routed, not fixed

- **2024 tight-hour under-pricing (the next object).** The 74 hours above $100 carry C3a. This is new evidence: a capacity-correct fleet. It is not the closed C3c exhaustion record.
- **Frontera 55098 fleet/benchmark membership in 2019–22.**
- **Decker/Silas Ray backfill double count.**
- **The split-child diagnostic row.** `bench.plants["3470"]` is whole-plant and 34702 has no plant row (a display item).
- **The remaining route list is unchanged:**
  - Decker steam seam;
  - Fusco in MISO (rule 25);
  - the `build_ercot_dam_resource_crosswalk.py` coal-row drop (COAL-SUB);
  - base-red fast tests;
  - CAMPD TX 2018 off disk.
