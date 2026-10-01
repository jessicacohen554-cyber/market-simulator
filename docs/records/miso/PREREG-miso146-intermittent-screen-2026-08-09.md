# PREREG — miso-146: an INTERMITTENT-RESOURCE SCREEN for MISO's masked offer corpus, or a proof that none is buildable

**Session:** miso-146, 2026-08-09, branch `claude/miso-146-offer-surface-14kwww`,
off `origin/main` at `e9f99e6`. §5.4 LIVE QUEUE — the **lane (A) prerequisite**
handed forward by miso-145 §8.

**This document is pushed BEFORE any adjudicating statistic is computed.**
Everything already read or computed at registration time is disclosed in §10,
including the EIA-860 control numbers, which are *reference-side* quantities
fixed here so the bars below are numeric rather than relative.

**Solve posture: NO LP. NO SOLVE. NO KEEPER MOVE. NO `ScenarioConfig` FIELD.
NO ARM. NO CELL VERDICT MINTED.** Lane (A) is a measurement on an input corpus;
it cannot produce a mechanism and none is proposed here. The one downstream
reading this document licenses (§6, G-C) can produce a **finding and an owner
escalation only** — never an arm, in this session or by this document.

---

## 0. The keeper's state, re-verified from committed artifacts

Re-verified in-session with `scripts/calibration_verdict.py --run-id
2026-08-05-miso-132b-cc-committed` (committed artifacts only, no re-solve, all
three years in ONE invocation), **not** taken from the handoff:

* determination **NOT-YET**, scorable years 2023, 2024, 2025;
* **sole FAIL C3a `price_mean`**, 2025 **−14.1 %** (2023/2024 pass and are not
  printed as failures; DA companions −4.4 / −8.4 / −15.8 % are `SKIPPED`
  diagnostics);
* **C3c the sole ledgered caveat**, all three years, budget 1 of 1 — SPENT;
* C1 / C2 / C3b / C4 / C6 / C8 **PASS**; C8 ST_GAS grounded above budget at
  **31.9 / 33.1 / 45.1 %** with all binding mechanisms clearing D-4;
* C1 skips all eight classes in 2025 and C2 both families in 2025 on the
  **preliminary EIA-923 vintage** — the blocker year's fuel mix is **UNGATED**.

MISO holds **no** `calibration-complete` marker. Rule 22: 2023–2025 only.
Nothing in this document touches a year outside that span.

---

## 1. The object, and why it is a prerequisite rather than a lever

miso-145 landed MISO's masked submitted-offer corpus and **could not measure the
LEVEL question cleanly**, for one measured reason it reported against its own
interest: the corpus carries MISO's wind and solar as offer rows — **19.945 GW
(RT) / 17.654 GW (DA) offered at or below $0/MWh in 2025 JJA h12–17** — while
the model's fleet carries none of them as rows (they are LP decision variables;
the keeper dispatches **16.286 GW** of wind + solar in the same hours). The
pre-registered declaration screen (`Curtailment Offer Price` non-null, storage
SOC bounds non-null) removes **0.459 of 107.007 GW**. So the corpus's *body*
is contaminated relative to the model's stack, every statistic whose value
depends on where the body sits is contaminated with it, and miso-145 left a
**standing rule**: *no level statistic from this corpus may be quoted by any
lane until a working screen exists.*

**This session's object is that screen — build one that works, or prove none is
buildable from the admissible inputs.** It is not a lever, it licenses no
mechanism, and its success or failure moves no gate. Its whole value is that it
either unblocks or permanently closes the level question for every downstream
MISO lane.

**Admissible inputs, fixed here:** (a) the corpus's own **declarations** —
`ecomax_mw`, `ecomin_mw`, `self_scheduled_mw`, the flags, the curtailment-offer
price and storage SOC bounds; (b) **EIA-860 at registration grain**, used as an
external control on magnitude, never as a per-unit label (the corpus is masked;
no join to EIA-860 exists or is attempted). **Offer PRICE is excluded from the
feature set by construction** — it is held out as the validation attribute
(§4, P-3b).

