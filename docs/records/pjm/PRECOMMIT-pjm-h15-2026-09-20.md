# PRECOMMIT — pjm-h15: the COVERED coal cohort's window is a 2023–2025 POOLED VINTAGE asserted on every solve year. Test `coal_sync_online_frac_per_year` (2026-09-20)

**Session:** pjm-h15 · **Branch:** `claude/pjm-h15-calibration-xbefei` · **ZERO LP IN THE PARENT**
(rule 32 `[R-SHARD]` (a)). Six shards, **one year each** (rule 36 `[R-YEAR-ISOLATION]` (a)).
**Keeper under test:** `2026-09-20-pjm-h14-coalmustrun-span` (2023–2025, CALIBRATED, 8/8 PASS, zero
caveats) + folded touchpoint `2026-09-20-pjm-h14-coalmustrun-touchpoint` (2020–2022, NOT-YET).
Bundles `results/calibration/pjm_h14_coalmustrun_{span,touchpoint}`, basis SHA `3b44a752`.

**EVERY GATE BELOW IS FIXED BEFORE ANY SOLVE AND IS NEVER RE-READ ONCE A NUMBER LANDS.**

---

## 0. The chartered lever, and where phase 0 took it (rule 28(a))

The handoff's **LEVER A** was *"the COVERED cohort's pooled-vintage limb … the admissible form is a
NEW per-year companion artifact (miso-172's `mustrun_online_frac_per_year` is the exact precedent),
never an edit to the committed file."* Phase 0 took it exactly there and **narrowed it**, because the
handoff's framing was imprecise in one load-bearing way: it cited the drift in `mustrun_online_pct`
and `pct_committed` (the tranche LEVEL columns), and those are **not** what miso-172's precedent
corrects. The precedent corrects `online_frac` — the **WINDOW**, i.e. how many hours of the year the
floor is held — and that is the column whose vintage this card moves. The level columns stay frozen
(rule 23 `[R-FROZEN-DERIVE]`, and xiso-5's refusal to regenerate `thermal_tranches_PJM.csv` is
untouched and not needed).

**The lever queue check (rule 28(a)).** `mustrun_online_frac_per_year` reads `U` in PJM's shard with
an explicit prerequisite note — *"this ISO must first HAVE the per-year artifact (only MISO does
today)"*. That prerequisite is discharged here. `mustrun_window_commitment_grain` also reads `U` and
is **deliberately not taken** (§6). Nothing adjudicated `R`/`I`/`G` is re-tested.

---

## 1. The defect, stated as a fact about a committed file and named plants

`data/raw/_processed-legacy/thermal_tranches_PJM.csv` publishes **ONE** `online_frac` per coal plant.
`assembly.py:542` stamps it onto the generator as `coal_sync_online_frac`, and
`arrays.py::_compose_min_gen_floors` applies it as **that solve year's** commitment window: the floor
is held in the top `online_frac × 8760` hours ranked by system load (or all 8,760 at
`_COAL_SYNC_FORCE_ALL = 0.99`).

**The artifact's derive window is 2023–2025 — re-established here, not assumed.** Re-running that
window through the **FROZEN** deriver (`derive_thermal_tranche_online_frac_by_year.py`, which
*imports* `derive_thermal_tranches` rather than restating it) and summing its per-year counts
reproduces the committed `online_frac` column on **168 of 168 rows, 0 mismatched** (`--verify-pooled`).
That is the rule-23 identity: **the grain refinement is exact and no committed value moves.**

So **2020–2022 are windowed on a share measured in years those plants had not yet reached**, and each
of 2023/2024/2025 carries the other two years' average. Measured, own-year minus pooled, on the 29
covered PJM coal plants (`scripts/probes/pjm_h15_coalwindow_phase0.py` §1):

| plant | pooled | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 3118 | 0.520 | **0.951** | **0.863** | 0.673 | 0.517 | 0.590 | 0.452 |
| 3136 | 0.413 | **0.906** | **0.944** | 0.666 | 0.362 | 0.415 | 0.461 |
| 6004 | 0.319 | 0.665 | **0.898** | **0.943** | 0.610 | **0.191** | **0.157** |
| 50888 | 0.684 | **0.013** | **0.126** | 0.551 | 0.671 | 0.656 | 0.726 |
| 7213 Clover | 0.314 | 0.343 | 0.305 | **0.179** | **0.102** | 0.324 | 0.516 |
| 10343 | 0.326 | 0.162 | **0.009** | 0.468 | 0.436 | 0.216 | — |

