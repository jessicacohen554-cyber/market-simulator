# FINDING — nyiso-168: the 0.70 gain is a SLOPE deficit in the ordinary 50th–90th load band, the market's steepness there is NOT physical, and the one new mechanism it points at is PROVABLY LP-INERT

**Date:** 2026-09-01 · **Lane:** NYISO calibration · **Shorthand:** nyiso-168
**Object:** the named successor nyiso-167 installed — the **price-response gain**
(model = 0.7032 × actual_RT + $11.03, R² 0.910), the single load-bearing thing
between NYISO and CALIBRATED via **C3a mean LMP 2025, −11.5 %**, on keeper
`2026-08-30-nyiso-159-loss-surface`.
**ZERO SOLVE.** Committed artifacts only, plus one clean-tree fleet read. No LP
ran. No `ScenarioConfig` field, mechanism, keeper, shard, marker or
determination changed. **Rule 22 `[R-HOLDOUT]`: every year read is 2023, 2024
or 2025** — no out-of-training year was solved, scored, registered or read; no
marker was requested; the spend freeze is untouched.
**Probes of record:** `scripts/probes/nyiso168_gap_anatomy.py` →
`results/calibration/_nyiso168_gap_anatomy.json`;
`scripts/probes/nyiso168_reserve_supply_slack.py` →
`results/calibration/_nyiso168_reserve_supply_slack.json`.
**nyiso-167's probe re-run first and reproduces bit-identically** (no diff on
`_nyiso167_price_gain_attribution.json`), so this session measures the same object.

---

## 0. The result in one paragraph

The gain deficit is **not** a tail phenomenon and **not** a level phenomenon: on
the DA basis, **73 % of 2025's −$4.91/MWh sits in the 50th–90th load-percentile
band** — ordinary daytime hours at 18.1–20.4 GW — while the **bottom half is
OVER-priced by +$1.75** and the top 1 % contributes only −$0.06. Five candidate
causes are killed on measurement, not argument: commitment floors cannot raise
the bottom (they add supply, moving the marginal unit *down* the stack); storage
arbitrage buys at most ~$1.4 of it; the peak-hour supply mix matches EIA-930 to
within 3 %; the reserve co-optimisation contributes $0.00 below the 90th
percentile; and — the decisive one — **NYISO's own CAMPD fleet shows the
market's physical incremental heat rate rising only 7.06 → 8.64 (+22 %) from low
to high output while its price-implied heat rate rises 13.3 → 29.0 (+118 %)**.
The market's supply-curve steepness is therefore **markup and congestion, not
physics**, which closes the heat-rate-dispersion family. The one new mechanism
the object points at — a per-generator ramp bound on reserve supply, the gap
that makes NYISO the only ISO of the three with the machinery to set
`supply_cap` and no `supply_cap` set — is **PROVABLY LP-INERT ex ante**: NYISO's
fast-start thermal capacity alone is **10.0× the spinning requirement** before
availability, dispatch or hydro are counted. **No solve was spent on it.**

---

## 1. What was measured, and off what

| input | path | role |
|---|---|---|
| keeper hourlies | `results/calibration/nyiso159_lossarm_B/hourly/{system,class_hourly,storage,reserve_family}_<year>.parquet` | the keeper's own P1 zonal price/demand, class dispatch, storage and reserve-family duals (rule 15's stated purpose: read the keeper, do not replay it) |
| hourly actual | `data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet` | DA/RT hub series on the model's own standard-time calendar |
| zonal actual | `data/raw/_validation-source/actual_lmp.json` → `NYISO.<year>.zones` | per-model-zone annual DA/RT |
| gas driver | `data/raw/gas-prices/transco_z6_ny_daily.csv` | measured Transco Z6 NY daily spot, **regressor only** |
| measured fuel mix | `data/raw/eia-930-hourly/NYIS hourly.parquet` | hourly NYIS demand + generation by fuel |
| **measured fleet burn** | `data/raw/campd-unit-level/NY_<year>.parquet` | hourly per-unit `grossLoad` + `heatInput` → the fleet's own incremental heat rate |
| **measured AS prices** | `data/clean/ancillary-services/NYISO/{DAM,RTM}` | NYISO's own posted zonal ancillary clearing prices |
| fleet capacity | `data/clean/fleet/fleet_<year>.parquet` | NYISO capacity by model fuel type, for the ramp-ceiling arithmetic |

