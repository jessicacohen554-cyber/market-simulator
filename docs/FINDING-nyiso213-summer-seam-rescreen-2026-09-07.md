# FINDING nyiso-213 — the re-screen **CLEARS all five corrected gates**, and the re-solve reproduces nyiso-212's numbers **exactly**, confirming the G-DRIFT audit by execution

**Session:** nyiso-213, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-b6er34`, on `main` at `5930e533`. **Date:** 2026-09-07.
**Keeper:** `2026-09-06-nyiso-202-startup-aware` — CALIBRATED, grade 7/8, fails 0, C3c the lone
ledgered caveat.
**Pre-registration:** `results/calibration/PREREG-nyiso213-summer-seam-rescreen.md`, committed and
pushed at `1ff08f04`-lineage **before the screen solve was launched** and not edited since.
**Machine record:** `results/calibration/_nyiso213_screen_gates_2025.json` (every number below).
**Scorer:** `scripts/probes/nyiso213_screen_gates.py`.

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES TO FIX.** NYISO's keeper reads CALIBRATED with **zero
failing criteria**. Nothing here was selected because a residual moved (rule 1 `[R-STRUCT]`,
rule 23 `[R-FROZEN-DERIVE]`).

---

## 0. The result in one paragraph

nyiso-212 built the `cc_summer_derate_reconciled_basis` seam repair, screened it on 2025, and
**killed its own arm on two gates whose wording was its own** — refusing to rewrite a bar after
seeing the number, and leaving the 2023–2025 span unspent. This session wrote those two gates
correctly **in a PREREG pushed before any new number was read**, re-solved the same screen year, and
the arm **CLEARS all five**: S-1 recipe identity, S-2(a)/(b)/(c) direction-and-bound, S-3 footprint
confinement, S-4 no load-bearing flip, and **S-5 — the object — which closes** (zero months in which
Cricket Valley 57185's meter exceeds the LP's monthly ceiling, against Jun/Jul/Aug on the keeper).
The corrected S-2(c) is **stricter in coverage** than the bar it replaces — it bounds all 15
reconciled plants individually rather than 3 — and every one of the 15 clears. Separately, the
PREREG's declared **third outcome did not fire**: the re-solve ran on a solve-path tree 11 files
(+1 docstring) removed from nyiso-212's, and it reproduced that session's numbers **to the last
declared digit**, so §4's hunk-by-hunk G-DRIFT audit is confirmed by execution rather than by
reading. Reported at full magnitude and **not a reason either way** (rule 1): the arm makes 2025's
price fit modestly WORSE — C3a −6.3 % → −7.3 %, C3b NRMSE 0.152 → 0.160, both still PASS — exactly
as PRED-B declared in advance.

---

## 1. The two corrected gates, and what each measured

### S-1 recipe identity — **PASS**

Declared bar: excluding `weather_year` and `gas_price_override` (which encode the `--year 2025`
selection, because the keeper's `run_config.json` is a **three-year** bundle's record carrying its
FIRST year's values), and classifying the armed flag as the **live delta** rather than as a new
dataclass default (the keeper's record predates the field, so absent *means* `False`), the live
recipe diff must be **exactly** `{cc_summer_derate_reconciled_basis: absent(False) → True}`.

Measured: **the recipe diff excluding the two year keys is EMPTY**, `{}`. The two excluded keys read
exactly as predicted — `weather_year 2023 → 2025`, `gas_price_override 2.54 → 3.52`. The flag reads
`absent(None) → True`. Nine keys are absent from the keeper's 810-field record; **eight** of them
take HEAD's `False` default and are reported, not counted (`eia860_vintage_tracks_solve_year`,
`ercot_ep_gas_basis_monthly`, `pjm_vre_accreditation_vintage`, `gas_offer_margin_anchor_vintage`,
`pjm_interface_feed_admissibility_gate`, `miso_seam_neighbour_hourly_ladder`,
`miso_seam_neighbour_hourly_spp`, `capacity_screen_peak_measured_hindcast`) — the ninth is the flag
itself, at `True`. **The arm is the keeper recipe plus one value.** nyiso-212's literal bar is
recomputed and written to the record as `False`, so the correction is auditable rather than
asserted.

### S-2(c) direction + bound — **PASS**, on a bar stricter than the one it replaces

Declared bar, from the mechanism's own algebra rather than the reconcile table's `mode` label: **a
plant's summer ceiling RISES iff its carried capacity is below its EIA-860 nameplate**, so no plant
may move further, in the direction its own ceiling moved, than its own ceiling moved — with **no
lower bound where the ceiling rose** (relieving a bound never compels a unit to run) and no upper
bound where it fell.

Measured, all 15 reconciled plants, 2025 (GWh, Jun–Sep):

| plant | ΔC_p (own ceiling) | Δ summer dispatch | bound | ok |
|---|---:|---:|---|:--:|
| 57185 Cricket Valley | +511.52 | +258.39 | Δ ≤ ΔC | ✓ |
| 55405 Athens | +370.10 | +210.18 | Δ ≤ ΔC | ✓ |
| 56940 CPV Valley | +185.05 | +138.83 | Δ ≤ ΔC | ✓ |
| 54574 Saranac | +83.16 | +34.60 | Δ ≤ ΔC | ✓ |
| 7314 Flynn | +56.80 | +17.96 | Δ ≤ ΔC | ✓ |
| **50978 Carr Street** | **+56.51** | **+54.27** | Δ ≤ ΔC | **✓** |
| 54593 Batavia | +33.09 | +27.86 | Δ ≤ ΔC | ✓ |
| 54592 Massena | +32.50 | +27.38 | Δ ≤ ΔC | ✓ |
| 54034 Rensselaer | +22.84 | **−0.59** | Δ ≤ ΔC | ✓ (moved against relief — REPORTED) |
| 50744 Sterling | +18.74 | +16.44 | Δ ≤ ΔC | ✓ |
| 10620 Carthage | +4.39 | +0.17 | Δ ≤ ΔC | ✓ |
| 10190 Castleton | +2.05 | **−3.38** | Δ ≤ ΔC | ✓ (moved against relief — REPORTED) |
| 56234 Caithness | −33.96 | −30.64 | Δ ≥ ΔC | ✓ |
| 55375 Astoria Energy | −42.16 | −40.68 | Δ ≥ ΔC | ✓ |
| 56196 Zeltmann | −84.03 | −81.16 | Δ ≥ ΔC | ✓ |

**50978 Carr Street — the single plant that failed nyiso-212's bar — sits inside its own +56.51 GWh
relief at +54.27**, which is what the sign-correct reading predicts and what the `mode`-label bar
could not see. The two plants that move *against* their relief (Rensselaer −0.59 on a 4.51 GWh
keeper summer, Castleton −3.38 on 56.89) are exactly the case the PREREG declared would carry no
lower bound: merit re-allocates around a small plant, and a relieved bound never compels it to run.
Legs (a) and (b) are unchanged from nyiso-212 and pass as before: 57185 **+258.39** within the tight
availability-inclusive bound **+376.18**; the 12 `cap` plants **+646.68** within **+1,236.21**.

## 2. The three gates that carried the structural claims — unchanged, and unchanged in verdict

* **S-3 confinement — PASS.** Δ annual CC_REGULAR **+567.95 GWh** within the phase-0 bound
  **[0, +892.95]**. Offsetting moves, reported at full magnitude: ST_GAS **−313.89**, CC_CHP
  **−109.72**, CT_PEAKER **−63.54**, CT_CHP −39.24, ST_CHP −24.90, oil −1.12; hydro / nuclear /
  wind / solar / import / biomass all **0.00**. Sum over every class **+15.54 GWh** against a fixed
  load. The 15 plants' **off-summer** dispatch rises **+382.42 GWh** although the flag provably does
  not touch off-summer availability (phase-0 F-1) — pure merit-order feedback, meaning CC_REGULAR
  plants *outside* the 15 give up roughly 0.44 TWh. **Merit displacement across classes is an
  INTENDED effect of a capability change, not a defect.**
* **S-4 no load-bearing flip — PASS.** No flips. C3a and C3b both stay PASS on the arm; C1 (all six
  classes) and C2 (gas, coal) are **SKIPPED identically on both sides** on the preliminary EIA-923
  vintage, so no data-vintage event occurred. **C8 is NOT computable for an unregistered screen
  bundle** (it needs `legitimacy_diagnostics.json`, written only by the register path) — reported,
  not faked; the arm moves Jun–Sep availability at 15 CC_REGULAR plants and **no floor**, so the D-2
  forced volume is untouched by construction, and it is re-scored on the full-span bundle.
* **S-5 the contradiction removed — PASS. This is the object of the whole lane.** At 57185 in 2025
  the meter exceeds the arm's monthly ceiling in **no month** (keeper: Jun, Jul, Aug), and dispatch
  never exceeds the ceiling (**max excess 0.0000 MW**):

  | month (2025) | Jun | Jul | Aug | Sep |
  |---|---:|---:|---:|---:|
  | arm dispatch GWh | 321.5 | 400.4 | 465.3 | 444.4 |
  | CAMPD meter GWh | 415.4 | 476.8 | 580.1 | 512.6 |
  | **arm ceiling GWh** | **470.7** | **486.3** | **611.9** | **619.7** |

  **Object (B) is untouched and remains open**, exactly as scoped: the plant still under-runs its
  meter by ~0.75 TWh on the year, which is a merit/offer-position question at the newest H-class CC,
  now cleanly separated from the capability seam.

## 3. Reported at full magnitude, and NOT a reason either way (rule 1 `[R-STRUCT]`)

PRED-B was declared in the PREREG **before the solve, precisely because it hurts the answer this
session prefers**, and it fired:

| criterion (2025) | keeper | arm |
|---|---|---|
| C3a mean LMP | PASS, **−6.3 %** (model 62.26 vs actual 66.43) | PASS, **−7.3 %** (model 61.58) |
| C3b price shape | PASS, NRMSE **0.152** | PASS, NRMSE **0.160** |
| C3c tail hours > $300 (reported) | 4 | 3 |
| system mean price $/MWh (reported) | 59.293 | 58.734 |
| C1 / C2, every cell | SKIPPED (preliminary EIA-923 vintage) | SKIPPED, identical |

The arm makes the 2025 price fit modestly worse while removing a physical contradiction. Under
rule 1 a structurally-correct mechanism is never judged by the residual — so this is neither a
reason to reject the repair **nor** smoothed over, and **it will not be tuned away**.

## 4. PRED-C did NOT fire — the G-DRIFT audit is confirmed by execution

nyiso-212's screen solved at `f76c3011`; this one solved at `5930e533`, a solve-path tree **11 files
(+502/−46, plus one SPP docstring from the mid-session rebase)** removed from it. The PREREG §4
classified every hunk INERT for a NYISO backcast and §7 declared that, if the audit is right, the
re-solve reproduces nyiso-212's numbers to a stated tolerance — and that **a miss would VOID the
screen** and become the session's result instead.

| quantity | predicted (±tol) | measured | |
|---|---:|---:|:--|
| Δ summer dispatch at 57185 | +258.39 (±0.01) | **+258.39** | hit |
| Δ annual CC_REGULAR | +567.95 (±0.01) | **+567.95** | hit |
| Δ annual ST_GAS | −313.89 (±0.01) | **−313.89** | hit |
| C3a arm model mean LMP | 61.58 (±0.01) | **61.58** | hit |
| C3b arm NRMSE | 0.160 (±0.001) | **0.160** | hit |
| months meter over arm ceiling at 57185 | `[]` (exact) | **`[]`** | hit |

**Six of six.** The audit is now an empirical result, not a reading. It is corroborated at the fleet
level independently: the entire zero-LP phase-0 chain, rebuilt from empty caches at this HEAD,
reproduces `_nyiso212_overceiling_decomposition.json` and `_nyiso212_arm_phase0.json`
**byte-identically for all three years**.

**Instrument identity.** The screen scorer rebuilds the payload year-block the rubric functions read
from a bundle's own hourly parquets. Rebuilt from the **keeper's** bundle it reproduces the
committed payload with max abs diff **0.0** on zone mean price, **0.0** on all 12 monthly prices of
all 6 zones, and **0.0** on every `gmModel` class total — so keeper and arm are scored by one
instrument on one basis (G-CTRL form 4: no control solve was spent, rule 29(b)).

## 5. Governance and environment

* **Rule 29(c):** the screen bundle `results/calibration/_nyiso213_screen_2025` is a throwaway
  diagnostic probe — never registered, never a keeper, **deleted before this PR merges**. This
  document and `_nyiso213_screen_gates_2025.json` carry every number the session will cite from it.
* **Rule 22:** the screen and the span are **training years only** (2023–2025). No out-of-training
  year was solved, scored or registered. `final` untouched, the locked-test freeze untouched,
  2020/2021 not spent — those remain a separate owner spend.
* **The five pending owner rulings are untouched and no new card is opened.**
* **Pre-existing failures, RE-MEASURED at this HEAD (rule 25 — reported, not repaired):**
  `tests/scoring/test_gate_a_provenance.py::test_live_board_passes`, which nyiso-210 / -211 / -212
  all recorded as **failing** on MISO's stale gate-(a) stamp, now **PASSES** — `main` repaired it
  between nyiso-212's HEAD and `5930e533`. Re-measured this session: that file (13 tests), the
  mechanism's own guard `tests/unit/data/test_cc_summer_derate_reconciled_basis.py`, and rule 30's
  guard `tests/scoring/test_holdout_render_parity.py` read **29 passed / 0 failed**. The prior
  sessions' "six charter files" set is not enumerated in any committed document this session could
  find, so it is named here rather than inherited as a stale number.
* **Environment, all measured at HEAD:** the keeper's 810-field config reconstructs with zero
  unknown fields and `cache_key() = 942480d844dfeaa1` (unchanged); `moved_rows("NYISO") == {}`,
  `SOLVE_EPOCHS == ()`; `nyiso196_rebuild_checks.py --year 2024` reproduces its committed record
  with the tree clean.

*(nyiso-213 screen, 2026-09-07. The gates were written before the solve; the arm cleared them; and
the one prediction that could have voided the whole exercise was tested and did not fire.)*
