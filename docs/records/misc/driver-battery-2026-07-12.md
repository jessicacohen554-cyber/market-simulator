# Tier-1 driver battery — findings (2026-07-12)

**Session:** P-1A, `docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md`
§2 Tier 1. Requires P-0A (`scripts/run_driver_battery.py`, merged on `main`).

**Scope:** all nine ladders (T1.1-T1.9), ERCOT + PJM, T1.6 on NEISO (RPS/ACP-bearing
ISO, per plan §2), forecast 2026-2030, legacy heat-rate bins
(`use_campd_bins=False`), sequential years within each invocation, ≤2 concurrent
invocations (rule 12: ERCOT + PJM ran concurrently as two separate
`run_driver_battery.py` processes; NEISO ran afterward as the plan's ISOs
list for T1.6 is NEISO-only). This is **measurement, not tuning** — no
model-code changes were made in this session. Every FAIL/crash below is a
root-cause issue, never a threshold widened (rules 1/11/14). These are
forecast probes — nothing here touches or registers on the backcast dashboard.

**Raw outputs (this session's run artifacts, not committed — see the
per-rung JSON in the sibling `driver-battery-2026-07-12.json` for the full
machine-readable ladder/rung/expectation data this report summarizes):**
`scripts/run_driver_battery.py --iso ERCOT --start-year 2026 --end-year 2030`
(6030s), `--iso PJM ...` (5296s), `--iso NEISO --start-year 2026 --end-year
2030` (95s, T1.6 only).

## Scoreboard

**24 PASS · 1 FAIL · 0 WARN · 4 SKIP** across 3 ISO runs / 17 ladder-ISO
combinations / 29 expectation rows.

| ISO | Ladders run | PASS | FAIL | SKIP |
|---|---|---|---|---|
| ERCOT | T1.1, T1.2, T1.3, T1.4, T1.5, T1.7(b), T1.8, T1.9 | 11 | 1 (T1.4a) | 2 (T1.2a, T1.9a) |
| PJM | T1.1, T1.2, T1.3, T1.4, T1.5, T1.7(a), T1.8 | 12 | 0 | 1 (T1.2a) |
| NEISO | T1.6 | 1 (vacuous, see below) | 0 | 1 (T1.6b) |

## Per-test PASS/FAIL against pre-registered expectations

| Test | ISO | Expectation | Gate | Status | Detail |
|---|---|---|:--:|:--:|---|
| T1.1a | ERCOT | coal generation monotone ↓ in carbon price | gate | **PASS** | ↓ [369.28, 218.86, 56.94, 3.03] TWh |
| T1.1b | ERCOT | system CO2 monotone ↓ | gate | **PASS** | ↓ [888.68, 770.22, 616.31, 523.59] Mt |
| T1.1c | ERCOT | load-weighted price ↑ (report) | rpt | PASS | ↑ [24.42, 35.30, 46.54, 70.20] $/MWh |
| T1.1d | ERCOT | coal gen actually moves | gate | PASS | Δ=366 TWh |
| T1.1a | PJM | coal generation monotone ↓ | gate | **PASS** | ↓ [1233.8, 762.0, 291.5, 55.6] TWh |
| T1.1b | PJM | system CO2 monotone ↓ | gate | **PASS** | ↓ [1961.4, 1590.3, 1238.4, 996.7] Mt |
| T1.1c | PJM | load-weighted price ↑ (report) | rpt | PASS | ↑ [34.44, 46.51, 59.53, 86.34] $/MWh |
| T1.1d | PJM | coal gen actually moves | gate | PASS | Δ=1178 TWh |
| T1.2a | ERCOT | binding-cap dual ≈ $25 | gate | **SKIP** | no covered mass-cap program (expected, see note) |
| T1.2a | PJM | binding-cap dual ≈ $25 | gate | **SKIP** | PJM RGGI inert per D1 audit (expected, see note) |
| T1.3a | ERCOT | coal generation ↑ with gas | gate | **PASS** | ↑ [242.0, 369.3, 505.8] TWh |
| T1.3b | ERCOT | load-weighted price ↑ with gas | gate | **PASS** | ↑ [12.54, 24.42, 35.37] $/MWh |
| T1.3a | PJM | coal generation ↑ with gas | gate | **PASS** | ↑ [811.9, 1233.8, 1393.6] TWh |
| T1.3b | PJM | load-weighted price ↑ with gas | gate | **PASS** | ↑ [23.77, 34.44, 46.96] $/MWh |
| T1.4a | ERCOT | scarcity hours monotone ↑ with demand | gate | **FAIL** | non-monotone: [34, 0, 58] (low, mid, high) — issue #2064 |
| T1.4b | ERCOT | final reserve margin monotone ↓ | gate | **PASS** | ↓ [0.086, 0.031, -0.042] |
| T1.4c | ERCOT | thermal entry ↑ (report) | rpt | PASS | ↑ [3.31, 3.31, 11.31] GW |
| T1.4a | PJM | scarcity hours monotone ↑ with demand | gate | **PASS** | ↑ [0, 0, 101] |
| T1.4b | PJM | final reserve margin monotone ↓ | gate | **PASS** | ↓ [0.101, 0.009, -0.089] |
| T1.4c | PJM | thermal entry ↑ (report) | rpt | PASS | ↑ [16.0, 16.0, 23.60] GW |
| T1.5a | ERCOT | renewable entry responds to IRA cliff move (report) | rpt | PASS | Δ=20 GW (0 → 20) |
| T1.5a | PJM | renewable entry responds to IRA cliff move (report) | rpt | PASS | Δ=6 GW (0 → 6) |
| T1.6a | NEISO | REC dual ≤ ACP ceiling | gate | **PASS (vacuous)** | both rungs crashed — see below; scored over an empty series |
| T1.6b | NEISO | REC dual ↓ as VRE builds toward target | gate | **SKIP** | insufficient rungs (0 solved) — issue #2063 |
| T1.7b | ERCOT | retirements byte-identical across net-CONE ladder (energy-only negative control) | gate | **PASS** | spread 0.0 over [0,0,0] |
| T1.7a | PJM | thermal retirements monotone ↓ in net-CONE | gate | **PASS (vacuous)** | flat at 0.0 across all 3 rungs — see note below |
| T1.8a | ERCOT | cumulative builds monotone ↓ as tech cost ↑ (report) | rpt | PASS | ↓ [19.31, 14.31, 14.31] GW |
| T1.8a | PJM | cumulative builds monotone ↓ as tech cost ↑ (report) | rpt | PASS | ↓ [28.0, 17.5, 17.5] GW |
| T1.9a | ERCOT | storage cap. value/MW monotone ↓ (report) | rpt | **SKIP** | all 3 rungs crashed — issue #2063 |

