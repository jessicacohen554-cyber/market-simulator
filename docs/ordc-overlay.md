# ERCOT ORDC scarcity-pricing overlay

**Status:** implemented (post-solve overlay + forecast revenue wiring), default off
(`ScenarioConfig.scarcity_pricing_enabled`). ERCOT only.
**Code:** `src/market_sim/results/scarcity.py`, `scripts/derive_ordc_overlay.py`,
runner wiring in `src/market_sim/runner.py` (capacity-economics prices).
**Validated against:** `results/calibration/run92_kiamichi` vs
`data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`.

## Why

The model's purpose is forecasting emissions from dispatch + capacity expansion
out to 2050. Emissions = volumes x rates, and volumes are calibrated — but the
capacity-expansion loop retires and builds on *revenue*, and in energy-only
ERCOT a peaker or battery earns most of its annual energy margin in the top
~100-200 price hours. The dispatch model is a perfect-foresight LP whose price
is the demand-constraint dual with zero unserved energy, so it **structurally
cannot produce scarcity prices**: the 2023 backcast cleared 0 hours above $500
against 99-104 actual (calibration log, "ERCOT Runs 85-87" §D). ERCOT's real
price *is* energy + an ORDC reserve-scarcity adder computed outside the
dispatch optimization — so a post-solve overlay replicates actual price
formation rather than approximating it. The overlay owns the price tail and
scarcity revenue; the LP remains the validated volumes/emissions engine and is
byte-identical with the overlay on or off.

## The published mechanism (provenance)

ERCOT's real-time settlement price adds reserve price adders to the energy
LMP. The on-line adder (RTORPA) is produced by the Operating Reserve Demand
Curve. In force June 2014 - December 4, 2025; replaced by AS demand curves at
RTC+B go-live on 2025-12-05 (ERCOT news release 2025-12-05; market notice
M-F110525-04). Formula, from the ERCOT Other Binding Document *"Methodology
for Implementing Operating Reserve Demand Curve (ORDC) to Calculate Real-Time
Reserve Price Adder"* (NPRR568;
ercot.com/files/docs/2015/08/04/2.2_Other_Binding_Document_Methodology_Implementing_ORDC.pdf)
as restated in the *2024 Biennial ERCOT Report on the ORDC* (2024-10-31;
ercot.com/files/docs/2024/10/31/2024-biennial-ercot-report-on-the-ordc-20241031.pdf):

```
LOLP(R; mu, sigma) = 1                                   if R <= X
                   = 1 - NormCDF(R - X; mu_eff, sigma)   if R >  X
mu_eff             = mu + shift * sigma

RTOFFPA = 0.5 * (VOLL - lambda) * LOLP(RTOLCAP + RTOFFCAP; mu,   sigma)
RTORPA  = RTOFFPA
        + 0.5 * (VOLL - lambda) * LOLP(RTOLCAP;           mu/2, sigma/sqrt(2))
```

The operating hour is split into two 30-minute halves: off-line 30-minute
reserves (RTOFFCAP) only help in the second half, so they earn only the
full-hour term; the first-half curve carries half the reserve uncertainty
(mu/2, sigma/0.707 — Brownian half-horizon scaling). lambda is the system
lambda of the power-balance constraint; the protocol caps lambda + adders at
the system-wide offer cap, and LOLP is administratively 1.0 at or below the
minimum contingency level X, where the adder pins to VOLL - lambda.

### Parameter provenance (all are `ScenarioConfig` fields — a PUCT change is a scenario, not a code edit)

| Parameter | Field | Default | Source |
|---|---|---|---|
| VOLL / offer cap | `ordc_voll` | $5,000/MWh | PUCT Project 52631 (16 TAC 25.505 amendment adopted 2021-12-02, recodified 25.509), effective 2022-01-01; $9,000 pre-Uri — runnable scenario |
| Min contingency level X | `ordc_mcl_mw` | 3,000 MW | OBDRR038 / PUCT Project 52373 Phase I blueprint order (2021-12-16), effective 2022-01-01; 2,000 MW pre-Uri |
| LOLP curve shift | `ordc_lolp_shift_sigma` | 0.5 sigma | PUCT Project 48551 (2019-01-17): two 0.25-sigma rightward shifts, 2019-03-01 and 2020-03-01 (mean shift, **not** a sigma inflation) |
| Multi-step RTORPA floor | `ordc_multistep_floor` + `constants.ORDC_FLOOR_STEPS` | $20 at R<=6,500 MW; $10 at 6,500-7,000 MW | OBDRR048, PUCT-approved 2023-10-12, effective 2023-11-01 (market notice M-A101623-01); date-gated in backcasts |
| Reserve-error mu, sigma | `ordc_lolp_mu_mw` / `ordc_lolp_sigma_mw` / `ordc_lolp_params_path` | 0 / 1,400 MW flat (provisional — see below) | ERCOT NP6-576-ER "LOLP Distribution by Season and TOD Block" (report 13233): 4 seasons x 6 four-hour TOD blocks, refit quarterly on reserve-error history since nodal go-live |
| AS plan netting | `ordc_as_plan_mw` | 0 (see "AS netting") | IMM 2023 State of the Market Report: 2023 average total AS 8,100 MW |
| Reliability-deployment offset | `ordc_reliability_deployment_mw` | 0 (recommended ERCOT ~2,500; see "Reliability-deployment overlay") | NOT a published ORDC parameter — the RTORDPA analogue, calibrated to the 2023 stress year |

