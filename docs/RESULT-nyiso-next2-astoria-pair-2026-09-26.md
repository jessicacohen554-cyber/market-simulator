# RESULT — NYISO-NEXT-2: the Astoria stack-duplicate boiler pair in the outage extract; promoted — 2026-09-26

**Session:** NYISO-NEXT-2 (orchestrator; no LP in this container, rule 32 (a)).
**PRECOMMIT:** `docs/PRECOMMIT-nyiso-next2-astoria-pair-2026-09-26.md`, pinned
`9fe82bde8aa2090c55c1440a307a8a99cf6861f8` before any solve.
**New keeper:** `2026-09-26-nyisonext2-astoria-pair-span` (bundle `results/calibration/nyisonext2_span`,
2022–2025).
**Stamped held-out run:** `2026-09-26-nyisonext2-astoria-pair-2021` (bundle
`results/calibration/nyisonext2_2021`).
**Superseded and pruned (rule 35):** `2026-09-26-nyisonext-floor-layup-span` and its stamped
`2026-09-26-nyisonext-floor-layup-2021`.

## 1. Headline

- **Lever (c), a data repair with ZERO `scenario_config` changes.** The outage deriver never folded
  CAMPD's stack-duplicate twins (Astoria 8906 `32SH`/`52SH`).
  - Each twin was booked at the generator's full peak, so the plant basis read 1,705 MW against a
    physical 934.
  - The duplicate was missing from the merit panel, so it failed open to "outage" on every stop its
    primary classified as lay-up.
  - The repair drops the duplicate rows. The committed hour-grain extract pair was re-derived under
    its committed invocation (rule 23; the nyiso-192 form).
  - Every non-8906 row is byte-identical. Offer curves are byte-identical. There are zero new free
    parameters.
- **Why not (a), (b) or (d):** see PRECOMMIT §2.
  - (a): the Con Ed VAC is unpublished, and the NYC steam plants file no EIA-923 receipts.
  - (b): P-27 offers carry no unit, zone or class identity.
  - (d): grounding CC higher hands the energy to NYC steam, and the `econ_high` 1.21 restore is a
    DO-NOT-REDO.
- **Determination: span CALIBRATED → NOT-YET.**
  - C3a mean LMP 2022 −8.8 → **−10.8 %** and 2025 −9.2 → **−11.0 %** both cross the ±10 % band.
    C3c is therefore no longer the lone failure and is not auto-ledgered (rule 22).
  - Held-out 2021 goes **NOT-YET → CALIBRATED** (C1 CC_REGULAR +3.81 FAIL → +3.68 PASS).
- **NYC steam moves further over EIA-923 in every year, as pre-registered.** Astoria gains 1.0 to
  1.8 TWh a year. My binding-hour bound (0–0.54 TWh) **under-predicted this by 2–5×**: once the
  availability basis doubled, Astoria is re-dispatched economically at a lower NYC price.
- **Promoted under the pre-registered rule (PRECOMMIT §7):**
  1. every leg passes acceptance;
  2. C6 and C8 pass in every year;
  3. no new `reliability_floor` D-4 row appears.

  The determination regression is reported, not a bar (rule 14 `[R-ACCURATE]`): the accurate input
  is kept, and the worse fit is the known open NYC-steam merit-order object.

## 2. Legs (rule 36; provenance SHAs only, rule 33 (d))

| year | shard commit | S0–S5 | solve |
|---|---|---|---|
| 2021 | `9b008aa403e4e1dbd5cf43e985dad3864efbe594` | OK | |
| 2022 | `00a2b48787272fac6c2e3959ea566636db33b605` | OK | |
| 2023 | `412c0f8aedbb76fd665adcb03eb77ad2f3c124cd` | OK | 246 s, peak 12.77 GiB |
| 2024 | `85b0ab6851e7c5bb755734d8f89fa81927a5062c` | OK | 282 s, peak 12.73 GiB |
| 2025 | `51674648560717d37499bfe58003c70eee53262b` | OK | 272 s |

- **Composition:** 2022–2025 composed at zero LP (`scripts/probes/nyisonext2_compose_span.py`), then
  `--rebuild-benchmark`. All 10 shared-input refs equal the outgoing keeper's (campd `7ea5a0beeb85`,
  eia923 `41fa13cb9274`, eia930 `12e2ee328d0a`).
- **2021:** `--restore-shared-inputs`, three inputs, hash-verified.
- **Launch record:** the first 2023 shard came up with no prompt (0 tokens). It was archived and
  relaunched on the same pin. All six shards are archived.

## 3. Per year, arm vs control (control = the keeper's committed bundles, rule 29 (b) form 4)

### 3.1 Rubric (keeper → arm)

