# ERCOT-58: the ercot57 joint round — three-probe adjudication of the ORDC-only design, and the binding-regime supply-mix gap it uncovers

**Session 2026-07-11 (owner-sanctioned: the ERCOT-57 filed completion — "measured
availability + an envelope re-identified on the measured-fleet basis … together with
the product-ladder design question (per-product VOLL ramps vs ORDC-only scarcity
pricing)"). Keeper under test: `2026-07-10-ercot56-nucwin`. All probes here are
rule-16 2023-only throwaways (never registered); the registered full-span record is
the `ercot58 joint` bundle + zero-forcing twin (see the ERCOT-58 calibration-log
entry for scores and disposition).**

**Verdict in one line: the joint round's market-faithful completion is v3 — plan-only
in-LP withholding + the measured-basis envelope as a PRICING-ONLY basis for a
post-solve realized-room RTORPA (the published RTSPP = SPP + adder construction) —
and it is LP-healthy and cures the phantom-scarcity channel, but its 2023 summer
over-fire measures a real +2.4 GW binding-regime thermal-dispatch excess vs CAMPD
(leading identified component: model storage discharging ~0.15 GW at binding hours
where the real fleet ran ~1–2 GW — the same open lane as the keeper's ledgered
C5c-2024 storage-shape caveat), sitting exactly on the steep end of the ORDC. The
scarcity-pricing structure is no longer the binding defect; the supply mix at the
peak is.**

## 0. What was re-identified (leg B — the envelope on the measured-fleet basis)

The ercot41/43 envelope A/Bs ran on the phantom-tight statistical availability stack
(the ERCOT-57 confound). The re-identification decomposes the old share (committed
on-line HSL ÷ INSTALLED capacity — commitment and outage state conflated) into:

* share = committed on-line HSL ÷ **measured AVAILABLE** capacity (the 60-Day DAM
  disclosure class-day fraction × installed) for the disclosure-covered classes
  (CC_REGULAR, CT_PEAKER);
* basis = the fleet's **finished availability** (`Σ pmax × availability(t)` — the
  measured rescale in backcast, the statistical stack forward: the G4 mode-aware
  seam), so availability carries the outage state and the share carries only
  commitment;