---

## 2. Three facts fixed BEFORE registration that bound what this lane may claim

**(a) There is no fuel or technology attribute in the corpus.** miso-145's P-A3
re-verified zero columns matching `fuel|type|technolog` across all 552 files,
and miso-138's offer-side class bridge was **REFUTED** (CC `|S_cap| > 0.50` at
both EIA-860 grains; COAL recall 0.382 *with labels in hand*). Re-attempting a
thermal class split is DO-NOT-REDO (rule 28(a)).

**A two-way intermittent / non-intermittent split is NOT that bridge**, and the
distinction is the whole of TRAP 5 below: an intermittent resource's declared
capability is a *weather forecast* and a thermal unit's is a *rating*, which is a
physical difference in the declaration itself. Coal-vs-CC is not. **The
non-intermittent population is never partitioned anywhere in this session.**

**(b) DA and RT are separate books and are never averaged.** RT is a genuine
SUBSET of DA (852–1,115 units, 0.815–0.930 within-summer persistence, vs DA
1,319–1,407 / ≥ 0.9985). Every reading is computed on each book separately and
labelled. Where a price basis is needed, it is the **measured RT actual**, on
both sides, labelled (miso-145's convention).

**(c) The screen is a classification of an INPUT corpus, not a model input.**
Nothing here enters the LP, so rule 13 `[R-MEASURED]` is not engaged by the
screen itself. It is engaged by anything a successor might build on it, and §9
records the adjudication in advance anyway.

---

## 3. G-F — footing gates, checked BEFORE any screen statistic

* **G-F0 (reproduce-before-extend, HARD STOP).** Reproduce miso-145's committed
  2025 JJA h12–17 corpus readings to ≤ **0.05 GW**: total offered capability
  **107.007 GW (RT) / 131.969 GW (DA)**, and mass at or below $0/MWh
  **19.945 GW (RT) / 17.654 GW (DA)**. Failure ⇒ `BRANCH-INSTRUMENT-FAIL`; the
  bar is **not** moved and the instrument reports **gaps only**, never levels.
* **G-F1 (TRAP 7, required only for the §6 G-C leg).** Reproduce miso-142/143's
  six committed window deficits on the single C3a weight: **−4.750 / −8.333 /
  −10.676 / −10.671 / −30.999 / −30.435**, to ≤ $0.01. Failure ⇒ G-C is not run
  and no level statistic is reported at all.
* **G-F2 (tail separation, TRAP 6 of miso-145's set).** Every window statistic
  is also reported on the **ordinary** subset (measured RT actual ≤ $200), whose
  committed 2025 JJA h12–17 deficit is **−12.874** of the −30.435 headline.

---

## 4. The screen — features, decision rule and thresholds, fixed here

### 4.1 The identification

An intermittent resource's **declared economic maximum is a forecast**; a
thermal resource's is a **rating**. Three consequences, all measurable from
declarations alone, computed per `unit_code` per year per market over the JJA
window (Jun 1 – Aug 31), on unit-hours where the unit declares any capability:

Let `C` = the unit's own **p99 `ecomax_mw`** over the window (its declared
capability scale; `ecomax_mw < 0` is treated as 0 — the corpus carries a −1
sentinel).

* **F1 `interior_frac`** — the fraction of the unit's declaring hours with
  `0.05·C < ecomax_mw < 0.95·C`. A forecast lands anywhere in its range; a
  rating sits at its top. A persistently derated thermal unit re-scales its own
  `C` and stays at the top of it.
* **F2 `step_frac`** — the fraction of consecutive declaring hour-pairs with
  `|Δ ecomax_mw| / C > 0.02`. A wind or solar forecast moves every hour; a
  rating does not.
* **F3 `n_levels_frac`** — distinct `ecomax_mw` levels rounded to 1 % of `C`,
  divided by the number of declaring hours. **Reported, not gating** — a
  redundancy check on F1/F2.
* **F4 `night_ratio`** — mean `ecomax_mw` over local h01–04 divided by the mean
  over h12–14. **Reported, not gating**, and used ONLY for the wind/solar
  validation split of §4.3.

**`step_price_usd_per_mwh` is not an input to any feature.** This is enforced in
the probe by loading the feature frame without the price column.

### 4.2 The decision rule (a priori, not tuned)

> A unit is **INTERMITTENT** iff `interior_frac > 0.50` **AND**
> `step_frac > 0.50`. Otherwise it is **NON-INTERMITTENT**.

Both thresholds are the **neutral midpoint of their own range** — "more often
than not, this unit's declared capability behaves like a forecast rather than a
rating." Neither is chosen against any outcome, and **neither is moved after any
number is seen** (TRAP 6). A full sensitivity sweep over
`{0.30, 0.40, 0.50, 0.60, 0.70}` (both thresholds moved together) is reported
alongside the headline so the reader sees the whole surface rather than one
point on it.

Capability is attributed as **Σ C over units**, and separately as the
**hour-mean offered MW** in the 2025 JJA h12–17 window so the screen's output is
directly comparable to miso-145's committed universe numbers.

### 4.3 The wind/solar sub-split — reported, never load-bearing

INTERMITTENT units with `night_ratio < 0.15` are labelled **solar-like**, the
rest **wind-like**. This exists for one purpose: EIA-860 publishes MISO wind and
solar separately, so the sub-split is a *second, independent* control on the
same population. **No verdict, branch or downstream statistic conditions on
it**, and it is not a class bridge (§2a, TRAP 5).

---

## 5. Predictions, with numeric bars fixed now

The EIA-860 control brackets below are computed from the current (2025 Early
Release) MISO snapshot, `Balancing Authority Code == "MISO"`, in service by
**July 1** of the year (`Operating Year`/`Operating Month`), nameplate MW; the
`≥ 20 MW` subset is the market-participating proxy and the all-sizes figure the
upper bracket. Numbers are disclosed in §10 and are reference-side only.

| id | prediction | bar | gating? |
|---|---|---|---|
| **P-1** | **Well-posedness.** The MW-weighted distribution of `interior_frac` is **bimodal**: less than **20 %** of Σ C falls in the middle band `interior_frac ∈ [0.30, 0.70]`. | < 20 % | **reported, not gating** — a failure means the threshold is load-bearing, and forces the §4.2 sweep to be reported as the primary result rather than a sensitivity |
| **P-2** | **Positive control (magnitude).** Screened INTERMITTENT Σ C, DA book, lies inside `[0.70 × (≥20 MW VRE nameplate), 1.30 × (all-sizes VRE nameplate)]`: **2023 [23,751 , 47,294] MW · 2024 [26,724 , 53,032] · 2025 [32,839 , 64,671]**. | inside, all 3 years | **reported, not gating** — can fail LOW for a reason external to the screen (the book may carry only part of MISO's VRE fleet), with the interpretation fixed in §6 |
| **P-3** | **Negative control (harm).** Screened NON-INTERMITTENT Σ C, DA book, lies inside `[0.60, 1.15] ×` EIA-860 MISO non-VRE **summer** capacity in service by Jul 1: **2023 [83,754 , 160,529] MW · 2024 [83,839 , 160,692] · 2025 [84,331 , 161,634]**. | inside, all 3 years | **GATING** — this is the test that thermal is not being eaten |
| **P-3b** | **Held-out validation.** Offer price is not in the feature set. In 2025 JJA h12–17, **≥ 60 %** of the INTERMITTENT population's offered MW is priced ≤ $0/MWh, and **≤ 15 %** of the NON-INTERMITTENT population's is. | both, RT and DA | **GATING** — this is the test that the screen separates the population it claims to |
| **P-4** | **Contamination removed.** The INTERMITTENT population accounts for **≥ 70 %** of miso-145's committed ≤ $0 mass — 19.945 GW (RT) / 17.654 GW (DA) — in 2025 JJA h12–17. | ≥ 70 %, both books | **GATING** — this is the test that the screen removes the specific contamination that blocked the level question |
| **P-5** | **The payoff (G-C), two-sided.** On the screened NON-INTERMITTENT universe, miso-145's LEVEL term at the model's own clearing percentile, 2025 JJA h12–17 RT, currently **−$14.376**. | see §6 | run **only** under `BRANCH-SCREEN-BUILT`; produces a **finding and escalation only, never an arm** |

**Why P-3/P-3b/P-4 gate and P-1/P-2 do not, stated before any number:** P-3,
P-3b and P-4 test the screen's *function* — does it separate the two
populations, does it avoid eating thermal, does it remove the named
contamination. P-1 and P-2 test its *quality and completeness*, and each can
fail for a reason that is not a defect of the screen (a genuine continuum of
unit behaviour; a book that carries only part of the registered VRE fleet).
Their interpretations are fixed in §6 so neither can be re-read after the fact.

### Two-sided prior

**The prior is that the screen is buildable and that it will identify 25–45 GW
of intermittent capability in the DA book**, because the declaration-dynamics
difference between a forecast and a rating is a physical one that MISO's own
market design forces into the data: a DIR must re-declare its capability hourly,
and a thermal unit has no reason to.

**The prior on the other side is not decorative, and it is the more likely
failure in one specific way.** MISO's non-dispatchable intermittent fleet may
simply not appear in the commercial-offer book at all, or may appear
self-scheduled with a flat declared max — in which case F1/F2 will find far less
than the registry carries and P-2 fails LOW while P-3b still passes. That is
neither a working screen nor a broken one; §6 fixes its reading in advance. The
genuinely fatal outcome is P-3b failing — the two populations not separating on
the held-out price attribute — which would mean the declaration dynamics do not
identify the population at all.

**Most likely nuisance, named in advance:** a thermal unit whose masked
`unit_code` aggregates several physical units (a CT site, a CC block) and which
therefore declares a *staircase* of capability as units come and go. It would
raise `interior_frac` without being intermittent. Counter-measurements: F2's
0.02 threshold (a staircase moves on commitment timescales, not hourly), F3's
level count (a staircase has few levels), and P-3b (a thermal staircase does not
offer at ≤ $0).

---

## 6. Pre-committed branches

* **`BRANCH-SCREEN-BUILT`** — P-3 **and** P-3b **and** P-4 all pass. The screen
  is a first-class instrument. miso-145's standing rule is **LIFTED for the
  screened universe and only for it**, and G-C runs. Its verdict is itself
  pre-committed:
  * screened LEVEL **≥ +$18** ⇒ the offer-level object is **REINSTATED** on a
    clean universe; miso-145's `BRANCH-CONDUCT-ABSENT` is superseded and this
    session must say so plainly. **No arm follows** — it is an owner escalation
    (rules 19/24), because the mechanism family is new.
  * screened LEVEL **≤ +$9** ⇒ `BRANCH-CONDUCT-ABSENT` is **CONFIRMED** on a
    clean universe, and the level family is closed by measurement rather than by
    a fired rule.
  * **$9 < LEVEL < $18** ⇒ **INDETERMINATE**, reported at full magnitude, no
    lever, no escalation.
* **`BRANCH-SCREEN-BOUNDED`** — P-3b passes but P-3 or P-4 fails. The screen
  identifies a real intermittent population but does not clean the universe.
  Level statistics are reported **with the bound stated** and marked
  **NOT-LICENSING**; miso-145's standing rule **STANDS**.
* **`BRANCH-NO-SCREEN`** — P-3b fails. **No screen is buildable from
  declarations + EIA-860 distribution-grain.** This is filed as a **REPORTABLE
  DATA BLOCKER** on the level question; the standing rule stands permanently
  absent a new data source; the shape lane (the miso-145 §8 *missing offer
  wall*) proceeds without it, since it rests only on band-restricted statistics.
* **`BRANCH-INSTRUMENT-FAIL`** — G-F0 (or, for the G-C leg only, G-F1) fails.
  Bars are **not** moved; the failed reading is reported at full magnitude and
  the instrument reports gaps only.
* **P-2-LOW sub-reading, fixed in advance:** if P-2 fails LOW while P-3b and P-4
  pass, the finding is *"the screen works on what the book carries; the book
  carries only part of MISO's registered VRE fleet"* — which is sufficient for
  the level question (what must be removed is the VRE that IS in the corpus) and
  insufficient for any claim about MISO's VRE fleet. Both halves are stated.

---

## 7. Look-alike traps, each with its counter-measurement

* **TRAP 1 — THE UNIVERSE, AGAIN (the miso-144/145 lesson).** A gate that passes
  by cancellation has not passed. *Counter-measurement:* every subtraction
  states its universe on **both** sides with MW **and** unit counts; the screen's
  own output IS a universe statement and is printed in full (MW and units, per
  year, per market, per population); the ≤ $0 mass is reported **separately for
  each population and never netted**; G-F0 reproduces miso-145's committed
  universe numbers before anything is subtracted.
* **TRAP 2 — RE-SWEEPING `gas_offer_margin`.** Armed, cell `K`; its anchor/level
  re-identification is DO-NOT-REDO. *Counter-measurement:* **no parameter of any
  kind is derived in this session.** The screen has no parameter that can enter
  the LP; `gas_offer_margin` is not read, not re-derived and not referenced by
  any computation here.
* **TRAP 3 — THE OUTCOME OVERLAY (rule 13).** *Counter-measurement:* the award
  columns have no column in the `energy-offers` schema and cannot be read (§2c);
  no measured curve, level or share produced here is proposed as a model input;
  §9 records the adjudication in advance regardless.
* **TRAP 4 — THE INSTRUMENT CROSSING.** *Counter-measurement:* DA and RT
  computed separately, never averaged; one price basis (**measured RT actual**)
  on both sides wherever a price basis is needed, labelled at the point of use;
  offer prices are compared to offer prices, never to SRMC.
* **TRAP 5 — CLASS BY THE BACK DOOR.** *Counter-measurement:* the screen is
  strictly two-way; the **NON-INTERMITTENT population is never partitioned**, no
  statistic in this session conditions on any thermal class, and the wind/solar
  sub-split (§4.3) is declared non-load-bearing before it is computed. If any
  reading below turned out to require a thermal class to interpret, it would be
  withheld.
* **TRAP 6 — FIXING THE NUMBER.** *Counter-measurement:* both thresholds are
  fixed at **0.50** in §4.2 before any number is seen, and are not moved; the
  full sensitivity sweep is reported; no bar in §5 is adjusted after
  measurement — a failing bar is reported at full magnitude (the miso-145 P-A2 /
  P-A4 precedent).
* **TRAP 7 — WEIGHTS.** *Counter-measurement:* G-F1 — the six committed window
  deficits reproduced on the single C3a weight before any G-C statistic.
* **TRAP 8 (new) — THE SCREEN THAT FINDS WHAT IT WAS BUILT TO FIND.** A
  classifier validated on its own features proves nothing.
  *Counter-measurement:* **offer price is excluded from the feature set by
  construction** (§4.1, enforced by the loaded column list) and is the sole
  validation attribute (P-3b), so the validation is genuinely held out. The
  second, fully independent control is EIA-860 (P-2/P-3), which shares no column
  with the corpus at all.

---

## 8. Kill gates

No LP is solved and no mechanism is armed, so **no kill gate can be reached**.
They are restated so the claim is checkable rather than assumed: C3b-2025 NRMSE
≤ 0.200 (currently 0.191, headroom 0.009); C3a 2023/2024 stay PASS (−0.4 /
−6.0 %); C1/C2 stay PASS on gated years, with **2025 UNGATED** and scored
descriptively vs EIA-930 if it is scored at all; C8 — no material class's forced
share rises and no D-4 window breaks; C3c's ledger is 1 of 1 and SPENT, so
nothing here may be tuned to the > $200 tail (G-F2 enforces the separation);
**the fail set must remain ⊆ {C3a}**. At the end of the session each is
re-stated as *untouched*, with the reason (no solve), not as *passing*.

---

## 9. Rule-13 admissibility, adjudicated in advance

**The screen itself is not a rule-13 object.** It classifies rows of an input
corpus for the purpose of measurement; nothing it produces is fed to the LP, and
no `ScenarioConfig` field is added.

**Anything a successor builds on it is.** Fixed here, binding on any successor:
a measured same-year offer curve pinned into the backcast is a measured
**outcome** overlay with no forward analogue — **forbidden as methodology**, and
admissible at most as an explicitly-labelled, default-**off** diagnostic probe.
The only admissible form is a parameter derived from **multi-year** offer history
and conditioned on drivers that exist in a forecast year (position in the stack /
headroom, load percentile, gas price) — the CEMS-emission-rate precedent — which
would regenerate for a forward year and respond to changed conditions. **If it
cannot be given a forward story, it is a finding, not a lever.** Any successor
must additionally state how it **replaces or subsumes** `gas_offer_margin`
(armed, cell `K`, same offer path) per rule 19 `[R-ONE-MECH]` — never stacks.

---

## 10. Full disclosure — everything read or computed before this registration

**Read:** the §5.4 LIVE QUEUE stamp (miso-145) in
`docs/mechanism-testing-matrix.md`; `FINDING-miso145-offer-conduct-2026-08-09.md`
in full; `PREREG-miso145-summer-offer-conduct-2026-08-09.md` §§5–8;
`data/dictionary/schema/energy-offers.schema.yaml` (v2) in full;
`scripts/probes/_miso145_offer_conduct.py` (the `load_real_segments` /
`price_at_pctl` / `curve_readings` construction, to be reused verbatim);
`scripts/probes/_miso138_da_co_class_bridge.py` §§EIA-860 loader; the handoff's
statements of miso-142/143/144's committed results.

**Computed (reference-side and availability only, no adjudicating statistic):**

1. **§0 re-verification** — `calibration_verdict.py --run-id
   2026-08-05-miso-132b-cc-committed`, output summarised in §0.
2. **Corpus availability** — DA 2025 clean parquet: 11,187,592 rows /
   2,751,348 unit-hours / **1,256 distinct `unit_code`** over the summer;
   `ecomax_mw`, `ecomin_mw`, `self_scheduled_mw` **0.0000 null**; `ecomax_mw`
   min **−1.0** (the sentinel §4.1 clips to 0), median 37.0, max 1,539.0. This
   is a *can-the-feature-be-computed* check; no feature was computed.
3. **EIA-860 MISO control (reference side, fixes the §5 brackets)** — current
   snapshot, BA `MISO`, in service by Jul 1, nameplate MW unless stated:

   | year | VRE all | VRE ≥20 MW | of which WND / SUN (all) | non-VRE summer, all | non-VRE summer, ≥20 MW |
   |---|---|---|---|---|---|
   | 2023 | 36,380 (n=1,392) | 33,930 (n=295) | 31,157 / 5,223 | 139,590 | 132,746 |
   | 2024 | 40,794 (n=1,499) | 38,177 (n=334) | 31,915 / 8,879 | 139,732 | 132,880 |
   | 2025 | 49,747 (n=1,645) | 46,913 (n=394) | 32,653 / 17,094 | 140,551 | 133,662 |

   Known limits of this control, stated now: it is the **operable** file, so
   units retired before the snapshot are absent; the in-service filter is
   month-grain; and EIA-860's registry population is not the same population as
   MISO's market-participant list. These are exactly why P-2 is **reported, not
   gating**.
4. **Corpus re-fetch** — `fetch_miso_energy_offers.py` +
   `curate_miso_energy_offers.py` re-run in-session; 552/552 files, all six
   clean parquets present.

**No feature, no classification, no screened aggregate, no level statistic and
no window statistic has been computed at the time this document is pushed.**
