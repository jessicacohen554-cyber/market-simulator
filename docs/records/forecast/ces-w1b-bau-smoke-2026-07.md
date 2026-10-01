# CES W1-B — ERCOT + PJM Forecast-BAU Readiness Smoke (2026-07-17)

**Status:** COMPLETE. Both 2026-only BAU smokes solved in-session and gated with
`scripts/check_forecast_invariants.py`. **ERCOT: 14/14 PASS.** **PJM: 12 PASS /
1 FAIL (I7 reliability floor) / 1 WARN (I12, derivative)** — the I7 FAIL is a
structural adequacy-accounting gap diagnosed below (B1), reported per the W1-B
charter, not fixed. Plan: `docs/handoffs/national-ces-eac-premium-plan-2026-07.md`
(v2, §0 gap 4, §7, §8 W1-B). Branch: `claude/wave-1b-ces-eac-premium-p1stlx`.

PJM's first-ever forecast-mode run otherwise completes end-to-end on pure
ScenarioConfig defaults — every loader, per-ISO registry, and the P0→P1 solve
resolve cleanly for PJM 2026.

## 1. What ran

Four new scenario YAMLs (`configs/scenarios/`), modeled on `ercot_base.yaml` —
the ScenarioConfig defaults ARE the keeper-calibrated BAU, so each sets only
mode/iso/horizon plus `entry_screen_diagnostics: true` (required later for
premium attribution, plan §6.4):

| File | iso | Years | Purpose |
|---|---|---|---|
| `ercot_ces_base_2026_2050.yaml` | ERCOT | 2026–2050 | campaign BAU base (W4) |
| `pjm_ces_base_2026_2050.yaml` | PJM | 2026–2050 | campaign BAU base (W4) — first committed PJM forecast config |
| `ercot_ces_base_2026_smoke.yaml` | ERCOT | 2026 only | this smoke |
| `pjm_ces_base_2026_smoke.yaml` | PJM | 2026 only | this smoke |

Smoke invocations (two concurrent background jobs, CLAUDE.md rule 12; from the
repo root — `results/` is CWD-relative, `cache.py:26`):

```
cd /home/user/market-simulator
PYTHONPATH=/home/user/market-simulator .venv/bin/python -m market_sim.runner run \
    --config configs/scenarios/ercot_ces_base_2026_smoke.yaml
PYTHONPATH=/home/user/market-simulator .venv/bin/python -m market_sim.runner run \
    --config configs/scenarios/pjm_ces_base_2026_smoke.yaml
```

(`PYTHONPATH` matters — see B4. Wall/RSS below were measured by an in-process
wrapper reading `resource.getrusage` because `/usr/bin/time` is absent in the
session container; the runner itself was invoked exactly as above.)

Invariants gate, per completed cache:

```
.venv/bin/python scripts/check_forecast_invariants.py --run-dir results/ERCOT/6274b843c3a69772
.venv/bin/python scripts/check_forecast_invariants.py --run-dir results/PJM/4bcab95006e93a6b
```

## 2. Runs, timings, memory

Cache keys are the runner's own effective keys (logged at
`run_scenario_iso start:`, runner.py:435-440; they differ from hashing the raw
YAML because the runner applies `resolve_policy_bundle` + per-ISO
`default_scenario_overrides` before keying, runner.py:405-433 — ERCOT picks up
`scarcity_price_overlay: True` from `iso_configs.py:251-253`).

| | ERCOT 2026 | PJM 2026 |
|---|---|---|
| cache dir | `results/ERCOT/6274b843c3a69772` | `results/PJM/4bcab95006e93a6b` |
| artifacts | `year_2026.parquet`, `evolution_2026.json`, `config.yaml` | same |
| wall clock (process) | **172.7 s** | **380.4 s** |
| peak RSS | **3.63 GB** (3,632,684 KB) | **8.73 GB** (8,734,492 KB) |
| phase: data_prep | 1.7 s | 4.3 s |
| phase: solve_p0 | 128.5 s | 297.9 s |
| phase: markup | 3.4 s | 11.2 s |
| phase: solve_p1 | 23.1 s | 51.0 s |
| phase: results_write | 0.7 s | 1.0 s |
| fleet | 1,450 EIA-860 generators → 304 per-plant CAMPD bins (81.7 GW curated sheet) | 1,922 generators, synthesized per-plant bins (`pjm_fleet_binned.parquet`), 170.7 GW thermal |
| confirmed exits loaded | 2 (477 MW, both 2025 → removed from 2026 base fleet as backlog) | 8 (6,063 MW, all 2028–2030 → no 2026 effect) + 3 superseded plants suppressed |
| planned additions due 2026 | 24 units, 640 MW | 4 units, 903 MW |
| warnings | 1 (known plant-55098 nameplate reconciliation) | benign only (5 CC-plant capacity reconciliations, 14/1,922 eGRID fallback zones) |

