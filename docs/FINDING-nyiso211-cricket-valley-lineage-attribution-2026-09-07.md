# FINDING nyiso-211 — the Cricket Valley deficit is the residue of ONE named flag, `unit_outage_extract_basis_share`, and it is an **accuracy repair falsified by the plant's own meter in the summer months**. Four standing readings of the CC_REGULAR object are corrected, including one of my own pre-registered verdicts.

**Session:** nyiso-211, NYISO backcast calibration. **Branch:**
`claude/nyiso-cc-regular-zonal-pa77pn`, off `main` `c7234b3b`. **Date:** 2026-09-07.
**Keeper: `2026-09-06-nyiso-202-startup-aware` — UNCHANGED.** No `ScenarioConfig` field, no
coefficient, no offer curve, no derive script, no scorer, no marker, no keeper, no gate moved.

**ZERO LP SPENT.** Rule 29 `[R-SCREEN]` step 0 in full. Every dispatch number below is read from
artifacts already committed to `main`; the only computation performed is the on-recipe
`fleet_only` fleet rebuild (no solve, no dispatch, no prices) that rule 29 step 0 names as its own
instrument. No screen, no arm, no bundle, no registration — so 29(c) has nothing to delete and
rule 15 `[R-DASHBOARD]` has nothing to register.

**Pre-registration:**
`results/calibration/PREREG-nyiso211-cricket-valley-lineage-attribution.md`, committed and pushed
at `8db2e40d` **before any payload was read at plant grain**, and not edited since.
**Machine records:** `_nyiso211_cricket_lineage_attribution.json`, `_nyiso211_overderate_test.json`,
`_nyiso211_clip_phase0.json`, `_nyiso211_clip_rebuild.json` (all under `results/calibration/`).
**Reproduce:** `uv run python scripts/probes/nyiso211_{cricket_lineage_attribution,overderate_test,clip_phase0,clip_rebuild}.py`
(the last three read the rebuild cache `scripts/probes/nyiso196_rebuild_checks.py --year {2023,2024,2025}`
populates; that probe had only ever been run for 2024, so its 2023 and 2025 records
`results/calibration/_nyiso196_rebuild_checks_{2023,2025}.json` are committed here as the by-product,
and its 2024 record reproduced byte-identically — see §9).

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES TO FIX.** NYISO's keeper reads **CALIBRATED, grade 7 of
8, fails 0**, C3c the lone ledgered non-downgrading caveat. Nothing below was selected because a
residual moved (rule 1 `[R-STRUCT]`, rule 23 `[R-FROZEN-DERIVE]`).

**Rule 22 `[R-HOLDOUT]`.** Every year read here is **in-sample (2023, 2024, 2025)**. 2022 was not
read at all. 2020, 2021 and the locked test are untouched; no marker byte moved.

---

## 0. The result in one paragraph

nyiso-210 handed forward one lead as "the sharper end": Cricket Valley (57185) was the **largest
positive** CC_REGULAR excess of 2023 on the pruned nyiso-186 control (+1.24 TWh on that record's
own basis) and is a **deficit** on the current keeper (−0.441 TWh), so "whatever moved it between
those keepers over-corrected". **It is answerable, the mover is a single named flag, and
"over-corrected" is the wrong word for what it did.** On the comparable half of the lineage,
`unit_outage_extract_basis_share` (nyiso-196) carries **89.7 % / 94.8 % / 96.1 %** of the
plant's movement in 2023 / 2024 / 2025 and **flips the sign in every year** (+0.084 → −0.509,
+0.797 → −0.535, +0.182 → −0.964 TWh). That flag is a zero-DOF construction repair with a stated
physical derivation — the CAMPD stack ids `U001`–`U003` collide with EIA-860's **steam** generator
ids, so each 1×1 block was booked at 174.2 MW against the fleet's 1,016.8 MW bin: **17.1 % removed
per block against a physical 33.3 %, and a fully dark plant kept 48.6 % available.** Under rule 14
`[R-ACCURATE]` it is the accurate input and it stays. What it costs is measurable and is reported
here at full magnitude: the repaired availability is **falsified by the plant's own meter** in
**three summer months of 2024 (Jul/Aug/Sep) and three of 2025 (Jun/Jul/Aug)** — CAMPD recorded more
energy than the LP was physically able to produce — and it hands Cricket Valley, the newest unit in
the fleet, a mean availability of **0.51 / 0.55** against **0.83–0.85** for the older units it is
supposed to displace. Against that, the same repair **cut class-wide over-ceiling months from
44 → 33, 37 → 32 and 29 → 26**, so it is right in the aggregate and wrong at this plant. Four
further standing readings are corrected in §4, one of them a pre-registered verdict of my own, and
the one candidate lever this session sized (`unit_outage_per_unit_clip`) is **measured two orders
of magnitude too small** to carry the object — killed at zero LP, before any solve.