* CHP classes on the **export basis** (CAMPD CEMS gross is full cogen host+grid;
  the model's CHP units and dispatch are grid-export — `1 − chp_btm_pct`), removing
  a ~2.5 GW host-gross room inflation.

Identification gate (`validate_ercot_online_capacity.py --measured`): binding regime
+3/+1/−3 % (2023/24/25), pooled top-2 % extreme tail **exact (−0.0 %)**, coverage
2.11×. The per-year extreme-tail ledger tightens from ercot43's **−23/−2/+18 %** to
**−13/−0/+9 %** — the availability decomposition genuinely carries about half the
cross-year capability spread, confirming the confound. A measured check of the
commitment share on the availability basis is essentially FLAT (~0.94–0.95) across
years and across both a within-year-rank and an absolute-net-load axis — commitment
choice was never the cross-year term; availability was.

## 1. v1 — in-LP ORDC total family + envelope LP row: REJECTED (the §7.4 defect, now on the honest fleet)

Config: measured availability + measured-basis envelope row + ε-ladder products +
in-LP `ercot_ordc_total` span demand. 2023 probe: C3a +55 %, Aug +72 %, Sep +119 %,
**62 GWh load shed in 41 hours**, and **12.8 GW of coal parked at zero output at the
Aug-25 peak hour** while reality ran it flat out. Decomposition: the cap-dual adder
is zero everywhere and the entire over-fire is quantized VOLL prints in the energy
dual — the ORDC total curve's sub-MCL steps sit AT VOLL (the OBDRR048 floors), so
holding reserve and serving load are exactly degenerate, and inside the envelope the
LP withholds up the full span instead of dispatching. This is the ercot43 §7.4
conclusion ("energy competes with the full ORDC span inside the envelope")
reproduced with the availability confound removed: **the in-LP span demand is the
defect, not the fleet.** Real pre-RTC+B SCED never solves this trade — it is
energy-only, and the ORDC prices realized reserves post-hoc.

## 2. v2 — plan-only withholding + envelope as a HARD LP row: REJECTED (the hard-cap-at-reality's-level failure)

Config: v1 minus the total family (RTORPA moved post-solve onto the realized room).
2023 probe: **833 GWh shed across 476 hours** (Jun–Sep afternoons, HE12–20), C3a
+707 %. With no span demand inside it, the envelope row itself binds on ENERGY: an
LP cap anchored to *reality's* committed capability converts every hour where the
model's supply mix differs from reality's (storage timing, class mix, demand shape)
into VOLL shed. This isolates the remaining ercot41/43 over-fire mechanism from both
availability and span demand: **a committed-capability constraint does not belong in
the dispatch engine at all.** Pre-RTC+B SCED carries none — commitment is
RUC/self-commitment, already embodied in the model's availability and floors.

## 3. v3 — the market-faithful form: envelope as PRICING-ONLY basis, post-solve realized-room RTORPA

Config: ε-held product plans (physical DAM-award withholding) + rigid pre-reform
ECRS_withheld + **no** envelope LP row + **no** in-LP total family;
`scarcity.ercot_ordc_realized_adder` computes RTORPA post-solve:

    online(t)  = max(env_all(t) − Σ_elig P[g,t], 0) + measured storage-AS award
                 + LR RRS-UFR credit
    offline(t) = forward RTOFFCAP (supply-cap row 1 − row 0)
    RTORPA(t)  = ordc_adder(online + offline, λ; online)   # two-half-hour LOLP +
                                                           # OBDRR048 floor, VOLL cap

2023 probe: **LP healthy** (shed 0.2 GWh, coal dispatches normally), adder mean
$164/MWh, >$10 in 1,583 h, model tail 1,022 h vs 310 DA — a broad summer over-fire
concentrated in the adder, i.e. the realized ROOM runs systematically too tight in
the binding regime.

## 4. The uncovered root cause: a +2.4 GW binding-regime thermal-dispatch excess

Class-resolved comparison of the model's P1 dispatch against the CAMPD export-basis
on-line gross (the envelope target's own dispatch side), top-30 % net-load hours:

| class | model P (MW) | CAMPD gross (MW) |
|---|---|---|
| COAL | 10,616 | 10,437 |
| CC_REGULAR | 23,842 | 22,333 |
| CC_CHP | 3,401 | 3,510 |
| CT_PEAKER | 1,666 | 2,311 |
| CT_CHP | 548 | 365 |
| ST_GAS | 4,841 | 3,555 |
| **TOTAL** | **44,922** | **42,512 (+2,411)** |

The model serves ~2.4 GW more of the binding-regime load with envelope-class thermal
than reality did, so `env − P` sits ~2.4 GW below the identified RTOLCAP-consistent
level exactly where the ORDC curve is steep. Leading identified component: **model
storage discharges 145 MW mean at binding hours (net +108 MW)** where the real 2023
battery fleet ran ~1–2 GW at evening peaks — the model's batteries are
AS-committed (measured award reserved out of the power cap) plus dissuaded by the
$10 throughput adder, and its perfect-foresight arbitrage does not reproduce the
real evening-peak discharge. This is the SAME open lane as the keeper's ledgered
C5c-2024 storage-dispatch-shape caveat (r = 0.361) and the G-37 duration-gate
finding ("storage loses its award in the tight evening peak") — the realized-room
construction converts that known shape error into a price error, which is exactly
what a structurally-honest mechanism should do (rule 14: the accurate structure
exposes the miscalibrated input; do not bury it back). Secondary terms: ST_GAS
+1.3 GW / CT_PEAKER −0.6 GW class-mix shifts (drag-floor-committed steamers serving
load the real market met with peakers), and the gross-vs-net metering wedge between
CAMPD gross and the model's net dispatch (which biases the room LOOSE, i.e. the
supply-mix gap is somewhat larger than +2.4 GW).

## 5. Disposition and the forward path

* The full-span `ercot58 joint` bundle + zero-forcing twin register as the honest
  record (rules 15/16); **keeper stays `ercot56-nucwin`** — the joint round's v3 is
  more structurally faithful on the scarcity-pricing side but the binding-regime
  supply mix it exposes prices 2023 far outside the gates (the same
  keep-the-structure/fix-the-root-cause posture as ercot57).
* The product-ladder design question is **adjudicated**: per-product VOLL-ramp
  ladders and the in-LP span demand are both non-market constructions that fail on
  the honest fleet; the realized-room post-solve RTORPA is the faithful form and
  stays built (default-off) for the next round.
* The next root-cause lane is the **binding-regime supply mix**, storage first: the
  evening-peak battery discharge (C5c/G-37 lane — forward AS commitment under
  uncertainty and/or measured-award energy co-participation), then the ST_GAS/CT
  class-mix at the peak. When that lane closes, re-probe v3 — its room is bounded by
  the same gap, and every other component (availability, envelope identification,
  plan withholding, adder construction) is measured-anchored and already gated.
* Rule-26 note: the ORDC tariff parameters (VOLL, MCL, LOLP μ/σ, floor steps) were
  NOT touched at any point; the three probes changed only which mechanism carries
  them.
