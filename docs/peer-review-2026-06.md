# Third-Party Peer Review — LP Market Simulator (June 2026)

**Scope:** full-model design review as an external energy-modeling expert would
conduct it — LP formulation & pricing, the commitment heuristic, capacity
evolution (retirement / new entry), the data pipeline, and the backcast
evaluation methodology (metrics & tolerances). The review's frame of reference
is the model's stated end goal: a credible **2026–2050 forecasting model** of
prices, retirements and new builds.

**Method:** independent code reads of `model/`, `policy/`, `data/`, `config/`,
`runner.py`, `results/calibration.py`, `scripts/run_calibration_full.py`, the
dashboard pass logic, the latest backcast runs (61/62, PJM n6), and the
methodology spec. The five highest-severity code findings were verified
line-by-line (marked **[verified]**); other findings are standard peer-review
observations with file references.

---

## Executive summary

The backcast/dispatch side of this model is unusually strong for a screening
LP — degeneracy hygiene, per-plant CAMPD offer curves, measured zonal load
shares, vintage capacity ramps and citation discipline are all above the bar
most commercial-tool users clear. The model also documents its own
limitations honestly, which reviewers reward.

The forecast side is where an expert panel would push back, in three layers:

1. **Capacity-evolution defects that invalidate current retirement/build
   trajectories.** The economic retirement screen compares **gross** energy
   revenue (price × dispatch) to fixed cost — variable cost is never
   subtracted — so almost nothing can retire on economics. New entry crashes
   for every ISO except ERCOT/CAISO, values peakers at the unconditional mean
   price, and the CCS-retrofit screen is dead code on the default
   aggregation path. These are mostly small fixes, but until they land, no
   forward run's retirement or new-build output should be quoted.
2. **Price formation is structurally incomplete for an energy-only forecast.**
   No ORDC/scarcity adders (prices are bimodal: marginal cost or VOLL), no
   ancillary-services co-optimization or reserve withholding, no ramp
   constraints, and storage dispatches with full-year perfect foresight in
   forecast mode (the daily-cycling mitigation exists but is not wired into
   `runner.py`). Scarcity-hour revenue — the thing that decides peaker and
   storage entry/exit in ERCOT — is the least-modeled part of the system.
3. **Backcast skill is not yet evidence of forecast skill.** The calibrated
   backcasts lean on historic overlays (actual outages, delivered fuel,
   per-plant CEMS rates, HSL rescale) that feed part of the answer in. The
   missing experiment is a **statistical-mode backcast** (forecast machinery,
   historical year) and a **capacity hindcast** (start in ~2018, predict
   2018–2025 retirements/builds, score against EIA-860 actuals). The
   companion document `docs/forecast-validation-plan.md` lays out that
   program with a prompt pack.

On metrics/tolerances (§D): the ±5 % per-fuel volume band is industry-normal,
not too generous, for large classes. The generosity is elsewhere — the
1-TWh OR-escape for small classes, the ±10 % "ok" tier drifting into
acceptance, price exempted as "diagnostic only", emissions not benchmarked at
all, the capacity-factor diagnostic unused, and no thresholds on the hourly
shape metrics. Specific recommended bands are in §D.4.

---

## A. LP formulation, pricing & commitment

| # | Finding | Sev | Affects |
|---|---------|-----|---------|
| A1 | No scarcity pricing beyond a single VOLL step | High | Forecast + backcast tails |
| A2 | No AS co-optimization / reserve withholding | High | Both |
| A3 | Daily SOC cap built but not wired in `runner.py` **[verified]** | High | Forecast |
| A4 | One-pass commitment screen vs pre-decommitment prices | High | Both |
| A5 | Min-run filter drops short profitable runs | High | Both |
| A6 | Adequacy backstop over-restores, clips scarcity prices | Med | Backcast |
| A7 | Coal pin makes coal never-marginal in P2 | Med | Backcast |
| A8 | Worst-case startup markup for never-run units; no fixed point | Med | Backcast |
| A9 | pmin=0 everywhere → no thermal-driven negative prices | Med | Both |
| A10 | Symmetric static lossless TTCs, no flowgates | Med | Backcast |
| A11 | WECC import node uncorrelated with West-wide stress; free export sink | Med | CAISO |
| A12 | Duals read without optimality/dual-status check | Med | Backcast |
| A13 | No ramp constraints | Med | Forecast |
| A14 | Startup costs in prices but absent from objective/cost accounting | Low | Both |
| A15 | `thermal-cycling-adders.md` describes unimplemented config | Low | Docs |

