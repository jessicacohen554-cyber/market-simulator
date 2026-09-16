# PRECOMMIT (pjm-h9) — is the LONG_RUN comparator biased by its gas-steam admixture?

**Session** `pjm-h9` · **ISO** PJM · **Date** 2026-09-16 · **Base** `origin/main` @ `af764ec8`
**ZERO LP, NO SHARD.** Rule 32 `[R-SHARD]` (a): the parent runs no LP, and this whole
measurement is a rule 29 `[R-SCREEN]` clause-0 phase 0 — there is no arm, no gate on a
residual, and nothing here can promote anything.
**PJM keeper `2026-09-11-pjm-d4-4-gasoutage`: CALIBRATED, 8/8, zero caveats — UNTOUCHED.**

Chartered by `docs/RESULT-pjm-h8-minload-measured-offer-screen-2026-09-16.md` §5 route **(b)**,
which the handoff names as the cheap test to run first. This document is written **before any
decisive number is computed** and carries the decision rule.

---

## 1. THE QUESTION, AS h8 LEFT IT

h8 installed PJM's own published offers on PJM coal's min-load rungs and the model's coal
fell to **12.70 TWh BELOW** what PJM's coal actually generated (control **+2.10** →
arm **−12.70** against 103.026 actual). Two readings were left unadjudicated. Route (b):

> the measured `LONG_RUN` segment is coal **plus** gas-steam (216 units, median
> `min_runtime` > 16 h), and gas-steam bids dearer, so a coal-only comparison against a
> blended ladder is biased HIGH — i.e. h8's `committed`-band correction may be an
> over-correction of a measurable size.

The already-measured magnitudes this bears on, from the committed h8 ladder
(`results/calibration/_pjm_h8_offer_ladder.json`, 2023, gas mean 3.2024 $/MMBtu):

| row | MW | share | model bid | measured (blended) | model/meas | gap |
|---|---:|---:|---:|---:|---:|---:|
| COAL `committed` | 12,550.3 | 0.434 | 6.117 | **8.488** | 0.721 | **+2.371** HR = **+7.59 $/MWh** |
| COAL `mustrun` | 14,062.2 | 0.178 | 1.411 | **7.856** | 0.180 | +6.445 HR = +20.64 $/MWh |

`committed` is the load-bearing row: h8's **G-5** measured that it produced **87.7 %** of the
arm's coal energy change while `mustrun` produced **8.4 %** (84.4 % of `mustrun` is floored by
`min_gen`). So the comparator's validity **at the `committed` row** is what route (b) turns on.

## 2. PHASE 0 KILLED THE METHOD THE HANDOFF ASSUMED — and that is the first result

The handoff specified *"a COAL-ONLY re-derive of `scripts/data/derive_pjm_offer_midcurve.py`"*.
**It cannot be done by fuel label. PJM's `energy_market_offers` feed publishes a MASKED
`unit_code` and no fuel column at all.** Measured this session on
`pjm_energy_offers_2023_07.parquet` (908,040 rows, 1,226 units):

* the 54 columns are `bid_datetime_*`, `unit_code`, `bid_slope_flag`, `mw1..mw20`,
  `bid1..bid20`, the cost/start parameters and the eco-min/max aggregates — **no fuel, no
  plant name, no EIA code**;
* every `unit_code` is an opaque base64 blob (`AAAADQYJAg8BLjUxMzM5MDA3` →
  `\x00\x00\x00\r\x06\t\x02\x0f\x01` + `.51339007`). The trailing digits are a stable PJM
  internal unit id with a plant-grouping structure (`.10502210 … .10502214`), **not** an EIA
  plant code and not crosswalkable to any fuel registry this repo carries.

