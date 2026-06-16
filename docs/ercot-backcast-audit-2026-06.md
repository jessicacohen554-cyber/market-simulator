# Third-Party Audit — ERCOT Backcast (best result so far, run 115b)

**Date:** 2026-06-15
**Subject:** the current best ERCOT dispatch backcast — keeper **run 115b**
(`results/calibration/run115b_ccduct_prb73_relief06`), plus the run-118
spatial probe and the 2026-06-15 within-class diagnosis.
**Frame:** an external energy-modeling panel reviewing the backcast *as a
backcast* — i.e. how credibly it reproduces 2023–2025 ERCOT dispatch,
volumes, emissions and prices, and how much of that fit is mechanism vs
fitted-to-history plumbing.
**Method:** code + bundle reads of `model/`, `data/outages.py`,
`fleet.py`, the offer-curve / binning methodology, the ORDC overlay, the
`derive_ct_deployment.py` / `derive_reliability_deployment.py` overlays, the
calibration log (runs 80→118), `calibration-best-so-far.md`, and the
prior whole-model review `docs/peer-review-2026-06.md` (which predates the
run-85→118 campaign and is referenced, not repeated). Findings carrying a
re-verified file/number are marked **[checked]**.

This audit is **diagnosis only** — no dispatch or calibration parameter was
changed.

> **Follow-up (2026-06-16):** tests D1–D4 of §D have been run — see
> `docs/audit-followup-tests-2026-06.md`. Headlines: out-of-sample (all
> overlays off) the in-scope fails **double, 5 → 10**, system CO₂ runs +8/+9%
> high and hourly-r degrades on 0/18 classes (D1, confirming B1); the
> historic-outage overlay is the dominant — and most defensible — leakage
> lever while the CEMS-pinned CT floor is the smaller, circular one (D2); the
> new CO₂ gate catches a real keeper failure the volume gate hides (2024 coal
> CO₂ −8.9%, D3); and the CC_REGULAR merit-ramp fixes the operating shape
> cleanly but the 2024/25 volume over-run is not offer-closable (D4, confirming
> the B2 spatial diagnosis).

---

## Executive summary

The backcast is a genuinely strong production-cost reconstruction: per-plant
CAMPD offer curves, measured zonal load shares, grid-delivered (BTM-held-out)
scoring, multi-year testing across three very different gas regimes, LP-dual
prices with clean degeneracy hygiene, and an unusually honest paper trail.
On **annual class volumes** — the metric most production-cost backcasts are
judged on — the large classes (CC, coal, nuclear, wind, solar) sit inside an
industry-normal band, and the fuel-split gates hold. That part is real and
above the bar most commercial-tool studies clear.

Three findings dominate the "where it falls short" column, in priority order:

1. **The fit is not yet validated out-of-sample, and it now leans on a
   growing stack of per-plant, per-hour, CEMS-keyed overlays that feed the
   answer in.** Historic outage windows, the CT AS/RUC-deployment floor (which
   *pins peakers to their observed CEMS output* in ~30–44 % of their energy),
   the new run-118 spatial reliability-deployment floor, F923 delivered fuel,
   per-plant CEMS emission rates, the HSL rescale and per-year nuclear/coal
   overlays are all legitimate calibration devices — but the headline error
   metric currently measures data plumbing, not forecast machinery. **The
   statistical-mode backcast (every overlay off) has still not been run**
   (`docs/statistical-mode-backcast.md` does not exist; Phase 3 of
   `forecast-validation-plan.md` is open). Until it is, the backcast's skill
   number is unknown, and — critically — the overlays that produce much of the
   CT/pocket-thermal fit **have no forward analogue**, so the dispatch logic
   being *validated* is not the dispatch logic being *forecast*.