Everything is stated on the **DA basis** — the like-for-like comparable for a
perfect-foresight LP, per nyiso-167 §2.1. RT adds the scarcity tail the model
has no mechanism to form, which is the ledgered C3c and is not this object.

## 2. Where the deficit lives — it is the ordinary band, not the tail

Load-sorted bands, model load-weighted system price vs actual DA, with each
band's contribution to the annual mean gap (`_nyiso168_gap_anatomy.json` §A):

| load pct | n | 2023 gap / contrib | 2024 gap / contrib | **2025 gap / contrib** |
|---|---|---|---|---|
| 0–50 | 4,380 | **+2.31** / +1.15 | **+2.70** / +1.35 | **+1.75** / **+0.87** |
| 50–80 | 2,628 | +0.71 / +0.21 | −1.09 / −0.33 | −6.20 / **−1.86** |
| 80–90 | 876 | −4.02 / −0.40 | −5.96 / −0.60 | −17.11 / **−1.71** |
| 90–95 | 438 | −2.36 / −0.12 | −6.05 / −0.30 | −18.51 / −0.93 |
| 95–99 | 350 | −2.54 / −0.10 | −5.26 / −0.21 | −16.22 / −0.65 |
| 99–99.9 | 79 | −18.67 / −0.17 | −34.60 / −0.31 | −64.32 / −0.58 |
| 99.9–100 | 9 | +33.74 / +0.03 | −46.65 / −0.05 | −54.50 / −0.06 |
| **annual** | 8,760 | **+0.61** | **−0.45** | **−4.91** |

Three readings:

1. **The 50–90 band carries 73 % of 2025's deficit** (−$3.57 of −$4.91) on
   3,504 hours of ordinary daytime load. The top 1 % carries **1.2 %**. Whatever
   the object is, it is not scarcity and it is not the tail — which is the
   independent confirmation that C3c is a separate, correctly-ledgered
   limitation and that **opening a C3c lever would not have touched this**.
2. **The bottom half is OVER-priced in all three years, stably** (+$2.31 /
   +$2.70 / +$1.75) while gas doubles. A stable additive over-price under a
   doubling fuel price is a **fuel-invariant** component, not a fuel-cost one.
3. **The magnitude scales with the year's price level and the sign flips at the
   crossover** — the gain law's own prediction, reproduced here at hourly
   resolution rather than monthly.

## 3. Four candidate causes killed by measurement

### 3.1 Commitment floors cannot be the over-priced bottom (framing 1's first suspect)

The brief directs: *"ask what floors the overnight price too high before you ask
what caps the peak too low."* Interrogated, and it is **structurally impossible**
in this direction. A min-gen or bridge floor **adds** supply to the energy
balance; the LP's marginal unit therefore moves **down** the stack and the dual
**falls**. A floor can depress the bottom price, never raise it. The keeper's own
D-2 attribution agrees that the floors are modest and passing
(`legitimacy_diagnostics.json`, 2025: `reliability_floor` on ST_GAS 18.4 % of
class, `nyiso_gas_commitment_bridge` 3.3 % of CC_REGULAR / 1.2 % of ST_GAS, all
inside their rule-20 caps, D-2 `passed: true`). **The floors are not the object
and no floor was touched.**

### 3.2 Reserve co-optimisation contributes nothing below the 90th percentile

Summed reserve-family duals on the keeper's own `reserve_family_<year>` sidecar
— the only artifact in which a locational family's binding is observable:

| year | mean | share of hours > 0 | p0–50 | p50–90 | p90–100 |
|---|---|---|---|---|---|
| 2023 | $0.108 | 0.2 % | 0.000 | 0.000 | 1.080 |
| 2024 | $0.038 | 0.1 % | 0.000 | 0.000 | 0.381 |
| 2025 | $0.162 | 0.4 % | 0.000 | 0.000 | 1.619 |

**Exactly zero** in both bands that carry the deficit. This both eliminates
reserves as the bottom-band cause and sets up §4.

### 3.3 Storage arbitrage buys ~$1.4 of the bottom, ~$0.35 of the top

