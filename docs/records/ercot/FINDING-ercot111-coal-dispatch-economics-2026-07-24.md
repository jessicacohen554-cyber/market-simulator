# FINDING — ERCOT-111: the coal over-run is an OFFER-LEVEL error, not a capability or commitment one

**Date** 2026-07-24 · **ISO** ERCOT · **Year** 2023 ·
**Baseline** `results/calibration/ercot110_coal_dam_avail` (coal DAM availability ARMED — *not*
the keeper, whose coal availability is the phantom one) ·
**Arm** `results/calibration/ercot111_coal_econ_marginal_hr` ·
**Gate** `ScenarioConfig.coal_econ_marginal_hr_bound` (default **off**; keeper unchanged)

## 1. The question

ERCOT-110 gave the coal fleet its measured 60-Day DAM availability and the over-run got **bigger**
(64.0 → 72.3 TWh against 62.3 actual) — the statistical derate had been silently substituting for
missing coal-side economics. The re-chartered question: **why does the model dispatch ~10 TWh/yr of
coal that the real ERCOT market left idle?**

## 2. Diagnosis — the channel, measured

`scripts/probes/ercot111_coal_dispatch_econ.py` (no LP) rebuilds three per-hour envelopes for the 26
registered ERCOT coal resources from the 60-Day DAM Gen_Resource disclosure (`CLLIG`) and splits the
model-minus-actual coal into mutually exclusive channels. Measured envelopes are scaled by
`model_pmax / DAM rating` (13,964 / 13,585 = 1.028) so the capacity-basis gap is charged to nobody.

2023, 6,575 covered hours (the Oct/Dec publication holes are the only gap), annualised:

| | TWh | vs actual |
|---|---|---|
| actual | 62.71 | — |
| model (ercot110) | 74.44 | **+11.73** |
| model capped at measured **LIVE capability** | 74.43 | +11.72 |
| model capped at measured **COMMITTED envelope** | 74.27 | +11.56 |

| channel | mean MW | share |
|---|---|---|
| a) above measured capability | +1 | 0 % |
| b) on uncommitted capacity | +18 | 1 % |
| **c) economic, inside the committed envelope** | **+1,319** | **99 %** |

**A capability ceiling buys 0.01 TWh and a commitment bridge buys 0.17 TWh.** Both candidate lanes
are refuted before a line of mechanism was written — including the coal analogue of the ERCOT-63 gas
bridge (charter lane 2), which cannot reach a 1.3 GW error through a channel worth 18 MW.

Supporting measurements, all from the same disclosure:

* **AS reservation is not the story.** Committed coal's awarded up-AS (RegUp + RRS + NonSpin + ECRS)
  totals 1.00 TWh against 79.7 TWh of committed HSL — **1.3 %**. Closed without reopening the
  reserve side (ERCOT-107/108).
* **Ramp is not the story, in the opposite direction.** The model's coal fleet ramps *less* than the
  real one: mean |ΔMW/h| 332 vs 431; mean daily range 3,402 vs 4,120 MW.
* **Real coal was not capability-bound.** Mean live HSL 10,772 MW, committed HSL 10,061 MW,
  committed LSL 3,912 MW, actual output 7,112 MW — 52 % up its own committed range. It reaches
  93–95 % of live HSL only above $200/MWh.

## 3. The mechanism it points at — the revealed supply curve

Coal MW binned by each side's **own** price (ercot110 baseline):

| $/MWh | actual MW | model MW |
|---|---|---|
| 0–10 | 4,199 | 2,417 |
| 15–20 | 5,787 | 5,637 |
| 20–25 | 7,563 | 7,786 |
| 25–30 | 8,604 | 9,395 |
| 30–40 | 9,089 | 11,004 |
| 40–60 | 9,301 | 12,028 |
| 60–100 | 9,979 | 12,146 |
| >200 | 10,922 | 12,276 |

The two curves agree to ~$25 and then diverge: **the model's coal is about twice as price-elastic as
the real fleet's.** The real fleet spans 3.6 → 10.9 GW across the whole price range; the model spans
2.4 → 12.3 GW.

