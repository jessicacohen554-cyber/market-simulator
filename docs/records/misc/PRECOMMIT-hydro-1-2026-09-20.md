# PRECOMMIT — hydro-1: hydro dispatch physics, PJM + NYISO (2026-09-20)

**Lane:** hydro-1 · **ISOs:** PJM, NYISO · **Mode:** backcast · **LP spent before this doc:** zero.

Every number below was measured with **no solve**, from the two designated keepers' own
committed `hourly/` sidecars, each ISO's own published hourly generation, and the committed
ORNL-EHA / HILARRI / USACE-NID sources. The arms are launched **after** this doc is pushed and
its SHA pinned (rule 32(c)(1)).

---

## 1. The defect, as reported and as measured

The report: *"hydro is allowed to be too optimised and dispatchable … it can't retain all the
water over a full month and dispatch at peaks … it's not a peaker but it's being given the
freedom to dispatch like one, plus perfect foresight. In PJM there are 0 hydro hours in my model
when that never actually happens. In NY it seems to have too much availability to meet summer
peaks."*

Both halves are real, they are **different defects**, and they need **different mechanisms**.

### 1.1 The structural cause

Conventional hydro enters the LP as a generator at `mc = VOM["hydro"]` with **one energy row per
(plant, month)**. That row's dual is the plant's water value — **a single number, identical in
hour 1 and hour 730**. So the plant's effective offer is a flat line across its whole `0 → pmax`
range, it is a pure price-taker block, and any within-month price difference is arbitrage profit
with **no offsetting cost**. Nothing in the formulation bounds *when* inside the month the energy
is taken, and nothing bounds it from below.

Two consequences follow directly, and both are measured below: the fleet goes **bang-bang**
(pinned at a ceiling or at zero, with nothing in between), and it **banks a month of water for
the peak**.

### 1.2 PJM — measured (`scripts/probes/_hydro_phase0_pjm_nyiso.py`, `_hydro_phase0_concentration.py`)

Keeper `2026-09-20-pjm-h13-meritalloc-span`, P1, its own committed `class_hourly_<year>.parquet`.
**Every hydro physics gate is off** in that keeper (`hydro_dispatch_envelope`,
`hydro_min_flow_floor`, `hydro_ror_split`, `hydro_budget_period_by_instrument` all `False`).

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| model hours at 0 MW (<1 % of fleet scale) | **2,210** | **2,946** | **3,067** |
| model overnight (HE 03-06) hours at exactly 0, of 1,460 | 363 | 516 | 514 |
| model overnight p05 (MW) | 0.0 | 0.0 | 0.0 |
| share of each month's water in the month's **top-decile load hours** | 0.280 | 0.297 | 0.313 |
| share on the month's **single peak day** (flat fleet = 0.033) | 0.063 | 0.070 | **0.078** |
| hourly CV | 1.045 | 1.119 | 1.123 |

**The "0 hydro hours" report is confirmed and it is the larger defect.** A quarter to a third of
the year at zero, and 2.4× a flat fleet's energy on the month's peak day.

### 1.3 NYISO — measured, same probes

Keeper `2026-09-20-nyiso247-fuel-invariance-disarm`, which **already arms** the envelope, the
min-flow floor and the instrument budget period. Reference: NYISO's own published real-time
fuel-mix `Hydro`.

| | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| model − actual, hourly **p05** (MW) | −215 | −70 | −158 | −107 |
| model − actual, hourly **p95** (MW) | +44 | +104 | +144 | +118 |
| model − actual, **summer peak window** mean (MW) | +86 | +37 | +110 | +52 |
| within-month **daily amplitude ratio** (model ÷ actual) | 1.204 | 1.237 | 1.295 | **1.338** |
| share of **all hours** within 1 % of the armed p95 ceiling | 0.168 | 0.253 | **0.309** | — |
| hourly CV, model vs actual | .249/.211 | .210/.184 | .233/.199 | .299/.257 |

NYISO is an order of magnitude better calibrated than PJM — three mechanisms are already
carrying it — and the residual has a clean signature: **the range is too wide at both ends**
(trough too low, peak too high) and the model **rides the p95 deliverability ceiling in 17-31 %
of all hours, against the 5 % a p95 ceiling is reached by construction.** That is bang-bang: the
fleet sits at the cap or at the floor because between them the LP is indifferent.