**Plant 50888 is the statement of the defect**: floored across **68.4 %** of 2020 by a fraction
measured three years later, in a year whose own meter says it synchronized in **1.3 %** of the hours.
Rule 17 `[R-FLOOR-WINDOW]` fails on clause (b) — the hours it may bind, and why — and rule 14
`[R-ACCURATE]` says prefer the measured quantity over an estimate standing in for it.

**The error is largest exactly where the model fails.** Max |own − pooled| by year: **0.671 (2020),
0.579 (2021), 0.624 (2022)** against 0.291 / 0.128 / 0.236 in 2023–2025 — the in-window years are
near-exact by construction and the out-of-window years drift. PJM's rubric failures are entirely in
2020–2022.

## 2. The mechanism

`coal_sync_online_frac_per_year` (`scenarios.py`, dataclass default **`False`**). Armed, a coal
plant's synchronization window is sized by the **solve year's own** measured fraction from
`thermal_tranches_online_frac_by_year_PJM.csv` instead of the pooled column. **One seam** —
`arrays.py::_compose_min_gen_floors`, the `coal_sync_any` block, at the existing
`frac = gen.coal_sync_online_frac` line.

- **Its OWN gate, not a widening of `mustrun_online_frac_per_year`** (rule 19 `[R-ONE-MECH]`,
  rule 28(d)). The gas seams are `MECH_CC_MUSTRUN_PER_PLANT` / `MECH_ST_GAS_MUSTRUN_PER_PLANT` and
  read `cc_mustrun_online_frac`; coal is `MECH_COAL_MUSTRUN` and reads `coal_sync_online_frac`. The
  gas field's own comment says so in terms: *"The COAL synchronization floor
  (`coal_sync_online_frac`) and the CT_PEAKER floors keep the hour grain — they are separate
  mechanism ids whose own conduct evidence this gate does not carry."* Separate ids ⇒ separate D-4
  evidence ⇒ separate gate and separate matrix cell.
- **Rule 21 `[R-DOF]`: ZERO free parameters.** No threshold, no share, no multiplier. The value is
  the same measured count ratio at a finer grain.
- **Rule 23 `[R-FROZEN-DERIVE]` NOT ENGAGED.** The frozen deriver is imported, not touched;
  `thermal_tranches_PJM.csv` is not regenerated; xiso-5's refusal stands and this card does not need
  it. The companion artifact is **additive**, and its pooled sum reproduces the committed column
  exactly (§1).
- **Rule 13 `[R-MEASURED]`: BACKCAST ONLY**, registered in `_BACKCAST_ONLY_OVERLAY_FIELDS` and
  gated again in the engine on `mode == "backcast"`. A forecast year keeps the pooled multi-year
  fraction — the same estimator's own forward form, which re-derives as each CEMS vintage lands.
- **Rule 19: the window VINTAGE is replaced, never stacked.** Tranche SIZE, floor LEVEL, membership
  and the `pmax × availability` clip are untouched, and no second floor is placed. Membership stays
  on the POOLED artifact: a plant reaches the seam only by carrying `coal_sync_pmin_mw > 0`, and a
  plant with **no own-year row keeps its pooled fraction** — the arm can never remove a floor for
  want of a measurement. The one deliberate membership consequence is the gas sibling's: an own-year
  fraction of **zero** means the meter says the plant never synchronized that year.
- **Rule 24 `[R-REGISTRY]` / nyiso-119 discipline:** registered in `_CACHE_KEY_OPTIONAL_FIELDS` +
  `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` **in the same commit as the field**. Verified against
  `origin/main`: the default cache key is **byte-identical** (`e8adfaefa24f1b4f`; PJM backcast
  `c8a2ffdeca6546a6`) and the armed key is distinct (`a716f2153909a0d0`).
- **Rule 25 `[R-ISO-SCOPE]`:** gated default off; the artifact is per-ISO; **no registered keeper in
  any ISO arms `mustrun_online_frac_per_year` or this field** (audited across all 18 committed
  `run_config.json`), so no other ISO's keeper moves. PJM's cell enters as its own test.
