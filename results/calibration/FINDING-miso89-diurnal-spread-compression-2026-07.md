# FINDING (miso-89, 2026-07-25) — C3b is diurnal-spread compression, and MISO's scarcity apparatus is already built but starved by a 25 GW CT availability hole

**Context.** The one load-bearing FAIL holding `2026-07-25-miso-88-egrid-hr` at
NOT-YET: **C3b price shape, 2025 NRMSE 0.208** against a ≤0.20 veto. Scored from
committed artifacts only — keeper `hourly/` sidecars, the run payload's
`lmpDeltaHr`, `frontend/data/backcast/bench/MISO/`, and direct calls into the
model's own data path. **No LP re-solve.**

The miso-87 finding framed this as a *2025 summer body level* miss. That framing
is incomplete in a way that changes the lane: the miss is **shape**, it is
present in **every year and every season**, and its enabling cause is an
availability-coverage hole, not a price-formation gap.

---

## 1. It is not a 2025 miss and not a summer miss — it is diurnal-spread compression

Peak (HE16–18) minus night (HE01–03), body-censored at $200, model vs actual:

| season | 2023 m / a / ratio | 2024 m / a / ratio | 2025 m / a / ratio |
|---|---|---|---|
| winter   | 4.3 / 10.9 / **0.39** | 3.8 / 13.1 / **0.29** | 2.9 / 9.9 / **0.30** |
| shoulder | 6.0 / 18.2 / **0.33** | 5.5 / 15.9 / **0.35** | 5.8 / 16.2 / **0.36** |
| summer   | 11.7 / 26.3 / **0.45** | 14.2 / 30.1 / **0.47** | 12.2 / 32.7 / **0.37** |

The model reproduces **29–47 %** of the observed diurnal price spread — in every
season, in every year. This is a standing structural property of the MISO build,
not a 2025 event.

What makes 2025 fail the veto is that the **actual** summer spread widened
(26.3 → 30.1 → **32.7**) while the **model's stayed flat** (11.7 → 14.2 → 12.2).
The model cannot follow a tightening market.

Both ends of the day miss, in opposite directions (Jun+Jul, body ≤ $200):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| night HE01–03, model − actual | **+8.1** | **+5.6** | **+7.5** |
| peak HE16–18, model − actual | **−5.9** | **−11.9** | **−16.3** |

In 2023 the two errors roughly cancel in the monthly mean (June Δ = +0.4). By
2025 the peak-side error dominates, because C3b is **load-weighted** and summer
load weights the afternoon. **The metric changed; the model's error did not.**

## 2. The model's supply stack is nearly flat

Empirical stack from the model's own 2025 summer hours — median price by
thermal-dispatch ventile:

| thermal dispatch | 33.8 GW | 48.1 | 56.1 | 65.3 | 72.9 |
|---|---|---|---|---|---|
| median model price | $28.6 | $33.3 | $36.2 | $41.8 | **$52.4** |

**$24 of price across 39 GW of dispatch — ~0.6 $/GW average, 2.0 $/GW at the
steepest ventile.** There is no convexity at the top of the stack. This is the
proximate reason the diurnal spread cannot widen: the marginal unit barely
changes price as the system tightens.

## 3. MISO's scarcity apparatus is ALREADY BUILT, ALREADY ON, and never prices

This is the load-bearing discovery, and it contradicts the standing assumption in
`pipeline/backcast_config.py` (~line 720) that "RDC/ELMP co-optimization is a
separate future lever." It is not future. It is wired, and it is live in the
keeper:

* `energy_reserve_coopt = True`
* `miso_measured_reserve_requirements = True` — measured hourly requirement,
  market-wide **mean 2.64 GW / max 3.30 GW** (2025)
* `miso_zonal_reserves = True`, `miso_midwest_subregional_reserves = True`,
  `miso_reserve_pergen = True`
* `model/reserves/spec.py::_miso_design` — market-wide reserve demand curve
  ramping to `MISO_RESERVE_DEMAND_CURVE_MAX = $3,500/MWh`

Reserve shadow price in the committed keeper hourlies:

| year | hours with reserve_price > 0 | max |
|---|---|---|
| 2023 | **0** / 8760 | $0.00 |
| 2024 | **6** / 8760 | $480.52 |
| 2025 | **2** / 8760 | $35.55 |

The demand curve is never on its sloped segment. **The mechanism is not missing —
it is starved.** Adding another price-formation mechanism on top would be a
second mechanism for a phenomenon that already has one (rule 17).

## 4. What starves it: 25.02 GW of CT with zero measured-outage coverage

CAMPD unit-level derate coverage for MISO 2025, computed directly from
`data.outages.unit_outage_derate_factors` + `_iso_plant_capacity` (the same maps
the LP consumes):

| group | covered GW | total GW | coverage | mean measured availability (covered) |
|---|---|---|---|---|
| COAL | 42.35 | 44.39 | 95.4 % | 0.723 |
| CC_REGULAR | 25.52 | 28.31 | 90.1 % | 0.722 |
| ST_GAS | 9.46 | 11.61 | 81.5 % | 0.377 |
| CC_CHP | 4.88 | 7.04 | 69.3 % | 0.891 |
| ST_CHP | 0.81 | 1.94 | 41.7 % | 0.295 |
| **CT_PEAKER** | **0.00** | **22.39** | **0.0 %** | — |
| **CT_CHP** | **0.00** | **2.63** | **0.0 %** | — |