This is why the whole derive family states its population rule as *"Segments are selected by
unit PHYSICS, never fuel labels"* (`derive_pjm_offer_surface.py` L15). **A coal-only ladder by
label is not obtainable from this source**, and no amount of re-fetching changes that. The
corpus is being re-fetched anyway (36 month-files, ~11 MB each, ~400 MB — an order of magnitude
under the README's "1–2 GB" estimate) because both measurements below need the raw offers.

## 3. M1 — THE MEASUREMENT THAT REPLACES IT: an EXACT mixture bound, no classifier at all

The ladder value at each (segment, year, net-load bin, within-unit share) is the
**capacity-weighted MEDIAN** of the implied-gas-HR distribution over the segment's unit-hours.
Write the blended cap-weighted CDF as a mixture of the coal and gas-steam sub-populations with
gas-steam capacity weight `w`:

```
F_blend = (1 - w) * F_coal + w * F_gas
```

If **all** gas-steam mass sits ABOVE the coal median (the worst case for route (b)'s own
hypothesis, i.e. the most favourable case for "the comparator is biased high"), then
`F_gas(m_coal) = 0` and

```
F_coal(m_coal) = F_blend(m_coal) / (1 - w) = 0.5   =>   m_coal = Q_blend(0.5 * (1 - w))
```

and symmetrically, if all gas-steam mass sits BELOW, `m_coal = Q_blend(0.5 * (1 + w))`. So

> **the coal-only ladder value lies in `[ Q_blend(0.5(1-w)) , Q_blend(0.5(1+w)) ]`, exactly,
> for ANY gas-steam distribution** — the bound assumes only that the admixture is one-sided,
> which is route (b)'s own premise.

`Q_blend` is computable from the **same histogram the frozen derive already builds**; the only
change is emitting the quantile function instead of only `p = 0.5`. **No unit is classified,
no fuel is inferred, and nothing is constructed by this probe.**

### 3.1 The admixture weight `w`

The independent estimate, already on record in the committed h8 ladder: the model's own PJM
fleet maps **11,525.5 MW of ST_GAS** and **49,371.7 MW of COAL** onto `LONG_RUN`, so

> **ŵ = 0.1893** (gas-steam = 18.9 % of the mapped LONG_RUN capacity).

Corroboration to be read from the corpus itself (reported, not chosen): the measured
`LONG_RUN` segment's own capacity (Σ per-unit median `avg_ecomax` over its 216 units) against
the model's 60,897 MW of mapped coal + gas-steam.

## 4. THE PRE-REGISTERED DECISION RULE — fixed here, before the numbers

Let `gap = measured_blend - model_bid` be h8's own correction at COAL `committed` (**+2.371**
implied-HR units, **+7.59 $/MWh**, 2023). Let `lo(w) = Q_blend(0.5(1-w))` be the worst-case
coal-only level. Define the **absorbed fraction**

```
phi(w) = (measured_blend - lo(w)) / gap
```

— the share of h8's correction that the admixture could account for, in its worst case.

> **(B-NO)   phi(ŵ) < 0.25** → the admixture cannot explain h8's correction. The comparator is
> exonerated and **route (a) — the missing PJM commitment mechanism — is the object.**
>
> **(B-YES)  phi(ŵ) > 0.75** → the comparator is the explanation; h8's arm was an
> over-correction and the remaining question is how much.
>
> **(B-PARTIAL)** otherwise → report `phi(ŵ)` as the measured partial contribution, and both
> readings survive with a measured split between them.

Also reported, as the form that needs no threshold at all: **`w½`** and **`w*`**, the admixture
weights at which `phi = 0.5` and `phi = 1.0`. If `w* > 1` the admixture can NEVER explain the
correction, whatever PJM's fleet mix is.

**This gates nothing and can promote nothing.** It is a rule 14 `[R-ACCURATE]` question about
the *accuracy of an input*, not a fit question: no residual appears anywhere in the rule above,
and the outcome cannot select a parameter. Whichever way it lands, **no value is proposed by
this session** — (B-YES) would require its own charter, its own footprint-named screen year and
an owner ruling, exactly as the handoff states.

**The same computation is run for the `mustrun` row and for 2024 and 2025**, reported in full;
the decision rule is read on **2023 `committed`**, the row and year h8 screened.

## 5. G-REPRO — the self-test that makes M1 trustworthy, pre-registered as a HARD STOP

My re-derived blended **median** must reproduce the committed frozen artifact
(`data/raw/_validation-source/pjm_offer_midcurve_condbinned.json`) **at every
(segment, year, bin, share) cell**, to the artifact's own 3-decimal rounding.

