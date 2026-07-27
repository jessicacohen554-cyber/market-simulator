# NYISO CT_PEAKER: the missing starts are not energy-economic — not hourly, and not as blocks

**Session:** nyiso-91 (CT start frequency) · **Date:** 2026-07-27
**Premise:** `docs/FINDING-nyiso90-ct-block-commitment-2026-07-27.md` §5,
`docs/FINDING-nyiso88-peaker-heat-rate-2026-07-27.md` §3
**Mode:** characterization on a same-HEAD zero-delta control. **No arm was built**
— see §5 for why, and §6 for what that leaves.
**Keeper: `2026-07-27-nyiso-89-ctmeas-hrloaded`, UNCHANGED.**

---

## 0. Summary

nyiso-90 closed the run-*length* question (the model already reproduces the
measured distribution) and handed this session the run-*count* question: why does
the model start the CT fleet 2–5× less often? The charter instructed that the
missing starts be priced — hour by hour, on the model's own P1 LMP and the
plant's own SRMC — and that the resulting three-way split *decide the mechanism*
before anything is built.

That measurement is now in, and it decides against every remaining
energy-economic candidate.

1. **The start deficit is the whole level gap.** 98 / 98 / 92 % of the class's
   measured energy sits inside runs the model never begins — **1.840 / 1.723 /
   2.031 TWh** against nyiso-90's class gap of 1.817 / 1.740 / 1.604 TWh (§1).
   Nothing else needs explaining.

2. **The three-way split is overwhelmingly "deeply out of merit."** Of the
   3,625 / 3,689 / 3,128 missing starts, only **8.6 / 10.5 / 5.8 %** are hours
   the model priced *in merit* and declined anyway; **10.4 / 6.2 / 9.3 %** miss
   by less than $5/MWh; **81.0 / 83.3 / 85.0 %** miss by more, at a median of
   **−$12.95 / −$13.94 / −$15.44 per MWh** (§2).

3. **Neither the model's price nor its offer is the error.** Repricing the same
   hours on the market's own realized DA price moves the deep share only to
   79.4 / 71.4 / 73.4 %. And the model's cheapest CT tranche is *measured* to bid
   at exactly bare SRMC — recovered offer intercept = VOM to the cent, no markup
   — so there is no offer-curve surface to repair (§2.1, §2.2).

4. **The block test kills start-cost recovery too.** Integrating each missed run
   *whole* — the thing a day-ahead commitment actually decides — only
   **21.7 / 30.0 / 36.1 %** of them are profitable as blocks at realized DA
   prices against the plant's own SRMC, and the pooled margin across ~1.8–2.0 TWh
   is **−$6.4M / +$5.2M / −$1.9M**, i.e. ≈ zero. The margin is negative at *every*
   position h1–h7 within the run, so there is no loss-leading-start-then-earn-it-
   back signature: only 12.6 / 13.8 / 18.9 % of blocks have that shape (§3).

**The conclusion this forces.** The real downstate CT fleet starts, and keeps
running, in hours that are not economic on energy at its own measured cost
against the market's own realized price — roughly two thirds of its runs lose
money as blocks. A merit-order LP cannot produce that at any commitment horizon,
because there is no horizon at which it pays. What is missing is therefore **not
a commitment mechanism at all**; it is a **non-energy commitment driver**, and
the only one still standing is local security-constrained commitment inside the
NYC / Long Island load pockets — finer than this model's five zones (§6).

**No arm was built.** Every mechanism that would reproduce the start count is
either refuted by the measurement above or forbidden by the charter's own
guardrails (§5). Registering one anyway would have spent a mechanism on a
phenomenon the evidence says it does not model — the mistake rule 1 [R-STRUCT]
and rule 19 [R-ONE-MECH] exist to prevent.

---

## 1. What is at stake: the model never begins the runs that hold the energy

`scripts/probes/nyiso91_ct_start_economics.py` against the same-HEAD zero-delta
control `results/calibration/nyiso91_ctrl_zerodelta`.

