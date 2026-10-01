# FINDING miso-203 — the summer-peak-demand anchor is the ADMISSIBLE one (miso-139's G-0 refusal is repaired), and it is REFUSED ANYWAY at G-D, because MISO's price tail lives in hours that are NOT the hot hours — it is an EVENING NET-LOAD RAMP object (2026-09-03)

**Session:** miso-203, branch `claude/miso-203-c3a-scarcity-tail-5j2q24`.
**Keeper at open AND at close: `2026-09-03-miso-202-unitclip`** (bundle
`results/calibration/miso202_unitclip_B`) — determination **NOT-YET** on
`{C3a-2025 −12.3845}` alone, C3c the single ledgered caveat, C6 attested
(ledger 41/2).

**NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED. NO RUN REGISTERED. NO
`ScenarioConfig` FIELD ADDED. NO PARAMETER SET. NOTHING WRITTEN UNDER
`data/raw/`.**

**PREREG** `results/calibration/PREREG-miso203-summer-peak-anchor-2026-09-03.md`,
pushed at **`011b2420`** BEFORE any adjudicating statistic, with three gates,
their decision rules fixed in advance, five scored predictions and five traps
with pre-committed counter-measurements.

---

## 1. Headline

**The pre-committed verdict is REFUSED AT G-D.** Queue item 1 is refused — but
for a reason neither the charter nor miso-139 anticipated, and the refusal
carries a finding about **the object** that outlives the lever.

Four results, in the order they were measured:

1. **G-A: the anchor question is settled from primary source, and the charter's
   instinct was right.** EIA states no reference temperature for net summer
   capacity: the rating is *"demonstrated by a multi-hour test, **at the time of
   summer peak demand** (period of June 1 through September 30)"*. The admissible
   anchor is therefore MISO's own measured summer peak-demand dry-bulb —
   **29.5–36.6 °C by zone-year**, not 15 °C, not the summer mean, and not the
   committed `gt_ambient_derate_ref_c = 35.0`, which
   `docs/parameter-citations.md:1314` carries as **"auto-generated,
   needs-citation"**.
2. **G-B PASSES, and this REPAIRS miso-139's G-0.** The charter's claim that a
   rating-condition anchor is summer-level-neutral **by construction** is
   confirmed on the model's own availability matrix: summer-mean capability moves
   by **−0.004 to −0.011 % (CT_PEAKER)** and **−0.002 to −0.004 % (CC_REGULAR)** —
   two to three orders of magnitude inside miso-139's ±1 % basis rule, which was
   inherited verbatim and not relaxed. miso-139 refused convention (A) at
   −3.6…−4.1 % and convention (B) on a −6.8 % annual capability cut; **this third
   anchor fails neither.** The anchoring objection to the merchant ambient derate
   is answered.
3. **G-D FAILS by three orders of magnitude, and not for miso-139's reason.** In
   the 15 scarce hours the mechanism removes **1.3 / 15.3 / 6.7 MW** at MISO's own
   slopes, against a reserve margin of **42.7 / 38.4 / 30.5 GW** — a share of
   **0.00 / 0.04 / 0.02 %** against a 25 % licensing line. Even measured against
   the armed classes' own idle capability alone (15.8 / 11.8 / **5.6 GW** — the
   tail genuinely is tighter than miso-139's window) the removal is **0.12 %** in
   2025. The ORDC cannot climb on this.
4. **AND HERE IS WHY, WHICH IS THE SESSION'S REAL RESULT: the scarce hours are
   not the hot hours.** In **18 of 18 zone-years** the top-1 %-of-actual-price
   Jun–Jul hours sit **BELOW** the summer peak-demand rating condition, by
   **1.4 to 8.4 °C**. A hinge anchored at the rating condition is at its **zero
   point** in exactly the hours the miss lives in. This is not a reach problem
   that a bigger slope could fix — it is a **location** problem, and it holds at
   any slope and any admissible anchor.

