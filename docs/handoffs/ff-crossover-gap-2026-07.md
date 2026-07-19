# FF-1D — T1-X crossover: the backcast→forecast input gap (ERCOT + PJM)

_Findings only. No tuning, no default change (plan §7.6; CLAUDE.md rules 1/11/13). This
session RUNS the FF-0E crossover instrument and reports; it changes nothing._

## 0. What was run

Two crossover bundles on the FF-0E hindcast harness (`scripts/run_capacity_hindcast.py
--crossover --vintage 2023`), each seeded from the **EIA-860 2023 vintage** and evolved
2023→2027 (2023–2025 on realized demand + realized gas; 2026–2027 on pure forward drivers):

```
python scripts/run_capacity_hindcast.py --iso ERCOT --crossover --vintage 2023 \
  --start-year 2023 --end-year 2027 --out-dir results/hindcast/ercot-2023-2027-crossover
python scripts/run_capacity_hindcast.py --iso PJM   --crossover --vintage 2023 \
  --start-year 2023 --end-year 2027 --out-dir results/hindcast/pjm-2023-2027-crossover
```

Both solved `[2023, 2024, 2025, 2026, 2027]`, no bridge year, **leakage guards clean**
(`assert_pipeline_from_vintage` + `assert_forward_drivers` returned `[]` for both — no
post-2023 pipeline unit enters, forward years consult no backcast-gated loader). Scored with
`scripts/score_crossover.py`; registered on the forecast-validation namespace
(`frontend/data/hindcast/{ercot,pjm}-2023-2027-crossover.json`, `kind="crossover"`).

**Rule-12 scheduling (measured).** Run **sequentially**, not concurrently: plan §2.4 records
per-plant multi-zone LPs at ≈8.6 GB each ("two cannot co-run on a 15 GB box, measured OOM").
PJM peaked at ≈7.0 GB RSS here (ERCOT ≈2.8 GB) on a 15 GB box, so overlap was declined by
policy. Years sequential within each invocation (runner loop). Wall/RSS per solve-year:

| ISO | 2023 | 2024 | 2025 | 2026 | 2027 | peak RSS |
|---|--:|--:|--:|--:|--:|--:|
| ERCOT | 132s | 163s | 163s | 208s | 226s | ~2.8 GB |
| PJM | 367s | 226s | 208s | 207s | 221s | ~7.0 GB |

(`data/clean` was absent in the fresh checkout — gitignored — so `scripts/regenerate_clean.py`
was run first; ~33 min, one-time.)

## 1. Quarantine holds BY CONSTRUCTION (rule 22)

Confirmed the scorer **structurally refuses** to read any bench/actual for a year ≥ 2026 —
every bench/actual loader path is guarded by `_assert_scoreable_year` *before* a file is
opened. Directly exercised:

| call | result |
|---|---|
| `load_bench_year("ERCOT", 2026)` | `ValueError: year 2026 is quarantined …` |
| `load_bench_year("PJM", 2027)` | `ValueError: year 2027 is quarantined …` |
| `crossover_actual_co2("ERCOT", [2026])` | `ValueError: year 2026 is quarantined …` |
| `_assert_scoreable_year(2025)` | returns `2025` (passes) |

The forward years (2026–2027) reach only the model's own `year_<y>.parquet` (invariants /
plausibility, `scored=False`). No H1-2026 file is opened. Dispatch skill and capacity events
are scored on **2023–2025 only**.

## 2. The measured input gap — dispatch skill 2023–2025

`input_gap = |forecast_mode_err| / |keeper_backcast_err|` (per metric per year). 1.0 = the
forward drivers reproduce the keeper's backcast-overlay skill; >1 = the forecast is worse. The
sign column is the **direction** of the forecast-mode error (from `forecast_signed`).

### ERCOT (keeper `2026-07-18-ercot82-measured-rtolcap`)

| metric | 2023 | 2024 | 2025 | forecast-mode direction |
|---|--:|--:|--:|:--|
| C1 fuel-mix (Σ\|Δ\| TWh) | **8.7×** | **9.9×** | **44.9×** | coal → 0; ST_GAS collapses |
| C3a price mean | **3.2×** | **21.1×** | **7.5×** | **under**-priced (−69% / −44% / −25%) |
| C3b monthly NRMSE | 2.6× | 1.7× | 3.2× | flatter than actual |
| C5a CO2 (full-plant) | **19.6×** | **92.3×** | **43.6×** | **under** (−49% / −46% / −55%) |

Actual load-weighted RT LMP $64 / $31 / $36; model ≈ $20 / $17 / $27. Actual CO2 ≈172 Mt/yr;
model ≈88–93 Mt.

### PJM (keeper `2026-07-18-pjm-115-unit-only`)

