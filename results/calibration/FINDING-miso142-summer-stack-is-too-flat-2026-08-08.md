# FINDING — miso-142: H1 is REFUTED in all three years — MISO's summer-afternoon problem is not a supply *quantity* defect but a **supply-curve SLOPE** defect. The model's stack rises $0.64/MWh per GW where the real one rises $2.15 — 3.4× too flat — so no quantity repair of any admissible size can close C3a. The PREREG stop rule fires.

**Session:** miso-142, 2026-08-08. **Lane:** §5.4 queue item 3 (NEW, owner-set
2026-08-08) — the summer-afternoon supply stack: four owner-observed objects
(O1–O5) against one unifying hypothesis (H1) and its null (H0).

**Posture: NO LP SOLVED**, no `ScenarioConfig` field, no parameter, no mechanism
armed, no run registered, **no cell verdict minted** (no mechanism tested).
Keeper **UNCHANGED** at `2026-08-05-miso-132b-cc-committed` (bundle
`results/calibration/miso132_ccmin_B`). Every instrument is a committed artifact;
G-D was never reached, so no solve was licensed and none was spent.

**PREREG** `results/calibration/PREREG-miso142-summer-supply-stack-2026-08-08.md`,
pushed at **`771cf19c`** (blob `f2315248`, verified against the remote) **BEFORE
any adjudicating statistic**, with **ten** falsifiable numeric predictions, four
pre-committed verdict branches, a stop rule, kill-gate bars fixed before their
numbers were seen, and **seven** traps each carrying a counter-measurement.

**Owner directive honoured:** the target is the 2024/2025 mean-LMP level miss. No
C7 lane, no C7 ledger.

---

## 0. §0 re-verified from committed artifacts

`calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed`, no re-solve,
all three years in one invocation (rule 16). Rule 22: MISO holds no marker, so
2023–2025 only.

`NOT-YET`, rubric v3.1, 8 criteria. **Sole FAIL C3a `price_mean`** RT
**−0.4 / −6.0 / −14.1 %** (model 32.72 / 30.37 / 39.05 vs 32.85 / 32.30 / 45.46);
DA companions −4.4 / −8.4 / −15.8. Sole ledgered caveat **C3c, 1 of 1**. C3b PASS
**0.075 / 0.112 / 0.191**. C1 / C2 / C4 / C6 / C8 PASS. **Identical to the charter
§0 in every cell**; determination unchanged.

---

## 1. The headline

The chartered hypothesis **H1** — that the model fills MISO's summer afternoon
with cheap non-thermal supply (hydro + OTHER + mis-shaped imports) that is not
really there — is **REFUTED**, on its own pre-registered bar, in **all three
years**. The measured quantity is not merely below the +2 GW bar; it is **below
the measuring instrument's own noise floor**.

| 2025 JJA h12–17 | measured |
|---|---|
| ΔQ over {hydro, OTHER, import}, model − actual | **+0.118 GW** (bar: ≥ +2 GW) |
| EIA-930 adjustment-residual noise floor | **1.71 GW** — ΔQ is **0.07×** it |
| model stack slope | **$0.637 /MWh per GW** |
| ΔQ's price reach | **$0.075 /MWh = 0.25 %** of the deficit |
| deficit to close | **−$30.43 /MWh** |
| GW of displacement that would close it | **47.7 GW** |
| idle cushion available | **13.28 GW** → required is **3.60×** the whole cushion |

**And the reason no quantity story can work is the finding.** Built the same way
on both sides — bin the window's hours by the thermal MW that had to be served,
take the median clearing price per bin — the two supply curves are not the same
shape:

| 2025 JJA h12–17 | slope ($/MWh per GW) |
|---|---|
| **model** | **+0.637** (se 0.032, R² 0.477) |
| **actual** | **+2.154** (se 0.318, R² 0.095) |
| ratio | **actual is 3.38× steeper** |