**What the 15 hours actually are (G-E, descriptive).** They are the **evening
net-load ramp after solar roll-off** — 13 of 15 fall in **h18–h21** in 2025, and
the scarce-hour mean hour-of-day has migrated **14.4 → 17.1 → 18.3** across
2023 → 2024 → 2025 as MISO's solar fleet grew. Against the 15 highest
**gross-load** Jun–Jul hours of 2025 they carry **11.6 GW less load** but only
**2.2 GW less net load**, because solar collapses from **11,435 MW to 1,859 MW**.
**Zero of 15** are top-15 load hours; **zero of 15** are top-15 dry-bulb hours;
only 4 of 15 are top-15 net-load hours.

**The consequence for the lane, stated as a finding and not as a lever.**
C3a-2025's residual does not live at the peak of load, or of temperature, or of
capacity tightness. It lives in a **ramp** window where the model has ample
quantity (44.3 GW of reserve-eligible idle, 0.0 MWh unserved) and prices the
marginal peaker at $39–166 against an actual $244–1,670. **Any mechanism that
works by removing capability in the hottest or tightest hours is aimed at hours
the object is not in** — which retires the ambient-derate family for this object
on stronger grounds than miso-139's reach argument, and re-aims the queue at
price formation in the evening ramp.

---

## 2. Verdicts against the pre-registered gates

| gate | result |
|---|---|
| **G-A** reference condition (primary source) | **SETTLED.** EIA glossary: the rating is demonstrated *at the time of summer peak demand*. No nominal temperature exists; the committed 35.0 °C is unsourced. §3 |
| **G-B** summer-level neutrality (GATING) | **PASS, by 2–3 orders of magnitude**, for every armed class in every year. miso-139's G-0 objection is REPAIRED. §4 |
| **G-C** tail reach | **1.3 / 15.3 / 6.7 MW** in the 15 scarce hours. §5 |
| **G-D** does it make reserves bind (GATING) | **FAIL** — 0.00 / 0.04 / 0.02 % of the reserve margin against a 25 % line. §6 |
| **N-0** reproduction | **EXACT in 2024/2025** (1.11e-16); a strict **UPPER BOUND** in 2023. §7 |
| *G-E* what the 15 hours are | *descriptive, post-hoc, no decision rule.* §8 |

**Stop rule honoured as written.** PREREG §3: *"If G-B passes and G-D fails, the
session reports that the mechanism is summer-level-admissible but quantitatively
incapable of the tail object, and does not arm."* It did. No field was added, no
solve was spent, and no second anchor was tried after G-D failed (**TRAP 1 armed
and held**).

---

## 3. G-A — the reference condition, and a needs-citation constant

EIA glossary, *Net summer capacity*, retrieved 2026-09-03, verbatim:

> "The maximum output, commonly expressed in megawatts (MW), that generating
> equipment can supply to system load, as demonstrated by a multi-hour test, **at
> the time of summer peak demand** (period of June 1 through September 30.)"

`pmax` **is** that rating (`fleet/eia860.py:1036`). So the anchor is not a
convention to be chosen — it is **fixed by the basis**, and it is a *load*
condition, not a temperature: whatever ambient prevailed when the fleet
demonstrated its summer rating. Measured on the model's own hourly zone dry-bulb,
load-weighted over the top 1 % of Jun–Sep load hours (miso-139 G-1's committed
construction, zero free parameters):

| year | MISO-West | MISO-Plains | MISO-Illinois | MISO-Indiana | MISO-East | MISO-South |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 35.00 | 36.62 | 33.31 | 32.76 | 30.45 | 38.22 |
| 2024 | 29.53 | 34.52 | 32.57 | 31.86 | 31.61 | 35.94 |
| 2025 | 32.25 | 33.34 | 32.70 | 33.02 | 31.90 | 35.67 |