Net storage discharge by decile, 2025: **−368 MW at d0** (charging) rising to
**+196 MW at d9**. At the model's own local ladder slope that is ≈ **$1.4/MWh**
of the bottom's over-price and ≈ **$0.35/MWh** of the top's under-price. And it
is not an over-cycling artifact to be trimmed: the model's pumped storage
discharges 0.540 TWh in 2025 on 1,220 MW, i.e. it **under**-cycles rather than
over-cycles. Real and small; not the object.

### 3.4 The peak-hour supply MIX is right — the model prices the right units too cheaply

Model top-decile dispatch vs EIA-930 NYIS, each on its **own** load ordering
(2025, MW): gas 12,850 vs 13,566 (**−716**), hydro 3,715 vs 3,461 (+254),
imports 2,691 vs 2,507 (+184), oil 282 vs 148 (+134), nuclear 3,253 vs 3,273
(−19). At 23.9 GW of load the mix agrees to **within 3 %**, and the classes with
the most headroom are nowhere near bound (nyiso-167: decile-9 mean dispatch is
43 % of ST_GAS's annual max, 23 % of CT_PEAKER's). **The model dispatches
essentially the right machines and charges too little for them** — which moves
the object off availability and merit order and onto price formation.

## 4. The decisive measurement: the market's steepness is NOT physical

The NY fossil fleet's **own measured incremental heat rate**, from CAMPD
unit-level hourly `grossLoad` + `heatInput` pooled to a fleet total, by
first differences (`|ΔMW| > 200`), binned by output quintile:

| year | low output → high output | rise |
|---|---|---|
| 2023 | 7.29 → 7.63 → 7.81 → 8.22 → **8.83** | **+21 %** |
| 2024 | 6.85 → 7.24 → 7.75 → 8.34 → **8.84** | **+29 %** |
| 2025 | 7.06 → 7.54 → 7.90 → 8.17 → **8.64** | **+22 %** |

Against the **price-implied** marginal heat rate (price ÷ Transco Z6), 2025:

| | d0 | d8 | d9 | rise |
|---|---|---|---|---|
| actual DA | 13.33 | 20.80 | **29.02** | **+118 %** |
| model | 15.33 | 17.34 | **23.71** | +55 % |

**The market's price rises five times faster with load than its own fuel burn
does.** Only about a fifth of the market's revealed supply-curve steepness is
physical heat-rate dispersion; the rest is markup and congestion. Two
consequences, both load-bearing for a successor:

* **The heat-rate-dispersion family is closed as the explanation.** Making the
  model's merit order more dispersed cannot reach a 118 % ladder from a 22 %
  physical one, and NYISO's heat rates are already measured (`measured_ct_heat_rates`,
  `measured_chp_heat_rates`, `egrid_identity_heat_rates`, all `K`).
* **The model is at 55 %, the market at 118 %, physics at 22 %.** The model
  already prices *more* curvature than physics justifies — it carries roughly
  half the market's non-physical steepness (the offer-curve peak tranches) and
  is short the other half. Closing it means representing more **markup or
  congestion**, and both routes are constrained (§5, §6).

## 5. The zonal split — and why it is not a locational story

Load-weighted deficit decomposed against the least-congested zone
(Upstate_West), `_nyiso168_gap_anatomy.json` §F:

| year | load-weighted deficit | gradient component | level component |
|---|---|---|---|
| 2023 | −$0.69 | **+$0.96** | −$1.65 |
| 2024 | −$1.43 | −$1.49 | **+$0.07** |
| 2025 | −$6.59 | −$2.32 | **−$4.27** |

**The gradient component has no consistent sign** — the model *over*-shoots the
zonal gradient in 2023 and under-shoots it in 2024/2025. The **level** component
is the one that tracks the year's price level (−1.65 / +0.07 / −4.27), which is
the gain law's own signature. In 2025 the split is **35 % gradient / 65 %
level**, and the level component is measured **in Upstate_West itself** — a zone
no downstate, in-city or seam mechanism reaches. This independently reproduces
nyiso-167 §2.3's upstate passthrough ratio of 0.799 and confirms its warning: a
locational fix cannot be the whole answer, and on this measurement it is not
even the reliable half.

## 6. The one new mechanism the object points at — and its ex-ante kill

### 6.1 The gap, proven in code