The model's own maximum clearing price anywhere in those 552 hours is **$51.97**,
against a load-weighted actual of **$74.68**. **The model's summer stack never
reaches the actual price at any quantity it ever observes.** That is not a
statement about where the model sits on the curve; it is a statement about the
curve.

Overlaid on a self-centred axis (GW relative to each side's own window median →
median price), the crossing is explicit:

| centred GW | −18.9 | −11.9 | −8.2 | −4.6 | −1.5 | +0.8 | +2.5 | +4.4 | +6.2 | +8.5 |
|---|---|---|---|---|---|---|---|---|---|---|
| **model** | 34 | 36 | 39 | 42 | 41 | 43 | 45 | 45 | 47 | 50 |
| **actual** | 26 | 31 | 39 | 40 | 44 | 48 | 51 | 52 | 62 | 75 |

Over-priced at the bottom, under-priced at the top, crossing near −2 GW. **This
is miso-137's compressed price distribution, seen on the supply curve and
measured as a slope for the first time.** The ratio grows with the C3a miss —
**1.74× (2023) → 3.04× (2024) → 3.38× (2025)** against C3a **−0.4 / −6.0 /
−14.1 %** — so the two are the same object tracked over three years.

**The PREREG stop rule fires as written**, and it is unconditional on O3/O4/O5:

> *"If G-B shows that no quantity displacement of any size within the ~12 GW
> cushion can produce the window deficit at the measured stack slope, the session
> reports 'no quantity lever can close C3a in MISO' and specifies a
> price-formation successor — regardless of what O3/O4/O5 turn out to be."*

---

## 2. G-A — attribution, and the owner's window is confirmed in detail

**G-A0 PASSES all three years**: annual totals **−0.1314 / −1.9330 / −6.4083**
$/MWh against the committed −0.13 / −1.93 / −6.41, additivity residual **exactly
0.0**, on miso-137's verified instrument (reused, not rebuilt — DO-NOT-REDO).

**2025 RT, load-weighted, the full 12 × 24 surface reported; windows marked on
it, never quoted alone (Trap 4):**

| window | hours | C ($/MWh) | share | model vs actual |
|---|---:|---:|---:|---|
| **W1 = Jun+Jul h8–20** | 793 | **−3.5373** | **55.2 %** | 44.44 / 75.44 (**−41.1 %**) |
| — Jun only h8–20 | 390 | −1.6947 | 26.4 % | 43.10 / 74.97 (−42.5 %) |
| — Jul only h8–20 | 403 | −1.8427 | 28.7 % | 45.61 / 75.84 (−39.9 %) |
| **W2 = Jun 21–24 h8–20** | 52 | **−1.4169** | **22.1 %** | 53.51 / 224.15 (−76.1 %) |
| complement of W1 | 7,966 | −2.8710 | 44.8 % | 38.35 / 41.59 (−7.8 %) |

Month totals 2025 ($/MWh): Jan −0.86 · Feb −0.23 · Mar −0.13 · Apr −0.16 · May
**+0.32** · Jun **−1.55** · Jul **−1.81** · Aug −0.33 · Sep −0.73 · Oct −0.21 ·
Nov −0.24 · Dec −0.48.

**The owner's O1 characterization is confirmed, including its internal
structure.** "Concentrated Jun 21–24 and ALL of July" is exactly what the surface
shows: **84 % of June's whole window deficit sits in those four days**
(−1.4169 of −1.6947), while July is **broadly** bad — the full month reads −1.81
and its window −1.84, spread across 403 hours at a nearly uniform −40 %.

**Three qualifications the number itself forces, none of them in the charter:**

1. **The window carries 55 %, not all.** The complement — 7,966 hours — still
   carries **−$2.87/MWh (44.8 %)** at −7.8 %. The gap is roughly 55/45, not
   localised.
2. **W2's 52 hours have a load-weighted actual of $224.15.** That is the
   scarcity regime C3c already ledgers as an accepted model-class limitation.
   *(Characterising a named calendar window, not re-splitting the gap at a price
   threshold — that split is on DO-NOT-REDO and was not re-run.)*
