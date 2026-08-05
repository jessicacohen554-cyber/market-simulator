# PRE-REGISTRATION — miso-129: does MISO's coal offer band lack a within-band incremental cost slope, and would MISO's own measured incremental heat rate supply one that organises off-peak dispatch hour-of-day?

**Date:** 2026-08-05 · **ISO:** MISO · **Years:** 2023–2025 (training only) ·
**Keeper at entry:** `2026-08-04-miso-127-onlinepmin`
(`results/calibration/miso127_onlinepmin_B`), determination **NOT-YET**, sole
FAIL **C7 `COAL_PRB` — 2025 only** (cv_ratio 0.347 vs the 0.5 gate), ledgered
caveats 2/3 {C3a, C3c}, `audit_keepers --iso MISO` 0/0.

**Pushed before any adjudicating statistic, before any derive output and before
any arm.** Rule 22 `[R-HOLDOUT]`: 2023–2025 only. MISO holds **no**
`calibration-complete` marker, so no out-of-training year (2018–2022, 2026) is
solved, scored **or read** — the CAMPD state-year parquets for those years exist
on disk and this session's derive enumerates {2023, 2024, 2025} explicitly and
never globs.

---

## §0 — OFF-QUEUE DECLARATION (rule 28(a)), stated because it is required

`docs/mechanism-testing-matrix.md` §5.4 carries the miso-128 QUEUE STAMP, which
records that MISO has **NO named, un-adjudicated, non-data-blocked queue item** —
miso-128 closed the last one (`coal_tranche_1/2/3_frac`, inert by wiring). The
two bounded items that remain are a **sourcing** pass (item 1's Form 580 tonnage
count) and a **data-blocked** intake (item 2's outage grain). Neither is a lever.

**This lane is therefore explicitly OFF-QUEUE by necessity.** It takes the one
object miso-128 **NAMED BUT DID NOT CHARTER** (§6.4 / matrix "NAMED, NOT
CHARTERED"): *the model's coal offer band has no within-band incremental cost
slope, so a plant is bang-bang in whichever band is marginal and saturates flat
once loading clears a step.* miso-128 explicitly declined to license it —
"it is **not** licensed by this finding" — and required that any successor bring
"its own pre-registration, its own derive, its own two-grain wiring proof and a
leave-one-year-out before any promotion." **This document is that licence
attempt, and it may fail at §3 P1 before a single number is measured.**

---

## §1 — DISCLOSURE: everything read before this document was written

Stated in full so no property below can be reverse-engineered from something the
reader cannot see. Each item is labelled **STRUCTURAL** (source/schema/config
plumbing) or **PRIOR** (a claim that bears on an adjudication).

**Carried from miso-128 (the brief's restatement, not re-derived here).**
`cv_ratio = R_tot × R_dfrac × R_level`; `R_tot` 0.907/0.877/**0.952**;
`R_level` 1.077/1.091/**1.025**; `R_dfrac` 0.524/0.549/**0.354**. Absolute
amplitude deficit 1145/858/**800** MW (monotone down). Reality's per-plant
off-peak amplitude-vs-loading fit `std_frac = +0.0558 × cf_off + 0.0289`
(cap-wtd LS, 92 plant-years, wR² 0.429); the model's `−0.0028` (wR² 0.003).
Flat census model 26.0/27.4/**59.4 %** of PRB nameplate vs actual
0.0/7.5/**12.3 %**; 10 plants / 11,958 MW newly flat in 2025, nine of ten while
model loading RISES; 2025 model flat set cap-wtd `cf_off` **0.534** vs varying
**0.440**, their *actual* amplitudes indistinguishable (0.0410 vs 0.0401).

**STRUCTURAL — the model's MISO coal construction, read from source this
session.**
* MISO runs `use_campd_bins=True`, `plant_level_fleet=True`, `iso=MISO`,
  `mode=backcast` (keeper `run_config.json`), i.e. the **CAMPD-binned limb**.
  `split_coal_tranches` and `coal_tranche_{1,2,3}_frac` live only in the `else`
  limb and are **inert by wiring at MISO** (miso-128 §4) — not re-tested here.
* `fleet_to_bins` (`data/fleet/campd_bins.py`) builds one bin row per
  `(plant_code, plant_group)`; `bins_to_fleet` (`data/fleet/assembly.py`) splits
  each coal bin into up to four LP tranches — `_mustrun`, `_committed`, `_econ`,
  `_peak` — each `pmin_mw = 0`.
* `_DEFAULT_TRANCHE_PCT_BY_GROUP["COAL"] = (45.0, 5.0, 2.0)`
  (must-run, committed, peaking %), overridden per plant from
  `data/raw/_processed-legacy/thermal_tranches_MISO.csv` (**44 coal rows**) via
  `thermal_tranche_overrides`; under the keeper's `coal_mustrun_online_pmin=True`
  the must-run share is the measured **online-Pmin** column. The economic band is
  the residual, `100 − mr − mc − peak`.
* `_DEFAULT_HR_MULT_BY_GROUP["COAL"] = {mr: 1.00, mc: 1.15, econ: 1.00,
  peak: 1.05}` — a hardcoded **between-band** heat-rate ladder of ERCOT/OEM
  lineage, not a MISO measurement.
* **`_econ_curve_steps` (`data/offer_curves.py`) ALREADY EXISTS** and already
  slices a rising economic ramp into `n` equal-capacity flat sub-tranches whose
  heat-rate multiplier rises `lo_mult → pk_mult` along `mult(t) = lo + (pk − lo)
  · t^exp` (or a two-segment `mid`-anchored piecewise ramp). Its own docstring
  says `exp == 1` is "a straight (linear) ramp **matching a thermal unit's
  gently-rising incremental heat rate**". It is driven by
  `config.offer_curve_by_group[<group>]` resolved through `_offer_curve_for_group`
  (coal routes by supply class via `_COAL_SUPPLY_TO_CURVE`, e.g. `COAL_PRB`,
  falling back to a generic `COAL` entry) and `econ_split_by_group`.
  **CONSEQUENCE, and it is why §3 P1 exists: the "within-band incremental cost
  slope" machinery is already in the codebase. Whether it is ARMED for MISO coal
  is unread, and it is this lane's premise.**
* **I have NOT read `config.offer_curve_by_group` for MISO, nor any coal entry
  in it, nor the assembled per-tranche marginal costs of any MISO coal plant.**
  That is P1's statistic and it is measured only after this document is pushed.

**STRUCTURAL — the keeper's armed coal flags** (read from
`run_config.json.scenario_config`, disclosed because they are the rule-19
neighbours): `coal_mustrun_online_pmin=True`, `coal_mustrun_per_plant=True`,
`coal_takeorpay_from_data=True`, `coal_committed_takeorpay_regulated=True`,
**`coal_econ_srmc_bound=True`**, `coal_supply_repricing=True`,
`coal_plant_monthly_pricing=True`, `coal_warm_committed=True`,
`commitment_screen_coal=True`; and OFF: `coal_econ_marginal_hr_bound=False`,
`coal_sync_srmc_tranche=False`, `coal_prb_committed_split=False`,
`coal_prb_committed_dispatchable=False`, `coal_bit_dispatchable=False`,
`miso_coal_night_floor=False`, `coal_perplant_offer_curves=None`, every
`coal_*_passthrough_sigmoid=False`.

**STRUCTURAL — the identification source's schema.**
`data/raw/campd-unit-level/{STATE}_{YEAR}.parquet` carries
`stateCode, facilityName, facilityId, unitId, date, hour, opTime, grossLoad,
steamLoad, so2Mass, co2Mass, noxMass, heatInput, primaryFuelInfo, unitType`
(IL_2024: 1,774,104 rows). `states_for_iso("MISO")` returns
`(AR, IA, IL, IN, KY, LA, MI, MN, MO, MS, ND, SD, TX, WI)`. `facilityId` is the
EIA plant code and joins directly to the D-1 bench keys, which are plant codes as
strings (`load_bench(REPO,"MISO",2025)` → 30 `COAL_PRB` plants, fields
`group/zone/npl/mw`). Plant→class membership: `bin_assignments_MISO.csv`
(`Plant_Code, Plant_Group, …`).

**PRIOR — DISCLOSED, and it is a live kill risk for P2.**
`scripts/data/derive_campd_marginal_hr.py` already exists; it already fits a
**per-unit quadratic** input–output curve to CAMPD `heatInput` vs `grossLoad` and
reports a marginal (incremental) heat rate per band, and
`data/raw/reference/miso_campd_marginal_hr_summary.csv` **exists on disk**.
**I have not opened that file or read any value from it** — its coal rows are
P2's adjudicating statistic. I *have* read the script's docstring, which asserts
the marginal heat rate "is ~**flat**-to-gently-rising with load". That claim is
of **ERCOT/NYISO lineage** and is **not** a MISO coal measurement — but it is a
disclosed prior pointing at P2's falsifier, and if MISO's coal reads "flat" this
lane dies at P2 with zero solves. Recording it now so a P2 kill cannot later be
narrated as a surprise, and a P2 pass cannot be narrated as merely confirming
what the docstring said.

**PRIOR — the miso-127 Lane B converse duty, declared binding.** If an
expected-inert or expected-flat prior **fails its own ex-ante measurement**, the
prior is RECORDED AS REFUTED and the lane proceeds to solve. A cancelling net is
never sufficient for an inertness call (miso-127: −533 MW net concealed 7,528 MW
gross on 39 of 44 plants).

---

## §2 — THE MECHANISM, stated in full BEFORE it is identified

**Name:** `coal_within_band_incremental_slope` — a NEW registered
`ScenarioConfig` boolean (rule 24 `[R-REGISTRY]`), default **False**, **MISO-scoped**
(rule 25 `[R-ISO-SCOPE]`), with its `docs/codebase-site/data/mechanism-matrix.js`
row added in the SAME PR (rule 28(c)).

**Construction.** For each MISO coal plant, replace the **single flat bid** of its
**dispatchable bands above the forced/sunk min-load band** (`_econ`, and `_peak`
where present) with `N` equal-capacity sub-tranches whose heat rates trace the
plant's **own measured incremental heat rate curve** across exactly that band's
load range, via the **existing** `_econ_curve_steps` machinery. The `_mustrun`
and `_committed` bands are **not touched**.

**Parameters and their identification** (rule 21 `[R-DOF]`):

| parameter | value | identification |
|---|---|---|
| per-plant `lo_mult`, `pk_mult` | measured | MISO's own CAMPD unit-level `d(heatInput)/d(grossLoad)` at the econ band's bottom and top load, expressed as a multiple of the plant's own base HR |
| ramp shape | measured | the same measured curve, discretized; **not** an `exp`/`mid` knob swept against anything |
| `N` (discretization) | **fixed at 4** ex ante | a discretization count, not a fitted value; declared here so it cannot be tuned. Reported sensitivity at N=8 is a robustness check only and never a promotion basis |

**Zero free parameters are fitted to any residual.** Every number comes from the
derive; `N` is pre-declared. A residual that can only be closed by tuning `N`,
`exp`, or `mid` is an open root-cause issue, **not** a parameter (rule 21).

**Derive (frozen, rule 23 `[R-FROZEN-DERIVE]`):**
`scripts/data/derive_campd_coal_incremental_hr.py`, writing
`data/raw/_processed-legacy/coal_incremental_hr_MISO.csv` at **plant** grain,
citing `data/raw/campd-unit-level/*_{2023,2024,2025}.parquet` as its source. It
re-derives **only** when that source data updates.

**Frozen derive construction, declared ex ante so it cannot be adjusted after
seeing an outcome:**
1. **Membership:** units whose `facilityId` is a `Plant_Group == "COAL"` plant in
   `bin_assignments_MISO.csv`, in the `states_for_iso("MISO")` states,
   years **{2023, 2024, 2025} enumerated explicitly**.
2. **Unit-hour screen:** `opTime ≥ 0.95` (steady-state full hour),
   `grossLoad > 0`, `heatInput > 0`.
3. **Operating range:** per unit-year, `LSL = p2(grossLoad)`,
   `HSL = p99(grossLoad)`; deciles over `[LSL, HSL]`.
4. **PRIMARY, nonparametric:** per decile take mean `grossLoad` and mean
   `heatInput`; the incremental heat rate between adjacent decile centroids is
   `IHR = ΔheatInput / ΔgrossLoad` (9 values per unit-year). `IHR(q10)`/`IHR(q90)`
   are the first/last of these. `IHR′` is the LS slope of those 9 `IHR` values on
   their load centroids.
5. **ROBUSTNESS ONLY:** a per-unit cubic fit of `heatInput` on `grossLoad`.
   Reported; never the adjudicating basis.
6. **Coverage floor:** a unit-year needs ≥ 500 qualifying unit-hours and ≥ 8
   populated deciles, else it is dropped and its **dropped capacity is reported**
   (no silent truncation).
7. **Aggregation:** unit → plant, capacity-weighted by HSL.

---

## §3 — NUMBERED PROPERTIES, each with its own falsifier

Properties are adjudicated **in order**. **P1 can kill the lane with no derive
output. P2/P2b/P3/P4 can kill it with zero solves.**

### P1 — PREMISE (EX ANTE; kills the lane with NO derive, NO solve)

**Claim under test:** the model's MISO coal econ band carries **no** within-band
incremental cost slope — miso-128 §6.4's premise.

**Measured at two grains** (miso-126(a) duty; instrument the **CAMPD** limb —
`fleet_to_bins` / `bins_to_fleet` / `_offer_curve_for_group` — **never**
`split_coal_tranches`):
* **Grain 1, config resolution:** resolve `_offer_curve_for_group("COAL",
  plant_code, keeper_config)` and `_econ_split_for_group` for every MISO coal
  plant under the keeper's own committed config. Report how many resolve to a
  curve and, where they do, the resulting `n`.
* **Grain 2, assembled fleet:** assemble the real MISO 2025 dispatch fleet at
  HEAD under the keeper's committed config and count, per coal plant, the number
  of **distinct marginal costs** among its econ-band LP tranches and the
  `max/min` ratio of those costs.

**Falsifier / adjudication:**
* If MISO coal plants resolve to **one flat econ tranche** (grain 2 distinct
  econ MC count == 1 for ≥ 90 % of coal capacity) → the premise **HOLDS**,
  proceed to P2.
* If the econ band **already** resolves to `n > 1` rising sub-tranches for
  ≥ 50 % of MISO coal capacity → **miso-128 §6.4's premise is FALSE**, the object
  does not exist as described, **the lane dies here with zero derive output and
  zero solves**, and the finding says so. This is a legitimate outcome and the
  cheapest one.
* Anything between (10–50 % of capacity laddered) → the premise is **partial**;
  the lane may proceed **only** on the un-laddered remainder, and the finding
  must report the split rather than averaging over it.

### P0 — REPRODUCTION (EX ANTE; construction validity, gates §3's comparisons)

Before any comparison against reality's `+0.0558`, this session's own
actual-side fit must reproduce miso-128's. Same construction: per plant-year,
hour-of-day mean profile over `h0–D1_OFFPEAK_LAST_HOUR (=14)`,
`cf_off = mean(profile[OFF])/npl`, `std_frac = std(profile[OFF])/npl`,
capacity-weighted LS with weight `npl`, over the committed bench
`frontend/data/backcast/bench/MISO/<year>.json.gz`, `COAL_PRB`, matched keys.

**Falsifier:** actual-side slope outside `+0.0558 ± 0.005` or wR² outside
`0.429 ± 0.05` → my construction differs from D-1's, every comparison below is
void, and the construction is fixed before anything is adjudicated.

### P2 — IDENTIFICATION-A, EXISTENCE (EX ANTE; kills the lane with ZERO SOLVES)

**Statistic:** capacity-weighted median across MISO coal plant-years of
`IHR(q90) / IHR(q10)`.

**Bar: ≥ 1.10.** **Falsifier:** `< 1.10` → MISO's coal units do **not** show a
materially rising incremental cost across their operating range; a sub-block
ladder would be within noise of the flat bid the model already carries; **the
mechanism has NO identification source and the lane dies with zero solves.**
This is the declared default and it is the miso-125 / miso-127-Lane-A pattern.

### P2b — CONSTRUCTIBILITY (EX ANTE; kills the lane with ZERO SOLVES)

A rising ladder is only constructible for a unit whose input–output curve is
**convex** (`IHR′ > 0`); a unit with `IHR′ ≤ 0` has a *falling* incremental cost
and cannot be represented as a rising offer ladder at all.

**Statistic:** share of MISO coal capacity with `IHR′ > 0`.
**Bar: ≥ 50 %.** **Falsifier:** `< 50 %` → the ladder is not constructible on
the majority of MISO's coal fleet; lane dies, zero solves. If the bar is cleared
but a material non-convex minority remains, those plants are **reported by name
and capacity** and keep their current flat bid — they are never silently
monotonized.

### P3 — IDENTIFICATION-B, SIGN (EX ANTE; kills the lane with ZERO SOLVES)

**This is the property miso-128 §6.3 demands, and it is the one this lane most
likely dies on.** A mechanism that does not put a **positive** amplitude-vs-loading
slope where reality has `+0.0558` cannot move `R_dfrac`, and `R_tot` is already at
0.952 so there is no room to buy the gate with more variability.

**Construction.** Under the mechanism a price-taking plant with rising offer
`MC_p(q) = fuel_p · IHR_p(q) + VOM_p` dispatches where `MC_p(q) = P`, so to first
order its off-peak output dispersion is
`std(q_p) ≈ σ_P / (fuel_p · IHR′_p(q̄_p))` and

> `implied_std_frac_p = c / (Cap_p · fuel_p · IHR′_p(q̄_p))`

evaluated at the plant's **measured** off-peak mean load `q̄_p`. `fuel_p` is
treated as **constant across `COAL_PRB` plants within a year** — justified by the
keeper's `coal_supply_repricing=True`, which reprices all coal to a flat annual
PRB/lignite trajectory — so it is absorbed into `c`. **Falsifier on that
assumption:** if `coal_supply_repricing` were off, fuel must be carried per plant;
it is on, and this is re-asserted from `run_config.json` at derive time.

`c` is **not free**: it is set so the capacity-weighted mean of
`implied_std_frac` equals the capacity-weighted mean of the **measured**
`std_frac` (P0's actual side). The test is therefore purely about **shape at
matched total amplitude** and carries **no fitted scale**.

**Statistic:** capacity-weighted LS slope of `implied_std_frac` on **measured**
`cf_off`, same weighting and construction as P0.

**Bar: slope > 0.** **Falsifier:** `≤ 0` → the mechanism puts a zero or
**wrong-sign** slope exactly where the finding says a positive one is required;
it cannot move `R_dfrac`; **lane dies, zero solves.** Note this is a real
possibility and not a formality: P2b requires `IHR′ > 0` for constructibility,
while a positive amplitude-vs-loading slope requires `IHR′` to **fall** with
load — the two are independent, and a fleet of convex-but-uniformly-steepening
units satisfies P2/P2b and fails P3.

### P4 — SUFFICIENCY, MAGNITUDE (EX ANTE; gates the SOLVE)

**Statistic:** P3's slope as a fraction of reality's `+0.0558`.

**Bar: ≥ 0.5 (i.e. slope ≥ +0.0279).** Justification, declared now: clearing the
2025 gate needs `R_dfrac ≥ 0.5 / (R_tot · R_level) = 0.5 / (0.952 × 1.025) =
0.5124`, i.e. a **1.447×** rise from 0.354. The amplitude-vs-loading slope is the
finding's identified carrier of that organisation; a mechanism supplying under
half of reality's carrier cannot plausibly deliver a 1.45× move on its own.

**Falsifier:** `0 < slope < +0.0279` → the mechanism is **identified but
under-powered**. Recorded as such, **NO SOLVE**, and named as needing a companion
mechanism — which rule 19 `[R-ONE-MECH]` forbids this session from manufacturing.

### P5 — WIRING, post-arm (EX ANTE; a clean null is a DEFECT, not a verdict)

miso-126(a): firing proven at **two grains** — (i) pre-arm **construction**
(`fleet_to_bins` / `bins_to_fleet` off vs on: per-coal-plant econ tranche count
and MC vector, gross elementwise delta), and (ii) post-arm **per-class ENERGY
delta** (`COAL_PRB` TWh, bar 0.05 TWh). **Falsifier:** a null at grain 2 with a
non-null grain 1 is a **WIRING defect** and is fixed before anything is
adjudicated — it is never reported as an inertness verdict. Instrument the CAMPD
limb; `split_coal_tranches` is inert at MISO and is not evidence either way.

### P6 — CONTROL INTEGRITY (EX ANTE)

miso-124: a same-HEAD **zero-delta control arm A** is solved FIRST, and every
delta is quoted against **it**, never against the committed keeper. Reuse
`scripts/probes/_miso127_online_pmin_ab.py`'s **K0** gate verbatim.
**Falsifier:** arm A failing K0 voids the whole A/B.

### P7 — FULL BALANCE (EX ANTE)

miso-126(b): `class_hourly` is not the whole balance. Score
`d_class + d_discharge − d_charge + d_slack − d_dump − d_demand == 0`. Reuse the
**K6** gate verbatim. **Falsifier:** non-zero residual voids the attribution.

### P8 — SCORING DISCIPLINE (EX ANTE, binding on how results may be quoted)

* Score **`R_dfrac`**, never raw variance and never raw CV (miso-128).
* The ratio form is scale-sensitive: **never** quote an absolute-amplitude
  improvement as a C7 result without the ratio, or the ratio without the
  absolute (miso-128).
* Decompose every net aggregate into **gross + sign** before any inertness or
  materiality claim (miso-127).
* **Binding is not marginality**; the predictive ex-ante statistic is **marginal
  share** (miso-121). `max_abs_class_hour_mw` is **not** a mechanism magnitude at
  MISO (miso-122).

### P9 — RULE 19 `[R-ONE-MECH]` LICENCE (EX ANTE, must be argued explicitly)

Enumerated: what already shapes MISO's coal band on the keeper, and what this
mechanism does to each.

| already armed | what it shapes | this mechanism |
|---|---|---|
| `coal_takeorpay_from_data` + `coal_committed_takeorpay_regulated` | the **LEVEL** of the `_mustrun` band's bid (which share of fuel is sunk) | **UNTOUCHED** — different band |
| `coal_mustrun_online_pmin` (keeper, K) | the **SIZE** of the `_mustrun` band | **UNTOUCHED** — and explicitly not re-swept (P11) |
| `_DEFAULT_HR_MULT_BY_GROUP["COAL"]` econ/peak (1.00 / 1.05) | the **BETWEEN-band** step ladder, hardcoded, ERCOT/OEM lineage | **REPLACED** by MISO's own measured curve |
| `coal_econ_srmc_bound=True` | a **LEVEL FLOOR** on the econ band's bid (fuel passthrough clamped ≥ 1.0) | **RECONCILED, NOT STACKED** — it is a floor on the band's *level*; this is a *slope* within the band. The ladder is built and the floor then applies to each sub-tranche unchanged, so the clamp keeps exactly its current meaning |
| `coal_supply_repricing`, `coal_plant_monthly_pricing` | the **FUEL PRICE** input | **UNTOUCHED** |

**Falsifier (KILL-4):** if reconciling with `coal_econ_srmc_bound` requires the
two to **stack** — i.e. if the ladder can only produce its effect by relaxing or
re-tuning that clamp — the mechanism is **REFUSED under rule 19** and no arm is
solved.

### P10 — ISO SCOPE (EX ANTE)

Rule 25 `[R-ISO-SCOPE]`: the field is MISO-gated and the artifact is
`coal_incremental_hr_MISO.csv`. **Falsifier:** any non-MISO ISO's fleet
construction changing under the new code (checked by assembling a non-MISO ISO's
fleet off vs on) → rule 25 breach, reverted before anything else.

### P11 — OUT OF SCOPE (EX ANTE, a prohibition)

`coal_mustrun_online_pmin` is **not** re-swept, re-tuned or re-sized in any arm,
in any year (rules 1 / 24, and the brief's DO-NOT-REDO). `coal_tranche_*_frac` is
not re-tested (inert by wiring, miso-128). No form in the closed families is
re-opened: take-or-pay period-budget (closed by proof, miso-127 §1.2),
take-or-pay removal (R twice, miso-102), regulated self-commitment forcing
(miso-111 R / 112 R / 113 I, confirmed 114), receipts-derived tonnage
(miso-103). **Falsifier:** none — this is a prohibition, and a session that finds
itself sizing any of these has already failed.

### P12 — LEAVE-ONE-YEAR-OUT (EX ANTE, gates promotion only)

No promotion without LOO within 2023–2025. In-sample gain with held-out
degradation is overfitting, not skill. **Falsifier:** LOO degradation → no
promotion, keeper unchanged, and the arm is registered as a rejected probe
(rule 15).

---

## §4 — KILL clauses

* **KILL-1 — no residual sizing.** Nothing in this session may be sized,
  re-sized or shape-selected from any Δ measured in this session. If a residual
  can only be closed by a tuned value it is an open root-cause issue, not a
  parameter (rule 21).
* **KILL-2 — holdout.** No out-of-training year (2018–2022, 2026) is solved,
  scored **or read**, in the derive or anywhere else (rule 22). The derive
  enumerates {2023, 2024, 2025} and never globs a year.
* **KILL-3 — inadmissible identification.** If the derive needs any quantity that
  is a model *outcome* rather than a measured input, or any parameter settable
  only from the C7 residual, the mechanism is inadmissible (rules 13 / 21) and
  no arm is solved.
* **KILL-4 — rule 19 stacking.** See P9: reconciliation with
  `coal_econ_srmc_bound` must be replacement or clean composition, never stacking.
* **KILL-5 — no manufactured successor.** If every property kills, the finding
  says so explicitly and **no successor is manufactured** (rule 19). "No arm
  solved" is a declared, legitimate default of this pre-registration, not a
  failure of it.

---

## §5 — what gets produced either way (rule 15)

* **If P1, P2, P2b, P3 or P4 kills:** a FINDING recording the kill and its
  measured statistic, the matrix cell stamped in this same session (rule 28(b)),
  the derive committed **only if it ran**, and an explicit statement that a
  **no-LP phase produced no run** — which is how rule 15 is satisfied, not by a
  registration.
* **If every screen clears:** arm A (same-HEAD zero-delta control) then arm B,
  `--years 2023 2024 2025` in ONE `replay_keeper.py` invocation each (rule 16),
  sequentially (never concurrent — two MISO solves OOM). Post-solve per bundle:
  `dashboard_add_run.py` → `legitimacy_diagnostics --bundle <dir> --iso MISO
  --years 2023 2024 2025 --json-out <dir>/legitimacy_diagnostics.json` →
  attestation → `calibration_verdict --run-id <id> --write-metrics` → the A/B
  scorer (K0 + K6 verbatim from `_miso127_online_pmin_ab.py`, plus an `R_dfrac`
  leg from `_miso128_c7_diurnal_organization.py::decompose`). **Both arms are
  registered on the dashboard in this session, keeper or rejected** (rule 15).
  `metrics.json` carries only STATUSES; per-record magnitudes come from
  `calibration_verdict --json`.

**Declared now: this pre-registration's most likely outcome is a kill.** Three of
its five screens (P1, P2, P3) are independent, each is a coin-flip on evidence I
have deliberately not read, and P3 is in genuine tension with P2b. miso-125,
miso-127 Lane A and miso-128's P9 all died on a pre-registered property with zero
solves. That is the point of writing this before looking.