**The mu/sigma table — RESOLVED (2026-06-13).** ERCOT publishes the
seasonal/TOD-block reserve-error statistics in NP6-576-ER (ercot.com is
egress-blocked from this execution environment, so the user fetched the
2025-06-13 and 2025-09-12 postings of report 13233 directly). The converted
table is committed at `data/raw/_validation-source/ercot_ordc_lolp_params.csv`
(values are season-constant across TOD blocks in these vintages: summer
904/1333, fall 917/1340, winter 930/1351, spring 947/1368 MW μ/σ). Two
findings: (1) the published σ ≈ 1,332–1,368 MW lands within 5% of the
a-priori flat 1,400 MW default, validating the OBDRR048 floor-anchor bound
below; (2) **the published Average already embeds the PUCT-48551 0.5σ
administrative shift** — μ/σ is constant at ≈ 0.68 across all four seasons
(a raw meteorological mean would not track σ proportionally), so when
`ordc_lolp_params_path` points at this table, set `ordc_lolp_shift_sigma`
to **0** (the deriver's `--shift 0`); applying the default 0.5σ on top
double-shifts (2024 MAE degrades 7.4 → 8.5, past the ±$1 guard). With the
table + shift 0 on the run-97a keeper: 2023 MAE 32.1 → 27.8 (>$500 hours
0 → 16 vs 104 actual), 2024 7.4 → 8.0, 2025 2.2 → 2.2 — within noise of
the flat default, confirming σ was never the 2023 residual's driver (the
gap attribution below stands). Both series are committed in the keeper
bundle as `scarcity_np6shift0.parquet` (canonical published-data overlay)
and `scarcity_np6.parquet` (the double-shift sensitivity). Vintage caveat:
these are the Summer-2025→Spring-2026 statistics applied to a 2023-25
backcast — quarterly refits move slowly (summer μ 904 → 964 across one
refit), but pre-2025 vintages would be preferable if archived copies
surface. The flat 0/1,400 ScenarioConfig default is retained for
continuity; a forecast scenario wanting the published curve points
`ordc_lolp_params_path` at the CSV with `ordc_lolp_shift_sigma = 0`.

**2023-vintage retry (2026-07-02) — still blocked.** A fresh fetch attempt
for the table in force during calendar 2023 failed on every host: ercot.com
and mis.ercot.com (report 13233 listing) return HTTP 403 both through the
egress proxy and the external fetcher; the 2022/2024 Biennial ORDC report
PDFs (ercot.com and the PUCT Interchange mirror, Project 55999 item 75 /
Project 52933) and web.archive.org are equally denied. NP6-576-ER was
decommissioned at the RTC+B go-live (PR447-03), so pre-2025 postings exist
only in the MIS archive — a manual fetch (as done for the 2025 postings) is
the only remaining route. Per the no-tuning rule the flat 0/1,400 fallback
stays for keepers; σ is documented as within 5% of the published 2025
vintage and not the 2023 residual driver.

## Model mapping

### Reserves

```
R = sum_thermal(pmax x availability - dispatch)        # gas/coal/nuclear/oil
  + (storage power cap - discharge + charge)           # ESR telemetry convention
  + (renewable potential cf x cap - dispatch)          # curtailed headroom
  - ordc_as_plan_mw                                    # default 0, see below
```

* Thermal availability is the exact hourly array the LP solved against
  (WEFOR/POF, CAMPD historic outage overlay, derates). For persisted bundles
  it is reconstructed — not re-solved — through
  `run_year(..., fleet_only=True)` from the bundle's `meta.json`, and cached
  as `availability.parquet`.