**A1 — Scarcity pricing.** `dispatch.py:213,753` — slack is priced at a single
`voll`, so hourly prices are either the marginal bid or exactly VOLL. Real
ERCOT prices carry a *continuum* of ORDC adders ($100–$5,000) in tight-but-
served hours, and those hours dominate peaker/storage net revenue. The model
can only generate scarcity rent by literally shedding load, making entry/exit
economics a knife-edge function of the load/outage draw. This is the single
biggest threat to forecast credibility. LP-compatible fix: a multi-step
pseudo-ORDC — priced slack tranches per zone-hour (e.g. 3–5 reserve-margin
steps at rising prices below VOLL).

**A2 — Ancillary services.** No reserve variables or rows exist; every MW is
available for energy every hour. Real ISOs withhold ~6–10 % of online
capacity (raising tight-hour energy prices), and AS revenue is 10–30 % of
ERCOT battery net revenue today — yet the storage entry stack
(`storage.py:321-380`) values arbitrage + capacity only. A static per-zone
hourly reserve constraint would both shift the supply curve and give an AS
price proxy (its dual) for the storage value stack.

**A3 — Storage perfect foresight [verified].** `dispatch.py` implements
`storage_daily_cycle_hours` and `run_calibration_full.py` wires
`--storage-daily-cycling`, but `runner.py:361-379` (`dispatch_kwargs`) never
passes it — `ScenarioConfig.storage_daily_cycling` is silently ignored in
forecast mode. Every forecast battery co-optimizes against all 8,760 prices
including the Jan↔Dec cyclic wrap. Tolerable for 4-h Li-ion; badly wrong once
the endogenous build adds 8-h/LDES assets, where perfect foresight
over-flattens net load and suppresses the very spreads that justified entry.
One-line wiring fix plus a config consult.

**A4 — Commitment screen one-pass bias.** `commitment.py:279-378`. P1 prices
come from the fully-committed (most price-depressed) fleet; units failing the
startup-IRR screen at those prices are decommitted and P2 re-solves once.
Decommitment raises prices, under which some screened units were profitable —
a true UC finds that equilibrium; one pass systematically over-decommits, then
the adequacy backstop (A6) papers over the result. Add one screen-and-resolve
iteration or a committed-set convergence check.

**A5 — Min-run filter.** `commitment.py:366-371` discards any profitable run
shorter than `min_run_hours` instead of extending it to min-run and testing
total profitability (which is what a unit facing a 6-h super-peak does).
Biases CC/CT out of exactly the high-price hours that matter; the foregone
revenue then propagates into the retirement screen.

**A6–A8 — Backstop / coal pin / markup.** The backstop
(`commitment.py:469-484`) requires P2 to reproduce P1 *thermal* output (not
feasibility) and restores all decommitted units rather than the marginal MW,
manufacturing a vertical supply segment that clips scarcity prices. The coal
pin (`commitment.py:424-432`) caps coal at its P1 dispatch so coal can never
set price in P2 — off-peak prices biased up to the gas floor. The startup
markup (`commitment.py:201-208`) hands a unit with zero P0 runs the full
startup cost on a 1-hour amortization — the worst-case adder — a
self-reinforcing exclusion (idle peakers in reality bid aggressively to get
starts). Also `_month_bounds` hard-codes 2023 (`commitment.py:159`), which
misaligns months from March onward on a leap weather year (2024).

**A9 — No min-load floors.** CAMPD tranches all carry `pmin=0`; the
"committed" tranche backs down to zero when out of merit. No thermal-driven
negative prices (only the wind PTC produces them), no min-gen drag cost, and
overnight troughs too shallow — which feeds directly into storage charging
economics.

