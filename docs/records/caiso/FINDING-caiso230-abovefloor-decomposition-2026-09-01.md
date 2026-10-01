# FINDING — caiso-230: the caiso-229 §A ABOVE-FLOOR term is DECOMPOSED, and **EVERY LIMB LARGE ENOUGH TO CLOSE C3a HAS A CLOSED OWNER**. The term is **+$1.28 / +$2.37 / +$2.49** annually against required moves of **$0 / −$0.85 / −$1.89**, and it is carried almost entirely by ONE family: the **CC body** (CC_REGULAR + CC_CHP committed+econ bands) at **+$4.62 / +$4.33 / +$4.95**, i.e. **2.6× the whole 2025 requirement** — the family whose offer-level door caiso-229 closed at any magnitude. The charter's other four limbs are each disqualified on their own arithmetic: **peaking** reaches 45 % of 2025's requirement at TOTAL removal; **imports/exports** and the **storage/hydro inter-temporal duals** already contribute **NEGATIVE** −$1.47 and −$1.56; and **zonal congestion is a NON-LEVER BY CONSTRUCTION** — a mean-preserving redistribution moves the dispersion without moving λ at all, and measured like-for-like against CAISO's own trading hubs the model **UNDER**-disperses by **$2.3–4.6**. The ONE door caiso-229 did not reach — CAISO's **three ERCOT-INHERITED gas classes** (CC_CHP / CT_CHP / ST_GAS) plus the two fitted `committed` bands — is opened, measured and **CLOSED ON SIGN IN ALL THREE YEARS**: a fully measured-faithful re-grounding moves the ISO's annual load-weighted price **UP +$0.55 / +$0.70 / +$0.71**. NO candidate survives Phase 0, NO PRECOMMIT is filed, NO solve is earned, keeper UNCHANGED. ZERO SOLVES (2026-09-01)

**Session:** caiso-230 · **Date:** 2026-09-01 · **Keeper at session:**
`2026-08-26-caiso-220-c1-crosswalk` — **re-verified this session on committed
artifacts** with `scripts/calibration_verdict.py --run-id` (no solve):
**NOT-YET**, basis *"undocumented out-of-tolerance (FAIL) criteria:
price_mean"*, **C3a the sole load-bearing FAIL — 2024 +12.5 %, 2025 +15.5 %**
(2023 +4.0 % PASSES); C1 12/12 free 8/8; C2/C3b/C4/C6/C8 PASS; C3c the single
ledgered caveat (budget 1 of 1). **Solves run: NONE.** No `ScenarioConfig`
field added, no LP built, no solver called, nothing registered.
`calibration-complete.json` (no CAISO marker) and `holdout-freeze.json`
(ACTIVE) untouched; every model and score read stayed inside 2023–2025.

**Charter:** the owner's 2026-09-01 caiso-230 handoff — *"PHASE 0, NO LP.
DECOMPOSE the Sep–Dec above-floor term … into its limbs, load-weighted, from
committed artifacts only … State each limb's $/MWh contribution to the ANNUAL
load-weighted mean so it can be read against the −$0.86 / −$1.89 requirements
directly … ADJUDICATE each limb against the matrix BEFORE proposing
anything."* **Every limb is measured, every limb is adjudicated, and the
honest outcome is again attribution + kill — the outcome the charter's step 2
gate exists to produce.**

**Instrument (committed, no LP, no solve, re-runs from cache in minutes):**
`scripts/probes/_caiso230_abovefloor_decomposition.py` →
`results/calibration/_caiso230_abovefloor_decomposition.json`. Inputs: the
keeper's `hourly/` sidecars, the committed actual-LMP reference, the committed
per-(ISO,year) benchmark parts, the committed raw CAISO hub-LMP CSVs, the
committed measured offer-surface artifact, `_CAISO_OFFER_CURVE`, and the
caiso-105/121/131 `run_year(fleet_only=True)` offer reconstruction imported
UNCHANGED from `_caiso202_marginal_rung.py` (only bundle + cache re-pointed —
the caiso-227/229 reuse pattern; the measured-hub loader follows
`_caiso215_c3a_zonal_decomp.py`). caiso-229 §10 item 1 is honoured: §A is a
REPLAY of caiso-229's own table, not a re-derivation, and it reproduces it.

