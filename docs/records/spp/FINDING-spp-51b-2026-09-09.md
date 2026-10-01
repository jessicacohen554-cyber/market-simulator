# FINDING — SPP-51b: the C3a price level is **the missing negative-price regime**, not a level. The band is refused a third time; the object is the **hourly allocation of SPP's measured wind curtailment**, and the price-formation path that would express it is already correct and already wired

**Lane** SPP-51b · **Model** Opus 5 (`claude-opus-5`) · **Date** 2026-09-09 ·
**Branch** `claude/spp-c3a-c3b-price-1i4bgi` · **Base** `15bbb371` (`origin/main` at launch) ·
**PRECOMMIT** `docs/handoffs/PRECOMMIT-spp-51b-2026-09-08.md`, pushed at `6f2ba0b8` **before legs A,
B and C were computed** · **Data profile** `spp` · **Charter** plan §8 W5-r#15 ·
**Owner ruling** P15 ("open the price level").

**LP SPENT: ZERO.** No screen, no control, no arm, no bundle, no registration. `keepers/SPP.json`
untouched; keeper-3 `2026-09-07-spp-3-screened-input` stands. No source file, plan, ledger, log or
other ISO's file touched. Every number below comes from committed artifacts plus six on-recipe
`fleet_only` rebuilds (rule 29 step 0).

**Outcome partition: 3 — (B-PARTIAL), the branch the PRECOMMIT predicted.**

---

## 0. Owner report

### 0.1 Phase 0 in one paragraph

SPP's model does not have a price *level* problem. It has a **missing tail** problem, at the bottom.
The measured market prints **992 / 1,172 / 1,018** hours below \$0 per year; the model prints
**4 / 7 / 0**. Those hours alone contribute **109 % / 222 % / 192 %** of the whole C3a load-weighted
error — more than all of it, because the model's other systematic miss (it is far too cheap above
\$40, which is C3c) partly cancels them. **A multiplier scales a surface; it cannot create a tail.**
That is the mechanical reason the price-family lane's G-2 steepening gate read `+0.5 %` against a
required `≥ 1.783`, and it is why the rule-1 carve-out is the wrong instrument here for the third
time — this time refused on a census of the *hours*, where SPP-46 refused it on a census of the
*inputs*.

### 0.2 Who is marginal in the rich hours, and what their cost is made of (charter 0.1)

In the measured-negative hours the model carries ~18 GW of wind, ~1.9 GW of nuclear and
**10.3 / 11.5 / 11.0 GW of thermal**, and prices at **+\$23.33 / +\$21.06 / +\$23.98** against a
measured −\$11.94 / −\$10.71 / −\$11.44. The marginal unit is a gas unit at its own
`heat_rate × fuel_price + vom`, and — this is the load-bearing part — **the LP is choosing that
thermal economically, not holding it at a floor**: it is 5.3–6.3 GW above the lowest thermal level
the LP reaches elsewhere in the same year, and 7.3–8.7 GW above its annual minimum. There is
nothing to curtail, so nothing can set a negative price.

### 0.3 Which channel the evidence chose, and the number that decided it

**(B), a missing structural object — and it is one limb of a two-limb object.** Not (A): the
model's capacity-weighted SPP gas price is **\$3.213/MMBtu pooled against a \$3.374 KS/OK measured
reference, −4.75 %** — *cheaper* than SPP's own delivered gas, in the pooled reading and in two
years of three. The PRECOMMIT's A-2 said that if the bias were **≥ +10 %** then "(A) is live, it
outranks (B), and this lane's result becomes 'route the fuel-basis repair first'". **A-2 did not
fire.** Reported against the other interest too: moving the fuel input *toward* the reference would
make SPP's gas ~5 % **dearer** and C3a **worse**.

