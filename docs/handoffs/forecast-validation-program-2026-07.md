# Forecast Validation Program — 2026-07 (W0-P4 design)

> **⚠️ ARCHIVED (2026-07-17) — machinery delivered.** The invariant suite (I1–I14 +
> P1–P3), evolution ledger, capacity-hindcast harness/scorer, golden bands, and the
> forecast-validation dashboard page this doc designed are all landed (§6).
> Coordination of forecast validation now lives in
> `docs/forecast-development-plan-2026-07.md` (tier ladder §2, rubric charter §3).
> The §1.4 band tables and §3.4 calibration-complete checklist remain citable; do not
> launch sessions from §4.

**Produced by:** W0-P4 (Fable planning session, `docs/fable-prompt-pack-2026-07.md`), 2026-07-05.
**Consumes:** `docs/fable-repo-audit-2026-07.md` §F (TC-3) / §J-T1, `docs/forecast-validation-plan.md`,
`docs/model-audit-prompt-pack-2026-06.md` (PP-0.1/0.2/0.3), `docs/out-of-sample-results-2026-07.md`,
`docs/handoffs/holdout-policy-memo-2026-07.md`, `docs/handoffs/co2-keeper-regate-2026-07-05.md`.
**Consumed by:** W2-P5 (invariants + capacity-hindcast build) and W3-P1 (statmode runs) — complete
implementation prompts in §4. **This session implemented nothing and ran no solve.**

Already delivered elsewhere — NOT in scope here: the sensitivity tornado and the MIP-UC
cross-benchmark (`scripts/run_sensitivity_tornado.py`, `docs/handoffs/diagnostics-tornado-mip-2026-07-04.md`).

---

## 0. Status snapshot (every claim re-verified on disk, 2026-07-05)

**Superseded note (re-verified again on disk, 2026-07-06):** every row below was accurate
*at the 2026-07-05 planning cut*, before the W2-P5/W3-P1 implementation sessions this doc
itself commissioned (§4) actually ran. §6 records what those sessions landed; this table is
kept as the "before" picture but the rows that §6 overtook are annotated in place rather than
silently left to contradict §6.

