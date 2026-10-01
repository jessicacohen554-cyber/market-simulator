# FINDING — nyiso-173: the CC availability over-statement is REAL as a bound violation but PROVABLY INERT as a lever — the armed overlay already carries 56 % of the measured shortfall, the model never once reaches its own CC availability envelope, and 2.0–2.7 GW of derated headroom sits UNUSED in exactly the violating hours

**Session:** nyiso-173 · **Date:** 2026-09-02 · **Keeper:**
`2026-08-30-nyiso-159-loss-surface` (determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}) · **Solves run: ZERO.**
**No parameter was touched, no band was swept, no run was registered.**

---

## 0. The result in one paragraph

The brief handed forward nyiso-172 §3.4's one object with a **one-sided proof**:
the measured CC fleet's within-month maximum is a strict lower bound on that
fleet's availability, and the model's CC exceeds it in **93 / 773 / 1,211
hours** of 2023 / 2024 / 2025 at a mean gap of **+224 / +495 / +636 MW**. §3.4
named a cause — `UNIT_OUTAGE_MIN_DAYS = 5` making sub-5-day derates invisible —
and explicitly declined to establish it. **The pre-registered stop condition P1a
fails, and it fails against the hypothesis.** Decomposing the measured CC
fleet's shortfall from its own demonstrated capability inside the violating
hours, the **armed ≥ 5-day overlay already carries 56.5 / 56.0 / 56.2 %** of it
— a majority, stable to half a point across three years — against 37.3 / 35.0 /
37.2 % in the two overlay-blind states combined, and within *those* the carrier
is partial derates (26.0 / 23.4 / 24.2 %), not the sub-5-day full stops §3.4
named (11.3 / 11.6 / 13.0 %), so **P1b fails too**. Measured directly, the
overlay turns out to be working hard: it derates the CC fleet in **100 % of
hours**, to a mean availability of **0.740 / 0.770 / 0.762** of its 13,092 MW
capacity. And then the decisive measurement, which needs no hypothesis at all:
**the model never once reaches that envelope** — 0 hours at it in any year, peak
utilisation 0.794 / 0.821 / 0.839 — and in the violating hours it runs 7,384 /
7,500 / 7,749 MW against an envelope of 10,129 / 10,129 / 10,112 MW, leaving
**2,745 / 2,630 / 2,363 MW of derated headroom UNUSED** (still **2,391 / 2,275 /
2,010 MW** net of a 3.5 % CC WEFOR). **An availability input would have to
remove more than three times the entire +636 MW gap before it began to bind at
all**, and the envelope is demonstrably not already over-tight — the measured
fleet exceeds it in **0** hours of all three years, with and without East River.
The object is additionally **portfolio-only**: the model exceeds the *additive
per-plant* bound `Σ_p M_p,m` in **0 hours** in every year (P3 fails). **The
whole availability-input family is adjudicated provably inert against this
object, ex ante, with no solve spent** — and the bound violation is relocated to
the merit-order/economics object nyiso-170 and nyiso-172 §3.2 already own,
observed on the CC side.

## 1. What was measured, and off what

Zero solve throughout. Every series is a committed artifact or a raw measured
record.

| instrument | source |
|---|---|
| model hourly MW by class | keeper `hourly/class_hourly_<year>.parquet`, pass **P1** |
| model hourly zonal demand | keeper `hourly/system_<year>.parquet`, pass **P1** |
| what already forces CC | keeper `legitimacy_diagnostics.json`, D-2 rows |
| armed availability config | keeper `run_config.json`, `scenario_config` |
| measured hourly MW per unit | `data/raw/campd-unit-level/NY_<year>.parquet`, `grossLoad` |
| class construction | CAMPD `unitType` × EIA-860 CHP flag — the nyiso-170/172 construction, unchanged |
| armed overlay windows | `data/raw/campd-unit-outages-NYISO.csv` (≥ 5-day) |
| lay-up reclassifications | `data/raw/campd-unit-outages-layup-NYISO.csv` |
| the overlay's own multipliers | `market_sim.data.outages.unit_outage_derate_factors` — **the engine's function, not a reimplementation** |
| the LP's CC bin capacity | `market_sim.data.outages._iso_plant_capacity(..., cc_nameplate_basis=True)` — reproduces `fleet_to_bins`' nameplate raise exactly (the caiso-184 identity) |
| actual price | `data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet` |
| clock | `STD_TZ = "Etc/GMT+5"` |

