# FINDING — closeout-PJM-2: what moved PJM 2025 C3a/C3b from PASS to FAIL (zero LP)

**Keeper unchanged:** `2026-10-02-w0-pjm-fix2` (bundle `w0_pjm_span`). **Zero LP, zero shards, no matrix cell moves, no ScenarioConfig change.**
Charter: owner ruling R-30 (`docs/backcast-closeout-plan-2026-10.md` §5.0), task (a).
Probe: `scripts/probes/_closeoutpjm2_2025_attribution.py` → `results/phase0/pjm/_closeoutpjm2_2025_attribution.json`.

**The move.** Incumbent `pjmnext16_A_span` (keeper 2026-09-30-pjm-next16-ovec) → W0 keeper `w0_pjm_span`:

| | 2025 C3a (load-weighted mean vs RT $49.83) | 2025 C3b (monthly NRMSE) |
|---|---|---|
| incumbent | $45.04, −9.6 % PASS | 0.182 PASS |
| W0 keeper | $44.04, −11.6 % FAIL | 0.222 FAIL |

The move is −$0.99/MWh (−2.0 pp). The ±10 % band edge sits $4.98 below the actual, so the incumbent was $0.04 inside it.

## §1 Readings

These are the charter's own readings, adopted unchanged. **They were not pushed before the computation.** The lane
read the hourly price delta first, and that diagnosis is what located the scarcity hours. No threshold below was
chosen by this lane.

- **R-a (bucket).** Name the bucket that carries ≥ 50 % of the move that takes C3a across the band.
- **R-b (classification).**
  - If that bucket is (i), the 2025 EIA-923 data drift, the miss is a **data-drift artefact**: it is labelled, and it
    is not a lever target.
  - If that bucket is (ii), the W0 fleet, the miss is a **W0 structural effect**: name the field and route it.
- **(iv) solver stack.** Documented only; there is no re-solve.

**Inputs.** All committed, all zero LP:
- **Hourly sidecars.** `system_2025`, `class_hourly_2025` and `unit_marginal_2025` for both bundles. The incumbent's
  sidecars are read from git at `d215d7a1^`, because they were pruned at the W0 promotion.
- **Bench.** `frontend/data/backcast/bench/PJM/2025.json.gz`.
- **Toggles.** Twenty-three fleet_only rebuilds of the incumbent's 2025 recipe through `build_fleet_census.rebuild_fleet`:
  - recorded;
  - w0;
  - each W0 field turned on alone;
  - each W0 field left out (leave-one-out);
  - w0 with the renewables lookup patched back to its pre-#7040 eGRID-only form.
- `dispatch/2025_P1.parquet` and `unit_hourly_2025` are not on main (gitignored), so the per-unit layer is `unit_marginal`.

## §2 Result

### 2.1 The whole move sits in 24 EMAAC VOLL hours

The incumbent's 2025 leg has energy-balance slack in **EMAAC only**, in 24 hours, priced at $2,000/MWh:
- **June heat wave:** Jun 23–25, 15:00–19:00.
- **July:** Jul 8, Jul 17, and Jul 29–30.

The W0 leg has slack in 5 of those hours. Splitting the system load-weighted move:

| hours | move ($/MWh, annual load-weighted) |
|---|---|
| the 24 slack hours | **−1.205** |
| the other 8,736 hours | +0.212 |
| total | −0.993 |

The swap test reproduces this:

| counterfactual | C3a | C3b |
|---|---|---|
| incumbent, with only the 24 hours swapped to W0 | −12.0 % FAIL | 0.216 FAIL |
| W0, with only the 24 hours restored to the incumbent | −9.2 % PASS | 0.187 PASS |

**The gate crossing is these 24 hours, on both criteria.**

### 2.2 What removed the shortfall (per hour, EMAAC in-zone supply, mean over the 24 hours)

| bucket | Δ supply into the EMAAC balance | Shapley share of the −1.205 |
|---|---|---|
| (ii) W0 fleet: in-zone available MW, w0 − recorded rebuild | **+901 MW** | **−1.173 (97 %)** |
| (i) must-run drift: EMAAC's 16.2 % demand share of the +607 MW system biomass/OTHER injection | +103 MW | −0.071 (6 %) |
| (iii) renewables fix #7040: EMAAC solar, w0 − pre-fix lookup | −209 MW | +0.031 |
| net-import residual | −19 MW | +0.010 |

- The counterfactual with all four buckets gives −1.203, against −1.205 solved, with no solver term.
- The +901 MW rebuild delta matches the solved bundles' `cap_mw` delta, +901.4 MW.
- **Drift alone clears 2 of the 24 hours**, the ones with a shortfall under ~100 MW. **The W0 fleet alone clears 20.**

**W0 fields in the EMAAC +901 MW** (mean over the 24 hours):

| field | alone | leave-one-out |
|---|---|---|
| `seasonal_capacity_basis` (E.1) | +595 | +567 |
| `admit_standby_units` | +416 | +399 |
| `commission_year_cod_fallback` | −68 | −91 |
| `unit_outage_dispatched_bin_denominator` | +20 | −3 |
| every other field | 0 | 0 |

`seasonal_capacity_basis` adds its MW as summer-rated CC_REGULAR +298 and CT_PEAKER +270.

**`admit_standby_units` in EMAAC.** These units are status SB in EIA-860 vintage_2025, and each generated in 2025
(EIA-923):

| plant | capacity | 2025 generation |
|---|---|---|
| NAEA Lakewood (54640), CC | 265 MW | 239 GWh |
| Salem GT3 (2410) | 38 MW | — |
| Christiana CH11/CH14 (591) | 2 × 25 MW | 767 MWh |
| Delaware City 10 (592) | 18 MW | — |
| Edge Moor 10 (593) | 12 MW | — |
| West Station (597) | 15 MW | 322 MWh |

