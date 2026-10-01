# ASSESSMENT — neiso-88: is NEISO ready for a 2022–2035 forecast run?

**Session:** neiso-88, 2026-08-06 · **Branch:** `claude/neiso-88-forecast-readiness-g0kmob`
**HEAD:** `7c857c51` · **Keeper (read live):** `2026-08-05-neiso-83-ca1-reclass`
**Markers:** `complete` HELD · `final` EMPTY · **Freeze:** `holdout-freeze.json` ACTIVE
**Scope:** assessment only. **No LP was built, no solve was run, no year was scored, no run
was registered, no mechanism was tested, no matrix cell verdict was minted (rule 28d), and no
holdout year was spent.** Every number below is read from committed artifacts or from
data-layer loader probes that read inputs and produce no model output.

---

## 0. Recommendation

> ### DO NOT AUTHORIZE the 2022–2035 solve. Three blockers; the first two are hard, and none is about compute.
>
> 1. **The window is not schedulable and cannot be made so by this gate.** 2022–2035 is
>    **14 solve-years** against a §2.1b cap of **5**. It is not merely over the cap — it is
>    *strictly larger than T2 itself* (2026–2035), and T2 is **DEFERRED, unschedulable at any
>    HEAD**. Authorizing it is not "opening the gate for NEISO"; it is authorizing a window no
>    tier in the ladder defines.
> 2. **No instrument in the repo can span it, and 2022 in particular cannot be solved.** The
>    hindcast harness bridges 2022 (never solves it) and caps at 2025; the crossover requires
>    `start ≥ 2023`; `run_full_horizon` is forecast-mode and would *de-grow* 2024 weather into
>    2022, which is not a hindcast of 2022 at all. Nothing in the codebase produces the
>    "2022–2025 hindcast + 2026–2035 forecast" object the request describes.
> 3. **A 2035 horizon is a capacity-evolution question, and NEISO's capacity-evolution skill
>    instrument fails on every band it measures.** T1-H FC-3: **12 of 12 bands FAIL** — all
>    three retirement bands and all nine addition bands. Ten hours of compute would buy a
>    mechanically clean 14-year trajectory whose governing mechanism has *zero* demonstrated
>    skill.
>
> **What I recommend instead**, in order, is in §6. The good news is real and is buried under
> a stale board: **§2.1b leg (a) now PASSES for NEISO**, and **the A1/I4 capacity-accounting
> leak — recorded as NEISO's sole T1-F blocker — is CLOSED**, in NEISO and in the other three
> ISOs the board still lists as blocked on it.

| question | answer |
|---|---|
| **1** gate state | (a) **PASS** (was fail on a two-promotions-stale keeper name) · (b) **FAIL, but on I7, not I4** · (c) **FAIL** (no NEISO T1-X exists) · (d) **none**. §1 |
| **2** year-span feasibility | **NOT BUILDABLE.** No instrument spans it; 2022 is unsolvable by every harness. Demand is *not* the obstacle — and 2019/2020 demand resolves too (§2.3, correcting neiso-87). §2 |
| **3** what carries into forecast | **4** overlays are code-refused; **11** keeper mechanisms are forward-admissible but **default-OFF and unreachable from `run_full_horizon.py`** — so no NEISO forecast has ever run the keeper's recipe. §3 |
| **4** capacity-evolution surface | Curve-ON, backstop resolves **ON**, confirmed exits **2 rows / 459 MW / 2028 only**. **BLK-10 is NOT bounded for NEISO** — the wave is measured post-D1. Net-CONE ladder ends 2027-28, so **8 of 14 years hold-last on a sunsetting construct**. §4 |
| **5** carried-forward items | (i) **material, bounded** · (ii) **not material — code-refused in every forecast/hindcast leg** · (iii) **NOT MATERIAL — wrong function; corrected with evidence**. §5 |

---

## 1. Q1 — the four §2.1b legs, re-scored at HEAD

`frontend/data/forecast/program-status.json` records the legs as read at `e2a422c1`
(session FFR-3A-3). Re-read at `7c857c51`:

