# nyiso 53 li-tsl — Zone-K LCR/TSL mechanism + v2 measured plant CO2 rates

**Run id:** `2026-07-06-nyiso-53-li-tsl` · **PROBE** (recommended keeper
candidate pending owner sign-off — see the 2026-07-06 calibration-log entry).
Years 2023/2024/2025, nyiso-41 keeper meta replayed at HEAD (= the nyiso-52
recipe: PR-#1442 re-derived floors + `nyiso_downstate_ct_gas_basis=True`)
plus the two lane-L-11 changes:

* **`nyiso_li_lcr_tsl=True`** (issue #1345): the published Zone-K locality
  import limit (325/275/275 MW) caps the NYC→Long_Island link in the HB14-21
  design-condition window, REPLACING the residual-identified Long_Island 0.45
  self-supply energy floor (DOF ledger S5). The `nyiso_local_selfsupply` D-2
  forcing row is gone; LI reliability energy clears economically. Boundary
  empirically reconciled (rule 14): measured top-100-load-hour LI implied
  inflow 1,493/1,440/1,598 MW (CEMS + zonal load) vs in-window capability
  1,525/1,475/1,475 MW.
* **`use_plant_emission_rates_v2=True`** (G-39 §9.6 ride-along): NYISO's
  first measured plant-specific CO2 rates in backcast, dispatch-affecting
  under the RGGI state carbon price. NOTE: the flag was silently unreachable
  from the CAMPD-bins backcast path until this session wired it in
  (`fleet.bins_to_fleet`) — the pre-wiring twin pair solved byte-identical,
  proving the gap (G-29 class).

## Scorecard (vs the v2off attribution twin and nyiso-52, same scoring basis)

| criterion | nyiso-52 | v2off twin (52+TSL) | **nyiso-53 (52+TSL+v2)** |
|---|---|---|---|
| C1 fuel-mix | FAIL (2024 ST_GAS −3.30) | FAIL (−3.25) | **PASS** |
| C3a mean LMP | −13.5/−14.7/−12.5% | −11.4/−12.7/−11.0% | **−9.0/−10.9/−10.6%** |
| C3b NRMSE | 0.213/0.247/0.203 | 0.199/0.234/0.190 | **0.182/0.221/0.190** |
| C3c >$300 h | 0/0/7 (of 10/12/42) | same | same (blocked on #1344) |
| C5a CO2 2024 | — | −8.3% | −8.2% |
| C7 diurnal | PASS | PASS | PASS |
| C8 CT forced | 54.5/45.8/39.3% (1.16–1.19 TWh) | 93.0/89.1/58.5% (1.45–1.56 TWh) | 92.7/86.7/56.6% |
| C8 ST_GAS | 34.9% (2024 FAIL) | 33.0% (2024 FAIL) | **<30% (clears)** |

**v2 flip attribution (nyiso-53 − v2off twin, identical config otherwise):**
C1-2024 ST_GAS FAIL→PASS; C3a +2.4/+1.8/+0.4 pp; C3b −0.017/−0.013/0.000;
system mean price +$0.61/MWh; C5a 2024 +0.1 pp. Measured plant rates
re-split the gas merit order under RGGI — a measured input replacing an
estimate (rule 10), not a tuned parameter.

**C8 reading (rule-20 mandate: down, not re-hidden):** total floor-forced CT
energy 1.49/1.56/1.45 TWh is DOWN vs the C8-fail baseline nyiso-48 (whose
selfsupply floor alone forced 1.84/2.87/1.86 TWh), and the selfsupply forcing
channel is eliminated outright. The share-of-class RISES because the class's
economic energy collapses without reserve-scarcity price formation — the
peakers the real market commits for reserve sit idle in the pure-ED LP
(issue #1344, the downstate-reserve handoff's confirmed root cause). Nothing
new forces; the remaining forcing is entirely the PR-#1442 windowed
temperature ramps.

**Determination: NOT-YET** (C6 unattested probe; C8 + C3c ledgered on #1344;
C3a/C3b soft, best-to-date; G-13 delivered-fuel ask still open for the CT
offer level). Keeper stays `2026-07-03-nyiso-41-hub-prices` pending owner
adjudication.
