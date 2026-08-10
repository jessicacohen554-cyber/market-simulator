# FINDING — miso-149: BOTH queue-head objects are REFUTED as independent objects. The all-months CC residual is **95 % the model's own price level** (item 9), the availability double-count MISO was assumed to carry **does not exist**, and what the census actually sized is a **7.9 GW PLANT-GRAIN RATING gap** that fleet-aggregate auditing cannot see

**Session:** miso-149, 2026-08-10, branch `claude/miso-149-calibration-whwlu0`.
**PREREG** `results/calibration/PREREG-miso149-overlay-contradiction-2026-08-10.md`
pushed at **`318c0542`** (424 lines, blob `sha256 e29817a4…`, verified against the
**FETCHED** remote ref) **BEFORE any adjudicating statistic**. Instruments committed
at **`d1740f7f`**, before any value existed.

**Posture held, as pre-registered: NO LP. NO SOLVE. NO ARM. NO `ScenarioConfig`
FIELD. NO RUN REGISTERED. NO YEAR OUTSIDE 2023–2025 TOUCHED.** Keeper
**UNCHANGED** at `2026-08-09-miso-148-basis-aware`; fail set **UNCHANGED** at
`{C3a, C3b}`; determination **UNCHANGED** at `NOT-YET`. The PREREG's §7 arm
condition required a single named layer owning ≥ 60 % of the census; it does not
exist, so no arm was authorised. **P9 (0.75) confirmed.**

**Concurrent-session check at open and close:** zero open MISO PRs (only
`claude/ercot-185-fault3-partial-layer-9nhbcx`), zero other remote MISO branches.

---

## 1. Headline — four results, in the order they matter

1. **Object A does not exist as a commitment/displacement object. It is the price
   level.** The pre-registered, against-interest G-3 test returns
   **`DISSOLVES-INTO-ITEM-9`**: of miso-147's `E − M` (S1-2025 **2,273 MW** of
   model CC available and in-merit *at the real price* and undispatched),
   **95.4 %** is capability that is simply **out of merit at the model's own
   price**. Congestion is **−200 MW** (it *helps* CC) and reserve-holding plus
   everything else is **304 MW / 13.4 %**, with the reserve dual at **0.000**.
   Same answer in every year: leg-1 share **0.891 / 0.948 / 0.954**. **P6 (0.55)
   confirmed against my own lane's interest.**
2. **The availability double-count MISO was assumed to carry is not there.** The
   caiso-187 frozen formula `residual_c = max(0, W_c − X_c)`, run on **MISO's own
   fleet** (rule 25 — CAISO's verdict transferred nothing), returns **`0` for
   every material MISO class**: CC_REGULAR `W 0.179` vs `X 0.240`, ST_GAS
   `0.235 / 0.298`, COAL `0.165 / 0.274`, ST_CHP `0.289 / 0.370`. Only CC_CHP has
   a positive residual, `0.0136` — about **49 MW** on a 3.6 GW class.
   **`wefor_residual` is IMMATERIAL for MISO. P5 (0.55) confirmed.**
3. **The census fired B-1 — and its own pre-registered traps show 92 % of the
   quantity is not an availability object at all.** `Kcc` = **3,674 MW** (CC
   family, 2025; 6,523 MW at all-fossil plant grain), material and flat across
   all twelve months. But **54 of 55 CC plants are contradicted**, and the
   per-plant detail names why: the top contributors are **industrial cogens**
   (Plaquemine, ExxonMobil Beaumont, Louisiana 1, R S Cogen, Taft, Midland
   Cogeneration — the BTM boundary miso-148 §3 already adjudicated as **NOT**
   missing capacity) and **plant-code / family splits inside matched plants**
   (Riverside 55641 vs its co-located 64020; Ninemile Point and Perryville, both
   of which carry **more** total model capacity than their own CAMPD total p99).
   On the clean scope the number is **515.4 MW (2025)**, 412.0 / 461.0 in
   2023 / 2024 — **7.9 % of the pre-registered figure**.
4. **What the measurement found instead is bigger than what it was looking for:
   a plant-grain rating gap of 7,915 MW (2025)** — 86 plants whose model total
   fossil capacity sits **below their own demonstrated CAMPD p99**. 4,090 MW of
   it is the adjudicated CHP boundary; **3,825 MW is at non-CHP plants**. It is
   invisible to miso-148's L2 audit **because that audit nets** (merchant CC
   `pmax` vs CAMPD p99 read −0.21 / −1.96 / −6.0 % at fleet aggregate): plants
   over-rated cancel plants under-rated, and the per-plant misallocation
   survives the cancellation.

