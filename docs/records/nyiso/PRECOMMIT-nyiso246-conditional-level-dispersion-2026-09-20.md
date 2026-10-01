# PRECOMMIT nyiso-246 — the ANCHORED CONDITIONAL-LEVEL-DISPERSION graft: every rule, bar and kill fixed EX ANTE, before any gated number exists

**Session nyiso-246 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); ZERO LP in this container).**
**Date** 2026-09-20. **Base** `origin/main` at `83543f3c`.
**Keeper** `2026-09-19-nyiso241-ct-committed-measured`, bundle
`results/calibration/nyiso241_ctcommitted_span`, `git_sha` `5356fb71`, years {2022, 2023, 2024,
2025}. **ISO tier (2023–2025, rule 30 `[R-TOUCHPOINT-FOLD]` (c)) = CALIBRATED**, C3c the lone
ledgered caveat. **Registered full span (2022–2025) = NOT-YET, on 2022's C3a + C3b alone.**
**Predecessor** `docs/RESULT-nyiso245-the-object-is-level-dispersion-not-shape-2026-09-20.md` §5.

**THIS DOCUMENT IS COMMITTED AND PUSHED BEFORE ANY GATED NUMBER IS COMPUTED.** Everything cited
below is either (i) a committed prior artifact, (ii) a property of an *input* series that selects
no hour set and decides no gate, or (iii) a rule fixed here. No statistic conditioned on the
mechanism's own TIGHT/ORDINARY windows exists at this commit.

---

## 0. THE OBJECT, AND WHY IT IS NOT THE ONE nyiso-245 REFUSED

nyiso-245 refused the within-unit SHAPE form on NYISO's own corpus (G3a: 0 of 12 populated cells
monotone against an 80 % bar; largest Δ anywhere $7.28/MWh) and its diagnostic located the real
object. Missed minus ordinary winter 2022, **within-unit** differences over gens present in BOTH
windows (so the ~9.4 GW fleet-scope gap cancels exactly), capacity-weighted median $/MWh:

| | curve BOTTOM | within-unit RISE |
|---|---:|---:|
| market (P-27, all gens) | +26.66 | +0.12 |
| market, multi-block only (203 gens, 31,547 MW) | +19.01 *(p75 +112.05, p90 +231.59)* | +1.03 |
| **model (the keeper)** | **+40.00** *(p75 +44.36)* | **+11.34** |

And in MW: **112 gens / 8,774 MW / 24.3 % of declared capacity reprice by more than $100/MWh**
when the event arrives — **1.86× the 4,715.7 MW object**. MW-weighted mean move: market **$54.66**,
model **~$40**.

**The model has approximately the right MEAN conditional passthrough and the wrong DISTRIBUTION.**
Since the energy dual is set by the *marginal* unit, it is the upper part of that distribution, not
its mean, that makes the price — which is why this reads as C3a (level) **and** C3b (shape), the two
criteria that fail.

### 0.1 The structural story — stated BEFORE the mechanism, because rule 1 `[R-STRUCT]` requires the mechanism to be real rather than to fit

The model prices **every** gas unit off ONE delivered-gas series (`_gas_series(config, year, 8760)`),
so unit *g*'s conditional move is `HR_g × ΔG` — deterministic in the heat rate, hence a tight
distribution about ~$40 whose only spread is the heat-rate spread. The real NYISO winter book has a
**distribution of own-delivered-fuel costs** around that reference:

* firm versus interruptible/non-firm pipeline transportation — a unit without firm transport buys at
  the intraday spot, a unit with it does not;
* the **opportunity cost of held gas** — a unit holding firm supply can resell it, so its offer
  carries the gas's *resale* value, not its contract cost;
* and a residual heterogeneity in contracting the model represents nowhere.

That is a named market structure, it is not a residual, and it regenerates forward: the *dispersion*
of own-fuel cost about a reference is a contracting/conduct parameter that exists in any forward
year, while the reference itself is the model's own forward gas trajectory. **Rule 13
`[R-MEASURED]`**: every input is a submitted OFFER, never a cleared price, a realised dispatch, an
award column or a residual.

