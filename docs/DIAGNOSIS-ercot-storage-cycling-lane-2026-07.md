# ERCOT storage-cycling lane — the binding-regime supply-mix gap, storage first (2026-07-11)

**Session 2026-07-11, follow-on to ERCOT-58 (the joint-round NOT-YET record).
Keeper under test: `2026-07-10-ercot56-nucwin` (unchanged). All solves here are
rule-16 2023-only / measured-train-year throwaways — none registered, none
committed as bundles.**

**Verdict in one line: the ERCOT-58 diagnosis attributed the +2.4 GW
binding-regime thermal excess mostly to storage "under-discharge at evening
peaks." Grounding that against the *measured* EIA-930 battery series
(2024 partial / 2025 full) refines it materially — the model's batteries are
purely *price-elastic arbitrage*, so they track reality well in a high-scarcity
year (2025 evening peak captured within ~10 %) but collapse in a flat-price year
(2023: 0.55 TWh vs a fleet that can do ~5.8 TWh). What the model structurally
lacks is the *price-inelastic* net-load-ramp component of real battery
dispatch — the ECRS/RRS energy that ERCOT deploys at the morning and evening
ramps regardless of the (modelled-too-flat) energy spread. The $10 dispatch
adder is NOT the defect (the derived li-ion cycling-degradation cost is
$14.25/MWh, higher than the adder). The fix is measured-award energy
co-participation (AS deployment), not adder tuning.**

## 0. What was measured (the observation throwaways)

Reconstructed the promoted keeper's exact `solve_and_persist` config from its
`meta.json` (`scripts/probes/_obs_keeper_storage.py`, the `_ercot58_ab.py`
mapping with NO deltas) and solved single years, dumping the per-unit
`storage.parquet`. Battery-only (`tech==li_ion`, pumped storage excluded).
Measured target = EIA-930 ERCOT `battery_discharge`/`battery_charge`
(`data.eia_loader.load_ercot_battery_gen`): **2023 is not reported**, 2024 begins
mid-Nov (1,681 h), 2025 is the first full measured year.

Fleet (EIA-860, battery power): 2023 = 3,973 MW; 2025 = 13,709 MW.

## 1. The measured-year (2025) comparison — the clean validation

| metric (2025) | MODEL keeper | MEASURED (EIA-930) |
|---|---|---|
| annual discharge | 3.44 TWh | 5.46 TWh |
| annual charge | 4.05 TWh | 6.67 TWh |
| top-30 % net-load-hr discharge | 739 MW | 931 MW |
| HE18 / HE19 discharge | 2,711 / 3,184 MW | 3,004 / 2,635 MW |

Hour-of-day discharge (MW), model vs measured:

```
hod   05    06    07  |  16    17     18     19     20
MODEL  44   136   145 |  26   988  2,711  3,184  1,635
MEAS  633 1,003   787 | 496 1,832  3,004  2,635  1,286
```

**The model captures the evening ramp (HE17–20) well** — a high-scarcity year
gives the intraday spread that price-elastic arbitrage needs. What it misses:

1. **The morning net-load ramp (HE05–07): ~140 vs ~800 MW.** Real batteries
   discharge before solar ramps in; the model is still charging/idle.
2. **The daytime baseload (HE00–16): ~5–25 vs ~120–250 MW.** A persistent
   discharge floor the model never carries.
3. **~2 TWh of annual throughput** (3.44 vs 5.46), i.e. the model cycles the
   fleet ~0.7× as often as reality.

## 2. The flat-price-year (2023) collapse — where the binding gap lives

| metric (2023) | MODEL keeper | MODEL adder=0 probe |
|---|---|---|
| annual discharge | 0.55 TWh | 1.24 TWh |
| top-30 % net-load-hr discharge | 145 MW | 210 MW |
| HE18 discharge | 397 MW | 864 MW |

The 2023 fleet (3,973 MW / ~16 GWh) *can* deliver ~5.8 TWh at one cycle/day; the
keeper delivers 0.55 TWh (~0.1 cycle/day). This is the ERCOT-58 §4 observation
(145 MW at binding hours) reproduced. 2023 has no measured battery series, but
the cross-year pattern is unambiguous: **the model's storage tracks reality in
the high-scarcity year and collapses in the flat year, because its cycling is
100 % price-elastic** while reality's is not. The AS-committed cap reservation
is a *second-order* suppressor here — at 2023 top-30 % hours the measured award
reserves ~1,535 MW of the 3,973 MW fleet, leaving ~2,438 MW free, yet the model
discharges only 145 MW. The binding constraint is the *incentive*, not the cap.

## 3. The $10 adder is not the defect (rule 14 checked, and it clears)

`battery_dispatch_adder = 10.0 $/MWh` (the keeper's dispatch discharge cost;
`storage_degradation` feeds only the entry screen, so dispatch sees the adder
alone). Removing it (§2, adder=0) roughly doubles throughput and *improves the
shape* (evening HE17–19 concentration sharpens) but still reaches only ~1/3 of
the implied evening level — so the adder is a real suppressor but not the root
cause.

Rule-14 test — is the $10 a fitted estimate masking a miscalibration? **No, in
the direction that matters:** the *derived* per-tech cycling-degradation cost
(`storage._degradation_cost_per_mwh`, capex/kWh ÷ rated cycles ×
replacement-fraction) is **$14.25/MWh for li-ion 4 h — higher than the $10
adder**. The accurate physical cycling cost is above the adder, so lowering the
adder toward "true cost" is unjustified and would only paper over the real gap.
The reason real batteries cycle ~1×/day at a ~$14/MWh degradation cost is that
they earn AS revenue and are *deployed* — value the energy-only arbitrage LP
does not see. **Do not touch the adder** (it is roughly correct); add the
missing structure.