| leg | board text | **HEAD verdict** | evidence |
|---|---|---|---|
| **(a)** backcast calibration proof | **fail** — "keeper 2026-08-03-neiso-caiso156-meter-screen" | **PASS** | `keepers/NEISO.json` designates `2026-08-05-neiso-83-ca1-reclass` (a full-span 2023–2025 keeper, rule 16); `calibration-complete.json` `complete` block names NEISO and is **already re-keyed** to that same run with a re-verified `CALIBRATED-WITH-CAVEATS`. Both halves §2.1b(a) asks for are present. The board is **two promotions stale** (neiso-81, then neiso-83). |
| **(b)** POC gates green | **fail** — "HOLD — FC-1 FAIL I4 (2028 coal off 54 MW)" | **FAIL — but the stated cause is wrong.** The live blocker is **I7**. | `frontend/data/hindcast/neiso-2026-2030-ffr3a2-t1f.json` (FFR-3A-2, 2026-08-03, curve-ON): **`I4 capacity accounting = PASS, "closes"`**. The one FC-1 FAIL is **`I7 reliability floor: 2028: accredited firm 25,386 < requirement 25,604 MW`** — a 218 MW adequacy shortfall. |
| **(c)** worth-the-compute | **green** (readiness) / **na** (crossover) | **FAIL** | §2.1b(c) requires *both* FF-3E readiness **and** "the T1-X crossover input gap (FC-4) measured and reported for the ISO". **NEISO has no T1-X run at all** — no `neiso-t1x` key exists in `ff-verdicts.json`, and FC-4 reads `n/a` in every NEISO verdict. Readiness/cost are green (§4.5); the crossover half has never been run. The board scores this leg on the readiness half alone. |
| **(d)** owner authorization | **none** | **none** | Unchanged. No assessment grants it, this one included. |

### 1.1 Is the A1/I4 leak still the sole T1-F blocker? **No — it is not a blocker at all, in any ISO.**

The board's `gate_reading` and its `honest_unfit` "I4 / A1" row both name the capacity-accounting
leak as the dominant T1-F blocker for CAISO/PJM/MISO/NEISO. On the **live FFR-3A-2 sidecars**,
read directly:

| ISO | I4 | live FC-1 FAIL |
|---|---|---|
| **NEISO** | **PASS** — "closes" | I7 (2028) |
| PJM | **PASS** — "closes" | I7 (2030) |
| MISO | **PASS** — "closes" | I7 (2026, 2027) |
| CAISO | **PASS** — "closes" | I12, I3, I7 |
| NYISO | — | I7 (2026, 2027) |
| ERCOT | — | I12, I3 |

**The A1 leak is closed** — consistent with `check_i4_capacity_accounting`'s own docstring,
which describes the FFR-1A `confirmed_derates` recorder added precisely to close it. The
dominant live T1-F blocker across the program is now **I7 adequacy in 4 of 6 ISOs**, not I4.

This is not a NEISO-lane finding to act on unilaterally; it is a **board-refresh finding** with
cross-ISO reach. I have corrected the **NEISO** row of `program-status.json` and left the
cross-ISO `gate_reading` / `honest_unfit` prose for the lane that owns it (§7), flagging it
there rather than rewriting four ISOs' status from one ISO's session.

### 1.2 The blocker that actually replaced it, and why it is worse news for a 2035 run

I4 was a **bookkeeping** defect — MW leaving the fleet without a ledger row. I7 is a
**behavioural** one: the fleet the model evolves is genuinely short of the reliability
requirement. NEISO's live T1-F trajectory:

| year | reserve margin | retire MW | build thermal / renew / storage MW |
|---|---|---|---|
| 2026 | 15.26 % | 0 | 0 / 0 / 0 |
| 2027 | **0.70 %** | **3,297.9** | 0 / 0 / 0 |
| 2028 | **−0.61 %** | 0 | 50.2 / 0 / 0 |
| 2029 | 4.38 % | 54.0 | 643.3 / 1,802 / 720 |
| 2030 | 9.56 % | 0 | 1,500 / 1,198 / 0 |

A 3.3 GW single-year exit wave, a reserve margin through zero and **negative**, and the
build response arriving **two years late**. That is the §1.5 de-firm→overshoot signature —
see §4.3.

---

## 2. Q2 — year-span feasibility: is 2022–2035 buildable?

### 2.1 The policy answer: no, and not by a margin that a single authorization closes

`market_sim/config/schedulable.py::MAX_UNAUTHORIZED_SOLVE_YEARS = 5`. A 2022–2035 window is
`2035 − 2022 + 1 = 14` solve-years. Every schedulable entry point shares that guard
(`assert_schedulable` / `assert_config_schedulable`), so `run_full_horizon.py`,
`run_ces_leg.py`, `market-sim run/sweep/ensemble/matrix` and the PB-5 drivers all refuse it
without `--full-solve-authorized`.

The sharper point is that **§2.1b does not contemplate this window at all**. Its deferred
tiers are T2 (2026–2035, 10 yr), T3 golden (2026–2050) and the W4/PB-5 campaigns. 2022–2035
is **T2 plus four backcast-tier years bolted on the front**. Authorizing it is not "opening
the T2 gate for NEISO" — it is authorizing an instrument the ladder does not define, on an
ISO that has not passed the T1 gate below it.

### 2.2 The mechanical answer: no instrument produces this object

Confirmed against `scripts/lib/holdout_policy.py` as the prompt asks:

```
HINDCAST_SOLVE_YEARS  = CALIBRATION_YEARS | HINDCAST_SEED_YEARS = {2021, 2023, 2024, 2025}
HINDCAST_BRIDGE_YEARS = {2022, 2026}
HINDCAST_SEED_YEARS   = {2021}
VALIDATION_YEARS      = {2020, 2021, 2022}
```