---

## §1 — the verdict, in one table

Every number is the limb's contribution to the **ANNUAL load-weighted mean**,
the C3a denominator, so it reads directly against the required move.

| limb (charter id) | 2023 | 2024 | 2025 | **required move** | owner | verdict |
|---|--:|--:|--:|--:|---|---|
| **(a) the CC-stack climb** — CC_REGULAR + CC_CHP `committed`+`econ` | **+4.62** | **+4.33** | **+4.95** | 0 / −0.85 / −1.89 | offer level | **CLOSED at any magnitude** (caiso-229 §3–§5; extended to CC_CHP by §7 below) |
| **(b) other class rungs** — CT_PEAKER, CT_CHP, ST_GAS, CC/ST `peak` | +4.01 | +1.77 | **+0.86** | | offer level / commitment | **SIZE KILL** — 45 % of 2025's requirement at TOTAL removal; measured bands already armed (move 0.0 %) |
| **(c) import / export tranches** | −2.01 | −1.84 | **−1.47** | | `IMPORT_TRANCHES[CAISO]` | **WRONG SIGN** — already pulls λ DOWN; 2 firm prices inert (caiso-229 §7), 4 spot capacities a declared residual |
| **(d) storage / hydro inter-temporal duals** (`unmatched`) | −5.03 | −1.60 | **−1.56** | | storage family | **WRONG SIGN** — already pulls λ DOWN; family K/R/G-adjudicated |
| **(e) zonal congestion** (limb Z) | +1.99 | +2.04 | +2.82 | | congestion | **NON-LEVER BY CONSTRUCTION** — mean-preserving; and measured, the model UNDER-disperses by $2.3–4.6 |
| coal / hydro / nuclear / renewable rungs | −0.31 | −0.30 | −0.28 | | — | wrong sign, trivial |
| **TOTAL above-floor term** | **+1.28** | **+2.37** | **+2.49** | | | |

**No candidate survives Phase 0. No PRECOMMIT is filed and no solve is
earned.** NOT-YET remains the honest determination (owner ruling 5: C3a must
genuinely pass).

## §2 — the basis, and why it is the SCORER's own (validity proof)

caiso-229 measured the above-floor term on the rubric-weight basis
(`load_demand` summed over zones). This probe annualises on the **scorer's
own** basis — the zone-hour mean over all 8,760 hours weighted by the model's
own zonal demand — because the charter requires the limbs to read against
−$0.86 / −$1.89 **directly**. That basis reproduces
`calibration_verdict.score_price_mean` to the cent:

| year | model lw | RT lw | C3a % | scorer C3a | **required move** | `cc_min` lw |
|---|--:|--:|--:|--:|--:|--:|
| 2023 | **56.31** | 54.17 | **+3.96 %** | +4.0 % | 0.00 | 55.04 |
| 2024 | **38.96** | 34.65 | **+12.45 %** | +12.5 % | **−0.848** | 36.59 |
| 2025 | **39.76** | 34.42 | **+15.50 %** | +15.5 % | **−1.893** | 37.26 |

§A separately replays caiso-229's own rubric-weight table and reproduces it
exactly (2024 annual +1.90 above-floor / Sep–Dec +5.33; 2025 +1.73 / +7.30;
spring −11.30 / −5.96). **Two independent weightings, both reproduced** — the
frame is the same object caiso-229 measured, re-expressed on the gated basis.

**One corroboration falls straight out of the last column.** From 2024 to 2025
the model's load-weighted price rises **+$0.80**, of which the **floor** rises
**+$0.67 (84 %)** and the above-floor term only **+$0.12 (16 %)**. caiso-229
§G's YoY mechanism — *"the measured fuel rise times a wedge the model holds
constant"* — is confirmed on the gated basis: **2025's deterioration against
2024 is a floor object, not an above-floor object**, which independently
deflates this lane as the place to fix 2025 before any limb is examined.

## §3 — limb (e): zonal congestion is a NON-LEVER **BY CONSTRUCTION**

The charter's limb (e) is the exact split

