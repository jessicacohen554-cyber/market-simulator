# DIAGNOSIS — ERCOT-121: fleet representation audit (coal ceiling, CC capacity basis, curtailment reconciliation, minor classes, storage)

**Date** 2026-07-27 · **ISO** ERCOT · **Lane** ercot121-fleet-repr ·
**Keeper under audit** `2026-07-26-ercot115-coal-marginal-hr` (bundle
`results/calibration/ercot115_coal_floor_only`) — unchanged by this session ·
**Method** Phase 1 is diagnostic only: committed sidecars/payload/bench + code
reading, plus ONE byte-faithful keeper replay for unit-grain evidence (the
sanctioned R-DASHBOARD unit-level exception: `replay_keeper` with **no
`--set`** into `results/calibration/_diag_ercot121fleetrepr_keeper_replay`,
NOT registered; fidelity verified — replay-vs-keeper class energy differs by
**0.0000 TWh in every class-year**, coal 59.342/57.323/60.289 TWh exact).
Environment parity matched the ercot115–119 baselines (fresh container,
gtc-limits clean partition absent → "static TTC kept" fallback; the known
lineage `ercot_wtx_curtailment_driver` kwarg-vs-prb stomp WARNING appeared,
prb `True` active as in every baseline).

Each owner observation gets: the measured evidence, a named root cause, and a
routed fix. §2 ships the one code change of this session (the C7/C8 scorer
correction). §3 is the Phase-2 re-evaluation of the already-solved measured
coal availability envelope (`ercot116_coal_avail_on_keeper`).

---

## 1. The six observations

### 1a. Oak Grove / lignite pinned at 100 % (observation #1)

**Evidence (payload/bench per-plant hourlies; replay tranche grain).** The
model does not run Oak Grove (6180, npl 1,795 MW) at 100 % of *nameplate*; it
runs it at 100 % of its *availability ceiling* essentially every summer hour:

- Measured ceiling plateaus (replay, exact): **summer 1,658.7 MW = 0.924 ×
  npl**, winter/shoulder ~1,597 MW = 0.890 × npl.
- Hours AT the ceiling, Jun–Sep: **2,848 of 2,928 h (2023)** — July is
  744/744 — 2,392 h (2024), 2,084 h (2025). The actual plant: **12 h / 2 h /
  623 h** at its own monthly max; actual Jun–Sep mean CF 0.757/0.746/0.736 vs
  model 0.919/0.839/0.753 (2025's March–May outages pull the model's summer
  mean down; the at-ceiling behaviour persists).
- Tranche decomposition (replay, July 2023): **all five tranches — mustrun
  746.4, committed 165.9, econ_lo 368.9, econ_hi 294.6, and the peak tranche
  82.9 MW — sit at max 744/744 h.** The offer curve is entirely in merit; the
  only binding constraint is the ceiling itself.
- The ceiling decomposes as npl × **statistical availability** (winter 0.890 =
  1 − WEFOR_residual − flat performance derate; summer 0.9665 after the
  summer-share WEFOR reallocation) × **net-summer derate 0.952** (summer
  months only) — `data/fleet/arrays.py` availability loop +
  `coal_nameplate_summer_derate`. CAMPD ≥5-day outage windows overlay the big
  dips (Mar-2023 0.487, Mar-2024 0.095, May-2025 0.127 monthly means).

**Named root cause — option (c) of the charter: the availability envelope,
not the derate.** The summer ceiling *level* is right: 0.920–0.924 × npl vs
the plant's CEMS summer max 0.937–0.94 (the derate is active and slightly
conservative). What is wrong is **utilization of the ceiling ≈ 100 % for
whole months**: the statistical availability is deterministic and month-flat
(the backcast caps coal WEFOR at the short-outage residual because the CAMPD
overlay carries ≥5-day events — so *sub-5-day forced outages and partial
derates are represented only as a flat haircut, never as events*), and
lignite's offer position keeps every tranche in merit, so the LP rides the
flat ceiling. The real fleet's summer mean runs ~0.16–0.20 *below* its own
ceiling with short dips and excursions. This is the exact D-1 signature the
scorer was blind to (§2): COAL_LIGNITE 2023 profile r 0.745, off-peak CV
ratio **0.294** (model CV 0.017 vs actual 0.057).

