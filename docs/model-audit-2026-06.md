# Third-Party Model Audit — Defensibility for Emissions-Trajectory Forecasting

**Date:** 2026-06-28
**Scope:** Whether the LP market simulator can *defensibly* forecast dispatch **and** capacity expansion, and specifically whether it can produce **emissions trajectories within probability bounds** suitable for professional/regulatory use.
**Benchmarks:** EPA IPM, GenX, PLEXOS (LT Plan + nodal), Aurora, EIA AEO conventions.
**Method:** Six independent subsystem audits (dispatch, capacity, uncertainty, calibration/overfitting, emissions accounting, data inputs), each evidenced to `file:line`. This document synthesizes them. It is an assessment only — no model code was changed.

---

## 1. Headline verdict

**The dispatch LP *core* is professionally defensible as a zonal production-cost engine. The model as a whole is *not yet* defensible for probability-bounded emissions-trajectory forecasting** — but the gap is well-defined and closable. Three things block a defensible forward emissions band today:

1. **No out-of-sample validation.** Every backcast year (2023/2024/2025) is simultaneously training and test. Backcast fit measures data plumbing, not forecast skill — a fact the team's own peer-review doc states plainly.
2. **No probabilistic machinery.** The only uncertainty propagated is weather, over **3 draws**. There is no Monte Carlo / Latin Hypercube over gas, load, carbon, or technology cost, and no correlation structure. A P10/P50/P90 emissions band is not currently producible with statistical content.
3. **Capacity expansion is myopic, not intertemporal.** Single-year-at-a-time greedy entry/exit (vs. the perfect/limited-foresight optimization in IPM and GenX) systematically biases the *emissions path* — delayed fossil exit, under-built clean-firm, gas-CT lock-in.

A fourth, IPM-specific gap: **emissions are never a binding constraint** (no mass cap / cap-and-trade), only a price adder — so the forecast cannot endogenously respond to a tightening CO₂ budget, which is the core mechanism of every regulatory power-sector emissions study.

Underlying all of this is a **large overfitting surface**: ~50–70 tunable per-ISO knobs against ~30–40 target numbers, with a documented history of residual-chasing in the calibration logs (mostly, but not entirely, walked back).

**Bottom line for the stated use case:** Today the model yields *deterministic scenario point-estimates plus a 3-draw weather sensitivity* — comparable to an AEO side-case table only after a scenario matrix is built, and **not** comparable to a probabilistic IPM/GenX-stochastic emissions band. The path to "defensible within probability bounds" is the prompt pack in `docs/model-audit-prompt-pack-2026-06.md`.

---

## 2. Subsystem scorecard

| Subsystem | Structural fidelity | Defensible today? | Primary gap vs IPM/GenX/PLEXOS |
|---|---|---|---|
| **Dispatch LP core** | High | Yes (zonal PCM) | LP-heuristic UC vs MIP; zonal pipe-and-bubble vs nodal DC-OPF |
| **Unit commitment** | Medium | With disclosure | No integer commitment / true min-up-down / startup non-convexity |
| **Transmission** | Medium | For zonal studies | No PTDF/loop-flow/nodal LMP |
| **Capacity expansion** | Medium | **No** (as IPM peer) | Myopic, not intertemporal; revenue signal known-broken |
| **Uncertainty / prob. bounds** | Low | **No** | One axis (weather), n=3, no correlation, no MC/LHS |
| **Emissions accounting** | Medium-High | Partly | No mass-cap constraint; flat (load-invariant) emission rate; startup/no-load emissions discarded |
| **Calibration rigor** | — | **No** | Zero out-of-sample test; ~50–70 knobs/ISO |
| **Data inputs** | High | Mostly | Load *shape* and renewable CF don't evolve; 436/814 params `needs-citation` |

---

## 3. What is genuinely strong (keep, and lead with it)

These are real and should be stated plainly in any deliverable:

- **LP formulation is textbook-correct.** Per-zone hourly energy balance, **prices = energy-balance duals** (no negation), **renewables as decision variables** on the LHS with endogenous curtailment, proper inter-temporal storage SOC with cyclic boundary, fully vectorized construction (no Python hour loops). Matches GenX/Aurora conventions. (`dispatch.py:1178-1281`, `:1466-1475`, `:2017`)
- **Energy + reserve co-optimization is real** when enabled — shared-headroom rows lift the energy LMP through the reserve dual, the correct SCED/GenX mechanism. ORDC shortfall steps price reserves endogenously. (`dispatch.py:851-887`, `:292-302`)
- **Economic retirement screens *inframarginal margin*** (Σ(price−mc)·dispatch vs FOM), not gross revenue — the correct going-forward economics, matching IPM/GenX. (`capacity.py:374-379`)
- **Wright's-law learning** tied to a *global* cumulative-deployment tracker; IRA ITC/PTC enter at the correct layer. (`capacity.py:690-723`, `:772-789`)
- **Technology costs are almost entirely NREL ATB-2024-cited** with learning curves — the AEO/IPM convention. (`constants.py:1550`, `:1738`)
- **Forecast-vs-backcast input separation is clean and principled** for outages, fuel, hydro, nuclear CF: statistical/parametric forward, measured overlays strictly backcast-gated. Hydro forecast (climatology mean + water-year lever) is exemplary. (`outages.py`, `constants.py:264-292`)
- **Honest internal documentation.** The peer-review and validation-plan docs already name most of these gaps; the calibration rubric is correctly designed to *fail* current keepers (all ERCOT keepers score NOT-YET). The practice is converging toward the rules.

