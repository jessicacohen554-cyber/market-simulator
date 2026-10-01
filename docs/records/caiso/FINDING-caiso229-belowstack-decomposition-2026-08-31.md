# FINDING — caiso-229: the caiso-227 §G below-stack wedge is taken to **A KILL, NOT A CANDIDATE**, with NO LP. Door A (the marginal CC rung's level / fuel coupling) is closed THREE ways — most sharply on **SIGN**: every one of CAISO's three measured CC bands sits AT OR ABOVE its armed value in 2025, so a measured-faithful offer repair moves the 2025 floor **UP** (+3.0 % committed / +1.8 % econ_low / +2.4 % econ_high), the wrong direction for the sole failing gate; and reality clears a **mean $12.3–26.5 BELOW** that floor, 9–19× the largest admissible level move. Door B (the committed-CC supply state) is closed on **SIZE**: the sub-floor supply deficiency in the discordant hours is **8.5–9.5 GW** against a caiso-140 committed-gas object of 2.3–2.6 GW and a caiso-227 §C belly wedge of 1.2 GW — **3–8× too small**. The one NEW limb the census surfaced — the two fitted firm-import prices ($28.00 / $48.00, 2 of CAISO's 6 live fitted binding-path scalars) — is **INERT BY CONSTRUCTION** under the armed self-schedule. And the charter's flag-vs-prose discrepancy is RECONCILED WITH A NUMBER: `caiso_scarcity_pricing=True` IS armed, and its maximum possible contribution is **$0.017 / $0.006 / $0.003 per MWh**. NO mechanism candidate survives Phase 0, NO PRECOMMIT is filed, NO solve is earned, keeper UNCHANGED. ZERO SOLVES (2026-08-31)

**Session:** caiso-229 · **Date:** 2026-08-31 · **Keeper at session:**
`2026-08-26-caiso-220-c1-crosswalk` — **re-verified this session on committed
artifacts** with `scripts/calibration_verdict.py --run-id` (no solve):
**NOT-YET**, basis *"undocumented out-of-tolerance (FAIL) criteria:
price_mean"*, **C3a the sole load-bearing FAIL — 2024 +12.5 %, 2025 +15.5 %**
(2023 passes, not printed); C1 12/12 free 8/8; C2/C3b/C4/C6/C8 PASS; C3c the
single ledgered caveat (budget 1 of 1). **Solves run: NONE.** No
`ScenarioConfig` field added, no LP built, no solver called, nothing
registered. `calibration-complete.json` (no CAISO marker) and
`holdout-freeze.json` (ACTIVE) untouched; every model and score read stayed
inside 2023–2025.

**Charter:** the owner's 2026-08-31 caiso-229 handoff — *"PHASE 0, NO LP. Take
the caiso-227 §G below-stack wedge to a NAMED MECHANISM CANDIDATE or kill
it. … is the marginal rung's fuel coupling structurally wrong (a passthrough /
offer-construction object), or is the model's committed-CC state wrong (a
commitment object)? Decide from committed artifacts."* **The answer is
NEITHER, and the charter's own kill-before-solve discipline is what produced
it.**

**Instrument (committed, no LP, no solve, re-runs from cache in minutes):**
`scripts/probes/_caiso229_belowstack_decomposition.py` →
`results/calibration/_caiso229_belowstack_decomposition.json`. Inputs: the
keeper's `hourly/` sidecars, the committed actual-LMP reference, the committed
measured offer-surface artifact `caiso_offer_curve_measured.json`, the
CA-composite citygate series, `IMPORT_TRANCHES`/`CAISO_SCARCITY_*` constants,
and the caiso-105/121/131 `run_year(fleet_only=True)` offer reconstruction
imported UNCHANGED from `_caiso202_marginal_rung.py` (only bundle + cache
re-pointed — the caiso-227 reuse pattern).

---

## §1 — the verdict, in one table