> **λ − cc_min ≡ (λ − p_min) + (p_min − cc_min)**,  limb Z + limb S

with `p_min` the cheapest CA zonal price. Limb Z is ≥ 0 by construction and is
large — annualised **+1.99 / +2.04 / +2.82**, more than the whole above-floor
term in 2023 and 2025. **It is nonetheless not a lever, and the reason is
arithmetic, not evidential:** a zonal redistribution that holds the
load-weighted mean fixed leaves λ — the scored quantity — **unchanged** while
moving `p_min` and therefore limb Z. Reducing dispersion around a fixed λ
raises `p_min`; it does not lower λ by one cent. The measured corroboration is
caiso-215's own: *"every zonal redistribution nets to ≈ 0 ISO-wide (bridge
terms ±$0.15), so no zonal lever closes C3a directly."*

**And the model errs in the direction that has no C3a value anyway.** Collapsing
the model's five CA zones onto CAISO's own three trading hubs with the model's
own demand weights, and computing the SAME dispersion statistic on both sides
(same weights, same zone set, same estimator):

| year | model | actual DAM | Δ | model | actual RTM | Δ |
|---|--:|--:|--:|--:|--:|--:|
| 2023 | 1.10 | 5.57 | **−4.48** | 1.10 | 5.70 | **−4.60** |
| 2024 | 1.17 | 4.67 | **−3.50** | 1.17 | 5.29 | **−4.13** |
| 2025 | 1.04 | 3.31 | **−2.27** | 1.04 | 4.25 | **−3.22** |

**The model under-disperses by $2.3–4.6/MWh in every year and both markets.**
The measured-faithful direction is therefore MORE zonal dispersion, and more
dispersion at a fixed mean is worth exactly $0.00 on C3a. This is the caiso-220
split witness (model NP15−SP15 > $15 in 50/40/17 h vs reality's
1,310/1,691/1,347) re-stated as a price-level statistic on the gated basis, and
it re-confirms the caiso-215 §F H4 strandedness object as a **C3b / D-A**
fidelity item, never a C3a instrument.

## §4 — limb (a): the CC body is 2.6× the requirement, and its door is shut

The zone-hour rung attribution — every CA zone-hour matched to the supply rung
whose reconstructed offer sits nearest its price (the caiso-202 estimator at
$0.75 tolerance, over the in-state fleet by TRANCHE BAND, the per-hub priced
import legs, the static firm blocks, the corridor export legs, and a zero rung
for renewable spill) — puts the term here:

| rung, 2025 annual | ann $/MWh | | rung, 2024 annual | ann $/MWh |
|---|--:|---|---|--:|
| `CC_REGULAR:econ` | **+2.435** | | `CC_REGULAR:econ` | **+2.503** |
| `CC_CHP:econ` | **+1.228** | | `CC_CHP:econ` | **+1.069** |
| `CC_REGULAR:committed` | **+1.015** | | `CT_PEAKER:econ` | +0.591 |
| `CT_CHP:committed` | +0.362 | | `CC_REGULAR:committed` | +0.532 |
| `CC_CHP:committed` | +0.274 | | `CT_CHP:committed` | +0.477 |
| `CC_REGULAR:peak` | +0.210 | | `CC_CHP:committed` | +0.229 |
| `CT_PEAKER:econ` | +0.164 | | `CC_REGULAR:peak` | +0.207 |
| `unmatched` | **−1.561** | | `unmatched` | **−1.595** |
| `imp:DSW_surplus_clean` | **−1.543** | | `imp:DSW_surplus_clean` | **−1.389** |

The **CC body** — CC_REGULAR and CC_CHP, `committed` + `econ` — totals
**+4.62 / +4.33 / +4.95**. It is the only limb anywhere in the decomposition
whose size exceeds the 2025 requirement, and it exceeds it by **2.6×**.

