# RESULT — R-ERCOT-12: Frontera dated membership, PROMOTED; the 2024 tight-hour lever closes with no arm; ISO reads NOT-YET

**Session:** R-ERCOT-12, 2026-09-28.
**PRECOMMIT:** `docs/records/ercot/PRECOMMIT-r-ercot-12-frontera-membership-2026-09-28.md`, pinned SHA `2af9ab74cae3ca183801ce6989ab930de6417c86`.
**Keeper:** `2026-09-28-r-12-frontera-membership` (bundle `results/calibration/r_ercot12_frontera_span`, 2019–2025). It supersedes `2026-09-28-r-11-parish-split`.

**Owner cards, verbatim answers:**
- Scope: *"Fleet + benchmark (Recommended)"*
- SCED key: *"Still declined"*
- Promotion: *"Promote (Recommended)"*

## Headline

- **ERCOT stays NOT-YET.** The train years are unchanged:
  - 2023 NOT-YET: carve-out, owner hold on k=33.
  - 2024 NOT-YET: C3a −10.7 %.
  - 2025 CALIBRATED.
- **2022 flips NOT-YET → CALIBRATED.** Five of seven years now pass their own verdict (2021, 2022 and 2025 CALIBRATED), up from two.
- **2019/2020 price gets much worse.** Frontera's non-existent 529 MW had been masking a 2019–20 over-scarcity. This is the named next object and is **not reverted** (rule 14).
- **Lever 1, the 2024 tight hours, closed at phase 0 with no arm.**
  - 87 % of the 2024 flip was ONE prior-keeper VOLL-shed hour: 2024-05-07 19:00, 3.1 MWh at Panhandle.
  - See `FINDING-r-ercot-12-2024-tight-hours-2026-09-28.md`.

## Per year (prior keeper → new keeper, P1; same scorer)

| year | tier | LW $/MWh | C3a | C3b | C1 CC_REG | C1 COAL_PRB | C1 ST_GAS | C8 ST_GAS | h ≥ $1k | slack MWh | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | val | 58.11 → **71.50** | +24.8 → **+53.6 %** | 0.677 → **1.228** | +7.95 P → **+9.63 F** | −8.84 → −8.15 F | +4.21 → +4.61 | 14.2 % | 36 → 48 | 2,017 → 4,662 | NOT-YET |
| 2020 | val | 27.20 → 28.27 | +7.1 → **+11.3 % F** | 0.272 → 0.343 | +8.03 → +9.56 F | −13.28 → −12.73 F | +6.72 → +7.12 | 11.6 % | 3 → 5 | 0 → 0 | NOT-YET |
| 2021 | val | 168.18 → 169.28 | +1.3 → +2.0 % | 0.101 → 0.104 | −3.11 → −1.52 | −1.43 → −1.33 | −0.88 → −0.60 | 24.7 % | 122 → 123 | 4,391 → 4,391 | CALIBRATED |
| **2022** | val | 67.31 → 68.54 | −10.3 F → **−8.7 % P** | 0.185 → 0.167 | −10.26 F → **−7.96 P** | +5.81 → +5.90 | −0.74 → −0.41 | 30.3 F → **28.7 % P** | 14 → 19 | 0 → 0 | NOT-YET → **CALIBRATED** |
| 2023 | train | 52.01 → 52.02 | −20.0 % | 0.293 | +2.30 → +2.50 | −1.88 → −1.86 | −0.02 → −0.40 | 16.9 % | 38 | 0 | NOT-YET |
| 2024 | train | 27.83 → 27.83 | −10.7 % | 0.189 | −1.35 | −1.22 | −1.27 | 14.7 % | 1 | 0 | NOT-YET |
| 2025 | train | 32.98 → 32.98 | −9.6 % | 0.127 | skipped | +3.72 | skipped | 20.8 % | 0 | 0 | CALIBRATED |

**Notes:**
- **C3c** is ledgered and non-downgrading in 2021, 2022, 2024 and 2025. It PASSES in 2019, 2020 and 2023.
- **2024/2025 are byte-identical in LW:** Frontera is a member all year in both.
- **Benchmark effect** (zero-LP A/B, the same builder): CC_REGULAR −3.100 / −2.756 / −2.193 / −3.042 / −0.260 TWh for 2019–2023. This equals FINDING-r-ercot-11's Frontera column exactly.

## Prediction scorecard (PRECOMMIT §4)