**Instrument validation.** The probe reproduces nyiso-172 §3.4 **exactly** off
its own independent per-unit construction: violation hours **93 / 773 / 1,211**
and mean gap **+223.9 / +494.6 / +635.7 MW** against §3.4's +224 / +495 / +636.
Nothing below rests on a re-derived object.

**One instrument defect of this session's own, found and repaired before any
result was read.** CAMPD reports `grossLoad` as NULL for a non-operating
unit-hour (52 % of NY CC unit-hours in 2025). nyiso-172 read the series through
`groupby().sum()`, which skips nulls; this probe's first pass used `np.add.at`,
which propagates them, and returned 0 violation hours and NaN gaps. The loader
now fills nulls to zero explicitly, which is what makes the reproduction above
exact. The gates were untouched by the repair — no result had been read when it
was made.

**`cap_u`, the per-unit capability reference, is the unit's own within-year
maximum `grossLoad`** — a *demonstrated* lower bound, the same logic as the
fleet bound itself. It is availability-INCLUSIVE, so a unit derated all year
measures a depressed `cap_u` and every shortfall statistic here is
**conservative**. Declared in the prereg before running, not discovered after.

**Detector thresholds are the code's own** (rule 23 `[R-FROZEN-DERIVE]`):
`ST_GAS_CF_PEAK = 0.02` (the event-based off threshold the CC/gas-steam detector
itself uses), `ST_GAS_MIN_OUTAGE_HOURS = 120`, `_CEILING_FRAC = 0.65`. None was
chosen, none was swept.

**Rule 13 `[R-MEASURED]` compliance.** CAMPD enters only as *conduct
identification*. The within-month bound is a measured **outcome used as
evidence** and is never fed back as an input; nothing is pinned to observed
generation; no statistic is tuned to any residual.

**Rule 22 `[R-HOLDOUT]`.** Every year read is 2023, 2024 or 2025. NYISO's
`complete` marker was declared 2026-07-31 and **withdrawn 2026-08-30**, and
NYISO has never appeared in `final`. Nothing out-of-training was read, solved,
scored or registered, and **no marker was requested**.

**Reproduction of the eight inherited probes.** All eight were re-run before
anything was measured, and all eight reproduce: nyiso-167 gain **0.703**, offset
**$11.03**, R² **0.910**; nyiso-168 deficit **−$6.59 = −$2.32 gradient + −$4.27
level**; nyiso-168 reserve ceiling **10.01×** thermal-only; nyiso-169 DA
coverage 8,760 h/yr with `ANY LINK CARRIES ALL THREE YEARS: True`; nyiso-169b
`PEAK-BAND PROPOSAL SUPPORTED: False` with ST_GAS **−28.6 %** / all-months-
negative **True**; nyiso-170 `proceed_to_phase_2: false` with G3 alone true;
nyiso-170b/c/d survival **True**; nyiso-171 coverage **0.253 / 0.502 / 0.313**
and over-run **51.1 / 69.3 / 80.4 %**; nyiso-172 all six gates false. The three
documented traps were hit and handled as prescribed: **(a)** the reserve-slack
JSON reproduced to float noise only (eight lines, e.g.
`30447.499999999996` → `30447.500000000004`) and the churn was **reverted, not
committed**; **(b)** the container held **0 DA months** against 21 RT, so the
congestion probe would have degraded silently — repaired with
`fetch_nyiso_zonal_lmp.py --start 202301 --end 202512 --kind both` (36 DA months
staged) then `regenerate_clean.py nyiso-interface-flows`, after which DA
coverage reads **8,760 h/year**, not the degraded 1,464; **(c)**
`STD_TZ = "Etc/GMT+5"` throughout.

## 2. The pre-registered gates and their outcomes

Registered in `results/calibration/PREREG-nyiso173-cc-availability-anatomy.md`
and committed **with the probe, before either was run** (`278ddf37`).

| gate | PASS condition | outcome |
|---|---|---|
| **P1a** | overlay-blind states carry > 0.50 of violation-hour shortfall, all 3 yr | **FAIL — 0.373 / 0.350 / 0.372**, §2.2 |
| **P1b** | given P1a, sub-5-day full stops (B) > partial derates (C) | **FAIL — B is half of C**, §2.2 |
| **P2** | 2025 gap > 0 in top-3 price deciles, top-3 load deciles, every on-count quintile | **PASS**, §2.3 |
| **P3** | model exceeds the ADDITIVE per-plant bound in ≥ 1 % of 2025 hours | **FAIL — 0 hours, all years**, §2.4 |
| **P4** | rule 19 attribution complete (reported, not gated) | **complete**, §2.1 |

