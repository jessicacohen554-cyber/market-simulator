# FINDING — nyiso-169: the zonal-gradient half is FOUR consistently-signed link terms that CANCEL, its content is congestion, and NO binding constraint carries it — ≥98.3 % of NYISO's measured congestion forms with every posted interface off its limit

**Date:** 2026-09-01 · **Lane:** NYISO calibration · **Shorthand:** nyiso-169
**Object:** the **zonal-gradient component** of NYISO's C3a price-response
deficit — nyiso-168 §5's `+0.96 / −1.49 / −2.32 $/MWh` (2023/24/25), the one
leg that finding measured but did not decompose — on keeper
`2026-08-30-nyiso-159-loss-surface`, determination **NOT-YET on {C3a-2025
−11.5 %, C3c}**.
**ZERO SOLVE.** No LP ran. No `ScenarioConfig` field, mechanism, keeper, shard
verdict, marker or determination changed. **Rule 22 `[R-HOLDOUT]`: every year
read is 2023, 2024 or 2025** — no out-of-training year was solved, scored,
registered or read; no marker was requested; the spend freeze is untouched.
**Probe of record:** `scripts/probes/nyiso169_congestion_gradient_anatomy.py`
→ `results/calibration/_nyiso169_congestion_gradient_anatomy.json`, **committed
before it was run** (`bccf58f4`) so its §F decision rule is verifiably
pre-registered.
**The three predecessor probes were re-run first.** `nyiso167_price_gain_attribution`
and `nyiso168_gap_anatomy` reproduce **bit-identically**;
`nyiso168_reserve_supply_slack` reproduces to **1e-15 relative** (float
summation order off a locally-regenerated `fleet` clean partition —
`30447.499999999996` vs `30447.5`; every cover ratio and every verdict
identical to 13 significant figures, so the committed record was left
unmodified). This session measures the same object.

---

## 0. The result in one paragraph

**No binding constraint carries the gradient deficit — in any single year, let
alone all three — and the reason is not that the constraints are the wrong
ones.** NYISO's posted cutsets sit within 50 MW of their limits in **0.0–0.8 %
of hours** (CENTRAL EAST - VC 0.75/0.13/0.21 %; TOTAL EAST, UPNY CONED,
SPR/DUN-SOUTH **0.00 %**), while NYISO's own posted congestion component is
non-zero in **4–64 %** of them; **at most 1.7 % of each link's annual mean
congestion arises in a posted-binding hour, and on three of the four links it is
0.00 % in every year.** The congestion is therefore real, large, general — and
**sub-interface**, invisible to a five-zone aggregate-TTC representation by
construction. Per the brief's own instruction, that is a **STOP**. Two things
are corrected on the way there. First, **the gradient component is not an
inconsistently-signed residual**: decomposed exactly along the model's radial
chain (identity error `0.00e+00` in all three years) it is **four per-link terms
each of consistent sign across 2023–2025 that partially cancel** — the aggregate
sign flip is a *cancellation artifact*, and two links clear the pre-registered
carry test with **opposing** signs. Second, the missing content is **congestion,
not losses**: congestion is 90–93 % of the Long Island premium and 59–87 % of
the Central-East spread, against a loss half the keeper already prices from the
measured surface.

---

## 1. What was measured, and off what

| input | path | role |
|---|---|---|
| keeper hourlies | `results/calibration/nyiso159_lossarm_B/hourly/system_<year>.parquet` | the keeper's own P1 per-zone price and demand (rule 15's stated purpose: read the keeper, do not replay it) |
| zonal actual | `data/raw/_validation-source/actual_lmp.json` → `NYISO.<year>.zones` | the **same** per-model-zone annual DA input nyiso-168 §5 used, so §A reproduces its statistic exactly |
| **posted LBMP components** | `data/raw/lmp-data/NYISO/{YYYYMM}01{damlbmp,realtime}_zone_csv.zip` | NYISO MIS per-zone **LBMP, MCL and MCC**, DA and RT, all 36 months |
| measured interface flows | `data/clean/nyiso-interface-flows/NYISO/nyiso-interface-flows_<year>.parquet` | hourly flow + posted positive/negative limit on all 18 NYISO interfaces |
| model topology | `src/market_sim/config/iso_configs.py` | the four-link radial chain and its TTCs |

