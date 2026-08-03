# FINDING — nyiso-115: the NYC reserve demand curve was the wrong SHAPE, and NYISO's own posted prices say so

**Date:** 2026-08-03 · **Scope:** NYISO 2023–2025 · **Keeper:**
`2026-08-02-nyiso-113-li-locational` → **`2026-08-03-nyiso-115-nyc-rcpf`** ·
**Pre-registration:** `PREREG-nyiso115-nyc-rcpf-step-curve-2026-08-03.md`
(committed and pushed before either solve).

---

## §1 — the question nyiso-114's instrument made askable

nyiso-114's per-family reserve-dual sidecar showed that NYISO's binding reserve
constraint is overwhelmingly the **NYC locational pair** — `nyc_10min_total`
priced in 17/6/29 hours of 2023/24/25 — and that those hours carry **large
shortfalls at small duals**: up to 307/358/317 MW against a 500 MW requirement,
clearing at $15.63 and $18.75.

A large shortfall clearing cheap is a statement about a **demand curve**, and the
NYC demand curve is a **measured input**. So the question is rule 14
`[R-ACCURATE]`, not a residual: does `NYISO_RCPF_LOCATIONAL` reproduce the
published NYC Reserve Capacity Penalty Factors? That is answerable **without a
solve**, and it was — before one was spent.

## §2 — the instrument, and why the isolation is checked rather than assumed

NYISO posts its Day-Ahead ancillary-service clearing prices **per zone** and per
product (`data/raw/NYISO-AS/NYISO_as_da_<year>.csv`). Its locational regions
**nest** — NYCA ⊃ East ⊃ SENY ⊃ NYC — so differencing zone J (`N.Y.C.`) against
a zone that shares every region **except** NYC isolates the NYC-only shadow
price.

Three zones qualify, and they are used as three independent readings rather than
one convenient one:

| reference | in SENY? | max isolated 30-min adder (23/24/25) | hours at exactly $25.00 | hours above $25.01 |
|---|---|--:|--:|--:|
| `DUNWOD` | yes | $25.00 / $25.00 / $25.00 | 17 / 45 / 141 | **0 / 0 / 0** |
| `MILLWD` | yes | $25.00 / $25.00 / $25.00 | 17 / 45 / 141 | **0 / 0 / 0** |
| `HUD VL` | yes | $25.00 / $25.00 / $25.00 | 17 / 45 / 141 | **0 / 0 / 0** |
| `CAPITL` | **no** | $27.00 / $35.17 / $65.00 | 42 (2024) / 71 (2025) | 4 / 110 |
| `WEST` | **no** | $27.00 / $35.17 / $65.00 | 42 / 71 | 4 / 110 |

The three SENY references agree **exactly**, and the two non-SENY controls do
**not** — they additionally carry the SENY component, and their $65.00 ceiling
decomposes as $25 (NYC) + $40 (the SENY increment), corroborating the ASM values
from a second direction. The isolation is therefore measured, not asserted.

## §3 — LEVEL: confirmed. The model's $25/MW is right.

The isolated NYC adder **never exceeds $25.00 in any of 26,301 hours** across the
three years. And the 10-minute product stacks to **exactly $50.00** in *precisely*
the hours the 30-minute one sits at $25.00 — **5/5, 16/16, 98/98**, with no
exceptions — because a 10-minute reserve also satisfies the 30-minute
requirement, so its price carries both duals.

A potential omission was checked at the same time and **closed**: ASM §6.8 item 2
prices "…New York City… Spinning Reserves" at $40/MW, so a NYC locational *spin*
family the model omits would be a second rule-14 gap. Isolating it
(`spin_10 − nonsync_10`, NYC minus upstate) gives a 1,668–3,257-hour **continuum**
with max $20.91–29.72 and **zero hours at $40** — opportunity cost, not an
enforced RCPF. **The model is correct to omit it.** No action.

## §4 — SHAPE: refuted