`proceed_to_phase_2: false`. **The prereg §3 stop condition fires on P1a**: the
named cause is refuted, and no input is proposed.

### 2.1 P4 — what shapes CC availability today (rule 19 `[R-ONE-MECH]`)

**Exactly one armed channel**, from the keeper's own `run_config.json`:
`outage_source = "historic"` — the CAMPD ≥ 5-day per-unit outage overlay
(`campd_outage_windows`, `K`), carrying **2,928 CC rows** in
`campd-unit-outages-NYISO.csv`. Everything else in the family is **off**:

| field | value | note |
|---|---|---|
| `historic_outage_overlay` | False | the removed facility-summed overlay |
| `unit_outage_short_windows` | False | **and provably inert — see below** |
| `unit_partial_outage_windows` | False | **and provably inert — see below** |
| `unit_outage_maxgen_events` | False | **and provably inert — see below** |
| `unit_outage_lp_capacity_basis` | False | §5 |
| `unit_outage_fleet_status_scope` | False | untested for NYISO |
| `temp_dependent_derate` | False | `G`, refused ex ante at nyiso-111 |
| `gt_ambient_derate` / `cc_winter_capability_basis` / `cc_outage_derate_from_top` | False | §4 |
| `cc_nameplate_summer_derate` | True | raises CC bins to full nameplate |
| `wefor_residual` | **null** | the FULL statistical CC WEFOR applies **on top of** the measured overlay — the caiso-186 rule 19 double count, live here too (§5) |

**Three channels a successor would reach for first are PROVABLY INERT for
NYISO, by empty file rather than by argument** — measured, not asserted:

| extract | rows | why |
|---|---|---|
| `campd-unit-outages-short-NYISO.csv` | **0** | the short-window detector is **coal-only**; NYISO has no coal |
| `campd-partial-outages-NYISO.csv` | **0** | the partial-plateau detector is likewise coal-only |
| `campd-unit-outages-maxgen-NYISO.csv` | **absent** | `data/raw/maxgen-events/` carries **`miso` only** — no NYISO registry exists |

All three sit on the matrix's single `unit_outage_short_windows` row (its `def`
registers all three window shapes), whose NYISO cell already reads `I` from
nyiso-93; this session adds the **measured** grounds.

**D-2 forcing of CC** is modest and unchanged: `chp_steam` on CC_CHP
(0.05 / 0.14 / 0.10 % of class) and `nyiso_gas_commitment_bridge` on CC_REGULAR
(4.37 / 3.83 / 3.29 %). **Any change proposed here would have to replace or
reconcile the one armed overlay, never stack on it** — and §2.5 is why none is.

### 2.2 P1a/P1b — THE STOP CONDITION: the overlay already carries the majority

The measured CC fleet's shortfall from its own demonstrated capability,
`Σ_u (cap_u − gen_u,t)`, partitioned over the **violating hours** into four
mutually exclusive per-unit-hour states (assigned A → B → D → C, so they
partition it exactly):

| state | meaning | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| **A** | inside a detected ≥ 5-day window — **VISIBLE, ARMED** | **0.565** | **0.560** | **0.562** |
| **B** | off, in an episode **< 120 h** — INVISIBLE | 0.113 | 0.116 | 0.130 |
| **C** | on but below capability — INVISIBLE | 0.260 | 0.234 | 0.242 |
| **D** | lay-up window — deliberately excluded (economic) | 0.062 | 0.090 | 0.066 |
| | **B + C, the overlay-blind total** | **0.373** | **0.350** | **0.372** |

The gate required B + C > 0.50 in all three years. It is **0.35–0.37**, and the
armed overlay's own share is a **majority in every year, stable to half a
point**. Over all 8,760 hours rather than the violating subset the picture is
the same (A 0.536 / 0.523 / 0.521).