| door | the charter's question | measured | verdict |
|---|---|---|---|
| **A — offer object** | is the marginal CC rung's LEVEL wrong? | every measured band ≥ armed in 2025 (+3.0 / +1.8 / +2.4 %); reality clears $12.3–26.5 BELOW the floor | **KILL, on sign AND on depth** |
| **A — offer object** | is its FUEL COUPLING wrong? | model floor slope **2.18–4.34** MMBtu/MWh vs measured DAM body coupling **6.7–7.4**; the offer form is ALREADY affine (`gas_offer_net_revenue_margin` armed) | **KILL — under-coupled, not over-coupled** |
| **B — commitment object** | is the committed-CC state wrong? | sub-floor deficiency **8.5–9.5 GW** vs caiso-140's 2.3–2.6 GW and caiso-227 §C's 1.2 GW | **KILL, on size** |
| C — the new limb | are the 2 fitted firm-import prices a lever? | `caiso_firm_import_selfschedule=True` floors both at full shaped capability | **INERT BY CONSTRUCTION** |
| D — charter records item | is `caiso_scarcity_pricing` armed, and does it matter? | armed = **TRUE**; max adder **$0.017/$0.006/$0.003** per MWh | **armed but arithmetically inert** |

**No candidate survives Phase 0. No PRECOMMIT is filed and no solve is
earned** — exactly the outcome the charter's step 2 gate exists to produce
when the design gates fail.

## §2 — the identity that separates the two doors (§A)

Per hour, load-weighted on the rubric's own demand weights:

> **λ − DA  ≡  (λ − cc_min)  +  (cc_min − DA)**

where `cc_min` is the model's cheapest AVAILABLE gas-CC offer in that hour —
the caiso-227 §G object, its effective mid-hour price floor. Term 1 is what an
offer lever **cannot** reach (the model already prices above its own cheapest
CC offer there); term 2 is the offer lever's **entire** domain.

| year | scope | λ − DA | λ − cc_min | cc_min − DA | DA < cc_min | cc_min lw |
|---|---|--:|--:|--:|--:|--:|
| 2023 | annual | −6.41 | +1.34 | −7.76 | 44.0 % | 53.93 |
| 2024 | annual | **+0.50** | **+1.90** | −1.40 | 46.9 % | 36.57 |
| 2024 | Sep–Dec | +0.89 | **+5.33** | −4.43 | 37.3 % | 36.79 |
| 2024 | spring | +5.27 | **−11.30** | **+16.57** | 70.5 % | 34.83 |
| 2025 | annual | **+3.57** | +1.73 | +1.84 | 44.9 % | 37.24 |
| 2025 | **Sep–Dec** | **+6.33** | **+7.30** | **−0.97** | **42.3 %** | 39.13 |
| 2025 | spring | +3.53 | **−5.96** | **+9.49** | 55.2 % | 33.83 |

(The `DA < cc_min` and `cc_min lw` columns reproduce caiso-227 §H exactly —
44.9 / 42.3 / 55.2 % and 37.24 / 39.13 / 33.83 for 2025 — which is the frame's
validity check, not a new measurement.)

**The first structural result: Sep–Dec — the 60 % of the 2025 residual — is
not a floor-level problem at all.** There the floor sits **$0.97 BELOW** the
DA actual and the entire +$6.33 gap is the **above-floor** term (+$7.30). In
spring the signs invert: the model prices $5.96–11.30 **below** its own
cheapest CC offer while the floor sits $9.49–16.57 above the DA. **The two
seasons are not one object**, and neither of them is a CC-offer-level object
in the direction a lever would need.

## §3 — DOOR A, leg 1: the SIGN kill (§B)

The only rule-13/14-admissible move of the CC offer level is toward CAISO's
**own measured DAM bid multipliers** (`caiso_offer_curve_measured.json`, the
caiso-92/152/153 lineage). Armed on the keeper: `committed` **1.000** (the
fitted Lever-A value from `_CAISO_OFFER_CURVE`; the measured committed band is
deliberately withheld — *"the Lever-A inversion lesson"*), `econ_low` **1.066**
and `econ_high` **1.072** (measured, pooled). The artifact's own measured
values, against those:

| band | armed | measured 2023 | measured 2024 | measured 2025 |
|---|--:|--:|--:|--:|
| **committed — THE BAND THAT SETS `cc_min`** | 1.000 | **1.030 (+3.0 %)** | **1.030 (+3.0 %)** | **1.030 (+3.0 %)** |
| econ_low | 1.066 | 1.063 (−0.3 %) | 1.027 (−3.7 %) | **1.085 (+1.8 %)** |
| econ_high | 1.072 | 1.060 (−1.1 %) | 1.099 (+2.5 %) | **1.098 (+2.4 %)** |