The reported "too much availability to meet summer peaks" is real but **small in level** — +37 to
+110 MW on a ~4 GW fleet. The larger, cleaner defect is the **within-month banking**, 1.20-1.34×
the actual's daily amplitude, worst in 2025.

### 1.4 One correction to the report, made rather than smoothed over

PJM's modelled hydro **energy is correct**: 8.90 / 8.86 / 8.46 TWh against EIA-923 `HY` of
8.976 / 8.864 TWh — the level matches the source exactly. The 15.5 TWh that PJM's own Data Miner
reports as `Hydro` **folds pumped storage** (PJM PS = 5,046 MW over five plants; Data Miner's
separate `Storage` category is batteries, 20 MW max), and this is already a known, fixed seam
(`hydro_level_923_hy`, cell **K**, `FINDING-pjm-h1-hydro-accounting-seam-2026-09-12.md`). **There
is no missing PJM hydro energy. The defect is entirely in the timing.**

---

## 2. What is launched, and why these and not others

### 2.1 PJM — `hydro_ror_split` (cell **U**, first test)

**The driver, from the external label alone (rule 17a).** ORNL EHA labels **47 of PJM's 82**
conventional-hydro plants `Run-of-river` or `Canal/Conduit`. After the HILARRI completion the
flat class is **57 plants / 1,555.8 MW / 4.872 TWh = 55.0 % of PJM's hydro energy**. A
run-of-river plant's output *is* its inflow — it has no reservoir in which to hold it — so
2,210-3,067 hours at 0 MW is a physics violation established with no residual and no reference
series.

**Window (17b):** all 24 hours; inflow is around the clock and the flat level is month-constant,
so no diurnal shape is pinned. **Forward story (17c):** the classification is a static plant
attribute; the level is the plant's own monthly budget, so it scales with the water year.
**DOF: zero** — a categorical external classifier and the plant's own budget.

**What cannot be checked for PJM, stated at the gate.** nyiso-111's falsification test — *does
the measured fleet swing more than the classifier's shapeable set allows?* — **is unavailable
here**, because PJM publishes no clean hourly conventional-hydro series (both `gen_by_fuel
Hydro` and EIA-930 `NG: WAT` fold PS). The corroboration that *is* admissible is one-sided and
is used only that way: folding can only **add** generation, so the folded series' overnight floor
is an **upper bound** on the conventional fleet — and it never drops below **95-148 MW** in any
of 1,460 overnight hours a year, against a model at exactly zero in a third of them.

**Not armed for PJM, and why:** `hydro_dispatch_envelope` and `hydro_min_flow_floor` both read
`NG: WAT` and would apply a pumped-storage-contaminated level to a conventional-only unit
population (rule 14). The *level pin* already refuses for this BA
(`EIA930_PS_FOLDED_INTO_WAT`); **these two readers do not, and that is a live code gap this lane
records rather than works around.** Measured cost of arming them anyway: the p95 envelope would
sit at roughly twice the conventional fleet (model bind share 0.086-0.109, mean bucket percentile
rank 0.22 — i.e. near-inert but wrong), and the floor would be an over-statement.

### 2.2 NYISO — `hydro_ror_split` (cell **G → U**, re-opened narrowly)

**nyiso-111's kill stands and is not being re-litigated.** Under the committed classification
rule NYISO's shapeable set is 1,261.6 MW while its own measured fleet swings 1,195 / 1,292 /
1,593 MW on the mean diurnal profile and 1,496 / 1,495 / 1,929 MW on the median day. A fleet
cannot swing more than its shapeable capacity. Correct kill, no solve spent.

**The new evidence (rule 28(a)), computed ex ante.** That falsifies the rule's **hybrid
resolution**, not the mechanism. The committed rule sent every hybrid EHA label
(`Run-of-river/Peaking`, `Run-of-river/Upstream Peaking`) to not-shapeable on the argument that
"EHA lists the plant's own hydraulic mode first". Those 23 plants are **2,639.8 MW** of NYISO,
Robert Moses Niagara among them — exactly the plants the swing says *do* shape.

