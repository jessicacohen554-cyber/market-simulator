# FINDING — nwpp-45: C1's `CC_REGULAR` row is NOT a `CC_REGULAR` defect. It is a demand-basis gap, and the miss is **0.219 TWh**.

**Lane:** NWPP-45 · **Date:** 2026-09-22 · **Branch:** `claude/nwpp-45-cc-regular-defect-2j8uuc`
**Keeper / control:** `2026-09-20-nwpp-44-measured-take`, bundle `results/calibration/nwpp44_takeorpay_reg`
**LP spent by this session: ZERO** (rule 32 `[R-SHARD]` (a)). Every number below is zero-LP, from the
keeper's committed `hourly/` sidecars, its registered payload, the committed benchmark parts, and a
`fleet_only=True` rebuild on the keeper's own recipe.
**Nothing was armed, nothing was solved, no keeper moved, no mechanism was selected.**

---

## 0. Status in one line

**The chartered defect is misdiagnosed in the record on two counts, and neither correction is
cosmetic.** (1) The C1 volume band is **±8.00 TWh**, not the ±5.41 the predecessor computed by hand.
The model-vs-actual error is indeed **−8.219 TWh** and is not disputed anywhere below — but the
**band overrun is 0.219 TWh**, 2.7 % of the band. Those are different quantities and the record
conflates them: what stands between this keeper and a C1 PASS is 0.219 TWh, while what stands
between it and a correct 2023 `CC_REGULAR` is 8.219.
(2) The shortfall is **not in `CC_REGULAR`**: it is a system-level energy-requirement gap of
**9.645 / 12.144 / 9.107 TWh** that the marginal class absorbs because every non-thermal class is
separately pinned to a measured budget. The gap's provenance is an exact, verified identity between
the **EIA-930 telemetry basis** the LP's demand is built on and the **EIA-923 plant basis** C1 scores
against. **The obvious fix is refuted before any LP is spent** (§5). The remedy is an owner-scope
question, not this lane's to take (§8).

---

## 1. THE RECORD CORRECTION — the band is ±8.00 TWh and the miss is 0.219 TWh

`calibration_verdict._fuelmix_vol_band` is `min(max(2 % ISO-load, 3 % actual-gen), 8 TWh)`. For NWPP
2023 the terms are `max(5.409, 8.405) = 8.405`, and **the 8 TWh cap binds**. The predecessor's
RESULT §1c.3 computed ±5.553 for 2024, noticed it contradicted the keeper's own `metrics.json`, and
correctly declined to score on it — but the wrong band then reached `keepers/NWPP.json`, the
mechanism-matrix stamp and the PRECOMMIT's §6.1 risk analysis, where it is still quoted as ±5.41 /
±5.55 / ±5.77.

Scored through `scripts/calibration_verdict.py` on the committed artifacts — **every gated C1 row, all
three years**:

| year | class | status | model | actual | Δ TWh | share pp | band |
|---|---|---|---|---|---|---|---|
| 2023 | **CC_REGULAR** | **FAIL** | 47.996 | 56.215 | **−8.219** | −2.32 | ±8.00 |
| 2023 | CC_CHP | PASS | 7.352 | 6.653 | +0.699 | +0.34 | ±8.00 |
| 2023 | CT_PEAKER | PASS | 2.746 | 7.089 | −4.343 | −1.52 | ±8.00 |
| 2023 | ST_GAS | PASS | 0.126 | 1.448 | −1.322 | −0.47 | ±8.00 |
| 2023 | ST_CHP | PASS | 0.034 | 0.376 | −0.342 | −0.12 | ±8.00 |
| 2023 | COAL_PRB | PASS | 25.623 | 25.242 | +0.381 | +0.46 | ±8.00 |
| 2023 | COAL_BIT | PASS | 18.264 | 14.594 | +3.670 | +1.54 | ±8.00 |
| 2023 | COAL_WC | PASS | 0.411 | 0.560 | −0.149 | −0.05 | ±8.00 |
| 2024 | CC_REGULAR | PASS | 50.590 | 56.913 | −6.323 | −1.42 | ±8.00 |
| 2024 | CT_PEAKER | PASS | 4.207 | 7.389 | −3.182 | −1.03 | ±8.00 |
| 2024 | ST_GAS | PASS | 0.224 | 4.617 | −4.393 | −1.51 | ±8.00 |
| 2024 | COAL_PRB | PASS | 24.125 | 21.030 | +3.095 | +1.43 | ±8.00 |
| 2024 | COAL_BIT | PASS | 12.380 | 12.832 | −0.452 | +0.03 | ±8.00 |
| 2025 | *(all 8 rows)* | SKIPPED | — | — | — | — | preliminary EIA-923 vintage |

