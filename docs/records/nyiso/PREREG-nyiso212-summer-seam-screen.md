# PREREG nyiso-212 (screen) — rule-29 ONE-year screen of `cc_summer_derate_reconciled_basis` on the NYISO keeper recipe

**Session:** nyiso-212, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-c7tc79` (HEAD `17c48f4e` when this was written). **Date:** 2026-09-07.
**Keeper:** `2026-09-06-nyiso-202-startup-aware` — CALIBRATED, grade 7/8, fails 0, C3c the lone
ledgered caveat. **Committed and pushed BEFORE the screen solve is launched.**

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES TO FIX.** The arm screened here is a rule-19
`[R-ONE-MECH]` construction repair measured by `docs/FINDING-nyiso212-cricket-valley-summer-seam-2026-09-07.md`;
it is not selected because a residual moved, and this screen is **never gated on any target
residual** (rule 29 `[R-SCREEN]`: a screen may KILL an arm, never promote one).

**Owner's standing formula, carried verbatim:** *"Is this a recommended keeper candidate? If so plz
promote. If structural integrity improves but gates regress that may still be a keeper.."* It
attaches only to a full-span arm; the screen decides only whether the span is spent.

## 1. The arm

`ScenarioConfig.cc_summer_derate_reconciled_basis = True` on the keeper's committed recipe,
through the replay override channel (`--replay-bundle` + `--cc-summer-derate-reconciled-basis`,
the same recorded generic bag `caiso_dsw_daytime_evening_trim` rides), so **G-DELTA is by
construction exactly one value**. Mechanism: at every plant `cc_capacity_reconcile_NYISO.csv`
lists (12 `cap` + 3 `raise` CC_REGULAR plants) the Jun–Sep availability multiplier becomes
`min(1, net_summer / capacity actually carried)` instead of `net_summer / nameplate` applied to an
already-reconciled capacity. Zero free parameters. Nothing else moves.

## 2. Phase 0 (zero LP) — the pre-solve gate is CLEARED (`_nyiso212_arm_phase0.json`)

| check | result |
|---|---|
| flag OFF at HEAD vs the pre-change rebuild (G-DRIFT for the code edit) | max abs Δ **0.0** in 2023 / 2024 / 2025 |
| F-1 footprint | moved units 81 / 80 / 81 of ~810, **all CC_REGULAR**, exactly the 15 table plants in 2023 and 2025; 14 in 2024 (Rensselaer 54034 is out all summer 2024 — its unit-outage factor is 0.0 in Jun–Sep — so 0 × ratio = 0 and nothing can move); `pmax`, heat rate and `mc_base` identical; **off-summer hours untouched** |
| F-2 identity | ON/OFF summer ratio = `min(1, ns/carried) / min(1, ns/nameplate)` at every moved plant to **2.2e-16** |
| F-3 Cricket Valley 57185 | summer statistical factor 0.747075 → **0.902140** (= 0.965 × 1016.1/1086.9); summer available energy 2,338.6 → 2,824.0 / 1,513.6 → 1,827.7 / **1,812.4 → 2,188.6 GWh**; summer hours the meter exceeds the ceiling 1,346 → 804 / 2,123 → 1,370 / 2,225 → 1,638; over-ceiling **months 7 → 1** (only Aug 2024 remains) |
| class Jun–Sep available energy delta | CC_REGULAR **+860.3 / +878.8 / +893.0 GWh**; no other class moves |

## 3. Screen year — chosen by the mechanism's OWN measured footprint, never by residual

**2025.** The seam is a constant MW at each plant, so the footprint is the meter energy the
constructed ceiling forbids: at 57185 **292.3 GWh** in 2025 against 220.8 (2023) and 222.0 (2024)
(`_nyiso212_summer_seam_census.json` → `cricket_valley_ceiling_counterfactual`), and the class
capability delta is largest in 2025 (+893.0 GWh). The residuals of 2025 played no part (C1-2025
CC_REGULAR is SKIPPED on the keeper — preliminary EIA-923 vintage — so 2025 is also the year in
which the target criterion is not even gated).

## 4. G-CTRL form 4 — the keeper's committed bundle is the control; G-DRIFT audited, ALL INERT

No control solve is spent (rule 29(b)). The keeper solved at `c7523509`; the code-level drift audit
`git diff c7523509 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` (72 files) was classified hunk by hunk
in three read-only passes (engine / data-config / model-scenario files) **before this document was
written**, and every hunk is INERT for a `mode="backcast"`, `iso="NYISO"`, 2023–2025 solve on the
keeper's recorded values:

* another ISO's branch (the SPP registration appends per-ISO keys dispatched by `iso`; PJM
  interface admissibility `=(iso.upper() == "PJM")`; ERCOT ORDC published params
  `if iso.upper() == "ERCOT" else {}`; MISO seam ladders `if iso != "MISO": return False`;
  ERCOT multi-product AS `iso == "ERCOT"`);
* eight new `ScenarioConfig` fields, all default-off and all absent from the keeper's 810-key
  `scenario_config` (`eia860_vintage_tracks_solve_year`, `capacity_screen_peak_measured_hindcast`,
  `gas_offer_margin_anchor_vintage`, `pjm_interface_feed_admissibility_gate`,
  `pjm_vre_accreditation_vintage`, `miso_seam_neighbour_hourly_{ladder,spp}`,
  `mass_cap_tons_by_year`); no existing default changed, no field removed;
* forecast-only paths (every `capacity_evolution` hunk; `runner.py`, which
  `scripts/run_calibration.py` never imports; `cap_and_trade._power_sector_cap` behind
  `mass_cap_enabled=False`, with the live RGGI backcast adder path untouched);
* record-only / docstring / logging / reformat / cache-sidecar bookkeeping (`persist.py`,
  `export.py`, `cache.py`, the new `solve_surface*` fingerprint modules).

Verified by execution rather than by reading: the keeper's 810-field config reconstructs against
HEAD's `ScenarioConfig` with zero unknown fields and **`cache_key() = 942480d844dfeaa1`
byte-identical**, `moved_rows("NYISO") == {}`, `SOLVE_EPOCHS == ()`; and the fleet-side instrument
`nyiso196_rebuild_checks.py --year 2024` reproduces its committed record with the tree clean.
**The one hunk on the shared backcast path unguarded by ISO or mode** — the EIA-860 vintage
resolver — is inert only because `eia860_vintage_year is None` and
`eia860_vintage_tracks_solve_year` is absent/False on the keeper (both verified); it would be LIVE
if that flag were ever armed on a replay, and it is not armed here. **Form 4 is therefore valid**:
the arm differences against `results/calibration/nyiso202_startup_aware` (2025) and the committed
payload `frontend/data/backcast/runs/2026-09-06-nyiso-202-startup-aware.js`.

## 5. The command

    uv run python scripts/run_calibration_full.py --iso NYISO \
      --replay-bundle results/calibration/nyiso202_startup_aware --year 2025 \
      --cc-summer-derate-reconciled-basis \
      --out-dir results/calibration/_nyiso212_screen_2025 \
      --note "nyiso-212 rule-29 screen: keeper recipe + cc_summer_derate_reconciled_basis, 2025 only; DELETE BEFORE MERGE (rule 29c)"

One year, sequential. The bundle is a **throwaway diagnostic probe**: never registered, never a
keeper, never quoted as a keeper number, **deleted from `results/calibration/` before the PR merges**
(rule 29(c)); every number this session will cite from it is carried in the FINDING addendum.

## 6. Screen gates — STRUCTURAL, STOP-ONLY, declared before the solve

All read from the arm bundle (`run_config.json`, `dispatch/2025_P1.parquet`,
`calibration_verdict.py --json <bundle>`) and the keeper's committed 2025 artifacts. Keeper 2025
baselines (payload `m_mon`, GWh): 57185 summer (Jun–Sep) dispatch **1,373.3**; 15-plant summer
dispatch 9,091.1; 12 cap plants' summer ceiling delta = Σ over cap plants of
`carried × (min(1, ns/carried) − ns/nameplate) × summer hours` as recorded in phase 0; 57185's is
**+376.2 GWh** (1,812.4 → 2,188.6).

| id | gate (arm KILLED if it fails) | why it is structural |
|---|---|---|
| **S-1 recipe identity** | the arm's recorded `scenario_config` differs from the keeper's in exactly one key: `cc_summer_derate_reconciled_basis` absent/False → **True** (new dataclass defaults that the keeper's record predates are REPORTED, not counted, as nyiso-202 did) | the arm is the keeper recipe plus one value |
| **S-2 direction + bound at the footprint** | (a) Δ summer dispatch at 57185 ∈ **(0, +376.2] GWh**; (b) Δ summer dispatch summed over the 12 cap plants ∈ **(0, +Σ cap ceiling Δ]**; (c) at the 3 raise plants (55375, 56234, 50978) Δ summer dispatch ≤ **+1 %** of each plant's keeper summer energy (their ceiling FELL; a small positive is merit feedback, a large one is not this mechanism) | the response has the sign and is bounded by the arithmetic of the ceiling change; no lower bound is gated because the keeper's per-plant bound-binding hours are not in any committed artifact (magnitude is REPORTED) |
| **S-3 footprint confinement** | Δ annual CC_REGULAR energy ∈ **[0, +893.0] GWh**; Δ off-summer dispatch at the 15 plants is REPORTED (merit feedback only — their off-summer bounds did not move); Σ over all classes of Δ annual energy is REPORTED with imports / slack / dump (load is fixed) | the mechanism can add at most the Jun–Sep capability it created, and only in CC_REGULAR |
| **S-4 no non-target load-bearing flip** | in 2025 no load-bearing criterion that is PASS on the keeper reads FAIL on the arm: **C3a-2025, C3b-2025** (C1-2025 and C2-2025 are SKIPPED on the keeper for data completeness and must stay SKIPPED — a status change there is a data-vintage event, reported); **C8-2025** (protective) does not flip; **C6** passes | rule 29's own clause |
| **S-5 the contradiction is removed** | in the arm bundle, 57185's dispatch never exceeds its ceiling (LP bounds) and the METER exceeds the arm's monthly ceiling in **no** month of 2025 (phase 0 predicts `[]`); the six-month object of the FINDING is closed in the screen year | the identity the arm asserts |

**Target criterion, declared so it is never gated:** C1 CC_REGULAR (SKIPPED in 2025 regardless).
**Explicitly NOT a gate:** any change in C3a/C3b *magnitude* short of a PASS→FAIL flip, the
CC_REGULAR volume residual, the price residual, the grade.

**If any gate fails:** the arm is killed, the full span is never spent, the screen bundle is
deleted, and the kill is the session's result. **If all clear:** the full span is solved as ONE
`--year 2023 2024 2025` invocation of the same replay + flag (rule 16 `[R-ALLYEARS]`), scored
artifact-only, and only then does the owner's formula apply; a promotion additionally owes D-5(b)
(re-verify the determination before re-keying `complete.NYISO.keeper`; a WORSE determination
STOPS the promotion), the 2022 touchpoint replay + stamp, `build_status.py --iso NYISO`, the
forecast gate (a) re-key, and pruning of the superseded touchpoint — all in the same PR.

## 7. What this screen does not decide

* Whether NYISO should instead **disarm** `cc_capacity_reconcile` (the caiso-185 disposition) —
  a keeper-recipe question the FINDING §5 records and does not prejudge.
* The WEFOR residual on a demonstrated-peak cap and the net-summer-vs-measured-summer-peak gap
  (FINDING §7): not touched by this arm, reported not absorbed.
* The five pending owner rulings — untouched.

*(nyiso-212 screen, 2026-09-07. Gates written before the solve; a kill is a success.)*
