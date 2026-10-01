# FINDING — pjm-177: the ST_GAS commitment SHAPE was wrong and is now fixed. The trough PRICE is untouched, and that is the result.

**Session** pjm-177 · **ISO** PJM · **Date** 2026-09-09 · **Branch** `claude/focused-pasteur-jzys8p`
**Keeper UNCHANGED** `2026-08-15-pjm-162-inputclock`. PJM headline stays **CALIBRATED** (rule 30(c)).
**Nothing promoted, nothing registered, no holdout year solved in this container.**
**PRECOMMIT** `docs/handoffs/PRECOMMIT-pjm177-st-gas-commitment-persistence-2026-09-09.md` — committed
(`0d4b434b`) **before** either leg was solved; every gate bar, the screen year and the control posture
below were fixed there and are quoted from it unchanged.

---

## 1. RESULT

> **The chartered hypothesis splits cleanly in two, and the split is the finding.**
>
> **The DISPATCH half is CONFIRMED.** PJM's ST_GAS net-load drag cycles gas-steam boilers on the
> diurnal net-load wave; the metered fleet does not cycle them at all. Replacing the drag's
> **hour-eligibility** with a persistence over each unit's own minimum run length — zero free
> parameters, the window read off this repository's own frozen NREL commitment table — moves every
> pre-registered instrument decisively toward the meter. Load-decile-1 online overlap goes
> **1.8 % → 22.0 %**, the hours CEMS says ON and the model says OFF collapse **24.0 % → 3.8 %**, the
> hour-of-day commitment ratio goes **1.80 → 1.02** against a measured **1.11**, and the rubric's own
> D-1 off-peak CV goes **0.462 → 0.188** against a measured 0.278.
>
> **The PRICE half is FALSIFIED, and it is falsified against the direction the residual wanted.**
> The same run moves C3a by **+$0.007/MWh** and the load-decile-1 trough by **−$0.075/MWh** — against
> a trough miss of **+$7.92** (pjm-171 §3). That is **1.0 %** of the defect. Forcing 307 MW of ST_GAS
> into the deepest load decile displaces CC_REGULAR almost one-for-one (**+0.430 vs −0.396 TWh**)
> **without changing which offer is marginal**, so the trough implied heat rate does not move.
>
> **pjm-176 §6 named ST_GAS as "the better object" for the trough IHR defect. On this evidence it is
> the right object for the DISPATCH defect and the wrong one for the PRICE defect.** The two were
> assumed to be the same object; they are not.
>
> **This is the rule 1 `[R-STRUCT]` case in its clean form.** The charter warned that this card was
> "the easiest possible card on which to bank a residual and call it structure". There is no residual
> to bank: the structure improved and the price did not move. What the card leaves is a mechanism that
> is *more faithful to the meter* and *costs* something on C1 — a promotion question for the owner
> (§7), not a fit question.

---

## 2. PHASE 0 — the form gap, on committed and raw measured data (ZERO LP)

Raw CAMPD unit-level `opTime` / `grossLoad` over the keeper's own ST_GAS census (14 plants / 12.29 GW
in 2023), the keeper's committed `hourly/` sidecars and run payload, and an on-recipe
`run_year(fleet_only=True)` rebuild through `scripts/replay_keeper.run_year_kwargs`.

**Census check, and it is exact.** The raw extraction reproduces the committed bench `campd` series at
**hourly r = 1.0000** in all three years (2024 after dropping Feb 29 — the model clock is 8760, the
calendar 8784; r = 0.892 before that repair and 1.0000 after), at a constant gross/net ratio of
1.073 / 1.073 / 1.070. Applying that ratio reproduces pjm-176 §6's decile-1 measured MW
(646 / 724 / 1,077) to the MW. Two plants are nameplate-only in 2023 — Joliet 9 (360 MW) and Yorktown
(882 MW) report `opTime > 0` with **zero** grossLoad all year — so 10.1 % of the class's nameplate is
dead capacity, and it is excluded from every number here.