- **P1 met.** Frontera P1 = 0.000 TWh in 2019–22, and 0 MWh before LP row 2447 in 2023 (1.00 TWh for the year).
- **P2 met.** 2024/2025 reproduce the keeper exactly: LW 27.83 / 32.98, and C1 is identical.
- **P3 partly MISSED.**
  - 2019 CC +9.63 and 2020 +9.56: inside their bands.
  - **2021 CC −1.52: just outside the [−1.9, −1.1] band.** Better, not worse.
  - **2022 −7.96: the knife edge landed PASS**, inside [−8.7, −7.4].
  - 2023 +2.50: inside.
- **P4 MISSED on magnitude.** The bound was LW 0 to +2 %.
  - **2019 rose +23 %** and 2020 +3.9 %; 2021 +0.7 % and 2022 +1.8 % are inside.
  - The 2019 miss is scarcity-hour pricing: ≥ $1k hours 36 → 48, shed 2,017 → 4,662 MWh. The pre-registration did not anticipate that removing 529 MW would cross the 2019 scarcity knee.
  - 2022 C3a flipped to PASS, as allowed.
- **P5 met.** 2022 ST_GAS forced share is 28.7 %, which clears 30 %.
- **P6 partly MISSED.**
  - The train years hold.
  - **2022 flipped to CALIBRATED**; this was predicted to stay NOT-YET, though the flip was named as possible.

## Decision and promotion (rules 31/35)

- **Fixed rule (§5):** no train-year determination moved, so the recommendation was to promote. The owner's answer was *"Promote (Recommended)"*.
- **Before the prune:**
  - The year union is {2019..2025}, and the new keeper covers all seven years.
  - `config_partition_overrides` is byte-equal to the outgoing keeper's, and `stamp_config_partition --check` is OK.
  - The DOF ledger is carried verbatim at 12 entries; this arm adds none.
- **Re-keyed:**
  - `keepers/ERCOT.json`: configs, `r_ercot12_extension`, notes;
  - `calibration-complete.json`: keeper plus `keeper_rekey_2026_09_28_r12`, marker still withdrawn;
  - `program-status.json`: gate (a), still fail;
  - `status/ERCOT.js`;
  - the matrix shard keeper/gates stamps and §5.1.
- **Checks:**
  - `audit_keepers --iso ERCOT` before the prune showed only E13 on the outgoing run plus a stale status. After the prune and status rebuild: **0 failures, 0 warnings**.
  - `prune_iso_runs --iso ERCOT --force-uncite` removed `2026-09-28-r-11-parish-split`.
  - `check_promotion_completeness --iso ERCOT`: OK.
  - `check_gate_a_provenance` fails on **CAISO only**. It cites a superseded CAISO keeper, is already red on `main`, and is not this lane's to fix (rule 25).

## Where the bytes are (rule 34(e))

- **On `main`:** the keeper bundle `results/calibration/r_ercot12_frontera_span` (rule-15 shape), its sidecar, run payload and bench parts.
- **Per-year legs:** gitignored; local disk only.
- **Leg SHAs** (provenance only, rule 33(d)), in `.gitignore`: 2019 `474ddd1c`, 2020 `f76abe7d`, 2021 `55d1aaeb`, 2022 `e7a4832b`, 2023 `3d4a4904`, 2024 `41061da2`, 2025 `6ad0a04b`.
- **Cost:** any leg re-solve is about 20–27 min of LP.

## Routed, not fixed

1. **2019/2020 over-scarcity (the NEXT OBJECT).**
   - The model over-prices 2019 by +53.6 %, almost all of it in ≥ $1k / shed hours (August 2019).
   - Candidates, all measured inputs, nothing fitted:
     - 2019 DC-tie imports;
     - 2019 ORDC parameters and VOLL ($9,000 in 2019);
     - 2019 outage windows in the peak week;
     - 2019 wind and solar potential at peak.
   - Diagnose at zero LP from the keeper's hourlies first.
2. **2019/2020 C1 COAL_PRB shortfall** (−8.15 / −12.73) and **CC_REGULAR overshoot** (+9.63 / +9.56). These are probably the same object as (1): too little cheap supply, so CC runs harder.
3. **The 2023 carve-out level:** owner hold on k=33. Do not touch.
4. **2024 C3a −10.7 %:** the compressed price distribution (the C3b/C3c conduct object). There is no admissible arm under rule 1(c).
5. **Unchanged route list:**
   - Decker steam seam;
   - Decker/Silas Ray CAMPD-backfill double count;
   - split-child bench display row;
   - Fusco in MISO (rule 25);
   - the `build_ercot_dam_resource_crosswalk.py` coal-row drop (COAL-SUB);
   - base-red fast tests;
   - CAMPD TX 2018 off disk;
   - **the CAISO gate-(a) row** (CAISO lane).