- **The artifact carries non-coal rows** (CC_REGULAR 401, CT_PEAKER 419, ST_GAS 60, COAL 233). They
  are inert: the gather filters on `plant_group == "COAL"`, and PJM's recipe leaves
  `mustrun_online_frac_per_year` False. **The gate is what scopes it, not the file.**

## 3. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — form 4 is VALID, NO control solves

Audit window `3b44a752` (the keeper pair's `basis_sha`) → `f083eb32` (`origin/main`, this branch's
base). Six files changed on the backcast solve path; **every hunk classifies INERT for PJM**:

| file | hunks | classification |
|---|---|---|
| `config/scenarios.py` | two new fields + their registrations | default-off, **absent from the PJM keeper's recipe** |
| `data/fleet/__init__.py` | `Generator.chp_grid_pmin_on_frac: float = 1.0` | new field at its neutral default |
| `data/fleet/arrays.py` | the CHP block restructured for `chp_steam_duty_window` | at `on_frac == 1.0` (the default, and what every unarmed run gets) the new branch executes `min_gen[g,:] = pmin_mw; min_gen_mech[g,:] = MECH_CHP_STEAM` — **line-for-line the removed code**, and `_chp_any_windowed` is False so `_chp_rank_key is None` |
| `data/fleet/assembly.py` | `chp_duty_on_frac = 1.0`, override inside `if config.chp_steam_duty_window` | default-off branch |
| `data/fleet/campd_bins.py` | a docstring correction + the NEW `thermal_tranche_chp_steam_duty` loader | called only from the armed path |
| `data/renewables.py` | `vre_reference_rate_year_own` + `_spp_wind_*` readers | default-off **and** another ISO's branch (SPP's own curtailment table) |