| measurement | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured ONLINE capacity, hour-of-day max/min | **1.19** | **1.07** | **1.05** |
| drag mandate, same axis | 3.98 | 3.18 | 2.40 |
| model ST_GAS dispatch, same axis | 5.15 | 4.60 | 3.23 |
| measured ONLINE mask, R² on hour-of-day | **0.003** | **0.001** | **0.001** |
| measured ONLINE mask, R² on net load | 0.338 | 0.362 | 0.365 |
| … month alone | 0.483 | 0.462 | 0.452 |
| drag mandate, R² on net load | 0.952 | 0.931 | 0.921 |
| ρ(online, net load) **inside** the bottom load decile | **0.143** | **0.154** | **0.275** |
| measured plant-online run length, median h | **25** | **28** | **57** |
| … share of runs ≥ 24 h / ≥ 72 h | 54 / 24 % | 57 / 31 % | 68 / 45 % |
| drag binding (frac ≥ 0.20) run length, median h | **7** | **8** | **7** |
| … share ≥ 24 h | 2.7 % | 5.9 % | 8.5 % |

**The defect is an INTERNAL INCONSISTENCY, not a residual observation.**
`config.constants.ST_GAS_COMMITMENT_PARAMS` (NREL/SR-5500-55433, Kumar et al. 2012) states in this
repository that a gas-steam boiler runs a **24 h** (efficient) or **48 h** (older subcritical) minimum,
*"because a stop-start is dearer than idling at minimum load over a sustained event"*. The mechanism
that decides when those boilers are committed cycles them with a median binding excursion of 7–8 h.
PJM's meter sides with the table.

**Two falsifiers were run; neither killed the card.**
1. **Steam host** — **zero** `steamLoad` reported by any ST_GAS facility in any of the three years. It
   is not a CHP block.
2. **Membership vs hours** — the measured trough block has a persistent, heterogeneous membership
   (2023 load-decile-1 online: Brunner Island 85.2 %, New Castle 63.6 %, Shawville 58.2 %, Big Sandy
   53.5 %, against Eddystone 0.9 % and Joliet 29 2.9 %), while the drag commits **every** plant at
   ~83 % duty in all hours and ~0 % in the trough. That is a real second defect — the ercot-259
   allocation object — and it is **NOT** what this arm fixes. Recorded, not taken.

**Rule 19 `[R-ONE-MECH]` discharged from committed artifacts**: the keeper's own
`legitimacy_diagnostics.json` shows `st_netload_drag` is the **sole** mechanism forcing PJM ST_GAS in
D-2 (52.4 / 49.1 / 39.9 % of class energy) and the sole ST_GAS floor in D-4. Nothing to stack on; the
arm **replaces** hour-eligibility.

**D-4 has low power here and is not cited as evidence** — `st_netload_drag`'s declared window is
`h0-23`, so `offwindow_share = 0.0` by construction, exactly as the charter warned.

---

## 3. THE MECHANISM — `netload_drag_min_run_persistence`, default **False**

Each floored row's `floor_frac` becomes a **centred circular moving average over that row's own
`min_run_hours`**, re-clipped to `[0, cap]`. Same rows, same membership, same `(slope, intercept,
cap)`, same `mech_id`, same availability clip. Circular because the LP's 8760 clock is cyclic; centred
so the transform is mean-preserving.

- **Zero free parameters** (rules 21/24). The window is the frozen heat-rate-keyed table — the
  identical lookup `model.commitment._commitment_params` performs for a legacy generator. It **cannot**
  read `gen.min_run_hours`: **every PJM ST_GAS row is a CAMPD bin carrying `min_run_hours = 0`** (the
  reason `class_commitment_overrides` exists), so the table is the only zero-DOF source. 45 of 48
  floored rows resolve to 48 h, 3 to 24 h.
- **Rule 23** — no coefficient moves. This is the driver's FORM, not its numbers.
- **Rule 18** — eligibility is unit physics. Structurally inert on a **windowed** floor (only the
  all-hours ST_GAS applier passes a table), so the CT evening-ramp limb is never persisted.
- **Rule 13** — forward-native; NOT in `_BACKCAST_ONLY_OVERLAY_FIELDS`.
- **Rule 25** — no per-ISO number exists to transfer.
- Cache key registered in the same commit as the field (nyiso-119 discipline): explicit `False` hashes
  identically to the default; `True` hashes distinctly.
- **Corroboration, never identification**: PJM's measured median run lengths (25 / 28 / 57 h) bracket
  24 h / 48 h. The window is read off the table, not fitted to that.

---

## 4. THE SCREEN — 2023, arm vs a SAME-HEAD control, one declared delta

