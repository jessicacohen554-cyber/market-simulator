# RESULT — NYISO-NEXT-3: the committed tranche share on the solve's own availability basis; promoted — 2026-09-26

**Session:** NYISO-NEXT-3 (orchestrator; no LP in this container, rule 32 (a)).
**PRECOMMIT:** `docs/records/nyiso/PRECOMMIT-nyiso-next3-tranche-basis-2026-09-26.md`, pinned
`67fd3d1b677faa56f356ca9349e045700140b352` before any solve.
**New keeper:** `2026-09-26-nyisonext3-tranche-basis-span` (bundle `results/calibration/nyisonext3_span`,
2022–2025).
**Stamped held-out run:** `2026-09-26-nyisonext3-tranche-basis-2021` (bundle `results/calibration/nyisonext3_2021`).
**Superseded and pruned (rule 35):** `2026-09-26-nyisonext2-astoria-pair-span` and its stamped
`2026-09-26-nyisonext2-astoria-pair-2021`.

## 1. Headline

- **A correctness repair with ZERO `scenario_config` changes and zero new free parameters.**
  1. `campd_bins.fleet_to_bins` read `committed_pct` without the `merit_guard` selector. Under
     `campd_outage_merit_order_guard`, every bin's committed share therefore came from the
     **unguarded `-perunit-`** tranche artifact, while every other tranche consumer read `-perunitmerit-`.
     That is two availability bases in one LP (rule 19). The fix is one argument. Only NYISO arms the
     guard, so no other keeper can move.
  2. The `-perunitmerit-` tranche artifact had lagged two extract re-derivations (nyiso-192 and
     NYISO-NEXT-2). It is now re-derived: 8 ST_GAS rows move. Astoria committed goes 17.8 → 9.0 % and
     median_cf 57.6 → 15.4 %, against a CAMPD median loading of 9–15 % when on.
- **Item (5) of the brief alone is solve-inert.** Re-deriving the artifact without (1) leaves the fleet
  byte-identical in every year, because no keeper consumer reads the columns that move.
- **The drift is fully attributed:**
  - HEAD's tranche deriver on the nyiso-187 extract reproduces the committed artifact exactly
    (0 differing values).
  - The day-grain extract's HEAD drift is 17 rows, all 2019–2020 windows at two coal retirees and Nassau.
    They are inert and were not absorbed: the extract was committed as a splice.
- **The result is as pre-registered.**
  - NYC ST_GAS rises +0.04 to +0.10 TWh/yr (predicted +0.05 to +0.30), away from EIA-923.
  - NYC CC_CHP falls 0.04–0.12 TWh.
  - Nothing else moves materially.
- **Determination unchanged:**
  - Span NOT-YET (C3a 2022 −10.8 %, 2025 −10.9 %; C3c not lone).
  - Held-out 2021 CALIBRATED.
