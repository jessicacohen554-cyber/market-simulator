# MISO energy + operating-reserve co-optimization (market-wide + zonal + deliverability)

**Status:** market-wide RBDC **wired into the backcast path 2026-07-02** and
confirmed structurally inert at 6-zone granularity (miso-37); locational
(zonal) reserve families added per scope §6 (`--miso-zonal-reserves`,
default off; miso-38); **10-minute reserve deliverability added 2026-07-03**
(`--miso-reserve-pergen`, default off; miso-39, the current keeper) — and
the gate-4 scarcity-tail question **closed negative**: even with reserve
supply capped at the availability-scaled 10-min class ramp, the
perfect-foresight LP clears every requirement at ≤ $23/MWh re-dispatch cost
and the published curve steps never fire (full diagnosis:
`docs/multi-iso/miso-scarcity-tail-diagnosis.md`). MISO. The in-LP MISO
analogue of the ERCOT ORDC / PJM Primary-Reserve / NYISO RCPF
co-optimization. **Zero parameters fitted to the price residual.**
**Code:** `config/reserve_config.py` (`_miso_design`, `MISO_ZONAL_ORDC_STEPS`,
`MISO_ZONAL_RESERVE_DEFAULT_ZONES`; pergen branch pooling (zone, fuel-class)
R columns bounded by hourly `Σ ramp10 × availability`),
`model/dispatch.py` (`_build_reserve_rows_pergen`; `build_variable_bounds`
accepts `(n_r, T)` hourly pergen caps), `scripts/run_calibration.py` (MISO
branch of the `run_year` co-opt chain), `runner.py` (forecast path),
constants `MISO_REGULATING_RESERVE_MW` / `MISO_RESERVE_DEMAND_CURVE_MAX` /
`MISO_RESERVE_DEMAND_CURVE_CRITICAL_MW`; probes
`scripts/probes/_miso_scarcity_bindgate.py` (deliverable-reserve bind gate
vs actual event hours, no LP re-solve) and
`scripts/probes/_miso39_tail_gate.py` (tail/timing/class-drift scorer).
**Tests:** `tests/test_reserve_config.py` (`TestMisoDesign`,
`TestMisoZonalDesign`, `TestMisoPergenDesign`), `tests/test_reserve_coopt.py`
(`TestMisoReserveCooptLP`, `TestMisoZonalReserveLP`,
`TestMisoPergenReserveLP`).
**Bundles:** `results/calibration/MISO/miso_36_coopt_flag_inert` (flag-inert
evidence probe), `miso_37_coopt_wired` (market-wide, in-LP, non-binding),
`miso_38_zonal_reserves` (zonal families), `miso_39_reserve_pergen`
(deliverability; keeper).

## The 2026-07-02 wiring discovery (honesty note)

Until 2026-07-02 the `--energy-reserve-coopt` flag was **silently inert for
MISO on the backcast path**: the co-opt dispatch-kwargs chain inside
`run_calibration.run_year` handled ERCOT/PJM/NYISO/NEISO only, and the MISO
design was reachable solely from the forecast runner (`runner.py:801`).
Every dashboard run made through `run_calibration_full.py` with the flag —
including probe `2026-07-01-miso-34-reserve-coopt` — solved an
**energy-only LP** (verified at miso-34's recorded clean sha `6712bdb`:
no MISO branch existed; and empirically by `miso_36_coopt_flag_inert`,
whose results replicate miso-35). miso-34's registered "+2/+3/+4 $/MWh
price lift vs miso-31" therefore could **not** have come from the reserve
co-opt; it was main-branch drift between the two runs' shas, misattributed.
The fix (a `run_year` MISO branch routing to the **unchanged**
`_miso_design`) is the same class as phase 1's unwired one-way link floor:
connecting existing, correct structure — not a redesign.

## The published mechanism (provenance)

