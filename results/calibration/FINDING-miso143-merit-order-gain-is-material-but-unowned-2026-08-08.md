# FINDING — miso-143: the coal→gas merit-order gain is **MATERIAL but SMALL** — $2.30–5.47/MWh, 7.5–18.0 % of the 2025 deficit — and **NO mechanism owns it**: all four G-B candidates are eliminated by measurement. Candidate (A) does not close, but it cannot be armed either. The session's largest result is one it did not go looking for: **19.3 GW of capability offered at or below the model's own clearing price sits IDLE**, and congestion is refuted as the cause.

**Session:** miso-143, 2026-08-08. **Lane:** §5.4 queue **item 4 (NEW)** — the
coal-vs-gas merit order in the 2025 high-gas regime, i.e. miso-142's named
successor candidate **(A)**.

**Posture: NO LP SOLVED.** No `ScenarioConfig` field, no parameter, no
mechanism armed, no run registered, **no cell verdict minted** (no mechanism
tested for arming). Keeper **UNCHANGED** at `2026-08-05-miso-132b-cc-committed`
(bundle `results/calibration/miso132_ccmin_B`). Every instrument is a committed
artifact or the orchestrator's own no-solve reconstruction exit; **G-C was never
reached, so no solve was licensed and none was spent.**

**PREREG** `results/calibration/PREREG-miso143-coal-gas-merit-order-2026-08-08.md`,
pushed at **`1f79a700`** (blob **`a7979fd8`**, verified against the remote)
**BEFORE any adjudicating statistic**, with **ten** falsifiable numeric
predictions, **four** pre-committed verdict branches (including the explicit
rounding-error close), **seven** kill-gate bars fixed before their numbers were
seen, and **six** traps each carrying a counter-measurement.

**Owner directive honoured:** the target is the 2024/2025 mean-LMP level miss,
and the arming constraint is the owner's 2026-08-08 addition (*close 2025
without disturbing the rest*). No C7 lane, no C7 ledger.

---

## 0. §0 re-verified from committed artifacts

`calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed`, no
re-solve, all three years in one invocation (rule 16). Rule 22: MISO holds no
marker in either block, so 2023–2025 only.

**`NOT-YET`, rubric v3.1, 8 criteria. SOLE FAIL C3a `price_mean`** — RT
**−0.4 / −6.0 / −14.1 %** (model 32.72 / 30.37 / 39.05 vs 32.85 / 32.30 /
45.46); DA companions **−4.4 / −8.4 / −15.8**. Sole ledgered caveat **C3c, 1 of
1**. C3b PASS **0.075 / 0.112 / 0.191**. C1 / C2 / C4 / C6 / C8 PASS, with C1
SKIPPED for all eight classes in 2025 and C2 SKIPPED for both families
(gas −11.2 %, coal +4.2 %). **Identical to the charter §0 in every cell**;
determination unchanged.

*(Recorded because it is a live discrepancy in the artifacts and it nearly
misled this session at open: the bundle's own `metrics.json` carries
`price_mean: CAVEAT` while the rubric-v3.1 scorer recomputes `FAIL`. The scorer
is authoritative; `metrics.json` is a stale write from an earlier rubric. Not
this session's object, not acted on, but it should not be discovered a third
time.)*

---

## 1. The headline

**Candidate (A) does not close, and it cannot be armed.** Those are two
findings, and the second is the more useful one.