**A10–A11 — Transmission.** Single symmetric static `ttc_mw` per link, no
direction asymmetry (real ERCOT GTC export vs import limits differ ~2×), no
seasonal ratings, losses, or hurdle rates; zonal duals are congestion-only
LMPs compared against settlement prices that embed losses. Per-direction TTC
(`ttc_fwd`/`ttc_rev`) is a 5-line change in `build_variable_bounds`. CAISO's
WECC import tranches don't tighten during West-wide heat events (when CAISO
actually spikes) and the export sink absorbs 5 GW at $0.

**A12 — Dual hygiene.** `dispatch.py:978,1006-1036` checks only primal status
before reading `row_dual`; assert `kOptimal` model status, and pin the dual
sign convention with an analytic 2-generator unit test so a HiGHS upgrade
can't silently flip prices. Degenerate-basis duals (flat renewable-surplus
hours, vertical segments from A6/A7) mean PDC tails can shift across solver
versions — worth knowing when comparing runs.

**A13 — Ramps.** Hourly delta-P bounds are sparse, well-conditioned LP rows.
Ramp scarcity in the evening net-load peak is a growing real-world price
driver that the 2030s forecast cannot currently produce.

## B. Capacity evolution — retirement & new build

| # | Finding | Sev | Affects |
|---|---------|-----|---------|
| B1 | Retirement screen uses **gross** revenue — MC never subtracted **[verified]** | Critical | Forecast |
| B2 | New entry KeyErrors for PJM/MISO/SPP/NYISO/NEISO; per-tech caps default to 0 **[verified]** | High | Forecast |
| B3 | Re-aggregation resets `online_year`→2000: CCS retrofit dead code, learning attribution broken | High | Forecast |
| B4 | Myopic entry: prior-year prices, zero lead time, full-cap build at $1 margin (cobweb) | High | Forecast |
| B5 | "PDC" revenue is flat mean price × CF, zones equally weighted | High | Forecast |
| B6 | Capacity revenue: full net-CONE forever, thermal-only on entry side, 3 inconsistent models | High | Forecast |
| B7 | RPS eligibility sets disagree across modules; no ACP slack (infeasibility risk) | Med-High | Forecast |
| B8 | `wright_cost` exponent inconsistent with retrofit path & docs **[verified]** | Med-High | Forecast |
| B9 | Lagged REC dual sawtooth; nuclear/hydro/wind never retirement-screened | Med-High | Forecast |
| B10 | Known-additions pipeline hard-coded `[]` in `runner.py:451` | Med-High | Forecast |
| B11 | Reliability floor ignores storage/VRE ELCC, uses gross peak | Med | Forecast |
| B12 | 45Q triple-inconsistency (new-build vs retrofit vs dispatch MC); retrofitted units exempt from retirement | Med | Forecast |
| B13 | PTC/45V levelized over 30-yr life but pays 10 yrs (~$10/MWh over-subsidy); new nuclear gets no 45Y/48E | Med | Forecast |
| B14 | No AS revenue in retirement/entry economics (currently masked by B1's opposite bias) | Med | Forecast |
| B15 | All new thermal in one zone; entry valued at all-zone mean — zonal prices exist but no zonal entry signal | Med | Forecast |

**B1 [verified].** `capacity.py:294-297`:
`net_revenue = Σ price[z,t] × dispatch[g,t]` — gross energy revenue —
compared against FOM-only going-forward cost (`capacity.py:327-331`). The
correct metric is inframarginal rent, `Σ (price − mc) × dispatch`. As
written, a coal bin at 20 % CF and $35/MWh realized price shows ~$61k/MW-yr
"revenue" against a $52k GFC and survives even with near-zero true margin.
Only units that barely run can retire; the whole thermal fleet under-retires,
which suppresses prices and entry downstream. The spec (§5.2) repeats the
same formula, so this is a spec bug too. Fix: subtract the dispatch `mc_base`
hour-by-hour — one array pass. **Fix this before any other capacity-side
tuning; the per-fuel thresholds and coal 1.3× multiplier are decoration until
the quantity they gate is a margin.**

**B2 [verified].** `capacity.py:910` indexes `QUEUE_CAP_GW[iso]`;
`constants.py:725-728` defines only ERCOT and CAISO → PJM forward run dies in
year 2. Worse, `QUEUE_CAP_PER_TECH_GW.get(iso, {})` silently yields 0-GW
per-tech caps. Add eastern-ISO entries and raise at config time when an ISO
lacks queue data.

**B3.** `evolve_fleet` ends in `aggregate_fleet` (`capacity.py:1334`); bin
representatives default `online_year=2000` (`fleet.py:141,838-851`). In
`apply_ccs_retrofit` every aggregated gas-CC bin then fails the
remaining-life gate forever — §5.6 is dead code on the default path — and
`runner.py:259-265`'s `g.online_year == year` never matches, so local builds
never feed the Wright's-Law tracker. Preserve a capacity-weighted vintage
through aggregation.

**B4.** `capacity.py:982-1006`: any tech with margin > $0 builds its **full**
per-tech cap, online the same year, judged on last year's prices — a textbook
cobweb bounded only by the exogenous caps. Minimum credible upgrades:
(a) tech-specific build lags (decide N, online N+lag), (b) build quantity
scaled to margin — or iterate entry until margin ≈ 0 against a re-estimated
price curve, (c) 2–3-yr smoothed revenue expectations. Then publish one
comparison against an equilibrium benchmark to size the residual bias.

**B5.** `estimate_expected_revenue` (`capacity.py:708-736`) computes
`cf × prices.mean() × 8760` with all zones weighted equally — the docstring
and spec claim PDC weighting but the code doesn't do it. Peakers (CF 0.10)
are valued at the unconditional mean instead of top-decile prices;
wind/solar at the mean instead of their generation-weighted price, ignoring
exactly the solar-hour price depression the prior-year feedback exists to
capture. The hourly CF profiles already exist in the runner; pass them.
Dispatchables: `Σ max(0, p − mc)` or top-`cf×8760` PDC hours.

**B6.** `capacity_revenue_per_mw_yr` (`capacity.py:198-220`) pays every
PJM/NYISO/NEISO/CAISO thermal unit full net-CONE × UCAP every year regardless
of surplus (actual BRA clears ~10–150 % of net-CONE along the VRR curve), the
entry side credits it **only** to `gas_cc`, and storage uses a third, better
model (`net_cone × ELCC(duration) × (1 − pen)^1.5`, `storage.py:415-447`).
Unify on one function — net-CONE scaled by a VRR-like curve on ELCC-weighted
reserve margin — applied to retirement, all entrants, and storage. Without
this, PJM retirement forecasting has no equilibrating channel.

**B8 [verified].** `wright_cost` (`capacity.py:639`) uses
`ratio ** (-learning_rate)` (solar LR 0.20 → 13 %/doubling), while
`_adjust_retrofit_capex` (`capacity.py:1046-1048`) correctly uses
`-log2(1 − LR)` and the constants document per-doubling rates. New-build
capex declines ~35 % slower than documented. One-line fix; decide one
convention.

**B9.** The year-lagged REC dual (`runner.py:210-213`) is its own cobweb
(binding → full-cap clean build → dual collapses → entry stops → dual
spikes); damp with a 2–3-yr rolling dual. The attribute-revenue block inside
the retirement loop (`capacity.py:299-311`) can never fire (loop covers
`_THERMAL_FOM` fuels only), and nuclear/hydro/wind are never
retirement-screened at all — existing nuclear cannot economically retire even
when its ZEC expires, a first-order omission for NYISO/PJM.

**B10.** `runner.py:451` passes `planned_additions=[]` always; spec §5.4's
deterministic EIA-860 pipeline never enters. The near-term years — where a
forecast is most checkable — carry no committed builds unless baked into the
base CSV. Wire EIA-860 (the loader machinery exists on the renewables side)
or delete the mechanism and the spec claim.

**B11.** `capacity.py:344-361` + `runner.py:318`: floor =
(gross peak − nuclear − hydro) × 1.15 backed by thermal only. With ERCOT
storage at 17–45 GW, thermal alone must still cover 115 % of gross peak —
blocking retirements storage demonstrably enables, and inconsistent with the
ELCC machinery that already exists for storage entry. Use ELCC-weighted firm
capacity against net peak.

## C. Data pipeline & forecast inputs

| # | Finding | Sev | Affects |
|---|---------|-----|---------|
| C1 | 2026 demand = 2024 actuals — two growth years dropped **[verified]**; flat scalar growth freezes load shape | High | Forecast |
| C2 | Single weather year, no inter-annual variability or tail events; deterministic smeared outages under-sample scarcity | High | Forecast |
| C3 | Backcast/forecast outage asymmetry: calibration leans on realized outages → metrics overstate forecast skill | High | Forecast |
| C4 | All new ERCOT wind/solar piled into West zone with the incumbent fleet's CF profile; mean CF frozen to 2050 | High | Forecast |
| C5 | ERCOT 2023 HSL rescale is circular (targets set so delivered output lands on actuals) | High/Med | Backcast integrity |
| C6 | Henry Hub trajectories are eyeballed AEO chart reads (TODO unresolved); real-$ vintage mismatch (2024$ vs 2026$ anchor) | Med | Forecast |
| C7 | Basis frozen to 2050 (Waha −$0.50 forever); no winter delivered-gas blowouts or gas-electric coordination | Med | Both |
| C8 | PJM forward renewables KeyError (`RENEWABLE_INSTALLED_MW`); proposed-plant pipeline ERCOT-only, ~3 yrs deep | Med | Forecast |
| C9 | Backcast mode inferred from `gas_price_override is not None` — a pinned-gas forecast sensitivity silently flips the loader to backcast | Med | Forecast |
| C10 | Fleet never ages (`fleet.py:404` keys age & nuclear CF to `weather_year`): 2050 coal has 2024 availability, nuclear repeats 2024's realized outages forever | Med | Forecast |
| C11 | PJM interchange frozen at 2024 hourly pattern and grows with demand growth | Med | Forecast |
| C12 | TTCs/zonal load shares static to 2050 (no Permian/765 kV program; Dominion share frozen) | Med | Forecast |
| C13 | `hydro.py` monthly-budget module never called — hydro runs flat-out | Low/Med | PJM+, later ISOs |
| C14 | Vintage pinning (eGRID 2023 hardcoded; PJM CAMPD extract missing OH/IN/KY/WV/VA → partial outage overlay) | Low | Both |
| C15 | Silent data repair (unbounded interpolate/bfill/ffill, mean-padding, wrong-year file used on warning) | Low | Both |

**C1 [verified].** `runner.py:91-98`: `_scale_demand` compounds
`range(START_YEAR, year)` over `base_demand` = weather-year (2024) actuals,
so 2026 = 2024 load exactly (~10 % low on ERCOT's near-term path), and the
error compounds through 2050. Separately, growth is one scalar on all 8,760
hours: load factor frozen at 2024's, while the loads being added (data
centers: flat, high-LF; electrification: winter-peaking) change the shape
that drives scarcity hours, storage value and entry.

**C3 / C5 — the in-sample problem.** The headline backcast numbers are
achieved with realized outage windows, per-plant CEMS rates, delivered F923
fuel and an HSL rescale whose targets are explicitly set so delivered
renewable output lands on actuals (`renewables.py:136-144`). All defensible
*as calibration devices*, but they mean current error metrics measure data
plumbing, not forecast machinery. The statistical-mode backcast (no
overlays) is the missing experiment — it is Phase 3 of the validation plan.

**C6.** The most important forecast price input (gas) is an approximate chart
digitization flagged `TODO: verify against AEO Table 13`
(`constants.py:269-339`), in 2024$ while `REAL_DOLLAR_BASE_YEAR = 2026` —
a systematic ~4–5 % real understatement of fuel cost against capex in every
entry screen. AEO2026 is out; ingest the table and deflate consistently.

## D. Backcast metrics & tolerances — assessment

### D.1 What is actually in use (three layers)

1. **Formal framework** (`results/calibration.py`): ±5 % on generation mix
   per fuel, PDC P10/P50/P90/mean, average price, per-fuel CFs.
   **Test-only scaffolding** — invoked from `tests/` only; not wired into the
   live workflow; last logged run 2026-05-17 (FAIL, superseded).
2. **Live report** (`scripts/run_calibration_full.py`): rich diagnostics
   (CHP split, EIA-930 reconciliation, per-class vs 923, monthly bias,
   hourly r/NRMSE, 11-plant panel, per-plant CAMPD fit) — **zero pass/fail
   logic anywhere in 1,924 lines**.
3. **Dashboard** (`scripts/_backcast_shell.py:141,655`): the operative
   tolerance. Per class: **pass** = (|err| ≤ 5 % OR |miss| ≤ 1.0 TWh) AND
   |share Δ| ≤ 1.5 pp; **ok** = within 2× (≤10 % / 2 TWh / 3 pp). Heatmap
   deadband ±2 % per zone-month. LMP shown but labeled "Diagnostic only —
   not a calibration target". Emissions: not benchmarked anywhere current.
   CF diagnostic: never computed in the live path.

Current performance (Run-62, ERCOT): classes in tolerance 7/11 (2023), 9/11
(2024), 5/10 (2025); nuclear/wind/solar within ±2 % everywhere;
CT_PEAKER +38/+25/+78 % (structural, known); 2025 prices broken by the stale
storage fleet (fake load shed, diagnosed in `tuning-proposal-runs-63-65.md`).
PJM: 4–5/12 in tolerance, hourly r materially weaker (gas 0.74–0.80,
wind 0.40–0.80).

### D.2 Are the tolerances acceptable or too generous?

**The headline band is fine.** ±5 % per fuel class on annual volumes is the
standard target for production-cost backcasts (utility IRP validation and
ISO model benchmarking typically use ±3–5 % on dominant fuels); your large
classes (CC, nuclear, wind, solar) are being held to an industry-normal bar
and are passing it legitimately. The share-Δ ≤ 1.5 pp AND-condition is a
good design that most shops don't have.

**Where it is too generous:**

1. **The 1-TWh OR-escape on small classes.** A 0.12-TWh class can "pass" at
   −26 %. Acceptable for triage, not for sign-off: a class that is 25 % wrong
   is telling you something about offer curves or fuel costs even when it's
   small. Recommend: pass requires |err| ≤ 5 % **OR** (|miss| ≤ 0.5 TWh AND
   |err| ≤ 25 %).
2. **Tier creep.** "ok" (≤10 %/2 TWh/3 pp) has drifted from "triage color"
   to de-facto acceptance in session logs. Make "ok" explicitly non-passing
   for sign-off; a frozen calibration should count only "pass".
3. **Price exempted entirely.** Defensible *today* because the no-ORDC gap is
   structural, but a forecasting model whose product is prices cannot
   permanently exempt price. Split the metric: (a) **off-peak/mid-merit
   shape** — P25/P50 of the PDC and monthly off-peak averages within ±10 %
   (these are ORDC-free and test fuel + offer curves now); (b) **scarcity
   tail** — top-100-hour price contribution, reported and excluded from
   pass/fail until a pseudo-ORDC exists, then brought in at ±25 %;
   (c) load-weighted (not simple) average price, since that is what
   retirement economics consume.
4. **Emissions unbenchmarked.** CAMPD/eGRID CO2 actuals are already in the
   repo's data orbit; total and per-class CO2 at ±5–7 % is nearly free and is
   an independent check on the coal/gas split that volume metrics can pass by
   compensation.
5. **No thresholds on shape metrics.** Hourly r/NRMSE are
   direction-of-improvement only. Convert the best-achieved values into
   **regression gates** (fail if a tuning run degrades them): ERCOT gas
   r ≥ 0.97, coal r ≥ 0.85, NRMSE caps similarly set at best-achieved + small
   margin. They protect against the classic failure of per-class tuning that
   silently worsens timing.
6. **Zonal/congestion metrics absent from pass logic.** The zone-month
   heatmap exists; add a zonal price-spread check (model vs actual West-Hub
   basis, monthly) once price comes in — congestion realism is what the TTC
   work was for.
7. **The deeper generosity is in-sample scoring (C3/C5).** Whatever bands you
   choose, score them twice: overlay mode (plumbing) and statistical mode
   (forecast machinery). The second number is the one that predicts forecast
   error, and today it doesn't exist.

### D.3 Recommended tolerance schedule

| Metric | Sign-off band | Notes |
|---|---|---|
| Volume, class ≥ 5 TWh | ±5 % | unchanged |
| Volume, class < 5 TWh | ±5 % OR (≤0.5 TWh AND ≤25 %) | closes the escape hatch |
| Share Δ per class | ≤ 1.5 pp | unchanged, keep AND |
| Fossil system total | ±2 % | already met; pin it |
| PDC P25/P50, monthly off-peak avg | ±10 % | ORDC-free price shape — adopt now |
| Load-weighted annual avg price | report now; ±15 % after pseudo-ORDC | replaces "diagnostic only" |
| Top-100-hr price contribution | report-only → ±25 % post-ORDC | scarcity tail |
| CO2 total / per class | ±5 % / ±7 % | vs CAMPD+eGRID — adopt now |
| Hourly r (gas/coal), NRMSE | regression gates at best-achieved | fail on degradation |
| Unserved energy (backcast) | = 0 | hard gate |
| Statistical-mode backcast volumes | ±10 % per major class | the out-of-sample bar |

### D.4 One process fix

Wire a single pass/fail evaluator (extend `results/calibration.py`, which
already has the right structure) into `run_calibration_full.py` and the
dashboard so all three layers share one tolerance table defined in one place.
Today the formal framework, the report and the dashboard can disagree — and
do (±5 % vs ±2 % heatmap vs 5 %/1 TWh/1.5 pp summary).

## E. What is done well (keep, and say so to reviewers)

- Degeneracy hygiene: storage ε tiebreaker, dump-cost floor sized to dominate
  production credits (kills the curtail-and-collect-PTC exploit), explicit
  slack/dump instead of infeasibility.
- Correct cyclic SOC boundary, consistent end-of-hour indexing.
- Commitment screen margins use *base* MC against P1 prices — dodges the
  classic startup double-count.
- Vectorized kron/CSR matrix assembly; presolve-off rationale documented.
- Per-plant CAMPD offer curves with rising tranche ramps; PROMOD-grade.
- T&D loss investigation (BTM CHP mislabel) settled with an audit trail.
- Measured hourly zonal load shares; ERCOT TTCs from the SCED
  binding-constraint archive with an honest "not a calibration lever" note.
- EIA-860 vintage monthly capacity ramps for in-year builds.
- 534-parameter citation registry with CI enforcement.
- `max(EAC, REC)` non-stacking; RPS-as-constraint with dual-as-REC-price
  architecture; ITC/PTC applied at the correct layers.
- The storage entry value stack (duration-sized windows, ELCC by duration,
  saturation derate, per-chemistry learning) is more sophisticated than most
  screening models — generalize its capacity-price treatment to the rest of
  the fleet (B6) rather than dumbing it down.
- Honest limitation notes throughout (perfect-foresight docstring, WECC TODO,
  CT gap history in the calibration log).

## F. Prioritized remediation roadmap

**P0 — before quoting any forward run (small, verified fixes):**
1. B1 retirement margin (subtract `mc_base`) — also fix spec §5.2.
2. B2 queue caps for the five eastern ISOs + fail-loud config check.
3. C1 demand growth gap (compound from `weather_year`, or define base as
   START_YEAR-level explicitly).
4. B8 `wright_cost` exponent → `-log2(1−LR)`.
5. A3 wire `storage_daily_cycling` through `runner.py`.
6. B3 preserve vintage through aggregation.
7. C8 PJM `RENEWABLE_INSTALLED_MW` entries; C9 explicit backcast flag.

**P1 — structural price formation (medium effort, LP-compatible):**
pseudo-ORDC slack ladder (A1); static zone-hour reserve constraint (A2);
B5 PDC/margin-based entry revenue; B6 unified VRR-style capacity price;
B10 wire known additions; one commitment iteration (A4) + min-run extension
(A5); per-direction TTCs (A10).

**P2 — forecast-input credibility:**
demand shape decomposition (data-center/electrification adders on the base
shape); new-build renewable siting + profile decorrelation (C4); AEO2026 gas
ingest + deflator (C6); fleet aging unfrozen (C10); B9 nuclear/hydro in the
retirement screen with ZEC logic; B11 ELCC-based reliability floor.

**P3 — uncertainty:**
weather-year library (load/wind/solar/hydro re-simulated per draw), discrete
outage draws, winter gas-event scenario; run forecast as small ensembles
rather than a single deterministic path.

Validation of all of this — including the capacity hindcast that tests
retirement/new-build skill directly — is specified with a ready-to-run
prompt pack in `docs/forecast-validation-plan.md`.
