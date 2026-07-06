# nyiso53 v2off twin — Zone-K LCR/TSL cap, v2 plant-rates OFF (attribution twin)

**Run id:** `2026-07-06-nyiso53-v2off-twin` · **PROBE** (never a keeper
candidate — it exists to isolate the `use_plant_emission_rates_v2`
contribution from its `2026-07-06-nyiso-53-li-tsl` parent, the §9.6
ablation−resolve technique). Years 2023/2024/2025, nyiso-41 keeper meta
replayed at HEAD (= nyiso-52 recipe: PR-#1442 re-derived floors +
`nyiso_downstate_ct_gas_basis=True`) **+ `nyiso_li_lcr_tsl=True`** (issue
#1345), `use_plant_emission_rates_v2=False`.

## What the TSL mechanism did (vs `2026-07-05-nyiso-52-floor-rederive`, same scoring basis)

* **The `nyiso_local_selfsupply` D-2 mechanism row is GONE** — Long Island
  reliability energy now clears economically behind the published Zone-K
  locality import limit (325/275/275 MW, HB14-21 window) instead of a forced
  0.45 × load `min_gen` floor. The residual-identified 0.45 scalar (DOF
  ledger S5) is out of the active config.
* **Price body improves in all years**: C3a −11.4/−12.7/−11.0% (52:
  −13.5/−14.7/−12.5%); C3b NRMSE 0.199/0.234/0.190 (52: 0.213/0.247/0.203).
  In-window downstate prices now come off in-zone marginal units behind a
  published limit — real structure, not an offer re-tune.
* **CT_PEAKER class energy falls to 1.60/1.75/2.48 TWh** (actual
  2.26/2.13/2.84; 52 carried 2.19/2.54/2.96 with floor-carried energy): with
  no LI energy floor, nothing commits the downstate peakers the real market
  runs — the C8 share of the (smaller, honest) class rises to 93.0/89.1/58.5%
  even though the forcing is now entirely the legitimate windowed temperature
  ramps. This is the naked issue-#1344 signature (reserve/scarcity price
  formation absent), not a new forcing channel: total floor-forced CT energy
  (1.49/1.56/1.45 TWh) is DOWN vs the C8-fail baseline nyiso-48
  (selfsupply alone forced 1.84/2.87/1.86 TWh).
* C7 (D-1 diurnal) PASS all years — the #1442 fix holds under the new
  mechanism. C1 2024 ST_GAS −3.25 TWh remains the standing HARD FAIL
  (delivered-fuel ask, G-13). C3c 0/0/7 h unchanged (blocked on #1344).

## Boundary reconciliation (rule 14, empirical)

Measured LI implied inflow (CEMS hourly gross gen + measured zonal load) at
the top-100 load hours: **1,493/1,440/1,598 MW** (2023/24/25) vs the
mechanism's in-window import capability (TSL + 1,200 MW external ties) of
**1,525/1,475/1,475 MW** — the published construction matches the measured
peak-hour boundary within ~5%. Window-mean inflow (~1,100–1,200 MW) sits well
below the cap, so it binds only in genuinely tight hours.

**Determination: NOT-YET** (C6 unattested probe; C1-2024 ST_GAS; C8 —
ledgered on #1344/G-13). See `docs/calibration-log.md` 2026-07-06 NYISO entry.
