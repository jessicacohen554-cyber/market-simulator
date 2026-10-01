# DIAGNOSIS — ERCOT-138 Phase 1: the coal-vs-gas ranking above coal min-load is a **GAS-SIDE** defect

**Date** 2026-07-29 · **ISO** ERCOT · **Lane** ercot138-coal-gas-ranking ·
**Phase** 1 (measurement, **NO LP** — no matrix built, no year solved, no
`ScenarioConfig` field or solve path touched, no keeper file touched, no
holdout year read) ·
**Keeper under test** `2026-07-29-ercot137-coal-margin-measured`
(bundle `results/calibration/ercot137_margin_arm`) ·
**Probe** `scripts/probes/ercot138_coal_gas_ranking.py` ·
**Artifact** `results/calibration/ercot138_coal_gas_ranking.json` ·
**Routed here by** `docs/PRECOMMIT-ercot137-coal-margin-offer-2026-07-29.md` §3
(the pre-registered falsifier FIRED) and `FINDING-ercot117` §5.1.

---

## 0. The answer, in one line

**(b) — the GAS stack.** Against each class's *own* measured RT conduct, the
model's **CC committed/econ bands are $2.8–6.6 /MWh too DEAR** through the
crossing band while the model's **coal committed/econ bands sit within
−1.6 to +3.9** of the real coal fleet's. The gas leg carries **78–99 %** of
the coal-vs-gas ranking gap in 2024 and **50–78 %** at p25–p50 in 2025. The
band-uniform coal over-run that survived ERCOT-137 is therefore **not** a coal
mispricing — it is coal correctly winning a merit order in which gas has been
priced out from underneath it.

---

## 1. The question, and why it was answerable with no LP

ERCOT-137 put the coal min-load PRICE on a measured basis (net-margin form,
level 15.8807 / anchor 1.7387) and the fleet on the MEASURED availability
envelope, and the residual did **not** move: coal still over-loads actual in
every RT band ≥ $15 by ~7–13 pp, band-UNIFORMLY (G1 3/21, C1 coal
+6.2/+8.8/+8.6 TWh, C3a −35.2/−14.5/−12.1), displaced ~1:1 from gas
(`DIAGNOSIS-ercot134` §§6/10: corr(dCoal, dGas) −0.93..−0.97). A band-uniform
over-run at a *correct* curve bottom is a **ranking** defect — the order in
which the two classes' incremental MW enter merit.

A ranking is a property of the two OFFER CURVES, not of a dispatch, and both
sides were already on disk. The measured side is the 60-Day SCED disclosure's
`Submitted TPO` three-part offers, which carry COAL **and** the CC control on
one corpus with one ONLINE convention — ERCOT-123's loader, **imported, never
re-implemented**. The model side is the bid array at the LP seam, captured by
the ERCOT-135 abort-early replay pattern extended to every class.

### 1.1 One convention, stated before any number

Both sides on the **capability** convention, with the min-load block counted at
every price because it is not price-responsive on either side:

```
cap_share(p) = [ minload + offered_MW(<= p) ] / capability
inc_share(p) =              offered_MW(<= p) / (capability - minload)   <- THIS lane
```

| | minload | capability | offered |
|---|---|---|---|
| MEASURED | `LSL` | `HSL` | submitted TPO curve, clipped into `[LSL, HSL]` |
| MODEL | `min_gen[g,t]` (the floors) | `pmax[g] x availability[g,t]` | each tranche's remaining MW at its own bid |

`capability` is HSL on both sides, so the AS reservation sits inside the
denominator for both and no HASL/HSL rebasing enters.

### 1.2 Two things this probe does that ERCOT-135/136 did not

1. **MATCHED HOURS.** ERCOT-135/136 compared an *annual* model statistic to a
   *probe-day* measured one. Here the model bid is evaluated on EXACTLY the
   (delivery-day, hour) pairs each SCED subset covers (300/264/264/240 hours),
   so fuel-price and sigmoid seasonality cannot enter as a sampling artifact.
2. **BOTH CLASSES AT ONE SEAM.** The capture is at `run_energy_solve`, i.e.
   after `apply_coal_tranches` **and** `apply_gas_offer_margin`. Capturing at
   `apply_coal_tranches` alone (the ERCOT-135 seam) records coal post-reform but
   gas *pre*-reform, which is exactly the comparison that must not be made.

### 1.3 Footing check (§A) — PASSES exactly

The probe recomputes the committed ERCOT-136 §B2 `floored` grid (`supply(p) =
clip(max{MW_k : price_k <= p}, LSL, HASL)` over `HASL`) on its own code. Max
absolute deviation across all 8 (year × family × class) rows and 5 price edges:
**4.8e-7**. This probe's measured half is demonstrably the same curve already
on the record.

