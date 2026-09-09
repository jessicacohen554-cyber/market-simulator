# PRECOMMIT — pjm-177: the ST_GAS net-load drag's HOUR-ELIGIBILITY, persisted across each unit's own minimum run

**Session** pjm-177 · **ISO** PJM · **Date** 2026-09-09 · **Branch** `claude/focused-pasteur-jzys8p`
**Keeper UNCHANGED** `2026-08-15-pjm-162-inputclock`; PJM headline stays **CALIBRATED** (rule 30(c)).
**COMMITTED BEFORE ANY SOLVE.** Every gate bar, the screen year, the confirming instrument and the
control posture below are fixed here and are not re-opened once a number exists.

---

## 0. WHAT IS BEING TESTED, IN ONE SENTENCE

`gas_st_netload_drag` reads its floor fraction off the net-load curve **hour by hour**, so it cycles a
gas-steam boiler on the diurnal net-load wave; `ST_GAS_COMMITMENT_PARAMS` — this repository's own frozen
NREL table — says such a boiler runs a **24 h / 48 h minimum**, and PJM's metered fleet agrees. The arm
replaces the drag's **hour-eligibility** with a centred circular moving average over each row's own
min-run, and **nothing else**.

**This is a SCREEN under rule 29 `[R-SCREEN]`. It may KILL the arm; it may never promote one.**

---

## 1. PHASE 0 — the measured form gap (ZERO LP, and it is the reason a solve is chartered at all)

Sources: raw CAMPD unit-level `opTime`/`grossLoad` (rule 14 `[R-ACCURATE]`) over the keeper's own
ST_GAS census; the keeper's committed `hourly/` sidecars and run payload; and an on-recipe
`run_year(fleet_only=True)` rebuild through `scripts/replay_keeper.run_year_kwargs` (the only sanctioned
reconstruction). **Census check: my raw extraction reproduces the committed bench `campd` series at
hourly r = 1.0000 in all three years** (2024 after dropping Feb 29 — the model clock is 8760), at a
constant gross/net ratio of 1.073 / 1.073 / 1.070; applying that ratio reproduces pjm-176 §6's decile-1
measured figures (646 / 724 / 1,077 MW) to the MW.

| measurement | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured ONLINE capacity, hour-of-day max/min | **1.19** | **1.07** | **1.05** |
| drag mandate, hour-of-day max/min | 3.98 | 3.18 | 2.40 |
| model ST_GAS dispatch, hour-of-day max/min | 5.15 | 4.60 | 3.23 |
| measured ONLINE mask, R² on hour-of-day | **0.003** | **0.001** | **0.001** |
| measured ONLINE mask, R² on net load | 0.338 | 0.362 | 0.365 |
| … of which month alone explains | 0.483 | 0.462 | 0.452 |
| drag mandate, R² on net load | 0.952 | 0.931 | 0.921 |
| ρ(online, net load) **inside** the bottom load decile | **0.143** | **0.154** | **0.275** |
| measured plant-online run length, median h | **25** | **28** | **57** |
| drag binding (frac ≥ 0.20) run length, median h | **7** | **8** | **7** |

**Two falsifiers were run and neither killed the card.** (a) **Steam host**: zero `steamLoad` reported by
any ST_GAS facility in any year — it is not a CHP block. (b) **Membership vs hours**: the measured trough
block has a persistent, heterogeneous membership (Brunner Island 85.2 %, New Castle 63.6 %, Shawville
58.2 %, Big Sandy 53.5 % of load-decile-1 hours online in 2023, against Eddystone 0.9 % and Joliet 29
2.9 %), while the drag commits **every** plant at ~83 % duty in all hours and ~0 % in the trough — a
uniform hourly switch on net load. That is a real second defect and it is **NOT** what this arm fixes;
it is `netload_drag_merit_allocation`'s object and is recorded, not taken.

**Rule 19 `[R-ONE-MECH]` duty discharged.** The keeper's own committed `legitimacy_diagnostics.json`
shows `st_netload_drag` is the **sole** mechanism forcing PJM ST_GAS in D-2 (52.4 / 49.1 / 39.9 % of
class energy) and the sole ST_GAS floor in D-4. There is nothing to stack on; the arm **replaces** its
hour-eligibility.

**Independent corroboration from a committed governance artifact**: D-1 reads `model_offpeak_cv`
0.461 / 0.397 / 0.251 against `actual_offpeak_cv` 0.278 / 0.140 / 0.112 — the model's off-peak ST_GAS is
**1.7–2.8× more variable** than the metered fleet's, the same object on the rubric's own instrument.

**D-4 has LOW POWER here and is not cited as evidence**: `st_netload_drag`'s declared window is `h0-23`,
so `offwindow_share = 0.0` by construction.

---