**On the component intake.** The RT and DA monthly archives are *regenerable*
inputs the repo tracks only in part (21 RT months committed, the rest
gitignored — `data/raw/lmp-data/README.md`); all 36 months of both products were
re-fetched with the frozen `scripts/data/fetch_nyiso_zonal_lmp.py` from NYISO's
public MIS tree. Under rule 22 as clarified 2026-08-06, **data intake needs no
authorization** — what is held out is the *score*, and no out-of-training year
was fetched, read or scored. Under rule 13 `[R-MEASURED]` a posted price is a
measured **outcome**: it is used here purely as evidence and **is not, and does
not become, an LP input**.

**Conventions are the repo's own, not re-implemented.** The probe imports
`_localize_ordered`, `_std_hour_index`, `NYISO_ZONE_MAP` and `NYISO_INTERNAL`
from `scripts/data/derive_actual_lmp.py` and applies the frozen contract
unchanged: RT 5-minute stamps are interval-**ending** (shifted back one second
before the hour floor), DA hourly stamps interval-**beginning**, the DST
fall-back hour disambiguated by row order, and a model zone is the **simple
mean** of its constituent A–K zones.

**Basis.** §A/§B are on the **DA annual** basis, because that is the input
nyiso-168 §5 defined the object on. §C reports **both** bases. §D/§E/§G are on
the DA basis. RT is shown where it differs materially; it never changes a sign.

## 2. Premise correction — the gradient is four consistently-signed terms that CANCEL

The model's NYISO topology is a **radial chain**,
`Upstate_West → Capital_Hudson → Lower_Hudson → NYC → Long_Island`, so a zone's
spread against the reference is the sum of the link spreads along it, and
nyiso-168's statistic re-associates **exactly**:

> `grad = Σ_z w_z·[(model_z − model_ref) − (actual_z − actual_ref)]`
> `     = Σ_ℓ W_ℓ·d_ℓ`,  `W_ℓ = Σ_{z ≥ ℓ} w_z`,  `d_ℓ = model spread_ℓ − actual spread_ℓ`

This is an identity, and the probe asserts it rather than assuming it:
**|reconstructed − reported| = `0.00e+00` in all three years.**

| link | `W` | 2023 model/actual → **grad** | 2024 model/actual → **grad** | 2025 model/actual → **grad** |
|---|---|---|---|---|
| Upstate_West→Capital_Hudson | 0.66 | +10.35 / +10.30 → **+0.032** | +2.94 / +4.54 → **−1.047** | +5.30 / +9.26 → **−2.605** |
| Capital_Hudson→Lower_Hudson | 0.52 | +0.59 / **−2.80** → **+1.746** | +0.69 / −0.08 → **+0.396** | +0.80 / **−2.16** → **+1.534** |
| Lower_Hudson→NYC | 0.46 | +0.29 / +0.37 → **−0.037** | +0.46 / +1.35 → **−0.412** | +0.55 / +2.42 → **−0.866** |
| NYC→Long_Island | 0.13 | +0.90 / **+6.82** → **−0.780** | +0.70 / +3.99 → **−0.432** | +0.52 / +3.46 → **−0.387** |
| **total** | | **+0.96** | **−1.49** | **−2.32** |

**Every one of the four is consistently signed across 2023–2025** (treating
`|v| ≤ 0.05` as noise). The aggregate's sign flip is produced entirely by the
**cancellation** of a positive `Capital_Hudson→Lower_Hudson` term against three
negative ones — in 2023 the +1.75 outweighs the −0.82 sum of the others; by 2025
the −3.86 sum outweighs the +1.53. **nyiso-168's "the gradient component is not
even consistently signed" is therefore true of the aggregate and false of every
component.** A successor should not read the aggregate sign as evidence of
absence.

Under the **pre-registered** §F rule — same sign in all three years *and*
smallest absolute contribution ≥ $0.25/MWh (≈10 % of 2025's gradient
component) — **two links carry**:

* **`Capital_Hudson→Lower_Hudson`** (+1.75 / +0.40 / +1.53). The model prices
  Lower_Hudson **above** Capital_Hudson in every year and every load band; the
  market prices it **below** in two of three years and in every band above the
  median. This is a **sign inversion**, not a magnitude error.
* **`NYC→Long_Island`** (−0.78 / −0.43 / −0.39). The model reproduces only
  **13 % / 18 % / 15 %** of the measured Long Island premium.

They pull in **opposite** directions, so neither is "the" object, and
`Upstate_West→Capital_Hudson` — the **largest single term in 2025** (−2.605,
larger than the whole gradient component) — fails the carry test only because
2023's contribution is genuinely ≈ 0 (model +10.35 vs actual +10.30, a $0.05
match).

## 3. Composition — it is congestion, not losses

NYISO posts `LBMP_z = E + MCL_z − MCC_z` (MST §17.1 / Manual 12: losses add,
congestion subtracts), so a link's actual spread splits **exactly** into a loss
half and a congestion half. **Gate: the recovered reference energy price
`E = LBMP − MCL + MCC` is uniform across the eleven internal zones to a maximum
of $0.02 (DA) / $0.01 (RT) against a $0.05 publication-rounding tolerance, in
every year** — so the decomposition is usable as published.

| link | 2023 loss / **cong** (share) | 2024 loss / **cong** (share) | 2025 loss / **cong** (share) |
|---|---|---|---|
| Upstate_West→Capital_Hudson | +1.32 / **+8.98** (87 %) | +1.85 / **+2.69** (59 %) | +3.22 / **+6.04** (65 %) |
| Capital_Hudson→Lower_Hudson | +0.43 / **−3.23** | +0.72 / **−0.80** | +0.94 / **−3.10** |
| Lower_Hudson→NYC | +0.23 / **+0.14** (38 %) | +0.38 / **+0.97** (72 %) | +0.55 / **+1.88** (77 %) |
| NYC→Long_Island | +0.49 / **+6.33** (93 %) | +0.38 / **+3.62** (91 %) | +0.35 / **+3.11** (90 %) |

Two readings. **The loss half is small and the keeper already prices it** — that
is the armed `nyiso_zonal_loss_surface` (`K`), and this measurement is
independent confirmation that it is a real, correctly-sized physical component
rather than a residual sink. **The congestion half is the object**, and on
`Capital_Hudson→Lower_Hudson` it is the *whole* of the inversion: the loss
component is positive on that link in every year, so the negative measured
spread is congestion overcoming losses.

## 4. THE DECISIVE MEASUREMENT — no binding constraint carries any of it

The question the brief poses is not whether congestion exists but whether a
**binding constraint** produces it. Measured directly, per link, per year:

| year | link | actual congested (>$1) | model separated (>$1) | posted interface binding | **share of annual congestion from posted-binding hours** |
|---|---|---|---|---|---|
| 2023 | UW→CH | 55.0 % | 98.7 % | CE-VC **0.75 %** | **1.65 %** |
| 2023 | CH→LH | 46.1 % | 1.9 % | UPNY CONED **0.00 %** | **0.00 %** |
| 2023 | LH→NYC | 4.1 % | 0.3 % | SPR/DUN-S **0.03 %** | **0.00 %** |
| 2023 | NYC→LI | 64.1 % | 8.1 % | *no posted cutset* | — |
| 2024 | UW→CH | 15.5 % | 84.1 % | CE-VC **0.13 %** | **1.73 %** |
| 2024 | CH→LH | 10.0 % | 8.5 % | UPNY CONED **0.00 %** | **0.00 %** |
| 2024 | LH→NYC | 16.3 % | 3.6 % | SPR/DUN-S **0.00 %** | **0.00 %** |
| 2024 | NYC→LI | 48.9 % | 10.0 % | *no posted cutset* | — |
| 2025 | UW→CH | 26.3 % | 82.0 % | CE-VC **0.21 %** | **0.98 %** |
| 2025 | CH→LH | 20.2 % | 30.3 % | UPNY CONED **0.00 %** | **0.00 %** |
| 2025 | LH→NYC | 25.7 % | 3.5 % | SPR/DUN-S **0.00 %** | **0.00 %** |
| 2025 | NYC→LI | 46.5 % | 11.8 % | *no posted cutset* | — |