* Hydro is excluded (energy-budget-limited; 552 MW in ERCOT — immaterial).
* Renewable curtailment headroom mirrors ERCOT's HSL-minus-output telemetry;
  it is ~0 in genuine scarcity hours (renewables run at potential) and only
  suppresses spurious adders in curtailment hours. In this LP it is small
  (mean ~260 MW) because the model curtails less than reality.

### AS netting — investigated and rejected as the default

The campaign brief proposed netting ERCOT's published AS plan out of reserves
(the energy-only LP doesn't withhold AS capacity from energy). Implemented and
tested (`--as-plan 8100`, the IMM 2023 average total AS). **Result: it
overshoots catastrophically** — netting 8,100 MW puts model reserves at or
below the MCL in 1,000+ hours of 2023 (vs 104 actual hours above $500),
2023 monthly LMP MAE 32.1 -> 512, and the 2024/2025 gates blow up (7.3 -> 100,
2.2 -> 43). The structural reason: ERCOT's published reserve inputs RTOLCAP /
RTOFFCAP **count AS-held capacity as reserves** (undeployed Reg/RRS/ECRS
headroom of on-line units is exactly what RTOLCAP measures), so subtracting
the AS plan from headroom double-counts scarcity. The default is therefore
`ordc_as_plan_mw = 0`. (Re-confirmed 2026-06-17 with the formulaic AS
requirement: netting ~5.8 GW still drives 2023 monthly MAE 32 -> 814 and fires
the adder in 3,300+ hours vs 181 actual. AS netting is the wrong lever.)

### On-line / off-line reserve split — implemented (2026-06-17)

The real overstatement is **perfect commitment**, not un-netted AS: the
energy-only LP counts a cold, slow-start unit it happened to leave idle as
fully available reserve. `reserve_headroom` now returns an **(online, offline)**
split (`results.scarcity`):

* **online (spinning)** — headroom on thermal units whose plant is running
  (plant-level, since per-plant binning splits a plant into tranches), plus
  storage and curtailed-renewable headroom;
* **offline (30-min non-spin)** — available capacity on *quick-start* units
  (gas CT / oil) whose plant is not running;
* a cold **slow-start** unit (coal / CC / steam / nuclear, idle) backs
  **neither** tier.

`ordc_adder` then evaluates the full-hour LOLP term on `online + offline` and
the first-half term on `online` alone (the published RTOLCAP / RTOFFCAP
structure), instead of the old RTOFFCAP = 0 shortcut. This is the
market-design-grounded replacement for the fitted RTORDPA offset and carries no
fitted constant.

**Validated on run 124 (all overlays off, offset 0):** the split moves 2023
from 2 -> 33 model hours >$200 (181 actual) and improves 2023 monthly LMP MAE
**32.3 -> 27.7**, with 2024/2025 ~neutral (7.8 -> 7.9, 2.3 -> 2.3). The online
reserve drops below the 6,500 MW floor in **178 hours ≈ the 181 actual >$200
hours**, so the split reproduces scarcity *incidence* correctly. It does **not**
fully close the 2023 magnitude gap (33 vs 181), and per Non-Negotiable Rule #1
that residual is **not** chased with an offset: its honest cause is that the
bang-bang LP never part-loads units to carry spinning reserve, so even the
online tier is generous. Closing it properly is **AS / reserve
co-optimization** in the LP (force units to part-load against a reserve
requirement) — the genuine next structural step, larger than this overlay.
**Implemented — see the next section.**

### Energy + operating-reserve co-optimization in the LP (`energy_reserve_coopt`, ERCOT)

**Status:** implemented, `ScenarioConfig.energy_reserve_coopt` (default off,
shared with the PJM co-optimization). The structural successor to the
post-solve overlay: instead of computing a reserve adder *after* an energy-only
solve, the published ORDC reserve demand curve enters the LP itself, so the
dispatch carries real spinning reserve and the energy LMP picks up scarcity
endogenously. This is ERCOT's own RTC+B design (co-optimized AS demand curves
in SCED, live 2025-12-05).

**Mechanism (reuses the existing co-optimization LP — `model.dispatch`).** The
LP already supports a per-zone upward-reserve variable `R[z,t]`, a shared-
headroom row `sum_{eligible g in z} P[g,t] + R[z,t] <= sum cap[g,t]`, a reserve-
balance row `sum_z R[z,t] + sum_k ORDC_k[t] >= requirement[t]`, and priced ORDC
shortfall steps, all gated on `reserve_requirement is not None`. The ERCOT
wiring (`scarcity.ercot_reserve_coopt_inputs` →
`scarcity.ercot_ordc_demand_steps`) supplies the three inputs:

* **reserve-eligible mask** — the same dispatchable thermal classes
  (`RESERVE_FUEL_TYPES`); wind/solar/hydro/imports hold nothing responsive.
* **VOLL-anchored ORDC demand steps** — the ORDC *is* a reserve demand curve:
  the marginal value of the R-th MW of reserve is `0.5 · VOLL · (LOLP_full(R) +
  LOLP_half(R))`, the same two half-hour LOLP terms as RTORPA, discretized into
  ascending shortfall-price bands (cheapest = highest-reserve band first). The
  OBDRR048 $20/$10 floor is applied (unconditionally — co-opt is primarily a
  forward/RTC+B mechanism, so the 2023 date-gating the overlay does is dropped).
* **flat requirement** at the curve's top (`mcl + mu_eff + 5σ`, where the price
  is ≈0). The hourly scarcity *incidence* comes from the hourly fleet
  availability in the shared-headroom RHS — a tight fleet clears reserve lower
  on the curve, at a higher price — not from a time-varying curve, so a
  seasonal/TOD `ordc_lolp_params_path` table is reduced to its mean.

**The VOLL-anchored vs (VOLL − λ) choice (the one modeling judgment).** The
legacy post-solve adder is `(VOLL − λ)·LOLP` because energy and reserve were
*not* co-optimized — the adder is what's *added* to an already-cleared energy
price. An LP objective coefficient must be constant, and λ is endogenous in
co-optimization, so the in-LP demand curve is **VOLL-anchored** (no λ
subtraction). This is the co-optimization-correct form and matches the
published RTC+B AS demand curves (fixed price-vs-MW schedules anchored at the
offer cap): the energy LMP the reserve dual lifts *already* carries λ, so the
cleared total reproduces the LMP + reserve-value the `(VOLL − λ)` overlay
approximated, without double-counting λ. The shared-headroom dual equals the
reserve clearing price in a binding hour, so the zone's energy LMP = energy MC +
reserve price = ERCOT's RTSPP — verified at LP scale by
`test_dispatch.test_reserve_scarcity_lifts_energy_lmp` ($20 MC + $1000 reserve →
$1020 LMP).

**Relationship to the overlay.** Co-opt **supersedes** `scarcity_pricing_
enabled`: when both the co-opt flag and the overlay are set, the runner/
calibration path uses the co-opt LMP (which already carries scarcity) and skips
the post-solve adder, so the price is never double-counted.

**GATED — not byte-identical.** Unlike the post-solve overlay (which writes only
new series and leaves dispatch/volumes/emissions untouched), co-optimization
**changes the dispatch**: reserve-eligible units part-load to hold headroom, so
volumes, emissions and the LP duals all move. It is therefore default-off and
the volume calibration must be re-run and re-gated before a co-opt keeper is
cut. The post-solve overlay remains the validated, volume-neutral price tail for
energy-only keepers; co-opt is the path for studying the reserve-carrying
dispatch and the RTC+B forward design.

**Remaining approximation:** the model omits Load Resources (~2-3 GW of
RRS/ECRS is load-side, not in the supply fleet), which the reserve
co-optimization would also carry.

### System lambda and the output series

lambda = the hourly demand-weighted system price (energy-balance duals), the
model analogue of ERCOT's system lambda. The adder is system-wide and is added
uniformly to every zone (in ERCOT the reserve price adder is a system-level
component of every settlement point price). The overlay is emitted as a
separate series — `scarcity.parquet` columns `reserves_mw, lolp,
scarcity_adder, lmp, lmp_scarcity` — next to the untouched energy-only LMP,
which the volume calibration gates remain defined on.
`analyze_lmp_residual.py --with-scarcity` reports the overlaid series. The
backcast dashboard's monthly-LMP panel now draws the overlaid series
(`lmp_scarcity`) as a clearly-labeled, display-only second line — "Model + ORDC
overlay" — beside the energy-only Model and actual DA/RT, with a per-year
energy-only→overlay monthly-MAE caption and a >$200/>$500 tail-hour table; the
energy-only LMP stays the gated calibration metric and its payload fields are
byte-identical (the overlay only adds parallel `lmpScar`/`ordc` keys).