**The share leg is not what fails.** 2023 `CC_REGULAR` reads −2.32 pp against a ±3.0 pp gate — inside.
The single failing leg is **volume, by 0.219 TWh.**

**This does not make the defect harmless and is not offered as a reason to relax anything.** It
changes what the defect *is*: a 0.219 TWh band overrun sitting on top of an 8.2 TWh model-vs-actual
error whose cause is elsewhere entirely — which is exactly what rule 14 `[R-ACCURATE]` predicted the
NWPP-44 promotion would expose.

---

## 2. What the shortfall is NOT — the charter's own three questions, answered

The charter set the diagnostic rule: *"A uniform shortfall points at capacity/availability; a peak
shortfall at commitment or offer level."*

### 2.1 It is UNIFORM in load — so it is not commitment, not offer level, not peak

`hourly/class_hourly_<y>.parquet` (P1) against the CEMS actual assembled from the committed benchmark
part, binned by the model's own hourly system demand:

| load quintile | 2023 model | 2023 act | **Δ** | | 2025 Δ |
|---|---|---|---|---|---|
| Q1 (low) | 9.701 | 11.340 | **−1.638** | | −0.751 |
| Q2 | 9.152 | 11.265 | **−2.113** | | −0.487 |
| Q3 | 8.854 | 11.212 | **−2.358** | | −0.415 |
| Q4 | 9.224 | 11.974 | **−2.749** | | −0.569 |
| Q5 (high) | 11.065 | 13.442 | **−2.377** | | −0.719 |

In mean MW the 2023 model runs **5,537 / 5,224 / 5,053 / 5,265 / 6,316** against an actual
**6,472 / 6,430 / 6,400 / 6,834 / 7,672** — roughly **−900 to −1,400 MW in every hour of the year**,
with no quintile carrying a disproportionate share. A commitment or offer-level defect concentrates in
the hours where the offer is pivotal; this does not.

### 2.2 It is NOT capacity- or availability-limited

Rebuilding the keeper fleet on its own recipe (`scripts/probes/_nwpp45_ccregular_phase0.py`,
`run_year(..., fleet_only=True)`, the sanctioned `replay_keeper` path):

| | 2023 |
|---|---|
| `CC_REGULAR` LP rows | 91 |
| Σ `pmax` | 11,751.1 MW |
| envelope `pmax × availability` mean / min / max | 8,944 / 6,097 / 10,610 MW |
| mean availability | 0.7611 |
| **envelope energy** | **78.347 TWh** |
| **dispatched** | **47.996 TWh** |

**~30 TWh of unused headroom.** The class is nowhere near its bound. Band-wise the envelope is
`committed` 31.919 / `econlo` 19.491 / `econhi` 19.491 / `peak` 7.445 TWh against dispatch of
19.489 / 11.448 / 11.418 / 5.641.

### 2.3 It is NOT coal displacing gas locally

Per-zone, per-family, CEMS basis (model − actual, TWh):

| zone | 2023 COAL / GAS | 2024 COAL / GAS | 2025 COAL / GAS |
|---|---|---|---|
| NWPP-EAST | **+0.19** / **−7.91** | +0.35 / −6.57 | −6.20 / −2.35 |
| NWPP-INLAND | −2.03 / −2.04 | −1.34 / −3.05 | −0.89 / −1.94 |
| NWPP-NW | −2.42 / −3.88 | −2.58 / −6.27 | −2.96 / −4.81 |
| NWPP-OR | +0.00 / −1.13 | +0.00 / −0.77 | +0.00 / −1.11 |
| NWPP-SNV | −1.05 / −1.82 | −1.45 / −0.86 | −1.47 / +0.07 |