- **Promoted under PRECOMMIT §7:**
  1. every leg passes S0–S5;
  2. C6 and C8 pass in every year;
  3. no new D-4 row (the FAIL set is identical to the keeper's).

## 2. Legs (rule 36; provenance SHAs only, rule 33 (d))

| year | shard commit | S0–S5 |
|---|---|---|
| 2021 | `1f411bffe6104d096a3faa44fb4f51be47bf55c6` | OK (240 s, peak 8.73 GiB) |
| 2022 | `6ad45aec642c6ae1b58698fd3abe93bc947a8c1c` | OK |
| 2023 | `c62da1f8a46d69544b1b0ba554abadecc06febc9` | OK (relaunch) |
| 2024 | `6be240a8c97410e94e0a8dd1439a11f78b309dd0` | OK |
| 2025 | `8b2063744565ffeb8229f1385c51792a10cc1d0a` | OK (273 s) |

- **Composition:** 2022–2025 composed at zero LP, then `--rebuild-benchmark`. All 10 shared refs
  equal the outgoing keeper's.
- **2021:** `--restore-shared-inputs`, three inputs, hash-verified.
- **Launch record:** the first 2023 shard backgrounded its data prep, ended its turn and stranded idle.
  It was archived and relaunched with a foreground-only prompt. All six shards are archived.

## 3. Per year, arm vs control (control = the keeper's committed bundles, rule 29 (b) form 4)

Full records: `results/calibration/_nyisonext3_compare_{span,2021}.txt` and `_nyisonext3_ccregular.json`.

### 3.1 Rubric (keeper → arm)

| criterion | 2021 (held out) | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| C1 ST_GAS (TWh) | −0.71 → −0.62 | −0.29 → −0.25 | +3.06 → +3.15 | +0.15 → +0.21 | SKIPPED |
| C1 CC_REGULAR | +3.68 → +3.71 | +1.32 → +1.36 | +0.57 → +0.56 | +2.97 → +2.97 | SKIPPED |
| C1 CC_CHP | −0.22 → −0.34 | −0.73 → −0.82 | +0.77 → +0.70 | +1.71 → +1.67 | SKIPPED |
| C1 CT_PEAKER | +1.30 → +1.27 | −1.13 → −1.14 | −1.85 → −1.85 | −1.60 → −1.60 | SKIPPED |
| C3a mean LMP | −6.5 → −6.5 % | **−10.8 → −10.8 % FAIL** | −2.5 → −2.6 % | −1.0 → −1.0 % | **−11.0 → −10.9 % FAIL** |
| C3b NRMSE | 0.192 → 0.192 | 0.190 → 0.190 | 0.126 → 0.126 | 0.161 → 0.162 | 0.172 → 0.171 |
| C3c h > $300 (model / RT) | 0 / 3 PASS | 5 / 101 | 0 / 10 FAIL | 0 / 13 FAIL | 2 / 42 FAIL |
| C4 gas r | 0.923 → 0.924 | 0.867 → 0.867 | 0.940 → 0.940 | 0.905 → 0.904 | 0.856 → 0.856 |
| C8 ST_GAS forced | 19.1 → 19.0 % | 15.9 → 15.8 % | 11.8 → 11.7 % | 17.6 → 17.5 % | 14.7 → 14.6 % |
| C6 governance | PASS | PASS | PASS | PASS | PASS |
| Determination | CALIBRATED → CALIBRATED | span NOT-YET → NOT-YET | | | |

### 3.2 ST_GAS vs EIA-923 (TWh: keeper → arm vs 923)

| year | NYC | Long Island | Capital/Hudson |
|---|---|---|---|
| 2021 | 5.53 → 5.63 vs 1.98 | 2.74 → 2.74 vs 5.75 | 0.30 → 0.29 vs 1.13 |
| 2022 | 5.57 → 5.61 vs 2.27 | 2.38 → 2.38 vs 4.10 | 0.58 → 0.58 vs 1.96 |
| 2023 | 8.83 → 8.92 vs 2.56 | 2.13 → 2.13 vs 3.98 | 0.30 → 0.30 vs 1.15 |
| 2024 | 5.70 → 5.76 vs 2.77 | 3.31 → 3.31 vs 5.03 | 0.74 → 0.74 vs 1.54 |
| 2025 | 6.19 → 6.26 vs 4.38 | 3.39 → 3.39 vs 5.33 | 1.17 → 1.17 vs 2.64 |

| plant | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Astoria 8906 | 3.64 → 3.65 vs 0.83 | 3.49 → 3.50 vs 0.73 | 2.73 → 2.73 vs 0.87 | 3.08 → 3.11 vs 1.36 |
| Ravenswood 2500 | 0.89 → 0.90 vs 0.48 | 3.91 → 4.00 vs 0.79 | 1.81 → 1.85 vs 0.63 | 1.23 → 1.24 vs 0.96 |
| Arthur Kill 2490 | 1.04 → 1.06 vs 0.96 | 1.43 → 1.43 vs 1.04 | 1.16 → 1.18 vs 1.27 | 1.88 → 1.91 vs 2.06 |
| Northport 2516 | 1.74 → 1.75 vs 2.90 | 1.44 → 1.44 vs 2.39 | 2.30 → 2.30 vs 3.71 | 2.52 → 2.52 vs 4.09 |

In 2021, Arthur Kill goes 0.78 → 0.84 (vs 0.87) and Ravenswood 1.50 → 1.51 (vs 0.44).

### 3.3 CC_REGULAR vs EIA-923 by zone

Every zone moves |Δ| ≤ 0.04 TWh in every year, and no plant moves > 0.05. The NEXT-2 table
(`RESULT-nyiso-next2` §3.3) stands:
- NYC 12.4–14.5 vs 10.3–13.8;
- Capital/Hudson over in 2021, 2024 and 2025;
- Upstate West 2024 / 2025 over.

### 3.4 Hourly price vs RT, ISO simple mean (bias / MAE, $/MWh)

| year | keeper | arm |
|---|---|---|
| 2021 | −2.16 / 10.89 | −2.14 / 10.89 |
| 2022 | −6.85 / 22.09 | −6.84 / 22.11 |
| 2023 | +0.14 / 8.78 | +0.11 / 8.78 |
| 2024 | +0.51 / 10.14 | +0.51 / 10.16 |
| 2025 | −12.22 / 25.28 | −12.18 / 25.30 |

### 3.5 D-4 unit-conduct FAIL rows

Identical to the keeper's in every year:
- 2021: 2480;
- 2022: 2480, 54574;
- 2023: 2480;
- 2024: 2480, 54574, 8906 (the bridge row);
- 2025: 2480, 8006.

No new row and none gone.

## 4. What remains (routed, not absorbed)

1. **NYC steam economic over-dispatch.** Astoria runs 2.7–3.7 TWh against 0.7–1.4 measured;
   Ravenswood runs 4.0 against 0.8 in 2023.
   - **Tranche shares cannot reach it, and that is now measured.** Every non-peak band offers at
     ~$32–36 against a ~$34 NYC mean. The committed/econ split moves the offer ~3 %, and the arm
     moved NYC steam +0.1 TWh.
   - The real plants run at minimum load (median 83–136 MW at Astoria) in hours the model runs them at
     full econ output. That is conduct or commitment (the Con Ed VAC is unpublished;
     `scuc_load_pocket_commitment` is `G`), not a tranche object.
   - The measured fuel and offer routes stay data-blocked (NYISO-NEXT-2 PRECOMMIT §2).
2. **C3a 2022 / 2025** (−10.8 / −10.9 %). The NYC price is pulled down by that cheap steam. nyiso-242
   measured the missed 2022 RT tail at $5.44/MWh, which would take C3a-2022 to −4.1 %, and found it
   foreclosed by 4.4 GW of idle sub-gate capacity.
3. **CC_REGULAR over-run** in NYC and Capital/Hudson (unchanged).
4. **Long Island level and spread** (unchanged).
5. **Latent, other lanes:**
   - `mustrun_layup_window_mask` / `netload_drag_layup_window_mask` resolve only the unsuffixed lay-up
     file, so MISO's must-run mask may be inert. This is for the MISO lane.
   - `outages._load_unit_outage_events` returns the curated clean table (the INCUMBENT extract) and
     ignores the per-unit / merit / hour-grain `csv_path` whenever `MARKET_SIM_USE_CLEAN` is set. It is
     off in every runner today, but it is a trap for anyone who turns it on.
6. **`-perunit-` tranche artifact:** it still carries the Astoria double count. NYISO no longer reads it
   (the guard selects `-perunitmerit-`), so it is left as committed.
7. **`complete` marker:** withdrawn (R-BC/Q5), and it cannot stand on a NOT-YET keeper.

## 5. Records

- **Keeper and status:**
  - keeper shard `keepers/NYISO.json` (superseded block nested);
  - `status/NYISO.js` rebuilt (NOT-YET);
  - gate (a) re-keyed in `program-status.json`; it stays fail;
  - no `calibration-complete.json` NYISO entry.
- **Checks:**
  - `audit_keepers --iso NYISO`: 0 failures, 1 warning. E11 has no former bundle to diff against after
    the prune; the recipe identity is proven by leg acceptance S1.
  - `check_promotion_completeness`: OK.
  - No new field, so no FR-22 declaration.
- **Matrix:** NYISO `campd_outage_merit_order_guard` stays K with this evidence; keeper and gates
  re-stamped; §5.5 header re-stamped.
- **On `main` with this PR (rule 33 (f)):**
  - the selector repair plus its test;
  - the spliced day-grain extract pair and the re-derived tranche artifact, with their sidecars;
  - the slim keeper bundle and the slim 2021 bundle;
  - both registry sidecars and run payloads;
  - the phase-0 census and the comparison files.
- **Not on `main`:** the four 2022–2025 per-year legs (gitignored, rule 32 (d)). Rebuilding one is a
  re-solve, about 5 min of LP per year in parallel shards (plus ~40 min of data prep).
- **Leftover refs the owner must delete** (sessions cannot):
  - `claude/nyisonext3-2021` through `claude/nyisonext3-2025`;
  - `claude/nyisonext2-2021` through `claude/nyisonext2-2025`;
  - `claude/nyisonext-2021` through `claude/nyisonext-2025`.
