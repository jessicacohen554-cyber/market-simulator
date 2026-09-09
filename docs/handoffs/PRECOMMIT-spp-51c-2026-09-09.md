# PRECOMMIT — SPP-51c: an hourly allocation instrument for SPP's measured wind curtailment, keyed on OVERSUPPLY

**Lane** SPP-51c · **Model** Opus 5 (`claude-opus-5`) · **Date** 2026-09-09 ·
**Branch** `claude/spp-51c-curtailment-allocation-izd5x2` · **Base** `b849a51b` (`origin/main` at
launch) · **Data profile** `spp` · **Charter** SPP-51b `docs/handoffs/FINDING-spp-51b-2026-09-09.md`
§5 **R-1** · **Predecessors** SPP-51b (the diagnosis), `FINDING-spp-price-family-2026-09-07.md`
(why a band is not the answer).

**This document is pushed BEFORE any number produced by the instrument is read.** Nothing in §2–§6
has been computed. §1 records only what is already committed in a predecessor's FINDING, cited to
it, and re-derives nothing.

---

## 0. What this lane is, in one paragraph

SPP-51b established, at zero LP, that SPP's C3a residual is a **missing bottom tail**: the market
prints 992 / 1,172 / 1,018 hours below \$0 and the model prints 4 / 7 / 0, and those hours alone
carry 109 / 222 / 192 % of the whole load-weighted error. It established that the **price-formation
path is already correct and already armed** — `wind_mc = −$26.000/MWh`, and in the 7 / 7 / 3 hours a
year the LP holds wind strictly interior the zonal price is **exactly −\$26.00**. And it established
that the defect is a **quantity in one input**: SPP's wind bound is `delivered_EIA930(t) / (1 −
0.096501)`, flat to 99.94 / 99.93 / 99.98 % of hours, so the measured 9.65 % curtailment is spread
**uniformly across all 8,760 hours — everywhere except where it happened.** The energy is there
(11.006 / 11.676 / 11.798 TWh available against 5.676 / 7.425 / 5.355 TWh needed); its **allocation**
is not. SPP-51b costed the obvious repair — reallocate on a **wind-availability** (reanalysis) shape
— and measured it insufficient: +999 / +1,005 / +2,022 MW against a 5,721 / 6,335 / 5,260 MW
deficit, 17.5 / 15.9 / 38.4 %. **This lane builds an instrument keyed on OVERSUPPLY instead of on
availability.** That is the one sentence that distinguishes it from the arm already priced, and §2
is written so it cannot quietly collapse back into that arm.

**The annual level is FROZEN** (rule 23 `[R-FROZEN-DERIVE]`): SPP-32's measured 9.6501 % stands
untouched and is not re-derived. This lane re-allocates the identical annual energy across hours and
**changes no annual total by construction** — that identity is leg **F-1** below and it is checked,
not assumed.

---

## 1. What is inherited, not re-measured (every number cited to a committed predecessor)

| quantity | 2023 | 2024 | 2025 | source |
|---|---|---|---|---|
| measured hours < \$0 | 992 | 1,172 | 1,018 | 51b §2 |
| model hours < \$0 (system LW) | 4 | 7 | 0 | 51b §2 (keeper-3 surface) |
| flat gross-up factor | 1.106808 | 1.106808 | 1.106808 | 51b §0.4 |
| LP re-curtailment, SPP-50 | 0.00058 % | 0.00172 % | 0.00030 % | SPP-50 registry sidecar |
| wind identity model/delivered, SPP-50 | 1.10680 | 1.10678 | 1.10681 | SPP-50 registry sidecar |
| C3a, SPP-50 (current input surface) | +15.0 % | +12.1 % | +14.2 % | SPP-50 registry sidecar |
| oversupply deficit in the negative hours | 5,721 MW | 6,335 MW | 5,260 MW | 51b §3 B-3 |
| availability-shape arm's reach | +999 MW | +1,005 MW | +2,022 MW | 51b §3 B-2a |
| availability-shape arm's share of C in the negative hours | 24.7 % | 27.5 % | 33.3 % | 51b §3 |
| uniform (today's) share of C in the negative hours | 11.3 % | 13.4 % | 11.6 % | 51b §3 |

**The last two rows are the bar this lane's instrument must clear.** They are the reason a
prediction in §3 is stated as a *share*, not as a MW.

---

## 2. THE INSTRUMENT — declared in full, before any of its numbers exist

### 2.1 The name and the gate

A new `ScenarioConfig` field, **`vre_curtailment_oversupply_allocation: bool = False`** — GATED,
**default OFF** (rule 24 `[R-REGISTRY]`), **ISO-agnostic** with **no SPP constant anywhere in shared
code** (rule 25 `[R-ISO-SCOPE]`). It fires wherever the reference-rate gross-up already fires — any
ISO-year-fuel in `_UNCURTAILED_FALLBACK_ISOS` with a reference curtailment rate, i.e. exactly the
`renewables._forecast_uncurtailed_cf` seam — and **replaces** that construction rather than stacking
on it (rule 19 `[R-ONE-MECH]`). Default-off means every one of the six existing keepers, and SPP's
own keeper-3, is byte-identical with the field absent from its recipe.

### 2.2 The construction, stated so it cannot be reshaped to the answer

All quantities in MW on the ISO's own 8,760-hour chronological clock (SPP's demand and its
renewables are drawn off the **same** EIA-930 `SWPP hourly` frame — `eia930/demand.py`
`_spp_demand_source` — so `demand[t]` and `delivered[t]` refer to the same wall-clock hour, and no
alignment step is introduced).

1. **Delivered** — `delivered(t)`: the EIA-930 delivered series for the fuel, identical to the series
   the flat rule grosses up. Unchanged.
2. **The frozen annual energy** — `C = (r / (1 − r)) · Σ_t delivered(t)` with `r = 0.096501`
   (SPP-32, rule 23). **This is the same C the flat rule distributes.** Nothing about the level moves.
3. **The oversupply indicator** — net load on delivered renewables:
   `NL(t) = load(t) − delivered_wind(t) − delivered_solar(t)`, where `load(t)` is the ISO total of the
   LP's own demand array (`eia930.demand.load_demand(iso, year, iso_config)` summed over zones — the
   same call the runner makes, `include_interchange=True`, which for SPP is the measured scalar
   schedule) and the two delivered series are the EIA-930 series already consumed.
   **Every leg is fully metered — there is no proxy and therefore no proxy error.** This is the
   substantive difference from the arm SPP-51b costed, whose key was a *reanalysis wind shape*.
4. **The physical cap** — `H(t) = max(0, cap_online(t) − delivered(t))`, where `cap_online(t)` is the
   fleet capacity online in that hour's month, summed over zones: the identical array `_mw_to_cf`
   divides by. Potential can never exceed the fleet's nameplate.
5. **The allocation** — a water-fill on net load:
   `curt(t; λ) = min( max(0, λ − NL(t)), H(t) )`, and **λ is the unique root of
   `Σ_t curt(t; λ) = C`**, found by bisection.
6. **The bound handed to the LP** — `potential(t) = delivered(t) + curt(t; λ*)`, converted to a CF
   profile by the existing `_mw_to_cf` and returned in place of `delivered(t)/(1−r)`.

**Why this is the oversupply key and not the availability key.** `NL(t)` is low when load is low
**and** renewables are high — jointly. A reanalysis shape is high whenever the wind blows, whether or
not the system had anywhere to put it. Curtailment is availability *meeting nowhere to go*, and
`NL(t)` is the second half that SPP-51b §3's arm did not carry.

**Why the functional form is a water-fill and not a threshold.** A threshold would be a fitted
parameter. λ is **not chosen** — it is the unique value that makes the frozen annual identity hold,
exactly as SPP-51b's `Â` was. It has a physical reading (the level of net load below which SPP could
not turn further down) and it is *reported*, never *set*.

### 2.3 Degrees of freedom — the ledger entry this instrument adds

**ZERO new free parameters**, and I state each candidate and why it is not one:

| candidate | why it is not a free parameter |
|---|---|
| `r = 0.096501` | SPP-32's measured annual rate, frozen by rule 23, **unchanged by this lane** |
| `λ` | determined uniquely by the frozen annual identity; not chosen, not swept, not selectable |
| the cap `H(t)` | the fleet's own EIA-860 online capacity — a measured physical limit |
| `load(t)`, `delivered(t)` | already-committed measured inputs the LP consumes today |

Nothing here is a multiplier on a residual, an adder, a haircut, a load proxy or a rescaled input.
The rules-1/13 authorized offer-curve channel is **not used**: SPP's `authorized_price_tuning` stays
NONE and every offer band stays 1.0.

### 2.4 Rule 13 `[R-MEASURED]` — the forward test, answered before the build

*Could this same quantity be produced for a forward year from forward drivers, and would it respond
to changed conditions?* **Yes, on every leg.** A forecast year has a forecast load array, forecast
wind/solar profiles and a forecast fleet capacity, so `NL(t)` regenerates; `r` is the reference rate
a forecast year **already uses today**; λ re-solves from those. And it responds correctly to changed
conditions in the direction physics requires: add wind capacity or flatten load and NL falls, λ's
root moves, and **more** energy is allocated to the low-net-load hours. Nothing in the construction
reads a target-year price, a target-year dispatch outcome or a residual.

### 2.5 The alternatives, refused or unavailable — stated BEFORE any measurement

The charter named three candidate sources. Each is adjudicated here, in advance, so none of these
reasons can be a post-hoc rationalisation:

- **SPP's own 5-minute VER-curtailment product (`portal.spp.org` `ver-curtailments`) — UNAVAILABLE,
  not refused.** `data/raw/spp-hsl/README.md` records the block: `isPublic: true`, returns `200 []`
  and 404s on download for an anonymous caller (evidence `FINDING-spp-12-2026-09-06.md`). If it ever
  unblocks it is **strictly better than this instrument** and should replace it; that is stated here
  so this lane's build is never mistaken for a preference over the real series.
- **The MMU ASOM figures (`data/raw/spp-hsl/spp_wind_curtailment_annual.csv`) — ALREADY IN USE, and
  they are the frozen level, not an allocation.** They publish an *average hourly MW* per year and
  no hourly profile at all. They cannot allocate anything.
- **SPP's RTBM binding-constraint log (`data/raw/spp-binding-constraints/`) — REFUSED AS AN INPUT ON
  RULE 13.** It is a measured market *outcome* log with no forward analogue: a 2035 forecast year has
  no binding-constraint file and no way to produce one from forward drivers, so an allocation keyed on
  it would be a backcast-only overlay that could never regenerate. **It is used instead as an
  EXTERNAL VALIDATION axis (leg V-1, §4), which is a diagnostic and not an input** — the distinction
  rule 13 turns on.
- **A wind-availability reanalysis shape — ALREADY PRICED AND INSUFFICIENT** (SPP-51b §3). This lane
  does not re-propose it, and §2.2 step 3 is written specifically so the instrument cannot degenerate
  into it.

---

## 3. PRE-REGISTERED PREDICTIONS — sign and magnitude, none of them computed

**Phase 0 is fully zero-LP: every leg in §3.1 is computable before any solve, and is computed before
any solve.**

### 3.1 The instrument's own footprint (zero LP)

- **F-1 (identity — the leg that voids everything if it fails).** `Σ_t potential(t)` must equal
  `Σ_t delivered(t) / (1 − 0.096501)` to within **0.1 %** in every year, and `potential(t) ≥
  delivered(t)` in every hour. **If λ has no root** — i.e. `Σ_t H(t) < C`, the fleet's own capacity
  headroom cannot hold the frozen annual energy — **the instrument has failed its own construction, I
  report an instrument failure and spend zero LP.**
- **F-2 (concentration — the discriminating prediction).** The share of `C` landing in that year's
  **measured**-negative hours is **≥ 45 %**, against **11.3 / 13.4 / 11.6 %** for today's uniform rule
  and **24.7 / 27.5 / 33.3 %** for the availability arm SPP-51b costed.
- **F-3 (breadth).** The number of hours receiving any allocation (`curt(t) > 0`) lands between
  **1,200 and 4,000** per year (today: 8,760, uniformly).
- **F-4 (reach).** The mean lift of the wind bound in the measured-negative hours, over today's flat
  bound, is between **+3.0 and +8.0 GW** — against the availability arm's **+1.0 / +1.0 / +2.0 GW**
  and the measured deficit of **5,721 / 6,335 / 5,260 MW**.
- **F-5 (λ, reported not set).** λ* lands between **15 and 32 GW** of net load in every year. This is
  a plausibility band on a quantity I do not choose; a value outside it does not kill the arm, it is
  **reported as a surprise** and its physical reading re-examined in the FINDING.

### 3.2 The screen's LP response (predicted before the screen is solved)

- **S-1.** The screen year's realized system-load-weighted negative-price-hour count rises from the
  control's essentially-zero to **between 120 and 900 hours**.
- **S-2.** The screen year's load-weighted mean model price falls by **1.5 to 6.0 \$/MWh**.
- **S-3.** The wind identity `model/delivered` falls from **1.10681** toward 1.0, landing between
  **1.02 and 1.09**, and **never below 1.00**.

### 3.3 AGAINST INTEREST — the predictions that hurt my preferred answer

- **X-1.** **I predict the instrument does NOT on its own create SPP's negative-price regime.**
  S-1's realized count will be **below 700**, i.e. under ~70 % of the ~1,000–1,170 measured, because
  SPP-51b routed two further limbs this lane does not touch: **R-3**, the zonal spread (measured
  |N−S| 12.13 / 17.23 / 15.18 \$/MWh against the model's 0.93 / 0.99 / 1.35, with both hubs negative
  together in only 68 / 64 / 68 % of the negative hours, so a *system* LW price needs both), and
  **R-2**, the thermal-commitment limb. **If the count lands above 700 I have under-predicted and I
  will say so in those words.**
- **X-2.** **I predict C3a still FAILS in the screen year** (|C3a| > 10 %), i.e. the instrument does
  not close the criterion it targets. **C3a is not a gate here** (§4); this prediction exists so that
  a C3a pass cannot later be presented as the lane's justification, and so that a C3a fail cannot be
  presented as a reason the mechanism is wrong.
- **X-3.** **I predict the instrument makes at least one reported band WORSE.** The most likely is
  C3c (hours > \$200): pushing 11 TWh of energy into the low hours cannot help the top tail and may
  further compress it. **A worsened C3c is not a reason to abandon a structurally-correct mechanism
  (rule 1 `[R-STRUCT]`) and I will not treat it as one** — it is reported at full magnitude.

---

## 4. THE SCREEN — STRUCTURAL, AND A STOP GATE ONLY

**C3a and C3b are what this mechanism targets, so they CANNOT be its gate.** They are reported at
full magnitude in every leg below and are explicitly marked **"not gated on"**. A screen **may kill
an arm; it may never promote one.**

**Screen-year selection rule, declared now so the result cannot choose it:** the screen year is the
year that **maximises the mechanism's own reallocated energy**,
`Σ_t | potential_new(t) − potential_old(t) |`, computed in phase 0; ties go to the **latest** year.
It is **NOT** the year whose C3a is worst (that would be residual-driven selection, which rule 1
forbids). The winning year and its three footprints are named in an **ADDENDUM to this PRECOMMIT,
pushed before the screen solve runs.**

| gate | requirement | STOP if |
|---|---|---|
| **G-1** negative-hour census | the realized system-LW hours < \$0 land within **[0.4×, 2.5×]** of the count predicted ex ante in the addendum from the phase-0 footprint | outside the band — the mechanism is not doing what its own arithmetic says |
| **G-2** footprint confinement | ≥ **90 %** of the absolute hourly change in model wind dispatch falls in hours the instrument allocated curtailment to (`curt(t) > 0`); nuclear + hydro + solar annual energy each move < **1 %** | the mechanism moves energy in hours it does not name |
| **G-3** wind identity | `model/delivered` moves from 1.10681 toward 1.0, lands within **±0.02** of the ex-ante prediction, and is **never < 1.00** | overshoot, undershoot, or a model that dispatches less wind than was delivered |
| **G-4** C1 non-regression | no C1 class row that PASSES in SPP-50's scoring of the screen year may FAIL in the arm; summed absolute class error must not rise > **20 %**. If the screen year is 2024, SPP-49's repaired `CC_REGULAR` and `CT_PEAKER` rows must each stay within **1.0 TWh** of their SPP-50 values | any of the above |
| **G-5** protective + supporting bands | C2, C4, C6, C8 must not flip PASS → FAIL | any flip |
| — | **C3a, C3b, C3c, C5a** | **REPORTED AT FULL MAGNITUDE, NOT GATED ON, in either direction** |

### 4.1 V-1 — the external validation leg (zero LP, uses a product refused as an input)

SPP's own RTBM binding-constraint log (`data/raw/spp-binding-constraints/RTBM-BC-YEARLY-2023.csv.zip`
and the 2025 monthlies) records, per interval, which flowgates bound. If this instrument's allocated
hours are really SPP's oversupply/congestion hours, they must carry **more** binding constraints than
the rest of the year. **Bar, declared now: the mean binding-constraint count per hour in allocated
hours ≥ 1.30 × the mean in unallocated hours**, on whichever year the log covers.
**V-1 is a validation, not a gate:** it can corroborate the instrument or embarrass it, and either
way it is reported. It does not kill the arm on its own and it never promotes it — rule 13 keeps this
series out of the model, and this leg does not smuggle it back in.

---

## 5. THE OUTCOME PARTITION — exhaustive, with an explicit instrument-failure branch

Exactly one of these is this lane's result and I commit to reporting whichever it is:

1. **INSTRUMENT FAILURE (zero LP).** F-1 fails — no λ root, the identity does not reproduce to 0.1 %,
   `potential < delivered` in some hour, or a required input is missing/misaligned. Report the
   failure, void the arm, spend **zero** LP.
2. **CONCENTRATION FAILURE — a clean NEGATIVE (zero LP).** λ solves and the identity holds, but F-2
   lands **< 20 %**: the oversupply key is no better than the availability key SPP-51b already priced
   and rejected. Result: **a measured, cited NEGATIVE** — no admissible instrument was found by this
   route — and **no screen is solved**. *(A clean negative is a success; it is not converted into a
   screen in the hope the LP rescues it.)*
3. **SCREEN STOP.** The screen runs and any of G-1…G-5 fails. The arm is **killed on the structural
   gate**, C3a/C3b reported at full magnitude whatever they did, and **the remaining two years are
   never spent** (rule 29).
4. **SCREEN CLEARS → FULL SPAN, SUFFICIENT.** G-1…G-5 all pass and the full-span bundle shows C3a in
   band in ≥ 2 of 3 years. Register (rule 15), report, put the promotion question to the owner in
   session (rule 31).
5. **SCREEN CLEARS → FULL SPAN, NECESSARY-NOT-SUFFICIENT** — *the branch X-1 predicts.* G-1…G-5 pass,
   the negative-price regime appears and is structurally sound, but C3a still fails in ≥ 2 years.
   Result: registered and reported as **one limb of the object SPP-51b named**, with R-2 and R-3
   carrying the remainder; promotion question still put to the owner; **not** dressed up as a fix.

**Two commitments about how these are read.** *"C3a improved" is not, and will not be made, a reason
to promote a mechanism through this gate.* And *"C3a did not improve" is not, and will not be made, a
reason to kill a structurally-correct one* — rule 1 `[R-STRUCT]` cuts both ways and this lane is
bound by both halves.

**A threshold that misses is reported in the words it was written in.** If F-2 lands at 44 %, the
declared bar was "≥ 45 %" and it **missed** — it will be recorded as a miss, not re-described as
"≈ 45 %". If S-1 lands at 705 hours, X-1 said "below 700" and I **under-predicted** — in those words.

---

## 6. Rule postures, declared

- **Rule 29 `[R-SCREEN]` — phase 0 first.** Every leg in §3.1 and V-1 is zero-LP and is computed
  before any solve. The screen is **one year**, named by footprint in the addendum. The full span is
  reached only through partition branch 4/5 and is then **one `--year 2023 2024 2025` invocation and
  one bundle** (rule 16 `[R-ALLYEARS]`).
- **Rule 29(b) — G-DRIFT, run at code level BEFORE any arm is solved; NO control solve is planned.**
  The control is **SPP-50 `2026-09-08-spp-50-rebaseline`**, the registered run that sits on the
  current input surface. Keeper-3 is **not** the control for anything on the input surface — SPP-48's
  wind repair and SPP-49's two seams are LIVE input-side hunks against it, exactly as this lane's
  charter says, and no differencing against keeper-3's inputs is claimed anywhere.
  `git diff 08e486f2..HEAD -- src/market_sim scripts/run_calibration*.py scripts/lib
  data/raw/_validation-source data/raw/reference` (08e486f2 = the commit registering SPP-50) is
  **17 files / 9 commits, and every hunk classifies INERT for an SPP backcast**:
  | commit(s) | change | why INERT for SPP backcast |
  |---|---|---|
  | `01c3baeb` | capx D88 `unit_id` uniqueness guard in `fleet/arrays.py` | a `ValueError` guard plus one variable reuse; the commit's own phase 0 proves it silent on all seven backcast keepers across 23 keeper-years, and duplicates are an **evolved-fleet** event a `mode="backcast"` run never reaches |
  | `5df6192f`, `c0efa7ad` | `hydro_budget_period_by_instrument` (`data/hydro.py`, `model/lp/rows.py`) | new `ScenarioConfig` bool, **dataclass default `False`**, absent from SPP's recipe; `rows.py`'s new branch is entered only when `hydro_period_hours is not None`, otherwise the pre-existing monthly path runs unchanged |
  | `d6cbc03a` | `netload_drag_merit_allocation` (`fleet/floors.py`) | new `ScenarioConfig` bool, **default `False`**, absent from SPP's recipe; an ERCOT drag-mandate lane (ercot-259) |
  | `f0d6ba2d`, `e1c7bc08`, `32f0110a` | capx D87 CCS clean-tier seam + retrofit ledger + cache epoch (`capacity_evolution/*`, `results/cache.py`) | **capacity-evolution path, which a `mode="backcast"` run never enters**; the cache-epoch registration names twelve target-row bundles, none of them SPP |
  | `b91ec584`, `1165519e` | merge commits | no content of their own |
  **All hunks INERT ⇒ form 4 is valid and SPP-50's committed numbers are the control.** What SPP-50
  *cannot* supply is hourly resolution — its bundle did not survive its container and it has **no
  `hourly/` sidecars**. Two consequences, stated rather than papered over: (a) every **band-level**
  control number (C1 class rows, C2/C3a/C3b/C3c/C4/C5a/C6/C8, the wind identity, LP re-curtailment)
  comes from SPP-50's committed sidecar and is a true form-4 differencing; (b) the control's
  **hourly negative-price census** is not directly available, so G-1's control side is taken as
  **structurally zero** — SPP-50 re-curtails 0.00058 / 0.00172 / 0.00030 % of its wind, so wind is
  interior in essentially no hour, and a negative LMP in this LP requires an interior wind column
  (SPP-51b §4's falsifier). I will attempt to reconstruct the control's hourly price exactly from the
  committed payload's `lmpDeltaHr` series; **if that reconstruction does not validate, the control
  side of G-1 stays the structural bound and the FINDING says so** — I will not claim a differencing
  I cannot do.
- **Rule 31 `[R-RETAIN]`.** `results/calibration/_spp51c_*` is added to `.gitignore` **at the moment
  the first bundle is written**, and **nothing is ever `rm`'d**. The promotion question is asked
  **explicitly in this session's final report**, with the LP reproduction cost stated, while the
  bundles are still alive on this ephemeral container.
- **Rule 15 `[R-DASHBOARD]`.** Any full-span bundle is registered in this session, keeper or rejected.
  A **screen** bundle is never registered (rule 29(2)) and is kept out of `main` by `.gitignore`.
- **Rule 28 `[R-MECH-MATRIX]`.** The new field gets its **base row in
  `docs/codebase-site/data/mechanism-matrix.js` plus a cell line in EVERY ISO shard, in this PR**
  (duty (c), CI-enforced). SPP's own shard cell is stamped with this lane's verdict in this session
  (duty (b)). No other ISO's shard verdict is touched: every other ISO enters as `U` (duty (d)).
  Cells already adjudicated `R`/`I`/`G` for SPP — `offer_curve_by_group` (R),
  `negative_renewable_offers` (I), `wind_ptc_vintage_offers` (I) — are **not re-tested**.
- **Rule 27 `[R-PUSH]`.** `renewables.py` and `scenarios.py` are both ≥ 300 lines; every edit is a
  local `Edit`, never a regenerated full-file push, and every push touching them is blob-verified
  before the next commit.
- **Out of scope, not absorbed:** R-2 (thermal commitment), R-3 (zonal spread), C3c / SPP-55, the
  C1-2024 `ST_GAS` Harrington fuel-vintage row (SPP-46 R-4). This lane opens **no owner card**.