**Its owner is closed.** caiso-229 §3 killed the CC offer level on SIGN (the
floor-setting `committed` band is armed at the fitted 1.000 while CAISO's own
measured value is 1.030, so a measured-faithful repair RAISES it; in 2025 all
three CC_REGULAR bands move up), §4 killed it on DEPTH size-independently, and
§5 killed the fuel-coupling variant (the model is UNDER-coupled at 2.18–4.34
vs a measured 6.7–7.4 MMBtu/MWh, because the affine
measured-marginal-HR-plus-fixed-margin form is already armed). §10 item 2
states the closure at any magnitude. **What caiso-230 adds is that the closed
door is the ONLY door big enough** — the limb it guards is 199 % of the whole
above-floor term in 2025 — and that the closure now extends to CC_CHP, which
caiso-229 never covered (§7).

## §5 — limbs (b), (c), (d): each disqualified on its own arithmetic

**(b) peaking — CT_PEAKER, CT_CHP, ST_GAS and the CC/ST `peak` bands.**
Annualised **+4.01 / +1.77 / +0.86**. In the worst year it is **+$0.86 against
a −$1.89 requirement — 45 % at TOTAL removal**, and total removal means
peakers never set price, which is not a mechanism. It also has no measured
level move available: CT_PEAKER's `econ_low`/`econ_high`/`peak` are ALREADY
armed at CAISO's own measured values, so their re-grounding move is **+0.0 %**
by construction (§7 table). The family's steep 2023→2025 decline (+4.01 →
+0.86) is itself the story of the storage build displacing peakers from the
evening margin — a mechanism already working, not one waiting to be armed.

**(c) imports / exports.** Annualised **−2.01 / −1.84 / −1.47**: the seam
already pulls λ DOWN, so no repair of it can deliver a further downward move
without a driver. The limb's internal census is fully adjudicated: the two
fitted firm prices are **inert by construction** under the armed
`caiso_firm_import_selfschedule` (caiso-229 §7), the four spot capacities are a
declared residual with a direct λ share below 5 % (caiso-191 §4, caiso-202
§C), and `imp:DSW_surplus_clean` alone contributes **−1.54** in 2025 at a
median price of $4.62 — the seam's cheap daytime block is one of the two
largest DOWNWARD limbs in the model.

**(d) storage / hydro inter-temporal duals** — the caiso-227 §B `unmatched`
limb, here **−1.56 / −1.60 / −5.03**, again the wrong sign. §D confirms its
identity rather than assuming it: in the unmatched zone-hours storage is active
in **86.0 / 86.2 / 89.0 %** (against an all-zone-hour baseline of 77.4 / 76.7
/ 81.9 %) and hydro in **100 %**, so these are indeed the hours whose price is set by a SOC or
budget dual with no offer counterpart. The storage family's matrix column is
already `K`/`R`/`G` across the board — `caiso_storage_shape_anchor`,
`battery_dispatch_adder`, `storage_degradation`, `storage_vintage_ramp`,
`caiso_ps_plant_params` armed; `storage_daily_cycling` **G**,
`caiso_ps_charge_shape_anchor` **G**, `caiso_da_rt_two_settlement` **R**,
`ercot_storage_adaptive_expectation` **I** — leaving only
`pumped_storage_cycling_depth` untested, against a limb that already prices λ
$1.56 BELOW the CC floor.

## §6 — WHEN the term sits, and what the D-A phase flag does and does not open

The charter names the keeper's D-A row as a corroborating signal: 2025 reads
**phase OFF (model peak h22 vs measured h18)** where 2023/2024 read OK. **The
flag localises the term exactly as the charter anticipated.** Family × hour-of-
day, annualised, Sep–Dec 2025:

| hod band | cc_body | peaking | imp/exp | coal/hydro/nuc | unmatched | **TOTAL** |
|---|--:|--:|--:|--:|--:|--:|
| night 0–6 | +0.648 | +0.052 | +0.088 | +0.000 | −0.034 | **+0.754** |
| morning 7–9 | +0.204 | +0.017 | −0.024 | −0.017 | −0.022 | +0.159 |
| belly 10–15 | +0.310 | +0.014 | −0.235 | −0.054 | −0.081 | **−0.045** |
| ramp 16–18 | +0.355 | +0.201 | +0.069 | −0.000 | +0.021 | **+0.646** |
| **evening 19–23** | **+0.552** | **+0.377** | +0.139 | +0.000 | +0.063 | **+1.131** |