A **new age-based derate is the wrong fix** and is not admissible here: the
ceiling *level* already matches the measured CEMS maxima for the pinned
plants (age-based WEFOR/derate escalation already exists in
`THERMAL_AVAILABILITY`), so an age haircut would cut a quantity that is not
wrong — and stacking it on the availability phenomenon would violate rule 19
`[R-ONE-MECH]`. The measured per-plant DAM availability envelope
(`ercot_thermal_dam_availability_coal`, already built and solved as
`ercot116_coal_avail_on_keeper`) is the rule-14 replacement for the
statistical estimate — §3 for its own merits.

**Per-plant heterogeneity the class view hides** (2023 numbers; same pattern
2024–25): the ceiling is *too high in utilization* for Oak Grove / Martin
Lake (918 h ≥0.95 npl vs 10 actual) / Fayette (1,131 h ≥0.90 vs 96), but
**too LOW in level** for J K Spruce (model max 0.886–0.888 × npl vs actual
routinely ≥0.90; model 3.59 TWh vs actual 5.10 — the model under-runs Spruce
every year) and Sandy Creek (model max 0.899 vs actual max 0.991). The
measured envelope fixes both directions by construction.

Two data defects found on the way:

- **Sandy Creek (56611) is absent from the model in 2025** (0.00 TWh) while
  CEMS shows 0.71 TWh through its actual ~May-2025 shutdown — a retirement
  effective-date error (model retires it at year-start). Worth a one-line fix
  in the retirement data; ~0.4–0.7 TWh of 2025 PRB deficit.
- **W A Parish (3470) contaminates plant-grain "coal" actuals**: the CAMPD
  bench series for 3470 is whole-plant (coal + its gas steamers), so its
  "actual" reaches 1.36–1.40 × the coal-side npl (2443 MW) and its actual
  TWh (10.75/12.16/15.51) overstates coal. C1 is unaffected (EIA-923
  rank-resolved), but the D-1 COAL_PRB actual profile and any per-plant
  eyeball comparison carry Parish's gas units.

### 1b. COAL_PRB seasonal misallocation (observation #2)

Monthly class means (model vs bench-actual, GW). With the bench actual as-is
(Parish gas included), the keeper runs **−1.2 to −1.8 GW under in
Nov/Dec–Apr and +0.4 to +1.4 GW over in Jun–Sep** — the owner's "up to 2 GW"
pattern, reproduced (2024: Aug +1.44, Apr −1.83). Excluding Parish from the
actual side (the gas contamination), the summer excess is larger (+2.0 to
+3.6 GW) and the shoulder deficit confines to Feb–Apr.

**Named root cause: the same statistical-availability seasonal shape.** The
statistical model books the entire planned-outage (POF) budget as a flat
shoulder-month block — too deep in Feb–Apr (the model's coal is
availability-capped below what the real fleet had live) — while summer sits
on the flat too-generous plateau of §1a. This is exactly what the ERCOT-116
pre-commit measured: the matched-price-band summer-minus-shoulder excess is
**19.2/18.6/20.6 pp** in the keeper and the measured envelope removes
**−9.1/−5.7/−7.2 pp** of it (G1 PASS) and narrows the monthly-ratio spread in
every year (G2 PASS). The remaining ~10–13 pp is within-envelope economic
over-dispatch at matched price — the coal offer-level successor question
(§3).

### 1c. C7/C8 protective-gate blindness (the highest-value check) — CONFIRMED, fixed, shipped

