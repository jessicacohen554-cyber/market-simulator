# PREREG nyiso-146 — per-plant measured minimum-run for the gas commitment bridge

**Written and committed BEFORE either arm is solved.** Session nyiso-146.
Keeper at HEAD: `2026-08-18-nyiso-144-layup-exclusion` (CALIBRATED, rubric
v3.4, C3c the lone ledgered caveat). Holdout spend freeze **ACTIVE** — 2023,
2024, 2025 only, one bundle each arm (rules 16 / 22), years sequential within a
run, arms sequential (rule 12; a 3-year NYISO solve peaks at 5.68 GB RSS).

---

## 1. THE OBJECT

nyiso-145 (`FINDING-nyiso145-cc-overcycling-and-d4-vintage-2026-08-19.md` §3a)
measured that the LP shatters NYISO's committed combined-cycle runs. On the
keeper's own committed P1 hourlies, at the common 0.05 × capacity threshold:

| plant | model P1 starts 2023/24/25 | metered starts | model median run | metered median run |
|---|---|---|---|---|
| 2539 Bethlehem (893 MW) | **320 / 519 / 250** | 6-7 / 5 / 7 | 12 / 7 / 15 h | 647 / 952-1217 / 486 h |
| 7314 Flynn (170 MW) | 241 / 327 / 237 | 115 / 79 / 103-106 | **20 / 15 / 17 h** | **19-20 h** |
| 56234 Caithness (368 MW) | 100 / 6 / 15 | ~6/yr | 22 / 354 / 259 h | 1,201 h |

(Model starts computed from the keeper payload
`frontend/data/backcast/runs/2026-08-18-nyiso-144-layup-exclusion.js` via
`decode_run_js` + `_decode_cf_bytes`; they reproduce the handoff's 327/524/264
to within byte-quantization of the payload encoding.)

Bethlehem is a near-baseload plant that reality starts 6-7 times a year; the
LP starts it 250-519 times, it is simultaneously the fleet's **largest
bridge-floor consumer** (779/490/485 GWh) and still **0.34×** of its EIA-923
net at P1 in 2023. The two named plants fail **differently**: Bethlehem's RUN
LENGTH is wrong by ~50×; Flynn's run length is RIGHT (19-20 h vs 19-20 h
metered) and only its start count is high — which this lever does NOT claim to
repair (§4, ADV-4).

## 2. PHASE 0 — the class-scalar refutation (measured BEFORE the lever was built)

Probe `scripts/probes/_nyiso146_perplant_minrun_phase0.py`, record
`results/calibration/_nyiso146_perplant_minrun_phase0.json`. No solve.