The model builds these curves with `critical_mw = 0`, which
`nyiso_rcpf_product_shortfall_steps` discretizes into an **8-step linear ramp**
$3.125 → $25.00 across the whole requirement.

The measured distribution is not that shape. It is a smooth opportunity-cost
continuum below the ceiling **plus one atom exactly AT it**:

| year | material hours (>$2) | **at the $25 ceiling** | **at the model's interior rungs** |
|---|--:|--:|--:|
| 2023 | 103 | **17** | **0** |
| 2024 | 167 | **45** | **1** |
| 2025 | 428 | **141** | **2** |

A linear ramp puts atoms at *every* rung; a single step at the RCPF puts exactly
this. That is the discriminator, and it does not require knowing NYISO's clearing
engine — only that a demand curve's flat regions are where price piles up.

The model's own NYC duals sat squarely on those rungs ($3.125 … $18.75) and
**never reached the published $25.00 in any of 26,280 hours, in either family, in
any year**:

| family | model mean dual when binding | published RCPF | under-priced by |
|---|--:|--:|--:|
| `nyc_10min_total` | $11.39 / $16.15 / $10.47 | $25.00 | **2.20× / 1.55× / 2.39×** |
| `nyc_30min_total` | $3.52 / $6.77 / $4.69 | $25.00 | **7.11× / 3.69× / 5.33×** |

The 30-minute family is worse **purely because its requirement is larger** (1,000
MW vs 500), which makes the same ramp shallower — an artifact of the construction
with no market basis whatsoever.

**A confound checked and excluded.** The NYC families do not carry a static
requirement — `nyiso_dynamic_reserve_requirements` is armed, so their RHS is the
measured as-enforced #1344 hourly series, while the ORDC step *widths* are built
off the STATIC published MW. Where the two differ, the curve is mis-spanned
(exactly the defect `nyiso_ordc_measured_step_span` exists to fix for SENY), and
that would be an alternative explanation for the under-pricing above. It is not
the explanation here: in **every hour in which `nyc_10min_total` actually binds,
in both arms and both years, the hourly requirement is exactly 500 MW** — the
static value — so the widths and the RHS agree wherever it matters, and
`nyiso_ordc_measured_step_span` is `False` on both arms so no width scaling was
applied either way. The shortfall reaches 0.61–0.63 of the requirement, which the
ramp prices at its 5th–6th rung and the published step prices at the full $25.
**The shape is the whole effect.**

## §5 — scope is the measurement's own boundary, not a choice

NYC is the **only** locational region whose published RCPF the measured market
ever reaches:

| region | model max penalty | measured isolated adder, max | verdict |
|---|--:|--:|---|
| **NYC** | $25 | **$25.00 / $25.00 / $25.00** | ceiling reached — shape identified |
| East | $775 | $27.00 / $36.05 / $46.22 | never approached — shape **unidentified** |
| SENY | $500 | $23.92 / $30.37 / **$40.00** | caps at the $40 #1344 increment |
| LI | $25 | no material hours, any year | never binds — shape **unidentified** |

East and LI keep the ramp. **SENY is deliberately not touched**: its $40 ceiling
is the issue-#1344 dynamic-requirement increment, which belongs to
`nyiso_ordc_measured_step_span` and its own pre-registration (rule 19
`[R-ONE-MECH]`). It is reported here as a finding for that lane, **not acted on**.

## §6 — the mechanism introduces no new number

`nyiso_nyc_rcpf_step_curve` (default off, NYISO-only) sets `critical == requirement`
for `NYISO_RCPF_STEP_CURVE_FAMILIES`. That collapses the ramp region to zero
width, leaving the **one band at the same published $25 RCPF** that the existing
constructor already emits for that input. Total step width is conserved, so the
reserve balance row stays feasible at zero reserve. **Ledger 30 → 31 entries,
`n_residual` UNCHANGED at 6** (rule 21 `[R-DOF]`): the level is published and the
shape is measured, so there is nothing in it to tune.

## §7 — gates, and the one that was written wrong

