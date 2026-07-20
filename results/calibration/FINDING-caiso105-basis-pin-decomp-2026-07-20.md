# FINDING (caiso-105): belly DA/RT price-basis wedge MEASURED (too small, wrong trend — the third and last storage-conduct family is closed with NO mechanism), pin-aware Q1 re-decomposition lands BOTH windows on the intertie supply curve; floor→$0-bid NOT filed (evidence contradicts efficacy); keeper UNCHANGED

**Session 2026-07-20 (CAISO-105 — executing the caiso-104 re-charters,
derive-first, measurement-only): keeper `2026-07-19-caiso-102-hourfix`
(NOT-YET, fail {C3c, C4, C5a(2024 CAVEAT)}) UNCHANGED; no mechanism armed, no
B-leg solved, nothing registered.** Baseline: fresh same-machine
`caiso102_repro_A` (this session, FINDING-caiso92b protocol) reproduces the
keeper ladder DIGIT-FOR-DIGIT — belly +6.0/+6.6/+4.3, evening −5.8/−4.9/−1.1,
overnight +0.8/−0.0/+1.4 (`_caiso92_report`). Instruments (committed):
`scripts/probes/_caiso105_da_rt_basis.py` (the wedge),
`scripts/probes/_caiso105_evening_q1_pin.py` (pin-aware Q1 decomposition,
evening + `--window belly`).

## 1. BELLY: the DA-vs-RT price-basis wedge is MEASURED and it cannot carry the residual — the storage-conduct enumeration is CLOSED

The caiso-104 §3b hypothesis: reality's charge clears in the DAM at DA prices
(DA-share 0.840/0.799/0.760) while the backcast scores RT λ, so the LP's
arbitrage-profitability requirement prices the charge against the wrong
basis. Measured (actual_lmp da/rt on the model clock; weights = storage-report
IFM / RTD charge mapped per model hour — annual totals reproduce
FINDING-caiso102 §1 exactly (IFM 4.190/7.137/9.816, RTD 3.989/8.024/12.223
TWh); model weights = the A-leg's fleet-battery charge):

| belly (hod 10-14) | 2023 | 2024 | 2025 |
|---|---|---|---|
| unweighted DA−RT | +3.9 | +0.9 | −0.5 |
| IFM-charge-weighted DA−RT | **+3.6** | **+1.1** | **−0.3** |
| RTD-charge-weighted DA−RT | +4.6 | +1.7 | +0.1 |
| model-charge-weighted DA−RT | +4.8 | +2.1 | +0.3 |
| belly residual (the target) | +6.0 | +6.6 | +4.3 |

Verdict: **the wedge has the wrong magnitude AND the wrong year-shape.** It
shrinks to ≈ 0 by 2025 (−0.3 to +0.3) while the residual persists (+4.3), and
is smallest in 2024 (+1.1) where the residual peaks (+6.6). DA sits slightly
ABOVE RT in the belly, not below — re-basing the LP's charge economics to DA
prices could not pull the model's belly λ down toward actuals. Per the
derive-first mandate: **NO mechanism, no ask.** With bid-cost
(caiso-100/101), allocation (caiso-104 M1) and now price-basis all measured
and closed, the belly residual is **not a storage-charge-conduct artifact**.
(Context: the model's own λ in its charge hours runs +8.2/+7.9/+5.2 above the
RT in the same hours — the residual seen through the charge lens; and the
evening DA−RT spread is large and positive, +16.4/+8.4/+3.7 unweighted — the
DA basis stays a useful reference for the evening lane, not the belly.)

## 2. EVENING: the pin-aware Q1 price-setter is the EQUALIZED IMPORT RUNG — the caiso-103 attribution is replaced

Method per the caiso-104 owner re-charter: interiority against the LP's OWN
bounds — `floors/<yr>_P1.npz` `min_gen` (RA-bridge floors included) as the
lower bound, `run_year(fleet_only=True)` `pmax × availability` as the cap —
never the unit-year p99 proxy. Q1 = deepest resid-quartile of evening (hod
17-21) hours:

| Q1 evening | 2023 | 2024 | 2025 |
|---|---|---|---|
| dw resid / model λ vs actual | −36.6 / 71.5 vs 105.9 | −25.5 / 41.8 vs 64.7 | −15.4 / 40.7 vs 55.9 |
| CA λ EQUALIZED to a WECC node (LP duals) | **76 %** | **100 %** | **97 %** |
| import interior share (interior MW) | 0.42 (811) | 0.12 (217) | 0.21 (431) |
| CC_REGULAR interior share (MW) | 0.44 (35) | 0.25 (16) | 0.25 (22) |
| battery envelope-BOUND | 36 % | 14 % | 8 % |
| Q1 λ below cheapest AVAILABLE CT offer (P0 mc) | +9.6 | +10.4 | +12.3 |

The evening margin is the **elastic hub-priced intertie supply**: CA λ is
hub-equalized in essentially all Q1 hours, thermal interior MW is negligible
(tens of MW), the battery envelope is NOT the binding rung (bound in only
8-36 % of Q1; discharge sits economically idle below the import-set λ), and
the margin never climbs the +10-12 $ to the CT rung because hub-priced import
depth fills the gap. Reality prices the same hours 8-40 $ ABOVE the measured
hubs (FINDING-caiso103 §6, unchanged and still the defect). The caiso-103 §3
"firm blocks price-setting / 1.7-2.5 GW withheld" attribution is definitively
replaced — the firm blocks are pinned (this session re-confirms
`dispatch == min_gen` at share 1.0000 in every year) and never marginal.

## 3. The floor→$0-bid replacement is NOT filed — the evidence contradicts its efficacy

The candidate (caiso-104 §1: measured conduct curtails firm flow in
negative-hub hours; bid constant $0) was to be filed as a new ask *if the
evidence supported it*. It does not:

- The Q1 evening price-setter is the economic import rung (§2), not the firm
  blocks; a $0-bid block that flows whenever λ > 0 changes no evening byte
  (it flows exactly as the floor forces today in every positive-λ hour).
- The model DOES force firm flow through negative own-zone λ (PNW block:
  2818/4165/2868 h, 2.9/7.8/4.6 TWh; DSW block: 97/211/504 h, 41/108/217
  GWh) — but in the PNW hours the CA-side λ is simultaneously HIGH (window
  means +19 to +64): the corridor is bound, the forced MWh displace economic
  tranche MWh at the node, and curtailing them is CA-price-inert. The only
  CA-visible slice is the DSW block's negative-CA-λ belly/pm hours (CA λ −4
  to −11; 51-282 h/yr, 20-90 GWh) — where curtailment would RAISE deep
  -negative belly hours toward zero, i.e. *worsen* the +6 belly over-price.