`TOTAL EAST` binds in **0.00 %** of hours in every year and contributes
**0.00 %** on every link.

**Read it three ways.**

1. **≥98.3 % of NYISO's measured congestion forms in hours when no posted
   interface is at its limit.** The binding hours do carry higher congestion
   (CENTRAL EAST: $19.62 / $37.15 / $28.73 when binding vs $8.89 / $2.65 / $5.99
   otherwise), but at 0.1–0.8 % of hours they are arithmetically negligible in
   the annual mean — the conditional mean barely moves ($8.98 all-hours vs
   $8.89 non-binding).
2. **The answer to the brief's question is therefore NO, and emphatically so.**
   No single binding constraint carries the gradient deficit in all three years,
   because **no posted constraint carries a material share of it in any year.**
   The instruction is to say so and stop, and that is this session's verdict.
3. **This independently reproduces and strengthens nyiso-109.** That session
   refused `measured_interface_limits` ex ante (cell `G`) on the observation
   that the posted limits do not bind — measuring CENTRAL EAST at
   0.8 / 0.1 / 0.2 %, which this probe reproduces to the digit off a different
   instrument. What is **added** is the stronger statement nyiso-109 could not
   make: the congestion is not merely *unexplained* by the posted limits, it is
   **statistically invariant to them**. A mechanism keyed to posted-limit
   binding cannot reach it, and no amount of re-estimating the limits changes
   that.

## 5. Why the model's own mechanism cannot reach it, and which hours it misses

A chain link's LP dual is non-zero only when that link's own flow is at its TTC,
so the model can price congestion **only** in the hours it separates. The
separation columns above show the mismatch is not a matter of degree:
`Upstate_West→Capital_Hudson` separates in **82–99 %** of hours against a market
congested in **15–55 %**, while the three downstream links separate in
**0.3–30 %** against **4–64 %**. **The model over-separates the link it
under-prices and under-separates the links it misses** — the mechanism is the
wrong *shape*, not the wrong *number*, which is why re-estimating a TTC does
nothing. (`nyiso_central_east_measured_ttc` is `K` and its measured limit is
correct under rule 14 `[R-ACCURATE]`; nothing here disturbs it.)

Where the deficit lives, by model-load band (DA basis, $/MWh of link spread —
`model / actual / deficit`):

| band | n | UW→CH 2025 | CH→LH 2025 | NYC→LI 2025 |
|---|---|---|---|---|
| 0–50 | 4,380 | +5.09 / +3.02 / **+2.06** | +0.66 / +0.18 / +0.48 | +0.16 / +0.57 / −0.41 |
| 50–80 | 2,628 | +5.57 / +11.11 / **−5.54** | +0.71 / −2.86 / +3.57 | +0.68 / +4.73 / −4.05 |
| 80–90 | 876 | +6.64 / +23.29 / **−16.65** | +0.84 / −7.54 / +8.38 | +1.32 / +8.07 / −6.75 |
| 90–95 | 438 | +5.86 / +19.03 / **−13.18** | +1.35 / −3.68 / +5.03 | +1.59 / +1.68 / −0.09 |
| 95–99 | 350 | +2.28 / +10.84 / **−8.55** | +1.67 / −3.09 / +4.76 | +0.13 / +12.25 / −12.12 |
| 99–100 | 88 | +3.65 / +69.59 / **−65.94** | +3.69 / −32.68 / +36.36 | +2.07 / +37.04 / −34.97 |

The same shape holds in 2023 and 2024 at smaller magnitude. **The gradient
deficit is a high-load object** — negligible or reversed below the median,
opening from the 50th percentile and widest at the top — which is the *same*
band structure nyiso-168 §2 measured for the level component. And the market's
high-load price surface is **non-monotone along the model's chain**: at the
80–90th percentile in 2025 the market prices Capital_Hudson **$23.29 above**
Upstate_West and **$7.54 above** Lower_Hudson, i.e. Capital is a local price
*peak*, while the model's chain is monotone increasing in every band of every
year. A four-link radial chain with aggregate TTCs cannot produce that surface
regardless of how its limits are set.

