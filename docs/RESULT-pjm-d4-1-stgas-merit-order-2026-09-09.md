# RESULT — PJM: the ST_GAS card resolves to ONE channel, and the allocation family is falsified at zero LP

**Session** `pjm-d4-1` · **ISO** PJM · **Date** 2026-09-09 · **Branch** `claude/pjm-d4-1-qa8gwk`
**PRECOMMIT** `docs/PRECOMMIT-pjm-d4-1-stgas-merit-order-2026-09-09.md` — committed **before** any arm
was built; every gate bar, the control posture and the rule-1 non-gates are quoted from it unchanged.
**Keeper UNCHANGED** `2026-09-09-pjm-fuelvintage-ep-level`. PJM's headline is **untouched**.
**No LP was solved. Nothing was promoted, nothing registered, no holdout year touched.**

---

## 1. RESULT

> **The card had two hypotheses. Phase 0 answers both, and neither survives in the form the handoff
> put them.**
>
> **(a) THE MERIT ORDER IS NOT INVERTED.** The handoff's claim — *"steam gas should sit ABOVE peakers
> in the stack, not below them"* — is **already true of the model's own assembled offers** in two of
> three training years. Capacity-weighted `mc_base` puts ST_GAS **above** CT_PEAKER by +1.276 (2024)
> and +1.835 (2025) $/MWh, and within **0.426** of it in 2023 (below in 49.6 % of hours — a coin
> flip); ST_GAS is above CC_REGULAR by +19.7 / +20.4 / +25.5 with **0 %** of hours below.
> **There is ONE channel, not two: the floor.** The displacement of CT_PEAKER needs no price
> inversion, only **adjacency**, and the two classes sit within ~2 $/MWh of each other against a
> ~50 $/MWh level — which is exactly the near-equal-and-opposite 2021 (+8.17 / −6.64 TWh) and 2022
> (+8.97 / −4.60) signature the handoff opened on.
>
> **(b) THE FLOOR IS CONVICTED, AND THE ALLOCATION FAMILY CANNOT ACQUIT IT.** Rule 17
> `[R-FLOOR-WINDOW]` is dispositive: **41 of 58 metered floored plant-years carry a measured median
> of 0.000 MW over the floor's own binding hours** — 73.8 % of the rider-covered forced energy —
> against a declared window whose stated justification is *"there is no hour the class's own driver
> evidence says it is offline"*. But the two mechanisms the record names as the fix **do not fix it**:
> `netload_drag_merit_allocation` (ercot-259) clears **zero** convictions in 2023, 2024 and 2025;
> `netload_drag_min_run_persistence` (pjm-177) clears **zero**; and **the composition pjm-177
> explicitly named as the one that "would have to compose to close the mask properly" is strictly
> WORSE than either half**, adding the same conviction (plant 3148) in both years it was scored.
>
> **THE ROOT CAUSE IS MEMBERSHIP, NOT ORDER OR HOURS — and this repository already owns the seam for
> it.** `data.outages.ST_GAS_PEAKER_PLANTS` exists precisely to keep *"peaker-class ST_GAS plants:
> patchy / spiky run rate (run only when called)"* out of the reliability min-gen floor. It names six
> ERCOT plants and three CAISO plants. **It names NO PJM plant** — while PJM's own meter says plant
> **3161 runs 2.3 / 4.3 / 3.0 % of the year** (the same character as the CAISO members, whose
> qualifying evidence was *"online only 0.4–2.5 % of hours"*) and is floored **7,666–7,885 hours** a
> year on 862 MW.
>
> **And the one arm that DOES clear the gate is the one that must be refused.** The measured
> economic-lay-up mask (`netload_drag_layup_window_mask`) takes the convictions to **0 in 2025** and
> **1 in 2023** — but it does so by cutting the mandate **~34 % in both years** (a LEVEL change, not
> an allocation one), and it is registered **backcast-only** under rule 13 `[R-MEASURED]`, so it has
> no forward story and cannot satisfy rule 17 clause (c). It is reported as a diagnostic and refused
> as a fix. Its most useful output is the number it puts on the object: **~34 % of PJM's ST_GAS drag
> mandate sits inside measured economic lay-up.**
>
> **Six LP arms at ~70 minutes each were not spent to learn any of this.** That is rule 29
> `[R-SCREEN]` clause (0) doing its job.

---

## 2. THE CONTROL POSTURE — pre-registered, and no control solve spent

