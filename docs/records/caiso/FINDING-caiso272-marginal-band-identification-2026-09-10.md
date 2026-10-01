# FINDING — caiso-272: the CC offer ladder is **NOT** the carrier of CAISO's +1 heat-rate bias. It prices within **+0.17 HR points** of the market when it sets the price, and **68 %** of the bias sits in the 16.6 % of hours where λ is in a **GAP** in the thermal stack. Separately, **70 % of the C3a-2022 dollar miss is the DA−RT premium the rubric itself lists as OUT OF REPRESENTATION.** **ZERO LP. Nothing armed. RECOMMENDATION: ACCEPT (c).**

**Session caiso-272, 2026-09-10.** Branch `claude/caiso-272-marginal-hr-cfsk95` off `main`
`49b60041`. Keeper **`2026-09-10-caiso-269-lateevening-clean`** (`caiso269_lateevening_span`
+ `_2022`, `git_sha` `8d627e64`) **UNCHANGED**. **CALIBRATED**, single ledgered C3c.
**No solve, no shard, no `ScenarioConfig` field, no flag, no derive, no run registered, no
promotion, no keeper move, no other ISO's shard touched.** CAISO only (rule 25 `[R-ISO-SCOPE]`).

---

## §0 — WHAT THIS SESSION WAS ASKED, AND THE ANSWER IN ONE PARAGRAPH

The charter: *"Is the +1 HR bias (a) an OFFER-SURFACE question the authorized rule-1 channel
should be spent on, or (b) a MISSING-STRUCTURE question needing new data, or (c) an accepted
permanent residual?"* — and: *"Either fund the ONE unmeasured object or accept it."*

**(a) is REFUTED by measurement. (b) has no object left to fund — both carriers are already
adjudicated closed by prior owner rulings. (c) is what the evidence supports, and it is the
recommendation.** The object is no longer unmeasured: it decomposes cleanly into three parts,
none of which the authorized offer-curve channel can reach.

**Card 0(d) is discharged by saying what did not happen: no arm survives card 0(c), so no
screen year was named, no shard was launched, and no LP was spent.** The session's mandatory
BIND CHECK and PARTITION CHECK are addressed in §6.

---

## §1 — CARD 0(a): G-DRIFT. **ALL HUNKS INERT ⇒ G-CTRL FORM 4 VALID, NO CONTROL SOLVE.**