**This is real capacity that ran.** The oil GTs, mc $260–540, are what set W0's EMAAC price in those hours: $250–410
instead of $2,000.

### 2.3 Outside the 24 hours (+0.212, greedy same-setter re-clear on `unit_marginal`)

| component | effect ($/MWh) |
|---|---|
| (i) must-run drift, +5.32 TWh, +607 MW mean | **−0.87 to −1.30** (adding it to the incumbent stack / removing it from the W0 stack) |
| (ii) W0 fleet in-merit capacity change, −746 MW mean (units at or below the setter) | +0.52 |
| unseparated: the renewables fix's zonal re-allocation (+7.0 GW of 2025 solar admitted, mostly AEP-Ohio/Dominion, EMAAC's share 11.1 % → 7.8 %); the solver stack; greedy error | +0.56 to +0.99 |

The W0 in-merit change is mainly `commission_year_cod_fallback`, which on its own changes available energy by
COAL_BIT −3.5, CT_PEAKER −5.1 and ST_GAS −1.8 TWh.

**The drift is large here, but it is offset.** Without the 24 hours, W0 would read −9.2 %: still a PASS, though a
weaker one. This is the **latent** effect of the drift: it lowers prices by about $1 and offsets roughly what W0's
in-merit cut and the unseparated term add. It does not cross the gate.

### 2.4 The incumbent's PASS was the right level for the wrong reason

The real system RT price in the 24 hours averaged **$470/MWh**, peaking at $1,830 on Jun 24 17:00. The models:
- **incumbent:** $456 (EMAAC at $2,000);
- **W0:** $176.

Annual load-weighted contribution: real $2.07, incumbent $1.98, W0 $0.78.

- **How the incumbent got there.** A single-zone VOLL from a ~530 MW EMAAC shortfall. That shortfall existed only
  because the incumbent fleet lacked about 900 MW of real EMAAC capacity: summer ratings and the standby units that
  ran.
- **What happened in reality.** The real event was system-wide. Real EMAAC was $549 against $470 for the system:
  heat-wave reserve scarcity, not an EMAAC energy shortfall.
- **The W0 model's reserve dual** is positive in **0 hours of 2025** (the incumbent: 6).

### 2.5 (iv) Solver stack (documentation only)

- **The two legs ran different solver versions.** The incumbent 2025 leg recorded highspy 1.15.1, pandas 3.0.6 and
  pyarrow 25.0.1. The W0 leg (solved at ce8820dd) recorded the locked 1.14.0, 3.0.3 and 24.0.0.
- **Why the solver cannot explain the 24 hours.** Slack there is a primal capacity shortfall, and §2.2 closes it from
  fleet and data inputs alone, to $0.002.
- **Where the solver could still matter.** It could reach the outside-hour duals inside the unseparated +0.56 to
  +0.99. Separating that needs a re-solve, which this lane does not do (charter).

## §3 Readings applied

| reading | result |
|---|---|
| **R-a** | **(ii) the W0 fleet: 97 % of the crossing** (−1.173 of −1.205). Fields: `seasonal_capacity_basis` (~59 % of the in-zone MW) and `admit_standby_units` (~41 %). |
| **R-b** | **A W0 structural effect, not a data-drift artefact.** The drift is 6 % of the crossing. Its −$0.9 to −1.3 outside the scarcity hours is latent and offset. |
| (iii) | Opposes the move in the scarcity hours (+0.03). It is unseparated outside them. |
| (iv) | Not a factor in the crossing. Documented. |

**Routing.**
- **Both fields stay.** They add capacity that EIA-860/923 show was real and ran in 2025 (rules 1 and 14). Reverting
  either to recover the incumbent's $2,000 hours would be reaching a number through a mechanism that is not real.
- **The open object is the missing system-wide reserve-scarcity price formation in the June–July 2025 heat-wave
  peaks.** The keeper's in-LP co-optimisation (`energy_reserve_coopt` K, PJM's published two-step ORDC) never binds
  in 2025. The likely question is real heat-wave availability (ambient derates and forced outages at extreme heat)
  against nominal summer ratings, but that is not measured here.
- **Before any lever** this needs a zero-LP census:
  - published PJM forced outages and derates, Jun 23–25 2025;
  - against the model's unavailable MW;
  - against the reserve requirement.
- **The adder route is closed.** `ordc_scarcity_overlay` is G (no adder, rule 19). 2025 C3a/C3b stay FAIL until the
  census is done. They are not ledgerable (rubric v3.1: only C3c).

## §4 Limits

- **The greedy re-clear is system-level.** It has no zonal transmission, storage or seam-ladder response, so the
  outside-hour figures are brackets, not identities.
- **Zonal must-run uses the injector's own rule.** `_must_run_profiles` allocates by annual demand share, so EMAAC's
  16.2 % is exact for the model, not for the real plants.
- **The renewables term is approximate.** It patches only `_renewable_zone_lookup` (the #7040 diff). Its outside-hour
  price effect is not computed.
- **The fleet rebuilds run at HEAD, not at the incumbent's 6d4c7749.** The recorded rebuild reproduces the
  incumbent's solved EMAAC `cap_mw` delta structure, and the w0 rebuild reproduces W0's: Δ +900.8 rebuilt vs +901.4
  solved.
- **2025 price actuals are unchanged** between the two scorings ($49.83, identical monthly vector). Only the bench's
  energy keys (`plants`, `e930`, `classFull`, `ctOnly`, `co2`) moved with the full-year EIA-923.