**The repair, applied where it broke:** a label **containing "Peaking" is shapeable**;
`Run-of-river`, `Canal/Conduit` and `Reregulating` are not. `Reregulating` is deliberately **not**
swept up — a re-regulating powerhouse exists to *absorb* an upstream peaker's discharge, which is
the opposite of shaping.

| | committed rule | repaired rule |
|---|---:|---:|
| NYISO shapeable | 1,261.6 MW | **4,098.4 MW** |
| vs max measured swing 1,929 MW | **falsified** | **clears, 2.1× headroom** |
| NYISO flat class | 73.1 % of MW | 94 plants / 582.6 MW / 2.022 TWh (7.3 % of energy) |

**Rule 25 intact:** no fitted number crosses a boundary — a categorical labelling rule is
repaired against one ISO's measured falsification. **Verified byte-identical for CAISO from the
source, not asserted:** the EHA sheet carries **zero** hybrid-labelled CISO plants (196 rows, 0
hybrid, 0.0 MW), and a differential re-run of both rules moves **0 of 195** CAISO plants (PJM
moves 1, NYISO 20). CAISO's keeper does not arm the field in any case.

### 2.3 NYISO — `hydro_pondage_bound` (**new field**, the storage half)

This is the direct answer to *"it can't retain all the water over a full month"*, and to the
offer-curve intuition — see §3.

**The row**, one per (plant, hour), in MWh:

```
P_g(t) + Spill_g(t) + V_g(t) − V_g(t−1) = inflow_g(t),      0 ≤ V_g ≤ B_g
```

`inflow_g(t) = budget[g, m] / hours[m]` — **the plant's own monthly budget, an array the LP
already carries, so no new energy datum enters.** `η ≡ 1`, so the balance is in energy and no
water unit or turbine efficiency is assumed. `B_g` is the plant's **measured usable forebay
storage**.

**No new LP code was written.** This is the existing `model/lp/hydro_cascade.py` row builder with
**zero links** — the pondage bound *is* the cascade without upstream terms. The resolver
`pipeline/kwargs.py::resolve_hydro_cascade` now serves both members and **raises if both are
armed** (rule 19, enforced rather than documented).

**The invariant, inherited and preserved:** spill is unbounded above, so **every row is feasible
at zero generation** and the family can never move a monthly total. It follows that **this
mechanism imposes no floor** — the trough is §2.1/§2.2's half. The two are complementary, never
stacked: a RoR-flat plant carries no pondage row.

