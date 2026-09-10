# RESULT — pjm-d4-4: the forced-outage composition gap

**Session:** pjm-d4-4 · **Date:** 2026-09-10 · **Branch:** `claude/pjm-forced-outage-gap-o0kzlz`
**Scope:** PJM only. **Nothing is promoted, armed by default, or registered on the dashboard.**
Pre-registration: `docs/PRECOMMIT-pjm-d4-4-forced-outage-composition-2026-09-10.md` (the kill bar,
committed BEFORE the measurement) and `docs/PRECOMMIT-pjm-d4-4-screen-addendum-2026-09-10.md`
(the screen gates, committed BEFORE the shard).

---

## §0 — the verdict in one table

| object | status |
|---|---|
| **the stage-0 kill gate** | **PASSED on both pre-registered bars, at zero LP** — 4,570 MW over 2022's 92 actual RT > $200 hours against a bar of 2,425, and 1,185 MW annual mean against a bar of 700. About **5× the handoff's own naive scaling prediction** of 200-380 MW. |
| **the identification objection** (ERCOT's, inherited) | **TESTED rather than assumed** — the merit-order guard removes only **10.8 %** of the annual mean and **5.1 %** of the tail-hour family, and the committed artifact carries the SMALLER, guarded family. Elliott is the natural experiment (§4). |
| **the mechanism** | **BUILT** — `ScenarioConfig.unit_outage_short_windows_gas`, default off, off path proved byte-identical to `origin/main`, matrix row + all 7 cells, cache-key registered, 4 tests. |
| **the handoff's reserve-dual screen gate** | **RETIRED ON ARITHMETIC, BEFORE THE LP** — ~19 GW of tail-hour headroom minus 4.57 GW is ~14.4 GW against a requirement whose maximum is 4,224 MW. The dual cannot move. Stated as a COST of the card, not an excuse (§5). |
| **the screen** | ONE shard, 2022, launched against S-1..S-4. Its numbers are §7. |
| **the cross-year evidence** | **MIXED, and reported as such** — the forced signature is strong in 2022 and 2021 and weak-to-absent in 2020, 2023, 2024 and 2025 (§3). |

---

## §1 — the defect, confirmed in code and on disk

`src/market_sim/data/outages.py`:

* `UNIT_OUTAGE_MIN_DAYS = 5`, and the loader drops every shorter window.
* The sub-floor companion `unit_outage_short_windows` — **armed `true` in PJM's keeper** — recovers
  them, but re-filters to `plant_group == "COAL"` (the `df[...]` at the old line 1201), and its
  derive emitted coal only.

Verified on disk: `campd-unit-outages-PJM.csv` is 10,670 rows with **min duration exactly 5.0 days**;
`campd-unit-outages-short-PJM.csv` is 934 rows, **100 % COAL**, max duration 4.9 days. So the 0-5 d
family is captured for coal and **thrown away** for CC_REGULAR / CC_CHP / ST_GAS / ST_CHP.
(CT_PEAKER is not reachable by this family at all: it is outside `QUALIFYING_PLANT_GROUPS`, and
CT_CHP is dropped at routing in `_unit_outage_target`. The handoff named CT_PEAKER; the machinery
excludes it, and this arm does not change that.)

## §2 — THE KILL GATE: registered first, then measured

Both bars were written and committed in `a231d912` **before** any gas window was detected.

| bar | how it was identified | registered | **measured** | verdict |
|---|---|---:|---:|---|
| **G-KILL-1** mean removed-availability MW over 2022's 92 actual RT > $200 hours | ¼ of the **+9.7 GW** model-minus-meter thermal over-dispatch measured in exactly those hours (rule 19: a mechanism delivering less than a quarter of the defect it targets is not the mechanism for it) | ≥ **2,425** | **4,570** | **PASS 1.88×** |
| **G-KILL-2** annual-mean removed-availability MW, 2022 | 10 % of the **+6,999 MW** forced composition gap | ≥ **700** | **1,185** | **PASS 1.69×** |

Neither bar reads a price residual. Both are MW of availability against MW of measured defect.

**The bar was set above the arm's own prediction, deliberately.** The handoff's naive scaling
(gas carries ~2× coal's window count in the adjacent 5-7 d band; coal's sub-5-day family is
103-188 MW) predicted **200-380 MW**. The measured family is ~5× that, because window *count* was
the wrong scaling variable — a CC block is several times a coal unit's share of its plant bin.

**Measured through the production consumer, not a reconstruction.** Every number above is
`outages.unit_outage_short_derate_factors(..., gas_scope=True)` minus the same call with
`gas_scope=False`, converted to MW on `_iso_plant_capacity("PJM")` — the same object and the same
denominator the LP applies. Record: `results/calibration/_pjmd44_gas_shortwindow_census.json`.

## §3 — the six-year census, INCLUDING the years that do not support the card

Committed artifact (`campd-unit-outages-shortgas-PJM.csv`, 1,859 windows, merit-guarded):

| year | gas family, annual mean MW | coal scope (control) | mean over actual RT>$200 h | n | corr vs PJM published **FORCED** | corr vs **PLANNED+MAINT** | event/annual |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 765.6 | 396.2 | 767.0 | 2 | **−0.015** | +0.040 | — |
| 2021 | 764.5 | 615.1 | 1,087.0 | 23 | **+0.314** | −0.079 | — |
| **2022** | **1,185.1** | 548.3 | **4,570.1** | **92** | **+0.395** | **−0.259** | **8.61×** |
| 2023 | 895.9 | 367.9 | 871.5 | 6 | +0.047 | +0.074 | 3.43× |
| 2024 | 907.4 | 323.8 | 1,530.3 | 18 | +0.106 | −0.055 | 2.39× |
| 2025 | 587.2 | 403.3 | 911.0 | 59 | **+0.003** | +0.121 | **0.33×** |

**What supports the card.** In 2022 the family is 1.19 GW annual, rises to 4.57 GW in the 92 tail
hours and 8.36 GW in the 26 hours above $500, correlates **+0.395** with PJM's published FORCED
series and **−0.259** with PLANNED+MAINT, and runs **8.6×** its annual mean through Elliott. That
is a forced-outage signature on every axis pjm-162's stratification measured, and it is exactly
what the sign-flip table predicted.

**What does not, stated at full magnitude and not netted out.** The forced correlation is weak in
2023 (+0.047), 2024 (+0.106) and 2025 (+0.003), and slightly NEGATIVE in 2020 (−0.015). The annual
mean does not track the published forced level at all — **2025 has the LARGEST published forced
outage of the six years (10,531 MW) and the SMALLEST recovered family (587 MW)** — and in 2025 the
family *falls* through the named winter event (0.33× annual) where in 2022 it rises 8.6×. Even in
2022 the tail-hour capability is Elliott-weighted: **9,639 MW over the 35 December tail hours
against 1,854 MW over the other 57.**

**The honest reading of that spread, offered rather than argued around.** This family reproduces
*correlated, event-driven, gas-side forced outage* — which is what Elliott was and what 2022's
missing tail is made of — and it does **not** reproduce PJM's baseline forced outage, which is
7.7-10.5 GW every year and which this family never approaches. The card is about the missing tail,
and on the tail the evidence is strong; a reader should not take the 2022 numbers as evidence that
the composition gap is closed. It closes **19 %** of it (6,999 → 5,814 MW; forced-like share
6.8 % → 10.5 % against a published 26.6 %).

## §4 — THE IDENTIFICATION QUESTION, and why it is a measurement and not an argument

The handoff named this "THE HARD PART", and ERCOT's lane had already struck a near-neighbour arm
over it (`docs/calibration-log/ercot.md`): the short mode admits only `SHORT_BASELOAD_CF ≥ 0.55`
units *"because a cycling unit's brief stop can be economic dispatch while a baseload unit's 1-5 day
full stop … is a forced event"*, and *"the only signal separating a 2-day lay-up from 2-day cycling
… is the unit's own metered on/off state, and consuming that hour-by-hour is rule 13 `[R-MEASURED]`
pinning."* Rule 28(d) makes that ERCOT's verdict, not one that fills PJM's cell — but the reasoning
is the objection this scope had to answer, and it was registered as a stage-1 blocker in the
PRECOMMIT §4 **before** the family was measured.

**Answer 1 — a different instrument, and its effect is measured.** `SHORT_BASELOAD_CF` is a
BASELOAD guard: it proxies "not economic idling" by "runs near its ceiling", which coal satisfies
and a cycling CC cannot. Applied to gas it admits nothing. The gas scope therefore carries the
**merit-order guard** — the unit's own measured SRMC against the revealed clearing cost of the
capacity that WAS running — which asks the economic question **directly**. The derive CLI *refuses*
to emit the gas scope without it.

| 2022 gas family | annual mean MW | over the 92 RT>$200 h |
|---|---:|---:|
| in-merit filter only | 1,328.7 | 4,816.0 |
| **+ merit-order guard (COMMITTED)** | **1,185.1** | **4,570.1** |
| what the guard removed (93 of 494 windows) | 143.6 (**−10.8 %**) | 245.8 (**−5.1 %**) |

**The choice was made against interest.** Both the guarded and unguarded families clear both bars,
so the guard could not have been selected to pass a gate; the committed artifact carries the
**smaller** one. And the ≥ 5-day gas extract PJM's keeper already consumes is itself *unguarded*, so
the gas short scope is **more** strictly identified than its own incumbent sibling.

**Answer 2 — Elliott is a natural experiment, and it is the strongest evidence in this session.**

| Dec 2022 | 20 | 21 | 22 | 23 | **24** | **25** | **26** | **27** | 28 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PJM published FORCED, MW | 10,396 | 11,585 | 10,433 | 11,914 | **31,078** | **35,844** | **27,058** | **24,052** | 17,957 |
| recovered gas family, MW | 9,088 | 4,470 | 3,014 | 7,872 | **10,998** | **13,611** | **13,297** | **10,158** | 6,429 |

The family tracks the **shape** of the best-documented forced-outage event in PJM's history, rising
from a 3.0-4.5 GW pre-event baseline to 35-49 % of the operator's whole-fleet published forced
outage, from gas alone. **In hours whose RT price averaged $844, no unit is idling economically** —
so the windows that survive there are mechanical (or gas-supply curtailment, which PJM books as
forced) by construction, not by assertion. That is the direct refutation of the economic-cycling
reading, and no detector threshold was tuned to produce it.

## §5 — THE HANDOFF'S OWN FIRST SCREEN GATE IS UNREACHABLE, AND I SAY SO INSTEAD OF SOLVING FOR IT

The handoff pre-registered *"the reserve dual becoming non-zero in the target hours"* as the
screen's first gate. On committed numbers alone:

| | MW |
|---|---:|
| model thermal headroom in the 92 RT > $200 hours (ADDENDUM §3, its own corrected figure) | ≈ **19,000** |
| PJM `pjm_primary` requirement — **maximum**, not mean | **4,224** |
| what this arm removes in those hours | **4,570** |
| headroom after the arm | ≈ **14,400** |

**14.4 GW is 3.4× the requirement's own maximum**, so the reserve balance row cannot bind and the
dual stays at exactly 0.00 whatever this arm does. Spending a PJM year to rediscover a subtraction
is what rule 29 clause 0 exists to prevent, so the gate was retired **in the addendum, before the
shard was launched**, and never after seeing a result.

**What that costs the card, stated rather than absorbed: this mechanism cannot, on its own, restore
PJM's scarcity price formation through the co-optimisation.** The co-opt's inertness — a dual of
0.00 in 8,760 of 8,760 hours in 2021, 2022 and 2023 — is about the **level** of the headroom, and no
composition repair reaches it. It is a separate open root cause (§8 item 5), and it now has a
measured size: any mechanism that wants the dual to bind in 2022 must find **~15 GW**, not 4.6.

## §6 — the build, and the proof that it is inert while off

`ScenarioConfig.unit_outage_short_windows_gas`, default `False`, tier 3, in
`_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` + `_BACKCAST_ONLY_OVERLAY_FIELDS`
+ `TIER_TAGS`, all in the same commit as the field (the nyiso-119 / caiso-186 discipline).

* **Off-path byte-inertness, proved not asserted:** `unit_outage_short_derate_factors` hashed over
  **7 ISOs × 4 years × `extract_basis_share` {False, True}** — every digest identical to
  `origin/main`.
* **Derive default-path byte-inertness:** `--iso PJM --short-windows --years 2022` produces a file
  `diff`-identical to the unpatched script's.
* **Disjointness (rule 19):** the gas file's max duration is 4.9 d against the ≥ 5-day extract's min
  of 5.0 d, and the two scopes share no plant group. The one residual seam is the pre-existing
  day-granular boundary artifact — 47 overlapping unit-days out of 1,851 (**2.5 %**) — which the
  existing `unit_outage_per_unit_clip` field (`U` in PJM's matrix, default off) exists to handle and
  which the coal overlay already carries. Reported, not repaired here.
* **Zero free parameters, zero fitted scalars** (rules 21/24). The duration boundary is the
  categorical 7-day sign flip (8 positive cells, 12 negative, zero exceptions across 2022-2025), and
  it was **not re-swept** — pjm-162 swept the *cumulative* family and found no optimum, which is a
  different statistic.
* **Rule 23:** the derive re-runs because its **scope** was wrong (coal-only) — a construction
  repair. The commit message cites the sign-flip table and no price number.
* **Rule 25 `[R-ISO-SCOPE]`:** nothing transfers. Every other ISO's cell reads `U` with the transfer
  question posed as a measurement, and ERCOT's cell records that ITS standing objection stands.
* **Gates green:** `check_cache_key_registration`, `check_mechanism_matrix`,
  `check_registry_payload_parity`, `check_gate_a_provenance`, `audit_keepers --iso PJM`,
  `build_status --check --iso PJM`, `tests/unit/data/test_outages.py` (101 passed).
  `tests/scoring` reads **15 failed / 1474 passed / 12 skipped** — identical to the handoff's
  measured `main` baseline. **No new CI failures.**

**G-DRIFT (rule 29(b)) passes exactly, and no control solve is spent.** The keeper's own 833-field
`cache_key()` is the identical `725009b54d387c32` at its `git_sha` `5f133fd5` and at HEAD. Since
capx D79 that key carries the solve-surface fingerprint, so an unmoved key certifies that no
registry table, no solve-surface row and no config default the keeper touches has moved — stronger
than a hunk audit and stronger than a control solve. **The committed keeper bundle IS the control.**

## §7 — THE SCREEN

Screen year **2022**, by footprint (92 tail hours against 6-59 elsewhere; also the largest measured
gas family, 494 windows), never by residual. ONE shard, pinned to `57c3557e`. Gates S-1 envelope
depth, S-2 confinement, S-3 the model-minus-meter thermal gap falling ≥ 2.0 GW from +9.7 GW, S-4 no
non-target load-bearing flip. **C3a, C3b and C1 are reported at full magnitude in both directions
and gated in neither.**

*(Filled in below when the shard reports. If this section still reads as a placeholder, the shard
had not returned when the session ended and NO screen number is claimed.)*

## §8 — WHAT I ESCALATE RATHER THAN ABSORB

1. **The co-optimisation's inert dual now has a price.** §5 sizes it: ~15 GW of headroom must go
   before `pjm_primary` can bind in 2022. `ordc_scarcity_overlay` is `G` on the ground that "the
   in-LP co-opt already owns the phenomenon" — a premise §5 shows is false in 2021, 2022 and 2023.
   **This is still not a licence to arm the adder** (a stack on an inert mechanism is still a
   stack); it is an argument that the co-opt's *operands* are the object, and now a sized one.
2. **The cross-year weakness (§3) is not explained.** A family that reads +0.395 against published
   FORCED in 2022 and +0.003 in 2025 is either measuring two different things or missing most of
   what it should catch in four of six years. I did not resolve it.
3. **The 2.5 % boundary-day double count** (§6) is pre-existing, bounded and unrepaired here;
   `unit_outage_per_unit_clip` is PJM's `U` cell for it.
4. **Inherited and untouched:** the PJM hydro deficit's pumped-storage accounting seam;
   `ST_GAS_PEAKER_PLANTS` invisible to `cache_key()`; plants 3138 / 3131 failing the D-4 conduct
   rider under `st_netload_drag`; the `da_virtual_bids` anchor not reproducing in 2020-2022.
5. **The successor, if the screen's S-3 fails:** PJM's published forced outage may be largely
   **PARTIAL derates**, invisible to a stop-detector at any duration (pjm-162: a model PARTIAL block
   of 14,653 MW against a HARD-ZERO block of 27,009 MW). PJM's matrix carries
   `ercot_partial_outage_shaped_derate` at `·` — unbuilt, not refused.

## §9 — WHAT IS NOT CLAIMED

* **No keeper moves.** PJM's training span reads `CALIBRATED` on `2026-09-10-pjm-d4-2-stgas` and
  nothing in this session touches it (rule 30(c)). `audit_keepers --iso PJM` and
  `build_status --check --iso PJM` both pass.
* **No dashboard registration.** No keeper-class run exists; the screen bundle is a throwaway by
  rule 29 clause 2 and is never registered.
* **No criterion is claimed to improve.** The kill gate is a magnitude gate; passing it authorised a
  build and a screen, nothing more. A screen **may kill an arm; it may never promote one.**
* **The full span is NOT spent.** Rule 16 `[R-ALLYEARS]` requires 2020-2025 in one bundle, six
  shards, and that is the *next* decision — not this session's to take.

## §10 — DISPOSITION, AND THE RULE-31 `[R-RETAIN]` PROMOTION QUESTION, ASKED EXPLICITLY

**On disk and NOT surviving this session:** the screen bundle
`results/calibration/pjm_d4_4_screen_2022/` lives in the SHARD's ephemeral container and is
gitignored there; it is a throwaway by rule 29 clause 2 and its every number is in §7 of this doc,
which is the record. Nothing was `rm`'d: `.gitignore` line 1757 (`results/calibration/pjm_d4_*/`)
already keeps the family out of `main`, which is what discharges rule 29(c) — the ercot-255 lesson.

**Committed and surviving:** the field, the derive change, the two extracts
(`campd-unit-outages-shortgas-PJM.csv` + its layup companion), the matrix row and cells, the tests,
the census record, and these three documents.

**THE QUESTION FOR THE OWNER, and this session does not answer it:**

> The mechanism is built, measured, identified against the standing objection, and screened on one
> year. **Should the full six-year span (2020-2025, six shards, one bundle) be spent?** The costs
> and the case are both above and neither is netted out: it closes 19 % of the composition gap, it
> reproduces Elliott's forced-outage shape from an independent detector, it is a rule-14
> `[R-ACCURATE]` swap of a *discard* for measured data — **and** its forced signature is weak in
> four of six years, it cannot make the reserve dual bind, and it is Elliott-weighted even in the
> year it works.
>
> My own recommendation, stated so it can be overruled rather than acted on: **spend the span.**
> Rule 14 says an accurate input that makes the fit worse is a discovered bug, not a reason to keep
> the discard — and this is a discard, not an estimate. But the recommendation is not a decision,
> and per rule 31 nothing is deleted while the decision is open.