Scope is the **pure-CT plants** — every model unit at the plant is `CT_PEAKER` —
the nyiso-88 §3 convention, which makes the measured series unambiguously
combustion-turbine energy and side-steps the nyiso-88 §5 bench multi-class
collapse entirely. Both sides are thresholded at one common physical bar
(`max(1 MW, 0.05 × the plant's own p99.5 output)`), and the measured side is the
committed **bench**, not the raw CAMPD files, because every number here is
hour-matched and only the bench shares the model's non-leap 8760 local-standard
clock.

| year | plants | measured starts | model starts | missed | measured online h | h in missed runs | measured TWh | **TWh in missed runs** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 2023 | 18 | 3,763 | 859 | 3,625 | 24,152 | 23,469 | 1.875 | **1.840** |
| 2024 | 18 | 3,798 | 772 | 3,689 | 23,840 | 23,262 | 1.755 | **1.723** |
| 2025 | 17 | 3,546 | 1,915 | 3,128 | 27,283 | 24,427 | 2.213 | **2.031** |

The last column is the whole finding in one number. nyiso-90 measured the class
gap at 1.817 / 1.740 / 1.604 TWh; the energy inside runs the model never starts
is 1.840 / 1.723 / 2.031 TWh. **The start deficit and the level gap are the same
quantity.** Explaining the starts explains the level, and nothing else does.

*A note on 2025.* The model makes 1,915 starts there against 772 in 2024 — the
year the reliability floors and the gas bridge put the most CT capacity on. That
shows up again in §2.2 as a much weaker offer recovery, and every 2025 number
below carries that caveat.

---

## 2. Pricing the missing starts