**A recorded defect, not adjudicated here.** `gt_ambient_derate_ref_c = 35.0` is
documented in `scenarios.py` as *"the net-summer capability-test reference (~35 C
/ 95 F, the standard summer GT rating point)"*, but
`docs/parameter-citations.md:1314` carries it as **auto-generated,
needs-citation** — and the measurement above shows the real per-zone rating
condition ranges **29.5–38.2 °C**, so a single scalar cannot express it. This is
a rule-5 `[R-NO-MAGIC]` / rule-14 `[R-ACCURATE]` basis item for whoever next
touches that field. It is **not** a price lever and must not be chartered as one.

---

## 4. G-B — the anchoring objection is answered

Measured on the model's **own** `generators_to_fleet_arrays` →
`_availability_matrix`, so the trailing `np.clip` and every overlay are the
code's. Summer-hours mean capability, arm relative to the same-config control, at
MISO's own identified slopes:

| year | CT_PEAKER summer Δ | CC_REGULAR summer Δ | CT annual Δ | CC annual Δ |
|---|---:|---:|---:|---:|
| 2023 | **−0.0040 %** | **−0.0016 %** | −0.0014 % | −0.0006 % |
| 2024 | **−0.0108 %** | **−0.0036 %** | −0.0037 % | −0.0014 % |
| 2025 | **−0.0067 %** | **−0.0029 %** | −0.0023 % | −0.0011 % |

Against the **±1 %** rule inherited verbatim from miso-139. Every cell passes by
**a factor of ~100–600**, and **the annual integral moves too little to be a
level lever** — so **TRAP 1 of miso-139** (a level cut in shape clothing, which
killed convention (B) at −6.8 % annual) does **not** fire here. Even at the
refused literature slopes the summer move is −0.023 % / −0.011 %; the anchor, not
the slope, is what makes this convention neutral.

**This is a genuine repair of miso-139's G-0**, and it is recorded as such: the
charter was right that the mechanism's anchor was the objection and that a
rating-condition anchor removes it. What the charter did not anticipate is that
removing the objection does not deliver the effect.

---

## 5. G-C — the reach, in the object's own hours

Capability removed, MW, averaged over the 15 scarce hours (the anatomy's own set:
Jun–Jul hours whose **actual** hub RT price is in the top 1 % of Jun–Jul —
thresholds 100.42 / 129.68 / 238.93 $/MWh):

| convention | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **measured anchor, MISO slopes** *(the only armable one)* | **1.3** | **15.3** | **6.7** |
| measured anchor, literature slopes *(diagnostic, rule-25 refused)* | 4.6 | 54.9 | 23.9 |
| `ref_c = 35.0`, MISO slopes *(diagnostic, unsourced anchor)* | 0.8 | 3.1 | 3.1 |
| `ref_c = 35.0`, `gt_ambient` default slopes *(diagnostic)* | 1.5 | 6.2 | 6.2 |

**TRAP 2 held** — miso-139's 732-hour summer-afternoon window is reported beside
it, and at the measured anchor it is **4.2 / 10.2 / 6.8 MW**, i.e. the *same*
order. **TRAP 3 held** — only MISO's own slopes license; the literature and
`gt_ambient` defaults are carried for contrast and never used. **TRAP 5 held** —
the unsourced 35.0 °C anchor does **not** rescue the arm either; nothing here
passes at 35.0 that fails at the measured anchor.

**And the reason the numbers are this small is P1, which I got wrong.** The
scarce-hour ambient against the rating condition, `scarce − T_ref`, °C:

| year | range across the six zones | sign |
|---|---|---|
| 2023 | **−8.37 … −3.72** | below in 6/6 |
| 2024 | **−4.25 … −1.41** | below in 6/6 |
| 2025 | **−3.45 … −1.45** | below in 6/6 |

**18 of 18 zone-years below the anchor.** The hinge is exactly zero at and below
its anchor, so the mechanism is at its **zero point** in the object's hours; the
few MW that survive come only from the handful of individual zone-hours that
briefly exceed their own zone's rating condition.