Screen year **2023**, named in the PRECOMMIT on the mechanism's own measured footprint (mean |Δ| of the
reallocated mandate: **380 MW** 2023, 366 MW 2025, 333 MW 2024), a **training** year. The footprint
ranking (2023 > 2025 > 2024) differs from the trough-residual ranking (2023 > 2024 > 2025), so the
footprint is doing the selecting.

**Control posture.** The keeper's recorded `git_sha` `457ae04` **does not resolve at HEAD** and has no
entry in `docs/governance/citation-commit-map.txt`, so G-DRIFT could not be run against it and G-CTRL
form 4 is void; a same-HEAD control was spent. **It earned itself**: the control reproduces the keeper
on every class to ≤0.25 % *except* **CT_PEAKER −2.34 %** (19.363 → 18.911 TWh) — HEAD drift in a class
this mechanism never touches, which form-4 differencing would have charged to the arm.

### 4a. Pre-registered gates — ALL CLEAR

| gate | claim | control | arm | bar | verdict |
|---|---|---|---|---|---|
| **S1** identity | the LP applies the transform | \|armed − independent prediction\| = **1.8e-12 MW** | ≤1e-6 | **PASS** |
| **S2** byte-identical off | no keeper moves | `min_gen`/`availability`/`pmax`/net-load `array_equal` to the pre-build baseline | exact | **PASS** |
| **S3** footprint confinement | only the rows it claims | **42** floored rows move, all ST_GAS non-peak, of 2,816 | 0 elsewhere | **PASS** |
| **S4a** hour shape | ST_GAS online should be flat | **1.801** | **1.017** | fall toward measured **1.11** | **PASS** |
| **S4b** trough mask | online in the hours CEMS says | overlap **1.79 %** | **22.02 %** | rise | **PASS** |
| **S4b** | | CEMS-on & model-OFF **24.02 %** | **3.79 %** | fall | **PASS** |
| **S4c** indiscriminate-commitment guard | not just "turn everything on" | r **0.286** | **0.370** | must not fall | **PASS** |
| **S5** D-1 shape | forcing must be shape-faithful | cv 0.462 / ratio 1.663 | **0.188 / 0.678** | fall toward actual 0.278 / 1.0 | **PASS** |

### 4b. REPORTED AT FULL MAGNITUDE — gates nothing, in either direction (rule 1)

| quantity | control | arm | Δ | actual |
|---|---|---|---|---|
| C3a system load-weighted mean $/MWh | 31.418 | 31.426 | **+0.007** | 29.58 |
| load-decile-1 (trough) $/MWh | 25.604 | 25.529 | **−0.075** | — |
| load-decile-10 (peak) $/MWh | 35.768 | 35.904 | +0.136 | — |
| D-A hour-of-day price range $/MWh | 7.067 | 7.313 | +0.246 | 22.71 |
| **C1 ST_GAS annual TWh** | 10.821 | **11.251** | **+0.430** | **8.883** |
| C1 CC_REGULAR annual TWh | 322.668 | 322.272 | −0.396 | 325.670 |
| C1 CT_PEAKER annual TWh | 18.911 | 19.027 | +0.116 | 21.663 |
| ST_GAS load-decile-1 mean MW | 64.8 | **371.6** | +306.8 | ≈528 (net) |
| D-2 ST_GAS forced share | 0.644 | 0.666 | +0.022 | — |

C3a vs actual: control **+6.22 %**, arm **+6.24 %** (band ±10 %).

---

## 5. THE COSTS, STATED AT THE GATE AND NOT MINIMISED

1. **C1 ST_GAS gets worse.** The class was already **+21.8 %** over actual (10.821 vs 8.883 TWh) and
   goes to **+26.7 %** (11.251). ST_GAS is immaterial to C8 in 2023 (1.4 % of ISO load, below the 2 %
   floor) so nothing gates it *in this year* — but 2025 is material and grounded-above-budget at
   39.9 %, and this mechanism pushes forced share up (+2.2 pts here). A full-span run must be read on
   2025's C8, not on 2023's silence.
