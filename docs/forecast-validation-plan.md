# Forecast Testing & Calibration Plan — Retirement and New Build

> **⚠️ SUPERSEDED — historical record only, not the live spec.**
> This document's 2018→2025 hindcast window and AEO2018 fuel-path design were
> **replaced 2026-07** by `docs/handoffs/forecast-validation-program-2026-07.md`,
> which is now the live capacity-hindcast design. The live plan initializes
> from the **EIA-860 2020 vintage**, solves **2021 / 2023 / 2024 / 2025** with a
> **2022 bridge year** (no solve — the one-pass evolution loop consumes 2021
> `prior_results` for both the 2022 and 2023 evolution steps), and uses
> **AEO2021** as the as-known-then fuel path, not AEO2018. Reasons for the
> change (no 2018 EIA-860 vintage on disk, demand profiles starting at 2021,
> etc.) are documented in that file's §1.1. The content below is retained
> unmodified as the historical original plan — do not treat it as current
> guidance; see the live doc for anything that conflicts with it.

**Purpose.** Backcast tuning validates *dispatch* against history with the
answer partially fed in (historic overlays). It says nothing about the
model's ability to forecast **retirements and new builds** — the capacity-
evolution loop is never exercised in a backcast year. This plan defines the
validation program for the forecast machinery, to be started once backcast
tuning reaches an acceptable state, plus a prompt pack of paste-ready Claude
Code session prompts for each step.

**Companion:** `docs/peer-review-2026-06.md` (finding IDs A*/B*/C* referenced
below).

---

## Design principles

1. **The capacity hindcast is the centerpiece.** Initialize the fleet as of a
   historical year (2018), run the model *forward* in pure forecast mode
   through 2025, and score predicted retirements/builds against what actually
   happened (EIA-860). This is the only test that exercises the
   retirement/new-entry screens out-of-sample.
2. **Separate machinery error from input error.** Every hindcast runs in two
   fuel variants: **realized fuel** (actual Henry Hub path 2018–2025 —
   isolates the capacity logic from fuel-forecast error) and **as-known-then
   fuel** (AEO2018 reference path — measures end-to-end skill). Score both;
   the gap between them is attributable to fuel inputs, not the model.
3. **Beat the baselines or it isn't skill.** Even ReEDS/IPM-class models show
   large hindcast errors; the defensible claim is "better than naive
   alternatives and inside the envelope of contemporaneous forecasts."
   Mandatory baselines: (a) frozen fleet (no retirements/builds),
   (b) announced-only (EIA-860 planned retirements/builds as known in 2018),
   (c) AEO2018 capacity projections for the region.
4. **Holdout discipline.** Tune capacity-evolution parameters on the
   2018→2022 window only; 2023–2025 outcomes are the untouched holdout. Never
   iterate parameters against the holdout; it gets scored once per
   parameterization freeze.
5. **Tolerances scale with horizon.** Year-1 errors should be small (the
   known pipeline dominates); year-7 errors are structurally larger. Score
   cumulative-to-year-N, not just terminal-year.

## Phase 0 — Gate: blocker fixes (do before any forecast run)