**Every zone is short of nearly everything, in every year.** There is no zone where the model
over-generates and none where a coal surplus offsets a gas deficit. NWPP-EAST is the extreme case —
its coal lands on the actual in 2023 while its gas runs **4.804 against 12.716 TWh** — and it is the
shape of a zone that is never asked for the energy, not of a zone whose merit order is inverted.

The zonal prices agree: four of the five zones cap at **$144.12 in 2023 and $40.88 / $41.25 in
2024 / 2025**, i.e. the most expensive unit the LP ever needs in NWPP-EAST / INLAND / NW / OR is a
$41/MWh offer. There is no scarcity anywhere in the footprint outside NWPP-SNV.

---

## 3. What it IS — the demand-basis identity, verified to 0.05–0.11 TWh in all three years

The LP generates what it is told to serve. It is told to serve a number built from **EIA-930 BA
telemetry**; it is scored against a number built from **EIA-923 plant reports**. All figures TWh.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| EIA-930 pool `Demand (Adj)` **[A]** | 284.206 | 290.540 | 293.483 |
| EIA-930 pool `Net generation (Adj)` **[B]** | 277.576 | 287.423 | 298.830 |
| → footprint net imports `A−B` | +6.630 | +3.116 | −5.346 |
| GRID Desert-SW legs subtracted **[C]** | 7.115 | 9.774 | 10.131 |
| **MODEL LP demand** | **270.461** | **277.649** | **288.698** |
| check `B − C` | 270.461 | 277.649 | 288.698 |
| | | | |
| **C1 benchmark `classFull` total [E]** | **280.154** | **289.852** | **297.913** |
| **MODEL total generation [F]** | **270.509** | **277.708** | **288.805** |
| **SCORED GAP `F − E`** | **−9.645** | **−12.144** | **−9.107** |
| | | | |
| decomposition (a) GRID-SW leg `−C` | −7.115 | −9.774 | −10.131 |
| decomposition (b) 930 `[B]` vs 923 `[E]` | −2.578 | −2.429 | +0.917 |
| (a)+(b) | −9.693 | −12.203 | −9.214 |
| residual (storage round-trip + slack) | 0.049 | 0.059 | 0.107 |

**`B − C` reproduces the LP's demand array to the milli-TWh in every year**, so the construction is
not in doubt and neither is the arithmetic. The gap the thermal residual must absorb is the whole of
`F − E`, and **the non-thermal classes absorb none of it**: hydro, nuclear, wind, solar, biomass and
OTHER are within **0.056 / 0.057 TWh** of actual in 2023 / 2024 (2025 is +4.904, from hydro +2.760 and
OTHER +2.161, and moves the gap the *other* way). Every non-thermal class is pinned to its own
measured budget or CF profile, so the entire residual falls on thermal — and within thermal on the
class that is marginal in the most hours.

**That is why `CC_REGULAR` fails and nothing else does.** Its own miss (−8.219) is *smaller* than the
system gap it is absorbing (−9.645).

### 3.1 The footprints are identical — this is a SOURCE disagreement, not a boundary error

Checked rather than assumed. `_iso_plant_ids("NWPP") → build_zone_lookup("NWPP")` yields 1,083 ORIS
codes, of which 881 match eGRID 2023. **All 881 carry a `BACODE` in the 17-member `NWPP_BAS`, and
zero pool-BA plants are missing from the benchmark footprint.** The benchmark's plant set and the
demand construction's BA set are the same footprint. The two sources simply disagree about it.

---

## 4. The GRID seam, measured — 73 % of the 2023 gap and 80 % of the 2024 gap

`nwpp_net_interchange` subtracts GRID's exports to PNM / SRP / WALC on the stated principle that they
are *"Desert-Southwest resources the fleet does not own"* — **7.115 / 9.774 / 10.131 TWh**. That
single term is the dominant component of the gap in all three years.