**Dashboard annual Δ-vs-actual uses the overlay (not energy-only).** The actual
ERCOT DA/RT series the dashboard compares against *include* the ORDC reserve
adder, which the energy-only LP structurally cannot produce — so the displayed
model-vs-actual deltas (the scorecard "LMP Δ vs DA/RT", the per-year card
"annual Δ" badge, the monthly-LMP table Δ columns, and the LMP-alignment
diagnostics) are taken against the **ORDC-overlaid** price wherever a run
carries an overlay, falling back to energy-only only for runs/ISOs with none.
Comparing the energy-only price against scarcity-inclusive actuals was
apples-to-oranges and overstated the gap (e.g. run115b 2023 annual Δ vs DA
−59% energy-only → −9% overlay; 2024 −30% → −22%). This is a display change in
`scripts/probes/_backcast_shell.py` only: the energy-only series is still shown and
remains the gated metric, the overlay is never a gate, and no run payload
changed (the overlay numbers were already baked into the `lmpScar`/`ordc`
keys). The residual under-bias in the milder years (2024/2025) is the known
flat-reliability-deployment-offset limitation, not a measurement artifact.

## Pre-implementation diagnostic (the honesty gate)

Before any adder: is the model thin in the hours reality was thin? If not, the
LMP gap would be an availability/load-shape bug and a curve must not paper
over it. On run92_kiamichi 2023 (`derive_ordc_overlay.py --diagnostic`):

| model headroom (thermal+storage) | hours | mean residual (actual - model) |
|---|---|---|
| < 4 GW | 3 | +$2,181 |
| 4-6 GW | 29 | +$1,539 |
| 6-8 GW | 93 | +$860 |
| 8-10 GW | 240 | +$197 |
| 10-12 GW | 350 | +$67 |
| 12-15 GW | 747 | +$23 |
| 15-20 GW | 1,753 | +$6 |
| > 20 GW | 5,544 | -$1 |

Monotone, with the actual >=$200 hours sitting at the thin end (their median
headroom 8.1 GW vs 23.0 GW overall; 100 of 181 in August). Spearman
rho(headroom, residual) = -0.39 (-0.48 Jun-Sep). 2024/2025 show the same
monotone shape with much fatter tail-hour headroom (medians 10.4 / 16.1 GW) —
the published curve should and does rarely bind there. **Diagnostic passed;
the outage overlay / load shape is sound and the missing piece is the price
mechanism.**

## Validation (run92_kiamichi, defaults: VOLL 5000, X 3000, sigma 1400 flat, shift 0.5, floors on, AS netting 0)

Monthly LMP MAE is the gate metric (demand-weighted |model - actual RT| of
monthly means).

| year | MAE energy-only | MAE with overlay | gate | hours >$200 act / model / +overlay | hours >$500 act / model / +overlay | Jun-Sep $.h gap closed |
|---|---|---|---|---|---|---|
| 2023 | 32.1 | **28.0** | target <= ~15: **missed** | 181 / 0 / 31 | 104 / 0 / 15 | 12% |
| 2024 | 7.3 | **7.9** | within +$1: **holds** | 53 / 7 / 10 | 16 / 0 / 4 | ~0% |
| 2025 | 2.2 | **2.2** | within +$1: **holds** | 31 / 19 / 19 | 3 / 0 / 0 | ~0% |

Adder incidence: 2023 — 163 h above $1, 37 h above $100, max $3,131;
2024 — 28 h above $1; 2025 — 4 h above $1 (the curve indeed rarely binds in
the comfortable years). Volumes tripwire: the overlay writes only new files
(`availability.parquet`, `scarcity.parquet`); dispatch/system parquets,
`_session_score` and both calibration gates are untouched by construction
(verified: no tracked bundle file modified).

**Scenario sanity (pre-Uri VOLL $9,000, overlay re-run only):** 2023 tail
moves up as expected — mean adder $2.97 -> $5.37, max $3,131 -> $5,671, hours
>$500 15 -> 22, gap closure 12% -> 21%.

### Sensitivity (NOT a tuning menu — reported so the unverified sigma's leverage is visible)

2023 monthly MAE / 2024 / 2025, with AS netting 0:

| sigma | 2023 | 2024 | 2025 |
|---|---|---|---|
| 1,400 (default) | 28.0 | 7.9 | 2.2 |
| 2,800 | 11.1 | 7.9 | 2.4 |

sigma 2,800 would hit the 2023 target while holding the 2024/2025 gates — but
it contradicts the OBDRR048 floor anchor above, and adopting it because it
scores well is precisely the forbidden residual fit. The honest reading: with
defensible parameters the published formula closes ~12% of the 2023 summer
$.h gap and builds the deep tail (15 hours near the cap vs 0 before); the
remaining gap decomposes into (a) the LP's perfect-commitment headroom
overstating real-time on-line reserves in the $100-1,000 shoulder hours, (b)
the documented 2023 *artificial scarcity*: the IMM found ERCOT's conservative
ECRS deployment roughly doubled Jun-Dec 2023 real-time prices (>$12B; 2023
State of the Market Report) — that pricing flowed through reliability
deployments (RTORDPA) and reserve withholding that an ORDC-only overlay
correctly does not reproduce, and (c) the unverified current sigma (real
post-2022 summer values are plausibly larger than the 2019-anchored bound).
Getting NP6-576-ER is the highest-value follow-up; modeling RTORDPA/ECRS
deployment is out of scope.

