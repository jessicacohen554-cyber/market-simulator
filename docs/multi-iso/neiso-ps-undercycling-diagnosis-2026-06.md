# NEISO pumped-storage under-cycling — root-cause diagnosis (2026-06)

**Question.** The C5b storage-throughput metric (just wired into
`scripts/render_calibration_html.py:build_payload`) shows NEISO under-cycling its
storage fleet:

| Year | Model storage TWh (li-ion + PS, P1) | Actual EIA-930 TWh (battery + PS, positive part) | Δ |
|---|---|---|---|
| 2023 | 0.34 | — (series absent) | SKIPPED |
| 2024 | 0.46 | 0.31 | **+47%** |
| 2025 | 0.56 | 2.08 | **−73%** |

The pumped-storage (PS) fleet is ~1865 MW peak but discharges only ~0.28–0.375
TWh/yr (~2% capacity factor), far below a real PS fleet. Power capacity is right;
the LP is not cycling it. This doc root-causes why and states the structural fix.

**TL;DR.**
1. **2024's "+47%" is not over-cycling — the *actual* is a 2-month partial.**
   EIA-930 NEISO only began reporting the `NG: PS` storage breakout in **November
   2024** (Jan–Oct are blank). The 0.31 TWh "actual" is a Nov–Dec figure being
   compared to the model's full 8760 hours. Extrapolated to a full year it is
   ~1.8 TWh — consistent with 2025. **2023 is fully blank** (correctly SKIPPED).
   Only **2025 is a complete observation** (8736/8760 hours).
2. **2025's −73% is real, and the root cause is the collapsed price/scarcity
   tail — case (a)**, not a storage knob. The energy-only LP under-shoots NEISO's
   peak/scarcity prices, so the intraday peak-to-trough spread is too small to
   beat PS round-trip losses, and PS sits idle. This is the *same* defect the
   neiso-25 keeper already documents as its dominant residual (winter-oil
   under-generation / monthly-AGT gas granularity ⇒ collapsed `>$200` tail). PS
   under-cycling is **downstream** of it.