Reading the model's own coal offer stack (fleet-build capture, no solve) explains it. The registered
ERCOT `COAL_PRB` econ ramp is **econ_low 0.400 → econ_high 1.380** — a 3.45× spread of the plant's
base heat rate, producing a per-plant ladder of **$12.96 → $28.07/MWh**. Every other coal group is
near-flat (`COAL` / `COAL_BIT` 0.95, `COAL_LIGNITE` 1.216, `COAL_WC` 0.90), and PRB is 7 of the 10
modelled ERCOT coal plants.

The 0.400 is not physical and not measured. It is the keeper's fitted `-0.30` run delta on the
already-fitted 0.70 ERCOT base. Against it stand two independent measurements:

* **This repo's own committed CAMPD artifact** (`data/raw/reference/ercot_campd_marginal_hr_summary.csv`,
  `scripts/data/derive_campd_marginal_hr.py`). ERCOT COAL **marginal (incremental)** heat rate:
  committed 0.867, econ_low **0.886**, econ_high **0.898** — essentially flat, as a coal boiler's
  input–output curve is. The registered 0.400 is **2.2× below** it.
* **The 2023 DAM submitted coal offer stack.** The real fleet price-takes only up to LSL (blocks at
  ~$1.00/MWh sized at the unit's LSL) and every submitted *incremental* offer above it prices
  **≥ ~$16.3/MWh**, median first point $16.6, median top-of-curve $21. Roughly 1,500 MW of model
  coal was offered below anything the real market offered above its min-load — almost exactly the
  size of the mean over-run.

## 4. The mechanism

`ScenarioConfig.coal_econ_marginal_hr_bound` (`--coal-econ-marginal-hr-bound`, default **off**).

Offer-curve bands are price-calibrated and may legitimately carry a **markup** above their physical
basis. They may not carry a bid **below** it: an already-committed coal unit's next MWh costs at
least its own measured incremental burn × delivered fuel. Each coal class's `econ_low` / `econ_high`
is therefore clamped **up** to the ISO's own measured CAMPD marginal heat rate for COAL. Markups
above the basis pass through untouched; the `committed` / `mustrun` take-or-pay bands (a contractual
discount, not a physical-burn claim) and the `peak` scarcity wall are out of scope (rule 19).

Applied to the **resolved** curve — after base registry, `--offer-curve-json` and
`--offer-curve-delta-json` — so it bounds what the calibration path actually produced.

For ERCOT it lifts exactly one band:

```
ERCOT coal econ marginal-HR floor (1): COAL_PRB.econ_low 0.400 -> 0.886
```

`COAL_LIGNITE` (1.216 / 1.113) and `COAL_PRB.econ_high` (1.380) already clear their measured basis
and are untouched. The per-plant PRB econ ladder moves **$12.96 → $28.07** to **$21.43 → $29.04**.

Admissibility: this **removes** a fitted degree of freedom rather than adding one, adds no tunable,
consumes an artifact this repo already derives and commits, and regenerates for a forward year from
the same CEMS input–output curves (rule 13). The PRB/lignite passthrough sigmoids are untouched
(rule 23). Default-off and registered in `_CACHE_KEY_OPTIONAL_FIELDS`, so every existing keeper is
byte-identical.

## 5. Pre-committed adjudication

Written before any A/B result was read (`--set` arms the ERCOT-110 coal availability overlay in
**both** arms; the solve log was checked for both mechanisms' INFO lines before scoring):

> **PRIMARY** — Jun–Sep coal ratio moves toward 1.0 from 1.206, **and** annual moves toward 1.0 from 1.161.
> **SECONDARY** (report, do not optimise) — C3a (−25.2 %), C3c settle (50/181), ERCOT-109 cheap-stack
> surplus (122/122 h, median +1,399 MW), gas deficit (−2.2 GW).
> **EXPECTED** — coal falls, gas rises, the model's price tail deepens. Over-correction is a live
> risk: coal may fall below actual.
> **FAIL SIGNATURE** — the ercot41/43 over-fire: model tail hours priced > $200 blow past ~181.

## 6. Result — **PRIMARY PASSES, both legs**

Solve log verified for BOTH mechanisms' INFO lines before scoring (the ERCOT-110 silent-inert trap):
`coal econ marginal-HR floor (1): COAL_PRB.econ_low 0.400 -> 0.886` and
`COAL plant-grain redistribution — 10 crosswalked plant(s), 0 unmapped tranche(s)`.

Model/actual coal by month:

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | **yr** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| keeper | 0.84 | 0.83 | 0.73 | 0.82 | 1.06 | 1.15 | 1.18 | 1.17 | 1.18 | 1.05 | 1.01 | 0.92 | **1.028** |
| ercot110 | 1.27 | 1.24 | 1.05 | 1.08 | 1.16 | 1.21 | 1.22 | 1.20 | 1.21 | 1.04 | 1.12 | 1.08 | **1.161** |
| **ercot111** | 1.00 | 1.00 | 0.85 | 0.91 | 1.09 | 1.16 | 1.18 | 1.18 | 1.16 | 0.95 | 1.03 | 0.87 | **1.053** |

**PRIMARY:** Jun–Sep **1.207 → 1.169** and annual **1.161 → 1.053** — both move toward 1.0. PASS.
Coal 72.32 → **65.57 TWh** (actual 62.29); gas 189.46 → **196.20 TWh** (actual 201.46), so the
displaced coal returns to gas, closing the ERCOT-109 gas deficit from −12.0 to −5.3 TWh annually.

Secondary (reported, not optimised):

| metric | keeper | ercot110 | **ercot111** |
|---|---|---|---|
| C3a 2023 | −27.3 % | −25.2 % | **−24.3 %** |
| C3c settle | 76/181 | 50/181 | **50/181** |
| coal @ 122 scarcity h | +424 MW | +922 MW | **+922 MW** |
| cheap-stack surplus | 118/122, +871 | 122/122, +1,399 | **122/122, +1,399** |
| gas deficit @ scarcity | −1.7 GW | −2.2 GW | **−2.2 GW** |

**FAIL SIGNATURE ABSENT** — the model's >$200 tail is 50 hours against 181 actual, i.e. it still
*under*-fires; nothing resembling the ercot41/43 over-fire.

### The limitation this exposes, stated plainly

The two arms are **byte-identical in 140 of the 144 actual ≥$300 hours** (1,877 of 8,760 hours
overall). That is not a defect — at scarcity the model already runs coal at 99.5 % of its measured
live envelope, so no offer-level change can move it. The floor bites exactly where coal is
*marginal* (the $10–25/MWh band that holds most hours) and is inert where coal is *capped*.

The consequence: **this mechanism fixes the annual coal LEVEL and does not touch the summer
scarcity-hour COMPOSITION.** The residual +922 MW of scarcity-hour coal, and the 122/122 cheap-stack
surplus with it, are an availability-basis and wind question, not an offer question — the model's
coal deliverable is 1.026× the measured live HSL there, and wind is +377 MW at hours that are
measurably low-wind. That is the open WIND-compression charter, not this lane.

### Rule 16 / promotion status

Only 2023 was solved, so this is a **PROBE**, not a keeper candidate. A full-span
`--years 2023 2024 2025` single-invocation re-solve plus leave-one-year-out (rule 24) is the
precondition for any promotion. Keeper remains `2026-07-23-ercot100-netrev-margin-keeper`.

## 7. What lands regardless of the verdict

* `scripts/probes/ercot111_coal_dispatch_econ.py` — the envelope decomposition, reusable for any
  ERCOT year and bundle. It is what refutes the capability and commitment lanes.
* `ScenarioConfig.coal_econ_marginal_hr_bound` + `market_sim.data.coal.coal_marginal_hr_bounds` /
  `apply_coal_econ_marginal_hr_floor` — gated off, ISO-generic (PJM 0.803/0.809, MISO 0.838/0.838,
  NEISO 0.933/0.631 read from their own artifacts; CAISO/NYISO have no COAL row and no-op).
* `tests/test_coal_econ_marginal_hr_bound.py` — pins both sides of the gate, the scope (committed /
  peak / non-coal untouched), and the cache-key neutrality.