| Item | State |
|---|---|
| Capacity hindcast | ~~**Never built.**~~ **Built and run** (§6): `scripts/run_capacity_hindcast.py`, `scripts/score_capacity_hindcast.py`, `scripts/build_capacity_actuals.py`, `scripts/register_hindcast.py` all exist; `docs/hindcast-reports/` holds ERCOT + PJM realized/asknown runs (plus later `-s2`/`-s3` re-runs from the Stage-2/3 revenue-side fix, `docs/handoffs/fom-scarcity-joint-protocol-2026-07-05-stage2.md`), registered under `results/hindcast/` and `frontend/data/hindcast/`. |
| Forecast invariant checker | ~~**Absent.**~~ **Landed** (§6): `scripts/check_forecast_invariants.py` (29KB, I1-I14 + P1-P3) exists on disk and is wired into `.github/workflows/forecast-invariants.yml`. |
| Forecast e2e coverage | ~~**Zero.**~~ **Closed** (§6): `tests/test_forecast_invariants.py` (not a separate `test_forecast_e2e.py` as originally named in §2.4 — folded into the same file) has 34 fast invariant-logic cases plus `test_real_forecast_invariants_pass` (`@pytest.mark.slow`, `RUN_SLOW_FORECAST=1`, a real 3-year ERCOT HiGHS solve) — the first real-LP exercise of the evolution loop, closing TC-3. `test_runner.py`'s mocked tests are unchanged. |
| Statistical-mode (D-7) backcast | REFRESHED 2026-07-05 (W3-P1), table in §5. **Stale as of 2026-07-06:** `frontend/data/backcast/keepers.json` now shows every ISO except CAISO re-gated again since this refresh (ERCOT/NEISO/MISO/NYISO 2026-07-06, PJM 2026-07-05) — the run ids this row and §5 cite (`nyiso41_hubprices`, `neiso_ctscrub`, etc.) are no longer the current keeper bundles. Per the doc's own standing rule (§3.2, "D-7 is keeper-relative"), a fresh D-7 refresh is now owed and has not been done in this doc. |
| Keepers | ~~All six dated 2026-07-03~~ **Only CAISO still is** (`2026-07-03-caiso-51-firm-base`). ERCOT, PJM, NYISO, NEISO, MISO have all been re-gated since (`frontend/data/backcast/keepers.json`: ERCOT `2026-07-06-ercot34-stage4-overlay-off`, PJM `2026-07-05-pjm-77-ct-relfloor`, NYISO `2026-07-06-nyiso-53-li-tsl`, NEISO `2026-07-06-neiso-49-stgas-netload`, MISO `2026-07-06-miso-42-coal-econ-ablation`). The NYISO re-gate this row flagged as "pending" has happened (nyiso-41 → nyiso-53-li-tsl); see `docs/handoffs/co2-keeper-regate-2026-07-05.md` for the resolution. |
| Holdouts | 2022 + H1-2026 fully quarantined (rule 22); `calibration-complete.json` `complete: {}` — still true as of 2026-07-06. ERCOT+PJM holdout *source data* intake landed 2026-07-04 under explicit owner authorization; CAISO/MISO/NYISO/NEISO zero holdout intake. **Update 2026-07-11: no longer current.** NEISO was declared complete 2026-07-07 (keeper `2026-07-08-neiso-54-steamgas-ct`, memo `docs/handoffs/neiso-calibration-complete-memo-2026-07.md`) and its 2019 + H1-2026 locked-test one-shot has been scored once (frozen `neiso-53` config, `2026-07-07-neiso53-winter-fuelsec-coldsnap`) and stands per rule 22 — not re-scored for neiso-54. The other five ISOs remain undeclared as of this update. |
| CI | **W1-P1 landed** (`.github/workflows/ci.yml`): a pytest job (`not slow and not integration`) plus a `quarantine-gates` job running `audit_keepers.py --check` and `legitimacy_diagnostics.py --keepers` on every PR, alongside `lint.yml` (ruff) and the weekly D-13 `bench-repro.yml` cron. Still current; a further `.github/workflows/forecast-invariants.yml` has since been added (scheduled tier for the slow invariant/golden/paired-run tests this doc's §2.4 designed). |
| W2-P1 emissions fixes | **Landed** (PR #1371: d3077a4 forward estimator, fff2c34 R2 basis, 968cead quarantine-row strip, R7 NOx unit fix). Validation artifacts built from HEAD now score the right quantity. `src/market_sim/data/emission_rates.py` exists and is in active use; the referenced commit hashes are no longer resolvable in `git log` (history has since moved/squashed) but the module and its behavior are confirmed on disk. |
| EIA-860 vintages on disk | ~~`data/raw/eia-860/vintage_2023/`, `vintage_2024/` **only**. No 2018/2019/2020 vintage snapshots exist~~ — **`vintage_2020/` now exists on disk** (§6: the W2-P5 stage-2 EIA-860 2020-vintage intake landed). 2018/2019 vintages still do not exist. |
| Demand model profiles | `eia_demand_profiles` covers **2021–2025** (full-8760 contract; no builder script in repo — F3, still true: no `scripts/build_demand_profiles.py` exists). Earliest solvable dispatch year is therefore **2021**. Separately, `scripts/curate_demand_profile.py` (a *repair*, not a from-scratch *builder*) now exists and fixes physically-impossible hours in the raw extract — see the §6 update below. |
| Henry Hub | 1997–2026 on disk. ~~AEO as-known-then paths: not yet intaken for a 2021 vintage.~~ **Landed** (§6): `HENRY_HUB_TRAJECTORIES` in `constants.py` now carries both `hindcast_realized` and `hindcast_asknown_aeo2021` entries. |
| Evolution ledger | ~~**Does not exist.**~~ **Landed** (§6): `src/market_sim/results/evolution_ledger.py` exists and is imported/used by `runner.py`, which writes `evolution_<year>.json` beside each cached year parquet. |

---

## 1. Capacity hindcast — concrete design

### 1.1 Window: 2020-vintage init → evolve 2021–2025, with a 2022 bridge

**Chosen window: initialize the fleet from the EIA-860 2020 vintage; evolve 2021 → 2025.**

- **2021 — solve + evolve.** 2021 is not a quarantined year. Demand profile exists (2021–2025);
  Henry Hub on disk. Caveat recorded up front: statistical outages will not reproduce Winter
  Storm Uri, so the 2021 *dispatch* is low-fidelity — acceptable, because 2021's role is to
  generate the price/margin signal for the 2022 evolution step, not to be scored.
- **2022 — BRIDGE year: no solve, no intake, no dispatch/emissions scoring.** The one-pass loop
  is already prior-year-driven (`prior_results` from year N feeds year N+1's screens), so the
  **2022 evolution step needs no 2022 solve**: it consumes the 2021 `prior_results`. The 2023
  evolution step then *also* consumes the 2021 `prior_results` (the last solved year). No 2022
  demand, fuel, outage, or bench data is read at all — the harness must assert this (a test
  patches the 2022 loader paths to raise).
- **2023, 2024, 2025 — solve + evolve + score.** In-sample dispatch years; capacity outcomes for
  these years were never tuned to (the retirement/entry parameters are literature/citation-set),
  so the capacity layer is genuinely out-of-sample here even though dispatch calibration is not.

**Documented bias from the bridge (do not paper over):** the model cannot see 2022's high-gas
year ($6.45 HH) when making 2023 decisions — the retirement-deferral signal that gas spike
created in reality is invisible. Expect the model to over-retire marginal gas/coal relative to
reality in 2023, and say so in the report. When an ISO's quarantine lifts (calibration-complete
marker), re-run the hindcast with 2022 solved as a one-shot sensitivity and publish the delta.

**Why not 2018-start (the original plan's window):** (a) no EIA-860 2018 vintage snapshot on
disk and none intaken; (b) demand model profiles start at 2021 and the profile builder is a
hand-uploaded artifact with no in-repo script (F3) — 2018–2020 solves are unbuildable today;
(c) it adds three more unscoreable dispatch years for little capacity-signal gain, since the
2018–2020 ERCOT capacity story is pipeline-dominated. The 2020→2025 window still contains the
hard test the plan wanted: the ERCOT 2021–2025 solar/storage boom and the IRA mid-window.

**Quarantine interpretation (owner may veto):** *cumulative* capacity scoring across the window
necessarily counts real-world units that retired or came online **during** 2022 — these are
EIA-860 registry facts (dates in the current 2025 release already on disk), not the quarantined
bench domain (EIA-930/CAMPD/delivered-fuel outcomes). We treat retirement/COD dates as
admissible registry data; we never score model-2022 dispatch, emissions, or prices, and the
model makes its 2022 capacity decisions on 2021 information only. Timing metrics near 2022
carry a bridge artifact — flagged in the scorer output.

### 1.2 Data prerequisites (all admissible — nothing touches 2022/2026)

1. **EIA-860 2020 vintage intake** (NEW, required): archived `eia8602020.zip` (Final Release,
   published Sept 2021) → `data/raw/eia-860/vintage_2020/` following the existing
   `vintage_2023/` file set (`eia860_generator_operable/proposed/retired…`, plant, owner, wind/
   solar/storage operable sheets). 2020 is not a quarantined year. Run through the data-intake
   skill conventions (schema-first, provenance header).
2. **As-known-then fuel path**: AEO2021 Reference case Henry Hub 2021–2025 (published Feb 2021 —
   the correct contemporaneous vintage for a 2021 start; the plan's AEO2018 reference belonged
   to the abandoned 2018 window). Add as cited `HISTORICAL`/`AEO2021_REFERENCE` entries in
   `constants.py` per `docs/parameter-citations.md`. Realized variant uses the on-disk monthly
   Henry Hub (1997–2026); the bridge year's fuel is never read.
3. **Actuals dataset** `data/raw/_validation-source/capacity_actuals_ercot.csv` (and `_pjm.csv`):
   every retirement (unit, fuel class via our taxonomy, MW, year, zone) and addition (tech, MW,
   COD year, zone) 2021–2025, built from the **latest** EIA-860 release (outcome registry data;
   provenance header; >300 MW units flagged). This is the scoring target, committed.
4. **Known-pipeline leakage guard**: the as-known-then pipeline comes from the 2020 vintage's
   proposed/planned sheets only (statuses U/V/TS, same rule as `load_planned_additions`). Assert
   no unit absent from the 2020-vintage proposed sheet enters the pipeline.

### 1.3 Harness (`scripts/run_capacity_hindcast.py`)

CLI: `--iso {ERCOT,PJM} --start-year 2021 --end-year 2025 --fuel-variant {realized,asknown}
--out-dir results/hindcast/<run_id>`.

- `ScenarioConfig` gains `start_year`/`end_year` fields (defaults 2026/2050 from
  `constants.py:2594-2595`; cache keys unchanged when at defaults) and a `hindcast: bool = False`
  flag. `mode` stays `"forecast"` — the hindcast IS the forecast machinery (capacity evolution
  on, statistical outages, forecast renewables, no backcast overlays; the backcast-gated
  overlays never fire because `mode != "backcast"`). `hindcast=True` additionally switches:
  per-year **realized demand profiles** (actual year's profile, no growth scaling — isolates
  capacity logic from demand-forecast error), fuel path per `--fuel-variant`, vintage fleet
  init, vintage pipeline restriction, and the 2022 bridge (skip the solve, reuse the last
  solved year's `prior_results` for the next evolution step).
- Rule 12 applies: years sequential within an invocation; the two fuel variants run as two
  concurrent background invocations with separate `--out-dir`s.
- Emissions in the scored years use the HEAD (R2, fff2c34) basis and the W0-P1 forward
  estimator for existing units — the hindcast doubles as the first out-of-sample exercise of
  that estimator against 2023–2025 CAMPD.

### 1.4 Scoring (`scripts/score_capacity_hindcast.py`) — metrics, bands, baselines

Scored against `capacity_actuals_<iso>.csv`, plant-level matching greedy on fuel+size.
Bands adapt `forecast-validation-plan.md` Phase 2c to the 5-year window and the ±10% CO2 goal:

| Metric (realized-fuel variant) | Band |
|---|---|
| Cumulative thermal GW retired 2021→2025 | ±10% total; ±20% per fuel |
| Unit-level retirement recall, units > 300 MW | ≥ 70% |
| False-retirement rate (model retires, reality didn't by 2025) | ≤ 15% of retired GW |
| Retirement timing, median \|model − actual\| year | ≤ 1.5 yr (2022-bridge artifact flagged) |
| Cumulative additions by tech 2021→2025 | ±15% wind/solar/gas; ±25% storage |
| Tech-mix shares of total additions | Δ ≤ 5 pp per tech |
| **System CO2 2025 with the hindcast fleet** | **±10% vs CAMPD/eGRID** (headline — the model-intent number); 2023/2024 report-only |
| Annual additions by tech; zonal siting rank-correlation | report-only |

**CO2 decomposition (the report's key table):** hindcast-2025 CO2 error ≈ dispatch error
(measured: keeper and D-7 statmode gaps on the true fleet) + fleet error (the new information).
Report all three columns so capacity-path error is isolated, not conflated with known dispatch
error.

**Baselines (must beat (a) and (b) on retirement recall and addition mix to claim skill):**
(a) frozen fleet — no retirements/builds after 2020; (b) announced-only — the 2020 vintage's
planned retirement/addition schedule applied verbatim; (c) AEO2021 regional capacity projection,
report-only context. The `asknown − realized` gap is fuel-input error, attributed separately.

**Attribution runs** (plan 2d) stay in the design: on a failed metric, re-run with one screen
pinned to actuals at a time (retirements pinned / builds free, and vice versa) to localize the
wrong screen. Cheap under one-pass. Diagnosis only — never a keeper, never a tuning channel.

### 1.5 Registration — a separate surface, deliberately outside the backcast registry

The hindcast bundle contains a **2021 solve year**. `audit_keepers.py` /
`legitimacy_diagnostics.py --keepers` correctly FAIL any backcast-registry bundle with a solve
year outside 2023–2025 — that gate must stay strict and must not learn exceptions. Therefore:

- Bundles: `results/hindcast/<run_id>/` (meta.json + run_config.json + per-year parquet +
  evolution ledger + score.json).
- Reports: `docs/hindcast-reports/<iso>-2021-2025-<variant>-<date>.md`.
- Dashboard: new sidecar namespace `frontend/data/hindcast/<run_id>.json` + a new
  `docs/codebase-site/forecast-validation.html` page (hindcast scorecards + invariant status +
  statmode gap table — the forecast-side sibling of `calibration-status.html`). Rule 15's
  spirit — results live on the dashboard, committed in the producing session — applies; the
  backcast run-explorer namespace does not.

### 1.6 Non-goals and discipline

- **No tuning in the build/run sessions.** The identifiability sweep (plan Phase 4) is out of
  scope until the harness lands — and note honestly: under the quarantine there is currently
  **no untouched capacity holdout** (2022 is unsolvable, 2023–2025 is the only scored window).
  If the owner later tunes capacity parameters against this hindcast, the scored window loses
  its out-of-sample status and a fresh protocol (e.g. leave-one-outcome-year-out inside
  2023–2025, or post-quarantine 2022) must be designated *first*.
- A failed band is a root-cause investigation (rules 1/14), never a band widening.
- ERCOT first, then PJM (calibrated reference + landed data; both fuel variants each). Other
  ISOs only after their dispatch calibration matures — actuals are national, so extension is
  mechanical.

---

## 2. Forecast invariant suite

### 2.1 Shared substrate first: the evolution ledger

Neither the invariant checker nor the hindcast scorer can exist without persisted capacity
events; today only `retrofit_log` is threaded (in-memory) and retirements/builds are log lines.
**W2-P5 stage 1 adds, per scenario-year, `evolution_<year>.json` in the cache dir** (written by
`runner.py` beside the dispatch parquet):

- retirements: `[{unit_id, fuel, mw, reason: known|economic|not_retained}, …]` plus units
  **retained by the reliability floor** that the economic screen wanted out (CX-3 attribution);
- additions: `[{tech, mw, zone, source: planned|economic|ccs_retrofit, eia860_id?}, …]`;
- fleet totals by fuel before/after; peak demand; reserve margin; RPS dual; solve counts per pass.

### 2.2 Invariant list (`scripts/check_forecast_invariants.py`)

Runs over a completed forecast scenario's cache (year parquets + ledgers). One PASS/FAIL/WARN
line per invariant with offending years/values; nonzero exit on FAIL; thresholds in one
dataclass at the top. Single-run invariants:

| # | Invariant | Check (source) | Threshold / severity |
|---|---|---|---|
| I1 | Energy balance | per zone-hour: thermal+wind+solar+dis−chg+net_flow+slack−dump = demand (parquet arrays) | \|residual\| ≤ 1e-3 MW; FAIL |
| I2 | No NaN/inf | every persisted array and summary field | any hit; FAIL |
| I3 | Unserved/dump | slack = 0 outside explicit scarcity tails; dump < 2% of renewable potential | FAIL |
| I4 | Capacity accounting closes | fleet(N+1) = fleet(N) − retirements + builds, by fuel (ledger) | exact; FAIL |
| I5 | No retire-and-reenter | unit_id retired then re-added (ledger) | any; FAIL |
| I6 | Economic-retirement sanity | each economic retirement has ≥ threshold consecutive loss years for its fuel; single-year economic retirement ≤ config-derived GW cap | FAIL |
| I7 | Reliability floor integrity | post-evolution thermal ≥ (peak − firm_clean) × 1.15 every year; floor-retained units logged distinctly | FAIL |
| I8 | Planned-additions mode-gating | backcast run: zero planned units; forecast: only U/V/TS statuses, EIA-860-traceable ids, none beyond data horizon | FAIL |
| I9 | Storage integrity | SOC ∈ [0, cap]; cyclic \|SOC₀−SOC_T\| ≤ tol; simultaneous charge+discharge energy ≈ 0 (ε-tiebreak working); per-ISO growth caps + `STORAGE_TECH_BUILD_SHARE_CAP` respected in ledger | FAIL |
| I10 | RPS dual sign + stability | dual ≥ 0 every year; once binding, YoY \|Δdual\| < 50% (B9) | sign FAIL; oscillation WARN |
| I11 | One-pass assertion | solve counts per year from ledger: exactly one P0+P1 (+P2 iff enabled) — no within-year iteration | FAIL |
| I12 | Reserve-margin band | within [floor, floor + 15 pp] every year | WARN (FAIL if 3+ consecutive years) |
| I13 | Cobweb detector | per-tech builds alternating full-cap/zero in ≥ 3 consecutive year-pairs (B4) | WARN |
| I14 | Price sanity | annual LW price ∈ [0.5×, 3×] fuel-implied CC MC; PDC monotone; negative-price hours bounded | WARN |

Paired-run invariants (`--paired base_dir other_dir`), run on demand and in the nightly tier:

| # | Invariant | Pairing | Threshold |
|---|---|---|---|
| P1 | CO2 monotone under rising carbon price | same config, carbon_price_path high vs base | cumulative-2050 CO2(high) < CO2(base) FAIL; per-year violations > 1% WARN (evolution feedback can locally wiggle) |
| P2 | Merit-order sign response | +$1/MMBtu gas | coal gen ↑ (coal-bearing ISOs), gas-CC gen ↓, LW price ↑, objective ↑; FAIL on sign |
| P3 | Perturbation stability | ±5% gas | cumulative-2035 builds move < 25% (cliff-edge detector); WARN |

### 2.3 Golden-scenario band regression

One pinned reference scenario — **ERCOT reference config, 2026–2032** — solved on real HiGHS.
Banded quantities stored in `tests/golden/ercot_2026_2032.json`: annual CO2 (±2%), capacity by
fuel at 2032 (±1 GW/fuel), annual LW price (±5%), total system cost (±2%), cumulative builds by
tech (±10%). The first W2-P5 run seeds the golden values; regeneration only via an explicit
script + commit citing the causal code change (rule 23 spirit — the golden is frozen against
residuals). Runtime is ~7 ERCOT LP years ⇒ nightly/weekly CI tier, not per-PR.

### 2.4 End-to-end tiers (closes TC-3)

- **Per-PR (seconds): `tests/test_forecast_e2e.py`** — a synthetic 2-zone ISO fixture (~10
  units + wind/solar/storage, real 8760 LP via HiGHS), 3 forecast years, engineered so the run
  exercises: one economic retirement, one economic entry, the planned pipeline, a binding RPS
  year, and storage evolution. Asserts the invariant checker passes end-to-end and that specific
  engineered events appear in the ledger. This is the first real-LP coverage of the evolution
  loop (trivial-case-first per the testing pattern). Keep `test_runner.py`'s mocked
  orchestration tests — they test different things.
- **Nightly/weekly: NEISO 2026–2030 smoke** (smallest real ISO) + the golden ERCOT band run +
  paired-run invariants P1/P2. Wire into the CI cadence W1-P1 establishes.

---

## 3. Sequencing

### 3.1 Order of landing

```
1. W1-P1  CI wiring (pytest-on-PR + audit_keepers/legitimacy gates)   [landed, `ci.yml`]
2. W2-P5 stage 1  evolution ledger + invariant checker + synthetic e2e + golden scaffold   [landed, §6]
3. W2-P5 stage 2  EIA-860 vintage-2020 intake + hindcast harness/actuals/scorer
                  → run+score ERCOT (both fuel variants), then PJM → forecast-validation page   [landed, §6]
4. W3-P1  statmode: re-solve CAISO/NYISO/NEISO D-7 at HEAD (+ paired HEAD keeper replays);
          re-SCORE (no solve) ERCOT/PJM/MISO statmode bundles under the R2 basis   [landed, §5;
          stale again as of 2026-07-06 — see the §0 Statistical-mode row, every ISO but CAISO
          has since been re-gated]
5. Ongoing: D-6 machinery prep (§3.3, partially landed — the run_calibration_full.py
          holdout-year solve guard exists; the demand-profile *builder* (F3) and the
          build_calibration_reference.py year-registration (F4) do not), owner re-gates
          (NYISO landed 2026-07-06, others pending), calibration-complete declarations per
          §3.4 (none declared as of 2026-07-06 — `complete: {}`; **update 2026-07-11: NEISO
          declared complete 2026-07-07**, keeper `2026-07-08-neiso-54-steamgas-ct`, its
          2019 + H1-2026 locked-test one-shot scored once against the frozen `neiso-53`
          config and standing per rule 22 — other five ISOs still undeclared) → one-shot
          holdout validation per ISO
```

Rationale: W1-P1 protects every artifact the rest produce (the quarantine gates currently run
only when someone remembers). The **emissions R2 basis change already landed** (fff2c34, PR
#1371), so validation artifacts built now score the correct quantity from day one — building
the invariant bands or hindcast scorer before that merge would have meant rebuilding them; that
blocker is gone, which is why W2-P5 starts immediately after W1-P1. Stage 1 precedes stage 2
because the ledger is the scorer's input.

### 3.2 Statmode: what actually remains

All six D-7 probes ran 2026-07-03 — but fff2c34 (R2) changes the merit order **only where
carbon price > 0**. Consequences (verified in `co2-keeper-regate-2026-07-05.md`):

- **ERCOT / PJM / MISO**: statmode solves remain valid (carbon = $0; R2 provably outside `mc`).
  W3-P1 re-scores their existing bundles under the new CO2 basis — cheap, no LP.
- **CAISO / NYISO / NEISO**: stale twice over — R2 moves their merit order AND their keepers
  predate the 07-04 offer merges. Each statmode re-solve must be **paired with a same-SHA keeper
  replay** (the `*-co2re-probe` pattern) so the D-7 gap compares like with like. NYISO carries
  an extra flag: nyiso-41's HEAD replay regresses C1/C7 — pair, publish, and flag; the keeper
  re-gate itself is the owner's separate decision, not W3-P1's.
- Standing rule going forward: **D-7 is keeper-relative — whenever a keeper is re-gated, its
  statmode twin re-runs in the same session** and the gap republishes on the dashboard.

### 3.3 D-6 unblocking WITHOUT touching quarantined years

Everything below is machinery, buildable and testable entirely on 2023–2025; the quarantined
intake for CAISO/MISO/NYISO/NEISO happens only at marker time (amended rule 22: intake is step 1
of the one-shot validation):

1. **F3 — demand-profile builder script.** None exists (hand-uploaded artifact). Write
   `scripts/build_demand_profiles.py`, validate by reproducing the committed 2023–2025 rows
   byte-identically. At one-shot time it builds 2022 directly; for H1-2026 see item 4.
2. **F4 — scoring-path year registration.** Make `build_calibration_reference.py` accept
   configurable years/HH entries behind the same `--holdout-authorized` guard as item 3 —
   code change now, data at validation time.
3. **Solve entry-point guard** (holdout memo Option 2, already owner-endorsed direction):
   `run_calibration.py`/`run_calibration_full.py` refuse years outside {2023,2024,2025} unless
   `--holdout-authorized` AND the ISO's calibration-complete marker exists. The hindcast harness
   gets the same guard with 2021 added to its own allowed set.
4. **H1-2026 scoring-window decision (proposed now, owner confirms at validation time):** solve
   the full 8760 with a spliced profile (H1 actual + H2 typical-year), score **H1 hours only**
   against bench. Satisfies the full-8760 contract without fabricating H2 actuals.
5. **One-shot runbook** in this doc's successor: intake (fetch scripts already year-agnostic) →
   verify (`verify_holdout_intake.py` pattern) → frozen-keeper solve via `replay_keeper.py` →
   score once → register with the marker → never re-tune (a new never-touched holdout must be
   designated before any calibration responds).
6. **External watches (not actionable now):** EPA CAMPD Q2-2026 hourly (unposted); EIA delivered
   gas May-2026+; scattered N3045/citygate withheld months. H1-2026 CAMPD-side scoring is
   Q1-limited until EPA posts Q2.

### 3.4 Calibration-complete decision rule (per ISO)

The owner declares an ISO complete by adding its marker to
`frontend/data/backcast/calibration-complete.json` (freezing the keeper id). Proposed checklist
— every line verifiable from committed artifacts, no judgment calls hidden in prose:

1. **Keeper current at HEAD:** re-gated after the last solve-affecting merge; passes the rubric
   on all years 2023–2025. (As of 2026-07-05: none qualified — all six keepers predated the
   07-04 merges; NYISO had a known HEAD regression. **Update 2026-07-06:** `keepers.json` now
   shows ERCOT/PJM/NYISO/NEISO/MISO all re-gated (dates 2026-07-05/06); only CAISO is still the
   2026-07-03 bundle. Whether the re-gated keepers satisfy this checklist item's other clauses
   — rubric pass on 2023-2025, current D-7/D-8 artifacts — has not been re-verified here.)
2. **Rules 19–21 artifacts current:** DOF ledger, registered zero-forcing ablation twin,
   forced-energy budget met (merchant ≤ 30%, peakers ≤ 10%).
3. **D-7 statmode gap published at the current code/basis** (per §3.2, re-run after any re-gate).
4. **D-8 stability clean:** no load-bearing coefficient family for that ISO with an unresolved
   sign-flip or > ~15% out-of-training drift. (Today this blocks CAISO — both SP15 limbs
   sign-flip and the CT floor ≈ the class it floors — and partially PJM.)
5. **LOYO within 2023–2025** passed for any structural mechanism promoted since the last gate
   (rule 22's existing requirement).
6. **Forecast invariants green** on that ISO's 2026–2030 forecast run (§2.2).
7. **Capacity hindcast within bands** for ERCOT/PJM; report-only context for the other four
   until their hindcasts run.
8. **No open red-flag investigation** on that ISO (e.g. CAISO CT floor scrub W3-P2, NYISO
   re-gate).

Then the one-shot proceeds per §3.3 item 5, results recorded whatever they are, and no
calibration change responds to them without a newly designated holdout.

---

## 4. Implementation prompts

### 4.1 W2-P5 — Forecast invariant suite + capacity hindcast build (Opus)

```
[W2-P5] Forecast invariants + capacity hindcast — implement per the plan.

Read docs/handoffs/forecast-validation-program-2026-07.md FIRST (it is the spec for this
session; its §0 facts were verified 2026-07-05), then CLAUDE.md (rules 12, 15, 16, 22),
docs/fable-repo-audit-2026-07.md §F TC-3, and docs/forecast-validation-plan.md Phase 1-2.
Work on a feature branch; commit and push per the CLAUDE.md 413 workflow (push_files for
anything bulky). HARD CONSTRAINTS: no solve, no scoring, and no data intake may touch 2022
or 2026 (rule 22) — the hindcast bridges 2022 without solving it (plan §1.1) and a test
must prove no 2022 loader path is read. Do not tune any parameter anywhere (plan §1.6).

STAGE 1 — evolution ledger + invariant suite (land this even if stage 2 slips):
1. Evolution ledger (plan §2.1): runner.py writes evolution_<year>.json beside each cached
   year parquet — retirements (unit, fuel, MW, reason: known|economic; plus reliability-
   floor-retained units the economic screen wanted out), additions (tech, MW, zone, source:
   planned|economic|ccs_retrofit, EIA-860 id where applicable), fleet totals by fuel
   before/after, peak demand, reserve margin, RPS dual, solve counts per pass. Backcast
   mode writes it too (it will show zero evolution — that is itself invariant I8's input).
2. scripts/check_forecast_invariants.py implementing the plan §2.2 tables exactly:
   single-run invariants I1-I14 and paired-run P1-P3 behind --paired. One PASS/FAIL/WARN
   line each with offending years/values; nonzero exit on any FAIL; all thresholds in one
   dataclass at the top, no scattered literals.
3. tests/test_forecast_e2e.py (plan §2.4): synthetic 2-zone ISO fixture, ~10 units +
   wind/solar/storage, REAL HiGHS solve, full 8760, 3 forecast years, engineered to
   exercise one economic retirement, one economic entry, the planned pipeline, a binding
   RPS year, and storage evolution; assert the invariant checker passes and the engineered
   events appear in the ledger. Keep test_runner.py's mocked tests as-is.
4. Golden scaffold (plan §2.3): tests/golden/ + the regen script + the band-checking test
   (skips loudly if the golden file is absent). Seed the golden by running ERCOT reference
   2026-2032 once in this session and commit the values with the config SHA recorded.
5. Run check_forecast_invariants.py on a fresh ERCOT 2026-2040 forecast and a NEISO
   2026-2030 forecast; write every failure with a one-line diagnosis to
   docs/forecast-invariant-findings.md. FINDINGS ONLY — do not fix model code this session.

STAGE 2 — capacity hindcast (ERCOT first):
6. Data intake (plan §1.2, use the data-intake skill): EIA-860 2020 vintage
   (eia8602020.zip Final) -> data/raw/eia-860/vintage_2020/ mirroring vintage_2023's file
   set; AEO2021 Reference Henry Hub 2021-2025 as cited constants; build
   data/raw/_validation-source/capacity_actuals_ercot.csv (+ _pjm.csv) per plan §1.2.4
   from the LATEST EIA-860 (registry facts; provenance header; >300 MW flagged).
7. scripts/run_capacity_hindcast.py per plan §1.3: ScenarioConfig start_year/end_year
   (defaults 2026/2050, cache keys stable at defaults) + hindcast flag; mode stays
   "forecast"; realized per-year demand profiles; --fuel-variant {realized,asknown};
   2020-vintage fleet + pipeline init with the leakage assertion (plan §1.2.4); the 2022
   bridge (no 2022 solve — evolution steps for 2022 AND 2023 consume the 2021
   prior_results; add the loader-raise test). Year guard: allowed solve years for the
   hindcast are {2021, 2023, 2024, 2025} only.
8. scripts/score_capacity_hindcast.py per plan §1.4: the metric/band table, greedy
   fuel+size plant matching (unit-test on a synthetic 5-unit case), the three baselines
   (frozen fleet, announced-only from the 2020 vintage, AEO2021 report-only), the CO2
   decomposition table (hindcast error vs keeper/statmode dispatch error), and a markdown
   report to docs/hindcast-reports/.
9. Run the ERCOT hindcast 2021-2025 in BOTH fuel variants as two concurrent background
   invocations with separate --out-dirs (rule 12; years sequential inside each), score
   both, and register per plan §1.5: bundle under results/hindcast/, sidecar under
   frontend/data/hindcast/, report under docs/hindcast-reports/, and the new
   docs/codebase-site/forecast-validation.html page (hindcast scorecard + invariant
   status; keep it simple — the backcast registry and its CI gates must NOT learn about
   hindcast bundles). Diagnosis only on misses: ranked largest unit-level errors each with
   a mechanism hypothesis naming the capacity.py screen responsible. NO parameter tuning.
   If the EIA-860 2020 vintage cannot be sourced, stop stage 2, record the blocker in the
   plan doc, and land stage 1.
10. If context runs short: land stage 1 complete + the stage-2 intake, and hand off with a
    status note appended to the plan doc.
```

### 4.2 W3-P1 — Statistical-mode backcasts, remaining ISOs (Sonnet)

```
[W3-P1] Statmode D-7 refresh — re-solve CAISO/NYISO/NEISO, re-score ERCOT/PJM/MISO.

Read docs/handoffs/forecast-validation-program-2026-07.md §3.2 FIRST, then CLAUDE.md
(rules 12, 15, 16, 22), docs/handoffs/co2-keeper-regate-2026-07-05.md, and
scripts/run_statmode_probe.py (the D-7 protocol: byte-faithful keeper replay with
outage_source=statistical, deployment/reliability floors off, WEFOR relief off, per-plant
monthly coal pricing off; every structural lever and realized gas unchanged). Context: all
six D-7 probes ran 2026-07-03, BEFORE the R2 CO2-basis merge (fff2c34) — R2 moves the
merit order only where carbon price > 0, so the three carbon-priced ISOs' statmode solves
are stale while the three carbon-zero ISOs' remain valid. Feature branch; 413 push rules;
no 2022/2026 anywhere.

1. Re-solve statmode for CAISO, NYISO, NEISO at HEAD via run_statmode_probe.py against
   each ISO's keeper bundle (keepers.json), all years 2023-2025, one bundle per ISO,
   years sequential per invocation. PAIR each with a same-SHA keeper replay via
   scripts/replay_keeper.py (the co2re-probe pattern) so the D-7 gap is code-consistent —
   the committed 07-03 keepers predate the 07-04 offer merges and are not a valid HEAD
   baseline. Launch as concurrent background jobs capped at 2 simultaneous (rule 12).
2. Re-SCORE (no LP) the existing ERCOT/PJM/MISO statmode bundles under the R2 CO2 basis
   (carbon=$0 there, so the solves are provably unchanged — re-run the verdict/scoring
   only) and refresh their dashboard sidecars if any number moved.
3. Register every run on the dashboard via the calibration-report skill IN THIS SESSION
   (rule 15): probes, never keepers, labelled "<iso> statmode d7 r2" / "<iso> head-replay
   r2". Honour top-15-per-ISO retention when pruning.
4. Publish the D-7 skill table in docs/handoffs/forecast-validation-program-2026-07.md
   (append a §5): per ISO, keeper-at-HEAD vs statmode-at-HEAD fail counts and CO2/volume
   gaps — the overlay-carried-skill number. NYISO caveat: the HEAD replay of nyiso-41 is
   known to regress C1/C7 (07-04 CT-offer grounding, see co2-keeper-regate doc) — publish
   the pair anyway, flag it, and leave the keeper re-gate decision to the owner; do NOT
   swap any keeper.
5. Do not tune anything to improve a statmode fit — a worse fit is the finding (rule 1).
   Going forward, note in the doc: D-7 re-runs in the same session as any keeper re-gate.
```

---

## 5. D-7 skill table — appended by W3-P1 (2026-07-05)

Keeper-at-HEAD vs statmode-at-HEAD, all years 2023-2025. "Keeper" reads each ISO's
*currently committed* keeper bundle (`frontend/data/backcast/keepers.json`) via
`calibration_verdict.py <keeper-id>` — for CAISO/NYISO this is **not** a fresh HEAD
replay (their committed bundles predate the 2026-07-04 offer merges; see §3.2/§0), so
the keeper-column CO2 numbers are the stale committed ones, not a same-SHA baseline.
Statmode is the D-7 probe (byte-faithful keeper replay, `outage_source=statistical`,
deployment/reliability floors + WEFOR relief + per-plant monthly coal pricing off):
`run_statmode_probe.py` for CAISO/NYISO/NEISO (fresh HEAD solve, this session);
`calibration_verdict.py` re-run on the existing bundle for ERCOT/PJM/MISO (no solve,
carbon=$0 ⇒ provably unaffected by R2).

| ISO | keeper CO2 (2023/24/25, model vs eGRID %) | statmode CO2 (2023/24/25) | keeper C1 free-class | statmode C1 free-class |
|---|---|---|---|---|
| ERCOT | PASS −0.4 / PASS −1.1 / PASS +0.5 | PASS +0.1 / PASS −2.4 / PASS +3.9 | 10/12 | 9/12 |
| PJM   | PASS +1.3 / PASS +1.3 / PASS +4.6 | FAIL +26.6 / FAIL +26.1 / FAIL +22.6 | 10/12 | 6/12 |
| MISO  | PASS −2.0 / PASS −3.6 / PASS +4.1 | FAIL +15.0 / FAIL +10.5 / FAIL +21.6 | 6/12 | 2/12 |
| CAISO | PASS +0.5 / **FAIL +8.4** / **FAIL +8.6** (stale, pre-07-04) | PASS −1.5 / PASS +6.9 / FAIL +10.4 | 7/8 | 6/8 |
| NYISO | PASS −3.6 / CAVEAT −7.2 / PASS −6.2 | PASS +3.7 / PASS −1.9 / PASS −1.0 | 10/10 | 6/10 |
| NEISO | PASS −3.0 / PASS −3.1 / PASS +4.0 | PASS −3.5 / PASS −3.4 / PASS +3.7 | 8/8 | 8/8 |

**Reading the table (rule #1 — a worse statmode fit is the finding, not a bug):**

- **ERCOT/NEISO**: the statmode CO2 gap stays inside the same PASS band as the
  keeper — the historic overlays (CAMPD outages, WEFOR relief, per-plant coal
  pricing, deployment floors) are buying comparatively little *system* CO2 skill
  for these two markets; the C1 free-class drop (ERCOT 10→9, still solid; NEISO
  unchanged 8/8) says the same for fuel-mix.
- **PJM/MISO**: statmode CO2 fails hard in all three years (PJM +22–27%, MISO
  +11–22%) against a keeper that PASSes cleanly — here the overlays are carrying
  real skill; removing them (statistical outages instead of measured CAMPD
  windows, no per-plant coal pricing) visibly breaks the fuel mix (PJM free-class
  10/12→6/12, MISO 6/12→2/12). This is the expected D-7 signal for markets with
  a large coal/CC fleet whose dispatch order is outage- and fuel-cost-sensitive.
- **CAISO**: the keeper's *committed* 2024/2025 CO2 already FAILs (stale,
  pre-07-04-merge bundle — see §0/§3.2); the fresh HEAD statmode solve actually
  reads *better* on 2023/2024 (PASS/PASS vs PASS/FAIL) because it inherits the
  07-04+ offer-curve work the committed keeper predates, and still FAILs 2025
  (+10.4%). Because this solve was not paired with a same-SHA keeper replay,
  the movement here is confounded (offer-curve improvement + overlay removal +
  R2, not R2 isolated) — flagged, not a claim that statmode overlays are net
  harmful for CAISO.
- **NYISO**: same confound as CAISO (committed keeper predates 07-04 merges),
  plus the **B-NYI-1 offer de-leak** (merge a4c219e, 2026-07-05 re-gate) is
  live in this HEAD solve — CT_PEAKER's offer wall dropped from the old
  13.15×/1.98 ceiling to 4.0×/1.0, which alone roughly doubles modelled
  CT_PEAKER energy per the keeper-regate doc. That is very likely why NYISO's
  statmode CO2 reads as *cleaner* than the stale committed keeper (all PASS,
  −1.0 to +3.7% vs the keeper's CAVEAT/-7.2% in 2024) — inherited, not
  compensated for, per this task's instruction.
- **R2 isolation (the one number this session can state cleanly):** for all
  three carbon-priced ISOs, `docs/handoffs/co2-keeper-regate-2026-07-05.md`'s
  ablation already isolated R2's own effect at ≤0.1-1% of modelled CO2 (CAISO
  +0.2-0.4 Mt, NYISO <0.1%, NEISO ~0) — small next to the offer-curve-driven
  swings above. R2 itself did not need re-running to confirm this; it is
  restated here for the record.

No parameter was tuned to any of these results (rule #1/#23); a worse statmode
fit vs. the keeper (PJM, MISO) is reported as-is, not chased. No solve, score,
or intake touched 2022 or H1-2026.

---

## 6. W2-P5 delivery status (2026-07-05)

Both stages landed. §0 facts that changed: the capacity hindcast is **built and
run**, the forecast invariant checker **exists**, and the EIA-860 2020 vintage is
**on disk**.

**Stage 1 — invariants + ledger (complete):**
- Evolution ledger: `runner.py` writes `evolution_<year>.json` beside each cached
  year parquet; `evolve_fleet`/`apply_economic_retirements` emit the events via an
  optional out-param (default solve path byte-identical). Dispatch parquets now
  persist per-zone demand (`outputs.to_parquet(demand=…)`) so the energy balance
  is checkable. Confirmed on a real ERCOT forecast: I1 closes to 3.6e-10 MW.
- `scripts/check_forecast_invariants.py` — I1-I14 single-run + P1-P3 paired, all
  thresholds in one dataclass, nonzero exit on FAIL.
- `tests/test_forecast_invariants.py` — 34 fast invariant-logic cases + a real-LP
  integration test (`RUN_SLOW_FORECAST=1`, 3-year ERCOT solve, 205 s) that closes
  TC-3 (first real-LP exercise of the evolution loop + ledger).
- Findings from the first invariant run: `docs/forecast-invariant-findings.md`
  (F0 NEISO default forecast infeasible → blocks the NEISO nightly smoke; F1/F2
  reliability-floor + reserve-margin FAIL because nothing force-builds to the
  absolute floor in the default forecast; F3 an I8 ledger-attribution fix).
  **Findings only — no model behaviour changed.**
- **Golden-scenario band regression (§2.3): now seeded** —
  `tests/golden/ercot_2026_2032.json` + `.run_config.json` committed (a 7-year
  ERCOT reference solve) and `tests/test_golden_forecast_bands.py` reads it;
  the band-checking test itself is `@pytest.mark.slow` (opt-in via
  `RUN_SLOW_FORECAST=1`), so per-PR CI only runs the fast fixture-presence
  check, not the full band comparison. The paired-run invariants P1-P3 are
  implemented, unit-tested, and run in the fast (non-slow) PR pytest tier.

**Stage 2 — capacity hindcast (ERCOT run complete):**
- `scripts/run_capacity_hindcast.py` + `scripts/score_capacity_hindcast.py` +
  `scripts/build_capacity_actuals.py` + `scripts/register_hindcast.py`.
- Intake: EIA-860 2020 vintage → `data/raw/eia-860/vintage_2020/`;
  `capacity_actuals_ercot.csv`; two hindcast gas paths in `HENRY_HUB_TRAJECTORIES`
  (`hindcast_realized`, `hindcast_asknown_aeo2021`).
- **ERCOT realized hindcast run + registered** on the new
  `docs/codebase-site/forecast-validation.html` (namespace
  `frontend/data/hindcast/`, outside the quarantine-gated backcast registry — CI
  gates confirmed to scan only `frontend/data/backcast/registry/`). The 2022
  bridge works: 2021/2023/2024/2025 solved, 2022 evolved-not-solved, **no 2022
  data read, no `year_2022.parquet`**. Report:
  `docs/hindcast-reports/ercot-2021-2025-realized-2026-07-05.md`.
- Headline result (**diagnostic, not a keeper**): the ERCOT capacity screens
  badly miss the real build-out — 0 GW solar built vs 25 GW actual, wind over-built
  +58%, 0 GW retired vs 1.5 GW actual, system CO2 2025 −23% (2023/24 −54%). These
  are the *result*, to be root-caused (rules 1/11/14), not tuned. The `asknown`
  variant runs alongside for the fuel-input-error attribution.
- **NOT done (at end of that session):** PJM (second ISO); the CO2
  decomposition's dispatch-error column (needs the keeper/D-7 CO2 gap threaded in);
  attribution runs (screen-pinned diagnostics, plan §1.4).

**PJM hindcast run complete (2026-07-05, this session):**
- `data/raw/_validation-source/capacity_actuals_pjm.csv` built (255 retirements
  / 11.2 GW, 692 additions / 24.1 GW, latest EIA-860). Both fuel variants run
  2021-2025 (2022 bridged, no solve/data read — leakage guard clean) and
  registered: `frontend/data/hindcast/pjm-2021-2025-{realized,asknown}.json`,
  reports `docs/hindcast-reports/pjm-2021-2025-{realized,asknown}-2026-07-05.md`.
- **Blocking bug found and hotfixed (out of this session's normal scope,
  flagged for the Stage-5/interchange-unification owner):** main HEAD
  (8d46b90, PR #1412) dropped three names from `runner.py`'s import blocks
  that its own new call sites need — `apply_interchange_topology`,
  `apply_interchange_injections`, `forward_corridor_interface_groups` — which
  broke `run_scenario_iso` with a `NameError` for **every** ISO, not just PJM.
  Fixed by restoring the three imports only (no other runner.py changes);
  confirmed via a 2021-only smoke solve before committing to the full run.
- Headline result (**diagnostic, not a keeper**): PJM's capacity screens miss
  the real build-out in the same direction as ERCOT — thermal retirements
  -63% (11.1 actual vs 4.1 GW modelled, recall 0/17 >300MW), but the model's
  4.1 GW of retired capacity is *entirely* a false-retire (100% of modelled
  retired GW): Exelon's Byron + Dresden nuclear stations, whose 2020-vintage
  EIA-860 "Planned Retirement Year" (2021) the model dutifully honors via the
  non-fossil announced-retirement channel — but Illinois's Sept-2021 CEJA
  legislation reversed those retirements in reality, a policy event with no
  admissible model input. Every actual thermal retirement (coal, gas_ct, oil,
  biomass) is separately missed entirely (0 GW modelled) — the
  economic-retirement screen under-retires, same qualitative miss as ERCOT.
  Additions over-build across every tech (wind +271%, solar +34%, gas_cc
  +41%, gas_ct +347%); system CO2 2025 −11% (2023/24 −40%/−49%).
- **Data-defect finding:** the unscored 2021 seed year is corrupted by 3 bad
  hours (hour-of-year 6983-6985) in the raw `data/raw/eia-930/
  eia_demand_profiles.parquet` PJM series — `raw_mw` values of 4.3×10⁸-2.1×10⁹
  MW against a ~90,000 MW backdrop — driving I3/I7/I12/I14 forecast-invariant
  failures in 2021 and plausibly confounding the 2022 evolution step's
  price/margin signal (2021's `prior_results` feeds it directly). I9
  storage-integrity also FAILs on 2023/2024 independent of this defect. Full
  attribution in the realized report's Diagnostic notes.
  **Update — fixed:** `scripts/curate_demand_profile.py` now repairs this at
  the curation seam (raw/ stays untouched; a physical-bounds screen +
  interpolation writes a repaired clean partition), and
  `docs/forecast-invariant-findings.md` F4 records the re-run confirming the
  fix: with the repaired 2021 series, I9 PASSes outright and simultaneous
  charge+discharge drops to float noise (~1e-18 of throughput) in every
  scored year — the corrupted price signal, not the LP/storage tiebreaker,
  was the cause.
- **Still NOT done:** the CO2 decomposition's dispatch-error column; screen-
  pinned attribution runs. (The 2021 raw-demand-data fix + re-run this bullet
  used to list as outstanding has landed — see the update above.)