**The Sep–Dec above-floor term is an EVENING/NIGHT object, not a belly
object**: evening + ramp carry **+1.78 of +2.64 (67 %)** and the belly is
**−0.05**. That is the exact complement of caiso-229 §6's finding that the
below-floor DISCORDANT hours are belly-dominated (227 h in hod 10–15 vs 75 in
17–21) — **the two seasons' two terms live in two different hour bands, and
neither is the other's mechanism.**

**Localising it does not open a door.** The evening cell is again
cc_body-dominated (+0.552 vs peaking's +0.377), and cc_body's owner is closed.
Annually the pattern is identical in all three years — evening 19–23 carries
**+2.62 / +2.61 / +2.61** — i.e. the evening limb is **flat across the two
failing years and the passing one**, so it cannot be what distinguishes them.
The D-A phase flag is corroborated as a real, localised shape defect and is
recorded as such; it is **not** a C3a instrument.

## §7 — THE NEW DOOR: CAISO's three ERCOT-INHERITED gas classes — OPENED, AND CLOSED ON SIGN

caiso-229's offer-side kill was measured on **CC_REGULAR** — the only class
besides CT_PEAKER that the measured artifact names. It never reached the
classes `_CAISO_OFFER_CURVE` itself flags in its own comment:

> *"CC_CHP / CT_CHP / ST_GAS below are PINNED to the values CAISO previously
> inherited from the generic ERCOT-lineage `else` branch. **They are NOT
> CAISO-grounded** — they are preserved verbatim ONLY so the neutral generic
> fallback (rule #24) does not silently change the caiso-51 keeper … CT_CHP's
> inherited 1.20 econ vs the measured 0.594 marginal is the largest such
> margin — surfaced for A/B, not asserted good."*

Together with the two fitted `committed` bands (CC_REGULAR's Lever-A 1.00 and
CT_PEAKER's NYISO-grounded 1.35), that is **five out-of-ISO or fitted band
multipliers on CAISO's binding path** — a standing rule 25 `[R-ISO-SCOPE]`
exposure, and §4 shows they price a large share of the above-floor term
(`CC_CHP:econ` +1.23, `CC_REGULAR:committed` +1.02, `CT_CHP:committed` +0.36,
`CC_CHP:committed` +0.27 in 2025 alone). **This is a genuine new limb with an
owner caiso-229 did not adjudicate, and it is the one the charter's step 3
would have promoted to a PRECOMMIT.**

**A measured counterpart exists, and the derive script says so itself.** The
masked OASIS public bids cannot be plant-mapped, so
`derive_caiso_offer_surface.py` discloses that *"the three OTC/RMR steamers
(ST_GAS: Alamitos / Huntington Beach / Ormond Beach, 2.9 GW) and priced CT_CHP
curves land in the CT bucket … CC_CHP (HR 6.90) lands in the CC bucket."* The
measured CC bucket is therefore the pooled CC_REGULAR+CC_CHP conduct and the CT
bucket the pooled CT_PEAKER+CT_CHP+ST_GAS conduct — so re-grounding each
un-grounded class on **its own bucket** is a measured-input substitution with
**zero free parameters**, not a new fitted lever. The candidate is admissible
in principle. **It dies on sign.**

| class | band | armed | measured | move |
|---|---|--:|--:|--:|
| CC_REGULAR | committed | 1.000 | 1.030 | **+3.0 %** |
| CC_REGULAR | econ_low / econ_high / peak | 1.066 / 1.072 / 1.386 | same | **+0.0 %** (already armed) |
| **CC_CHP** | **econ_low** | **0.960** | **1.066** | **+11.0 %** |
| CC_CHP | econ_high | 1.120 | 1.072 | −4.3 % |
| CC_CHP | committed | 1.000 | 1.030 | +3.0 % |
| CC_CHP | peak | 2.250 | 1.386 | −38.4 % |
| CT_PEAKER | committed | 1.350 | 1.166 | −13.6 % |
| CT_PEAKER | econ_low / econ_high / peak | 1.145 / 1.166 / 1.166 | same | **+0.0 %** (already armed) |
| CT_CHP | committed | 1.100 | 1.166 | +6.0 % |
| CT_CHP | econ_low / econ_high / peak | 1.200 / 1.200 / 1.400 | 1.145 / 1.166 / 1.166 | −4.6 / −2.8 / −16.7 % |
| ST_GAS | committed | 0.810 | 1.166 | **+44.0 %** |
| ST_GAS | econ_low | 1.050 | 1.145 | +9.0 % |
| ST_GAS | econ_high / peak | 1.400 / 4.200 | 1.166 / 1.166 | −16.7 / −72.2 % |

Weighting each band's move by the zone-hours in which that class-band is the
marginal rung, at the offer's own clearing price (a strict UPPER bound in
magnitude — the multiplier scales only the FUEL component of the offer, so the
true move is smaller; the sign is exact because both multipliers are committed
constants):

| year | first-order bound on a FULL measured re-grounding | required move |
|---|--:|--:|
| 2023 | **+0.553** | 0.00 |
| 2024 | **+0.700** | −0.848 |
| 2025 | **+0.709** | −1.893 |

**Every year moves UP.** The dominant term is `CC_CHP:econ_low`, armed at an
ERCOT-inherited 0.960 against a CAISO-measured 1.066 — **+11.0 %, worth
+0.44 / +0.54 / +0.61 on its own**, more than the whole net bound. The bands
whose measured move points DOWN are real but land on rungs that barely price:
the three `peak` bands (`CC_CHP` −38.4 %, `ST_GAS` −72.2 %, `CT_CHP` −16.7 %)
are the marginal rung in **1 / 3 / 0** and **5 / 17 / 0** and **38 / 21 / 0**
zone-hours across 2023/2024/2025, worth **−0.03 in total in 2023 and 2024 and
−0.000 in 2025**; `CT_PEAKER:committed`, the largest downward move on an armed
band (−13.6 %), reaches **−0.040 / −0.012 / −0.000**. Summed, every negative
band together contributes **−0.22 / −0.17 / −0.19** against positives of
+0.77 / +0.87 / +0.90.

**And the armed conditional ladder is arithmetically inert on this term.**
`caiso_offer_surface_conditional` reprices 380 gas peak-rung rows across four
net-load bins (its tightest bin binds 263/8,760 hours), but **not one of those
`peak2`–`peak5` rungs is the marginal rung in a single CA zone-hour of any of
the three years** — the charter's limb-(a) sub-question about the ladder
resolves to zero, measured.

**This is the caiso-229 §3 sign kill, reproduced independently on the three
classes caiso-229 did not cover, and it closes the last un-adjudicated
offer-side door in CAISO.** Even with the sign reversed it would reach only
37 % of 2025's requirement, so the kill does not depend on direction alone.

**The rule-14 tension is named, not buried.** Rule 14 `[R-ACCURATE]` says a
measured input that worsens the backcast stays in and the worse fit is treated
as a discovered bug. That argues these five bands SHOULD be re-grounded on
structural-integrity grounds regardless of C3a. Two things stop this session
from doing it: (i) it needs its own PRECOMMIT and a three-year solve, which is
outside a Phase-0 charter whose gate this candidate fails; and (ii) rule 14's
own stated exception is live here — the measured multiplier is defined against
its BUCKET's base heat rate (CC 7.442 / CT 10.862 MMBtu/MWh) while the classes
it would be transplanted onto carry materially different ones (CC_CHP 6.90,
ST_GAS ~11.85), so a naive transplant does not round-trip to the measured bid
level and is a **different aggregation than our representation**, exactly the
misalignment rule 14 carves out. It is filed as an owner-fundable
structural-integrity item in §9, with its measured sign and size attached so no
successor spends a solve on it expecting C3a relief.

## §8 — what this changes, honestly stated

* **The caiso-227 §K / caiso-229 §9 honest null hardens again, and this time
  from the OTHER side of the identity.** caiso-229 closed both doors on the
  FLOOR term. caiso-230 decomposes the ABOVE-FLOOR term and finds that the only
  limb of sufficient size is guarded by that same closed door, that three limbs
  have the wrong sign, that one is a non-lever by construction, and that the
  last un-adjudicated offer-side door closes on sign in all three years.
  **Both terms of `λ − DA ≡ (λ − cc_min) + (cc_min − DA)` are now attributed
  and adjudicated end to end.**
* **The in-model lever queue is confirmed empty at limb grain**, which is a
  finer grain than the caiso-200/caiso-185 "queue empty" statements were made
  at. Nothing is promoted, nothing is armed, no gate moves; the keeper's
  determination is re-verified unchanged on committed artifacts.
* **Two records items are added**: the zonal-congestion limb is measured as a
  non-lever with the model's own under-dispersion quantified (§3), and CAISO's
  five out-of-ISO/fitted band multipliers are named, sized and sign-tested (§7).

**Filed items (carried, not discharged):**
1. **The five out-of-ISO / fitted band multipliers** (`CC_CHP`, `CT_CHP`,
   `ST_GAS` entire; `CC_REGULAR:committed`; `CT_PEAKER:committed`) remain a
   rule 25 `[R-ISO-SCOPE]` exposure on CAISO's binding path. Re-grounding them
   is an **owner-fundable structural-integrity item**, NOT a C3a lever: its
   measured sign is UP in all three years (+0.58 / +0.73 / +0.71) and it
   carries the §7 base-heat-rate misalignment caveat. Funding it means
   accepting a C3a regression on structural grounds (rule 1 / rule 14) — an
   owner call, and one this finding does not make.
2. `IMPORT_TRANCHES[CAISO]`'s **4 spot capacities** stay live and fitted on the
   binding path (caiso-229 filed item 1, carried unchanged).
3. The **G-26 / issue #1350** price-ladder provenance gap for CAISO stays open
   as a documentation/DOF item (caiso-229 filed item 2, carried unchanged).

## §9 — DO-NOT-REDO (new, binding)

1. **Never re-derive §A–§H while the caiso-220 keeper stands.** The probe
   reproduces every number from committed bytes (the fleet recon caches per
   year). Re-run it only against a NEW keeper.
2. **Never propose zonal congestion, a Path-15 split, sub-zonal topology or
   any locational repricing as a C3a instrument.** It is mean-preserving on
   the scored metric BY CONSTRUCTION (§3), and measured the model
   UNDER-disperses by $2.3–4.6 against its own trading hubs — the admissible
   direction is MORE dispersion, worth $0.00 on C3a. It remains a legitimate
   C3b / D-A fidelity lane; it is never a C3a lane.
3. **Never propose re-grounding CC_CHP / CT_CHP / ST_GAS — or the CC_REGULAR /
   CT_PEAKER `committed` bands — as a C3a lever.** §7 measures the
   measured-faithful move at **+0.55 / +0.70 / +0.71 UPWARD** in 2023/2024/2025
   with the sign exact, and at 37 % of 2025's requirement even if the sign were
   reversed. It survives ONLY as the §8 filed-item-1 structural-integrity ask.
4. **Never re-attribute the above-floor term to the peaking family.** It is
   +0.86 in 2025 — 45 % of the requirement at TOTAL removal — and CT_PEAKER's
   econ and peak bands are already armed at CAISO's own measured values, so no
   measured level move exists for them (+0.0 %).
5. **Never quote the above-floor term as the 2025 driver.** From 2024 to 2025
   the model's gated price rises +$0.80, of which the FLOOR carries +$0.67
   (84 %) and the above-floor term +$0.12 (16 %) — caiso-229 §G's mechanism,
   confirmed on the gated basis (§2).
6. **Never re-measure the caiso-215 zonal decomposition, the caiso-220 split
   witness, the caiso-227 §A–§H numbers or the caiso-229 §A–§G numbers** — all
   quoted here from their own committed findings under their own DO-NOT-REDO
   clauses.

Carried forward unchanged and in full: caiso-229 §10 entire, caiso-227 §K,
caiso-228 §6, caiso-131 §10, caiso-226 §6, caiso-222 §9 Q1 terminal rest, the
caiso-225 watch sweep's dated trigger (Order-881 effective ≤ 2026-12-01 or the
next DMM print — **not re-run here**), and every `R`/`I`/`G` cell in
`docs/codebase-site/data/mechanism-matrix/CAISO.js`.

Next number: caiso-231.
