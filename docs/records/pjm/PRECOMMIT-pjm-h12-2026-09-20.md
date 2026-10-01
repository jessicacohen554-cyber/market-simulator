# PRECOMMIT — pjm-h12 card D-3: the CC commitment-feasibility clip (2026-09-20)

**Session:** pjm-h12 · **Branch:** `claude/pjm-h12-midcurve-seam-ar8wcb`
**GATES ARE DECLARED HERE, EX ANTE, BEFORE ANY SOLVE. None is re-read once a number is on the table.**
**Prior cards (both closed, zero LP):** `docs/FINDING-pjm-h12-the-midcurve-rebuild-is-a-clean-rederivation-2026-09-20.md` (D-1),
`docs/ADDENDUM-pjm-h12-the-seam-is-a-variance-compression-2026-09-20.md` (D-2).

---

## 1. The arm

`ScenarioConfig.mustrun_commitment_feasibility_clip = True` on PJM, **single delta**, applied to the
designated keeper's own recipe via `replay_keeper.py --set`. **No code change, no new field, no new
artifact, no CLI addition** — the field already exists (default `False`), is already registered in
`_BACKCAST_ONLY_OVERLAY_FIELDS`, and is already implemented at
`src/market_sim/data/fleet/arrays.py` (~3417).

**What it does.** The per-plant must-run floor asserts a *commitment* — the plant synchronized at its
own CEMS-measured minimum online level. The incumbent clip is `min(cc_mustrun_pmin_mw, pmax ×
availability)`, and because the committed tranche's `cc_mustrun_pmin_mw` **is** its own `pmax`, that
reduces to `tranche pmax × availability` — i.e. the floor inherits the outage derate **linearly**. A
commitment is not linear. Where a dated outage leaves a plant less available capacity than its own
minimum online level, **no configuration the plant has ever operated is feasible**, and `np.minimum`
silently substitutes a smaller, equally infeasible commitment instead of none. The clip zeroes the
floor in exactly those hours and leaves every other hour's incumbent clip untouched.

**Why it is admissible, by rule:**

- **Rule 17 `[R-FLOOR-WINDOW]` gives it its mandate.** "A floor binding in hours its own driver
  evidence says the class is offline is a bug by definition, whatever it does to the residual." The
  keeper's own committed `legitimacy_diagnostics.json` **D-4 FAILS** on `cc_mustrun_per_plant`
  (plants 2393, 7153 floored in hours their own meter reads zero in 83.3 %+ of them).
- **Rule 21 `[R-DOF]` / 24 `[R-REGISTRY]`: ZERO free parameters.** The test is the plant's own
  committed level against its own available capacity, on the same basis the incumbent clip already
  uses. No threshold, share, multiplier, length or plant list.