---

## 2. THE MEASUREMENT — the matched-band bid comparison (§E)

Capacity-weighted quantiles of the price attached to a MW of **above-min-load**
capability. Denominator-free: it does not depend on how much capability either
side counts, so the ONLINE-restriction asymmetry declared in §5 cannot drive it.

### 2.1 2024 (both day families) — the decisive year

`$/MWh`, model = committed+econ bands:

| | p10 | p25 | **p50** | p75 |
|---|---|---|---|---|
| **COAL measured** (tail / control) | 9.75 / 10.41 | 17.47 / 17.91 | **20.44 / 20.82** | 22.28 / 22.76 |
| **COAL model** | 16.43 / 16.63 | 17.78 / 17.97 | **19.10 / 19.42** | 21.65 / 22.09 |
| **Δ coal** | +6.68 / +6.22 | +0.31 / +0.06 | **−1.34 / −1.40** | −0.63 / −0.67 |
| **CC measured** | 4.73 / 5.98 | 8.38 / 9.03 | **12.10 / 12.94** | 16.92 / 18.10 |
| **CC model** | 13.33 / 13.35 | 15.02 / 15.29 | **17.38 / 17.85** | 20.17 / 20.95 |
| **Δ CC** | +8.60 / +7.37 | +6.64 / +6.26 | **+5.28 / +4.91** | +3.25 / +2.85 |

### 2.2 The ranking, in dollars

```
spread(q)  = bid_q_COAL(q) - bid_q_CC(q)
spread_gap = spread_model - spread_measured = coal_leg - gas_leg
```

| year·family | q | spread **measured** | spread **model** | gap | coal_leg | gas_leg | **owner** | gas share |
|---|---|---|---|---|---|---|---|---|
| 2024 tail | p25 | **+9.09** | +2.75 | −6.34 | +0.31 | **+6.64** | GAS | **0.96** |
| 2024 tail | p50 | **+8.34** | +1.72 | −6.62 | −1.34 | **+5.28** | GAS | **0.80** |
| 2024 tail | p75 | +5.36 | +1.48 | −3.88 | −0.63 | **+3.25** | GAS | 0.84 |
| 2024 control | p25 | **+8.88** | +2.69 | −6.19 | +0.06 | **+6.26** | GAS | **0.99** |
| 2024 control | p50 | **+7.88** | +1.57 | −6.31 | −1.40 | **+4.91** | GAS | 0.78 |
| 2024 control | p75 | +4.66 | +1.15 | −3.51 | −0.67 | **+2.85** | GAS | 0.81 |
| 2025 control | p25 | −0.38 | −1.77 | −1.39 | +3.92 | **+5.31** | GAS | 0.58 |
| 2025 control | p50 | +0.68 | −1.92 | −2.60 | +1.01 | **+3.61** | GAS | 0.78 |
| 2025 tail | p25 | −1.33 | −1.90 | −0.57 | +3.86 | **+4.43** | GAS | 0.53 |
| 2025 tail | p50 | −1.29 | −1.32 | −0.03 | +2.49 | **+2.52** | GAS | 0.50 |

**Read the `spread_measured` column.** In 2024 the real ERCOT market prices its
median incremental coal MW **$7.9–8.3/MWh ABOVE** its median incremental CC MW.
The model compresses that to **$1.6–1.7**. In 2025 the real spread is ~0 and the
model runs it **negative** (coal cheaper than CC). Either way the model puts
coal ahead of gas relative to reality, and in every crossing-band cell the gas
leg is the larger one.

Direction is stable across all four subsets and both day families; the tail /
control split (the deliberate price-based day selection) is its own control and
never flips a verdict.

### 2.3 The same defect in quantity terms (§C `inc_share`)

Share of **above-min-load** MW offered at or below a price, 2024 tail:

| | ≤$10 | ≤$15 | ≤$20 | ≤$25 |
|---|---|---|---|---|
| **CC measured** | **0.345** | **0.647** | 0.805 | 0.866 |
| **CC model** | **0.009** | **0.231** | 0.690 | 0.858 |
| **gap** | **−33.6 pp** | **−41.6 pp** | −11.5 pp | −0.8 pp |
| **COAL measured** | 0.109 | 0.151 | 0.452 | 0.837 |
| **COAL model** | 0.000 | 0.070 | 0.626 | 0.914 |
| **gap** | −10.9 pp | −8.1 pp | **+17.4 pp** | +7.7 pp |