3. **The summer-afternoon deficit exists in ALL THREE YEARS** — W1 carries
   **−0.53 / −1.19 / −3.54** — and 2023 only passes C3a because an
   **over**-priced complement (**+0.40**, +1.4 %) cancels it. miso-137 §4 said a
   passing C3a year here is not evidence of correct price formation; the calendar
   split says the same thing independently.

---

## 3. G-B — signature vs cause: coal IS marginal, and that still does not license the causal claim

**P5 / TRAP 1 discharged first, before anything was attributed to capability.**
In 2025 W1 the model runs CT_PEAKER at **34.2 %** of capability (6,013 of 17,591
MW), holding **11,578 MW idle**; JJA h12–17 gives 36.3 % and 11,239 MW. The
cushion **reproduces miso-139 §7 to the megawatt** on its own Jun–Sep basis —
**17,543.8 / 18,828.3 / 13,719.7 MW** against miso-139's 17,544 / 18,828 /
13,720. *A class 12 GW below its ceiling does not under-run because its ceiling
is 2.5 GW too low*; the miso-141 derate is not re-opened as a cause of O2.

**The marginal class, measured from the model's own behaviour** (OLS slope of
each class's dispatch on total thermal requirement; slopes sum to 1.000):

| 2025 JJA h12–17 | CT_PEAKER | COAL_PRB | COAL_BIT | ST_GAS | CC_REGULAR |
|---|---:|---:|---:|---:|---:|
| dClass/dThermal | **+0.320** | **+0.298** | **+0.138** | +0.113 | +0.099 |

**Coal absorbs 43.6 % of the model's marginal thermal MW in the summer
afternoon.** So O2's coal overrun is not only a level fact — coal is genuinely
*at the margin* in the model, which is the condition the miso-129 bar requires
before any causal claim is entertained.

**But the bar is met and the claim still does not follow at the magnitude
needed**, because the price consequence is the stack slope, and the slope is
$0.64/MWh per GW. The full arithmetic, all years, both windows:

| year / window | deficit | model slope | actual/model | ΔQ (GW) | reach | reach % | GW needed | / cushion |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 W1 | −4.75 | 0.507 | 1.89× | +0.695 | +0.352 | 7.4 % | 9.4 | 0.51× |
| 2023 JJA h12–17 | −8.33 | 0.583 | 1.74× | +1.036 | +0.604 | 7.2 % | 14.3 | 0.86× |
| 2024 W1 | −10.68 | 0.447 | 2.06× | +0.770 | +0.344 | 3.2 % | 23.9 | 1.14× |
| 2024 JJA h12–17 | −10.67 | 0.491 | 3.04× | +0.658 | +0.323 | 3.0 % | 21.7 | 1.16× |
| **2025 W1** | **−31.00** | **0.635** | **2.70×** | **+0.100** | **+0.063** | **0.20 %** | **48.9** | **3.53×** |
| **2025 JJA h12–17** | **−30.43** | **0.637** | **3.38×** | **+0.118** | **+0.075** | **0.25 %** | **47.7** | **3.60×** |

**Branch C in every year-window pair, and Trap 7's guard fires in every one of
them too** — ΔQ is below the EIA-930 residual noise floor throughout, so it is
not assertable as non-zero in either direction.

**An honest limit on what this bounds, stated rather than glossed.** The slope
measures **d(price)/d(thermal *quantity*)**. A coal→gas substitution at constant
quantity is a **different channel** — it changes *which* unit is marginal, not
how many MW are needed — and **this session did not measure that channel's
gain**. It is not bounded by the number above, and it is the successor's target
(§6). Claiming the substitution is harmless because the quantity slope is flat
would be exactly the kind of inference the miso-129 bar exists to prevent.

---

## 4. G-C — the four objects, one at a time