## 1. Pre-registered verdicts, exactly as declared

| prediction | declared bar | measured | fires |
|---|---|---:|:--:|
| **I1** (186 anchor's measured side is the bench's) | every shared plant within 2 % | **FAILS at one plant**, Astoria Energy 55375, worst rel **0.4929** | **NO** |
| **I2** (payload plant sum vs bundle class total) | rel ≤ 0.05, all 9 anchor-years | worst **0.0037** | **PASS** |
| **I3** (rebuild reproduces at HEAD) | committed `mean_avail` to 4 dp, all plants | worst \|Δ\| **0.000000** | **PASS** |
| **P1** (extract-basis repair dominant) — *the preferred answer* | \|Δ₂\| ≥ 0.60 × S at 57185, 2023 | share **0.3488** | no |
| **P2** (mover upstream of nyiso-192) | \|Δ₁\| ≥ 0.60 × S | share **0.6111** | **YES** |
| **P3** (diffuse) | no step ≥ 0.60 × S | — | no |
| **P4** (repair year-flat while deficit grows) — *the one declared to HURT P1* | CV(Δ₂) ≤ 0.35 **and** deficit monotone | CV **0.3064**, monotone **true** | **YES** |
| **P5** (lineage did not move the over-runners) | \|Δ_total\| < 0.5 TWh each, 2023 | Bethlehem **+2.666 TWh** | **FALSIFIED** |
| **P7** (repair is plant-specific, reported only) | \|Δ₂(56940)\| ≤ 0.25 × \|Δ₂(57185)\| | +0.034 vs −0.593 | holds |
| **P8** (class redistribution, reported only) | \|Δ_total\| ≤ 0.5 TWh, 2023 | **−0.280** (2024 −1.832, 2025 −2.013) | holds on the declared year only |

**The pre-registered verdict is P2, and this session sets it aside under its own pre-registered
rule.** PREREG §3.1 declared, before any measurement: *"If I1 fails, the 186 anchor is not on the
bench's CAMPD basis, Δ₁ is not comparable, and the attribution is reported on the payload-only
lineage 192→196→202 with the failure stated — never repaired into a pass."* **I1 failed.** P2's
verdict rests entirely on Δ₁, the step I1 voids. It is reported as fired-as-declared in the table
above and carries no weight in §3; the load-bearing attribution is the declared fallback.

## 2. Why the 186 anchor does not survive: I1

| year | plant | bench CAMPD (TWh) | nyiso-186 record's own CAMPD (TWh) | rel |
|---|---|---:|---:|---:|
| 2023 | 55375 Astoria Energy | 4.2578 | **8.2924** | 0.4865 |
| 2024 | 55375 Astoria Energy | 4.2823 | **8.4451** | 0.4929 |
| 2025 | 55375 Astoria Energy | 4.0162 | **6.3278** | 0.3653 |

Exactly one plant fails, and it fails by roughly a **factor of two**. It is the plant nyiso-192's
*"astoria panel"* promotion was named for. Two other consequences of the record's vocabulary are
reported with it: three of its rows carry **no** CAMPD column at all, and the bench keys a plant
that splits across groups as `<code>:<group>` (2500, 50292) while the record keys every plant
plainly, so the record's row for a split plant covers **both** groups and cannot be compared to a
`CC_REGULAR`-only bench row. Those two plants are **excluded from every nyiso-186 comparison** and
the exclusion is carried in the machine record.