3. **The fix belongs to the scarcity/winter-gas workstream, not storage.** Adding
   a PS dispatch adder, shrinking duration, or otherwise tuning the storage
   formulation to reach 2.08 TWh would be fitting to the residual
   (`claude.md` #1/#11/#12) and is rejected. The in-scope, forward-valid fixes
   delivered here are (i) a measurement-coverage gate so a partial storage
   vintage is no longer scored as a full year, and (ii) the documented handoff.

---

## Step 1 — validate the actual first (rule #11 measurement alignment)

Source: `data/raw/eia-930-hourly/ISNE hourly.parquet`, column `NG: PS` (PS net
generation; positive = discharge to grid). Charging/pumping appears as load in
EIA-930, **not** as a negative `NG: PS` value, so the series is discharge-only —
which is exactly what C5b's `_actual_storage_twh` sums (positive part).

| Year | Valid (non-NaN) hours | Coverage | Raw discharge sum | Reporting span |
|---|---|---|---|---|
| 2023 | 0 / 8760 | 0% | — | none |
| 2024 | **1296 / 8760** | **14.8%** | 0.300 TWh | **Nov (576h) + Dec (720h) only** |
| 2025 | 8736 / 8760 | 99.7% | 1.933 TWh | full year |

The 2024 monthly valid-hour counts are `{Jan–Oct: 0, Nov: 576, Dec: 720}`: ISNE
added the storage breakout to its filing in Nov 2024. `load_eia_hourly_benchmark`
back/forward-fills NaNs, so the 0.300 TWh is essentially just the Nov–Dec actual
(the leading fill contributes ~0). **A 2-month throughput cannot be compared to a
12-month model output** — the "+47%" is a measurement artifact, not over-cycling.

Sanity check against EIA-860 + a plausible CF: NEISO PS is Northfield Mountain
(~1168 MW, ~10 h) + Bear Swamp (~600 MW), ~1865 MW total. 2025's ~2.0 TWh ⇒
~12% capacity factor, a normal PS duty cycle. 2024 extrapolated from Nov–Dec
(0.300 TWh / 2 months × 12 ≈ 1.8 TWh) lands in the same place. So the **complete
years agree (~2 TWh); the 2024 number is partial, not low.**

**Conclusion (Step 1):** 2023 and 2024 are incomplete reporting vintages and must
not be scored as full-year actuals. 2025 is the real observation, and against it
the model genuinely under-cycles (0.56 vs ~2.0 TWh). The diagnosis proceeds on
2025.

---

## Step 2 — diagnose the model (2025)

### Causes ruled out

- **(b) PS dispatch adder too high — NO.** NEISO is not in
  `PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO` (only `{"PJM": 10.0}`), and
  `config.pumped_storage_dispatch_adder` is `null`, so
  `resolve_pumped_storage_dispatch_adder("NEISO", cfg)` returns **0.0**. PS has
  *no* throughput cost — the adder cannot be suppressing it.
- **(c) energy capacity / duration too small — NO.** The fleet build
  (`load_eia860_pumped_storage`) yields Central 1834 MW / 18 340 MWh + Connecticut
  31 MW / 310 MWh (`PUMPED_STORAGE_DURATION_HOURS = 10`), 18.65 GWh total. Reaching
  2 TWh/yr needs ~107 full cycles (≈ once / 3.4 days). The model performs only
  **~20 cycles/yr** (0.375 TWh ÷ 18.65 GWh) — the energy cap is nowhere near
  binding. Power cap (1865 MW) is likewise non-binding.
- **(d) round-trip / SOC constraints — NO.** RTE 0.80, cyclic SOC; standard. The
  Connecticut unit's 31 MW peak discharge is its true small nameplate, not a bug.

### Confirmed cause: (a) collapsed price / scarcity tail

PS arbitrage value lives in the upper price tail and in intraday spread. The
energy-only LP reproduces NEISO's **mean** price but **collapses the tail**.
Model 2025/2024 prices (`results/calibration/neiso_probe_v2_base_2024/system.parquet`
P1, and the neiso-25 keeper's own report) vs actual RT:

| Statistic | Model 2024 | Actual 2024 RT | Model 2025 | Actual 2025 RT |
|---|---|---|---|---|
| mean $/MWh | 39.8 | 39.5 | 68.7 | 65.9 |
| p50 | 30.8 | 30.1 | — | 44.5 |
| p95 | 87.8 | 95.3 | — | 180.4 |
| p99 | 91.2 | 168.1 | — | 245.8 |
| max | **134** | **2113** | **259** | **1110** |
| hours > $200 | **0** | 43 | **14** | 290 |

The bulk/median is right; the top ~1% of hours — the scarcity hours — are
flattened from ~$170–$2100 down to ~$90–260. The decisive arbitrage metric:

- PS round-trip breakeven at RTE 0.80 requires an intraday price ratio
  **P_high / P_low > 1 / RTE = 1.25**.
- Model 2024 **median daily max/min ratio = 1.15** (below breakeven) and median
  daily spread only **$5.3**. Only **50 / 365 days** clear the 1.25 breakeven.

So on ~85% of days arbitrage is unprofitable and PS stays idle ⇒ ~20 cycles ⇒
0.56 TWh. The model is behaving *correctly given its prices*; the defect is
upstream in the prices.

### Why the tail collapses (attribution)

This is the neiso-25 keeper's own documented dominant residual:
`scarcity_pricing_enabled = false` (no NEISO operating-reserve / ORDC scarcity
price in the LP) **and** winter gas is priced at **monthly** AGT (Algonquin
city-gate) granularity (`gas_hub_basis_overlay = true`, `gas_hub_basis_daily =
false`). NEISO winter scarcity is set by cold-snap **daily** gas spikes that make
oil peakers economic; with monthly gas the model under-fires winter oil (model
0.00/0.00/0.06 vs EIA-930 0.32/0.37/1.24 TWh) and the `>$200` tail collapses
(model 0/0/14 vs actual 72/43/290). The keeper records daily-AGT winter-oil
convexity as **rejected-as-a-fitted-constant** pending measured daily-AGT spot
data (upload "U4"). PS under-cycling is one more downstream symptom of that same
collapsed tail.

---

## The fix

**No model dispatch change.** Per `claude.md` #1/#11/#12 and the task brief, the
structural fix is upstream pricing (daily-AGT winter-gas convexity / NEISO
scarcity-reserve pricing), which is the existing scarcity workstream — **handed
off, not forced here.** A PS adder/duration/RTE knob tuned to reach 2.08 TWh is
explicitly rejected (it would mask the price defect behind a storage residual).

Two forward-valid corrections are delivered in this session:

1. **Measurement-coverage gate (`src/market_sim/data/eia_loader.py`).**
   `load_eia_hourly_benchmark` now drops a storage breakout series
   (`battery` / `pumped_storage`) whose raw EIA-930 coverage is below
   `_STORAGE_MIN_COVERAGE_FRAC = 0.5`. A partial reporting vintage (NEISO PS 2024
   = 14.8% of hours; 2023 = 0%) is no longer interpolated across the year and
   scored as a full-year actual — C5b stays **SKIPPED** for those years instead of
   emitting a spurious "+47%". This generalises the existing all-NaN guard
   (coverage = 0) and is a gate on the *measured input*, not a residual knob;
   2025 (99.7% coverage) is unaffected.

2. **C5b classification / ledger (bundle `calibration_attestation.json`).**
   - 2023, 2024 → **SKIPPED** (incomplete EIA-930 storage vintage; the gate above).
   - 2025 → **MODEL MISS** (under-cycle −73%), classified as downstream of the
     C3c scarcity-tail residual the keeper already carries. It is **not** ledgered
     as an accepted limitation (the 2025 series is complete, so the miss is a real
     model defect), so C5b is out-of-tolerance and the determination is
     **NOT-YET** until the scarcity-pricing fix lands. This is the honest,
     rubric-correct outcome — the rubric is built to fail a keeper on a real,
     undocumented model miss.

## Handoff

Owner: scarcity / winter-gas workstream. The lever that will lift the PS
throughput *as a consequence* (never as a target) is daily-granularity winter AGT
gas pricing (`gas_hub_basis_daily`, sourced from measured daily AGT spot — upload
"U4") and/or a NEISO operating-reserve scarcity price
(`scarcity_pricing_enabled` / `neiso_rcpf_*`). When the `>$200` tail recovers
toward the actual 72/43/290 hours, the intraday spread will exceed the 1.25 PS
breakeven on far more days and C5b throughput will follow. **Re-score C5b only
after that fix; do not touch the storage formulation to move the number.**