| gate | result |
|---|---|
| **G1** curve armed | **PASS** — the NYC families reach exactly $25.00 in 14/6/19 (10-min) and 2/6/8 (30-min) hours, and sit on an interior ramp rung in **zero** hours of all three years |
| **G2** scope | **see below** |
| **G3** LP row identity | **PASS** — `held + shortfall ≥ requirement` everywhere, tight exactly where the family prices |
| **G4** feasibility | **PASS** — zero unserved-energy slack and zero dump in **both** arms, all three years |
| **G5** span | **PASS** — 2023–2025 in one bundle; holdout freeze ACTIVE and untouched |
| **G6** scoring | **PASS** — both arms scored; determinations identical |
| **K-A** drift | **does not fire** — discharged by construction: every attribution is against the same-HEAD zero-delta control, never the keeper bundle |

**G2 as pre-registered was mis-specified, and it fails.** §7 of the
pre-registration asked for every non-NYC family to be "byte-identical to control
in `dual`, `requirement_mw`, `held_mw`, `shortfall_mw`". But three of those four
are **solved outputs of a co-optimization**: changing one family's demand curve
re-solves the joint reserve/energy dispatch, so other families' held MW and duals
move as an equilibrium response. A gate that can only pass when the mechanism
does nothing cannot distinguish a scope leak from the mechanism working.

Decomposed onto what kill **K-C** actually asks — did the mechanism touch a
family it was not scoped to, which is a question about **construction** — the
answer is clean:

* every non-NYC family's `requirement_mw` and `shortfall_mw` are **byte-identical
  to control in all three years** (0.00e+00, all seven families);
* the solve logs confirm it from an independent direction: **73 → 59 ORDC steps**,
  exactly 14 fewer = 2 families × 7 lost rungs;
* the quantities that do move are `held_mw` on **slack** families — degenerate
  above a non-binding requirement — and `seny_30min_total`'s dual in 2025, which
  is the intended NYC-inside-SENY nesting responding.

**K-C does not fire.** The mis-specification is recorded rather than quietly
redefined, and the gate script now reports both readings.

## §8 — effect, and a null that was pre-registered

Measured treatment-vs-control at one HEAD:

| year | mean zonal price Δ | NYC max ($/MWh) | **LI hours >$300 (C3c)** |
|---|--:|---|--:|
| 2023 | +0.0111 % | 185.61 → **207.49** | 3 → **3** |
| 2024 | +0.0062 % | 199.13 → 199.13 | 0 → **0** |
| 2025 | +0.0213 % | 253.51 → **293.33** | 14 → **14** |

**C3c is unchanged, and §4 of the pre-registration said so in advance.** A step
and a ramp are *both* $0 at or above the requirement, so this changes the **level**
of the reserve price in hours a family already binds and **cannot add binding
hours**. It therefore does **not** reach nyiso-110's everyday-reserve-formation
gap — the model prices reserve in 17/6/34 hours against a measured NYISO DA spin
price above $1 in **100 %** of peak-window hours — and **is not reported as
closing it**. That gap remains open and is untouched by this session.

## §9 — why it is promoted anyway

Determination **CALIBRATED-WITH-CAVEATS**, C3c the sole ledgered caveat. **All
twelve scored numeric fields are EQUAL** between the new keeper and its same-HEAD
control; C1 14/14 all-class and 10/10 free-class, C2/C3a/C3b/C4/C6/C7/C8 PASS in
both arms; zero slack and zero dump.

The promotion rests on rule 1 `[R-STRUCT]` and rule 14 `[R-ACCURATE]`, not on
gate movement: the published curve belongs in the model because it is the real
one. The same ground nyiso-111 and nyiso-113 were promoted on.

**The June-2026 `nyiso 25 rcpf-steep` probe is not a DO-NOT-REDO bar.** It
transferred the **NYCA-30min** curve's `critical = 0.75 × requirement` anchor to
the locational products — a different parameterization derived from a different
family — carried **no matrix row**, and was rejected on the **C3c tail count**,
i.e. on fit, which rule 1 explicitly forbids as grounds for rejecting a
structurally-correct mechanism. The present value is measured from NYISO's own
locational prices.