G-DRIFT (rule 29(b)) is **NOT RUNNABLE for PJM** — inherited unchanged from pjm-177 §4 and
`PRECOMMIT-pjm-fuelvintage-solve-2026-09-09.md` §(a) (the previous keeper's `git_sha` `457ae04` is
dead post-rewrite; the surrogate window is 221 files / 187,385 insertions). **G-CTRL form 4 declared
IMPAIRED**, bands ±0.25 % / ±2.4 % CT_PEAKER, fixed in the PRECOMMIT.

**It never bound.** Every measurement below is either a committed artifact or an arm-vs-control pair
built in the **same process, at the same HEAD, from the same recipe**, so HEAD drift cancels
identically on both sides. No control solve was spent, and none was needed.

---

## 3. RULE 19 `[R-ONE-MECH]` — DISCHARGED FROM THE ARTIFACT

D-2 rows with `class == "ST_GAS"` across both committed bundles, all six years:
**`st_netload_drag` is the ONLY mechanism forcing PJM ST_GAS**, in every year. It is likewise the only
ST_GAS floor in D-4. Nothing stacks; there was nothing to reconcile.

---

## 4. THE SIX-YEAR TABLE, AND THE NUMBER THE HANDOFF DID NOT HAVE

| year | forced TWh | class TWh (D-2) | forced share | **measured class TWh** | **forced ÷ MEASURED** |
|---|---|---|---|---|---|
| 2020 | 5.511 | 10.149 | 54.3 % | 6.631 | **83.1 %** |
| **2021** | 6.585 | 10.294 | 64.0 % | **3.792** | **173.7 %** |
| **2022** | 6.027 | 12.953 | 46.5 % | 5.790 | **104.1 %** |
| 2023 | 4.765 | 12.182 | 39.1 % | 8.883 | 53.6 % |
| 2024 | 4.428 | 12.093 | 36.6 % | 13.107 | 33.8 % |
| 2025 | 7.156 | 17.311 | 41.3 % | 14.788 | 48.4 % |

The forced-share column reproduces the handoff exactly. The last column is new: **in 2021 the floor
alone mandates 74 % more energy than PJM's entire gas-steam fleet metered that year, and in 2022 more
than 100 % of it.**

**2024 is the cleanest case for rule 1 `[R-STRUCT]`.** ST_GAS is dead on actual there (m/a = **1.00**,
+0.4 %) with **36.6 % of it forced**. The class reaches the right total by mandating a third of it. A
residual-driven reading sees nothing wrong in 2024; the mechanism is just as unfaithful there as in
2021. **The residual is not the object, and this table is why.**

Class composition, model vs the committed bench `classFull` (reproduces the handoff):

| class | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| ST_GAS m/a | 1.74 | **3.15** | **2.55** | 1.52 | **1.00** | 1.29 |
| CT_PEAKER Δ % | −1.6 | **−32.2** | **−24.9** | −10.6 | +1.5 | +19.2 |
| CC_REGULAR Δ % | +3.3 | +9.9 | +8.4 | +1.5 | +1.0 | +0.9 |

---

## 5. THE DECLARED WINDOW EXISTS — AND ITS OWN PREMISE IS FALSE IN PJM

`D4_WINDOWS[(MECH_ST_NETLOAD_DRAG, None)] = (0, 24)` — **h0-23, ISO-neutral**, no PJM override in
`D4_WINDOWS_BY_ISO`. So this is **not** a rule-17 missing-declaration failure, and the handoff's
"NO DECLARED WINDOW IS ALREADY A RULE-17 FAILURE" branch does not apply.

- **Driver:** RUC-style reliability commitment — boilers held online at part load through the
  low-price trough (`derive_pjm_st_gas_netload_drag.py`). Applied as
  `clip(0.01029·netGW − 0.7263, 0, 0.39) × pmax` ⇒ zero below **70.6 GW** net-load, capped at 108.5.
- **Forward story:** net-load from load forecast + VRE build; rule-23 frozen derive.
- **The hours it may bind, and why —** the registry states this as a *factual claim about the class*:
  > *"the gas-steam fleet 'committed every day and every night, never fully off' … **Unlike CT
  > (overnight CF ≈ 0), there is no hour the class's own driver evidence says it is offline**, so the
  > all-hours boiler floor binds nowhere off-window **by measurement**."*

  The evidence cited is **ERCOT's** (`docs/ercot-st-gas-netload-drag-2026-06.md`). In PJM the premise
  fails for most of the floored fleet — §6.