NYISO's market clears reserves **above zero in 100.0 % of DAM hours in every
zone**, with both a locational and a load gradient
(`_nyiso168_reserve_supply_slack.json`). The keeper clears them at zero in
99.6 % of hours (§3.2). Measured DAM reserve cascade — the three products are a
**nested cascade, so MAXed, never summed** (the xiso-cascade rule):

| year | mean | share > 0 | p0–50 | p50–90 | p90–100 |
|---|---|---|---|---|---|
| 2023 | $6.72 | 99.9 % | 4.89 | 7.46 | 12.94 |
| 2024 | $6.29 | 100.0 % | 4.82 | 6.86 | 11.37 |
| 2025 | $12.17 | 99.9 % | 6.78 | 13.37 | **34.34** |

By zone (2025 DAM mean): WEST / GENESE / CENTRL / NORTH / MHK VL **$6.27** ·
CAPITL $8.50 · DUNWOD / HUD VL / MILLWD / LONGIL $9.31 · N.Y.C. **$12.17** —
positive in 100.0 % of hours in **every** zone, Niagara's and St. Lawrence's
included.

And the structural asymmetry, verified in source rather than inferred:
`_nyiso_design` returns a `ReserveDesign` with **`supply_cap=None`,
`headroom_eligible=None` and no `pergen_*`** — every eligible unit's FULL
headroom backs reserve at zero cost. `_ercot_design`, `_ercot_multiproduct_design`
and `_pjm_design` all set `supply_cap`; PJM additionally runs the full
per-generator layout. **NYISO is the only ISO with the machinery and none of it
armed.**

### 6.2 The kill, pre-registered and fired before any solve

**Pre-registered kill:** *if the ramp10-capped supply CEILING still clears every
NYCA family's requirement by a wide margin on the capacity basis alone, a
per-generator ramp bound is PROVABLY LP-INERT for NYISO and no solve is spent.*

The ceiling is `Σ_g ramp10_frac_g × pmax_g` over each eligibility class —
fractions from `fleet.withholding.RAMP10_FRAC_BY_FUEL` (NREL/TP-5500-55588
App. H class ramp rates + EIA generator ramp ranges), before availability or
dispatch subtract anything. 2025:

| family | requirement | ceiling **with** hydro | cover | ceiling **thermal only** | cover |
|---|---|---|---|---|---|
| `nyca_30min_total` | 2,620 MW | 18,815 MW | 7.18× | 12,837 MW | **4.90×** |
| `nyca_10min_total` | 1,310 MW | 12,538 MW | 9.57× | 6,560 MW | **5.01×** |
| `nyca_10min_spin` | 655 MW | 12,538 MW | 19.14× | 6,560 MW | **10.01×** |

**The kill fires, and it fires on the thermal fleet alone.** NYISO's
`QUICK_START_FUEL_TYPES` capacity (gas_ct 3,091 MW + oil 3,468 MW, both at
ramp10 fraction 1.00) is **6,560 MW against a 655 MW spinning requirement** —
ten times over, with hydro excluded entirely and before a single hour of
availability is applied. Stable across all three years (4.89–4.90× / 4.99–5.01×
/ 9.97–10.01×). **A per-generator ramp bound cannot bind in NYISO. No solve was
spent, and the mechanism is not built.**

### 6.3 What this corrects on the record, and what it does not

nyiso-144 confirmed `nyiso_spin_reserve_online` = `I` and nyiso-145 narrowed its
re-open condition to *"a defensible 10-minute deliverable-ramp capability for
NYISO hydro,"* naming the hydro RAMP10 coverage gap as the blocker and two code
seams as lane-sized. **Both records stand and neither is overturned.** Two
things are added:

* **The ramp-CAPACITY route is inert independently of hydro**, at 4.9–10× cover
  on thermal capacity alone. This is a *different* construction from the rho
  gate nyiso-144 measured (`R ≤ ρ × Σ_g P`, which gates on **dispatch**, where
  hydro genuinely does dominate: min Σ P is 1,912 MW with hydro, 59 MW without).
  **The rho route is untouched by this finding**; only the capacity-cap route is
  adjudicated, and only it moves a cell.
