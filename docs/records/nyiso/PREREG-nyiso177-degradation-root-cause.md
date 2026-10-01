# PREREG — nyiso-177: why the accurate CAMPD attribution makes the NYISO backcast worse

**Committed BEFORE any repair is written, before either A/B leg is derived, and
before any guarded artifact is produced.** Eleventh consecutive NYISO session to
pre-register. Keeper `2026-08-30-nyiso-159-loss-surface`, determination
**NOT-YET** on {C3a-2025 −11.5 %, C3c}. **No C3c lever is opened.** Every solve,
score and registration is **2023 / 2024 / 2025** (rule 22 `[R-HOLDOUT]`; NYISO
holds neither `complete` nor `final` and neither is requested).

## 0. The object

nyiso-176 §8a armed `ScenarioConfig.campd_per_unit_attribution` — the accurate
per-unit CAMPD attribution — and the backcast got **worse**: C1 PASS→FAIL,
C3b PASS→FAIL, C3a moved from a 2025-only −11.5 % miss to a 2023-only +17.4 %
blow-out, target grade 5→3. Class energy moved **ST_GAS −5.28 / −2.39 / −1.05
TWh** into CC.

Rule 14 `[R-ACCURATE]` binds and was stated in advance by the predecessor: the
accurate input is **KEPT**, and the degradation is a **DISCOVERED BUG
ELSEWHERE**. This session's object is that bug. **Nothing here reverts the
per-unit repair, and nothing here tunes a parameter against the residual**
(rule 1 `[R-STRUCT]`).

## 1. Phase-0 attribution — a REPORTING DUTY, not a gate

Discharged from committed bytes with no solve, and reported whatever it shows:
the per-bin availability delta (`unit_outage_derate_factors`, both extracts,
all three years), the per-plant outage-window delta, the metered CEMS conduct of
the plants that move most, and the decomposition of the *year signature* into a
price-level denominator effect versus a genuine per-year availability path.
No threshold; no branch depends on it.

## 2. Gates

### G1 — the rule-19 stack at Ravenswood

**HYPOTHESIS.** `outages._FLEET_GROUP_OVERRIDE = {2500: "ST_GAS"}`
(`src/market_sim/data/outages.py:280`) is a **hardcoded per-plant instance of
the very defect the general per-unit crosswalk repairs**, and under the arm it
**STACKS** on the general repair (rule 19 `[R-ONE-MECH]`) — it is also a
hardcoded per-plant dict in a `data/` module, which rule 24 `[R-REGISTRY]`
names explicitly.

**TEST.** Mean availability of `(2500, ST_GAS)` and `(2500, CC_REGULAR)`,
2023–2025, over the 2×2 {incumbent, per-unit routing} × {override on, off}.

* **G1 PASSES** iff, under **per-unit** routing, removing the override leaves
  `(2500, ST_GAS)` materially unchanged (**|Δ availability| ≤ 0.05** in every
  year) **AND** gives `(2500, CC_REGULAR)` a non-trivial derate
  (**availability ≤ 0.95** in at least one year) where the override leaves it at
  exactly 1.000. That is the signature of a compensator that is **redundant** on
  the repaired path and is **stealing the CC bin's own windows**.
* **G1 FAILS** otherwise, and the override is left untouched.

**Stated in advance:** G1 is a **CORRECTNESS** gate, discharged from artifact
bytes with **no solve**. If it passes, the repair lands **whatever it does to
the residual**. The override is scoped **OFF only where `per_unit_crosswalk` is
armed** — never unconditionally, because on the incumbent path it is
load-bearing and removing it there would be a regression, not a repair.

### G2 — is the arm's availability envelope physically admissible?

The arm books Ravenswood's 1,724.8 MW steam bin as ~87 % unavailable in 2023.
**Already measured for that one bin in Phase 0 and reported there; what G2 fixes
in advance is the ISO-wide statistic, its threshold and its comparison norm,
none of which has been measured.**

**METRIC.** `booked_share(year)` = nameplate-weighted mean of
`1 − availability` over every NYISO **ST_GAS** bin carrying a derate, from
`unit_outage_derate_factors` × `_iso_plant_capacity`.