**Handoff option (c) is closed.** For an all-hours window the D-4 `window` check is arithmetically
incapable of failing (`off = sel & ~in_window` is empty ⇒ `offwindow_share ≡ 0.0`), so the old 12-row
form measured **nothing** for this mechanism. The ~210-row form's per-unit conduct rider (owner
decision 2026-08-16, nyiso-140 §5) is the first provenance check ever applied to it in PJM. Reverting
the checker would restore a guaranteed PASS, not a measurement.

---

## 6. THE CONDUCT EVIDENCE — 41 of 58 PLANT-YEARS, AND THE SPLIT IS BIMODAL

Committed D-4 unit-conduct rows, all six years, both bundles. The rider already excludes the two
false-positive routes: plants carrying the benchmark's CT-only CEMS flag (a metering artifact, rule
14) and rows with no meter.

| | rows | floored TWh | share |
|---|---|---|---|
| **FAIL** — measured median 0.000 MW over the floor's own binding hours | **41** | **16.234** | **73.8 %** |
| pass | 17 | 5.749 | 26.2 % |

**No overlap.** FAILing rows carry `measured_zero_share` **0.532 – 0.986** (median 0.724); passing rows
**0.000 – 0.457**. The gap 0.457 → 0.532 is empty — two populations, not a threshold artifact.

Per plant across six years: **593 (6/6), 3138 (6/6), 3775 (6/6), 384 (4/4), 874 (3/3), 599 (1/1)** fail
every year they are floored; 3131 (5/6), 3148 (5/6), 3149 (4/6) fail most; 1353 (0/6), 3140 (1/6),
3809 (0/1) pass.

**The rider is a LOWER BOUND:** it covers 21.983 of the mechanism's 34.472 TWh of six-year forced
energy (63.8 %); the rest sits on plants it declines to convict for want of a trustworthy meter.

---

## 7. C8 IS PURELY PROVENANCE, AND IT GATES IN EXACTLY ONE YEAR

Scored through `calibration_verdict.score_forced_share` on the committed artifacts:

| year | ST_GAS C8 | D-2 forced | why |
|---|---|---|---|
| 2020 / 2021 / 2022 | SKIPPED | 54.3 / 64.0 / 46.5 % | immaterial — 1.5 / 1.5 / 1.8 % of ISO load |
| 2023 / 2024 | SKIPPED | 39.1 / 36.6 % | immaterial — 1.7 / 1.6 % |
| **2025** | **FAIL** | **41.3 %** | material at **2.2 %** |

The 2025 failure text names one cause and only one:

> *"above the 30 % cap **and NOT grounded**: **provenance — floors a unit its own meter says is
> offline** (D-4 per-unit conduct FAIL): `st_netload_drag` (plant 3131), (3138), (3148), (3775),
> (593)"*

**The 30 % cap is not what fails PJM.** Rubric v2.2's grounded-above-budget escalation is available
and the D-1 shape leg is never reached. **So the mandate's LEVEL does not have to move for C8 — its
MEMBERSHIP does.** That reframes the whole card, and it is why the arms below target allocation
rather than level.

---

## 8. THE ALLOCATION FAMILY, FALSIFIED PRE-SOLVE

Fleet builds off the keeper's own recipe (`replay_keeper.run_year_kwargs`, the only sanctioned
reconstruction — caiso-243/244), 3,789 rows reproducing the keeper's fleet, armed through the same
`prb_overrides` bag `replay_keeper --set` uses. The conduct rider is scored on `{min_gen > 0}` — a
**superset** of the solve's `at_floor_mask`, hence the **more forgiving** basis, so a mechanism that
cannot improve here cannot improve on the real one for a better reason than noise.

### 8a. Identity and confinement — arm M does exactly what its docstring says

| gate | measured (2023) |
|---|---|
| **aggregate preserved** | control **8.8093** TWh → arm **8.8093** TWh, Δ = **0.000000**; **max hourly \|Δ\| = 0.000000 MW** |
| **confinement** | **42 of 3,789 rows move, all ST_GAS**; `mc_base` max \|Δ\| = **0.0000000000 $/MWh** |

Same MW, different plants, no price effect — exactly the ercot-259 contract.

### 8b. And it clears nothing