GRID's own EIA-930 book against its own plants:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| GRID `Net generation (Adj)` | 16.774 | 18.624 | 17.716 |
| of which `NG: COL` / `NG: NG` / `NG: WND` / `NG: SUN` | 4.143 / 10.177 / 2.073 / 0.381 | 2.816 / 13.211 / 2.179 / 0.418 | 3.166 / 12.135 / 2.003 / 0.412 |
| GRID `Demand` | 0.000 | 0.000 | 0.000 |
| **eGRID plants with `BACODE == GRID`** | **1** (55328 Hermiston, OR) | — | — |
| **their generation** | **3.918** | — | — |
| **GRID NG not attributable to a footprint plant** | **12.856** | — | — |

So GRID's BA telemetry carries **12.856 TWh** the plant set does not contain — including **4.143 TWh
of coal**, which Hermiston (a gas CC) cannot have produced.

**And GRID is not the only one.** Per-BA, 2023, EIA-930 `Net generation (Adj)` against the eGRID
annual generation of the plants eGRID assigns to that BA (TWh):

| BA | 930 NG | eGRID plant gen | Δ |
|---|---|---|---|
| BPAT | 79.709 | 94.878 | **−15.169** |
| **GRID** | 16.774 | 3.918 | **+12.856** |
| PGE | 7.823 | 14.737 | −6.914 |
| PSEI | 8.057 | 13.511 | −5.454 |
| GCPD | 7.996 | 4.131 | +3.865 |
| PACW | 5.225 | 8.619 | −3.394 |
| NEVP | 33.116 | 36.242 | −3.126 |
| WAUW | 0.553 | 3.377 | −2.824 |
| PACE | 52.213 | 54.848 | −2.635 |
| NWMT | 19.051 | 17.737 | +1.314 |
| *(7 others, each \|Δ\| < 0.4)* | | | |
| **TOTAL** | **277.299** | **298.593** | **−21.294** |

The pattern is the signature of **generation-only balancing authorities** (GRID and AVRN both report
zero demand) plus federal-hydro marketing: EIA-930 attributes output to the telemetry BA while eGRID /
EIA-860 attribute the plant to its physical host. `GRID +12.856` against `PGE −6.914 + PACW −3.394 =
−10.308` is suggestive but **not established here**, and this lane does not claim it — resolving it
needs a plant-level EIA-930 attribution the repo does not carry. What *is* established is the size:
**21.3 TWh, 7.1 % of the footprint's generation, on an identical plant set.**

---

## 5. THE OBVIOUS FIX IS REFUTED — before any LP was spent

The construction's stated principle is *"the LP fleet is never asked to generate energy that EIA-860
places outside the footprint."* Applied literally, the subtrahend should be GRID's **out-of-footprint
generation** (12.856 TWh in 2023), not its **Southwest interchange legs** (7.115 TWh). Under that
correction:

```
model demand = Σ₁₇ NG_adj − 12.856 = 277.576 − 12.856 = 264.720 TWh
```

— **5.741 TWh LOWER than today's 270.461**, which would make `CC_REGULAR` materially **worse**.

So the current construction is already **more generous than its own stated principle**, and tightening
it to match moves C1 the wrong way. Equally, zeroing the subtraction outright (`model demand =
277.576`) would ask a fleet that produced 264.720 TWh on the 930 basis to generate 277.576 — the
over-ask the subtraction exists to prevent.

**Neither limb is a fix, and neither is offered as one.** Recording the refutation is the point: it is
the cheapest possible outcome for the next lane, and it was obtained for zero LP.

---

## 6. Where this leaves C1, stated without overclaiming

`CC_REGULAR`'s 2023 miss (−8.219) is smaller than the system gap it absorbs (−9.645), so **closing
the gap is sufficient in principle to clear the row** and the direction is unambiguous. How the
recovered energy splits across `CC_REGULAR`, `CT_PEAKER` and `ST_GAS` — all three of which are short
in all three years — is a question **only a solve answers**, and this lane did not solve. No number
in this section is a result.