- **Rule 18 `[R-PHYSICS]`:** eligibility is unit physics ("can this plant carry the configuration the
  floor asserts"), never a class tuple or conduct statistic.
- **Rule 13 `[R-MEASURED]`:** nothing measured enters — both operands are arrays the LP already
  holds, so it regenerates identically in a forecast year and responds to that year's own
  EFOR/maintenance envelope.
- **Rule 19 `[R-ONE-MECH]`:** the ONE floor's clip is **replaced** in the infeasible hours, never
  stacked, and it is scoped by mechanism stamp so no other floor is reachable.
- **Rule 25 `[R-ISO-SCOPE]`:** no number is transferred from any ISO. PJM's matrix cell is **`U`**
  (untested) — verified this session — so there is no DO-NOT-REDO bar (rule 28(a)).
- **Rule 1 `[R-STRUCT]`:** **the arm is promotable on rule 17 alone.** The gates in §4 are
  *falsifiable structural predictions* that test this lane's causal chain — they are **not** the
  promotion bar, and the arm is not selected because a residual moved.

## 2. The causal chain this arm tests

Measured this session, all at zero LP (D-1/D-2 docs above):

1. PJM's model price **amplitude is 29.9–32.9 % of measured**, phase correct (hod *r* 0.87–0.97) —
   from the keeper's own REPORTED-ONLY, band-free `D-A` diagnostic, which no gate catches.
2. The model's fossil fleet **barely turns down**: CC_REGULAR runs at **61.8 %** of its own maximum
   in the *cheapest* measured-DA decile, reaching only 81.2 % in the dearest (coal 34.7 % → 58.0 %).
3. The largest floor in PJM is `cc_mustrun_per_plant` — **188.31 TWh of asserted commitment floor**
   across 416,837 row-hours in 2023 (measured on a `fleet_only` rebuild of the keeper's own recipe).
4. A too-expensive trough under-clears the seam ladder's deep export blocks (the ladder's rungs are
   measured-DA quantiles), producing the **9–13 TWh/yr export shortfall**.
5. Energy not exported must be served domestically ⇒ **COAL_BIT and CC_REGULAR over-generate on C1**.

**One defect, four symptoms.** The arm attacks step 3, which is the only one with a zero-parameter,
rule-17-mandated repair already built.

## 3. Ex-ante footprint census (ZERO LP, already measured)

The clip's own test, applied offline to a `fleet_only` rebuild of the keeper's 2023 recipe
(`scripts/probes/pjm_h12_clip_census.py`):

| year | floored plant-groups | **infeasible groups** | infeasible plant-hours | **floor released** | of CC/ST floor |
|---|---|---|---|---|---|
| 2023 | 69 | **65** | 114,264 | **6.7829 TWh** | 3.60 % of 188.3102 TWh |

**65 of 69 floored plant-groups are infeasible in at least some hours** — this is a systematic
construction defect, not a handful of bad plants. The released MWh is the *floor level* lifted, and
is therefore an **upper bound** on the dispatch change: the LP may still dispatch those units
economically. Remaining years are censused by their own shard before its solve.

## 4. THE GATES — fixed here, before any solve

| gate | bar |
|---|---|
| **G1 — footprint is real** | The armed run's own log line (`mustrun_commitment_feasibility_clip ARMED`) reports **> 0 infeasible plant-hours** in every year. **KILL: if any year reports 0, the arm is inert for that year and is reported as such.** |
| **G2 — census reproduces through the solver** | 2023's released MWh from the armed run's log is within **±20 %** of the 6.7829 TWh censused above. A miss means the offline census mis-modelled the mechanism and every number below is re-derived before use. |
| **G3 — the floor is what binds (STRUCTURAL PREDICTION)** | CC_REGULAR annual energy **FALLS** vs the control in ≥ 5 of 6 years. Directional only; no magnitude bar. |
| **G4 — the trough loosens (STRUCTURAL PREDICTION)** | Mean model price in measured-DA **decile 1 FALLS** vs the control in ≥ 5 of 6 years. |
| **G5 — the seam responds (STRUCTURAL PREDICTION)** | PJM net **export RISES** vs the control in ≥ 5 of 6 years. |
| **G6 — rule 17 is served** | D-4 failures attributable to `cc_mustrun_per_plant` **do not increase** vs the control. |
| **G7 — nothing stacked** | No mechanism id other than `MECH_CC_MUSTRUN_PER_PLANT` / `MECH_ST_GAS_MUSTRUN_PER_PLANT` changes its floored MWh by > 0.5 % vs the control (rule 19). |

**REPORTED AT FULL MAGNITUDE, GATING NOTHING** (rule 1): C1 per-class errors incl. COAL_BIT, the
eight rubric criteria, and the D-A amplitude ratio. **G3–G5 are predictions, not promotion bars** —
if they fail, the arm still repairs a rule-17 defect and the failure is reported as a refutation of
§2's chain, not as a reason to drop a zero-parameter correctness fix. That asymmetry is declared
*here*, ex ante, precisely so it cannot be invented afterwards.

## 5. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — form 4 is **VOID**, a control solve is **EARNED**

`git diff 3b719484…HEAD` over the solve path: **1,800 insertions across 20 files** since the keeper's
`basis_sha`. Every changed hunk classified:

| file(s) | classification | reason |
|---|---|---|
| `pipeline/commitment.py`, `runner.py`, `pipeline/year.py`, `data/gas_st_campaign.py`, `data/floor_mechanisms.py`, `fleet/campd_bins.py` | **INERT** | SOCO's new-ISO branch (`MECH_SOCO_GAS_ST_CAMPAIGN = 25`, purely additive registry entries) — another ISO's branch |
| `pipeline/backcast_config.py` | **INERT** | NYISO/CAISO/NEISO-scoped — another ISO's branch |
| `fleet/eia860.py`, `fleet/assembly.py`, `fleet/__init__.py` | **INERT** | the `measured_st_heat_rates` gate: `ScenarioConfig` default **`False`** and **ABSENT** from the PJM keeper's `run_config.json` and `meta.json` — rule 29(b)'s explicit default-off-and-absent category |
| `model/capacity_evolution/new_entry.py` | **INERT** | capacity evolution — a `mode="backcast"` run never enters it |
| `data/input_completeness.py` | **INERT** | diagnostics accounting |
| **`data/fuel/hubs.py`** | **LIVE** | `_basis_bridge_blackouts` (new, +163) replaces constant-extension across citygate publication blackouts with an HH-basis interpolation. **It is NOT gated by any `ScenarioConfig` flag** — it fires whenever `bridge_all_years and bridge_hh` are present (`hubs.py:1080`). It therefore changes **delivered citygate gas**, which is the *denominator of PJM's entire offer surface* (the mid-curve is an implied-HR multiplier **× delivered gas day**). |

**Consequence, and it is not optional:** one LIVE hunk voids form 4, so **each year's shard solves its
own CONTROL alongside its ARM, at one pinned HEAD**. The keeper's committed bundle is *not* the
control for this arm.

**Second-order finding, recorded rather than absorbed:** this is a **second** latent input drift on
`main` for PJM, exactly parallel to the offer-midcurve rebuild card D-1 found — and like that one, it
lands on every PJM lane that next re-solves. The control solves will measure it as a by-product
(control vs the committed keeper); that number is **reported, not gated**.

## 6. Shard plan (rules 32 / 34 / 36)

- **SIX shards, ONE YEAR EACH** — rule 36 `[R-YEAR-ISOLATION]` (a): no cross-year state, no
  cross-year warm start. Years: **2020, 2021, 2022, 2023, 2024, 2025** (rule 16 `[R-ALLYEARS]`, rule
  34(c): every year PJM carries).
- **Each shard solves TWO legs** (ARM + CONTROL) into two out-dirs, via `replay_keeper.py` against
  its year's source bundle — `pjm_h11_touchpoint_span` for 2020–2022, `pjm_h11_keeper_span` for
  2023–2025. Budget is therefore **~2× a single-year PJM solve and is stated here** rather than
  silently exceeding rule 32(b)'s 20-minute guidance; a shard approaching its budget with no
  artifact **stops and reports** and never pushes a half-written bundle.
- **Every shard PUSHES its full bundle** including `dispatch/<year>_P1.parquet` (rule 34
  `[R-SHARD-PROMOTABLE]` (a)), by appending a `.gitignore` NEGATION for its own out-dir and then a
  **plain `git add`** — never `git add -f`.
- **The parent composes, scores and registers** (rule 32(d)); the parent never solves (rule 32(a)).
- **Bundle names avoid `results/calibration/pjm_h11_{arm,ctl}_*/`**, which `.gitignore` carries at
  directory grain (a `!<bundle>/**` negation under an excluded directory cannot re-include).

## 7. What is NOT in this arm

`mustrun_plant_exclusions` (the lay-up membership correction) is **not armed**: no PJM lay-up census
exists (`data/raw/_processed-legacy/campd_bridge_layup_exclusions_PJM.csv` is absent — only MISO and
NYISO are built), so arming it would require a new derived artifact. It stays `U` and is named here
as the next lever in PJM's queue. `mustrun_layup_window_mask` likewise stays `U`.

Carried open and untouched, as the charter instructed: **Q1** (three truncated ladder rungs), **Q3**
(the MER dual is ungated), **Q4** (the three-year default pair, D-1 §5), **Q5/Q6** (the seam hourly
bar and the quantile-indexed ladder, D-2 §6), and the proposed rule 32(c)(8) addendum.

---

## 8. ADDENDUM — shards launched (2026-09-20, pinned SHA `65ab6205c40a3d5703f084bf747f2b132eee5c28`)

Six shards, one year each (rule 36 `[R-YEAR-ISOLATION]` (a)), each solving ARM + CONTROL at the
pinned SHA because §5's LIVE hunk voids form 4. Parent session
`session_01WbCsWznBof14T4nGCR2z3V` — **the parent ran ZERO LP** (rule 32 `[R-SHARD]` (a)).

| year | source bundle | shard session | branch | out-dirs |
|---|---|---|---|---|
| 2020 | `pjm_h11_touchpoint_span` | `session_01X6W7jxFh92pyN3jZT5mgY7` | `claude/pjm-h12-clip-2020` | `pjm_h12_{ctl,clip}_2020` |
| 2021 | `pjm_h11_touchpoint_span` | `session_01DbUWV5WBmdHnEnuBgsXte3` | `claude/pjm-h12-clip-2021` | `pjm_h12_{ctl,clip}_2021` |
| 2022 | `pjm_h11_touchpoint_span` | `session_01X9cxuDGSnZDRpnqwmiWWg5` | `claude/pjm-h12-clip-2022` | `pjm_h12_{ctl,clip}_2022` |
| 2023 | `pjm_h11_keeper_span` | `session_01Uy7EKjSNH1FX8qesERBYaJ` | `claude/pjm-h12-clip-2023` | `pjm_h12_{ctl,clip}_2023` |
| 2024 | `pjm_h11_keeper_span` | `session_01WAaxKmKyrwbeQx87mLavLY` | `claude/pjm-h12-clip-2024` | `pjm_h12_{ctl,clip}_2024` |
| 2025 | `pjm_h11_keeper_span` | `session_01484AyepkaXi63KGoGkmkKR` | `claude/pjm-h12-clip-2025` | `pjm_h12_{ctl,clip}_2025` |

**Arming route — no code change was needed.** `replay_keeper.py --set
mustrun_commitment_feasibility_clip=true` applies the override on top of the keeper's committed
recipe through the generic channel, which is exactly the single-delta A/B the driver documents. The
field has no CLI flag and is not in `run_year`'s signature; that is why `--set` is the route, and it
is why nothing under `src/` or `scripts/` is touched by this lane.

**Retrievability (rule 34 `[R-SHARD-PROMOTABLE]` (d)/(e)):** every shard pushes BOTH full bundles to
its own branch including `dispatch/<year>_P1.parquet`, so a promotion costs zero re-solves. The
parent verifies `git ls-tree -r <sha> -- <bundle>` returns > 0 files before archiving anything
(rule 33 `[R-SHARD-ARCHIVE]` (a)), and records recovery by FULL SHA, never branch name.
