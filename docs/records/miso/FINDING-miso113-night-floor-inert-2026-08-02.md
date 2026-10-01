# FINDING miso-113 (phase 2) — `miso_coal_night_floor` is INERT once wired

Session miso-113 phase 2, 2026-08-02, branch
`claude/miso-113-coal-prb-floor-wtd8kl`, off `origin/main` at `1d3ec21`.
Continues the merged miso-113 lane (`62a469e` … `5949eb2`), whose
pre-registration is `results/calibration/PREREG-miso113-prb-night-floor-2026-08-01.md`
and whose registered control is `2026-08-01-miso-113a-control`.

## 0. Verdict

**`miso_coal_night_floor` is INERT (matrix cell `I`, not `R`). Keeper
`2026-07-31-miso-109b-hy-level` stays.** The mechanism binds — 2.37 / 4.24 /
1.09 TWh of forced energy, D-4 clean — and changes **nothing** that is
scored: identical C-series, identical D-1 to three decimals, COAL_PRB energy
unchanged to 0.000 TWh, and **identical to four decimals on the per-plant
night-level statistic it exists to move**.

This is a phase-2 completion of the merged lane, not a competing arm. It
contributes the two things that lane was missing: the **wiring fix** without
which no A/B against it could have measured anything, and the **arm B** it
never produced.

## 1. Why the lane had a control and no arm: the mechanism never fired

`miso_coal_night_floor` was threaded into `pipeline/year.py` and
`runner.py`. **`scripts/run_calibration.py` — the orchestrator every
calibration arm and keeper actually runs — builds its own `p1_fleet_prep=`
chain, and the hook was never constructed or passed there.** `run_calibration`
carried only the config kwarg (`miso_coal_night_floor: bool | None`), so an
armed run was accepted, recorded armed in `run_config.json`, solved to
completion, and the floor never applied: no error, no log line.

That is the nyiso-87 failure mode verbatim. `tests/unit/pipeline/test_p1_prep_wiring.py`
exists to catch exactly it, but its `_BRIDGE_BUILDERS` registry is
hand-maintained and did not carry this builder, so the guard was blind. The
row is now added and the guard verified to fail on the real bug
(`'miso_night_floor_prep' never reaches a p1_fleet_prep= chain`).

**The fix is wiring only** — construction, scope, level and window are
untouched, per the owner's "defer to theirs unchanged" instruction.

## 2. The A/B

Both arms 2023+2024+2025 in ONE bundle (rule 16), years chained sequentially
(rule 12) via `scripts/probes/_miso113_chain.sh`, at the wiring-fixed HEAD:

- **A (control)** `results/calibration/miso113b_control_A` →
  `2026-08-02-miso-113c-control`
- **B (arm)** `results/calibration/miso113b_nightfloor_B` →
  `2026-08-02-miso-113b-night-floor` (A + `miso_coal_night_floor=true`)

A fresh control was required rather than reusing `2026-08-01-miso-113a-control`:
that bundle was solved at `247e795`, and `scenarios.py`, `schedulable.py`,
`arrays.py` and `runner.py` all changed between it and `1d3ec21`.

**Control integrity.** Arm A reproduces the committed 109b keeper at
**L1 0.00000 %** in 2023 and 2024 (max class-hour |diff| 0.0000 MW) and
carries **0.03007 %** in 2025 — the same HEAD-drift figure miso-112 measured
and the same one this session measured independently at a different HEAD, so
the drift is pre-existing and not attributable to the wiring fix.

**The mechanism fires.** 197 scoped tranches; 116,616 / 115,320 / 123,912
unit-hours floored; **15.89 / 15.41 / 17.39 TWh** of floor volume; 97 / 79 /
85 committed blocks, **none shorter than 24 h** and most longer than 168 h —
the baseload committed-run window the rule-17 declaration claims, with no
clock-hour banding. D-2 id 22 (`MECH_MISO_COAL_NIGHT_FLOOR`) is present on
115,728 unit-hours of the 2023 floors array.

## 3. Results — inert on every scored axis

**Arm B against its own same-HEAD control:**

| year | class-hour L1 | max class-hour Δ | COAL_PRB TWh (A → B) |
|---|---|---|---|
| 2023 | 0.02038 % | 912.50 MW | 123.69 → 123.69 (**−0.000**) |
| 2024 | 0.01768 % | 912.50 MW | 118.33 → 118.33 (**−0.000**) |
| 2025 | 0.02264 % | 927.83 MW | 147.14 → 147.14 (**+0.000**) |

**D-1 COAL_PRB (the C7 gate) — byte-identical between the arms:**

| year | profile_r | model off-peak CV | actual | cv_ratio |
|---|---|---|---|---|
| 2023 | 0.988 → 0.988 | 0.072 → 0.072 | 0.155 | 0.466 → **0.466** |
| 2024 | 0.978 → 0.978 | 0.058 → 0.058 | 0.121 | 0.475 → **0.475** |
| 2025 | 0.971 → 0.971 | 0.023 → 0.023 | 0.074 | 0.314 → **0.314** |

**C-series — identical, criterion for criterion:** C1 PASS 16/16 (free
12/12), C2 PASS, C3a FAIL (2025 −14.2 % in BOTH arms), C3b PASS, C3c FAIL,
C4 PASS, C7 FAIL (the same three COAL_PRB cells with the same numbers), C8
PASS.

**The structural night-level test** (`scripts/probes/_miso113_night_level_test.py`,
the statistic the mechanism exists to move, measured cap-weighted 0.4343):