**The number that decided (B).** Rebuilding the keeper's own arrays at HEAD: SPP's wind dispatch
offer is **already −\$26.000/MWh** (the full §45 PTC), and in the **7 / 7 / 3** hours per year where
the LP holds wind strictly inside its bound, **the zonal price is exactly −\$26.00** — in every one
of them. **The price-formation path is correct, complete and already armed.** The model goes long
7 hours a year instead of ~1,000. That is a *quantity* defect in one input, and nothing else.

### 0.4 The object, named exactly

SPP's wind bound is `delivered_EIA930(t) / (1 − 0.096501)` — verified flat to **99.94 / 99.93 /
99.98 %** of hours (leg B-1). `renewables.py`'s own module docstring gives the design intent of the
reference-rate gross-up as *"so the LP still curtails endogenously"*; the keeper re-curtails
**0.00248 / 0.00184 / 0.00043 %** against SPP's measured **9.65 %**. A flat gross-up preserves the
**delivered** shape, and delivered is *already net of* the curtailment — so the rule puts the
missing energy uniformly across all 8,760 hours, i.e. **everywhere except where it actually
occurred**.

**The energy is not missing. Its allocation is.**

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured curtailment energy in the gross-up | 11.006 TWh | 11.676 TWh | 11.798 TWh |
| energy needed to make the measured-negative hours *long* | 5.676 TWh | 7.425 TWh | 5.355 TWh |
| **available / needed** | **1.94×** | **1.57×** | **2.20×** |
| delivered into those hours by the flat rule | uniform — no preference at all | | |

### 0.5 What this lane can and cannot promise the successor

The obvious repair — reallocate the same measured annual curtailment onto the hours the
meteorology says the potential exceeded delivery — was costed here, at zero LP, and **it is not
enough on its own.** §3 measures it: it moves 1.0 / 1.0 / 2.0 GW into the negative hours against a
5.3 / 6.3 / 5.3 GW deficit, closing **17.5 / 15.9 / 38.4 %**. **My PRECOMMIT predicted that against
my own interest (B-4) and it is what happened.** So the honest result is a *named object with a
measured reach*, not a repair ready to arm — and §5 routes what a sufficient instrument would have
to do.

**Reach bound of the whole object** (labelled: **not a fit, not a mechanism, not achievable by any
lever** — it is the arithmetic ceiling of the low tail, computed by pricing the measured-negative
hours at their measured value): C3a **+14.10 → −1.29 %**, **+7.41 → −9.07 %**, **+7.20 → −6.61 %**
on keeper-3's surface. The point is only the magnitude: **the low tail is the whole of C3a and
then some.**

---

## 1. Instrument validation (declared as the precondition for believing anything below)

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| this lane's LW actual | 24.438 | 24.531 | 27.957 |
| committed bench `rt_lw` | 24.44 | 24.53 | 27.96 |
| this lane's C3a | +14.10 % | +7.41 % | +7.20 % |
| registered C3a | +14.1 % | +7.5 % | +7.2 % |

**PASS** — ≤ 0.1 pp in every year. Also established: the committed `rt` series is the **simple mean
of `SPPNORTH_HUB` and `SPPSOUTH_HUB`** (max |rt − mean(N,S)| = 1e-4), which the bench then
load-weights; noted so a later lane does not mistake it for a load-weighted zonal aggregate.

## 2. Leg 0.1 — the decomposition (the table the whole finding rests on)

Contribution of each **measured**-price bucket to the whole-year LW gap; the column sums to the gap.

