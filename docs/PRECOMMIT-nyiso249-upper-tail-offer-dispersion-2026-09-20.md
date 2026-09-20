# PRECOMMIT nyiso-249 — the UPPER-TAIL conditional offer dispersion: the discriminator first, and every bar fixed before the numbers

**Session** nyiso-249 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **zero LP in this container**).
**Date** 2026-09-20. **Base** `origin/main` at `ef6a498a` (nyiso-248's branch merged as PR #6443).
**Keeper** `2026-09-20-nyiso247-fuel-invariance-disarm`, bundle `results/calibration/nyiso247_fuelinv_span`,
years {2022, 2023, 2024, 2025}, basis sha `42d750537532c95d335286b63bca881e8a01c76b`.
**NYISO IS CALIBRATED** and nothing here proposes to revert any part of that keeper (rule 1 `[R-STRUCT]`).

---

## 0. THE OBJECT — ONE SENTENCE, AND IT IS THE *CORRECTED* ONE

In tight hours a minority of NYISO capacity raises the **implied heat rate of its
bottom-of-curve offer** far above its ordinary-hour level, and the model — after nyiso-247's
disarm — moves it **not at all**. Measured on the P-27 book under nyiso-248's corrected
daily-in-both-roles coordinate: **p50 −0.123, p75 +4.685, p90 +21.974 MMBtu/MWh.**

**The median rise is gone and is not this lane's object.** `+2.035` at p50 and the `25.845`
headline are **arm-A artifacts** of a monthly denominator against a daily market, and no form
here is anchored on either (handoff brief; nyiso-248 §A2).

**Why it matters for the rubric.** C3c (price tail / scarcity, RT hourly) is NYISO's **lone**
failing criterion in every year — model **16 / 0 / 0 / 3** hours > $300 against **101 / 10 / 13 / 42**
actual. The whole reserve / RCPF / ORDC successor is **foreclosed** (nyiso-242 §4: NYISO's own
posted DA AS prices cap the stack at $136/MWh, short in every window of every year by $49–636),
so the **offer side is the only live route to that tail**.

---

## 1. G-DRIFT — THE CONTROL IS THE KEEPER'S COMMITTED BUNDLE (rule 29 `[R-SCREEN]` (b), form 4)

`git diff 42d750537532c95d335286b63bca881e8a01c76b origin/main -- src/market_sim
scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference` → **6 files, 588 insertions, 34 deletions**, from
three commits: `1fd5d769` (caiso-293), `f7d6112c` (pjm-h14), `cc66a606` (SPP-67).

| file | hunk | classification | reason |
|---|---|---|---|
| `config/scenarios.py` | 3 new fields: `coal_mustrun_requires_measured_row`, `chp_steam_duty_window`, `vre_reference_rate_year_own` | **INERT** | all `bool = False`; **all three absent from the keeper's `run_config`** |
| `data/fleet/__init__.py` | `chp_grid_pmin_on_frac: float = 1.0` | **INERT** | default 1.0 selects the pre-change branch in `arrays.py` |
| `data/fleet/arrays.py` | CHP min-gen duty window | **INERT** | `_chp_any_windowed` is False unless some gen has `frac < 1.0`; nothing sets that without `chp_steam_duty_window`, so `_chp_rank_key is None` and the loop executes the **identical** pre-change statement |
| `data/fleet/assembly.py` | `chp_duty_on_frac` | **INERT** | initialised 1.0; only moved inside `if getattr(config, "chp_steam_duty_window", False)` |
| `data/fleet/campd_bins.py` | docstring correction + new `thermal_tranche_chp_steam_duty` | **INERT** | new function's only caller is the gated `assembly.py` branch |
| `data/renewables.py` | SPP wind curtailment refactor + `_spp_wind_year_own_curtailment_rate` | **INERT** | both readers are registered under the key `("SPP", "wind")` — unreachable for NYISO (another ISO's branch) |

**ALL HUNKS INERT ⇒ form 4 is valid and the keeper's committed bundle IS the control.** No control
solve is earned. **G-DRIFT-M** (below) verifies the one hunk that touches a path NYISO actually
executes, mechanically rather than by reading.

---

## 2. G-1 / G-2 — THE DISCRIMINATOR, RUN BEFORE ANY FORM IS DESIGNED

### 2.1 Why there is a discriminator at all

`m = bid bottom ($/MWh) / G(hour) ($/MMBtu)`, and **`G` is a choice**. nyiso-248 moved it from a
monthly step to the daily **HUB**. But a NYISO generator does not buy at the hub — it pays a
**delivered** price, hub commodity plus that zone's LDC delivery charge. If a unit bids
`HR × P_delivered` while the estimator divides by `P_hub`, then `m = HR × (P_delivered / P_hub)`
and **any widening of the delivered-over-hub basis in tight hours manufactures a positive
tight-minus-ordinary delta from a unit whose true heat rate never moved.** That is the *third*
instance of the identical artifact shape nyiso-248 already found twice.

**It is not hypothetical, because the model already prices part of that basis.** The keeper arms
`nyiso_downstate_ct_gas_daily`, which **SETS** every NYC / Long Island `CT_PEAKER` to the measured
per-zone delivered index (Transco Z6 NY daily spot + the measured LDC non-firm transport rate).
If the measured upper tail is that same delivered basis, it is a mechanism this ISO **already
has**, and an offer-dispersion form on top of it is the rule 19 `[R-ONE-MECH]` stack that rule
forbids. **This must be settled before a form exists, not after.**

### 2.2 The ladder — conditioner held FIXED at daily, denominator swapped

`scripts/probes/nyiso249_denominator_ladder.py`, running the family's **own** estimator
(`year_unit_rows`, `per_unit_delta`, `weighted_quantiles`, the frozen 199-point `QUANTILE_GRID`,
the registered `NETLOAD_PCTS` ladder). Re-implementing the population rules would itself be a
tuning channel — the derive's docstring forbids it.

| arm | conditioner | denominator |
|---|---|---|
| **A** | monthly step | monthly step | *(= the committed artifact; **REPRODUCTION CHECK ONLY**)* |
| **D** | daily hub | daily hub | *(= nyiso-248's corrected arm D; the brief's baseline)* |
| **E** | daily hub | the model's own cap-weighted **delivered** gas for CC_REGULAR + ST_GAS, read out of the keeper's assembled `fuel_prices` |
| **F** | daily hub | the measured **NYC LDC delivered index** — the identical series `apply_nyiso_downstate_ct_gas_daily` already SETS on downstate CT_PEAKER |

CT_PEAKER is deliberately **excluded** from arm E's weighting: it is the one class that already
carries the delivered index, so including it would blend the armed and unarmed halves.

### 2.3 THE READING, FIXED HERE, BEFORE ANY ARM IS RUN

**"Collapses" ≡ pooled p90 falling below `+8.0` MMBtu/MWh** — a round third of the corrected
+21.974, chosen ex ante and **never swept**.

| outcome | verdict | what this lane then does |
|---|---|---|
| tail **survives** under **both** E and F | not a fuel artifact — the object is **conduct** | design the form (§3) and solve |
| tail **collapses** under F but **survives** under E | the object is the **missing LDC delivered basis on the price-setting classes** | it is a rule 14 `[R-ACCURATE]` measured-**INPUT** question, **not** an offer-dispersion mechanism — **route it, do not build a form** |
| tail **collapses** under **E** | **already armed** | **report and stop** (rule 19 `[R-ONE-MECH]`) — a nyiso-248-shaped outcome |

**HARD GATE: arm A must reproduce the committed `nyiso_offer_level_dispersion.json` to
`max abs err < 1e-4`, or nothing else here may be read.**

### 2.4 G-1, the re-derivation the handoff's duty (a) requires

`derive_nyiso_offer_level_dispersion` reaches for `gas_series_by_year()` in **two** places, which
is the defect. The repair lands properly: **the gas array becomes a parameter** in both roles
(`state_windows(gas=…)`, `build(gas=…)`), default preserved so every existing caller and the
committed artifact are byte-identical, and the corrected array is passed explicitly. The committed
artifact is **arm A and is not consumed as-is** by anything in this lane.

### 2.5 G-DRIFT-M — mechanical inertness of the one live-path hunk *(zero LP)*

At `origin/main`, on the keeper's own resolved config, assert for a NYISO year:
`chp_steam_duty_window is False`, `coal_mustrun_requires_measured_row is False`,
`vre_reference_rate_year_own is False`, and **every** assembled generator carries
`chp_grid_pmin_on_frac == 1.0`. All four must hold, or form 4 is void and a control solve is
earned. Reading a branch is weaker than executing it; this executes it.

---

## 3. THE FORM — CONTINGENT ON §2.3, SPECIFIED HERE SO THE RESULT CANNOT CHOOSE IT

**Armed only if §2.3 returns "conduct".** Registered as `nyiso_offer_tail_dispersion`
(ScenarioConfig bool, default **False**; NYISO-only, `iso != "NYISO"` returns immediately).

### 3.1 What it does

In **tight** hours only — `gas_bin ≥ 2 AND load_bin ≥ 2` on the **daily** delivered-gas coordinate
and the same `NETLOAD_PCTS = (0.80, 0.90, 0.97)` within-year ladder the book is measured on — the
**top-ranked fraction of merchant gas capacity** has its offer lifted by

```
Δmc[g, h]  =  τ_g  ×  G[g, h]        ($/MWh, τ in MMBtu/MWh)
```

where `G[g, h]` is **that unit's own delivered fuel price** (so the lift is fuel-indexed and
regenerates forward, rule 13 `[R-MEASURED]`) and `τ_g` is drawn from the **measured book's own
upper-tail quantiles** by capacity rank, not fitted.

### 3.2 Identification — the rule is fixed here, the numbers are read off the arm §2.3 selects

`τ` is the measured cross-unit delta vector at the ranks the book reports, assigned by capacity
rank within the eligible class set, **truncated below at p75**: units below the p75 rank get
`τ = 0` (the book says the median unit does not move), units between p75 and p90 get the p75
value, units above p90 get the p90 value. **Two values, both read directly off the selected arm's
pooled vector at p75 and p90. Zero fitted parameters; no interpolation; no sweep.**

### 3.3 THE THREE ALTERNATIVES REFUSED ON STRUCTURE, BEFORE ANY NUMBER

1. **A uniform tight-hour adder** (`Δmc = c` for every eligible unit). **REFUSED**: the book's
   own finding is that the median unit does **not** move (p50 −0.123). A uniform lift asserts the
   opposite of the measurement and would be a pure level intervention — the "fitted adder" rules
   1 / 13 forbid.
2. **Scaling the existing `peak` band multiplier** (CT_PEAKER 4.0, ST_GAS 4.2). **REFUSED**: the
   band multipliers are time-**invariant** by construction, so they cannot express a *conditional*
   response; raising them would move the offer in all 8760 hours to buy a move in ~20–140. That is
   the annual-level intervention duty (d) exists to prevent, and it would also re-open the rule-1
   authorized-tuning channel for an object that is not a level object.
3. **A continuous `τ(rank)` interpolated across the whole 199-point vector.** **REFUSED**: below
   p75 the measured vector is negative-to-zero, so a continuous form would *lower* offers on the
   majority of capacity in tight hours — a second, opposite-signed mechanism smuggled in under one
   gate, and one with no measured warrant (the disarm already put the model at zero there).

### 3.4 WHAT IT DOES NOT CLAIM

It does not close C3c. It does not claim the tail's *cause* — the book is masked (no class, no
fuel, no unit; nyiso-244 §4 built and **refuted** the class bridge), so `τ` is a measured
cross-unit *magnitude*, never an attribution to a named behaviour.