| metric | 2023 | 2024 | 2025 | forecast-mode direction |
|---|--:|--:|--:|:--|
| C1 fuel-mix (Σ\|Δ\| TWh) | **11.0×** | **13.3×** | — (2025 EIA-923 incomplete) | coal → 0 |
| C3a price mean | **0.66×** | 2.1× | 2.1× | +3% (2023) → **−19%** (2025) |
| C3b monthly NRMSE | 0.64× | 1.3× | 1.4× | on-shape 2023, drifts |
| C5a CO2 (full-plant) | **25.1×** | **13.3×** | **20.0×** | **under** (−46% / −42% / −58%) |

Actual RT LMP $30 / $31 / $46; actual CO2 ≈264 / 273 / 292 Mt (coal ≈115–138 Mt of it).
Notably PJM's **price** skill starts near-keeper (2023 input-gap 0.66×, a PASS) and degrades
only as the fleet drifts — the gap is concentrated in **volume/mix/CO2**, not price level.

## 3. Capacity events 2023–2025 vs EIA-860 registry actuals

| | ERCOT | PJM |
|---|---|---|
| thermal GW retired (model / actual) | **21.1 / 1.53** (+1273%, 97.6% false) | **0.06 / 11.1** (−100%) |
| unit recall >300 MW | 1/3 | **0/17** |
| additions (model / actual) | 16.0 / 55.4 GW | 17.5 / 24.1 GW |
| worst-miss retire | gas_ct 9.8 (act 0.5), gas_st 11.3 (act 0) | coal 0 (act 6.9), gas_ct 0 (act 3.5) |
| worst-miss add | **solar 0 (act 25.1)**, gas_ct 0 (act 3.7) | gas_cc 2.5 (act 8.5), storage 0 (act 0.3) |

**The two ISOs miss in opposite directions** — ERCOT force-retires 21 GW of peakers/steam it
should have kept; PJM keeps 11 GW of coal it should have retired. This is the signature of the
per-fuel consecutive-loss retirement rule (`retirement_rule="legacy"`,
`retirement_consecutive_years=2`) racing fuels differently under each ISO's margin structure —
exactly plan §1.2 row 1 (the FF-0C/FF-1A redesign lane), now confirmed at the crossover level
in both directions.

## 4. Forward years 2026–2027 (invariants / plausibility only — no skill scored)

| ISO | year | model CO2 (Mt) | gen (TWh) | dispatch ≥ 0 | reserve margin |
|---|--:|--:|--:|:--|--:|
| ERCOT | 2026 | 131.9 | 281.5 | True | 8.1% |
| ERCOT | 2027 | 140.0 | 316.6 | True | 6.7% |
| PJM | 2026 | 277.9 | 781.1 | **False** | (over-supplied) |
| PJM | 2027 | 282.2 | 798.5 | **False** | (over-supplied) |

- **ERCOT forward adequacy collapses** (RM 30.7% → 6.7%); the I1–I14 sidecar flags I6
  (26.9% of thermal retired in one year), I7 (reliability floor breached), I12 (RM band),
  I3 (2027 slack 0.01%), and an I14 WARN ($254.7 LW price in 2027 — scarcity finally forming
  only once the over-thinned fleet is short). This is plan §1.2 row 4's two-phase trajectory,
  visible inside the 5-year crossover window.
- **PJM `dispatch_nonneg=False` for 2026–2027** is a forward-plausibility flag (a dispatch
  array element < −1e-6). PJM's I1–I14 set is 14/14 PASS, so this is not an adequacy break;
  it is a numerical/column artifact worth a follow-up look (candidate: a storage or
  net-flow column bleeding into the `res.dispatch` slice the plausibility check reads).
  Context only — no bench is involved.

## 5. Decomposition — which forward DRIVER explains each large gap

The 2023 solve is on the **correct 2023-vintage fleet** (retirement first bites at the 2025
step), so the 2023 column isolates **dispatch-side drivers**; 2024–2025 add the
**fleet-evolution** driver on top. Three drivers account for essentially the whole gap.

### D1 — Coal dispatched to zero (dominant CO2 + fuel-mix driver, both ISOs)

Coal **capacity is present** (ERCOT 14 GW, PJM 37 GW; coal `plant_groups` in the fleet) but
generates **~0 TWh** (ERCOT COAL_PRB 0 vs 45, COAL_LIGNITE 0 vs 15; PJM COAL_BIT 0 vs 103).
Coal is monthly-priced from data (`coal_plant_monthly_pricing=True`), so this is **not** a
coal fuel-price overlay gap. The driver is the **coal commitment/must-run structure**: the
calibrated backcast keepers keep coal committed (CAMPD-binned must-run/take-or-pay tranches +
per-plant passthrough floors — ERCOT `coal_prb_passthrough_floor=0.76`, PJM
`coal_bit_passthrough_floor=0.65`); on the forecast path the coal-commitment flags are all
off and the exact-`0` (not merely low) coal output indicates **no binding must-run tranche
attaches to the vintage-2023 coal units** — they enter as fully-economic and the cheap
realized-gas + oversupplied-renewable stack prices them out for all 8760 h. This alone is
~−63 Mt (ERCOT) / ~−115 Mt (PJM) of CO2, i.e. the bulk of the C5a and C1 gaps.

