# NYISO 39 — priced-interchange restore (unified-engine migration complete)

## What this run is

The close of the keeper-34 → unified-engine migration. Identical to the
nyiso-38 probe (`nyiso_unified_downstate_v3`: keeper-34-exact offer curve,
`--gas-hub-basis-daily` + `--gas-hub-basis-overlay`, zonal gas basis,
local-self-supply, energy+reserve co-opt, unified continuous-ramp reliability
floor) **plus `--priced-interchange`** — the keeper-34 flag the migration
template had silently dropped.

## Root cause of the nyiso-38 "Capital_Hudson ST economic squeeze"

Three findings, in order of discovery:

1. **The dropped flag.** Keeper 34's `run_config.json` records
   `priced_interchange: true` (explicitly passed; NYISO resolves to False by
   default in both code eras — `resolve_priced_interchange` is unchanged).
   The nyiso-38 template omitted it, and BOTH `--nyiso-firm-imports` and
   `--nyiso-import-reconciliation` are hard-gated on it
   (`run_calibration.py` "if priced_interchange and …"), so nyiso-38 silently
   ran a different market: measured EIA-930 interchange netted into demand as
   a fixed hourly subtraction, no priced import node, no HQ firm floor, no
   monthly reconciliation band. The fixed import schedule displaced exactly
   the un-floored mid-merit supply (downstate steam). Restoring the flag
   recovers 2024 ST_GAS 8.89 → 9.41 TWh and fixes both 2023 C1 fails
   (CC_REGULAR +2.61 → +1.06, ST_GAS −1.30 → −0.86).

2. **The "keeper 34 CH ~1.2 TWh" premise was wrong.** Decoding keeper 34's
   committed run payload: its model 2024 Capital_Hudson ST was **0.157 TWh**
   (Bowline 0.10, Roseton 0.06, Danskammer 0.00), not ~1.2. The 1.2 figure is
   the measured CAMPD **actual** (2023 1.21, 2024 1.64 TWh — Bowline alone
   1.36 in 2024), which keeper 34 under-ran just as badly (r=0.30). This run's
   CH ST (0.21 TWh) is slightly *better* than the keeper's. The genuine CH
   under-run (Bowline/Roseton merit position vs the Iroquois-Z2 zonal gas
   basis) is a real, pre-existing open item shared by every NYISO run to date
   — it was never a migration regression. Per-plant residuals offset inside
   the C1 class band, exactly as ledgered in keeper 34's attestation.

3. **The "band" that made ±1.35 look like a fail is the quick-probe's, not
   the rubric's.** `_c1_fuelmix_quick.py` bands on 1% of total *generation*
   (±1.35 TWh, 2024); the authoritative rubric (`calibration_verdict.py`,
   rubric §1) bands on 1% of ISO *load* capped at 5 TWh → **±1.50 TWh**.
   2024 ST_GAS −1.40 TWh passes the actual gate.

## Migration fidelity checks (all verified against 180d579)

- `resolve_priced_interchange`: identical both eras; keeper passed the flag.
- Interchange unification (f04bad2d): NYISO import tranches, per-year ladders,
  export sink, firm-import floors (`HQ_hydro` 1.0 / `IESO_Ontario` 0.0),
  node links (Upstate_West 3000 / NYC 1000 / Long_Island 1200 MW),
  `IMPORT_EFORD` 0.0, recon band 0.02 — all byte-identical;
  `inject_nyiso_firm_imports` and `build_import_node_reconciliation`
  behaviorally unchanged (docstring-only edits).
- NYISO topology + Central-East TTC-by-year/month tables: identical.
- `nyiso_zonal_gas_hub.csv` (SOM Figure A-6 hub table): unchanged.
- Keeper 34's dirty diff (bundle `model_changes.diff`): when-available floor
  coefficients + Ravenswood outage routing — already migrated into the
  unified engine / `outages._FLEET_GROUP_OVERRIDE`.
- One post-keeper structural addition: `NYISO_simultaneous_import` 4,350 MW
  SIL (Gold Book / IRM-LCR, measured) — kept per rule #10.

## Result

C1 (HARD) PASS all scorable years — the 2024 ST_GAS miss that blocked
nyiso-36/37/38 clears at −1.40 TWh (band ±1.50), with 2024 CC_REGULAR −0.44,
2023 CC_REGULAR +1.06 and ST_GAS −0.86 also inside. C2, C4, C5a PASS. 2025
gas classes SKIPPED (preliminary EIA-923 vintage), governed by C2 which
passes.

Soft price criteria C3a/C3b/C3c fail with the same reserve-scarcity-frontier
mechanism keeper 34 ledgered (must-run floor adds inframarginal supply; no
ORDC shortage pricing): C3a −15.6/−19.2/−13.2%, C3b NRMSE 0.211/0.304/0.203,
C3c 0h vs 10/12/42h >$300. 2023 is deeper than keeper 34 (−15.6 vs −8.0):
the priced node (elastic imports) softens 2023 prices ~6 pp vs the
measured-schedule probe (−9.5%). Same documented frontier; not chased
(rules #1/#12).

## Remaining open item (not a blocker, ledgered)

Bowline/Roseton (Capital_Hudson, Iroquois Z2 basis) under-run vs CAMPD
actuals ~1.4 TWh/yr inside a passing class total — the model's CH steam runs
only on the hottest afternoons while the real units carried a summer-long
duty cycle in 2023–2025. Root-cause candidates for a future session: the
annual-mean Iroquois Z2 basis vs the summer basis collapse (CH gas is priced
$0.7–1.1/MMBtu over NYC/upstate year-round, but summer spot spreads
compress), and downstate reserve procurement. Any fix must be a measured
input (SOM monthly basis), never a floor or offer adder.