Two distinct blind spots, both confirmed and both corrected **scorer-side**
in `scripts/calibration_verdict.py` (rubric v2.8, commit `ab7ce17` on this
branch; committed artifacts re-score in place, no regeneration):

1. **C8 vocabulary bug.** The D-2 per-class summary labels classes by CAMPD
   `plant_group` — ERCOT/MISO/PJM coal plants are `"COAL"` — while the
   payload `gmModel` / bench `classFull` carry the scored-class rank split
   (`COAL_LIGNITE`/`COAL_PRB`/…; the payload's vestigial `COAL` key is 0.0).
   `_class_load_share("COAL")` read 0.0 TWh on both sides → share 0.0 % →
   `SKIPPED … COAL immaterial (0.0% of ISO load)` — **while the artifact's own
   `load_share` field said 14.2/13.1/13.2 % (ERCOT), 32.6–35.8 % (MISO),
   14.0–16.2 % (PJM), `immaterial: false`.** The C8 gate had never actually
   scored any coal fleet. Fixed with a `PLANT_GROUP_MEMBERS` aggregate bridge
   in `_class_load_share`.
2. **C7 gate-set scope.** `score_shape` scored only artifact-baked
   `gated=True` D-1 rows, and `D1_GATED_CLASSES` was `("CT_PEAKER",
   "ST_GAS")` — so a merchant-coal class pinned flat (the exact caiso-42
   flat-floor signature C7 exists to catch) was *reported* by D-1 and never
   *scored*. C7 now derives gatedness rubric-side (`C7_GATED_CLASSES` =
   peaker/intermediate + merchant coal; CHP stays ungated — host-steam-pinned
   duty, the same structural rationale as `D2_EXEMPT_CLASSES`; CC_REGULAR
   ungated pending an owner call) and evaluates each row's stored
   `profile_r`/`cv_ratio` against the artifact's gates block — the same
   measured-value-overrides-baked-verdict design C8 has used since v2.1.
   Verified zero drift vs every baked verdict on previously-gated rows across
   all six keepers.

**Re-score effects (all six keepers, before → after):**

| ISO keeper | determination | C7/C8 change |
|---|---|---|
| ERCOT-115 | NOT-YET → NOT-YET | **C7 PASS → FAIL** (COAL_LIGNITE 2023 r 0.745 / cv_ratio 0.294 — machine confirmation of observation #1); C8 COAL rows SKIPPED → PASS ×3 |
| MISO-88 | **CALIBRATED-WITH-CAVEATS → NOT-YET** | C7 FAIL COAL_PRB **all three years** (cv_ratio 0.453/0.441/0.364 on a 33–36 %-of-load class); C8 COAL SKIPPED → PASS ×3 |
| PJM-121 | CALIBRATED (unchanged) | COAL_BIT gates and passes (r 0.835–0.884, cv 0.85–1.16); COAL_PRB/WC immaterial; C8 COAL SKIPPED → PASS ×3 |
| CAISO-126 / NYISO-81 | unchanged | no coal D-1 rows |
| NEISO-61 | unchanged | COAL_BIT 0.2–0.3 TWh immaterial-skip |

No C8 verdict flips anywhere: every coal fleet's non-exempt forced share is
0.0–0.4 % (coal floors are exempt take-or-pay mechanisms), so the newly-gated
rows all PASS — the correction closes the blindness rather than reversing any
C8 outcome. The MISO determination flip is reported here per the charter
("treat a flip as evidence to report, never as something to suppress") and is
an honest new open item in the MISO lane (model PRB held ~2× too flat
off-peak), exactly like the v2.7 NYISO flip.

### 1d. CC_REGULAR CF-band distribution (observation #3)

**Evidence.** Capacity-weighted hours-by-CF-band (37 CC plants, 30.8 GW bench
npl), model vs CAMPD:

| band | 2023 m−a | 2024 m−a | 2025 m−a |
|---|---|---|---|
| [0.0,0.2) | −624 h | −654 h | −479 h |
| [0.6,0.8) | **+2,199 h** | **+2,288 h** | **+1,838 h** |
| [0.8,∞) | **−1,599 h** | **−1,685 h** | −1,061 h |

**The capacity-basis hypothesis is REFUTED as the driver.** Re-basing the
actual side on the CAMPD sustained peak (`cc_capacity_reconcile_ERCOT.csv`,
8 plants / 8.5 GW raised +4.8–11.2 %) moves the actual band counts by **< 60
h** — two orders of magnitude smaller than the bulge. The reconcile fix is
real but tiny; arming `cc_capacity_reconcile` cannot explain observation #3.

**Named root cause, from the replay tranche grain:** two stacked effects,
neither a nameplate artifact.

1. **Dispatch spreading on a too-flat inter-plant CC offer surface.** The
   biggest CCs' *non-peak* tranches alone reach 0.90–0.93 × npl (peak
   tranches are tiny: e.g. 55480 peak max 22 MW of 1,894), so there is no
   tranche wall at 0.8. The LP simply spreads the CC block across many plants
   at their similarly-priced econ tranches — 55480 spends 5,276 h in
   [0.6,0.8) — where the real market concentrates the efficient plants at
   0.8–1.08 (actual max CF exceeds 1.0×npl at 4+ plants every year) and
   cycles the inefficient ones off (hence the model's −500/−650 h deficit in
   the <0.2 band too).
2. **The measured availability top-cap**: model plant maxima are 0.90–0.93 ×
   npl (the measured DAM COP live fraction), while real operation exceeds
   nameplate (1.03–1.16 on the reconcile plants — the understated-capacity
   leg, small).

**Routed fix:** an offer-surface *dispersion* question (per-plant heat-rate
ranking of the CC econ bands — measured per resource in the 60-Day
disclosure), explicitly distinct from the per-year *level* rebasis that
ERCOT-119 closed as a C3c fix. Any arm is its own pre-committed single delta;
this lane routes it behind ERCOT-120 (the owner's queue order stands).
`cc_capacity_reconcile` may ride along as a measured input but is not the
explanation.

### 1e. Wind/solar vs actual — curtailment reconciliation (observation #4)

**Confirmed: not a data mismatch.** ERCOT wind/solar bounds are the NP6 HSL
*uncurtailed potential* (`renewable_bound_provenance = measured_potential`;
model dispatch never exceeds potential: 0 violation hours), and the LP
re-curtails endogenously (rule 3). Model-minus-actual **is** the model's
curtailment decision vs ERCOT's realized curtailment. The reconciliation
(`data/raw/ercot-hsl/ercot_<y>_hsl_hourly.parquet`, potential − delivered =
reported curtailment):

| year | tech | potential TWh | reported curt | model curt | model − reported |
|---|---|---|---|---|---|
| 2023 | wind | 114.04 | 6.03 (5.3 %) | 5.63 (4.9 %) | −0.40 |
| 2023 | solar | 34.25 | 2.37 (6.9 %) | 1.52 (4.4 %) | −0.85 |
| 2024 | wind | 118.71 | 7.17 (6.0 %) | 6.38 (5.4 %) | −0.79 |
| 2024 | solar | 51.42 | 3.72 (7.2 %) | 2.52 (4.9 %) | −1.20 |
| 2025 | wind | 123.69 | 8.76 (7.1 %) | 6.89 (5.6 %) | **−1.87** |
| 2025 | solar | 72.83 | 5.31 (7.3 %) | 4.23 (5.8 %) | −1.08 |

The model **under-curtails** both techs every year, increasingly with the
2025 buildout; the model's extra delivered wind/solar is exactly the owner's
observed wind gap. Monthly shape tracks (spring/fall congestion peaks
reproduced, shallower); the **intraday locus diverges for wind**:
hour-of-day curtailment correlation 0.610 (2023) → 0.459 (2024) →
**−0.079 (2025)** — the model curtails wind in overnight economic troughs
(peak h22–23) while real 2025 curtailment peaks mid-afternoon (h15–16,
solar-flood congestion hours). Solar shape corr stays 0.82–0.97. Zonal 2023
(NP4-742/745 regions; region↔zone crosswalk is approximate): measured
panhandle-region curtailment 9.3 % of potential (1.53 TWh) vs the model's
~2 % on its Panhandle zone — the missing curtailment concentrates in the
corridor.

**The wtx-driver double-count question, answered:**

- **West: no double-count.** The model's West zone price-separates from North
  in only **5/17/7 hours** (>$1) across 2023–25 — the zonal West→North pipe
  indeed never binds, so the driver is the *sole* congestion mechanism there
  (rule 19 satisfied; exactly the reduced-form role the module documents).
- **Panhandle: the two mechanisms stack.** Panhandle price-separates
  **2,708/3,221/4,074 h** — the zonal ties DO bind endogenously — and the
  driver's ceiling (active ~8,750 h/yr at a mean ~6.5 % cut in those hours,
  `WEST_CORRIDOR_ZONES = ("West","Panhandle")`) overlaps **100 %** of those
  hours. Because `depth` was identified jointly (LOYO, with the endogenous
  ties live), the *level* is calibrated-not-double-counted — but attribution
  between the driver and the tie is opaque, and the net result still
  under-curtails.

**Routed fix:** the volume gap is dominated by **solar** (−0.85/−1.20/−1.08
TWh, and the 2025 wind midday miss is solar-coincident congestion). Candidate
single-delta probes, each requiring its own pre-commit: (i) re-derive the
driver's solar depth / extend the congestion-share table's coverage of
solar-flood hours from the same NP6-86 SCED incidence (measured, rule-14
admissible); (ii) scope the driver to West-only and let the Panhandle tie
carry its own congestion (removes the rule-19 stack; expect the Panhandle
delta to need a TTC re-check first). Not pursued in this lane.

### 1f. biomass / geothermal / OTHER (observation #5)

- **biomass (0.41 TWh)** and **OTHER (1.99 TWh, other/process-gas·waste-heat·
  petcoke)** are measured EIA-923 must-run *injections* (netted from demand,
  re-added as pseudo-units; `inject_biomass_mustrun` — raw biomass LP units
  dropped so nothing is served twice). They equal their measured annual
  energy **by construction**; they are price-insensitive in the LP exactly as
  they are in reality (fuel/contract-limited). Forward analogue: vintage-carry
  of the 923 profile — rule-13 admissible.
- **geothermal is correctly absent**: ERCOT has no utility-scale geothermal;
  the class exists only in CAISO.
- **hydro (0.35 TWh)** is an LP resource under measured monthly energy
  budgets (annual pinned by budget, hourly free); **oil** is dispatched
  (model 0.03 vs actual 0.15 TWh — immaterial).
- **What the owner saw on the dashboard is a definitional gap, not a model
  gap**: the Charts-tab `other` panel compares the model's 923-defined
  injection (OTHER 1.99 + biomass 0.41 = 2.40 TWh) against **EIA-930's ERCO
  "Other" cell (1.15 TWh in 2023, collapsing to 0.27 in 2025** as ERCO's BA
  reporting re-buckets those plants into NG) — two different vocabularies;
  and the hydro/oil panels draw no 930 actual at all (no ERCO breakout).
  None of these classes is C1-scored (`FUELMIX_EXCLUDED` = CT_CHP, OTHER,
  OTHER_FOSSIL; C1 gates gas+coal classes only) and C2's family fallback
  re-buckets the mixed plants, so **no scoring is distorted**.
- Verdict: **immaterial and correctly represented, with one real defect
  found nearby** — the Sandy Creek 2025 retirement dating error (§1a), which
  belongs to the coal fleet, not these classes.

### 1g. Storage capacity confidence (observation #6)

The keeper's ERCOT battery fleet is on the **measured** basis
(`ercot_storage_capability_measured=True`): hourly ISO-wide registered
non-OUT HSL from the 60-Day DAM disclosure
(`data/raw/ercot-storage-capability.csv`) — mean **2.88 GW (2023, max
4.19)**, **6.54 GW (2024, max 9.67)**, **11.43 GW (2025, max 14.99)** —
allocated to zones by EIA-860 power shares, energy = power × EIA-860 fleet
duration, RTE 0.85 (4 h) / 0.80 (8 h) from `ScenarioConfig`. This replaced
the EIA-860 COD ramp the summer-availability audit measured ~2 GW low
(5.8 vs 7.7 GW Aug-2024, 10.6 vs 12.5 GW Jul-2025). Known hole: Oct-2023
(720 NaN hours → EIA-860 fallback). `storage_deployment="mid"` is the
forecast-side scenario only; the backcast fleet is measured.

**Confidence: power capability HIGH** (measured hourly, embeds CODs, hybrid
halves and real outages); **duration/energy MEDIUM** (EIA-860 fleet
duration; the audit found the energy envelope feasible); **RTE is a cited
config constant**; **dispatch volume runs LOW vs the observed EIA-930
months**: model discharge 0.70/1.81/3.98 TWh vs bench-observed Nov/Dec-2024
211/146 vs 296/338 GWh and 2025 3.98 vs 5.46 TWh (~27 % under) — reported as
a diagnostic only (C5b/C5c were removed from the rubric v2.7 because EIA-930
storage data is not gate-grade). The capacity representation is not the
limiting uncertainty; the dispatch/AS-deployment split is.

---

## 2. Shipped this session

1. **Rubric v2.8 scorer correction** (`scripts/calibration_verdict.py`,
   `scripts/legitimacy_diagnostics.py` D1_GATED_CLASSES, tests, rubric doc
   §C7 + §9 v2.8 entry) — §1c above. Commit `ab7ce17`.
2. This diagnosis.
3. §3's Phase-2 artifacts on the `ercot116_coal_avail_on_keeper` bundle
   (legitimacy artifact + rubric re-score; no re-solve).

## 3. Phase 2 — the measured coal DAM availability envelope on its own merits

*(`ercot116_coal_avail_on_keeper` — already solved 2026-07-26 as keeper + the
single `ercot_thermal_dam_availability_coal=true` delta; run id
`2026-07-26-ercot116-coal-avail-probe`, registered NOT-YET. No re-solve in
this session.)*

**Verbatim pre-committed scorer** (`scripts/probes/ercot116_seasonal_shape.py`
— thresholds fixed 2026-07-26 before any arm year was solved), reproduced
exactly this session:

| gate | result |
|---|---|
| G1 matched-band excess −≥5 pp every year | **PASS** — 19.18/18.57/20.59 → 10.04/12.87/13.38 |
| G2 spread narrows every year, mean ≥0.10 | **PASS** — +0.435/+0.591/+0.333 → +0.233/+0.400/+0.230 |
| G3 scarcity (C3a ≤2 pp, C3c ≤5 h vs keeper) | **FAIL** — C3a −16.6→−24.2 / +1.3→−5.7 / +1.5→−4.1 (7.6/7.0/5.6 pp); C3c 72→49/13→7/1→1 |
| BITE | PASS — coal +6.8/+9.2/+12.9 TWh |

**Does the envelope un-pin Oak Grove? Yes — the pin, not the level.**
Jun–Sep at-max hours collapse **2,848 → 798 (2023), 2,392 → 552 (2024),
2,084 → 492 (2025)** (actual: 12/2/623), and the D-1 lignite profile
improves in every year (committed-artifact values — 2023 r 0.745→0.792,
cv_ratio 0.294→0.426; 2024 0.862→0.952 / 1.117→0.986; 2025 0.913→0.949 /
1.612→1.341) — but 2023 still sits below
both D-1 gates: the measured envelope removes the *availability* half of the
pin and leaves the *dispatch* half (no economic load-following at lignite's
modeled offer). And the summer **level moves away from actual**: arm Jun–Sep
mean 0.952/0.916/0.879 × npl vs actual 0.757/0.746/0.736 — the measured
series tops at 1.0 × npl (it supersedes the net-summer cap; the model then
dispatches the full declared availability), which is exactly the
within-envelope economic over-dispatch the ERCOT-116 pre-commit named as the
successor question (model coal SRMC top ~$28 vs the real fleet's ~$21+ top
submitted DAM offer, the F923 delivered-price lead).

**Full rubric on the arm** (C7/C8 scored from the legitimacy artifact
generated this session into the bundle; determination **NOT-YET**): C1 FAIL
15/16 · free 11/12 (COAL_PRB 2025 +8.66 TWh — the envelope's known level
uplift), C2 PASS, C3a FAIL all years on the v2.4 load-weighted basis —
keeper −26.9 %/−7.7/−7.6 (FAIL/PASS/PASS) → arm **−35.2/−14.5/−13.0 (all
FAIL — the two keeper passes flip)**, C3b/C3c FAIL, **C4 FAIL — new vs
keeper** (2024 coal r 0.864/NRMSE 0.301 vs the keeper's passing
0.848/0.271; the envelope's redistributed coal trades correlation for
volume), C5a PASS, C6 UNATTESTED, **C7 FAIL 2023 via COAL_LIGNITE (r 0.792,
cv_ratio 0.426 — improved from the keeper's 0.745/0.294 but still below
both gates)** with all 2024/2025 coal rows passing, C8 PASS (coal 0.0 %
forced, load_share 14.5–15.0 % properly resolved under the v2.8 bridge).

**Recommendation (recommend-and-STOP; keeper untouched, owner decides):**

1. **Do not promote `ercot116` alone.** Its own pre-committed G3 gate fails
   reproducibly (C3a −7.6/−7.0/−5.6 pp — the envelope's added coal energy
   suppresses prices the keeper was holding up by under-carrying coal), its
   C1 coal level regresses (predicted, reported-not-gated), and §3's summer
   level moves away from actual. Under rules 13/14 these are *discovered
   compensations* — the statistical availability was hiding a coal
   offer-level error — but a keeper promotion on a net-worse rubric with the
   root cause identified and unfixed would be premature.
2. **The envelope is the right availability-side half and the promotion
   candidate for #1/#2 remains envelope + measured coal offer top as ONE
   pre-committed successor arm** (ERCOT-122 candidate, behind the owner's
   ERCOT-120 queue): `ercot_thermal_dam_availability_coal=true` + the coal
   econ/peak band tops re-derived from measured delivered coal cost (F923)
   and/or the measured top-of-curve submitted coal offers — measured inputs,
   not fitted values (rules 13/23), with G1/G2-style shape gates AND a C3a/
   C3c gate fixed ex ante. If that arm passes, it un-pins Oak Grove (#1),
   fixes the PRB seasonal shape (#2), and removes a fitted availability
   estimate — three of the owner's items with two measured inputs.
3. No new derate mechanism (age-based or otherwise) — §1a; the quantity an
   age derate would cut is not the quantity that is wrong.

## 4. Closed items honoured

No re-solve of any registered configuration; no keeper file touched; the
EP-rebasis C3c lane, peak-p50/quantile-ladder legs, pooled HH-0.50
artifacts, `ercot_zonal_gas_basis` ablations, West/Panhandle topology split,
and the committed-band data gap all stay closed per their findings; ERCOT-120
stays queued next, un-renumbered. Holdout years untouched (span exactly
{2023, 2024, 2025}). The diagnostic replay bundle is unregistered by design
and carries a note naming this exception.