MISO co-optimizes energy with its market-wide operating reserves (Regulating +
Contingency = Spinning + Supplemental) in a single clearing. When cleared
market-wide reserves fall below the requirement, MISO's VOLL-anchored
Reliability-Based Demand Curve (RBDC) sets the reserve clearing price, and
through energy/reserve co-optimization that shadow price flows into the LMP —
the scarcity tail an energy-only LP cannot produce (MISO BPM-002 "Energy and
Operating Reserve Markets" / Schedule 28 / Schedule 28-A). Market-wide
requirement magnitudes for the backcast years (BPM-002-r23 / MISO shortage-
pricing deck to PJM RCSTF, Nov 2024): Regulation 500–800 MW hourly, Spin
900/1,200 MW, Supplemental 1,110 MW, Short-Term Reserve ≥ 3,000 MW. VOLL
$3,500/MWh through the backcast window (raised toward $10,000 with a $6,000
ORDC bound only from the Sept-30-2025 tariff revision — a partial-2025
refinement deliberately not modeled).

MISO additionally enforces **minimum Zonal Operating Reserve Requirements**
per Reserve Zone (zones drawn quarterly from the IROL/RDT/SOL constraint
set; BPM-002 §3.3/§3.3.1) and prices zonal shortfalls on the published
**Zonal Operating Reserve Demand Curve** (BPM-002 §5.2.1.2 / Tariff
Schedule 28-A):

- cleared ≥ 100% of the zonal requirement → $0;
- 80–100% → **$200/MWh**;
- 10–80% → **$1,100/MWh** (Energy Offer Price Cap $1,000 + Contingency
  Reserve Offer Price Cap $100);
- < 10% → **VOLL − Zonal Regulating Reserve Demand Curve price** (the
  monthly average peaker proxy, Schedule 28 §IV; posted monthly values run
  ~$156–$222 across 2025-26 → a ~$3,300 top step).

The zonal requirement anchor is the **pre-determined largest zonal
contingency event** (Chen et al., "Market Implications of Short-Term Reserve
Deliverability…", the MISO STR design paper; BPM-002 §3.3.2).

## Model mapping

- **Market-wide family** (`miso_rbdc`, unchanged from the miso3/miso-34
  probes): requirement = MSSC (plant-aggregated common-mode, fleet-responsive)
  + `MISO_REGULATING_RESERVE_MW` (400 MW, Tier-3) ≈ 4.4 GW at 6-zone 2023;
  demand curve = piecewise ramp $0 → $3,500 (VOLL / RBDC anchor) discretized
  into ascending shortfall steps. Zone-count-agnostic
  (`zone_mask = np.ones(n_zones)`).
- **Zonal families** (`config.miso_zonal_reserves`, GATED default off; CLI
  `--miso-zonal-reserves`): one family per zone in
  `config.miso_zonal_reserve_zones` (default `MISO-South` — the sub-region
  whose reserves the RDT separates from the Midwest pool, scope §6;
  `MISO-East` is the optional Michigan-pocket second family). Requirement =
  **within-zone MSSC** (same `largest_single_contingency_mw`, masked to the
  zone — 3,953 MW for MISO-South 2023), the forward-reproducible analogue of
  BPM-002 §3.3.2's zonal minimum. Shortfalls price at the published zonal
  curve (`MISO_ZONAL_ORDC_STEPS`: 20% @ $200, 70% @ $1,100, 10% @ $3,300).
  The zonal family shares the market-wide reserve class, so a South reserve
  MW counts toward both constraints (nested, like NYISO East ⊂ NYCA).
- **Reserves** = per-zone aggregate reserve-eligible thermal headroom
  (`RESERVE_FUEL_TYPES`); the reserve-balance-row dual is persisted as
  `reserve_price` in `system.parquet`.

Nothing is fitted to the LMP residual: requirements are measured/derived
reliability quantities and both curves are the cited market design.

## Results

- **miso-37 (market-wide only, 6 zones, 2023-25):** reserve clearing price
  **exactly $0 in all 26,280 hours**; dispatch differs from the energy-only
  LP only by degenerate-tie reshuffling (max LMP delta $0.29). Same result
  as the 3-zone `miso3_reservecoopt` probe and the PJM campaign
  (`pjm-reserve-ordc.md`): the ~4.4 GW market-wide requirement never binds
  against tens of GW of idle eligible headroom. Congestion does not change
  this — the market-wide sum is congestion-blind. Per CLAUDE.md #1/#11 the
  requirement was **not** inflated and the penalty **not** raised; the
  structure is retained as the baseline.
- **miso-38 (+ MISO-South zonal family):** see the dashboard run report —
  the structural gate is whether South scarcity hours price the zonal curve.
  Outcome: fires 266/287/875 h but only at re-dispatch opportunity cost
  ($8–21 max); the >$200 tail stays 0 h.
- **miso-39 (+ 10-min deliverability, `--miso-reserve-pergen`; KEEPER):**
  reserve supply per (zone, fuel-class) pool capped at the
  availability-scaled 10-minute class ramp, with joint P+R ≤ cap per
  pool-hour so reserve competes with energy at the pool margin. The zonal
  family fires more (59/64/207 h; max $11/$11/$23) and the bind-gate probe
  had predicted deliverable-reserve shortfalls coinciding with 28/38 of
  2025's actual DA-tail hours — but the LP relieves every one by re-timing
  ~100 MW of South thermal/exports, always cheaper than the $200 first step.
  Tail 0 h, volumes/fit byte-comparable to miso-38. **Empirical closure:**
  no admissible supply-side reserve structure can price MISO's curve steps
  under deterministic perfect-foresight hourly dispatch; the residual is
  commitment posture + RT sub-hourly transients + the missing Midwest
  locational family (`docs/multi-iso/miso-scarcity-tail-diagnosis.md`).

## Memory note

The co-opt LP nearly doubles constraint-matrix nonzeros (per-zone shared-
headroom rows ≈ n_eligible nnz × 8760). On the 15 GB box the 6-zone co-opt
build peaked ~15.9 GB and was OOM-killed once; a 12 GB swapfile absorbs the
~2-3 GB transient (`MALLOC_ARENA_MAX=1 MARKET_SIM_HIGHS_THREADS=1` still
required). **Do not** add per-generator reserve rows (memory-infeasible at
MISO plant scale).

## How to run

```bash
MALLOC_ARENA_MAX=1 MARKET_SIM_HIGHS_THREADS=1 PYTHONPATH=.:src \
  .venv/bin/python scripts/run_calibration_full.py --iso MISO \
  --year 2023 2024 2025 --out-dir results/calibration/MISO/<name> \
  <miso-35 keeper flags> --energy-reserve-coopt [--miso-zonal-reserves] \
  [--miso-reserve-pergen]
```