* **The remaining blocker is not a capability estimate.** NYISO's requirements
  are simply small relative to a 30 GW fleet, so no *quantity* mechanism closes
  the measured reserve-price gap. What is left is either **offer-side AS
  availability bids** — inadmissible here, `measured_offer_surface` = `G`, and
  NYISO publishes no AS offer data — or the **online/synchronised structure**
  the rho gate targets, whose identification is the owner-funded AS-certification
  + water-limit intake nyiso-145 named. **Neither is reachable in this lane.**

**Rule 13 `[R-MEASURED]` bars the shortcut.** NYISO's posted reserve price is a
measured *outcome*. Feeding it in as an input to lift the energy price would be
pinning the backcast to actuals — precisely the forbidden move. It is used here
as **evidence that a gap exists**, never as an input, and no adder was built.

## 7. Framing (2) — the NEISO existence proof is not available on the committed record

The brief requires establishing **first, from NEISO's own record**, that the four
gates nyiso-167 §4 associated with NEISO's 0.986 gain are what closes it.
Census of every committed NEISO bundle's `run_config.json`
(`_nyiso168_gap_anatomy.json` §G):

| bundle | `neiso_winter_fuel_inventory` | `..._mustrun` | `neiso_gas_coldsnap_derate` | `scarcity_price_overlay` | `temp_dependent_derate` |
|---|---|---|---|---|---|
| `neiso86_2022_corrected` | true | true | true | true | true |
| `neiso97_dstrepair_A` | true | true | true | true | true |
| `neiso99_basis_A` | true | true | true | true | true |
| `neiso99_joint_B` (keeper) | true | true | true | true | true |

**4 of 4 arm all five. There is no committed NEISO arm without them**, so the
attribution nyiso-167 asked a successor to make **cannot be made from the
committed record at all** — the association stays an association. Framing (2) is
closed on evidence, not on judgement, and **no NEISO cell was read as a verdict
and no NYISO cell was filled from one** (rule 25 `[R-ISO-SCOPE]`, rule 28(d)).

Separately, and checked before anything else was read: NYISO's four `·` cells
are `·` because **NYISO's own equivalents are armed under NYISO-native names** —
`nyiso_rcpf_family`, `nyiso_nyc_rcpf_step_curve`, `nyiso_ordc_measured_step_span`
and `nyiso_seny_rcpf_increment_step` (all `K`) are NYISO's scarcity-pricing
family, and `dual_fuel_switching` + `nyiso_downstate_ct_gas_basis` (both `K`) are
its cold-snap fuel family. The `·` is correct on the merits, not a gap.

## 8. Lines this session closes

* **CLOSED — "the deficit is a scarcity/tail object."** 73 % of 2025's sits in
  the 50–90 band; the top 1 % carries 1.2 %. Do not open a C3c lever for C3a.
* **CLOSED — "a commitment floor over-prices the overnight."** Structurally
  impossible in that direction; floors add supply and lower the dual.
* **CLOSED — "the model's merit order is too compressed."** The market's own
  physical incremental heat rate rises only 21–29 % across the load range while
  its price rises 118 %; the model already prices more curvature (55 %) than
  physics justifies (22 %).
* **CLOSED — "mix or availability at peak."** The model's top-decile mix matches
  EIA-930 to within 3 %.
* **CLOSED — a per-generator ramp bound on NYISO reserve supply** (`reserve_pergen`
  `·` → `I`): provably inert ex ante at 4.9–10× cover on thermal capacity alone.
* **CLOSED — framing (2) as an attributable transfer**: no NEISO arm without the
  four gates exists.
* **NOT OPENED — the offer-side and rho routes.** Both named, both bounded, both
  blocked on data this lane cannot obtain (§6.3).

## 9. Honest expected value

**What is delivered.** A reproducible, zero-solve anatomy that (a) relocates the
object from the tail to the ordinary 50–90 load band and sizes it at 73 % of
2025's deficit, (b) kills four candidate causes on measurement, (c) establishes
from NYISO's own CAMPD burn that the market's supply-curve steepness is ~80 %
non-physical, which closes the heat-rate family and re-points the search at
markup and congestion, (d) splits the 2025 deficit 35 % gradient / 65 % level and
shows the gradient component is not even consistently signed, (e) produces the
first measurement of NYISO's own AS clearing prices against the keeper's reserve
duals and proves the structural asymmetry in source, and (f) adjudicates the one
new mechanism the object points at as provably inert **before** spending a solve.

