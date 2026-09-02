# nyiso-177 — the accurate CAMPD attribution is NOT what broke the NYISO backcast: the availability basis is, and the guarded companion reproduces the keeper's envelope to `np.array_equal`

**Session:** nyiso-177, NYISO backcast-calibration track, 2026-09-02.
**Keeper:** `2026-08-30-nyiso-159-loss-surface` — **UNCHANGED**, NOT-YET on
{C3a-2025 −11.5 %, C3c}.
**Gates:** `results/calibration/PREREG-nyiso177-degradation-root-cause.md`,
committed at `966da189` **before any measurement**, amended at `499430f4`
**before any solve** and with no score of any kind consulted.
**Runs registered:** `2026-09-02-nyiso-177-destack-unguarded`,
`2026-09-02-nyiso-177-vintage-matched` (both PROBES, both NOT-YET, neither
promoted).
**Machine artifacts:** `results/calibration/_nyiso177_root_cause_phase0.json`,
`results/calibration/_nyiso177_availability_basis_gates.json`; probes
`scripts/probes/nyiso177_degradation_root_cause.py`,
`scripts/probes/nyiso177_availability_basis_gates.py`.

---

## 1. The one-paragraph answer

nyiso-176 asked why a more accurate input made the backcast worse, and handed
the question forward under rule 14 `[R-ACCURATE]`. **The accurate input did not
make the backcast worse.** `campd_per_unit_attribution` is one gate over two
artifacts (nyiso-176 §6.1), and arming it imported the per-unit *attribution*
repair **together with an unguarded HEAD re-derivation of the availability
envelope**. Separating them attributes **all** of the damage to the second:
adding a *vintage-matched* availability basis — the deriver's own,
already-existing, zero-DOF `--merit-order-guard`, which takes economically-idle
windows out of the mechanical-outage envelope — returns the price level to the
keeper's (32.97 / 37.79 / 58.99 against 33.01 / 37.66 / 58.81), returns
load-bearing **C3b to PASS**, and leaves the accurate attribution in place. The
guarded companion reproduces the keeper's availability envelope at Ravenswood
**`np.array_equal`, hour for hour, in all three years**. What is left of the
degradation after that is **one criterion in one year**: C1 2023 `ST_GAS`
+3.86 TWh against the keeper's +3.33 — marginally outside a band the keeper sits
marginally inside. **Neither leg is promoted; the keeper is untouched.**

---

## 2. Phase 0 — the attribution, discharged from committed bytes with no solve

### 2.1 The damage is an availability collapse, and it is concentrated

`unit_outage_derate_factors` under the two extracts, mean availability, 2023:

| bin | nameplate MW | keeper | nyiso-176 arm |
|---|---|---|---|
| **(2500, ST_GAS) Ravenswood** | **1,724.8** | **0.772** | **0.129** |
| (2517, ST_GAS) Port Jefferson | 385.0 | 0.925 | 0.289 |
| (2490, ST_GAS) Arthur Kill | 876.6 | 0.855 | 0.360 |
| (54593, CC_REGULAR) Batavia | 48.8 | 1.000 | 0.008 |
| (54041, CC_CHP) Lockport | 219.0 | 1.000 | 0.320 |
| (50978, CC_REGULAR) Carr Street | 58.0 | 1.000 | 0.498 |

Ravenswood alone is 1,724.8 MW × 0.643 × 8,760 h ≈ **9.7 TWh of capacity-hours
removed** — against a measured ISO-wide `ST_GAS` fall of −5.28 TWh. The
mechanism is not subtle and it is not the attribution.

### 2.2 The year signature is mostly a denominator, and the rest is Ravenswood

nyiso-176 flagged the +14.71 / +7.32 / +5.36 % price signature as "unexplained
and … probably the bug". It decomposes into two ordinary parts:

* **The percentages differ mainly because the base differs.** The *absolute*
  monthly load-weighted delta is $4.14 / $2.51 / $2.95 per MWh; the keeper's own
  base level is $31.73 / $36.27 / $55.81. Same money, three denominators.
* **The residual heterogeneity is the Ravenswood availability path.** The
  keeper's `(2500, ST_GAS)` availability is **0.772 / 0.465 / 0.297** for
  2023 / 2024 / 2025 — so the keeper's `ST_GAS` surplus is largest in 2023
  (11.47 TWh against an actual 8.14) and so is its removal (−5.28 / −2.39 /
  −1.05 TWh). Within 2023 the delta concentrates in **Jun–Sep** (+$5.81 to
  +$7.11) against **October's +$0.70**.

