# ADDENDUM miso-247 (second) — **`D-1` RETURNS `B` LIVE: 55 MISO rows / 624.8 MW move in ALL THREE YEARS, so rule 29(b) FORM 4 IS FALSIFIED BY MEASUREMENT and the handoff's pinning instruction does not recover it.** Screen year **2024** on the pre-registered rule. **AND MY OWN `P-3` PREDICTOR HAS A DEFECT I CAN NAME WITHOUT ANY REALISED NUMBER — pre-repair values are published verbatim below, the repair is declared before a repaired number exists, and it is STRICTER**

**Governs:** `PREREG-miso247-the-P19-posture-at-MISO-2026-09-09.md` §2a's pre-declared branch, and
the **reporting** of `P-3`. **`D-1`…`D-5`, `P-1`, `P-2`, §4's selection rule and `G-1`…`G-4`'s bars
are UNTOUCHED.** Machine record `results/calibration/_miso247_p19_posture_phase0.json`,
provenance-stamped at HEAD **`ebb47756`**, tree clean. **ZERO LP so far.**

---

## 1. **`D-1`: `B` IS LIVE AT MISO. FORM 4 IS FALSIFIED.**

`market_sim.data.fleet.eia860._apply_simple_cycle_hr_floor`, rebuilt on the keeper's exact recipe
both ways:

| year | rows moved | MW moved | max \|Δhr\| | min signed Δhr | clamp only RAISES? |
|---|---:|---:|---:|---:|---|
| 2023 | **55** | **624.8** | 13.580667 | **0.0** | **yes** |
| 2024 | **55** | **624.8** | 13.580667 | **0.0** | **yes** |
| 2025 | **55** | **624.8** | 13.580667 | **0.0** | **yes** |

**`P-2`'s identity for `B` HOLDS exactly**: every moved row satisfies `hr_after = max(hr_before,
floor)` — `min_signed_dhr` is **0.0** in all three years (the clamp never lowers a rate), and
`hr_after` takes exactly **three** values, `{9.0, 9.9, 39.6}`: the raw floor
`EGRID_CT_HR_PHYSICAL_FLOOR = HEAT_RATE_BINS["gas_ct"]["aero"] = 9.0` on legacy-bin rows, and that
same floor carried through the CAMPD tranche multipliers on the per-plant rows
(`econlo`/`econhi` = 9.0 × 1.1, `peak` = 9.0 × 4.4). Eight legacy plants (1128, 1154, 1873, 1967,
1982, 2013, 7865 …) plus 33 `CT_PEAKER_<zone>_p<plant>_<band>` tranche rows.

> **CONSEQUENCE, and it is the adverse branch of the two my PREREG fixed in advance.** The handoff's
> instruction — *"the keeper's committed bundle IS a valid rule 29(b) form-4 control ONLY with that
> field explicitly set to `False`"* — **is measured FALSE.** Pinning
> `f923_gas_price_plausibility_screen=False` leaves `B` in the arm and out of the control, and **`B`
> has no gate to pin.** Per PREREG §2a, **a LIVE hunk is the one thing that earns a control solve**,
> and it is spent **for the screen year ONLY**, as **`control` = HEAD with
> `f923_gas_price_plausibility_screen=False`**. `arm − control` then isolates **A**;
> `control − the keeper's committed bundle` isolates **B** and **falsifies my own `D-4`
> classification** if anything else moved. **No bar moved to reach this** — the branch and its cost
> were written before `D-1` ran.

**`D-2` and `D-3` are INERT, measured not read.** The `floors.py` net-load-drag refactor: the
assembled per-unit `min_gen` array is **bit-identical** between the two trees in all three years
(sha `ba627175…` / `4d36567e…` / `cb78b8ae…`, keeper == arm), on a keeper that **does** run
`ct_netload_drag=True`. The hydro-family refactor: `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` carries
**only `NYISO`**, so MISO's period vector is `None` and the pre-refactor single-family path is taken.