For each missed start the hour is priced two ways on the price side (the model's
own P1 zonal energy dual, and the market's realized DA price) and two ways on the
cost side (the model's recovered offer, and the plant's bare SRMC). The bands
are: **(a)** in merit and declined anyway, **(b)** out of merit by less than
$5/MWh — the scale of the fleet's whole measured margin, so the band where a
small cost or price error flips a start — and **(c)** out of merit by more.

| year | n | price basis | cost basis | (a) in merit | (b) < $5 out | (c) deep | median margin |
|---|--:|---|---|--:|--:|--:|--:|
| 2023 | 3,625 | model P1 LMP | model offer | 312 (8.6 %) | 376 (10.4 %) | **2,937 (81.0 %)** | −12.95 |
| 2024 | 3,689 | model P1 LMP | model offer | 387 (10.5 %) | 229 (6.2 %) | **3,073 (83.3 %)** | −13.94 |
| 2025 | 3,128 | model P1 LMP | model offer | 180 (5.8 %) | 290 (9.3 %) | **2,658 (85.0 %)** | −15.44 |
| 2023 | 3,625 | actual DA | bare SRMC | 372 (10.3 %) | 388 (10.7 %) | **2,865 (79.0 %)** | −12.77 |
| 2024 | 3,689 | actual DA | bare SRMC | 644 (17.5 %) | 468 (12.7 %) | **2,577 (69.9 %)** | −10.26 |
| 2025 | 3,128 | actual DA | bare SRMC | 598 (19.1 %) | 262 (8.4 %) | **2,268 (72.5 %)** | −13.70 |

Band (a) — the branch a commitment mechanism could actually fix, because there
the model's own cost and price already say "run" — is **6–11 %** of the missing
starts on the model's own numbers. Band (b) adds another 6–10 %. The rest is
band (c), and it is the great majority in every year on every basis.

### 2.1 Locational robustness

The realized-DA column above is the 11-zone hub the C criteria score against,
while this fleet sits in NYC and Long Island. Adding the measured premium over
that hub (`nyiso88_peaker_economics.measured_locational_premium`, from the raw
zonal RTD files on disk: +$1.23 / +$2.80 / +$1.41 for NYC and +$7.39 / +$5.64 /
+$2.10 for Long Island) is the most generous defensible reading:

| year | (a) in merit | (b) < $5 out | (c) deep | median margin |
|---|--:|--:|--:|--:|
| 2023 | 799 (22.0 %) | 435 (12.0 %) | **2,391 (66.0 %)** | −10.38 |
| 2024 | 1,020 (27.6 %) | 554 (15.0 %) | **2,115 (57.3 %)** | −7.06 |
| 2025 | 670 (21.4 %) | 308 (9.8 %) | **2,150 (68.7 %)** | −12.17 |

It roughly doubles band (a) and still leaves 57–69 % deep. It is also mostly
*already in* the primary column: the model's own price is a zonal energy dual,
and its downstate spread tracks the measured one — model NYC−LI **−2.81 / −3.15 /
−1.80** against a measured **−6.16 / −2.83 / −0.69**. The model is not missing
the downstate locational structure, which closes locational price formation as a
route in its own right.

### 2.2 The model's CT offer is measured to be bare SRMC — there is no markup to fix

The dispatch frame carries dispatched MW and the zonal LMP but not the
generator's marginal cost, so the offer the LP charged is **recovered from the
solve**: in any hour a tranche is loaded strictly between zero and its own
maximum, LP optimality makes it marginal and its offer equals the zonal LMP, so
writing the offer as `HR × gas(t) + k` recovers `k` as the median of
`lmp(t) − HR × gas(t)` over those hours. Done per tranche, with the plant offer
taken as the per-hour minimum, because the offer that decides a *start* is the
cheapest tranche's.

The recovered cheapest-tranche intercept is **VOM exactly ($3.50) in every plant,
in all three years** — `median offer − direct SRMC = +0.00`. The model's CT start
offer carries no tranche markup and no offer-curve band. That is why the
"model offer" and "bare SRMC" rows of the table above are within a few tenths of
a point of each other, and it removes the offer surface from the candidate list
without an arm.

**Self-test.** The recovery is validated by the share of hours in which a plant
is online while its recovered offer sits *above* the LMP — which a correct offer
should almost never do. That rate is **0.8 % (2023) / 6.5 % (2024) / 35.5 %
(2025)**. 2023 and 2024 confirm the recovery cleanly. **2025 does not**: at
35.5 %, a third of the model's CT on-hours that year are not price-driven at all
but forced by the floors and the gas bridge, so 2025's offer-based bands should
be read as indicative only. The 2023–2024 conclusion does not depend on it.

---

## 3. The block test: start-cost recovery does not rescue them either

An hourly merit screen judges the *start hour*; a day-ahead commitment judges the
*block* it commits to, and can rationally accept a loss-making first hour if the
run as a whole covers it. That is the last energy-economic story available, and
it is directly testable without an LP: integrate every run the model never begins
against realized DA price minus the plant's own bare SRMC, over the whole run.

| year | blocks | mean h | 1st hour profitable | **block profitable** | loss-lead but block+ | $/MWh over SRMC | total | block+ (zonal) | $/MWh (zonal) |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 2023 | 3,625 | 6.47 | 10.3 % | **21.7 %** | 12.6 % | −3.50 | −$6.4M | 34.3 % | −1.01 |
| 2024 | 3,689 | 6.31 | 17.5 % | **30.0 %** | 13.8 % | +3.02 | +$5.2M | 41.8 % | +6.31 |
| 2025 | 3,128 | 7.81 | 19.1 % | **36.1 %** | 18.9 % | −0.93 | −$1.9M | 39.0 % | +0.56 |

Two thirds of the runs the model never begins **lose money as whole blocks**, and
the pooled margin over ~1.8–2.0 TWh is indistinguishable from zero (−$3.50 /
+$3.02 / −$0.93 per MWh; −$1.01 / +$6.31 / +$0.56 with the locational premium).
The loss-leading-start pattern that block commitment would explain is present in
only 12.6 / 13.8 / 18.9 % of them.

The margin profile by position inside the run says the same thing more directly —
median actual-DA margin over bare SRMC, $/MWh:

| year | h1 | h2 | h3 | h4 | h5 | h6 | h7 | h8 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 2023 | −12.8 | −9.9 | −7.3 | −6.6 | −7.1 | −6.0 | −3.5 | −2.4 |
| 2024 | −10.3 | −7.4 | −4.6 | −3.8 | −3.7 | −2.6 | −0.3 | +1.3 |
| 2025 | −13.7 | −8.6 | −4.7 | −3.0 | −3.9 | −4.4 | −3.8 | −3.5 |

**Negative at every position.** The run does not start under water and climb out
of it; it is under water throughout. A commitment horizon cannot fix a block that
is unprofitable at every horizon.

### 3.1 Reconciliation with nyiso-88 §3

nyiso-88 measured this fleet **at the money** (energy-weighted margin −$1.39 /
+$5.82 / +$3.49, roughly half its energy below its own SRMC) and read that as the
signature of a fleet dispatched on energy economics at the margin. Both
measurements are correct and they are the same fact seen at different resolution.
The energy-weighted annual margin is near zero because **a profitable minority of
blocks (22–36 %) carries a loss-making majority** — not because the typical run
is marginal. At start-decision resolution the fleet is not at the money; it is
below it, and the annual average is an artifact of pooling.

---

## 4. What is now closed

Combined with the three prior sessions, every energy-economic route into this
class is measured and eliminated:

| candidate | verdict | evidence |
|---|---|---|
| C3c price formation | ≤ 12–17 % of the gap | nyiso-88 §2; here, repricing on the *actual* DA moves the deep share by only 2–12 points (§2) |
| a non-energy obligation (published reserve ladder) | +0.11 TWh | nyiso-83; nyiso-88 §3 |
| the measured heat rate | now the keeper's input | nyiso-89 |
| day-ahead block commitment / min-run | inert — runs already the right length | nyiso-90 |
| the offer-curve markup | **there is none** — cheapest tranche bids bare SRMC | §2.2 |
| locational price formation | model's downstate spread already tracks measured | §2.1 |
| **start-cost recovery over a committed block** | **refuted — the blocks are not profitable either** | §3 |

---

## 5. Why no arm was registered

The charter asked for one arm against the control. The characterization it also
asked for — and told this session to run *first*, because "that split DECIDES the
mechanism and must be measured before anything is built" — left nothing
admissible to arm.

* The mechanisms that **would** reproduce the start count are the ones the
  charter forbids outright: a windowed floor or CT-scoped `reliability_floor`
  limb (automatic REJECT, and already refuted by the G-20 probe at 12.8 %
  overnight binding), a start subsidy, a fitted start-cost haircut, or an adder
  tuned to the start count (rule 13 [R-MEASURED]).
* The one admissible commitment-basis variant the charter allowed — a
  forecast-rather-than-realized-price commitment basis — is refuted by §3 rather
  than permitted by it. A forecast basis can only change *which* hours are
  chosen; it cannot make a block profitable that loses money at realized prices
  in two thirds of cases and breaks even in aggregate. It would move starts
  around, not create 2,800 of them.
* A cost-basis correction large enough to close band (c) is not available as an
  input question. The median deep miss is $12.77–$15.44/MWh, which at these
  units' ~10 MMBtu/MWh is **$1.3–1.5/MMBtu of delivered gas**, and the p90
  shortfall ($25–37/MWh) is $2.5–3.7/MMBtu — 53–82 % of the entire delivered
  price on the keeper's own seam (NYC $4.54 / $4.91 / $7.82, LI $3.70 / $4.09 /
  $7.25 per MMBtu). No defensible re-derivation of a measured commodity-plus-
  transport index moves by that much, and moving it *because* the residual wants
  it is exactly the rule-13 prohibition.