**G-C0 (the Trap 2 direction check) PASSES all three years** before any shape was
compared: actual net import over Jun–Aug is **+5,584 / +3,951 / +3,980 MW**,
positive as the convention requires. The convention itself
(`actual_net_import_MW := −(Total interchange)`, positive = net export in the
file) was fixed in the PREREG from the 74,390-row identity `NG − D − TI ≈ 0`,
which is the smaller residual in **every year of the file**. Recorded because it
nearly went the other way: **the file's very first row satisfies the opposite
identity exactly**, and taking that one row as the convention would have inverted
this session's entire O5 verdict.

### O3 — hydro: **REFUTED AS STATED**, by this session's own pre-registered rule

P6 committed in advance: *"CV ratio ≥ 0.5 **and** level within ±20 % in all years
⇒ O3 REFUTED as stated."* Measured on four independent legs:

| leg | 2023 | 2024 | 2025 |
|---|---|---|---|
| hour-of-day *r* (JJA, vs `NG: WAT`) | +0.890 | +0.869 | +0.864 |
| hour-of-day CV ratio model/actual | 1.00 | 0.90 | 1.21 |
| **monthly** *r* | +0.876 | +0.862 | +0.799 |
| monthly peak month, model vs actual | 5 vs 5 | 6 vs 6 | 6 vs 7 |
| annual level | −12.1 % | −15.7 % | −8.2 % |

Every leg clears. Model hydro is a genuinely dispatched LP resource — **3,503 /
3,769 / 4,254 distinct hourly values**, min 0, max ~2.4 GW — not a flat block.
**And where it errs it errs the wrong way for the hypothesis:** it is *under*
measured in Jul/Aug 2025 (Jul 1,202 vs 1,583 MW; Aug 928 vs 1,131), which would
push price **up**, not down. At 1.5–1.7 % of ISO load this is immaterial either
way. **MISO hydro is not "way off" on any measurement this session could
construct.**

### O4 — `OTHER`: **EXPLAINED, and it is not a dispatch defect at all**

The classification question came first, as the charter required, and it dissolved
the dispatch question. **The MISO fleet contains ZERO `OTHER` units.** The
sidecar's `OTHER` class is an **injected must-run residual**
(`_INJECTED_MUSTRUN_CLASSES = ("biomass", "OTHER")`, `_must_run_profiles`): its
annual energy is its **EIA-923** benchmark, shaped **flat within each month**,
split across zones by demand share, and **netted out of the LP's demand** before
being re-added to the dispatch frame for reconciliation.

Measured structurally rather than asserted: `OTHER` has **exactly 12 distinct
hourly values per year** (as does `biomass`), against hydro's 3,503–4,254. It is
a **demand reduction, not a supply-stack participant** — it can neither set price
nor respond to it.

So the apparent overrun (+60 % to +470 % vs EIA-930 `NG: OTH`, depending on
comparator) is an **EIA-923 vs EIA-930 instrument crossing**, in precisely the
residual bucket where two taxonomies diverge most. For scale, the same two
instruments disagree by **~6 % on coal**, a well-measured fuel. And the reach is
nil regardless: the whole class averages **666 MW** in 2025, so even zeroing it
buys **$0.42/MWh** at the measured slope.

### O5 — imports: a **REAL shape defect**, year-dependent, with **no reach in the blocker year**

Hour-of-day *r*, model `import` vs `actual_net_import_MW`, JJA:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| *r* | −0.236 | **−0.821** | −0.062 |
| CV ratio model/actual | **5.15** | **2.23** | **2.31** |
| annual level | +4.3 % | +4.4 % | −6.8 % |
| W1 delta | +311 MW | +565 MW | **−94 MW** |

Per this session's own pre-registered rule (*"−0.3 ≤ r ≤ +0.3 ⇒ no clear phase
relation, NOT inversion"*): **2024 is genuinely inverted (r = −0.821); 2023 and
2025 are not — they show no clear phase relation.** So the owner's O5 is
**confirmed for 2024 only**, and **2025 — the blocker year — is not an
inversion.**