---

## 6. G-D — the margin, and why no slope rescues this

| year | reserve requirement (Σ four families) | reserve-eligible idle | **margin, min over the 15 h** | removal | **share** |
|---|---:|---:|---:|---:|---:|
| 2023 | 6,460 MW | 54,105 MW | **42,736 MW** | 1.3 MW | **0.00 %** |
| 2024 | 6,761 MW | 53,758 MW | **38,375 MW** | 15.3 MW | **0.04 %** |
| 2025 | 7,148 MW | 44,263 MW | **30,533 MW** | 6.7 MW | **0.02 %** |

Against a **25 %** licensing line fixed in the PREREG. **TRAP 4 held** — the
traversal is stated rather than skipped: a removal inside a unit's own headroom
eats slack and cannot move the marginal unit, and here the removal is 0.02 % of
the slack it would have to consume.

**The one number that moves in the arm's favour, reported in full.** On the
**armed classes' own** idle capability the tail *is* materially tighter than
miso-139's window: **15,789 → 11,752 → 5,621 MW** in the scarce hours, against
miso-139's 11.6–13.3 GW summer-afternoon CT idle. In 2024 and 2025 the armed
classes alone cannot even cover the reserve requirement (margin **−1,869** and
**−5,759 MW**) — coal, nuclear and steam headroom carry it. So the charter's
intuition that the tail is a tighter place than the 732-hour window is **correct
and measured**. It does not help: 6.7 MW is **0.12 %** of even that 5,621 MW, a
factor of ~200 short of the line.

**Why no slope value changes this.** The removal scales linearly in the slope,
so reaching the 25 % line in 2025 would need a slope **~200×** MISO's measured
CT value — 0.73/°C, i.e. total capability loss within 1.4 °C of the rating
point. The literature slope (already rule-25-refused for MISO at 3.5× the
measured value) delivers 23.9 MW, still 0.4 % of the armed margin. **The
parameter debate is moot for the second time in this family**, and for a
different reason than miso-139's: not because the cushion is too big, but
because **the mechanism's driver is not extreme where the object is**.

---

## 7. N-0 — the reconstruction, and a composition-order fact worth recording

Production's `gt_ambient_derate` block is **structurally unreachable on the MISO
keeper**: `arrays.py` guards it with `and not _td_on`, and the keeper sets
`temp_dependent_derate=True` while scoping it to `['CT_CHP','ST_CHP']`. **The
guard is global while the scope is per-class**, so arming `gt_ambient_derate` for
MISO's merchant classes today would change nothing. The hinge was therefore
applied as an overlay on the model's own control availability matrix, and N-0
asserts that overlay against the production block on a
`temp_dependent_derate=False` pair:

| year | max abs diff | cells overlay removes MORE | cells overlay removes LESS | verdict |
|---|---:|---:|---:|---|
| 2023 | 0.109476 | **99,528** (35 units) | **0** | upper bound |
| 2024 | 1.11e-16 | 0 | 0 | **exact** |
| 2025 | 1.11e-16 | 0 | 0 | **exact** |

**The 2023 divergence is diagnosed, not waved through.** Production composes the
derate with the **later** retiree CEMS availability cap (`arrays.py:1407`, an
`np.minimum`) as `min(a·f, cap)`; the overlay computes `min(a, cap)·f`. The two
differ only where that cap binds — 35 units, all CC/CT in MISO-South — and since
`f ≤ 1` the overlay can then only remove **more**. Production is the correct
composition; the overlay is the approximation. **Every reach number in §5 is
therefore an upper bound on the mechanism's real reach**, which is the
conservative direction for a refusal: the arm is refused on numbers that
*overstate* it.

---

## 8. G-E — what the 15 hours actually are (descriptive, post-hoc, NOT pre-registered)

G-C falsified P1 in a direction that raises a question about **the object**, so
the object was characterised. This block carries **no gate and licenses
nothing**; it is written so the next lever is chosen against a measurement rather
than an assumption.

