# FINDING — nyiso-206: the Capital_Hudson fill delivers **7.3–8.0× the min-stable level its own coefficient asserts** — a real, large, previously unmeasured construction gap. And the repair that would close it is **REFUTED by nyiso-205's own decisive test**, inheriting `pro_rata`'s exact rule-17 signature. A clean negative on the repair, and an owner card on the gap

**Session:** nyiso-206, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-ruj0qb`, off `main` `4fa2a714`. **Date:** 2026-09-06.
**DATA PROFILE:** `nyiso`. **Keeper:** `2026-09-06-nyiso-202-startup-aware` — **UNCHANGED**.
Nothing promoted, nothing registered, no `ScenarioConfig` field, no coefficient edit, no CSV edit,
no `src/market_sim/` change.

**ZERO LP WAS SPENT.** Rule 29 `[R-SCREEN]` step 0 gated the solve to zero, as the PREREG said it
expected to: the only outcomes on the table were a clean negative and a card, and **neither is an
arm.**

**PREREG:** `results/calibration/PREREG-nyiso206-ch-fill-level-basis.md` — committed and pushed
**before any number was read** (`2a68cc24`), with **addendum §A** (the min-stable-capped
counterfactual, declared with its closed-form prediction) committed alongside the probe
(`032ef4e8`) **before the probe was ever executed**, and **addendum §B declared POST-HOC and
labelled as such** (§4.2 below).
**Instrument:** `scripts/probes/_nyiso206_ch_fill_level_basis.py` →
`results/calibration/_nyiso206_ch_fill_level_basis.json`.
**Companion:** `docs/DECISION-CARD-nyiso206-ch-fill-level-basis-2026-09-06.md`.

---

## 0. Verdict in one paragraph

The pre-registered question was whether `cheapest_first` delivers the physics that
`floor_pct = commit_frac × min_stable_pct` asserts. **It does not, and the gap is not marginal.**
The coefficient's own derive script documents `min_stable_pct` (ST_GAS **0.12**) as *"the class's
physical min-stable level of a **committed unit** … once committed it sits at this physical
Pmin"*; measured on the limb's own binding window, the shipped fill places the floor at an
MW-weighted **0.871 / 0.895 / 0.958** of a row's own available capacity — **7.26× / 7.46× / 7.98×
that level** — with **100.0 % / 100.0 % / 98.5 %** of all forced energy delivered *above* it, a
maximum intensity of **exactly 1.0000 in every year** (rows pinned at full availability), and
**74.3 % / 14.1 % / 81.9 %** of the forced energy delivered at that pin. This is a genuine
construction mismatch of the nyiso-203 §6 class and **larger in relative terms than that one by a
factor of ~150** (NYC: −5.0 %). **But the obvious repair is refused by the meters.** Capping the
fill at each row's min-stable level — the construction the coefficient literally describes, with
**zero free parameters** and a **closed-form** committed share — would floor Danskammer 2480 in
**100 % of binding hours in all three years (504 / 432 / 600 h) at a metered P(on) of
0.125 / 0.255 / 0.370**: the **identical signature**, hour-for-hour, that nyiso-205 used to refute
`pro_rata` one session ago, and it manufactures **1.54×** the energy (0.03595 vs 0.02332 TWh).
**The root cause is that the coefficient's two factors describe a fleet that does not exist:**
`commit_frac = 0.8105` says *many* units commit, at *minimum*; the meters (nyiso-205, 9-of-9
unanimous g/a) say *few* units run *hard*. Any fill honouring the min-stable half must reach ~81 %
of capacity and therefore the bottom of the stack in **every** binding hour. **`cheapest_first`
resolves that contradiction in the direction the meters support, and pays for it by discarding the
per-unit meaning of `min_stable_pct` while preserving the product's aggregate — which it holds
exactly (max hourly gap 0.0 MW).** So the gap is real and is **reported at full magnitude and not
taken**; the mechanism is nonetheless the best of the three measured; and the **target-level**
question the charter names is **re-specified, not answered**: lowering `floor_pct` scales the
aggregate and does not touch the intensity mismatch, which is structural to *any* aggregate-target
fill.

**Not a keeper candidate. There is nothing to promote, and nothing is proposed.**

---

## 1. The object, and why it is not a cell anyone has already adjudicated

The live limb: `Capital_Hudson` / `ST_GAS` / `tmax` / `31.1 °C`, `floor_pct = 0.0973`,
`min_event_hours = 48`, `exclude_plant_codes` **empty**, `distribution` **empty →
`cheapest_first`** by dataclass default. 24 LP rows, three plants, 2,878.9 MW nameplate.

Three sessions have now worked this limb and each closed a different column:

| session | question | verdict |
|---|---|---|
| nyiso-204 | membership (2480 **+** 8006) | **REFUSED**, two independent grounds |
| nyiso-204b | membership (2480 alone) | **REFUSED**; DO-NOT-REDO covers both forms |
| nyiso-205 | **which** units the floor lands on (`cheapest_first` vs `pro_rata`) | `cheapest_first` **CONFIRMED**, `pro_rata` **REFUTED**; DO-NOT-REDO |
| **nyiso-206 (this)** | **at what level, relative to each row's own physical minimum stable point, the floor is placed on the rows the fill reaches** | **a real gap — and every measured repair is worse** |

**This is not nyiso-205's cell re-tested.** nyiso-205 asked *which* rows carry the floor and
answered it on the meters. This asks *how hard* the fill loads the rows it reaches — a question
about the per-row cap in the fill loop, not about the ordering. **`cheapest_first`'s ordering
remains CONFIRMED and is not re-litigated here**; the PREREG §2 fixed that distinction before any
number was read, precisely so it could not be blurred afterwards. Nothing marked `R`/`I`/`G` on
the NYISO shard was re-tested.

### 1.1 The mismatch, stated from two committed artifacts and no model output

`scripts/data/derive_reliability_coeffs.py`, module docstring — the source of the coefficient:

> `floor_pct = commit_frac x min_stable_pct` … `min_stable_pct` = the class's **physical
> min-stable level (Pmin/Pmax) of a committed unit** … the temperature gate reliability-commits a
> merchant unit on an extreme day; **once committed it sits at this physical Pmin** … `commit_frac`
> = the share of the class's nameplate that is *online* on temperature-flagged days — **a
> commitment count**.

`model/interchange/core.py::_distribute_group_floor` — the delivery:

```python
target = frac * avail_cap.sum(axis=0)          # a ZONAL aggregate
for r in order:                                 # rows sorted by heat rate
    cap_r = pmax[r] * availability[r, :]
    take = np.minimum(remaining, cap_r)         # fill to FULL available capacity