| instrument | can it start at 2022? | can it reach 2035? |
|---|---|---|
| **plain hindcast** (`run_capacity_hindcast.py`) | **No.** 2022 is a **bridge** year — `is_hindcast_bridge_year` evolves the fleet across it and never solves it or reads its data. `hindcast_solve_year_violations` fails it closed as validation tier. | **No** — `_validate_window` caps `end ≤ 2025`. |
| **crossover** (`--crossover --vintage 2023`) | **No.** `_validate_window` requires `start ≥ 2023`. | **No** — window is exactly `{2023,2024,2025,2026,2027}`; `score_crossover.py::_assert_scoreable_year` refuses any bench read ≥ 2026. |
| **T1-FF full-forward** (`--forward-from-base`) | **No** — keeps the plain window rules (2021 floor, `end ≤ 2025`, 2022 bridged). | **No.** |
| **`run_full_horizon.py`** (forecast mode) | Mechanically yes, **semantically no**: with `weather_year=2024` and `start_year=2022`, `_scale_demand` takes the **backward-span branch and de-grows** 2024's measured load into 2022. That is a synthetic 2022, not a hindcast of it. | Only past the 5-year guard. |

**So "2022–2025 hindcast + 2026–2035 forecast in one run" has no implementation.** The two
regimes live in two different harnesses with disjoint, non-adjacent legal windows
(`≤2025` and `≥2023`/`≥2026`), and the one year the request starts on is the one year
*both* harnesses are built to skip.

### 2.3 What a 2022 START would require — and a correction to the recorded demand blocker

**What 2022 needs, if the owner wants it:**

1. **A freeze lift.** 2022 is validation tier; `holdout-freeze.json` is **ACTIVE** (re-armed
   2026-08-06). Solving, scoring *or registering* 2022 is a spend. NEISO holds `complete`, so
   the marker exists — the freeze is what is in the way, and only the owner lifts it.
2. **A code change to un-bridge it**, in both `market_sim.runner.HINDCAST_BRIDGE_YEARS` and
   `scripts/lib/holdout_policy.HINDCAST_BRIDGE_YEARS` (the runner keeps its own constant with
   a parity test), plus the `_validate_window` floor. This is not a flag; 2022 is bridged by
   construction.
3. **A 2021 seed decision.** `HINDCAST_SEED_YEARS = {2021}` and 2021 is marker-free *by
   design* — it prices the first evolution step and is never scored. A window that *starts*
   at 2022 has no seed year, so the first evolution step (2022→2023) would be priced off no
   solved prior. Either 2021 comes in as the seed (making it 2021–2035, **15** solve-years) or
   the first step runs unpriced.

**Correction — the demand driver is not a blocker, and it does not block 2019/2020 either.**
`ASSESSMENT-neiso87-declaration-2026-08-06.md` §3.1 records NEISO 2019/2020 as hard-blocked:
*"`eia_demand_profiles.parquet` carries NEISO for 2021–2025 only … the LP cannot be constructed
at all."* That probe called **`load_demand_meta`**, not `load_demand`. Reproduced exactly this
session (loader probes; no LP, no model output):

```
load_demand_meta('NEISO', 2019) -> ValueError: No EIA-930 data for ISO 'NEISO' in year 2019   [neiso-87's exact error]
load_demand_meta('NEISO', 2021) -> peak_mw 25,101   [neiso-87's exact number]
load_demand_meta('NEISO', 2022) -> peak_mw 24,233   [neiso-87's exact number]

load_demand('NEISO', 2019, cfg) -> OK  (5, 8760)  peak 20,617 MW   95.54 TWh
load_demand('NEISO', 2020, cfg) -> OK  (5, 8760)  peak 21,524 MW   92.10 TWh
load_demand('NEISO', 2021, cfg) -> OK  (5, 8760)  peak 22,529 MW   98.55 TWh
load_demand('NEISO', 2022, cfg) -> OK  (5, 8760)  peak 22,933 MW  100.21 TWh
```

`load_demand` is what `runner.py:961` calls to build the LP's demand array.
`load_demand_meta` is a summary helper with **no consumer in the solve path at all** (its only
repo-wide caller is `scripts/probes/_pjm159_final_readiness.py`). NEISO's demand comes from the
per-BA EIA-930 `ISNE hourly` extract via `DEMAND_LOADERS["NEISO"]`, which resolves
**8,760 h for every year 2016–2025** (raw frame: 2015 partial, 2016–2025 complete, 2026 partial
at 3,359 h). The `eia_demand_profiles` fallback is only reached `if raw_mw is None`.