In the sub-$15 region where the crossing lives, the model is missing **~42 pp of
CC incremental supply** and only ~8 pp of coal's — and at $20 it has **+17 pp
too much coal**. That is the merit inversion, measured on quantity as well as
price.

### 2.4 SAME-PLANTS robustness (§H) — the verdict survives

The §E comparison is between two nominally-same classes that are not literally
the same units. §H re-runs it restricted to the EIA plant codes the committed
`ercot-dam-plant-crosswalk.csv` accepts on **both** sides (coal 49–54 % of
measured HSL / 4 plants; CC 21–23 % / 12 plants):

| year·family | p10 | p25 | p50 | p75 | owner p10–p75 |
|---|---|---|---|---|---|
| 2024 tail — coal_leg / gas_leg | −2.22 / **+6.21** | −2.79 / **+5.99** | −2.52 / **+6.19** | −1.00 / **+6.14** | **GAS ×4** |
| 2024 control | −2.28 / **+6.28** | −2.73 / **+6.22** | −2.23 / **+6.04** | −0.50 / **+5.55** | **GAS ×4** |
| 2025 control | −1.80 / **+6.31** | −1.58 / **+4.00** | +1.21 / **+4.55** | +3.20 / +2.86 | GAS ×3, COAL ×1 |
| 2025 tail | −1.55 / **+5.93** | −1.21 / **+3.25** | +2.20 / **+3.28** | +4.29 / −0.52 | GAS ×3, COAL ×1 |

On **identical plants**, 2024 is a flat **+$6/MWh CC overpricing** at every
quantile p10–p75, with coal running ~$1–2.8 *cheap*. The "different fleets"
objection is dead.

### 2.5 WHICH gas mechanism (§J) — not the margin form, the band multipliers

| 2024 CC committed+econ | value |
|---|---|
| bid p50 | 17.38 |
| pre-margin-form bid p50 | 17.22 |
| **`gas_offer_net_revenue_margin` delta, p25 / p50 / p75** | **0.00 / 0.00 / +0.11** |
| offer heat rate (cap-wtd) | 7.610 |
| physical heat rate (cap-wtd) | 6.915 |
| **offer / physical** | **1.101** |

Two things follow, and they are the Phase-2-relevant distinction:

1. **The margin form is NOT the owner.** It changes the CC committed/econ bid by
   $0.00 at p50. Re-identifying `gas_offer_margin_anchor`/level would move
   nothing here — that lever is inert on this band.
2. **The band multipliers are.** `offer_curve_by_group['CC_REGULAR']` prices
   these bands at **1.101 × physical heat rate** (offer `committed` 0.998 /
   `econ_low` 0.723 / `econ_high` 1.324 against physical 1.006 / 0.825 / 0.95).
   At 2024's $2.213/MMBtu delivered gas that markup is **~$1.54/MWh** — real,
   but only ~29 % of the ~$5.3 gap.

**The remaining ~71 % is structural, and it is the finding of this section.**
The model's CC physical SRMC at HR 6.915 and $2.213 gas is ~$15.3/MWh before
VOM, while the real CC fleet's **median** incremental MW is offered at
**$12.10** and its p25 at **$8.38**. The real ERCOT CC fleet offers a large
share of its above-LSL incremental energy **below its own fuel cost** — the
committed-unit economics that keep a synchronised CC from being backed to LSL.
**The model has no mechanism that can produce a below-cost CC incremental
offer at all**: its cheapest CC band, `econ_low` at 0.723×, is a *heat-rate*
discount on a positive-cost curve and bottoms out at $13.3 (p10).

This is the exact gas-side analogue of the defect ERCOT-136/137 just closed on
coal — where the model's fitted $4.50 take-or-pay tranche *was* its below-cost
committed block, and was replaced by a MEASURED level. Coal has such a
mechanism and it is now measured. **Gas does not have one.**

---

## 3. What this CONFIRMS from the record, and what is new

**Confirms** (independently, on a different instrument): `FINDING-ercot117`
§1.1(3) — "the model's CC supply is displaced dear in the crossing band, every
year" — measured there from the **DAM** disclosure at ≤$15 (model 1.8/4.6/0.4 GW
vs measured committed 12.5/14.3/15.1 GW). This probe reproduces the same
direction and a compatible magnitude on the **RT (SCED TPO)** instrument, which
ERCOT-136 established as the admissible one for ERCOT offer conduct.

**New:**

1. The defect is **sized in $/MWh per class against each class's own conduct**,
   so it is attributable rather than inferred: gas +2.8..+6.6, coal −1.6..+3.9.