**A construction repair made mid-session, disclosed rather than buried.** My first pass folded the
bench's `<code>:<group>` keys onto the plain code on **both** sides. That was wrong: folding adds a
split plant's `CC_CHP` energy into the `CC_REGULAR` class sum, and I read the defective class-grain
numbers (P8) before catching it. P8 is a **reported-only** prediction on which no verdict hangs,
and the repair is stated here rather than silently applied. **P1–P5 and P7 are untouched by it** —
all five watched plants are plain-keyed in every source, which the probe now asserts.

**The repaired instrument reproduces nyiso-210 exactly**, which is the strongest available check
that the two sessions read the same object: CC_REGULAR class gap at the keeper, over the full bench
plant set, **−0.0945 / −0.1195 / +0.8833 TWh** against nyiso-210 §3's **−0.094 / −0.119 / +0.883**.

## 3. The attribution, on the lineage that is comparable

Model − CAMPD at Cricket Valley 57185 (Capital_Hudson, 1,312 MW npl), TWh, **CAMPD on both sides in
every year**. Δ₁ = 186→192 (lumped, several pruned promotions), Δ₂ = 192→196
(`unit_outage_extract_basis_share`, single live flag), Δ₃ = 196→202
(`nyiso_gas_bridge_startup_aware`, single live flag):

| year | CAMPD | gap@186 | gap@192 | gap@196 | gap@202 | Δ₁ | **Δ₂** | Δ₃ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 5.321 | +1.124 | **+0.084** | **−0.509** | −0.441 | −1.040 | **−0.593** | +0.068 |
| 2024 | 4.241 | +1.758 | **+0.797** | **−0.535** | −0.608 | −0.961 | **−1.332** | −0.073 |
| 2025 | 4.862 | +1.140 | **+0.182** | **−0.964** | −1.010 | −0.958 | **−1.146** | −0.047 |

**Three statements, in order of load-bearing:**

1. **Δ₂ owns the sign flip, in every year.** The gap is ≥ 0 at nyiso-192 and < 0 at nyiso-196 in
   all three years, and Δ₂ carries **89.7 % / 94.8 % / 96.1 %** of the movement across the two
   comparable steps. `nyiso_gas_bridge_startup_aware` (Δ₃) is ±0.07 TWh — it does not participate.
2. **The declared 2023-only statistic is the one year where the ranking inverts, and I report that
   rather than re-choosing the year.** On the full three-anchor decomposition Δ₁ (−1.040) exceeds
   Δ₂ (−0.593) in 2023 alone; in 2024 and 2025 Δ₂ is larger by 39 % and 20 %. The PREREG bound
   P1/P2/P3 to 2023, so P2 fires — and would not have fired on 2024 or 2025. **The year was chosen
   before the measurement and is not re-chosen after it**; the fallback in §2 is what carries the
   conclusion, and it agrees across all three years.
3. **The "monotone worsening" is not a monotone mechanism — P4 fires exactly on this.** The
   keeper's deficit reads −0.441 → −0.608 → −1.010, but `gap@202 = gap@192 + Δ₂ + Δ₃` and
   **neither component is monotone**: the pre-repair gap runs +0.084 → +0.797 → +0.182 and the
   repair runs −0.593 → −1.332 → −1.146. The monotone appearance is the sum of two non-monotone
   terms. P4's declared consequence therefore binds and is stated at full strength: **§3 names the
   step that flipped the sign and explicitly does NOT explain the growth.**

## 4. Four standing readings corrected

### 4.1 "The two newest H-class units under-run" is **two objects, not one** (P7)

CPV Valley 56940 was **already a deficit at the nyiso-186 control** — −0.374 / −0.261 / −0.358 TWh
— moved entirely by the lumped upstream step (Δ₁ = −0.386 / −0.425 / −0.498) and **untouched by the
repair** (Δ₂ = +0.034 / +0.058 / 0.000). Cricket Valley's deficit is **new** and created by the
repair. nyiso-210 §3.1 paired them as one "merit-order inversion inside CC_REGULAR"; they have
different provenance, different age, and must not be pursued as one lever.

### 4.2 The "persistent over-runners" are a property of the lineage **from nyiso-192 onward** (P5)

| plant | gap@186 (2023) | gap@202 (2023) | Δ_total |
|---|---:|---:|---:|
| **2539 Bethlehem Energy Center** | **−2.097** | **+0.569** | **+2.666** |
| 56196 Zeltmann | +1.003 | +0.556 | −0.447 |
| 55375 Astoria Energy | −0.129 | +0.294 | +0.423 |

