# Model-Audit Prompt Pack — Path to Defensible Emissions-Trajectory Forecasting

**Companion to:** `docs/model-audit-2026-06.md` (the audit).
**Purpose:** Ready-to-paste handoff prompts, one per improvement, sequenced so the model becomes defensible for **probability-bounded emissions-trajectory forecasting** vs IPM/GenX/PLEXOS/Aurora.

**How to use:** Each prompt is a self-contained brief for a fresh Claude Code session. Paste one as the first message. They are grouped into tiers; **do Tier 0 first** — those are gates on *any* forecast claim and several later tiers depend on their outputs. Within a tier, prompts are independent and can run in parallel sessions. Each prompt states its dependencies.

**Conventions every prompt inherits (do not repeat in the session):** obey `CLAUDE.md` non-negotiable rules (esp. #1 structure-first, #5 cite every number, #10/#11/#12 no output-pinning, #16 parallelism), keep changes on a `phase-N/...` branch, add tests, register any backcast run on the dashboard, and never tune a parameter to move a residual.

---

## Tier 0 — Validation gates (block every forward claim; do these first)

### PP-0.1 — Statistical-mode backcast (the single missing experiment)
```
Run the statistical-mode backcast specified in docs/forecast-validation-plan.md Phase 3:
re-solve every available backcast year (CAISO/PJM/NEISO/NYISO --year 2023 2024 2025;
ERCOT its full span) with ALL measured/calibration overlays turned OFF — no CAMPD
outage windows, no F923 delivered fuel, no CEMS emission-rate pins, no CEMS ct_deployment,
no HSL rescale, no per-run offer-curve _deltas, no measured interchange band. Use only the
forward statistical/parametric models (statistical EFORd/POF, AEO fuel paths, parametric
offer curves at their default multipliers). Goal: measure the model's TRUE skill — what it
predicts from forward drivers alone — and produce the dispatch/price/emissions error
distribution that becomes the structural-error prior for forecast bands.

Deliverables: (1) an audit of which overlays are wired and how to disable each (extend
docs/backcast-measured-data-audit-2026-06.md); (2) a single CLI/flag (e.g.
--overlays-off / mode="statistical-backcast") that disables all of them coherently, with a
test; (3) the run bundles registered on the dashboard, labelled clearly as statistical-mode
(NOT keepers); (4) a short report comparing statistical-mode error vs the overlay-on keepers,
per ISO, per metric (emissions, fuel-class volumes, load-weighted price). Do NOT tune anything
to improve the statistical-mode fit — a worse fit here is the finding, not a bug to patch.
Start by reading docs/peer-review-2026-06.md §3, forecast-validation-plan.md, and
backcast-measured-data-audit-2026-06.md.
```

### PP-0.2 — True out-of-sample / hold-out skill test
```
Implement an out-of-sample forecast-skill test. Today calibration fits and scores on the same
2023-2025 years, so backcast fit cannot be cited as forecast skill (docs/peer-review-2026-06.md).
Build a leave-one-year-out harness: calibrate all per-ISO knobs on a training subset (e.g.
2023-2024), FREEZE them, then score the held-out year (2025) blind — and rotate. Report the
held-out error vs the in-sample error per ISO and per metric (emissions_mt, fuel-class volumes,
load-weighted price). The delta is the overfitting penalty. Add a make/script target and a test
that fails if anyone scores a year that was in its own training set (a calibration_reference_guard
analogue). Read docs/calibration-determination-rubric.md and results/calibration.py first. Do not
re-tune to shrink the held-out error; document it.
```

### PP-0.3 — Capacity-expansion hindcast
```
Validate the fleet-evolution layer that produces the emissions trajectory. It has never been
scored against reality. Build a capacity hindcast: initialize the fleet at ~2018 from EIA-860,
run the one-pass year-evolution loop (retirements → economic retirement → additions → CCS →
economic entry) forward to 2024 under historical fuel/load/policy, and compare PREDICTED
retirements, builds (by technology), and annual emissions against realized EIA-860 / EIA-923 /
CAMPD. Report hit/miss on major retirements and the emissions-path error. This directly tests
the myopia bias flagged in docs/forecasting-entry-exit-assessment.md. Read capacity.py, the
runner.py year loop, and that assessment doc first. Deliverable: a hindcast script, a scorecard
doc (docs/capacity-hindcast-2026-06.md), and a verdict on whether the capacity layer is fit to
quote forward.
```

---

## Tier 1 — Probability bounds (the explicit client requirement)

### PP-1.1 — Structured scenario matrix (cheap, ship first)
```
Build an AEO/IPM-style scenario matrix using the EXISTING SweepDefinition engine
(config/scenarios.py:2989-3015) — do not write a new sweep. Define named cases as the cross of
gas_price_path × demand_growth_path × carbon_price_path × retirement_aggressiveness (start with a
reference + high/low gas + high/low load + policy-on/off set, ~10-15 named cases). Add a YAML
scenario-matrix definition and a runner entrypoint that solves all cases and emits a per-case
emissions trajectory table (2026-2050) plus a min/max envelope. This is a deterministic SCENARIO
RANGE, not yet a probability band — label it as such. Read runner.py:1037-1144 and
config/scenarios.py:44-67 first. Add a test on the matrix expansion.
```

### PP-1.2 — Multivariate uncertainty sampler with correlation (the core machinery)
```
Add a probabilistic forecast driver — the central deliverable for "emissions within probability
bounds." Extend the ensemble pattern in src/market_sim/ensemble.py (keep its parallel
ProcessPoolExecutor + per-member cache design) from one axis (weather_year) to a multivariate
Latin Hypercube / Monte Carlo sampler over: gas price, demand growth, carbon price, retirement
aggressiveness, technology cost (ATB range), and weather year. Requirements:
  (1) Source-justified marginal distributions per input — gas as lognormal around the AEO
      reference with vol from NYMEX implied vol; load growth from the AEO range; tech cost from
      ATB low/high; carbon from policy-scenario weights. Cite each (CLAUDE.md #5).
  (2) A CORRELATION / Gaussian-copula structure linking gas ↔ load ↔ weather (and carbon ↔ policy
      regime) — without it the joint band is indefensible. Make the correlation matrix an explicit,
      documented, sourced input.
  (3) ≥50-100 draws (configurable) for stable tail quantiles; report P10/P50/P90 (and n) on every
      annual metric, emissions_mt first. Drop ddof=0 / 3-point percentiles; document the estimator.
Deliverable: a sampler module, a CLI, a probabilistic emissions-trajectory report with a fan chart,
and tests. Read ensemble.py, constants.py:541-615 (gas paths), :1003-1005 (carbon), :466-502
(demand), :1550 (ATB) first. Depends on nothing but is only DEFENSIBLE once Tier 0 supplies the
structural-error prior (PP-1.3).
```

### PP-1.3 — Fold the structural-error prior into the published band
```
Combine input uncertainty (PP-1.2) with model structural error (PP-0.1 statistical-mode backcast
+ PP-0.3 hindcast) into a single published P10/P50/P90 emissions band. Convolve the input-driven
distribution with the measured forecast-error distribution so the band reflects BOTH sources, not
input spread alone. Document the convolution method and its assumptions. Deliverable: the final
banded emissions-trajectory report and a methodology note (docs/probabilistic-emissions-
methodology.md). Depends on PP-0.1, PP-0.3, PP-1.2.
```

---

## Tier 2 — Structural fidelity for the emissions trajectory

### PP-2.1 — Emissions mass-cap constraint (IPM parity, biggest single emissions gap)
```
Add an optional CO2 (and NOx) MASS-CAP LP constraint so the model can represent RGGI/CSAPR/
EPA-111 budgets as binding caps whose dual is the endogenous allowance price — instead of the
current exogenous $/ton adder. The extension point exists: policy/constraints.py:28
get_active_policy_constraints returns []. Add a per-region annual mass-budget row to the LP
(Σ dispatch×emission_rate ≤ cap), wire its dual back as the effective carbon price, and let the
budget decline on a schedule (ScenarioConfig field, default off / no cap). This is the core IPM
mechanism for emissions trajectories. Keep it pure-LP. Read policy/constraints.py, policy/carbon.py,
model/dispatch.py constraint assembly, and model-methodology-spec.md emissions sections first.
Test with a trivial 1-gen/1-zone case where the cap binds and the dual equals the expected
switching price. Add a test that cap-off reproduces today's results exactly.
```

### PP-2.2 — Multi-year foresight / NPV entry-exit (fix myopia)
```
Reduce the myopia bias in capacity expansion (docs/model-audit-2026-06.md §4.3,
docs/forecasting-entry-exit-assessment.md). Replace the single-year margin-vs-cost entry/exit
test with a multi-year discounted net-revenue (NPV-over-life) screen: project forward energy +
capacity + AS revenue over a build's economic life (a simple forward-price extrapolation is an
acceptable first step), discount, and compare to annualized fixed cost / going-forward FOM. Also
make the retirement consecutive-loss counter hysteresis-aware so break-even units stop thrashing
(don't fully reset on one marginal year). Keep the one-pass-per-year structure (CLAUDE.md #9) — this
is a better per-year SIGNAL, not within-year iteration. Where full foresight is out of scope, label
outputs "myopic recursive-dynamic," not "capacity-expansion-optimal." Read capacity.py:374-379,
:1045-1112, :1426-1590 and the assessment doc first. Add tests on the NPV screen and the hysteresis.
```

### PP-2.3 — Fix the capacity-economics revenue signal
```
The economic entry/exit screens are governed by the 15% reliability floor, not economics, because
the energy-only LP duals recover only ~1-6% of benchmark peaker/storage net revenue
(docs/forecasting-entry-exit-assessment.md §3,§5). Fix the signal so economics does the work:
  (1) Add the AS-revenue stream to the capacity economics (currently exactly $0 there) using the
      existing ancillary machinery, not a new exogenous adder.
  (2) Calibrate annual scarcity rent recovered by the screen to a published anchor (ERCOT IMM /
      PNM) as a forward-reproducible adjustment — NOT a residual-fit to backcast price.
  (3) Re-examine the below-ATB FOM exit thresholds ($8/$12/$40 vs ATB $21/$30/$45) which currently
      compensate for the under-counted revenue — fix both together so neither hides the other
      (CLAUDE.md #11).
Verify against PP-0.3's hindcast that retirements become economics-driven rather than floor-driven.
Read capacity.py:429-445, model/ancillary.py, and the assessment doc first.
```

### PP-2.4 — Wire startup / no-load / partial-load emissions into the tally
```
The CAMPD loader already decomposes marginal + no-load + per-start emissions
(data/campd.py:703-808) but the dispatch tally uses a single flat tCO2/MWh and discards startup and
partial-load emissions (docs/model-audit-2026-06.md §4.4). Wire the already-computed startup_* and
co2_noload_kg_per_hr into the post-dispatch emissions tally (results/emissions.py), using the
commitment run-lengths from the 3-solve screen to count starts. Optionally expose a partial-load
emission curve (marginal + no-load) instead of the flat per-MWh rate, matching IPM load segments.
Cheap, material fidelity gain for the cycling fleet. Read campd.py:703-808, results/emissions.py,
model/commitment.py first. Add a test on the startup-emissions accounting.
```

---

## Tier 3 — De-risk overfitting & magic numbers

### PP-3.1 — Sensitivity/tornado on high-leverage knobs + freeze overlays
```
Quantify and contain the overfitting surface (docs/model-audit-2026-06.md §5). (1) Run a
tornado/sensitivity analysis on the highest-leverage emissions-trajectory knobs: coal FOM
multiplier 1.3x (scenarios.py:136), retirement reliability floor 1.15 (:144), per-fuel
consecutive-loss thresholds (:129-135), net-load drag coefficients (per-ISO), storage ELCC
saturation exponent 1.5 (constants.py:1419), and the gas/coal FOM exit thresholds — report how
much each moves a 2030/2040 emissions number. (2) FREEZE the per-run offer-curve _deltas.json
overlays and per-plant committed-pct overrides as the least forward-defensible knobs: move them
behind an explicitly-labelled, default-off diagnostic flag (CLAUDE.md #10), and re-confirm keepers
still gate without them or document the gap. Deliverable: docs/sensitivity-tornado-2026-06.md.
Do not tune anything; this is measurement and containment.
```

### PP-3.2 — Citation sweep + re-cite emission factors to EPA
```
Close the citation gap: 436 of 814 registered parameters are flagged needs-citation
(docs/parameter-citations.md:27), violating CLAUDE.md #5. Priorities:
  (1) Re-cite FUEL_CO2_FACTOR_PER_MMBTU (constants.py:170) to EPA Part 98 / AP-42 PRIMARY factors
      (gas ≈0.0531, bituminous coal ≈0.0933 tCO2/MMBtu) instead of the current back-solved 0.057/
      0.100; document any intentional deviation. This is a regulatory-product red flag.
  (2) Replace the chart-eyeballed AEO gas trajectories (constants.py:528, "approximate
      interpolations from charts") with API-pulled values via scripts/data/fetch_eia_aeo.py; upgrade to
      AEO2026.
  (3) Verify the Tier-3 needs-citation block for non-ERCOT/CAISO RENEWABLE_AVG_CF,
      RENEWABLE_INSTALLED_MW, demand growth, and gas availability (constants.py:478-492, 1795-1825)
      against EIA-860/923 before any non-ERCOT forecast is quoted.
Read docs/parameter-citations.md first. Each fix is a citation comment + value correction where the
real source differs; treat a value change as a potential bug (CLAUDE.md #11), not a cosmetic edit.
```

### PP-3.3 — Forward load-shape evolution
```
The forecast load is a pinned weather year scaled by one scalar (runner.py:119-134) — no shape
evolution for the resources that drive the forward story (docs/model-audit-2026-06.md §4.5). Add a
load-shape evolution layer on top of the scaled weather year: a data-center flat base-load adder,
an EV evening-charging shape, and an electrification winter-peak premium, each as a sourced,
forward-reproducible ScenarioConfig input (AEO EVOLVED / ISO interconnection-queue load), default
calibrated to current AEO. Decompose DEMAND_GROWTH_RATES by driver (data center / EV /
electrification / baseline) so the rate is auditable. This affects peak, scarcity pricing, and
capacity entry — re-run PP-0.3 hindcast and PP-1.1 matrix after. Read runner.py:119-134,
constants.py:466-502, data/eia_loader.py first. Add tests on the shape adders.
```

### PP-3.4 — (Optional, disclosure-driven) MIP-UC and rolling-horizon storage cross-checks
```
Bound the two disclosed fidelity gaps vs PLEXOS/GenX. (1) Add a true MIP unit-commitment mode
(binary on/off + explicit min-up/min-down/startup) runnable on representative weeks, as a VALIDATION
cross-check against the LP 3-solve heuristic — quantify the relaxation error in prices/commitment;
keep the LP screen as the default. (2) Make rolling-horizon (or default daily-SOC-cap) storage the
default to remove the perfect-foresight arbitrage bias, which worsens as LDES enters forecasts (the
storage_daily_cycling flag and estimate_storage_revenue building blocks already exist). Read
model/commitment.py, model/dispatch.py:1099-1110 storage notes, and model-methodology-spec.md §1.6.
Only needed if clients compare directly to MIP/nodal tools; otherwise disclosure (audit §7) suffices.
```

---

## Suggested execution order

1. **PP-0.1, PP-0.2, PP-0.3** in parallel — until these land, no forward number is quotable.
2. **PP-2.1** (mass cap) and **PP-1.1** (scenario matrix) — independent, high value, can start alongside Tier 0.
3. **PP-1.2** then **PP-1.3** — the probability-band machinery (PP-1.3 needs Tier 0 outputs).
4. **PP-2.2, PP-2.3** — fix the capacity layer; re-score with PP-0.3.
5. **PP-2.4, PP-3.1, PP-3.2, PP-3.3** — fidelity + de-risk, parallelizable.
6. **PP-3.4** — only if direct MIP/nodal comparison is required.

A forward emissions band is defensible to publish once Tier 0 + PP-1.2 + PP-1.3 + PP-2.1 are complete and PP-3.1 confirms the band is not an artifact of in-sample tuning.