2. **The flattening OVERSHOOTS the meter.** D-1 `model_offpeak_cv` lands at **0.188** against a measured
   **0.278** — the model's off-peak ST_GAS is now *less* variable than the real fleet, where it was
   1.66× *more* variable. `cv_ratio` 0.678 still clears D-1's 0.50 floor, but by 0.178. The dispatch
   hour-of-day ratio moves 5.18 → 1.81 against a measured 2.31, i.e. from 2.24× too peaky to 0.78× too
   flat. A 24/48 h moving average removes **100 %** of the diurnal component where the measurement says
   ~99 % should go, and it raises the low-frequency share (week-of-year R² 0.578 → 0.865 against a
   measured 0.715). `profile_r` degrades 0.974 → 0.883 (gate 0.8).
3. **The pro-rata allocation defect is amplified, not fixed.** All-hours model online duty rises
   **65.8 % → 77.5 %** against a measured **31.4 %**. The uniform fleet fraction still commits every
   plant identically; persistence makes it do so in more hours. S4c rises anyway (0.286 → 0.370), so
   agreement improved despite this — but the honest reading is that the HOURS are now right and the
   PLANTS are still wrong. That is `netload_drag_merit_allocation`'s object (ercot-259, **U** for PJM),
   and the two would have to compose to close the mask properly.

---

## 6. WHAT IS NOT CLAIMED

- **No price improvement is claimed, and none was found.** −$0.075/MWh on the trough is inside the
  noise of a re-solve and is ~1 % of the miss. Any future session that quotes this card as a price
  lever is misquoting it.
- **No holdout year was solved, scored or registered in this container.** The 2020–2022 validation
  ladder is authorized (PJM holds `complete`) and is running in a parallel shard; the locked test
  (2019, H1-2026) is **refused** — PJM is absent from `final` and the tier is frozen for every ISO.
- **The DEMAND-SERIES defect is reported, not fixed, and it is not this card's.** `data/clean/` in a
  fresh PJM container carries no repaired `demand-profile` partition, so the loader falls back to a
  series it calls corrupted (`PR #1426`). **The registered keeper was solved on that fallback**: its
  committed 2023 hourlies read peak 147,605 MW / 784.82 TWh, which my control reproduces exactly — so
  this A/B is on the keeper's own basis and is unaffected. Whether the *repaired* series would move
  PJM's keeper is a live **rule 14 `[R-ACCURATE]`** question, opened here and answered by nobody.
  PJM **2021 is unsolvable** on the fallback: its peak reads **2,147,480,000 MW**, an int32 sentinel.
  (Found by the parallel shard during prep; `docs/handoffs/PREP-pjm177b-phase1-2026-09-09.md`.)
- **The S4 masks carry a stated resolution bound**: a plant counts as model-online at ≥1 % of
  nameplate, matching the payload codec's own quantization. The model's trough ST_GAS is 64.8 MW in
  the control, so its trough absence is real and not a codec artifact.
- **`--help` on `run_calibration_full.py` is broken on `main`** (a stray `%` in a pre-existing help
  string raises in argparse). Verified pre-existing by stash; not touched, not this card's.

---

## 7. DISPOSITION — and the promotion question is the OWNER'S (rule 31 `[R-RETAIN]`)

Keeper `2026-08-15-pjm-162-inputclock` and PJM's **CALIBRATED** headline are **UNCHANGED**. A
2023-only bundle could not be a keeper in any case (rule 16 `[R-ALLYEARS]`), and a screen may kill an
arm but never promote one (rule 29 `[R-SCREEN]`).

**The question put to the owner, explicitly, because a screen cannot answer it:** rule 1
`[R-STRUCT]` says a structurally-correct mechanism stays in even when it does not help the fit — and
this one is structurally correct on its own confirming instrument, measured against the meter, with
zero free parameters. It also makes C1 ST_GAS worse and overshoots D-1 past the measured value. Those
two facts do not resolve each other, and the rule does not decide it either way. **Promote to a full
2023–2025 span, or leave the field on `main` default-off?**

The field is already on `main` (PR #5712), **default off and byte-identical off**, so leaving it costs
nothing while unarmed. If the answer is "no", the honest follow-up is a rule 26 `[R-DELETE]` question
rather than a dormant flag.

**Bundles.** `results/calibration/pjm177_control_2023/` and `pjm177_arm_2023/` are **gitignored**
(rule 29(c) discharged in full) and were **NOT deleted** (rule 31). They are on local disk in an
ephemeral container and **will not survive its reclamation**; every number this session will ever cite
is in this document, per rule 29(c).