**Where the 15 hours sit in the Jun–Jul distribution of each driver** (mean
percentile rank):

| year | load | net load | dry-bulb | also top-15 load | also top-15 net-load | also top-15 dry-bulb |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | p83.2 | p80.4 | p79.2 | — | **0 / 15** | — |
| 2024 | p83.8 | p83.6 | p84.7 | — | 4 / 15 | — |
| 2025 | **p88.4** | **p94.3** | **p89.6** | **0 / 15** | 4 / 15 | **0 / 15** |

**The driver contrast, 2025** — the 15 scarce hours against the 15 highest
**gross-load** Jun–Jul hours:

| | scarce hours | top gross-load hours | all Jun–Jul |
|---|---:|---:|---:|
| load | 105,843 MW | **117,415 MW** | 86,370 MW |
| **solar** | **1,859 MW** | **11,435 MW** | 4,639 MW |
| wind | 5,965 MW | 5,758 MW | 7,969 MW |
| **net load** | **98,018 MW** | 100,223 MW | 73,762 MW |
| dry-bulb | 30.8 °C | 32.7 °C | 24.9 °C |
| **mean hour-of-day** | **18.3** | 14.5 | 11.5 |

**11.6 GW less gross load, but only 2.2 GW less net load, because solar has
collapsed by 9.6 GW.** The 2025 hour-of-day histogram is `h14:1, h16:1, h18:6,
h19:4, h20:2, h21:1` over 9 distinct days — **13 of 15 in h18–h21**. And the
scarce-hour mean hour-of-day migrates **14.4 → 17.1 → 18.3** across the three
years, tracking MISO's solar build: **the tail is moving into the evening**, which
makes this a forward-relevant structural statement rather than a backcast
curiosity.

**The model is not missing the hours — it is missing their price.** In the three
highest net-load scarce hours of 2025 the model prices 165.58 / 134.45 / 127.64
$/MWh against actual 1,669.52 / 244.22 / 519.43; across all 15 it prices
$38.84–165.58 against $244.22–1,669.52. Its price *ordering* is roughly right and
its *magnitude* is 5–10× short, with 44.3 GW of reserve-eligible idle and 0.0 MWh
unserved.

---

## 9. My prior, scored against interest

| prediction | stated | measured | verdict |
|---|---|---|---|
| **P1** scarce-hour ambient within ±2.0 °C of the anchor | conf. 0.75 | **below by 1.4–8.4 °C in 18/18 zone-years** | **WRONG** — and it is the load-bearing one, exactly as flagged |
| **P2** G-B passes, CT < 0.3 % / CC < 0.15 % | conf. 0.85 | 0.004–0.011 % / 0.002–0.004 % | **RIGHT, badly under-stated** |
| **P3** G-C removal < 300 MW in 2025 | conf. 0.75 | **6.7 MW** | **RIGHT, badly under-stated** |
| **P4** G-D fails, removal < 5 % of the margin | conf. 0.80 | **0.02 %** (0.12 % on the armed-class basis) | **RIGHT** |
| **P5** scarce-hour margin ≥3× narrower than miso-139's cushion | conf. 0.60 | **1.75×** broad (53.5 → 30.5 GW); **~2.2×** on the armed classes (12–13 → 5.6 GW) | **WRONG** — the direction is right, the factor is not |
| net: P(arm licensed and solved) | 0.15 | refused at G-D | slightly too high |

**Where I was wrong, and it changed the finding.** I predicted the scarce hours
would be *near* the rating condition and that the refusal would come from the
cushion, i.e. a quantitative version of miso-139's argument. Both halves are
wrong. The scarce hours are systematically **cooler** than the rating condition,
and the refusal comes from **location**, not reach. Getting P1 wrong is what
produced §8 — the session's most useful output — so the miss is recorded as the
reason the finding exists, not as a footnote to it.

