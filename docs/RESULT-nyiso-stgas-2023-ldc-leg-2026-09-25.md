# RESULT — NYISO-STGAS-2023: the Con Ed generator delivery leg closes C1-2023; NYISO is CALIBRATED — 2026-09-25

**Session:** NYISO-STGAS-2023 (orchestrator; no LP in this container, rule 32 (a)).
**PRECOMMIT:** `docs/PRECOMMIT-nyiso-stgas-2023-ldc-leg-2026-09-25.md`, pinned
`54ac9e1a509c0cad01aadcb9d7583535fd27d883` before any solve.
**New keeper:** `2026-09-25-nyiso-stgas-ldc-leg` (bundle `results/calibration/nyisostg_span`,
2022–2025).
**Stamped held-out run:** `2026-09-25-nyiso-stgas-ldc-2021` (bundle `results/calibration/nyisostg_2021`).
**Superseded and pruned (rule 35):** `2026-09-24-nyiso-r-inputs-860vintage`.

## 1. Headline

- **ONE field armed:** `nyiso_ldc_generator_delivered_gas`.
  - Gas generators that EIA-860 records as Con Edison-served (≥ 50 MW, non-CT) pay Con Ed's filed
    PSC No. 9 SC 9 **Rate D(2)** power-generation transport on top of the Transco Z6 hub: 1.92 ¢/therm
    + 0.5 % losses.
  - Zero free parameters; offer curves are byte-identical to the keeper's.
  - 42 unit rows at 6 NYC plants move.
- **Determination NOT-YET → CALIBRATED** over the registered span. C3c (price tail) is the single
  ledgered caveat under rule 22 `[R-C3C]`.
- **C1-2023 ST_GAS: +4.99 → +3.17 TWh (+4.1 → +2.7 pp), FAIL → PASS.**
- **2021** (held out, stamped) reads **CALIBRATED on every criterion**, C3c included.
- **Promoted** under the pre-registered rule (PRECOMMIT §8):
  - every leg passes acceptance;
  - no protective criterion newly fails;
  - no criterion regresses to FAIL.

## 2. Legs (rule 36; provenance SHAs only, rule 33 (d))

| year | shard commit | S0–S2 | S5 footprint |
|---|---|---|---|
| 2021 | `e1e5815b3c975005c78efa31a398342b9a50bc6a` | OK | OK |
| 2022 | `50a175125ae02b4398e829da62c9e4b6625b8624` | OK | OK |
| 2023 | `a557f13d7c0d65067361b6f2e6b13fb8808268fa` | OK | OK |
| 2024 | `1bff2c3017fc41a4b2a647fe5a94359287666691` | OK | OK |
| 2025 | `56e086fd5109ac3527aa97061b9bd08d2a1a0191` | OK | OK |

- **Composition:** 2022–2025 composed at zero LP (`scripts/probes/nyisostg_compose_span.py`). The
  span's benchmark was re-adopted with `--rebuild-benchmark` (actuals only, no LP). Its hashes equal
  the outgoing keeper's exactly: campd `7ea5a0beeb85`, eia923 `41fa13cb9274`, eia930
  `12e2ee328d0a`.
- **2021:** restored byte-identical to the 2021 control (campd `e5af8125b647`).
- **Launch record:** the first launch's five shards sat PENDING for 17 min while later-created shards
  from other lanes ran. They were archived just as four of them had started, so about a minute of
  their work was lost. All five were relaunched on the same pin.

## 3. Per year, arm vs control (control = the keeper's committed bundle, rule 29 (b) form 4)

The 2021 control is R-NYISO-2021's committed sidecars (PR #6636, closed unmerged; branch head
`8671806`).

### 3.1 Rubric

| criterion | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| C1 ST_GAS | +0.57 → **−0.49** PASS | −0.86 → −1.08 PASS | **+4.99 → +3.17, FAIL → PASS** | +0.48 → −0.09 PASS | SKIPPED (prelim. 923) |
| C1 CC_REGULAR | +3.32 → +3.50 PASS | +1.43 → +1.49 | −0.64 → +0.39 | +2.90 → +3.02 | SKIPPED |
| C1 CC_CHP | −0.59 → −0.37 | −0.62 → −0.54 | +0.27 → +0.76 | +1.44 → +1.73 | SKIPPED |
| C3a mean LMP | −7.4 → **−6.4 %** | −9.4 → −9.1 % | −3.4 → **−1.9 %** | −0.9 → +0.2 % | −9.8 → −9.4 % |
| C3b NRMSE | 0.195 → 0.192 | 0.179 → 0.177 | 0.125 → 0.123 | 0.165 → 0.163 | 0.163 → 0.160 |
| C3c h > $300 (model / RT) | 0 / 3 PASS | 7 / 101 | 0 / 10 | 0 / 13 | 2 / 42 |
| C4 gas r | 0.924 → 0.923 | 0.865 → 0.865 | 0.940 → 0.942 | 0.904 → 0.904 | 0.854 → 0.855 |
| C8 ST_GAS forced | 19.2 → 22.4 % | 16.8 → 17.6 % | 12.2 → 15.2 % | 17.3 → 18.8 % | 14.9 → 15.6 % |
| C5a CO2 vs eGRID (reported) | +5.7 % | −3.0 % | +2.3 % | +1.1 % | +2.8 % |

C1 and C3a are shown in TWh and % respectively. The C3c 2022–2025 cells are CAVEATs, auto-ledgered.
C8 moves as pre-registered (the numerator is unchanged and the denominator shrinks), and PASSES in
every year.