This does **not** re-open the `final` question — neiso-87's §3.3 argument stands on its own and
is the stronger one (2019 had **0** actual RT hours > $300, so C3c returns a free small-count
PASS and cannot discriminate on NEISO's declared frontier), and the three genuine *scoring*
gaps it lists (`calibration_reference.json`, `actual_tail.json`, `NEISO_2019_renewable_capacity.csv`)
are unaffected. It does mean the recorded reason is wrong: **2019 is not undispatchable; it is
unscoreable and non-discriminating.** Correcting that matters here because the same claim was
about to be carried into this assessment as a reason the 2022–2025 leg could not be built.

---

## 3. Q3 — what the keeper formula does and does not carry into forecast mode

Read from the keeper's committed `results/calibration/neiso83_ca1reclass_B/run_config.json`
(685 config keys), then tested by **constructing** `ScenarioConfig(mode="forecast")` with each
arm and observing what the model accepts, coerces or refuses. Rule 13 is the test the code
itself applies.

### 3.A Code-REFUSED in forecast mode — a hard substitution, enforced not merely intended

`ScenarioConfig.__post_init__` raises on `_BACKCAST_ONLY_OVERLAY_FIELDS` plus
`outage_source="historic"`, *"including the capacity-hindcast/crossover harness
(mode='forecast', hindcast=True): that IS the forecast path being validated, so feeding it the
measured record makes the validation self-fulfilling."* Four of the keeper's arms hit it:

| keeper arm | value | what replaces it in forecast mode |
|---|---|---|
| `outage_source` | `"historic"` (CAMPD unit-outage windows) | `"statistical"` — EFORd/planned-outage draws. The **entire** measured availability envelope the keeper is calibrated against is gone. |
| `gas_monthly_actuals` | `True` (measured EIA-923 ISO-month delivered gas) | forward gas path (AEO / `crossover_forward_gas_path`). |
| `gas_hub_basis_overlay` | `True` (measured ISO-NE MA / constrained-hub month basis) | `basis_differential_factor` on the forward path. **This is the input neiso-85/86 spent two sessions repairing**; the forecast does not consume the repaired series at all. |
| `gas_hub_basis_daily` | `True` (measured AGT city-gate daily prints) | nothing — no daily hub shape forward. |

### 3.B Forward-ADMISSIBLE but DEFAULT-OFF — and unreachable from the forecast runner

These eleven construct **without error** in `mode="forecast"` (verified), so they are
rule-13-admissible forward. But they are `False` by default **and there is no way to set them
through `scripts/run_full_horizon.py`**: its `reference_config()` is documented as *"all
defaults, forecast mode"* and passes only `iso`, `mode`, horizon, `capacity_market_clearing(_by_iso)`,
`transmission_expansion_enabled`, `electrification_path`, `entry_screen_diagnostics`,
`caiso_nqc_accreditation`, `forecast_xyear_warmstart` and the four D-1/D-2 arms.

| keeper arm | forecast default | what it is |
|---|---|---|
| `measured_ct_heat_rates` | `False` | measured CT heat rates (neiso-caiso156 meter screen) |
| `measured_chp_heat_rates` | `False` | measured CHP heat rates (neiso-81) |
| `cc_steam_part_reclass` | `False` | **the current keeper's own promoted mechanism** (neiso-83) |
| `nuclear_unit_availability` | `False` | per-reactor availability overlay (neiso-71) |
| `neiso_winter_fuel_inventory` | `False` | winter fuel-security stack |
| `neiso_winter_fuel_mustrun` | `False` | winter fuel-security must-run |
| `dual_fuel_switching` | `False` | oil/gas dual-fuel switching |
| `dual_fuel_oil_reattribution` | `False` | dual-fuel oil re-attribution |
| `temp_dependent_derate` | `False` | temperature-dependent derate |
| `scarcity_price_overlay` | `False` | scarcity price formation |
| `gas_plant_monthly_fuel_pricing` | `False` | plant-monthly fuel pricing |

Plus `weather_year`: keeper **2023**, forecast default **2024**.

> **This is the finding that matters most for the request as phrased.** "A 2022–2035 run built
> on the keeper's recipe" is **not what any NEISO forecast has ever been.** The T1-F run on the
> board (`neiso-2026-2030-ffr3a2-t1f`) is an all-defaults forecast: it carries **none** of these
> eleven, including `cc_steam_part_reclass` — the mechanism the *current keeper was promoted
> for*. NEISO's winter fuel-security stack, its dual-fuel physics, its measured heat rates and
> its scarcity price formation are all absent from every forecast number NEISO has produced.
>
> The gap is not a rule-13 problem — the code says these are admissible forward. It is a
> **plumbing** problem: the keeper's recipe has no route into the forecast entry point. Closing
> it needs either a keeper-recipe carrier on `run_full_horizon.py` or a scenario-YAML path
> through `assert_config_schedulable`. Until then, "forecast built on the keeper" is not a
> thing the repo can express, and no §2.1b authorization should be read as authorizing it.

### 3.C Forecast-only posture the keeper has never seen

`datacenter_load_path="mid"` (coerced `off` in backcast), `correlated_forced_outage=True`
(ERCOT-only curve — inert at NEISO, matrix §4 item 6), `entry_lookahead_reprice=True`
(forecast/screen-only), `rps_enabled=True` (the keeper runs `False`), and `capacity_market_clearing`
resolved **ON** for NEISO via the shipped `capacity_market_clearing_by_iso`
(`{PJM, MISO, CAISO, NEISO}`). Also: the keeper runs `priced_interchange=False`, i.e. demand net
of the **measured** EIA-930 net-interchange wedge; forward, that wedge must come from the priced
`HQ_import` node instead — a node whose forward behaviour **no keeper validates**.

---

## 4. Q4 — the capacity-evolution surface, which is where a 2035 horizon lives

### 4.1 State at HEAD, for NEISO

| element | state | note |
|---|---|---|
| **retirement rule** | `"pipeline"` (owner D-1, 2026-08-02) | Execution lags: coal 3, gas_cc 1, gas_ct 2, gas_st 1, oil 1, nuclear 3. Legacy per-fuel thresholds do not apply under the pipeline rule. |
| **reserve-margin backstop** | **ON** | `reserve_margin_build_enabled=None` (tri-state) resolves per market design; NEISO has `MARKET_DESIGN.capacity_market=True` → **fires**. The live T1-F carries a **backstop share of 11.7 %** (FC-2 CAVEAT band `(10 %, 30 %]`). |
| **confirmed exits** | `confirmed_exits_enabled=True`; registry has **2 rows, 459.2 MW, both 2028** | The *only* exogenous fossil exit channel, and it is empty for **2029–2035**. Every exit in the back two-thirds of the requested horizon is the economic screen alone. |
| **storage entry** | `storage_capacity_value=True`, `storage_degradation=True`, `storage_deployment="mid"`, `storage_measured_base_fleet=True` | Value stack, not compound growth. Live T1-F builds storage in **one** year (720 MW, 2029) and none in the other four. |
| **capacity_market_clearing** | **curve-ON** | Net CONE 108.94 $/kW-yr, FCA-18 curve, `demand_curve_delivery_year="2027-2028"`. |
| **adequacy basis** | `claimed_capability` (R5b, no EFORd derate), PRM **0.11015**, DR fraction 0.09701, external firm ties 567 MW | Both R5b halves closed on ISO-NE's own published basis (FF-2B). |

### 4.2 Open BLK rows, read rather than re-derived

- **BLK-9** (capacity payment ≥ 1.26–4.92× FOM ⇒ fossil economic retirement arithmetically
  impossible, nuclear inverted): **no longer the active default for NEISO** — the FF-2C flip
  put NEISO on the CR-1 curve, so fixed-mode BLK-9 now persists only for NYISO.
- **BLK-10** (adequacy-backstop / additions-need over-fire; the curve-ON over-retirement wave):
  **OPEN.** The row's own status is *"re-measure after D1 lands"*, with evidence from PJM
  (6.43 GW gas_ct in one step) and NYISO (gas_ct +5,494 %).
- **R5b** (NEISO qualified-capacity pairing): **CLOSED**, both halves — with a live dating
  caveat quoted verbatim: *"the FCM sunsets after CCP2027-2028 (final FCA already held); this
  basis is current-through-sunset only, not checked against ISO-NE's Capacity Accreditation
  Reform successor."*
- **R5c** (hydro unaccredited): **CLOSED 2026-07-31 by FFR-1C**; NEISO hydro nameplate 1,899 MW
  now credited.

### 4.3 Is the curve-ON over-retirement wave (BLK-10) bounded for NEISO? **No.**

BLK-10 asks to be re-measured after D1. **D-1 was signed 2026-08-02; the live NEISO T1-F solved
2026-08-03 with `retirement_rule="pipeline"`. It IS the post-D1 measurement**, and it shows the
signature intact:

- a **3,297.9 MW single-year exit** in 2027 — **13.6 %** of the 24,209.58 MW NEISO fleet — with
  **zero** build in the same step;
- reserve margin **15.26 % → 0.70 % → −0.61 %**, i.e. straight through the requirement and
  below zero;
- **I7 FAILs in 2028** (25,386 < 25,604 MW) and **I12 WARNs** at both ends
  (2026: 15.3 % over a 15.2 % ceiling; 2028: −0.6 % under a 0.2 % floor);
- the correction arriving **two years late** and then overshooting — 643 MW thermal + 1,802 MW
  renewables + 720 MW storage in 2029, then 1,500 MW thermal in 2030;
- an **11.7 % backstop share**, i.e. the force-build channel is doing an eighth of the work.

That is de-firm → overshoot, unbounded, inside a **five-year** window. Nothing in the record
suggests it damps over ten more. **BLK-10 should be updated to record NEISO as a third measured
instance, post-D1** — I have not written that row myself (§7: it is a cross-ISO lane's ledger
and its PJM/MISO text is not mine to re-measure).

### 4.4 The 2035-specific problem the board does not surface: the net-CONE vintage cliff

`MARKET_DESIGN_VINTAGES["NEISO"]` runs `2020-2021 … 2027-2028` and **stops**. FF-G3's
hold-last carry then prices **every year from 2028 onward on the FCA-18 2027/28 anchor held
flat**. In a 2022–2035 span that is **8 of 14 years — 57 % of the horizon — on a single frozen
anchor**, and per R5b the construct that anchor describes (the FCM) **sunsets after
CCP2027-2028**. FF-G3's owner box **D-3(a), the forward-evolution MODE, is still DEFERRED and
unsigned** — so there is no signed methodology for what the anchor does past the last vintage,
in the ISO where the horizon spends most of its time past it.

For a curve-ON ISO this is not a second-order calibration detail: the capacity price is what
the retirement screen and the entry screen both read. The 2029–2035 half of the requested run
would be a capacity-market simulation of a capacity market that has been retired.

### 4.5 Compute is not the constraint, and the board is right about that

T1-F measured **553.3 s / 5 years (9.2 min)**, global peak RSS **3,417 MB**; plan §2.4 anchors
NEISO at ~85 s median/yr, 25 yr = 72 min, 3.9 GB. **14 years ≈ 20–26 min at ~4 GB, pairable.**
The board's readiness note is exactly right and worth quoting: *"Compute is not the binding
constraint; the T1-F structural blockers are."*

**Environment note, separate from the above:** this container ships **no scientific Python
stack** — `pandas`, `pyarrow`, `numpy`, `pydantic`, `scipy` were absent and installed by this
session for the loader probes; `highspy` is still absent and `data/clean/` is empty. Nothing
could have been solved here today regardless of authorization. Routine to fix, but it means
"readiness green" describes a different machine than this one.

---

## 5. Q5 — the three carried-forward backcast items, each with a materiality call

### (i) The committed keeper no longer reproduces at HEAD in 2025 — **MATERIAL, bounded, and it blocks the A/B discipline before it blocks the forecast**

Recorded at neiso-87 §4.0: replaying the keeper's own recipe at HEAD against unmodified data
reproduces 2023 and 2024 **identically** and diverges in 2025, confined entirely to
**January (731 h)**, max |Δλ| $25.52 in one hour, mean Δλ **−0.334 $/MWh** over the year
(69.715 vs 70.049). The AGT daily series, the monthly basis rows and the FFR-7B RPS change are
all ruled out by direct comparison; the cause lies in ~50 commits and was not isolated.

**Call: material, but not on the level — on the method.** −0.33 $/MWh is 0.5 % of level and
would not by itself change a forecast trajectory. What it does change is that **the committed
keeper bundle is no longer a valid A/B baseline**, so every future NEISO comparison must solve
its own same-HEAD control. That is a per-session cost on every NEISO lane, and it compounds:
the longer it goes un-isolated, the more drift accumulates between the calibrated recipe and
the code a forecast would actually run. **For a forecast specifically it is the weaker of the
three — §3.B is the one that bites**, because a forecast does not inherit the keeper's recipe
at all. Isolating it is worth a bisect session; it is not on the critical path to this gate.

### (ii) The CAMPD outage-detector vintage split — **NOT MATERIAL to any forecast or hindcast leg**

2018–2022 windows were appended at a different detector vintage than the committed 2023–2025
rows, and the file carries no vintage column, so the split is invisible in the data.

**Call: it cannot reach the hindcast leg, by code.** The overlay is consumed only under
`outage_source="historic"`, and `__post_init__` **raises** on that in `mode="forecast"` — with
the refusal text naming the hindcast harness explicitly: *"This applies to the
capacity-hindcast/crossover harness too (mode='forecast', hindcast=True)."* Every hindcast,
crossover, T1-F, T1-H and T1-X leg runs `outage_source="statistical"`; NEISO's live T1-F FC-7
confirms it at the verdict layer (`"no backcast overlay armed (outage_source='statistical')"` →
PASS). The vintage split is a **backcast-only** exposure, and specifically an exposure of the
out-of-training backcast years 2018–2022 — i.e. it bears on the 2022 touchpoint and on any
future 2020/2021 touchpoint, **not** on a forecast. It stays an open backcast item and does not
gate this decision.

### (iii) The demand loader's "corrupted legacy series" warning — **NOT MATERIAL. The warning is real; the inference from it is not.**

The claim carried forward is that the loader falls back to the corrupted legacy
`eia_demand_profiles` series *for every NEISO year including in-sample*, and that this reaches
the forecast because demand is the primary driver.

**Call: it does not reach the solve at all, in any mode.** Three facts, each checked:

1. **The warning is emitted by `_demand_profile_clean`**, which `load_demand` reaches **only
   `if raw_mw is None`** — i.e. only when the ISO's per-BA extract fails. NEISO's per-BA
   `ISNE hourly` loader returns a full 8,760 h series for **2019–2025** (probed above), so that
   branch is never taken in a NEISO solve. The `load_demand` probes in §2.3 emitted **no such
   warning** for any year.
2. **The path that *does* warn is `load_demand_meta`**, reproduced this session — it warns for
   2021 and 2022 and errors for 2019/2020, matching neiso-87's observation exactly. It has
   **zero consumers in the solve path** (only `scripts/probes/_pjm159_final_readiness.py`).
   The warning was a probe artifact.
3. **The trigger is an empty `data/clean/`**, which is gitignored and disposable by design —
   *"routinely absent until someone runs `scripts/regenerate_clean.py demand-profile`."* It is
   an environment state, not a defect in a committed input. (It is confirmed empty here.)

And for the forecast years specifically the question does not arise: `_demand_profile_clean`
returns `None` **silently** for any `(iso, year)` the raw manifest does not cover — *"an
uncovered forecast year"* — because forward demand is growth-scaled from `weather_year`, not
read per-year. **Running `scripts/regenerate_clean.py demand-profile` remains good hygiene and
would silence the warning; it is not a prerequisite for anything.**

---

## 6. Recommendation

**Do not authorize the 2022–2035 solve.** Not because NEISO is far from the gate — it is the
closest ISO to it, and leg (a) now genuinely passes — but because the requested instrument is
undefined, unbuildable, and would exercise the one mechanism NEISO has no measured skill on.

Ranked, with an owner for each:

| # | blocking item | owner | why it blocks |
|---|---|---|---|
| **1** | **Window is 14 solve-years vs a 5-year cap, and exceeds the deferred T2 tier itself** | **Owner** (§2.1b(d)) | Not a lane's to fix. If a long-horizon NEISO run is wanted, the ask should be **T2 (2026–2035, 10 yr)**, which the ladder at least defines — and that is still gated on (b) and (c). |
| **2** | **No instrument spans it; 2022 is bridged/refused by every harness** | **FF harness lane** + **owner** (freeze) | Needs a code change in two `HINDCAST_BRIDGE_YEARS` constants + `_validate_window`, a seed-year decision, and an explicit freeze lift. None is in this session's remit. |
| **3** | **T1-H FC-3: 12/12 capacity-evolution bands FAIL** | **FF-1A / FF-2A retirement + entry lanes** | A 2035 horizon *is* capacity evolution. Every retirement band and every addition band misses. |
| **4** | **BLK-10 unbounded for NEISO, now measured post-D1** — 3.3 GW exit wave, RM to −0.61 %, I7 FAIL 2028, 11.7 % backstop | **Flip-gate / retirement lane** (BLK-10 owner) | This is §2.1b(b)'s live blocker. It is a real behavioural defect, not a bookkeeping one. |
| **5** | **§2.1b(c) has never been satisfied — NEISO has no T1-X crossover run** | **FF-1D crossover lane** | The board scores (c) on the readiness half only. The input-gap half is unmeasured for NEISO. |
| **6** | **The keeper's recipe has no route into the forecast entry point** (§3.B, 11 mechanisms) | **FF harness lane** | Until this is closed, "a forecast built on the keeper's recipe" cannot be produced, so no authorization can mean what the request means. **Owner elected this as the FIRST item — D-88.1, §6.1.** |
| **7** | **Net-CONE ladder ends 2027-28; FCM sunsets; D-3(a) unsigned** | **Owner** (FF-G3 box D-3(a)) + L-CAP | 8 of 14 requested years price capacity on a frozen anchor for a construct that has been retired. |

### 6.1 OWNER DECISIONS, taken 2026-08-06 on this assessment

Put to the owner at the close of session neiso-88 (`AskUserQuestion`) and signed the same day.
**These SUPERSEDE the ordering this session originally recommended** (which led with the T1-X
crossover); the record of that recommendation is kept below so the change is visible rather
than silently overwritten.

| # | decision | owner's choice | consequence |
|---|---|---|---|
| **D-88.1** | What the next NEISO forecast session does | **Close the recipe-carrier gap first** (§3.B) | The T1-X crossover is **deferred behind it**, not cancelled. Rationale the choice implies: I7 is currently measured on a forecast that carries **none** of the keeper's eleven mechanisms, so its magnitude — and possibly its existence — is not yet attributable. Diagnosing a blocker on a stripped-down model risks chartering a lane against an artifact. Build the carrier, re-run T1-F, *then* see what survives. |
| **D-88.2** | Who fixes the board's stale cross-ISO I4/A1 text | **A separate cross-ISO session** | This session corrected the **NEISO row only**. The `gate_reading` and `honest_unfit` "I4 / A1" prose, and the per-ISO blocking rows for CAISO/PJM/MISO, stay as they are until that session runs. The evidence is already gathered and cited in §1.1 — all four sidecars read `I4 = PASS ("closes")` — so that session does not need to re-measure, only to re-word and re-verify. |
| **D-88.3** | The keeper's HEAD non-reproduction (§5 item (i)) | **Bisect it in its own session** | Not absorbed into another lane and not papered over with a re-solve. The reason bisecting wins over "live with it": the workaround (every NEISO A/B solves its own same-HEAD control) is a permanent per-session tax, and the drift compounds silently the longer the cause is unknown. A re-solve would fix the symptom without answering whether the change was intended. |

**Consequent order of work:**

1. **Close the recipe-carrier gap** (§3.B) — give `run_full_horizon.py` a route for the
   keeper's eleven default-OFF, forward-admissible mechanisms (or a scenario-YAML path through
   `assert_config_schedulable`). Then **re-run T1-F** and re-read I7 against a forecast that
   actually carries NEISO's winter fuel-security stack, dual-fuel physics, measured heat rates
   and scarcity price formation. **[D-88.1]**