CTs are outside CEMS coverage **by construction** — a peaker's economic idleness
is indistinguishable from an outage in a generation-derived derate — so they fall
through to the statistical WEFOR/POF layer. `data/fleet/arrays.py` says so
explicitly: *"CTs have no overlay coverage and keep the full statistical model."*

That fallback is **anti-conservative exactly where it matters**. Per
`_availability_matrix` + `THERMAL_AVAILABILITY["CT_PEAKER"] =
(POF 0.03, WEFOR 0.07 +0.003/yr past 20, DERATE 0.05 +0.002/yr past 20)`:

* **POF applies in shoulder months only — zero planned outage in summer.**
* **Only `_SUMMER_WEFOR_SHARE = 0.30` of WEFOR applies in summer**; the rest is
  redistributed into the shoulder.

So summer CT availability is **0.929 (age < 20)** to **0.871 (age 40)** — the
*highest* it is all year, by design. Meanwhile the measured classes carry their
real outages wherever those outages actually fell, summer included (coal 0.72,
CC 0.72).

**The asymmetry is the defect**: measured classes are derated in summer, the 25 GW
CT fleet is deliberately un-derated in summer, and the reserve requirement it has
to clear is only 2.6 GW.

Consistent with that, the model never runs out of peakers. 2025 Jun/Jul HE16–18:
`CT_PEAKER` averages **7.0 GW dispatched of ~20.2 GW available**, peaking at
15.0 GW — **≥5 GW idle at the single tightest hour of the year**, and ~13 GW idle
on average across summer afternoons.

## 5. Why the peak price is not a merit-order number at all

Implied marginal heat rate at summer peak (HE16–18 price ÷ the model's own MISO
delivered gas), body-censored:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| gas $/MMBtu (Jun/Jul mean) | 4.20 | 3.03 | 3.43 |
| model implied HR | 9.0 | 11.4 | 13.4 |
| **actual implied HR** | **10.4** | **15.3** | **18.1** |

At **18.1 MMBtu/MWh** the 2025 actual summer body peak sits far above the
marginal cost of the *worst physical unit in MISO's fleet* (legacy CT 11.5,
ST_GAS ~13). The real summer-peak body price is **not** a fuel-and-heat-rate
number — it is reserve/opportunity-cost rent. The model tops out at 13.4 because
its P1 start-up amortization is the only thing it has above physical cost, and
its reserve leg contributes exactly $0.

---

## 6. Conclusion — Lane B is the precondition for Lane A, not a parallel lane

The handoff listed the CT coverage hole (LANE B) as a separate lane that
"plausibly interacts" with the price lane (LANE A). The evidence is stronger than
that: **they are one causal chain.**

> 25 GW of CT carries no measured outage signal, and its statistical substitute
> empties summer of outages → the model never runs short of peaking capacity in
> summer afternoons → a 2.6 GW reserve requirement never binds → the
> already-built $3,500 reserve demand curve never leaves its flat segment → the
> stack stays at 0.6 $/GW → the diurnal spread reproduces at 37–47 % → C3b fails.

The correct next mechanism is therefore **a measured, non-CAMPD availability
instrument for the CT classes** (rule 13: reproducible physical input, forward
story intact — it regenerates for any year from a published class rate and
responds to fleet age/mix). Not a new pricing mechanism, not a summer multiplier,
not a widened C3c ledger.

### Pre-registered expectation, and the honest limit of it

At the model's own measured local stack slope (~2 $/GW at the top ventile),
removing 2–3 GW of CT capacity buys only **~$4–6** of the **$16.3** peak-hour
body gap *through merit order alone*. The remainder has to come from the reserve
shadow price switching on — a **step**, not a slope. That step is exactly what
this mechanism is meant to arm, and it is **not proven here**.

So the pre-registered bar is deliberately two-part:

1. **Primary (mechanism):** MISO reserve shadow price becomes non-zero in a
   material, summer-afternoon-concentrated set of hours (target: ≥ 200 h/yr with
   `reserve_price > 0`, ≥ 60 % of them in HE12–20). This is the structural claim
   and it is what the run is judged on (rule 1).
2. **Secondary (fit):** C3b-2025 NRMSE falls below 0.20. **If (1) lands and (2)
   does not, the mechanism still stays** — an accurate measured input is kept
   even when the fit does not close (rules 1/11), and the residual becomes the
   next root-cause charter.

**Failure mode that would reject it:** the derate binds outside its declared
window (rule 12/D-4) — e.g. it removes CT capacity in shoulder months where the
model is already short — or it re-breaks C1 by pushing CT_PEAKER volume below its
band. Both are checked before promotion, and any verdict flip is scored
leave-one-year-out within 2023–2025 (rule 22).

## 7. What this finding does NOT license

* **Not** an offer adder, summer multiplier, or residual-tuned band (rules 1/10).
* **Not** widening the C3c ledger — §5 shows the miss is a body phenomenon and
  §3 shows the tail apparatus is present, not absent.
* **Not** re-importing MISO's published aggregate outage total to attribute
  outages across fuels — refuted at charter on two independent grounds
  (`FINDING-miso87-cross-fuel-attribution-refuted-2026-07.md`). The instrument
  must be a **class-level measured rate keyed to the CT fleet itself**, not a
  residual carved out of an ISO-wide total.
* **Not** a fitted CT availability number. If no measured non-CAMPD source
  resolves at CT class grain, the correct outcome is to report that and stop —
  a tuned availability is an answer key (rule 24).