→ **Route: L-INP / L-CAP — NEW plan §1.2 row (see §6, row A).** Coal take-or-pay is
rule-13-admissible (regenerates for a forward year from contract data), so the fix is
*promoting the coal-commitment structure onto the forecast/vintage fleet* (bin-coverage +
`coal_takeorpay_from_data`), **not** re-importing a measured outcome. Findings-only here.

### D2 — ERCOT in-year scarcity never forms (dominant price driver, ERCOT)

On the correct 2023 fleet ERCOT prices at mean ≈$20 with **max LMP $29 and zero hours >$200** —
the ORDC/co-opt scarcity footing never fires because the oversupplied vintage fleet (RM 26%) +
**statistical outages** (`outage_source="statistical"`) never form tightness. The keeper carries
ERCOT's measured availability envelope / outage windows and calibrated co-opt that create the
scarcity the merit-order body cannot. This is plan §1.2 row 2 (ERCOT screen revenue + in-year
scarcity formation, the G-20/G-22/G-31 blocker), now confirmed **at the dispatch level** by the
crossover.

→ **Route: existing plan §1.2 row 2 (L-SCAR).** The measured availability envelope is a
rule-13 overlay whose forward analogue is the correlated-outage derate (FF-1B, default-off);
that the overlay carries most of the backcast's scarcity skill is a **finding about
forecast-input quality, never a change**.

### D3 — Fleet-evolution error (compounds 2024→2025→forward, both ISOs)

The legacy consecutive-loss per-fuel retirement rule over-retires ERCOT (21 GW gas_ct+gas_st,
97.6% false) and under-retires PJM (misses the 11 GW coal wave, recall 0/17); the entry screen
under-builds both (ERCOT solar 0 vs 25 GW; PJM gas_cc 2.5 vs 8.5 GW). ERCOT's 2025 column
carries this on top of D1/D2 (its C1 gap jumps 9.9×→44.9× once 21 GW retires).

→ **Route: existing plan §1.2 row 1 (retirement rule, L-CAP, FF-0C/FF-1A) + row 3 (ERCOT
solar entry, L-CAP).** No new row — the crossover corroborates the open lanes.

## 6. Proposed NEW plan §1.2 rows (L-INP — for the owner/plan-keeper to adopt)

> Appended as candidates; not yet written into §1.2 (this is a findings session). Each is an
> **input/driver** defect, not a tuning knob.

- **Row A — forecast coal commitment structure (L-INP/L-CAP).** Coal collapses to 0 TWh in
  forecast mode on both ISOs because the CAMPD must-run/take-or-pay bin structure does not
  attach to the forecast/vintage-2023 coal fleet. Driver, not overlay: coal take-or-pay is
  forward-admissible (rule 13). Owned files: `data/fleet.py` (CAMPD bin coverage for the
  vintage fleet), `coal_takeorpay_from_data` wiring, `config/scenarios.py`. Evidence: this doc
  §2–§5, D1.
- **Row B — crossover/forecast renewable-CF weather basis (L-INP, low-priority verify).** The
  harness pins `weather_year=2025` for all crossover years so 2023/2024 renewable shapes are
  drawn from 2025 weather, not their own year. This is a deliberate crossover construction
  (forward demand anchors on the last realized year) but may inflate the 2023/2024 C1/C3b gap
  slightly; worth a bounded check that per-year realized renewable CF is used for the scored
  2023–2025 years. Not asserted as a defect — flagged for verification. Owned files:
  `data/renewables.py`, harness `weather_year` pin.

Everything else routes to **existing** rows (§1.2 rows 1/2/3/4).

## 7. Artifacts

- Bundles: `results/hindcast/{ercot,pjm}-2023-2027-crossover/` (meta + `crossover_score.json`
  + per-year parquets/ledgers).
- Reports: `docs/hindcast-reports/{ercot,pjm}-2023-2027-crossover-crossover-2026-07-19.md`.
- Dashboard sidecars: `frontend/data/hindcast/{ercot,pjm}-2023-2027-crossover.json`
  (`kind="crossover"`); `docs/codebase-site/forecast-validation.html` regenerated.

**Bottom line.** The measured overlays carry most of the backcast skill: strip them and both
ISOs' dispatch degrades 2–90× on volume/CO2, with a smaller (ERCOT large, PJM modest) price
gap. The gap decomposes cleanly into three named drivers — coal-commitment structure (D1, new
row A), ERCOT in-year scarcity formation (D2, §1.2 row 2), and the retirement/entry screens
(D3, §1.2 rows 1/3) — none of which is closable by re-importing a measured outcome.
