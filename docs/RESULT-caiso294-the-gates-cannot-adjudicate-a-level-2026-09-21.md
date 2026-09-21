# RESULT caiso-294 — both level arms fail, and the gate set is why: G-3/G-4 are algebraically tests that the level did NOT change

**Lane:** caiso-294 · **Date:** 2026-09-21 · **LP spent: ZERO.** No shard was launched.
**Keeper untouched**: nothing armed, nothing disarmed, no committed artifact byte moved, no run
registered, no bundle written.
PRECOMMIT (pushed before the ARM B statistic was computed):
`docs/PRECOMMIT-caiso294-chp-steam-level-2026-09-20.md`.
Predecessor: `docs/RESULT-caiso293-the-chp-steam-floor-is-an-energy-average-2026-09-20.md`.

---

## 0. The answer in four paragraphs

**ARM A does not do what the lane instruction says it does.** It was handed over as "keep the
diluted level, confine only its hours — energy-conserving by construction, so G-4 passes
trivially". `steam_level_cf` is *already* `on_freq × p50(loading-when-on)`, so holding **that**
level in `on_frac` of the hours applies the on-frequency **twice**. Measured at zero LP on the
keeper's own fleet: it **removes 80.4–83.8 % of the class-A/B forced energy** and also breaks
the G-3 flat-host control in 2022 (2.294 % against a < 2 % bar). It is not a partial repair of
the level; it is an ~82 % deletion with a token residue left in the right hours.

**ARM B — the never-below-when-online level, `p2` of the online sample, declared ex ante and
never swept — also fails, on all three gates.** Cyclers −85.1 / −85.8 / −87.3 / −86.1 %/yr
against G-4's < 10 %; flat hosts −48.4 / −48.2 / −47.5 / −47.9 %/yr against G-3's < 2 %.

**But the reason both arms fail is provable rather than evidential, and that is this lane's
actual result.** Under the windowed construction the window size is
`on_frac ≡ steam_level_cf / median_cf`, so a level `L` held in `on_frac × H` hours delivers
`L × on_frac × H` against today's `steam_level_cf × H`, and the ratio collapses to

> **forced-energy ratio ≡ `L / median_cf`**, exactly — independent of the window's placement.

G-4 (< 10 % move) therefore admits only `L ∈ [0.9, 1.1] × median_cf`, and G-3 (< 2 %) only
`L ∈ [0.98, 1.02] × median_cf`. **Both gates are, algebraically, tests that the LEVEL DID NOT
CHANGE.** They were correct and load-bearing for caiso-293's arm, which changed only hours.
Inherited onto an arm that changes the level they are degenerate: the single level that passes
them is `median_cf`, which is the saturating level caiso-293 already rejected for running 5–14×
the capacity of the tranches carrying it. **The gate set cannot adjudicate a level repair.**
Re-specifying a pre-registered gate is a governance act and is not this lane's to take
(rule 1 `[R-STRUCT]`), so the lane stops and hands it over.

**A fourth thing fell out that nobody was looking for: the "frozen" derive is not
reproducible.** Re-running `derive_thermal_tranches.py --iso CAISO --years 2023 2024 2025` at
HEAD does not regenerate the committed artifact — **29 of 156 plant-groups carry real value
drift** (6 of them CHP; `online_hours` moves by up to 514 h and `steam_level_cf` with it), the
row count goes 156 → 158, and the **`chp_btm_pct` column, populated on 21 committed rows, is not
emitted at all.** Rule 23 `[R-FROZEN-DERIVE]` protects a derive from being re-run against a
residual; it does not make the artifact reproducible, and this one is not.

---

## 1. ARM A — measured and falsified on its own premise

Probe `scripts/probes/caiso294_arm_a_energy.py`. Reached without touching `src/`:
`fleet/assembly.py` consumes the loader's `(on_frac, level_on_cf)` pair as
`chp_duty_on_frac, pmin_cf`, so returning `(on_frac, on_frac × level_on_cf)` puts the level
exactly where the unarmed path puts it and moves only the hours.