### 0.2 A SECOND defect this mechanism deliberately does NOT address, named so it is not silently absorbed

The keeper's delivered gas is `annual price × monthly seasonal shape` (`gas_seasonality` on,
`gas_monthly_actuals` off): a **smooth** series. 2022 runs $6.239 → $12.745 (mean $8.657), 2025
$3.240 → $14.095. The real winter citygate is spiky at daily grain. A spikier COMMON gas signal is a
**different** mechanism (the NYISO analogue of `caiso_citygate_spot_coverage` /
`miso_winter_citygate_daily`), it needs its own PRECOMMIT, and it is **named here as a successor, not
folded in**. It also cannot produce the measured object on its own: a common series moves every unit
together, and the measurement says three quarters of capacity moves < $25 while a quarter moves
$100–232.

---

## 1. THE MECHANISM — `ScenarioConfig.nyiso_offer_level_dispersion_anchored` (bool, default False, NYISO-gated)

A NYISO member of the **`miso_offer_spread_anchored` family** (miso-179/180,
`data/offer_curves.py::apply_miso_offer_spread_anchored`,
`scripts/data/derive_miso_offer_level_dispersion.py`). **Rule 25 `[R-ISO-SCOPE]`: the METHOD, the
population rules, the estimator and the registered grid geometry cross; NO MISO VALUE CROSSES.**
`MISO_OFFER_SPREAD_ANCHOR_RANK = 0.875` is MISO's and is **not** read here. Every number the graft
consumes is measured on NYISO MIS **P-27** against NYISO's own delivered-gas series and NYISO's own
measured net load.

**What differs from MISO's, and why.** MISO's object is *unconditional* offer level. NYISO's is the
**conditional response** — the within-unit change between a tight state and an ordinary one. The
family's form is therefore evaluated at conditional grain: the measured vector is a distribution of
*differences*, not of levels.

### 1.1 The two states — INPUT-SIDE ONLY, and the one declared departure from nyiso-245's geometry