What must not happen: closing the 0.219 TWh by weakening NWPP-44's take-or-pay arm. The arm is
measured (EIA-923 Schedule-5 + EIA-860 `Regulatory Status`), carries zero free parameters, and its
scope was fixed ex ante by owner ruling. Reverting it to recover a 0.219 TWh band overrun is precisely
the burying rule 14 `[R-ACCURATE]` forbids, and it would leave a 9.6 TWh system gap untouched
underneath.

---

## 6b. The C2 PASS carries no information about the gas family — by design, not by defect

A reader of the keeper's `metrics.json` sees `C2 system volume (gas/coal families): PASS` and could
reasonably conclude NWPP's gas volume is fine. It is not, and C2 was never asked.

| year | family | C2 status | model | actual | Δ TWh | Δ % |
|---|---|---|---|---|---|---|
| 2023 | **gas** | **PASS** | 58.25 | 71.78 | **−13.53** | **−18.8 %** |
| 2023 | coal | PASS | 44.30 | 40.40 | +3.90 | +9.7 % |
| 2024 | **gas** | **PASS** | 62.41 | 76.82 | **−14.41** | **−18.8 %** |
| 2024 | coal | PASS | 36.71 | 34.44 | +2.27 | +6.6 % |
| 2025 | gas | SKIPPED | 68.21 | 71.27 | −3.06 | −4.3 % |
| 2025 | coal | SKIPPED | 35.01 | 42.26 | −7.25 | −17.2 % |

`score_sysvol` hard-codes `"status": PASS` for a **fully-reported** family — *"fully-reported family:
governed by C1 per-class"* — and delegates every verdict to C1's per-class band, so it cannot fail on
its own and cannot fail twice for a row C1 already failed. The 2023 gas row even prints
`magnitude: "C1 flags: CC_REGULAR"` beside its PASS. **This is the documented rubric v2.5 design
(owner amendment 2026-07-13), not a bug**, and the reasons for retiring the old ±2.5 %-of-family
percent band are good ones: it invented fails on mid-size families and masked real per-class misses
that netted out.

**Recorded because of what it means for reading this keeper**, not as a criticism of the rubric: the
only year whose gas family is measured against a family-level percent band is 2025, the preliminary
vintage, where it is **SKIPPED**. So no gate anywhere in NWPP's determination tests the gas family's
volume, and a **−18.8 % family error in two consecutive years passes C2 silently**. That is the same
object §3 measures from the demand side, seen through the scorer.

---

## 7. Carried, absorbed nowhere

* **C4 `dispatch_corr` still FAILS in all three years.** Re-scored on the committed artifacts: coal
  `r = 0.605 / 0.595 / 0.610` against a 0.70 floor; `NRMSE = 0.260 / 0.246 / 0.284`, inside 0.30 in
  every year. The root cause is the **rising-curve defect** (NWPP-43 §4.1) — NWPP-44 enlarged the
  cheap block, it did not build a stack — and that remains C4's real successor. Untouched here.
* **`CC_REGULAR` is short in every year, not only 2023**: −8.219 / −6.323 / −4.714. 2024 passes at
  −6.323 and 2025 is SKIPPED on the preliminary EIA-923 vintage. **2023 is not a special year** — it
  is the year the same defect is largest, and 2025's apparent improvement is partly the vintage skip
  plus the +4.904 non-thermal swing, not a structural gain.
* **`ST_GAS` is effectively dead in the model** — 0.126 / 0.224 / 0.176 TWh against an actual
  1.448 / 4.617 / 4.053. It passes C1 only because the 8 TWh band is wide. Named, not diagnosed.
* **Energy balance −10.02 TWh in 2025 against a ±3.0 tol** — §3 now supplies the arithmetic behind it.
  It is the same object as the C1 gap, measured on the EIA-930 leg instead of the EIA-923 leg.
* Unchanged and inherited verbatim: Chief Joseph's pond dual; C5a CO2 a reported-only FAIL
  (−12.1 / −16.2 / −15.1 %); Jim Bridger absent from `thermal_tranches_NWPP.csv`; `highspy` 1.15.1 in
  shard containers against 1.14.0 in older keepers; the NWPP-42 keeper's `meta.json` `gas_prices`
  defect; **the NWPP-40/41/42 attestation corrections (`use_campd_bins` is NOT inert and
  `thermal_tranches_NWPP.csv` IS read) are still owed** and were not discharged here.