Two concurrent single-year smokes peaked at ~12.4 GB combined on a 15 GB
container — fine for two, no headroom for a third (rule 12's cap holds).

## 3. Invariants (single-run I1–I14)

| Check | ERCOT | PJM | Detail (PJM) |
|---|---|---|---|
| I1 energy balance | PASS | PASS | max residual 1.2e-10 MW (ERCOT 5.8e-11) |
| I2 no NaN/inf | PASS | PASS | |
| I3 unserved/dump | PASS | PASS | |
| I4 capacity accounting | PASS | PASS | |
| I5 no retire-and-reenter | PASS | PASS | |
| I6 econ-retirement sanity | PASS | PASS | |
| I7 reliability floor | PASS | **FAIL** | 2026: accredited firm 143,332 < requirement 148,771 MW → **B1** |
| I8 planned-additions gating | PASS | PASS | |
| I9 storage integrity | PASS | PASS | |
| I10 RPS dual | PASS | PASS | no PJM RPS row by design (constants.py:3893-3895); dual 0.0 |
| I11 one-pass | PASS | PASS | P0=1, P1=1, P2=0 |
| I12 reserve-margin band | PASS | **WARN** | 2026: −12.6% vs band [13.8%, 28.7%] — same accounting as I7 (F4) |
| I13 cobweb | PASS | PASS | vacuous on one year |
| I14 price sanity | PASS | PASS | load-weighted price in [0.5×, 3.0×] CC-MC band, neg-price hours ≤ 10% |
| **exit code** | **0** (0 FAIL, 0 WARN) | **1** (1 FAIL, 1 WARN) | |

Single-year notes: I4-continuity/I5-cross-year/I10-oscillation/I13 are vacuous
with one ledger year, and I12 cannot FAIL (needs ≥3 consecutive out-of-band
years, checker :593-596). Year 1 does write a real `evolution_2026.json`
(base-fleet snapshot + solve_counts, runner.py:2079-2115), so the ledger checks
are evaluated against real data, not vacuously absent.

## 4. Blockers and findings

### B1 — PJM I7 FAIL: adequacy ledger omits PJM demand response and firm ties (STRUCTURAL, blocks plan §7 R4)

The model's own two sides of the PJM adequacy accounting disagree by 5,439 MW
in the 2026 base year:

- **Supply** (`accredited_firm_capacity_mw`, capacity.py:2602): thermal at the
  published PJM 2026/27 BRA ELCC class ratings
  (`THERMAL_ACCREDITATION_BASIS_BY_ISO["PJM"] = "elcc_class_rating"`,
  constants.py:3618-3642), wind 41% / solar 7.9% marginal ELCC, storage ELCC
  3,904 MW → **143,332 MW** (ledger `reserve_margin` −12.617% × peak).
- **Requirement** (`resolve_adequacy_requirement_mw`, capacity.py:835-880): the
  checker passes `year=None` (check_forecast_invariants.py:451) → fallback
  `gross peak × (1 + IRM) × ICAP→UCAP` = 164,027 × 1.178 × 0.7699
  (constants.py:3701-3704) = **148,771 MW**. The published-FPR path (0.9170)
  would be *higher* (150,413 MW), so the construction choice doesn't rescue it.
- **The gap:** `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO` has **no PJM entry**
  (constants.py:3665-3667, ERCOT-only; consumed via `.get(iso, 0.0)` at
  capacity.py:870) and `ADEQUACY_EXTERNAL_TIE_FIRM_MW` has **no PJM entry**
  (constants.py:3674-3676, ERCOT-only; consumed at capacity.py:2656). PJM's
  real RA construct clears several GW of demand response as capacity — more
  than the 5.4 GW shortfall — and the model credits none of it for PJM. The
  model is faithfully reproducing "PJM needs its load-side products to meet
  its requirement" and then omitting those products.

Consequences: year 1 never calls `evolve_fleet` (runner.py:735-757), so the
adequacy backstop (`resolve_reserve_margin_build_enabled`, capacity.py:2714 —
market-design-dependent default ON for PJM) can never act on the base year.
**Every PJM forecast bundle, single- or multi-year, will FAIL I7 on 2026 until
the adequacy side-registries gain cited PJM entries.** That makes plan §7 R4
("I1–I14 pass on fresh ERCOT+PJM BAU forecasts") currently unachievable for
PJM and is a blocking input to the W3-R go/no-go. Fix = data/constants intake
with primary citations (PJM BRA planning parameters: DR/load-management UCAP,
CIL firm-import treatment) — its own session; per rules 5/13 the values must be
published PJM parameters, never a number tuned to clear I7. Demand-path
context: model 2026 peak 164.0 GW is the 2024 metered peak grown on the mid
path (`DEMAND_GROWTH_RATES["PJM"]` near-term ~3.5%/yr); a softer path shrinks
but does not close the gap, and the missing DR term remains structural.

### B2 — F923 measured H1-2026 fuel costs leak into forecast mode (STRUCTURAL, both ISOs, rule-22 crossover hygiene)

`apply_plant_monthly_fuel_prices` gates only on
`year not in available_years(costs)` — no mode check (fuel.py:3973-3977) — and
`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet` now contains
**1,994 measured rows for 2026 (months 1–4)** (verified this session). With
`coal_plant_monthly_pricing: True` by default (scenarios.py:5030), both smokes
priced plant-months from measured H1-2026 delivered costs: **ERCOT 12
generators, PJM 51 generators** ("F923 fuel costs for 2026: … priced from their
own plant" in both run logs). The module docstring's premise that "the F923
lookup simply finds nothing in a forward year" (fuel.py:3515-3521) went stale
the moment 2026 data was intaken. This contradicts the forecast-mode
convention that overlays use no measured H1-2026 actuals (CLAUDE.md rule 22;
methodology spec §1.7) and quietly contaminates the crossover window's
forecast side. It also affects any ERCOT 2026+ forecast, including a regen of
`tests/golden/ercot_2026_2040.json` — a fresh golden solve may drift for a
data-intake reason, not a code change. Candidate fixes (owner decision, NOT
applied here): mode-gate the overlay to backcast, or clamp
`available_years` to `< START_YEAR` in forecast mode.

### B3 — `data/clean/` is derived and absent in fresh checkouts; confirmed-exits channel degrades to a warn-only no-op (OPERATIONAL, materially affects ERCOT)

`load_confirmed_exits` returns `[]` with only a WARNING when the clean
partition is missing or unimportable (confirmed_retirements.py:95-121 and
:206-210 for reversal suppression). ERCOT's 2026 base fleet **materially
depends** on it: both ERCOT confirmed exits (V H Braunig 1/2, plant 3612,
225 + 252 = 477 MW) carry `exit_year 2025` and are removed as backlog at fleet
build; without the partition the 2026 fleet silently gains 477 MW. PJM's 8
live exits are all 2028–2030 (zero 2026 effect, but multi-year runs need
them). Regenerate before any forecast run on a fresh checkout:
`PYTHONPATH=. .venv/bin/python scripts/data/curate_confirmed_retirements.py`.
Corollary: `cache_key()` hashes only the config, never data-file state
(cache.py:31-48), so a year cached before a data fix is silently reused —
delete `results/<ISO>/<key>/` after regenerating inputs (done this session).

### B4 — `scripts.lib.clean_io` import seam: the confirmed-exits channel only loads when the repo root is on `sys.path` (OPERATIONAL)

`src/market_sim/data/confirmed_retirements.py:95/:206` imports
`scripts.lib.clean_io` (a namespace package under the repo root, not part of
the installed `market_sim` package). `python -m market_sim.runner` from the
repo root works (CWD lands on `sys.path`); any other invocation shape — a
wrapper script elsewhere, an installed console script run from another CWD —
silently loses the channel with only the B3 warning. The first smoke attempt
this session hit exactly this (timing wrapper in the scratchpad →
`sys.path[0]` = scratchpad); both runs were redone with `PYTHONPATH` set and
stale caches deleted. Suggestion for a later session: fail loudly (or import
via an installed seam) when `confirmed_exits_enabled` is on in forecast mode
and the registry can't be read — a silent 477 MW fleet delta is exactly the
class of quiet degradation rule 27's spirit targets.

### F1 — `entry_screen_diagnostics` emits zero rows in a 2026-only run (EXPECTATION, not a defect)

The per-candidate ledger is built inside `evolve_fleet` step 5
(capacity.py:3371-3401) and year 1 is a base-fleet snapshot with no evolution
(runner.py:735-757), so the smokes validate that the flag **parses and keys
the cache** — nothing more. The diagnostic ledger the campaign's premium
attribution needs (plan §6.4) is first exercised by a ≥2-year run. Also note
the flag is **not cache-key-neutral** (absent from `_CACHE_KEY_OPTIONAL_FIELDS`,
scenarios.py:24-35): the campaign configs will never share caches with
flag-off runs. Keep it on consistently (as these YAMLs do).

### F2 — ERCOT scarcity overlay is OFF in the keeper-default BAU (CAMPAIGN flag, not a smoke issue)

The ERCOT ISOConfig override only sets the *eligibility* half
(`scarcity_price_overlay: True`, iso_configs.py:245-253 — "Still requires
scarcity_pricing_enabled (the master switch)"); the post-solve ORDC overlay
fires only when `scarcity_pricing_enabled` AND `scarcity_price_overlay` AND
not `energy_reserve_coopt` (runner.py:1715-1719). Defaults leave the master
switch False, so the 2026–2050 ERCOT campaign as configured would run its
retirement/entry/CCS screens on bare LP duals — the documented over-retirement
failure mode (runner.py:1700-1713; plan §7 R2, ERCOT over-retires ~15×). This
is the retirement-calibration lane's territory and the campaign is D9-gated on
it anyway; flag for the W3-R owner decision — do not silently enable gated
mechanisms in the BAU YAML (it would depart the keeper-calibrated defaults).

### F3 — PJM by-design zeros (context for interpreting campaign results)

Silent in a green run, all documented design choices, none failures: RGGI
carbon adder $0 (`CAP_AND_TRADE_PROGRAMS["PJM"].price_key=None`,
constants.py:2073-2085); no PJM RPS row → `rps_dual` 0.0 and no REC signal to
the entry screen (constants.py:3893-3895); LP VOLL = `iso_config.voll` = 2,000
$/MWh vs ERCOT 5,000 (iso_configs.py:736); no scarcity overlay
(capacity-market ISO — fixed-cost recovery via `MARKET_DESIGN` capacity
revenue); datacenter load block OFF by default (`datacenter_load_path: "off"`;
PJM anchors of mid = 30 GW by 2030 exist in `DATACENTER_ADDITIONS_MW`,
constants.py:846-853 — a live owner lever for the campaign).

### F4 — PJM I12 WARN is derivative of B1

Same ledger `reserve_margin` field (−12.6%) measured against the generic band;
no independent information. Resolves with B1.

### Known multi-year defects NOT exercised by a 2026-only smoke

BLK-8 (zero solar entry vs 25.1/13.1 GW actuals), BLK-9 (capacity payment
1.26–4.92× FOM → fossil economic exit impossible in capacity-market ISOs),
BLK-10 (backstop over-build) — `docs/gap-register-2026-07.md`; the campaign
stays gated on the §7 readiness criteria (D9) regardless of these smokes.

## 5. Acceptance vs the W1-B charter

- Four YAMLs committed; both 1-year BAU smokes ran in-session (concurrent,
  rule 12); invariants ran on both caches. ✅
- ERCOT: green end-to-end (14/14, 0 WARN). ✅
- PJM: completes end-to-end; **one structural FAIL (B1) precisely diagnosed
  and reported, not fixed** — per the charter's fix-forward line (config-level
  only). The PJM blocker list for W2/W3-R is: **B1** (blocks §7 R4), **B2**
  (owner decision, both ISOs), with B3/B4 as operational prerequisites for any
  runner of these configs. ✅
- Nothing in this smoke touches out-of-training years (2026 forecast-mode runs
  are unrestricted, rule 22) and no dashboard registration applies (forecast
  runs; rules 15/16 govern backcasts only).