**P1b fails on top of that**: within the blind remainder the carrier is
**partial derates (C), at roughly twice the sub-5-day full stops (B)** — so even
the *minority* is not the thing §3.4 named. The duration histogram says why: NY
CC off-episodes are overwhelmingly *very* short (2025: **1,852** episodes under
24 h, 349 of 24–72 h, 187 of 72–120 h, 427 of ≥ 120 h), and a fleet of 68 units
cycling overnight generates thousands of sub-day stops that are economics, not
outages — which is precisely why the CC/gas-steam detector is event-based in the
first place. **The 5-day floor is not what is missing.**

### 2.3 P2 — the gap is not a shape artifact (the one gate that passes)

nyiso-172 §6 flagged that the +636 MW mean gap is two-sided and could be
produced by dispatch shape. In **2025** it survives every conditioning:

| conditioning | result |
|---|---|
| by actual DA price decile | +652, +704, +596, +622, +615, +637, **+809, +800, +717, +205** — positive in all ten |
| by model load decile | +543 … +732 … **+665, +349** — positive in all ten |
| by measured online-unit-count quintile | +775, +758, +591, +656, **+398** — positive in all five |

2024 passes all three legs identically. **2023 fails the on-count leg** (top
quintile **−6.4 MW**) and is reported as such; the gate binds on 2025, the
failing year, exactly as pre-registered. So the gap is **not** economics-shaped
in the failing year: it does not vanish at the top of the price distribution,
where no rational unit is backed off. **This is the one leg of the brief's
phase-0 question that answers in the object's favour** — and §2.5 is why it
still does not produce a lever.

### 2.4 P3 — it is a PORTFOLIO statistic, exactly the nyiso-171 failure mode

The additive per-plant bound `Σ_p M_p,m` (each plant's own within-month maximum,
summed) is ≥ the fleet bound by construction, so exceeding it is a strictly
stronger claim:

| year | hours above the FLEET bound | hours above the ADDITIVE per-plant bound | coverage `M_fleet / Σ_p M_p` |
|---|---|---|---|
| 2023 | 93 | **0** | 0.807 |
| 2024 | 773 | **0** | 0.831 |
| 2025 | 1,211 | **0** | 0.803 |

**The model's CC never exceeds what NYISO's CC plants individually demonstrated
they could produce — only what they demonstrated *simultaneously*.** About 20 %
of the bound's tightness is non-coincidence rather than unavailability. The
object is therefore **portfolio-only**, and must be quoted at that strength: it
is the same discriminator nyiso-171 used to kill the CC_CHP floor, applied to
this session's own inherited object and reaching the same verdict.

**East River (2493), measured.** The unrepaired nyiso-171 §5 crosswalk defect —
`ST_CHP` in `thermal_tranches_NYISO.csv` but `CC_CHP` under the shared CAMPD
construction — inflates the *measured* CC series and therefore **loosens** the
bound. Removing it raises the violation count **93 → 208, 773 → 1,500,
1,211 → 1,864**: the defect masks roughly a third of the violating hours. That
is a real and material finding for whoever repairs the crosswalk, and it does
**not** change P3, which is computed on the additive bound.

Plants carrying the violation-hour shortfall (2025, GWh): 55405 **1,196**,
57185 **900**, 10725 **508**, 2539 **445**, 55375 **425**.

### 2.5 The decisive measurement — reported IN ADDITION to the gates

S1–S3 are **not** pre-registered gates. They were measured *because* P1a failed,
and are reported in addition to the registered gates, never in place of them
(the nyiso-171 A5b / nyiso-172 S7–S10 discipline).
`results/calibration/_nyiso173b_overlay_delivery.json`.

**S1 — the overlay's routing delivers.** **2,880 of 2,928** CC rows land on a
model fleet bin; **48 (1.64 %)** are dropped, all of them plant **2682**
(S A Carlson), whose extract rows are tagged `CC_REGULAR` while the model fleet
carries only `ST_GAS` (45 MW) and `CT_PEAKER` (42 MW) bins for it. That is the
Ravenswood-2500 class-tag mismatch `_FLEET_GROUP_OVERRIDE` exists to repair, at
87 MW — **0.7 % of CC capacity**. Named for the record; far too small to be this
object, and out of this session's scope.

**S2 — the overlay is working hard.** Against the LP's own nameplate-raised CC
capacity of **13,092 MW**, the overlay derates the fleet in **100 % of hours**,
to a mean availability of **0.740 / 0.770 / 0.762**.