What *is* wrong in all three years is **dispersion**: the model's import profile
is **2.2–5.2× more variable** than the measured one. With `interchange_shaping=False`
the import profile is set by economics against the seam ladder rather than by any
measured diurnal shape, which is the mechanical origin. Real MISO net interchange
is nearly flat (CV 0.06–0.22); the model's swings (CV 0.31–0.50). **A real
representation defect** — and in 2025 W1 it is worth **−94 MW**, i.e. nothing.

### O2 — coal-for-gas: **CONFIRMED, 2025-specific, and currently UNGATED**

On the **scorer's own basis** (C2, EIA-923 — not my EIA-930 comparison, which
carries the instrument offset above):

| | 2023 | 2024 | **2025** |
|---|---|---|---|
| coal model/actual | −2.4 % | −2.3 % | **+4.2 %** |
| gas model/actual | −5.4 % | −2.7 % | **−11.2 %** |

**2025 is a step change** — coal flips **+6.5 pp** and gas **−8.5 pp** against
two stable prior years. Gas went $2.19 → $3.52/MMBtu; the model re-ranks coal
ahead of gas **harder than the real market did**. On EIA-930's hourly basis the
same substitution reads **+14.6 % coal / −18.3 % gas** in W1 2025.

**And the criterion that measures it is not gated in that year.** C2 2025 is
**SKIPPED for both families** (preliminary EIA-923 vintage: −11.2 % gas, +4.2 %
coal), and C1 2025 is SKIPPED for all eight classes for the same reason. So the
largest measured fuel-mix miss in the blocker year currently scores nothing.

### The Trap 3 inventory, stated plainly as the charter asked

| object | scored by |
|---|---|
| hydro | **nothing** — C8 reports it, SKIPPED as immaterial (1.5–1.7 % of load) |
| `OTHER` | **nothing** — not a key in any criterion |
| `import` | **nothing** — not a key in any criterion |
| coal / gas volumes | C1 + C2 — **but both SKIPPED in 2025** |

Three of the four owner-observed objects sit entirely outside the gated surface,
and the fourth is ungated in the year that matters. **That is a real finding
about where a defect can hide** — and it cuts both ways: it is also why none of
O3/O4/O5 having reach was ever likely.

---

## 5. Predictions scored, against interest

| # | prediction | outcome |
|---|---|---|
| **P1** | W1 carries 45–70 %, point 55 % | ✅ **55.2 %** |
| **P2** | \|C\| bigger in 2025 than 2024; 2023 within ±$1.00 of zero | ✅ (−3.54 vs −1.19; −0.53) |
| **P3** | W2 < 15 % of the 2025 gap | ❌ **point missed — 22.1 %** (falsification bar was ≥25 %, not hit) |
| **P4** | coal +5 % to +30 % in W1 2025 | ✅ **+14.6 %** |
| **P5** | CT < 45 % loaded, > 8 GW idle | ✅ **34.2 %, 11.6 GW** |
| **P6** | hydro flatter + level off > 20 % | ❌ **both legs fail ⇒ O3 REFUTED by my own rule** |
| **P7** | ≥60 % of OTHER capacity is gas; naive comparator *overstates* | ❌ **direction wrong AND object wrong** — see below |
| **P8** | import hod *r* < 0 in 2025 | ⚠️ **−0.062 — inside my own "no clear phase relation" band**; 2024 −0.821 is the inverted year |
| **P9** | ΔQ ≥ +2 GW (H1) vs \|ΔQ\| < 1 GW (H0) | **H0: +0.10 / +0.66 / +1.04 GW ⇒ Branch C** |
| **P10** | slope < $3/MWh per GW, reach < 30 % | ✅ **0.637 and 0.25 %** — confirmed by ~5× and ~120× |

**Recorded against interest, four times:**

