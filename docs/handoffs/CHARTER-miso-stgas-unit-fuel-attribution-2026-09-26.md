# CHARTER — MISO ST_GAS unit-level fuel attribution re-derive (owner ruling 2026-09-26)

```
DATA PROFILE: miso
MODEL: Opus or Fable (rule 27 — edits derive scripts and possibly src/ loaders)
OWNER RULING: miso-277, "Charter re-derive (Recommended)"
```

**Object.** The frozen thermal-tranche artifact and the sync estimator attribute CAMPD stacks by **facility**, so at
mixed coal/gas facilities gas-steam units are filed as COAL (Brame 6190 unit 1; Big Cajun 2 6055 unit 2B2) or not at
all (Baxter Wilson 2050 unit 1; Teche 1400 unit 3 under CT_PEAKER), and coal units count as ST_GAS sync (Dan E Karn
1702 units 1–2; Burlington 1104 through 2021; R D Green 6639). Measured: 4.81 / 3.92 / 1.73 / 1.74 / 2.85 TWh of
gas-steam generation filed outside ST_GAS (2019–23); 5.38 TWh (2019) of coal inside ST_GAS-filed facilities.
Evidence: `docs/FINDING-miso277-phase0-congestion-crosswalk-stormprint-2026-09-26.md` §2,
`results/calibration/_miso277_crosswalk_footprint.json`.

**Rule 23 trigger.** The attribution defect (nyiso-175 "crosswalk repair" precedent), never the C1 residual. CAMPD's
own per-unit `primaryFuelInfo` gives the same totals as the EPA crosswalk; the crosswalk
(`data/raw/reference/camd-eia-crosswalk/`, v0.3, EIA-860 2018 basis) supplies generator nameplate for the sync
denominator.

**Scope.**
1. Extend the deriver's `--per-unit-attribution` path with a per-unit fuel split (gas units → ST_GAS, coal units →
   COAL), for MISO only (rule 25); regenerate the artifact; commit citing the data change.
2. A cited manual remap of Riverside 55641 CT-03/CT-04 → EIA 64020 (not in the crosswalk; built 2020), mirroring
   `CAMPD_UNIT_PLANT_REMAP` — the unblock for candidate 1 (CC outage numerator basis).
3. Zero-LP footprint first (fleet_only rebuild): ST_GAS pmax / floor membership / floor TWh per year, and which
   floors appear or disappear.
4. Then PRECOMMIT + one shard per year 2019–2025 (rules 34, 36) against the then-current keeper.

**Stated risk.** Re-filing moves the population into ST_GAS; whether the model then dispatches it is unmeasured. The
FINDING-miso276 §2 floored plants were short for economic reasons, and these South units are committed in reality for
local reliability (MISO VLR), which the model does not represent (`scuc_load_pocket_commitment` = `·`).