```

**The per-row cap in the fill is `cap_r`, not `min_stable_pct × cap_r`.** That is the whole object,
and it is visible without running anything. What needed measuring is how much of it binds.

## 2. The measurement

Hour sets are built on the engine's own code path (`iso_zone_tmax` → `tmax > 31.1 °C` →
`_bridge_flagged_runs(48)`); the probe **re-verifies the 504 / 432 / 600 binding-hour counts and
aborts on a mismatch** before computing anything, so no off-object number can be written. The
fleet is the keeper bundle's own `fleet_only` reconstruction; the floor is produced by calling the
**shipped** kernel on a row-sliced shim, never re-implemented.

**Two identities were verified before any intensity number was read**, because every number below
is meaningless if either fails:

| year | zonal target | `cheapest_first` delivered | max abs hourly gap |
|---|---:|---:|---:|
| 2023 | 38,635.842 MWh | 38,635.842 | **0.0 MW** |
| 2024 | 75,831.262 | 75,831.262 | **0.0 MW** |
| 2025 | 90,432.081 | 90,432.081 | **0.0 MW** |

and `pmin / pmax = 0.000` for **all 24 rows**, so every raised cell is pure forced energy with no
pre-existing floor underneath it. *(The targets reproduce nyiso-204 §1.1 and nyiso-205 §1 exactly.)*

### 2.1 The result — intensity `i = floor / cap_r` over every raised cell

**Read off the `binding` cut, which is the mask the engine applies.**

| year | raised cells | rows ever raised | `i` mean (cell-wt) | **`i` mean (MW-wt)** | **× min-stable 0.12** | `i` max |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 840 | **5 of 24** | 0.6132 | **0.8710** | **7.26×** | **1.0000** |
| 2024 | 480 | **3 of 24** | 0.7488 | **0.8947** | **7.46×** | **1.0000** |
| 2025 | 1,464 | **4 of 24** | 0.6851 | **0.9579** | **7.98×** | **1.0000** |

Banded by forced energy:

| year | **pinned `i ≥ 0.999`** | above min-stable, not pinned | **at or below min-stable** |
|---|---:|---:|---:|
| 2023 | **74.26 %** | 25.74 % | **0.00 %** |
| 2024 | **14.12 %** | 85.88 % | **0.00 %** |
| 2025 | **81.85 %** | 16.63 % | **1.52 %** |

**Essentially none of the forced energy is delivered at or below the min-stable level the
coefficient asserts** — 0.00 % in two years and 1.52 % in the third. The fill concentrates on
3–5 of the limb's 24 rows and loads them near or at their ceiling.

**It survives every pre-registered cut.** The unbridged `tmax > 31.1` flagged hours and the
h14–21 evening-peak narrowing return the same picture (MW-weighted `i` = 0.8725 / 0.8962 / 0.9623
and 0.8710 / 0.8947 / 0.9579 respectively; pinned energy shares within 1 pt of the binding cut in
every year). **No cut dissents.**

### 2.2 The row-level picture, which is what the aggregate hides

2025's leading row is the clearest case:

| year | row | pmax | HR | raised h | **pinned h** | forced MWh | `i` mean |
|---|---|---:|---:|---:|---:|---:|---:|
| 2025 | 2625 Bowline | 243.5 | 10.695 | 576 | **504** | 66,656.8 | **0.9762** |
| 2025 | 2625 Bowline | 123.7 | 11.043 | 504 | **360** | 19,942.2 | 0.7452 |
| 2023 | 2625 Bowline | 243.5 | 10.695 | 288 | **216** | 26,262.6 | 0.8897 |
| 2024 | 2625 Bowline | 243.5 | 10.695 | 408 | 48 | 74,662.3 | 0.8412 |

A row **pinned at `i = 1.0000` is not floored at a minimum stable level — it is a must-run at full
available output.** In 2025 that is the state of Bowline's cheapest tranche in 504 of 600 binding
hours. **This is also the mechanism behind the unit-grain C8 exposure** the charter carries
forward (`ST_GAS` 0.351 / 0.343 / 0.268 against the 0.30 cap): a handful of rows pinned at their
ceiling is exactly what a unit-grain forced-share statistic is built to see and a plant-grain one
is not. *(Stated as a consistency observation. `DECISION-CARD-nyiso193` stays **UNRULED**; nothing
here rules it, and no scorer file was touched.)*

### 2.3 The `pro_rata` counterfactual is NOT evidence, and the PREREG said so first

`pro_rata` floors every row at `0.0973 × cap_r`, so its intensity is **arithmetically forced** to
`0.0973 < 0.12` for every raised row. It therefore "passes" this test by construction and the
measurement confirms it does. **That is not a result**, it is a restatement of the definition, it
was declared as such in PREREG §4 item 4 before running, and it is **not** an argument for
`pro_rata` — which nyiso-205 refuted on evidence this session does not disturb.

## 3. The repair the coefficient itself describes — and why the meters refuse it

### 3.1 It works exactly as predicted, including the closed form

PREREG addendum §A declared, before running, a min-stable-capped fill: the same merit-ordered fill
with each row capped at `min_stable_pct × cap_r`. It is **feasible by arithmetic** (`0.0973 < 0.12`)
and its committed-capacity share is `floor_pct / min_stable_pct = 0.8108 = commit_frac` **in closed
form**. Measured:

| year | target met | max gap | `i` mean (MW-wt) | `i` max | committed cap share | vs `commit_frac` 0.8105 |
|---|---|---:|---:|---:|---:|---:|
| 2023 | **yes** | 5.7e-14 MW | 0.1188 | **0.1200** | 0.8322 | **+2.7 %** |
| 2024 | **yes** | 8.5e-14 MW | 0.1185 | **0.1200** | 0.8282 | **+2.2 %** |
| 2025 | **yes** | 5.7e-14 MW | 0.1178 | **0.1200** | 0.8357 | **+3.1 %** |

Zero forced energy at the pin, `i` capped at exactly 0.1200, and the same aggregate delivered to
14 decimal places. **The prediction is confirmed in the quantity it governs and OVERSHOOTS in the
proxy, and the overshoot is reported rather than rounded away:** the committed-share statistic
counts the *marginal* row as committed while it is only partly loaded, so it sits 2.2–3.1 % above
the closed form. The energy identity — the thing that actually matters — is exact.

### 3.2 The post-hoc leg that destroys it (PREREG addendum §B)

**Declared post-hoc, because it is.** It was added *after* reading §3.1, precisely because §3.1
makes the counterfactual look good, and the honest move at that moment is to run the test that
could kill it. nyiso-205's **decisive** leg against `pro_rata` was rule 17 `[R-FLOOR-WINDOW]`.
Run on the same meter, the same window and the same statistic:

| year | plant | shipped `cheapest_first` h | **min-stable-capped h** | metered P(on) on those hours |
|---|---|---:|---:|---:|
| 2023 | **2480 Danskammer** | 192 | **504 (100 %)** | **0.125** |
| 2024 | **2480** | 24 | **432 (100 %)** | **0.255** |
| 2025 | **2480** | 0 | **600 (100 %)** | **0.370** |
| 2023 | 8006 Roseton | 24 | 240 (47.6 %) | 0.821 |
| 2024 | 8006 | 0 | 288 (66.7 %) | 0.837 |
| 2025 | 8006 | 24 | 576 (96.0 %) | 0.736 |

**Compare nyiso-205 §3.2's refutation of `pro_rata`, hour for hour: 504 / 432 / 600 at 100 %,
P(on) 0.125 / 0.255 / 0.370. It is the same table.** The min-stable-capped fill **inherits
`pro_rata`'s refutation entire.** And the do-no-harm statistic agrees:

| year | `cheapest_first` | min-stable-capped | ratio | *(`pro_rata`, nyiso-205)* |
|---|---:|---:|---:|---:|
| 2023 | 0.00401 TWh | 0.00718 | **1.79×** | *0.00787* |
| 2024 | 0.01585 | 0.01446 | 0.91× | *0.01545* |
| 2025 | 0.00346 | 0.01431 | **4.13×** | *0.01489* |
| **total** | **0.02332** | **0.03595** | **1.54×** | *0.03822 (1.64×)* |

2024 is again the one year they are level (0.91×), stated plainly rather than averaged away.
**The shipped fill's 0.02332 TWh reproduces nyiso-205 §3.1's 0.02332 exactly** — an independent
instrument agreeing with a prior session's on a number neither was built to match.

**So the repair that restores the coefficient's per-unit meaning manufactures 54 % more energy and
recreates, exactly, the off-window exposure the previous session refused a different mechanism
over.** It is **not proposed**, and PREREG addendum §B fixed that decision rule before the leg was
run.

## 4. Why both results are true at once — the finding under the finding

The two halves of `floor_pct` describe a fleet the meters do not show:

- `commit_frac = 0.8105` asserts **many** units commit on a hot day.
- `min_stable_pct = 0.12` asserts each committed unit sits at **minimum**.
- nyiso-205 measured, 9-of-9 unanimous across every year and cut, that Capital_Hudson steam's
  hot-day commitment is **concentrated by heat rate**: the cheapest plant runs *above* its
  availability share (g/a 1.19–2.01) and both dearer plants *below* (0.15–0.99).

**Few units, running hard — not many units, running at minimum.** Any fill that honours the
min-stable half must therefore commit ~81 % of available capacity and so reach the bottom of the
stack in every binding hour, which is precisely what §3.2 measures. `cheapest_first` honours the
**product** (exactly) and the **metered concentration** (nyiso-205), and pays by discarding the
per-unit reading of `min_stable_pct`.

**Consequently `floor_pct`'s two factors are not separately identified in delivery — only their
product is.** That is the sentence the owner card turns on, and it **re-specifies the
target-level question the charter names**: lowering `floor_pct` rescales the aggregate and leaves
the intensity ratio essentially untouched, because the fill will simply pin fewer row-hours at the
same ceiling. **The level is not the instrument for this gap**, exactly as nyiso-203 §7 found on a
different limb for a different reason.

## 5. Governance

| item | state |
|---|---|
| **LP spent** | **none.** Rule 29 `[R-SCREEN]` step 0 gated the solve to zero; no screen year was pre-registered because no arm was ever on the table (PREREG §5) |
| **Rule 29(b) G-DRIFT** | **re-validated EMPIRICALLY at this HEAD, not by reading hunks**, as the charter requires: `scripts/probes/nyiso198_rebuild_checks.py --year 2024` re-run leaves `git diff` **CLEAN** — the committed `_nyiso198_rebuild_checks_2024.json` regenerates byte-identically. G-CTRL **form 4** valid; **no control solve spent**, and none could be owed since nothing was differenced against a solve. *(That probe prints its own `"VERDICT": "STOP"` — the adjudicated nyiso-198 duct-peaking gate for `cc_duct_peaking_row_scoped`, an `R` cell. Part of the committed record, **not** a drift signal; nothing here re-opens it.)* |
| **Keeper** | `2026-09-06-nyiso-202-startup-aware`, **UNCHANGED**. Not a keeper candidate; no promotion, no re-stamp, no `build_status` / `prune_iso_runs` / gate-(a) re-key owed |
| **Markers** | untouched. `complete` (WITHDRAWN, Q5) and `frontier` re-entry are **owner** acts. Card C-19 / Q51 stays **PARKED** |
| **Rule 1 `[R-STRUCT]`** | no mechanism selected on a residual. NYISO reads **fails 0**; C3c is the ledgered non-downgrading caveat and was **not** an objective. **No metrics file, price series or volume residual was opened at any point in this session.** The `offer_curve_by_group` channel is owner court under carve-out condition (c) and was **not touched** |
| **Rule 21 `[R-DOF]` / 23 `[R-FROZEN-DERIVE]`** | zero fields, zero DOF entries, zero re-derivations. `floor_pct` 0.0973, `commit_frac` 0.8105, `min_stable_pct` 0.12 and the `distribution` column were all **read and none written**. No value is proposed for any of them |
| **Rule 25 `[R-ISO-SCOPE]`** | NYISO only. `_distribute_group_floor` is the shared kernel behind **37 of 50** live program-wide limbs (ERCOT 5/5, MISO 12/12, NEISO 6/6, PJM 14/14 by dataclass default, per nyiso-205's committed census), so **no patch was written and none is proposed from this lane** — the consequences for those five ISOs are **unmeasured and were not measured here** |
| **Rule 22 `[R-HOLDOUT]`** | 2023–2025 only. No out-of-training year solved, scored or registered |
| **Rule 26 / 28 `[R-MECH-MATRIX]`** | NYISO shard `reliability_floor` cell updated **in this session** with this outcome, per duty (b); key set verified identical to `main` before commit |
| **Rule 15 `[R-DASHBOARD]`** | nothing registered — no run finished, so there is no run. Git history + this finding + the card are the record |
| **Files added** | 1 probe, 1 JSON record, 1 PREREG (+2 addenda), this finding, 1 decision card. **No `src/market_sim/` change, no CSV edit, no scorer edit** |

### 5.1 Reported, not fixed — other lanes' pre-existing failures at HEAD

Measured at this session's HEAD across the charter's named files, with this session's tracked
changes being **additive only** (new probe + docs; no tracked file that could affect them was
modified): **37 failed / 68 passed.**

| file | failures | owner |
|---|---:|---|
| `tests/unit/model/test_d62_published_going_forward_bar.py` | 15 | capx |
| `tests/unit/model/test_d74_no_default_cap_convention.py` | 12 | capx |
| `tests/scoring/test_ff_readiness_battery.py` | 4 | FF-readiness |
| `tests/scoring/test_collate_scenario_campaign_common_set.py` | **4** | SCN-WS5A-LOAD |
| `tests/regression/test_constants_facade.py::test_moved_surface_is_complete` | 1 | — |
| `tests/unit/data/test_caiso_st_gas_peak_measured.py` (1.154 vs 1.166) | 1 | CAISO |

**Corrected against the charter's expectation, which was measured at nyiso-205's HEAD as 32 / 62:**
the count has **risen to 37 / 68** because `main` has moved — `test_collate_scenario_campaign_common_set.py`
now fails **4** tests, not 1. **Not fixed from this lane** (rule 25): none is NYISO's file or
NYISO's number, and silently re-baselining another lane's regression constant is how a real
regression gets buried. Reported for their owners.

## 6. What this closes, what stays open, what is deliberately NOT taken

**Closed (negative).** The **min-stable-capped fill** — the only construction the coefficient's own
prose describes, and the one repair with zero free parameters — is **REFUTED** on this limb's own
meters: it recreates `pro_rata`'s refuted rule-17 signature exactly (2480 floored 100 % of binding
hours at P(on) 0.125 / 0.255 / 0.370) and manufactures 1.54× the energy. **DO-NOT-REDO** absent new
measured NYISO conduct data. With nyiso-204 / 204b (membership, twice) and nyiso-205 (fill order),
**all three cheap instruments aimed at the Capital_Hudson D-4 rows are now closed, and so is the
first repair aimed at the fill's per-row cap.**

**Established (positive, and it is the session's substantive result).** The delivered floor sits at
**7.26–7.98×** the min-stable level the coefficient asserts, with 98.5–100 % of forced energy above
it and rows pinned at exactly full availability. **`floor_pct`'s two factors are not separately
identified in delivery — only their product is.** This is documented, sized, and handed to the
owner in `docs/DECISION-CARD-nyiso206-ch-fill-level-basis-2026-09-06.md`.

**Open.** Rule 20 `[R-FORCED-BUDGET]` leg (a), and the unit-grain C8 exposure it rests on
(`ST_GAS` 0.351 / 0.343 / 0.268 against the 0.30 cap, 2 of 3 years) — unchanged by this session,
though §2.2 now names the mechanism that produces it.
`DECISION-CARD-nyiso193-d2-unit-grain-2026-09-05.md` remains **UNRULED**; nothing here rules it.

**Deliberately NOT taken, named so silence is not read as absence.**

- **The shared kernel.** No patch to `_distribute_group_floor`, whose per-row cap is the object.
  37 of 50 program-wide limbs ride it across five other ISOs; rule 25 `[R-ISO-SCOPE]` makes that
  owner court, exactly as `DECISION-CARD-nyiso193` describes for `legitimacy_diagnostics.py`.
- **The TARGET LEVEL** — the charter's named instrument. Not taken, not re-derived, no value
  proposed (rule 23: no source-data trigger). **And now re-specified rather than merely deferred**
  (§4): the level is not the instrument for this gap.
- **A fourth fill operator, or any hybrid.** Not sought, consistent with nyiso-205's charter.
- **Re-litigating the fill ORDER or the membership**, in any refused form.
- **The NYC persistent-base limb's daily-mean-identified / hourly-applied gap** — nyiso-203 §6,
  sized at −0.0087, still awaiting an owner ruling, still not taken. *(This session's gap is the
  same class of defect on a different limb, ~150× larger in relative terms, and the two are now
  presentable to the owner together.)*
- **Measuring the shared kernel's intensity behaviour for any other ISO** (rule 25).

---

*(nyiso-206, 2026-09-06. Zero LP. A real construction gap measured at full magnitude, and a clean
negative on its only zero-parameter repair — which the charter names a full result.)*