2. **Bisect the keeper drift** (~50 commits, Jan-2025, −0.33 $/MWh) so NEISO has a valid A/B
   baseline again. Independent of 1 and can run in parallel. **[D-88.3]**
3. **Refresh the board's cross-ISO text** — leg (a), the closed A1 leak, and the I7 reality
   across four ISOs. **[D-88.2]**
4. **Then** NEISO's T1-X crossover (2023–2027, 5 yr, schedulable today, ~10 min) to close
   leg (c)'s missing half — now interpretable, because the run it is compared against will
   carry the keeper's recipe.
5. **Then** charter the I7/BLK-10 lane, if step 1 leaves a blocker to charter.
6. Only then put a **T2 (2026–2035)** authorization to the owner — with the net-CONE
   forward-mode question (D-3(a), §4.4) answered first.

*Session neiso-88's original recommendation, superseded by D-88.1: run the T1-X crossover
first (cheapest, closes leg (c), measures the §3 gap), then charter I7/BLK-10, with the
recipe-carrier gap fourth. The owner inverted it — carrier first — on the attributability
argument in D-88.1.*

**One thing this assessment does not do:** it takes no position on `final` or on the locked
test. NEISO's locked test is **UNSPENT**; the record claiming otherwise is flagged for owner
correction at neiso-87 §1 and is not repeated or corrected here.