| measured RT bucket | 2023 hrs / contrib | 2024 hrs / contrib | 2025 hrs / contrib |
|---|---|---|---|
| **< \$0** | 992 / **+3.761** | 1,172 / **+4.043** | 1,018 / **+3.861** |
| \$0–10 | 920 / +1.888 | 1,164 / +2.202 | 1,038 / +2.358 |
| \$10–20 | 2,203 / +2.636 | 2,384 / +2.493 | 1,487 / +2.149 |
| \$20–30 | 2,554 / +1.416 | 2,153 / +1.089 | 2,467 / +1.759 |
| \$30–40 | 1,056 / −0.429 | 790 / −0.372 | 1,304 / −0.247 |
| \$40–60 | 570 / −1.225 | 506 / −1.169 | 841 / −1.425 |
| \$60–100 | 307 / −1.766 | 319 / −1.869 | 386 / −1.963 |
| \$100–200 | 110 / −1.495 | 201 / −2.647 | 145 / −1.852 |
| **> \$200** | 42 / −1.343 | 59 / −1.952 | 68 / −2.628 |
| **total (= C3a gap)** | **+3.445** | **+1.818** | **+2.012** |

Census: model hours < \$0 (system LW) **4 / 7 / 0**; model hours with **any zone** < \$0 **7 / 7 / 6**;
model hours < \$5 **7 / 9 / 4** against measured **1,381 / 1,687 / 1,486**. The surface is compressed
at **both** ends — C3c is the same defect at the top and stays SPP-55's object.

**Surface caveat, carried everywhere.** §2 is **keeper-3's** (pre-repair) surface. `main` now carries
SPP-48's wind repair and SPP-49's seams, under which SPP-50 measured C3a **+15.0 / +12.1 / +14.2 %**.
SPP-50's bundle did not survive its container, so no hourly decomposition of the live surface exists
and **none is claimed**; the object is if anything larger there, because the model's prices in the
negative hours are higher.

## 3. Leg B — the candidate's reach, against the deficit

**Construction, declared in the PRECOMMIT before it was computed:**
`potential(t) = max( delivered(t), Â · Σ_z cap_z·SHAPE_z(t) )` with `Â` the unique scalar preserving
`Σ potential = Σ delivered / (1 − 0.096501)`. **Zero new free parameters.** `Â` = 1.12045 / 1.02856 /
1.02343; the annual-potential identity holds exactly in all three years.

| leg | declared bar | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|---|
| **B-1** gross-up is flat | ≥ 99 % of hours within ±0.5 % of 1.106808 | **99.94 %** | **99.93 %** | **99.98 %** | **PASS** — leg B live |
| **B-2a** reach in the negative hours | between **+1.0 and +5.0 GW** | **+999 MW** | +1,005 MW | +2,022 MW | 2024/2025 inside; **2023 MISSES the declared band** |
| **B-2b** share of hours grossed up | between 10 % and 60 % | 31.9 % | 33.3 % | 27.6 % | **PASS** (today: 100 %, uniformly) |
| **B-3** deficit | computed, no bar | 5,721 MW | 6,335 MW | 5,260 MW | (7,281 / 8,667 / 7,887 MW on the absolute-minimum-thermal basis) |
| **B-4** *against interest* | I expect **B-2 < B-3** | **0.175** | **0.159** | **0.384** | **CONFIRMED — necessary, not sufficient** |

**B-2a is reported in the words it was written in.** The PRECOMMIT said "raises the mean wind bound
above today's by between **+1.0 and +5.0 GW**". 2023 came in at **+999 MW**, below that band. It is
a miss — by 1 MW, on a prediction I wrote myself — and it is recorded as a miss rather than
re-described as "≈ 1 GW".

The candidate does concentrate: 24.7 / 27.5 / 33.3 % of the curtailment lands in hours that are
11.3 / 13.4 / 11.6 % of the year (2.2× / 2.1× / 2.9× enrichment over uniform), and 48.8 / 51.5 /
57.4 % of the negative hours receive some gross-up against 29.7 / 30.5 / 23.7 % of the rest. It is
**strictly better than the flat rule and still 3–6× short**, because a reanalysis shape predicts
*wind availability*, and curtailment is availability **meeting low net load and congestion**.

## 4. Leg A — the fuel basis (charter 0.2), and leg C — two cells closed at zero LP