**The signature is explained. It is not a separate bug.**

### 2.3 Gate G1 — the rule-19 stack: **PASSES**

`outages._FLEET_GROUP_OVERRIDE = {2500: "ST_GAS"}` enumerates, per plant, the
very defect the general per-unit crosswalk repairs — and rule 24
`[R-REGISTRY]` names "hardcoded per-plant dicts in `data/` modules" explicitly.
The 2 × 2, mean availability 2023 / 2024 / 2025:

| leg | (2500, ST_GAS) | (2500, CC_REGULAR) |
|---|---|---|
| L0 keeper (incumbent + override) | 0.772 / 0.465 / 0.297 | **1.000 / 1.000 / 1.000** |
| L1 arm (per-unit + override) | 0.129 / 0.097 / 0.111 | **1.000 / 1.000 / 1.000** |
| **L2 (per-unit, override OFF)** | **0.141 / 0.097 / 0.121** | **0.823 / 0.918 / 0.923** |
| L3 (incumbent, override OFF) | 1.000 / 1.000 / 1.000 | 0.096 / 0.184 / 0.049 |

Both pre-registered legs hold: `ST_GAS` moves by at most **0.012**, and
`CC_REGULAR` — pinned at exactly 1.000 under the override — takes a real derate
once the override is disarmed. **The override is redundant on the repaired path
and, where it is not redundant, it is wrong**: it drags Ravenswood's
correctly-routed CC units onto the steam bin and leaves the CC bin with no
derate at all. **L3 is why it is disarmed on that path ONLY**: on the incumbent
extract the override is load-bearing exactly as its comment says.

### 2.4 Gate G2 — the envelope is **OVER-BOOKED**, and the keeper is too

Nameplate-weighted share of the NYISO `ST_GAS` bin-capacity-year booked as
mechanical outage, against a documented EFOR+planned norm of **0.10–0.15**:

| leg | 2023 | 2024 | 2025 |
|---|---|---|---|
| **keeper** | **0.536** | **0.560** | **0.501** |
| nyiso-176 arm | 0.794 | 0.742 | 0.688 |

**G2 fires — on the arm and on the keeper alike.** The over-booking is
**PRE-EXISTING**, roughly 3.5–5× the top of the norm, and **nothing in this
session repairs it.** It is stated here at full strength because it is the
larger object and it stays open (§6).

---

## 3. Gate G3 — **FAILED**, on both legs, and the failure is reported not repaired

* **G3(a) "strictly between the control's and the arm's".** The guarded extract
  reads `(2500, ST_GAS)` = **0.7715010038884795 / 0.4653023102142477 /
  0.2967897806694284** — the **control's value to 16 significant figures**, with
  the hourly arrays `np.array_equal` in all three years. It lands **ON** the
  endpoint. **FAIL.**
* **G3(b) "booked_share below 0.40".** The guarded extract reads
  **0.534 / 0.560 / 0.501**. **FAIL — and the gate was mis-constructed**: the
  keeper's own value is 0.536 / 0.560 / 0.501, so the threshold measured a
  pre-existing property and no guarded construction could ever have passed it.
  Disclosed in the PREREG §6.1 amendment, committed before any solve.

**The consequence is honoured. The merit-order guard is NOT armed as a repair
of the availability envelope, and this session claims nothing of the kind.**

---

## 4. The brief's own item-(1) instrument is REFUTED

The brief directed a confound-removal companion derived with
`--no-fullstop-override`, "so it matches the incumbent extract's own vintage",
and named it "the cheapest thing that could make this promotable". Derived
(2019–2026, per-unit routing) and measured for zero solves — **it does not
match.** Nameplate-weighted L1 distance of the mean-availability vector from the
keeper's, over every bin and all three years:

| candidate companion | L1 from keeper |
|---|---|
| unguarded per-unit (nyiso-176's arm) | 0.0943 |
| **`--no-fullstop-override`** | **0.1055 — FURTHER than the arm** |
| **`--merit-order-guard`** | **0.0006** |

It moves **41 bins** by more than 0.02 in 2023 alone, in **both** directions: it
deletes genuine long mechanical outages the in-merit filter alone would keep,
while leaving the economically-idle ones that filter admits. **The confound the
brief was reaching for is ECONOMIC LAY-UP, not the full-stop override.** The
`--merit-order-guard` companion is the instrument the brief wanted, and it is
better than the one it named: it matches by a principled, cited, zero-DOF
classifier rather than by vintage.

**G3′** (PREREG §6.3, metric and both thresholds fixed before any solve:
L1 ≤ 0.01 **and** `np.array_equal` on `(2500, ST_GAS)`) **QUALIFIES the guarded
companion and disqualifies the other two.** One honest wrinkle, reported rather
than fitted: G3′ was specified against the code **before repair 1 landed**. On
that configuration the guarded companion reads L1 **0.0006** with array-equality
in all three years. With repair 1 applied — a separately adjudicated,
G1-PASS correctness change that deliberately gives `(2500, CC_REGULAR)` its own
derate — it reads L1 **0.0024**, still inside the bar, and the array-equality
leg no longer holds *because of repair 1*, not because of the guard. Both
numbers are in `_nyiso177_availability_basis_gates.json`; neither threshold was
moved.

---

## 5. The A/B — a 2 × 2, every cell a single delta from a neighbour

Control = **the committed keeper**, which nyiso-176 §8a.1 established reproduces
bit-identically at HEAD. No control leg was solved.

| | incumbent routing | per-unit routing **+ repair 1** |
|---|---|---|
| **keeper-vintage availability** | **KEEPER** — grade 6, fails 2 | **B1′** `-vintage-matched` — grade **4**, fails **3** |
| **HEAD-unguarded availability** | *(not solved — no such artifact)* | **B1** `-destack-unguarded` — grade 3, fails 4 |
| *(nyiso-176's arm: per-unit routing WITHOUT repair 1, unguarded)* | | grade 3, fails 4 |

### 5.1 Load-weighted price, $/MWh

| leg | 2023 | 2024 | 2025 |
|---|---|---|---|
| **actual (RT, load-weighted)** | **32.25** | **38.12** | **66.43** |
| keeper | 33.01 | 37.66 | 58.81 |
| nyiso-176 arm | 37.86 | 40.42 | 61.96 |
| **B1** (destack, unguarded) | 38.01 | 40.49 | 62.00 |
| **B1′** (vintage-matched) | **32.97** | **37.79** | **58.99** |

### 5.2 Class energy, TWh

| class | year | actual | keeper | 176 arm | B1 | **B1′** |
|---|---|---|---|---|---|---|
| ST_GAS | 2023 | 8.141 | 11.471 | 6.191 | 6.341 | **11.999** |
| | 2024 | 9.913 | 9.321 | 6.928 | 6.942 | **9.799** |
| | 2025 | 13.712 | 9.787 | 8.732 | 8.832 | **10.014** |
| CC_REGULAR | 2023 | 33.012 | 32.863 | 36.150 | 35.899 | **32.796** |
| | 2024 | 34.060 | 37.206 | 38.770 | 38.702 | **37.401** |
| CC_CHP | 2023 | 14.802 | 15.074 | 16.292 | 16.338 | **15.043** |
| CT_CHP | 2023 | 2.434 | 1.765 | 1.887 | 1.920 | **1.314** |
| CT_PEAKER | 2023 | 2.114 | 0.392 | 0.923 | 0.938 | **0.350** |

### 5.3 What each leg establishes

* **B1 reproduces nyiso-176's arm at the criterion level exactly** — same
  determination, same grade 3, same four failures, price within $0.15. **Repair
  1 is not LP-inert** (37,557 of 52,560 hourly zonal prices move in 2023, max
  $7.84) but it moves **no criterion**. The rule-19 stack was real; it is not
  the degradation.
* **B1′ recovers everything the availability basis cost except one thing.**
  Load-bearing **C3b returns to PASS**; C2, C4, C8 stay PASS; the price level
  returns to the keeper's. What remains is **C1 2023 `ST_GAS` +3.86 TWh, share
  +3.2 pp** against the keeper's **+3.33 TWh** — a band the keeper sits
  marginally inside and B1′ marginally outside. Every other C1 cell passes or is
  SKIPPED on the preliminary EIA-923 2025 vintage.
* **Gate R6 / G5 is SILENT, and that is the point.** B1′'s C3a-2025 is
  **−11.2 %** against the keeper's −11.5 %. The representation repair's ~zero
  C3a expectation — carried verbatim from nyiso-175b K5 through nyiso-176 R6 —
  **is confirmed by the one leg that could test it cleanly**. Against the keeper
  B1′ moves ~80 % of hourly zonal prices, at a mean |Δ| of only **$0.23 / $0.27
  / $0.27**: a real redistribution at an unchanged level, exactly what a
  representation repair should look like.

### 5.4 The mechanism of the one regression, stated

The repaired attribution measures a **higher committed share on NYISO's largest
non-Ravenswood steam plants**, because the incumbent artifact diluted each
plant's conduct across a facility-summed denominator that included its non-steam
units:

| plant | MW | committed % incumbent → per-unit+guard | `online_hours` |
|---|---|---|---|
| 2516 Northport | 1,592.2 | 10.7 → **15.3** | 25,264 → 25,232 |
| 2625 Bowline Point | 1,159.6 | 16.5 → **20.1** | 6,993 → 6,835 |
| 8906 Astoria | 923.2 | 17.8 → 17.8 | 11,405 → **17,027** |
| 2480 Danskammer | 497.3 | 9.9 → **17.8** | 346 → 557 |
| **2500 Ravenswood** | 1,724.8 | 10.7 → **6.5** | 24,685 → **7,293** |
| 2682 S A Carlson | 45.0 | ST_GAS row → **CT_PEAKER** | — |
| 2493 East River | 309.5 | ST_CHP row → **CT_CHP** | 26,253 → 0 |

The rises on ~4.9 GW outweigh the fall on Ravenswood's 1.7 GW, and `ST_GAS`
gains +0.53 TWh in 2023. **This is a measured change, not a fitted one**, and
under rule 14 it stays.

---

## 6. Disposition, and what is NOT claimed

**NEITHER LEG IS PROMOTED. THE KEEPER IS UNTOUCHED.** Against the brief's
promotion bar:

* **(a) a single adjudicated object — FAILS.** B1′ is three: the attribution
  repair, repair 1, and the guarded availability basis.
* **(b) every regressed criterion has a stated mechanism — passes** (§5.4).
* **(c) not an unexplained side effect — passes.**

And independently: **B1′ is strictly worse than the keeper** (grade 4 vs 6,
fails 3 vs 2). It adds a load-bearing failure and improves no scored criterion.
Rule 1 `[R-STRUCT]` permits promoting a more structurally faithful run over gate
regressions — but the guard's availability basis is **not** demonstrably more
accurate than the keeper's; **G3 says so explicitly**. It was selected because
it *matches*, which is a vintage criterion, not an accuracy one. The only
unambiguous structural gains B1′ carries over the keeper are the per-unit
attribution (rule 14) and repair 1 (rule 19). **That is a candidate to put to
the owner, not a promotion to take.**

**Three things this session does not claim.** It does not claim the guard
repairs the availability over-booking (G2 fires on the keeper too, and G3
records the failure). It does not claim any C3a improvement (R6/G5 silent, by
design). It does not claim the ST_GAS-2023 regression is an artifact — it is
real, measured, and it stays.

---

## 7. Handed forward

1. **THE OVER-BOOKING IS THE REAL OBJECT, and it is now sized.** The NYISO
   `ST_GAS` overlay books **0.50–0.56** of the bin-capacity-year as mechanical
   outage **in the keeper**, against an EFOR+planned norm of 0.10–0.15 — and the
   model still runs the remaining capacity at ~3× the fleet's measured annual CF
   (keeper 2023: 11.47 TWh on 8,902 MW at 46 % mean availability = 0.32 CF
   when-available, against the real fleet's 0.10 all-in). **The overlay is
   carrying economic idling the offer curves should be producing.** That is the
   NYISO steam lane's next object, and it is an offer-side question, not an
   availability-side one.
2. **THE MISSING RUNG, and it is one solve.** A leg arming the guard **alone**
   (incumbent routing, `--merit-order-guard` with no `--per-unit-crosswalk`)
   would make the guard a true single adjudicated object against the keeper and
   would satisfy promotion-bar leg (a) for the pair. The companion does not
   exist yet; deriving it is data prep and unrestricted.
3. **C1 2023 `ST_GAS` is now a NAMED, SIZED, SINGLE object** — +3.86 TWh on the
   repaired attribution against +3.33 on the incumbent, both against an actual
   8.141. The keeper passes this criterion by ~0.5 TWh of margin that the
   attribution defect was supplying. Anyone quoting the keeper's C1 PASS should
   know that.
4. **The four `U` cells transfer without a solve.** `campd_outage_merit_order_guard`
   enters CAISO / PJM / MISO / NEISO as `U`, and each cell states a question
   answerable from committed bytes: measure that ISO's own `booked_share` by
   class against the 10–15 % norm, and its already-derived layup census. The
   defect family is known to be present elsewhere (neiso-99 carved a per-plant
   rule 14 exception out of the same short-circuit family).
5. **`mustrun_layup_window_mask` (NYISO `U`) now has a matched companion.** The
   guarded derivation wrote `campd-unit-outages-layup-perunitmerit-NYISO.csv`;
   `unit_layup_csv_for_iso` resolves only the unsuffixed name, so a lane arming
   that mask on the per-unit path needs the resolver extended.
6. **nyiso-176's other carry-forwards stand**: the tranche half's provenance
   sidecar for the incumbent artifacts, `--fix-anchors` on the shared matrix
   (not run here — it rewrites every row of a file five other lanes edit), and
   nyiso-175/175b's own list.

---

## 8. Honest expected value

**What is delivered.** The chartered question is answered with a bit-exact
identification: the accurate attribution is exonerated, the availability basis
is convicted, and the separation is demonstrated by an instrument that
reproduces the keeper's envelope `np.array_equal`. Two zero-DOF repairs are
built, tested and registered. The brief's own proposed instrument is refuted
with a stated metric for zero solves. A pre-registered gate is recorded FAILED
with its own construction defect disclosed. The year signature nyiso-176 called
unexplained is explained and closed. The larger object — the over-booking — is
sized for the first time, **including in the keeper**.

**What is NOT delivered.** No keeper. No C3a movement, and none was expected.
The over-booking is measured, not repaired. B1′ is a candidate for an owner
ruling, and this session does not pretend otherwise: it is strictly worse on the
rubric, and the case for it rests entirely on rule 14 `[R-ACCURATE]` plus rule 1
`[R-STRUCT]`, which is exactly the class of judgement the NYISO lane has
reserved to the owner in nyiso-155, -157 and -159.

---

## 9. Governance

* **Rule 1 `[R-STRUCT]`** — both repairs are justified on mechanism. No residual
  was consulted in choosing to derive, to repair, or to solve; no parameter was
  fitted to a gap.
* **Rule 13 `[R-MEASURED]`** — the guard's inputs are measured heat rates and
  delivered fuel prices; the attribution's are EIA-860 prime movers and CAMPD
  unit types. All regenerate for a forward year. No measured *outcome* enters.
* **Rule 14 `[R-ACCURATE]`** — the accurate input is **KEPT**, including where a
  statistic gets worse (§5.4, §6). Nothing was reverted.
* **Rule 19 `[R-ONE-MECH]`** — repair 1 REPLACES a per-plant enumeration with
  the general rule rather than stacking; the guard is ONE field over BOTH
  artifacts through `campd_attribution_selectors`, which returns the pair so a
  call site cannot take one without the other.
* **Rule 21 `[R-DOF]`** — zero free parameters. `MERIT_OOM_FRAC`,
  `MERIT_RCC_PCTL`, `FULL_STOP_OVERRIDE_*`, `UNIT_OUTAGE_MIN_DAYS`,
  `HIGH_LOAD_PCTL`, `MIN_INMERIT_HOURS` are untouched at their committed values
  (stop condition S1).
* **Rule 22 `[R-HOLDOUT]`** — every solved, scored and registered year is
  2023–2025. Deriving multi-year *inputs* is data prep, which the rule does not
  gate. NYISO's `complete` marker was **not** requested and NYISO remains absent
  from both markers.
* **Rule 23 `[R-FROZEN-DERIVE]`** — each re-derivation commit cites its defect
  (the rule-19 stack; the lay-up/outage conflation the guard was built for),
  never a residual.
* **Rule 24 `[R-REGISTRY]`** — `campd_outage_merit_order_guard` is a
  `ScenarioConfig` field, in `_CACHE_KEY_OPTIONAL_FIELDS` and the default-string
  registry in the same commit, reaching `run_config.json`. Repair 1 additionally
  *removes* an off-registry channel on the repaired path.
* **Rule 25 `[R-ISO-SCOPE]`** — only NYISO artifacts were derived; every other
  ISO's tranche and outage CSVs are byte-untouched; no verdict crossed an ISO
  boundary.
* **Rule 27 `[R-PUSH]`** — every pushed file ≥ 300 lines was blob-verified (line
  count + object hash against local) immediately after the push: 24 files, all
  OK.
* **Rule 28 `[R-MECH-MATRIX]`** — the new field's base row plus a cell line in
  **every** ISO shard, same PR (duty c); the tested cells updated in the same
  session (duty b).
* **Rules 15 / 16** — both completed solves registered on the dashboard, all
  three years in one bundle each, committed and pushed in this session.
* **Tests** — `tests/unit` + `tests/iso/nyiso`: 4,387 passed, 31 skipped, 195
  subtests passed. The 4 failures in `tests/unit/results/test_export.py`
  reproduce identically on a clean stash of HEAD (a missing
  `confirmed-retirements` clean partition) and are pre-existing.