The mechanism's conditioning may never touch the residual. nyiso-245's diagnostic window ("missed
hours") is defined by the model's own price error and is **forbidden** anywhere in this
identification or applier. Both coordinates below are measured inputs that exist in a forecast year:

* **net load** — EIA-930 `Demand − NG:WND − NG:SUN`, per year (nyiso-245's own construction);
* **delivered gas** — the keeper's own resolved `_gas_series`, the identical object the applier
  passes in (one gas object, one identification).

Both are binned on the **registered cross-ISO percentile ladder** `NETLOAD_PCTS = (0.80, 0.90,
0.97)` (`derive_nyiso_offer_surface.py`), **within each year's own distribution**, giving bins
{0,1,2,3}. **No new number is invented: the ladder is adopted unchanged and applied to both
coordinates.**

> **TIGHT** = `gas_bin ≥ 2` **AND** `load_bin ≥ 2` (both at or above the year's own 90th percentile)
> **ORDINARY** = `gas_bin == 0` **AND** `load_bin == 0` (both below the year's own 80th percentile)

**THE ONE DECLARED DEPARTURE, with its measured reason.** nyiso-245's derive binned gas on **pooled**
terciles, on the stated ground that "a delivered gas price is directly comparable across years in a
way a load level is not". That is right for a LEVEL surface and wrong here, and the input series says
so: **2022's MINIMUM delivered gas ($6.239) exceeds 2023's and 2024's MAXIMUM ($5.095 / $6.060).**

| year | min | p50 | p80 | p90 | p97 | max |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | 6.239 | 8.702 | 9.962 | 11.067 | 12.745 | 12.745 |
| 2023 | 2.613 | 3.069 | 3.568 | 4.579 | 5.095 | 5.095 |
| 2024 | 2.170 | 2.309 | 2.731 | 4.285 | 6.060 | 6.060 |
| 2025 | 3.240 | 4.235 | 7.396 | 8.085 | 14.095 | 14.095 |

A pooled gas bin would therefore place essentially the whole of 2022 in the top bin and essentially
none of 2023–2024 — **a year selector wearing a scarcity selector's clothes**. Within-year
percentiles make the coordinate relative and unit-free, exactly as nyiso-245's own net-load rationale
requires, and they regenerate for a forecast year whose gas *level* differs. **This is a property of
the input series alone; it selects no hour set and decides no gate.** It is fixed here and never
re-tuned (rule 23 `[R-FROZEN-DERIVE]`).

**Reported beside the artifact, adjudicating nothing:** the month composition of each year's TIGHT
set. The physical driver is a winter gas-supply event; if TIGHT is not winter-dominated, the reader
must be able to see that. **No month filter is applied** — adding one would be an unfrozen DOF.

### 1.2 The measured artifact — `data/raw/_validation-source/nyiso_offer_level_dispersion.json`

Derived by `scripts/data/derive_nyiso_offer_level_dispersion.py`. Corpus: NYISO MIS **P-27**
`genbids`, **DAM only**, 2022–2025, **pooled** (per-year sub-vectors are a stationarity check and are
**never consumed** — a per-year vector would be a same-year measured-outcome pin, rule 13).
Population rules are the family's, **adopted unchanged** (a re-invented exclusion set is a tuning
channel): `Upper Oper Limit > 0`, not fully self-scheduled, hour in range.

For each masked gen *g* and window *W* ∈ {TIGHT, ORDINARY}:

```
b_g(h)   = the unit-hour's curve BOTTOM  =  Dispatch $/MW1            ($/MWh)
β_g,W    = capacity-weighted MEDIAN over h ∈ W of  b_g(h) / G(h)      (MMBtu/MWh)
δ_g      = β_g,TIGHT − β_g,ORDINARY                                   (MMBtu/MWh)
```

* **Within-unit difference**, over gens present in **BOTH** windows only — so unit identity, class,
  fuel level, market level and the ~9.4 GW fleet-scope gap cancel **exactly**. P-27's masking cannot
  block it, for the same reason nyiso-245's coordinate could not be blocked.
* **Normalized by the model's own `G(h)`** — MISO's normalization (`m = level / G_ref`), which is
  what makes δ an implied-heat-rate object that regenerates forward. Using the model's own series
  (not a second, independently built one) is deliberate: one gas object, one identification, and the
  graft reproduces the measured *dollar* effect when it multiplies back by the same G.
* **Estimator**: capacity-weighted, step-function (sort → cumulative weight → `searchsorted`), the
  family's convention throughout. Weight = the unit-hour's declared `Upper Oper Limit`.

**The vector**: capacity-weighted quantiles of δ on the family's **frozen 199-point grid**
`p = 0.5 %, 1.0 %, …, 99.5 %` → `Δ̂(p)` in MMBtu/MWh. **sha256-pinned** in `constants.py`
(`NYISO_OFFER_DISPERSION_ARTIFACT_SHA256`); the applier hard-errors on drift and never falls back
silently (rules 21/24).

**Self-test (must pass before any gate is read):** T-1 recovery of a known answer; **T-2 LEVEL
INVARIANCE** — shifting a unit's whole curve by a constant in BOTH windows leaves δ bit-identical;
T-3 a unit whose bottom is unchanged between windows has δ = 0.

### 1.3 The graft — SPREAD-ONLY, RAISE-ONLY, LEVEL-AGNOSTIC

With `a` the anchor rank (§2), `aff` the affected tranches (§1.4), `r_g` each tranche's
capacity-weighted **mass-midpoint rank** in `aff` (MISO's estimator, unchanged) computed once per
year from its TIGHT-hour mean `mc`, and `G(t)` the model's own delivered gas:

```
for each TIGHT hour t:
    A(t)      = the affected stack's OWN capacity-weighted a-quantile of mc[aff, t]
    target[g] = A(t) + ( Δ̂(r_g) − Δ̂(a) ) × G(t)          for every g with r_g > a
    mc[g, t]  = max( mc[g, t], target[g] )
```

Tranches at or below the anchor are **untouched**. Hours outside TIGHT are **untouched**. The graft
is applied to the BASE cost, so P0 run discovery and the P1 bid see the same curve and the P1
startup-amortization markup stays on top unchanged (the measured levels are ENERGY offers).

Three properties, each load-bearing:

1. **SPREAD ONLY, NEVER LEVEL.** The target is pinned to `A(t)` — *the model's own* a-quantile at
   that hour. **No measured level is transferred, from MISO or from NYISO.** The body the
   measurement says the model already over-prices (+$40 vs +$19/+$26.66 at the median) is untouched
   by construction, and raising it is forbidden by that same measurement.
2. **RAISE-ONLY and RANK-PRESERVING** inside the affected stack (the max of two monotone-in-rank
   curves), so the graft cannot invert a merit order some other mechanism established.
3. **LEVEL-AGNOSTIC**, which is how it satisfies rule 19 — see §3.

### 1.4 The affected rows

The family's registered selector, **adopted unchanged** except for dropping `COAL`, which NYISO does
not have:

* **band suffix** — `econ*` or `peak*`. `committed` / `mustrun` / `sync` bands are the model's
  analogue of the book's self-scheduled and must-run mass and are **never repriced** (the family's
  own rule). Row ids are `<CLASS>_<ZONE>_p<plant>_<band>`; the band token is
  `unit_id.rpartition("_")[2]` (note `peak` itself starts with `p`, so a plant token is tested with
  `tok[1:].isdigit()`).
* **class** — `^(CC_|CT_|ST_GAS)` on `plant_group`. This admits `CC_CHP` and `CT_CHP` and excludes
  `ST_CHP`, exactly as the family's regex does; the exclusion set is **not** re-invented.

---

## 2. THE ANCHOR — IDENTIFIED EX ANTE BY A FROZEN RULE, COMPUTED ONCE, NEVER SWEPT

miso-180's **crossing rule is a METHOD** and is reused. **Its rank, 0.875, is MISO's and is not
read.** With `GRID` the frozen 199-point grid and both curves built by the **identical**
construction — capacity-weighted quantiles, step-function estimator, the same TIGHT/ORDINARY windows,
the same per-hour normalization by `G(t)`, pooled 2022–2025:

* `Q_book(p)` — the p-quantile of the measured book's δ (§1.2);
* `Q_mod(p)`  — the p-quantile of the MODEL's own conditional response over the affected tranches,
  `δ_mod,g = mean_{t∈TIGHT}( mc[g,t]/G(t) ) − mean_{t∈ORD}( mc[g,t]/G(t) )`, weights `pmax`.

> **`r_anchor = max{ p ∈ GRID : Q_mod(p) ≥ Q_book(p) }`** — the last rank at which the model's
> conditional response is at or above the book's.

This is the empirical boundary between the measured **over**-region (the body, where raising is
forbidden) and the measured **under**-region (the tail, where the object lives). Its identification
path contains **inputs only**: two input-side state definitions, the model's input offer surface
`mc_base` (no solve output), the model's own gas series, and the measured book (no LMP, no residual,
no award column). Nothing in the path moves when the model's price error moves.

**ANTI-SWEEP CLAUSE, binding.** The anchor is computed **ONCE** by this rule, written into
`constants.py` as `NYISO_OFFER_DISPERSION_ANCHOR_RANK`, and frozen before any solve. **An anchor
evaluated at a second value, or chosen because a gate or a criterion passed, is the fitted-mechanism
selection rule 1 `[R-STRUCT]` exists to forbid, and is a KILL — not an option.** The same holds for
every bin edge, bar and threshold in this document.

**STOP-IDENTIFICATION guards** (FINDING written, matrix cell minted `R` citing identification
failure, **NO LP**, no anchor variant tried):

* **(g1)** no `p` with `Q_mod(p) ≥ Q_book(p)` — the model is under everywhere; the body-over premise
  is broken.
* **(g2)** `r_anchor > 0.975` — fewer than four grid points above the anchor; no interior room.
* **(g3)** `r_anchor ≤ 0.50` — the crossing is not in the upper half; the premise fails.

---

## 3. THE GATES — every bar fixed HERE, evaluated in this order, all at ZERO LP

A **FAIL** on any gate refuses the mechanism **before a shard**. Rule 26 `[R-DELETE]`: on a refusal
the `ScenarioConfig` field and the applier are **REVERTED**, never committed default-off.

### G0 — SUPPORT. *(bar fixed here)*
≥ **100** TIGHT hours in **≥ 3 of 4** years, and **≥ 150** gens present in BOTH windows pooled.
Below either, the conditional object is not measurable and the answer is STOP-IDENTIFICATION.

### G1 — REACH. *(nyiso-245's 50 % bar, CARRIED FORWARD UNCHANGED, denominator unchanged)*
Above-anchor (`r_g > a`) affected-tranche capacity that is **available, idle and priced below $300**
in the **median missed winter hour of 2022**, as a share of the **4,715.7 MW** object. **Bar: ≥ 50 %.**

*Stated plainly, because it cuts against the mechanism:* an anchored form is **structurally
disadvantaged** on a footprint bar — it reaches only the ranks above `a` by design, where nyiso-245's
un-anchored row gate reached 78.5 % and nyiso-244's peak-rung form 15.8 %. That is the correct
conservatism and the bar is **not** relaxed for it. **There is no fallback gate.** The missed-hour
window enters only as the object's own definition and sizing — it touches no parameter, no bin edge
and no anchor.
*Reported beside it, gating nothing:* the same share measured on the mechanism's OWN input-side
TIGHT window, and the un-anchored row-gate share (comparable to 78.5 %).

### G2 — RULE 19 `[R-ONE-MECH]`. *(see §4 for the full argument)*
**Zero** affected rows may also be the base row of another armed writer. The five armed non-base
writers are enumerated from the keeper's own `run_config.json`, never from memory.

### G3 — THE CORPUS. *(the gate that can refuse on the book alone, as nyiso-245's G3a did)*
* **G3a — THE DISPERSION EXISTS, AND IS NOT A PRICE-TAKER ARTIFACT.**
  `Δ̂(0.90) − Δ̂(0.50) ≥ 2.0` MMBtu/MWh, required on **BOTH** the all-gens population **and** the
  multi-block-only population (every single-block price taker excluded). *Bar rationale, from a
  committed prior artifact only:* nyiso-245 measured the market's conditional bottom at +$19.01
  (p50) versus +$231.59 (p90) on the multi-block population, which at any winter gas reference in the
  committed series (≥ $6.24/MMBtu in 2022) is ≥ 30 MMBtu/MWh. **2.0 is deliberately an order of
  magnitude below the committed measurement**, so it refuses only a corpus whose dispersion is an
  estimator or price-taker artifact — it is not a bar the object has to strain to clear.
* **G3b — STATIONARITY.** The same statistic ≥ the same bar in **≥ 3 of 4** years. Per-year vectors
  are a check and are never consumed.
* **G3c — CONTAMINATION.** Single-block price-taker share of unit-hours and of capacity, **reported
  at full magnitude, gating nothing**, exactly as nyiso-245 pre-registered. They are **KEPT** (the
  family's population rules keep them); excluding them is a DIFFERENT mechanism needing its own
  PRECOMMIT. Their weight can only pull δ toward zero, so the bias is conservative.

### D — THE DEGENERACY GUARD. *(owed by the handoff; bars fixed here)*
A graft that moves every unit by the same amount is a level shift wearing a dispersion costume.
All three are **hard-errors in the armed applier**, not merely phase-0 checks:

* **D1 — rank variation.** `max(r_g) − min(r_g) ≥ 0.50` over the affected tranches.
* **D2 — graft variation.** Over the above-anchor rows in the **median TIGHT hour**, the assigned
  rise `(Δ̂(r_g) − Δ̂(a)) × G(t)` must have **IQR ≥ $5.00/MWh** and **max − min ≥ $25.00/MWh**.
  *Bar rationale, from committed measurements only:* the model's own conditional response already has
  p75 − p50 = **$4.36** (nyiso-245), so a graft whose own IQR is under $5 has added nothing the model
  did not already have; $25 is a quarter of the $100 threshold at which the committed measurement
  finds 24.3 % of market capacity.
* **D3 — artifact non-degeneracy.** `Δ̂(0.95) − Δ̂(a) ≥ 1.0` MMBtu/MWh.

### G4 — NOT INERT.
≥ **500 MW** of repriced capacity moves ≥ **$1.00/MWh** in the median TIGHT hour of 2022 (nyiso-245's
own bar and construction, unchanged).

### G5 — C1/C2 EXPOSURE, MEASURED BEFORE THE SOLVE.
Reported, gating nothing at phase 0 — the share of thermal capacity on repriced rows, and the median
and p95 move over all hours. It exists so the size of the intervention is written down **before** any
result is seen.

---

## 4. RULE 19 `[R-ONE-MECH]` — THE FULL ARGUMENT, INCLUDING WHAT IT DOES *NOT* CLAIM

**(a) Enumeration** — five armed fields can write a NYISO non-base rung (nyiso-245 §3(a), from the
keeper's own `run_config.json`): `gas_offer_net_revenue_margin`, `gas_offer_margin_zonal_anchor`,
`gas_offer_margin_zonal_anchor_vintage`, `nyiso_st_gas_econ_bands_deleaked`,
`nyiso_ct_peaker_committed_measured`. `nyiso_zonal_loss_surface` name-matches and is adjudicated
rather than filtered: it splits internal transmission chain links and writes no generator row.

**(b) REPLACE, NEVER STACK — and the mechanism by which that holds.** The graft's target is
`A(t) + spread`, where `A(t)` is the affected stack's own a-quantile of the **post-incumbent** `mc`.
Whatever the incumbents did to the LEVEL is therefore **inherited, not overwritten and not stacked
upon**: the graft transfers only the spread above a level it does not touch. It is raise-only and
rank-preserving, so it cannot invert an incumbent's ordering below the anchor, and it writes nothing
at or below the anchor. The one way this could fail is a row that is both a target and another
target's base — **G2 measures it and the bar is zero.**

**(c) WHAT THIS MECHANISM DOES NOT CLAIM, STATED AT THE GATE RATHER THAN ABSORBED.** nyiso-245 §3
measured that in the 70 missed winter hours of 2022 the armed `gas_offer_net_revenue_margin`
contributes a **capacity-weighted mean of −$51.75/MWh** to the tagged rows, negative in **88.3 %** of
row-hours: its term is `markup_hr × (anchor − fuel)` and goes negative exactly when delivered gas
spikes above the frozen $3.9046 anchor. **This graft does not fix that, and must not be read as
fixing it.** Because the graft is level-agnostic it *inherits* that level through `A(t)` — so if the
level is depressed in the very hours that fail, the graft's target is depressed with it and the
mechanism **under-delivers**. That is the correct separation of concerns: repairing the level is the
other lane's job (the handoff names it as worth a PRECOMMIT of its own, and
`nyiso_st_gas_econ_bands_deleaked` already routes the ST_GAS markup to OPEN ROOT CAUSE issue #1344).
**Inflating this graft's spread to cover a level defect would be precisely the fitted adder rule 1
forbids**, and it is not done.

---

## 5. THE CONTROL — form 4, and the G-DRIFT audit that validates it (rule 29 `[R-SCREEN]` (b))

**No control solve is spent.** The committed keeper bundle is the control. Two things establish it:

1. **nyiso-245 §6 measured rule 36 `[R-YEAR-ISOLATION]` (f) CLOSED for NYISO** — all four years
   replayed at HEAD, year-isolated, both knobs OFF: **max |Δ class TWh| = 0.0000 and 0 of 43,800
   zonal price cells moved, in every year.** NYISO does not carry the warm-start artifact.
2. **G-DRIFT over `4a01ae60 → 83543f3c`** (nyiso-245's pinned SHA to this base), the paths rule 29
   (b) names. Five files changed; **every hunk is INERT for a NYISO backcast**:

| path | classification | reason |
|---|---|---|
| `data/raw/_validation-source/nyiso_offer_surface_positional.json` | INERT | new artifact; the mechanism that would read it was refused and no `ScenarioConfig` field survives — nothing in the solve path opens it |
| `src/market_sim/config/scenarios.py` | INERT | one new field, `gas_flow_date_year_start_package: bool = False`, default off and absent from the keeper's recipe |
| `src/market_sim/data/fuel/hubs.py` | INERT | adds `_year_start_package_seed` and a `prior_year_dated=None`-defaulted parameter on `_flow_date_staircase`; **caller enumeration**: the only three callers are `_caiso_hub_daily_gas_prices` and the two MISO basis callers. NYISO enters none of them |
| `src/market_sim/data/fuel/basis/miso.py` | INERT | another ISO's branch |
| `src/market_sim/pipeline/backcast_config.py` | INERT | `coal_takeorpay_from_data=(iso in ("MISO","NWPP"))`; NYISO is neither |

**All hunks INERT ⇒ form 4 is valid and the committed keeper is the control.** Recorded here, before
the arm is solved, so it cannot be written to fit the result.

---

## 6. THE SOLVE, IF AND ONLY IF EVERY GATE CLEARS

Rule 36 `[R-YEAR-ISOLATION]` (a): **one year, one shard, one container, its own `--out-dir`** —
2022, 2023, 2024, 2025, four shards, pinned to this document's commit SHA. Rule 32 (b)'s fan-out ban
does not apply to a backcast; rule 36 (a) says so in terms. `MARKET_SIM_WARMSTART_XYEAR` and
`MARKET_SIM_P1_BASIS_SEED` are **left at their defaults (OFF)** and are not set.
Rule 34 `[R-SHARD-PROMOTABLE]` (a): **every shard pushes its FULL bundle including
`dispatch/<year>_P1.parquet`**, by a `.gitignore` NEGATION plus a PLAIN `git add` — never
`git add -f`. Rule 34 (c): **all four years of the keeper's union are solved**, none left out.
The parent composes at zero LP, scores, registers (rule 15) and asks the promotion question
(rule 31).

## 7. THE PROMOTION CRITERIA — fixed here, so the residual cannot choose them

* **P1** — every §3 gate clears and the §2 anchor identifies. *(Prerequisite for solving at all.)*
* **P2** — the **ISO tier (2023–2025)** determination does not degrade from **CALIBRATED**.
* **P3** — **C1 and C2 do not cross a PASS→FAIL boundary in ANY of the four years.** Both are
  reported **at full magnitude beside C3a/C3b/C3c for every scored year**. **A C1/C2 degradation is
  REPORTED, never traded for price** — a price gain bought with a volume loss is refused here, in
  advance.
* **P4** — **2022's C3a and C3b are REPORTED, and are NOT a promotion criterion.** Rule 1
  `[R-STRUCT]` is explicit: a structurally-correct mechanism is never judged by whether the residual
  moved, and is never reverted because it did not. **If P1–P3 hold and 2022 still fails, the
  mechanism remains promotable on structure and this session will say so.** Conversely, **2022
  improving is not by itself a reason to promote** — P1 is.
* **P5** — rule 31 `[R-RETAIN]`: nothing is deleted, and the promotion question is put to the owner
  explicitly before this session ends.

## 8. DUTIES THIS SESSION OWES REGARDLESS OF OUTCOME

* **Rule 15 `[R-DASHBOARD]`** — an arm that solves is registered in this session, keeper or not.
* **Rule 28 `[R-MECH-MATRIX]`** (b)/(c) — the NYISO cell is minted with its verdict and citation in
  `docs/codebase-site/data/mechanism-matrix/NYISO.js`; a new `ScenarioConfig` field owes its base row
  in `mechanism-matrix.js` **plus a cell line in EVERY ISO shard**, in the same PR.
* **Rule 26 `[R-DELETE]`** — on a refusal, the field and the applier are REVERTED, not committed
  default-off. A deprecated knob that still parses is a re-armable answer key.
* **Rule 33 `[R-SHARD-ARCHIVE]`** — shards archived once the parent holds and has verified their
  bytes; a shard branch is TRANSPORT, not STORAGE.