**S3 — and the model never reaches that envelope. Not once.**

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| hours the model is **at** its CC envelope | **0** | **0** | **0** |
| peak utilisation of the envelope | 0.794 | 0.821 | 0.839 |
| *in the violating hours:* envelope | 10,129 | 10,129 | 10,112 MW |
| *in the violating hours:* model CC | 7,384 | 7,500 | 7,749 MW |
| *in the violating hours:* measured CC | 6,338 | 6,192 | 6,102 MW |
| **UNUSED derated headroom** | **+2,745** | **+2,630** | **+2,363 MW** |
| unused headroom **net of a 3.5 % CC WEFOR** | +2,391 | +2,275 | **+2,010 MW** |
| hours at the WEFOR-net envelope | **0** | **0** | **0** |

**This is what makes the availability family inert, and it needs no
hypothesis.** In the very hours the model violates a measured lower bound on CC
availability, it is leaving **two to two and three-quarter gigawatts** of
already-derated CC capability on the table. A measured availability input can
only lower the envelope; to change a single megawatt-hour of dispatch it would
first have to remove **2.0 GW — more than three times the entire +636 MW gap** —
and only then begin to bind. **No admissible measured input is remotely that
large**, and one built to be that large would be a derate fitted to make the
model's CC land under the bound, which rule 13 `[R-MEASURED]` forbids and the
brief named as the one trap to avoid.

**And the envelope is not already over-tight**, so this is not an artifact of
over-derating: the **measured** fleet exceeds the envelope in **0 hours of all
three years**, with and without East River. The overlay asserts no incapability
the CEMS record refutes — the caiso-185 failure mode is absent here.

## 3. What the object actually is

nyiso-172 §3.4's bound violation is **real and its proof stands**: the model's
CC output does exceed a strict lower bound on the measured fleet's within-month
availability, in 1.06 / 8.82 / 13.82 % of hours, growing with the failing year.
What this session establishes is that **the violation is a symptom, not a
cause** — and specifically not a cause located in the model's availability
representation:

* the armed overlay **already carries the majority** of the measured shortfall
  in those hours (P1a);
* the model's CC envelope is **nowhere near binding** in them (S3);
* the model exceeds no plant's own demonstrated capability, only the fleet's
  coincident one (P3).

So the model runs more CC than the market did **by choice inside a correctly
derated envelope**, not because it believes machines are available that were
not. That is an **economics/merit-order** object — precisely where nyiso-170 §4
(the controlled `ds_CC`-vs-price-gap association) and nyiso-172 §3.2 (the model's
cost stack doing *correct* isolated physics while the market leaned the other
way) already left it. This session's contribution is to close the one route that
looked like it escaped that framing.

**The rule 14 `[R-ACCURATE]` framing the brief opened with does not survive
contact with the measurement, and it is worth saying why precisely.** Rule 14
governs swapping an *estimate* for accurate measured data. Here there is no
estimate to swap: the accurate measured availability data is **already in, already
applied, and already the sole armed channel**, and the three unarmed channels
are empty for NYISO by construction. The remaining question was never accuracy
but *sufficiency* — and S3 answers it: even a perfectly complete availability
input cannot reach an envelope the LP is not using.

## 4. Lines this session closes

* **CLOSED — the `UNIT_OUTAGE_MIN_DAYS = 5` floor as the cause of the CC
  availability over-statement.** Failed its own pre-registered gate: the armed
  ≥ 5-day overlay carries **56.5 / 56.0 / 56.2 %** of the violation-hour
  shortfall, and within the blind remainder partial derates outweigh sub-5-day
  full stops about two to one. Do not re-open the 5-day-floor framing for NYISO
  CC without an instrument that survives that split.
* **CLOSED — the whole MEASURED-AVAILABILITY-INPUT family as a lever against
  this object**, ex ante and for any construction, on S3: the model reaches its
  CC envelope in **0 hours** of all three years and leaves **2.0–2.7 GW**
  unused in the violating hours, so an input would have to remove > 3× the gap
  before binding. Re-open only if a future keeper's CC utilisation reaches its
  envelope — which is a measurable, stated re-open condition, not a judgement.
* **CLOSED — `unit_outage_short_windows`, `unit_partial_outage_windows` and
  `unit_outage_maxgen_events` for NYISO, on MEASURED grounds** rather than the
  ex-ante argument nyiso-93 had: the first two extracts are **0 rows** (coal-only
  detectors; NYISO has no coal) and no NYISO maxgen registry exists. Arming any
  of the three is a literal no-op.