## 2. THE MECHANISM — `netload_drag_min_run_persistence` (ScenarioConfig, default **False**)

Each floored row's `floor_frac` becomes a **centred circular moving average over that row's own
`min_run_hours`**, re-clipped to `[0, cap]`. Circular because the LP's 8760 clock is cyclic; centred so
the transform is mean-preserving. Same rows, same membership, same `(slope, intercept, cap)`, same
`mech_id`, same availability clip.

- **Zero free parameters** (rules 21/24). The window is `ST_GAS_COMMITMENT_PARAMS` keyed by the row's own
  heat rate — the identical lookup `model.commitment._commitment_params` performs for a legacy
  generator. It **cannot** read `gen.min_run_hours`: every PJM ST_GAS row is a CAMPD bin carrying
  `min_run_hours = 0` (the reason `class_commitment_overrides` exists), so the frozen table is the only
  zero-DOF source. 45 of 48 floored rows resolve to 48 h, 3 to 24 h.
- **Rule 23 `[R-FROZEN-DERIVE]`**: no coefficient moves. This is the driver's FORM, not its numbers.
- **Rule 18 `[R-PHYSICS]`**: eligibility is unit physics, not a class name. Structurally inert on a
  **windowed** floor — only the all-hours ST_GAS applier passes a table — so the CT evening-ramp limb is
  never persisted (fast-start peakers genuinely cycle).
- **Rule 13 `[R-MEASURED]`**: forward-native; NOT in `_BACKCAST_ONLY_OVERLAY_FIELDS`.
- **Rule 25 `[R-ISO-SCOPE]`**: no per-ISO number exists to transfer.
- Registered in `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` in the same commit
  as the field (the nyiso-119 discipline): **off is byte-stable, on hashes distinctly** (verified —
  explicit `False` key == default key; `True` key differs).
- Corroboration, **not** identification: PJM's measured median run lengths are 25 / 28 / 57 h, which
  bracket 24 h / 48 h. The window is taken from the table, never fitted to the measurement.

---

## 3. SCREEN YEAR = **2023**, named here, on MEASURED FOOTPRINT, before any solve

Footprint = the MW of mandate the transform reallocates, measured exactly on the keeper's own fleet
arrays (`fleet_only`, availability clip applied):

| year | mandate now | persisted | Δ | **mean \|Δ\| (footprint)** | total \|Δ\| | load-dec-1 floor |
|---|---|---|---|---|---|---|
| **2023** | 8.809 TWh | 8.848 | **+0.44 %** | **380 MW** | **3.332 TWh** | 4 → **370 MW** |
| 2024 | 8.605 | 8.623 | +0.20 % | 333 MW | 2.914 TWh | 15 → 323 MW |
| 2025 | 11.506 | 11.533 | +0.23 % | 366 MW | 3.203 TWh | 58 → 416 MW |

**2023 is the largest footprint** and is a **TRAINING** year, so no holdout authorization is spent and no
out-of-training year is solved, scored or registered.

**Disclosed coincidence, stated before the solve**: 2023 also carries pjm-171's largest trough leg
(+3.42 $/MWh). The selection criterion is the footprint, and the two orderings differ — footprint ranks
2023 > 2025 > 2024, the trough residual ranks 2023 > 2024 > 2025 — so the footprint is doing the
selecting. Had the residual been the criterion, 2024 would outrank 2025; it does not.

**Reference point the arm is aimed at, NOT a gate**: measured CEMS trough (load-decile-1) is 1,436 MW
online / 567 MW gross (≈528 MW net) generation against a model ST_GAS of 70 MW.

---

## 4. CONTROL POSTURE — a SAME-HEAD control is spent (G-CTRL form 4 is unavailable)

The keeper's recorded `git_sha` is **`457ae04`, which does not resolve at HEAD** (`git cat-file` fails)
and carries no entry in `docs/governance/citation-commit-map.txt`, so the rule-29(b) **G-DRIFT** code
audit **cannot be run at all** against it. Independently, the pjm-177 charter records two LIVE hunks on
the PJM backcast path since the keeper (`f923_gas_price_plausibility_screen`, default True; and
`EGRID_CT_HR_PHYSICAL_FLOOR`), and this session adds its own solve-path change. **Form 4 is VOID and a
same-HEAD control is spent for the screen year.** Both legs run at the same HEAD with exactly one
declared delta (`--netload-drag-min-run-persistence`), sequentially (peak RSS ~13.9 GiB each against a
13.34 GiB cgroup + swap; two concurrent PJM per-plant LPs would OOM).

---

## 5. S-GATES — pre-registered, STOP-ONLY, and NONE of them is the price residual