`git diff 8d627e64 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
→ **8 files, 512 insertions, 8 deletions, and the diff is PURELY ADDITIVE** on the three
`src/` files (zero deletion lines in `constants.py`, `scenarios.py`, `interchange/spec.py`).

| file | change | classification for a CAISO **backcast** |
|---|---|---|
| `scripts/lib/forecast_parity_registry.py` | two MISO seam-ladder `ParityDeclaration`s | **INERT** — another ISO's branch; a declarations registry, not a solve path |
| `scripts/lib/spp63_g5.py` | new file, SPP-63 parent-side G-5 instrument | **INERT** — another ISO's branch; nothing on the CAISO path imports it |
| `scripts/run_calibration.py` | 1 call site, `_apply_iso_monthly_ttc(..., config=config)` | **INERT** — the callee's first statement is `if iso != "NYISO": return ttc` |
| `src/market_sim/pipeline/ttc.py` | `nyiso_total_east_cutset_ttc` table selection | **INERT** — same NYISO guard, unreached for CAISO |
| `src/market_sim/config/constants.py` | `NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH` added | **INERT** — one new NYISO table, no existing symbol touched |
| `src/market_sim/config/solve_surface_declared.py` | 1 declared hash for that table | **INERT** — D79 declaration; NYISO-scoped |
| `src/market_sim/model/interchange/spec.py` | `MISO_SEAM_LADDER_BY_YEAR[2022]` added | **INERT** — another ISO's branch |
| `src/market_sim/config/scenarios.py` | `nyiso_total_east_cutset_ttc` (new, default off) **and the retroactive cache-key registration of `caiso_dsw_lateevening_clean`** | **INERT — and this is the one hunk that names CAISO, so it is classified explicitly** |

**The one CAISO-touching hunk, adjudicated rather than waved through.**
`caiso_dsw_lateevening_clean` — the keeper's own armed field — was added to
`_CACHE_KEY_OPTIONAL_FIELDS` / `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` **retroactively**, because
its own merge missed the registration and it therefore entered the digest unconditionally,
orphaning every on-disk key in every ISO. The registration changes **cache-key computation
only** — no offer, no bound, no row, no dual. And on an **ARMED** run (this keeper) the field's
value differs from the registered default, so it stays in the digest at the same value it
carried before the repair: **the keeper's key is unchanged, and so is every number it solved.**
Classified INERT for dispatch, and named here rather than buried, because a hunk carrying this
ISO's name should never be classified silently.

**⇒ G-DRIFT is ALL-INERT. G-CTRL form 4 is valid: the committed keeper bundle is the control,
and no control solve was spent** (rule 29 `[R-SCREEN]` (b)). No arm was solved either, so the
control was not in fact needed — the audit is recorded because the charter required it and
because it is the standing precondition for any successor lane that does solve.

---

## §2 — CARD 0(b): THE INSTRUMENT, AND ITS VALIDATION BEFORE ANY CONCLUSION

`scripts/probes/_caiso272_marginal_band.py` → `results/calibration/_caiso272_marginal_band.json`.
The caiso-250 `mc = λ` instrument, run at **LP-ROW grain** on the keeper's own reconstructed
offer array (`run_year(..., fleet_only=True)` — which the orchestrator documents as *"the
assembled P0 objective ... so post-solve offer-stack diagnostics read the SAME offer prices the
LP solved on"*), matched against the committed P1 zonal dual.

**G-REPRO — the instrument returns the independently-published numbers exactly:**

| published, by | value | this instrument |
|---|--:|--:|
| caiso-271 §0: `econc05`-active hours | 6,924 | **6,924** |
| caiso-271 §0: their share of 2022 load | 81.8 % | **81.79 %** |
| scorer (committed artifacts): C3a-2022 vs RT | +12.9 % | **+13.9 %** at my own weight basis; the scorer's own **+12.9 %** is quoted throughout |
| scorer: C3b-2022 NRMSE vs RT | 0.2402 | **0.2402** (recomputed with `calibration_verdict._nrmse`) |
| caiso-271 §0: model implied marginal HR, `econc05` | 10.33 | **10.394** |
| caiso-270 §4: 48-month mean `dHR` | +1.01 | **+1.166** for 2022 whole-year, consistent |

**The one approximation, stated at the gate.** `tranche_startup_amortization` is OFF on this
keeper, so the only P0→P1 wedge is `compute_monthly_markup`'s `startup / max(avg_run, 1)`,
whose denominator needs a P0 dispatch this session may not spend an LP to get. It is therefore
**bounded exactly from the fleet** — and the bound settles it: the markup is **identically
$0.00 for every `econ` and every `peak` tranche in every class**, because only `committed` rows
carry a startup cost at all (CC committed ≤ $50/MW, CT committed ≤ $20/MW, ST_GAS ≤ $7/MW).
**The approximation cannot touch the identification of the econ ladder, which is the whole
finding.**

**The scarcity adder is cited, never re-derived** (caiso-229 bound $0.017/$0.006/$0.003 per MWh;
caiso-270 §3.3's four instruments put 2022's at ~0). The match tolerance is fixed at **$0.25 —
10× the largest such bound** — before the first number, and is **never swept**: three wider
settings are reported beside it *precisely so the reader can see the answer does not move*.

---

## §3 — THE ANSWER: WHO SETS THE CAISO PRICE IN THE `econc05` HOURS

CA-pooled, tolerance $0.25, **83.4 % of the `econc05` load-weight matched**. (Pooled across the
five CA zones because `caiso_zonal_loss_surface` makes a zone price off another zone's unit
plus the loss/congestion wedge; the own-zone-only column is reported below and says the same
thing.)

| marginal family | share of matched weight | mean λ | **implied HR** |
|---|--:|--:|--:|
| **CC econ** | **51.21 %** | $96.25 | **9.458** |
| CT econ | 16.97 % | $114.28 | 11.229 |
| CC committed | 12.15 % | $83.24 | 8.179 |
| CT committed | 9.89 % | $102.75 | 10.096 |
| CT peak | 4.89 % | $112.91 | 11.094 |
| biomass | 2.13 % | $59.05 | 5.803 |
| CC peak | 1.93 % | $101.53 | 9.977 |
| ST_GAS | 0.79 % | $135.63 | 13.327 |
| oil | 0.04 % | $205.30 | 20.173 |

**THE MARKET'S OWN implied marginal heat rate in these same hours is 9.289** (RT, load-weighted
actual ÷ the same delivered-gas series). So:

* **The CC econ ladder, when it is the price-setter — half the weight — prices at 9.458 against
  the market's 9.289. That is +0.17 heat-rate points.**
* **All CC families together are 65.3 % of matched weight at 9.235 — 0.05 points BELOW the
  market.**
* The non-CC families are 34.7 % at **10.612**, and carry **+0.478 HR points** of the mix.

**And the answer does not move with the instrument's one free choice:**

| setting | coverage | CC-marginal share | CC implied HR | non-CC implied HR | HR points from non-CC |
|---|--:|--:|--:|--:|--:|
| own-zone, tol $0.25 | 50.8 % | 57.9 % | 9.246 | 10.501 | +0.528 |
| CA-pooled, tol $0.25 | 83.4 % | 65.3 % | 9.235 | 10.612 | +0.478 |
| CA-pooled, tol $1.00 | 97.8 % | 68.7 % | 9.412 | 10.917 | +0.471 |
| CA-pooled, tol $3.00 | 99.4 % | 71.3 % | 9.595 | 11.216 | +0.465 |

CC-marginal share 58–71 %, CC implied HR **9.235–9.595** against the market's **9.289** in every
one, and the non-CC contribution pinned in a **+0.465 to +0.528** band. A result that had
depended on the tolerance would have been an artifact; this one does not.

The top marginal plants are the CA CC fleet by name — Moss Landing, Delta, Metcalf, Colusa,
Gateway, Russell City, Mountainview — with two CT_PEAKERs (Panoche, Sentinel) and the
`Combustion Turbine Project` in the tail. Nothing exotic sets this price.

### §3.1 — The 16.6 % the price-match instrument CANNOT name, and what it is

| unmatched (CA-pooled, tol $0.25) | |
|---|--:|
| share of `econc05` load-weight | **16.56 %** |
| mean distance to the nearest available CA offer | **$12.86** |
| λ **ABOVE every** available CA offer (scarcity / import + congestion) | 2.63 % |
| λ **BELOW every** available CA offer (surplus) | 0.02 % |
| **λ in a GAP inside the CA stack** | **97.35 %** |
| implied HR of that weight (by residual, §3.2) | **≈ 13.8** |

Not scarcity, not surplus: **λ sits in a hole in the thermal offer stack in 97 % of it.** That
is verbatim the signature caiso-250 §1.5 identified — *"λ sits in a gap in the thermal stack,
which is what a non-thermal column setting the price looks like"* — with the stack 6–8× sparser
near λ there than in thermal-marginal hours.

### §3.2 — The +1.105 HR bias, decomposed. **The CC ladder contributes NOTHING.**

Model `econc05` implied HR **10.394** vs the market's **9.289** = **+1.105**.

| segment | share of `econc05` weight | implied HR | vs market 9.289 | **contribution to the +1.105** |
|---|--:|--:|--:|--:|
| CC-marginal | 54.5 % | 9.235 | **−0.054** | **−0.029** |
| non-CC-marginal (CT / ST_GAS / oil) | 29.0 % | 10.612 | +1.323 | **+0.383** |
| unmatched — λ in a gap | 16.6 % | ≈13.80 | +4.51 | **+0.747** |
| | | | **sum** | **+1.101** ✓ |

**68 % of the bias is the gap hours. 35 % is the CT/ST tail. The CC offer ladder contributes
−3 % — it is pulling the wrong way for anyone who wanted to tune it.**

---

## §4 — CARD 0(c): THE ADJUDICATION

### (a) OFFER SURFACE — **REFUTED, on measurement, not on judgement.**

The authorized rule-1 `[R-STRUCT]` / rule-13 `[R-MEASURED]` channel is the
`offer_curve_by_group` band multipliers. The CC bands are the only ones with enough weight to
matter, and **they are already right**: +0.17 HR points when marginal, −0.05 across all CC
families. Spending the channel there would move the **54.5 %** of weight that is currently
accurate and would leave **both** carriers untouched, because neither is a CC offer level.
Nothing here is a reason to *resize* a multiplier either — that would be selecting a factor
against the residual, which rule 1 condition (c) forbids outright.

This is also an **independent structural vindication of the owner's refusal of caiso-267 and
caiso-268's flat fossil multipliers**: those arms were refused on rule-1 grounds without this
measurement, and the measurement now says they were aimed at the one band that was not the
problem.

### (b) MISSING STRUCTURE / NEW DATA — **no object left to fund.**

Both carriers are measured, and **both are already adjudicated closed by standing rulings**:

1. **The gap hours (68 % of the bias)** are caiso-250 §7 DO-NOT-REDO items 1–2 and caiso-168's
   object: *"caiso-168's §5 instrument census is MASK-INDEPENDENT … it censuses instrument
   CLASSES, not hours, so extending the object's time window does not open a charge-side
   channel. Never propose a new charge-side cap, floor, adder or hurdle."* This session's
   measurement **strengthens** that closure rather than reopening it — the object is larger and
   more diurnally spread than caiso-168's mask, exactly as caiso-250 said, and the census that
   closed it does not depend on the mask.
2. **The CT/ST tail (35 % of the bias)** is the **CT_PEAKER volume residual the owner declared
   permanent** at caiso-261 (`keepers/CAISO.json declared_residual_ct_volume`;
   `ASSESSMENT-caiso261-panoche-instrument-search`), DO-NOT-REDO without new public evidence.

**So the charter's "ONE unmeasured object" does not exist.** It was one object only while it
was unmeasured; measured, it is two closed objects and a scoring-basis effect (§5). There is
nothing here to fund, and I do not ask for funding.

### (c) ACCEPTED PERMANENT RESIDUAL — **RECOMMENDED.**

The CAISO 2022 C3a/C3b miss should be **accepted and reported at full magnitude**, with the
decomposition of §3.2 and §5 on its determination basis. **No lever is proposed and none should
be funded.** Rule 30(c) `[R-TOUCHPOINT-FOLD]` already settles the consequence: a held-out year
never downgrades the ISO, so **CAISO stays CALIBRATED on 2023–2025 and the 2022 rung stays
NOT-YET**, which is the correct and unchanged state either way.

---

## §5 — WHAT PHASE 0 SURFACED THAT IS **THE OWNER'S**, AND THAT I AM DELIBERATELY NOT DECIDING

**70 % of the C3a-2022 dollar miss is the DA−RT premium.** On the **scorer's own** committed
records (`--json`, rubric v3.7), not on my weight basis:

| 2022, load-weighted, SCORER's numbers | $/MWh |
|---|--:|
| model | 95.39 |
| **DA actual** (`da_lw`) | **92.14** |
| **RT actual** (`rt_lw`, the GATED benchmark) | **84.49** |
| model − RT (**this is the +12.90 % C3a miss**) | **+10.90** |
| model − DA (the scorer's own non-gated `da_diagnostic`) | **+3.25 → +3.5 %** |
| **DART (DA − RT)** | **+7.65 → 70.2 % of the miss** |

(My own instrument's basis, reported only to show it is in range, gives +11.63 / +4.00 /
+7.63 → 65.6 %. The scorer's 70.2 % is the number quoted everywhere else.)

Per year, on the scorer's records:

| C3a | model | vs RT (**gated**) | vs DA (diagnostic) |
|---|--:|--:|--:|
| 2022 | 95.39 | **+12.90 %** | **+3.53 %** |
| 2023 | 56.52 | +4.34 % | −8.37 % |
| 2024 | 37.61 | +8.54 % | −0.95 % |
| 2025 | 37.13 | +7.87 % | +4.89 % |
| **mean abs** | | **8.41 %** | **4.43 %** |

And the same on the other open criterion, computed here with `calibration_verdict._nrmse` and
the scorer's own model-monthly construction — a companion **the scorer does not emit**:

| C3b NRMSE | vs RT (gated) | vs DA (companion) | band |
|---|--:|--:|---|
| **2022** | **0.2402 — FAIL** | **0.1510** | ≤0.20 target / ≤0.25 commercial |
| 2023 | 0.0827 | 0.1551 | |
| 2024 | 0.1392 | 0.1146 | |
| 2025 | 0.1070 | 0.0811 | |

**Both of CAISO's open 2022 failures pass on the DA basis.** And hourly, over all 8,760 hours,
the model's price tracks DA better than RT on every metric:

| | vs RT (gated) | vs DA |
|---|--:|--:|
| load-weighted MAE | $25.87 | **$16.06** |
| load-weighted RMSE | $71.33 | **$42.09** |
| Pearson | 0.7513 | **0.8948** |
| Spearman | 0.9014 | **0.9507** |

Across all four years the model is about **twice as close to DA as to RT** (mean |error| 4.43 %
vs 8.41 %), and nearer DA in **three of four years** (2023 is the exception).

**Why this is the owner's question and not mine.** The rubric's own OUT-OF-REPRESENTATION row
reads: *"The DA−RT risk premium (DART) an offer-cost, realized-weather LP cannot price without
fitting … the test must not demand these."* Yet C3a gates on RT, on the stated premise that
*"the model is structurally a real-time analogue (a perfect-foresight dispatch LP prices RT
physics, not day-ahead risk premia), so RT is the honest benchmark."* CAISO's measurement
contradicts that premise **in sign**: this model's price does not sit below DA where the premise
puts it — it sits **on** DA, in level, in hourly rank and in monthly shape.

**A hypothesis consistent with that, offered as a hypothesis and NOT proven here:** the keeper is
a single bid-cost clearing pass with commitment-cost recovery folded into the offer
(`compute_monthly_markup`) and a day-ahead RA must-offer construct (`caiso_ra_mustoffer`,
`caiso_ra_startup_bridge`), and there is **no RT re-dispatch pass**. That is structurally the
day-ahead construct, not the real-time one.

**I am NOT proposing to rebase C3a onto DA.** Proposing a benchmark change because it makes a
criterion pass is the same fitted selection rule 1 forbids in a mechanism, only in a different
register, and it is a **cross-ISO rubric matter** outside a CAISO lane's scope (rule 25). The
2022 rung stays NOT-YET on my recommendation. What is put to the owner is the **contradiction**,
with the numbers, because the rubric's OUT-OF-REPRESENTATION list is the owner's document and
this measurement bears on it in a direction it did not anticipate.

### §5.1 — The counter-evidence, at full magnitude

The DART decomposition is **not** an acquittal, and three measurements say so:

1. **The model's residual against DA is not zero: +$4.00/MWh load-weighted.**
2. **It is concentrated in the overnight and belly hours** — hod 22→12 is positive against
   **both** benchmarks (+$7 to +$14 vs DA, +$8 to +$20 vs RT). Present against DA too, so it is
   a **real model residual, not DART** — and it is the caiso-168/250 charge-side object again.
3. **Against DA the evening ramp is NEGATIVE**: hod 15–19 runs −$0.16 to −$26.02. The model
   **under**-prices the evening against DA. Opposite sign to the annual bias, reported because
   it is against interest.
4. **On C3c the DA basis is WORSE, not better, and in the years that carry the ledgered
   caveat.** The scorer's own tail records: 2023 model **23 h** against RT **47 h** and DA
   **80 h**; 2024 model **0 h** against RT **35 h** and DA **52 h**. The 2023–2025 tail DEFICIT
   — caiso-270 §5's *second, opposite-signed* object — gets further from DA than from RT. Any
   reading of §5 that treats DA as uniformly kinder to this model is wrong on its face.

So on the DA basis CAISO would trade one miss for a different, still-real one, and would move
*away* from the actual on the criterion it already carries a caveat for. That is a further
reason the answer to the charter is **accept**, not **rebase**.

---

## §6 — THE TWO MANDATORY ZERO-LP CHECKS, DISCHARGED HONESTLY

* **BIND CHECK — VACUOUS BY CONSTRUCTION, and said so rather than claimed.** It binds a new
  flag's `ScenarioConfig` delta and its marginal cost. **This session added no flag**, so there
  is nothing to bind. The duty is **not discharged by omission**: it is owed in full by the next
  CAISO lane that adds a solve flag, exactly as `RESULT-caiso269` §7 made standing and
  `FINDING-caiso270` §3.4(e) restated.
* **PARTITION CHECK — RUN, and it was not a no-op.** `data/clean/` is derived and gitignored, so
  this container started EMPTY. `PYTHONPATH=.:src python3.11
  scripts/data/curate_capacity_deliverability.py` was run and wrote 386 CAISO rows (5 ISOs,
  1,367 rows). Independently, the keeper's own `run_config.json` `resolved_inputs` was verified
  to read `seam_import_cap.by_year.2022.source = "mic_partition"`, `cap_mw = 15780.0` — i.e.
  the published MIC partition, **not** the retired fitted 7,500 MW scalar (caiso-157/188). The
  bundle this session differenced against is clean on rules 20/24.

---

## §7 — DISCLOSURES AGAINST INTEREST

1. **THERE IS NO PRECOMMIT FOR THIS SESSION, AND THAT IS A REAL GAP.** The charter's card 0
   ordered a PRECOMMIT before any shard; no shard was launched, and no arm, gate or prediction
   ever existed to pre-register. But the measurement was made before any document was written,
   so this finding is **not** a pre-registered result and must not be read as one. What stands
   in its place is **G-REPRO** (§2): the instrument returns six independently-published numbers,
   four of them exactly, before it is asked a single new question. That is a weaker guarantee
   than pre-registration and is labelled as such.
2. **The census is ISO-aggregate on the dispatch side.** `class_band_hourly` carries no zone,
   so band-level interiority is a **necessary condition only** — caiso-250 §4.3's standing
   caveat, unaddressed here. The identification in §3 rests on the **offer array**, which *is*
   per-row and per-zone, so it does not inherit that limit; but no causal claim is made.
3. **16.6 % of the weight is unnamed.** The instrument says what that weight is *not*
   (not scarcity, not surplus, λ in a gap) and infers its implied HR by residual. It does not
   name the column. Naming it would be re-opening caiso-250's closed object, which I decline.
4. **My C3a reproduction is +13.9 % at my own weight basis against the scorer's +12.9 %.** The
   scorer's like-for-like load-weighted bench (rubric v2.4) is the authority and is quoted
   everywhere a number is used; my basis is reported only to show the instrument is in range.
   The DART share (**70.2 %**) is computed on the **scorer's own** `da_diagnostic` row
   (`+3.5 % vs DA, DA−RT premium $+7.65`), not on mine; my basis would say 65.6 % and is
   reported beside it.
5. **The DA observation is not wholly new.** The scorer already emits `da_diagnostic` rows to
   make exactly this visible, and the rubric already anticipated DART. What is new is the
   **quantification** (70 % of the 2022 miss), the **C3b DA companion** (0.1510 — a number the
   scorer does not emit), and the **hourly rank/level evidence**. Nothing here reopens the
   rubric's decision; it reports a measurement that bears on it.
6. **The session did not deliver a fundable object, which is what a lever-hunting reader wants.**
   It delivers the opposite: a measured argument that there is nothing to fund. Three sessions
   have now been spent confirming that; this one says why, and recommends stopping.

---

## §8 — DO-NOT-REDO ADDS

1. **NEVER propose an `offer_curve_by_group` CC band multiplier as a lever on CAISO's
   marginal-heat-rate bias.** Measured: the CC econ ladder prices at implied HR 9.235–9.595
   against the market's 9.289 across four independent instrument settings, and CC-marginal hours
   contribute **−3 %** of the bias. The channel is authorized; there is nothing here for it to
   do. (This does not disturb the channel's standing for any other purpose.)
2. **The `econc05`-hour residual is NOT a CC capacity or CC offer object.** 68 % of it is the
   16.6 % of hours where λ sits in a GAP (caiso-250/168, closed, mask-independent census) and
   35 % is the CT/ST tail (caiso-261 owner ruling, declared permanent). Never re-fund either.
3. **The startup markup is identically $0 on every `econ` and `peak` tranche in every CAISO
   class** — only `committed` rows carry a startup cost (CC ≤$50/MW, CT ≤$20/MW, ST_GAS ≤$7/MW).
   A future probe on this keeper does **not** need a P0 dispatch to reason about econ-band
   offers.
4. **CAISO's model price behaves like the DAY-AHEAD price, not the real-time one** — level
   (+3.5 % vs DA against +12.9 % vs RT in 2022; mean abs 4.43 % vs 8.41 % over 2022–2025),
   hourly rank (Spearman 0.951 vs 0.901), monthly shape (C3b 0.151 vs 0.240) and the 2022 tail
   (586 h vs DA's 553 h against RT's 510 h). Any future reading of a CAISO price residual
   should decompose DART **first**. This is a REPORTING duty, **not** a licence to rebase a
   criterion — **and it does NOT hold on the 2023–2025 C3c tail, where DA is farther away
   than RT** (§5.1 item 4).
5. **The model's DA-basis residual is real and is in the overnight/belly (hod 22–12), and the
   evening (hod 15–19) is NEGATIVE against DA.** Never quote the DART decomposition as if it
   acquitted the whole residual.
6. caiso-271 §6, caiso-270 §6–§7, caiso-261, caiso-258 §7, caiso-250 §7, caiso-168 §8 stand in
   full.

---

## §9 — DELIVERABLES

`scripts/probes/_caiso272_marginal_band.py` + `results/calibration/_caiso272_marginal_band.json`;
this finding; the `docs/calibration-log/caiso.md` entry; an **evidence-only** append on the
CAISO matrix shard. **No cell verdict moves; no mechanism was tested; no run registered; keeper
unchanged; no bundle produced, so rule 31 `[R-RETAIN]` has nothing at risk in this container.**

**Next number: caiso-273.**