Two things fall out and both are kills:

1. **`cc_min` is the committed tranche of the most efficient CC plant**, and
   the measured committed band is **1.03 against an armed 1.00 in every
   year** — so the model's floor already sits ~3 % BELOW reality's own
   measured CC floor, and a measured-faithful repair **raises** it. There is
   no admissible direction in which the floor comes down.
2. **In 2025 — the worst failing year — all three bands move UP** (+3.0 /
   +1.8 / +2.4 %). A fully measured-faithful CC offer surface makes C3a-2025
   **worse**, unanimously.

The one sliver pointing the other way — 2024's measured `econ_low` at 1.027,
−3.7 % below the armed pooled value — **is rule-13 inadmissible**: a per-year
measured bid multiplier has no forward analogue (you cannot produce a future
year's CAISO bid multiplier from forward drivers), which is precisely why the
**pooled** value is the one armed. Arming per-year measured conduct would be
an answer-key channel, not an input. It is named here so it is not
re-discovered as an opportunity.

## §4 — DOOR A, leg 2: the DEPTH kill, size-independently (§B)

How far below the model's floor reality actually clears, in the hours it does:

| year | scope | n hours | lw share | mean depth | p50 | p90 |
|---|---|--:|--:|--:|--:|--:|
| 2023 | annual | 4,105 | 44.0 % | **$20.77** | 16.78 | 45.12 |
| 2024 | annual | 4,380 | 46.9 % | **$17.16** | 12.55 | 45.39 |
| 2024 | spring | 1,589 | 70.5 % | **$26.52** | 26.02 | 55.08 |
| 2025 | annual | 4,013 | 44.9 % | **$17.50** | 15.23 | 39.04 |
| 2025 | **Sep–Dec** | 1,234 | 42.3 % | **$13.58** | 13.44 | 24.01 |
| 2025 | spring | 1,243 | 55.2 % | **$25.58** | 26.78 | 48.79 |

The largest *admissible* level move available anywhere in §3 is 3.7 % of a
~$37 floor ≈ **$1.4/MWh**, and its sign is wrong in 2025. Reality clears
**$12.3–26.5** below the floor. **The gap is 9–19× the entire admissible
lever**, so the kill does not depend on the candidate's size — it is the
caiso-228 §3.3 scale-invariance form applied to the offer level rather than to
a gas-side derate. No offer-level mechanism, at any magnitude, reaches this
wedge.

## §5 — DOOR A, leg 3: the COUPLING kill — the model is UNDER-coupled (§C)

The charter's first hypothesis was that the marginal rung's **fuel coupling**
is structurally wrong — that the model propagates the measured autumn-2025 gas
rise 1:1 through a rung reality increasingly clears under. Measured on the
model's own bytes, the daily median `cc_min` regressed on the CA-composite
citygate with the caiso-153 estimator (Theil–Sen, for the caiso-153 reason —
the citygate's Jan-2023 $24.29/MMBtu tail makes OLS inadmissible):

| year | model floor slope (MMBtu/MWh) | intercept ($/MWh) | r | n days |
|---|--:|--:|--:|--:|
| 2023 | **2.78** | 30.82 | 0.86 | 361 |
| 2024 | **2.18** | 30.46 | 0.28 | 362 |
| 2025 | **4.34** | 23.98 | 0.53 | 364 |

Against CAISO's **measured** DAM body coupling — the classifier's own slope,
*"CC_REGULAR … marginal body HR measured 0.9–1.0× of"* a cap-weighted
`base_hr` of 7.442, i.e. **6.7–7.4 MMBtu/MWh**
(`derive_caiso_offer_surface.py` docstring; caiso-153 §b).

**The model's price floor is under-coupled to fuel by roughly a factor of two,
not over-coupled.** And the reason is already in the keeper: the armed
`gas_offer_net_revenue_margin` (matrix `K`, caiso-115) **already implements the
affine bid form** — the solve log prints *"gas offer net-revenue margin: 1,223
tranches compressed at anchor 4.7964 $/MMBtu (median fixed margin
14.37 $/MWh)"* — pricing the rung at the **measured physical marginal heat
rate** (`phys_econ_low` 0.836 × 7.442 = 6.22 MMBtu/MWh) plus a fixed margin,
rather than at a multiplier on the full average heat rate. The
"offer-construction / passthrough object" the charter posited **is already
armed, measured, and pointing the other way.** Door A is closed.

## §6 — DOOR B: the SIZE kill — the deficiency is 8.5–9.5 GW (§D, §F)

In an LP, λ < cc_min **iff** demand can be met entirely from supply offered
below cc_min. So the exact, mechanism-free measure of what door B would have
to deliver is the **sub-floor supply deficiency**

> D(h) = CA demand − Σ available capacity priced below cc_min − storage discharge

evaluated in the **discordant hours** — those where reality's DA cleared below
the floor and the model's λ did not. The criterion reproduces caiso-227 §H's
model-side shares **exactly** (2025: 30.1 % annual / 23.2 % Sep–Dec;
2024: 33.9 % / 23.1 %; 2023: 37.7 % / 29.0 %), which is the frame's validity
proof.

| year | scope | n discordant h | D mean | D p50 | firm correction | **D corrected** |
|---|---|--:|--:|--:|--:|--:|
| 2023 | Sep–Dec | 380 | 10,245 | 10,516 | −1,110 | **9,135 MW** |
| 2024 | Sep–Dec | 477 | 11,300 | 10,665 | −1,769 | **9,531 MW** |
| 2025 | **Sep–Dec** | **547** | **9,857** | 9,567 | −1,308 | **8,549 MW** |
| 2025 | annual | 1,352 | 10,605 | 9,905 | −1,577 | **9,028 MW** |

(The **firm correction** subtracts the firm-import capability that is priced
above the floor but is must-take under the armed self-schedule — see §7 — so
these are strict lower bounds on the model's sub-floor supply and strict
*upper* bounds are larger still.)

**Against the named CAISO supply-state objects:**

| object | measured size | share of the 2025 Sep–Dec deficiency |
|---|--:|--:|
| caiso-140 §C committed-gas ride-through, FULL measured size | 2,300–2,600 MW | **27–30 %** |
| caiso-227 §C Sep–Dec belly wedge (gas −762 + hydro −453) | 1,215 MW | **14 %** |
| caiso-186 §a.3 PS water-state ceiling on 2025 | 10.4 % of the required C3a move | — |

**Even a PERFECT repair of the entire measured committed-gas object — the very
object caiso-140 §D/§G, caiso-142/143 and caiso-191 already adjudicated
R/unfunded — closes at most 30 % of the deficiency and leaves the margin
sitting on the CC stack.** The below-stack "wedge" is not a wedge at the
margin: it is a **~9 GW gap in the composition of CAISO's cheap-supply set**,
i.e. a representation-grain statement, and the representation-grain ask is
terminally rested (caiso-221 §E; caiso-222 §9 Q1, owner-ruled). Phase 0
therefore lands caiso-227 §G's object back on an already-closed door **with a
number attached**, which is the deliverable.

**The discordant hours are belly-dominated**, which independently forecloses
the RA-must-offer framing any import- or commitment-side successor would
reach for: of 2025's 547 Sep–Dec discordant hours, **227 sit in hod 10–15 and
only 75 in hod 17–21** (2024: 141 vs 22; 2023: 136 vs 37). The CPUC
D.20-06-028 availability-assessment-hour obligation covers the evening, not
the belly, so a must-offer citation cannot be stretched across the hours where
the residual actually lives without becoming a fitted window choice.

## §7 — the NEW limb, and why it is NOT a lever (§F)

The limb census in the discordant hours (2025 Sep–Dec, 547 h; demand
23,442 MW; cc_min $39.50, λ $44.64, DA $30.51) shows **two-thirds of the
model's available import capability priced AT OR ABOVE the in-state CC
floor** — 7,968 MW above vs 3,959 MW below — and the per-tranche split names
the reason:

| tranche | avail MW | price | vs floor | below floor |
|---|--:|--:|--:|--:|
| `PNW_hydro_base` | 1,535 | **$28.00 flat** | −11.50 | 1,535 |
| `PNW_midC` | 1,764 | 44.40 | +4.89 | 449 |
| **`DSW_solar_PV`** | **1,769** | **$48.00 flat** | **+8.50** | 461 |
| `DSW_CCGT` | 1,764 | 43.14 | +3.63 | 504 |
| `DSW_CT` | 2,156 | 48.19 | +8.68 | 381 |
| `WECC_scarcity` | 2,940 | 46.76 | +7.26 | 627 |

The two **flat**-priced rows are the firm/contracted blocks held at their
static contract-cost proxies by the armed `caiso_perhub_firm_base` — and they
are **2 of the 6 live fitted scalars** the caiso-188/189 census puts on
CAISO's backcast binding path. `spec.py` labels them itself: *"the $/MWh
values are still **static-fitted-pending-measured** — Tier-3 proxies, not a
Q-Q derivation of measured flow × hub LMP like `MISO_SEAM_LADDER_BY_YEAR` /
the NEISO ladders"* (gap register G-26, issue #1350, audit C-6). A
`DSW_solar_PV` firm block priced at a flat **$48.00** sits above the in-state
CC floor in **every** discordant hour of **all three years** (+$5.08 / +$10.23
/ +$8.50) — and the mechanism's own docstring says these blocks are *"bid
at/below $0/MWh … i.e. price-taking firm blocks"* and must be
**INFRAMARGINAL**. That reads like a lever.

**It is not one, and the reason is dispositive.** The keeper also arms
`caiso_firm_import_selfschedule=True`, which floors each firm tranche's hourly
`min_gen` at its **full shaped capability**; `scenarios.py` states the
consequence verbatim:

> *"the tranche $/MWh stays as inframarginal contract-cost bookkeeping and
> **can no longer gate the flow (never sets the margin at pmin = pmax)**"*

Both blocks are already must-take. **Re-identifying their two prices cannot
move one MWh of dispatch or one dollar of λ on this keeper.** The G-26
price-ladder gap is therefore a **DOF-ledger honesty item** — two declared-
residual scalars that should be retired or measured for provenance — and
**not** a C3a mechanism. It is recorded here so no successor session spends a
solve on it, and so the DOF ledger's 6-scalar `IMPORT_TRANCHES[CAISO]` row is
read correctly: **4 of those 6 (the spot capacities) are live on the binding
path; the 2 firm prices are inert while the self-schedule is armed.**

## §8 — the charter's flag-vs-prose item, RECONCILED WITH A NUMBER (§G)

The handoff flagged a discrepancy to *"check the flag, not the prose"*:
`docs/CHARTER-c3c-scarcity-program-2026-08-31.md` §4 says CAISO *"keeps no
scarcity overlay by measured refusal (caiso-144 §D)"*, while the keeper's
`run_config.json` carries `caiso_scarcity_pricing=True`.

**The flag reading: the prose is wrong on the flag and right on the
substance.** The keeper carries `caiso_scarcity_pricing = True` **and**
`scarcity_pricing_enabled = True` — these arm the CAISO post-solve LOLP price
adder at `runner.py:3372` — alongside `scarcity_price_overlay = False`, which
is a *different, generic* flag. So an overlay **is** armed. What caiso-144 §D
refused was the claim that it CLOSES C3c, measured at ≤1 tail-hour overlap in
90.

**And it is arithmetically inert on C3a as well.** The adder is
`LOLP(R) × (VOLL − λ)` with CAISO's own constants (VOLL $2,000, MCL 1,400 MW,
σ 2,500 MW, shift 0). LOLP is monotone **decreasing** in the reserve measure,
so caiso-131 §4's committed **minimum**-headroom hour (quoted, never
re-derived — caiso-228 §6 item 3) bounds the year's **maximum** adder:

| year | min headroom (caiso-131 §4) | max LOLP | **max adder** |
|---|--:|--:|--:|
| 2023 | 12,173 MW | 8.19e−06 | **$0.017/MWh** |
| 2024 | 12,689 MW | 3.16e−06 | **$0.006/MWh** |
| 2025 | 13,137 MW | 1.33e−06 | **$0.003/MWh** |

At the single tightest hour of the year. The overlay contributes nothing to
C3a and nothing to C3c. **Recommended correction to the charter's wording (a
records repair, not a finding reversal):** *"the backcast lane keeps an armed
overlay (`caiso_scarcity_pricing=True`) that is measured inert — ≤1 tail-hour
overlap in 90 (caiso-144 §D) and a maximum C3a contribution of $0.017/MWh
(caiso-229 §G)"*. The charter's adjudication is untouched.

## §9 — what this changes, honestly stated

* **caiso-227 §K item 2 stands and is SHARPENED.** The below-stack hour wedge
  is still the C3a-2025 root-cause statement of record. What caiso-229 adds is
  its **magnitude in MW (8.5–9.5 GW) and its two-door disposition** — and both
  doors the charter named are closed, one on sign and depth, the other on
  size.
* **The honest null hardens.** caiso-227 §H concluded *"no admissible in-model
  lever of the required 2025 size exists at this representation grain."*
  caiso-229 removes the qualifier's ambiguity: the offer-side door is closed
  **at any size** (§3–§5), and the supply-state door needs **3–8× the largest
  measured object CAISO has** (§6). NOT-YET remains the honest determination
  (owner ruling 5: C3a must genuinely pass).