**Leg A.** Model capacity-weighted SPP gas, from the `fleet_only` rebuilds at HEAD (32.7 GW,
639–641 rows, SPP-49's screen active):

| | model | KS `N3045KS3` | OK `N3045OK3` | KS/OK 50-50 | US |
|---|---|---|---|---|---|
| 2023 | \$2.993 | \$3.205 (−6.6 %) | \$2.851 (+5.0 %) | \$3.028 (**−1.1 %**) | \$3.394 (−11.8 %) |
| 2024 | \$2.872 | \$2.820 (+1.8 %) | \$2.947 (−2.6 %) | \$2.884 (**−0.4 %**) | \$2.745 (+4.6 %) |
| 2025 | \$3.775 | \$4.496 (−16.0 %) | \$3.923 (−3.8 %) | \$4.210 (**−10.3 %**) | \$3.923 (−3.8 %) |
| **pooled** | **\$3.213** | | | **\$3.374 → −4.75 %** | |

**A-1 PASS** (|pooled bias| < 10 %). **A-2 does not fire** (never ≥ +10 %). **A-3 unfalsified**: no
positive gas price produces a negative LMP, and leg C confirms every sub-\$0 model price in the
bundle comes from the wind column. *Instrument limitation, stated:* `FleetArrays.state` is populated
on only **12.0–12.1 %** of gas MW, so the per-state rows above are a 3.9 GW subsample; the
fleet-level model price and the reference series are complete.

**Leg C — both cells adjudicated, `U → I`.**

- **`negative_renewable_offers` → INERT (wind limb) / rule-25 REFUSED (solar limb).** Measured
  `wind_mc = −$26.000/MWh` in all three years, so the flag's floor `min(−26, −renewable_keep_running_value=−20)`
  **is −26**: it changes nothing. The solar limb would put SPP solar at −\$20, which the field's own
  docstring scopes to CAISO's RPS/REC value and forbids re-using on another ISO.
- **`wind_ptc_vintage_offers` → INERT**, and for the reason that matters more than the verdict: it
  makes the wind offer *less* negative, and **a bid change on a column that is never marginal cannot
  move a price** — wind sits at its upper bound in 99.92 / 99.92 / 99.97 % of hours.
- **The declared falsifier fired, and it is this lane's best evidence.** It returned **7 / 7 / 3**
  wind-interior hours, and in **every one** the zonal price is **exactly −\$26.00** (whole-year
  minimum zonal price: −\$26.00 in all three years). The mechanism works. Only the quantity is absent.

## 5. What is routed (no card opened; these are lane items for the SPP desk)

- **R-1 — the successor object: an hourly allocation instrument for SPP's measured wind
  curtailment.** The annual level (SPP-32, 9.65 %) is measured and correct and must not be re-derived
  (rule 23). What is missing is *which hours it belongs to*. §3 shows a wind-availability shape
  recovers only 16–38 %; a sufficient instrument has to key on **oversupply**, not availability.
  Candidates, in the order I would test them: SPP's own published congestion/curtailment products
  (`data/raw/spp-hsl/`, the MMU ASOM figures behind the annual rate); an allocation keyed to a
  measured net-load/oversupply indicator; SPP's own manual-curtailment logs if any are fetchable.
  Rule 13's test applies to whichever wins: it must regenerate for a forward year from forward
  drivers.
- **R-2 — the second limb, which §0.2 measures and this lane did not pursue.** Closing the
  5.3–6.3 GW deficit purely from the wind side needs ~5–6 GW more potential in those hours; part of
  it may instead belong to a **thermal commitment structure** (SPP carries zero floors and zero
  bridges, and the LP takes thermal to 2.8–3.1 GW at its annual minimum). Any such floor is
  rule 17 `[R-FLOOR-WINDOW]` work — driver, window, forward story — and rule 19 says it must be
  reconciled with R-1, never stacked on it. **Sizing note against the limb:** SPP's *measured*
  non-wind non-nuclear output in those hours is ~12 GW, close to the model's, so reality was not
  running much more thermal than the model is — which argues the deficit sits mostly on the wind
  side, i.e. in R-1.
- **R-3 — the zonal spread, a third and separate limb.** Measured mean |North − South| is
  **12.13 / 17.23 / 15.18** \$/MWh; the model's is **0.93 / 0.99 / 1.35**. Both hubs are negative
  together in only 68 / 64 / 68 % of the negative hours, so ~a third of them are *locational*. Even
  a perfect R-1 will under-deliver the LW depth while the two-zone surface prices flat — visible in
  this lane's own §4 evidence, where a −\$26 zone produced only a −\$1.12 to −\$6.22 system LW price.
  This is the keeper note's known zonal-spread miss, now sized against the price object.
- **R-4 — `vre_reference_rate_curtailment_grossup` stays `U`.** Its footprint was measured here at
  zero LP but **no arm was solved**, so no verdict is minted (rule 28(b)); the evidence is appended
  to the cell.
- **R-5 — a note for MISO's desk, not an instruction.** MISO uses the identical flat reference-rate
  gross-up at ~4.9 %. Whether the same shape defect bites there is MISO's measurement to make;
  rule 25 forbids this lane from filling MISO's cell, and nothing here does.

## 6. Rule postures and disclosures

- **Rule 28 `[R-MECH-MATRIX]`.** `offer_curve_by_group` stays **`R`** for SPP. The charter opened a
  door to re-test it on the ground that SPP-46's input confound is now repaired; **this lane declines
  to walk through it**, because §2 refuses the channel on a different and stronger ground than
  SPP-46 did — the residual is a missing *tail*, and no multiplier makes one. The cell's evidence is
  extended with that reason; nothing is re-tested. Cells moved: `negative_renewable_offers` and
  `wind_ptc_vintage_offers`, `U → I`.
- **Rule 29 `[R-SCREEN]`.** Phase 0 was the whole lane, as the charter said it might be. No screen
  year was named because no screen was reached.
- **Rule 29(b).** No control was used, because no arm was solved. Recorded: **keeper-3 does not
  reproduce on `main`'s own inputs** (SPP-48 + SPP-49 are LIVE input-side hunks), so form 4 does not
  hold for SPP; every §2 number is labelled keeper-3's surface. The prompt's cache-key caution is
  moot — no cached solve was reused.
- **Rule 31 `[R-RETAIN]`.** **No bundle was written, so nothing is at risk from this container.**
  The promotion question is therefore not open for this lane: **there is nothing to promote and
  nothing to lose.** The one artifact worth naming is SPP-50's already-registered run, whose bundle
  died in its own lane — if the owner ever revisits P15, that promotion still costs a full ~13 min
  three-year re-solve, unchanged by this lane.
- **Ordering, disclosed again.** Leg 0.1 (§2) was measured before the PRECOMMIT existed; PRECOMMIT
  §0 states that in full and says what would have made it unclean. Legs A, B and C — every leg that
  could have selected anything — were pre-registered with bars, then run. One declared bar (B-2a,
  2023) missed and is reported as a miss.
- **Files touched:** this FINDING, the PRECOMMIT, and SPP's matrix shard cell lines. Nothing else.

---

## Log entry

```
## 2026-09-09 — spp-18: SPP-51b the price level — the object is the MISSING NEGATIVE-PRICE REGIME, not a level; band refused a third time; ZERO LP
Owner ruling P15 ("open the price level") executed as phase 0 alone (charter: phase 0 decides the
lane). Outcome partition 3 (B-PARTIAL), the branch the PRECOMMIT predicted. THE DECOMPOSITION: the
measured-negative hours (992/1,172/1,018 per year, model 4/7/0 on the system LW basis and 7/7/6 with
any zone <$0) contribute 109%/222%/192% of the whole C3a LW error; with the $0-10 bucket,
164%/344%/309%. The model prints 7/9/4 hours under $5 against 1,381/1,687/1,486 measured. The
surface is compressed at BOTH ends -- C3c is the same defect at the top (SPP-55's object) and partly
cancels the bottom, which is why the residual reads as a modest level. A multiplier scales a
surface and cannot create a tail: offer_curve_by_group stays R, refused on an hour census where
SPP-46 refused it on an input census, and the charter's re-open door was declined. (A) IS NOT LIVE:
model cap-weighted SPP gas $3.213/MMBtu pooled vs a $3.374 KS/OK measured reference = -4.75%, i.e.
CHEAPER than SPP's own delivered gas in the pooled reading and in two years of three; the
pre-registered A-2 trigger (bias >= +10% makes the fuel repair outrank the structural object) did
not fire, and moving the input toward the reference would make C3a worse. THE OBJECT: SPP's wind
bound is delivered_EIA930/(1-0.096501), verified flat to 99.94/99.93/99.98% of hours, so the
measured 9.65% curtailment is spread uniformly across all 8,760 hours -- everywhere except where it
happened. The LP re-curtails 0.00248/0.00184/0.00043% against renewables.py's own stated design
intent ("so the LP still curtails endogenously"). The energy is not missing, its ALLOCATION is:
11.006/11.676/11.798 TWh available against 5.676/7.425/5.355 TWh needed to make the negative hours
long, 1.94x/1.57x/2.20x. THE PRICE-FORMATION PATH IS ALREADY CORRECT AND ARMED: wind_mc is already
-$26.000/MWh (full PTC), and in the 7/7/3 hours per year where the LP holds wind inside its bound
the zonal price is EXACTLY -$26.00, in every one. The model goes long 7 hours a year instead of
~1,000 -- a quantity defect in one input and nothing else. THE CANDIDATE REPAIR WAS COSTED AND IS
NOT SUFFICIENT, as the PRECOMMIT predicted against its own interest (B-4): potential(t) =
max(delivered(t), A_hat x reanalysis fleet shape) with the annual-potential identity preserved
exactly and ZERO new free parameters moves +999/+1,005/+2,022 MW into the negative hours against a
5,721/6,335/5,260 MW deficit -- 17.5%/15.9%/38.4%, necessary but not sufficient. B-2a's declared
band was "+1.0 to +5.0 GW" and 2023's +999 MW MISSES it, reported as a miss. Reach bound of the
whole object, labelled not a fit and not achievable by any lever: C3a +14.10 -> -1.29%, +7.41 ->
-9.07%, +7.20 -> -6.61%. CELLS: negative_renewable_offers U -> I (wind limb inert, wind already at
-$26 so the flag's -$20 floor changes nothing; solar limb rule-25 REFUSED, $20 is CAISO's REC
value), wind_ptc_vintage_offers U -> I (makes the offer LESS negative and is unreachable while wind
is at its bound 99.92/99.92/99.97% of hours), vre_reference_rate_curtailment_grossup stays U
(footprint measured, no arm solved, rule 28(b)), offer_curve_by_group R evidence extended. Routed:
R-1 an hourly allocation instrument keyed on OVERSUPPLY not availability (the successor), R-2 the
thermal-commitment second limb with a sizing note against it (measured SPP non-wind non-nuclear
output in those hours ~12 GW, close to the model's), R-3 the zonal spread as a third limb (measured
|N-S| 12.13/17.23/15.18 vs model 0.93/0.99/1.35; both hubs negative together in only 68%/64%/68% of
the negative hours, and a -$26 zone produced only a -$1.12 to -$6.22 system LW price), R-4/R-5.
ZERO LP, no bundle, no registration, keepers/SPP.json untouched, no source file touched. Also
recorded: the committed SPP `rt` series is the simple mean of the two hubs (maxdiff 1e-4).
FINDING: docs/handoffs/FINDING-spp-51b-2026-09-09.md
```