1. **P7 was wrong in both directions and about the wrong object.** I predicted the
   naive `OTHER`↔`NG: OTH` comparison would *overstate* the overrun because most
   of `OTHER` would be gas-fuelled. On the repo's own authoritative rollup the
   naive comparison **understates** it (+130/+203/+60 % → +311/+469/+140 %) — and
   then the real answer turned out to be neither: **`OTHER` is not a fleet class
   at all.** I named this in the PREREG §9 as "the most likely way this session
   goes wrong" and it was, just not by the mechanism I named.
2. **My own G-A0 gate caught a defect in my own probe on its first run.** The 2025
   annual total came back `NaN` because the RT actual series has a NaN hour and
   miso-137's `contrib` does not mask. The fix was to adopt miso-137's own G-1
   masking convention verbatim. *A gate that only ever passes has not been
   tested* — this one was.
3. **The `OTHER` probe's first version returned 0 units** against a sidecar
   dispatching ~1 GW, because I filtered on `plant_group`, which is populated for
   the fossil classes only. Caught by an assertion I had written for a different
   reason (TRAP 5's spirit — an unmapped class must fail loudly, never read
   zero). Had it returned a *plausible* number instead of an absurd one, the O4
   verdict would have been wrong.
4. **P3's point estimate missed.** I priced 52 hours at <15 % of the annual gap;
   they carry 22.1 %. The owner's four-day window is far more concentrated than I
   allowed for — Trap 4's counter-measurement (report the full surface) was
   right to be there, but it protected against cherry-picking, not against my
   under-estimate.