**`D-4` (read, git) — every remaining hunk INERT, with its reason:** `interchange/{__init__,pjm,
spec}.py` = PJM's own neighbour-anchored ladder registry, consumed only by `interchange/pjm.py` under
the default-off `pjm_seam_neighbour_hourly_ladder`, and **`MISO_SEAM_LADDER_BY_YEAR` has ZERO diff
lines in the whole window**; `capacity_evolution/{ccs,evolve}.py` = forecast-only, `config.mode ==
"forecast"` a hard gate a backcast never passes; `results/cache.py` (+154) = **prose only**, the capx
D88 epoch ledger, no code; `data/fleet/arrays.py` = D88's duplicate-`unit_id` guard, which only
`raise`s — and MISO's fleet built **twelve times** here (3 years × 4 postures) without raising, so it
is measured inert, not assumed; `eia930/envelopes.py` = `measured_pjm_neighbour_prices`, PJM's
branch; `run_calibration{,_full}.py` = the three CLI flags for the three default-off fields, none in
the keeper's recipe; `solve_surface_declared.py` = two entries appended **at their frozen
registration hash**, which by that module's own design moves no key; `pipeline/*`, `lp/{__init__,
model}.py` = `hydro_period_hours` plumbing. **`D-5`**: `actual_lmp.json`'s per-ISO canonical hashes —
**only CAISO moved**; MISO, ERCOT, NEISO, NYISO, PJM and SPP identical.

## 2. **SCREEN YEAR = 2024, on the rule fixed before the statistic existed**

`P-1`'s footprint `F_AB` = pmax MW of rows whose hour-mean `mc_base` moves > $0.01/MWh:

| year | `F_A` rows / MW | `F_B` rows / MW | **`F_AB` rows / MW** | MW-wtd signed Δmc (A) | (B) |
|---|---:|---:|---:|---:|---:|
| 2023 | 862 / 31,842.897 | 55 / 624.8 | 884 / **31,904.097** | **−20.965** | +5.203 |
| **2024** | 858 / 33,270.826 | 55 / 624.8 | 886 / **33,414.826** | **−15.276** | +4.655 |
| 2025 | 793 / 28,845.763 | 55 / 624.8 | 820 / **28,988.713** | **−13.574** | +4.965 |

**`argmax_y F_AB` = 2024 (33,414.826 MW). The screen year is 2024.** No residual, band or criterion
entered the selection. **Disclosed:** 2024 is also the year miso-243's own footprint rule selected,
and this agreement is **EXPECTED** (both statistics are footprints of fuel-side objects on the same
fleet), **not corroboration**. The two repairs push **opposite ways** — A makes the moved rows
cheaper, B makes 624.8 MW of small simple-cycle capacity dearer — which is why `F_AB` is reported
alongside both legs rather than as a single number.

**Also EXPECTED, and named as such:** the screen's own 2024 log line — *123 plant-months on 29
plants → reference* — reproduces SPP-49's published MISO footprint exactly. Same mechanism, same
ISO, same measured input; it is a plumbing check, **not** evidence for anything.

## 3. **`P-3` AS COMPUTED — PUBLISHED VERBATIM BEFORE THE REPAIR, so the repair cannot launder it**

Per-class energy delta (arm − keeper), TWh, from the pre-registered single-zone re-clear:

| class | 2023 | **2024 (screen)** | 2025 |
|---|---:|---:|---:|
| COAL | −1.1053 | **−2.2488** | −1.1598 |
| CT_PEAKER | +1.1039 | **+1.0309** | +0.1041 |
| CC_REGULAR | +0.9293 | **−0.3369** | +1.1293 |
| *(unattributed)* | −0.5858 | **−0.9553** | −0.2842 |
| ST_GAS | −0.5144 | **+1.5693** | −0.0150 |
| CC_CHP | +0.2191 | **+0.8825** | +0.0973 |
| ST_CHP | −0.0223 | **+0.1151** | +0.1446 |
| CT_CHP | −0.0245 | **−0.0566** | −0.0164 |
| hydro | 0.0 | **0.0** | 0.0 |

## 4. **THE DEFECT IN MY OWN PREDICTOR, AND THE REPAIR — declared BEFORE a repaired or realised number exists**

Two faults, both identifiable **from the predictor's own construction** and neither from any realised
number:

1. **IT CLEARS THE WHOLE LOAD AGAINST FLEET ROWS ONLY.** Renewables are LP decision variables
   (rule 3 `[R-RENEW-VAR]`), so they are **not** in `fleet_arrays`; my re-clear filled the entire
   committed load from thermal, import, nuclear and hydro rows, omitting the keeper's own
   **103.3 TWh of wind and 14.4 TWh of solar** in 2024. It therefore clears ~117 TWh too deep, puts
   the marginal unit far too high in the stack, and inflates every class's delta.
2. **THE UNATTRIBUTED BUCKET IS A REPORTING FAULT, NOT A CLASS.** `_class_of` fell through to `""`
   for 664 rows / 32,247.7 MW, which are `oil` (587), `import` (64) and `nuclear` (13) by
   `FUEL_TYPE_MAP`. My PREREG's `G-1` reads *"for each class"*, and an unattributed bucket is not a
   class.

**THE REPAIR, `P-3′` — and it is STRICTER, not wider:**

> **(a) Clear against the thermal residual the fleet rows actually serve**, taken from the keeper's
> **own committed** `class_hourly_2024.parquet`: target(t) = the keeper's committed P1 MW at hour `t`
> summed over every `klass` EXCEPT `wind` and `solar`. Measured, not assumed; no LP.
> **(b) Attribute every row**: `plant_group` where non-blank, else the `FUEL_TYPE_MAP` fuel name. **No
> row is dropped and no class is excluded.**
> **(c) The bundle-side mapping `G-1` will use**, fixed here: `COAL_PRB` / `COAL_BIT` /
> `COAL_LIGNITE` / `COAL` → **`COAL`**; `wind` and `solar` excluded from **both** sides (they are not
> fleet rows and are removed from the clearing target too); every other `klass` name-for-name.

**`G-1`'s BAR IS NOT MOVED.** It stays *"same sign, and within [1/3, 3]× the magnitude, for every
class where |prediction| ≥ 0.5 TWh"* — evaluated on `P-3′`. The repair makes the predictor **sharper
and more falsifiable** (a shallower, correctly-sited margin gives smaller, better-located
predictions against an unchanged tolerance band), and it puts **more** classes in scope, not fewer.
**`P-3` above stands on the record as computed**, and if `P-3′` should happen to make `G-1` easier
rather than harder, that fact is reported.

## 5. Non-claims

1. **No bar is moved anywhere.** §1's control solve is the branch PREREG §2a fixed in advance; §4
   repairs a predictor's construction and leaves `G-1`'s bar verbatim.
2. **No realised number exists yet.** Nothing in §4 can have been shaped to a screen result.
3. **`D-1`'s finding is adverse to this session's cheap path** — it converts a zero-control screen
   into a two-solve one — and it is reported because it is what the measurement says.
4. **Zero LP so far**; keeper unchanged; DOF **41/2**; no `ScenarioConfig` field created or changed.
5. **No marker is sought or implied**; 2023–2025 only; **the screen year is 2024**, an in-training
   year.
6. **C3c is untouched** and is a target in neither direction.