## §10 — governance

* **Rule 15** — both arms registered on the dashboard in this session.
* **Rule 16** — 2023, 2024, 2025 in one bundle per arm.
* **Rule 22** — the holdout spend freeze is **ACTIVE** and untouched; no year
  outside 2023–2025 solved, scored or read. NYISO's `complete` marker re-keyed
  per D-5(b) with the determination **re-verified on committed artifacts only**
  (identical, not worse); `keeper_at_declaration` preserved. NYISO remains absent
  from `final`, so the locked test stays blocked.
* **Rule 28(b)/(c)** — the matrix row landed in the same PR as the
  `ScenarioConfig` field, seeded `O`, and is updated to `K` in this session; the
  header keeper stamp re-stamped.
* **Rule 27** — every push touching a file ≥ 300 lines blob-verified.

---

## §11 — C3c (brief item 4): both admissible routes closed on measurement, NO lever proposed

The brief allowed C3c only if items 1–3 left room, and admitted exactly two
routes: **(a)** Long Island genuinely tighter than the model has it — a load /
import-limit / availability **data** question — or **(b)** a different oil offer
level, which rule 1 forbids unless it arrives from **measured oil-offer data**.
It also required a **source named in advance**. Both are now closed, with no
solve spent.

**Route (a), leg 1 — LOAD. Named source: NYISO's own posted zonal load actuals**
(`data/raw/zone-specific-demand/NYISO/NYISO_load_actuals_<year>.csv`). The model
does not under-carry Long Island:

| year | LI model mean | LI measured mean | Δ | LI model peak | LI measured peak | Δ |
|---|--:|--:|--:|--:|--:|--:|
| 2023 | 2,212.8 | 2,212.8 | **−0.00 %** | 5,053.9 | 5,048.0 | **+0.12 %** |
| 2024 | 2,254.7 | 2,254.8 | **−0.01 %** | 4,925.1 | 4,932.8 | **−0.16 %** |
| 2025 | 2,278.2 | 2,278.2 | **−0.00 %** | 5,537.2 | 5,530.5 | **+0.12 %** |

NYC matches to the same tolerance (−0.01 % … +0.00 % mean). **Long Island
tightness is not a load question.**

**Route (a), leg 2 — IMPORT LIMITS.** nyiso-114 already measured that both LI
import paths saturate together in the pinned hours (`NYC>Long_Island` 275/275 MW,
`NYISO_external>Long_Island` 1200/1200 MW). Those limits are the **published
Zone-K LCR/TSL locality import cap**, already a measured input, and the matrix
cell `nyiso_gj_locality_tsl` is **G** — governance-refused, so DO-NOT-REDO
(rule 28a) bars re-opening it without new evidence, which this session does not
have.

**Route (a), leg 3 — AVAILABILITY.** Also already measured by nyiso-114: **596.9
MW sits idle at the annual peak-price hour** (561.6 MW oil across 12 tranches plus
35.3 MW of demand response), all *available* and all offered **above** the
marginal rung. The capacity is present and unforced; it is a price question, not
an availability one.

**Route (b) — a different oil offer level — has no admissible source.** §Task-3 of
this session established on the record (and set the matrix cells `G`
accordingly) that **NYISO publishes no submitted-offer disclosure at any grain**.
Without measured oil-offer data, changing the oil rung is exactly the residual
tune rule 1 `[R-STRUCT]` forbids — the model already reaches $503.74 (2023) and
$489.62 (2025) on the same fleet and the same curves, so the ladder demonstrably
extends far above $300 and 2024 simply never calls the next rung.

**Conclusion: C3c stays a ledgered caveat, unchanged at 3/0/14, and NO lever is
proposed.** The novelty here is only that route (a)'s load leg is now *measured*
rather than merely unexamined — it was the one leg nobody had checked, and it is
clean. The exhausted-queue finding for the C3c / peak-half lane is untouched and
still stands.