---

## 4. DUTY (d) — THE LEVEL-vs-SHAPE GUARD, REPORTED BEFORE THE SOLVE

**Held fixed by construction, and the construction is the argument:** the lift is confined to the
tight window, which is **45 / 18 / 68 / 129 hours** (monthly coordinate) or **138 / 22 / 61 / 108**
(daily coordinate) out of 8760 — **0.25 % – 1.58 % of the year**. A form that cannot fire outside
that window cannot move the annual level by more than that share of its own magnitude.

**Reported anyway, at full magnitude, per zone per year, BEFORE the solve** (`G-LEVEL`): the
cap-weighted **annual mean** `Δmc` per zone per year. **NYC is a level pocket** — nyiso-247's
removed term ran **−4.36 to −5.73 $/MWh** in NYC against **−1.49 to −2.77** ISO-wide, because the
per-zone anchors are not each zone's own delivered mean once `nyiso_zonal_gas_basis` applies. Any
zonal offer work inherits that, and this form's NYC number is reported beside its ISO-wide number
rather than averaged into it.

**Bar:** ISO-wide cap-weighted annual mean `Δmc` **≤ +0.60 $/MWh** in every year — well inside the
magnitude nyiso-247 moved and declared. **Above it, the form is a level intervention and is
declared as such in the RESULT**, not quietly absorbed.