| year | **C** control | **M** merit_allocation | **P** min_run_persistence | **MP** both |
|---|---|---|---|---|
| 2023 | 4 FAIL | **4** | **4** | **5** |
| 2024 | 2 FAIL | **2** | **2** | **2** |
| 2025 | 2 FAIL | **2** | **2** | **3** |
| mandate TWh 2023 | 8.8093 | 8.8093 | 8.8481 | 8.8481 |
| mandate TWh 2025 | 11.5063 | 11.5063 | 11.5332 | 11.5332 |

**Not one plant flips FAIL → pass under any arm, in any year.** The composition is **strictly worse**
than either half in two of three years, and the extra conviction is **the same plant both times**
(3148, `pass → FAIL`): persistence widens each plant's binding window toward all 8,760 h while merit
allocation concentrates the mandate onto fewer plants; on 3148 the widening wins and the median falls
through zero.

**This falsifies the explicit successor hypothesis pjm-177 §5 item 3 left on the record** —
*"the HOURS are now right and the PLANTS are still wrong … `netload_drag_merit_allocation`'s object,
and the two would have to compose to close the mask properly."* They do not compose. They interfere.

### 8c. WHY IT CANNOT WORK — the mandate's hours against the meter's

A passing median needs more than half the binding hours non-zero, so the largest floorable window is
≈ 2 × the meter's non-zero hours.

| plant | year | mandate h | **meter > 0 h** | **mandate ÷ max floorable** | conduct |
|---|---|---|---|---|---|
| **3775** | 2023 | 7,666 | **707** | **5.42** | FAIL |
| 3149 | 2023 | 7,666 | 1,253 | 3.06 | FAIL |
| 593 | 2023 | 7,625 | 1,414 | 2.70 | FAIL |
| 384 | 2023 | 2,759 | 1,437 | 0.96 | FAIL |
| **3775** | 2024 / 2025 | 7,579 / 7,885 | 1,348 / 1,985 | **2.81 / 1.99** | FAIL |
| 593 | 2024 / 2025 | 5,818 / 7,718 | 1,922 / 2,860 | 1.51 / 1.35 | FAIL |
| 1353 / 3131 / 3138 / 3140 | all | — | — | **0.45 – 0.85** | pass |
| **fleet TOTAL** | 2023 / 2024 / 2025 | 56,110 / 49,424 / 59,617 | 30,723 / 35,152 / 39,212 | **0.91 / 0.70 / 0.76** | — |

**Read the last row against the ones above it.** In aggregate the mandate's hours are comfortably
supportable by the metered fleet (0.70 – 0.91). The failure is entirely **distributional**. Plant 3775
is floored for **87 % of the year on a unit whose meter reads non-zero in 8 % of it.**

An ALLOCATION swap cannot fix that, because `merit_allocation`'s merit signal is **bid heat rate**,
and heat rate is not duty — its own docstring records the weakness rather than tuning around it
(*"Spearman(heat rate, CAMPD online fraction) … only −0.286 (p = 0.49) in 2025"*).

---

## 9. THE ROOT CAUSE, AND THE SEAM THIS REPOSITORY ALREADY OWNS

`data.outages.ST_GAS_PEAKER_PLANTS`, verbatim:

> *"Peaker-class ST_GAS plants: patchy / spiky run rate (run only when called), so they get NO outage
> overlay (and **no reliability min-gen floor** in `fleet.generators_to_fleet_arrays`) — they dispatch
> purely economically. The remaining ST_GAS units run sustained idling / drag patterns and DO get the
> outage + reliability treatment."*

Its CAISO members were admitted on exactly the evidence this session has for PJM — *"CAMPD 2024-25
shows them online only 0.4–2.5 % of hours (spiky, run-when-called), so the event-based outage rule
would flood them with economic-idleness windows."*

**The registry names 6 ERCOT plants and 3 CAISO plants. It names NO PJM plant.**

PJM's ST_GAS fleet against that criterion — meter online share of 8,760 h, from the committed bench:

| plant | MW | 2023 | 2024 | 2025 | mean | D-4 conduct, 6 y |
|---|---|---|---|---|---|---|
| **3161** | 862 | **2.3 %** | **4.3 %** | **3.0 %** | **3.2 %** | skipped (ct_only) — zero-share 0.97 |
| 50279 | 23 | 7.7 % | 3.1 % | — | 5.4 % | skipped |
| **3775** | 475 | **8.1 %** | 15.4 % | 22.7 % | **15.4 %** | **6 FAIL / 0 pass** |
| **384** | 1,320 | 16.4 % | — | — | **16.4 %** | **4 FAIL / 0 pass** |
| 1571 | 1,318 | 13.4 % | 17.8 % | 33.8 % | 21.7 % | skipped (ct_only) |
| **593** | 710 | 16.1 % | 21.9 % | 32.6 % | **23.6 %** | **6 FAIL / 0 pass** |
| 3148 | 1,701 | 15.9 % | 48.6 % | 50.7 % | 38.4 % | 5 FAIL / 1 pass |
| 3149 | 1,758 | 14.3 % | 49.3 % | 73.8 % | 45.8 % | 4 FAIL / 2 pass |
| 3138 | 354 | 65.4 % | 56.6 % | 53.1 % | 58.4 % | 6 FAIL / 0 pass |
| 3131 | 632 | 65.5 % | 59.2 % | 55.6 % | 60.1 % | 5 FAIL / 1 pass |
| 3140 | 1,616 | 74.5 % | 76.3 % | 76.4 % | 75.7 % | 1 FAIL / 5 pass |
| 1353 | 280 | 74.4 % | 73.9 % | 82.7 % | 77.0 % | **0 FAIL / 6 pass** |

**Every plant below ~25 % duty is convicted in every year it is floored, with zero passes.** Plant
3161, at 2.3–4.3 % duty on 862 MW, is materially the same unit class as the CAISO plants already in
the registry, and it carries a floor in 7,666–7,885 hours a year.

**Stated honestly, because the split is not perfectly clean at the top:** 3138 (58.4 % duty) and 3131
(60.1 %) are also convicted on the committed at-floor basis, and duty alone does not explain them.
So a membership repair is the *largest* part of this defect, not provably all of it.

### 9a. THE LAY-UP DIAGNOSTIC — it clears the gate completely, and it is still refused

`netload_drag_layup_window_mask` (ercot-256) masks the floor by the **measured** economic-lay-up share
(`pmax × max(0, availability − layup_share)`). PJM's artifact targets precisely the convicted plants:
2023 mean laid-up share **3161 98.9 %**, **3775 95.5 %**, **1571 70.3 %**; 2025 **3161 98.2 %**,
**3775 80.4 %**, **3148 50.3 %**.

Built and scored on the same basis as the other arms:

| year | **C** control | **L** layup_mask | **ML** merit + layup |
|---|---|---|---|
| 2023 | **4 FAIL** | **1** | **1** |
| 2025 | **2 FAIL** | **0** | **0** |
| mandate TWh 2023 | 8.8093 | **5.8008** (−34.2 %) | 5.8008 |
| mandate TWh 2025 | 11.5063 | **7.5974** (−34.0 %) | 7.5974 |

Plant by plant it is emphatic — 2025 plant 3775 goes **7,885 → 2,055** binding hours with its median
**0 → 142 MW**; 593 goes 7,718 → 2,962 with median **0 → 121**; 3161 goes 7,885 → **168**.

**Three readings, and the third is the one that decides it.**

1. **It is not an allocation swap — it is a LEVEL cut.** The mandate falls **~34 % in both years**.
   That places it in a different mechanism class from M / P / MP, all of which preserved the aggregate
   exactly. It clears the gate by removing forcing, not by relocating it.
2. **It quantifies the object precisely, and this is the session's most useful single number:
   ~34 % of PJM's ST_GAS drag mandate sits inside measured economic lay-up.** The convicted binding
   is not scattered — it is almost entirely concentrated in hours the plant had economically stood
   itself down. That is independent confirmation of §9's diagnosis from a completely different
   instrument.
3. **It is REFUSED as a fix, on governance, not on measurement.**
   `netload_drag_layup_window_mask` is registered in `_BACKCAST_ONLY_OVERLAY_FIELDS` — a rule-13
   `[R-MEASURED]` overlay with **no forward analogue**. Rule 17 `[R-FLOOR-WINDOW]` clause (c) requires
   a floor to state *how it regenerates in a forecast year*; grounding the drag's provenance on a
   backcast-only overlay would make the mechanism unfalsifiable forward and would buy the C8 pass with
   a measured outcome — the exact route rule 1 `[R-STRUCT]` exists to forbid. **The fact that it is
   the one arm that works is a reason for suspicion, not for adoption.**

