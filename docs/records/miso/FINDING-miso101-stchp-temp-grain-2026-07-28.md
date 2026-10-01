# FINDING miso-101 — the hour-grain diurnal temperature input is BUILT, MISO's own derate slope and onset are DERIVED, and the arm puts the measured wave on the floored cogens: Beaumont goes from byte-flat to r = +0.96…+0.98 against its own meter with every pre-registered gate passing

**Lane:** the arm lane FINDING-miso100 §7 proposed and the owner pre-authorized.
Rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]` in force: structural fidelity is the
objective, and an admissible physical input is never reverted on fit alone.
**Pre-registration:** `PREREG-miso101-stchp-temp-grain-2026-07-28.md`, committed
before either arm was solved (commit `4a4cfcf`). Runs:
`2026-07-28-miso-101a-control` / `2026-07-28-miso-101b-tempgrain`.
Matrix: `temp_dependent_derate` MISO `U` → **`K`** (duty (b), this session).

---

## 0. Summary

1. **The hour-of-day temperature grain did not exist anywhere in the model, and
   now does.** `iso_zone_tmax` broadcasts daily TMAX flat within the day, so the
   temperature-derate curve — even armed — carried zero diurnal signal.
   `iso_zone_hourly_drybulb` reconstructs the within-day wave from the same
   curated daily TMIN/TMAX via the standard climatological two-piece cosine
   bridge. **No new floor and no new mechanism** (rule 19 `[R-ONE-MECH]`): the
   existing `MECH_CHP_STEAM` floor is already clipped to `pmax × availability`,
   so the finer availability shape propagates to every floored cogen by itself.

2. **MISO's own identification refutes the committed slope AND the committed
   onset.** Within-day plant-day fixed-effects regression over the six
   CEMS-identifiable MISO cogens, 2023–25: capacity-weighted p50 =
   **0.00141/°C**, ~5× below the committed literature CC slope (0.0076/°C).
   The onset scan finds **no 15 °C hinge** — the response is measured at
   0.0036/0.0030 per °C in the 5–10/10–15 °C bins (r −0.38/−0.28) where
   `max(0, T − 15)` is identically flat. MISO's own confirmation of pjm-95
   (rule 25 `[R-ISO-SCOPE]`).

3. **The metered machine is a gas turbine, not a boiler.** Beaumont's CEMS units
   are 3 × combined cycle; the only other substantial CEMS cogen meter is a
   26 MW CT. FINDING-miso100's condenser-back-pressure framing was directionally
   right about *temperature* but pointed at the wrong slope family — and the GT
   physics is exactly why the winter wave survives with no onset.

4. **All four pre-registered gates PASS in all three years.** Beaumont's model
   slice goes from **byte-flat** to a wave troughing h15 — the meter's own
   trough hour — correlating **+0.964 / +0.958 / +0.984** with its CEMS
   hour-of-day profile.

5. **The control reproduces the committed keeper to 0.00000 %** on every class
   in every year, so the A/B is a true single-delta test and the five new
   `ScenarioConfig` fields are provably inert when off.

6. **Nothing regressed on any gate.** D-1 `profile_r` improves in every year for
   both in-scope classes; the C-series rubric is **identical** between arms. One
   pre-registered prediction (P6) was **wrong in direction** and is recorded as
   such in §5.

## 1. The identification

`scripts/data/derive_campd_temp_derate_params.py --iso MISO` →
`data/raw/_processed-legacy/campd_temp_derate_params_MISO.csv` (+ `_onset`,
`_phase`).

**Estimator.** Within-day, **plant-day fixed-effects** regression of
`log(CEMS gross load)` on the hour-grain dry-bulb: both series demeaned inside
each (plant, day), so every day-level confounder — outage, host steam demand,
fuel switch, maintenance season — differences away and the OLS coefficient is
directly a *fractional* capability response per °C. Conditioned on the unit
being online (p99.5 HSL proxy, 20 % floor — the repo's existing
`derive_campd_gas_commitment_params` convention). The temperature series is the
model's own `diurnal_drybulb_from_daily`, imported, so derivation and LP cannot
drift apart.

*(A first version demeaned per DATE rather than per PLANT-day. That leaks
cross-plant level and cross-zone temperature into both regressors and produced a
pooled slope of −0.069/°C — an order of magnitude outside every individual
plant's range. Caught and fixed before any parameter was taken; the corrected
fit also moved the phase-scan optimum to exactly lag 0.)*

| plant | zone | GWh/yr | HSL MW | within-day slope /°C | r |
|---|---|--:|--:|--:|--:|
| ExxonMobil Beaumont Refinery `50625` | MISO-South | 6034 | 892 | **+0.00399** | −0.362 |
| Dearborn Industrial Generation `55088` | MISO-East | 3494 | 591 | −0.00699 | +0.178 |
| Louisiana 1 `1391` | MISO-South | 3483 | 695 | +0.00141 | −0.119 |
| Primient `64854` | MISO-Indiana | 689 | 87 | +0.00060 | −0.054 |
| Portside Energy `55096` | MISO-Indiana | 75 | 32 | +0.00080 | −0.082 |
| Otsego Paper `55799` | MISO-East | 70 | 24 | +0.00447 | −0.129 |

**Class parameter = capacity-weighted p50 = 0.00141/°C** — the same population
statistic `derive_campd_gas_commitment_params.py` uses for `min_load_frac`.

**No screen is applied, and the hypothesis that would have justified one is
refuted by the data.** The tempting move is to pin the identification to the
most capability-limited plant, arguing merchant dispatch biases the others'
meters downward. That premise predicts the most-pinned plants show the LARGEST
slope. MISO's most-pinned cogens show the **smallest** — Primient (online
CV 0.094) +0.00060, Portside (CV 0.058) +0.00080 — against Beaumont (CV 0.159)
+0.00399. Beaumont and Dearborn are indistinguishable on every a-priori
pinnedness metric (loading ratio 0.80 vs 0.81) yet have opposite-signed slopes.
So the class-population statistic stands and the armed slope deliberately
**under-claims** Beaumont's own.

**Onset scan (dominant plant), the decisive evidence against the hinge:**

| bin °C | 5–10 | 10–15 | 15–20 | 20–25 | 25–40 |
|---|--:|--:|--:|--:|--:|
| slope /°C | 0.00359 | 0.00295 | 0.00374 | 0.00422 | 0.00488 |
| r | −0.381 | −0.278 | −0.326 | −0.405 | −0.410 |

**Validation, reported not fitted.** Beaumont's own fitted slope reproduces
Beaumont's own measured amplitude (0.00399 × 11.05 °C ≈ 4.4 % predicted vs 3.7 %
observed, 2024) — the regression recovers the real wave. The phase scan
independently confirms the h05/h15 climatological anchors at **lag 0**.

**Leave-one-year-out (rule 22).** Re-deriving the class slope on each 2-year
subset: **0.00153** (drop 2023) / **0.00140** (drop 2024) / **0.00130**
(drop 2025) against 0.00141 full-sample — ±8 %, no year drives it. *Scope note:
this is LOO on the parameter identification, which is where the fitting risk
lives; a solve-level LOO would require three further 2-year re-solves and was
not run.*

## 2. What was built

| field | default | what it does |
|---|---|---|
| `temp_derate_hourly_grain` | off | feed the curve `iso_zone_hourly_drybulb` instead of day-flat TMAX |
| `temp_derate_mean_anchored` | off | no hinge; curve about the zone annual-mean dry-bulb, annual mean exactly 1.0 |
| `temp_derate_classes` | None | scope the mechanism to a class subset |
| `temp_derate_slope_st_chp` | None | ST_CHP slope (None ⇒ ST_GAS) |
| `temp_derate_slope_ct_chp` | None | CT_CHP slope (None ⇒ CT) |

**Mean-anchored is the level-neutrality guarantee.** The curve is
`1 − slope × (T − T̄_zone)`, composed **on top of** the existing level treatment
rather than replacing it. The estimator behind the slope differences every level
term away, so the arm claims **only** shape and claims **nothing** about level —
deliberately the smaller claim. Two implementation consequences that had to be
handled explicitly: `_td_covers` must return False in this mode (or the flat
class derate would be removed and the level would move), and the multiplier must
not be clipped at 1.0 (or only the downward half of the wave survives, turning a
reshape into a net level cut).

## 3. Scope, as pre-registered

**Armed: `ST_CHP` + `CT_CHP` only** — the two tranches the CEMS cogen meter
spans; they identify jointly and must move together. **Not armed:** `ST_GAS`,
`COAL_*`, `CC_*`, `CT_PEAKER` — no MISO identification exists for them and
pjm-95 makes the literature slopes non-transferable.

Both Beaumont tranches do breathe together: ST_CHP rel-amplitude 1.56–1.62 %,
CT_CHP 1.62–1.67 %. Arming ST_CHP alone would have had half of one
combined-cycle cogen breathing while the other half stayed flat.

## 4. Result — every pre-registered gate passes

**G1 phase / G4 direction** — Beaumont `50625`, model slice vs its own meter:

| year | meter trough/peak | meter rel-amp | model trough/peak | model rel-amp | **corr** |
|---|---|--:|---|--:|--:|
| 2023 | h15 / h05 | 5.68 % | **h15 / h05** | 1.62 % | **+0.964** |
| 2024 | h15 / h06 | 3.67 % | **h15 / h05** | 1.56 % | **+0.958** |
| 2025 | h15 / h06 | 4.81 % | **h15 / h05** | 1.59 % | **+0.984** |

The control slice is **byte-flat** (amplitude 0.000000 MW, std 0) — its
correlation is undefined because there is no shape to correlate. The arm creates
a diurnal signal where the model had none and lands it on the meter's phase.

**G2 level neutrality** (bound 1.0 %): ST_CHP max |move| 0.396 %, CT_CHP 0.050 %.
**G3 scope containment** (bound 0.1 %): worst out-of-scope class CT_PEAKER
0.068 %; coal 0.002–0.011 %, CC_REGULAR 0.012 %, ST_GAS 0.031 %. The arm changes
**no** out-of-scope unit's availability (0.000 %, verified no-LP); the residual
energy motion is the LP rebalancing around the in-scope cogens' new hourly
capability, not a scope leak.

**Control integrity.** `miso101_control_A` reproduces the committed keeper
`miso99_chp_hr_B` to **0.00000 %** on every class in every year.

## 5. Reported, not gated — including one falsified prediction

**D-1 `profile_r` improves in every year, for both in-scope classes:**

| year | ST_CHP A → B | CT_CHP A → B |
|---|---|---|
| 2023 | −0.797 → **−0.587** | +0.652 → **+0.684** |
| 2024 | −0.762 → **−0.647** | −0.104 → **−0.033** |
| 2025 | −0.771 → **−0.680** | +0.171 → **+0.298** |

ST_CHP stays negative exactly as **P2** pre-registered: the statistic composites
R S Nelson's anti-phase merchant hump and the flat report-side BTM add-back,
neither of which the lever owns. Per rule 1 that is not grounds to widen the
lever, and it was not widened.

**P6 was WRONG, in direction.** It predicted the model's within-day variance
would *rise* toward the actual. It **fell**: ST_CHP `model_offpeak_cv`
0.0120/0.0130/0.0130 → 0.0080/0.0100/0.0090, so `cv_ratio` went
0.386/1.345/1.019 → 0.253/1.041/0.664 — closer to 1.0 in 2024, further in 2023
and 2025. The mechanism is now clear and was not anticipated: the arm's wave is
*anti-correlated* with Nelson's merchant afternoon hump, so summing them
partially **cancels** and the class composite's within-day variance drops. The
same cancellation is what moves `profile_r` the right way. Neither class is
gated, so nothing is at risk — but the prediction was wrong and is recorded as
wrong.

**System level (P5 confirmed).** Mean price +0.0034 % (2023) / +0.0024 % (2024);
demand, dump and reserve price bit-identical. 2024 mean slack rose 0.87 % with a
single-hour delta of 4,273 MW — one scarcity hour reshuffling on a 645 TWh year
whose mean slack is 0.27 MW.

**C-series rubric: identical between arms** (`scored 6 / target_grade 4 /
fails 2`, C1 all 16/16 · free 12/12; C3a mean LMP FAIL in both). Both read
`NOT-YET` only because a replayed bundle carries no governance attestation —
identical for both arms, not a difference between them.

**Materiality, plainly.** ST_CHP is 0.29–0.43 % and CT_CHP 0.81–0.84 % of MISO
load; both sit under the rule-20 2 % line, which is why they are D-1-ungated and
D-2-exempt. **No gate anywhere was at risk in either direction.** The case for
this arm is rule-1 structural fidelity, plus the fact that the same missing
hour-grain input flattens every floored steam cogen in every ISO.

## 6. Keeper decision

**Recommended: promote `2026-07-28-miso-101b-tempgrain` to MISO keeper —
recommended, NOT performed, and there is a concrete governance step in the
way.**

The keeper shard was deliberately **not** edited. Two reasons, both binding:

1. **Rule 21 `[R-DOF]`: every keeper carries a DOF ledger.** The outgoing keeper
   `miso99_chp_hr_B` ships `calibration_attestation.json`
   (`free_parameters` / `governance` / `disclosures` / `exceptions`);
   a `replay_keeper` bundle does not, and this session cannot author one.
2. **The attestation encodes OWNER decisions, not measurements.** MISO's
   current determination is `CALIBRATED-WITH-CAVEATS` only by the miso-90 owner
   re-gate, which ledgers C3b-2025 and saturates the non-protective caveat
   budget at **3/3**. Promoting a bundle with no attestation would silently drop
   the ISO from `CALIBRATED-WITH-CAVEATS` to `NOT-YET` — on a missing file, not
   on model quality — and reproducing those `governance`/`exceptions` entries
   here would be asserting an owner decision this session does not hold.

**What the owner needs to do to promote:** carry the attestation forward onto
`miso101_tempgrain_B` (the ledger is otherwise unchanged — this arm adds **zero
free parameters**: the slope is measured from CAMPD conduct, LOO-stable at
±8 %, and frozen against residuals by rule 23), then edit
`frontend/data/backcast/keepers/MISO.json` + `build_status.py --iso MISO`.

The merits, separately from that mechanics:

Grounds: a measured, physically-grounded, forward-reproducible input (rule 13 —
zone ambient dry-bulb is exogenous, curated per zone-year, regenerates for any
forward year and responds to changed conditions) replaces a
flat-by-construction representation; every pre-registered gate passes; D-1
improves in all three years for both in-scope classes; the parameter is stable
under leave-one-year-out; the control proves the change is a true single delta;
and no rubric criterion moves in either direction. Under rules 1 and 14 the
absence of a headline-metric gain is not an argument against it — the argument
for it is that the model now reproduces a real market/physical behaviour it
previously could not represent at all.

Honest counterweight: the affected classes are ~1.2 % of MISO load, the D-1
pairing is effectively one refinery, the modelled amplitude is 28–43 % of the
meter's by deliberate construction, and `cv_ratio` moves away from 1.0 in two of
three years. A reader who values only headline fit should read this as neutral.

## 7. DO-NOT-REDO / carried forward

* **Do not raise the slope to close the amplitude gap.** 0.00141 is the class
  population statistic; Beaumont's own 0.00399 is one plant, and §1's screen
  hypothesis is refuted. Re-deriving is legitimate only when the CAMPD or
  weather source updates (rule 23 `[R-FROZEN-DERIVE]`).
* **Do not re-arm the committed hinge for MISO.** The 15 °C onset is measured
  false on MISO's own fleet (§1 onset scan), and the day-flat input cannot
  produce a diurnal wave at all.
* **Do not widen the lever to ST_GAS/COAL to move ST_CHP `profile_r`.** The
  residual belongs to Nelson's merchant conduct and the flat BTM add-back —
  separable questions FINDING-miso100 §7 already scoped as their own decisions.
* `gt_ambient_derate` remains inert in MISO (miso-90) — a different mechanism
  on different classes; this arm does not revisit it.
* The class-composite **cancellation** effect (§5) is new information: a shape
  fix on a floored plant can *reduce* a class's measured within-day variance
  when the class's other members run anti-phase. Any future ISO arming this leg
  should expect `cv_ratio` to move either way.