**All hunks INERT ⇒ form 4 is valid and the keeper pair's committed bundles ARE the control.**
Six arm shards, **no control solves**. (`chp_steam_duty_window` and `vre_reference_rate_year_own` are
both **absent from the PJM keeper's `scenario_config`**, checked, so they cannot even be re-armed by
`replay_keeper`'s config carry.)

**Control config signature (both bundles), which every shard must echo back:**
`mode=backcast`, `use_campd_bins=True`, `coal_mustrun_per_plant=True`,
`coal_mustrun_online_pmin=True`, `coal_sync_srmc_tranche=True`, `coal_bit_passthrough_sigmoid=True`,
`netload_drag_merit_allocation=True`, `coal_mustrun_requires_measured_row=True`,
`mustrun_online_frac_per_year=False`, `mustrun_plant_exclusions=False`,
`mustrun_commitment_feasibility_clip=False`, `pjm_da_virtual_bids=True`, and
**`coal_sync_online_frac_per_year` ABSENT on the control / `True` on the arm.**

## 4. THE GATES — declared ex ante, never re-read

**Baselines, read off the incumbent keeper pair's own committed artifacts:**

| C1 error (TWh) | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| **COAL_BIT** | +25.422 | +19.486 | +2.738 | +0.650 | −1.654 | +7.449 |
| **CC_REGULAR** | +2.634 | +1.470 | +11.782 | +4.167 | +1.047 | +3.087 |

- Determination: span **CALIBRATED**, eight criteria PASS, zero caveats; touchpoint **NOT-YET**.
- D-4 `coal_mustrun` unit-conduct **FAIL** rows on the control: 

| control FAIL row | floored TWh | binding h | measured median MW | pooled → own-year frac | in G3's population? |
|---|---:|---:|---:|---|---|
| **2020 / 1040** Whitewater Valley | 0.0015 | 105 | 0.0 | 0.093 → 0.102 (**+0.009**) | **no** |
| **2021 / 7213** Clover | 0.0003 | 30 | 0.0 | 0.314 → 0.305 (**−0.009**) | **no** |
| **2023 / 1384** Cooper | 0.1900 | 2,499 | 0.0 | 0.318 → 0.337 (**+0.019**) | **no** |
| **2023 / 7213** Clover | 0.3656 | 2,672 | 0.0 | 0.314 → **0.102** (**−0.212**) | **YES** |

  **Total control coal conduct FAIL energy: 0.5574 TWh.** These four rows are re-derived by this
  lane over the two committed keeper bundles at this HEAD (`legitimacy_diagnostics.py --only D4`),
  because the touchpoint bundle ships **no** `legitimacy_diagnostics.json` — an artifact gap in the
  incumbent, reported not absorbed. **One discrepancy against pjm-h14's RESULT, disclosed:** that
  doc names *five* failures including 7213/2022, which re-reads as **pass** here (48 binding hours,
  median 25.443 MW, zero-share 0.500 — a 0.004 TWh row on the edge of the test). This PRECOMMIT's
  baseline is the re-derivation, which is what the arm will be differenced against.

| gate | bar | kills the card if |
|---|---|---|
| **G1 — the arm fires** | the arm's D-2 `coal_mustrun` forced **TWh** differs from the control's by > 0 in **every** year | it is inert |
| **G2 — SCOPE: nothing outside the coal seam is touched** | no D-2 mechanism id outside `{coal_mustrun}` moves its forced **TWh** by more than **0.05 TWh** in any year | the arm reaches past its own seam (rules 19/25) |
| **G3 — RULE 17 IS SERVED on the population this card can reach** *(this lane's justification gate)* | **(a)** every control D-4 `coal_mustrun` conduct FAIL row **whose own-year fraction is lower than pooled by ≥ 0.05** either clears to `pass` or has its `floored_twh` cut by **≥ 50 %**; **AND (b)** the arm's total coal conduct FAIL `floored_twh` over all six years is **≤ 0.5574 TWh** (the control's) | the card's own justification fails |
| **G4 — no NEW conduct failure** | the arm adds **zero** D-4 `coal_mustrun` conduct FAIL rows the control does not already carry | widening a window where the meter says the plant WAS synchronized convicts a plant that previously passed |
| **G5 — WINDOW ONLY, never capacity or level** | on a zero-LP `fleet_only` build under the arm config, every coal generator's `pmax_mw` **and** `coal_sync_pmin_mw` are unchanged from the control to **< 1e-6 MW**, in every year | it is secretly a tranche-sizing or level change rather than a window change |

**G3's population is FIXED BY RULE HERE, and enumerated below before any solve** (this is the pjm-h14
correction the lane owes: pjm-h14 wrote its G3 absolutely over all coal when its card's population
was a subset, and the gate failed on rows the arm never touches). The rule is: a control FAIL row is
in scope **iff** `own_frac(plant, year) ≤ pooled_frac(plant) − 0.05`. It selects:

**It selects EXACTLY ONE ROW: `2023 / 7213` (Clover), pooled 0.314 → own-year 0.102.** That is
narrow, and it is narrow *correctly*: the other three FAIL rows have an own-year fraction that is
**not lower** than pooled (+0.009, −0.009, +0.019), so this card's mechanism cannot move them and a
gate that demanded it would be testing a claim the card never made. **7213/2023 is nevertheless
65.6 % of the control's total coal conduct FAIL energy** (0.3656 of 0.5574 TWh), so the one row is
not a trivial one.

Because a one-row leg is thin, G3 carries a **second leg over the whole coal seam**, which can
genuinely fail if widened windows convict plants that previously passed:

- **G3a** — `2023 / 7213` clears to `pass`, **or** its `floored_twh` falls by ≥ 50 % (0.3656 → ≤ 0.1828).
- **G3b** — the arm's **total** D-4 `coal_mustrun` conduct FAIL `floored_twh`, summed over all six
  years, is **not greater** than the control's **0.5574 TWh**.

Both legs must hold for G3 to pass.

**G3 is this lane's justification gate** — written to test the card's own claim, which is what
caught pjm-h12's charter and what pjm-h13's and pjm-h14's G3s were.

**G2's family scoping** (pjm-h14 correction #6, discharged before the solve). The appliers this flag
reaches are enumerated now: the single seam `arrays.py::_compose_min_gen_floors`, `coal_sync_any`
block, and nothing else — `coal_sync_pmin_mw` and `coal_sync_online_frac` are stamped upstream in
`assembly.py` and are **not** touched. **The coal must-run family is therefore `{coal_mustrun}`**;
every other D-2 id is "outside". The bar is stated in **absolute TWh, not share**, because pjm-h14's
G5 failed on a denominator move in a 1.7 TWh class — a share can move when nothing was stacked.

### 4.1 THE ASYMMETRY — what is REPORTED and can never move a gate (rule 1 `[R-STRUCT]`)

Written down **before** the solve, so no number can be re-read into a criterion:

- **Every scored band — C1, C2, C3a, C3b, C3c, C4, C8 — and the determination itself.** A
  structurally-correct mechanism **stays in even if the residual worsens**, and nothing here is
  selected because a residual moved.
- **AND THE EXPECTED DIRECTION ON C1 IS ADVERSE IN 2020–2022, STATED NOW, ON THE OPERAND THAT
  CANNOT HIDE BEHIND A MOVING DENOMINATOR** (pjm-h14 correction #6: forced **energy**, never a
  share). Asserted coal-floor energy, pooled → own-year, measured off the model's own fleet:

  | year | asserted TWh, pooled | own-year | Δ TWh | Δ % |
  |---|---:|---:|---:|---:|
  | 2020 | 52.155 | 56.533 | **+4.377** | **+8.39** |
  | 2021 | 52.155 | 59.060 | **+6.904** | **+13.24** |
  | 2022 | 52.155 | 57.012 | **+4.856** | **+9.31** |
  | 2023 | 52.155 | 50.695 | −1.460 | −2.80 |
  | 2024 | 52.155 | 51.634 | −0.521 | −1.00 |
  | 2025 | 52.271 | 54.194 | +1.923 | +3.68 |

  **The arm ADDS asserted floor in 2020–2022 — exactly the years the model already over-runs
  COAL_BIT (+25.422 / +19.486 / +2.738 TWh).** The cause is plain in the per-plant table: Conemaugh
  (0.520 → 0.951 in 2020), Keystone (0.413 → 0.944 in 2021), Pleasants (0.319 → 0.943 in 2022) and
  Gavin ran hard in 2020–2022 and wound down afterwards, so the 2023–2025 pooled average
  **under**-commits them in the early years. **So the honest expectation is that C1 COAL_BIT gets
  WORSE in 2020–2022.** That is rule 14 `[R-ACCURATE]` in its own words — *"if swapping a hand
  estimate for real data makes the backcast worse, that is a signal that something else in the model
  is miscalibrated and the estimate was silently compensating for it"* — and rule 1 `[R-STRUCT]`
  keeps the mechanism in regardless. **It is not a gate in either direction.** If COAL_BIT degrades
  and G1–G5 pass, the card stands and the regression is surfaced to the owner as a promotion fact
  (rule 30(c): a held-out year never downgrades the ISO).
- **IT IS STILL NOT A LEVEL CHANNEL, and that is measured rather than asserted.** A tuning channel
  moves one way; this moves **both ways within every single year**, across plants: 2020 23 up / 15
  down, 2021 19/16, 2022 21/14, 2023 12/24, 2024 16/18, 2025 20/14 (of ~40 floored plant-rows each).
  The year totals move both ways too (+4 / −2 across the span). There is no value to tune: the
  operand is a measured count ratio (rule 21 `[R-DOF]`).
- **The training span 2023–2025.** 2023's windows move materially (max |Δ| 0.291; plant 7213
  0.314 → 0.102, 6166 0.566 → 0.375, 6004 0.319 → 0.610), so the span can move. A downgrade from
  `CALIBRATED` is **reported, never used to select or reject** the mechanism.
- **The control D-4 FAIL rows this card CANNOT reach**, named in §4.2(c) below and routed to a
  successor, not absorbed.

### 4.2 Stated as a LIMIT, not buried — three things phase 0 does NOT establish

**(a) THE WINDOW-CONDUCT PROBE IS NOT A D-4 PREDICTOR, and the measurement says so.** Phase 0
computes the median measured MW over the whole asserted *window*; D-4 computes it over the hours the
floor actually *binds in the solved dispatch*, a subset. Measured against the control's own 54
committed D-4 rows: **`binding_hours ≤ k_window` on 54 of 54** (so the window is a strict superset —
that inference is valid and is the only structural one made), but the ratio `binding/k` has **median
0.068** and the probe's window median **disagrees with D-4's binding median on 3 of 16 rows in 2023**
(879: probe 0.00 vs D-4 535.6; 3136: 0.00 vs 1263.2; 6166: 0.00 vs 755.0). So the probe's headline
— 25 zero-median plant-years under the pooled window falling to 17 under the own-year window, 8
repaired, 17 unmoved, **0 newly convicted** — is a window statistic and is **NOT** a prediction of
the D-4 FAIL count. **Only the solve can move G3 or G4.**

**(b) A SMALLER WINDOW IS NOT A SMALLER DISPATCH.** pjm-h14 measured this the expensive way: 58.04
TWh of withdrawn asserted floor produced 2.71 TWh of dispatch response, a ~10× over-prediction,
because removing a FLOOR does not remove a cheap BAND — the released capacity lands in the economic
band and still clears on price. The same discount applies here and in both directions. No C1
magnitude is predicted.

**(c) THIS CARD CANNOT REACH EVERY RULE-17 COAL FAILURE, and does not claim to.** The control's FAIL
rows outside G3's population fail for a different reason: their own-year fraction is **not lower**
than pooled, so the plant ran that year — just not in the top-system-load hours the window selects.
That is a window **PLACEMENT** defect, which is `mustrun_window_commitment_grain`'s object (cell `U`
in PJM, untested), not a window **VINTAGE** defect. Named and routed; **bundling it here would make
any verdict unattributable** (rule 19 `[R-ONE-MECH]`, and it is what cost pjm-h12 its charter).