The peer review found defects that invalidate current forward trajectories.
Phase 0 is the P0 list from `peer-review-2026-06.md` §F: B1 (retirement
margin), B2 (eastern-ISO queue caps), C1 (demand growth gap), B8 (learning
exponent), A3 (daily-cycling wiring), B3 (vintage preservation), C8/C9 (PJM
forward inputs, explicit backcast flag), B10 (known-additions wiring — needed
because the hindcast's early years are pipeline-dominated).

**Exit criterion:** ERCOT and PJM 2026–2050 runs complete without error; a
2026-vs-2024-actual demand check passes; unit tests cover each fix.

> **Status (2026-06-09): ✅ complete.** All Phase-0 items (including B10)
> landed — see `CHANGELOG.md` for the item-by-item record. 2-year ERCOT and
> PJM forecast smoke runs complete; the full test suite covers each fix.
> Prompts P0.1–P0.5 below are retained for the historical record and as
> regression context; the program now starts at P1. Note for hindcast work:
> `ScenarioConfig.mode` now exists and cache keys rotated with it.

## Phase 1 — Forecast smoke tests & invariants

Build an automated invariant checker that runs after any forecast run and
fails loudly. Invariants (initial set):

- Unserved energy = 0 in all years except explicit scarcity tails; dump
  energy < 2 % of annual renewable potential.
- Reserve margin within [floor, floor + 15 pp] every year (no runaway
  surplus or deficit).
- No boom-bust sawtooth: per-tech annual builds must not alternate
  full-cap/zero in ≥3 consecutive year pairs (cobweb detector, B4).
- REC dual not oscillating: year-over-year |Δdual| < 50 % once RPS binds
  (B9 detector).
- Retirements monotone plausibility: no unit retires and re-enters; no
  single-year retirement > X GW (config-derived).
- Price sanity: annual load-weighted average within [0.5×, 3×] of fuel-cost-
  implied CC marginal cost; PDC monotone; negative-price hours bounded.
- Capacity accounting closes: fleet(N+1) = fleet(N) − retirements + builds,
  by fuel, exactly.
- Perturbation stability: ±5 % gas-price tweak changes cumulative 2035
  builds by < 25 % (cliff-edge detector).

## Phase 2 — Capacity hindcast 2018→2025 (the core test)

**2a. Harness.** New entry point (e.g. `scripts/run_capacity_hindcast.py`):
initialize the fleet from EIA-860 (2017 final + 2018 early-release), seed
`consecutive_loss_years` empty, known pipeline = EIA-860 2018-vintage
planned/under-construction (NOT today's knowledge — leakage), statistical
outages only, no historic overlays, weather year held at the model's standard
profile. Run ERCOT first, then PJM.

**2b. Actuals dataset.** Build `inputs/validation/capacity_actuals_{iso}.csv`
from EIA-860 2018–2025: every retirement (unit, fuel, MW, year) and every
addition (tech, MW, COD year, zone). This is the scoring target and lives in
the repo.

**2c. Scoring metrics.**

Retirement:
| Metric | Target (realized-fuel variant) |
|---|---|
| Cumulative GW retired by fuel, 2018→2025 | ±20 % per fuel; ±10 % total thermal |
| Timing: median \|model year − actual year\| matched at plant level | ≤ 1.5 yr |
| Unit-level recall, units > 300 MW that actually retired | ≥ 70 % |
| Unit-level false-retirement rate (model retires, reality didn't, by 2025) | ≤ 15 % of retired-GW |
| Survival-curve comparison (GW-weighted, by fuel) | visual + KS-stat reported |

New build:
| Metric | Target |
|---|---|
| Cumulative additions by tech, 2018→2025 | ±15 % for wind/solar/gas; storage ±25 % |
| Tech mix shares of total additions | Δ ≤ 5 pp per tech |
| Annual additions by tech | report-only (year-to-year is queue noise) |
| Zonal siting distribution (once B15/C4 fixed) | directional: rank correlation > 0 |

All metrics scored against the three baselines; the model must beat
frozen-fleet and announced-only on retirement recall and addition mix to
claim skill. Expect ERCOT solar/storage 2021–2025 to be the hardest test
(IRA mid-window) — that is the point.

**2d. Attribution runs.** When a metric fails, re-run with one mechanism
pinned to actuals at a time (retirements pinned, builds free; builds pinned,
retirements free) to localize which screen is wrong. The one-pass
architecture makes these cheap.

## Phase 3 — Statistical-mode dispatch backcast (out-of-sample dispatch)

Re-run the tuned 2023/2024/2025 backcasts with every calibration-only device
off: `outage_source="statistical"`, trajectory fuel prices (no F923), class
emission rates (no CEMS), no HSL rescale, no per-plant-year CF overrides.
Score on the same dashboard with the **statistical-mode bands** (volumes ±10 %
per major class, hourly-r regression gates relaxed by 0.05). This number —
not the overlay-mode number — is the dispatch-error prior for forecast years,
and it feeds the hindcast interpretation (Phase 2 errors include it).

## Phase 4 — Calibration & identifiability of capacity parameters

With the hindcast harness in place, tune on 2018→2022 only:

- Sweep: `retirement_years_{coal,gas_ct,gas_cc}`, FOM multipliers,
  `retirement_reserve_margin`, entry-margin scaling / build-lag params (post
  B4 fix), capacity-price curve shape (post B6).
- Latin-hypercube or coarse factorial; score every draw on the Phase 2
  metrics; report **identifiability**: which parameters the hindcast actually
  constrains (narrow posterior) vs which are flat (don't pretend to calibrate
  those — set them from literature and document).
- Freeze the parameterization; score the 2023–2025 holdout once; log the
  result in `docs/calibration-log.md` whatever it says.

## Phase 5 — Forward credibility cross-checks

For the frozen model, run 2026–2035 and compare against external references:
ERCOT CDR/LTRA reserve margins, EIA AEO2026 regional capacity, NREL Standard
Scenarios, announced interconnection-queue composition. Differences are not
failures — but each one gets a one-paragraph explanation (ours vs theirs,
why). Add the cobweb/equilibrium sizing run: one scenario with entry damping
disabled vs enabled to publish the myopia bias band (B4). Finally, run the
forecast as a small ensemble (3–5 weather/gas draws once Phase P3 of the
remediation roadmap lands) and report ranges, not point estimates, for
retirement and build trajectories.

---

# Prompt pack

Paste-ready prompts for Claude Code sessions. Run them in order; each assumes
the repo conventions in `claude.md` and references
`docs/peer-review-2026-06.md` (finding IDs). Keep one prompt per session so
diffs stay reviewable. Prompts marked ⛔ are gates — don't proceed past them
until green.

### P0.1 — Retirement margin fix (B1) ⛔

```
Fix the economic retirement screen in src/market_sim/model/capacity.py
(apply_economic_retirements, ~line 294): net_revenue currently sums
price × dispatch (gross energy revenue). Change it to inframarginal energy
margin: sum over hours of (price[z,t] − mc_base[g,t]) × dispatch[g,t], using
the same mc_base array the dispatch consumed (thread it in from the runner —
see runner.py where mc_base is built). Keep the attribute-revenue and
capacity-revenue terms as-is. Update model-methodology-spec.md §5.2 which
documents the same wrong formula. Add a unit test: a unit dispatching at a
price equal to its own MC must accumulate a loss year (margin 0 < FOM); a
unit with price = MC + FOM/MWh-equivalent must not. Then run one ERCOT
forecast year-pair and report how many GW of loss-year flags change vs the
old formula — I want the magnitude of the bug documented in the PR
description. Do not retune any thresholds in this session.
```

### P0.2 — Eastern-ISO entry wiring (B2, C8)

```
Two forecast-mode crashes to fix. (1) constants.py QUEUE_CAP_GW /
QUEUE_CAP_PER_TECH_GW only define ERCOT and CAISO; capacity.py:910 KeyErrors
for PJM/MISO/SPP/NYISO/NEISO, and the per-tech .get(iso, {}) silently yields
0-GW caps. Add cited entries for the five missing ISOs (PJM/MISO queue
throughput from recent LBNL queue reports / ISO planning docs; follow the
parameter-citation convention in docs/parameter-citations.md) and add a
config-time validation that raises if an ISO in iso_configs.py lacks queue
caps. (2) renewables.py RENEWABLE_INSTALLED_MW lacks PJM/MISO/SPP/NYISO/NEISO
entries → KeyError on a non-backcast PJM run; add cited entries. Acceptance:
`python -m market_sim run` for a 2-year PJM forecast config completes; a new
test asserts every registered ISO has queue caps and installed-MW entries.
```

### P0.3 — Demand growth gap + explicit mode flag (C1, C9)

```
(1) runner.py _scale_demand compounds growth over range(START_YEAR, year) but
base_demand is the weather_year (2024) actual load, so 2026 demand equals
2024 actuals — two growth years are dropped. Fix by compounding from
config.weather_year (forecast mode only; backcast must keep using the year's
actuals unscaled). Add a test pinning 2026 ERCOT demand = 2024 base ×
(1+g2024)(1+g2025) within float tolerance. (2) renewables.py:663-679 infers
backcast mode from `gas_price_override is not None` — a forecast sensitivity
that pins gas would silently flip the renewables loader into backcast mode.
Introduce an explicit ScenarioConfig.mode: "forecast"|"backcast" (default
forecast), set it in the backcast scripts, and replace all implicit
inferences (grep for gas_price_override used as a mode signal). Keep cache
keys stable for existing backcast bundles if possible; if not, say so in the
PR description.
```

### P0.4 — Learning exponent, vintage preservation, daily-cycling wiring (B8, B3, A3)

```
Three small verified fixes from docs/peer-review-2026-06.md:
(1) capacity.py wright_cost uses ratio**(-learning_rate); the retrofit path
(_adjust_retrofit_capex) and the constants' documented "%/doubling" semantics
use exponent = -log2(1-LR). Make wright_cost use -log2(1-LR), update its
docstring, add a test: LR=0.20, ratio=2 → cost × 0.80 exactly.
(2) aggregate_fleet (fleet.py ~838) builds bin representatives without
online_year (defaults 2000), which kills the CCS-retrofit remaining-life gate
(capacity.py:1129) and the local-build learning attribution
(runner.py:259-265). Preserve a capacity-weighted online_year through
aggregation and add a test that a fleet of 2020-vintage CCs aggregates to a
~2020-vintage bin.
(3) runner.py dispatch_kwargs never passes storage_daily_cycle_hours, so
ScenarioConfig.storage_daily_cycling is silently ignored in forecast mode
(the backcast script wires it; the runner doesn't). Wire it: when
config.storage_daily_cycling is True pass storage_daily_cycle_hours=24 to all
three solve_dispatch calls. Add a smoke test that the flag changes the
LP row count.
```

### P0.5 — Known-additions pipeline (B10) ⛔

```
runner.py:451 hard-codes planned_additions=[] so the EIA-860
planned/under-construction pipeline (spec §5.4) never enters capacity
evolution — the near-term forecast years have no committed builds. Wire it:
load EIA-860 proposed/under-construction units (status U/V/TS) with expected
online year for the running ISO (the renewables side already has an EIA-860
proposed-plant loader in renewables.py — reuse its parsing; thermal needs the
generator sheet), convert to Generator objects with correct fuel_type, zone
(use data/zone_assignment.py), and online year, and pass them into
evolve_fleet so step 3 applies them in the matching year. Gate behind
forecast mode. Acceptance: an ERCOT 2026–2030 run shows the known pipeline
appearing in the build log with EIA-860-traceable unit IDs, and a test
fixture with one fake planned unit lands in the right year. Do NOT include
projects beyond the data horizon; the economic screen owns those years.
```

### P1 — Forecast invariant checker

```
Create scripts/check_forecast_invariants.py: loads a completed forecast
scenario's cached parquet years (results/{iso}/{cache_key}/) and evaluates
the Phase 1 invariant list in docs/forecast-validation-plan.md (unserved
energy, dump share, reserve-margin band, cobweb detector on per-tech builds,
REC-dual oscillation, no retire-and-reenter, capacity accounting closure,
price sanity bands, PDC monotonicity). Output: one PASS/FAIL line per
invariant with the offending years/values, exit code nonzero on any FAIL.
Make the thresholds a dataclass at the top, not scattered literals. Add a
--perturb mode documentation stub (not implemented) describing the ±5% gas
stability check. Then run it on a fresh ERCOT 2026–2040 forecast and a PJM
2026–2040 forecast and report every failure with a one-line diagnosis each.
Do not fix model code in this session — findings only, written to
docs/forecast-invariant-findings.md.
```

### P2a — Hindcast harness ⛔

```
Build the capacity-hindcast harness per docs/forecast-validation-plan.md
Phase 2a. New script scripts/run_capacity_hindcast.py: arguments --iso
--start-year 2018 --end-year 2025 --fuel-variant {realized,asknown}.
It must (1) initialize the fleet from EIA-860 as of the start year — check
what 860 vintages exist under data/raw/; if 2017/2018 files are
absent, stop and list exactly what I need to download rather than
substituting today's fleet; (2) restrict the known pipeline to what EIA-860
reported as planned in the start-year vintage (no leakage from later
vintages); (3) use statistical outages, forecast-mode renewables (no HSL
rescale, no per-plant-year overrides), and for --fuel-variant realized, the
actual annual Henry Hub path 2018–2025 (add HISTORICAL entries with
citations) vs asknown, the AEO2018 reference path (add with citation);
(4) run the standard year loop with capacity evolution and cache results
under results/hindcast/. START_YEAR/END_YEAR are constants today — refactor
minimally so the year window is configurable per run without changing
forecast behavior (keep cache keys stable for existing runs). Smoke-test
2018→2020 ERCOT and report wall time and any crashes. Do not score anything
yet.
```

### P2b — Actuals dataset + scorer

```
Two deliverables. (1) Build inputs/validation/capacity_actuals_ercot.csv and
..._pjm.csv from EIA-860 retired/proposed schedules 2018–2025: columns
unit_id, plant_name, fuel_class (mapped to our taxonomy via
config/plant_taxonomy.py), capacity_mw, event {retired,added}, year, zone
(via data/zone_assignment.py). Document provenance at the top of each file
and note units >300 MW separately. (2) Create
scripts/score_capacity_hindcast.py: takes a hindcast cache dir + actuals CSV,
computes the Phase 2c metric table from docs/forecast-validation-plan.md
(cumulative GW by fuel ±20%, plant-level timing median ≤1.5yr via
greedy fuel+size matching, recall ≥70% for >300MW retirements,
false-retirement rate ≤15%, addition mix shares Δ≤5pp, plus the three
baselines: frozen fleet, announced-only from the 2018 vintage, and a stub
for AEO2018 totals I will supply). Emit a markdown report to
docs/hindcast-reports/ with a PASS/FAIL per metric and the baseline
comparison table. Unit-test the matcher on a synthetic 5-unit case.
```

### P2c — Run & interpret the hindcast ⛔

```
Run the ERCOT capacity hindcast 2018→2025 in both fuel variants (realized,
asknown) using scripts/run_capacity_hindcast.py, then score both with
scripts/score_capacity_hindcast.py against
inputs/validation/capacity_actuals_ercot.csv. Launch the two runs as
concurrent background jobs with separate --out-dirs per claude.md rule 11.
Produce docs/hindcast-reports/ercot-2018-2025-run1.md containing: the metric
table for both variants, the realized-vs-asknown gap (fuel-input
attribution), baseline comparisons, and a ranked list of the largest unit-
level misses (false retirements, missed retirements, missed build waves)
each with a one-paragraph mechanism hypothesis referencing the capacity.py
screen responsible. Do NOT tune any parameter in this session — diagnosis
only. If results are catastrophically off (e.g. zero retirements), check
first whether a Phase 0 fix regressed rather than inventing new mechanisms.
```

### P3 — Statistical-mode dispatch backcast

```
Run the out-of-sample dispatch experiment from
docs/forecast-validation-plan.md Phase 3: re-run the current best ERCOT
backcast years (2023, 2024, 2025 — same configs as the latest dashboard run)
but with every calibration-only overlay disabled: outage_source=statistical,
trajectory gas prices instead of F923 delivered, class-default emission
rates instead of CEMS, no HSL rescale, no per-plant-year CF overrides
(audit run_calibration_full.py and fleet.py for any other backcast-only
device and disable it too — list what you found and turned off). Run the
three years concurrently per claude.md rule 11. Score with the standard
calibration report and add the runs to the dashboard registry tagged
"statistical-mode". Then write docs/statistical-mode-backcast.md comparing
overlay-mode vs statistical-mode error per class and per metric — this gap
is our measured overlay-leakage and the dispatch-error prior for all
forecast years. No tuning in this session.
```

### P4 — Capacity-parameter sweep & identifiability

```
Using the hindcast harness, run a parameter sweep on the 2018→2022 window
ONLY (2023–2025 is a holdout — do not score it in this session). Sweep, via
the existing sweep machinery (config/scenarios.py): retirement_years_coal
{1,2}, retirement_years_gas_ct {1,2,3}, retirement_years_gas_cc {2,3,4},
retirement_fom_multiplier_coal {1.0,1.3,1.6}, retirement_reserve_margin
{0.10,0.15}, and the entry damping parameters added by the B4 fix if landed
(build-lag, margin scaling). Use mode: list with ~25 hand-paired draws, not
full factorial. Score every draw with score_capacity_hindcast.py
(realized-fuel variant), concurrent background jobs, separate out-dirs.
Deliver docs/hindcast-reports/identifiability.md: per-parameter sensitivity
of each Phase 2c metric, which parameters the data actually constrains vs
flat directions, and a recommended frozen parameterization with rationale.
Flag explicitly any parameter whose best-fit value is at the edge of its
swept range.
```

### P5 — Holdout scoring + forward cross-check

```
Two-part session. (1) Freeze the parameterization recommended in
docs/hindcast-reports/identifiability.md (commit the ScenarioConfig default
changes), then score the 2023–2025 holdout exactly once: extend the ERCOT
hindcast to 2025 with the frozen params and run the scorer on the holdout
window. Log the result in docs/calibration-log.md verbatim, pass or fail —
do not retune. (2) Run a frozen-model ERCOT 2026–2035 forecast and write
docs/forward-crosscheck-2026.md comparing: reserve margin vs the latest
ERCOT CDR, cumulative additions by tech vs the CDR interconnection queue
and NREL Standard Scenarios mid case, retirements vs announced ERCOT
retirements, with a one-paragraph our-view-vs-theirs explanation for each
material divergence (>15%). Use WebSearch to pull the current CDR figures
and cite them. End by listing which peer-review findings (docs/
peer-review-2026-06.md §F P1/P2 items) the divergences implicate.
```

### PM — Metrics upgrade (can run anytime; pairs with §D of the review)

```
Implement the recommended tolerance schedule from
docs/peer-review-2026-06.md §D.3 as a single shared evaluator. Extend
src/market_sim/results/calibration.py with a TOLERANCES table (one source of
truth) covering: per-class volume bands with the small-class rule (pass =
|err|≤5% OR (|miss|≤0.5 TWh AND |err|≤25%)), share Δ ≤1.5pp, fossil system
total ±2%, PDC P25/P50 and monthly off-peak average ±10%, load-weighted
average price (report-only flag until pseudo-ORDC lands), top-100-hour price
contribution (report-only), CO2 total ±5% and per-class ±7% vs CAMPD/eGRID,
hourly pearson-r/NRMSE regression gates seeded from the current best run's
values, and unserved-energy==0 as a hard gate. Wire this evaluator into
scripts/run_calibration_full.py (print PASS/FAIL summary) and
scripts/probes/_backcast_shell.py so the dashboard's pass logic reads the same
table (replace the inline SUM_TOL_* constants). Mark "ok" tier as explicitly
non-passing for sign-off. Add emissions actuals loading (CAMPD CO2 already
in the data layer; eGRID totals for the system check) — if an actuals file
is missing, the metric reports SKIPPED, never silently passes. Update
docs/calibration-log.md's targets section to match. Tests for the evaluator
on synthetic summaries covering each band edge.
```

---

## Sequencing summary

```
P0.1–P0.5 (gate) → P1 → P2a (gate) → P2b → P2c (gate) → P3
                                              ↓
                                   P4 (tune 2018–22) → P5 (holdout + forward)
PM (metrics upgrade): anytime after P0; before P3 ideally so the
statistical-mode runs are scored on the new bands.
```

Rough effort: P0 items are hours each; P2a is the only multi-day build;
P2c/P4 are compute-bound (run concurrent, per claude.md rule 11). The
program is designed so that every session produces a committed artifact
(fix + test, dataset, report) and no session both tunes and scores the same
window.