**`B` is measured, with zero free parameters** (`scripts/data/build_hydro_pondage.py`): USACE NID
`Max Storage` summed over the plant's **distinct `NID ID` impoundments** × NID `Hydraulic
Height`, else `NID Height` as the labelled proxy (nyiso-219's committed rule, frozen under rule
23), at turbine efficiency **1.0** — a deliberately generous upper bound, so the constraint can
only be too **loose**, never too tight. Distinctness is load-bearing: NID files one row per
*structure* and repeats an impoundment's volume on every dike (St. Lawrence carries eight rows,
all 803,000 acre-ft).

**Validation — the derive independently reproduces nyiso-219 to three figures:**

| | nyiso-219 (committed) | this derive |
|---|---:|---:|
| share of fleet MW under 24 h | 72.01 % | **72.0 %** |
| under a week | 97.54 % | **97.5 %** |
| under a month (the LP's period today) | 98.31 % | **98.3 %** |
| St. Lawrence pondage | 73.07 h | **73.04 h** |

**One correction to nyiso-219, and it is why this arm can exist.** 219 measured Robert Moses
Niagara at **0.244 h** from NID `NY16253`, the 71-acre / 5,350 acre-ft powerhouse forebay —
the only dam HILARRI links to plant 2693. But a plant holding fifteen minutes **cannot produce
the 1,195-1,593 MW mean diurnal swing nyiso-111 measured on a fleet it dominates (51.9 % of MW).
Those two committed findings contradict each other**, and the resolution is physical: the Niagara
Project's shaping store is the **Lewiston Reservoir** (NID `NY00689`, NYPA, **76,000 acre-ft**,
hydraulic height 119 ft, completed 1963 with the powerhouse), which NYPA fills overnight from
treaty-allowed diversion and draws back down through the 2,429 MW Robert Moses conventional
units. The 240 MW Lewiston pump-turbines (EIA 2692, modelled separately as storage) cannot
themselves carry the swing.

Linked through `constants.HYDRO_PONDAGE_EXTRA_NID_BY_PLANT` — a **linkage**, not a value, with
its citation — Niagara holds **4.06 h** against the LP's 730-hour budget period. **nyiso-219's
conclusion is untouched** (still two orders of magnitude short of a month); only its Niagara
figure moves, and it moves in the direction that reconciles it with nyiso-111.

**Coverage.** NYISO 152 plants / 4,611 MW with identified storage, of which **129 carry a binding
row**; the other 23 hold their largest month whole, so their row is **mathematically redundant**
against the budget row and is not built (a proof on the artifact, never a selection). 66.2 % of
fleet MW holds under 6 h.

### 2.4 Not launched, and why

* **`hydro_budget_period_by_instrument`** (NYISO cell **R**, nyiso-238) is **superseded, not
  retried.** A partitioned period still permits a full period's banking and a **2× concentration
  at the period seam**; a forebay bound is a *sliding* constraint at the plant's own physical
  tolerance. Never armed together.
* **PJM `hydro_pondage_bound`.** The artifact is built (78 plants / 3,320 MW; 54 binding rows;
  only 15.6 % of MW under 24 h, 53.4 % under a week — PJM's hydro sits on far larger
  impoundments). It is **the named successor** for PJM, not in this batch: PJM's dominant defect
  is the trough, and confounding two arms in one ISO would make neither readable.
* **Tuning `HYDRO_ENVELOPE_PERCENTILE` off 95.** Refused. That is a fitted parameter
  (rules 5/21), whatever the bind share says.

---

## 3. The offer-curve question, answered

The intuition — *"perhaps it needs an offer curve that's higher above 70 %, and maybe some amount
of must-run"* — **diagnoses both defects correctly**, and it is two asks, which is right.

**The must-run half is §2.1/§2.2**: `hydro_ror_split` sets `min_gen = cap = the plant's own
inflow` for plants that physically cannot do anything else. That is the must-run, and it is
measured rather than chosen.

**The rising-offer half should not be imposed as a curve.** A hydro offer curve with a
hand-set breakpoint and adder is a fitted mechanism (rules 5/13/21) — and the rule-1 carve-out
for `offer_curve_by_group` band multipliers does **not** reach hydro, which is not one of those
registered groups. But the curve the intuition is reaching for is real, and it has a
zero-parameter source: **give the reservoir its storage back and the LP produces the curve
itself.** With `0 ≤ V ≤ B`, the dual on the forebay bound is non-zero exactly when the plant is
drawing down against its limit, so its effective marginal water value **rises with cumulative
draw** instead of sitting at one flat monthly number. That is §2.3.

So: **the offer curve is an output of the physics, not an input to it.** The same change makes
the sentence *"it can't retain all the water over a full month"* literally true in the model —
a plant that tries to bank a month overflows its forebay — which the new test
`test_the_forebay_bounds_how_much_energy_can_be_shifted` asserts on the assembled matrix.

**Honest limits of this framing.** (a) The bound uses NID **gross impoundment** volume, not the
licensed operating band, so it is **generous** — nyiso-219 makes the same point about
St. Lawrence. Any binding we observe is therefore a **lower bound** on the true constraint, and
the mechanism will under-constrain rather than over-constrain. (b) It does not represent head
loss, licence ramp-rate limits, or the reserve-headroom opportunity cost — three other real
sources of a rising hydro offer. (c) Perfect foresight remains, and is not addressed: a bounded
forebay shortens the horizon over which foresight is worth anything, but does not remove it.

---

## 4. Gates, declared before the solves

Decided on structure (rule 1), not on the residual. A gate that fails does **not** on its own
kill an arm; a gate that passes does not on its own promote one.

**G1 — MECHANISM LIVENESS.** Each arm's mechanism must bind. PJM RoR: ≥ 1,000 MW-average of
`MECH_HYDRO_ROR_FLAT` stamped, and model zero-hours **< 500/yr** (from 2,210-3,067). NYISO RoR:
≥ 400 MW of flat class stamped. NYISO pondage: the `V` column at its bound in ≥ 1 % of
plant-hours. *An INERT arm is reported as inert and is not a verdict on the mechanism.*

**G2 — THE INVARIANT HOLDS.** Annual hydro energy per ISO-year moves by **< 0.1 %** vs the
keeper. The pondage family cannot move a monthly total by construction; this is the check that
it didn't. *A breach is a defect in my code, not a finding.*

**G3 — THE TARGETED STATISTIC MOVES THE RIGHT WAY.** PJM: peak-day share falls toward 0.033 and
zero-hours fall. NYISO pondage: within-month daily amplitude ratio falls toward 1.0 from
1.20-1.34. NYISO RoR: p05 gap closes from −70..−215 MW.

**G4 — NO SILENT BREAKAGE ELSEWHERE.** C1 zonal bands, C2 and C3a/b re-scored on every year.

**Rule 1 and rule 14 restated before any number arrives:** hydro is ~20 % of NYISO generation, so
re-timing it **will** move C3a/C3b/C3c. **If the faithful representation makes the price fit
worse, it stays**, and the worse fit becomes a root-cause question — the 2026-07-25 precedent,
and nyiso-219 §6's own standing instruction.

---

## 5. Control, drift and shard plan

**Control (rule 29(b) form 4):** the designated keepers' **committed bundles** —
`results/calibration/pjm_h13_meritalloc_span` and `results/calibration/nyiso247_fuelinv_span`.
No control solve is spent.

**G-DRIFT.** The solve-path changes in this commit are: a new default-off `ScenarioConfig` field
(`hydro_pondage_bound`, dropped from the cache key at its default — **verified**: default and
explicit `False` share key `9ca2c6052b4850ea`, armed hashes `c7887677b4251fe3`; 18/18 committed
run configs rebuild with it `False`); a resolver that returns `UNSET` unless a gate is armed; four
new tri-state CLI flags defaulting to `None`; and a **classification-rule repair whose per-ISO
effect is measured, not assumed** (CAISO 0 plants, PJM 1, NYISO 20). **INERT for every other ISO
and for every keeper that does not arm a hydro gate.**

Because no CLI surface existed for `hydro_dispatch_envelope` / `hydro_min_flow_floor` /
`hydro_ror_split` — a **rule-24 `[R-REGISTRY]` gap this lane closes** — each shard passes its
ISO's keeper-recorded hydro posture **explicitly**, so the arm differs from the control in
exactly one field.

**Shards — one per (arm, year), rule 36 `[R-YEAR-ISOLATION]`; every shard pushes its full bundle,
rule 34(a).**

| arm | ISO | years | shards |
|---|---|---|---:|
| A — `hydro_ror_split` | PJM | 2023, 2024, 2025 | 3 |
| B — `hydro_ror_split` | NYISO | 2022, 2023, 2024, 2025 | 4 |
| C — `hydro_pondage_bound` | NYISO | 2022, 2023, 2024, 2025 | 4 |

Full spans, because rule 34(c) requires a promotable result to carry every year the ISO's keeper
carries. **No year is deliberately omitted.**

**Worst years, for the record** (the report asked): PJM **2024** (2,946 zero-hours on a complete
72-plant EIA-923 census; 2025 is worse at 3,067 but runs on a 10-plant early-release backfill, so
it is confounded). NYISO **2025** (amplitude ratio 1.338, within-month daily r 0.247 — both worst
of the span).

**Retrievability (rule 34(e)):** every shard commits its own bundle including
`dispatch/<year>_P1.parquet` to its own branch; the parent fetches, composes and lands the
keeper bundle on `main` before this lane's PR merges (rule 33(f)(4)(ii)).

---

## 6. Pre-existing failures this lane did not cause and is not fixing

* `tests/regression/test_run_year_kwargs_recipe.py::TestNoNewByNameProbes` — fails at HEAD on
  `caiso291_bridge_candidacy_census.py`, committed by the CAISO lane at `e071f0e9`.
* `tests/unit/data/test_caiso_st_gas_peak_measured.py` — registry/artifact drift (1.154 vs 1.166),
  CAISO lane.
* `scripts/check_cache_key_registration.py` already failed at HEAD on two undeclared
  solve-surface names (`PPA_COST_RECOVERY_YR`, `REGIONAL_RENEWABLE_CF`). The remedy is
  all-or-nothing and **moves no key**, so declaring this lane's name cleared all three. Guard now
  green.