**Both of the charter's named objects are therefore closed as objects, and the
lane's next question is not the one the queue was pointing at.** §8 states it.

---

## 2. Footing — G-F PASSES, and stronger than the gate asked

The three miso-147 artifacts were re-run at HEAD and diffed field-by-field
against their committed copies: **`_miso147_footing.json` 0 diffs (422 fields),
`_miso147_headroom.json` 0 diffs (903), `_miso147_january.json` 0 diffs (355) —
1,680 fields, ZERO diffs.** Stronger than the pre-registered bar: the regenerated
files are **byte-identical** to the committed blobs (`git status` reports them
unmodified), so the reproduction is exact rather than merely within tolerance.

The footing probes target `results/calibration/miso132_ccmin_B`, the keeper they
were written against (hard-coded in `scripts/probes/_miso143_stack.py`). Every
**new** measurement below targets the **CURRENT** keeper `miso148_basis_B`, by
re-pointing that module's global once, after the footing run — declared in PREREG
§2 and done exactly there.

**Disclosed (PREREG §8):** the footing re-run was launched *before* the PREREG was
pushed. It re-executes committed probes and produced no new statistic; every §3–§6
measurement was designed and run after the push.

---

## 3. G-1 — the census as pre-registered, reported at full magnitude

Plant-hour grain, model NET capability vs CAMPD NET output, plants present on both
sides only:

| CC family | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `Kcc` mean MW | 3,468.8 | 3,560.2 | **3,674.2** |
| S1 mean MW | 3,757.3 | 3,858.9 | 4,235.9 |
| plants both / contradicted | 56 / 55 | 56 / 55 | 55 / **54** |

2025 monthly: `[3708.8, 3854.8, 3593.2, 4061.9, 4101.7, 3562.6, 3196.1, 3118.7,
3404.8, 3511.0, 3950.6, 4052.4]` — nine of twelve months ≥ 3,500 MW, so the
pre-registered non-summer materiality test (≥ 4 non-Jun–Sep months ≥ 300 MW)
passes overwhelmingly. **Branch as written: `B-1 overlay_over_removal`.**

**Traps, all pre-committed, all measured:**

* **TRAP 1 (basis).** Gross basis 3,717.8 vs net 3,674.2 — a 43.6 MW difference,
  because MISO's parasitic map covers 463 plants (mean 0.951, p50 0.970) but not
  every plant, and unmapped plants fall back to 1.0. **The verdict uses NET only**
  and B-1 holds on it. The unmapped-plant fallback is a real instrument limit and
  is quantified in §6.
* **TRAP 3 (CHP boundary).** CC_REGULAR alone: **1,681.7 / 1,835.8 / 1,837.5 MW**
  — exactly half. B-1's ≥ 500 MW bar holds on CC_REGULAR alone, as the PREREG
  required, but the halving is the first signal that the CHP boundary carries a
  large share.
* **TRAP 4 (alignment).** ±1 h shift moves `Kcc` by **1.1 MW** (3,675.3 / 3,674.2
  / 3,675.0). No timezone or ramp-edge artifact.
* **TRAP 2 (crosswalk).** Model-only plants 14/14/15, CAMPD-only 4/4/4 (1391,
  1404, 50625, 55120 — the same four miso-148 §3 named). All excluded from the
  census both ways and counted, never silently dropped.

**66 % of `Kcc` (2023) survives with the ENTIRE overlay stack removed**, which is
already fatal to the branch's own label — see §4.

---

## 4. G-2 — attribution: NO SINGLE LAYER OWNS IT, on either reading

MISO's historic-backcast availability is built multiplicatively as
`stat × ufac(≥5-day) × sfac(short) × mgfac(maxgen)`. The three overlay dicts were
read back through the **shipped** loaders with the keeper's own arguments and the
statistical layer recovered by division. **T-EXACT: the reconstruction reproduces
the fleet's own `availability` array to `5.6e-17`** in all three years.

Share of the census removed by dropping each layer:

| dropped | as pre-registered (CC family, 2025) | clean scope (2025) |
|---|---:|---:|
| `ufac` (≥ 5-day windows) | 18.1 % | **43.7 %** |
| `sfac` (short windows) | **0.0 %** | 0.8 %† |
| `mgfac` (maxgen events) | 0.2 % | 0.8 % |
| **all three** | **18.3 %** | **45.7 %** |
| ⇒ statistical layer | 81.7 % | **54.3 %** |

† `sfac` is **coal-only by construction** — verified, not assumed: all **987** rows
of `campd-unit-outages-short-MISO.csv` carry `plant_group = COAL`. Its zero
contribution to CC is a property of the detector, not a measurement about MISO.