## 5. Shard plan (rules 32 / 34 / 36)

Six shards, **one year each** (rule 36 `[R-YEAR-ISOLATION]` (a)), all against their own committed
control, all pushing their **full** bundle including `dispatch/<year>_P1.parquet` (rule 34(a):
a `.gitignore` **negation** scoped to the shard's own out-dir + a **plain `git add`**, never
`git add -f`).

| year | source bundle | out-dir | branch |
|---|---|---|---|
| 2020 | `pjm_h14_coalmustrun_touchpoint` | `results/calibration/pjm_h15_coalwindow_2020` | `claude/pjm-h15-coalwindow-2020` |
| 2021 | `pjm_h14_coalmustrun_touchpoint` | `…_2021` | `claude/pjm-h15-coalwindow-2021` |
| 2022 | `pjm_h14_coalmustrun_touchpoint` | `…_2022` | `claude/pjm-h15-coalwindow-2022` |
| 2023 | `pjm_h14_coalmustrun_span` | `…_2023` | `claude/pjm-h15-coalwindow-2023` |
| 2024 | `pjm_h14_coalmustrun_span` | `…_2024` | `claude/pjm-h15-coalwindow-2024` |
| 2025 | `pjm_h14_coalmustrun_span` | `…_2025` | `claude/pjm-h15-coalwindow-2025` |