* **Nothing is promoted, nothing is armed, no gate moves.** The keeper's
  determination is re-verified unchanged on committed artifacts.
* **Two records items are discharged**: the G-26 firm-price ladder is
  correctly classified (DOF honesty, not a lever — §7), and the charter's
  scarcity-flag discrepancy is reconciled with an arithmetic bound (§8).

**Filed items (carried, not discharged):**
1. `IMPORT_TRANCHES[CAISO]`'s **4 spot capacities** (8,800 MW, uncited) remain
   live and fitted on the binding path — untouched here, and NOT re-opened by
   §7 (that section closes only the 2 firm *prices*).
2. The G-26 / issue #1350 price-ladder provenance gap for CAISO stays open as
   a documentation/DOF item with its measurement route named (the existing
   `MISO_SEAM_LADDER_BY_YEAR` / NEISO Q-Q derivation), explicitly **not** as a
   calibration lever.

## §10 — DO-NOT-REDO (new, binding)

1. **Never re-derive §A–§G while the caiso-220 keeper stands.** The probe
   reproduces every number from committed bytes (the fleet recon caches per
   year). Re-run it only against a NEW keeper.
2. **The offer-side door is CLOSED FOR CAISO at any magnitude.** A successor
   differing only in which band it moves, by how much, pooled vs per-year, or
   with a different anchor is refuted in advance by §3 (sign: the measured
   value is ABOVE the armed one in the floor-setting band in all three years,
   and in ALL THREE bands in 2025) and §4 (depth: $12.3–26.5 vs a $1.4
   admissible move). **Per-year measured bid multipliers are rule-13
   inadmissible** — no forward analogue — and must never be armed to reach
   2024's −3.7 % `econ_low` sliver.