I also under-stated P2 and P3 by two orders of magnitude each. The common cause
is the same one P1 missed: I reasoned about the *summer* temperature
distribution, where a rating-condition hinge is rarely active, and then assumed
without checking that the *scarce* hours sat in its active region. They do not.

---

## 10. What this licenses — nothing armed, and a re-aimed queue

**No lever is licensed and none is proposed.** Concretely:

1. **The ambient-derate family is CLOSED for the C3a-2025 tail object on a second,
   independent and stronger ground.** miso-139 closed it on **reach** (30–39×
   too small against a 732-hour cushion); miso-203 closes it on **location** (the
   object's hours sit *below* the mechanism's anchor in 18 of 18 zone-years, so
   it is at its zero point there). The location argument does not depend on the
   cushion, the slope, or the anchor convention, and it is the one to cite.
   Re-testing needs new evidence about **where the object is**, not about the
   mechanism.
2. **miso-139's G-0 objection is REPAIRED and should not be re-litigated.** A
   rating-condition anchor **is** summer-level-neutral (§4). If the merchant
   ambient derate is ever wanted for **basis correctness** — which is a real
   rule-14 `[R-ACCURATE]` item, since the merchant classes carry a flat
   `SUMMER_CLASS_DERATE` on top of a `pmax` that is already the net-summer rating
   — this is the convention to build, and §4 is the evidence that it is
   admissible. It must **not** be chartered as a price lever.
3. **Two bounded defects are NAMED, neither chartered, neither a lever.**
   (a) `gt_ambient_derate` is **unreachable whenever `temp_dependent_derate` is
   on**, because the guard is global while the scope is per-class — so the flag
   is silently inert on the MISO keeper rather than merely off. (b)
   `gt_ambient_derate_ref_c = 35.0` is **needs-citation** and is a scalar where
   the measured rating condition ranges 29.5–38.2 °C by zone-year.
4. **THE QUEUE IS RE-AIMED BY §8.** The C3a-2025 object is an **evening
   (h18–21) net-load-ramp price-formation** object, in hours that are *not*
   extreme in load, temperature or capacity adequacy, where the model has 44 GW
   of idle reserve-eligible capability and prices the marginal peaker 5–10×
   below the market. Two consequences for lever choice:
   * **Any capability-removal mechanism keyed to heat or to peak load is aimed at
     the wrong hours** and should be bounded at the object's own position in its
     own driver **before** a solve — the cheap check this session was.
   * **The model carries no ramp-constrained product.** `model/reserves/spec.py`
     builds MISO's families as capacity reservations only (`miso_rbdc`,
     `miso_rbdc_regspin`, `miso_subregional_or_midwest`,
     `miso_zonal_or_miso_south`); there is no ramp-capability family anywhere in
     the MISO spec. Whether MISO's real market prices a ramp product in these
     hours is a **primary-source question this session did not answer** (the MISO
     site returned HTTP 403), so this is **NAMED, NOT CHARTERED**: it needs its
     own phase 0 establishing the product from primary source, its measured
     requirement, and its reach against the same 15 hours before any field is
     minted.
5. **The D-2 5(i) seam-response object is untouched by this session** and remains
   the largest named candidate, still awaiting the owner's admissibility ruling.
   §8 adds one datum to it: the scarce hours are ramp hours, so the +3.8 GW of
   binding-hour import the anatomy measured is import arriving *into a ramp*,
   which is the form the ruling would have to address.

---

## 11. Rule duties