**A limit disclosed rather than papered over.** The actual-side supply curve's
R² is low (0.095–0.097): real prices are hugely dispersed at any given quantity,
because outages, congestion and short-term uncertainty all enter. The **slope**
is nevertheless well identified (se 0.318 ⇒ 6.8σ from zero and 4.8σ from the
model's 0.637), and the qualitative result — *the model's own curve never reaches
the actual price* — does not depend on the fit at all.

---

## 6. What this licenses, and the successor

**Nothing was armed, and G-D was never reached.** No object resolved to a
repairable input defect with an existing mechanism *and* material reach:

- O3 hydro — **refuted**, no defect to repair.
- O4 `OTHER` — **explained**; an EIA-923-anchored accounting block, reach $0.42/MWh.
- O5 imports — **a real shape defect**, but its 2025 W1 quantity is −94 MW. Under
  rule 14 it is worth repairing **for input correctness**, and it must **never be
  chartered as a price lever** (the miso-139 §10(3) / miso-141 precedent).
- O2 coal-for-gas — **the only object with a live price channel**, and its channel
  is **merit order, not quantity**, which this session did not measure.

**THE SUCCESSOR IS A PRICE-FORMATION LANE, AND IT NOW HAS A NUMERIC TARGET.**
Not a residual to close — a measured property of the market to reproduce:

> **MISO's real summer-afternoon supply curve rises $2.15/MWh per GW. The model's
> rises $0.64. The model must get ~3.4× steeper in that window, and the
> steepening must be structural (rule 1), never a level adder (DO-NOT-REDO).**

Two candidate objects fall out of this session's own measurements, **neither
tested here and neither licensed by it**:

1. **The coal-vs-gas merit order in the 2025 high-gas regime.** Coal absorbs
   **43.6 %** of the model's marginal summer-afternoon MW; C2 2025 reads coal
   **+4.2 %** / gas **−11.2 %** against two prior years at −2.3 % / −2.7 %. The
   substitution is 2025-specific and tracks the $2.19 → $3.52/MMBtu gas move. Its
   price gain is **unmeasured** and measuring it is the first thing a successor
   should do.
2. **Whatever makes the real curve steep** — offer conduct above SRMC at high
   load, reserve/scarcity co-optimization, congestion, peak-day capability loss.
   Unmeasured here. Note that MISO's admissible-mechanism list for the scarcity
   tail is already recorded as exhausted (C3c frontier designation), so this
   needs a **new measured identification**, not a re-run of that list.

**A governance observation the lane should act on independently:** C1 and C2 are
both **SKIPPED for 2025** on EIA-923 vintage grounds, so MISO's largest measured
fuel-mix miss in its blocker year is currently ungated. That is not a defect in
the rubric — the vintage really is preliminary — but it means the coal-for-gas
substitution surfaced here would not have been caught by the gate board, and a
successor should not read C1/C2 PASS as evidence against it.

---

## 7. Kill gates

Not exercised — **no arm was proposed and no solve was spent**, so nothing could
disturb C3b (2025 NRMSE 0.191 vs the ≤0.200 bar fixed in advance), C1/C2/C4, C8
(ST_GAS 45.1 % grounded), or C3c (ledger 1 of 1, spent). The bars are recorded in
the PREREG for the successor that does reach G-D. **The `cc-high-cf-investigation`
precedent named in the PREREG stands as the standing warning**: any repair that
changes what the thermal fleet must serve should expect C1/C2 to be the first
casualty.

---

## 8. Rule duties

- **Rule 15** — no LP solved, so **no run to register** (the miso-131…141
  precedent).
- **Rule 28(b)** — **no cell verdict minted**: no mechanism was tested, armed, or
  refused. The **§5.4 queue stamp is written in this session**, and item 3 is
  written into the queue. No `ScenarioConfig` field added, so 28(c) does not
  fire; no other ISO's cell touched (28(d)).
- **Rule 22** — 2023, 2024, 2025 only; MISO holds no marker in either block.
- **Rules 13 / 14 / 19 / 21 / 24 / 25** — every input a measured physical or
  market quantity; nothing sized to a residual; no derive script re-run; no
  tuning channel created; no cross-ISO transfer (no other ISO was read).
- **Probe hygiene (miso-140b §6)** — all five probes insert the **repo root** and
  assert `load_zonal_shares(...) is not None`, including those that consume no
  per-zone demand, so the guard cannot rot.
- **DO-NOT-REDO** — the price-threshold gap split was **not** re-run (the
  calendar/hour-of-day split is a different object and is in scope); miso-134's
  **trough** marginal-unit work was not re-run (G-B's **summer-peak** window is a
  different one); no level adder; no third `*_lw` derivation; the miso-141 and
  miso-139 successors were not re-opened as price levers.
- **Concurrent-session check** — zero open PRs and no other MISO remote branch at
  session open and at close.

---

## 9. The generalisable lesson

**A QUANTITY HYPOTHESIS MUST BE MULTIPLIED BY A SLOPE BEFORE IT IS A PRICE
CLAIM.** Four separate objects in this charter were each large enough to look
like an explanation in MW — a 42 % `OTHER` overrun, a phase-inverted import
profile, a 15 % hydro level miss, a 14.6 % coal overrun. Every one of them, when
multiplied by the model's own measured supply-curve slope, buys a fraction of a
dollar against a −$30 deficit. The MW were real; the *reach* never was.

The corollary is the more useful half: **when every quantity in a window is
roughly right and the price is badly wrong, the defect is in the curve's slope,
not in its position** — and the slope is directly measurable from committed
artifacts on both sides, without a single solve.

---

**Artifacts** (all committed):
`results/calibration/PREREG-miso142-summer-supply-stack-2026-08-08.md` (`771cf19c`) ·
`_miso142_gap_attribution.json` · `_miso142_supply_vs_eia930.json` ·
`_miso142_marginal_and_slope.json` · `_miso142_stack_slope_vs_actual.json` ·
`_miso142_other_bucket_and_hydro.json` · `_miso142_verdict_arithmetic.json` ·
probes `scripts/probes/_miso142_gap_attribution.py`,
`_miso142_supply_vs_eia930.py`, `_miso142_marginal_and_slope.py`,
`_miso142_stack_slope_vs_actual.py`, `_miso142_other_bucket_and_hydro.py`,
`_miso142_verdict_arithmetic.py`.
