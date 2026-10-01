# RESULT — NYISO-NEXT: the NYC persistent-base floor stops forcing laid-up steam; promoted — 2026-09-26

**Session:** NYISO-NEXT (orchestrator; no LP in this container, rule 32 (a)).
**PRECOMMIT:** `docs/PRECOMMIT-nyiso-next-floor-layup-2026-09-25.md`, pinned
`5a977fecc5770ae77aade7a585791675b85ea544` before any solve.
**New keeper:** `2026-09-26-nyisonext-floor-layup-span` (bundle `results/calibration/nyisonext_span`,
2022–2025).
**Stamped held-out run:** `2026-09-26-nyisonext-floor-layup-2021` (bundle
`results/calibration/nyisonext_2021`).
**Superseded and pruned (rule 35):** `2026-09-25-nyiso-stgas-ldc-leg` and its stamped
`2026-09-25-nyiso-stgas-ldc-2021`.

## 1. Headline

- **ONE field armed:** `reliability_floor_layup_window_mask` (lever (b) of the lane brief: the
  pro-rata fill base).
  - A pro-rata reliability-floor limb no longer forces a unit on inside the windows the
    merit-order guard itself classifies as economic lay-up.
  - `floor_pct`, `availability` and every offer-curve band are byte-identical to the keeper's.
  - Zero free parameters; backcast-only (rule 13).
- **Determination CALIBRATED → CALIBRATED** (C3c the single ledgered caveat, rule 22).
- **Structural integrity improves in every year:**
  - the D-4 FAIL set shrinks 11 → 7 rows in 2022–2025, a strict subset of the keeper's;
  - it shrinks 3 → 1 in 2021;
  - the C8 ST_GAS forced share falls in every year.
- **Promoted** under the pre-registered rule (PRECOMMIT §7): every leg passes acceptance, no
  protective criterion newly fails, and no new reliability-floor D-4 row appears.
- **The one regression, reported and not a bar:** held-out 2021 reads NOT-YET on C1 CC_REGULAR
  (+3.50 → +3.81 TWh, out of band), because the displaced steam lands on CC. Under rule 30(c) a
  held-out year never downgrades the ISO.
- **Brief correction:** the NYC limb has read `floor_pct` **0.1663**, not 0.175, since nyiso-227
  (2026-09-11). The keeper solved on it, so lever (c) was already spent.

## 2. Legs (rule 36; provenance SHAs only, rule 33 (d))

| year | shard commit | S0–S2 | S5 | solve |
|---|---|---|---|---|
| 2021 | `398ba3fb8b3cbb1f98f839adede756b5c7eb380c` | OK | OK | 233 s |
| 2022 | `d3e0166b10fcba43e03a294901f1257e43080d45` | OK | OK | |
| 2023 | `86ffb0b9cfca2f2864b5d16d7b139fb2abfae69f` | OK | OK | 4.4 min |
| 2024 | `94c21c2daaa95ac9766bcf8d42cfcb95575c9e00` | OK | OK | 371 s |
| 2025 | `37bd24b8099eb5323dd6a5ae2ecda1a46719f96b` | OK | OK | peak mem 12.94 GiB |

- **Composition:** 2022–2025 composed at zero LP (`scripts/probes/nyisonext_compose_span.py`), then
  the benchmark was re-adopted with `--rebuild-benchmark`. All 10 shared inputs are byte-identical
  to the outgoing keeper's (campd `7ea5a0beeb85`, eia923 `41fa13cb9274`, eia930 `12e2ee328d0a`).
- **2021:** `--restore-shared-inputs`, hash-verified, identical to the 2021 control.
- **Launch record:**
  - The first launch's five shards cloned `main`, ignoring `source_revision`, and each correctly
    hard-stopped at H1 with no solve and no push.
  - The relaunch fetched and detached onto the pin before H1.
  - One relaunched 2021 shard came up with no prompt (0 tokens) and was re-launched again.

## 3. Per year, arm vs control (control = the keeper's committed bundles, rule 29 (b) form 4)

### 3.1 Rubric

| criterion | 2021 (held out) | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| C1 ST_GAS (TWh) | −0.49 → −1.60 | −1.08 → −1.34 | **+3.17 → +2.14** | −0.09 → −0.44 | SKIPPED |
| C1 CC_REGULAR | +3.50 → **+3.81 FAIL** | +1.49 → +1.60 | +0.39 → +1.05 | +3.02 → +3.14 | SKIPPED |
| C1 CC_CHP | −0.37 → −0.06 | | +0.76 → +1.00 | +1.73 → +1.91 | SKIPPED |
| C3a mean LMP | −6.4 → −5.3 % | −9.1 → −8.8 % | −1.9 → −1.1 % | +0.2 → +0.6 % | −9.4 → −9.2 % |
| C3b NRMSE | 0.192 → 0.188 | 0.177 → 0.175 | 0.123 → 0.124 | 0.163 → 0.164 | 0.160 → 0.159 |
| C3c | PASS | CAVEAT | CAVEAT | CAVEAT | CAVEAT |
| C4 gas r | 0.923 | | 0.942 → 0.941 | 0.904 | 0.855 |
| **C8 ST_GAS forced** | **22.4 → 19.8 %** | **17.6 → 16.1 %** | **15.2 → 12.2 %** | **18.8 → 17.2 %** | **15.6 → 14.5 %** |
| Determination | CALIBRATED → NOT-YET | span CALIBRATED → CALIBRATED | | | |

Blank cells were not extracted into this table. Every 2022 and 2025 C1 row not shown passes.

### 3.2 ST_GAS vs EIA-923 (TWh: keeper → arm vs 923)