**Bethlehem was a 2.1 TWh UNDER-runner on the nyiso-186 control and is a 0.57 TWh over-runner on
the keeper.** P5 is falsified decisively. nyiso-210 §3.1's "every plant in the 2022 top-3 over-runs
in all four years" is true **of the current lineage** and is not a standing property of the model;
any inference that treats those three as a durable object needs to state the lineage it holds over.
(Astoria Energy's own move is additionally implicated by the I1 failure at that plant.)

### 4.3 The lineage is a sequence of derate repairs that **cut** class energy, not a redistribution (P8)

CC_REGULAR class gap over the comparable plant set: **+0.520 → +0.240** (2023), **+1.867 → +0.035**
(2024), **+3.120 → +1.107** (2025). P8's declared 0.5 TWh bar holds on the declared year (−0.280)
and is exceeded in the other two (−1.832, −2.013). The lineage did not shuffle energy between
plants at constant class level; it removed 0.3–2.0 TWh of class energy while shuffling.

### 4.4 A committed measured-side record can disagree with the bench, and citations must say which basis

The nyiso-186 record carries an Astoria Energy CAMPD column ~1.9× the bench's. Any future citation
of `_nyiso186_cc_attribution.json` at plant grain must state its basis; its headline `E_twh`
statistic is a **one-sided positive-excess sum on the E-923 basis** and is not comparable to a
signed CAMPD gap at all. The "+1.24 TWh" that opened this investigation is that statistic; on the
CAMPD basis the same plant-year reads **+1.124 TWh**, and the swing to the keeper is **−1.565**,
not −1.68.

## 5. POST-HOC: the repaired availability is falsified by the plant's own meter

**Not pre-registered. Decides no declared verdict.** The test is a physical contradiction between
two *measured inputs* — the outage extract and CAMPD generation — and not an argument about any
residual: available energy is `Σ_h Σ_tranches pmax × availability[h]` on the LP's own availability
array; a month where the meter exceeds it is a month the LP **could not** have produced what the
meter recorded.

Cricket Valley 57185 (LP pmax 1,086.9 MW):

| year | basis | mean avail | available (GWh) | CAMPD (GWh) | meas/avail | months meter > ceiling |
|---|---|---:|---:|---:|---:|---|
| 2023 | pre-196 | 0.8008 | 7,624.2 | 5,321.4 | 0.698 | Jul |
| 2023 | **keeper** | 0.7145 | 6,802.5 | 5,321.4 | 0.782 | Jul |
| 2024 | pre-196 | 0.6955 | 6,621.7 | 4,240.9 | 0.641 | **none** |
| 2024 | **keeper** | **0.5097** | 4,853.1 | 4,240.9 | **0.874** | **Jul, Aug, Sep** |
| 2025 | pre-196 | 0.7175 | 6,831.4 | 4,861.8 | 0.712 | Aug |
| 2025 | **keeper** | **0.5526** | 5,261.0 | 4,861.8 | **0.924** | **Jun, Jul, Aug** |

**Reported against it, at full magnitude — the condition is endemic, not unique to this plant.**
On the keeper basis **12 / 9 / 9 of the 21** CC_REGULAR plants carry at least one over-ceiling
month in 2023 / 2024 / 2025, and several are over-derated on an **annual** basis, which Cricket
Valley is not — 2023: Ravenswood 2500 (meas/avail **1.014**), Rensselaer Cogen 54034 (1.017), CPV
Valley 56940 (1.0005); 2024: Ravenswood 2500 (1.001), Carthage 10620 (**2.893**), CH Resources
Syracuse 10621 (1.486); 2025: CPV Valley 56940 (1.0003). **And the repair improved the class on
every measure**: class-wide over-ceiling months fall **44 → 33, 37 → 32, 29 → 26**, the
plants carrying one fall **13 → 12, 10 → 9, 10 → 9**, and the one plant that was over-derated
annually in **every** year before it — Athens 55405 (1.042 / 1.059 / 1.028) — no longer is in any.
No plant becomes annually over-derated that was not already; Ravenswood 2500 (1.030 → 1.014 in
2023) and CPV Valley 56940 (1.010 → 1.0005) are reduced but not cleared.

What is distinctive at Cricket Valley is narrower than "uniquely broken", and is stated as such —
but it is exact, and it was measured rather than asserted: across the whole class and all three
years, **57185 is the ONLY plant that gains an over-ceiling month from the repair** (2024 none →
Jul/Aug/Sep; 2025 Aug → Jun/Jul/Aug). **Every other movement in the class is a loss** — Athens
55405 7 → 3, 7 → 3, 7 → 4; Bethpage 50292 5 → 0 and 3 → 0; CPV Valley 56940 7 → 5; Bethlehem 2539
1 → 0; Astoria Energy II 57664 2 → 0. So the repair is one-sidedly corrective everywhere except at
the plant it was named for,
and its availability is the lowest of any large modern CC in the fleet — 0.51 / 0.55 against
(2024) Bethlehem 0.855, Zeltmann 0.833, Ravenswood 0.840, Astoria Energy 0.892 — which inverts the
physical expectation for the newest unit. (Athens 55405, 1,222 MW, sits at 0.439 and is named here
as an unexplained second instance; its gap is small, so it is reported and not pursued.)

**Rule 14 `[R-ACCURATE]` reading, stated plainly.** The repair has a derivation, zero free
parameters, and improves the class; it is the accurate input and **it stays**. The worse fit at
this plant is therefore a **discovered bug**, exactly as rule 14 says — the old 17.1 % share was
silently compensating for something else. What this session adds is that the compensation is not
purely a merit-order story: in six plant-months the repaired ceiling is *below the meter*, so part
of the deficit is an **outage-window construction** defect that no offer curve can reach.

## 6. POST-HOC: the one candidate lever, sized and killed before any solve

`unit_outage_per_unit_clip` (miso-202, GATED default-off, zero free parameters) enforces "one unit
cannot be more than 100 % out of service" and by construction can only ever remove **less**. Its
NYISO cell reads `U` and its own evidence line says *"this ISO's own extracts must be censused
before the cell can move"*. Censused here, two ways:

* **All four loader channels at once**, by diffing `FleetArrays.availability` across two on-recipe
  `fleet_only` rebuilds of the **current keeper's** meta: it moves **71 / 64 / 55 units of ~810**
  and restores **78.8 / 68.8 / 81.6 GWh** of available energy per year (2023: ST_GAS 62.9,
  CC_REGULAR 11.9, CC_CHP 4.0). **It is not identically inert at NYISO** — the largest single
  beneficiaries are Ravenswood-family ST_GAS bins (2625, 8906, 2480, 2500) and, in 2025, Astoria
  Energy II 57664 at 27.6 GWh.
* **At Cricket Valley it restores 8.39 GWh/yr** — against a deficit of **441 / 608 / 1,010 GWh**.
  It changes **zero** over-ceiling months and moves the plant's mean availability by
  **+0.0008**.

**Verdict: the clip is two orders of magnitude too small to carry this object, and the arm is
killed at zero LP** — rule 29 step 0 doing exactly what it exists to do. **The cell stays `U`**,
not `I`: the flag has a real, un-adjudicated NYISO-wide footprint that a future session may screen
on its own object (the ST_GAS restoration), and calling it inert would over-claim from a
measurement that only shows it inert *here*. Rule 28(d) is respected throughout — MISO's verdict
and MISO's numbers transfer nothing.

## 7. What this hands forward

* **The named object for the next session, in-sample and with one channel now closed:** *why the
  model under-dispatches Cricket Valley at corrected availability.* The availability channel is
  measured (§5): at the keeper's own ceiling the plant would need 87 % / 92 % of every available
  MWh to reach its meter, and in six plant-months it could not reach it at all. The residual is
  therefore **two** objects — an outage-window construction defect (the six months) and a
  merit/offer-position defect at the newest H-class CC (the rest) — and they should be separated
  before either is levered.
* **Do not pursue Cricket Valley and CPV Valley as one lever** (§4.1). CPV's deficit is old,
  stable, and upstream of every flag this lineage carries.
* **`unit_outage_per_unit_clip` is not the lever for this object** (§6), measured, zero LP.
* **The NYC over-run** — nyiso-210's object 2, and the one its §5 said the winter downstate
  locational premium most directly implicates — is **untouched here** and remains blocked on
  identification and owner-executable.
* **No owner card is opened.** Whether C1 should see a zonal decomposition remains the owner
  question nyiso-210 declined to prejudge, and this session declines it too; §4.2 and §4.3 sharpen
  the record behind it without moving a gate.

## 8. Reported at full magnitude — measured, not the finding

* **P8 on the declared year holds and on the other two does not** (§4.3) — reported, and the
  mid-session key-vocabulary repair that produced the correct numbers is disclosed in §2.
* **Athens Generating Plant 55405** carries a mean availability of 0.218 / 0.439 / 0.389 on the
  keeper basis at 1,222 MW npl, and over-ceiling months in all three years. Named, not pursued.
* **Three of the 21 CC_REGULAR plants have mean availability below 0.08** (Carthage 10620 at
  **0.0026** in 2024, CH Resources Syracuse 10621 at 0.013, Rensselaer Cogen 54034 at 0.029), and
  Carthage's meas/avail reads **2.89**. These are small units and this session claims nothing about
  them; they are recorded because a census that found them and stayed silent would be the more
  misleading report.

## 9. Environment and pre-existing state (rule 25 `[R-ISO-SCOPE]`: re-measured, not repaired)

* **`scripts/probes/nyiso196_rebuild_checks.py --year 2024` reproduces its committed record
  exactly** — worst \|Δ\| **0.000000** over all 17 `F2_identity` plants × both availability fields,
  and identical `F1_footprint` (128 units, same 17 plants). This is I3 and it is a stronger
  environment statement than the handoff's nominated check.
* **`scripts/probes/nyiso198_rebuild_checks.py --year 2024`** was also run as the handoff's named
  check: it reproduces its committed record and leaves `git status --porcelain -uno` **empty** (its
  own "VERDICT: STOP" is the nyiso-198 gate, not drift).
* **G-DRIFT is not owed** — no arm reached a solve, so there is no control to validate (rule 29(b)).
* **Pre-existing failures at this HEAD, re-measured:** the charter-named test files read
  **37 failed / 80 passed** (`test_d62_published_going_forward_bar`,
  `test_d74_no_default_cap_convention`, `test_ff_readiness_battery`,
  `test_collate_scenario_campaign_common_set`, `test_collate_scenario_campaign`,
  `test_caiso_st_gas_peak_measured`). `tests/scoring/test_gate_a_provenance.py::test_live_board_passes`
  fails on **MISO's** stale gate-(a) stamp — the board cites `2026-09-06-miso-230-ctdrag-seam`
  against a live keeper of `2026-09-06-miso-232-hourly-seam`. **Neither is this lane's to fix.**

## 10. Governance

| item | state |
|---|---|
| **Rule 1 `[R-STRUCT]`** | a structural mis-specification named and a mechanism's cost measured; no residual optimized, no mechanism armed or disarmed |
| **Rule 14 `[R-ACCURATE]`** | the accurate input **stays**; the worse fit is reported as a discovered bug and routed, not buried back into an estimate |
| **Rule 22 `[R-HOLDOUT]`** | in-sample years only; 2022 not read; no marker byte moved |
| **Rule 29 `[R-SCREEN]`** | step 0 only — one candidate lever sized and killed pre-solve; no screen, no arm, no bundle, so (c) has nothing to delete |
| **Rule 15 `[R-DASHBOARD]`** | no run produced, nothing to register |
| **Rule 28 `[R-MECH-MATRIX]`** | NYISO shard stamped in this session; **no cell verdict letter moves** — `unit_outage_per_unit_clip` stays `U` with its census recorded, `unit_outage_extract_basis_share` stays `K` with its measured cost recorded |
| **Rule 25 `[R-ISO-SCOPE]`** | NYISO only; MISO's gate-(a) failure reported, not touched |
| **Rule 27 `[R-PUSH]`** | source files ≥ 300 lines pushed are blob-verified after push |
| **Markers / keeper / gates** | untouched; D-5(b) does not attach (no candidate) |
| **Owner cards** | all five stay UNRULED; none is prejudged |

---

*(nyiso-211, 2026-09-07. The preferred answer did not fire, the answer that did fire was voided by
the session's own identity check, and the conclusion rests on the fallback the pre-registration
named in advance. A clean negative on the one candidate lever, and a measured physical
contradiction inside a keeper input that no offer curve can reach.)*