Building an arm regardless would have added a mechanism, a D-2 row and
parameters to a phenomenon the measurement says it does not model — rule 1
[R-STRUCT] ("never reach the right number through a mechanism that isn't real")
and rule 19 [R-ONE-MECH]. The control is registered on its own as the probe that
carries this evidence.

---

## 6. What is left, and what it needs

One candidate survives the measurement: **the fleet is committed for local
reliability, not for energy.** NYISO's downstate CTs carry ICAP obligations and a
DAM must-offer; SCUC commits them for load-pocket security and makes them whole
through BPCG uplift, which is precisely how a unit can run at an energy loss on
two thirds of its runs and still be rationally operated. That is a real market
structure (rule 1), it has a forward analogue, and it is the only story
consistent with all of §2 and §3.

It is **not** the published reserve ladder — nyiso-83 built and measured that at
+0.11 TWh. It is security-constrained commitment against transmission limits
*inside* NYC and Long Island, which this model's five zones collapse away. That
makes it a data-intake and topology question before it is a mechanism question,
and it needs owner scoping:

1. Do sub-zonal NYC / Long Island local-security requirements exist in a
   citable, reproducible form (NYISO local reliability rules, load-pocket
   minimum-oil-burn / gas-security requirements, the Con Ed / LIPA local
   transmission plans)? Rule 17 [R-FLOOR-WINDOW] needs a driver, a window and a
   forward story before any of it can bind.