**And its own residual failure argues for the successor rather than for itself.** The single 2023
conviction it cannot clear is plant **3149** — a unit with 14.3 % meter duty that year, which the
lay-up derive **never classified at all** (it carries no 2023 ST_GAS lay-up series). A membership
criterion keyed to duty catches 3149; a lay-up mask does not. So even setting rule 13 aside,
**membership is the more faithful object.**

---

## 10. CARD 2 — THE RESIDUAL VOLUME SURPLUS, RE-MEASURED

Card 1 landed no solve, so the handoff's "re-measure after card 1 lands" is not available. What the
committed artifacts already say, and it changes the card:

| year | model fossil | actual fossil | **SURPLUS** | ST_GAS Δ | CT_PEAK Δ | CC_REG Δ | COAL Δ | virtual net |
|---|---|---|---|---|---|---|---|---|
| 2020 | 492.19 | 457.09 | **+35.10** | +4.93 | −0.30 | +9.23 | **+21.25** | −2.62 |
| 2021 | 505.13 | 478.26 | **+26.87** | +8.17 | −6.64 | **+27.59** | −3.70 | −11.16 |
| 2022 | 518.24 | 483.79 | **+34.46** | +8.97 | −4.60 | **+24.84** | +5.16 | −14.03 |
| 2023 | 486.87 | 478.96 | **+7.90** | +4.65 | −2.29 | +4.94 | −0.51 | +0.96 |
| 2024 | 499.32 | 498.95 | **+0.36** | +0.05 | +0.35 | +3.47 | −3.34 | +1.55 |
| 2025 | 534.91 | 515.67 | **+19.24** | +4.30 | +4.57 | +3.09 | +7.93 | −3.61 |

Reproduces the handoff's 2020-22 figures (+35.09 / +26.96 / +34.55). **Two things the handoff did not
have:**

1. **The surplus is 2–90× larger in the holdout years than in the training years** (+35.1 / +26.9 /
   +34.5 against +7.9 / +0.4 / +19.2). It is overwhelmingly a **2020-2022 phenomenon**, not a defect
   of the trained recipe carried forward.
2. **Its composition is not stable**: 2020 is carried by **COAL** (+21.25) while 2021/2022 are carried
   by **CC_REGULAR** (+27.59 / +24.84). One mechanism is unlikely to own both.
3. The DA-virtual phantom-demand position is **negative in exactly the three touchpoint years**
   (−2.62 / −11.16 / −14.03) and ≈0 in the training years — i.e. the channel pjm-142/158/166 opened is
   also a **holdout-year** phenomenon.

**ST_GAS is 14–33 % of the touchpoint surplus, so card 1 could not close it even if fully repaired.**
Per the handoff, the phantom-demand remainder is **ROUTED, not armed**, to PJM's owner-declared-closed
price-formation frontier (pjm-142). The hydro deficit is a separate accuracy lane and is not touched
here. **Rule 30(c): none of this downgrades PJM** — the ISO's determination is the train-tier verdict.

---

## 11. WHAT IS NOT CLAIMED

- **No LP was solved, so no criterion moved in either direction.** Every number here is a committed
  artifact or a zero-LP fleet build. Nothing is offered as evidence of forecast skill.
- **The conduct proxy is a proxy.** The rider's true basis is `at_floor_mask` (LP dispatch *at* the
  floor), a strict subset of the `{min_gen > 0}` set used here; on 2023 it gives 4 convictions where
  the committed artifact gives 6, and on 2025 it gives 2 where the artifact gives 5. It is the
  **more forgiving** basis, which is why "zero flips" is meaningful — but a solved arm could differ,
  and that is stated rather than assumed away.
- **A membership repair is not proven sufficient.** §9's split is absolute below ~25 % duty and
  imperfect above it (3138, 3131). The successor card must measure, not assume.
- **The offer-band asymmetry is reported, not adjudicated.** CT_PEAKER carries 1.05 / 1.25 / 1.65
  authorized bands against ST_GAS's flat 1.000; the assembled offers say it produces no inversion,
  but whether the asymmetry is itself right is a different question and was not this card's.
- **Nothing in ERCOT's or CAISO's verdict was transferred** (rule 25 `[R-ISO-SCOPE]`). The ercot-259
  and nyiso-140 mechanisms were tested **in PJM, on PJM's fleet and PJM's meter**, and the
  conclusions are PJM's.

---

## 12. THE SUCCESSOR CARD, SPECIFIED