* **DOWNGRADED, not closed — the bound itself.** It is **portfolio-only**: 0
  hours above the additive per-plant bound in every year, coverage 0.80–0.83.
  It must be quoted at that strength from here on, including in any citation of
  nyiso-172 §3.4.
* **NOT OPENED — any capacity or nameplate change**, `cc_winter_capability_basis`
  included (refused ex ante in the prereg §4; additionally blocked at CAISO on
  an unresolved rule 19 WEFOR double count that is not NYISO's to resolve).
* **NOT OPENED — any C3c lever**, per the brief.
* **NOT RE-TESTED — the twenty closed lines** carried into this session.

## 5. What is handed forward

**The object returns to the merit-order lane, where it is already adjudicated.**
This session produces no lever and names no successor input, because the
measurement says none exists in this family.

Three measured items are handed forward, none of them scoped here:

1. **The East River (2493) crosswalk defect is materially larger than recorded.**
   It masks **93 → 208 / 773 → 1,500 / 1,211 → 1,864** violating hours — about a
   third of the object. Repairing it changes the basis of four committed
   findings (169b/170/171/172), as nyiso-171 §5 already noted; this session adds
   the size.
2. **A small, real overlay-delivery defect at plant 2682 (S A Carlson):** 48
   CC-tagged extract rows land on no fleet bin, because the model carries only
   `ST_GAS` + `CT_PEAKER` bins there. 87 MW, the `_FLEET_GROUP_OVERRIDE` class.
3. **The caiso-186 WEFOR double count is live on this keeper too**
   (`wefor_residual = null`): the full statistical CC WEFOR applies *on top of*
   an overlay that already carries every detected outage. It is a genuine rule
   19 `[R-ONE-MECH]` question — but note its direction: resolving it would make
   CC **more** available, i.e. it points *away* from this object, which is why
   it is recorded rather than proposed.

Two instrument limits travel with the finding. **Per-unit model dispatch is not
observable** from `class_hourly` (nyiso-172 §2.4), so the S3 envelope is a
**class aggregate**: in principle the LP could be bound below it by unit-level
structure (one plant at its own ceiling while others hold headroom). The
magnitude — 2.0–2.7 GW of aggregate headroom against a 636 MW gap — makes that
implausible as a full explanation, but it is stated rather than worked around.
And **model-side zonal dispatch is likewise unobservable**, so a locational
reading of the same headroom is untested.

## 6. Honest expected value

**What is delivered.** A reproducible, zero-solve, pre-registered adjudication
that (a) **kills the brief's own named hypothesis on its own stop condition**,
by a stable 56 % majority rather than a marginal miss, (b) kills it *twice* —
even the blind remainder is carried by a different mechanism than the one named,
(c) **downgrades the inherited object from a fleet claim to a portfolio-only
one** on the same discriminator nyiso-171 established, at 0 hours above the
additive bound in every year, (d) delivers the decisive measurement the lane
needed — the model reaches its CC availability envelope in **0 hours** and
leaves 2.0–2.7 GW unused in exactly the violating hours — which adjudicates the
**entire availability-input family provably inert before a solve is spent**,
(e) validates that result against its own most likely artifact (the envelope is
not over-tight: the measured fleet exceeds it 0 times) and against its own most
likely omission (a 3.5 % WEFOR changes nothing), (f) converts three matrix
channels from argued-inert to **measured-inert by empty extract**, and (g) sizes
the East River defect at roughly a third of the object.

**What is NOT delivered. No gate moves.** C3a-2025 is still −11.5 %, C3c still
fails, the determination is still **NOT-YET on {C3a-2025, C3c}**, and NYISO
still does not read CALIBRATED. **No solve ran**, so rule 15 registers nothing —
the dashboard is untouched by design, not by omission. **No lever was armed**,
and the 0.70 gain is unmeasured against any arm because no arm was built. The
one gate that passed (P2, the gap is not shape) buys nothing on its own once S3
holds.

**What could still be wrong.** The S3 envelope is a **class aggregate** built
from the engine's own loader but omitting pmin/ramp/commitment structure, the
reserve co-optimisation and the Jun–Sep summer derate; it is deliberately an
UPPER bound, which makes utilisation a LOWER bound and the headroom conclusion
one-sided in the safe direction — but it cannot exclude unit-level binding, and
per-unit model dispatch is not observable to check (nyiso-172 §2.4). The state
partition in §2.2 depends on `cap_u`, a demonstrated within-year maximum, which
is availability-inclusive and therefore understates shortfall for a unit derated
all year; the direction of that bias is conservative for P1a's *blind* share, so
the true A share is if anything larger, but it is a real approximation. State A
is assigned from the day-granular window reconstruction, which can over-cover up
to 23 h at each window edge (the caiso-183 seam), slightly inflating A — the
margin is 6 points, not one, so the verdict holds, but the number is not exact.
The 3.5 % WEFOR in the robustness leg is CAISO's published CC figure (caiso-186)
used as an order-of-magnitude check, not an NYISO-identified value. And P2's
price conditioning uses a hub DA series against a model load-weighted composite
— the same spatial caveat nyiso-168 §9 and nyiso-170 §6 both recorded.

**The honest read on the object.** nyiso-172 handed forward the strongest thing
the NYISO lane had produced in six sessions: an input-side defect with a
one-sided proof rather than an association. That proof survives — the bound is
violated, and the violation grows with the failing year. What does not survive
is the reading that it points at an input. The model's CC fleet is derated in
every hour of every year, by a mechanism that is armed, correctly routed and
demonstrably not over-tight, and the LP simply does not use two-thirds of a
gigawatt-scale headroom it already has. **The CC over-run is therefore the
merit-order object seen from the other side, not a second object** — which
means C3a-2025 has one fewer escape route than it appeared to have yesterday,
and a successor should not expect the availability lane to close it. The
standing $27.79–$56.03/MWh pass window nyiso-167 derived should still be planned
around rather than solved away.

## 7. Evidence

* `results/calibration/PREREG-nyiso173-cc-availability-anatomy.md` — the gates,
  committed with the probe before either ran (`278ddf37`)
* `scripts/probes/nyiso173_cc_availability_anatomy.py` +
  `results/calibration/_nyiso173_cc_availability_anatomy.json` — P1–P4
* `scripts/probes/nyiso173b_overlay_delivery.py` +
  `results/calibration/_nyiso173b_overlay_delivery.json` — S1–S3, the
  overlay-delivery and envelope-utilisation addendum
* keeper `results/calibration/nyiso159_lossarm_B/` —
  `run_config.json`, `legitimacy_diagnostics.json` (D-2),
  `hourly/class_hourly_<year>.parquet`, `hourly/system_<year>.parquet`
* `src/market_sim/data/outages.py:239` (`UNIT_OUTAGE_MIN_DAYS = 5`),
  `unit_outage_derate_factors`, `_iso_plant_capacity`,
  `_generic_unit_outage_target`, `_FLEET_GROUP_OVERRIDE`;
  `scripts/lib/outage_detect.py` (`ST_GAS_CF_PEAK`,
  `ST_GAS_MIN_OUTAGE_HOURS`); `scripts/data/derive_campd_unit_outages.py`
  (the coal-only short/partial guards)
* `data/raw/campd-unit-outages-NYISO.csv` (2,928 CC rows),
  `campd-unit-outages-short-NYISO.csv` (**0 rows**),
  `campd-partial-outages-NYISO.csv` (**0 rows**),
  `campd-unit-outages-layup-NYISO.csv` (1,012 CC rows),
  `data/raw/maxgen-events/` (`miso` only)
* predecessors: `docs/FINDING-nyiso172-st-gas-response-deficit-2026-09-01.md`
  §3.4 §5 §6, `-nyiso171-chp-floor-portfolio-artifact-` §2.3–§2.5,
  `-nyiso170-merit-order-displacement-` §§2.1/3/4,
  `-nyiso168-supply-curve-slope-anatomy-` §4 §8–§9
* `docs/codebase-site/data/mechanism-matrix/NYISO.js` —
  `campd_outage_windows` (`K`, evidence added; **no verdict moves**) and
  `unit_outage_short_windows` (`I`, measured grounds added), both re-read
  before anything was proposed; `node --check` and
  `scripts/check_mechanism_matrix.py` both pass.
* CLAUDE.md rules 1 `[R-STRUCT]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`,
  15 `[R-DASHBOARD]`, 19 `[R-ONE-MECH]`, 22 `[R-HOLDOUT]`,
  23 `[R-FROZEN-DERIVE]`, 25 `[R-ISO-SCOPE]`, 28 `[R-MECH-MATRIX]`

Next shorthand: nyiso-174.