2. Would representing it require splitting NYC / Long Island into load pockets —
   a topology change with cross-class consequences — rather than adding a
   mechanism inside the existing zones?

Until that is answered, **CT_PEAKER's level gap should be recorded as a known,
diagnosed, unclosed structural limitation of the five-zone representation**, not
as an open tuning target. It is diagnosed to a specific cause with a specific
piece of missing structure; it is not a residual looking for a parameter.

**Still open, unchanged, not this session:** the nyiso-88 §5 bench multi-class
collapse (cross-ISO scorer defect, needs its own lane and owner scoping); the
minimum-energy screen for the CT heat-rate derive (nyiso-89 §5b); and the
min-run percentile convention on the keeper's CC/ST bridge legs (nyiso-90 §3.1).

---

## 7. Governance

* **Rule 13 [R-MEASURED].** No measured outcome entered any model input. This is
  scoring-side characterization on committed artifacts plus one zero-delta
  control solve; no parameter was derived, so rule 24 [R-FROZEN-DERIVE]'s
  pre-registration requirement had nothing to bind and none was written.
* **Rule 1 [R-STRUCT] / rule 19 [R-ONE-MECH] / rule 21 [R-DOF].** No mechanism,
  no parameter and no degree of freedom was added.
* **Closed routes stay closed.** The NYCA/East spin gate, the J/K ladders, the
  h14-21 peak-window floors, `td_loss_factor` as the C1 instrument, the
  West/Panhandle topology split and CT block commitment are all untouched and
  default-off.
* **Rule 16 [R-ALLYEARS].** One bundle, `--year 2023 2024 2025`, sequential
  within the invocation.
* **Gas seam.** The keeper's `nyiso_downstate_ct_gas_daily=True` /
  `nyiso_downstate_ct_gas_basis=False` seam is inherited unchanged by the replay
  and is the seam every SRMC in this document is priced on.
* **Rule 15 [R-DASHBOARD].** The control is registered as a PROBE with this
  document as its write-up.

### 7.1 A defect fixed in the probe layer

`_dispatch_frame` relabels a gas unit that switched to its backup oil as
`klass == "oil"`, so selecting `klass == "CT_PEAKER"` silently drops those
unit-hours and returns a short series — 8,736 rather than 8,760 hours for plant
2494 in 2023, for instance. nyiso-90's probes filter that way; for their
totals-only decomposition the effect is negligible, but every number here is
hour-matched, so this probe resolves the CT unit ids first and then takes **all**
of their rows whatever the hour's fuel label, reindexing onto the full clock. Left
unfixed it silently reduced the analysable fleet from 18 plants to 9.