**One hypothesis checked and closed on the way:** that the inversion is
misplaced imports. It is not — the keeper already attaches its external ties
per landing zone through `nyiso_seam_par_attribution` (`K`), which computes all
four border links (`NYISO_external→{Upstate_West, Capital_Hudson, NYC,
Long_Island}`) from measured MIS P-32 rows. The geography is already right.

## 6. What a perfect close would even buy

Stated so the expected value is arithmetic rather than adjective. Closing the
**entire** gradient component — an unattainable upper bound, since §4 shows no
admissible mechanism reaches it — moves the load-weighted DA-basis error to:

| year | model LW | actual LW (DA) | error | **error, gradient perfectly closed** |
|---|---|---|---|---|
| 2023 | $31.73 | $32.42 | −2.13 % | **−5.10 %** |
| 2024 | $36.28 | $37.70 | −3.79 % | **+0.18 %** |
| 2025 | $55.84 | $62.44 | −10.56 % | **−6.84 %** |

*(DA basis; C3a gates on the RT load-weighted actual, where 2025 reads −11.48 %.
The DA/RT difference is the expected one — nyiso-167 §2.1.)*

So even a perfect close **costs 2023 nearly three points** (−2.13 → −5.10 %),
because the model *over*-shoots that year's gradient. It is not a free win in
the direction C3a needs, and it leaves 2025's level half — the other 65 % —
entirely untouched.

## 7. Lines this session closes

* **CLOSED — "a binding transmission constraint carries the zonal-gradient
  deficit."** ≥98.3 % of the measured congestion forms with every posted
  interface off its limit; three of four links take **0.00 %** from
  posted-binding hours in every year. Do not re-open on a re-estimated limit.
* **CLOSED — the aggregate-TTC route in general**, not just the posted-limit
  variant. The model over-separates the link it under-prices and
  under-separates the links it misses; the mechanism's *shape* is wrong, so no
  setting of the limits reaches the object.
* **CLOSED — "the gradient component is inconsistently signed, therefore not a
  mechanism."** It is four consistently-signed terms that cancel. The premise is
  corrected; the conclusion (stop) survives it for a *different and stronger*
  reason.
* **CLOSED — misplaced imports as the `Capital_Hudson→Lower_Hudson` inversion.**
  The keeper already attaches ties per landing zone (`nyiso_seam_par_attribution`
  `K`).
* **CONFIRMED, verdict unmoved — `measured_interface_limits` = `G`.** nyiso-109's
  ex-ante refusal reproduced off an independent instrument and strengthened from
  "the limits do not bind" to "the congestion is invariant to whether they bind."
* **NOT OPENED — a zonal congestion adder.** Feeding NYISO's posted MCC back in
  to lift the model's zonal spreads is exactly the rule 13 `[R-MEASURED]`
  forbidden move: it is a measured *outcome*, it has no forward analogue, and it
  would make the fit measure plumbing. **No adder was built and none is
  proposed.** Equally, tightening a TTC below its measured value to force
  separation is the rule 1 `[R-STRUCT]` forbidden move — a steepener adopted
  because the residual wants one — and is refused here on that ground and not
  on its effect.

## 8. Honest expected value

**What is delivered.** A reproducible, zero-solve, pre-registered decomposition
that (a) proves the gradient component re-associates **exactly** into four
per-link terms and corrects nyiso-168's "not consistently signed" read — every
component is consistently signed, the aggregate flip is cancellation; (b) splits
each link's measured spread into loss and congestion halves off NYISO's own
posted components, gated on the published identity, and shows congestion is
59–93 % of it while the loss half the keeper already prices is small and real;
(c) answers the brief's question **NO** with the sharpest available construction
— ≥98.3 % of the congestion forms in non-binding hours; (d) generalises the kill
from posted limits to the aggregate-TTC mechanism class via the separation-share
mismatch; and (e) prices the upper bound of a perfect close, showing it would
cost 2023 three points.