| 2025 JJA h12–17, load-weighted (C3a's own basis) | measured |
|---|---:|
| model | **$44.245** |
| actual (RT, miso-137's verified instrument) | **$74.680** |
| **deficit** | **−$30.435** |
| **merit-order gain, C2-measured displacement (+4.2 %), LOWER bound** | **+$2.297** = **7.5 %** |
| **merit-order gain, C2-measured displacement (+4.2 %), UPPER bound** | **+$5.474** = **18.0 %** |
| *(EIA-930 endpoint, +14.6 %, separately labelled — TRAP 3)* | *+$11.28 → +$28.55* |

**BRANCH-MATERIAL fires**, on the pre-registered thresholds
($1.50 ≤ gain < $9.13), **at BOTH replacement-supply bounds** — so the branch
stands on either and the bracket is not load-bearing. **P4 is CONFIRMED**: the
predicted band was [$0.50, $6.00] with a point estimate of **$2.20**, and the
lower bound came in at **$2.297**.

**But BRANCH-MATERIAL does not license an arm, and its own condition is not
met.** It reads: *"Arm only if G-B resolves to ONE mechanism with measured
identification and every KG bar passes."* **G-B resolved to NO mechanism.** All
four candidates named in the PREREG are eliminated **by measurement**, not by
judgement:

| candidate | verdict | the measurement that killed it |
|---|---|---|
| **B-1** gas offer margin's fixed-anchor form | **INERT as a price channel** | fleet haircut is large (**$5.70**/MWh) but the **price-relevant** haircut — at the tranche actually sitting at the clearing price — is **$0.33**, and its 2023→2025 swing is **$0.18** against a $0.50 inert bar |
| **B-2** delivered coal price | **REFUTED** | trajectory-fallback share is **0.6 %** of coal capability in 2025 (**0.0 %** in 2023/24): 99.4 % of coal is priced at its OWN measured EIA-923 monthly delivered cost, so there is no coal-price input to be wrong |
| **B-3** coal tranche offer-curve slope | **ELIMINATED** | the marginal coal tranches' effective fuel passthrough is **1.000** (2023/24: 0.998/0.997) — the sunk-fuel 0.0 / 0.35 bands are **inframarginal** |
| **B-4** CC/CT heat-rate distribution | **STRUCTURALLY INCAPABLE** | cap-weighted heat rates are flat across years (CC 8.096 / 8.091 / 8.066; CT 14.391; ST_GAS 11.66; COAL 11.054) — they cannot produce a 2025-specific step |

**So the gain is real, material, and unowned.** No admissible mechanism on this
record can deliver it, and manufacturing one to fit the number is precisely
TRAP 6. Per the PREREG the session **reports, names the successor, and queues
it**. Nothing is armed.

---

## 2. G-A0 — the footing gate FAILED, and the bar was not moved

The pre-registered stop gate: a copperplate merit-order clear of the rebuilt
stack against the model's own hourly thermal requirement must reproduce the
keeper's committed P1 price at median |Δ| ≤ **$4.00** and *r* ≥ **0.85**.

| 2025 JJA h12–17 | `lo` (P0 basis) | `hi` (+ measured-horizon startup markup) |
|---|---:|---:|
| model clear | 32.75 | 33.01 |
| keeper P1 | 43.61 | 43.61 |
| **bias** | **−10.86** | **−10.60** |
| **median \|Δ\|** | **9.998** | **9.661** |
| *r* | 0.853 | 0.859 |
| **P1 verdict** | **FAIL** | **FAIL** |

It fails in every year and both windows (bias **−8.7 to −12.8**), and the
startup-markup bracket moves it by **$0.25**. **BRANCH-INSTRUMENT-FAIL fired as
pre-committed.** The bar was **not** moved, the failed reading is reported here
at full magnitude, and the response was the one written down in advance: the
ladder was re-anchored on the keeper's **OWN committed P1 price** and reports
**differences above that anchor only** — the merit-order channel is made of
differences, and a level bias cannot corrupt them.

**A validity check that the re-anchored instrument then passed, independently.**
On the load-weighted basis the six window deficits come out
**−4.75 / −8.333 / −10.676 / −10.671 / −30.999 / −30.435** against miso-142's
committed **−4.75 / −8.33 / −10.68 / −10.67 / −31.00 / −30.43** — **exact in
all six pairs**, against an instrument built independently. *(Reported against
interest: the first version of this probe mixed a load-weighted actual against
an unweighted model mean inside a single subtraction — a basis crossing of
exactly the kind TRAP 3 exists to catch, found by this reproduction check and
fixed before any verdict. It moved the 2025 JJA deficit from −31.07 to −30.435.)*

### 2b. WHY it failed — congestion is REFUTED, and the real answer is bigger

The obvious explanation, and the one PREREG §9 leaned toward, was the
copperplate defect: a system-wide merit order over-uses cheap capacity MISO's
zonal network cannot deliver. **That hypothesis is refuted by its own
prediction.** It requires the under-price to grow with the hour's zonal price
spread. Measured on the keeper's committed per-zone P1 prices:

| zonal price spread | hours | mean under-price |
|---|---:|---:|
| **0.00** (no congestion at all) | 320 | **$12.06** |
| 0.00–2.66 | 414 | $11.20 |
| 2.66–27.83 | 138 | **$9.84** |

*r* = **−0.113**. The under-price is **LARGEST where there is no congestion**.
The relationship runs backwards, so congestion is not the cause.

**What is measured instead is much larger.** In 2025 JJA h12–17 the model
offers **84.2 GW** at or below its own clearing price while serving **65.8 GW**
of thermal requirement:

> **19.3 GW — a 29 % surplus — of capability is offered AT OR BELOW the model's
> own clearing price and is not dispatched.** 2023: 22.0 GW. 2024: 20.0 GW.

By class, idle fraction in 2025: **CT_PEAKER 64.5 %**, **ST_GAS 41.6 %**,
CC_REGULAR 7.3 %, **COAL 4.1 %**. (The CT figure reproduces miso-139 §7 /
miso-142's ~12 GW cushion from a third direction.) **The model's dispatch is
not merit-order at the margin**: cheap capability is held out and dearer
capability is held in. With ST_GAS at **45.1 %** forced (C8, grounded) and
twelve reliability-floor limbs live, the floors are the obvious suspect — but
that is a hypothesis this session did **not** test, and it is §6's successor,
not a claim.

---

## 3. G-A1 / G-A2 — what the ladder actually says

**2025 JJA h12–17, model-only, anchored on the keeper's own P1 price:**

| reading | value | prediction | outcome |
|---|---:|---|---|
| marginal coal SRMC (within $5 below anchor) | **$40.25** | — | — |
| gas SRMC at +1 GW above anchor | **$45.12** | — | — |
| **P3 — SRMC gap, gas − marginal coal** | **$4.86** | [$2, $12], point **$5.00** | ✅ **CONFIRMED**, point near-exact |
| **P8 — marginal-coal effective passthrough** | **1.000** | ≥0.85, point 0.95 | ✅ **CONFIRMED** |
| **P5 — true within-hour ladder slope, +1 GW** | **$1.496**/MWh/GW | ≥$1.00 | ✅ **CONFIRMED** |
| P5 — same, vs miso-142's model-side empirical **0.637** | **2.35×** | point 1.8× | ✅ |
| **P4 — merit-order gain (cap / idle bound)** | **$2.297 / $5.474** | [$0.50, $6.00], point **$2.20** | ✅ **CONFIRMED**, both bounds |

**P5 is a real correction to a prior session's instrument, and it is two-sided
by design, so it could have gone the other way.** miso-142's supply curve is
*empirical* — it bins hours by thermal MW and takes the median price per bin,
which mixes hours with different availability and fuel. The within-hour
**offer ladder** is the true marginal object, and it is steeper in **every**
year-window pair (model side vs model side; the actual-side curve is never
crossed):

| ladder ÷ miso-142 empirical | W1 | JJA h12–17 |
|---|---:|---:|
| 2023 | 1.23× | **3.03×** |
| 2024 | 1.42× | **2.59×** |
| 2025 | 2.49× | **2.35×** |

**And this loosens miso-142's quantity bound.** Walking the model's own ladder
up to the measured actual price takes **16.14 GW** (median; mean 16.8) in 2025
JJA h12–17, against the **47.7 GW** miso-142 computed from the empirical curve
— a factor of **~3**.

**What that does NOT license, stated rather than glossed.** It is tempting to
divide 16.14 GW by miso-142's 13.28 GW cushion and announce that the quantity
family is 1.2× from closing rather than 3.6×. **That arithmetic is not safe
here**, because §2b just measured **19.3 GW of in-merit capability already
idle**: the ladder above the anchor and the "cushion" below it are not disjoint,
and a displacement story cannot spend the same megawatts twice. The honest
statement is narrower and still useful:

> **miso-142's VERDICT survives — no quantity lever of admissible size closes
> C3a in MISO — but its MARGIN was overstated, because the instrument it
> measured the margin with understates the model's own ladder by 2.3–3.0× in
> the summer window. Re-deriving that margin correctly requires resolving the
> in-merit idle block first, and belongs to the successor.**

---

## 4. G-B — the four candidates, and the one that was interesting

### B-1 — the gas offer margin's fixed-anchor form: LARGE, and INERT where it counts

The mechanism is real and it is big. `apply_gas_offer_margin` adds
`markup_hr × (anchor − fuel)` at `gas_offer_margin_anchor = 3.0492` $/MMBtu;
the MISO fleet carries **555 marked-up tranches** at a median `markup_hr` of
**3.34** MMBtu/MWh (cap-weighted 4.43). In the summer window the fleet-wide
haircut is **$7.41 / $5.46 / $5.70**/MWh across 2023/24/25.

**P6 IS FALSIFIED, and in the direction opposite to the prediction — twice
over.**

1. **The premise was wrong.** I predicted 2023 gas sat *below* the anchor (the
   charter's $2.19/MMBtu) so the form would *lift* 2023 offers and *cut* 2025's,
   producing a monotone swing. Measured: the **delivered** gas price in the
   summer window — after basis, citygate and plant-monthly pricing — is
   **$4.28 / $3.93 / $4.24**/MMBtu, **above the $3.0492 anchor in EVERY year,
   2023 included**. The $2.19 figure is the run's annual Henry-Hub-style scalar,
   not what a MISO gas unit pays in July. **I crossed a fuel-price basis inside
   my own prediction** — the very error TRAP 3 is written against, committed in
   the PREREG rather than in the measurement.
2. **The swing has the wrong sign.** Fleet haircut 2023→2025 is **−$1.71**, i.e.
   the cut is *smaller* in 2025, not larger.

**And the price-relevant reading is what settles it.** A haircut on an
inframarginal tranche moves no price. At the tranche actually sitting at the
hour's own clearing price, the haircut is **$0.15 / −$0.22 / $0.33** with a
2023→2025 swing of **$0.18** — **below the $0.50 inert bar fixed in the
PREREG**. The mechanism is large where it does not matter and absent where it
would.

This is **exactly the ERCOT-138 §J scope nuance, reproduced independently in a
second ISO**: the cell stays **K** — the form is armed, adopted and structurally
correct — and re-identifying the anchor or the level is the **wrong lever** for
the defect this lane is chasing.

### B-2 — delivered coal price: REFUTED, and by construction

The keeper runs `coal_plant_monthly_pricing=True`, so a coal plant reporting an
EIA-923 monthly delivered cost is priced at **its own measured cost**. Measured
structurally (a trajectory-priced plant has an identical price in every month;
a measured one varies): the trajectory fallback covers **0.62 %** of coal
capability in 2025 and **0.00 %** in 2023 and 2024. The window delivered coal
price is **$2.342 / $2.383 / $2.310**/MMBtu — essentially flat, and it is the
measured series. **P7 confirmed**; there is no coal-price input left to be
wrong.

### B-3 — the coal tranche offer curve: ELIMINATED at G-A1

The marginal coal tranches' effective fuel passthrough, read back out of the
offer itself as `(offer − VOM) / (HR × delivered fuel)`, is **1.000** in 2025
and **0.998 / 0.997** in 2023/24 — the `coal_econ_srmc_bound` floor doing
exactly what it says. **The sunk-fuel 0.0 / 0.35 bands never reach the
margin**, so the tranche structure cannot be the merit-order channel.

### B-4 — CC/CT heat rates: structurally incapable

Cap-weighted heat rates move by **<0.4 %** across the three years. Heat rates do
not track the gas price; they cannot produce a 2025-specific step. Named last
in the PREREG for this reason, and the measurement agrees.

---

## 5. Predictions scored, against interest

| # | prediction | outcome |
|---|---|---|
| **P1** | footing median \|Δ\| ≤ $4.00 **and** *r* ≥ 0.85 | ❌ **FAILED — 9.998 / 0.853.** The stop gate fired; BRANCH-INSTRUMENT-FAIL |
| **P2** | marginal coal share 30–55 %, point 42 % | ✅ **38.0 %**, and it corroborated miso-142's OLS 43.6 % from an independent instrument |
| **P3** | SRMC gap ∈ [$2, $12], point $5.00 | ✅ **$4.86** |
| **P4** | gain ∈ [$0.50, $6.00], point $2.20 | ✅ **$2.297 / $5.474** — both bounds inside |
| **P5** | ladder ≥ $1.00/MWh/GW, point 1.8× | ✅ **$1.496, 2.35×** |
| **P6** | 2025 haircut ∈ [$0.60,$3.00]; 2023 uplift ∈ [$0.80,$2.50]; swing ∈ [$1.50,$5.00] | ❌ **FALSIFIED on its own inert bar** — price-relevant swing **$0.18** — and the premise was wrong: 2023 delivered gas is ABOVE the anchor, so there is no uplift at all |
| **P7** | model coal price within ±15 % of measured | ✅ trivially — it **is** the measured series (0.0–0.6 % fallback) |
| **P8** | marginal-coal passthrough ≥ 0.85, point 0.95 | ✅ **1.000** |
| **P9** | rebuilt coal reproduces sidecar coal to 1 % | ✅ coal dispatch / capability **0.959**, alias map clean |
| **P10** | CLOSE 30 % · **MATERIAL 55 %** · DOMINANT 15 % | **MATERIAL** — the modal call, but see §6: "material" turned out not to imply "armable" |

**Recorded against interest, five times:**

1. **P1 — my primary instrument failed its own gate.** The copperplate clear was
   the whole design of G-A and it does not work. It is reported at full
   magnitude rather than buried, and the bar was not moved.
2. **P6 was wrong about the premise, not just the number.** I built the
   session's leading G-B candidate on the belief that 2023 delivered gas sat
   below the $3.0492 anchor. It does not, in any year. I read an annual scalar
   as a delivered summer price — a fuel-price basis crossing inside my own
   PREREG. TRAP 3 caught it, but only after it had already shaped the charter.
3. **A basis crossing in my own probe**, found by the miso-142 reproduction
   check: a load-weighted actual subtracted from an unweighted model mean.
   Fixed before any verdict; it moved the 2025 JJA deficit −31.07 → −30.435.
   *A check that only ever agrees has not been tested* — this one disagreed.
4. **PREREG §9 named the wrong reason for the right failure.** I predicted the
   footing would fail from hand-reproducing `runner.py`'s offer sequence, and
   pre-empted that by using the orchestrator's own `fleet_only` exit. The gate
   failed anyway, for a cause I had ranked second and then measured to be
   something else again (not congestion, but a 19.3 GW in-merit idle block).
5. **The charter's framing does not survive its own blocker year.** The lane was
   opened on "coal is marginal in the model". At the model's own clearing price
   in 2025 JJA h12–17 the marginal tranche is **CT_PEAKER 43.7 %** and
   **COAL 20.1 %** — coal's marginal share **falls** in 2025 (33.3 % → 45.7 % →
   20.1 %) while the marginal coal band halves (2,734 → 3,503 → **1,602 MW**)
   and coal runs at **95.9 %** of capability. Three instruments give three
   different marginal-coal shares (OLS absorption 43.6 %, copperplate clearing
   tranche 38.0 %, at-anchor tranche 20.1 %) because they measure three
   different things — and the one anchored on the model's own price is the one
   that bears on price formation.

---

## 6. What this licenses, and the successor

**Nothing was armed and G-C was never reached.** The gain is material but no
admissible mechanism produces it, and sizing one to the number is TRAP 6.

**Candidate (A) is therefore CLOSED AS A LEVER, NOT AS AN OBJECT.** The
substitution is real and worth $2.30–5.47/MWh; it simply has no owner on this
record. Re-opening it requires a **new measured identification of what makes
the model run coal harder than the market did in 2025** — and, per §5(5), that
question should be re-posed at the margin rather than in annual volumes, because
in the blocker year coal is *less* marginal, not more.

**THE SUCCESSOR IS THE IN-MERIT IDLE BLOCK, and it is a price-formation object
with a measured target for the first time:**

> **In 2025 JJA h12–17 the model offers 84.2 GW at or below its own clearing
> price while serving 65.8 GW — 19.3 GW (29 %) of in-merit capability is not
> dispatched. Congestion is refuted as the cause (r = −0.11; the under-price is
> LARGEST at zero zonal spread). CT_PEAKER is 64.5 % idle and ST_GAS 41.6 %,
> against ST_GAS 45.1 % forced (C8, grounded) and twelve live reliability-floor
> limbs.**

That is candidate **(B)** territory — *whatever makes the real curve steep* —
approached from the model's side rather than the market's, and it is the first
MISO object in this lane that is simultaneously (i) large, (ii) measured, (iii)
about price formation rather than quantity, and (iv) not on DO-NOT-REDO. It is
**NOT opened here** (rule 19): it needs its own owner decision and its own
PREREG. Two cautions for whoever takes it:

1. **The floors are a hypothesis, not a finding.** This session measured the
   idle block and refuted congestion. It did **not** attribute the block to the
   floors, and the D-2 attribution must be done before any floor is touched
   (rule 19 `[R-ONE-MECH]`, and rule 17 `[R-FLOOR-WINDOW]` for anything armed).
2. **MISO's scarcity-tail admissible-mechanism list is already recorded as
   EXHAUSTED** (C3c frontier designation 2026-07-20). This is a *different*
   object — in-merit capability idle in ordinary summer hours, not the spike
   tail — but the successor must show that difference explicitly rather than
   re-running that list.

**A governance item the lane must keep carrying.** C1 and C2 are both **SKIPPED
for 2025** on EIA-923 preliminary-vintage grounds, so MISO's largest measured
fuel-mix miss sits in its blocker year **ungated**. This session's entire object
lives inside that blind spot: the +4.2 % coal / −11.2 % gas substitution that
sized the displacement **is not certifiable against EIA-923 until the final 2025
vintage lands**. That is a **reportable limit on this finding**, stated here
rather than left to be inferred, and it cuts both ways — C1/C2 PASS was never
evidence against candidate (A), and it would not have caught a regression
either.

---

## 7. Kill gates

**Not exercised — no arm was proposed and no solve was spent**, so nothing could
disturb KG-1 (C3b 2025 NRMSE 0.191 against the ≤0.200 bar fixed in advance),
KG-2 (C3a 2023/2024), KG-3 (C1/C2 on gated years, with 2025 ungated), KG-4 (C4),
KG-5 (C8 ST_GAS 45.1 % grounded / CT_PEAKER 10.7 %), KG-6 (C3c ledger 1 of 1,
spent) or KG-7 (fail set {C3a}). The bars stand recorded in the PREREG for the
successor that does reach G-C, and the `cc-high-cf-investigation` precedent
stands with them: **a merit-order arm changes fuel mix by construction**, so
C1/C2 are its expected casualty — in a year where C1/C2 cannot see it.

---

## 8. Rule duties

- **Rule 15** — no LP solved, so **no run to register** (the miso-131…142
  precedent).
- **Rule 28(b)** — **no cell verdict minted**: no mechanism was armed, refused,
  or proposed for arming. `gas_offer_net_revenue_margin` **stays `K`** in all
  six lanes; its MISO **reach** was measured, so the cell's note and evidence
  gain miso-143 alongside the parallel ERCOT-138 §J nuance, with **no status
  change**. The **§5.4 queue stamp is written in this session** and item 4 is
  written into the queue. No `ScenarioConfig` field added, so 28(c) does not
  fire; no other ISO's cell touched (28(d)).
- **Rule 22** — 2023, 2024, 2025 only; MISO holds no marker in either block. No
  out-of-training year solved, scored or registered.
- **Rules 13 / 14 / 19 / 21 / 23 / 24 / 25** — every input a measured physical or
  market quantity; the displacement sized by the **measured** C2 miss, never by
  the price residual; no derive script re-run; no tuning channel created; no
  cross-ISO transfer (the ERCOT-138 parallel is cited as a **precedent for a
  measurement pattern**, never as a transferred verdict — MISO's reading is its
  own).
- **Probe hygiene (miso-140b §6)** — all four probes insert the **repo root**
  and assert `load_zonal_shares(...) is not None`, including those consuming no
  per-zone demand.
- **DO-NOT-REDO** — the quantity family was not re-opened as a price lever; the
  price-threshold gap split was not re-run; no level adder; no third `*_lw`
  derivation (miso-137's instrument reused verbatim); `miso_cc_coal_rebalance`
  was not re-opened; miso-134's **trough** work untouched (this is the
  **summer-peak** window).
- **Concurrent-session check** — at open and at close: **zero open PRs on this
  charter and no other live MISO remote branch** (`claude/miso-summer-supply-diagnosis-05q9bm`
  is miso-142's, already merged into `main`).

---

## 9. The generalisable lesson

**A MATERIAL EFFECT WITH NO MECHANISM IS NOT A LEVER.** miso-142 ended by
naming a channel it had not measured and warning against assuming its size in
either direction. Measured, the channel is real and worth 7.5–18 % of the
deficit — comfortably past every "rounding error" threshold — and it is still
**unarmable**, because every mechanism that could deliver it is either
inframarginal, already measured-correct, or structurally unable to produce a
2025-specific step. The gap between *"this effect is material"* and *"this
effect is actionable"* is a whole session's work, and skipping it is how a
fitted parameter gets born.

The corollary is sharper and is this lane's third instrument lesson in three
sessions: **measure a mechanism where it is MARGINAL, not where it is LARGE.**
B-1's fleet-wide haircut is $5.70/MWh and its price-relevant haircut is $0.33 —
a factor of **17**. The same distinction is what separates miso-142's empirical
curve from this session's ladder, and what makes 19.3 GW of *in-merit but idle*
capability a more important number than any of the four candidates that were
chartered.

---

**Artifacts** (all committed):
`results/calibration/PREREG-miso143-coal-gas-merit-order-2026-08-08.md` (`1f79a700`, blob `a7979fd8`) ·
`_miso143_footing.json` · `_miso143_ladder.json` · `_miso143_gb_mechanisms.json` ·
probes `scripts/probes/_miso143_stack.py`, `_miso143_footing.py`,
`_miso143_ladder.py`, `_miso143_gb_mechanisms.py`.