3. **Never re-argue that the model's CC rung over-propagates fuel.** §5
   measures it under-coupled (2.18–4.34 vs a measured 6.7–7.4 MMBtu/MWh), and
   the affine measured-marginal-HR-plus-fixed-margin form is ALREADY armed
   (`gas_offer_net_revenue_margin`, matrix K).
4. **Never propose re-pricing the two firm import tranches as a C3a lever.**
   They are must-take under `caiso_firm_import_selfschedule=True` and their
   $/MWh provably cannot set the margin (§7). Their provenance gap is a DOF
   item only.
5. **Never quote "CAISO keeps no scarcity overlay" as a statement about the
   flag.** `caiso_scarcity_pricing=True` is armed; it is *inert*, bounded at
   $0.017/MWh (§8). Cite the bound, not the absence.
6. **Never re-measure the caiso-131 §4 headroom surface, the §5 band, the
   caiso-140 belly object or the caiso-227 §A–§H numbers** — all quoted here
   from their own committed findings under their own DO-NOT-REDO clauses.

Carried forward unchanged and in full: caiso-227 §K, caiso-228 §6, caiso-131
§10, caiso-226 §6, caiso-222 §9 Q1 terminal rest, the caiso-225 watch sweep's
dated trigger (Order-881 effective ≤ 2026-12-01 or the next DMM print — **not
re-run here**), and every `R`/`I`/`G` cell in
`docs/codebase-site/data/mechanism-matrix/CAISO.js`.

Next number: caiso-230.