| year | control | arm |
|---|---|---|
| 2023 | 0.4957 (err 0.1175) | **0.4957 (err 0.1175)** |
| 2024 | 0.4482 (err 0.1089) | **0.4482 (err 0.1089)** |
| 2025 | 0.5666 (err 0.1418) | **0.5666 (err 0.1418)** |

Identical to four decimals. The floor does not move the fleet's night level
at all.

**D-2 / D-4:** forced share 1.3 % / 2.5 % / 0.5 % of COAL energy against a
30 % budget; D-4 off-window binding **0.0 %** in all three years, window
`h0-23` as declared. Both gates PASS — the mechanism is legitimate by every
rule-17/20 test. It simply does nothing.

## 4. Why it is inert

Not the miso-111/112 failure mode (a mechanism that moves the wrong thing),
and not miso-111's LSL argument (a floor beneath another floor). This floor
binds in real hours and still changes no outcome, for two compounding
reasons:

1. **The keeper already sits ABOVE the measured night level.** Per plant,
   capacity-weighted, the control is 0.4957 / 0.4482 / 0.5666 against a
   measured 0.4343 (FINDING-miso112 §4 established the same on its own
   control). A floor placed at a level the model is already above is slack in
   most hours by construction.
2. **Where it does bind, the plant absorbs it internally.** The detector's
   eligibility gate (`_ra_bridge_unit_params` rejects binned incremental
   tranches) floors only the `_committed` band, so the plant's `_econ` and
   `_peak` tranches are free to give back exactly what the floor forces. Net
   plant output is unchanged; only the *composition* inside the plant moves,
   which is why 15–17 TWh of floor volume produces a 0.02 % class-hour L1 and
   a 0.000 TWh energy delta.

The ex-ante reach probe (`results/calibration/miso113_floor_inertness.txt`)
records the sizing consequence of that same gate: 18 of 26 regulated plants
carry a non-zero floor above their `_mustrun` band (69.2 % of regulated-PRB
nameplate, 4,274 MW), but **911 MW of it, on 12 of those 18 plants, sits
above the plant's `_committed` capacity** and is therefore clipped away — so
the applied floor is below the measured night level the field docstring
targets ("the plant's TOTAL floor is then exactly night_p50 × plant
capacity") on two thirds of the clearing plants.

## 5. What this means for the lane

**Do not iterate this form.** Widening the floor to reach the full measured
night level (spreading it across `_committed → _econ` in fill order) was
built and tested independently in this session's phase 1 and **it does not
help**: the stronger floor moved C7 cv_ratio 0.466 → 0.460 and 0.475 → 0.420,
i.e. **worse than control in the two years that had to clear 0.5**, and
regressed C3a (−14.2 → −15.8 %) and flipped C3b PASS → FAIL. The reason is
structural rather than a sizing question: **C7's failure is that the model's
overnight distribution is too NARROW, and a lower bound can only narrow it
further.** A slack floor changes nothing; a binding one clips the cheap hours
that are the entire source of the model's off-peak variability.

That closes the regulated-PRB self-commitment family in all three admissible
forms — whole-band repricing (miso-111, **R**), the measured per-plant split
(miso-112, **R**), and the night-level floor (miso-113, **I**). Jointly the
three sessions establish that COAL_PRB's C7 failure is **not a coal-conduct
defect**: the class's night level is right, its volume is right (C1 16/16),
its phase is right (profile_r 0.97–0.99), and neither pricing nor flooring
the band moves the amplitude in the right direction. What is missing is the
**dispersion of the overnight price signal** the fleet responds to — model
off-peak p10 $29.71 against an actual hub p10 of $17.95 — i.e. the
data-blocked miso-78/79 congestion + sub-hourly-RT lane, which now carries
the C7 COAL_PRB residual in all three years.

No successor is chartered. Rule 19 forbids stacking a fourth coal mechanism
on a price-formation residual.

## 6. Rule duties discharged

- **Rule 15**: both arms registered this session
  (`2026-08-02-miso-113c-control`, `2026-08-02-miso-113b-night-floor`);
  top-15 MISO retention honoured (pruned
  `2026-07-27-miso-98a-sectorabsent-control`,
  `2026-07-27-miso-98b-sectormeasured`).
- **Rule 16**: one bundle per arm, `--year 2023 2024 2025`, years sequential.
- **Rule 22**: `--year` strictly {2023, 2024, 2025}; MISO holds no holdout
  marker and none was touched.
- **Rule 23**: the measured artifact was consumed, never re-derived.
- **Rule 26b**: the `miso_coal_night_floor` cell is stamped **I** with this
  finding. No new `ScenarioConfig` field was added.
- **Rule 21**: no free parameter added; the arm is not a keeper, so no DOF
  ledger entry is created.

## 7. Operational notes for the next MISO session

- **A P1-native bridge must be wired into all THREE orchestrators**
  (`pipeline/year.py`, `runner.py`, `scripts/run_calibration.py`) **and added
  to `_BRIDGE_BUILDERS`** in `tests/unit/pipeline/test_p1_prep_wiring.py` in
  the same commit. The guard is hand-maintained; a builder missing from it is
  unguarded, and this lane lost a full A/B to that twice.
- **Always verify the mechanism fired** before trusting an arm: check the D-2
  id in `<bundle>/floors/<year>_P1.npz`, not just the flag in
  `run_config.json`.
- **Memory (15 GB / 4 cores).** Rule 12's "~2 simultaneous" does not hold for
  MISO per-plant here: two concurrent single-year chains OOM-killed one arm at
  9.99 GB anon-rss, and a single armed link peaked at 15.85 GB and was killed
  alone. Run **one chain at a time plus an 8 GB swapfile**. At this HEAD a
  cold year solve is ~1,500 s, so a 3-year chain is ~1.5 h and an A/B is ~3 h.