Arming needs **no further code change beyond this PRECOMMIT's own commit**:
`replay_keeper.py <source> --out-dir <dir> --years <year> --set coal_sync_online_frac_per_year=true`.

Rule 34(c) / rule 35(b): PJM's registered year set, enumerated from
`frontend/data/backcast/registry/*.json` **before** anything is pruned, is
**{2020, 2021, 2022, 2023, 2024, 2025}** (span `[2023,2024,2025]` + touchpoint `[2020,2021,2022]`).
All six are launched; **none is omitted**.

**THE SHARD ENVIRONMENT IS NOT FREE, and this is the correction pjm-h15 owes its successor.** A
fresh container carries **neither** the gitignored `data/raw/pjm-da-virtuals/` corpus (the PJM keeper
arms `pjm_da_virtual_bids=True`, and `virtual_bids.py` raises `FileNotFoundError` rather than
no-opping) **nor** `data/clean/` (gitignored in full). Every shard prompt therefore carries, before
the solve: `pip install -r requirements.txt` (with `--ignore-installed PyYAML`),
`scripts/data/fetch_pjm_da_virtuals.py --years <y> --feeds hrl_da_incs_decs` (~4 min for one year),
and `scripts/regenerate_clean.py transfer-interface-limits ramp-capability` (~2 min) — the exact and
complete set, established here by running the fleet build to completion for all six years.
**Budget: 40 minutes per shard**, stated under rule 32(b) ("a longer single shard with the budget
stated in its prompt") because a PJM year is ~13 min of LP on top of ~10 min of setup. A shard that
reaches its budget with no artifact **STOPS and reports**; it never pushes a half-written bundle.

**Retrievability (rule 34(e)):** each bundle lands on its shard branch, and the parent composes and
lands the keeper bundles on `main` **before** its PR merges (rule 33(f)(4)(ii)). Shard branches are
transport, not storage.

**Composition (rule 32(d)):** the parent composes the per-year legs into a span (2023–2025) and a
touchpoint (2020–2022), **regenerates `legitimacy_diagnostics.json` over each COMPOSITE** (pjm-h13
correction #1 — per-leg D-4 borrows `ct_only` vintage flags across sibling years and is not
comparable to a composed span), rebuilds the benchmark parquets, scores, and registers with
`--no-prune`. **`prune_iso_runs.py --keep <touchpoint-id>`** on any promotion (pjm-h14 correction #1:
the script does **not** honour a `holdout.keeper` stamp, so a promotion otherwise deletes its own
touchpoint). Run ids keep the distinguishing word **inside the first four** (pjm-h14 correction #2:
`_slug` caps at 4 words and a shared prefix silently overwrites a sidecar) — hence
`pjm-h15-coalwindow-span` / `pjm-h15-coalwindow-touch`.

## 6. What this lane will NOT do

- **Not arm `mustrun_window_commitment_grain`** — the window-PLACEMENT sibling, cell `U` in PJM.
  Bundling it makes any verdict unattributable (rule 19). It is the named successor for §4.2(c).
- **Not arm `mustrun_online_frac_per_year`** (the gas seam) in the same run, for the same reason,
  even though the companion artifact this lane commits would make it reachable for the first time.
- **Not REGENERATE `thermal_tranches_PJM.csv`** — xiso-5's rule-23 refusal stands and this card does
  not need it. The level columns (`mustrun_online_pct`, `pct_committed`) do **not** move.
- **Not take `eia860_vintage_tracks_solve_year`** (LEVER B) — cell `R` in PJM (pjm-168 screened and
  rejected it). The year-blind coal fleet is real and is carried forward as a finding, not a lever.
- **Not re-test `mustrun_commitment_feasibility_clip`** (`R`, pjm-h12 D-3) or **rebuild an hourly
  seam ladder** (killed at zero LP, pjm-h12 D-2) — rule 28(a) DO-NOT-REDO.
- **Not fix the 19 pre-existing `cache_key` pin-test failures on `main`** (§7). Off charter, and
  bundling an infrastructure repair with a mechanism arm is what rule 19 forbids.

## 7. Carried forward, not absorbed

- **19 `cache_key` pin tests FAIL at `origin/main`, before this branch touches anything.** Verified
  by stashing: the failure set is **byte-identical** with and without this lane's change (19 / 19,
  `diff` clean), and this field's own registration is proven correct the direct way — the default
  key is **unchanged** against `origin/main` and the armed key is distinct. Someone pinned a literal
  that HEAD no longer produces; it is not this lane's to fix but it is this lane's to report.