| year | NYC | Long Island | Capital/Hudson |
|---|---|---|---|
| 2021 | 5.67 → **4.54** vs 1.98 | 2.77 → 2.78 vs 5.75 | 0.34 → 0.35 vs 1.13 |
| 2022 | 4.57 → **4.30** vs 2.27 | 2.49 → 2.50 vs 4.10 | 0.67 → 0.68 vs 1.96 |
| 2023 | 8.85 → **7.86** vs 2.56 | 2.20 → 2.15 vs 3.98 | 0.31 → 0.32 vs 1.15 |
| 2024 | 5.26 → **4.88** vs 2.77 | 3.45 → 3.47 vs 5.03 | 0.80 → 0.81 vs 1.54 |
| 2025 | 5.32 → **5.21** vs 4.38 | 3.58 → 3.53 vs 5.33 | 1.30 → 1.31 vs 2.64 |

NYC steam moves **toward** EIA-923 in every year.

| plant | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| Ravenswood | 3.06 → 1.96 vs 0.44 | 1.06 → 0.99 vs 0.48 | 5.03 → 4.45 vs 0.79 | 2.04 → 1.88 vs 0.63 | 1.25 → 1.25 vs 0.96 |
| Astoria | | 2.28 → 2.12 vs 0.83 | 1.78 → 1.72 vs 0.73 | 1.91 → 1.72 vs 0.87 | 2.09 → 1.99 vs 1.36 |
| Arthur Kill | 0.83 → 0.87 vs 0.87 | 1.23 → 1.19 vs 0.96 | 2.05 → 1.69 vs 1.04 | 1.31 → 1.28 vs 1.27 | |

### 3.3 Hourly price vs RT, ISO simple mean (bias / MAE, $/MWh)

| year | keeper | arm |
|---|---|---|
| 2021 | −2.16 / 10.85 | −1.75 / 10.85 |
| 2022 | −5.56 / 22.13 | −5.36 / 22.17 |
| 2023 | +0.30 / 8.72 | +0.54 / 8.84 |
| 2024 | +0.90 / 10.16 | +1.08 / 10.25 |
| 2025 | −11.25 / 25.08 | −11.14 / 25.11 |

Bias moves up about $0.1–0.4 in every year and MAE moves +$0.00–0.12. This is not a promotion
criterion.

### 3.4 D-4 unit-conduct FAIL rows

| year | keeper | arm |
|---|---|---|
| 2021 | 2480, **2500 (0.312 TWh)**, bridge 55405 | 2480 |
| 2022 | 2480, bridge 54574, bridge 8906 | 2480, bridge 54574 |
| 2023 | 2480, **8906 (0.105 TWh)** | 2480 |
| 2024 | 2480, bridge 54574, bridge 8906 | 2480, bridge 54574 |
| 2025 | 2480, 8006, bridge 55405 | 2480, 8006 |

**No new row appears.** The surviving rows (2480, 8006) sit on the cheapest-first Capital_Hudson
limb, which the mask deliberately does not touch.

## 4. What remains (routed, not absorbed)

1. **NYC steam economic dispatch.** 2023 is still +5.3 TWh over EIA-923, with Ravenswood at 4.45
   vs 0.79 TWh. The floor share of it is now small; the rest is merit order. The unpublished
   Con Ed VAC and the fuel basis are the obvious carriers.
2. **CC_REGULAR over-run.** The displaced steam lands on CC_REGULAR, which crosses its C1 band in
   held-out 2021 (+3.81 TWh) and runs +3.14 TWh in 2024. This is the same object nyiso-203b /
   nyiso-190 found in the `committed` / econ tranches.
3. **Guard extract defect (pre-existing).** Astoria's paired boilers (31RH/32SH, 51RH/52SH) carry
   identical stop windows, booked half as outage and half as lay-up. This is a likely contributor
   to nyiso-177's open NYC steam availability over-booking (G3). The mask clips correctly on top
   of it.
4. **Long Island** level and spread (unchanged; LI steam slightly further under in 2023 / 2025).
5. **C3c**, ledgered.
6. **Latent, other lanes.** `mustrun_layup_window_mask` / `netload_drag_layup_window_mask` still
   resolve the unsuffixed lay-up file. MISO ships only `-layup-perunitmerit-MISO.csv`, so its must-run
   mask may be reading nothing. That is reported for the MISO lane, not acted on.
7. **`complete` marker:** withdrawn under Q5 and still an owner decision; not taken.

## 5. Records

- Keeper shard `keepers/NYISO.json` (with lineage) and `status/NYISO.js` rebuilt (CALIBRATED).
- Gate (a) re-keyed in `program-status.json`; it stays fail on the withdrawn marker.
- FR-22: `reliability_floor_layup_window_mask` is declared `BACKCAST_ONLY` in
  `scripts/lib/forecast_parity_registry.py`.
- Matrix: the NYISO cell moves O → K, the keeper is re-stamped, and the §5.5 header is updated.
- Checks: `audit_keepers --iso NYISO` 0 failures; `check_promotion_completeness` OK.
- **On `main` with this PR (rule 33 (f)):**
  - the slim keeper bundle and the slim 2021 bundle (meta, run_config, metrics, legitimacy,
    attestation, `hourly/`);
  - both registry sidecars and run payloads.
- **Not on `main`:** the four 2022–2025 per-year legs (with `dispatch/`) are gitignored. A leg
  rebuild would be a re-solve, about 5 min of LP per year in parallel shards.
- **Leftover refs the owner must delete** (sessions cannot): `claude/nyisonext-2021` through
  `claude/nyisonext-2025`.