**No layer reaches the pre-registered 60 % ownership bar on either reading.** Per
PREREG §3 G-2 that is the "**the cause is distributed and no single layer owns
it**" outcome — reported, **not engineered around** (rule 19 `[R-ONE-MECH]`: I
will not stack a new relief on an unattributed residual). This is the condition
that **denies the arm** under §7(3).

### 4.1 `W_c` vs `X_c` on MISO's own fleet — and a bound stated in my disfavour

| class | fleet MW | `W_c` | `X_c` | `X/W` | `residual_c` |
|---|---:|---:|---:|---:|---:|
| CC_REGULAR | 28,315.1 | 0.1793 | **0.2402** | 1.34 | **0** |
| CC_CHP | 3,620.6 | 0.0805 | 0.0669 | 0.83 | **0.0136** |
| ST_GAS | 11,610.4 | 0.2353 | 0.2980 | 1.27 | **0** |
| ST_CHP | 698.3 | 0.2886 | 0.3703 | 1.28 | **0** |
| COAL | 44,377.5 | 0.1648 | 0.2736 | 1.66 | **0** |

**Declared against my own result: my `W_c` is NOT the pure WEFOR.** caiso-187
defines it as the unfitted `THERMAL_AVAILABILITY` base plus age escalation; mine is
`1 − mean(statistical-layer availability)`, which also folds in the basis-aware flat
summer derate and the COD/retirement vintage mask (`arrays.py` multiplies
`availability *= ramp`). That makes `W_c` **larger** than the formula's, hence
`residual_c` **larger** — so these zeros are an **upper bound that still lands at
zero**, and the conclusion is conservative rather than flattered.

**`wefor_residual` MISO cell: `U → I`.** The mechanism as specified has nothing to
give on this fleet. The one non-zero (CC_CHP 0.0136 ≈ 49 MW) is immaterial and
sits on the class whose measurement is least trustworthy anyway (§6).

### 4.2 What this does NOT adjudicate, stated so it is not later misread