**(a) The class is not one run-length population.** The keeper's minimum-run
extension fills every row of a class from one scalar
(`nyiso_gas_bridge_cc_min_run_hours = 21.0` / `_st_ = 13.0`, the
capacity-weighted class p50s). Measured per plant on the plant-summed series
(the lay-up artifact's own construction), the live bridge population spans:

| class | keeper scalar | per-plant p25 range | per-plant p50 range | spread |
|---|---|---|---|---|
| CC_REGULAR (11 live plants) | 21 h | **7 h → 646 h** | 10 h → 1,201 h | **92×** |
| ST_GAS (6 live plants) | 13 h | **2.5 h → 213 h** | 4 h → 503 h | **85×** |

(The 2,421 h CC p25 maximum in the record is the misaligned Astoria campus
series and is excluded — see §3.) Bethlehem's own p25 is **134.75 h** — 6.4×
the class scalar; Flynn's is **15 h** — below it; Carr Street's is 7 h. One
scalar provably cannot describe this population: it simultaneously
over-constrains the true cyclers and lets the LP shatter the near-baseload
CCs. **The lever proceeds.**

**(b) The percentile, chosen on stated reasoning BEFORE any solve — p25 of the
plant's own within-year run-length distribution.** The `scenarios.py` field
docstring's own argument: an OBSERVED run is an upper-ish bound on a
minimum-run CONSTRAINT (a unit that ran 21 h because it was economic does not
prove a 21 h floor), so the observed distribution bounds the constraint from
ABOVE and a LOW order statistic is the correct estimator — the class p50 the
keeper ships overstates by that same reasoning. p25 rather than p10 because
runs are computed WITHIN a year, so every run spanning a year boundary splits
into two spurious short ones and p10 absorbs that truncation artifact — the
identical reasoning, pre-registered verbatim, that chose the CT leg's p25
(`nyiso_gas_bridge_ct_min_run_hours`, docs/handoffs/nyiso90-preregistration.md
§2). **No second percentile will be tried; a residual is never grounds to
revisit it (rules 5 / 21 / 23).**

**(c) The basis — plant-summed series, not per-unit.** Bethlehem's per-UNIT
p25 is 13 h (its turbines rotate inside a continuously-online plant), while
its PLANT series starts 6-7 times a year. The mechanism lives on the plant
basis three ways: the floor is `min_load_frac × PLANT capacity` (summed over a
plant's tranches), the LP's per-plant tranches share one plant dispatch
pattern (the model has no unit rotation), and the nyiso-145 object is measured
at 0.05 × plant capacity. The lay-up artifact uses the same construction
("units summed to one PLANT series").

## 3. THE LEVER

`nyiso_gas_bridge_plant_min_run` (`ScenarioConfig`, default off; CLI
`--nyiso-gas-bridge-plant-min-run`): fill each slow-start row's minimum-run
duration from ITS OWN plant's measured value in
`data/raw/_processed-legacy/campd_perplant_min_run_NYISO.csv`
(`scripts/data/derive_campd_perplant_min_run.py`), REPLACING the class scalar
for covered plants — never stacking (rule 19 `[R-ONE-MECH]`; the per-plant
value substitutes inside the same `_nyiso_bridge_min_run_hours` vector the
detector already consumes, so there is exactly ONE minimum-run mechanism).
Uncovered rows keep the class fallback; the CT leg keeps its own required
measured horizon (the artifact never covers `gas_ct` rows).

* **ZERO new fitted scalars** (rule 21 `[R-DOF]`): the artifact is a measured
  per-plant statistic (28 plants), the same DOF shape as the nyiso-144 lay-up
  plant-code set. `n_residual` unchanged. If a tuned multiplier on top were
  ever needed, the lever has FAILED identification and is rejected, not
  patched.
* **Plumbing already existed**: `caiso_ra_mustoffer_min_gen` takes
  `min_run_hours` as an `(n_gen,)` vector; `_nyiso_bridge_min_run_hours`
  already builds it. Zero new detector parameters (the miso-113 per-gen-vector
  precedent).
* **Rule 19 enumeration — what already sets run length for this class**: the
  NREL class table (`COMMITMENT_PARAMS_BY_FUEL`), the two per-class overrides
  (the keeper's 21/13 h), and the min-run leg's gap interaction (an extension
  reaching the next run CLOSES that gap rather than bridging it twice — in the
  detector, unchanged). The per-plant value REPLACES the per-class override
  for covered plants; no second mechanism is added.
* **Excluded, with cause stated ex ante**: the Astoria campus pair
  55375/57664. CAMPD reports both EIA plants under ONE facilityId (55375, all
  four CTs — nyiso-145 §5), so the campus series is boundary-misaligned to
  either plant (rule 14's misalignment clause); both keep the class scalar.
  Plant 2500 (mixed CC/ST classes at one facility) is unattributable at CAMPD
  facility level and keeps the class scalar (the class artifact's own
  convention). Lay-up-excluded plants have artifact rows but the bridge's
  membership gate scopes them out before min-run is read — inert.

## 4. FALSIFIABLE EXPECTATIONS, computed BEFORE the arm solves

Probe `scripts/probes/_nyiso146_k2_prediction.py`, record
`results/calibration/_nyiso146_k2_prediction.json`. The bridge floor is a
DETERMINISTIC function of the base-cost P0 pattern and the config, and P0 is
config-invariant across the arms (the bridge injects at the P0→P1 seam), so
the ARM's floor is computed EXACTLY from a control-side capture — the solves
replay the keeper recipe with zero config delta (the nyiso-145 instrumentation
pattern; nothing registrable).

**EXACT floor predictions (±2 % tolerance for toolchain noise only):**

| year | total bridge floor ctl → arm | 2539 floor ctl → arm | 7314 floor ctl → arm |
|---|---|---|---|
| 2023 | 1.94 → **2.57 TWh** | 779.4 → **1,376.8 GWh** | 130.7 → **121.0 GWh** |
| 2024 | 1.86 → **1.97 TWh** | 490.1 → **602.4 GWh** | 127.0 → **121.6 GWh** |
| 2025 | 1.38 → **1.55 TWh** | 484.5 → **601.2 GWh** | 79.9 → **72.8 GWh** |

Other exact per-plant floor moves recorded in the K2 record and held to the
same ±2 %: Caithness 56234 **55.3 → 133.9 / 40.7 → 156.3 / 32.1 → 158.8
GWh** (its 646 h measured min-run), Valley 56940 **128.5 → 108.3 /
177.9 → 108.7 / 94.4 → 53.7 GWh** (its bimodal p25 of 12 h SHRINKS its
floor), Port Jefferson 2517 **29.8 → 3.2 / 63.2 → 20.3 / 36.5 → 16.1 GWh**
(13 → 3 h — shrinking exactly the forcing nyiso-143 flagged), Cricket 57185
essentially unchanged (19.75 vs 21 h).

**Predicted start-count direction, and the mechanism-shape caveat found by
this instrumentation and REGISTERED BEFORE THE SOLVE:** the min-run extension
floors only hours the unit was OFF in P0. It therefore repairs the 2023-style
shattering — Bethlehem's floored-union on-share jumps **0.64 → 0.92** and its
P0-off fragmentation is glued — but it can only modestly reach 2024/2025,
where P0 already ran Bethlehem near-continuously (union on-share 0.90/0.93
before arming) and the 519/250 P1 starts live INSIDE unfloored P0-on hours,
which no gap/extension floor touches. Gluing those is the ercot141
`floor_online_hours` leg — a DIFFERENT mechanism, deliberately not armed here
(one lever per session); if K3(a) shows the residual fragmentation is
in-run, that leg becomes a named successor candidate. Flynn's floor FALLS
~5-9 % (its measured p25 of 15 h is BELOW the class 21 h) — its start count
is predicted NOT to improve (ADV-4).

**ADVERSE CASES, registered against interest:**

* **ADV-1 — CC_REGULAR forced share RISES** (the floor grows ~+0.6 TWh in
  2023). K4 pre-registers this escalation; it clears only on the two K6′ legs.
* **ADV-2 — Bethlehem's energy rises toward its EIA-923 net** (0.34× at
  control-2023): C1 class-volume errors move; C1 must stay PASS.
* **ADV-3 — 2023's floored volume rises in a year whose C3a is already +9.0 %**:
  C3a must stay inside ±10 % in every year.
* **ADV-4 — Flynn is NOT repaired by this lever** (stated in §1): its
  identified value is BELOW the class scalar, so its start count may tick UP.
  The gate is no-degrade (K3c), and the start-count defect stays on the queue
  as its own object.

## 5. KILL GATES — pre-registered, numeric, evaluated on the committed bundles

**K1 — EXACTNESS.** Exactly ONE `scenario_config` field differs between the
arms: `nyiso_gas_bridge_plant_min_run` False → True. Verified field-by-field
from the two bundles' `run_config.json`. *Fails otherwise.*

**K2 — LIVENESS, two legs.**
(a) *Floor, exact:* each arm-year's total bridge floor volume and the
per-plant floors for 2539 and 7314 land within **±2 %** of §4's predictions
(the tolerance covers toolchain noise only — the computation is
deterministic). A miss means the seam did not deliver the identified vector.
(b) *Starts, banded to the §4 mechanism-shape prediction:* Bethlehem's arm
P1 starts (0.05 × capacity, from the arm's own committed hourlies) fall by
**≥ 50 % in 2023** (the year whose fragmentation is P0-off and now floored)
and by **≥ 10 % in 2024 and 2025** (where the reachable share is small — §4).
An inert arm (floors unchanged, starts unchanged) fails — the nyiso-89 §4a
"mechanism does nothing" failure mode.

**K3 — THE OBJECT ITSELF.**
(a) 2539's P1 starts move toward metered in all three years (arm < control),
and its P1 median run length RISES in all three years.
(b) No-degrade cohort — for each plant-year of {56940 Valley, 55405 Athens,
56196 Poletti, 2511 Barrett, 2500, 50292 Bethpage, 57185-2024/25,
56234-2024/25}: the arm's start-count error vs metered stays within
`1.5 × control error + 5 starts`. (Proportional so the bar measures
DEGRADATION rather than penalizing plants whose control error is already
large — e.g. Valley's control is 73 starts vs 11 metered; a flat band would
make the gate about the control's own defect.)
(c) 7314 Flynn no-degrade: arm P1 starts ≤ control + 25 %.
Start counts for plants absent from the run payload are measured from the
bundles' own per-plant hourlies with the same 0.05 × capacity rule.

Numeric baselines, fixed ex ante (metered = plant-basis CAMPD run counts per
year from the phase-0 record; control = keeper committed payload where
present, else measured from the control bundle at scoring time):

| plant | metered starts 23/24/25 | control P1 starts 23/24/25 |
|---|---|---|
| 2539 Bethlehem | 6 / 7 / 7 | 320 / 519 / 250 |
| 7314 Flynn | 115 / 78 / 103 | 241 / 327 / 237 |
| 56234 Caithness | 4 / 6 / 8 | 100 / 6 / 15 |
| 56940 Valley | 11 / 3 / 8 | 73 / 11 / 21 |
| 55405 Athens | 29 / 13 / 63 | 110 / 43 / 62 |
| 57185 Cricket Valley | 23 / 20 / 13 | 181 / 24 / 31 |
| 56196 Poletti | 9 / 5 / 11 | 4 / 7 / 8 |
| 50292 Bethpage | 63 / 109 / 64 | (from control bundle) |
| 2511 Barrett | 42 / 45 / 36 | (from control bundle) |
| 2517 Port Jefferson | 149 / 195 / 161 | (from control bundle) |

(56234-2023 is NOT in the no-degrade cohort: the control over-starts it 100
vs 4 metered, so 2023 belongs to the improvement leg's spirit; its floor more
than doubles and its runs merge under a 646 h measured min-run.)

**K4 — D-4 / D-2, the K6′ two-leg escalation (nyiso-143/144 form).** Zero NEW
D-4 unit-conduct failures vs control (same-vintage comparison, both arms on
the same EIA-923 vintages). The CC_REGULAR forced-share RISE is pre-registered
(ADV-1) and escalates rather than kills: the arm passes only if (a) zero new
D-4 failures anywhere and (b) zero new D-1 shape misses. C8 stays PASS (under
its budget caps) in every year.

**K5 — GATED CRITERIA.** C1 / C2 / C3a / C3b / C4 / C6 / C8: no PASS → FAIL
against the control in any year. C3c is the standing ledgered caveat: reported
at full magnitude, never gated, and NOT reached back by any route (the
nyiso-144 tail anatomy is CLOSED — the real tail is NYCA-wide, not
Long-Island-locational).

**K6 — LEAVE-ONE-YEAR-OUT stability (rule 22) before any promotion.**
(a) *Derive-side, MEASURED BEFORE THIS PREREG WAS COMMITTED* (no solve — a
phase-0-class data measurement): re-derive the artifact on each 2-year subset
(2023-24, 2023-25, 2024-25). Bars: for the object plant 2539 the LOO p25 stays
**> 2× the class scalar (42 h)** in every subset and **> 100 h** in at least
2 of 3; for every live plant the LOO value stays on the same side of its class
scalar in at least 2 of 3 subsets. Measured: 2539 = 137 / 47 / 167.75 h
(clears both legs); side-stability 3/3 for 14 of 16 live plants and 2/3 for
the two bimodal ones (56940 Valley, 57185 Cricket) — **K6(a) CLEARS ex ante**
and is recorded here so the solve cannot re-litigate it.
(b) *Gate-side:* K2(b) and K3(a) hold in each year SEPARATELY (already
per-year above), so no single year carries the verdict.

**PROMOTE CRITERION: K1–K6 clean (K4 may escalate and clear).** Not "the fit
improves". Under rule 1 `[R-STRUCT]` a measured commitment structure stays in
even if the residual worsens; a worse fit is a discovered bug whose root cause
becomes the successor, never a reason to revert (rule 14).

## 6. WHAT THIS ARM IS NOT

* Not `startup_aware` (carries the ERCOT-63 refusal; PRUNES floors — the wrong
  direction for this object; not armed, not tested).
* Not a fuel-price, heat-rate, or outage change for 7314 — all three refuted
  at nyiso-145 §4 (DO-NOT-REDO).
* Not an extension of `nyiso_downstate_ct_gas_daily` to the LI CC/ST fleet
  (refuted on EIA-923 Schedule 5 evidence, nyiso-145 §4a).
* Not the merit-order inversion on mothballed small CCs (defect B) — the named
  SUCCESSOR, a duty-role offer-shape object, one pre-registered lever per
  session.
* Not a change to the bridge's min-load fractions, its window, its physics
  gate, or its membership exclusions.
* Not a benchmark change: the Astoria campus attribution stays untouched (out
  of lane; needs its own pre-registration).
* Not transferable (rule 25 / 28(d)): this verdict fills no other ISO's cell.

## 7. REPRODUCTION

```
# identification artifact (rule 23; re-derives only when CAMPD updates)
python scripts/data/derive_campd_perplant_min_run.py --iso NYISO

# phase-0 measurement + K2 prediction (instrumentation, no bundle)
python scripts/probes/_nyiso146_perplant_minrun_phase0.py
python scripts/probes/_nyiso146_k2_prediction.py

# control — the keeper recipe replayed at HEAD
python scripts/run_calibration_full.py \
  --replay-bundle results/calibration/nyiso144_layup_arm \
  --out-dir results/calibration/nyiso146_control

# arm — the same recipe + the one field
python scripts/run_calibration_full.py \
  --replay-bundle results/calibration/nyiso146_arm_recipe \
  --out-dir results/calibration/nyiso146_perplant_arm
```

(the arm recipe is the keeper's `meta.json` with
`nyiso_gas_bridge_plant_min_run: true` — the replay path takes the whole
config from the bundle, so the flag is set in the recipe rather than on the
command line.)