**Rule 15 `[R-DASHBOARD]`** — no LP solved, so there is **no run to register**
(the miso-131…139 / miso-179 / miso-194 zero-solve precedent). Keeper unchanged.
**Rule 28(b) `[R-MECH-MATRIX]`** — `temp_dependent_derate` MISO **stays `K`**
(the cell's verdict is the committed **cogen** scope, untouched here); the
**merchant** scope was re-tested under a new anchor and is refused at G-D, and
the cell's note and evidence citation are amended in this session, with a §5.4
queue stamp. No other ISO's cell moved (rule 28(d)); the pre-existing NYISO §5.x
prose drift on main is not this lane's to repair (rule 25).
**Rule 28(a)** — the DO-NOT-REDO argument for re-opening a `REFUSED` cell is
recorded in PREREG §0 and both limbs held up: the object *had* changed (level →
tail) and the anchor *was* new (§4 repairs G-0, which is the proof the re-test
was not a redo).
**Rule 22 `[R-HOLDOUT]`** — 2023/2024/2025 only; MISO holds no
`complete`/`final` marker and the locked-test freeze is active. No out-of-training
year was read, solved, scored or registered.
**Rule 13 `[R-MEASURED]`** — every input is a registration rating, a measured
zone dry-bulb or metered load, entering as a forward-reproducible formula; the
keeper's committed sidecars were read for dispatch, demand and requirement only,
never fed back.
**Rules 1 / 21 / 24** — nothing sized to any residual; the scarce-hour *set* is
used only to **localise** reporting and never entered a construction; no tuning
channel created; nothing written under `data/raw/`.
**Rule 19 `[R-ONE-MECH]`** — no mechanism added; the existing treatments of the
same phenomenon (`temp_dependent_derate`, `gt_ambient_derate`,
`SUMMER_CLASS_DERATE`, `cc_nameplate_summer_derate`,
`coal_nameplate_summer_derate`) were enumerated and reconciled in §10, not
stacked.
**Rules 20 / 23 / 25** — no free parameter added; no derive script re-run; only
MISO's own identified slopes were treated as armable and no non-MISO artifact was
touched.
**Rule 27 `[R-PUSH]`** — no existing ≥300-line source file was rewritten; the two
probes are new files.

---

## 12. The generalisable lesson — **LOCATE THE OBJECT IN THE MECHANISM'S OWN DRIVER BEFORE BOUNDING ITS REACH**

miso-139 taught that a mechanism's anchor is part of the mechanism, and that
bounding its reach settles what a parameter argument cannot. This session
repaired the anchor — correctly, and from primary source — and the mechanism
still did nothing, for a reason that neither the anchor nor the reach argument
would have surfaced.

An ambient derate is a function of temperature. It was refused twice on
*magnitude* questions: how big is the slope, how big is the cushion. Nobody had
asked the prior question: **where does the object sit in the temperature
distribution?** The answer — p90 at best, below the rating condition in 18 of 18
zone-years — makes every magnitude question moot, and it cost one probe and no
solve to establish.

The check generalises to any driver-keyed mechanism. Before bounding the reach of
a mechanism keyed to a driver, measure the **object's own percentile in that
driver**. If the object is not extreme where the mechanism is active, no
parameter and no anchor will reach it — and the measurement that shows this is
usually the same one that tells you what the object *is*. Here it did: the hours
that are only p88 in load and p90 in temperature are p94 in **net load** and 13
of 15 in **h18–21**, which named the object the lane had been circling for four
sessions.

*A mechanism is aimed, not just sized. Check that it points at the object before
you argue about how hard it hits.*

Family: miso-137 *a threshold is a hypothesis, not a definition* → miso-138
*measure an identification's ceiling where the answer is known* → miso-139 *a
mechanism's anchor is part of the mechanism; bound its reach before debating its
parameter* → miso-202 *measure where the residual is before choosing what moves
it* → **miso-203 *locate the object in the mechanism's own driver before bounding
its reach***.

---

**Probes** `scripts/probes/_miso203_summer_peak_anchor_phase0.py`,
`scripts/probes/_miso203_scarce_hour_identity.py` ·
**Records** `results/calibration/_miso203_summer_peak_anchor_phase0.json`,
`results/calibration/_miso203_scarce_hour_identity.json` ·
**PREREG** `results/calibration/PREREG-miso203-summer-peak-anchor-2026-09-03.md`
@ `011b2420`.