Rule 1 `[R-STRUCT]` trap, named: **adding ST_GAS overnight lowers the trough price, which is exactly the
direction C3a wants.** C1 / C3a / C3b / D-A are therefore **REPORTED AT FULL MAGNITUDE AND GATE NOTHING,
in either direction.** A gate that reads "did the trough improve" is the fitted-mechanism selection this
rule exists to forbid.

| gate | claim it tests | bar (fixed here) |
|---|---|---|
| **S1 identity** | the LP applies exactly the transform | `max\|armed − independent prediction\|` on ST_GAS `min_gen` ≤ 1e-6 MW; ST_GAS mandate hour-of-day ratio 3.79 → 1.00 |
| **S2 byte-identical off** | no keeper moves | control leg's ST_GAS `min_gen` `array_equal` to the pre-build baseline |
| **S3 footprint confinement** | only the rows the mechanism claims | zero `min_gen` change on any row outside ST_GAS-non-peak |
| **S4a CONFIRMING INSTRUMENT — hour shape** | *"ST_GAS should be ONLINE flat across the day"* | the model's ST_GAS **online-capacity hour-of-day max/min** must FALL toward the measured 1.19 (control 2023: model dispatch 5.15) |
| **S4b CONFIRMING INSTRUMENT — trough mask** | *"ST_GAS should be online in the hours CEMS says"* | in load-decile-1, capacity-weighted overlap must RISE **and** `CEMS-on & model-off` must FALL (control 2023: 1.9 % / 23.9 %) |
| **S4c indiscriminate-commitment guard** | it must not just turn everything on | all-hours hourly r(model-online MW, CEMS-online MW) must NOT FALL (control 2023: 0.283) |
| **S5 D-1 shape (rule 20's own escalation leg)** | forcing must be shape-faithful | `model_offpeak_cv` must FALL toward `actual_offpeak_cv` (control 2023: 0.461 vs 0.278) |
| **S6 collateral** | no non-target load-bearing flip | no C1/C2/C3a/C3b criterion flips PASS → FAIL **other than** by the replay artifacts named in §6 |

**S1–S3 are already satisfied pre-solve** on the keeper's own fleet arrays (S1 to 1.8e-12 MW; S2
`array_equal=True` on `min_gen`/`availability`/`pmax`/net load; S3 exactly 42 of 2,816 rows moved, all
ST_GAS non-peak). They are re-checked on the bundle so the record is the solve's, not the probe's.

**S4a/S4b/S4c are THE gate** — the charter's lesson (c) from pjm-174, whose central claim went untested
until the end. **If S4a or S4b fails, the arm is dead and this session reports that as its result.**

---

## 6. BUDGETED IN ADVANCE — what will look like a failure and is not this mechanism's

- **C8 `forced_share` ST_GAS FAILs on ANY replayed PJM bundle** (control-off 50.6 %, arm 48.6 % on
  pjm-174/175's replays, against the registered keeper's grounded 39.9 %), with D-4 conduct FAILs on
  plants 3131 / 3138 / 3148 / 3775 / 593. **REPLAY-PATH ARTIFACT** — it appears in the control's own gate
  run and is never attributed to a mechanism.
- **C6 reads UNATTESTED** and the determination reads **NOT-YET** on any replay, for procedural reasons
  alone (a replay bundle carries no attestation).
- **ST_GAS is IMMATERIAL to C8 in 2023** (1.4 % of ISO load, below the 2 % floor), so the screen year
  cannot itself demonstrate the rule-20 story; that is a limitation of the screen, stated here rather
  than discovered afterwards.
- **Forced SHARE is expected to RISE.** The transform is mean-preserving on the fraction but the MW moved
  into the trough are forced where the MW removed from the peak were being dispatched economically
  anyway. That is the mechanism working; it is scored on rule 20's shape-and-provenance escalation (S5),
  never waived.
- `scripts/check_mechanism_matrix.py --base origin/main` **already fails on a clean tree** with exactly
  one error, for another lane's unregistered `vre_curtailment_oversupply_allocation` (SPP-51c). This
  session adds **zero** new errors and does not adopt that debt.
- `scripts/run_calibration_full.py --help` **is already broken on `main`** (a stray `%` in a pre-existing
  help string raises `ValueError` in argparse). Verified pre-existing by stash; not touched.

---

## 7. WHAT THIS SESSION WILL NOT DO

- **Not promote.** A screen may kill, never promote; and a 2023-only bundle could not be a keeper anyway
  (rule 16 `[R-ALLYEARS]`).
- **Not register.** Screen and control bundles are gitignored and never reach `main` (rule 29(c)); they
  are **NOT deleted** (rule 31 `[R-RETAIN]`) and the promotion question is put to the owner explicitly.
- **Not touch a holdout year.** 2021/2022 are validation-tier and are not solved, scored or quoted.
- **Not re-fit anything.** If the arm's shape is wrong, the answer is that the form is wrong, not a new
  slope, intercept, cap or window.