### 3.2 ST_GAS by zone, model keeper → arm vs EIA-923 (TWh)

| year | NYC | Long Island | Capital/Hudson | Upstate West |
|---|---|---|---|---|
| 2021 | 6.75 → 5.67 vs 1.98 | 2.76 → 2.77 vs 5.75 | 0.33 → 0.34 vs 1.13 | 0.04 → 0.04 vs 0.45 |
| 2022 | 4.81 → 4.57 vs 2.27 | 2.49 → 2.49 vs 4.10 | 0.66 → 0.67 vs 1.96 | 0.06 → 0.06 vs 0.56 |
| 2023 | **10.71 → 8.85 vs 2.56** | 2.19 → 2.20 vs 3.98 | 0.30 → 0.31 vs 1.15 | 0.12 → 0.13 vs 0.63 |
| 2024 | 5.91 → 5.26 vs 2.77 | 3.41 → 3.45 vs 5.03 | 0.77 → 0.80 vs 1.54 | 0.40 → 0.42 vs 0.68 |
| 2025 | 5.66 → 5.32 vs 4.38 | 3.55 → 3.58 vs 5.33 | 1.28 → 1.30 vs 2.64 | 0.54 → 0.54 vs 0.68 |

**2023 by plant:**
- Ravenswood 6.10 → **5.03** (923: 0.79)
- Arthur Kill 2.60 → 2.05 (1.04)
- Astoria 2.01 → 1.78 (0.73)
- Northport, Barrett, Bowline and Roseton move by ≤ 0.01.

### 3.3 Prices

**Hourly price vs RT, ISO simple mean** (payload `lmpDeltaHr`; bias / MAE, $/MWh):

| year | keeper | arm |
|---|---|---|
| 2021 | −2.56 / 10.86 | −2.16 / 10.85 |
| 2022 | −5.83 / 22.10 | −5.56 / 22.13 |
| 2023 | −0.17 / 8.56 | +0.30 / 8.72 |
| 2024 | +0.50 / 10.04 | +0.90 / 10.16 |
| 2025 | −11.55 / 25.01 | −11.25 / 25.08 |

The zonal price level rises $0.3–0.7 in every zone, and the bias moves toward zero in 2021, 2022 and
2025. MAE is flat to +$0.16 (2023). This is **not** a promotion criterion (never on MAE, owner
guidance).

### 3.4 Structural integrity

- **D-4 FAIL set:** the membership is identical to the control's (2480 every year; 8906 2023 floor;
  bridge rows at 54574 / 8906 / 55405; 8006 2025; 2500 2021). Floored energy rises where the
  economics recede: 8906 in 2023 goes 0.054 → 0.105 TWh, and 2500 in 2021 goes 0.234 → 0.312 TWh.
- **Nothing outside the footprint moved:**
  - no offer-curve band;
  - no availability, heat-rate or pmax array (G-FOOTPRINT, PRECOMMIT §4);
  - no tuned value.
- The DOF ledger gains one **measured-market** entry with zero scalars (n_residual unchanged at 6).

## 4. What remains (routed, not absorbed)

1. **NYC steam is still +6.3 TWh over EIA-923 in 2023.** Part of it is floor energy: about 1.6 TWh of
   NYC persistent-base limb on Ravenswood at unit grain, against its measured 0.79. The rest is
   economic dispatch that the lower-bound leg only partly prices; the unpublished Con Ed VAC is
   omitted. The next lever is the NYC persistent-base limb's membership and coefficient (nyiso-226's
   screened re-basing, undecided) at unit grain.
2. **Long Island price level and spread.** LI is $4.7 below RT in 2023, and the LI−NYC spread is
   about 1.6 in the model vs 7.6 actual. LI / Hudson steam are under-dispatched in every year
   (LI −1.6 to −3.0 TWh).
3. **C3c** (price tail): the model-class limitation, ledgered.
4. **Scope limits of the new field:**
   - Central Hudson (Danskammer, Roseton), NYSEG (Greenidge), National Grid NY and Niagara Mohawk
     generator classes are not intaken.
   - The CT daily leg applies KEDNY SC-22 to every NYC CT, including Con Ed-served ones. KEDNY also
     publishes an SC 20 generator class (first statement 2026-01).
5. **`complete` marker:** NYISO's `complete` entry was withdrawn under Q5 because it stood on a
   NOT-YET keeper. The keeper is now CALIBRATED, so reinstating it is an **owner decision**; this lane
   has not taken it.

## 5. Records

- **Gate (a):** re-keyed; its status stays fail on the withdrawn marker.
- **Keeper shard:** `keepers/NYISO.json`, with lineage.
- **Status:** `status/NYISO.js` rebuilt (CALIBRATED).
- **Matrix:** the NYISO shard cell is K and the keeper is re-stamped; the §5.5 header is updated.
- **Checks:** `audit_keepers --iso NYISO` 0 failures; `check_promotion_completeness` OK.
- **Parity:** registry/payload parity is RED locally only on the four gitignored per-year legs, the
  documented filesystem-walk false red (rule 31, 2026-09-16 correction). They stay on disk (rule 31);
  CI sees only committed dirs.
- **On `main` with this PR (rule 33 (f)):**
  - the slim keeper bundle (meta, run_config, metrics, legitimacy diagnostics, attestation, 20
    `hourly/` sidecars);
  - the 2021 slim bundle;
  - both registry sidecars and run payloads;
  - the 2021 bench part.
- **Not on `main`:** the four per-year legs, with `dispatch/`, are gitignored and on the shard
  branches. A leg rebuild would be a re-solve, about 15 min per year in parallel shards.