| year | class A+B forced TWh, keeper | **ARM A** | Δ | G-3 flat-host Δ |
|---|--:|--:|--:|--:|
| 2022 | 0.1908 | 0.0374 | **−80.41 %** | **2.294 % FAIL** |
| 2023 | 0.1883 | 0.0333 | **−82.30 %** | 1.914 % |
| 2024 | 0.2412 | 0.0443 | **−81.62 %** | 1.841 % |
| 2025 | 0.1786 | 0.0290 | **−83.79 %** | 1.690 % |

Structurally it is worse than its score. Its object says *"in the top ~5 % of load hours this
cogen must produce at ~2 % of nameplate"* — neither a steam obligation nor a commercial output.
It **keeps** the energy-average magnitude caiso-293 diagnosed as the defect and divides the
hours, so the magnitude error grows while four fifths of the floor disappears. A deletion is a
legitimate outcome for these plants (caiso-293 §4 option 3), but it should be taken deliberately
and named, not reached through a mechanism presenting itself as a window.

---

## 2. ARM B — the level, declared before it was computed

`_CHP_STEAM_FLOOR_ON_PCTILE = _CHP_PMIN_PCTILE = 2`, new column **`chp_pmin_on_cf`**: the
file's existing never-below convention applied to `on_cat` instead of `all_cat`. Declared in
PRECOMMIT §3 and pushed at `0450553d` **before** the statistic was computed; no percentile was
swept, and `p25_cf` was refused again for the reason caiso-293 refused it.

**The derive ran to a SCRATCH path only.** No committed artifact byte moved, so rule 23's
subject was never touched; the owner ruled *"measure first, rule after"* and this is the
measurement.

Levels, all 13 `ok` CHP rows populated, **none reads 0.0** (the declared degeneracy risk did
not materialise):

| | `chp_pmin_on_cf` | `median_cf` | ratio | `steam_level_cf` (today) |
|---|--:|--:|--:|--:|
| ten cyclers | **5.6 – 15.2** | 33.9 – 98.0 | **0.073 – 0.217** | 0.4 – 21.3 |
| three flat hosts | **38.8 – 81.8** | 94.5 – 101.6 | **0.382 – 0.818** | 86.2 – 99.8 |

Gates (`scripts/probes/caiso294_arm_b_gates.py`):

| year | cyclers TWh off → ARM B | G-4 | flat hosts TWh off → ARM B | G-3 |
|---|--:|---|--:|---|
| 2022 | 0.1908 → 0.0284 (**−85.14 %**) | FAIL | 5.1191 → 2.6412 (**−48.41 %**) | FAIL |
| 2023 | 0.1883 → 0.0267 (**−85.80 %**) | FAIL | 4.7628 → 2.4667 (**−48.21 %**) | FAIL |
| 2024 | 0.2412 → 0.0306 (**−87.31 %**) | FAIL | 3.8353 → 2.0124 (**−47.53 %**) | FAIL |
| 2025 | 0.1786 → 0.0248 (**−86.10 %**) | FAIL | 4.0188 → 2.0932 (**−47.92 %**) | FAIL |

The measured aggregates land inside the per-plant `L / median_cf` band predicted by §3's
algebra (cyclers 0.127–0.149 measured against a 0.073–0.217 per-plant range), which is what
turns §3 from an assertion into a check.

---

## 3. THE LOAD-BEARING FINDING — the gate set is degenerate on a level arm

The window size is the identity caiso-293 established, `on_frac ≡ steam_level_cf / median_cf`.
So for any level `L` held in the top `on_frac × H` live hours, against today's `steam_level_cf`
held in all `H`:

```
ratio = (L × on_frac × H) / (steam_level_cf × H)
      = L × (steam_level_cf / median_cf) / steam_level_cf
      = L / median_cf                      ← window placement cancels entirely
```

Consequences, none of them about ARM B:

* **G-4 (< 10 %) ⇒ `L ∈ [0.90, 1.10] × median_cf`. G-3 (< 2 %) ⇒ `L ∈ [0.98, 1.02] × median_cf`.**
  The only level that clears both is `median_cf` itself.