> **If it does not, the corpus I fetched is not the corpus the frozen artifact was built
> from, M1's quantiles are not trustworthy, and the session STOPS and reports that** — it does
> not "adjust" anything to make them agree. Rule 23 `[R-FROZEN-DERIVE]`: the frozen surface is
> reproduced, never re-tuned.

## 6. M2 — the gas-elasticity discriminator, CORROBORATIVE ONLY, with its own void condition

A *measured physical* discriminator that needs no label: **a gas-fired unit's offer tracks the
daily gas price; a coal unit's does not** (coal is contracted monthly/quarterly). Per masked
unit in `LONG_RUN`, regress its own min-load offer on the model's delivered-gas day series,
**demeaned within calendar month** so seasonality cannot manufacture the correlation, and read
the slope and R².

**VOID CONDITION, fixed before it is run.** The discriminator is validated on `CC_LIKE`, a
segment whose fuel is known from physics (PJM's CC fleet is gas):

> **`CC_LIKE` must read ≥ 80 % gas-linked by capacity. If it does not, the discriminator has
> no demonstrated power, M2 is DISCARDED, and only M1 stands.**

Second reported control: M2's implied gas-steam share of `LONG_RUN` against **ŵ = 0.189**.
M2 is a POINT estimate reported beside M1's bound; **M1 is the load-bearing measurement** and
the decision rule in §4 reads M1 alone. M2 cannot overturn a bound; it can only locate the
coal-only value inside one.

## 7. WHAT IS NOT TOUCHED

* The keeper, its recipe, its registration and PJM's `CALIBRATED` headline.
* The frozen surface `pjm_offer_midcurve_condbinned.json` — **read and reproduced, never
  rewritten** (rule 23). No re-derivation is committed by this session.
* `gas_mid` (3.40 live) and the standing rule-23 wart — untouched, still unchartered (h7 §4/§5).
* The registered `committed` multiplier 0.548, the `offer_curve_by_group` bands, the
  `pjm_offer_midcurve_*` scope fields — **nothing is proposed and nothing is swept**
  (rule 21 `[R-DOF]`: this session adds zero free parameters and zero `ScenarioConfig` fields).
* The h8 arm bundle at `b2b3d7d572ce56cd0fc25c4e08c8b46fce740be7`, and the open h7 promotion
  question — carried forward, nothing deleted (rule 31 `[R-RETAIN]`).
* The two pre-existing parity REDs (`caiso279_ablate_dswcouple_span`, `soco15_spp_arm`) — not
  PJM's.
* `data/raw/pjm-energy-offers/` is gitignored by the repo already and **stays uncommitted**
  (PJM DataMiner2 redistribution restriction, `docs/data-licensing.md` §4). Only multipliers
  and ratios are reported; **no PJM offer price is published by this session.**

## 8. RULES

Rule 1 `[R-STRUCT]` (§4 — the decision rule contains no residual and selects no parameter) ·
rule 13 `[R-MEASURED]` (the operand is PJM's own published offers; M2's discriminator is a
physical property of fuel contracting, not a fitted label) · rule 14 `[R-ACCURATE]` (the whole
question is the accuracy of a measured input; nothing is reverted either way) ·
rule 21 `[R-DOF]` (zero free parameters, zero proposed values, nothing swept) ·
rule 23 `[R-FROZEN-DERIVE]` (§5 — the frozen surface is reproduced as a hard stop, never
re-tuned; no derive output is committed) · rule 24 `[R-REGISTRY]` (no new field) ·
rule 25 `[R-ISO-SCOPE]` (PJM's own offers, PJM's own fleet) · rule 28 `[R-MECH-MATRIX]` (b)
(the PJM shard cell is stamped in this session) · rule 29 `[R-SCREEN]` (clause 0 — this is the
zero-LP phase 0 and no arm is screened) · rule 30(c) (no held-out year touches PJM's
determination) · rule 31 `[R-RETAIN]` (nothing deleted) · rule 32 `[R-SHARD]` (a) (the parent
runs no LP; no shard is launched because nothing here requires one).