---

## 5. DUTY (e) — C1 / C2 GUARD BANDS, AND THE ONE AT ITS EDGE

**NAMED RISK, BY NAME: C1-2023 ST_GAS.** It sits at **+3.59 TWh** against ±3.82 and **+3.0 pp**
against ±3 pp — **essentially no headroom**, and nyiso-247 moved it the wrong way to get there.
**ST_GAS is inside this form's eligible class set**, so this form can push it over.

**PASS → FAIL band, pre-registered:** any increase in 2023 ST_GAS annual energy beyond
**+0.23 TWh** (3.82 − 3.59) or **+0.0 pp** of share fails C1-2023. **That is the tightest gate in
this lane and it is a hard one**: a C1 failure is a load-bearing-tier failure and no rule ledgers
it.

Also pre-registered as hard: **no C1 or C2 per-year status may move PASS → FAIL in any year**
(nyiso-247's G-D bar, adopted unchanged).

---

## 6. DUTY (f) — THE C3c PREDICTION, FALSIFIABLE

**What the form should do: raise the count of model hours > $300 in the years whose tight window
is largest, and leave 2023 and 2024 nearly untouched.** Stated as a number, before the solve:

| year | model h > $300 now | actual | tight hours (daily coord.) | **predicted model h > $300** |
|---|---:|---:|---:|---:|
| 2022 | 16 | 101 | 138 | **≥ 25** |
| 2023 | 0 | 10 | 22 | 0 – 3 |
| 2024 | 0 | 13 | 61 | 0 – 5 |
| 2025 | 3 | 42 | 108 | **≥ 8** |

**The falsification is explicit and it is the point of the gate:** *an arm that moves the mean
without moving the tail has not found the tail.* If 2022 and 2025 do **not** clear their bars
while `G-LEVEL` shows a non-trivial annual-mean move, the form is a level intervention wearing a
tail's clothes and **fails**, whatever the residual does.

**This is a prediction, not a promotion criterion** (rule 1 `[R-STRUCT]`): the run is a keeper for
being structurally faithful, and C3c is a **ledgered** caveat under rule 22 `[R-C3C]` that does
not downgrade the determination either way.

---

## 7. DUTIES (b) AND (c) — RULE 19 `[R-ONE-MECH]` AND RULE 25 `[R-ISO-SCOPE]`

### 7.1 Every armed non-base offer / min-gen writer in the keeper, and how this form is disjoint

| armed mechanism | what it writes | disjoint because |
|---|---|---|
| `nyiso_st_gas_econ_bands_deleaked` | ST_GAS `econ_*` band **multipliers** | time-**invariant**; this form is conditional and additive on top of the resolved `mc`, and touches no band |
| `nyiso_ct_peaker_committed_measured` | CT_PEAKER `committed` band = 0.843 | same — a band multiplier, all 8760 h |
| `tranche_startup_amortization` | amortized startup markup, **P0→P1 seam** | a **commitment-cost recovery** keyed to run length, not to system state; fires in every committed hour, not in tight ones |
| `nyiso_gas_commitment_bridge` (+ `_min_run`, `_startup`, `_startup_aware`) | a **`min_gen` floor** | a *quantity* floor, not an offer price; different object entirely |
| `reliability_floor_overrides` | `min_gen` floors | quantity, as above |
| `nyiso_downstate_ct_gas_daily` | **SETS** downstate CT_PEAKER delivered gas | a **fuel-price input**, and `CT_PEAKER` is **excluded from this form's eligible set** precisely so the two cannot stack — see §7.2 |
| `gas_hub_basis_overlay` + `gas_hub_basis_daily` + `nyiso_zonal_gas_basis` | delivered gas level/shape | fuel-price inputs; this form multiplies `τ` **by** that delivered price rather than re-deriving it |
| `dual_fuel_oil_daily_parity`, `dual_fuel_oil_reattribution` | `min(gas, oil)` delivered price | fuel-price inputs, upstream of `mc`; unchanged |
| `nyiso_nyc_rcpf_step_curve`, `nyiso_seny_rcpf_increment_step`, `nyiso_ordc_measured_step_span`, `nyiso_dynamic_reserve_requirements` | **reserve** demand curves | the reserve side, foreclosed as a C3c route by nyiso-242 §4; this form is on the **energy offer** and adds nothing to the reserve stack |
| `gas_offer_net_revenue_margin` | **DISARMED** by nyiso-247 | the conditional offer-level channel is **EMPTY**. This form **occupies it; it does not stack on it** — and it is **not a re-arm**: the disarmed term made the implied heat rate *fall* with gas on **all** capacity, where this raises it on the measured **upper tail only**. |

**The rule-19 statement, plainly:** after nyiso-247 **nothing in the NYISO recipe writes a
state-conditional offer-level response.** This form **REPLACES nothing and is disjoint from every
armed writer**, because each of them is either time-invariant, a quantity floor, a fuel-price
input, or on the reserve side.

### 7.2 The eligible class set, and why CT_PEAKER is out

Eligible: **merchant `CC_REGULAR` + `ST_GAS`** — the 16.4 GW price-setting rungs, the same set
nyiso-248 §3 measured as carrying 89–105 % of the source gas swing. **`CT_PEAKER` is excluded**
because `nyiso_downstate_ct_gas_daily` already re-grounds its delivered gas on the measured LDC
index; lifting its offer again on the same driver is the stack rule 19 forbids. CHP classes are
excluded (steam-host obligation, not merchant conduct).

### 7.3 Rule 25 `[R-ISO-SCOPE]`

`miso_offer_surface_measured` and `miso_offer_spread_anchored` are **MISO's**. The **method** may
cross; **no value may.** Every `τ` comes from NYISO's own P-27 book. `MISO_OFFER_SPREAD_ANCHOR_RANK`
is not read. The matrix cell `nyiso_offer_tail_dispersion` × NYISO enters as **`U`**.

---

## 8. THE ANTI-SWEEP CLAUSE, BINDING

**One arm.** `τ` is read off the arm §2.3 selects, at p75 and p90, and is **not tuned**. If the arm
fails a gate, the lane **reports the failure** — it does not try p80/p95, a different truncation
rank, a different eligible class set, or a scaling factor. A second arm exists only if the FIRST
arm exposes a **construction error** (a mis-wired seam, a routing failure), never because a gate
missed. Any second arm is declared in an addendum **before** it is solved, with what changed and
why the change is a repair rather than a search.

**No band multiplier moves.** Rule 1 `[R-STRUCT]`'s authorized price-tuning carve-out is **NOT
invoked**; `authorized_price_tuning` stays `null` and C6 is attested without it.

---

## 9. THE SOLVE, IF AND ONLY IF EVERY ZERO-LP GATE CLEARS

Rule 36 `[R-YEAR-ISOLATION]`: **four year-isolated shards, one per year**, own `--out-dir`, own
branch, each pushing its **full** bundle including `dispatch/<year>_P1.parquet` (rule 34
`[R-SHARD-PROMOTABLE]` (a): `.gitignore` **negation** + **plain** `git add`, never `git add -f`),
pinned to a full 40-char SHA, solve in the **foreground**. Both warm-start knobs left at their OFF
defaults. Rule 34 (c): the year union is **{2022, 2023, 2024, 2025}** — enumerated from the
registry **before** anything is pruned — and **all four are solved**. The parent composes at zero
LP with `scripts/probes/nyiso247_compose_span.py`, mints the attestation from the keeper's
(`gen_nyiso247_attestation.py` — `replay_keeper.py` writes none, so C6 would score UNATTESTED),
builds the DOF ledger, rebuilds the benchmark, registers, and puts the promotion question to the
owner (rule 31 `[R-RETAIN]`).

**Routing check before the solve** (nyiso-247 PRECOMMIT §2): a `solve_and_persist` kwarg routes
through the kwarg channel; a `ScenarioConfig`-only field routes through `prb_overrides` and **can
be re-stomped**. Verified before any shard launches, not after.

---

## 10. WHAT THIS SESSION OWES REGARDLESS OF OUTCOME

1. The **G-1 derive repair** (gas array as a parameter) lands whether or not a form is armed — it
   is a correctness fix to a committed derive, independent of this lane's verdict.
2. The **matrix shard** `docs/codebase-site/data/mechanism-matrix/NYISO.js` is updated in this
   session (rule 28(b)), rejected outcomes included.
3. Every number this lane cites lives in this doc or the RESULT (rule 29 `[R-SCREEN]` (c)).
4. **Nothing is deleted** (rule 31 `[R-RETAIN]`), and the promotion question is **asked**, not
   answered on the lane's own judgement.