2. It is **not the gas margin form** (§J: $0.00 delta at p50) — which ERCOT-118
   / ERCOT-119 could not have shown, since both predate the margin form's ERCOT
   arming and both moved the DAM *multipliers*, not this band's markup.
3. The residual is **a missing below-cost committed-CC offer**, not a level
   error — the model's whole CC curve starts above its own physical SRMC.
4. The CC class **passes the same RT-instrument licensing test coal passed**
   (ERCOT-136 §A, committed): CC offers **95.3–98.5 %** of RT-dispatchable
   headroom into SCED, price-taking bucket 0.008–0.035, residual 0.006–0.015.
   The "a near-zero/whatever bid is faithful" escape does not apply to CC either.

---

## 4. Rule 19 `[R-ONE-MECH]` — what already prices each class above min-load

Enumerated from the keeper's own `run_config.json` (§G), because any Phase-2
mechanism must **replace or reconcile**, never stack:

| class | band | mechanism | status |
|---|---|---|---|
| COAL | committed+econ | PRB / lignite supply passthrough sigmoids (floors 0.76 / 0.675, tiered) | ARMED |
| COAL | econ | `coal_econ_marginal_hr_bound` (ERCOT-115) | ARMED |
| COAL | min-load | `coal_offer_net_revenue_margin` (15.8807 / 1.7387) | ARMED — **CLOSED lane** |
| COAL | min-load | `ercot_coal_min_config_floor` + `coal_mustrun_per_plant` | ARMED (floors, not pricing) |
| CC | committed+econ | `offer_curve_by_group['CC_REGULAR']` band multipliers | ARMED — **§J says this one owns the level** |
| CC | committed+econ | `gas_offer_net_revenue_margin` (anchor 2.2494) | ARMED — **§J says INERT on this band** |
| CC | econ (P1 only) | `ercot_offer_surface_cleared_share` (+`_rt`, mode `replace`) | ARMED |
| CC | peak (P1 only) | `ercot_offer_surface_conditional` | ARMED |
| CC | commitment | `ercot_gas_commitment_bridge` @ `min_load_frac` 0.574 | ARMED (floor, not pricing) |

Note the P1-only surfaces make gas **dearer still**: including them (`p1`
variant) moves the CC p75/p90 to +7.12/+36.01 in 2024 tail. They are ARMED in
the keeper, so the scored P1 gas curve is dearer than §2.1's base-cost table
shows — the verdict is conservative as reported.

---

## 5. Honest limits, stated with the result

1. **The measured corpus is probe days, not a span** — 79 delivery days across
   2024–2025 only, hours 11–22 for three of four subsets, December-2025
   intervals dropped by the shared loader. Every number is split by day family;
   nothing here is an annual statistic. **No 2023 SCED exists on disk**, so 2023
   has no measured counterpart and is not scored.