- Conclusion: the swap is conduct-faithful bookkeeping at the WECC nodes with
  ≈ zero-to-adverse CA λ effect. Filing it would un-promote part of caiso-77
  for no residual-relevant gain. It remains available if a later intertie
  redesign wants the conduct-correct bid form.

## 4. The belly Q1 (over-price) decomposition lands on the SAME locus: the intertie supply curve

Same instrument, `--window belly`, Q1 = deepest OVER-price quartile
(resid ≥ p75):

| Q1 belly | 2023 | 2024 | 2025 |
|---|---|---|---|
| dw resid / model λ vs actual | +29.2 / 48.7 vs 19.1 | +24.9 / 16.3 vs **−8.6** | +19.2 / 23.3 vs 3.8 |
| import interior share (interior MW) | **0.91 (2300)** | **0.78 (1809)** | **0.85 (2253)** |
| CA strictly ABOVE every WECC node | 57 % | 37 % | 49 % |
| battery discharge in Q1 | 0.00 GW | 0.00 GW | 0.00 GW |
| model net imports in Q1 (vs measured EIA-930) | **+3740 vs +1106** | **+3271 vs +487** | **+4215 vs +1837** |
| measured RT < 0 share in Q1 (vs model λ < 0) | 0.22 (0.05) | 0.56 (0.25) | 0.34 (0.18) |

In the hours the model over-prices the belly most, it is importing 3.3-4.2 GW
— 2.4-2.8 GW MORE than reality (all-belly over-import +2.2/+2.6/+2.2 GW) —
with an import tranche interior (price-setting at its hub-linked offer) in
78-91 % of those hours, while reality's surplus collapses the RT to ≤ 0 in
22-56 % of them. The belly λ is propped not by storage conduct (§1 closed the
last family) but by **hub-anchored import willingness**: the intertie tranches
keep flowing (and pricing) at positive hub-linked offers through hours whose
real market is in deep surplus (exporting/curtailing at ≤ $0).

**Unified diagnosis (both lanes, one locus):** the model's WECC intertie
supply is hub-anchored and too elastic in BOTH directions — in the belly it
imports too deep at hub prices (propping λ ABOVE the surplus-collapsed RT),
in the evening it supplies the margin at hub-equalized prices (holding λ
BELOW the hub-separated RT). The existing conditioning machinery (the WEIM
clean-transfer depth tranches are already condition-scoped: surplus-trigger /
overnight / daytime-trigger-OFF) points at the mechanism family: a
**measured, condition-derived evening/belly depth-and-direction structure**
(reality's belly conduct is export-leaning; its evening intertie margin is
exhausted/inelastic). Rule-1 guardrail: NO fitted throttle/haircut — any
depth must be a measured WEIM/e-tag quantity conditioned on an observable
state, regenerable for a forecast year (the ask design goes to the owner;
this session builds nothing).

## 5. Session artifacts + housekeeping

- Probes committed: `_caiso105_da_rt_basis.py`, `_caiso105_evening_q1_pin.py`
  (evening + belly modes). Bundle: gitignored `caiso102_repro_A` (fresh,
  ladder-verified; un-registered per the FINDING-caiso92b same-machine
  protocol — no dashboard registration is due since no calibration leg
  solved).
- DAM-outage intake (owner-directed lane, caiso-104 handoff §3): the
  RESOURCE ID → ORIS crosswalk stage is DONE and committed
  (`scripts/data/derive_caiso_dam_resource_crosswalk.py` +
  `data/raw/reference/caiso-dam-resource-crosswalk.csv`): 139 thermal
  resources → 88 plants; token matcher over the CAMPD CA universe with
  non-thermal/sub-15-MW exclusion, 10 hand-verified prefix pins resolved
  against EIA-860 (Carlsbad 59002, King City Peaking 55811, Gilroy Cogen
  10034 ≠ Gilroy Peaking 55810, Greenleaf 2 10349 = "Yuba City Energy
  Center", Carson Cogeneration 10169 ≠ SMUD Carson Ice-Gen 7527, City-of-Lodi
  GTs 7451 ≠ Lodi Energy Center, Midway Sunset Cogen 52169 ≠ Midway Peaking,
  AltaGas Ripon 50299 ≠ Ripon Generation Station), 6 adjudicated
  false-positive excludes (Diablo Canyon vs Canyon Power etc). Remaining
  stages (schema-first clean_io intake, rule-19 AMBIENT_DUE_TO_TEMP
  exclusion, unit-level DAM-before-CAMPD loader precedence, single-delta A/B)
  hand off to a dedicated session.
- #2546 ($5 fallback delete + re-gate): untouched, remains a dedicated
  -session item.