## Elasticity magnitudes (report-only round, per plan §2)

| Ladder | ISO | Driver → response | Implied slope |
|---|---|---|---|
| T1.1 carbon | ERCOT | $/t → load-wtd price | (70.20−24.42)/100 ≈ **0.458 $/MWh per $/t** |
| T1.1 carbon | PJM | $/t → load-wtd price | (86.34−34.44)/100 ≈ **0.519 $/MWh per $/t** |
| T1.1 carbon | ERCOT | $/t → system CO2 | (888.68−523.59)/100 ≈ **3.65 Mt per $/t** |
| T1.1 carbon | PJM | $/t → system CO2 | (1961.4−996.7)/100 ≈ **9.65 Mt per $/t** |
| T1.3 gas | ERCOT | 0.5×→1.5× → load-wtd price | (35.37−12.54)/1.0 ≈ **22.8 $/MWh per unit gas-factor** |
| T1.3 gas | PJM | 0.5×→1.5× → load-wtd price | (46.96−23.77)/1.0 ≈ **23.2 $/MWh per unit gas-factor** |

Both ISOs' carbon-price → price slope (0.458, 0.519 $/MWh per $/t) sits at or
just **above** the plan's pre-registered 0.37-0.45 t/MWh marginal-emission-rate
band (the expected slope if the marginal unit in gas-marginal hours is a
~0.40 t/MWh gas-CC). This is a magnitude cross-check, not a gate (plan §2:
"these become gates only after a baseline round establishes the model's own
bands") — flagged here as the first baseline reading, not a finding to
action. The gas-factor → price slope (~23 $/MWh per unit) has no
pre-registered band; recorded for future baseline comparison.

## Findings

### Finding 1 (CRITICAL — crash, not a directional result): T1.6 and T1.9 could not be scored at all

All 3 ERCOT T1.9 rungs and both NEISO T1.6 rungs crashed with
`AttributeError: 'ScenarioConfig' object has no attribute
'ira_other_clean_75pct_year'`. Traced to `src/market_sim/policy/ira.py:131-159`
(`ira_phaseout_fraction`), which references two `ScenarioConfig` fields
(`ira_other_clean_75pct_year`, `ira_other_clean_50pct_year`) that were never
added to `scenarios.py` — only `ira_other_clean_last_full_year` and
`ira_other_clean_phaseout_end` exist. The function is called from
`model/storage.py:917` (storage entry-economics/value-stack) and
`model/capacity.py:1572` (geothermal LCOE credit), so it fires whenever a
storage or geothermal entry candidate is evaluated for a year past
`ira_other_clean_last_full_year` (default 2028) — which any 2026-2030+
forecast horizon will eventually reach. **This is not confined to T1.6/T1.9**:
it is a latent crash risk for every forecast run (including the planned P-3A
full-horizon 2026-2050 runs) whose storage/geothermal entry screen reaches
a post-2028 candidate year. Filed as
[jessicacohen554-cyber/market-simulator#2063](https://github.com/jessicacohen554-cyber/market-simulator/issues/2063).

Because the rung solves failed, `T1.6a`'s `le_target` rule scored a **vacuous
PASS** ("all ≤ 1.0" over an empty series) — flagged here so it is not read as
a genuine confirmation that the REC dual respects the ACP ceiling; that claim
is simply untested this round.

### Finding 2 (directional FAIL): ERCOT T1.4a — scarcity hours non-monotone across the demand-growth ladder

`scarcity_hours` for `demand_growth_path` ∈ {low, mid, high} = **[34, 0, 58]**
— a U-shape, not the pre-registered monotone-↑. Root cause: the **low**-demand
rung retires 10.18 GW of thermal capacity over 2026-2030 while **mid** retires
none and **high** retires none (entry stays flat at 3.31 GW for low/mid,
jumping only at high) — i.e. the lower-growth path is the one that loses the
most capacity, and that capacity loss (not organic demand) is what produces
its scarcity hours. `reserve_margin_final` still falls monotonically
(0.086 → 0.031 → −0.042), so the load ladder's demand mechanism itself is
correct; the anomaly is specifically in how the retirement/reliability-floor
screen (`model/capacity.py`, evolution steps 2 "economic retirement" and 6
"reserve-margin adequacy backstop") responds to the lower-demand price path.
Mechanism hypothesis: a discrete retirement-threshold crossing in the
attainable pro-forma net-revenue screen that a small load-level shift near
the boundary flips only in the `low` case, with the entry screen not
re-evaluating adequacy in light of that same-year retirement before scarcity
is realized (one-pass evolution — no within-year convergence, by design —
can produce exactly this kind of discontinuity). Filed as
[jessicacohen554-cyber/market-simulator#2064](https://github.com/jessicacohen554-cyber/market-simulator/issues/2064).

### Finding 3 (expected, documented — not a new issue): T1.2a SKIPs on both ISOs

Both ERCOT and PJM SKIP the mass-cap/adder duality check because neither ISO
has a *live* covered mass-cap program in this config (ERCOT has none; PJM
RGGI is inert per the D1 audit in the plan). This SKIP is explicitly
anticipated by the ladder's own note in `run_driver_battery.py` ("a SKIP here
is therefore a mass-cap WIRING finding to route to P-1A, not a harness
failure") — routed here as confirmation, not a new issue. The G-20/G-22 AS
co-opt lane and the mass-cap wiring gap (audit D1) already own this; no new
filing.

### Finding 4 (report-only observation): T1.7a on PJM passes vacuously — the net-CONE signal expresses through entry, not retirement, in a 5-year window

`retired_thermal_gw` is flat at 0.0 across all three PJM net-CONE rungs
(0×, 1×, 2×), so the monotone-↓ check technically passes but on a
constant series — it is not evidence the retirement screen actually responds
to net-CONE within this horizon. The net-CONE signal *does* show up
elsewhere: `entry_thermal_gw` rises 15.55 → 16.0 → 24.0 GW and
`reserve_margin_final` rises −0.093 → 0.009 → 0.049 as net-CONE scales
0×→2×, both directionally consistent with capacity revenue mattering more to
new entry than to retirement over a short 2026-2030 window (retirement
decisions have more inertia and are gated by other criteria — fuel-type
years-of-negative-margin thresholds — that a 5-year window may not clear).
Not filed as an issue: this reads as a real horizon-length effect, not a bug,
but it means **T1.7a's "PASS" should not be cited as confirmation that PJM
thermal retirements respond to net-CONE** — only that they don't move
*against* it. A longer-horizon rerun (P-3A/P-3B territory) is the right place
to actually test the retirement side of this ladder.

## What this session did NOT do

Per rules 1/11/14 and the plan's standing constraints: no model-code changes,
no threshold widening, no backcast-dashboard registration (all runs are
forecast-mode 2026-2030 probes), no solve/score of 2022 or H1-2026.