MISO's measured `X_cc = 0.240` — the overlay removes **24.0 % of CC capacity-hours**
— sits squarely in the 23–46 % band the matrix already records as a **standing
cross-ISO defect** ("the detector books economic layup as mechanical outage in ALL
SIX extracts … MISO/PJM/NYISO **RE-TUNE REQUIRED**"), and MISO has not been
re-tuned. **This session independently corroborates the magnitude at MISO and
adjudicates nothing about it.** A contradiction census structurally cannot: as
caiso-181 put it, zero interior contradiction establishes that the units *were*
down, never *why*. The `campd_outage_windows` MISO cell is therefore **untouched**.

---

## 5. G-3 — the pre-registered against-interest test, and it retires my own priority-1 object

`E − M` split into a telescoping sum that closes exactly, on the keeper's own
committed sidecars. **S1, CC:**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `U = E_actual − M` | 2,966.6 | 1,624.2 | **2,273.0** |
| leg 1 price-level | 2,644.1 | 1,540.4 | 2,169.5 |
| leg 1 markup | 0.0 | 0.0 | 0.0 |
| leg 2 congestion | −34.5 | −225.9 | −200.5 |
| legs 3+4 residual incl. reserve | 357.0 | 309.7 | 304.0 |
| **leg-1 share (LOWER bound)** | **0.891** | **0.948** | **0.954** |

**Bound direction, declared:** `markup_ceiling` is a *lower* bound on the P1
markup, so `E_bid` is an upper bound and leg 1 is a **lower** bound — a
"dissolves" verdict is conservative. In the event the markup leg measures exactly
**0.0**, so the whole of leg 1 is price level, not offer markup.

**Reserve is not the blocker.** 5,336.9 MW held in S1-2025 at a max family dual of
**0.000** — held costlessly, exactly as miso-147 §5 measured in the January tail.
Congestion is **negative** for CC in all three years: the zonal test admits *more*
CC than the system test, so congestion is helping, not blocking.

**Corroboration across families:** ST_COAL leg-1 share 0.981 / 0.976 / 0.796.
ST_GAS reads **>1** (1.322 / 1.450 / 1.556) because its residual leg is
*negative* — the model dispatches ST_GAS **above** what its own price makes
in-merit. That is the floored/must-run energy C8 already tracks at 34.1 / 35.8 /
48.4 %, seen from an independent instrument, and it is **not** a new object.

**And the May stratum answers the "both signs" question.** May `U` is **negative**
in every year (−3,944 / −2,913 / **−5,327**) — the model dispatches *more* CC than
is in-merit at the actual price, because in May the model's price sits *above*
actual — with leg-1 share **1.051 / 0.994 / 0.973**. So in both directions, in
every month, **the model's CC quantity tracks the model's own price level.**
miso-147's "one object, both signs" is vindicated as a description — and the
object is the **price level**, not availability and not commitment.

---

## 6. G-4 — the May split, with a defect in my own pre-registered arithmetic

**Reported first, against interest: the gate as I wrote it is malformed.** It
attributes shares of the family-grain, net `AV_CC − A_CC` deficit (1,201 MW) using
a **plant-grain, one-sided** census, and returned `share_b_overlay = 3.415` — a
part 3.4× its own whole. A component share above 1 is a construction error, not a
result; the branch label `M-2 overlay_may` it produced is **withdrawn as
unsupported by its own arithmetic**, and the pre-registered number is left on the
record rather than deleted.

What is measurable, on the clean scope and like-for-like:

* **(a) the 2025 EIA-860 vintage under-carry** — the 5 plants / 9 rows / 594.7 MW
  `OP` in `vintage_2024` and dropped in 2025 generated **447 MW mean in May-2025**
  CEMS, i.e. **37.2 %** of the 1,201 MW deficit. Just under the 40 % M-1 bar, and
  the largest single **named** contributor. Cottonwood alone is 525.8 MW of the
  2025 rating gap (§7).
* **(b) the clean-scope contradiction in May** — 570.9 / 728.0 / **609.4 MW**
  (2023/24/25). It is **not** May-specific: May is the 3rd, 2nd and 2nd largest
  month respectively, on a series that never drops below 230 MW.
* **(c) G-3** shows May's CC quantity is **97.3 %** price-level-driven, with the
  sign flipped.

**Corrected branch: `M-3 open`** — no single source reaches 40 %, and the honest
reading is that May is not a separate cause at all but the same price-level object
with the sign reversed. **The 2023 control holds the reading:** May-2023 has
`AV−A = +1,074` and is not over-priced, yet its clean-scope contradiction (570.9
MW) is *comparable* to 2025's — so the contradiction cannot be what makes May-2025
over-price.

---

## 7. The object this session actually sized — plant-grain rating

86 plants carry model total fossil capacity **below their own CAMPD total p99**:

| 2025 | MW |
|---|---:|
| total gap | **7,915.0** |
| at CHP-bearing plants (adjudicated BTM boundary) | 4,090.4 |
| at non-CHP plants | **3,824.6** |
| after a parasitic-fallback sensitivity (0.97 for unmapped plants) | 6,610.0 (**−16.5 %**) |

2023 / 2024 totals: 9,280.7 / 7,923.5 — **standing, not 2025-specific.**

Top of the non-CHP head, named so the successor can adjudicate rather than
re-measure:

| plant | gap MW | model | p99 | reading |
|---|---:|---:|---:|---|
| 55641 Riverside Energy Center | 774.6 | 534.8 | 1,309.4 | **plant-code split** — co-located 64020 is carried separately by the model and is in the CC `model_only` list; eGRID's own PLHTIAN warning names the 454 m pair |
| 55358 Cottonwood Energy | 525.8 | 580.4 | 1,106.2 | **the known cross-ISO 2025-vintage defect** — reported, not repaired (rule 25) |
| 55714 Magnet Cove | 184.5 | 641.5 | 826.0 | un-adjudicated |
| 2103 Labadie / 1733 Monroe / 6090 Sherburne | 196 / 151 / 101 | ratio 0.92–0.95 | | consistent with the gross/net basis, i.e. probably the sensitivity above, not a defect |

**The two largest are an instrument artifact and a defect already owned by another
lane.** What remains un-adjudicated is a tail of ~0.92–0.95-ratio plants that the
parasitic sensitivity may absorb entirely. **No claim is made that this gap is
missing capacity**, and none of it is offered as progress against the level miss.

---

## 8. What the queue should do next — stated as evidence, not as a recommendation to act on my own object

* **Item 11 L3 (Object A) is CLOSED.** It is not a commitment/displacement object;
  95 % of it is item 9. Any successor that re-opens it as commitment is re-opening
  a measured negative.
* **The May object (Object B) is CLOSED as a separate object.** It is the same
  price-level object with the sign reversed; its largest *named* separable
  contributor is the cross-ISO 2025-vintage under-carry at 37 %.
* **Items 8 and 9 STAND UNMODIFIED, and this session strengthens item 9
  substantially** — three independent instruments (G-3 across three years and
  three families, the May sign flip, and miso-147's own "marginal on gas in 76 %
  of S1-2025 hours yet clearing $40.7 below actual") now point at the same object.
  **I add nothing to item 9's specification**; deciding what to do about it is the
  owner's, per the standing item-9 owner decision.
* **New, filed not opened:** plant-grain fossil rating (§7), which needs the
  parasitic-fallback and plant-split questions settled *before* any capacity claim;
  and MISO's un-re-tuned outage extract (§4.2), which is a cross-ISO item with a
  named instrument (`outage_detect.filter_merit_order_layup`) and is **not**
  adjudicable by a contradiction census.

---

## 9. Prior, scored — including where I was wrong

| # | statement | P | outcome |
|---|---|---:|---|
| P1 | G-1 returns B-1 | 0.60 | **fired as written; refuted as an object by its own traps** |
| P2 | `Kcc` ∈ [300, 2500] MW | 0.70 | **WRONG** — 3,674 MW as registered (515 clean) |
| P3 | a single layer owns ≥ 60 % | 0.45 | **WRONG** — none does, on either reading |
| P4 | if P3 fires, it is `mgfac`/`sfac` | 0.55 | vacuous (P3 failed); `ufac` was the largest at 43.7 % |
| P5 | MISO `X_cc > W_cc` ⇒ relief immaterial | 0.55 | **CORRECT** |
| P6 | G-3 leg 1 ≥ 60 % ⇒ Object A dissolves | 0.55 | **CORRECT** (0.954) |
| P7 | G-4 returns M-1 | 0.40 | **WRONG** — 0.372, just under the bar |
| P8 | G-4 returns M-3 | 0.35 | **CORRECT** on the corrected arithmetic |
| P9 | no LP, no arm | 0.75 | **CORRECT** |

Four of nine wrong, two of them (P2, P3) badly. The two I staked against my own
lane (P5, P6) both came in — which is the only reason this session has a result
rather than a mechanism.

---

## 10. Kill gates — UNTOUCHED, with the reason

No LP was solved and no mechanism armed, so every kill gate is **untouched, not
passing**: C3b-2025 ≤ 0.212 and must-not-rise — untouched; C3b 2023/2024 PASS
(0.082 / 0.125) — untouched; C3a 2023/2024 PASS (−1.98 / −8.03 %) — untouched;
**May 2025 (+12.4 % over) — no mechanism was armed, so there is no May *effect* to
report; its May *measurements* are §6**; C1/C2 gated years — untouched (2025 stayed
descriptive vs EIA-930 throughout, per the preliminary-EIA-923 blocker); C8 forced
shares and D-4 windows — untouched; C3c ledger **1/1 SPENT** — untouched, and the
tail motivated nothing. **Fail set remains `{C3a, C3b}`.**

**The against-interest bound is carried and was never breached:** 2023 carries
nearly the same CC gap and C3a-2023 PASSES. Nothing here is offered as progress
against 2025's −15.6 %, and no repair was predicted or sized against it.

---

## 11. Duties discharged

* **Rule 15 (dashboard):** no calibration run was produced — no solve, no bundle,
  nothing registrable. Stated explicitly so the absent registration is not read as
  a lapse (the miso-147 / caiso-187 precedent).
* **Rule 16 / 22 (holdout):** MISO holds **no** marker, verified this session from
  `calibration-complete.json` (`complete` = NEISO/NYISO/PJM; `final` = none). Only
  2023–2025 were touched, and only by no-LP measurement.
* **Rule 28(b) (matrix):** `wefor_residual` MISO **`U → I`** with the measured
  evidence and the CC_CHP caveat; §5.4 queue stamped. No other cell moved — in
  particular `campd_outage_windows` MISO stays `K` (§4.2).
* **Rule 28(c):** no new `ScenarioConfig` field, so no new matrix row and no
  `_CACHE_KEY_OPTIONAL_FIELDS` registration is due.
* **Rules 13 / 14 / 19 / 21 / 23 / 25:** CEMS was used **only** as a lower bound on
  an availability input, never as a dispatch target and never as a pin; no
  parameter was derived, no derive script re-run, no data byte written; no
  cross-ISO value adopted (ERCOT's 0.02 and PJM's 0.015 were neither used nor
  sanity-checked against); no mechanism stacked on an unattributed residual.
* **Known-red at HEAD:** this session wrote only new probe files under
  `scripts/probes/` and documents — no existing source file was modified, so no
  new test failure can be attributable to it.
* **Artifacts:** `_miso149_overlay.json`, `_miso149_clean_scope.json`,
  `_miso149_displacement.json`; probes
  `scripts/probes/_miso149_{overlay,clean_scope,displacement}.py`.