| criterion | 2021 (held out) | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| C1 ST_GAS (TWh) | −1.60 → −0.71 | −1.34 → −0.29 | +2.14 → +3.06 | −0.44 → +0.15 | SKIPPED |
| C1 CC_REGULAR | **+3.81 FAIL → +3.68 PASS** | +1.60 → +1.32 | +1.05 → +0.57 | +3.14 → +2.97 | SKIPPED |
| C1 CC_CHP | −0.06 → −0.22 | −0.47 → −0.73 | +1.00 → +0.77 | +1.91 → +1.71 | SKIPPED |
| C1 CT_PEAKER | +1.82 → +1.30 | −0.79 → −1.13 | −1.83 → −1.85 | −1.57 → −1.60 | SKIPPED |
| C3a mean LMP | −5.3 → −6.5 % | −8.8 → **−10.8 % FAIL** | −1.1 → −2.5 % | +0.6 → −1.0 % | −9.2 → **−11.0 % FAIL** |
| C3b NRMSE | 0.188 → 0.192 | 0.175 → 0.190 | 0.124 → 0.126 | 0.164 → 0.161 | 0.159 → 0.172 |
| C3c h > $300 (model / RT) | 0 / 3 PASS | 9 → 5 / 101 | 0 / 10 | 0 / 13 | 2 / 42 |
| C4 gas r | 0.923 → 0.923 | 0.865 → 0.867 | 0.941 → 0.940 | 0.904 → 0.905 | 0.855 → 0.856 |
| C8 ST_GAS forced | 19.8 → 19.1 % | 16.1 → 15.9 % | 12.2 → 11.8 % | 17.2 → 17.6 % | 14.5 → 14.7 % |
| Determination | NOT-YET → **CALIBRATED** | span CALIBRATED → **NOT-YET** | | | |

C3c for 2022–2025 is CAVEAT in the keeper and FAIL in the arm; the magnitudes are unchanged except
2022, where the model's hours above $300 fall from 9 to 5. It is not auto-ledgered because it is no
longer the lone failure.

### 3.2 ST_GAS vs EIA-923 (TWh: keeper → arm vs 923)

| year | NYC | Long Island | Capital/Hudson |
|---|---|---|---|
| 2021 | 4.54 → **5.53** vs 1.98 | 2.78 → 2.74 vs 5.75 | 0.35 → 0.30 vs 1.13 |
| 2022 | 4.30 → **5.57** vs 2.27 | 2.50 → 2.38 vs 4.10 | 0.68 → 0.58 vs 1.96 |
| 2023 | 7.86 → **8.83** vs 2.56 | 2.15 → 2.13 vs 3.98 | 0.32 → 0.30 vs 1.15 |
| 2024 | 4.88 → **5.70** vs 2.77 | 3.47 → 3.31 vs 5.03 | 0.81 → 0.74 vs 1.54 |
| 2025 | 5.21 → **6.19** vs 4.38 | 3.53 → 3.39 vs 5.33 | 1.31 → 1.17 vs 2.64 |

| plant | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| Astoria 8906 | 1.71 → **3.25** vs 0.66 | 2.12 → **3.64** vs 0.83 | 1.72 → **3.49** vs 0.73 | 1.72 → **2.73** vs 0.87 | 1.99 → **3.08** vs 1.36 |
| Ravenswood 2500 | 1.96 → 1.50 vs 0.44 | 0.99 → 0.89 vs 0.48 | 4.45 → 3.91 vs 0.79 | 1.88 → 1.81 vs 0.63 | 1.25 → 1.23 vs 0.96 |
| Arthur Kill 2490 | 0.87 → 0.78 vs 0.87 | 1.19 → 1.04 vs 0.96 | 1.69 → 1.43 vs 1.04 | 1.28 → 1.16 vs 1.27 | 1.97 → 1.88 vs 2.06 |
| Northport 2516 | 1.95 → 1.92 vs 3.95 | 1.82 → 1.74 vs 2.90 | 1.45 → 1.44 vs 2.39 | 2.38 → 2.30 vs 3.71 | 2.60 → 2.52 vs 4.09 |
| Bowline 2625 | 0.24 → 0.20 vs 0.98 | 0.51 → 0.43 vs 1.47 | 0.17 → 0.16 vs 0.94 | 0.55 → 0.50 vs 1.29 | 0.85 → 0.75 vs 1.96 |

### 3.3 CC_REGULAR vs EIA-923 by zone (TWh: keeper → arm vs 923; `_nyisonext2_ccregular.json`)

| year | NYC | Capital/Hudson | Long Island | Upstate West |
|---|---|---|---|---|
| 2021 | 12.44 → 12.43 vs 10.25 | 17.92 → 17.85 vs 16.59 | 3.70 → 3.64 vs 3.22 | 0.08 → 0.08 vs 0.25 |
| 2022 | 13.40 → 13.39 vs 11.33 | 19.75 → 19.56 vs 20.02 | 3.04 → 2.97 vs 3.16 | 0.21 → 0.20 vs 0.26 |
| 2023 | 14.51 → 14.50 vs 13.31 | 16.20 → 15.80 vs 15.90 | 2.99 → 2.94 vs 3.38 | 0.40 → 0.39 vs 0.45 |
| 2024 | 14.41 → 14.39 vs 13.75 | 18.75 → 18.69 vs 16.88 | 2.80 → 2.74 vs 2.87 | 1.19 → 1.17 vs 0.56 |
| 2025 | 12.62 → 12.59 vs 11.02 | 17.60 → 17.49 vs 15.97 | 3.42 → 3.35 vs 3.42 | 2.05 → 2.02 vs 0.64 |