**Object:** PJM membership in `data.outages.ST_GAS_PEAKER_PLANTS` — the existing seam, not a new
mechanism (rule 19 `[R-ONE-MECH]`), on-registry (rule 24), per-ISO from PJM's own meter (rule 25).

**What its charter must fix ex ante, before any solve:** the qualifying criterion and its threshold,
declared in a PRECOMMIT and **never swept** (rule 1 `[R-STRUCT]` / rule 29 `[R-SCREEN]`); the rule-13
argument that peaker-vs-baseload character regenerates forward (the registry's other members were
admitted on measured duty, so the precedent exists but is not automatic); and the **second consumer**
— membership also removes the plant's **outage overlay**, so the blast radius is larger than the floor
and must be measured on both legs.

**Its zero-LP phase 0 is already half-written**: §9's duty census, plus the same conduct-rider
recomputation this session used, will say pre-solve whether membership clears the convictions that
`merit_allocation` and persistence could not.

**And §9a gives it a pre-registered target with no free parameter in it.** The backcast-only lay-up
mask removes **34.2 % / 34.0 %** of the 2023 / 2025 mandate and clears all but one conviction. A
forward-native membership repair is aiming at the **same object by a different route**, so
"does membership reach a comparable share of the mandate, and does it clear the plant (3149) the
lay-up route missed?" is a structural question fixable ex ante — not a residual.

---

## 13. DISPOSITION — AND THE RULE-31 PROMOTION QUESTION

**Keeper `2026-09-09-pjm-fuelvintage-ep-level` and PJM's headline are UNCHANGED.** Nothing was
promoted, registered, or solved; no holdout year was touched (2019 and H1-2026 were neither attempted
nor designed around — locked tier, `final` empty, freeze ACTIVE).

**There is nothing to promote from this session, and that is the honest answer to rule 31
`[R-RETAIN]`'s question rather than an evasion of it:** no LP was run, so **no solve results exist on
disk to preserve or lose**. The only artifacts are this document and the PRECOMMIT, both committed and
pushed. The zero-LP `.npz` fleet snapshots under `/tmp/` are regenerable in ~4 minutes each from the
committed recipe and carry no result the documents do not.

**The question actually put to the owner is a different one, and it is about the incumbent keeper:**

> PJM's single remaining criterion is C8 on 2025 ST_GAS, and this session establishes that **the two
> mechanisms already on `main` for it cannot close it** — one of them (`netload_drag_min_run_persistence`)
> being the arm pjm-177 left open as a promotion question the same day. **Should that promotion
> question now be answered NO on this evidence** (it clears zero convictions and, composed with
> merit allocation, adds one), and the lane re-chartered onto the `ST_GAS_PEAKER_PLANTS` membership
> object in §12?

### 13a. GATE BASELINE — this tree changes NO source code

The diff against `origin/main` is two docs, a `.gitignore` block, PJM's matrix shard and PJM's
calibration log.

| gate | result |
|---|---|
| `check_mechanism_matrix --base origin/main` | **integrity OK**; keeper stamps and §5.x prose headers match every `keepers/<ISO>.json`; all four ratchets OK |
| `audit_keepers --iso PJM` | **PASS — 0 failures, 0 warnings** |
| `build_status --check --iso PJM` | **status parts in sync** |
| `check_cache_key_registration --base origin/main` | **green** — no new fields; 832 fields / 287 registered / 304 solve-surface names all declared. *(The `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` RED the handoff expected is no longer present on `main`.)* |
| `check_registry_payload_parity` | fails on the **five pre-existing `ercot262_arm_*`** bundles only — ERCOT's, committed on `main`; rule 25 `[R-ISO-SCOPE]` says leave them. **This tree adds none**, and wrote no bundle at all. |
| `pytest tests/scoring` | **15 failed / 1,533 passed / 12 skipped**, all in `test_golden_manifest_provenance.py` and `test_registration_marker_gate.py` — files this diff cannot reach. The handoff's expected baseline was 16, i.e. `main` moved by one; **this session adds none.** |
| `pytest tests/unit/config/test_mechanism_matrix_*` | **33 passed** |

No `ruff` run was owed: no repository Python was written (the probe scripts live in the session
scratchpad and are not committed).

**Rule 28 duty discharged:** PJM's matrix shard is re-stamped in this session with the
`netload_drag_floors` cell verdicts for both sub-gates. No other ISO's shard, keeper, status part or
calibration log was touched.