* `median_cf` is the level caiso-293 measured as **5–14× the capacity of the tranches carrying
  it** (Gilroy 82.810 MW against a 22.577 MW carrying capacity), which saturates against
  `pmax × availability` and is why its G-4 read −10.220 % in 2025 rather than 0.
* So the gate set admits exactly one level, and that level is the one already rejected on
  structure. **Every level repair fails these gates by construction, before any evidence.**

**This is not a reason to move the gates, and this lane does not move them.** G-3 and G-4 were
declared ex ante for an arm that redistributes hours at a fixed level, and for *that* arm they
are exactly right — G-3 in particular is what proved caiso-293's arm was a measured no-op on the
flat hosts. What is now visible is that they were **inherited onto a different question**. The
premise they encode — *"this repair redistributes hours, it does not remove energy"* — is in
direct conflict with the diagnosis, which is that the annual energy is **itself wrong**: five of
thirteen metered plants were forced above their own whole-year meter. Conserving that energy
conserves the error. **Re-specifying a pre-registered gate is the owner's act, not a lane's**, so
the lane reports the conflict and stops.

---

## 4. G-5 FAIL — the committed artifact is not reproducible at HEAD

G-5 was declared in PRECOMMIT §4 as a purely-additive check on the re-derive. It fails, and the
failure is about the derive rather than about ARM B:

| | committed | re-derive at HEAD |
|---|--:|--:|
| rows | 156 | **158** (`55077/CC_REGULAR`, `57901/CC_REGULAR` appear) |
| plant-groups with **real value drift** | — | **29 of 156** (6 CHP) |
| `chp_btm_pct` | populated on **21** rows | **column not emitted at all** |
| `online_frac` blank → populated | — | 70 cells (a deriver GROUP-SET difference) |

Value drift by column: `online_frac` 70 (blank→value), `online_hours` 29, `p25_cf` 24,
`median_cf` 23, `committed_pct` 21, `peaking_pct` 7, `steam_level_cf` 5, `chp_pmin_cf` 2,
`nameplate_mw` 2. Worked examples on the plants this lane cares about — Gilroy `online_hours`
1191 → 1612 and `steam_level_cf` 19.7 → 31.4; King City 1082 → 1596 and 21.3 → 14.3; Double C
601 → 942 and 11.3 → 2.1; Goal Line 678 → 920 and 17.3 → 30.3. Seven of the thirteen CHP rows,
including every plant in the D-4 failing set that matters most, are **unchanged**.

The artifact's own sidecar already says the deriver group sets in force at its derive time are
**UNKNOWN and not recoverable from the file** (`provenance: "backfill-descriptive"`, xiso-6), so
the `online_frac` and `chp_btm_pct` differences are that unknown surfacing. The `online_hours`
drift is not — it is a different CAMPD/availability sample.

**Why this matters beyond this lane.** Rule 23 `[R-FROZEN-DERIVE]` says a measured parameter
re-derives only when its source data updates, and that a re-derivation commits must cite the data
change. That discipline presumes the derive is a function of its inputs that can be re-run. Here
the committed CAISO artifact **cannot be regenerated at HEAD**, so there is no way to tell a
legitimate source-data update from an accidental one, and the artifact is frozen only in the
sense that nobody has re-run it. **It was not measured before, because nobody had reason to
re-run the derive.** This lane had one, and found it. Routed, not absorbed — it is not a CHP
question and is not fixed here.

---

## 5. What the evidence DOES say about ARM B's level (reported, never substituted for a gate)

Two things, both from tests that already existed, so neither is a criterion minted after seeing
the result:

**(a) No saturation.** The level goes from 5–14× the carrying tranche capacity (`median_cf`) to
5.6–15.2 % of nameplate — comfortably inside the econ band on every plant. The clip that broke
caiso-293's G-4 in both directions (per-plant ratios 0.808–1.990) does not arise.