- Plants that moved more than 0.05 TWh: Bethlehem 2539 (2022 4.92 → 4.83 vs 5.14; 2023 4.43 → 4.09
  vs 4.36) and Flynn 7314 (2022 0.49 → 0.42 vs 0.67).
- **NYC CC_REGULAR does not move.** Its C1 over-run is not the object the Astoria steam displaces.

### 3.4 Hourly price vs RT, ISO simple mean (bias / MAE, $/MWh)

| year | keeper | arm |
|---|---|---|
| 2021 | −1.75 / 10.85 | −2.16 / 10.89 |
| 2022 | −5.36 / 22.17 | −6.85 / 22.09 |
| 2023 | +0.54 / 8.84 | +0.14 / 8.78 |
| 2024 | +1.08 / 10.25 | +0.51 / 10.14 |
| 2025 | −11.14 / 25.11 | −12.22 / 25.28 |

The price falls $0.4–1.5 in every year. MAE improves in 2022–2024 and worsens in 2021 and 2025.
MAE is not a promotion criterion.

### 3.5 D-4 unit-conduct FAIL rows

| year | keeper | arm |
|---|---|---|
| 2021 | 2480 | 2480 |
| 2022 | 2480, bridge 54574 | 2480, bridge 54574 |
| 2023 | 2480 | 2480 |
| 2024 | 2480, bridge 54574 | 2480, bridge 54574, **bridge 8906** |
| 2025 | 2480, 8006 | 2480, 8006 |

- **One new row: `nyiso_gas_commitment_bridge × ST_GAS` at 8906 in 2024.** It covers 0.005 TWh in 54
  binding hours, with a measured-zero share of 0.70. The bridge now reaches newly available Astoria
  capacity in hours its meter read zero. This row is reported, and it is the successor's to repair.
- **Every Astoria `reliability_floor` row passes.** The floored energy rises (e.g. 2024 0.039 →
  0.115 TWh), and its off-window share stays ≤ 0.053, as §1.3 of the PRECOMMIT placed it.

## 4. What remains (routed, not absorbed)

1. **NYC steam economic dispatch is now worse, and it is plural.**
   - Astoria is at 3.1–3.6 TWh against 0.7–1.4 measured, on top of Ravenswood.
   - The repaired availability exposes that the model finds Astoria (Z6 + D(2) gas, heat rate
     ~10.4–10.8) in merit far more often than it ran.
   - This is the same merit-order object as before. Its measured routes (a) and (b) are
     data-blocked (PRECOMMIT §2).
2. **C3a 2022 / 2025** now sit just outside ±10 %. The whole move is the lower NYC price from the
   added cheap steam.
3. **The day-grain `-perunitmerit-` extract and `thermal_tranches-perunitmerit-NYISO.csv`** still
   carry the Astoria double count. Neither reproduces at HEAD even before the repair, so re-deriving
   them is a separate lane.
4. **The gas bridge at 8906 2024** (the new D-4 row).
5. **The Long Island level and spread** are unchanged.
6. **Latent, other lanes:** `mustrun_layup_window_mask` / `netload_drag_layup_window_mask` resolve
   only the unsuffixed lay-up file, so MISO's must-run mask may be inert. This is reported for the
   MISO lane and not acted on.
7. **`complete` marker:** withdrawn (R-BC/Q5). The keeper now reads NOT-YET, so it cannot be
   reinstated on this keeper.

## 5. Records

- **Keeper and status:**
  - keeper shard `keepers/NYISO.json` (with lineage);
  - `status/NYISO.js` rebuilt (NOT-YET);
  - gate (a) re-keyed in `program-status.json`; it stays fail;
  - `calibration-complete.json` carries no NYISO entry to re-key.
- **Checks:** `audit_keepers --iso NYISO` 0 failures; `check_promotion_completeness` OK. There is no
  new field, so no FR-22 declaration is needed.
- **Matrix:** the NYISO `campd_outage_merit_order_guard` cell stays K with this evidence; the keeper
  and gates are re-stamped; the §5.5 header is updated.
- **On `main` with this PR (rule 33 (f)):**
  - the deriver repair plus its test;
  - the re-derived extract pair;
  - the slim keeper bundle and the slim 2021 bundle;
  - both registry sidecars and run payloads;
  - the phase-0 census JSONs and the comparison JSONs.
- **Not on `main`:** the four 2022–2025 per-year legs (with `dispatch/`) are gitignored. Rebuilding a
  leg would be a re-solve, about 5 min of LP per year in parallel shards.
- **Leftover refs the owner must delete** (sessions cannot): `claude/nyisonext2-2021` through
  `claude/nyisonext2-2025`, plus the earlier `claude/nyisonext-2021` through
  `claude/nyisonext-2025`.