**NORM.** The detector's own documented real-world rate: **EFOR + planned
≈ 10–15 %** (`derive_campd_unit_outages.py --merit-order-guard` help text;
`docs/handoffs/campd-economic-layup-fix-charter-2026-07.md`, which sizes the
unguarded detector at 23–46 % of every ISO's CC capacity-year).

* **G2 DECLARES THE OVERLAY OVER-BOOKED** iff `booked_share > 0.40` in any year
  under the per-unit extract — more than **2.7×** the top of the cited norm.
* **If G2 does NOT fire, repair 2 is NOT proposed** and the session stops at
  repair 1. The control leg's `booked_share` is reported alongside, both
  directions.

### G3 — the economic-layup channel, sized at artifact level

`--merit-order-guard` already exists in the deriver and already writes a NYISO
layup companion; **no `ScenarioConfig` field selects a guarded standard
extract**, so nothing in any solve has ever read one. Re-derive the per-unit
companion **with** the guard at its **committed constants** — `MERIT_OOM_FRAC`,
`MERIT_RCC_PCTL`, `FULL_STOP_OVERRIDE_*` **untouched** — plus its matching
tranche companion on the same basis (the derate feeds the tranche denominator;
the two artifacts must never be derived on different bases).

* **G3 PASSES** iff the guarded per-unit extract (a) puts
  `(2500, ST_GAS)` availability **strictly between** the control's and the
  unguarded arm's in every year, **and** (b) brings `booked_share` **below the
  G2 threshold** in every year.
* **G3 FAILS** otherwise. On a fail the guard is **reported at its measured
  strength and NOT armed** — it does not get a second construction.

### G4 — the A/B ladder

Control = **the committed keeper**, which nyiso-176 §8a.1 established reproduces
**bit-identically** at HEAD (0 of 52,560 hourly zonal prices differ, all three
years). No control leg is solved.

| leg | arm | isolates |
|---|---|---|
| **B1** | per-unit attribution **+ repair 1** | the rule-19 stack, against nyiso-176's registered arm |
| **B2** | B1 **+ the merit-order guard** (only if G3 passes) | the economic-layup channel, against B1 |

One invocation each, `--year 2023 2024 2025`, one bundle each, years sequential
(rule 16), the two invocations concurrent (rule 12). Both legs are registered on
the dashboard whatever they score (rule 15).

### G5 — R6 / K5, CARRIED FORWARD VERBATIM

**A large favourable C3a-2025 move attributed to the per-unit REPRESENTATION
repair FAILS.** Both East River bins carry heat rate 7.4205 and the same
delivered gas, so moving energy between them changes no unit's marginal cost and
no marginal price; the representation repair's C3a expectation is **~ZERO**.

**Extended, explicitly, for this session.** Repairs 1 and 2 act on
**AVAILABILITY**, not on representation. A C3a move from them **is**
mechanistically expected — an availability change moves the supply stack — so
G5 does not forbid one. What G5 forbids is **banking it as the representation
repair's**, or promoting a C3a move whose mechanism is not stated. Any C3a
movement is reported with its own magnitude, sign and named mechanism.

## 3. Promotion bar (from the brief, restated and binding)

A leg may be promoted under rule 1 `[R-STRUCT]` even if some gates regress, but
**only** when (a) the arm is a **single adjudicated object**, (b) **every**
regressed criterion has a **stated mechanism**, and (c) the regression is **not
an unexplained side effect**. nyiso-176's arm failed all three. If neither leg
clears all three, **neither is promoted** and both are registered as probes.

## 4. Stop conditions

* **S1 — ZERO free parameters.** `MERIT_OOM_FRAC`, `MERIT_RCC_PCTL`,
  `FULL_STOP_OVERRIDE_DAYS`, `FULL_STOP_OVERRIDE_CF`, `UNIT_OUTAGE_MIN_DAYS`,
  `HIGH_LOAD_PCTL`, `MIN_INMERIT_HOURS` are used at their **committed** values.
  If a gate can only be passed by moving one of them, **the lever is REFUSED**
  and that is the session's result.
* **S2 — the per-unit repair is NEVER reverted** (rule 14), including if both
  legs score worse than the keeper.
* **S3 — no C3c lever** (brief).
* **S4 — rule 25 `[R-ISO-SCOPE]`:** only NYISO artifacts are derived. Every
  other ISO's tranche and outage CSVs stay **byte-untouched**, and no verdict
  crosses an ISO boundary.
* **S5 — rule 22:** every solved, scored and registered year is 2023–2025.
* **S6 — rule 23 `[R-FROZEN-DERIVE]`:** every re-derivation commit cites the
  **defect** (the rule-19 stack; the layup/outage conflation the guard was built
  for), **never a residual**. No residual is consulted in choosing to derive.
* **S7 — rule 24:** any new selector is a `ScenarioConfig` field reaching
  `run_config.json`, default-off and byte-inert off.

## 5. What this session will NOT claim

The repairs are proposed on **mechanism**, not on score. If B1 or B2 improves
C3a-2025 it is **not** evidence for the representation repair (G5) and it is not
quoted as one. If both legs score worse than the keeper, the accurate input and
the repairs **stay**, the keeper is **untouched**, and the result is a sized,
named root cause — which is the chartered deliverable either way.

---

# 6. AMENDMENT — committed BEFORE either A/B leg is solved, with NO score of any kind consulted

**Status at amendment: G1 PASS, G2 OVER-BOOKED, G3 FAILED AS WORDED.** No LP has
run. Everything below is driven by artifact-level measurement only; the
amendment changes a gate's **CONSTRUCTION**, never a threshold in response to a
result (the nyiso-175b K2 precedent).

## 6.1 G3 is recorded as FAILED, at full strength, and its consequence is honoured

Both legs fail, for different and separately-reported reasons:

* **G3(a) — "strictly between the control's and the unguarded arm's".** The
  merit-guarded per-unit extract puts `(2500, ST_GAS)` at **0.7715010038884795 /
  0.4653023102142477 / 0.2967897806694284**, which is the **control's value to
  16 significant figures** — the availability arrays are `np.array_equal` to the
  keeper's in all three years. It lands **ON** the endpoint, not strictly
  between it and the arm. **FAIL.**
* **G3(b) — "booked_share below 0.40 in every year".** The guarded extract
  reads **0.534 / 0.560 / 0.501**. **FAIL** — and the reason is a **defect in
  the gate's construction, disclosed here**: the **KEEPER ITSELF** reads
  **0.536 / 0.560 / 0.501**. The threshold therefore measures a **pre-existing
  property of the keeper**, not the guard's effect, so no guarded construction
  could ever have passed it. That was not visible when the gate was written.

**The consequence is honoured in full. The merit-order guard is NOT armed as a
repair of the availability envelope, and this session makes NO claim that it
fixes the over-booking.** G2 fires on the keeper as well as on the arm
(0.50–0.56 against a 10–15 % EFOR+planned norm); **that object stays OPEN and is
handed forward unrepaired.**

## 6.2 The brief's own item-(1) instrument is REFUTED at artifact level

The brief directed a confound-removal leg derived with `--no-fullstop-override`,
"so it matches the incumbent extract's own vintage". Derived and measured
(2019–2026, per-unit routing, zero solves): **it does not match.** On the
nameplate-weighted L1 distance of the mean-availability vector from the
keeper's, over every bin and all three years — a **post-registration
descriptive statistic, labelled as such and used for no gate below without
being fixed in advance in §6.3**:

| candidate companion | L1 distance from the keeper |
|---|---|
| unguarded per-unit (nyiso-176's arm) | 0.0943 |
| **`--no-fullstop-override`** | **0.1055 — FURTHER than the arm** |
| `--merit-order-guard` | **0.0006** |

`--no-fullstop-override` moves **41 bins** by more than 0.02 in 2023 alone, in
both directions: it deletes genuine long mechanical outages the in-merit filter
alone would keep, while leaving the economically-idle ones the filter admits.
**The confound the brief was reaching for is ECONOMIC LAYUP, not the full-stop
override**, and the item-(1) instrument is recorded as refuted.

## 6.3 G3′ REPLACES G3 — the question the brief actually posed

G3 asked whether the guard **repairs** the envelope; it does not, and that is
recorded above. What the brief asked is a **different** question: does a
candidate companion **hold the availability envelope at the keeper's** so that
the representation repair becomes a clean single delta?

**METRIC, fixed here before any solve** (both directions stated): for each
candidate, (a) the nameplate-weighted L1 distance above, and (b) hour-by-hour
`np.array_equal` on `(2500, ST_GAS)` — the bin that carries the damage.

* **G3′ QUALIFIES a candidate** iff L1 ≤ **0.01** **AND** (b) holds in all three
  years. On this bar the merit-guarded companion **QUALIFIES** and both the
  unguarded and `--no-fullstop-override` companions **DO NOT**.
* **If no candidate qualified**, no vintage-matched leg would be solved and the
  object would be handed forward. Stated so the gate could have gone the other
  way; the measurement, not the preference, decides.

**The claim a qualifying candidate earns is EXACTLY ONE THING and no more:**
that a solve on it changes the **representation** while holding the
**availability envelope** at the keeper's. It earns **no** claim about the
over-booking, which G2 leaves open.

## 6.4 The ladder, restated

Control = the committed keeper (bit-identical at HEAD, nyiso-176 §8a.1;
no control leg is solved).

| leg | arm | isolates |
|---|---|---|
| **B1** | per-unit attribution **+ repair 1**, on the **unguarded** companions | repair 1 (the rule-19 stack), against nyiso-176's registered arm |
| **B1′** | per-unit attribution **+ repair 1**, on the **G3′-qualifying** companions | the representation repair alone, availability held at the keeper's |

Together with the keeper and nyiso-176's registered arm these form a **2 × 2**:
{keeper-vintage availability, HEAD-unguarded availability} × {incumbent routing,
per-unit routing + repair 1}. Every cell is a single delta from a neighbour.

**G5 (R6/K5) BINDS HARDEST ON B1′ and is not relaxed by this amendment.** B1′ is
by construction the leg on which the representation repair's C3a expectation is
**~ZERO**. If B1′ moves C3a-2025 materially, that is a **result requiring a
named mechanism**, not a promotion argument, and the burden is on the mechanism.

**S1–S7 are unchanged.** No detector constant is touched; the guard runs at its
committed `MERIT_OOM_FRAC` / `MERIT_RCC_PCTL`. The promotion bar (a)(b)(c) is
unchanged and is not waived for B1′.