---

## 7. What this session changed, and what it deliberately did not

**Changed:**

- **This document.**
- **`frontend/data/forecast/program-status.json`, the NEISO row only** — corrected to HEAD:
  `keeper` → `2026-08-05-neiso-83-ca1-reclass`; gate **(a) fail → pass**; gate (b) detail
  I4 → **I7 (2028, 25,386 < 25,604 MW)**; `blocking_rows` likewise; `fc.FC-2` **PASS →
  CAVEAT** (the board carried the FF-2D baseline value while the live FFR-3A-2 verdict and the
  FFR-3A2 scorecard both read CAVEAT); gate **(c) na → fail** with the reason (no NEISO T1-X).
  This is a **committed seed**, and `register_forecast_run.py --reindex` regenerates
  `program-status.js` from it — so the correction is the supported path, and it records HEAD
  rather than moving any verdict.
- **`docs/mechanism-testing-matrix.md` §5.6** — a neiso-88 block recording that this session
  ran, tested nothing, and moved no cell.

**Deliberately not changed:**

- **No matrix cell verdict, and no matrix header keeper/gate re-stamp.** Rule 28d: an
  assessment tests no mechanism, so it mints nothing. The §5.6 header already names the
  correct keeper.
- **The board's cross-ISO `gate_reading` and `honest_unfit` "I4 / A1" prose**, which still
  names CAISO/PJM/MISO/NEISO as blocked on a leak that passes in all four. I verified all four
  sidecars, but rewriting four ISOs' program-level narrative from one ISO's session is the
  cross-ISO lane's call — **flagged here as the highest-value board item outstanding.**
- **`docs/gap-register-2026-07.md` BLK-10**, which should record NEISO as a post-D1 measured
  instance (§4.3). Same reasoning: its PJM/MISO text is not mine to re-measure.
- **`calibration-complete.json`** and every locked-test record. Owner acts.
- **No forecast run was registered**; had one been, it would go to the forecast namespace via
  `scripts/register_forecast_run.py` alone (rule 15).

**Rule compliance.** Rule 22: no out-of-training year was solved, scored or registered; the
loader probes read *inputs only* and produce no model output, which the 2026-08-06 amendment
places explicitly outside the spend (*"what is held out is the SCORE, never the DATA"*). Rule
16: the backcast keeper was not touched. Rule 15: nothing registered on either dashboard.
Rule 27: the model assignment is Opus, and no file ≥300 lines was rewritten.