**(b) caiso-293's own published headline test: forced energy against the plant's own annual
meter.** That is the measurement the whole diagnosis was built on ("five of thirteen metered
floored plants are forced to deliver more energy than their meter recorded for the entire year").

| plants forced ABOVE their own annual meter | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|
| keeper today | 2 / 10 | 1 / 10 | **4 / 10** | **5 / 10** |
| ARM B | **0 / 10** | **0 / 10** | **0 / 10** | **0 / 10** |

Per-plant it swings a long way the other side: ARM B forces 0.02–0.83 of each plant's own meter.
For a *never-below* floor that is the right side to be on — a floor should sit well under actual
output — but it is a large move and it is reported at full magnitude, not netted.

**This is offered as evidence for the owner's decision, not as a pass.** No gate was
re-specified, and (b) is not claimed to substitute for G-3 or G-4.

---

## 6. THE STRUCTURAL QUESTION THIS PUTS ON THE TABLE

ARM B cuts the **flat hosts** by 48 % as well, and that is not a defect in the measurement —
it is the two populations pulling the statistic in opposite directions:

* For the **ten cyclers**, `MECH_CHP_STEAM` should be a **never-below-when-online** floor: the
  steam obligation the host imposes whenever the unit is committed. `p2` of the online sample is
  that object.
* For the **three flat hosts**, the mechanism currently implements an **operating level** — the
  level a 96 %-capacity-factor baseload cogen actually runs at — and `steam_level_cf ≈ median_cf`
  there because `on_freq ≈ 1`. A `p2` over 22,000 online hours catches roughly 450 hours of ramp
  tail, so it reads 38.8 % where the operating level reads 99.8 %.

**One statistic cannot be both**, and G-3's very existence encodes the assumption that a repair
must leave class C untouched. The honest options are a per-population level source (which needs
a membership rule, and rule 19 `[R-ONE-MECH]` wants that reconciled rather than stacked), or
accepting that the flat hosts' floor is an operating level and the cyclers' should be a
never-below, or caiso-293 §4's option 3 for the cyclers alone. All three are larger objects than
this lane and none is decided here.

---

## 7. LANDED AND SETTLED, independent of everything above

**D-5 is CLEARED** (commit `0450553d`), as a declaration rather than a repair.
`caiso_ra_mustoffer` is market design and rule-13 admissible in both modes — the bridge reads the
model's own base-cost P0 run pattern against the physical `CC_COMMITMENT_PARAMS` min-down time,
so no measured outcome enters. The parity difference is the known `w2-caiso-ra-p2` forecast
**wiring gap**: the symbol is called **twice in `scripts/run_calibration.py` and zero times in
`src/market_sim/runner.py`** (measured). Declared in
`docs/backcast-measured-data-audit-2026-06.md` with **what the declaration costs stated rather
than hidden** (a CAISO forecast year carries no RA must-offer commitment while every backcast
year does), registry row flipped to `declared=True`, and `test_wiring_gap_fails` **retargeted
onto `gas_st_netload_drag` rather than deleted** (rule 26 `[R-DELETE]`) so the guard against a
future undeclared wiring gap is intact. Measured after: **D-5 failures `[]`, 12 rows, 0 FAIL.**
The keeper's committed `legitimacy_diagnostics.json` still reads D-5 FAIL until the bundle is
regenerated — the scorer is fixed, the artifact is a snapshot. Closing the wiring gap for real is
a forecast-path model change and is deliberately not bundled in.

**D-1 is measured IMMATERIAL and nothing was spent on it.** The two failures are ST_GAS 2024
(`r` 0.468) and 2025 (`r` −0.036). Rule 19 `[R-FORCED-BUDGET]`'s shape leg binds only at ≥ 2 % of
ISO load on `max(model, actual)`:

| year | ISO load TWh | 2 % bar | ST_GAS model | ST_GAS actual | max / load |
|---|--:|--:|--:|--:|--:|
| 2022 | 219.538 | 4.391 | 0.331 | 1.339 | 0.61 % |
| 2023 | 207.473 | 4.149 | 0.080 | 1.384 | 0.67 % |
| 2024 | 212.162 | 4.243 | 0.086 | 0.086 | **0.04 %** |
| 2025 | 204.837 | 4.097 | 0.013 | 0.056 | **0.03 %** |

In the two failing years it is **50–150× below the bar**. Report-only; recorded so the next lane
does not re-open it.

---

## 8. Gates as they fell, provenance, and what was not spent

| gate | bar | caiso-293 ARM | **ARM A** | **ARM B** |
|---|---|---|---|---|
| **G-1** identity, all 13 ISO artifacts | ≤ 0.05 | PASS (0.000000) | PASS | PASS (unaffected) |
| **G-2** off-inert | bit-identical | PASS (two-version snapshot) | n/a (no src change) | n/a (no src change) |
| **G-3** flat-host control | < 2 %/yr | PASS 0.831/0.363/0.505/0.050 | **FAIL 2022** | **FAIL all four** |
| **G-4** cyclers energy | < 10 %/yr | **FAIL 2025** (−10.220) | **FAIL all four** | **FAIL all four** |
| **G-5** derive purely additive | exact | n/a | n/a | **FAIL** (§4) |
| **G-6** D-4 prediction | declared | 28 → 20 | 28 → 16 | 28 → 16 |

* **G-DRIFT (rule 29 `[R-SCREEN]` (b)) — discharged by MEASUREMENT, not argument.** The branch
  was rebased mid-lane from `ef6a498a` onto `0359a178` (hydro-1: `hydro_pondage_bound`
  default-off, plus a RoR hybrid-label repair its own lane verified byte-identical for CAISO).
  G-1/G-3/G-4 were re-run on the rebased tree and reproduce **every digit** of the pre-rebase
  numbers, so hydro-1 is inert for this measurement as a fact rather than a classification.
* **The D-4 prediction is LEVEL-INDEPENDENT** and holds for both arms: the conduct rider convicts
  on `median(measured MW over the binding hours) ≤ 0`, which reads an hour set and never a
  magnitude. Declared 28 → 16 (7→2 / 7→5 / 7→4 / 7→5). The probe **reproduces the keeper's
  committed 28 exactly** on its control leg, and its twelve clearing plant-years are a strict
  superset of caiso-293's pooled-window eight.
* **Retrievability (rules 31 / 34):** nothing to retrieve — **no solve was run and no bundle
  exists**, so no promotable artifact is stranded on this container. The five probe artifacts
  (`results/calibration/_caiso29{3,4}_*.json`) and the scratch re-derive are gitignored; every
  number they carry is reproduced here and in the PRECOMMIT. **Nothing was deleted.**
* **Shards (rule 33 `[R-SHARD-ARCHIVE]`):** none launched, so none to archive.
* `D4_WINDOWS[(MECH_CHP_STEAM, None)]` **stays `(0, 24)`** and is not narrowed.

---

## 9. THE DECISION THIS LANE OWES THE OWNER

1. **The gate set is the blocker, not the arm.** G-3 and G-4 admit exactly one level,
   `median_cf`, which is the saturating one. If the level is to be repaired at all, those two
   gates need re-specifying for a level arm — a governance act, yours. The natural replacement
   already exists in the record rather than needing to be invented: caiso-293's own headline test
   (forced energy ≤ the plant's own annual meter), on which ARM B goes 2/1/4/5 → 0/0/0/0.
2. **If the gates are re-specified, ARM B is ready**: the column is declared, the derive change
   is written, and the four shards are specified in PRECOMMIT §8.
3. **The two populations want different statistics** (§6) and the mechanism currently serves one.
   That question is larger than either arm.
4. **The derive is not reproducible** (§4). Independent of all of the above, and not a CHP
   question — routed rather than absorbed.
5. **D-5 and D-1 are done** (§7) and depend on none of it.

My recommendation is **(1) then (2)**: re-specify G-3/G-4 for a level arm on the meter test that
already exists, then run ARM B against them. I am not making that change myself, because
selecting the criterion after seeing which one the arm passes is precisely what rule 1
`[R-STRUCT]` exists to forbid — even when, as here, the replacement is the predecessor's own
published test.