2. **MEASURED is ONLINE-restricted; the MODEL side is not.** This moves the
   §B/§C *capability shares* (measured min-load is 0.42–0.58 of capability, the
   model's 0.00–0.18) and is why the verdict rests on §E/§H, which are
   denominator-free. Mitigating evidence: measured online capability is 87.5 %
   (coal) and 96.2 % (CC) of the model's available capability on these hours, so
   the asymmetry is small **and nearly equal between the two classes**.
3. **The gas commitment bridge's `min_gen` floor is injected inside
   `run_energy_solve`**, i.e. after this capture — so the model's CC min-load
   share here is its pre-bridge value. The bridge moves `min_gen`, never `mc`,
   so no bid number in §E/§H/§J is affected.
4. **The P1 startup amortization is absent from every model bid here** (it needs
   P0 run lengths, i.e. an LP). It is non-negative and lands overwhelmingly on
   gas cycling classes, so omitting it can only **understate** how dear the
   model's gas is. Direction-safe.
5. **§H coverage is bounded** (coal ~50 % of measured HSL, CC ~22 %) and its p90
   column is noisy at 12 plants. It is a sign check on §E, not a
   coverage-weighted magnitude.
6. **A second, separable defect is visible and is NOT this lane's target.** At
   p90 the model's **coal** curve runs $9.6–15.5/MWh UNDER measured in all four
   subsets (−10.21 / −9.60 / −11.59 / −15.49) — it tops out too low. CC's p90 is
   not the same story and is reported as it falls: **+5.13 / +4.93 in 2024**
   (still dear) but **−0.12 / −8.02 in 2025**. So the top-decile finding is
   coal-owned and year-dependent on gas, and it belongs to the near-tail / C3c
   lane already attributed by ERCOT-99/101/107/108 and ERCOT-119. Reported here,
   left there — and note it runs OPPOSITE to this lane's crossing-band finding,
   which is why a single level lever on either class cannot serve both.

---

## 6. What this LICENSES, and what it explicitly does NOT

**Licensed** — a **gas-side** Phase 2 targeting the CC committed/econ offer
SHAPE, identified from ERCOT's own SCED TPO conduct, on the ERCOT-136→137
template that this lane has now validated end-to-end:

* the instrument is admissible for CC on the same grounds it was for coal
  (§3.4 — 95.3–98.5 % RT offer coverage);
* the identification is a **measured** distribution, not a residual fit
  (rules 13/23);
* it is **rule-19 replace-not-stack**: the band multipliers are the single
  mechanism that sets this level (§J proves the margin form is inert here), so
  a re-identification REPLACES them rather than adding a fourth surface;
* it is **rule-25 clean**: ERCOT-identified from ERCOT data, no transfer.

**NOT licensed by this document, and explicitly refused:**

* **Any coal-side lever.** The coal legs are −1.6..+3.9 in the crossing band and
  coal's enumeration is exhausted (ERCOT-122…137). Touching coal to close a gas
  residual is precisely the compensating-error pattern rules 1/14 forbid.
* **Re-testing `ercot_offer_hrmult_ep_rebasis` / `_bands`.** ERCOT-118 and
  ERCOT-119 are ORDINARY REJECTIONS on C3c (72→49, 13→3, identically in both),
  and ERCOT-119 proved the econ legs own both the gain and the tail drain. Rule
  26(a): not re-tested without new evidence. §J supplies evidence about a
  *different* object (this band's markup vs its multipliers on the RT
  instrument), which is why the successor is a new identification and not a
  re-run of those arms — and any Phase 2 must carry ERCOT-119's C3c gate as a
  pre-registered failure mode, because deflating the CC curve is exactly what
  drained the sub-$200 tail there.
* **`measured_ct_heat_rates` on this defect.** §J locates only ~29 % of the gap
  in the offer/physical heat-rate markup, and the model's physical CC HR (6.915)
  is already physically reasonable. A heat-rate lever cannot reach a below-cost
  offer.
* **Any residual-tuned adder** (rule 13), any re-tuning around the retired
  availability estimate (rule 14 — it is retired), and any change to
  `coal_tranche_1_frac` (measured min-load 0.425–0.457 > model 0.30; rule 19).

**No mechanism is proposed here and no Phase 2 is started.** Phase 2 requires
its own pushed pre-commit before any solve, a full-span `--year 2023 2024 2025`
single bundle (rule 16), and registration keeper-or-rejected with the matrix
cell stamped in the same session (rules 15/26b).

---

## 7. Open owner rulings carried forward (NOT decided here)

1. **Carried over from ERCOT-137 §7, still open:** whether the retired
   `coal_tranche_1_fuel_passthrough` pricing path and the legacy non-CAMPD
   `split_coal_tranches` `_t1/_t2/_t3` path are **DELETED outright (rule 26
   `[R-DELETE]`) or left inert.** The margin form makes the CAMPD path
   independent of them; the legacy path still consumes the fields for
   non-CAMPD fleets.
2. **New, surfaced by §J:** `ercot_offer_hrmult_ep_rebasis` and
   `ercot_offer_hrmult_ep_rebasis_bands` are solve-affecting `ScenarioConfig`
   fields with **no row in the cross-ISO mechanism matrix** — a rule-26(c) gap
   predating this lane. Recorded, not fixed here (this session adds no
   `ScenarioConfig` field).
3. Whether to charter the Phase 2 in §6 at all, and if so whether the CC
   committed/econ re-identification should be a level re-derivation or a
   below-cost committed-block mechanism (the coal `_mustrun` analogue).

---

## 8. Scope

Holdout years (2022 / 2019 / ≤2021 / H1-2026) untouched (rule 22). No LP built,
no year solved, nothing registered, no keeper file touched, no `ScenarioConfig`
field added or changed, no solve path touched. No new GitHub Actions workflow.
ERCOT-scoped only (rule 25). Every CLOSED lane honoured: coal min-load PRICE
(ercot137), coal offer REACH (ercot123 §7.1), coal offer LEVEL rebasis
(ercot132 leg B), pooled `econ_high` 2.856 (ercot122 §5.2), F923 delivered-coal
price as a price question (ercot135 §3), coal ramp trajectory (ercot127/132),
availability ENVELOPE layer (ercot126), min-config upper bound (ercot130),
plant-grain fractional min-load floor (ercot127 §3), unit-grain commitment STATE
(ercot128), age/temp derates (ercot121 §1a), EP-rebasis C3c (ercot119),
`ercot_zonal_gas_basis`, West/Panhandle topology split.