## Forecast-mode revenue wiring (the capacity-expansion deliverable)

Audit result: forecast-mode economics consumed **raw LP duals** —
`runner.py` stashed `result.prices` into `prior_results["prices"]`, consumed
by `capacity.evolve_fleet` for the economic-retirement screen
(`apply_economic_retirements`: inframarginal margin `(price - mc) x
dispatch`), the new-entry screen (`apply_economic_new_entry` /
`estimate_expected_revenue`) and the CCS retrofit screen. With zero scarcity
rent in the duals, dispatchables that live on the tail (CT_PEAKER, storage)
under-earn -> over-retirement and under-build. **This was the over-retirement
bias, now fixed:** with `scarcity_pricing_enabled` (and ERCOT only), the
runner computes the adder from the solved year's headroom and hands
`prices + adder` to the capacity-economics path. Dispatch, persisted results
and emissions are untouched; capacity-market ISOs are untouched (they recover
fixed cost through `capacity_revenue_per_mw_yr`; PJM/CAISO revenue modules
are a different campaign).

Per-class energy revenue, run92_kiamichi backcast, energy-only -> with adder
($M, `derive_ordc_overlay.py --revenue-report`):

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| CT_PEAKER | 188 -> 346 (**+83%**) | 147 -> 196 (+33%) | 308 -> 309 (+0.2%) |
| STORAGE (discharge) | 31 -> 84 (**+168%**) | 40 -> 77 (+92%) | 233 -> 234 (+0.3%) |
| ST_GAS | 476 -> 693 (+46%) | 385 -> 418 (+9%) | 582 -> 583 (+0.1%) |
| CC_REGULAR | 3,375 -> 4,043 (+20%) | 3,094 -> 3,233 (+4%) | 4,947 -> 4,948 (+0.0%) |
| wind | 1,952 -> 2,124 (+9%) | 1,681 -> 1,744 (+4%) | 2,955 -> 2,956 (+0.0%) |

Direction sanity holds: peakers and storage move most (in relative terms), and
the adder revenue vanishes in the comfortable 2025 reserve year.

## Reliability-deployment overlay (RTORDPA analogue) — DEPRECATED

**Status (2026-06-17): SUPERSEDED by the on-line/off-line reserve split above.**
`ScenarioConfig.ordc_reliability_deployment_mw` was a flat, non-physical offset
**fitted to the 2023 LMP residual** (~2,500 MW). Per claude.md (no pinning the
backcast to actuals) it is no longer part of the default reserve computation;
it is retained only as a default-0, explicitly-labelled diagnostic probe that
still subtracts from the online reserve when set. The grounded mechanism (the
on-line/off-line split) now plays its role. The history below is kept for
context.

**Why it exists.** The published ORDC overlay above is parameter-honest and
therefore recovers only ~7% of the 2023 summer scarcity gap (2023 monthly LMP
MAE 32.5 → 30.1, 17 of 181 actual >$200 hours). The root cause is *not* the
formula — it is the reserve input: in the 181 actual >$200 hours of 2023 the
perfect-foresight LP shows **median 8.6 GW of reserve headroom** (it counts
cold/slow/AS-held capacity as available — the perfect-commitment overstatement
the AS-netting section flags). At that headroom the ORDC LOLP ≈ 0, so the adder
≈ 0 exactly where it should bite. Real 2023 scarcity was driven by ERCOT's
out-of-market reliability deployments and conservative ECRS commitment (the IMM
estimated this roughly doubled Jun–Dec 2023 RT prices, >$12B) — the **RTORDPA**
reliability-deployment adder, which an ORDC-only overlay correctly does not
reproduce.