- `tests/unit/data/test_fleet.py::TestLoadRetiredWithinWindow::test_neiso_includes_mystic_cc` also
  fails at clean `origin/main` (NEISO's lane).
- pjm-h14's open owner questions Q1 (three truncated ladder rungs), Q3 (the ungated MER dual), Q4
  (both PJM offer-pipeline scripts still default to `--years 2023 2024 2025`), Q5, Q6, the pjm-h12
  D-3 promotion, and the proposed rule 32(c)(8) addendum — all still open, none touched.

## 8. The phase-0 probes, all committed, all zero LP

| probe | what it establishes |
|---|---|
| `scripts/probes/pjm_h15_coalwindow_phase0.py` | the pooled-vs-own-year gap per covered coal plant per year; the window each fraction implies against the keeper's OWN committed system load; the CAMPD conduct over each window; **and the predictor's own standing** against the control's 54 committed D-4 rows |
| `scripts/probes/pjm_h15_floor_footprint_phase0.py` | the asserted floor ENERGY, pooled vs own-year, read off the model's own fleet via `run_year(fleet_only=True)` under the keeper's committed recipes — G1's and G5's pre-solve footprint, and the sign test |
| `derive_thermal_tranche_online_frac_by_year.py --iso PJM --years 2023 2024 2025 --verify-pooled` | the rule-23 identity: **168 exact, 0 mismatched** — the grain refinement reproduces the committed pooled column and the derive window is 2023–2025 |