**What is NOT delivered.** **No gate moves.** C3a-2025 is still −11.5 %, C3c
still fails, the determination is still **NOT-YET on {C3a-2025, C3c}**, and
NYISO still does not read CALIBRATED. **No solve ran**, so rule 15 registers
nothing — the dashboard is untouched by design, not by omission. One matrix cell
moves (`reserve_pergen` `·` → `I`) and two carry added evidence without moving.
The gain itself is **unmeasured against any arm**, because no arm was built.

**What could still be wrong.** The incremental-heat-rate measurement is a
*fleet-pooled* first difference: it captures the marginal machine's burn only to
the extent the fleet's hour-to-hour move is made by the marginal machine, and it
cannot see within-unit incremental heat-rate curvature that CEMS reports only in
aggregate. The band decomposition uses the DA hub series for the actual and the
model's load-weighted zonal composite for the model — appropriate for a level
comparison, but the two are not the same spatial object, so the *gradient*
component of §5 is the weaker of the two legs. The ramp-ceiling kill is a
capacity-basis bound and is therefore conclusive **only for the capacity-cap
construction**; it says nothing about the rho/online construction, which remains
`I` on nyiso-144's own separate grounds. And the reserve-price gap is proven to
exist without being explained: this finding shows that no quantity mechanism
closes it, not that the offer-side explanation is right.

**The honest read on the object.** After nyiso-167 and this session, the gain
deficit has been narrowed from "the model's price response is uniformly too
weak" to "the model is short roughly half of the market's *non-physical* supply-
curve steepness, in ordinary daytime hours, in the least-congested zone as much
as downstate." Every admissible NYISO-measured lever for that is now either
adjudicated or blocked on an intake the owner has closed. **A successor should
not expect to close C3a-2025 with a mechanism from the current data set**, and
the standing $27.8–$56.0/MWh pass window nyiso-167 derived should be planned
around rather than solved away.

## 10. A brief-premise correction, recorded

The brief directs: *"`DECISION-CARD-nyiso161` — FILED AND UNRULED; check whether
it has been ruled before planning around it."* **Checked: it has been ruled.**
Owner ruling **R-H** decided it **OPTION A — NOT-YET STANDS** (no rubric
amendment, no new caveat class), recorded at board D-7 in the v18b completion
(PR #4498, `9e4291b6`) after the brief was written. Nothing in this session
plans around the card, and nothing here re-litigates it.

## 11. Evidence

* `results/calibration/_nyiso168_gap_anatomy.json` + `scripts/probes/nyiso168_gap_anatomy.py`
  — measurements A–G.
* `results/calibration/_nyiso168_reserve_supply_slack.json` +
  `scripts/probes/nyiso168_reserve_supply_slack.py` — the AS-price/dual gap and
  the ramp10 ceiling.
* `results/calibration/_nyiso167_price_gain_attribution.json` — re-run first,
  reproduces bit-identically.
* `docs/FINDING-nyiso167-c3a-price-response-gain-2026-09-01.md` §§2–6 — the
  object, and the four lines it closed which this session did not re-open.
* `src/market_sim/model/reserves/spec.py::_nyiso_design` (no `supply_cap`, no
  `headroom_eligible`, no `pergen_*`) vs `_ercot_design` / `_ercot_multiproduct_design`
  / `_pjm_design` (all set `supply_cap`); `pjm_pergen_structure`,
  `pjm_pergen_pool_ramp10`; `market_sim.data.fleet.withholding._ramp10_capability`
  and `RAMP10_FRAC_BY_GROUP` / `_BY_FUEL`.
* `docs/codebase-site/data/mechanism-matrix/NYISO.js` — `nyiso_spin_reserve_online`
  (nyiso-144 §1.4, nyiso-145 §5) and `measured_ramp_capability` (nyiso-113 §4),
  both re-read before anything was proposed; neither verdict moves.
* `docs/handoffs/audit-program-director-board-2026-08.md` D-7 — ruling R-H (§10).
* CLAUDE.md rules 1 `[R-STRUCT]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`,
  17 `[R-FLOOR-WINDOW]`, 19 `[R-ONE-MECH]`, 22 `[R-HOLDOUT]`, 25 `[R-ISO-SCOPE]`,
  28 `[R-MECH-MATRIX]`.

Next shorthand: nyiso-169.