**What it is — and the honesty boundary.** `ordc_reliability_deployment_mw` is
a flat MW offset subtracted from reserves before the ORDC curve is evaluated.
It is **not** a published ORDC parameter and **not** physically derived (the
physical reserve biases partly offset — perfect commitment overstates reserves,
omitted Load Resources understate them). It is an **explicit, scenario-
adjustable calibration of stress-year scarcity intensity**, kept deliberately
separate from the published ORDC formula (which stays untouched and honest), so
the provenance mirrors ERCOT's real price decomposition: RTORPA = published
formula; RTORDPA = discretionary deployment. The ORDC curve's nonlinearity
makes the offset **self-targeting** — it lifts the adder only when reserves are
already low (tight hours), so a slack year is ~unchanged. This is the lever a
forecast varies as a scenario ("2023 reserve conservatism recurs" vs "prices to
fundamentals").

**Calibration sweep (keeper `run115b`, dispatch byte-identical throughout — the
adder is a separate series and never gates volumes):**

| offset MW | 2023 MAE | 2023 hrs >$200 (act 181) | 2023 Jun–Sep gap closed | 2024 MAE | 2025 MAE |
|---|---|---|---|---|---|
| 0 (ORDC only) | 32.5 → 30.1 | 0 → 17 | 7% | 8.0 | 2.2 |
| 2,000 | 32.5 → 14.7 | — | — | 8.6 | 2.2 |
| **2,500 (recommended)** | 32.5 → **12.3** | 0 → **112** | **74%** | 8.8 | 2.2 |
| 3,000 | 32.5 → 16.1 | 0 → 184 | — | 9.0 | 2.1 |
| 4,000 | 32.5 → 47.2 | overshoot | — | 8.7 | 2.1 |
| 8,100 (full AS plan) | → 512 | catastrophic | — | blows up | blows up |

At 2,500 MW the 2023 stress year is reproduced far more faithfully under its own
market design; 2024/2025 (genuinely less tight) lift modestly (10 of 53 and 1 of
31 tail hours) — a flat offset anchored to 2023 under-serves the milder years, a
documented limitation a tightness-responsive offset would refine. The scarcity
series is committed as `scarcity_reldeploy2500.parquet` alongside the canonical
`scarcity.parquet` (ORDC-only) and the `scarcity_np6shift0.parquet` sensitivity.

**Recalibration on the AS-aware keeper (run124, 2026-06-17).** The 2,500 MW
recommended offset is calibrated to a keeper *without* the measured storage-AS
commitment. On run124 (`--storage-as-commitment`), the AS reservation already
caps the battery peak dump and so tightens peak-hour reserves on its own,
supplying ~1 GW-equivalent of the discretionary reliability tightness the offset
used to carry — so **2,500 MW now overshoots** (2023 hours >$200 220 vs actual
181; 2024/2025 MAE degrade to 9.9 / 7.1). Re-swept on run124, the offset that
reproduces the run115b "2,500 MW" outcome (2023 MAE ~12.5, ~120 of 181 tail
hours, 2024 within ~±$1) is **~1,500 MW**, committed as
`scarcity_reldeploy1500.parquet` in the run124 bundle (the run124-appropriate
stress series). This is an interaction between two display-only levers; it never
gates volumes. See `docs/lmp-decomposition-2026-06.md`.

**Capacity-economics effect (net revenue $/kW-yr vs the going-forward retirement
bar, ORDC-only → +reliability-deployment):** 2023 ST_GAS 21 → **127** (bar 35:
retire → KEEP), COAL_PRB 22 → **143** (bar 52: retire → KEEP), CT_PEAKER 12 →
**109**. The stress year now keeps the marginal units it should — see the
steam-gas screen note below.

### Market-design regime switch (containing the erroneous 2023 design)

The reliability-deployment offset is calibrated to the 2023 ECRS-conservatism /
RTORDPA reserve withholding — a design the IMM judged erroneous and that ERCOT
reformed at **RTC+B go-live (2025-12-05)**, when ORDC reserve adders were
replaced by co-optimized AS demand curves. So it must not be carried silently
into a forecast. `ScenarioConfig.ercot_market_design` (`"auto"` / `"ordc"` /
`"rtcb"`) selects the regime, and `scarcity.ercot_market_regime(year, config)`
/ `effective_reliability_deployment_mw(year, config)` apply it:

- **ORDC regime** (auto: years ≤ 2025): the RTORDPA offset is
  `ordc_reliability_deployment_mw` — so the 2023 backcast is reproduced under
  its own design (MAE 32.5 → 12.3).
- **RTC+B regime** (auto: years ≥ 2026, the forecast): the offset is
  `rtcb_reliability_deployment_mw`, **default 0** — forward scarcity prices to
  fundamentals under the reformed design. A scenario can raise it to model
  "2023-style conservatism recurs." The ORDC overlay formula itself stays the
  first-order representation of RTC+B scarcity (ASDCs are VOLL-anchored and
  ORDC-shaped); only the discretionary reliability-deployment component is
  regime-gated. This is what separates the 2023 backcast design from the
  forward design rather than conflating them in one year-agnostic knob.

### Steam-gas retirement screen (companion fix)

Legacy gas steam carries `fuel_type = "gas_st"`, which was **absent from
`capacity._THERMAL_FOM` = {gas_cc, gas_ct, coal}** — so `apply_economic_
retirements` skipped every steam-gas unit and old steam gas could **never**
retire on economics, regardless of revenue. `gas_st` is now screened
(`fixed_om_gas_st = 35 $/kW-yr`, `retirement_years_gas_st = 2`, multiplier 1.0).
This is what makes the reliability-deployment revenue actionable: with realistic
stress-year scarcity, a screened steam unit's loss counter resets in a tight
year and it is kept, rather than (previously) being immortal or (without the
scarcity fix) spuriously retired.

## Ancillary-service (AS) revenue in the capacity economics

**Status:** implemented, `ScenarioConfig.as_revenue_enabled` (default off,
ERCOT-only) + `as_revenue_multiplier` scenario knob. Code:
`src/market_sim/model/ancillary.py`, credited in `capacity.apply_economic_
retirements` / `apply_economic_new_entry` and `storage.apply_storage_new_entry`.

**Why.** ERCOT's energy-only design pays no capacity revenue, but resources
earn material AS income (Reg-Up/Down, RRS, ECRS, Non-Spin) the energy-only LP
cannot produce. In 2023 AS was **~85% of ERCOT battery revenue** (~$169/kW-yr
of a ~$196/kW total; IMM 2023 SOM / Modo Energy). Omitting it undervalues
storage ~6× in the entry screen (its stack was energy arbitrage + capacity
value, and capacity value is 0 in ERCOT) and makes tail thermal under-earn —
over-retirement and under-build. This is **not** an AS co-optimization (out of
scope); it is an exogenous calibrated $/kW-yr stream, the AS analogue of the
scarcity overlay.

**Rates and saturation.** Base $/kW-yr by tech (`constants.ERCOT_AS_REVENUE_
PER_KW_YR`: storage 169, gas_ct 22, gas_st 15, gas_cc 8) at the 2023 ~4 GW
calibration point, scaled by `as_revenue_multiplier` and a **saturation**
factor — AS is a small, quickly-saturated market, so per-kW revenue falls as
the AS-eligible (mostly storage) fleet grows: `(ref_gw / max(storage_gw,
ref_gw)) ** 2.5`. Calibrated to reproduce the observed crash:

| storage fleet | model storage AS $/kW-yr | observed (Modo) |
|---|---|---|
| 4 GW (2023) | 169 | ~169 |
| 6.5 GW (2024) | 50 | ~40–45 |
| 10 GW (2025) | 17 | ~15–20 |
| 16 GW | 5 | (collapsing — AS −90% 2023→2025) |

The saturation is what stops a forecast over-building storage forever on a
static AS rate. The storage-entry screen sees the rate at the prior-year
fleet's penetration; the thermal screens take the storage fleet through
`evolve_fleet` (`prior_results["storage_power_mw"]`).

## Scope notes

* **RTORDPA** (reliability deployment price adder — RUC/ERS/ECRS-deployment
  pricing) is a separate, non-ORDC adder and is not modeled. Material in 2023
  (see above).
* **RTC+B** (2025-12-05) replaced ORDC adders with AS demand curves inside
  co-optimized SCED; ASDCs remain VOLL-anchored with ORDC-like shapes, so for
  forward years this overlay is the right first-order representation of
  scarcity pricing until an AS co-optimization module exists.
* **PJM/CAISO out of scope** — capacity-market / RA revenue modules, different
  campaign.
* The overlay never enters the LP objective or constraints. `voll`
  (ScenarioConfig tier 0) remains the LP's slack penalty; `ordc_voll` is the
  pricing-rule VOLL. They coincide at $5,000 today but are deliberately
  separate knobs.

## How to run

```bash
# Overlay + report on a solved bundle (post-solve only, no LP):
python scripts/derive_ordc_overlay.py results/calibration/run92_kiamichi --revenue-report

# Pre-adder honesty diagnostic:
python scripts/derive_ordc_overlay.py results/calibration/run92_kiamichi --diagnostic

# Scenario: pre-Uri cap
python scripts/derive_ordc_overlay.py results/calibration/run92_kiamichi --voll 9000 --mcl 2000 --shift 0 --tag preuri

# Tail localization with the overlay applied:
python scripts/analyze_lmp_residual.py results/calibration/run92_kiamichi --months 6 7 8 9 --with-scarcity
```