## 4. The structural root cause: missing price-inelastic AS-energy participation

Real ERCOT battery dispatch = arbitrage **+** ancillary-service energy
(~85 % of 2023 battery revenue was AS). The model represents AS as a pure
*power reservation* — `reserve_storage_as_power` subtracts the measured hourly
storage up-AS MW from the discharge cap in **all 8,760 h**, and that capacity is
*never deployed back as energy*. So the model's batteries only ever cycle on
pure energy arbitrage, which the flat modelled spread (itself depressed by the
+2.4 GW binding-regime thermal excess — the coupling ERCOT-58 §4 flagged) does
not support in 2023, and only partly supports in 2025.

The physical signature of the missing energy is in the **measured PRC (Physical
Responsive Capability)** series (`ercot_<year>_ordc_reserves_hourly.parquet`):
PRC dips at exactly the ramps the model misses —

```
PRC mean MW by hod:  2023  HE06 6,909  HE18 5,898 (min)  HE19 6,004
                     2025  HE06 9,914  HE18 9,069 (min)  HE19 8,563
```

— i.e. ERCOT draws down responsive capability (deploys ECRS/RRS as energy) at
the morning and evening net-load ramps. That is the ~800 MW morning discharge
and the daytime/evening baseload the model omits. It is **price-inelastic**: it
happens on the ramp whether or not the ORDC scarcity adder fires (2023 rtorpa is
>$0.5 in only 364 h, mean $0.95; 2025 in 21 h) — so no amount of arbitrage
retuning reproduces it, and the mechanism cannot be an economic offer. This is
also why the coupling is *circular* and self-reinforcing: no battery energy at
the ramp → thermal serves it (+2.4 GW) → evening not scarce → spread stays flat
→ no battery arbitrage. An exogenous, price-inelastic battery injection at the
ramp is the only thing that breaks it.

## 5. The mechanism to build next: measured-award energy co-participation (AS deployment)

Default-off, ERCOT, forward-valid — the "measured-award energy co-participation"
lane the ERCOT-58 forward path named. Specification:

* **Deployable award (rule-13 measured input):** the measured hourly storage
  up-AS MW (`scarcity.ercot_storage_as_reserve_mw`, the 60-Day DAM
  per-resource-type `storage` column) — the capacity the fleet actually held for
  responsive products and that ERCOT can call as energy.
* **Deployment weight w(t) ∈ [0,1] — the net-load-ramp draw-down, the open
  design point.** It must (a) concentrate on the morning + evening ramps (track
  the PRC draw-down), (b) be forward-derivable and respond to conditions, and
  (c) carry NO residual-fitted threshold (rule 1/23). The G4 mode-aware seam is
  the template: measured PRC draw-down `(PRC_ref − PRC(t))/PRC_ref` in backcast
  (a measured physical fraction, not the price residual), the WS-A forward
  net-load-ramp formula in forecast. Candidate closed forms to test on the 2023
  probe: (i) PRC-relative draw-down against the day's/window's own PRC envelope;
  (ii) the ORDC LOLP `Φ((μ−R(t))/σ)` on a *reserve-level* R (needs a pre-solve
  reserve proxy — circular, weaker); (iii) net-load ramp-rate normalised by the
  fleet. (i) is the most direct measured analogue and the recommended first
  probe.
* **LP wiring:** `deploy(t) = award(t) × w(t)`, allocated to battery units
  pro-rata by power (the `reserve_storage_as_power` pattern), enters as a
  storage **discharge lower bound** (`build_variable_bounds` gains a
  `storage_discharge_min`, mirroring the existing `storage_soc_min`) AND is
  **added back to the discharge power cap** for those hours so the released award
  is feasible (`Dis` upper bound ≥ deploy). SOC feasibility: deployment is
  concentrated in a few ramp hours ≤ 4 h energy, so the daily-cycle LP charges
  ahead of it; guard by clipping `deploy` at a share of energy_cap.
* **Rule-12 floor discipline:** driver = the measured net-load-ramp PRC
  draw-down; window = the morning/evening ramp hours it is nonzero; forward story
  = award × forward ramp formula. Storage is <2 % of ISO annual energy, so the
  C8 forcing budget does not gate it — but keep the forcing grounded and
  shape-faithful (D-1) regardless.
* **Rule 19 (one mechanism per phenomenon):** the deployment RELEASES what
  `storage_as_commitment` reserved; the two must reconcile (reserve in
  non-ramp hours, deploy at the ramp), not stack. Mutually exclusive with the
  endogenous co-opt path (`ercot_storage_as_endogenous`), which prices the split
  itself.

## 6. Disposition

* **Keeper stays `2026-07-10-ercot56-nucwin`.** No code changed; no bundle
  registered (all solves rule-16 throwaways — a 2023-only or single-measured-year
  solve is never a keeper, rule 16).
* The ERCOT-58 forward path is **sharpened, not overturned**: storage first, but
  the target is the price-inelastic morning/daytime/evening-ramp AS-deployment
  energy (measured-anchored on the 2024/2025 EIA-930 battery series), not
  evening arbitrage — the evening peak is already ~captured in a scarcity year.
  The +2.4 GW binding-regime thermal excess and the flat 2023 spread are the
  same coupled defect; the price-inelastic injection breaks the circle.
* **Do not touch** the $10 adder (§3) or the ORDC tariff params (rule 26).
* When the deployment mechanism lands and clears its 2023 probe + measured-year
  (2024/2025) shape gate, re-probe the ERCOT-58 v3 realized-room RTORPA — its
  realized room is bounded by exactly this supply-mix gap.