* **Pre-existing test state — re-verified BY CONSTRUCTION, which is stronger than a suite run.**
  `git diff --name-status origin/main...HEAD -- src scripts` returns **two `A` rows and nothing else**:
  the two new probe files, which no module imports. There is **no `M` under `src/` or `scripts/`**, so
  no code path this lane could have moved exists, and every failure in
  `tests/unit/{pipeline,config,data}` is pre-existing by definition. **An exact whole-suite census was
  NOT obtained** and is not claimed: the run was stopped at **27 % with 17 failures**, the first being
  `test_forecast_xyear_warmstart_flag.py::TestFieldRegistration::test_default_cache_key_unmoved`
  (also reproduced on its own under `-x`). Extrapolated, that is consistent with the ~35 the charter
  carries. **Not repaired; they belong to other lanes.**
* **CORRECTION to the charter's carried list: `scripts/check_cache_key_registration.py` now PASSES on
  `main`.** It reads *"ok: 869 ScenarioConfig fields, 323 registered in `_CACHE_KEY_OPTIONAL_FIELDS`,
  all resolve; 323 declared defaults all match HEAD; 309 solve-surface names across 7 module(s), all
  declared"*, exit 0, at `e2609a8f`. The `PPA_COST_RECOVERY_YR` / `REGIONAL_RENEWABLE_CF` failure the
  charter and `RESULT-nwpp-44` §7 both carry has been fixed by its own lane since. Carried forward as
  an open item it is no longer, and a successor should stop re-reporting it.

---

## 8. THE QUESTION FOR THE OWNER — this lane deliberately did not decide it

Closing the gap means changing the **energy requirement** the LP serves. That is a
demand-construction change worth **9–12 TWh/yr**; it moves every class in every NWPP year, and it is
the only channel that reaches this defect. Three framings, none of which this lane may pick on its
own — rule 1 `[R-STRUCT]` forbids selecting a mechanism because the residual moves, and the residual
is exactly what would be moving:

1. **Resolve the GRID / AVRN attribution** and rebuild the subtrahend from plant-level evidence
   rather than interchange legs. Needs an EIA-930 generation-only-BA plant crosswalk the repo does
   not carry — an intake, not a solve.
2. **Anchor the demand construction to the same plant basis C1 scores on** (EIA-930 hourly *shape*,
   EIA-923 plant *energy*). Defensible under rule 14's misalignment exception — *"prefer a reconciled
   version of the real data over a pure guess"* — but it is a reconciliation of a measured input whose
   effect is to close the scored residual, which sits close to what rule 13 `[R-MEASURED]` forbids.
   **This lane will not make that call unilaterally.**
3. **Rule that the 930-vs-923 disagreement is a benchmark-side question** and route it to the scorer
   rather than the demand path.

**Cost, stated before anything is spent (rule 31 `[R-RETAIN]`):** whichever is chosen, validating it
is a full NWPP span — **one shard per year under rule 36 `[R-YEAR-ISOLATION]`, ~90 min/year and up to
~3 h for 2024** (whose warm-started P1 ran 11,600 s against its own P0's 1,400 s), each pushing its
FULL bundle including `dispatch/<y>_P1.parquet` (rule 34 `[R-SHARD-PROMOTABLE]` (a)), plus
`--hydro-backfill-year 2024` on every leg. **This session spent zero LP and left nothing on
ephemeral disk**, so there is no promotion decision pending and nothing is at risk of being lost.

---

## 9. Reproduction

```
python3 scripts/calibration_verdict.py --run-id 2026-09-20-nwpp-44-measured-take
python3 scripts/probes/_nwpp45_ccregular_phase0.py 2023 2024 2025
python3 scripts/probes/_nwpp45_demand_basis.py
```

The first two need only the committed artifacts; `_nwpp45_demand_basis.py` additionally reads
`data/raw/eia-930-hourly/` and `data/raw/eia-930-interchange/` (`DATA PROFILE: nwpp`).