**What is NOT delivered. No gate moves.** C3a-2025 is still −11.5 %, C3c still
fails, the determination is still **NOT-YET on {C3a-2025, C3c}**, and NYISO
still does not read CALIBRATED. **No solve ran**, so rule 15 registers nothing —
the dashboard is untouched **by design, not by omission** (brief §GUARDRAILS,
nyiso-152/168 precedent). No matrix cell verdict moves; one cell
(`measured_interface_limits`) takes added evidence for the verdict it already
holds. Phase (2) of the brief — pre-registering kills and a required move in the
0.7032 gain — is **not reached**, because phase (1) returned the stop condition
the brief itself specified.

**What could still be wrong.** §A/§B are annual-mean statistics on the DA basis
by construction (that is the basis nyiso-168 defined the object on), so the
per-link attribution is exact for the *annual* gradient and only indicative
hour-by-hour; §E carries the hourly structure but on a model-load ordering, not
a matched-hour join to the actual. The binding test uses a 50 MW proximity band
on NYISO's posted *positive* limit and one hourly sample per interface-hour;
a constraint enforced at a sub-hourly grain, or one whose posted limit is not
the binding security limit, would be under-counted — though the margin here
(≥98.3 %) is far too wide for that to reverse the verdict. The negative-limit
direction is not tested, and the `NYC→Long_Island` link has **no posted internal
cutset** in the flow record at all, so its 90–93 %-congestion premium is
characterised but not attributed to any named constraint. And the finding
establishes what does *not* produce the measured congestion without identifying
what does: "sub-interface nodal constraints" is an inference from the exclusion,
consistent with nyiso-109's own reading, not a positive identification.

**The honest read on the object.** After nyiso-167, nyiso-168 and this session,
the C3a deficit is fully partitioned and every partition is adjudicated. The
**level** half (65 % of 2025) is the price-response gain, whose remaining
explanation is markup or reserve-offer structure, both blocked on data this lane
cannot obtain (nyiso-168 §6.3). The **gradient** half (35 %) is congestion the
five-zone representation cannot form, and this session closes the last named
route to it. **The congestion half is a representation limit, not a missing
mechanism** — it would take a sub-zonal or nodal NYISO topology, which is a
program-level scope decision and not a lever. A successor should not expect to
close C3a-2025 from the current data set at the current grain, and the standing
$27.8–$56.0/MWh pass window nyiso-167 derived should be planned around rather
than solved away.

## 9. Evidence

* `results/calibration/_nyiso169_congestion_gradient_anatomy.json` +
  `scripts/probes/nyiso169_congestion_gradient_anatomy.py` — measurements A–E, G;
  the probe committed at `bccf58f4` **before** it was run.
* `results/calibration/_nyiso168_gap_anatomy.json` §F — the gradient/level split
  this session decomposes, reproduced bit-identically in §A.
* `docs/FINDING-nyiso168-supply-curve-slope-anatomy-2026-09-01.md` §5, §8 — the
  object handed forward and the seven lines it closed, none re-opened here.
* `docs/FINDING-nyiso167-c3a-price-response-gain-2026-09-01.md` §2 — the gain
  law and the C3a pass window §6 plans around.
* `results/calibration/_nyiso109_trough_offer_stack.json` +
  `results/calibration/FINDING-nyiso109-zonal-margin-anchor-2026-08-01.md` — the
  `measured_interface_limits` `G` this session reproduces and strengthens.
* `scripts/data/derive_nyiso_loss_surface.py` — the published component identity
  `LBMP = E + MCL − MCC` and the MCL half the keeper already prices.
* `scripts/data/derive_actual_lmp.py` — the frozen timestamp/zone conventions
  the probe imports rather than re-implements.
* `src/market_sim/config/iso_configs.py` — the four-link radial chain whose
  structure makes the per-link decomposition an identity.
* `docs/codebase-site/data/mechanism-matrix/NYISO.js` —
  `measured_interface_limits` (`G`, evidence added), `nyiso_central_east_measured_ttc`,
  `nyiso_seam_par_attribution`, `seam_flow_envelopes`, `nyiso_zonal_loss_surface`
  (all `K`, all re-read before anything was proposed; **no verdict moves**).
* CLAUDE.md rules 1 `[R-STRUCT]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`,
  15 `[R-DASHBOARD]`, 22 `[R-HOLDOUT]`, 25 `[R-ISO-SCOPE]`, 28 `[R-MECH-MATRIX]`.

Next shorthand: nyiso-170.