2. **The newest, tighter gate exposes a real within-class shape failure that
   the old class-total gate hid.** Under the 2026-06-15 universal gate
   (|model−actual| ≤ 0.33 % of annual generation, ≈1.5 TWh), run 115b has
   **5 in-scope fails**: CT_PEAKER 2023/2024, **CC_REGULAR 2024/2025**, and
   COAL_PRB 2024. The CC_REGULAR class total used to pass at ±5 %, but the
   efficient grid CCs are running as **flat baseload blocks that miss
   thousands of >90 % CF hours** (Freestone logs **0** hours ≥90 % CF against
   CAMPD's 1 300–3 000), over-generating in the North (+6 TWh) while
   South_Central thermal is under by −8.7 TWh. This is a class passing on its
   *total* while getting the *operating shape and spatial allocation wrong* —
   exactly the failure annual-volume gates are blind to.

3. **Scarcity-price formation is reproduced by a fitted knob, not a
   mechanism.** The energy-only LP structurally cannot price scarcity (0 hours
   >$500 vs 99–104 actual in 2023). The ORDC overlay is methodologically
   honest but, with defensible parameters, recovers only ~7–12 % of the 2023
   summer scarcity gap; the rest is closed by `ordc_reliability_deployment_mw`
   — an explicitly **non-physical, flat-MW offset calibrated to the 2023 stress
   year** (2,500 MW → 2023 monthly LMP MAE 32.5 → 12.3). For a model whose
   stated end-products are prices, revenue and emissions, the price tail is the
   least-grounded part, and the milder years (2024/2025) are under-served by
   the single 2023-anchored offset.

Verdict: **excellent volume backcast, unproven forecast prior, and a
within-class/price layer that is still being carried by calibration devices
rather than mechanism.** The single highest-value next step is the
statistical-mode backcast — it converts every claim below from "asserted" to
"measured."

---

## A. Where it is doing well (keep, and say so)

- **Annual class-volume calibration across three gas regimes.** 2023 ($2.54),
  2024 ($2.19, the cheap-gas stress on coal) and 2025 ($3.52) are calibrated
  *jointly*, not one year cherry-picked. The dominant classes hold, and the
  **fuel-split gates** (total gas / total coal within ±2.5 %) pass — a real
  guard against the classic "right total, wrong split" compensation.
- **Per-plant CAMPD binning with rising tranche offer curves.** One LP unit
  per plant on its own measured `Plant_Avg_HR`, committed floors derived
  per-plant from the CAMPD CF-P5 (min stable load), CHP host steam pulled out
  of the LP and added back post-solve. This is PROMOD-grade representation and
  the backbone of the result.
- **Grid-delivered scoring basis.** Judging model grid dispatch against
  EIA-923 **minus** the authoritative BTM host supply (`btm.parquet`) is the
  correct, honest denominator — it stops the model being credited for steam it
  never optimized. The 2025 switch to EIA-930 (because the 2025 EIA-923 is the
  incomplete monthly vintage) is the right call and caught a phantom gas-split
  fail.
- **The justified-anomaly reasoning on PRB 2024.** Recognizing that the 2024
  PRB low is the LP *correctly* idling loss-making self-committed coal (40–52 %
  CF while $2.19 gas put it below marginal cost, no outage) — rather than
  forcing an even miss with a cheaper floor — is exactly the right modeling
  instinct: it preserves a real price-response signal instead of fitting it
  away. The W A Parish per-plant check (+0.22/−1.36/+0.15 TWh vs CEMS) backs it.
- **ORDC overlay design.** Post-solve, additive, emitted as a *separate
  series* that never gates volumes or LMP; built from the published NPRR568 /
  OBDRR formula with every parameter a cited `ScenarioConfig` field; the
  pre-adder honesty diagnostic (monotone residual-vs-headroom table) is
  textbook. The model is thin in the hours reality was thin (Spearman
  ρ ≈ −0.39), so the price gap is correctly attributed to the price mechanism,
  not an availability bug.
- **AS-netting investigated and rejected with the right reason** (RTOLCAP
  already counts AS-held headroom as reserves → subtracting it double-counts).
- **Degeneracy hygiene, LP-dual prices, citation discipline, honest
  "do-not-chase" structural diagnoses** throughout. The calibration log is a
  model of its kind.

---

## B. Where it falls short

### B1 — In-sample overlay dependence; no out-of-sample number yet **[checked]**

The backcast's fit is produced with a stack of devices that each inject part
of the answer:

| Overlay | What it feeds in | Where |
|---|---|---|
| Historic CAMPD outage overlay | per-plant realized outage windows | `historic_outage_overlay` |
| **CT AS/RUC-deployment floor** | **peakers pinned to observed CEMS net output in out-of-merit hours (~1.3/1.9/2.2 TWh = 30/35/43 % of covered CT energy)** | `derive_ct_deployment.py` → `ct_deployment_floor_for_year` |
| **Spatial reliability-deployment floor** (run 118) | pocket CC/coal/ST pinned to observed CEMS net in congestion hours (2.7/3.6/5.2 TWh) | `derive_reliability_deployment.py` |
| F923 delivered fuel | actual per-plant monthly coal cost | `coal_plant_monthly_pricing` |
| Per-plant CEMS emission rates | realized rates, not class defaults | bundle `campd.parquet` |
| HSL rescale | renewable output retargeted onto actuals | `renewables.py` |
| Nuclear monthly CF / per-year coal pricing | realized utilization | run config |

The CT deployment floor is the sharpest case: in the hours it covers, the
unit's output is *set to the CEMS value*, so the match in those hours is close
to definitional, not earned by the merit order. The reliability-deployment
floor generalizes the same mechanism to pocket thermal. These are defensible
**as calibration**, but two consequences follow that the headline numbers do
not currently disclose:

- **The error metric measures plumbing.** No statistical-mode run exists
  (`docs/statistical-mode-backcast.md` absent; Phase 3 unopened), so the
  share of the fit attributable to the LP vs the overlays is **unmeasured**.
- **The validated model ≠ the forecast model.** Every CEMS-keyed overlay is
  default-off and *byte-identical to a no-op in forecast mode* (correctly — it
  has no forward input). So the CT and pocket-thermal dispatch that the
  backcast is scored on **simply is not present in any forward year**. The
  thing being calibrated is not the thing being deployed.

This is the #1 finding. It does not say the backcast is wrong — it says its
forecast-relevant skill is **currently unknown**, and the dependence has grown
(runs 109→115→118 each added a CEMS-keyed floor).

### B2 — CC_REGULAR within-class shape & spatial misallocation (open) **[checked]**

The class total passes the old ±5 % bar but fails three sub-tests:

- **Operating shape.** Efficient F-class CCs run flat baseload and miss their
  observed >90 % CF mass. Run-118 measured: Freestone **0** model hours ≥90 %
  CF (CAMPD 1 630/1 338/3 065); Colorado Bend II puts **5** hours in 95–100 %
  CF where the real plant put **1 159**. Root cause is structural, not a tuning
  residual: the CC **duct-firing peak band sits at 2.0–2.6× base HR as a flat
  tranche above the econ ramp**, creating a price wall, and combined with the
  ~5 % availability derate it imposes an effective steady ceiling of ~87–92 %
  of nameplate. **This is physically wrong** — true duct firing is ~5 % of
  nameplate at ~1.3–1.5× incremental, not 8 % at 2.57×; the model is pricing
  ordinary baseload output as if it were duct firing.
- **Merit axis.** The class-total fit was bought with the `econ_high −0.40`
  calibration delta, which *flattened/inverted* the econ ramp (resolved
  1.06 → 1.01) so the most-efficient unit's whole econ tranche pins at the
  bottom of the CC merit order. Per-plant miss correlates with heat rate at
  −0.75/−0.79/−0.85 — a clean efficient-over / inefficient-under signature.
  A calibration choice made for the *total* broke the *distribution*.
- **Spatial axis.** Thermal miss by zone (2025): North **+6.1 TWh**,
  South_Central **−8.7**, West −1.8, Northeast −1.0; CC_REGULAR North is
  +4.5 TWh of the over-run. The binding ERCOT constraints are **intra-zonal
  pockets** (NE_LOB, Rio Grande Valley, HMLTN, WHARTN) the 7-zone reduction
  cannot form, so ~44 TWh of under-zone thermal that ran "out of merit vs the
  hub" is dispatched to the wrong zone. Inter-zonal TTC moves were measured
  no-ops; this is a topology-resolution limit, not a TTC mis-set.

Under the new 0.33 % gate this surfaces as CC_REGULAR **2024 +6.31 / 2025
+3.61 TWh** fails. The merit-ramp probe (run 118 deltas) is a Pareto
improvement (WH2 2025 +21.7 → +17.6 %, fills the cycling bands) but cannot
close it — the run-90 gas-price year-gradient means any year-uniform econ
raise that clears 2025 over-corrects 2023. The real levers (shrink/cheapen the
duct band toward physical; finer zones or the NP6-785-ER spatial overlay) are
parked on a data dependency.

### B3 — Scarcity price reproduced by a fitted, non-physical offset **[checked]**

`ordc_reliability_deployment_mw` is, by its own documentation, "**not** a
published ORDC parameter and **not** physically derived" — a flat MW offset
subtracted from reserves, "an explicit, scenario-adjustable calibration of
stress-year scarcity intensity." The 2023 sweep shows it is the dominant lever
on the price tail: 0 MW → MAE 30.1 (7 % gap closed); **2,500 MW → MAE 12.3
(74 % closed)**; 4,000 → 47.2 (overshoot). So the headline "2023 annual LMP
Δ vs DA −59 % → −9 %" improvement is largely this fitted knob, not mechanism.
Three honest caveats the audit endorses but flags:

- The knob is anchored to 2023 ECRS conservatism; 2024/2025 (genuinely less
  tight) are **under-served** by the same flat offset — a documented limitation
  a tightness-responsive offset would fix.
- The underlying reason it is needed is a **real reserves bug**: in the 181
  actual >$200 hours the perfect-foresight LP shows **median 8.6 GW of
  headroom** (it counts cold/slow/AS-held capacity as available), so the ORDC
  LOLP ≈ 0 exactly where it should bite. The offset papers over the
  perfect-commitment overstatement rather than fixing it.
- The gate metric — **monthly demand-weighted** LMP MAE within ±$1 — is
  forgiving (monthly averaging washes out hourly tail error), and the gated
  series is the energy-only LMP while the series *displayed against actuals* is
  the overlay (which contains the fitted offset). Hourly price correlation and
  the price *distribution* are not gated at all.

### B4 — Calibration governance: ratcheting toward a greedy local optimum

The "never regress a class vs the keeper, with signed-off exceptions" rule has
produced an accumulating set of "accepted, do-not-chase" structural fails
(CT carried −0.5 → −2.1 TWh to fix CC; PRB 2024 left lumpy; 2024 coal split
−9.3 %). Each step is individually well-reasoned, but the *sequence* is a
greedy hill-climb: run 115b's CC fix was bought by deepening CT, and the
result is locked in as the new floor. Several keeper knobs are also fitted at
the ~1 % sensitivity boundary — the PRB floor swings the 2023 coal split
across pass/fail between 0.71/0.73/0.74. An expert panel would ask for a
periodic **from-scratch global re-fit / sensitivity sweep** to confirm the
keeper is not a path-dependent local optimum, and would want the sigmoid
passthrough floors (0.73/0.63/0.675) tied to observed coal self-commitment
behavior rather than left as pure fit parameters.

### B5 — Structural LP gaps that bound backcast realism (mostly known)

- **No AS co-optimization / reserve withholding** in the LP — every MW is
  available for energy every hour. This is the root of the overstated ORDC
  headroom (B3) and why the reliability-deployment fudge is required. AS is
  bolted on only as an exogenous $/kW-yr stream for capacity economics.
- **pmin = 0 everywhere; no ramp constraints.** No thermal-driven negative
  prices, overnight troughs too shallow → biases the off-peak PDC and storage
  charging economics. The evening ramp scarcity that increasingly drives ERCOT
  prices cannot form.
- **Single deterministic weather/outage year per backcast year**, with
  smeared (expected-value) outages — under-samples the scarcity tail and the
  winter delivered-gas blowouts (gas is one uniform Henry Hub + basis price, so
  Winter-Storm-style fuel spikes don't reach the merit order).
- **Emissions — the model's stated end product — are never benchmarked.**
  CAMPD/eGRID CO2 actuals are already in the bundle (`campd.parquet`), but no
  total or per-class CO2 check exists in the live path. A volume split that
  passes by gas-over/coal-under compensation would not be caught.

---

## C. Severity-ranked findings

| # | Finding | Severity | Type |
|---|---|---|---|
| B1 | Overlay in-sample leakage; no statistical-mode/out-of-sample number; validated≠forecast dispatch | **Critical** | Validity of the skill claim |
| B2 | CC_REGULAR within-class shape (missed >90 % CF) + North/SC spatial misallocation | **High** | Open dispatch error |
| B3 | Scarcity price carried by a fitted non-physical offset; loose monthly LMP gate; ungated hourly price | **High** | Price/revenue credibility |
| B5d | Emissions never benchmarked (end product unchecked) | **High** | Missing gate |
| B4 | Greedy calibration ratchet; fitted sigmoid floors at the ~1 % pass/fail boundary | Med-High | Governance / robustness |
| B5a | No AS co-opt / reserve withholding (drives B3 headroom) | Medium | Structural |
| B5b | pmin=0, no ramps → off-peak PDC & storage economics | Medium | Structural |
| B5c | Single weather/outage year; uniform gas price (no winter fuel spike) | Medium | Structural |
| — | 7-zone reduction can't form binding intra-zonal pockets (B2 spatial root) | Medium | Topology |

---

## D. Recommended next tests (prioritized)

**D1 — Statistical-mode backcast (THE test; Phase 3).** Re-run 2023/24/25
with every calibration-only device off — statistical outages, trajectory gas
(no F923), class emission rates (no CEMS), no HSL rescale, no per-plant-year CF
overrides, **and the CT/reliability-deployment floors off**. Score on the same
0.33 %/0.5 % gate. The overlay-mode → statistical-mode gap per class *is* the
measured leakage and the forecast-error prior. Until this exists, no backcast
number should be quoted as evidence of forecast skill. *(Highest value, lowest
cost — the harness exists.)*

**D2 — Leave-one-overlay-out ablation.** Run the keeper with each overlay
removed individually and report the class-level Δ. Specifically quantify what
fraction of the CT_PEAKER and pocket-CC fit is the deployment floor vs the
merit order — the answer to "how much did we earn vs pin."

**D3 — Gate the operating-shape and emissions metrics, not just totals.**
(a) Promote `cf_emd` / the 5 %-band `[7b]` CF-distribution to a *gate* so a
class cannot pass on annual total while failing operating shape (catches B2).
(b) Convert the per-plant hourly Pearson-r / NRMSE from reported diagnostics
into **regression gates** seeded at best-achieved (fail on degradation).
(c) Add **CO2 total ±5 % and per-class ±7 %** vs CAMPD/eGRID — nearly free,
independent of the volume split (catches compensation).

**D4 — Fix-and-validate CC_REGULAR.** Apply the merit-ramp deltas + shrink the
CC duct band toward physical (~5 % of nameplate, ~1.4–1.6× incremental), sweep
across the full panel (watch Colorado Bend EC, which already over-runs the top
bins), validate on the 5 %-band `[7b]` and `cf_emd` before adopting. Land the
spatial axis by ingesting NP6-785-ER zonal/hub prices (enables the spatial
overlay) or by splitting the Valley/Permian pockets into finer zones.

**D5 — Proper scarcity-tail price validation.** Report top-100-hour price
contribution, hours >$200/$500/$1000 (model vs actual), and **load-weighted**
(not monthly-demand-weighted) average price — the quantity retirement/entry
economics actually consume. Report the ORDC-honest component and the
RTORDPA-offset component **separately**, and prototype a tightness-responsive
offset for 2024/2025.

**D6 — Out-of-sample year holdout.** Freeze the keeper parameterization on two
years and score the third untouched; or add **2022** (a structurally different,
high-price year, outside the current tuning loop) as a true holdout. All three
current years are inside the calibration loop, so none is a clean test.

**D7 — Reserve-headroom validation in stress hours.** Compare model
real-time headroom against ERCOT's actual physical responsive capability /
PRC in the 2023 >$200 hours. This quantifies how much of the price gap is the
perfect-commitment reserves bug (B3/B5a) vs the price mechanism, and tells you
whether the right fix is the AS/reserve constraint rather than a larger offset.

---

## E. Bottom line for an external reviewer

Run 115b is a **credible, well-documented annual-volume backcast** of ERCOT
2023–2025 and would pass a production-cost volume review on the large fuel
classes. What it has not yet earned is the right to be called a *forecast
prior*: the fit increasingly rests on CEMS-keyed overlays that (a) feed the
answer in and (b) vanish in forecast mode, and the experiment that would size
that dependence — the statistical-mode backcast — has not been run. The two
open dispatch problems (CC_REGULAR operating shape + spatial allocation) and
the fitted scarcity offset are honestly diagnosed but unresolved, and the
model's headline end-product — emissions — is not benchmarked at all. The work
to convert this from "strong backcast" to "validated forecast prior" is mostly
*measurement* (D1–D3, D6–D7), not new mechanism, and is the panel's clear
priority order.