---

## 4. Material weaknesses, by theme

### 4.1 Validation — the crux (blocks all forecast claims)
- **No out-of-sample test.** Fit and score on the same 2023–2025. `docs/peer-review-2026-06.md:44-52` — *"current error metrics measure data plumbing, not forecast machinery."*
- The **statistical-mode backcast (all overlays off)** is specified in `forecast-validation-plan.md` Phase 3 but **never run** — the single missing experiment.
- No **capacity hindcast** — the fleet-evolution layer that produces the emissions path has never been validated against realized EIA-860 retirements/builds.

### 4.2 Probability bounds (the explicit ask)
- `ensemble.py` varies **only `weather_year`** over a **3-member** pool; `numpy.percentile` on n=3 has no statistical content (`ensemble.py:143-153`, `constants.py:3830`).
- Scenario levers (`gas_price_path`, `demand_growth_path`, `carbon_price_path`, ...) are **discrete low/mid/high point selectors**, not distributions, and are varied **independently** — no correlation between gas ↔ load ↔ weather, which is where the fat-tail emissions days live.
- A factorial **sweep engine already exists** (`scenarios.py:2989-3015`) — the raw material for a scenario matrix — but is used for tuning, not structured UQ.

### 4.3 Capacity expansion — myopia biases the emissions trajectory
- Each year sees only one year of backward-looking prices; no NPV-over-life, no cross-year co-optimization. Greedy highest-single-year-margin entry (`capacity.py:1112`).
- Emissions-path biases: retirement **thrashing** (loss counter resets on any profitable year → fossil stays online longer → emissions over-stated in transition); **under-build of capital-intensive clean** (can't anticipate a future binding RPS/carbon price); **gas-CT lock-in** via the cheap-firm-MW adequacy backstop.
- The **revenue signal is documented as broken** — peaker/storage net revenue recovers ~1–6% of PNM/IMM benchmarks (`forecasting-entry-exit-assessment.md`), so the **15% reliability floor — not economics — governs retirements** (`capacity.py:429-445`). Verdict in that doc for tail-dependent tech: *"No — not as it stands."*
- CCS retrofit uses **simple payback** (`capacity.py:1354`), weaker than the rest of the entry logic, on a placeholder flat CF=0.55 (`capacity.py:139`, flagged TODO).

### 4.4 Emissions accounting (IPM parity gaps)
- **No CO₂/NOx mass cap.** `get_active_policy_constraints` returns `[]` (`constraints.py:28`). RGGI/CSAPR/111 modeled as exogenous $/ton adders, not binding budgets whose dual clears an allowance market. This is the biggest single gap vs IPM for an emissions product.
- **Emission rate is dispatch-level-invariant.** CAMPD provides marginal + no-load + startup decomposition (`campd.py:703-808`) but dispatch uses a single flat tCO₂/MWh and **discards startup/partial-load emissions**. IPM uses load-segment heat-rate curves.
- **No SO₂ output** (priced but not tallied); seasonal-NOx not supported — both needed for CSAPR/regional-haze.
- New/forecast units fall through to fuel-class defaults, creating a silent vintage discontinuity as CEMS-rated units retire.

### 4.5 Inputs that don't evolve forward
- **Load shape is a pinned weather year, uniformly scaled** (`runner.py:119-134`) — no data-center flat-load, EV evening charging, or electrification winter-peak re-shaping. Growth magnitude captured; shape evolution absent. Understates future peak/ramp and net-load deepening.
- **Renewable CF profiles don't degrade or improve** (no PV degradation, no hub-height/tracking gains, no resource-quality decline); new builds inherit the existing fleet's shape (`renewables.py:1643`).
- **436 of 814 registered parameters are flagged `needs-citation`** (`parameter-citations.md:27`).

---

## 5. Magic-number & overfitting register (high-leverage subset)

These are the values most likely to draw a "calibrated curve-fit" objection. Full inventories are in the subsystem audits; this is the subset that materially moves the **emissions trajectory** or **price level**.

### 5.1 Capacity / retirement (drives the emissions path directly)
| Value | Location | Role | Why suspect |
|---|---|---|---|
| **1.3×** | `scenarios.py:136` | Coal effective-FOM bump "for ESG/regulatory risk" | Pure judgment, no citation; directly accelerates coal exit |
| **1.15 (15%)** | `scenarios.py:144` | Retirement reliability floor | Arbitrary; per the assessment it does the economics' job |
| **1/2/3/2/2/3/3 yr** | `scenarios.py:129-135` | Per-fuel consecutive-loss thresholds | Ordering defensible, integers unsourced; reset behavior fragile |
| **FOM $8/$12/$40** | gas_ct/cc/coal | Exit thresholds | Far below NREL ATB ($21/$30/$45) — a compensating error vs under-counted revenue |
| **1.5** | `constants.py:1419` | Storage ELCC saturation exponent | Self-labeled "tunable" shape knob |
| **GW/yr build & queue caps** | `constants.py:1192-1198`, `1459-1491` | Entry throughput | Eastern-ISO caps self-flagged "Tier 3 … needs-citation"; bind and bias trajectory |

### 5.2 Dispatch / offer curve (drives price level → economic signals)
| Value | Location | Role | Why suspect |
|---|---|---|---|
| `COAL_TRANCHES` splits | `constants.py:115-119` | Coal offer-curve shape | Comment: "calibrated to EIA-930 2023-24 hourly ERCOT coal" — fitted shape |
| offer-curve multipliers | `offer_curve_by_group`, per-run `_deltas.json` | ~28 multipliers/ISO + hand-set deltas | The primary calibration lever / residual-fitting surface |
| `ERCOT_AS_REVENUE_PER_KW_YR` 169/22/15/8; sat. exp 2.5 | `constants.py:1329-1357` | Exogenous AS revenue overlay | ERCOT-only "calibrated, exogenous"; shape exponent is a pure fit |
| net-load drag coeffs | per-ISO (ERCOT 0.00703/−0.1427/0.47; CAISO re-fit 0.00901/−0.1124/0.36) | CT/ST availability vs net load | Least-squares-fit to 2023–25 measured CF-vs-netload, re-fit per ISO |

### 5.3 Emissions factors (regulatory-product red flags)
| Value | Location | Role | Why suspect |
|---|---|---|---|
| gas **0.057**, coal **0.100** tCO₂/MMBtu | `constants.py:170` | Fuel CO₂ factors | **Back-solved from internal CO2_RATES, not EPA Part 98** (EPA: gas ≈0.0531, bit. coal ≈0.0933) |
| `CO2_RATES`/`NOX_RATES` inline edits | `constants.py:154-157` | Class rates | "was 0.0001 → 0.00008" hand-tuning without re-citation |

### 5.4 Overfitting summary
- **~50–70 tunable knobs per ISO** vs **~30–40 target numbers** (3 yrs × fuel-class volumes + annual prices). The fit is not over-determined.
- Documented residual-chasing despite the anti-fit rules, e.g. `prb_floor` chosen by "which year passes" (`calibration-best-so-far.md:225-232`), `wefor_residual` dropped 0.11→0.06 to hold a volume target (`:382-385`), CEMS-pinned `ct_deployment` enabled in past keepers (`backcast-measured-data-audit-2026-06.md:51`), HSL output-rescale fixed only 2026-06-17 (`:81-85`).
- **Mitigating:** current keepers reject the worst overlays; the NYISO log shows genuine discipline; the rubric's C6 governance gate is hard and correctly fails today's keepers. The system is *converging* toward its own rules — it has not yet arrived.

---

## 6. What "defensible within probability bounds" requires (gate list)

A forward emissions band is defensible when **all** of these hold. None are satisfied today; ordered by leverage:

1. **Statistical-mode backcast run** (all measured overlays OFF) → a measured dispatch/emissions error distribution = the structural-error prior. *(Phase 3, specified, unrun.)*
2. **True out-of-sample test** — fit on 2023–2024, score 2025 blind (or leave-one-year-out). Forecast skill, not fit.
3. **Capacity hindcast** — start ~2018, predict retirements/builds, score vs EIA-860.
4. **Multivariate uncertainty sampler** (LHS/MC) over gas, load, carbon, retirement, tech-cost, weather — with **correlation/copula** structure and source-justified marginals (AEO spread, NYMEX implied vol, ATB ranges); ≥50–100 draws for stable tail quantiles.
5. **Structural-error prior folded into the published band**, so P10/P90 reflects model error + input spread, not input spread alone.
6. **Emissions mass-cap constraint** so the trajectory responds endogenously to tightening budgets (IPM parity).
7. **Sensitivity/tornado on the §5 high-leverage knobs**, with the offer-curve `_deltas` and per-plant overrides frozen — so the band isn't an artifact of in-sample tuning.

Items 1–3 are gates on *any* forecast claim. Items 4–5 are the probability-band machinery proper. Items 6–7 are emissions-trajectory fidelity and overfitting de-risk.

---

## 7. Honest framing for clients (until the gates are met)

- **Defensible to state:** "Zonal LP production-cost model with co-optimized reserves and a recursive-dynamic fleet-evolution layer; dispatch mechanisms mirror real market structure; technology costs ATB-anchored."
- **Not yet defensible to state:** "Validated forward emissions forecast," "P10/P50/P90 emissions band," "capacity-expansion-optimal," or any forward number whose credibility rests on backcast fit.
- **Disclose:** zonal (not nodal) congestion; LP-relaxed (not MIP) commitment; myopic (not intertemporal) expansion; emissions priced (not capped).

Implementation is sequenced in **`docs/model-audit-prompt-pack-2026-06.md`**.
